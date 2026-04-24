---
name: signal-score-rubric
description: Scoring rubric that converts the four TriageGuard sub-agent verdicts (Reproducibility, Root Cause, Duplicate, Hallucination) into a 0–100 Signal Score and a SIGNAL/SLOP/UNCERTAIN label. Use whenever computing, critiquing, or displaying a Signal Score, writing the synthesizer, or debating whether a report is signal or slop.
---

# Signal Score Rubric

This is the **rules engine**, not a formula. The synthesizer does not
average sub-scores. It applies these rules in order and stops at the
first match.

---

## 1 · Final labels

| Label | Range | Meaning |
|-------|-------|---------|
| SIGNAL | 70–100 | Accept for human triage; evidence strong |
| UNCERTAIN | 40–69 | Borderline; surface to a maintainer for a fast read |
| SLOP | 0–39 | Reject; AI-generated low-quality or stale claim |

A maintainer reads only SIGNAL and UNCERTAIN. SLOP flows to an
auto-reply.

---

## 2 · Sub-agent outputs (what the synthesizer consumes)

Each sub-agent writes one JSON artifact. Exact schemas in
`.claude/skills/findings-journal/SKILL.md`. The synthesizer reads the
five fields below:

| Field | Source | Values |
|-------|--------|--------|
| `reproducibility.verdict` | Agent A | `reproduced` / `failed_to_reproduce` / `no_poc` / `build_error` |
| `root_cause.match` | Agent B | `match` / `partial_match` / `mismatch` / `file_not_found` |
| `duplicate.verdict` | Agent C | `novel` / `duplicate` / `similar` |
| `duplicate.matched_cve` | Agent C | CVE ID string or null |
| `hallucination.invalid_refs` | Agent D | list of unverified claims |

---

## 3 · Synthesizer rules (apply top-down, first match wins)

```
RULE 1 — Killer: explicit slop
  IF A.verdict == "failed_to_reproduce"
     AND len(D.invalid_refs) >= 2
  THEN label=SLOP, score=max(5, 30 - 5*len(D.invalid_refs))
       reason="PoC failed AND {N} fabricated references"

RULE 2 — Killer: build never worked and claims don't match code
  IF A.verdict in ("build_error", "no_poc")
     AND B.match in ("mismatch", "file_not_found")
  THEN label=SLOP, score=15
       reason="No working PoC and claims do not match code"

RULE 3 — Duplicate of a public CVE
  IF C.verdict == "duplicate"
  THEN label=SLOP (or UNCERTAIN if A reproduced), score=25
       reason="Duplicate of {matched_cve}"

RULE 4 — Hallucinations only, nothing else
  IF len(D.invalid_refs) >= 3
  THEN label=SLOP, score=20
       reason="{N} fabricated code references"

RULE 5 — Clean signal
  IF A.verdict == "reproduced"
     AND B.match == "match"
     AND C.verdict == "novel"
     AND len(D.invalid_refs) == 0
  THEN label=SIGNAL, score=90
       reason="Reproduced, matches code, novel, no fabrications"

RULE 6 — Partial signal: reproduced but root cause partial
  IF A.verdict == "reproduced"
     AND B.match == "partial_match"
     AND len(D.invalid_refs) <= 1
  THEN label=SIGNAL, score=75
       reason="Reproduced, partial root-cause match"

RULE 7 — Borderline
  IF A.verdict == "reproduced"
     AND (B.match == "mismatch" OR len(D.invalid_refs) >= 2)
  THEN label=UNCERTAIN, score=55
       reason="PoC runs but claims drift from code"

RULE 8 — No PoC but claims check out
  IF A.verdict == "no_poc"
     AND B.match == "match"
     AND len(D.invalid_refs) == 0
  THEN label=UNCERTAIN, score=50
       reason="No PoC provided, but code claims verify"

RULE 9 — Default
  label=UNCERTAIN, score=45
  reason="Insufficient evidence either direction"
```

---

## 4 · Display format (human verdict card)

```
SIGNAL SCORE: 85/100 — SIGNAL

Reproducibility: PASS
  Build succeeded at wolfssl@v5.6.4-stable. PoC triggered heap overflow
  in wolfSSL_d2i_SSL_SESSION (ssl.c:13421) under ASan.

Root cause:      MATCH
  Claim points to wolfSSL_d2i_SSL_SESSION; bug is at that function, line
  13421 ± 20 lines.

Duplicate:       NOVEL
  No matching record in NVD or GHSA since 2023-01.

Hallucination:   CLEAN
  All 6 concrete references verified (2 functions, 3 files, 1 CVSS string).

Recommendation: ACCEPT for triage.
```

For SLOP:

```
SIGNAL SCORE: 12/100 — SLOP

Reproducibility: FAILED
  PoC did not compile: undefined reference to `verify_integrity`.
  No such symbol exists in wolfssl@v5.6.4-stable.

Root cause:      MISMATCH
  Claim cites parse_header() — no function with that name in src/.

Duplicate:       NOVEL

Hallucination:   3 invalid references
  - function verify_integrity (not found)
  - function wolf_safe_check (not found)
  - CVE-2025-99999 (not in NVD)

Recommendation: REJECT. Likely AI-generated without codebase verification.
```

---

## 5 · Tuning guardrails

- **Never average.** Averaging lets one strong signal mask one killer.
- **No silent clamps.** If a score is forced into a range by a rule, the
  reason text must say so.
- **Tie-breakers favor rejection.** In borderline cases, default to
  UNCERTAIN, not SIGNAL. Maintainers pay the cost of false positives.
- **The synthesizer is code, not an LLM.** It reads JSON and applies the
  rules above deterministically. Only the per-agent verdicts are LLM
  outputs. This is deliberate: the scoring is auditable.

---

## 6 · Expected scores for the six demo samples

| # | Input | Expected label | Expected score | Triggering rule |
|---|-------|----------------|----------------|-----------------|
| 1 | CVE-2026-2646 | SIGNAL | 85–90 | Rule 5 |
| 2 | CVE-2026-3849 | SIGNAL | 80–90 | Rule 5 or 6 |
| 3 | CVE-2026-5194 | SIGNAL | 85–95 | Rule 5 |
| 4 | curl slop #1 | SLOP | 10–25 | Rule 1 or 4 |
| 5 | curl slop #2 | SLOP | 10–25 | Rule 1 or 4 |
| 6 | Live GPT-4o slop | SLOP | 5–20 | Rule 1 or 2 |

If a sample lands outside these ranges during Day 2, the bug is in
the sub-agent, not the rubric. Do not fudge the rubric to make a
sample pass.
