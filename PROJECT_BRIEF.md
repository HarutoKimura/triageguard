# TriageGuard — Project Brief

## What we are building

TriageGuard is an autonomous validator for vulnerability reports.

A user (typically an OSS maintainer or a bug bounty program triager) drops
in a vulnerability report — markdown text + optional PoC + claimed affected
code — along with the target repository. TriageGuard runs four sub-agents
in parallel for up to 15 minutes, each verifying one dimension of the report.
A synthesizer combines their findings into a single Signal Score (0-100)
with a human-readable verdict and reasoning.

The point of the product is not to find vulnerabilities. It is to tell a
maintainer whether an incoming report is real signal or AI-generated slop,
before a human spends hours triaging it.


## Why this product matters right now

The bug bounty industry is collapsing under AI-generated low-quality reports.

- 2026-03-27: HackerOne paused the Internet Bug Bounty program after
  13 years, $1.5M paid out, 1000+ CVEs
- 2026-03: Google's OSS VRP now rejects AI-generated submissions outright
- 2026-03: The Linux Foundation raised $12.5M in emergency security funding
  from Anthropic, AWS, GitHub, Google, Google DeepMind, Microsoft, and OpenAI
- 2026-01: curl ended its HackerOne bug bounty program
- Valid submission rate at a major program dropped from ~15% to under 5%
- curl maintainer Daniel Stenberg describes the state of the program
  as effectively being DDoS'ed by AI slop

The ecosystem bottleneck has shifted from discovery to validation.
TriageGuard attacks that new bottleneck.


## Why I (the builder) can credibly build this

I am a bug bounty researcher who has published 9 CVEs across wolfSSL,
Mozilla NSS, and PowerDNS. I use AI agents in my own vulnerability
discovery pipeline. I have lived experience on both sides of this
problem: I am one of the people whose work made validation the
bottleneck, and I watch the OSS maintainers I report to struggle
under the volume.

Pitch framing: "I helped create this crisis. TriageGuard is my
contribution to solving it."


## Target domain (MVP scope)

Primary target OSS: wolfSSL (C, cryptographic library, used in ~5B devices).

wolfSSL is chosen because:
- I have 4 published CVEs in it, giving live demo credibility
- Anthropic's Frontier Red Team (Nicholas Carlini) has also reported
  CVEs to wolfSSL, letting the pitch land the parallel with Anthropic
- It is a single, reproducibly-buildable codebase — Docker setup is tractable in 4 days
- Cryptographic vulnerabilities exercise Opus 4.7's reasoning harder
  than simple memory bugs

Secondary: public curl slop reports (used as negative-example inputs).
We do NOT build curl tooling; curl reports are just sample inputs.


## The six demo samples

We validate TriageGuard against six fixed samples during the demo:

