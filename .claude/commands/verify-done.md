---
description: Verify that a task is actually done before claiming so — build, test, output shape, and honesty checks. Run before every commit of consequence.
---

PROJECT_BRIEF.md §Operating principles rule 1: "Verify before claiming
done. If a build succeeds, rerun it. If a test passes, print the
output. Do not mark a task complete on plausibility."

This command runs that rule.

## Steps

Prompt the user: "What was just 'completed'? Paste the task
description or the last commit message."

Then run these checks, in order, stopping at the first failure:

1. **Build**: run `docker build` on any changed Dockerfiles. If
   `pyproject.toml` changed, run `uv sync` or `pip install -e .`.
   Print the exit code.
2. **Static checks**: run whatever linter/type-checker exists
   (`ruff check`, `mypy`, `tsc --noEmit`). Print the exit code.
3. **Tests**: run the smallest relevant test.
   - If the change touched `orchestrator/`: run
     `pytest tests/test_orchestrator.py`.
   - If the change touched `agents/`: run the sub-agent against
     sample 1 (expect SIGNAL 80–90) and sample 4 (expect SLOP <25).
   - If the change touched `frontend/`: run
     `npm run build && npm run typecheck`.
4. **Schema check**: if the change produced or consumed artifacts
   under `findings/`, validate one sample artifact against the
   schemas in `.claude/skills/findings-journal/SKILL.md`.
5. **Honesty check**: grep the diff for fallback/placeholder strings
   ("TODO", "FIXME", "placeholder", "mock", "stub"). Report any hits.
   If present, ask the user: "are these intentional?" Do NOT remove
   them yourself.
6. **No-regression check**: run `pytest -q` over the whole suite if
   it exists and is fast (< 60 s). Otherwise skip.

## Output

Print a checklist like:

```
verify-done for: "{task description}"
  ✓ build          (exit 0, 12 s)
  ✓ lint           (ruff clean)
  ✓ tests          (3 passed)
  ✓ schema         (1 artifact validated)
  ⚠ honesty        (2 TODO in orchestrator/main.py:45, :112)
  ✓ no-regression  (41 passed)

STATUS: passes with honesty warning. Acceptable to commit if TODOs
are tracked.
```

## Don't

- Do NOT mark `STATUS: OK` if any step failed.
- Do NOT "fix" surfaced failures inside this command — report them
  and exit.
- Do NOT skip a step without saying "skipped because <reason>" and
  explicitly.
