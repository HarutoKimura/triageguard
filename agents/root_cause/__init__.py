"""Agent B — Root Cause Analyzer.

Public entry point:
- `run_agent_b(sample_dir, findings_dir, ...)` — async; verifies each
  concrete claim in the report against the source tree at the claimed
  tag, writes `findings_dir/B_root_cause.json` conforming to
  `orchestrator.schemas.RootCauseArtifact`.
"""

from agents.root_cause.agent import run_agent_b

__all__ = ["run_agent_b"]