1. Real CVE — CVE-2026-2646 (wolfSSL session deserialization heap overflow, mine)
2. Real CVE — CVE-2026-3849 (wolfSSL HPKE/ECH stack buffer overflow, mine)
3. Real CVE — CVE-2026-5194 (wolfSSL ECDSA validation bypass, Anthropic's Carlini)
4. Slop — a public HackerOne slop report filed against curl
5. Slop — a second public HackerOne slop report
6. Slop — generated LIVE during the demo with GPT-4o, submitted on the spot

Expected verdicts: 1-3 marked Signal, 4-6 marked Slop, with reasoning
that cites concrete evidence (reproduction result, function existence,
CVE database matches).


## Architecture

### High-level
Vulnerability report + PoC + target repo
│
▼
Orchestrator (Python, Claude Agent SDK)
│
├──▶ Agent A: Reproducibility Verifier
├──▶ Agent B: Root Cause Analyzer
├──▶ Agent C: Duplicate Detector
└──▶ Agent D: Hallucination Detector
│
▼
Synthesizer Agent
│
▼
Signal Score (0-100) + structured reasoning
│
▼
Streamed to Web UI via SSE

### The four sub-agents

**Agent A — Reproducibility Verifier**
- Clones the target repo at the claimed vulnerable version
- Builds it in a sandboxed Docker container
- Runs the provided PoC
- Observes whether the claimed behavior (crash, leak, etc.) actually occurs
- Verdict: reproducible / failed to reproduce / no PoC provided
- Uses Opus 4.7's long-horizon autonomy (builds can take minutes)
  and tool-use reliability (many git, make, gdb calls)

**Agent B — Root Cause Analyzer**
- Reads the report's claim about where and why the bug exists
- Opens the actual source at the claimed file/function/line
- Checks whether the claimed code path matches reality
- Flags: "claim matches code" / "partial match" / "claim does not match code"
- Uses Opus 4.7's precise instruction following and vision for diagrams

**Agent C — Duplicate Detector**
- Queries NVD, GitHub Security Advisories, past CVEs for the same product
- Uses semantic similarity over advisory text, not just string match
- Flags: novel / duplicate of CVE-XXXX-YYYY / similar to past report
- Uses Opus 4.7's long context to compare multiple advisories at once

**Agent D — Hallucination Detector**
- Extracts every concrete technical claim in the report: function names,
  file paths, variable names, CVE IDs referenced, CVSS vector
- Verifies each claim against the actual codebase (ctags, symbol search,
  file existence) and against public databases
- Flags: all references valid / N references not found: [list]
- Uses Opus 4.7's "pushes back" trait — refuses to confirm a plausible-looking
  claim without evidence

### Synthesizer

Takes the four agent outputs and produces:
SIGNAL SCORE: 12/100 — LIKELY SLOP
Reproducibility: FAILED  — PoC did not compile (missing symbol verify_integrity)
Root cause:       MISMATCH — claimed function parse_header was removed 8 months ago
Duplicate:        NOVEL   — no matching CVE
Hallucination:    3 invalid references — verify_integrity, wolf_safe_check, CVE-2025-99999
Recommendation: REJECT. Likely AI-generated without codebase verification.

The synthesizer does not average scores. It applies rules:
- If reproducibility FAILS and hallucinations exist, it is slop
- If root cause MISMATCH, it is at best stale, probably slop
- Signal verdicts require at least reproducibility PASS and zero hallucinations


## Non-goals (explicitly out of scope for this hackathon)

Do not build any of the following. They are tempting but will eat time.

- Support for languages other than C/C++
- Integration with HackerOne / Bugcrowd / Intigriti APIs
- Automatic patch generation
- Authentication, user accounts, billing
- A persistent database (filesystem + FINDINGS.md is enough)
- Any UI beyond: input form, live agent log stream, final verdict card
- Any form of multi-tenancy


## Tech stack (committed)

| Layer | Choice | Why |
| --- | --- | --- |
| Agent runtime | Claude Agent SDK (Python) | First-class, what CrossBeam used |
| Orchestration | asyncio + `@tool` decorators | Simple, matches builder's prior experience |
| Sandboxing | Docker per agent run | Isolation, reproducible builds |
| Model | Opus 4.7 at `xhigh` effort for agents, Haiku 4.5 for glue | Hybrid, cost-controlled |
| Frontend | Next.js 16 + Tailwind | Same as CrossBeam |
| Streaming | Server-Sent Events | Lets the UI show agent thinking in real time |
| Deploy | Vercel (frontend) + a container host for the orchestrator | Free-tier is enough |
| Domain | None — use `triageguard.vercel.app` | Save time, no marketing before submission |


## How Opus 4.7's specific strengths map to the product

This is the answer we give under "Opus 4.7 Use (20%)" in judging:

- **Long-horizon autonomy**: one report validation takes 10-15 min of
  uninterrupted agent work (clone, build, run PoC, search DBs). Earlier
  models give up or loop.
- **Self-verification**: Agent A must honestly report "could not reproduce"
  rather than fabricating a plausible success. This is the single most
  important capability for this product.
- **Strict instruction following**: agents follow the verdict schema
  exactly, no skipped fields.
- **Tool-use reliability**: each agent makes dozens of git, docker, fs,
  and HTTP calls per run. Tool errors are the old bottleneck.
- **Pushes back**: Agent D refuses to accept hallucinated references
  even when the surrounding prose is persuasive.
- **Vision**: for reports that include crash screenshots or call-graph
  diagrams, Opus 4.7 reads them at 3.75 MP.


## Development plan (4 days)

### Day 1 (Friday 4/25)
- Python env, Agent SDK installed
- Dockerfile that builds wolfSSL at a chosen vulnerable version
- Orchestrator skeleton that can spawn one agent
- Agent A (Reproducibility Verifier) end-to-end on sample 1
- Output: CLI prints a verdict for one sample

### Day 2 (Saturday 4/26)
- Agents B, C, D implemented
- Synthesizer combining all four
- All six samples run end-to-end via CLI
- Minimal Next.js UI with file drop and a streaming verdict panel

### Day 3 (Sunday 4/27) — submission day
- UI polish using design-system-in-HTML approach
- Record 3-minute demo video with Remotion
- Write README with problem framing, architecture, demo samples, limitations
- Deploy to Vercel
- Flip repo public
- Submit by Sunday night


## Operating principles while building

These are directives for Claude Code during this project:

1. **Verify before claiming done.** If a build succeeds, rerun it. If a
   test passes, print the output. Do not mark a task complete on plausibility.
2. **Honest about missing information.** If data is not available, say so.
   Do not synthesize a placeholder that looks real.
3. **Minimum code that works.** Prefer deleting code over adding it.
   Prefer small obvious functions over clever abstractions. We have 4 days.
4. **No inventing APIs.** Every function, library, or tool call must be
   verifiable in documentation or source. If unsure, stop and check.
5. **One feature at a time, end-to-end.** Finish Agent A fully — including
   a test that runs it against sample 1 — before starting Agent B.
6. **FINDINGS.md is the source of truth.** Every agent writes its output
   there. The synthesizer reads only from FINDINGS.md.
7. **Fail loudly.** Surface errors to the user rather than swallowing them.
   The product's entire value proposition is honest failure.
