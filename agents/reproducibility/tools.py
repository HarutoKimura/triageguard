"""Custom in-process MCP tools for Agent A: `think` and `emit_verdict`.

Both are factories — they close over the per-run `findings_dir` and
`report_id` so the model can't pass a wrong path. The returned
`SdkMcpTool` objects are registered under an in-process MCP server
(name: `agent_a`) via `create_sdk_mcp_server`.

`emit_verdict` validates its payload against
`orchestrator.schemas.ReproducibilityArtifact` before persisting; a
malformed call surfaces as a tool-result error rather than silently
producing a bad JSON file.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from claude_agent_sdk import SdkMcpTool, tool
from pydantic import ValidationError

from orchestrator.findings import atomic_write_json
from orchestrator.schemas import ReproducibilityArtifact, ReproEvidence

THINK_SCHEMA: dict[str, type] = {"content": str}

EMIT_VERDICT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["verdict", "confidence"],
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["reproduced", "failed_to_reproduce", "no_poc", "build_error", "timeout"],
        },
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "evidence": {
            "type": "object",
            "properties": {
                "target_tag": {"type": ["string", "null"]},
                "build_time_sec": {"type": ["number", "null"]},
                "build_exit_code": {"type": ["integer", "null"]},
                "poc_exit_code": {"type": ["integer", "null"]},
                "poc_signal": {"type": ["string", "null"]},
                "sanitizer_summary": {"type": ["string", "null"]},
                "sanitizer_frames": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": False,
        },
        "log_files": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
        "errors": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
}


def _text_result(text: str, *, is_error: bool = False) -> dict[str, Any]:
    block: dict[str, Any] = {"content": [{"type": "text", "text": text}]}
    if is_error:
        block["is_error"] = True
    return block


def make_think(scratchpad: list[str]) -> SdkMcpTool[Any]:
    """A no-op scratchpad. Append-only; content is surfaced in logs post-run."""

    @tool(
        "think",
        (
            "Free-form scratchpad. Use before calling emit_verdict to list "
            "(1) the rules you applied, (2) the evidence you collected, "
            "(3) any remaining uncertainty. Content is recorded but does "
            "not affect the verdict."
        ),
        THINK_SCHEMA,
    )
    async def _think(args: dict[str, Any]) -> dict[str, Any]:
        scratchpad.append(str(args.get("content", "")))
        return _text_result("noted")

    return _think


def make_emit_verdict(
    *, findings_dir: Path, report_id: str, started_at: datetime
) -> SdkMcpTool[Any]:
    """Persist the final Reproducibility verdict. Call exactly once."""

    @tool(
        "emit_verdict",
        (
            "Write the final JSON verdict for Agent A (Reproducibility). "
            "Call this ONCE and exactly once at the end of your investigation. "
            "Schema: verdict is one of reproduced/failed_to_reproduce/no_poc/"
            "build_error/timeout; confidence is 0.0-1.0 and must reflect real "
            "uncertainty (cap at 0.5 for build_error or timeout); evidence is "
            "an object with optional target_tag, build_time_sec, build_exit_code, "
            "poc_exit_code, poc_signal, sanitizer_summary, sanitizer_frames. "
            "After calling this, stop."
        ),
        EMIT_VERDICT_SCHEMA,
    )
    async def _emit(args: dict[str, Any]) -> dict[str, Any]:
        try:
            evidence_raw = args.get("evidence") or {}
            artifact = ReproducibilityArtifact(
                report_id=report_id,
                verdict=args["verdict"],
                confidence=float(args["confidence"]),
                evidence=ReproEvidence(**evidence_raw),
                log_files=args.get("log_files", {}),
                timestamps={
                    "started_at": started_at,
                    "finished_at": datetime.now(UTC),
                },
                errors=list(args.get("errors", [])),
            )
        except (ValidationError, KeyError, TypeError, ValueError) as exc:
            return _text_result(f"verdict rejected: {exc}", is_error=True)

        path = findings_dir / "A_reproducibility.json"
        atomic_write_json(path, artifact.model_dump(mode="json"))
        return _text_result(f"verdict written to {path}")

    return _emit
