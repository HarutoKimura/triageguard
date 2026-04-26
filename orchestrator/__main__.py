"""Command-line entry for the orchestrator.

Usage:
    python -m orchestrator <sample-dir> [--dry-run] [--skip-source-clone]

Runs the full four-agent pipeline against one sample directory and
prints a terse verdict. Exit codes:

- 0: all four sub-agents completed and a Signal Score was produced
- 0: dry-run (plumbing verified, no API calls made)
- 1: one or more sub-agents missing or errored — partial state printed
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from orchestrator.run import OrchestratorResult, run_triage

load_dotenv()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="orchestrator",
        description=(
            "Fan out TriageGuard's four sub-agents against one sample "
            "and print a Signal Score verdict."
        ),
    )
    p.add_argument("sample_dir", type=Path, help="e.g. demo-inputs/s1-cve-2026-3849/")
    p.add_argument(
        "--findings-root",
        type=Path,
        default=None,
        help="where to create findings/{report_id}/ (default: ./findings/)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="stage inputs + build options per agent but do not call the Agent SDK",
    )
    p.add_argument(
        "--skip-source-clone",
        action="store_true",
        help="skip Agent B's git clone (offline dev / tests)",
    )
    p.add_argument(
        "--no-haiku",
        action="store_true",
        help="skip the Haiku 4.5 preflight digest (saves ~$0.001 + ~1s)",
    )
    return p


def _fmt_agent_line(name: str, result: Any) -> str:
    if isinstance(result, Exception):
        return f"  {name:<16} → ERROR {type(result).__name__}: {result}"
    # Each AgentXRunResult exposes `.artifact`. A/C have `verdict`, B has
    # `match`, D has `stats` (count-based). Duck-type rather than importing
    # four dataclasses just to branch.
    artifact = getattr(result, "artifact", None)
    if artifact is None:
        tag = "(no artifact written)"
    elif hasattr(artifact, "verdict"):
        tag = f"{artifact.verdict} (conf {artifact.confidence:.2f})"
    elif hasattr(artifact, "match"):
        tag = f"{artifact.match} (conf {artifact.confidence:.2f})"
    elif hasattr(artifact, "stats"):
        st = artifact.stats
        tag = f"invalid={st.invalid}/{st.total} (verified={st.verified})"
    else:
        tag = "(unknown artifact type)"
    cost = getattr(result, "total_cost_usd", 0.0)
    dur = getattr(result, "duration_sec", 0.0)
    return f"  {name:<16} → {tag}  [${cost:.2f}, {dur:.1f}s]"


def _print_result(res: OrchestratorResult) -> None:
    tag = "DRY-RUN" if res.dry_run else "DONE"
    print(f"[{tag}] sample: {res.sample_id}")
    print(f"        report_id: {res.report_id}")
    print(f"        findings_dir: {res.findings_dir}")
    if res.preflight is not None:
        print(
            f"        preflight (Haiku 4.5): {res.preflight.wallclock_sec:.1f}s, "
            f"${res.preflight.cost_usd:.4f}"
        )
        for line in res.preflight.summary_md.splitlines():
            if line.strip():
                print(f"          {line}")
    print("        agents:")
    for name in ("reproducibility", "root_cause", "duplicate", "hallucination"):
        print(_fmt_agent_line(name, res.agent_results.get(name)))
    if res.signal_score is not None:
        s = res.signal_score
        print(
            f"        SIGNAL SCORE: {s.score}  label={s.label.value}  "
            f"rule={s.triggering_rule}  ({s.reason})"
        )
    else:
        if res.missing_agents:
            print(
                f"        SIGNAL SCORE: (skipped — missing artifacts: "
                f"{', '.join(res.missing_agents)})"
            )
        else:
            print("        SIGNAL SCORE: (skipped)")
    print(
        f"        total_cost: ${res.total_cost_usd:.2f}  "
        f"runtime: {res.total_runtime_sec:.1f}s"
    )


async def _run(args: argparse.Namespace) -> int:
    kwargs: dict[str, Any] = {
        "sample_dir": args.sample_dir,
        "dry_run": args.dry_run,
        "skip_source_clone": args.skip_source_clone,
        "enable_haiku_preflight": not args.no_haiku,
    }
    if args.findings_root is not None:
        kwargs["findings_root"] = args.findings_root

    result = await run_triage(**kwargs)
    _print_result(result)

    if args.dry_run:
        return 0
    if result.signal_score is None:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    return asyncio.run(_run(args))


if __name__ == "__main__":
    sys.exit(main())
