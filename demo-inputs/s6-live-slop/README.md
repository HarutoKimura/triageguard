# s6-live-slop — regenerate before every demo take

This directory is a **regeneration slot** for the live-demo slop
moment. Unlike s1–s5, the files here are not frozen — they are
overwritten each time the slop generator runs.

## Regenerate

```bash
.venv/bin/python scripts/generate_slop.py \
    --output-dir demo-inputs/s6-live-slop \
    --variation rce
```

Omit `--seed` to get fresh slop per take. Set `OAI_MODEL` in `.env` or
pass `--model` to swap to the strongest model available on demo day
(e.g. `gpt-5.4` or whatever OpenAI ships next). The stronger the
model, the more confident-looking the hallucinations — which makes for
better demo narrative.

## Run immediately after generation

```bash
.venv/bin/python -m orchestrator demo-inputs/s6-live-slop/
```

Expected outcome: SLOP label, score 10–25, rule 2 or rule 4 fires
because Agent D catches fabricated function/file references.

## Gitignore status

`INPUT.md` and `INPUT_meta.json` in this directory are committed as
last-known-good reference files (so dry-runs and CI can validate the
slot schema), but they are OVERWRITTEN by every generator run.
Regenerate before recording the demo.
