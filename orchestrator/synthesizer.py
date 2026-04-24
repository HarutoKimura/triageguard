"""Deterministic Signal Score synthesizer.

The rubric is canonical in `.claude/skills/signal-score-rubric/SKILL.md`
§3. Keep this module as its machine-checkable mirror — changes to one
must flow to the other.

This module contains ZERO LLM calls. The scoring is rule-based by
design — it is auditable, repeatable, and testable without API credits.
Only the per-agent verdicts are LLM outputs; the synthesis is code.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from orchestrator.confidence import compute_ensemble_confidence
from orchestrator.schemas import (
    DuplicateArtifact,
    HallucinationArtifact,
    Recommendation,
    ReproducibilityArtifact,
    RootCauseArtifact,
    SignalLabel,
    SignalScore,
)


def synthesize(
    *,
    report_id: str,
    a: ReproducibilityArtifact,
    b: RootCauseArtifact,
    c: DuplicateArtifact,
    d: HallucinationArtifact,
) -> SignalScore:
    """Apply the nine rules from signal-score-rubric §3 top-down.

    The first matching rule wins. Rule 9 is the default; every run
    lands in exactly one rule.
    """
    invalid_count = len(d.invalid_refs)
    common: dict[str, Any] = {
        "report_id": report_id,
        "sub_agent_verdicts": {
            "reproducibility": a.verdict,
            "root_cause": b.match,
            "duplicate": c.verdict,
            "hallucination_invalid_count": invalid_count,
        },
        "generated_at": datetime.now(UTC),
        "ensemble_confidence": round(
            compute_ensemble_confidence(a=a, b=b, c=c, d=d), 4
        ),
    }

    # Rule 1 — Killer: explicit slop.
    if a.verdict == "failed_to_reproduce" and invalid_count >= 2:
        score = max(5, 30 - 5 * invalid_count)
        return SignalScore(
            **common,
            score=score,
            label=SignalLabel.SLOP,
            recommendation=Recommendation.REJECT,
            reason=f"PoC failed AND {invalid_count} fabricated references",
            triggering_rule=1,
        )

    # Rule 2 — Killer: no working PoC and claims don't match code.
    if a.verdict in ("build_error", "no_poc") and b.match in ("mismatch", "file_not_found"):
        return SignalScore(
            **common,
            score=15,
            label=SignalLabel.SLOP,
            recommendation=Recommendation.REJECT,
            reason="No working PoC and claims do not match code",
            triggering_rule=2,
        )

    # Rule 3 — Duplicate of a public CVE.
    if c.verdict == "duplicate":
        # If A still reproduced it, escalate to UNCERTAIN for maintainer confirmation.
        if a.verdict == "reproduced":
            return SignalScore(
                **common,
                score=35,
                label=SignalLabel.UNCERTAIN,
                recommendation=Recommendation.REVIEW,
                reason=f"Reproduced but duplicate of {c.matched_cve}",
                triggering_rule=3,
            )
        return SignalScore(
            **common,
            score=25,
            label=SignalLabel.SLOP,
            recommendation=Recommendation.REJECT,
            reason=f"Duplicate of {c.matched_cve}",
            triggering_rule=3,
        )

    # Rule 4 — Hallucinations only, nothing else dispositive.
    if invalid_count >= 3:
        return SignalScore(
            **common,
            score=20,
            label=SignalLabel.SLOP,
            recommendation=Recommendation.REJECT,
            reason=f"{invalid_count} fabricated code references",
            triggering_rule=4,
        )

    # Rule 5 — Clean signal.
    if (
        a.verdict == "reproduced"
        and b.match == "match"
        and c.verdict == "novel"
        and invalid_count == 0
    ):
        return SignalScore(
            **common,
            score=90,
            label=SignalLabel.SIGNAL,
            recommendation=Recommendation.ACCEPT,
            reason="Reproduced, matches code, novel, no fabrications",
            triggering_rule=5,
        )

    # Rule 6 — Partial signal: reproduced but root cause partial.
    if a.verdict == "reproduced" and b.match == "partial_match" and invalid_count <= 1:
        return SignalScore(
            **common,
            score=75,
            label=SignalLabel.SIGNAL,
            recommendation=Recommendation.ACCEPT,
            reason="Reproduced, partial root-cause match",
            triggering_rule=6,
        )

    # Rule 7 — Borderline: reproduced but claims drift.
    if a.verdict == "reproduced" and (b.match == "mismatch" or invalid_count >= 2):
        return SignalScore(
            **common,
            score=55,
            label=SignalLabel.UNCERTAIN,
            recommendation=Recommendation.REVIEW,
            reason="PoC runs but claims drift from code",
            triggering_rule=7,
        )

    # Rule 8 — No PoC but claims check out.
    if a.verdict == "no_poc" and b.match == "match" and invalid_count == 0:
        return SignalScore(
            **common,
            score=50,
            label=SignalLabel.UNCERTAIN,
            recommendation=Recommendation.REVIEW,
            reason="No PoC provided, but code claims verify",
            triggering_rule=8,
        )

    # Rule 9 — Default.
    return SignalScore(
        **common,
        score=45,
        label=SignalLabel.UNCERTAIN,
        recommendation=Recommendation.REVIEW,
        reason="Insufficient evidence either direction",
        triggering_rule=9,
    )
