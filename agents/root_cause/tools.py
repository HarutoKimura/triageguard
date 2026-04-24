"""Custom in-process MCP tools for Agent B: `think` and `emit_verdict`.

Mirrors agents.reproducibility.tools but emits a `RootCauseArtifact`
(match / partial_match / mismatch / file_not_found) instead of a
reproducibility verdict. The schema is enforced against the Pydantic
model before the file is persisted.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from claude_agent_sdk import SdkMcpTool, tool
from pydantic import ValidationError

from orchestrator.findings import atomic_write_json
from orchestrator.schemas import ClaimCheck, RootCauseArtifact

THINK_SCHEMA: dict[str, type] = {"content": str}

EMIT_VERDICT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["match", "confidence"],
    "properties": {
        "match": {
            "type": "string",
            "enum": ["match", "partial_match", "mismatch", "file_not_found"],
        },
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "claims_checked": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["claim", "status"],
                "properties": {
                    "claim": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["verified", "partially_verified", "not_verified"],
                    },
                    "file": {"type": ["string", "null"]},
                    "line_start": {"type": ["integer", "null"]},
                    "line_end": {"type": ["integer", "null"]},
                    "snippet": {"type": ["string", "null"]},
                    "note": {"type": ["string", "null"]},
                },
                "additionalProperties": False,
            },
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
            "(1) the claims you extracted, (2) the verification outcome per "
            "claim, (3) why you chose match/partial_match/mismatch/"
            "file_not_found. Content is recorded but does not affect the "
            "verdict."
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
    """Persist the final Root Cause verdict. Call exactly once."""

    @tool(
        "emit_verdict",
        (
            "Write the final JSON verdict for Agent B (Root Cause). Call "
            "this ONCE and exactly once at the end of your investigation. "
            "Schema: match is one of match/partial_match/mismatch/"
            "file_not_found; confidence is 0.0-1.0 (cap at 0.5 for "
            "file_not_found); claims_checked is a list of "
            "{claim, status, file?, line_start?, line_end?, snippet?, note?} "
            "where status is verified/partially_verified/not_verified. "
            "After calling this, stop."
        ),
        EMIT_VERDICT_SCHEMA,
    )
    async def _emit(args: dict[str, Any]) -> dict[str, Any]:
        try:
            claims_raw = args.get("claims_checked") or []
            artifact = RootCauseArtifact(
                report_id=report_id,
                match=args["match"],
                confidence=float(args["confidence"]),
                claims_checked=[ClaimCheck(**c) for c in claims_raw],
                errors=list(args.get("errors", [])),
            )
        except (ValidationError, KeyError, TypeError, ValueError) as exc:
            return _text_result(f"verdict rejected: {exc}", is_error=True)

        # `started_at` is stored in the orchestrator-side log, not in the
        # B_root_cause.json payload itself (schema does not carry timestamps).
        _ = started_at
        path = findings_dir / "B_root_cause.json"
        atomic_write_json(path, artifact.model_dump(mode="json"))
        return _text_result(f"verdict written to {path}")

    return _emit
