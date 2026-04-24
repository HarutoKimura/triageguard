"""Command-line entry for Agent D.

Usage:
    python -m agents.hallucination <sample-dir> [--dry-run] [--budget 3]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

from agents.hallucination.agent import (
    DEFAULT_BUDGET_USD,
    DEFAULT_EFFORT,
    DEFAULT_MAX_TURNS,
    DEFAULT_MODEL,
    run_agent_d,
)

load_dotenv()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agents.hallucination",
        description="Run Agent D (Hallucination Detector) on a recorded sample.",
    )
    p.add_argument("sample_dir", type=Path, help="e.g. demo-inputs/s1-cve-2026-3849/")
    p.add_argument(
        "--findings-root",
        type=Path,
        default=None,
        help="where to create findings/{report_id}/ (default: ./findings/)",
    )
    p.add_argument("--budget", type=float, default=DEFAULT_BUDGET_USD, dest="budget_usd")
    p.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--effort", default=DEFAULT_EFFORT)
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="stage inputs + build options but do not call the Agent SDK",
    )
    p.add_argument(
        "--skip-source-clone",
        action="store_true",
        help="skip the git clone of the target tree (tests / offline dev only)",
    )
    return p


async def _run(args: argparse.Namespace) -> int:
    kwargs = {
        "sample_dir": args.sample_dir,
        "budget_usd": args.budget_usd,
        "max_turns": args.max_turns,
        "model": args.model,
        "effort": args.effort,
        "dry_run": args.dry_run,
        "skip_source_clone": args.skip_source_clone,
    }
    if args.findings_root is not None:
        kwargs["findings_root"] = args.findings_root

    result = await run_agent_d(**kwargs)

    tag = "DRY-RUN" if result.dry_run else "DONE"
    print(f"[{tag}] findings_dir: {result.findings_dir}")
    if result.artifact is not None:
        stats = result.artifact.stats
        print(
            f"        invalid={stats.invalid}/{stats.total}  "
            f"(verified={stats.verified}, unchecked={stats.unchecked})"
        )
    elif not result.dry_run:
        print(
            "        verdict: (no D_hallucination.json written — sub-agent did not finish)"
        )
    print(
        f"        cost: ${result.total_cost_usd:.2f}  "
        f"turns: {result.total_turns}  duration: {result.duration_sec:.1f}s"
    )
    return 0 if (result.artifact is not None or result.dry_run) else 1


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    return asyncio.run(_run(args))


if __name__ == "__main__":
    sys.exit(main())
