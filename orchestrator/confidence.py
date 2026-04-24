"""Ensemble the four sub-agents' confidences into a single 0.0-1.0 dial.

Each agent reports how sure it is of its own verdict. The synthesizer
already reasons about which rule fires; this module answers a different
question: "across all four agents, how much of the evidence was clean
and conclusive?" A high ensemble confidence means every agent reached
its verdict without hedging; a low one means at least one agent was
uncertain, so the deterministic label deserves a second look from a
maintainer even if the number looks strong.

Method: geometric mean of the four per-agent confidences. Geometric
mean is harsh about low outliers — if any one agent reports 0.3,
the ensemble cannot reach 0.9, no matter how confident the others.
This is the property we want: one wobbly agent is enough to warrant
review.

Agent D does not ship a top-level `confidence` field in its artifact.
We derive one from its stats: the fraction of extracted claims the
agent was able to actually check (verified + invalid) / total. An
agent that could not verify its inputs should not drag the ensemble
down any less than an agent that reports low confidence directly.
"""

from __future__ import annotations

from orchestrator.schemas import (
    DuplicateArtifact,
    HallucinationArtifact,
    ReproducibilityArtifact,
    RootCauseArtifact,
)


def _hallucination_confidence(d: HallucinationArtifact) -> float:
    """Coverage of claim-checking. No claims → full confidence."""
    total = d.stats.total
    if total <= 0:
        return 1.0
    checked = d.stats.verified + d.stats.invalid
    if checked <= 0:
        return 0.0
    ratio = checked / total
    # Clamp against FP drift when total == verified + invalid but rounding
    # pushed the quotient slightly above 1.0.
    return max(0.0, min(1.0, ratio))


def compute_ensemble_confidence(
    *,
    a: ReproducibilityArtifact,
    b: RootCauseArtifact,
    c: DuplicateArtifact,
    d: HallucinationArtifact,
) -> float:
    """Geometric mean of the four per-agent confidences, in [0.0, 1.0]."""
    confidences = (
        max(0.0, min(1.0, a.confidence)),
        max(0.0, min(1.0, b.confidence)),
        max(0.0, min(1.0, c.confidence)),
        _hallucination_confidence(d),
    )
    # If any component is exactly zero, the geometric mean is zero — which
    # is the correct signal: one agent with no confidence collapses the
    # ensemble. Short-circuit to avoid log(0) surprises.
    product = 1.0
    for x in confidences:
        product *= x
    return float(product ** (1.0 / len(confidences)))
