---
name: wolfssl-domain
description: Domain knowledge for running, building, and reasoning about wolfSSL — the primary TriageGuard target. Use whenever the task involves wolfSSL source, CVE claims against wolfSSL, sandboxed builds, PoC execution, or the three real wolfSSL CVEs in the demo set (2026-2646, 2026-3849, 2026-5194).
---

# wolfSSL Domain Skill

This skill is Agent A's (Reproducibility) home turf and Agent B's
(Root Cause) reference. Load it before touching wolfSSL source.

---

## 1 · Project facts

- **Language**: C (C89 with optional C99)
- **Build system**: autotools (`./autogen.sh && ./configure && make`) and CMake
- **License**: GPL-2.0-or-later (commercial alternatives available)
- **Upstream**: https://github.com/wolfSSL/wolfssl
- **Mirror of advisories**: https://www.wolfssl.com/docs/security-vulnerabilities/
- **Typical footprint**: 20–100 KB built for embedded; ~5 B devices shipping

wolfSSL's code style is defensive and verbose. Functions are often
1000+ lines; macros hide version conditionals. Be suspicious of any
report that quotes a "function at line 42" — wolfSSL rarely has short
functions.

---

## 2 · Common build configurations (pick one per CVE)

| Configure flags | Why |
|-----------------|-----|
| `--enable-all` | Broadest attack surface; default for fuzzing |
| `--enable-session-ticket --enable-tls13` | For session-resumption CVEs |
| `--enable-hpke --enable-ech` | For HPKE/ECH class (CVE-2026-3849) |
| `--enable-ecc --enable-ecdsa` | For ECDSA class (CVE-2026-5194) |
| `--enable-asan` | ASan build for heap corruption detection |
| `--enable-debug` | Symbols + no inlining for gdb |

Always add `CFLAGS="-O0 -g -fsanitize=address"` when a CVE claims a
memory bug. Without ASan, a real overflow may not crash.

---

## 3 · Canonical build recipe (wolfSSL inside Docker)

```dockerfile
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y \
    build-essential autoconf automake libtool pkg-config \
    git ca-certificates \
    clang llvm \
    gdb valgrind \
    libssl-dev \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /src
RUN git clone --depth=1 https://github.com/wolfSSL/wolfssl.git
WORKDIR /src/wolfssl
ARG WOLFSSL_TAG=v5.7.6-stable
RUN git fetch --depth=1 origin tag ${WOLFSSL_TAG} && git checkout ${WOLFSSL_TAG}
RUN ./autogen.sh
# Flags filled in by the specific CVE's recipe
ARG CONFIGURE_FLAGS="--enable-all --enable-debug"
RUN CC=clang CFLAGS="-O0 -g -fsanitize=address -fno-omit-frame-pointer" \
    LDFLAGS="-fsanitize=address" \
    ./configure ${CONFIGURE_FLAGS}
RUN make -j"$(nproc)"
```

Pin to a specific tag. Do not build from `master` — the CVE may already
be patched.

---

## 4 · The three real CVEs (demo samples 1–3)

### Sample 1 — CVE-2026-2646 (builder's own CVE)

- **Class**: Heap-based buffer overflow on session deserialization
- **Vulnerable function**: `wolfSSL_d2i_SSL_SESSION` in `src/ssl.c`
- **Trigger**: Malformed session ticket passed to `d2i_SSL_SESSION`
- **Build flags**: `--enable-all --enable-session-ticket`
- **PoC language**: C + provided session blob
- **Expected crash**: ASan heap-buffer-overflow in `XMEMCPY` called from
  `wolfSSL_d2i_SSL_SESSION`
- **Pre-fix tag**: choose the tag listed in the report (check the
  report body; do not hardcode here, as the report provides it)

### Sample 2 — CVE-2026-3849 (builder's own CVE)

- **Class**: Stack buffer overflow in HPKE/ECH handling
- **Vulnerable function**: HPKE context-copy in ECH acceptance path
- **Build flags**: `--enable-hpke --enable-ech --enable-tls13`
- **Expected crash**: ASan stack-buffer-overflow during ECH handshake

### Sample 3 — CVE-2026-5194 (Anthropic's Carlini)

- **Class**: ECDSA signature validation bypass
- **Note**: Not a memory-corruption bug. Reproducibility is measured by
  the PoC producing a valid-looking signature that should have been
  rejected. Agent A must not look for an ASan crash — absence of
  rejection *is* the vulnerability.
- **Build flags**: `--enable-ecc --enable-ecdsa`
- **This is a critical anti-pattern case** — use it to test that
  Agent A does not over-fit on "crash = signal".

---

## 5 · Fast source-navigation tips (for Agent B)

wolfSSL's function names follow conventions. Agent B can use these to
reality-check a report's claimed function:

- `wolfSSL_*` / `SSL_*` — public OpenSSL-compatible API
- `wolf_*` — internal helpers
- `wc_*` — wolfCrypt (primitives)
- `*_ex` suffix — extended variant
- No function starts with `parse_` at the top level; reports that cite
  `parse_header` are almost certainly fabricated.

Useful commands:

```bash
# Is the function real?
git grep -n "^[A-Za-z_ *]* wolfSSL_d2i_SSL_SESSION" -- '*.c'

# Every definition (not declaration)
ctags -x --c-kinds=f src/ssl.c | grep wolfSSL_d2i_SSL_SESSION

# What CVEs reference this file historically?
git log --all --oneline -- src/ssl.c | grep -iE 'cve|security'
```

---

## 6 · Signals of slop specific to wolfSSL

Agent D looks for these patterns:

1. **Claims against `ssl.c` lines that don't exist**. wolfSSL's `ssl.c`
   is ~18k lines; LLMs hallucinate specific line numbers frequently.
2. **Non-existent configure flags**. `--enable-tls15`, `--enable-safe-mode`,
   `--disable-heap-overflow` are all fake.
3. **OpenSSL-only APIs**. Reports citing `EVP_PKEY_ctx_new_from_pkey`
   as if it exists in wolfSSL. wolfSSL has a compatibility layer but
   not all OpenSSL APIs.
4. **CVE IDs that don't exist in NVD**. Always verify with
   `https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-XXXX-YYYY`
5. **CVSS vectors that don't parse**. Use
   `https://www.first.org/cvss/calculator/3-1` format; reports citing
   `AV:X/Y` garbage are a cheap tell.

---

## 7 · Sandboxing (Agent A)

Run every build and PoC inside a disposable Docker container. Never
execute an untrusted PoC on the host. Kill the container after the run;
do not reuse.

```bash
docker run --rm --network=none \
  --cpus=2 --memory=2g --pids-limit=256 \
  --read-only --tmpfs /tmp --tmpfs /src/wolfssl/build-tmp \
  triageguard/wolfssl:${WOLFSSL_TAG} \
  timeout 600 ./poc_runner.sh
```

- `--network=none` — PoCs don't need the network; blocks exfiltration.
- `--read-only` with tmpfs writes — contains any filesystem damage.
- `timeout 600` — PoC is allowed 10 minutes; Agent A has an upper bound.

---

## 8 · When wolfSSL isn't buildable

If the build fails *for reasons unrelated to the CVE* (missing dep,
broken tag), Agent A must say so. Do not auto-patch. A build failure
against the claimed vulnerable tag is itself diagnostic evidence —
Agent B will correlate it with "claim cites stale code".

Verdict string convention:

- `reproduced` — build OK, PoC triggers claimed behavior
- `failed_to_reproduce` — build OK, PoC runs but behavior not observed
- `build_error` — could not build the claimed tag; include `error.tail`
- `no_poc` — report did not include a PoC
