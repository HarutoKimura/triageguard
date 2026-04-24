"""Agent C — Duplicate Detector: SDK orchestration.

Mirrors `agents.root_cause.agent` but with `WebFetch` access so the
sub-agent can query NVD and GHSA. No source clone is staged — Agent C
operates from `INPUT.md` + public advisory databases. The decision rule
lives in `.claude/prompts/agent-c-duplicate.md`.
"""

from __future__ import annotations

import json
import shutil
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

from agents.duplicate.prompt import load_system_prompt
from agents.duplicate.tools import make_emit_verdict, make_think
from orchestrator.findings import make_report_id, prepare_findings_dir
from orchestrator.schemas import DuplicateArtifact, InputMeta

EffortLiteral = Literal["low", "medium", "high", "max"]

REPO_ROOT = Path(__file__).resolve().parents[2]

MCP_SERVER_NAME = "agent_c"

ALLOWED_TOOLS: list[str] = [
    "Read",
    "Grep",
    "WebFetch",
    f"mcp__{MCP_SERVER_NAME}__think",
    f"mcp__{MCP_SERVER_NAME}__emit_verdict",
]

DEFAULT_BUDGET_USD = 3.0
DEFAULT_MAX_TURNS = 500
DEFAULT_MODEL = "claude-opus-4-7"
DEFAULT_EFFORT = "xhigh"


@dataclass
class AgentCRunResult:
    report_id: str
    findings_dir: Path
    artifact: DuplicateArtifact | None
    scratchpad: list[str] = field(default_factory=list)
    total_cost_usd: float = 0.0
    total_turns: int = 0
    duration_sec: float = 0.0
    dry_run: bool = False


def _stage_inputs(sample_dir: Path, findings_dir: Path) -> InputMeta:
    """Copy INPUT.md + INPUT_meta.json. No source clone needed for Agent C."""
    input_md = sample_dir / "INPUT.md"
    input_meta = sample_dir / "INPUT_meta.json"
    if not input_md.exists() or not input_meta.exists():
        raise FileNotFoundError(
            f"sample_dir {sample_dir} missing INPUT.md or INPUT_meta.json"
        )

    shutil.copy2(input_md, findings_dir / "INPUT.md")
    shutil.copy2(input_meta, findings_dir / "INPUT_meta.json")
    return InputMeta.model_validate_json((findings_dir / "INPUT_meta.json").read_text())


def _build_user_prompt(meta: InputMeta) -> str:
    return (
        "Determine whether this vulnerability report duplicates a publicly-"
        "known CVE.\n\n"
        "Files available:\n"
        "- `INPUT.md` — the report body as submitted (verbatim)\n"
        "- `INPUT_meta.json` — structured metadata about the target\n\n"
        "Target summary (from INPUT_meta.json):\n"
        f"- vendor/product: {meta.target.vendor} / {meta.target.product}\n"
        f"- repo: {meta.target.repo}\n"
        f"- claimed_tag: {meta.target.claimed_tag}\n"
        f"- claimed_cve: {meta.target.claimed_cve}\n"
        f"- bug_class: {meta.bug_class}\n\n"
        "Follow the procedure in your system prompt. Use WebFetch against "
        "the allowed hosts (NVD, api.github.com, wolfssl.com) only. Call "
        "`think` before the verdict. Call `emit_verdict` exactly once to finish."
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
        add_dirs=[str(REPO_ROOT)],
        max_turns=max_turns,
        max_budget_usd=budget_usd,
        model=model,
        effort=cast(EffortLiteral, effort),
        include_partial_messages=True,
    )


async def run_agent_c(
    *,
    sample_dir: Path,
    findings_root: Path = REPO_ROOT / "findings",
    report_id: str | None = None,
    budget_usd: float = DEFAULT_BUDGET_USD,
    max_turns: int = DEFAULT_MAX_TURNS,
    model: str = DEFAULT_MODEL,
    effort: str = DEFAULT_EFFORT,
    dry_run: bool = False,
) -> AgentCRunResult:
    """Run Agent C end-to-end against a recorded sample."""
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
    meta = _stage_inputs(sample_dir, findings_dir)
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
        return AgentCRunResult(
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
    return AgentCRunResult(
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
    (findings_dir / "C_think.txt").write_text(
        "\n\n---\n\n".join(scratchpad), encoding="utf-8"
    )


def _load_and_validate_artifact(
    findings_dir: Path, report_id: str
) -> DuplicateArtifact | None:
    path = findings_dir / "C_duplicate.json"
    if not path.exists():
        return None
    try:
        return DuplicateArtifact.model_validate_json(path.read_text())
    except Exception:
        return None
