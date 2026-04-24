# TriageGuard

Autonomous validator for vulnerability reports. Drops in a report +
PoC + claimed affected code, returns a Signal-vs-Slop verdict with
reasoning.

**Hackathon deadline: 2026-04-26 20:00 EST.** Judging: Impact 30%,
Demo 25%, Opus 4.7 Use 20%, Depth 20%.

## Where to look first

| Question | File |
| --- | --- |
| How do I operate during this sprint? | [.claude/RULES.md](.claude/RULES.md) |
| What are the six demo samples? | [.claude/RULES.md §2](.claude/RULES.md) |
| How do I score a report? | [.claude/skills/signal-score-rubric/SKILL.md](.claude/skills/signal-score-rubric/) |
| How do I build wolfSSL for a CVE? | [.claude/skills/wolfssl-domain/SKILL.md](.claude/skills/wolfssl-domain/) |
| What's the FINDINGS schema? | [.claude/skills/findings-journal/SKILL.md](.claude/skills/findings-journal/) |
| How do I use the Agent SDK here? | [.claude/skills/agent-sdk-patterns/SKILL.md](.claude/skills/agent-sdk-patterns/) |
| How do I prompt Opus 4.7? | [.claude/skills/opus-4.7-playbook/SKILL.md](.claude/skills/opus-4.7-playbook/) |
| How do I make the demo video? | [.claude/skills/demo-recorder/SKILL.md](.claude/skills/demo-recorder/) |

## Problem

HackerOne paused the Internet Bug Bounty program on 2026-03-27. curl
killed its bounty program in January. Google rejects AI-generated
submissions. Valid submission rate dropped from ~15% to under 5%. AI
slop is crushing OSS maintainers.

## Target

- Primary OSS: wolfSSL (C, cryptographic library, ~5 B devices)
- Secondary: curl (for public slop examples)

## Architecture (v1)

- Orchestrator: Python, Claude Agent SDK
- 4 parallel sub-agents: Reproducibility, Root Cause, Duplicate,
  Hallucination
- Synthesizer → Signal Score (0–100) + reasoning
- Frontend: Next.js 16 + Tailwind, streamed via SSE, deployed on Vercel

Sub-agent system prompts live in [.claude/prompts/](.claude/prompts/).
They are read by the Python orchestrator at runtime — do not
duplicate.

## Rules (full list in [.claude/RULES.md](.claude/RULES.md))

- Type hints mandatory (Python), strict TS, no `any`.
- Each product sub-agent: one directory under `agents/`.
- Shared state via file-based handoff under `findings/{report_id}/`.
- Never invent functions or APIs; verify before calling.
- Report "unknown" / "failed to reproduce" honestly; no
  plausible-but-wrong fallbacks.
- Minimum code that works; prefer `/simplify` thinking over
  scaffolding.
- Opus 4.7 at `xhigh` for sub-agents + synthesizer; Haiku 4.5 for
  glue. This split is mentioned in the pitch.

## Out of scope (do not build)

- Languages beyond C/C++
- HackerOne / Bugcrowd / Intigriti API integration
- Authentication, billing, DB persistence
- Automatic patch generation
- Multi-tenant, user accounts
- Anything that doesn't change the 3-minute demo

## Verification before marking complete

1. Does the code compile?
2. Did the relevant test pass?
3. Does output match the schema in
   [.claude/skills/findings-journal/SKILL.md](.claude/skills/findings-journal/)?

If any answer is unclear, state it — do not guess. Run `/verify-done`.

## Slash commands (in [.claude/commands/](.claude/commands/))

- `/status` — sprint state, hours to deadline
- `/record-finding` — add a sample to `demo-inputs/`
- `/run-sample` — run one sample end-to-end
- `/demo-dryrun` — run all six via the demo-rehearser subagent
- `/verify-done` — pre-commit verification
- `/ship-check` — submission-day preflight
- `/opus-audit` — detect CLAUDE.md / skill conflicts

## Sub-agents (in [.claude/agents/](.claude/agents/))

- `simplify-reviewer` — ruthless deletion list
- `security-reviewer` — sandbox, secrets, supply-chain review
- `demo-rehearser` — timed rehearsal of all six samples

## Memory

Long-term user preferences + project state live at
`~/.claude/projects/-Users-HarutoKimura-stella-sec-triageguard/memory/`.
See `MEMORY.md` there.
