"""Generate an AI-written slop vulnerability report for curl.

Produces TriageGuard SLOP evaluation samples (s4, s5) and the live demo
"we made this 30 seconds ago" sample (s6). The generator intentionally
asks the model to fabricate specific function names, file paths, and
line numbers — which Agent D is designed to catch, and which drive the
synthesizer to rule 2 or rule 4 (SLOP 15–20).

Why AI-generated rather than scraped from HackerOne: the H1 hackers
API gates `vulnerability_information` on report-participant scope, so
we cannot retrieve the verbatim body of a public curl "not-applicable"
disclosure. AI-generated slop is the same thing maintainers actually
drown in today — Daniel Stenberg's Jan 2024 blog post describes exactly
these patterns — so synthesizing it is substantively honest, not a
workaround for convenience.

Usage:

    python scripts/generate_slop.py \\
        --output-dir demo-inputs/s4-curl-slop-1 \\
        --variation buffer_overflow \\
        --seed 4001

Omit `--seed` (or pass a different one) for s6 to get fresh slop per
demo take. Override the model via `OAI_MODEL` env var or `--model`.

Env:
    OPENAI_API_KEY     (required)
    OAI_MODEL          (optional; overrides --model default)
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from datetime import UTC, datetime
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

VARIATIONS: dict[str, dict[str, str]] = {
    "buffer_overflow": {
        "bug_class": "buffer_overflow",
        "lede": (
            "Stack buffer overflow in curl's HTTP header parsing when "
            "processing an oversized Content-Type header, triggered from "
            "curl_easy_perform() on the client side."
        ),
    },
    "use_after_free": {
        "bug_class": "use_after_free",
        "lede": (
            "Use-after-free in curl's connection cache during parallel "
            "multi-handle transfers, reachable from curl_multi_perform() "
            "when a connection is evicted mid-request."
        ),
    },
    "sig_bypass": {
        "bug_class": "signature_bypass",
        "lede": (
            "TLS certificate verification bypass in curl when processing a "
            "malformed SNI extension on 307 redirect chains, allowing "
            "man-in-the-middle attackers to impersonate any HTTPS origin."
        ),
    },
    "rce": {
        "bug_class": "command_injection",
        "lede": (
            "Remote code execution in curl via unsanitised URL parser when "
            "processing shell metacharacters in the user:password@host "
            "field, reachable with default build options."
        ),
    },
}

SYSTEM_PROMPT = (
    "You are a security researcher drafting a vulnerability report for "
    "the curl HTTP library project. Produce a plausible, detailed "
    "security advisory that looks professional but will contain "
    "technical inaccuracies typical of AI-written reports (fabricated "
    "function names, drifted line numbers, wrong file paths).\n\n"
    "Constraints:\n"
    "- Output ONLY the report body. No meta-commentary.\n"
    "- Length: 400-700 words.\n"
    "- Include sections: Summary, Affected Component, Root Cause "
    "Analysis, Exploitation Path, Impact, Suggested Fix.\n"
    "- Cite SPECIFIC function names from curl (e.g. curl_easy_perform, "
    "Curl_connect). It is acceptable to reference auxiliary helpers "
    "that may not exist.\n"
    "- Cite SPECIFIC file paths like lib/http.c, lib/url.c, lib/tls.c "
    "with line numbers.\n"
    "- Include a claimed CVSS 3.1 vector with score >= 7.5.\n"
    "- Do NOT include a working PoC (no compilable C code); a "
    "natural-language attack description is enough.\n"
    "- Target: curl 8.6.0 (tag curl-8_6_0)."
)


def build_user_prompt(variation: str) -> str:
    v = VARIATIONS[variation]
    return (
        f"Lede: {v['lede']}\n\n"
        "Write the full advisory now. Prefix with a title line "
        "(e.g. `# <title>`)."
    )


def generate(*, model: str, variation: str, seed: int | None, temperature: float) -> str:
    client = OpenAI()
    kwargs: dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(variation)},
        ],
    }
    if seed is not None:
        kwargs["seed"] = seed
    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


def write_sample(
    *,
    output_dir: pathlib.Path,
    sample_id: str,
    body: str,
    variation: str,
    model: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "INPUT.md").write_text(body, encoding="utf-8")
    meta: dict[str, Any] = {
        "sample_id": sample_id,
        "submitter": f"AI-generated slop (model={model})",
        "target": {
            "vendor": "curl",
            "product": "curl",
            "repo": "https://github.com/curl/curl",
            "claimed_tag": "curl-8_6_0",
            "claimed_cve": None,
        },
        "bug_class": VARIATIONS[variation]["bug_class"],
        "poc": {"present": False, "path": None, "entry": None},
        "submitted_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "expected": {
            "label": "SLOP",
            "score_min": 10,
            "score_max": 25,
            "triggering_rule_hint": 2,
        },
    }
    (output_dir / "INPUT_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    load_dotenv(".env")
    p = argparse.ArgumentParser(prog="generate_slop")
    p.add_argument(
        "--output-dir",
        type=pathlib.Path,
        required=True,
        help="e.g. demo-inputs/s4-curl-slop-1",
    )
    p.add_argument("--variation", choices=sorted(VARIATIONS), required=True)
    p.add_argument("--model", default=os.environ.get("OAI_MODEL", "gpt-4o"))
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="for reproducible slop (e.g. 4001 for s4); omit for live demo",
    )
    p.add_argument("--temperature", type=float, default=0.7)
    args = p.parse_args(argv)

    body = generate(
        model=args.model,
        variation=args.variation,
        seed=args.seed,
        temperature=args.temperature,
    )
    sample_id = args.output_dir.name
    write_sample(
        output_dir=args.output_dir,
        sample_id=sample_id,
        body=body,
        variation=args.variation,
        model=args.model,
    )
    print(f"Generated {sample_id}: {len(body)} chars via {args.model}")
    print(f"Run: .venv/bin/python -m orchestrator {args.output_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
