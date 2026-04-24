"""Unit tests for the deterministic Signal Score rubric.

These tests encode every rule in
`.claude/skills/signal-score-rubric/SKILL.md` §3 plus the expected
outcomes for the six demo samples in §6.

Running `pytest tests/test_synthesizer.py` verifies the scoring engine
works without touching the Anthropic API — this is the Day-1 green
milestone.
"""

from __future__ import annotations

import pytest

from orchestrator.schemas import (
    DuplicateArtifact,
    ExtractedClaim,
    HallucinationArtifact,
    HallucinationStats,
    InvalidRef,
    Recommendation,
    ReproducibilityArtifact,
    RootCauseArtifact,
    SignalLabel,
)
from orchestrator.synthesizer import synthesize

REPORT_ID = "test-report-id"


# ---------------------------------------------------------------------------
# Builders — keep each test's intent visible at the top of the test.
# ---------------------------------------------------------------------------


def _a(verdict: str, confidence: float = 0.9) -> ReproducibilityArtifact:
    return ReproducibilityArtifact(
        report_id=REPORT_ID, verdict=verdict, confidence=confidence
    )


def _b(match: str, confidence: float = 0.9) -> RootCauseArtifact:
    return RootCauseArtifact(report_id=REPORT_ID, match=match, confidence=confidence)


def _c(
    verdict: str, matched_cve: str | None = None, confidence: float = 0.9
) -> DuplicateArtifact:
    return DuplicateArtifact(
        report_id=REPORT_ID,
        verdict=verdict,
        matched_cve=matched_cve,
        confidence=confidence,
    )


def _d(invalid_count: int = 0) -> HallucinationArtifact:
    invalid = [
        InvalidRef(kind="function", value=f"fake_fn_{i}", note="not found")
        for i in range(invalid_count)
    ]
    extracted = [
        ExtractedClaim(kind="function", value=f"fake_fn_{i}", status="invalid")
        for i in range(invalid_count)
    ]
    return HallucinationArtifact(
        report_id=REPORT_ID,
        extracted_claims=extracted,
        invalid_refs=invalid,
        stats=HallucinationStats(total=invalid_count, invalid=invalid_count),
    )


def _call(a, b, c, d):
    return synthesize(report_id=REPORT_ID, a=a, b=b, c=c, d=d)


# ---------------------------------------------------------------------------
# Rule-by-rule coverage
# ---------------------------------------------------------------------------


def test_rule_1_failed_repro_plus_hallucinations_is_slop() -> None:
    score = _call(_a("failed_to_reproduce"), _b("match"), _c("novel"), _d(3))
    assert score.label == SignalLabel.SLOP
    assert score.triggering_rule == 1
    assert score.recommendation == Recommendation.REJECT
    assert score.score <= 20


def test_rule_2_no_poc_and_mismatch_is_slop() -> None:
    score = _call(_a("no_poc"), _b("mismatch"), _c("novel"), _d(0))
    assert score.label == SignalLabel.SLOP
    assert score.triggering_rule == 2
    assert score.score == 15


def test_rule_2_build_error_and_file_not_found_is_slop() -> None:
    score = _call(_a("build_error"), _b("file_not_found"), _c("novel"), _d(0))
    assert score.label == SignalLabel.SLOP
    assert score.triggering_rule == 2


def test_rule_3_duplicate_and_not_reproduced_is_slop() -> None:
    score = _call(
        _a("no_poc"), _b("match"), _c("duplicate", matched_cve="CVE-2020-1234"), _d(0)
    )
    assert score.label == SignalLabel.SLOP
    assert score.triggering_rule == 3
    assert "CVE-2020-1234" in score.reason


def test_rule_3_duplicate_but_reproduced_escalates_to_uncertain() -> None:
    score = _call(
        _a("reproduced"),
        _b("match"),
        _c("duplicate", matched_cve="CVE-2020-1234"),
        _d(0),
    )
    assert score.label == SignalLabel.UNCERTAIN
    assert score.triggering_rule == 3


