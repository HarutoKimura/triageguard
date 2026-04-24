---
description: Print current TriageGuard sprint status — hours to deadline, what's built, what's missing, what ships next.
---

You are reporting TriageGuard's current state back to the builder.
Keep it ruthless and under 25 lines.

Do this:

1. Compute hours remaining to the deadline
   (`TRIAGEGUARD_DEADLINE` in `.claude/settings.json`, currently
   2026-04-26 20:00 EST).
2. Run these commands and summarize their output:
   - `git status --porcelain`
   - `git log --oneline -10`
   - `ls orchestrator agents 2>/dev/null`
   - `ls findings/ 2>/dev/null | tail -5`
   - `ls demo-inputs/ 2>/dev/null`
3. Check whether the six demo samples exist as files.
4. Check whether `WRITTEN_SUMMARY.md` exists and its word count.

Emit a report in this shape:

```
TriageGuard status — {hours}h to deadline

Built:
  - {component}: {one-line state}
  - ...

Missing (blocking submission):
  - {item}
  - ...

Next action (single smallest next step):
  → {action}
```

If "Missing" is empty, say so and list the three biggest remaining
polish items instead. Do NOT pad. Do NOT offer to do the work — just
report.
