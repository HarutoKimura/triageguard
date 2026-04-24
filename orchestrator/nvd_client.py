"""On-disk, rate-limited cache in front of the NVD REST API.

Problem: Agent C and Agent D both query NVD (primarily via the
2.0 `services.nvd.nist.gov/rest/json/cves/2.0` endpoint). The default
anonymous rate limit is 5 requests per 30 seconds — a full six-sample
demo dry-run can trip it, especially if the demo-rehearser fans out.

Fix: read-through cache keyed by the exact request URL. Hits return
from disk instantly; misses hit NVD once, wait a polite cool-down, and
persist the response under `orchestrator/_cache/nvd/`. The cache
survives across processes and across dry-runs, so every repeated rehearsal
becomes effectively free.

NVD_API_KEY from the environment is passed as an `apiKey` header when
present — it lifts the rate limit to 50 / 30 s, ~10× the anonymous quota.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
from claude_agent_sdk import SdkMcpTool, tool

REPO_ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = REPO_ROOT / "orchestrator" / "_cache" / "nvd"

# NVD anonymous limit: 5 requests per 30s. With an API key: 50 / 30 s.
# Cooldown between misses is conservative by design — we would rather
# serialize than ever see a 429.
_ANON_COOLDOWN_SEC = 7.0
_KEYED_COOLDOWN_SEC = 1.0

# Cache entry lifetime. One week is plenty for hackathon-era CVE data;
# the CVE record itself rarely changes after publication.
_DEFAULT_TTL_SEC = 7 * 24 * 3600

# Shared across a process so concurrent agent calls don't double-fetch.
_GLOBAL_LOCK = asyncio.Lock()
_LAST_MISS_AT = 0.0


@dataclass(frozen=True)
class CacheEntry:
    status_code: int
    body: str
    fetched_at: float
    content_type: str


def _slug(url: str) -> str:
    """Stable filename for a URL — short hex prefix keeps the dir human-scannable."""
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
    return digest


def _cache_path(url: str) -> Path:
    return CACHE_ROOT / f"{_slug(url)}.json"


def _has_api_key() -> bool:
    return bool(os.environ.get("NVD_API_KEY", "").strip())


def _cooldown_sec() -> float:
    return _KEYED_COOLDOWN_SEC if _has_api_key() else _ANON_COOLDOWN_SEC


def _load_entry(path: Path, *, ttl_sec: float) -> CacheEntry | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    fetched_at = float(payload.get("fetched_at", 0.0))
    if time.time() - fetched_at > ttl_sec:
        return None
    return CacheEntry(
        status_code=int(payload.get("status_code", 0)),
        body=str(payload.get("body", "")),
        fetched_at=fetched_at,
        content_type=str(payload.get("content_type", "application/json")),
    )


def _store_entry(path: Path, entry: CacheEntry) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(
            {
                "status_code": entry.status_code,
                "body": entry.body,
                "fetched_at": entry.fetched_at,
                "content_type": entry.content_type,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    tmp.rename(path)


async def _respect_cooldown() -> None:
    """Ensure no two cache misses hit NVD closer than _cooldown_sec apart."""
    global _LAST_MISS_AT
    async with _GLOBAL_LOCK:
        now = time.monotonic()
        wait = (_LAST_MISS_AT + _cooldown_sec()) - now
        if wait > 0:
            await asyncio.sleep(wait)
        _LAST_MISS_AT = time.monotonic()


def is_nvd_url(url: str) -> bool:
    return "services.nvd.nist.gov" in url or "nvd.nist.gov/vuln/detail" in url


async def fetch_cached(
    url: str,
    *,
    ttl_sec: float = _DEFAULT_TTL_SEC,
    timeout_sec: float = 20.0,
) -> CacheEntry:
    """Read-through cache for NVD URLs. Raises on network error after retry.

    Cache hits skip rate limiting entirely. Misses respect a cooldown
    window so concurrent agents never double-hammer NVD. On HTTP 429
    we retry once after 30 s, respecting NVD's documented window.
    """
    if not is_nvd_url(url):
        raise ValueError(f"refusing to cache non-NVD url: {url}")

    path = _cache_path(url)
    cached = _load_entry(path, ttl_sec=ttl_sec)
    if cached is not None:
        return cached

    headers = {
        "User-Agent": "TriageGuard/0.1 (+github.com/HarutoKimura/triageguard)",
        "Accept": "application/json",
    }
    api_key = os.environ.get("NVD_API_KEY", "").strip()
    if api_key:
        headers["apiKey"] = api_key

    await _respect_cooldown()
    async with httpx.AsyncClient(timeout=timeout_sec) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 429:
            await asyncio.sleep(30.0)
            resp = await client.get(url, headers=headers)
        resp.raise_for_status()

    entry = CacheEntry(
        status_code=resp.status_code,
        body=resp.text,
        fetched_at=time.time(),
        content_type=resp.headers.get("content-type", "application/json"),
    )
    _store_entry(path, entry)
    return entry


# ---------------------------------------------------------------------------
# MCP tool shared by Agent C (duplicate) and Agent D (hallucination).
# ---------------------------------------------------------------------------


NVD_FETCH_SCHEMA: dict[str, type] = {"url": str}


def make_nvd_fetch(*, cache_hits: list[str], cache_misses: list[str]) -> SdkMcpTool[dict[str, str]]:
    """MCP tool that reads NVD through the on-disk cache.

    Both Agent C and Agent D call this instead of WebFetch when they
    need to query NVD. The two lists let the agent's wrapper log
    cache-hit/miss counts for post-run debugging without changing the
    agent's prompt.
    """

    @tool(
        "nvd_fetch",
        (
            "Fetch a URL on services.nvd.nist.gov through the on-disk cache. "
            "Use this INSTEAD OF WebFetch for any NVD query (e.g. "
            "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-XXXX-YYYY). "
            "Cached responses return instantly; first-time queries respect "
            "NVD's 5-req/30-s anonymous limit. Returns the raw JSON body as text. "
            "If the URL is not on NVD, this tool refuses — use WebFetch for "
            "GHSA, vendor advisory pages, etc."
        ),
        NVD_FETCH_SCHEMA,
    )
    async def _nvd_fetch(args: dict[str, str]) -> dict[str, object]:
        url = args.get("url", "").strip()
        if not url:
            return {
                "content": [{"type": "text", "text": "url is required"}],
                "is_error": True,
            }
        if not is_nvd_url(url):
            msg = (
                f"nvd_fetch refused: {url!r} is not an NVD URL. "
                "Use WebFetch for other hosts."
            )
            return {
                "content": [{"type": "text", "text": msg}],
                "is_error": True,
            }
        path = _cache_path(url)
        was_cached = path.exists() and _load_entry(path, ttl_sec=_DEFAULT_TTL_SEC) is not None
        try:
            entry = await fetch_cached(url)
        except httpx.HTTPError as exc:
            err = f"nvd_fetch network error: {type(exc).__name__}: {exc}"
            return {
                "content": [{"type": "text", "text": err}],
                "is_error": True,
            }
        (cache_hits if was_cached else cache_misses).append(url)
        prefix = "[cache-hit] " if was_cached else "[cache-miss] "
        return {"content": [{"type": "text", "text": prefix + entry.body}]}

    return _nvd_fetch
