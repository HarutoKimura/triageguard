---
description: Full demo rehearsal — invoke the demo-rehearser subagent to run all six samples, time each, and emit a GO/HOLD/BLOCK verdict. Mandatory before recording.
---

Kick off the `demo-rehearser` subagent. Its job is to run the full
six-sample battery, time it, compare verdicts to expected, and tell
you whether the demo is fit to record.

## Steps

1. Confirm `demo-inputs/` has six subdirectories (s1..s6). If not,
   abort and point the user at `/record-finding`.
2. Spawn the `demo-rehearser` subagent. Give it this instruction:

   > Run the full rehearsal now. Use the procedure in
   > .claude/agents/demo-rehearser.md verbatim. Write the report to
   > rehearsals/{UTC timestamp}/report.md.

3. When the subagent returns, read the report and echo its final
   verdict (GO / HOLD / BLOCK) into the current chat. Cite the
   report path so the user can click through.
4. If HOLD or BLOCK:
   - Surface the single most important issue.
   - Stop. Do not attempt fixes from this command. The user runs
     `/verify-done` or the relevant build command next.

## Why a subagent, not inline

The rehearsal floods context with tool calls, SSE streams, and six
full synthesis outputs. Running it in a subagent isolates that noise
so the main conversation stays focused on the verdict.

## Don't

- Do NOT skip samples to "save time." A partial rehearsal is
  useless.
- Do NOT green-light a demo where sample 6 (live-generated slop)
  landed above SLOP. That's the most demo-critical sample; if it's
  wrong, the theatrical beat breaks.
