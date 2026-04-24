---
name: agent-sdk-patterns
description: Python Claude Agent SDK idioms for TriageGuard — spawning parallel sub-agents, streaming tool events, file-based handoff, break-on-result, budget caps, and sandboxed tool calls. Use whenever writing or debugging anything under `orchestrator/` or `agents/` or any file that imports from `claude_agent_sdk`.
---

# Claude Agent SDK — TriageGuard patterns

These are the non-negotiable Python patterns. They come from (1) the
Agent SDK docs we ship with, and (2) cc-crossbeam's bitter learnings
as a past hackathon winner. Every pattern here has a reason.

---

## 1 · The canonical orchestrator call

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def run_subagent(
    *,
    system_prompt: str,
    user_prompt: str,
    tools: list[str],
    findings_dir: pathlib.Path,
    budget_usd: float = 5.0,
    max_turns: int = 500,
    model: str = "claude-opus-4-7",
    effort: str = "xhigh",
) -> SubAgentResult:
    options = ClaudeAgentOptions(
        system_prompt={"type": "preset", "preset": "claude_code",
                       "append": system_prompt},
        setting_sources=["project"],         # enables skill discovery
        permission_mode="bypassPermissions",  # fully autonomous sub-agent
        allowed_tools=tools,
        cwd=str(findings_dir),                # scope fs work
        additional_directories=[str(REPO_ROOT)],
        max_turns=max_turns,
        max_budget_usd=budget_usd,
        model=model,
        effort=effort,
        include_partial_messages=True,        # for SSE streaming
    )

    async for msg in query(prompt=user_prompt, options=options):
        await emit_sse(msg)                   # stream to UI
        if msg.type == "result":
            return SubAgentResult.from_message(msg)
            # NOTE: do NOT `continue` past result — SDK will yield
            # follow-up conversations that drain budget (crossbeam).
    raise RuntimeError("query ended without result")
```

Six load-bearing knobs, in order of importance:

1. **`setting_sources=["project"]`** — required for `.claude/skills/` to
   be discovered by the sub-agent. Without it, skills are invisible
   even if they exist on disk.
2. **`max_budget_usd`** — hard cap per sub-agent. Set A (build+PoC) to
   $8, B/C/D to $3 each, synthesizer to $2. Orchestrator gets $25.
3. **`max_turns=500`** — the default 80 is not enough once a sandbox
   starts logging tool calls. Crossbeam: "raised to 500 after
   multiple silent truncations."
4. **`allowed_tools`** — narrow per sub-agent. Agent A gets `["Bash",
   "Read", "Write", "Grep"]`. Agent B gets `["Read", "Grep"]`. Fewer
   tools = sharper behavior.
5. **`include_partial_messages=True`** — required to stream tool calls
   to the UI. Without it, the frontend sees silence until the run ends.
6. **`break on result`** — explicit exit from the async loop. SDK keeps
   yielding follow-up messages after `result`; those burn budget with
   no visible benefit.

---

## 2 · Parallel sub-agents via `asyncio.gather`

```python
async def run_triage(report: Report) -> SignalScore:
    findings_dir = prepare_findings_dir(report)
    save_input_artifacts(findings_dir, report)

    # Fire all four sub-agents concurrently. Do NOT chain.
    a, b, c, d = await asyncio.gather(
        run_agent_a_reproducibility(report, findings_dir),
        run_agent_b_root_cause(report, findings_dir),
        run_agent_c_duplicate(report, findings_dir),
        run_agent_d_hallucination(report, findings_dir),
        return_exceptions=True,
    )

    for name, result in zip("ABCD", (a, b, c, d)):
        if isinstance(result, Exception):
            log_exception(findings_dir, f"agent_{name}", result)

    # Synthesizer reads the five files, not the in-memory results.
    return synthesize(findings_dir)
```

`return_exceptions=True` is deliberate: one sub-agent's crash must not
take down the other three. Each sub-agent's failure mode must still
produce a JSON artifact (marker file with `errors: [...]`).

---

## 3 · File-based handoff (the cc-crossbeam pattern)

Do NOT thread the sub-agent transcript into the next stage. The
synthesizer reads from disk:

```python
def synthesize(findings_dir: pathlib.Path) -> SignalScore:
    artifacts = load_sub_agent_artifacts(findings_dir)
    for agent_name, required in [("reproducibility", True),
                                 ("root_cause", True),
                                 ("duplicate", True),
                                 ("hallucination", True)]:
        if required and agent_name not in artifacts:
            return SignalScore.errored(f"missing {agent_name}")
    return apply_rules(artifacts)  # see signal-score-rubric skill
```

Accept multiple filenames per sub-agent. Sub-agents sometimes rename
files under Opus 4.7's literal interpretation of a prompt:

```python
REPRO_CANDIDATES = [
    "A_reproducibility.json",
    "reproducibility.json",
    "agent_a.json",
]

def load_with_fallback(dir_: pathlib.Path, names: list[str]) -> dict | None:
    for name in names:
        p = dir_ / name
        if p.exists():
            return json.loads(p.read_text())
    return None
```

Crossbeam's flush wait:

```python
async def read_artifact_after_agent(path: pathlib.Path) -> dict:
    for _ in range(5):
        if path.exists() and path.stat().st_size > 0:
            return json.loads(path.read_text())
        await asyncio.sleep(1)
    raise FileNotFoundError(path)
