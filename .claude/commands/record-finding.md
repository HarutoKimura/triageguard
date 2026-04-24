---
description: Record a new vulnerability report as a TriageGuard input sample, enforcing the INPUT schema so sub-agents have everything they need.
argument-hint: [sample-id]
---

A new vulnerability report is being added to TriageGuard's input set.
Ensure it lands in `demo-inputs/{sample-id}/` with the canonical shape:

```
demo-inputs/{sample-id}/
  INPUT.md          # the report body as-provided, no edits
  INPUT_meta.json   # structured metadata
  poc/              # optional — PoC code, inputs, shell scripts
  artifacts/        # optional — screenshots, crash dumps
```

## Steps

1. Ask the user which sample id to use (e.g. `s1-cve-2026-2646`,
   `s4-curl-slop-1`, `s6-live-slop`). If `$ARGUMENTS` is set, use it;
   otherwise ask.
2. Ask for the report body. Accept paste or a path. Write to
   `INPUT.md` verbatim — no reformatting, no summarization.
3. Generate `INPUT_meta.json` with this schema and fill it in from
   the report body, asking the user for anything ambiguous:
   ```json
   {
     "sample_id": "s1-cve-2026-2646",
     "submitter": "anonymous | <name>",
     "target": {
       "vendor": "wolfSSL",
       "product": "wolfssl",
       "repo": "https://github.com/wolfSSL/wolfssl",
       "claimed_tag": "v5.6.4-stable",
       "claimed_cve": "CVE-2026-2646"
     },
     "bug_class": "heap_overflow | use_after_free | signature_bypass | ...",
     "poc": {
       "present": true,
       "path": "demo-inputs/s1-cve-2026-2646/poc/",
       "entry": "poc/run.sh"
     },
     "submitted_at": "2026-04-24T00:00:00Z",
     "expected": {
       "label": "SIGNAL | UNCERTAIN | SLOP",
       "score_min": 80,
       "score_max": 95,
       "triggering_rule_hint": 5
     }
   }
   ```
4. If a PoC is included, copy it into `poc/` and note it in
   `INPUT_meta.json`.
5. Validate the directory:
   - `INPUT.md` non-empty
   - `INPUT_meta.json` parses as JSON
   - `target.claimed_tag` reachable at the target repo
     (`git ls-remote --tags <repo> | grep <tag>`)
6. Print a summary:
   ```
   Recorded {sample_id}: expected {label} {score_min}–{score_max}.
   ```

## Do not

- Do not edit the report body to "clean it up." The submitter's
  prose is the input; altering it defeats the test.
- Do not guess `expected.label` when the user hasn't said. Ask.
- Do not overwrite an existing sample directory without an explicit
  `--force` in the arguments.
