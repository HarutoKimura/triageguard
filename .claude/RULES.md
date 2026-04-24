# TriageGuard Operating Rules

Distilled from: Anthropic engineering blog posts, cc-crossbeam (past
hackathon winner), Claude Code docs, and the three hackathon live sessions
(Kickoff, Session 1 with Tariq, Session 2 with Michael Cohen). Every rule
has a source. Read this once before starting a session.

---

## 0 · North Star

Boris Cherny (Kickoff): **"If it's easier to demo than to explain, you're
on the right track."** The judges watch the 3-minute video first. Every
decision must make that video tighter.

Four axes, exact weights:

| Axis | Weight | What wins |
|------|--------|-----------|
| Impact | 30% | Real OSS maintainer pain, credible framing |
| Demo | 25% | Works live, cool to watch, self-explanatory |
| Opus 4.7 Use | 20% | Long-horizon autonomy, self-verification, pushes back |
| Depth & Execution | 20% | Real craft, wrestled with, not a quick hack |

Everything in this repo must optimize one of these axes. If it does not,
delete it.

---

## 1 · Build discipline (2 days remaining)

Today is 2026-04-24. Submission is 2026-04-26, 20:00 EST. That is
**~44 hours**. Apply in this order:

1. **Vertical slice first, breadth later.** One sample end-to-end beats
   four samples half-finished. Target: Sample 1 (real wolfSSL CVE) runs
   through Agent A and prints a verdict by end of Day 1.
2. **No premature parallelism.** Get one sub-agent working synchronously
   first. Parallelize in asyncio only after the single-agent path is
   green. (Agent SDK learning from cc-crossbeam: `for await (msg) break
   on result` — do not let loops drain budget.)
3. **Cut by default.** Prefer `/simplify` thinking over scaffolding.
   Before adding a file, ask: "does this change the 3-minute demo?" If
   no, do not add it.
4. **Test ladder (cc-crossbeam L0–L4).** Run cheap checks before expensive
   ones:
   - L0: Claude reads FINDINGS.md schema. 10s, ~$0.10.
   - L1: One sub-agent on one sample. ~$1, 1 min.
   - L2: All four sub-agents on one sample. ~$3, 5 min.
   - L3: Full synthesizer over six samples. ~$8, 12 min.
   - L4: Full UI run recorded for the demo video. Only at end.
5. **Budget tripling.** Whatever you estimate a test will cost, assume
   3× in practice. Reserve $80 headroom before submission.

---

## 2 · The six demo samples are sacred

They are the evaluation set. Do not change them mid-build.

| # | Input | Expected | Why this sample |
|---|-------|----------|-----------------|
| 1 | CVE-2026-3849 (wolfSSL HPKE/ECH stack overflow) | SIGNAL ~90 | Builder's sole-credit CVE, full PoC + ASan trace — live demo credibility |
| 2 | CVE-2026-2646 (wolfSSL session deserialization) | SIGNAL ~85 | Builder's own CVE, different bug class (heap vs stack) |
| 3 | CVE-2026-5194 (wolfSSL ECDSA bypass, Carlini/Anthropic) | SIGNAL ~90 | Parallel to Anthropic Frontier Red Team, pitch lands |
| 4 | Public HackerOne curl slop #1 | SLOP <25 | Negative example, broad recognition |
| 5 | Public HackerOne curl slop #2 | SLOP <25 | Negative example, different slop pattern |
| 6 | Live-generated GPT-4o slop at demo time | SLOP <25 | Demo theater: "we made this 30 seconds ago" |

If a sample won't run, fix the sample, not the rubric.

---

## 3 · Opus 4.7 — exploit what changed

Boris (Kickoff): **"4.7 is a giant step up. However, if you use it the
same way that you used 4.6, you won't feel that step up."**

Four capabilities to visibly exploit:

1. **Long-horizon autonomy.** Agent A clones, builds, runs PoC, checks
   output — 10–15 min of uninterrupted work. Do not babysit.
2. **Self-verification / honest failure.** Agent A *must* say "could not
   reproduce" when it cannot. This is the product's entire thesis. Do
   not write a fallback that "tries harder" — let it fail honestly.
3. **Pushes back.** Agent D (Hallucination) refuses to confirm plausible
   prose without evidence. Prompt it to *cite or reject*.
4. **Precise instruction following.** Tariq (Session 1): "Opus 4.7 takes
   instructions more literally. If it's over-triggering, give it more
   flexibility." Sub-agent prompts should be short and explicit; do not
   over-constrain.

Effort levels: **xhigh for all four sub-agents + synthesizer. Haiku 4.5
for glue** (file parsing, schema coercion, JSON extraction). Model
split is mentioned explicitly in the pitch — it is a signal of depth.

---

## 4 · Sub-agent architecture (copy cc-crossbeam patterns)

Four parallel sub-agents, one synthesizer, file-based handoff. Do NOT
have the orchestrator pass raw sub-agent transcripts into the
synthesizer's context. Each sub-agent writes a structured artifact:

```
findings/{report_id}/
  A_reproducibility.json   # {verdict, evidence, build_log_tail}
  B_root_cause.json        # {match_status, file, line, snippet}
  C_duplicate.json         # {verdict, matched_cve, similarity}
  D_hallucination.json     # {invalid_refs: [...], verified_refs: [...]}
  SYNTHESIS.md             # human-readable final verdict
```

The synthesizer reads only these five files. This mirrors crossbeam's
`session/*.json` pattern. It also mirrors Anthropic's multi-agent
research system post: *"separation of concerns — the detailed search
context remains isolated within sub-agents, while the lead agent
focuses on synthesizing."*

