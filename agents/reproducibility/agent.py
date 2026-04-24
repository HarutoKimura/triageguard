"""Agent A — Reproducibility Verifier: SDK orchestration.

Spawns a Claude Agent SDK query with the Agent A system prompt, the
custom `think` + `emit_verdict` tools, and the six load-bearing knobs
from `.claude/skills/agent-sdk-patterns/SKILL.md §1`. Streams messages,
breaks on `ResultMessage` (crossbeam's bitter lesson), writes the
scratchpad sidecar, and validates that the sub-agent produced a
schema-conformant verdict.

The public entry point is `run_agent_a`. The CLI wrapper lives in
`agents.reproducibility.cli`.
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

from agents.reproducibility.prompt import load_system_prompt
from agents.reproducibility.tools import make_emit_verdict, make_think
from orchestrator.findings import make_report_id, prepare_findings_dir
from orchestrator.schemas import InputMeta, ReproducibilityArtifact

EffortLiteral = Literal["low", "medium", "high", "max"]

REPO_ROOT = Path(__file__).resolve().parents[2]

MCP_SERVER_NAME = "agent_a"

ALLOWED_TOOLS: list[str] = [
    "Bash",
    "Read",
    "Write",
    "Grep",
    f"mcp__{MCP_SERVER_NAME}__think",
    f"mcp__{MCP_SERVER_NAME}__emit_verdict",
]

DEFAULT_BUDGET_USD = 8.0
DEFAULT_MAX_TURNS = 500
DEFAULT_MODEL = "claude-opus-4-7"
DEFAULT_EFFORT = "xhigh"


@dataclass
class AgentARunResult:
    report_id: str
    findings_dir: Path
    artifact: ReproducibilityArtifact | None
    scratchpad: list[str] = field(default_factory=list)
    total_cost_usd: float = 0.0
    total_turns: int = 0
    duration_sec: float = 0.0
    dry_run: bool = False


def _stage_inputs(sample_dir: Path, findings_dir: Path) -> InputMeta:
    """Copy INPUT.md + INPUT_meta.json (and poc/ if present) into the findings dir.

    Returns the parsed InputMeta — used to compute the report id and to
    render a brief at the top of the user prompt.
    """
    input_md = sample_dir / "INPUT.md"
    input_meta = sample_dir / "INPUT_meta.json"
    if not input_md.exists() or not input_meta.exists():
        raise FileNotFoundError(
            f"sample_dir {sample_dir} missing INPUT.md or INPUT_meta.json"
        )

    shutil.copy2(input_md, findings_dir / "INPUT.md")
    shutil.copy2(input_meta, findings_dir / "INPUT_meta.json")

    poc_src = sample_dir / "poc"
    if poc_src.is_dir():
        shutil.copytree(poc_src, findings_dir / "poc", dirs_exist_ok=True)

    meta = InputMeta.model_validate_json((findings_dir / "INPUT_meta.json").read_text())
    return meta


def _build_user_prompt(meta: InputMeta) -> str:
    poc_line = (
        f"- PoC present, entry: {meta.poc.entry}"
        if meta.poc.present and meta.poc.entry
        else "- PoC: none provided (call emit_verdict with verdict=no_poc)"
    )
    sandbox_image = f"triageguard/wolfssl:{meta.target.claimed_tag}"
    return (
        "Evaluate the vulnerability report in your current working directory.\n\n"
        "Files available:\n"
        "- `INPUT.md` — the report body as submitted (verbatim)\n"
        "- `INPUT_meta.json` — structured metadata about the target\n"
        f"- `poc/` — the reproduction assets (if poc.present)\n\n"
        "Target summary (from INPUT_meta.json):\n"
        f"- vendor/product: {meta.target.vendor} / {meta.target.product}\n"
        f"- repo: {meta.target.repo}\n"
        f"- claimed_tag: {meta.target.claimed_tag}\n"
        f"- claimed_cve: {meta.target.claimed_cve}\n"
        f"- bug_class: {meta.bug_class}\n"
        f"{poc_line}\n\n"
        "Sandbox:\n"
        f"- A pre-built Docker image `{sandbox_image}` is available. It has wolfSSL "
        "configured at the claimed tag with ASan (gcc libasan), static-linked, at "
        "`/src/wolfssl`. Do NOT rebuild wolfSSL from scratch — use this image to "
        "compile and run the PoC.\n"
        "- Run the PoC inside a container with: `docker run --rm --network=none "
        "--cpus=2 --memory=2g --read-only --tmpfs /tmp --tmpfs /work/scratch "
        f"-v $(pwd):/work:ro {sandbox_image} timeout 600 bash -c '<commands>'`\n\n"
        "Follow the procedure in your system prompt. Use `think` before the verdict. "
        "Call `emit_verdict` exactly once to finish."
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
        # The SDK's type stub accepts low|medium|high|max, but the
        # Anthropic API (and CLI) also accept "xhigh" — we forward the
        # string verbatim. See opus-4.7-playbook §2.
        effort=cast(EffortLiteral, effort),
        include_partial_messages=True,
    )


async def run_agent_a(
    *,
    sample_dir: Path,
    findings_root: Path = REPO_ROOT / "findings",
    report_id: str | None = None,
    budget_usd: float = DEFAULT_BUDGET_USD,
    max_turns: int = DEFAULT_MAX_TURNS,
    model: str = DEFAULT_MODEL,
    effort: str = DEFAULT_EFFORT,
    dry_run: bool = False,
) -> AgentARunResult:
    """Run Agent A end-to-end against a recorded sample.

    1. Creates `findings_root/{report_id}/`, stages INPUT files + poc/.
    2. Constructs the SDK options with system prompt + custom tools.
    3. If `dry_run`, returns after staging (no API call).
    4. Otherwise streams the Agent SDK query, breaks on `ResultMessage`,
       and verifies that `A_reproducibility.json` was written.
    """
    sample_dir = sample_dir.resolve()
    if not sample_dir.is_dir():
        raise FileNotFoundError(f"sample_dir not found: {sample_dir}")

    if report_id is None:
        meta_text = (sample_dir / "INPUT_meta.json").read_text()
        meta_preview = json.loads(meta_text)
        report_id = make_report_id(meta_preview.get("sample_id", "unnamed"))

    findings_dir = prepare_findings_dir(findings_root, report_id)
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
        return AgentARunResult(
            report_id=report_id,
            findings_dir=findings_dir,
            artifact=None,
            scratchpad=scratchpad,
            dry_run=True,
        )

    t0 = time.monotonic()
    total_cost_usd = 0.0
    total_turns = 0

    # try/finally ensures the SDK's underlying asyncgen is closed when
    # we break out early on ResultMessage. Without this, the interpreter
    # teardown raises "aclose(): asynchronous generator is already
    # running". `query()` is typed as AsyncIterator but the runtime
    # object is a generator with aclose — call it defensively.
    stream = query(prompt=user_prompt, options=options)
    try:
        async for msg in stream:
            if isinstance(msg, AssistantMessage):
                total_turns += 1
            if isinstance(msg, ResultMessage):
                total_cost_usd = getattr(msg, "total_cost_usd", 0.0) or 0.0
                total_turns = getattr(msg, "num_turns", total_turns) or total_turns
                break  # SDK yields follow-ups that drain budget — crossbeam lesson
    finally:
        aclose = getattr(stream, "aclose", None)
        if aclose is not None:
            await aclose()

    duration_sec = time.monotonic() - t0
    _persist_scratchpad(findings_dir, scratchpad)

    artifact = _load_and_validate_artifact(findings_dir, report_id)
    return AgentARunResult(
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
    (findings_dir / "A_think.txt").write_text(
        "\n\n---\n\n".join(scratchpad), encoding="utf-8"
    )


def _load_and_validate_artifact(
    findings_dir: Path, report_id: str
) -> ReproducibilityArtifact | None:
    path = findings_dir / "A_reproducibility.json"
    if not path.exists():
        return None
    try:
        return ReproducibilityArtifact.model_validate_json(path.read_text())
    except Exception:
        return None
