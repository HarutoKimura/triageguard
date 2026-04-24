"""Load Agent A's system prompt from disk at runtime."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

PROMPT_PATH = (
    Path(__file__).resolve().parents[2]
    / ".claude"
    / "prompts"
    / "agent-a-reproducibility.md"
)


@lru_cache(maxsize=1)
def load_system_prompt() -> str:
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"agent A prompt not found at {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8")