**Naming flexibility**: cc-crossbeam's bitter learning — sub-agents
ignore exact filenames. Validate with multiple accepted names:

```python
REPRO_NAMES = ["A_reproducibility.json", "agent_a.json", "reproducibility.json"]
```

**Flush wait**: crossbeam also learned that files may not be visible
immediately after an agent claims success. `await asyncio.sleep(2)`
before reading.

---

## 5 · Agent SDK — non-negotiable patterns

From cc-crossbeam + Agent SDK docs:

1. **`settingSources: ['project']`** — required for skill discovery.
2. **`maxTurns: 500`** — sandbox + tool logging burns turns fast.
3. **`maxBudgetUsd` per run** — hard cap. Set $5 per sub-agent, $20 orchestrator.
4. **`includePartialMessages: true`** — required for SSE streaming to UI.
5. **`additionalDirectories`** — sub-agents need read access to test-assets/.
6. **Break on result**:
   ```python
   async for msg in query:
       if msg.type == "result":
           break  # SDK keeps yielding follow-ups that burn budget
   ```
7. **`detached: true` for long-running sandboxed work**. HTTP streaming
   dies at ~5 min (crossbeam's biggest bug). Use detached + poll.

---

## 6 · Context engineering

From Anthropic's context-engineering blog and multi-agent research post:

1. **Always-on context** (in CLAUDE.md / skill frontmatter):
   - Signal Score rubric
   - The six sample IDs and expected verdicts
   - FINDINGS.md schema
2. **Just-in-time context** (via tool calls):
   - Fetching vulnerability report body
   - Cloning wolfSSL source
   - NVD advisory lookups
3. **Handoff context** (files, not chat):
   - FINDINGS/*.json per sub-agent
   - SYNTHESIS.md as final artifact
4. **Think tool**: each sub-agent gets a `think` tool (scratchpad, no
   side effects). Required before finalizing a verdict. From Anthropic's
   think-tool post: policy compliance went 37% → 57% on τ-Bench.

---

## 7 · Verify before claiming done

The product's value proposition is honest failure. The build rules mirror it:

1. If a build succeeds, rerun it. Print the output.
2. If a test passes, save the log to `logs/`.
3. Never mark a task complete because it *looked* right. Run it.
4. If data is not available, say so. Do not synthesize a placeholder.
5. No inventing APIs. Every `anthropic`, `claude_agent_sdk`, `wolfssl`
   function call must be verifiable in docs or source. If unsure, stop
   and grep.

This is the `/verify-done` command's checklist. Run it before every
commit.

---

## 8 · Demo craft (25% of the score)

Tariq (Session 1): Remotion + design-system-in-HTML produces video
quality that competitors will not match with plain screencapture.
Michael Cohen (Session 2): verbose agent-thinking logs in the UI —
"intentionally very techie and verbose" — lets judges see the model
working.

For the 3-minute video:

| Time | Shot | Purpose |
|------|------|---------|
| 0:00–0:20 | Problem statement with IBB pause headline | Impact framing |
| 0:20–0:50 | Upload real CVE-2026-2646 → sub-agents spawn → SIGNAL 85 | Demo |
| 0:50–1:30 | Upload public curl slop → sub-agents spawn → SLOP 12 | Demo, negative case |
| 1:30–2:00 | "Let's generate fresh slop with GPT-4o right now" → SLOP <20 | Theatrical, memorable |
| 2:00–2:30 | Architecture card: 4 parallel Opus 4.7 sub-agents + synthesizer | Opus 4.7 Use |
| 2:30–3:00 | Pitch close: "I helped create this crisis, TriageGuard is my contribution" | Impact + credibility |

Record at 1080p60. Export via Remotion. No live camera. No music
louder than narration.

---

## 9 · Written summary (100–200 words)

Ivan (Kickoff): *"Please make sure to describe exactly how you used
Claude, how those managed agents worked, because that is what will be
graded on alongside the code."*

Structure:
1. One-sentence product description
2. The crisis (one sentence, with a date or number)
3. The four sub-agents, named, in one sentence
4. Three Opus 4.7 capabilities used, with concrete hooks
5. Builder credibility (9 CVEs, wolfSSL, NSS, PowerDNS)

Draft lives in `WRITTEN_SUMMARY.md`. Freeze on 2026-04-26 18:00 EST.

---

## 10 · Red flags — things that lose points

Directly quoted from live sessions:

- Tariq (Session 1): **"If you have a lot of instructions for the
  agent, you sort of over-constrain Claude."** Do not write 500-line
  sub-agent prompts. Give tools, let Opus decide.
- Tariq (Session 1): **"Claude.md can conflict with skills... making
  sure that Claude, if you give it conflicting information, tends to
  do different things."** Audit every session for drift.
- Boris (Kickoff): **"Don't put Claude in a place where it can't make
  any mistakes... you want to be able to let it iterate."** Do not
  over-fence the sub-agents.
- Michael (Session 2): stubbed endpoints that "don't work" sink demos.
  Wire every button to real output before Day 3.
- Real-time data flow is NOT Claude Code's strength. For TriageGuard
  that's fine — reports come in async.

---

## 11 · When you're stuck

1. Open `.claude/skills/opus-4.7-playbook/SKILL.md` and re-read the
   "adaptive thinking" section — prompt Claude to think harder.
2. Run `/simplify` on the last file you touched.
3. Ask: "what's the smallest demo that still closes the 3-minute video?"
   Cut to that.
4. Commit whatever works. Push. Take a 15-minute break. Return.

The bug bounty ecosystem is watching. Ship something honest.
