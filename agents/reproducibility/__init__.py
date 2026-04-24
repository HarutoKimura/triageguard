"""Agent A — Reproducibility Verifier.

Public entry point:
- `run_agent_a(sample_dir, findings_dir, ...)` — async; spawns a Claude
  Agent SDK query, streams tool events, and writes
  `findings_dir/A_reproducibility.json` conforming to
  `orchestrator.schemas.ReproducibilityArtifact`.
"""

from agents.reproducibility.agent import run_agent_a

__all__ = ["run_agent_a"]
