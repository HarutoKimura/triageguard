"""Findings directory management — creation, atomic writes, name-flexible reads.

Canonical spec lives in `.claude/skills/findings-journal/SKILL.md`.

Two bitter lessons from cc-crossbeam are encoded here:

1. Sub-agents sometimes rename output files despite explicit prompts.
   Readers accept multiple candidate names.
2. A file may not be visible immediately after an agent claims done.
   Readers wait a few seconds before giving up.
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Accepted filenames per sub-agent. First-match wins.
CANDIDATES: dict[str, list[str]] = {
    "reproducibility": [
        "A_reproducibility.json",
        "reproducibility.json",
        "agent_a.json",
    ],
    "root_cause": [
        "B_root_cause.json",
        "root_cause.json",
        "agent_b.json",
    ],
    "duplicate": [
        "C_duplicate.json",
        "duplicate.json",
        "duplicate_detector.json",
        "agent_c.json",
    ],
    "hallucination": [
        "D_hallucination.json",
        "hallucination.json",
        "hallucination_detector.json",
        "agent_d.json",
    ],
}


def slugify(text: str) -> str:
    """Make a string safe for use as a directory name."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:80] or "unnamed"


def make_report_id(title: str) -> str:
    """Build `YYYY-MM-DDTHH-MM-SS-mmm_<slug>`; guaranteed filesystem-safe.

    Millisecond precision avoids collisions when two runs land in the same
    wall-clock second (typical during rehearsals and back-to-back demos).
    """
    now = datetime.now(UTC)
    ms = now.microsecond // 1000
    ts = now.strftime("%Y-%m-%dT%H-%M-%S") + f"-{ms:03d}"
    return f"{ts}_{slugify(title)}"


def prepare_findings_dir(root: Path, report_id: str, *, exist_ok: bool = False) -> Path:
    """Create `{root}/{report_id}/` and return it.

    `exist_ok` defaults to False so the single-agent CLI path still errors
    on accidental rerun with a collision-prone id. The orchestrator passes
    `exist_ok=True` so the two parallel sub-agents can share one directory.
    """
    path = root / report_id
    path.mkdir(parents=True, exist_ok=exist_ok)
    return path


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON via a temp file + rename so readers never see a half-written file."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, default=str))
    tmp.rename(path)


async def read_artifact_with_retry(
    findings_dir: Path, agent_key: str, *, attempts: int = 5, delay: float = 1.0
) -> dict[str, Any]:
    """Read a sub-agent artifact, accepting any candidate filename.

    Retries `attempts` times with `delay` seconds between attempts to
    absorb the flush race described in cc-crossbeam's learnings.
    """
    if agent_key not in CANDIDATES:
        raise ValueError(f"unknown agent key: {agent_key}")

    last_error: Exception | None = None
    for _ in range(attempts):
        for name in CANDIDATES[agent_key]:
            candidate = findings_dir / name
            if candidate.exists() and candidate.stat().st_size > 0:
                try:
                    parsed: dict[str, Any] = json.loads(candidate.read_text())
                    return parsed
                except json.JSONDecodeError as exc:
                    last_error = exc
        await asyncio.sleep(delay)

    raise FileNotFoundError(
        f"no artifact for {agent_key} in {findings_dir} "
        f"(tried {CANDIDATES[agent_key]}; last error: {last_error})"
    )
