"""Pydantic schemas for the five JSON artifacts produced per triage run.

Canonical schema definitions live in
`.claude/skills/findings-journal/SKILL.md`. When that skill file
changes, update these models — they are the machine-checkable form.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Shared types
# ---------------------------------------------------------------------------


class AgentName(StrEnum):
    REPRODUCIBILITY = "reproducibility"
    ROOT_CAUSE = "root_cause"
    DUPLICATE = "duplicate_detector"
    HALLUCINATION = "hallucination_detector"


class SignalLabel(StrEnum):
    SIGNAL = "SIGNAL"
    UNCERTAIN = "UNCERTAIN"
    SLOP = "SLOP"
    ERRORED = "ERRORED"


class Recommendation(StrEnum):
    ACCEPT = "ACCEPT"
    REVIEW = "REVIEW"
    REJECT = "REJECT"


# ---------------------------------------------------------------------------
# Agent A — Reproducibility
# ---------------------------------------------------------------------------


ReproVerdict = Literal[
    "reproduced",
    "failed_to_reproduce",
    "no_poc",
    "build_error",
    "timeout",
]


class ReproEvidence(BaseModel):
    target_tag: str | None = None
    build_time_sec: float | None = None
    build_exit_code: int | None = None
    poc_exit_code: int | None = None
    poc_signal: str | None = None
    sanitizer_summary: str | None = None
    sanitizer_frames: list[str] = Field(default_factory=list)


class ReproducibilityArtifact(BaseModel):
    agent: Literal["reproducibility"] = "reproducibility"
    report_id: str
    verdict: ReproVerdict
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: ReproEvidence = Field(default_factory=ReproEvidence)
    log_files: dict[str, str] = Field(default_factory=dict)
    timestamps: dict[str, datetime] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Agent B — Root Cause
# ---------------------------------------------------------------------------


RootCauseMatch = Literal["match", "partial_match", "mismatch", "file_not_found"]
ClaimStatus = Literal["verified", "partially_verified", "not_verified"]


class ClaimCheck(BaseModel):
    claim: str
    status: ClaimStatus
    file: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    snippet: str | None = None
    note: str | None = None


class RootCauseArtifact(BaseModel):
    agent: Literal["root_cause"] = "root_cause"
    report_id: str
    match: RootCauseMatch
    confidence: float = Field(ge=0.0, le=1.0)
    claims_checked: list[ClaimCheck] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Agent C — Duplicate Detector
# ---------------------------------------------------------------------------


DupVerdict = Literal["novel", "duplicate", "similar"]
CandidateVerdict = Literal["different_class", "related_but_distinct", "likely_same"]


class DuplicateCandidate(BaseModel):
    id: str
    title: str
    similarity: float = Field(ge=0.0, le=1.0)
    verdict: CandidateVerdict


class DuplicateArtifact(BaseModel):
    agent: Literal["duplicate_detector"] = "duplicate_detector"
    report_id: str
    verdict: DupVerdict
    confidence: float = Field(ge=0.0, le=1.0)
    queried_databases: list[str] = Field(default_factory=list)
    top_candidates: list[DuplicateCandidate] = Field(default_factory=list)
    matched_cve: str | None = None
    errors: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Agent D — Hallucination Detector
# ---------------------------------------------------------------------------


RefKind = Literal[
    "function", "file", "line", "symbol", "cve", "cvss_vector", "tag", "option"
]
RefStatus = Literal["verified", "invalid", "unchecked"]


class ExtractedClaim(BaseModel):
    kind: RefKind
    value: str
    status: RefStatus
    source: str | None = None
    note: str | None = None


class InvalidRef(BaseModel):
    kind: RefKind
    value: str
    note: str | None = None


class HallucinationStats(BaseModel):
    total: int = 0
    verified: int = 0
    invalid: int = 0
    unchecked: int = 0


class HallucinationArtifact(BaseModel):
    agent: Literal["hallucination_detector"] = "hallucination_detector"
    report_id: str
    extracted_claims: list[ExtractedClaim] = Field(default_factory=list)
    invalid_refs: list[InvalidRef] = Field(default_factory=list)
    stats: HallucinationStats = Field(default_factory=HallucinationStats)
    errors: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Synthesizer output
# ---------------------------------------------------------------------------


class SignalScore(BaseModel):
    report_id: str
    score: int = Field(ge=0, le=100)
    label: SignalLabel
    recommendation: Recommendation
    reason: str
    triggering_rule: int = Field(ge=0, le=99)
    sub_agent_verdicts: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime | None = None


# ---------------------------------------------------------------------------
# Input metadata (what /record-finding writes)
# ---------------------------------------------------------------------------


class Expected(BaseModel):
    label: SignalLabel
    score_min: int = Field(ge=0, le=100)
    score_max: int = Field(ge=0, le=100)
    triggering_rule_hint: int | None = None


class Target(BaseModel):
    vendor: str
    product: str
    repo: str
    claimed_tag: str | None = None
    claimed_cve: str | None = None


class PoC(BaseModel):
    present: bool
    path: str | None = None
    entry: str | None = None


class InputMeta(BaseModel):
    sample_id: str
    submitter: str
    target: Target
    bug_class: str | None = None
    poc: PoC
    submitted_at: datetime
    expected: Expected
