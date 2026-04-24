"""Regenerate the Opus 4.7 narrative for an existing findings/ run.

Usage:
    .venv/bin/python scripts/regenerate_narrative.py <findings_dir>

Loads the four agent artifacts + SIGNAL_SCORE + INPUT.md from the given
directory, calls `orchestrator.reasoning.generate_narrative`, and
writes the result back into both SIGNAL_SCORE.json (as the `narrative`
field) and a sibling NARRATIVE.md.

Exists so prior Day-1 runs can pick up Day-2's narrative layer without
re-running the four sub-agents.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from orchestrator.reasoning import generate_narrative
from orchestrator.schemas import (
    DuplicateArtifact,
    HallucinationArtifact,
    InputMeta,
    ReproducibilityArtifact,
    RootCauseArtifact,
    SignalScore,
)


async def regenerate(findings_dir: Path) -> None:
    load_dotenv()

    meta = InputMeta.model_validate_json(
        (findings_dir / "INPUT_meta.json").read_text(encoding="utf-8")
    )
    repro = ReproducibilityArtifact.model_validate_json(
        (findings_dir / "A_reproducibility.json").read_text(encoding="utf-8")
    )
    root_cause = RootCauseArtifact.model_validate_json(
        (findings_dir / "B_root_cause.json").read_text(encoding="utf-8")
    )
    duplicate = DuplicateArtifact.model_validate_json(
        (findings_dir / "C_duplicate.json").read_text(encoding="utf-8")
    )
    hallucination = HallucinationArtifact.model_validate_json(
        (findings_dir / "D_hallucination.json").read_text(encoding="utf-8")
    )
    signal_raw = json.loads(
        (findings_dir / "SIGNAL_SCORE.json").read_text(encoding="utf-8")
    )
    signal = SignalScore.model_validate(signal_raw)
    input_md = (findings_dir / "INPUT.md").read_text(encoding="utf-8")

    print(f"calling Opus 4.7 for {findings_dir.name} ...", flush=True)
    result = await generate_narrative(
        input_md=input_md,
        input_meta=meta,
        repro=repro,
        root_cause=root_cause,
        duplicate=duplicate,
        hallucination=hallucination,
        signal=signal,
    )
    print(
        f"  → {result.output_tokens} output tokens,"
        f" ${result.cost_usd:.4f},"
        f" {len(result.narrative_md.split())} words",
        flush=True,
    )

    # Write NARRATIVE.md for direct reading.
    (findings_dir / "NARRATIVE.md").write_text(
        result.narrative_md + "\n", encoding="utf-8"
    )

    # Update SIGNAL_SCORE.json in place so web/ picks up the narrative.
    signal_raw["narrative"] = result.narrative_md
    (findings_dir / "SIGNAL_SCORE.json").write_text(
        json.dumps(signal_raw, indent=2) + "\n", encoding="utf-8"
    )

    print(f"wrote NARRATIVE.md and refreshed SIGNAL_SCORE.json in {findings_dir}")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    findings_dir = Path(argv[1]).resolve()
    if not findings_dir.is_dir():
        print(f"not a directory: {findings_dir}", file=sys.stderr)
        return 2
    asyncio.run(regenerate(findings_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
