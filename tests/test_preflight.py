"""Unit tests for the Haiku 4.5 preflight summarizer.

The preflight is fail-open glue: it must (1) write its artifact in the
happy path, (2) record a stub in dry-run mode, and (3) swallow API
exceptions without raising. We test all three with a stub Anthropic
client so no live API calls happen.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from orchestrator.preflight import (
    PREFLIGHT_MODEL,
    PreflightResult,
    preflight_summarize,
)
from orchestrator.schemas import Expected, InputMeta, PoC, SignalLabel, Target


def _meta(sample_id: str = "s-test") -> InputMeta:
    return InputMeta(
        sample_id=sample_id,
        submitter="tester",
        target=Target(
            vendor="wolfssl",
            product="wolfssl",
            repo="https://github.com/wolfSSL/wolfssl",
            claimed_tag="v5.6.4-stable",
            claimed_cve=None,
        ),
        bug_class="memory-corruption",
        poc=PoC(present=True, path="poc", entry="poc/reproduce.sh"),
        submitted_at=datetime.now(UTC),
        expected=Expected(label=SignalLabel.SIGNAL, score_min=80, score_max=95),
    )


class _Block:
    def __init__(self, text: str) -> None:
        self.text = text


class _Usage:
    def __init__(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class _Response:
    def __init__(self, text: str, in_tok: int = 1200, out_tok: int = 80) -> None:
        self.content = [_Block(text)]
        self.usage = _Usage(in_tok, out_tok)


class _StubAnthropic:
    def __init__(self, response_text: str | None = None, raises: Exception | None = None) -> None:
        self._text = response_text
        self._raises = raises
        self.calls: list[dict[str, Any]] = []
        self.messages = self  # so .messages.create works

    async def create(self, **kwargs: Any) -> _Response:
        self.calls.append(kwargs)
        if self._raises is not None:
            raise self._raises
        assert self._text is not None
        return _Response(self._text)


def _write_input(tmp_path: Path, meta: InputMeta, body: str = "stack overflow in HPKE") -> Path:
    sample = tmp_path / "sample"
    sample.mkdir()
    (sample / "INPUT.md").write_text(body, encoding="utf-8")
    (sample / "INPUT_meta.json").write_text(meta.model_dump_json(), encoding="utf-8")
    return sample


@pytest.mark.asyncio
async def test_preflight_happy_path_writes_artifact(tmp_path: Path) -> None:
    meta = _meta()
    sample = _write_input(tmp_path, meta)
    findings = tmp_path / "findings"
    findings.mkdir()
    summary = (
        "- Claimed bug class: stack-buffer-overflow\n"
        "- Claimed location(s): src/wolfcrypt/hpke.c:492\n"
        "- Claimed evidence: PoC + ASan trace\n"
        "- One-line risk read: heap corruption reachable from network input"
    )
    stub = _StubAnthropic(response_text=summary)

    result = await preflight_summarize(
        sample_dir=sample,
        meta=meta,
        findings_dir=findings,
        dry_run=False,
        client=stub,  # type: ignore[arg-type]
    )

    assert isinstance(result, PreflightResult)
    assert result.summary_md == summary
    assert result.input_tokens == 1200
    assert result.output_tokens == 80
    assert result.cost_usd > 0

    artifact = json.loads((findings / "INPUT_summary.json").read_text())
    assert artifact["model"] == PREFLIGHT_MODEL
    assert artifact["summary_md"] == summary
    assert artifact["dry_run"] is False
    assert len(stub.calls) == 1
    assert stub.calls[0]["model"] == PREFLIGHT_MODEL


@pytest.mark.asyncio
async def test_preflight_dry_run_writes_stub_without_calling_api(tmp_path: Path) -> None:
    meta = _meta()
    sample = _write_input(tmp_path, meta)
    findings = tmp_path / "findings"
    findings.mkdir()
    stub = _StubAnthropic(response_text="should not be returned")

    result = await preflight_summarize(
        sample_dir=sample,
        meta=meta,
        findings_dir=findings,
        dry_run=True,
        client=stub,  # type: ignore[arg-type]
    )

    assert result is None
    assert len(stub.calls) == 0
    artifact = json.loads((findings / "INPUT_summary.json").read_text())
    assert artifact["dry_run"] is True
    assert artifact["cost_usd"] == 0.0


@pytest.mark.asyncio
async def test_preflight_swallows_api_exception(tmp_path: Path) -> None:
    meta = _meta()
    sample = _write_input(tmp_path, meta)
    findings = tmp_path / "findings"
    findings.mkdir()
    stub = _StubAnthropic(raises=RuntimeError("simulated 500"))

    result = await preflight_summarize(
        sample_dir=sample,
        meta=meta,
        findings_dir=findings,
        dry_run=False,
        client=stub,  # type: ignore[arg-type]
    )

    assert result is None
    err_log = findings / "errors_preflight.log"
    assert err_log.exists()
    assert "simulated 500" in err_log.read_text()
    # The artifact must NOT be written on failure.
    assert not (findings / "INPUT_summary.json").exists()
