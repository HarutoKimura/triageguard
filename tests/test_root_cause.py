"""Offline smoke tests for Agent B wiring.

No live Claude Agent SDK calls, no git clone (skipped via
`skip_source_clone=True`). Exercises:
- system-prompt load
- custom tool handlers round-trip to RootCauseArtifact
- dry-run staging of a real sample into a findings directory
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from agents.root_cause.agent import run_agent_b
from agents.root_cause.prompt import PROMPT_PATH, load_system_prompt
from agents.root_cause.tools import make_emit_verdict, make_think
from orchestrator.schemas import RootCauseArtifact

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_S1 = REPO_ROOT / "demo-inputs" / "s1-cve-2026-3849"


def test_prompt_loads() -> None:
    assert PROMPT_PATH.exists()
    text = load_system_prompt()
    assert "Agent B" in text or "Root Cause" in text
    assert "emit_verdict" in text


def test_make_think_returns_tool() -> None:
    pad: list[str] = []
    t = make_think(pad)
    assert t.name == "think"
    assert "scratchpad" in t.description.lower()


def test_make_emit_verdict_returns_tool(tmp_path: Path) -> None:
    t = make_emit_verdict(
        findings_dir=tmp_path, report_id="rep-1", started_at=datetime.now(UTC)
    )
    assert t.name == "emit_verdict"
    assert isinstance(t.input_schema, dict)


async def test_think_handler_appends_scratchpad() -> None:
    pad: list[str] = []
    t = make_think(pad)
    res = await t.handler({"content": "claim: wc_HpkeLabeledExtract at hpke.c:492"})
    assert pad == ["claim: wc_HpkeLabeledExtract at hpke.c:492"]
    assert res.get("is_error") is not True


async def test_emit_verdict_writes_schema_conformant_json(tmp_path: Path) -> None:
    t = make_emit_verdict(
        findings_dir=tmp_path, report_id="rep-42", started_at=datetime.now(UTC)
    )
    result = await t.handler(
        {
            "match": "match",
            "confidence": 0.88,
            "claims_checked": [
                {
                    "claim": "wc_HpkeLabeledExtract exists in wolfcrypt/src/hpke.c",
                    "status": "verified",
                    "file": "wolfcrypt/src/hpke.c",
                    "line_start": 461,
                    "line_end": 503,
                    "snippet": "int wc_HpkeLabeledExtract(Hpke* hpke, ...) { ... }",
                },
                {
                    "claim": "rawLen set without upper bound in SetEchConfigsEx",
                    "status": "verified",
                    "file": "src/ssl_ech.c",
                    "line_start": 571,
                    "line_end": 571,
                    "snippet": "workingConfig->rawLen = length + 4;",
                },
            ],
            "errors": [],
        }
    )
    assert result.get("is_error") is not True
    path = tmp_path / "B_root_cause.json"
    assert path.exists()
    artifact = RootCauseArtifact.model_validate_json(path.read_text())
    assert artifact.match == "match"
    assert artifact.confidence == pytest.approx(0.88)
    assert len(artifact.claims_checked) == 2
    assert artifact.claims_checked[0].file == "wolfcrypt/src/hpke.c"


async def test_emit_verdict_rejects_unknown_match_value(tmp_path: Path) -> None:
    t = make_emit_verdict(
        findings_dir=tmp_path, report_id="rep-x", started_at=datetime.now(UTC)
    )
    result = await t.handler({"match": "sort_of", "confidence": 0.8})
    assert result.get("is_error") is True
    assert not (tmp_path / "B_root_cause.json").exists()


async def test_dry_run_stages_sample_without_clone(tmp_path: Path) -> None:
    if not SAMPLE_S1.exists():
        pytest.skip(f"sample {SAMPLE_S1} not present")
    result = await run_agent_b(
        sample_dir=SAMPLE_S1,
        findings_root=tmp_path,
        dry_run=True,
        skip_source_clone=True,
    )
    assert result.dry_run is True
    assert result.artifact is None
    assert (result.findings_dir / "INPUT.md").exists()
    meta = json.loads((result.findings_dir / "INPUT_meta.json").read_text())
    assert meta["sample_id"] == "s1-cve-2026-3849"
    assert not (result.findings_dir / "source").exists()  # skip_source_clone


async def test_dry_run_missing_sample_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        await run_agent_b(
            sample_dir=tmp_path / "nonexistent",
            findings_root=tmp_path,
            dry_run=True,
            skip_source_clone=True,
        )
