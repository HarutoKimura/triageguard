---
name: findings-journal
description: JSON schemas and file-layout conventions for the per-run findings directory (`findings/{report_id}/`) — the single source of truth passed between the four sub-agents and the synthesizer. Use when writing agent outputs, designing the synthesizer, streaming SSE events, or debugging missing handoffs between agents.
---

# Findings Journal

The findings directory is TriageGuard's scratchpad. The orchestrator
creates it, each sub-agent writes one artifact, the synthesizer reads
all five. Nothing flows through Python in-memory state across agents —
everything is on disk.

Rationale: cc-crossbeam's biggest learning was "file-based handoff
beats passing transcripts through the lead agent's context." Anthropic's
multi-agent research post: *"the detailed search context remains
isolated within sub-agents."*

---

## 1 · Directory layout

```
findings/
└── {report_id}/                     # e.g. 2026-04-24T15-32-08_cve-2026-2646
    ├── INPUT.md                     # original report as submitted
    ├── INPUT_meta.json              # { target_repo, claimed_tag, poc_path, ... }
    ├── A_reproducibility.json       # Agent A output
    ├── A_build_log.tail.txt         # last 200 lines of the build for UI display
    ├── A_poc_log.tail.txt           # PoC run output (ASan, gdb, etc.)
    ├── B_root_cause.json            # Agent B output
    ├── C_duplicate.json             # Agent C output
    ├── D_hallucination.json         # Agent D output
    ├── SYNTHESIS.md                 # human-readable verdict (synthesizer)
    └── SIGNAL_SCORE.json            # { score, label, reason, agent_deltas }
```

**`report_id` format**: `{ISO_UTC_timestamp_colonless}_{slugified_title}`.
Timestamp prefix guarantees uniqueness and gives natural ordering.

**Single directory per run, never in-place rewrites.** Re-running a
report creates a new dir. Old dirs feed the UI's history panel.

---

## 2 · Schema — Agent A (Reproducibility)

```json
{
  "agent": "reproducibility",
  "report_id": "2026-04-24T15-32-08_cve-2026-2646",
  "verdict": "reproduced",
  "confidence": 0.9,
  "evidence": {
    "target_tag": "v5.6.4-stable",
    "build_time_sec": 97,
    "build_exit_code": 0,
    "poc_exit_code": 139,
    "poc_signal": "SIGSEGV",
    "sanitizer_summary": "AddressSanitizer: heap-buffer-overflow ...",
    "sanitizer_frames": [
      "wolfSSL_d2i_SSL_SESSION in src/ssl.c:13421",
      "XMEMCPY in src/memory.c:502"
    ]
  },
  "log_files": {
    "build": "A_build_log.tail.txt",
    "poc": "A_poc_log.tail.txt"
  },
  "timestamps": {
    "started_at": "2026-04-24T15:32:15Z",
    "finished_at": "2026-04-24T15:39:04Z"
  },
  "errors": []
}
```

**Allowed `verdict` values**:
- `reproduced` — claimed behavior observed
- `failed_to_reproduce` — built but behavior not observed
- `no_poc` — report did not include a PoC
- `build_error` — could not build the claimed tag
- `timeout` — PoC did not finish within the 10-minute cap

`confidence` is 0.0–1.0 and must reflect real uncertainty. An agent
that hit a timeout does not get confidence 0.9.

---

## 3 · Schema — Agent B (Root Cause)

```json
{
  "agent": "root_cause",
  "report_id": "2026-04-24T15-32-08_cve-2026-2646",
  "match": "match",
  "confidence": 0.85,
  "claims_checked": [
    {
      "claim": "Vulnerability is in wolfSSL_d2i_SSL_SESSION",
      "status": "verified",
      "file": "src/ssl.c",
      "line_start": 13398,
      "line_end": 13445,
      "snippet": "int wolfSSL_d2i_SSL_SESSION(...) { ... }"
    },
    {
      "claim": "Memory copy is unchecked at offset 0x80",
      "status": "partially_verified",
      "file": "src/ssl.c",
      "line_start": 13420,
      "line_end": 13422,
      "snippet": "XMEMCPY(ssn->masterSecret, data + idx, ...);",
      "note": "XMEMCPY is present; length check presence is ambiguous"
    }
  ],
  "errors": []
}
```

**Allowed `match` values**:
- `match` — all primary claims verified in source
- `partial_match` — some claims verified, some not
- `mismatch` — primary claims contradicted by source
- `file_not_found` — claimed file does not exist at the claimed tag

---

## 4 · Schema — Agent C (Duplicate Detector)

