---
description: Run one of the six demo samples end-to-end through the TriageGuard pipeline and print the verdict, timings, and per-sub-agent deltas.
argument-hint: [sample-id]
---

Run a single demo sample end-to-end.

## Steps

1. If `$ARGUMENTS` is empty, list the samples in `demo-inputs/` and
   ask which one.
2. Confirm `demo-inputs/{sample-id}/INPUT.md` and `INPUT_meta.json`
   exist. If not, point at `/record-finding`.
3. Execute:
   ```bash
   .venv/bin/python -m orchestrator demo-inputs/$SAMPLE_ID
   ```
   Stream stdout to the terminal. Do NOT swallow it. Pass `--dry-run` to
   validate plumbing without any Agent SDK calls.
4. When the run finishes, read:
   - `findings/*/SIGNAL_SCORE.json` (the latest run's JSON)
   - `findings/*/SYNTHESIS.md` (the human verdict card)
5. Print:
   ```
   Sample: {sample-id}
   Expected: {label} {score_min}-{score_max}  (from INPUT_meta.json)
   Actual:   {label} {score}                  (from SIGNAL_SCORE.json)

   Verdict match: ✓ | ✗
   Wall-clock: {sec}s
   Cost: ${cost}
   Per-agent:
     A (reproducibility): {verdict} ({sec}s)
     B (root cause):      {verdict} ({sec}s)
     C (duplicate):       {verdict} ({sec}s)
     D (hallucination):   {invalid_count} invalid refs ({sec}s)

   Synthesis:
   {inline SYNTHESIS.md}
   ```
6. If the actual verdict does not match expected:
   - Do NOT modify the rubric.
   - List the most likely cause in one sentence (usually Agent A's
     build config or Agent D's allow-list).
   - Suggest which log file to read first.

## Don't

- Do NOT delete old `findings/` runs — they are demo history.
- Do NOT silently retry on failure. Surface the error.
