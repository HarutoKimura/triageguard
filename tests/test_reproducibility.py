"""Offline smoke tests for Agent A wiring.

No live Claude Agent SDK calls. Exercises:
- system-prompt load
- custom tool handlers round-trip to ReproducibilityArtifact
- dry-run staging of a real sample into a findings directory
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from agents.reproducibility.agent import run_agent_a
from agents.reproducibility.prompt import PROMPT_PATH, load_system_prompt
from agents.reproducibility.tools import make_emit_verdict, make_think
from orchestrator.schemas import ReproducibilityArtifact

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_S1 = REPO_ROOT / "demo-inputs" / "s1-cve-2026-3849"


def test_prompt_loads() -> None:
    assert PROMPT_PATH.exists()
    text = load_system_prompt()
    assert "Agent A" in text or "Reproducibility" in text
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
    res = await t.handler({"content": "rules: I will verify build + PoC before verdict"})
    assert pad == ["rules: I will verify build + PoC before verdict"]
    assert res.get("is_error") is not True


async def test_emit_verdict_writes_schema_conformant_json(tmp_path: Path) -> None:
    t = make_emit_verdict(
        findings_dir=tmp_path, report_id="rep-42", started_at=datetime.now(UTC)
    )
    result = await t.handler(
        {
            "verdict": "reproduced",
            "confidence": 0.9,
            "evidence": {
                "target_tag": "v5.8.4-stable",
                "build_time_sec": 97.0,
                "build_exit_code": 0,
                "poc_exit_code": 1,
                "poc_signal": "ASAN",
                "sanitizer_summary": "stack-buffer-overflow in wc_HpkeLabeledExtract",
                "sanitizer_frames": [
                    "wc_HpkeLabeledExtract wolfcrypt/src/hpke.c:492",
                    "wc_HpkeKeyScheduleBase wolfcrypt/src/hpke.c:659",
                ],
            },
            "errors": [],
        }
    )
    assert result.get("is_error") is not True
    path = tmp_path / "A_reproducibility.json"
    assert path.exists()
    artifact = ReproducibilityArtifact.model_validate_json(path.read_text())
    assert artifact.verdict == "reproduced"
    assert artifact.confidence == pytest.approx(0.9)
    assert artifact.evidence.sanitizer_frames[0].startswith("wc_HpkeLabeledExtract")


async def test_emit_verdict_rejects_unknown_verdict(tmp_path: Path) -> None:
    t = make_emit_verdict(
        findings_dir=tmp_path, report_id="rep-x", started_at=datetime.now(UTC)
    )
    result = await t.handler({"verdict": "mostly_yes", "confidence": 0.8})
    assert result.get("is_error") is True
    assert not (tmp_path / "A_reproducibility.json").exists()


async def test_dry_run_stages_sample_into_findings(tmp_path: Path) -> None:
    if not SAMPLE_S1.exists():
        pytest.skip(f"sample {SAMPLE_S1} not present")
    result = await run_agent_a(
        sample_dir=SAMPLE_S1, findings_root=tmp_path, dry_run=True
    )
    assert result.dry_run is True
    assert result.artifact is None
    assert (result.findings_dir / "INPUT.md").exists()
    meta = json.loads((result.findings_dir / "INPUT_meta.json").read_text())
    assert meta["sample_id"] == "s1-cve-2026-3849"
    assert (result.findings_dir / "poc" / "reproduce.sh").exists()


async def test_dry_run_missing_sample_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        await run_agent_a(
            sample_dir=tmp_path / "nonexistent",
            findings_root=tmp_path,
            dry_run=True,
        )