def test_rule_4_many_hallucinations_is_slop() -> None:
    score = _call(_a("reproduced"), _b("match"), _c("novel"), _d(3))
    assert score.label == SignalLabel.SLOP
    assert score.triggering_rule == 4


def test_rule_5_clean_signal() -> None:
    score = _call(_a("reproduced"), _b("match"), _c("novel"), _d(0))
    assert score.label == SignalLabel.SIGNAL
    assert score.triggering_rule == 5
    assert score.score == 90
    assert score.recommendation == Recommendation.ACCEPT


def test_rule_6_partial_match_still_signal() -> None:
    score = _call(_a("reproduced"), _b("partial_match"), _c("novel"), _d(1))
    assert score.label == SignalLabel.SIGNAL
    assert score.triggering_rule == 6
    assert score.score == 75


def test_rule_7_reproduced_but_mismatch_is_uncertain() -> None:
    score = _call(_a("reproduced"), _b("mismatch"), _c("novel"), _d(1))
    assert score.label == SignalLabel.UNCERTAIN
    assert score.triggering_rule == 7


def test_rule_7_reproduced_with_two_hallucinations_is_uncertain() -> None:
    score = _call(_a("reproduced"), _b("partial_match"), _c("novel"), _d(2))
    assert score.label == SignalLabel.UNCERTAIN
    assert score.triggering_rule == 7


def test_rule_8_no_poc_but_claims_check_out() -> None:
    score = _call(_a("no_poc"), _b("match"), _c("novel"), _d(0))
    assert score.label == SignalLabel.UNCERTAIN
    assert score.triggering_rule == 8


def test_rule_9_default_is_uncertain() -> None:
    score = _call(_a("timeout"), _b("partial_match"), _c("novel"), _d(0))
    assert score.label == SignalLabel.UNCERTAIN
    assert score.triggering_rule == 9


# ---------------------------------------------------------------------------
# Demo-sample expectations (rubric §6)
# ---------------------------------------------------------------------------


def test_sample_1_real_cve_2646_expected_signal() -> None:
    """CVE-2026-2646: reproduced, match, novel, no hallucinations → SIGNAL 90."""
    score = _call(_a("reproduced"), _b("match"), _c("novel"), _d(0))
    assert score.label == SignalLabel.SIGNAL
    assert 80 <= score.score <= 95


def test_sample_3_real_cve_5194_even_without_crash_but_verified_match() -> None:
    """ECDSA bypass doesn't crash — reproduced means the bypass was observed."""
    score = _call(_a("reproduced"), _b("match"), _c("novel"), _d(0))
    assert score.label == SignalLabel.SIGNAL


def test_sample_4_curl_slop_expected_slop() -> None:
    """Public slop with fabricated refs + failed repro → SLOP <25."""
    score = _call(_a("failed_to_reproduce"), _b("mismatch"), _c("novel"), _d(3))
    assert score.label == SignalLabel.SLOP
    assert score.score < 25


def test_sample_6_live_gpt4o_slop_expected_slop() -> None:
    """Live-generated slop typically fails build + mismatches → SLOP <25."""
    score = _call(_a("build_error"), _b("mismatch"), _c("novel"), _d(2))
    assert score.label == SignalLabel.SLOP
    assert score.score < 25


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a_verdict,b_match,c_verdict,invalid_count",
    [
        ("reproduced", "match", "novel", 0),
        ("failed_to_reproduce", "mismatch", "novel", 3),
        ("build_error", "file_not_found", "novel", 0),
        ("timeout", "partial_match", "similar", 1),
        ("no_poc", "match", "novel", 0),
    ],
)
def test_score_always_in_range_0_100(
    a_verdict: str, b_match: str, c_verdict: str, invalid_count: int
) -> None:
    score = _call(_a(a_verdict), _b(b_match), _c(c_verdict), _d(invalid_count))
    assert 0 <= score.score <= 100


def test_triggering_rule_is_set() -> None:
    score = _call(_a("reproduced"), _b("match"), _c("novel"), _d(0))
    assert 1 <= score.triggering_rule <= 9
