"""Custom in-process MCP tools for Agent D: `think` and `emit_verdict`.

Mirrors agents.duplicate.tools but emits a `HallucinationArtifact`.
Payload is validated against the Pydantic model before the file is
written atomically. The stats block is derived from `extracted_claims`
if the model omits it.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from claude_agent_sdk import SdkMcpTool, tool
from pydantic import ValidationError

from orchestrator.findings import atomic_write_json
from orchestrator.schemas import (
    ExtractedClaim,
    HallucinationArtifact,
    HallucinationStats,
    InvalidRef,
)

THINK_SCHEMA: dict[str, type] = {"content": str}

_REF_KINDS = [
    "function",
    "file",
    "line",
    "symbol",
    "cve",
    "cvss_vector",
    "tag",
    "option",
]
_REF_STATUSES = ["verified", "invalid", "unchecked"]

EMIT_VERDICT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["extracted_claims"],
    "properties": {
        "extracted_claims": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["kind", "value", "status"],
                "properties": {
                    "kind": {"type": "string", "enum": _REF_KINDS},
                    "value": {"type": "string"},
                    "status": {"type": "string", "enum": _REF_STATUSES},
                    "source": {"type": ["string", "null"]},
                    "note": {"type": ["string", "null"]},
                },
                "additionalProperties": False,
            },
        },
        "invalid_refs": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["kind", "value"],
                "properties": {
                    "kind": {"type": "string", "enum": _REF_KINDS},
                    "value": {"type": "string"},
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
            "(1) every reference you extracted, (2) how you verified each "
            "one, (3) which were invalid and why. Content is recorded but "
            "does not affect the verdict."
        ),
        THINK_SCHEMA,
    )
    async def _think(args: dict[str, Any]) -> dict[str, Any]:
        scratchpad.append(str(args.get("content", "")))
        return _text_result("noted")

    return _think


def _derive_stats(claims: list[ExtractedClaim]) -> HallucinationStats:
    counts = Counter(c.status for c in claims)
    return HallucinationStats(
        total=len(claims),
        verified=counts.get("verified", 0),
        invalid=counts.get("invalid", 0),
        unchecked=counts.get("unchecked", 0),
    )


def make_emit_verdict(
    *, findings_dir: Path, report_id: str, started_at: datetime
) -> SdkMcpTool[Any]:
    """Persist the final Hallucination Detector verdict. Call exactly once."""

    @tool(
        "emit_verdict",
        (
            "Write the final JSON verdict for Agent D (Hallucination Detector). "
            "Call this ONCE and exactly once at the end of your investigation. "
            "Schema: extracted_claims is a list of "
            "{kind, value, status, source?, note?} where kind is one of "
            f"{'/'.join(_REF_KINDS)} and status is one of "
            f"{'/'.join(_REF_STATUSES)}. Provide invalid_refs only if you "
            "want to override the auto-derived list (otherwise it will be "
            "built from the status=invalid rows). After calling this, stop."
        ),
        EMIT_VERDICT_SCHEMA,
    )
    async def _emit(args: dict[str, Any]) -> dict[str, Any]:
        try:
            claims_raw = args.get("extracted_claims") or []
            claims = [ExtractedClaim(**c) for c in claims_raw]
            # Default: derive invalid_refs from the claims with status=invalid.
            if "invalid_refs" in args:
                invalid = [InvalidRef(**r) for r in args["invalid_refs"]]
            else:
                invalid = [
                    InvalidRef(kind=c.kind, value=c.value, note=c.note)
                    for c in claims
                    if c.status == "invalid"
                ]
            artifact = HallucinationArtifact(
                report_id=report_id,
                extracted_claims=claims,
                invalid_refs=invalid,
                stats=_derive_stats(claims),
                errors=list(args.get("errors", [])),
            )
        except (ValidationError, KeyError, TypeError, ValueError) as exc:
            return _text_result(f"verdict rejected: {exc}", is_error=True)

        _ = started_at
        path = findings_dir / "D_hallucination.json"
        atomic_write_json(path, artifact.model_dump(mode="json"))
        return _text_result(f"verdict written to {path}")

    return _emit
