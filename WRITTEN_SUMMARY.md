# TriageGuard

**TriageGuard is an autonomous validator for vulnerability reports: drop in a report + PoC + claimed affected code, and it returns a Signal-vs-Slop verdict with auditable reasoning.**

The crisis: HackerOne paused the Internet Bug Bounty program on 2026-03-27; curl killed its bounty in January; OSS valid-submission rates fell from ~15% to under 5% as AI slop floods maintainers.

TriageGuard spawns four parallel Claude Opus 4.7 sub-agents: **Reproducibility** (builds + runs the PoC in an ASan sandbox), **Root Cause** (greps the claimed source), **Duplicate** (queries NVD/GHSA), and **Hallucination** (cites-or-rejects every concrete technical reference). A deterministic synthesizer maps their JSON artifacts to a 0–100 Signal Score.

Three Opus 4.7 capabilities, used concretely: **long-horizon autonomy** — Agent A clones, builds, runs the PoC, and parses sanitizer output in one ~10-minute uninterrupted run; **self-verification** — every agent's schema admits `failed_to_reproduce` / `file_not_found` / `unchecked`, and the synthesizer refuses to fabricate a score when any artifact is missing; **push-back** — Agent D cites or rejects, catching invented CVE IDs and phantom function names. Haiku 4.5 handles glue (input parsing, JSON coercion).

Builder: 9 credited CVEs across wolfSSL, NSS, and PowerDNS; I authored two of the three wolfSSL CVEs in the eval set.
