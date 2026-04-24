"""Orchestrator — fan out sub-agents, synthesize a Signal Score.

Single-sample pipeline:

1. Parse `INPUT_meta.json`, mint a shared `report_id`, create the findings
   directory.
2. Dispatch the sub-agents concurrently via `asyncio.gather(..., return_exceptions=True)`.
   Each sub-agent receives the shared `report_id`; the two agents share
   one findings directory (see `prepare_findings_dir(exist_ok=True)`).
3. When all return, load the four JSON artifacts from disk (file-based
   handoff — no transcript passing). If all four validate, run the
   deterministic synthesizer. Otherwise return a partial result and
   name the missing agents.

Canonical rules:
- `.claude/RULES.md §4` — four parallel sub-agents, one synthesizer.
- `.claude/skills/agent-sdk-patterns/SKILL.md §2` — `return_exceptions=True`
  so one sub-agent's crash does not take down the other three.
- `.claude/skills/findings-journal/SKILL.md` — schema + naming.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from agents.duplicate.agent import AgentCRunResult, run_agent_c
from agents.hallucination.agent import AgentDRunResult, run_agent_d
from agents.reproducibility.agent import AgentARunResult, run_agent_a
from agents.root_cause.agent import AgentBRunResult, run_agent_b
from orchestrator.findings import (
    atomic_write_json,
    make_report_id,
    prepare_findings_dir,
)
from orchestrator.reasoning import generate_narrative
from orchestrator.schemas import (
    DuplicateArtifact,
    HallucinationArtifact,
    InputMeta,
    ReproducibilityArtifact,
    RootCauseArtifact,
    SignalScore,
)
from orchestrator.synthesizer import synthesize

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class OrchestratorResult:
    report_id: str
    findings_dir: Path
    sample_id: str
    signal_score: SignalScore | None
    # agent_name -> AgentARunResult | AgentBRunResult | NotBuilt | Exception
    agent_results: dict[str, Any] = field(default_factory=dict)
    total_runtime_sec: float = 0.0
    total_cost_usd: float = 0.0
    dry_run: bool = False
    missing_agents: list[str] = field(default_factory=list)


async def run_triage(
    *,
    sample_dir: Path,
    findings_root: Path = REPO_ROOT / "findings",
    dry_run: bool = False,
    skip_source_clone: bool = False,
) -> OrchestratorResult:
    """Fan out the sub-agents against one sample and try to synthesize."""
    sample_dir = sample_dir.resolve()
    if not sample_dir.is_dir():
        raise FileNotFoundError(f"sample_dir not found: {sample_dir}")

    meta_path = sample_dir / "INPUT_meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"missing INPUT_meta.json in {sample_dir}")
    meta = InputMeta.model_validate_json(meta_path.read_text())
    report_id = make_report_id(meta.sample_id)

    # First creator — default exist_ok=False so we never collide on ids.
    findings_dir = prepare_findings_dir(findings_root, report_id)

    t0 = time.monotonic()

    # Fan out all four sub-agents. return_exceptions=True so one crash
    # doesn't take down the other three (agent-sdk-patterns §2).
    a_coro = run_agent_a(
        sample_dir=sample_dir,
        findings_root=findings_root,
        report_id=report_id,
        dry_run=dry_run,
    )
    b_coro = run_agent_b(
        sample_dir=sample_dir,
        findings_root=findings_root,
        report_id=report_id,
        dry_run=dry_run,
        skip_source_clone=skip_source_clone,
    )
    c_coro = run_agent_c(
        sample_dir=sample_dir,
        findings_root=findings_root,
        report_id=report_id,
        dry_run=dry_run,
    )
    d_coro = run_agent_d(
        sample_dir=sample_dir,
        findings_root=findings_root,
        report_id=report_id,
        dry_run=dry_run,
        skip_source_clone=skip_source_clone,
    )

    a_res, b_res, c_res, d_res = await asyncio.gather(
        a_coro, b_coro, c_coro, d_coro, return_exceptions=True
    )

    agent_results: dict[str, Any] = {
        "reproducibility": a_res,
        "root_cause": b_res,
        "duplicate": c_res,
        "hallucination": d_res,
    }

    # Persist any unexpected exceptions so a post-run reviewer can see them.
    for name, result in agent_results.items():
        if isinstance(result, Exception):
            (findings_dir / f"errors_{name}.log").write_text(
                f"{type(result).__name__}: {result}\n", encoding="utf-8"
            )

    runtime_sec = time.monotonic() - t0
    total_cost_usd = _sum_cost(agent_results)
    signal_score, missing, parsed_artifacts = _try_synthesize(report_id, findings_dir)

    if signal_score is not None:
        narrative_cost = await _attach_narrative(
            signal_score=signal_score,
            sample_dir=sample_dir,
            meta=meta,
            artifacts=parsed_artifacts,
            findings_dir=findings_dir,
            dry_run=dry_run,
        )
        total_cost_usd += narrative_cost
        _write_signal_score(findings_dir, signal_score, runtime_sec, total_cost_usd)
        _write_synthesis_md(findings_dir, signal_score, meta)

    return OrchestratorResult(
        report_id=report_id,
        findings_dir=findings_dir,
        sample_id=meta.sample_id,
        signal_score=signal_score,
        agent_results=agent_results,
        total_runtime_sec=runtime_sec,
        total_cost_usd=total_cost_usd,
        dry_run=dry_run,
        missing_agents=missing,
    )


def _sum_cost(agent_results: dict[str, Any]) -> float:
    total = 0.0
    for res in agent_results.values():
        if isinstance(
            res, (AgentARunResult, AgentBRunResult, AgentCRunResult, AgentDRunResult)
        ):
            total += float(res.total_cost_usd)
    return total


def _try_synthesize(
    report_id: str, findings_dir: Path
) -> tuple[SignalScore | None, list[str], dict[str, Any]]:
    """Load the four artifacts from disk; synthesize only if all present.

    Returns `(SignalScore | None, missing_agent_keys, parsed_artifacts)`.
    File-based handoff per `.claude/skills/findings-journal/SKILL.md §1`.
    """
    missing: list[str] = []
    pairs: list[tuple[str, str, type[Any]]] = [
        ("reproducibility", "A_reproducibility.json", ReproducibilityArtifact),
        ("root_cause", "B_root_cause.json", RootCauseArtifact),
        ("duplicate", "C_duplicate.json", DuplicateArtifact),
        ("hallucination", "D_hallucination.json", HallucinationArtifact),
    ]
    parsed: dict[str, Any] = {}
    for key, filename, model in pairs:
        path = findings_dir / filename
        if not path.exists():
            missing.append(key)
            continue
        try:
            parsed[key] = model.model_validate_json(path.read_text())
        except Exception as exc:
            (findings_dir / f"errors_{key}_parse.log").write_text(
                f"{type(exc).__name__}: {exc}\n", encoding="utf-8"
            )
            missing.append(key)

    if missing:
        return None, missing, parsed

    return (
        synthesize(
            report_id=report_id,
            a=parsed["reproducibility"],
            b=parsed["root_cause"],
            c=parsed["duplicate"],
            d=parsed["hallucination"],
        ),
        [],
        parsed,
    )


async def _attach_narrative(
    *,
    signal_score: SignalScore,
    sample_dir: Path,
    meta: InputMeta,
    artifacts: dict[str, Any],
    findings_dir: Path,
    dry_run: bool,
) -> float:
    """Ask Opus 4.7 for a maintainer-facing narrative. Best-effort.

    Mutates `signal_score.narrative` in place on success. On any
    failure, logs to `errors_narrative.log` and returns 0.0 cost so
    the deterministic verdict still reaches the UI.
    """
    if dry_run:
        return 0.0

    input_md_path = sample_dir / "INPUT.md"
    input_md = (
        input_md_path.read_text(encoding="utf-8") if input_md_path.exists() else ""
    )

    try:
        result = await generate_narrative(
            input_md=input_md,
            input_meta=meta,
            repro=artifacts["reproducibility"],
            root_cause=artifacts["root_cause"],
            duplicate=artifacts["duplicate"],
            hallucination=artifacts["hallucination"],
            signal=signal_score,
        )
    except Exception as exc:
        (findings_dir / "errors_narrative.log").write_text(
            f"{type(exc).__name__}: {exc}\n", encoding="utf-8"
        )
        return 0.0

    signal_score.narrative = result.narrative_md
    (findings_dir / "NARRATIVE.md").write_text(
        result.narrative_md + "\n", encoding="utf-8"
    )
    return result.cost_usd


def _write_signal_score(
    findings_dir: Path,
    score: SignalScore,
    runtime_sec: float,
    total_cost_usd: float,
) -> None:
    payload = score.model_dump(mode="json")
    payload["total_runtime_sec"] = round(runtime_sec, 2)
    payload["total_cost_usd"] = round(total_cost_usd, 4)
    atomic_write_json(findings_dir / "SIGNAL_SCORE.json", payload)


def _write_synthesis_md(
    findings_dir: Path, score: SignalScore, meta: InputMeta
) -> None:
    """Human-readable SYNTHESIS.md for the demo UI + post-run review."""
    generated = score.generated_at or datetime.now(UTC)
    lines = [
        f"# TriageGuard Synthesis — {meta.sample_id}",
        "",
        f"**Label:** {score.label.value}  ",
        f"**Score:** {score.score} / 100  ",
        f"**Recommendation:** {score.recommendation.value}  ",
        f"**Triggering rule:** {score.triggering_rule}  ",
        f"**Reason:** {score.reason}",
        "",
        "## Sub-agent verdicts",
        "",
    ]
    for key, value in score.sub_agent_verdicts.items():
        lines.append(f"- **{key}**: `{value}`")
    if score.narrative:
        lines.extend(
            [
                "",
                "## Narrative (Opus 4.7)",
                "",
                score.narrative,
            ]
        )
    lines.extend(
        [
            "",
            "## Target",
            "",
            f"- vendor/product: {meta.target.vendor} / {meta.target.product}",
            f"- repo: {meta.target.repo}",
            f"- claimed_tag: {meta.target.claimed_tag}",
            f"- claimed_cve: {meta.target.claimed_cve}",
            "",
            f"_Generated {generated.isoformat()}_",
            "",
        ]
    )
    (findings_dir / "SYNTHESIS.md").write_text("\n".join(lines), encoding="utf-8")
