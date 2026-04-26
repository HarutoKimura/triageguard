# TriageGuard — State, Architecture, and What's Left

This document gives a single-pass mental model: what TriageGuard is,
what we've built, and exactly what's left between here and the
3-minute submission demo.

Last updated: end of Day-2 (PR #2 merged into `main`).
Branch in flight: `sprint/day-3`.

---

## 1. Problem

Open-source maintainers are being crushed by AI-generated vulnerability
reports.

- HackerOne paused the Internet Bug Bounty program on 2026-03-27.
- curl killed its bounty program in January 2026.
- Google rejects AI-generated submissions outright.
- The valid-submission rate dropped from ~15% to under 5%.

Every fabricated report still costs a human ~30–60 minutes to dismiss
(read, attempt repro, search for the named function/file, write the
rejection). That cost is the bottleneck. Maintainers don't need
better detection of *real* bugs — they need a triager that can reject
AI slop before it lands in their inbox.

## 2. Product (one sentence)

**TriageGuard takes a vulnerability report + optional PoC + claimed
affected code, runs four parallel sub-agents (Reproducibility, Root
Cause, Duplicate, Hallucination), and emits a Signal Score (0–100) +
SIGNAL/UNCERTAIN/SLOP label + 2–3 paragraph natural-language
explanation that a maintainer can act on in 60 seconds.**

The pitch line: **"Signal vs. Slop, with receipts."** Every claim in
the verdict cites a concrete artifact field — file, line, sanitizer
frame, fabricated function name.

---

## 3. Approach (why this shape)

Four observations drove the architecture:

1. **The four checks a triager actually does are independent.** "Does
   the PoC reproduce?" / "Does the cited code match source?" / "Is
   this already a known CVE?" / "Are the cited functions/lines real?"
   are answered by different evidence and don't need to share state.
   → Parallel sub-agents, file-based handoff.

2. **The scoring rule should be auditable, not LLM-judged.** A judge
   should be able to read the rule that fired and check it against
   the agents' outputs. → Deterministic Python synthesizer with 9
   numbered rules; zero LLM calls in scoring.

3. **Maintainers want prose, not just a number.** A "SIGNAL 90" with
   no explanation is worse than a "SIGNAL 90 because A reproduced
   under ASan, B verified all 8 cited lines, C found no duplicate, D
   found 0 fabrications." → A separate Opus 4.7 narrative pass *after*
   the deterministic rule fires. The rule is the verdict; the narrative
   restates *why*.

4. **Demo > explain.** "Easier to demo than to explain" (Boris
   Cherny). A 3-minute video that shows the agents fanning out,
   landing verdicts, and lighting up fabricated refs in red beats any
   architecture diagram. → A Next.js replay UI fed from cached
   `findings/{report_id}/` artifacts via SSE.

---

## 4. Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  INPUT: demo-inputs/{sample_id}/                                 │
│    - INPUT.md           (report body, verbatim)                  │
│    - INPUT_meta.json    (vendor, tag, claimed CVE, expected ...) │
│    - poc/               (optional PoC source + reproduce.sh)     │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
                ┌────────────────────────────────────┐
                │  orchestrator/run.py               │
                │  asyncio.gather(return_exceptions) │
                └────────────────────────────────────┘
                                 │
       ┌─────────────────┬───────┴────────┬────────────────┐
       ▼                 ▼                ▼                ▼
   ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐
   │ Agent A │      │ Agent B │      │ Agent C │      │ Agent D │
   │ Repro   │      │ RootCause│     │ Duplicate│     │ Halluc.  │
   │ ASan/   │      │ Source  │      │ NVD     │      │ Cite or │
   │ Docker  │      │ verify  │      │ + GHSA  │      │ reject  │
   │ $8 cap  │      │ $3 cap  │      │ $3 cap  │      │ $3 cap  │
   └────┬────┘      └────┬────┘      └────┬────┘      └────┬────┘
        │                │                │                │
        └────────────────┴───────┬────────┴────────────────┘
                                 │ writes JSON artifacts to
                                 ▼
        ┌──────────────────────────────────────────────────┐
        │  findings/{report_id}/                            │
        │   A_reproducibility.json   (verdict, sanitizer)   │
        │   B_root_cause.json        (claims_checked)       │
        │   C_duplicate.json         (queried_databases)    │
        │   D_hallucination.json     (extracted_claims)     │
        │   {A,B,C,D}_think.txt      (per-agent scratch)    │
        │   INPUT.md, INPUT_meta.json (copied)              │
        │   poc/, source/            (PoC + vendor clone)   │
        └────────────────────┬──────────────────────────────┘
                             │
                             ▼
        ┌──────────────────────────────────────────────────┐
        │  orchestrator/synthesizer.py  (DETERMINISTIC)    │
        │   9 numbered rules, first-match wins             │
        │   → SignalScore { score, label, recommendation,  │
        │                   triggering_rule, ensemble_conf }│
        └────────────────────┬──────────────────────────────┘
                             │
                             ▼
        ┌──────────────────────────────────────────────────┐
        │  orchestrator/reasoning.py  (OPUS 4.7 xhigh)     │
        │   Single non-tool call, adaptive thinking        │
        │   → 3-paragraph narrative grounded in artifacts  │
        └────────────────────┬──────────────────────────────┘
                             │
                             ▼
        ┌──────────────────────────────────────────────────┐
        │  findings/{report_id}/                            │
        │   SIGNAL_SCORE.json   (final verdict + narrative) │
        │   NARRATIVE.md        (human-readable Opus 4.7)   │
        │   SYNTHESIS.md        (machine-rendered summary)  │
        └────────────────────┬──────────────────────────────┘
                             │
                             ▼
        ┌──────────────────────────────────────────────────┐
        │  web/  (Next.js 15 + Tailwind v4)                │
        │   /                  → list of samples           │
        │   /run/[reportId]    → 4 lanes + Signal Card     │
        │   /api/replay/[id]   → SSE replay of artifacts   │
        └──────────────────────────────────────────────────┘
```

Key invariants:

- **File-based handoff.** Sub-agents write JSON; the synthesizer reads
  it. No transcript passing, no shared memory. This is what makes the
  four agents truly parallel and what makes a partial run still
  useful (3/4 land → the synthesizer can still report missing).
- **English on disk.** All comments, prompts, commit messages, doc
  files. Conversational chat may mirror the user's language; artifacts
  may not.
- **Opus 4.7 at xhigh** for sub-agents + the narrative call. Haiku
  4.5 reserved for any future glue work. This split is part of the
  pitch ("the right model for each job").

---

## 5. Sub-agent contracts

Each sub-agent is a Claude Agent SDK process with two custom in-process
MCP tools (`think`, `emit_verdict`) plus a tightly-scoped allowlist.

| Agent | Verdict | Allowed tools | Budget | Output schema |
|---|---|---|---|---|
| **A** Reproducibility | `reproduced \| failed_to_reproduce \| no_poc \| build_error \| timeout` | Bash, Read, Write, Grep | $8 | `ReproEvidence` (target_tag, sanitizer_summary, sanitizer_frames, exit codes) |
| **B** Root Cause | `match \| partial_match \| mismatch \| file_not_found` | Read, Grep | $3 | `claims_checked[]` (claim, status, file, line_start, snippet, note) |
| **C** Duplicate | `novel \| duplicate \| similar` | Read, Grep, WebFetch, **nvd_fetch** | $3 | `queried_databases[]`, `top_candidates[]`, `matched_cve` |
| **D** Hallucination | n/a (stats-driven) | Read, Grep, WebFetch, **nvd_fetch** | $3 | `extracted_claims[]` (kind, value, status), `invalid_refs[]`, `stats` |

`nvd_fetch` is a custom MCP tool added in Day-2 §6. Read-through disk
cache (`orchestrator/_cache/nvd/`, gitignored, 7-day TTL) with a
polite rate limiter. Both C and D prefer it over `WebFetch` for NVD
URLs; `WebFetch` remains allowed for GHSA and vendor pages.

---

## 6. Synthesizer rubric

`orchestrator/synthesizer.py` — top-down, first-match wins. Lives
parallel to `.claude/skills/signal-score-rubric/SKILL.md` (canonical
spec; the Python is a machine-checkable mirror).

| # | Trigger | Verdict |
|---|---|---|
| 1 | A=failed_to_reproduce + invalid_refs ≥ 2 | SLOP 5–25 |
| 2 | A∈{build_error,no_poc} + B∈{mismatch,file_not_found} | **SLOP 15** |
| 3 | C=duplicate | UNCERTAIN 35 (if reproduced) / SLOP 25 |
| 4 | invalid_refs ≥ 3 | SLOP 20 |
| 5 | A=reproduced + B=match + C=novel + invalid=0 | **SIGNAL 90** |
| 6 | A=reproduced + B=partial_match + invalid ≤ 1 | SIGNAL 75 |
| 7 | A=reproduced + (B=mismatch OR invalid ≥ 2) | UNCERTAIN 55 |
| 8 | A=no_poc + B=match + invalid=0 | **UNCERTAIN 50** |
| 9 | (default) | UNCERTAIN 45 |

Bolded rules are the three rubric buckets demonstrated by our four
live-verified samples. The 38 unit tests in `tests/test_synthesizer.py`
encode every one of these rules.

---

## 7. Demo set (six samples, four verified)

| ID | Content | Expected | State |
|---|---|---|---|
| **s1** | wolfSSL HPKE/ECH stack overflow (real CVE-2026-3849) | SIGNAL 85–90 | ✅ live SIGNAL 90, rule 5, conf 95% |
| **s2** | wolfSSL session deserialization, no PoC (CVE-2026-2646) | UNCERTAIN 45–55 | ✅ live UNCERTAIN 50, rule 8, conf 93% |
| s3 | wolfSSL ECDSA bypass (CVE-2026-5194) | SIGNAL ~90 | ⏳ not registered (optional) |
| **s4** | curl AI-slop, fabricated `parse_content_type_header` | SLOP 10–25 | ✅ live SLOP 15, rule 2, conf 92% |
| **s5** | curl AI-slop, fabricated `Curl_verify_sni_extension` | SLOP 10–25 | ✅ live SLOP 15, rule 2, conf 92% |
| s6 | curl AI-slop (regenerable on demand) | SLOP 10–25 | ⚠ generator works, but **no live findings on disk yet** |

(s7 candidate dropped — out of scope for the 3-minute demo.)

---

## 8. Demo flow (3 minutes, what we want the judge to see)

**Per `.claude/skills/demo-recorder/SKILL.md`** (the canonical shot
list lives there). Approximate beats:

```
0:00–0:15  Hook: state the problem (5% submission rate, IBB paused,
           Google rejecting AI). Cut to maintainer inbox.

0:15–0:50  s1 SIGNAL: click sample, hit Run triage. Watch four lanes
           fill in (C → D → B → A). SIGNAL 90 lands. Read the
           narrative aloud, point at the sanitizer frame +
           hpke.c:492.

0:50–1:30  s4 SLOP: click sample, hit Run triage. Same animation.
           When Hallucination lane lands, three invalid_refs light
           up in red (parse_content_type_header, lib/http.c:342,
           strcpy in lib/http.c). SLOP 15. Point at "what's actually
           at lib/http.c:342" in the narrative.

1:30–2:10  s6 LIVE: switch to terminal. Run the slop generator
           against gpt-4o (or frontier model on demo day). Show the
           500-word advisory. Switch back to UI, click newly-appeared
           s6 card. SLOP again. Punchline: "even the frontier model
           cannot ground claims without source access."

2:10–2:40  Pitch: Opus 4.7 ×4 at xhigh, deterministic synthesizer,
           file-based handoff. Show the SYNTHESIS.md + NARRATIVE.md
           on disk. Show the confidence meter.

2:40–3:00  Wrap: TriageGuard runs on every report before a human
           sees it. Maintainer sees SLOP 15 with a 3-paragraph
           explanation; rejects in 30 seconds, not 30 minutes.
```

The "live regenerate" beat (1:30–2:10) is the demo's theatrical
moment. It requires s6 to be runnable end-to-end on the demo machine
in <60 s. We have the generator script (`scripts/generate_slop.py`)
and the orchestrator handles it natively, but **no s6 findings dir
has been produced live yet** — that's a Day-3 prerequisite.

---

## 9. What's done (Day-1 + Day-2)

### Day 1 (PR #1, merged)

- 4-agent orchestrator + synthesizer + 38 unit tests
- s1 SIGNAL 90 + s4/s5 SLOP 15 live-verified
- Slop generator script with 4 prompt variations
- WRITTEN_SUMMARY.md (199 words)
- Skills, slash commands, sub-agent prompts

### Day 2 (PR #2, merged)

| # | Item | Commit |
|---|---|---|
| §1 | **Web replay UI** — Next.js 15 + Tailwind v4, SSE replay from `findings/`, 4 agent lanes + Signal Card with confidence meter + narrative block. Two routes: `/` and `/run/[reportId]`. | `48c790c` |
| §2 | **Opus 4.7 narrative** — single-shot adaptive-thinking call at xhigh effort, after the deterministic rule. Stored as `signal.narrative` + `NARRATIVE.md`. ~$0.05/call, ~25s wall. | `77bd3c4` |
| §3 | **Ensemble confidence** — geometric mean of 4 sub-agent confidences (D derived from claim-checking coverage). Colored meter on the Signal Card. 7 unit tests. | `94b0000` |
| §4 | **s2 live verify** — UNCERTAIN 50 rule 8 as predicted, $2.89, 133s. (artifacts in gitignored `findings/`) | n/a |
| §6 | **NVD fetch tool** — read-through disk cache + rate limiter, exposed as MCP tool `nvd_fetch` to Agents C and D. Prevents 6-sample dry-run from tripping NVD's 5-req/30-s anonymous limit. | `e9f4f9d` |

### Code health

- 45/45 pytest pass
- ruff clean, mypy strict clean across 34 source files
- `pnpm typecheck` clean, `pnpm build` green (3 routes; CSS bundle 19 KB)

### Budget

| | Spent | Remaining |
|---|---|---|
| Day-1 | ~$17 | |
| Day-2 | ~$3 | |
| **Total** | **~$20** | **~$60 of $80 reserve** |

---

## 10. What's left (Day 3)

### Demo-critical (must-have before recording)

1. **s6 live regeneration + one orchestrator run** (~$3, ~2 min)
   - `python scripts/generate_slop.py --output-dir demo-inputs/s6-live-slop --variation rce`
   - `python -m orchestrator demo-inputs/s6-live-slop/`
   - Confirms findings/ is populated; the home page picks s6 up automatically.

2. **In-browser smoke test** (5–15 min)
   - Open localhost:3100. Click each of s1, s2, s4, s5, s6.
   - Hit Run triage; watch the animation; confirm:
     - The narrative paragraph block renders cleanly (no overflow, line breaks correct)
     - The confidence meter transitions smoothly
     - The 3 invalid_refs on s4 light up in red
     - The "0.5×" / "2×" speed controls feel right
     - Mobile-ish viewport doesn't break the lanes

3. **Demo recording** (2–4 h depending on takes)
   - Per `.claude/skills/demo-recorder/SKILL.md`. Tools likely:
     QuickTime/OBS for screen capture, Audacity for voiceover,
     Remotion (optional) for transitions and overlays.
   - 3 takes minimum; tighten between each.

4. **`/ship-check`** (~5 min, last hour)
   - Verifies repo public-ready, video uploaded, summary in word
     count, license present, no secrets.

### Nice-to-have (Day 3 if time permits)

5. **Vercel deployment** (~30 min if the strategy is just "commit a
   curated set of findings/ JSON"; longer if we want a real seed
   step). Worth it only if judges want a live link.

6. **`/demo-dryrun`** against all 6 samples
   - Sanity check that the NVD cache + sequential rehearser keep
     timing predictable.

7. **Unit tests for Agents C and D plumbing**
   - Currently A/B/synthesizer/confidence are tested. C/D are
     plumbing-verified only.

### Out of scope (don't build)

- s3 (CVE-2026-5194) — not demo-critical
- HackerOne / Bugcrowd / Intigriti API integration
- Auth, billing, DB persistence
- Languages beyond C/C++
- Anything that doesn't change the 3-minute demo

---

## 11. File map (where things live)

```
triageguard/
├── CLAUDE.md                          ← project instructions for Claude
├── STATE.md                           ← this file
├── PROJECT_BRIEF.md                   ← original brief
├── WRITTEN_SUMMARY.md                 ← 199-word submission summary
├── HACKATHON_RULES.md                 ← contest rules
├── README.md
│
├── pyproject.toml                     ← Python deps + ruff/mypy/pytest config
├── Dockerfile.wolfssl                 ← Agent A's sandboxed wolfSSL build
│
├── orchestrator/
│   ├── run.py                         ← fans out 4 agents, synthesizes, narrates
│   ├── synthesizer.py                 ← deterministic 9-rule scorer
│   ├── reasoning.py                   ← Opus 4.7 narrative (Day-2 §2)
│   ├── confidence.py                  ← ensemble geo-mean (Day-2 §3)
│   ├── nvd_client.py                  ← cached fetch tool (Day-2 §6)
│   ├── findings.py                    ← report_id minting, atomic writes
│   ├── schemas.py                     ← Pydantic models for all artifacts
│   └── _cache/nvd/                    ← (gitignored) NVD response cache
│
├── agents/
│   ├── reproducibility/               ← Agent A
│   ├── root_cause/                    ← Agent B
│   ├── duplicate/                     ← Agent C
│   └── hallucination/                 ← Agent D
│       (each has agent.py + tools.py + prompt.py + cli.py)
│
├── web/                               ← Day-2 §1 Next.js UI
│   ├── app/
│   │   ├── page.tsx                   ← home (sample list)
│   │   ├── run/[reportId]/page.tsx    ← detail shell
│   │   └── api/replay/[reportId]/route.ts ← SSE
│   ├── components/
│   │   ├── LiveReplay.tsx             ← orchestrates SSE
│   │   ├── AgentCard.tsx              ← per-agent lane
│   │   ├── SignalCard.tsx             ← score + narrative + confidence
│   │   └── ScorePill.tsx
│   └── lib/
│       ├── findings.ts                ← server-side reader
│       └── types.ts
│
├── demo-inputs/                       ← canonical sample sources
│   ├── s1-cve-2026-3849/
│   ├── s2-cve-2026-2646/
│   ├── s4-curl-slop-1/
│   ├── s5-curl-slop-2/
│   └── s6-live-slop/                  ← regenerated each demo take
│
├── findings/                          ← (gitignored) per-run output
│   └── {report_id}/                   ← one dir per orchestrator invocation
│
├── scripts/
│   ├── generate_slop.py               ← OpenAI-backed AI-slop generator
│   └── regenerate_narrative.py        ← backfill narrative + confidence
│
├── tests/                             ← pytest, 45 tests
│   ├── test_reproducibility.py
│   ├── test_root_cause.py
│   ├── test_synthesizer.py
│   └── test_confidence.py             ← Day-2 §3
│
├── .claude/
│   ├── prompts/                       ← system prompts for the 4 agents +
│   │                                    synthesizer-reasoning
│   ├── skills/                        ← canonical specs (rubric, etc.)
│   ├── agents/                        ← demo-rehearser, simplify-reviewer,
│   │                                    security-reviewer
│   └── commands/                      ← /status, /demo-dryrun, /ship-check, ...
│
└── vendor/                            ← (gitignored) cached vendor clones
```

---

## 12. Mental model — single-paragraph version

You give TriageGuard a vulnerability report (markdown) and metadata
(JSON). Four Opus 4.7 sub-agents — each at xhigh effort, each with a
tightly-scoped tool allowlist — run in parallel against that report.
They write structured JSON artifacts to a shared `findings/` directory.
A deterministic Python synthesizer reads those artifacts and applies
nine numbered rules to pick a Signal Score (0–100), a label
(SIGNAL/UNCERTAIN/SLOP), and a triggering rule number. A second Opus
4.7 call produces a 3-paragraph maintainer-facing explanation grounded
in the artifacts. The whole thing is replayed in a Next.js UI as a
streaming SSE animation, which we screen-capture into the 3-minute
submission video. The pitch is: every claim in the verdict is
auditable; the rule is auditable; the narrative cites the artifacts;
the agent prompts and the rubric live alongside the code.

---

## 13. North star

> "Easier to demo than to explain." — Boris Cherny

If a future change makes the 3-minute demo stronger, ship it. If it
doesn't, defer it.
