"""Agent B — Root Cause Analyzer: SDK orchestration.

Mirrors `agents.reproducibility.agent` but for a read-only source
review. Key differences:

- Tools: `Read`, `Grep` only. No Bash, no network.
- Budget: $3 (vs. $8 for A) — code navigation, not execution.
- `_stage_inputs` ensures a shallow clone of the target repo at the
  claimed tag exists under `vendor/{vendor}-{tag}/`, then symlinks
  `findings_dir/source` at it (per agent-b-root-cause.md §inputs:
  "A local clone ... already on disk under {findings_dir}/source/").
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    create_sdk_mcp_server,
    query,
)

from agents.root_cause.prompt import load_system_prompt
from agents.root_cause.tools import make_emit_verdict, make_think
from orchestrator.findings import make_report_id, prepare_findings_dir
from orchestrator.schemas import InputMeta, RootCauseArtifact

EffortLiteral = Literal["low", "medium", "high", "max"]

REPO_ROOT = Path(__file__).resolve().parents[2]
VENDOR_ROOT = REPO_ROOT / "vendor"

MCP_SERVER_NAME = "agent_b"

ALLOWED_TOOLS: list[str] = [
    "Read",
    "Grep",
    f"mcp__{MCP_SERVER_NAME}__think",
    f"mcp__{MCP_SERVER_NAME}__emit_verdict",
]

DEFAULT_BUDGET_USD = 3.0
DEFAULT_MAX_TURNS = 500
DEFAULT_MODEL = "claude-opus-4-7"
DEFAULT_EFFORT = "xhigh"

CLONE_TIMEOUT_SEC = 240


@dataclass
class AgentBRunResult:
    report_id: str
    findings_dir: Path
    artifact: RootCauseArtifact | None
    scratchpad: list[str] = field(default_factory=list)
    total_cost_usd: float = 0.0
    total_turns: int = 0
    duration_sec: float = 0.0
    dry_run: bool = False


def _ensure_source_clone(repo: str, tag: str, product: str) -> Path:
    """Shallow-clone `repo` at `tag` into `vendor/{product}-{tag}/` if missing.

    Idempotent — if the directory exists and is non-empty, the clone is
    skipped. The vendor tree is shared across samples that target the
    same tag.
    """
    VENDOR_ROOT.mkdir(parents=True, exist_ok=True)
    dest = VENDOR_ROOT / f"{product}-{tag}"
    if dest.exists() and any(dest.iterdir()):
        return dest
    subprocess.run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            tag,
            repo,
            str(dest),
        ],
        check=True,
        timeout=CLONE_TIMEOUT_SEC,
    )
    return dest


def _stage_inputs(
    sample_dir: Path, findings_dir: Path, *, skip_source_clone: bool = False
) -> InputMeta:
    """Copy INPUT files and (unless skipped) materialize `findings_dir/source`."""
    input_md = sample_dir / "INPUT.md"
    input_meta = sample_dir / "INPUT_meta.json"
    if not input_md.exists() or not input_meta.exists():
        raise FileNotFoundError(
            f"sample_dir {sample_dir} missing INPUT.md or INPUT_meta.json"
        )

    shutil.copy2(input_md, findings_dir / "INPUT.md")
    shutil.copy2(input_meta, findings_dir / "INPUT_meta.json")

    meta = InputMeta.model_validate_json((findings_dir / "INPUT_meta.json").read_text())

    if skip_source_clone:
        return meta
    if meta.target.claimed_tag is None:
        raise ValueError(
            f"sample {meta.sample_id} has no target.claimed_tag; "
            "cannot stage source clone for Agent B"
        )

    vendor_dir = _ensure_source_clone(
        repo=meta.target.repo, tag=meta.target.claimed_tag, product=meta.target.product
    )
    source_link = findings_dir / "source"
    if source_link.exists() or source_link.is_symlink():
        source_link.unlink()
    source_link.symlink_to(vendor_dir, target_is_directory=True)
    return meta


def _build_user_prompt(meta: InputMeta) -> str:
    return (
        "Verify the report's root-cause claims against the source tree.\n\n"
        "Files available:\n"
        "- `INPUT.md` — the report body as submitted (verbatim)\n"
        "- `INPUT_meta.json` — structured metadata about the target\n"
        "- `source/` — shallow clone of the target at the claimed tag "
        "(a symlink into `vendor/`; treat it as the canonical source)\n\n"
        "Target summary (from INPUT_meta.json):\n"
        f"- vendor/product: {meta.target.vendor} / {meta.target.product}\n"
        f"- repo: {meta.target.repo}\n"
        f"- claimed_tag: {meta.target.claimed_tag}\n"
        f"- claimed_cve: {meta.target.claimed_cve}\n"
        f"- bug_class: {meta.bug_class}\n\n"
        "Follow the procedure in your system prompt. Read/Grep only — no "
        "Bash, no network. Call `think` before the verdict. Call "
        "`emit_verdict` exactly once to finish."
    )


def _build_options(
    *,
    findings_dir: Path,
    system_prompt: str,
    think_tool: Any,
    emit_verdict_tool: Any,
    budget_usd: float,
    max_turns: int,
    model: str,
    effort: str,
) -> ClaudeAgentOptions:
    mcp_server = create_sdk_mcp_server(
        name=MCP_SERVER_NAME,
        version="0.1.0",
        tools=[think_tool, emit_verdict_tool],
    )
    return ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": system_prompt,
        },
        setting_sources=["project"],
        permission_mode="bypassPermissions",
        allowed_tools=ALLOWED_TOOLS,
        mcp_servers={MCP_SERVER_NAME: mcp_server},
        cwd=str(findings_dir),
        add_dirs=[str(REPO_ROOT), str(VENDOR_ROOT)],
        max_turns=max_turns,
        max_budget_usd=budget_usd,
        model=model,
        effort=cast(EffortLiteral, effort),
        include_partial_messages=True,
    )


async def run_agent_b(
    *,
    sample_dir: Path,
    findings_root: Path = REPO_ROOT / "findings",
    report_id: str | None = None,
    budget_usd: float = DEFAULT_BUDGET_USD,
    max_turns: int = DEFAULT_MAX_TURNS,
    model: str = DEFAULT_MODEL,
    effort: str = DEFAULT_EFFORT,
    dry_run: bool = False,
    skip_source_clone: bool = False,
) -> AgentBRunResult:
    """Run Agent B end-to-end against a recorded sample.

    If `skip_source_clone` is True, staging skips the git clone and
    symlink. Used by tests; not recommended for real runs.
    """
    sample_dir = sample_dir.resolve()
    if not sample_dir.is_dir():
        raise FileNotFoundError(f"sample_dir not found: {sample_dir}")

    caller_supplied_id = report_id is not None
    if report_id is None:
        meta_preview = json.loads((sample_dir / "INPUT_meta.json").read_text())
        report_id = make_report_id(meta_preview.get("sample_id", "unnamed"))

    findings_dir = prepare_findings_dir(
        findings_root, report_id, exist_ok=caller_supplied_id
    )
    meta = _stage_inputs(sample_dir, findings_dir, skip_source_clone=skip_source_clone)
    user_prompt = _build_user_prompt(meta)

    started_at = datetime.now(UTC)
    scratchpad: list[str] = []
    think_tool = make_think(scratchpad)
    emit_verdict_tool = make_emit_verdict(
        findings_dir=findings_dir, report_id=report_id, started_at=started_at
    )

    options = _build_options(
        findings_dir=findings_dir,
        system_prompt=load_system_prompt(),
        think_tool=think_tool,
        emit_verdict_tool=emit_verdict_tool,
        budget_usd=budget_usd,
        max_turns=max_turns,
        model=model,
        effort=effort,
    )

    if dry_run:
        _persist_scratchpad(findings_dir, scratchpad)
        return AgentBRunResult(
            report_id=report_id,
            findings_dir=findings_dir,
            artifact=None,
            scratchpad=scratchpad,
            dry_run=True,
        )

    t0 = time.monotonic()
    total_cost_usd = 0.0
    total_turns = 0

    # See agents/reproducibility/agent.py for why the try/finally is
    # needed (SDK asyncgen cleanup on early break).
    stream = query(prompt=user_prompt, options=options)
    try:
        async for msg in stream:
            if isinstance(msg, AssistantMessage):
                total_turns += 1
            if isinstance(msg, ResultMessage):
                total_cost_usd = getattr(msg, "total_cost_usd", 0.0) or 0.0
                total_turns = getattr(msg, "num_turns", total_turns) or total_turns
                break
    finally:
        aclose = getattr(stream, "aclose", None)
        if aclose is not None:
            await aclose()

    duration_sec = time.monotonic() - t0
    _persist_scratchpad(findings_dir, scratchpad)

    artifact = _load_and_validate_artifact(findings_dir, report_id)
    return AgentBRunResult(
        report_id=report_id,
        findings_dir=findings_dir,
        artifact=artifact,
        scratchpad=scratchpad,
        total_cost_usd=total_cost_usd,
        total_turns=total_turns,
        duration_sec=duration_sec,
    )


def _persist_scratchpad(findings_dir: Path, scratchpad: list[str]) -> None:
    if not scratchpad:
        return
    (findings_dir / "B_think.txt").write_text(
        "\n\n---\n\n".join(scratchpad), encoding="utf-8"
    )


def _load_and_validate_artifact(
    findings_dir: Path, report_id: str
) -> RootCauseArtifact | None:
    path = findings_dir / "B_root_cause.json"
    if not path.exists():
        return None
    try:
        return RootCauseArtifact.model_validate_json(path.read_text())
    except Exception:
        return None
