"""Unit tests for the ensemble confidence calculator.

Geometric mean semantics: one wobbly agent should be enough to drag
the ensemble below the strong agents' level.
"""

from __future__ import annotations

import math

import pytest

from orchestrator.confidence import compute_ensemble_confidence
from orchestrator.schemas import (
    DuplicateArtifact,
    ExtractedClaim,
    HallucinationArtifact,
    HallucinationStats,
    ReproducibilityArtifact,
    RootCauseArtifact,
)

REPORT_ID = "test-report-id"


def _a(conf: float) -> ReproducibilityArtifact:
    return ReproducibilityArtifact(
        report_id=REPORT_ID, verdict="reproduced", confidence=conf
    )


def _b(conf: float) -> RootCauseArtifact:
    return RootCauseArtifact(report_id=REPORT_ID, match="match", confidence=conf)


def _c(conf: float) -> DuplicateArtifact:
    return DuplicateArtifact(report_id=REPORT_ID, verdict="novel", confidence=conf)


def _d(total: int, verified: int, invalid: int) -> HallucinationArtifact:
    unchecked = total - verified - invalid
    return HallucinationArtifact(
        report_id=REPORT_ID,
        extracted_claims=[
            ExtractedClaim(kind="function", value=f"fn_{i}", status="verified")
            for i in range(verified + invalid)
        ],
        stats=HallucinationStats(
            total=total, verified=verified, invalid=invalid, unchecked=unchecked
        ),
    )


def test_all_high_confidence_produces_high_ensemble() -> None:
    score = compute_ensemble_confidence(
        a=_a(0.97), b=_b(0.95), c=_c(0.90), d=_d(52, 52, 0)
    )
    # Geometric mean of 0.97, 0.95, 0.90, 1.0
    expected = (0.97 * 0.95 * 0.90 * 1.0) ** 0.25
    assert math.isclose(score, expected, rel_tol=1e-6)
    assert score >= 0.94  # all strong confidences


def test_single_wobbly_agent_drags_ensemble_down() -> None:
    # A is very uncertain; B/C/D are rock solid.
    low = compute_ensemble_confidence(
        a=_a(0.30), b=_b(0.95), c=_c(0.95), d=_d(10, 10, 0)
    )
    high = compute_ensemble_confidence(
        a=_a(0.95), b=_b(0.95), c=_c(0.95), d=_d(10, 10, 0)
    )
    assert low < 0.75
    assert high > 0.90
    assert low < high


def test_zero_confidence_zeros_ensemble() -> None:
    score = compute_ensemble_confidence(
        a=_a(0.0), b=_b(0.9), c=_c(0.9), d=_d(10, 10, 0)
    )
    assert score == 0.0


def test_agent_d_no_claims_defaults_to_full_confidence() -> None:
    # Slop reports with no refs to check should not self-penalize D.
    score = compute_ensemble_confidence(
        a=_a(0.9), b=_b(0.9), c=_c(0.9), d=_d(0, 0, 0)
    )
    expected = (0.9 * 0.9 * 0.9 * 1.0) ** 0.25
    assert math.isclose(score, expected, rel_tol=1e-6)


def test_agent_d_partial_coverage_reduces_confidence() -> None:
    # 10 claims extracted, 5 checked (3 verified + 2 invalid), 5 unchecked.
    partial = compute_ensemble_confidence(
        a=_a(0.9), b=_b(0.9), c=_c(0.9), d=_d(10, 3, 2)
    )
    full = compute_ensemble_confidence(
        a=_a(0.9), b=_b(0.9), c=_c(0.9), d=_d(10, 8, 2)
    )
    assert partial < full


def test_confidence_is_bounded() -> None:
    # Even with a pathological input, output stays in [0.0, 1.0].
    score = compute_ensemble_confidence(
        a=_a(1.0), b=_b(1.0), c=_c(1.0), d=_d(1, 1, 0)
    )
    assert score == pytest.approx(1.0)


def test_hallucination_confidence_clamps_overshoot() -> None:
    # Sanity: if stats overcount (shouldn't happen but be defensive),
    # coverage clamps to 1.0 not >1.0.
    d = HallucinationArtifact(
        report_id=REPORT_ID,
        stats=HallucinationStats(total=5, verified=4, invalid=2, unchecked=0),
    )
    score = compute_ensemble_confidence(a=_a(0.9), b=_b(0.9), c=_c(0.9), d=d)
    assert 0.0 <= score <= 1.0
