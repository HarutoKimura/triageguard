"""Custom in-process MCP tools for Agent C: `think` and `emit_verdict`.

Mirrors agents.root_cause.tools but emits a `DuplicateArtifact`
(novel / similar / duplicate). Payload is validated against the Pydantic
model before the file is written atomically.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from claude_agent_sdk import SdkMcpTool, tool
from pydantic import ValidationError

from orchestrator.findings import atomic_write_json
from orchestrator.schemas import DuplicateArtifact, DuplicateCandidate

THINK_SCHEMA: dict[str, type] = {"content": str}

EMIT_VERDICT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["verdict", "confidence"],
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["novel", "duplicate", "similar"],
        },
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "queried_databases": {
            "type": "array",
            "items": {"type": "string"},
        },
        "top_candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "title", "similarity", "verdict"],
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "similarity": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "verdict": {
                        "type": "string",
                        "enum": [
                            "different_class",
                            "related_but_distinct",
                            "likely_same",
                        ],
                    },
                },
                "additionalProperties": False,
            },
        },
        "matched_cve": {"type": ["string", "null"]},
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
            "(1) the candidate CVEs you considered, (2) why each was "
            "classified different_class / related_but_distinct / likely_same, "
            "(3) the decision rule that produced your final verdict. Content "
            "is recorded but does not affect the verdict."
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
    """Persist the final Duplicate Detector verdict. Call exactly once."""

    @tool(
        "emit_verdict",
        (
            "Write the final JSON verdict for Agent C (Duplicate Detector). "
            "Call this ONCE and exactly once at the end of your investigation. "
            "Schema: verdict is one of novel/duplicate/similar; confidence "
            "is 0.0-1.0; queried_databases is a list of DB names you "
            "queried; top_candidates is a list of "
            "{id, title, similarity, verdict} where verdict is "
            "different_class/related_but_distinct/likely_same; matched_cve "
            "is the CVE ID iff verdict=duplicate, otherwise null. "
            "After calling this, stop."
        ),
        EMIT_VERDICT_SCHEMA,
    )
    async def _emit(args: dict[str, Any]) -> dict[str, Any]:
        try:
            candidates_raw = args.get("top_candidates") or []
            artifact = DuplicateArtifact(
                report_id=report_id,
                verdict=args["verdict"],
                confidence=float(args["confidence"]),
                queried_databases=list(args.get("queried_databases", [])),
                top_candidates=[DuplicateCandidate(**c) for c in candidates_raw],
                matched_cve=args.get("matched_cve"),
                errors=list(args.get("errors", [])),
            )
        except (ValidationError, KeyError, TypeError, ValueError) as exc:
            return _text_result(f"verdict rejected: {exc}", is_error=True)

        _ = started_at
        path = findings_dir / "C_duplicate.json"
        atomic_write_json(path, artifact.model_dump(mode="json"))
        return _text_result(f"verdict written to {path}")

    return _emit
