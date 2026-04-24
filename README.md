# TriageGuard

**Autonomous validator for vulnerability reports.** Drop in a report
+ PoC + claimed affected code; get back a Signal-vs-Slop verdict with
reasoning in ~12 minutes.

> Built for the Anthropic "Built with Opus 4.7" hackathon,
> 2026-04-24 – 2026-04-26.

## Why

The bug bounty industry is collapsing under AI-generated low-quality
reports. HackerOne paused the Internet Bug Bounty program on
2026-03-27 after 13 years. Google's OSS VRP rejects AI-generated
submissions outright. curl ended its program. Valid submission rate
at major programs dropped from ~15 % to under 5 %.

The ecosystem bottleneck has shifted from **discovery** to
**validation**. TriageGuard attacks that new bottleneck.

## How it works

```
Report + PoC + target repo
         │
         ▼
  Orchestrator (Python + Claude Agent SDK)
         │
         ├──▶ Agent A — Reproducibility (Opus 4.7, xhigh)
         ├──▶ Agent B — Root Cause       (Opus 4.7, xhigh)
         ├──▶ Agent C — Duplicate        (Opus 4.7, xhigh)
         └──▶ Agent D — Hallucination    (Opus 4.7, xhigh)
         │
         ▼
  Synthesizer — deterministic rule engine
         │
         ▼
  Signal Score 0–100  +  SIGNAL / UNCERTAIN / SLOP
         │
         ▼
  Streamed to the web UI via SSE
```

Four Claude Agent SDK sub-agents run in parallel, each writing a JSON
artifact. A deterministic rule engine (not an LLM) produces the final
score — auditable, reproducible, cheap.

Primary target: **wolfSSL** (C, cryptographic library, ~5 B devices).

## How Opus 4.7 is used

- **Long-horizon autonomy** — Agent A spends 10–15 min unattended
  cloning wolfSSL, building with ASan, running the PoC, and inspecting
  the crash.
- **Pushes back** — Agent D refuses to confirm plausible-looking
  references without evidence. This is the product's core trait.
- **Self-verification** — every sub-agent calls a `think` tool before
  emitting its verdict; adaptive thinking fires only where reasoning
  is hard.
- **Precise instruction following** — strict verdict schemas, closed
  enum values, zero hedging.

Hybrid model split: Opus 4.7 at `xhigh` for the sub-agents and
synthesizer; Haiku 4.5 for glue (report parsing, output shaping).

## Demo samples

Six fixed inputs. Three real wolfSSL CVEs (mine), two public curl slop
reports, one live-generated during the demo itself.

## Repo layout

```
orchestrator/         Python pipeline (Agent SDK orchestrator + synthesizer)
agents/               Per-sub-agent Python wrappers
frontend/             Next.js 16 + Tailwind + SSE consumer
findings/             Per-run artifacts (git-ignored)
demo-inputs/          The six evaluation samples
video/                Remotion project for the 3-minute demo
Dockerfile.wolfssl    Sandboxed wolfSSL build for Agent A
.claude/              Claude Code harness — skills, agents, commands, hooks
```

## Getting started

```bash
# 1. Env — edit, don't commit.
cp .env.example .env  # fill ANTHROPIC_API_KEY
chmod 600 .env

# 2. Python deps.
uv sync  # or: pip install -e ".[dev]"

# 3. Prove the rubric works (no API calls).
pytest tests/

# 4. Build the wolfSSL sandbox (first time only, ~5 min).
docker build -f Dockerfile.wolfssl \
  --build-arg WOLFSSL_TAG=v5.6.4-stable \
  -t triageguard/wolfssl:v5.6.4-stable .

# 5. Run one sample (requires demo-inputs populated first).
python -m orchestrator.cli --input demo-inputs/s1-cve-2026-2646
```

Inside Claude Code: read [.claude/RULES.md](.claude/RULES.md) first,
then use `/status` · `/record-finding` · `/run-sample` ·
`/demo-dryrun` · `/verify-done` · `/ship-check`.

## License

MIT. See [LICENSE](LICENSE).

## Credits

Built by [Haruto Kimura](mailto:harutokimura0608@gmail.com) — a bug
bounty researcher with 9 published CVEs across wolfSSL, Mozilla NSS,
and PowerDNS. "I helped create this crisis. TriageGuard is my
contribution to solving it."
