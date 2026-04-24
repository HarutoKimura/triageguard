---
name: opus-4.7-playbook
description: Prompting and harness patterns that exploit Opus 4.7's specific strengths (long-horizon autonomy, precise instruction following, pushes back, self-verification). Use when writing or editing any sub-agent system prompt, Claude.md, tool description, or when Opus 4.7 is behaving unexpectedly (over-triggering, looping, giving up early).
---

# Opus 4.7 Playbook

Reference notes synthesized from:
- `anthoropic-engineering-blog/best-practices-for-using-claude-opus-4-7-with-claude-code.md`
- `live-session-built-with-opus-4.7/hackathon-kickoff-opus-4.7-transcript.md` (Boris Cherny)
- `live-session-built-with-opus-4.7/live-session-1-built-with-opus-4.7-transcript.md` (Tariq)
- `anthoropic-engineering-blog/harness-design-for-long-running-application-development.md`

Boris (Kickoff): **"4.7 is a giant step up in capability. However, if
you use it the same way that you used 4.6, you won't feel that step up."**

Treat every rule in this file as "do this *because* the model changed,
not because it's general prompt wisdom."

---

## 1 · Capabilities worth exploiting

### Long-horizon autonomy

> "I've run 4.7 for multiple days at a time, and it stays on track."
> — Boris, Kickoff

TriageGuard hooks:
- **Agent A** runs 10–15 min unattended (clone → build → run PoC →
  inspect crash). Do not add interactive checkpoints.
- **Auto-mode permissions** for the whole sub-agent run. No human
  presses "yes, continue."

### Precise instruction following

> "Opus 4.7 takes instructions more literally. If you ask it to do
> something, it'll listen more precisely to what you said, and follow
> the instructions better." — Boris

> "If you find Opus 4.7 is over-triggering on something, usually means
> you need to edit your Claude.md to give it a little bit more
> flexibility." — Tariq

TriageGuard hooks:
- Sub-agent prompts are **short, declarative, explicit**. No hedging
  words like "maybe" or "try to".
- If a sub-agent is over-eager, loosen the prompt, don't tighten it.
- Verdict schemas specify allowed values as closed enums. Opus 4.7
  respects enums.

### Pushes back

> Opus 4.7 will refuse an ambiguous prompt rather than hallucinate.
> — `best-practices-for-using-claude-opus-4-7-with-claude-code.md`

TriageGuard hooks:
- **Agent D (Hallucination)** is prompted to *cite or reject*. If a
  reference cannot be verified, mark it `invalid` — do not guess.
- Agent A's "honest failure" mode (`failed_to_reproduce`) relies on
  this trait. Do not write a fallback prompt that says "try harder."

### Self-verification

Opus 4.7's adaptive thinking uses more tokens on harder sub-tasks.

TriageGuard hooks:
- Each sub-agent must call the `think` tool before `emit_verdict`.
  Lists (1) rules applied, (2) evidence gathered, (3) uncertainty.
- Anthropic's think-tool post reports policy compliance jumped 37% →
  57% on τ-Bench.

### Vision

Opus 4.7 reads images at 3.75 MP.

TriageGuard hooks:
- If a report includes a crash screenshot or call-graph, attach as an
  image content block, do not OCR to text.
- Not a blocking capability — many reports are text-only.

---

## 2 · Effort levels

| Effort | Use for | Why |
|--------|---------|-----|
| `xhigh` | All four sub-agents, synthesizer | Autonomy + intelligence without runaway tokens |
| `high` | — | Skip — jump to xhigh |
| `medium` | Haiku glue calls | n/a (Haiku runs at its own effort) |
| `max` | Never | "Runaway token usage on long agentic runs" per best-practices blog |

`xhigh` is the default for everything that matters. If you're tempted
to use `max`, tighten the prompt instead.

---

## 3 · Prompt shapes that work

### Role + responsibility + constraints + output (XML blocks)

Anthropic's multi-agent research post: structure sub-agent system
prompts with clear XML sections. Opus 4.7 attends to them reliably.

```
<role>Reproducibility Verifier (Agent A)</role>

<responsibility>
Determine whether the vulnerability report's claimed behavior can be
reproduced when building the target software at the claimed vulnerable
version.
</responsibility>

<constraints>
- You may run Docker, make, gdb, and ASan-instrumented binaries.
- You may not edit source code. Only build and execute.
- If the build fails for reasons unrelated to the claimed bug, say so.
- You may call `think` unlimited times.
- You must call `emit_verdict` exactly once to finish.
</constraints>

<output_format>
Write a JSON artifact per the schema in
.claude/skills/findings-journal/SKILL.md §2.
</output_format>
```