```json
{
  "agent": "duplicate_detector",
  "report_id": "2026-04-24T15-32-08_cve-2026-2646",
  "verdict": "novel",
  "confidence": 0.8,
  "queried_databases": ["NVD", "GHSA", "wolfssl-advisories"],
  "top_candidates": [
    {
      "id": "CVE-2023-3724",
      "title": "wolfSSL TLS 1.3 pre-shared key confusion",
      "similarity": 0.34,
      "verdict": "different_class"
    },
    {
      "id": "CVE-2024-14031",
      "title": "wolfSSL session cache integer overflow",
      "similarity": 0.58,
      "verdict": "related_but_distinct"
    }
  ],
  "matched_cve": null,
  "errors": []
}
```

**Allowed `verdict` values**: `novel`, `duplicate`, `similar`.

`matched_cve` is non-null only if `verdict == "duplicate"`. A `similar`
verdict flags partial overlap but a distinct bug.

---

## 5 · Schema — Agent D (Hallucination Detector)

```json
{
  "agent": "hallucination_detector",
  "report_id": "2026-04-24T15-32-08_cve-2026-2646",
  "extracted_claims": [
    {
      "kind": "function", "value": "wolfSSL_d2i_SSL_SESSION",
      "status": "verified", "source": "src/ssl.c:13398"
    },
    {
      "kind": "file", "value": "src/ssl.c",
      "status": "verified", "source": "git show v5.6.4-stable:src/ssl.c"
    },
    {
      "kind": "cve", "value": "CVE-2025-99999",
      "status": "invalid",
      "note": "Not present in NVD"
    }
  ],
  "invalid_refs": [
    {
      "kind": "cve", "value": "CVE-2025-99999",
      "note": "Not present in NVD"
    }
  ],
  "stats": {
    "total": 6,
    "verified": 5,
    "invalid": 1,
    "unchecked": 0
  },
  "errors": []
}
```

**`kind` taxonomy**: `function`, `file`, `line`, `symbol`, `cve`,
`cvss_vector`, `tag`, `option`.

**`status` values**: `verified`, `invalid`, `unchecked` (skipped due to
time budget, but time budget should allow every claim — flag to
orchestrator if unchecked > 0).

---

## 6 · Schema — SIGNAL_SCORE.json (synthesizer output)

```json
{
  "report_id": "2026-04-24T15-32-08_cve-2026-2646",
  "score": 87,
  "label": "SIGNAL",
  "recommendation": "ACCEPT",
  "reason": "Reproduced, matches code, novel, no fabrications",
  "triggering_rule": 5,
  "sub_agent_deltas": {
    "reproducibility": "+40",
    "root_cause": "+25",
    "duplicate": "+15",
    "hallucination": "+7"
  },
  "sub_agent_verdicts": {
    "reproducibility": "reproduced",
    "root_cause": "match",
    "duplicate": "novel",
    "hallucination_invalid_count": 0
  },
  "generated_at": "2026-04-24T15:41:22Z",
  "total_runtime_sec": 548,
  "total_cost_usd": 4.12
}
```

`sub_agent_deltas` are illustrative only (the rubric is rule-based, not
additive). They exist so the UI can animate a progress bar as agents
finish.

---

## 7 · Write conventions

1. **Write via a temp file + rename** so the UI never reads a half-written
   JSON:
   ```python
   tmp = path.with_suffix(".json.tmp")
   tmp.write_text(json.dumps(payload, indent=2))
   tmp.rename(path)
   ```
2. **Always include `errors: []`** — empty list is meaningful signal.
3. **UTC timestamps only**, suffixed with `Z`.
4. **Never include the full build log** — tail to the last ~200 lines
   into the `*_log.tail.txt` sidecar. Synthesizer does not read these.
5. **Pretty-print with `indent=2`**. The files are human-read during
   demo debugging.

---

## 8 · Read conventions

The synthesizer and UI are the only legitimate readers.

- **Name-flexibility on read** (cc-crossbeam learning):
  ```python
  CANDIDATES = ["A_reproducibility.json",
                "agent_a.json",
                "reproducibility.json"]
  ```
- **Flush wait**: after an agent claims done, sleep 2 seconds before
  reading. Files may not be visible yet (crossbeam's race).
- **Schema validation on every read**. Reject a run if any of the five
  files is missing or malformed. Mark the run `errored`, do not
  fabricate a score.

---

## 9 · SSE events emitted as files land

The UI subscribes to `/events/{report_id}`. The orchestrator emits one
event per file arrival:

```
event: agent_done
data: {"agent":"reproducibility","verdict":"reproduced","delta":"+40"}

event: agent_done
data: {"agent":"root_cause","verdict":"match","delta":"+25"}

event: synthesis_ready
data: {"score":87,"label":"SIGNAL","reason":"..."}
```

The UI animates the Signal Score bar from 0 upward as deltas arrive.
This is the moment the demo video sells the product.
