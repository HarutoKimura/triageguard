---
description: Audit TriageGuard's CLAUDE.md, skills, and sub-agent prompts for conflicts, stale references, and over-constraints. Run at the start of each day and before any big recording.
---

Tariq (Session 1): **"Claude.md can conflict with skills... making
sure that Claude, if you give it conflicting information, tends to do
different things."**

This command runs the conflict audit.

## Steps

1. List every file in `.claude/skills/*/SKILL.md`, every file in
   `.claude/agents/*.md`, every file in `.claude/prompts/*.md`, the
   root `CLAUDE.md`, and `.claude/RULES.md`. Read each.
2. Check for **dead references**:
   - Any skill description that names a file or directory that does
     not exist in the repo.
   - Any prompt referencing a schema field not present in
     `.claude/skills/findings-journal/SKILL.md`.
   - Any command referring to a slash command that is not in
     `.claude/commands/`.
3. Check for **trigger overlap**:
   - Pairs of skills whose `description` frontmatter fires on the
     same phrases. Opus 4.7 will pick one, non-deterministically.
   - Report the pair and suggest which to narrow.
4. Check for **over-constraint**:
   - Any sub-agent prompt with more than ~60 lines of procedure.
     Tariq's rule: "a lot of instructions over-constrains Claude."
   - Flag; suggest which sections to trim.
5. Check for **contradictions**:
   - Any two rules in RULES.md, PROJECT_BRIEF.md, or CLAUDE.md that
     directly conflict (e.g. "never use asyncio.gather" vs. "run all
     four sub-agents via asyncio.gather").
6. Check for **stale dates**:
   - The deadline in `.claude/settings.json` vs. the deadline quoted
     in each file. They must match.

## Output

Respond with:

```
opus-audit — {N} findings

Dead references:
  - .claude/skills/foo/SKILL.md:12 mentions `orchestrator/main.py` —
    file not present.

Trigger overlap:
  - skills/wolfssl-domain and skills/agent-sdk-patterns both trigger
    on "sub-agent". Narrow one.

Over-constraint:
  - prompts/agent-a-reproducibility.md has 87 lines of procedure.
    Recommend trimming §procedure to 40 lines.

Contradictions:
  - (none)

Stale dates:
  - (none)
```

If the audit is clean, respond in one sentence and stop.

## Don't

- Do NOT edit any of the files in this command. Just report.
- Do NOT re-trigger the audit if the user hasn't changed anything
  since the last run; point at the last report instead.