### Directives beat hedges

Bad (4.6-era): "It might be helpful to try running the PoC once the
build is complete, if that makes sense."

Good (4.7-era): "Run the PoC. Capture stdout and stderr. If the binary
exits non-zero, include the last 50 lines in `evidence.poc_log_tail`."

Opus 4.7 executes literal instructions precisely; hedging just adds
latency.

### Ask for reasoning when it's hard

> "This vulnerability classification is harder than it looks; think
> carefully step-by-step before choosing a verdict."

Prompt like this triggers deeper adaptive thinking. Use only for the
synthesizer's hard cases and when Agent B must decide `partial_match`
vs `mismatch`.

---

## 4 · CLAUDE.md conflict audit

Tariq (Session 1): **"Claude.md can conflict with skills... making
sure that Claude, if you give it conflicting information, tends to do
different things."**

Run `/opus-audit` (see `.claude/commands/`) at the start of Day 2 and
before the final demo recording. The command:

1. Diffs every skill's `description` against the last week of
   conversation context.
2. Lists any `description` that names a file that no longer exists.
3. Lists any two skills with overlapping triggers.
4. Reports unresolved TODOs in CLAUDE.md.

If the audit lists a conflict, the highest-priority source of truth
is this file + `.claude/RULES.md` + the six demo samples. Older
drafts lose.

---

## 5 · When Opus 4.7 is misbehaving

### Symptom: over-triggering a skill

*"Every time I ask to read a file it also re-runs a build."*

Fix: the skill's `description` is too broad. Rewrite to narrow the
trigger with specific phrases ("when the task involves wolfSSL PoC
execution") and mark which keywords should *not* match ("NOT for
generic C programs").

### Symptom: sub-agent returns without writing the artifact

*"Agent B finished successfully but `B_root_cause.json` doesn't exist."*

Fix: the system prompt told Opus to "write the file"; Opus wrote a
text response describing the file instead. Replace with a custom
`emit_verdict` tool and instruct: "You have not finished until you
have called `emit_verdict` once."

### Symptom: agent refuses to produce a verdict

*"Agent B keeps calling Grep and never decides."*

Fix: add a turn-budget hint in the prompt: "After 10 Grep calls,
commit to the best available verdict. You may mark `confidence` low
— that is acceptable."

### Symptom: agent confidently produces the wrong result

Bad sign. Root cause is usually a conflicting instruction elsewhere.
Run `/opus-audit`. Look for a skill description or CLAUDE.md line
that contradicts the sub-agent's intent.

---

## 6 · Context engineering

From Anthropic's context-engineering blog:

- **Always-on**: role preamble, rubric, schema. These sit in the
  system prompt.
- **Just-in-time**: source files, advisory text. Sub-agent pulls them
  via tools.
- **Compacted**: none for TriageGuard. A triage run is <15 min; no
  compaction needed.

> "CLAUDE.md files are naively dropped into context up front, while
> primitives like `glob` and `grep` allow it to navigate its
> environment and retrieve files just-in-time." — context-engineering
> blog

Do not pre-load the wolfSSL source into context. Sub-agents grep it.

---

## 7 · Cost control on xhigh

`xhigh` + Opus 4.7 is not cheap. Four sub-agents × six demo samples
is 24 runs. Budget math:

| Sub-agent | Per-run budget | Typical use |
|-----------|----------------|-------------|
| A Reproducibility | $8 | Docker builds are expensive |
| B Root Cause | $3 | Code navigation only |
| C Duplicate | $3 | HTTP + small context |
| D Hallucination | $3 | Grep + small HTTP |
| Synthesizer | $1 | Rule application |
| Orchestrator | $5 | Coordination, glue |

Per-report total: ~$23. Six samples: ~$140. Live demo re-runs: budget
another $50. Total: ~$190.

Anthropic provides $500 in hackathon credits. Stay well under.

---

## 8 · Quick reminders for the live demo

- Agent A in auto-mode; do not press "continue" during the 3-minute
  video. The model's autonomy is part of the pitch.
- Show the `think` tool's scratchpad in the UI. Judges value
  visible reasoning (Michael Cohen, Session 2).
- Verbose tool-use logs in the UI. Not consumer-facing — judge-facing.
- If the build fails mid-demo on the live GPT-4o slop, **that is the
  demo**. Agent A saying "build_error" proves the product works.
