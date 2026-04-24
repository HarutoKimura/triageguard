"""Post-synthesis narrative via one Opus 4.7 call.

The deterministic synthesizer picks the rule and score
(`orchestrator/synthesizer.py`). This module adds a human-readable
2-3 paragraph explanation, grounded in the four agents' JSON
artifacts, so a maintainer can accept/reject the verdict in under a
minute.

Single-shot, no tools, no retrieval. System prompt lives in
`.claude/prompts/synthesizer-reasoning.md`. Extended thinking is
enabled to honor the "Opus 4.7 at xhigh for the synthesizer" pitch.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from anthropic import AsyncAnthropic
from anthropic.types import OutputConfigParam, TextBlock, ThinkingConfigAdaptiveParam

from orchestrator.schemas import (
    DuplicateArtifact,
    HallucinationArtifact,
    InputMeta,
    ReproducibilityArtifact,
    RootCauseArtifact,
    SignalScore,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = REPO_ROOT / ".claude" / "prompts" / "synthesizer-reasoning.md"

# Canonical model IDs live in CLAUDE.md. Env var lets us swap for
# debug/budget runs without touching code.
REASONING_MODEL = os.environ.get("TRIAGEGUARD_REASONING_MODEL", "claude-opus-4-7")
# Opus 4.7 only accepts "low" | "medium" | "high" | "xhigh" | "max". The
# pitch says "Opus 4.7 at xhigh for sub-agents + synthesizer" — honor it.
EffortLevel = Literal["low", "medium", "high", "xhigh", "max"]
_RAW_EFFORT = os.environ.get("TRIAGEGUARD_REASONING_EFFORT", "xhigh")
_ALLOWED_EFFORTS: tuple[EffortLevel, ...] = ("low", "medium", "high", "xhigh", "max")
if _RAW_EFFORT not in _ALLOWED_EFFORTS:
    raise ValueError(
        f"TRIAGEGUARD_REASONING_EFFORT must be one of {_ALLOWED_EFFORTS}, got {_RAW_EFFORT!r}"
    )
REASONING_EFFORT: EffortLevel = _RAW_EFFORT
# Generous headroom: adaptive thinking at xhigh can consume several thousand
# tokens of reasoning before the 3-paragraph output lands.
MAX_TOKENS = int(os.environ.get("TRIAGEGUARD_REASONING_MAX_TOKENS", "8000"))

# Token-price snapshot for cost accounting. Opus 4.7 at 2026-04 list pricing:
# $5.00 / 1M input, $25.00 / 1M output. Update if pricing changes materially —
# approximate is fine for hackathon cost tracking.
OPUS_INPUT_USD_PER_MTOK = 5.0
OPUS_OUTPUT_USD_PER_MTOK = 25.0


@dataclass
class NarrativeResult:
    narrative_md: str
    cost_usd: float
    input_tokens: int
    output_tokens: int


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n... [truncated]"


def _compact_hallucination(d: HallucinationArtifact) -> dict[str, Any]:
    """Shrink D's payload: keep all invalid + first 8 verified claims."""
    payload = d.model_dump(mode="json")
    claims = payload.get("extracted_claims", [])
    invalid = [c for c in claims if c.get("status") == "invalid"]
    verified = [c for c in claims if c.get("status") == "verified"][:8]
    payload["extracted_claims"] = invalid + verified
    return payload


def _compact_root_cause(b: RootCauseArtifact) -> dict[str, Any]:
    """Truncate long snippets so the prompt stays compact."""
    payload = b.model_dump(mode="json")
    for claim in payload.get("claims_checked", []):
        snippet = claim.get("snippet")
        if isinstance(snippet, str) and len(snippet) > 240:
            claim["snippet"] = snippet[:240].rstrip() + " ..."
    return payload


def _build_user_payload(
    *,
    input_md: str,
    input_meta: InputMeta,
    repro: ReproducibilityArtifact,
    root_cause: RootCauseArtifact,
    duplicate: DuplicateArtifact,
    hallucination: HallucinationArtifact,
    signal: SignalScore,
) -> str:
    meta_view = {
        "sample_id": input_meta.sample_id,
        "submitter": input_meta.submitter,
        "target": input_meta.target.model_dump(mode="json"),
        "bug_class": input_meta.bug_class,
        "poc_present": input_meta.poc.present,
        "submitted_at": input_meta.submitted_at.isoformat(),
    }

    bundle = {
        "input_excerpt": _truncate(input_md, 1500),
        "input_meta": meta_view,
        "signal_score": signal.model_dump(mode="json"),
        "reproducibility": repro.model_dump(mode="json"),
        "root_cause": _compact_root_cause(root_cause),
        "duplicate": duplicate.model_dump(mode="json"),
        "hallucination": _compact_hallucination(hallucination),
    }
    return (
        "Write the three-paragraph narrative for the following triage run. "
        "All four agents have already reported; the deterministic synthesizer "
        "has already chosen the rule and score. Ground every factual claim "
        "in the JSON below.\n\n"
        "```json\n"
        + json.dumps(bundle, indent=2, default=str)
        + "\n```"
    )


def _estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens * OPUS_INPUT_USD_PER_MTOK / 1_000_000
        + output_tokens * OPUS_OUTPUT_USD_PER_MTOK / 1_000_000
    )


async def generate_narrative(
    *,
    input_md: str,
    input_meta: InputMeta,
    repro: ReproducibilityArtifact,
    root_cause: RootCauseArtifact,
    duplicate: DuplicateArtifact,
    hallucination: HallucinationArtifact,
    signal: SignalScore,
    client: AsyncAnthropic | None = None,
) -> NarrativeResult:
    """Generate the three-paragraph narrative. Raises on API failure.

    Caller is expected to catch and log so one failed narrative does
    not take down the rest of the run.
    """
    api = client or AsyncAnthropic()
    system = PROMPT_PATH.read_text(encoding="utf-8")
    user = _build_user_payload(
        input_md=input_md,
        input_meta=input_meta,
        repro=repro,
        root_cause=root_cause,
        duplicate=duplicate,
        hallucination=hallucination,
        signal=signal,
    )

    thinking: ThinkingConfigAdaptiveParam = {"type": "adaptive"}
    output_config: OutputConfigParam = {"effort": REASONING_EFFORT}
    response = await api.messages.create(
        model=REASONING_MODEL,
        max_tokens=MAX_TOKENS,
        thinking=thinking,
        output_config=output_config,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    text_parts: list[str] = []
    for block in response.content:
        if isinstance(block, TextBlock):
            text_parts.append(block.text)
    narrative = "\n\n".join(p.strip() for p in text_parts if p.strip()).strip()
    if not narrative:
        raise RuntimeError("reasoning response contained no text content")

    usage = response.usage
    input_tokens = int(getattr(usage, "input_tokens", 0))
    output_tokens = int(getattr(usage, "output_tokens", 0))
    cost_usd = _estimate_cost_usd(input_tokens, output_tokens)

    return NarrativeResult(
        narrative_md=narrative,
        cost_usd=cost_usd,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
