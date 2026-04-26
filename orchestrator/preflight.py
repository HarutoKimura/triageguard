"""Haiku 4.5 preflight: cheap, fast structured summary of the input.

Runs once per triage, before the four Opus 4.7 sub-agents fan out.
Reads `INPUT.md` + `INPUT_meta.json`, asks Haiku 4.5 for a 4-bullet
structured digest, and writes the result to
`findings/{report_id}/INPUT_summary.json`.

Why a separate model: the digest is mechanical (extract claimed bug
class, claimed file paths, claimed CVE, evidence type). Opus 4.7 is
overkill for this; Haiku 4.5 is ~50× cheaper and ~10× faster. The
sub-agents already re-read the raw input themselves — preflight is
purely informational, surfaced in the synthesizer narrative and the
CLI output as a sanity check.

Fail-open by design: a Haiku error is logged but never blocks the
sub-agents. This is glue, not judgment.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from anthropic import AsyncAnthropic

from orchestrator.findings import atomic_write_json
from orchestrator.schemas import InputMeta

PREFLIGHT_MODEL = os.environ.get(
    "TRIAGEGUARD_PREFLIGHT_MODEL", "claude-haiku-4-5-20251001"
)
PREFLIGHT_MAX_TOKENS = int(os.environ.get("TRIAGEGUARD_PREFLIGHT_MAX_TOKENS", "400"))

HAIKU_INPUT_USD_PER_MTOK = 1.0
HAIKU_OUTPUT_USD_PER_MTOK = 5.0

SYSTEM_PROMPT = (
    "You are TriageGuard's preflight summarizer. The downstream four "
    "Opus 4.7 sub-agents will re-read the raw report; your job is "
    "purely a fast structured digest for the human reviewer.\n\n"
    "Return EXACTLY four bullet lines, each starting with `- `, in this "
    "fixed order:\n"
    "- Claimed bug class: <one phrase>\n"
    "- Claimed location(s): <file:line or function name, comma-separated>\n"
    "- Claimed evidence: <PoC / advisory text / static analysis / none>\n"
    "- One-line risk read: <under 20 words>\n\n"
    "If any field is unclear from the report, write `unknown` for that "
    "bullet. Do not invent or speculate. No prose before or after."
)


@dataclass
class PreflightResult:
    summary_md: str
    cost_usd: float
    wallclock_sec: float
    input_tokens: int
    output_tokens: int


def _estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens * HAIKU_INPUT_USD_PER_MTOK / 1_000_000
        + output_tokens * HAIKU_OUTPUT_USD_PER_MTOK / 1_000_000
    )


def _build_user_payload(input_md: str, meta: InputMeta) -> str:
    meta_view = {
        "sample_id": meta.sample_id,
        "target": meta.target.model_dump(mode="json"),
        "bug_class": meta.bug_class,
        "poc_present": meta.poc.present,
    }
    return (
        "INPUT_meta.json:\n```json\n"
        + json.dumps(meta_view, indent=2)
        + "\n```\n\n"
        + "INPUT.md:\n```\n"
        + (input_md[:6000] if len(input_md) > 6000 else input_md)
        + "\n```"
    )


async def preflight_summarize(
    *,
    sample_dir: Path,
    meta: InputMeta,
    findings_dir: Path,
    dry_run: bool = False,
    client: AsyncAnthropic | None = None,
) -> PreflightResult | None:
    """Run the Haiku 4.5 digest. Returns None on dry-run or failure.

    On success, writes `INPUT_summary.json` to `findings_dir` and
    returns the PreflightResult. On any exception, writes
    `errors_preflight.log` and returns None — never raises.
    """
    if dry_run:
        artifact = {
            "model": PREFLIGHT_MODEL,
            "summary_md": "(dry-run — Haiku 4.5 not called)",
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "wallclock_sec": 0.0,
            "generated_at": datetime.now(UTC).isoformat(),
            "dry_run": True,
        }
        atomic_write_json(findings_dir / "INPUT_summary.json", artifact)
        return None

    input_md_path = sample_dir / "INPUT.md"
    input_md = (
        input_md_path.read_text(encoding="utf-8") if input_md_path.exists() else ""
    )

    api = client or AsyncAnthropic()
    user = _build_user_payload(input_md, meta)

    t0 = time.monotonic()
    try:
        response = await api.messages.create(
            model=PREFLIGHT_MODEL,
            max_tokens=PREFLIGHT_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user}],
        )
    except Exception as exc:
        wall = time.monotonic() - t0
        (findings_dir / "errors_preflight.log").write_text(
            f"{type(exc).__name__}: {exc}\n  wallclock={wall:.2f}s\n",
            encoding="utf-8",
        )
        return None
    wall = time.monotonic() - t0

    # Duck-type the text blocks so a stubbed SDK in tests works without
    # constructing real `TextBlock` Pydantic models.
    text_parts: list[str] = []
    for block in response.content:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            text_parts.append(text)
    summary = "\n".join(p.strip() for p in text_parts if p.strip()).strip()
    if not summary:
        (findings_dir / "errors_preflight.log").write_text(
            "Haiku 4.5 returned no text content\n", encoding="utf-8"
        )
        return None

    usage = response.usage
    input_tokens = int(getattr(usage, "input_tokens", 0))
    output_tokens = int(getattr(usage, "output_tokens", 0))
    cost_usd = _estimate_cost_usd(input_tokens, output_tokens)

    artifact = {
        "model": PREFLIGHT_MODEL,
        "summary_md": summary,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost_usd, 6),
        "wallclock_sec": round(wall, 3),
        "generated_at": datetime.now(UTC).isoformat(),
        "dry_run": False,
    }
    atomic_write_json(findings_dir / "INPUT_summary.json", artifact)

    return PreflightResult(
        summary_md=summary,
        cost_usd=cost_usd,
        wallclock_sec=wall,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