```

---

## 4 · Tool design for sub-agents

Each sub-agent gets a tiny, named tool set. Names describe intent, not
mechanism.

| Sub-agent | Tools | Why |
|-----------|-------|-----|
| A Reproducibility | `Bash`, `Read`, `Write` | Needs to run docker/make/gdb, read logs |
| B Root Cause | `Read`, `Grep` | Navigates source; no execution |
| C Duplicate | `WebFetch`, `Read`, `Grep` | Queries NVD/GHSA, reads local advisory cache |
| D Hallucination | `Read`, `Grep`, `WebFetch` | Verifies references in source + NVD |

Anti-pattern: giving every sub-agent `Edit` and `Write`. Sub-agents
should write exactly one file — the JSON verdict. Overly broad write
access encourages scope creep.

### Custom `@tool` for verdict emission

```python
from claude_agent_sdk import tool

@tool(
    name="emit_verdict",
    description=(
        "Write the final JSON verdict for this sub-agent. Call this once "
        "and exactly once at the end of your investigation. The schema "
        "is defined in .claude/skills/findings-journal/SKILL.md. After "
        "calling this, stop."
    ),
)
async def emit_verdict(agent: str, verdict: dict, findings_dir: str) -> str:
    path = pathlib.Path(findings_dir) / f"{agent}.json"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(verdict, indent=2))
    tmp.rename(path)
    return f"verdict written to {path}"
```

A custom tool is better than instructing the model to "write a file
named ...". Opus 4.7 takes instructions literally — give it a single
purpose-built tool.

---

## 5 · Streaming to the UI (SSE)

```python
async def emit_sse(msg) -> None:
    payload = {
        "type": msg.type,
        "ts": time.time(),
    }
    if msg.type == "tool_use":
        payload["tool"] = msg.tool_name
        payload["input_preview"] = truncate(msg.tool_input_json, 200)
    elif msg.type == "tool_result":
        payload["tool"] = msg.tool_name
        payload["exit_status"] = msg.exit_status
    elif msg.type == "thinking":
        payload["thinking_preview"] = truncate(msg.thinking_text, 300)
    elif msg.type == "text":
        payload["text"] = msg.text
    elif msg.type == "result":
        payload["cost_usd"] = msg.total_cost_usd
        payload["turns"] = msg.num_turns
    await sse_queue.put(payload)
```

Michael Cohen (Session 2): the demo effect comes from making agent
reasoning visible. Stream `tool_use` and `thinking` events. Filter
nothing at the UI level; filter in the frontend.

---

## 6 · Sandboxed Bash inside Agent A

Agent A is the only sub-agent that executes untrusted code. Wrap every
build and PoC in Docker:

```python
SANDBOX_CMD = [
    "docker", "run", "--rm",
    "--network=none",
    "--cpus=2", "--memory=2g", "--pids-limit=256",
    "--read-only",
    "--tmpfs", "/tmp",
    "--tmpfs", "/work/scratch",
    "-v", f"{host_workdir}:/work:ro",
    "triageguard/wolfssl-build:latest",
    "timeout", "600", "/work/run_poc.sh",
]

proc = await asyncio.create_subprocess_exec(
    *SANDBOX_CMD,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.STDOUT,
)
```

Crossbeam's learning: HTTP streaming into a sandbox dies at ~5 min due
to load-balancer idle kills. For anything longer, use the detached
pattern (start, poll `docker inspect`, tail logs).

---

## 7 · Think tool for policy compliance

Anthropic's think-tool post (τ-Bench 37% → 57%): add a `think` tool
that has no side effects. Instruct each sub-agent:

> Before calling `emit_verdict`, use the `think` tool to list (1) the
> rules you followed, (2) the claims you verified, (3) any uncertainty.
> Only after `think` may you emit a verdict.

```python
@tool(
    name="think",
    description=(
        "Free-form scratchpad. Use before finalizing a verdict to list "
        "the rules applied, evidence gathered, and remaining uncertainty. "
        "The content is stored but does not affect the verdict."
    ),
)
async def think(content: str) -> str:
    scratch.append(content)
    return "noted"
```

---

## 8 · Model split (Opus 4.7 + Haiku 4.5)

- **Opus 4.7** at `effort=xhigh` for: the four sub-agents, synthesizer.
- **Haiku 4.5** for: parsing the raw report into `INPUT_meta.json`,
  slugifying titles, converting sub-agent outputs into frontend-ready
  snippets.

Haiku is cheap, fast, and reliable for structured transforms. Using it
visibly is a signal of depth in the judging criteria.

---

## 9 · Caching to save budget

Prompt-cache the large static blocks per sub-agent:

```python
system_prompt = [
    {"type": "text", "text": ROLE_PREAMBLE},
    {"type": "text", "text": SIGNAL_RUBRIC,
     "cache_control": {"type": "ephemeral"}},
    {"type": "text", "text": WOLFSSL_DOMAIN_NOTES,
     "cache_control": {"type": "ephemeral"}},
]
```

During the demo, the six samples are run back-to-back. Cache hits drop
cost by 20–40%. Measure, don't assume.

---

## 10 · Error modes that must never silently pass

1. Sub-agent writes no file. Orchestrator must raise.
2. Sub-agent writes malformed JSON. Orchestrator must raise.
3. Sub-agent exceeds budget. Artifact still written, verdict marked
   `errored`, synthesizer produces `SLOP, score=0, label=ERRORED`.
4. Sandbox killed by OOM. Agent A verdict: `build_error` with the OOM
   evidence in `errors`. Never `reproduced`.

The product's entire value proposition is honest failure. The code
must model that.
