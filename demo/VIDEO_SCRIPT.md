# TriageGuard — 3-Minute Submission Video Script

**Hackathon:** Built with Opus 4.7 (Anthropic) — submission deadline
Sunday 2026-04-26, 8 PM EST.
**Builder:** Haruto Kimura (Stella LLC, Tokyo).
**Target length:** 180 seconds (9 pods × 20 s).
**Tone:** warm, sincere, first-person. Mike Brown style. Short
sentences (5–12 words). Let visuals breathe. Trust the accent.
**Narrative arc:** *I am a hunter → the industry is breaking → I am
one of those breaking it → so I built this → watch it work, three
verdicts → here is why Opus 4.7 → I owed them this.*

**Source interview:** [`INTERVIEW_2026-04-25.md`](./INTERVIEW_2026-04-25.md)

---

## Production constants

| Item | Value |
|---|---|
| Hero numbers (must be spoken aloud) | **9 CVEs**, **100+ reports**, **2 months**, **$65K**, **March 27, 2026**, **5%** (submission rate) |
| Author profile shown | Name + 9 CVEs + "founder of Stella LLC" — one chyron, ~3 s |
| Lilith naming | **Do NOT name Lilith.** Say "my AI pipeline" / "I use AI to hunt vulnerabilities" |
| OSS targets to logo-flash | wolfSSL, Mozilla NSS, PowerDNS |
| Demo samples (FINAL) | **s1 SIGNAL 90 · s4 SLOP 15 · s2 UNCERTAIN 50** — three verdict buckets, all live-verified |
| Capture | localhost:3100 web UI; no terminal split needed (was for the rejected GPT-4o pod) |

---

## Pod 1 — Hook & Self-Intro (0:00–0:30)

**Main point:** Establish who I am — bug-bounty hunter with
verifiable, recent receipts. Visuals lead the proof; voice-over
narrates over them.

**Visual timeline (already cut on the editor):**

| Time | Clip | Purpose |
|---|---|---|
| 0:00–0:10 | `pod1.MOV` (face, half-frame) | Self-intro to camera |
| 0:10–0:14 | `doing-bug-hunt.MOV` (B-roll) | "I do this every day" |
| 0:14–0:17 | `typing-on-editor.MOV` (B-roll) | Hands on keyboard, source on screen |
| 0:17–0:24 | `intigriti-payout-page.png` + overlays `mozilla-$1000.png`, `mozilla-$2000.png`, `YesWeHack-accepted.png` | Real recent payouts |
| 0:24–0:31 | `cve-search.mov` | Search a CVE database, my name hits |

**Voice-over (≈85 words, ~3 words/sec, segmented to clip cuts):**

**A · 0:00–0:10 (face — `pod1.MOV`):**
> "Hello, I am Haruto Kimura, a bug bounty hunter supercharged by Claude Code.
> I find vulnerabilities across the stack the internet quietly runs
> on — Intel, Arm, wolfSSL, Mozilla, PowerDNS."

**B · 0:10–0:17 (B-roll — `doing-bug-hunt.MOV` → `typing-on-editor.MOV`):**
> "This is what I do every day.
> I run multiple Claude Code agents in parallel to hunt vulnerabilities at scale."

**C · 0:17–0:24 (payout pages — Intigriti / Mozilla / YesWeHack):**
> "In the past three months alone — nine real CVEs. Over sixty-five
> thousand dollars in bounties. Intigriti, Mozilla, YesWeHack."

**D · 0:24–0:31 (`cve-search.mov` — my name appears in CVE results):**
> "Search any CVE database for my name. These vulnerabilities are
> real. They are mine."

**On-screen overlays:**
- Lower-third chyron during segment A:
  **Haruto Kimura · Stella LLC · 9 CVEs across wolfSSL, NSS, PowerDNS.**
- During segment C, hold a single caption: **"Last 60 days · 9 CVEs · $65K+"**
- During segment D, briefly highlight the matched reporter/author
  field on the CVE search result.

**Transition:** Hard cut to black + dateline card for Pod 2.

**Timing note:** This pod is now **30 seconds** (was 20 s). Net video
runtime grows from 3:00 → 3:10 unless we trim 10 s elsewhere.
Recommended absorbers: tighten Pod 4 by 5 s (drop the lane-name
recital — the diagram already shows them) and Pod 8 by 5 s (cut the
Opus-trait list to three items, not four). Pods 3, 5, 6, 7, 9 stay
intact — they carry the credibility weight.

---

## Pod 2 — The Crisis (0:30–0:55)

**Main point:** AI now finds vulnerabilities at industrial scale —
both real signal and unprecedented noise. The industry is racing to
catch up. Show three external receipts, then my own curve.

**Visual timeline (already cut on the editor):**

| Time | Clip | Source / Purpose |
|---|---|---|
| 0:30–0:37 | Anthropic Red zero-days article screenshot | [red.anthropic.com/2026/zero-days](https://red.anthropic.com/2026/zero-days/) — Opus 4.6 finds 500+ high-severity zero-days in OSS (Feb 5, 2026) |
| 0:37–0:43 | Anthropic Glasswing announcement screenshot | [anthropic.com/glasswing](https://www.anthropic.com/glasswing) — Glasswing exists because **Claude Mythos** (frontier model, 83.1% on CyberGym vs Opus 4.6's 66.6%) is too capable in cyber to be released publicly. Instead, Mythos is gated behind a 12-partner coalition: AWS, Apple, Cisco, Google, JPMorgan, Linux Foundation, Microsoft, NVIDIA, Palo Alto, CrowdStrike, Broadcom, Anthropic |
| 0:43–0:49 | HackerOne press-release screenshot (9th annual report, **2025-10-01**) | [hackerone.com — 9th annual Hacker-Powered Security Report](https://www.hackerone.com/press-release/hackerone-report-finds-210-spike-ai-vulnerability-reports-amid-rise-of-ai-autonomy) — **210% YoY spike in AI vulnerability reports**, 540% surge in prompt-injection reports |
| 0:49–0:55 | `monthly_bumper.mp4` (chart of HackerOne's own data, **2026-04-21**) | Bar chart from the [HackerOne h1 Validation press release on BusinessWire](https://www.businesswire.com/news/home/20260421791520/en/HackerOne-Introduces-h1-Validation-to-Help-Enterprises-Manage-Surge-in-AI-Discovered-Vulnerabilities) — Mar 2025 (≈26.7 k, back-calculated) vs **Mar 2026 (46,947, official, all-time high, +76% YoY)**. Source string baked into the chart by [`scripts/render_growth_bumper.py`](../scripts/render_growth_bumper.py) |

**Voice-over (≈90 words, ~3 words/sec, one connected causal arc — *capability rising (Opus 4.6) → next tier too dangerous to ship (Mythos / Glasswing) → but the released tier is in every hand → spike → still accelerating*):**

**A · 0:30–0:37 (Anthropic Red zero-days article) — capability:**
> "Look at what AI can do today. In February, Claude Opus 4.6 found
> over five hundred high-severity zero-days in open-source code."

**B · 0:37–0:43 (Glasswing announcement) — *too capable to ship*:**
> "Anthropic's next model — Claude Mythos — is too capable in cyber
> to release publicly. They gated it behind Project Glasswing —
> a twelve-partner coalition with AWS, Apple, Google, Microsoft."

**C · 0:43–0:49 (HackerOne 9th annual report, 2025-10-01) — *but the models that did ship are everywhere*:**
> "But the models that *did* ship are already in every researcher's
> hands. Last October, HackerOne measured a two-hundred-and-ten-percent
> year-over-year spike in AI vulnerability reports."

**D · 0:49–0:55 (`monthly_bumper.mp4`, HackerOne h1 Validation release 2026-04-21) — six months later, still accelerating:**
> "Six months later — a new all-time high.
> Forty-six thousand submissions in March alone."

**On-screen overlays:**
- During segment A, hold a chyron: **"Claude Opus 4.6 · 500+ zero-days · Feb 2026"**
- During segment B, hold a chyron: **"Claude Mythos · too capable in cyber to release publicly · gated through Project Glasswing (12 partners)"**
- During segment C, hold a single ticker: **"+210% YoY AI vuln reports · HackerOne · Oct 2025"**
- During segment D, no overlay — let the bars breathe. The chart IS the headline. (Source + "+76% YoY · Mar 2026 · all-time high" caption is already baked into the chart by `render_growth_bumper.py`.)

**Transition:** Slow fade. Music dips. The last word "signal" should
hang for a half-beat before Pod 3 cuts in.

**Timing note:** This pod is now **25 seconds** (was 20 s). Combined
with Pod 1's +10 s, net video runtime is **3:15** unless we trim
elsewhere. See updated absorber recommendations in Pod 1's timing
note.

**Fact-check note (must verify before recording):**
- "500+ high-severity zero-days" — confirmed from red.anthropic.com,
  Feb 5, 2026 update.
- "12 founding partners" — confirmed Glasswing page (AWS, Anthropic,
  Apple, Broadcom, Cisco, CrowdStrike, Google, JPMorganChase, Linux
  Foundation, Microsoft, NVIDIA, Palo Alto Networks).
- "Claude Mythos · too capable in cyber to release publicly" —
  Glasswing page describes Mythos as a frontier model with cyber
  capability above Opus 4.6 (83.1% vs 66.6% on CyberGym) being made
  available *only* to the 12 founding partners and ~40 additional
  vetted critical-infrastructure orgs during the research phase.
  Use "too capable" rather than "too dangerous" — Anthropic has not
  publicly characterized Mythos as dangerous, only as restricted in
  release. "Too capable to release publicly" is the factual frame.
  Verbs: "gated behind Glasswing" / "chose not to release publicly"
  — both accurate to the access model and avoid implying weaponized
  intent.
- **Segment C uses October 2025 data; segment D uses April 2026 data
  — this is intentional and timestamped in VO ("Last October..." →
  "Six months later..."). The two sources are different on purpose:
  the screenshots in the editor are the Oct 2025 9th annual report;
  the chart in `monthly_bumper.mp4` is the Apr 2026 h1 Validation
  release. Together they show acceleration, not duplication.**
- "210% YoY spike in AI vulnerability reports" — confirmed HackerOne
  9th annual Hacker-Powered Security Report, 2025-10-01. (Press
  release also cites 540% prompt-injection surge and 270% AI program
  adoption, but VO holds to the single 210% number to keep the
  through-line clean.)
- "All-time high · +76% YoY" + "46,947 submissions in March 2026"
  — confirmed HackerOne / BusinessWire press release on h1 Validation,
  2026-04-21. The 46,947 figure is HackerOne's own published number;
  the prior-year comparison bar in `monthly_bumper.mp4` (≈26.7 k) is
  back-calculated from the +76% YoY ratio (HackerOne did not publish
  the Mar 2025 raw count). Lead the VO with the official Mar 2026
  number, not the back-calculated one.
- We DO name "Claude Mythos" in segment B (it is the load-bearing
  point — the *next-tier* model is too capable to ship). We do NOT
  name any specific public model in segment C. Reason: the HackerOne
  210% YoY figure was measured for the year ending Oct 2025, and
  Opus 4.6 only shipped around Feb 2026 — so the Oct 2025 spike was
  driven by *prior-generation* frontier models (Opus 4.5 / Sonnet
  4.5 / GPT-5-class / etc.), not Opus 4.6. Naming Opus 4.6 next to
  the Oct 2025 number would be anachronistic. Segment C uses the
  generic phrasing "the models that did ship" instead.

---

## Pod 3 — "I am part of the problem" (0:55–1:15)

**Main point:** Direct continuation from Pod 2's "submissions
surging" — *and I sent some of that noise.* Three redacted triager
replies flash by as a single visual proof block (no company names,
no triager handle visible — all blacked out). Land the personal
admission, then **pivot into TriageGuard**: "I am part of the
problem. So I built TriageGuard." Sets up Pod 4's product reveal.

**Visual timeline (already cut on the editor):**

| Time | Clip | Source / Purpose |
|---|---|---|
| 0:55–1:00 | Face / B-roll (rejected report screen) | "And I sent some of them" — personal admission lead-in |
| 1:00–1:09 | `screenshots/pod1-credentials/commanderstrax-redacted.png` → `commanderstrax2-redacted.png` → `commanderstrax3-redacted.png` (3 quick flashes, ~3 s each) | Three real redacted triager replies to my own reports. Triager handle and product names blacked out. Visible quoted phrases: "actually try the PoC on a new machine" / "closed this submission as informative" / "self-inflicted scenario rather than a genuine security vulnerability" |
| 1:09–1:15 | Face / B-roll (rejected report screen) | Landing + pivot — "I am part of the problem. So I built TriageGuard." |

**Voice-over (≈55 words, ~3 words/sec, slow delivery on the landing — *carry the surge from Pod 2 → admit complicity → pivot into product*):**

**A · 0:55–1:09 (face → 3 redacted screenshots flash) — admission + proof:**
> "In fact, I sent some of them — and they were not high-quality
> reports. The triagers wrote back: *try the PoC on a new machine.*
> *Closed as informative.* *A self-inflicted scenario, not a
> vulnerability.*"

**B · 1:09–1:15 (face / B-roll) — landing + pivot to Pod 4:**
> "I am part of the problem I am trying to solve. Therefore, I built
> TriageGuard."

**On-screen overlays:**
- During the 3 screenshot flashes (1:00–1:09), highlight only the
  one phrase per screenshot that the VO is currently quoting — they
  are pre-redacted (`-redacted.png`) so triager handle and product
  names are already blacked out. Do NOT add product names back via
  caption.
- During segment B, no overlay — let "I am part of the problem"
  land in silence, then "So I built TriageGuard" leads visually
  into Pod 4's home page.

**Transition:** Direct hand-off into Pod 4 — the word "TriageGuard"
is the cue for the product home page to appear. No black frame, no
breath; the spoken name and the visual reveal hit on the same beat.

**Timing note:** Pod 3 is now back to **~20 seconds** (was 29 s in
the prior 4-segment version). Combined with Pod 1 (+10 s) and Pod 2
(+5 s), net video runtime is **~3:15** — Pod 3 no longer absorbs
overrun. Three screenshots flash as a single visual block (~3 s
each) rather than getting their own segments, per "時間もあまりない"
direction.

**Fact-check note:**
- Use the **redacted** versions in
  `demo/screenshots/pod1-credentials/`:
  `commanderstrax-redacted.png`, `commanderstrax2-redacted.png`,
  `commanderstrax3-redacted.png`. The originals at the repo-root
  level still contain product names and the triager handle.
- Do NOT name the affected products in VO. The screenshots are
  redacted to remove company identifiers — the VO must stay
  consistent. The point is the *pattern of noisy reports*, not the
  target.
- Quoted phrases in VO ("try the PoC on a new machine", "closed as
  informative", "self-inflicted scenario, not a vulnerability") are
  taken verbatim from the redacted screenshots — verify before
  recording that the on-screen highlights match the spoken phrasing.

---

## Pod 4 — The Product (1:15–1:40)

**Main point:** Walk the architecture diagram beat-by-beat. This
pod earns the **Opus 4.7 Use (20%)** judging category — name the
model split (Haiku for glue · Opus 4.7 for sub-agents and
synthesizer), the fan-out / fan-in pattern, file-based handoff (no
agent judges another), and the deterministic synthesizer. The
diagram does the heavy lifting; VO narrates the circuit lighting up.

**Visual timeline (use `demo/architecture.excalidraw` — single full-frame asset, animated reveal):**

| Time | Highlighted region of diagram | VO segment |
|---|---|---|
| 1:15–1:20 | Title card → **INPUT** box (Report + PoC + claimed code) lights up | A — name + input |
| 1:20–1:27 | **ORCHESTRATOR** (Python · Claude Agent SDK · Haiku 4.5 glue) → 4 fan-out arrows light up to the four sub-agent boxes | B — orchestrator fans out |
| 1:27–1:34 | The 4 sub-agent boxes light in sequence (REPRODUCIBILITY · ROOT CAUSE · DUPLICATE · HALLUCINATION), then the `findings/{report_id}/` box with `repro.json` / `root_cause.json` / `duplicate.json` / `hallucination.json` appears | C — what each lane does + file-based handoff |
| 1:34–1:40 | **SYNTHESIZER** (Opus 4.7 xhigh, weighted rubric) → **VERDICT** box (Signal Score 0–100 · SIGNAL · UNCERTAIN · SLOP) lights up | D — synthesis + verdict |

**Voice-over (≈75 words, ~3 words/sec — *name → input → fan-out → 4 specialists + file handoff → deterministic synthesis → verdict*):**

**A · 1:15–1:20 (INPUT box) — name + input:**
> "This is TriageGuard. First, you drop in a vulnerability report, the
> proof-of-concept, and the claimed source code."

**B · 1:20–1:27 (ORCHESTRATOR + fan-out) — fan-out:**
> "A Python orchestrator — Claude Haiku 4.5 for the glue — fans out
> to four Claude Opus 4.7 sub-agents, running in parallel."

**C · 1:27–1:34 (4 sub-agents → `findings/{report_id}/`) — specialists + file-based handoff:**
> "They rebuild the PoC, read the source, check for duplicates,
> fact-check every reference. Each writes its findings as JSON.
> No agent judges another."

**D · 1:34–1:40 (SYNTHESIZER → VERDICT) — deterministic synthesis:**
> "A synthesizer applies a weighted rubric. Signal Score, zero to
> one hundred. SIGNAL, UNCERTAIN, or SLOP."

**On-screen overlays:**
- Hold the diagram title-bar caption visible throughout: **"TriageGuard · Signal vs. Slop verdict for vulnerability reports."**
- During segment B, a small chyron under the orchestrator: **"Haiku 4.5 · glue · routing"**
- During segment B/C transition, a small chyron under each sub-agent box as it lights: **"Opus 4.7 · xhigh effort"**
- During segment D, the `VERDICT` box's three labels (SIGNAL · UNCERTAIN · SLOP) flash in sequence as they are spoken — green / amber / red.
- Optional: a faint corner caption **"fan-out · file-based handoff · fan-in"** for the entire pod.

**Transition:** Cursor moves to the home page sample list and clicks
**s1** — hard cut into Pod 5.

**Timing note:** This pod is **25 seconds** (was 20 s, +5 s). The
architecture walkthrough is the *Opus-4.7-Use* judging anchor —
recommend keeping the full 25 s rather than compressing. Combined
with Pod 1 (+10 s), Pod 2 (+5 s), Pod 3 (±0), net video runtime is
**~3:20** — Pod 5 onward shift by +20 s from their original cues.
Absorb in Pod 8 (drop to ~15 s by trimming the Opus-trait list to
two items, since Pod 4 already established Haiku/Opus split).

**Fact-check note:**
- Architecture diagram source: `demo/architecture.excalidraw`. Text
  labels match VO verbatim — verify before recording that nothing has
  drifted (e.g. "Reproducibility" vs "Repro", "Root Cause" vs
  "Root-Cause").
- "Haiku 4.5 for the glue" — confirmed in `CLAUDE.md` ("Opus 4.7 at
  xhigh for sub-agents + synthesizer; Haiku 4.5 for glue. This split
  is mentioned in the pitch.")
- "No agent judges another" — this is the file-based-handoff design
  point: agents write to `findings/{report_id}/*.json`, the
  synthesizer reads JSON. No agent reads another agent's reasoning
  trace; the synthesizer applies a *deterministic* Python rubric, not
  an LLM judgment. This is the core defensibility claim — do not
  soften the wording.
- "Signal Score 0–100, SIGNAL/UNCERTAIN/SLOP" — confirmed against
  `.claude/skills/signal-score-rubric/SKILL.md`.

---

## Pod 5 — Demo 1: SIGNAL (1:20–1:40)

**Main point:** Real CVE → SIGNAL 90 → maintainer can act.
"This is one of mine."

**Voice-over (≈55 words):**
> "Sample one is a real CVE I reported to wolfSSL — a stack overflow
> in their HPKE implementation. Click Run. Four lanes light up. The
> reproducibility agent rebuilds it under AddressSanitizer and points
> at the exact line. Zero fabricated references. SIGNAL ninety. The
> maintainer reads three paragraphs and ships a patch."

**On-screen:**
- Click → 4 lanes animate (C → D → B → A).
- Sanitizer frame highlights `hpke.c:492`.
- Confidence meter swings to 95%.
- Narrative paragraph block fades in; cursor lingers on one citation.

**Transition:** Cut back to home, click s4.

---

## Pod 6 — Demo 2: SLOP (1:40–2:00)

**Main point:** Polished AI slop → caught in red → 30 minutes becomes
30 seconds.

**Voice-over (≈55 words):**
> "Sample four is AI slop against curl. The report cites a function
> called `parse_content_type_header`. TriageGuard opens the actual
> source — that function does not exist. Three fabricated references
> light up red. SLOP fifteen. The maintainer's thirty-minute
> rejection becomes a thirty-second one."

**On-screen:**
- Same animation, same lanes.
- When the Hallucination lane lands, **three invalid_refs flash red**
  in sequence: `parse_content_type_header`, `lib/http.c:342`,
  `strcpy in lib/http.c`.
- Score pill snaps to **SLOP 15**, rule 2 caption.

**Transition:** Cut back to home, click s2.

---

## Pod 7 — Demo 3: UNCERTAIN (honest doubt) (2:00–2:20)

**Main point:** A real CVE without a working PoC. The system refuses
to fake confidence — it says "I cannot verify." This is the
self-verification trait of Opus 4.7, made literal.

> *Note: this pod replaces the originally-planned LIVE GPT-4o slop
> generation, which was rejected on grounds that GPT-4o is no longer a
> credible state-of-the-art model in 2026 and the demo would read as
> contrived.*

**Voice-over (≈55 words):**
> "Sample two is also a real CVE I reported — but the report came
> without a working proof-of-concept. Watch what TriageGuard does.
> The reproducibility agent is honest: it cannot reproduce. The
> root-cause agent confirms the code matches. Verdict: UNCERTAIN,
> fifty. Not SIGNAL. Not SLOP. The system refuses to fake confidence
> it does not have."

**On-screen:**
- Click s2 → 4 lanes animate.
- Reproducibility lane lands on `no_poc` (or `failed_to_reproduce`),
  visually distinct from a green check — a yellow open-circle.
- Root Cause lane lands on `match` (green).
- Score pill snaps to **UNCERTAIN 50**, rule 8 caption: *"A=no_poc +
  B=match + invalid=0 → UNCERTAIN."*
- Confidence meter at 93%.
- Narrative paragraph: highlight one phrase like **"cannot be
  reproduced without a PoC"** to emphasize honest doubt.

**Transition:** Pull back to architecture.

---

## Pod 8 — Why Opus 4.7 (2:20–2:40)

**Main point:** Combine "4 parallel Opus 4.7 agents" + "deterministic,
auditable score." This pod earns the Opus-4.7-Use 20% category.

**Voice-over (≈55 words):**
> "Why Opus 4.7? One million tokens of context. Faithful
> instruction-following. Low hallucination. World-class coding. Four
> sub-agents at xhigh effort, in parallel. They write JSON to disk.
> A deterministic Python rule chooses the score — auditable, with
> the rule number cited. A second Opus 4.7 pass writes the
> explanation. No LLM judges itself."

**On-screen:**
- Architecture diagram from `STATE.md`, animated: 4 agents →
  `findings/{id}/` → synthesizer → narrative.
- Caption strip: **"Opus 4.7 × 4 · xhigh effort · file-based handoff
  · deterministic synthesizer."**
- Brief flash of `SYNTHESIS.md` and `NARRATIVE.md` filenames on disk.

**Transition:** Cut back to face.

---

## Pod 9 — Close (2:40–3:00)

**Main point:** Personal close. *I owed them this.* The line that
should ring after the screen goes black.

**Voice-over (≈45 words):**
> "I helped flood maintainers with AI reports. I owed them this.
> TriageGuard is open source. wolfSSL today, every C codebase next.
> Built with Opus 4.7 — because the same model that broke the queue
> is the only one strong enough to clear it."

**On-screen:**
- Builder back in frame.
- End card: **TriageGuard · github.com/HarutoKimura/triageguard ·
  Built with Claude Opus 4.7 · Stella LLC.**
- Hold for 2 seconds of silence before fade.

---

## Per-pod numbers checklist (must be spoken)

| Pod | Number / phrase | Source |
|---|---|---|
| 1 | "nine real CVEs", "two months", "over sixty-five thousand dollars", "Intigriti, Mozilla, YesWeHack" | personal record |
| 2 | "five hundred high-severity zero-days", "Claude Mythos", "too capable in cyber to release publicly", "twelve-partner coalition", "two-hundred-and-ten-percent year-over-year spike", "all-time high", "forty-six thousand vulnerability submissions" | Anthropic Red (Feb 2026) / Glasswing / HackerOne 9th annual report (Oct 2025) → HackerOne h1 Validation (Apr 2026) |
| 3 | "a hundred reports in two months", "try the PoC on a new machine" (verbatim), "closed as informative" (verbatim), "self-inflicted scenario, not a vulnerability" (verbatim), "I am part of the problem I am trying to solve", "So I built TriageGuard" | three redacted triager replies (Jan–Feb 2026 — product names blacked out per platform anonymization) |
| 4 | "four Claude Opus 4.7 sub-agents", "Claude Haiku 4.5 for the glue", "fans out... in parallel", "writes its findings as JSON", "no agent judges another", "weighted rubric", "Signal Score, zero to one hundred", "SIGNAL, UNCERTAIN, or SLOP" | `demo/architecture.excalidraw` (single-frame walk-through) |
| 5 | "SIGNAL ninety", "ninety-five percent" (confidence) | live s1 verdict |
| 6 | "SLOP fifteen", "thirty minutes", "thirty seconds" | live s4 verdict |
| 7 | "UNCERTAIN fifty", "ninety-three percent" (confidence) | live s2 verdict |
| 8 | "one million tokens", "Opus 4.7 × 4", "xhigh" | model facts |
| 9 | "open source", "wolfSSL today, every C codebase next" | repo + roadmap |

---

## Production notes

1. **English script, native pacing.** ~3 words/sec. Pods are designed
   at 50–55 words each so a non-native delivery can breathe without
   overrun.
2. **Read pods 3 and 9 slower than the others.** They carry the
   personal weight. Aim ~2.5 words/sec there.
3. **No emoji on screen, no jokes.** Coldly sincere. Mike Brown beats
   Steve-Jobs-keynote here.
4. **Music:** sparse piano, fades during pods 3 and 9. Ducks under
   voice always.
5. **Captions:** burned-in English captions for non-native judges.
   Numbers in digits, not words, for readability ($65K, 9 CVEs).
6. **B-roll order of priority:** real maintainer email → HackerOne
   profile → wolfSSL/NSS/PowerDNS logos → IBB/curl headlines.
7. **Re-shoot threshold:** if any of the hero numbers is misread,
   re-shoot the pod. Numbers are the credibility spine.
8. **Order of recording:** pods 5–7 first (UI demos must be exact and
   timed), then pods 1, 3, 9 (emotional reads — fresh voice), then
   pods 2, 4, 8 (factual — easy).
9. **Hold for the silence at 2:58–3:00.** Two seconds of nothing
   makes the close land.

---

## Change log

- **2026-04-25** — Initial 9-pod spec drafted from interview.
- **2026-04-25** — Pod 7 replaced: GPT-4o LIVE slop generation →
  s2 UNCERTAIN 50 demo. Reasons: (1) GPT-4o is not SOTA in 2026;
  (2) running real SOTA models live for 30–60 min overruns demo
  budget; (3) s4 already covers SLOP; (4) UNCERTAIN bucket completes
  the SIGNAL / UNCERTAIN / SLOP triple and showcases Opus 4.7's
  self-verification trait directly. See
  [`INTERVIEW_2026-04-25.md`](./INTERVIEW_2026-04-25.md) Q11.
- **2026-04-26** — Pod 1 expanded 0:00–0:20 → 0:00–0:30 to match
  the cut B-roll (face → bug-hunt → typing → payout collage →
  CVE-database name search). VO split into 4 segments (A/B/C/D)
  aligned to clip boundaries; "the same AI breaking the industry"
  framing moved from Pod 1 to Pod 2 (it overlaps Pod 2's thesis).
  Net runtime + 10 s — absorb in Pods 4 and 8 (see Pod 1 timing note).
- **2026-04-26** — Pod 2 rewritten 0:20–0:40 → 0:30–0:55 to match
  new article-screenshot cuts (Anthropic Red zero-days · Glasswing ·
  HackerOne 210% spike) plus self-made `monthly_bumper.mp4`. Old IBB /
  curl / Google framing dropped — replaced with industrial-scale AI
  vulnerability discovery as the new "crisis" thesis. Source links
  embedded in Pod 2; fact-check note added. Net runtime + 5 s on top
  of Pod 1 → 3:15 total without further trims.
- **2026-04-26** — Pod 2 VO restructured into a single causal arc:
  *capability* (Opus 4.6 zero-days) → *coalition response*
  (Glasswing) → *consequence* (HackerOne 210% spike) → *proof*
  (`monthly_bumper.mp4` chart). 540% prompt-injection figure dropped
  from VO to keep the chain clean — it diluted the through-line.
  Each segment now opens with a connector phrase ("Look at what AI
  can do" → "to channel that capability" → "showing up in the data"
  → "this is what that spike looks like").
- **2026-04-26** — Pod 2 segments C and D re-sourced to the HackerOne
  h1 Validation press release (BusinessWire, 2026-04-21) — the
  *actual* data behind `monthly_bumper.mp4`. Numbers updated:
  "+210% YoY" (old 9th annual report) → "all-time high · +76% YoY"
  + "46,947 submissions in March 2026" (matches the chart). Segment
  D framing softened from "I plotted it myself" to "HackerOne's own
  numbers, charted" — accurate, since the data is HackerOne's and
  only the chart rendering is mine. See the data-source table in
  this commit's user message for the back-calculation note on the
  Mar 2025 reference bar.
- **2026-04-26** — Pod 2 C and D split across two timestamped
  HackerOne sources to match what is actually on screen. The
  October 2025 9th annual report (210% YoY spike) is the screenshot
  shown during segment C, so segment C reverts to "Last October,
  HackerOne measured a 210% YoY spike." Segment D keeps the April
  2026 chart with "Six months later, the curve only steepened —
  March 2026, all-time high, 46,947 submissions." The chronology
  ("Last October..." → "Six months later...") is now explicit in
  VO so the timeline is unmistakable to the listener.
- **2026-04-26** — Pod 2 segments B and C reframed to make the
  *cyber-capability* throughline explicit. B now opens "That cyber
  capability is now too powerful to ignore" — naming the *defense*
  side of the same capability shown in A. C opens "But that same
  capability is also in every researcher's hands" — the *offense /
  research* side, which is what produces the HackerOne spike. The
  arc now reads: *capability rises (A)* → *too powerful, coalition
  defends (B)* → *also weaponized at researcher scale (C)* → *and
  still accelerating (D)*. Net runtime + 2 s — Pod 2 now ≈ 27 s.
- **2026-04-26** — Pod 2 segment B sharpened with the actual
  Glasswing premise: Anthropic's *next* model **Claude Mythos** is
  too capable in cyber to be released publicly, so it was gated
  behind the 12-partner Glasswing coalition. Replaces the weaker
  "too powerful to ignore" framing. Segment C connector updated to
  "But what is already shipped — like Opus 4.6 — is in every
  researcher's hands" so the contrast is now Mythos (gated) vs Opus
  4.6 (in every hand) → 210% spike. Earlier "do not name the model"
  guidance reversed: naming Mythos is now the load-bearing point.
  Net runtime + 1–2 s — Pod 2 now ≈ 28–29 s.
- **2026-04-26** — Pod 2 segment C corrected for chronology: removed
  "like Opus 4.6" because Opus 4.6 only shipped around Feb 2026 and
  the cited HackerOne 210% YoY figure measures the year ending Oct
  2025 — naming Opus 4.6 would be anachronistic. Segment C now uses
  the generic "the models that *did* ship are already in every
  researcher's hands." The Mythos-vs-public-frontier contrast is
  preserved (B: gated next-tier · C: generations-already-shipped)
  without misattributing the spike to a model that did not yet exist.
- **2026-04-26** — Pod 2 segment B softened: "so dangerous in cyber
  they refused to release it publicly" → "too capable in cyber to
  release publicly." Reason: Anthropic has not publicly characterized
  Mythos as *dangerous* — only as restricted in release. "Dangerous"
  imputes weaponized intent we cannot prove; "too capable" is the
  factual frame supported by the CyberGym 83.1% vs 66.6% gap and the
  gated access model. Verb also changed from "locked" → "gated" for
  the same neutral-but-accurate reason.
- **2026-04-26** — Pod 2 segment D compressed from 22 words / ~10 s
  read time → 14 words / ~7 s to fit the actual clip duration.
  Drops "the curve only steepened" (visual already shows it) and
  "vulnerability submissions" (collapses to "submissions" — chart
  context disambiguates) and "March 2026 hit" → "in March alone."
  Hero number "forty-six thousand" preserved.
- **2026-04-26** — Pod 3 rewritten 0:40–1:00 → 0:55–1:24 to match
  the three real triager-reply screenshots (commanderstrax.png /
  commanderstrax2.png / commanderstrax3.png, Jan–Feb 2026, Arm +
  Intel programs). VO split into A/B/C/D segments mirroring the
  screenshots' chronology + a closing personal beat. The arc now
  reads: *valid-but-noisy report* (A) → *fragile PoC, doesn't
  reproduce* (B) → *closed as informative, not a vulnerability* (C)
  → *I am part of the problem* (D). Verbatim quotes preserved
  ("actually try the PoC on a new machine", "self-inflicted
  scenario", "closed as informative"). Earlier paraphrased line
  "Please verify your PoC yourself before submitting" replaced with
  the actual triager wording. "Programs delisting" and "triage
  queues stretching to three months" cut — Pod 2 already establishes
  the industry-wide spike, and Pod 3 stays 100% personal. Net
  runtime + 9 s (Pod 3 now ≈ 29 s) → total video ≈ 3:24 without
  later trims.
- **2026-04-26** — Pod 3 compressed 0:55–1:24 → 0:55–1:15 (29 s →
  20 s) and switched to the **redacted** screenshot variants in
  `demo/screenshots/pod1-credentials/*-redacted.png`. Reasons:
  (1) the original screenshots showed product names (Arm, Intel,
  OpenVINO) and the triager handle — speaker requested anonymization;
  (2) per "時間もあまりないので、1つ1つ触れてる時間はない" direction,
  the three replies now flash as a single visual proof block (~3 s
  each) rather than getting their own A/B/C segments. Pod 3 also now
  *bridges into Pod 4* — closes with "So I built TriageGuard," with
  the spoken product name landing on the same beat as the home-page
  reveal in Pod 4. Continuity from Pod 2 sharpened: opening line
  "And I sent some of them" picks up the surge from Pod 2D's
  "Forty-six thousand submissions in March alone." Net runtime back
  to ~3:15 (Pod 3 no longer absorbs overrun).
- **2026-04-26** — Pod 4 rewritten 1:00–1:20 → 1:15–1:40 to walk
  through the architecture diagram (`demo/architecture.excalidraw`)
  beat-by-beat. The diagram is held on screen for the full pod with
  progressive region-highlighting synced to VO segments A/B/C/D.
  This pod is the **Opus 4.7 Use (20%)** judging anchor — VO now
  explicitly names: (1) Python orchestrator + Claude Agent SDK,
  (2) Haiku 4.5 for glue/routing, (3) four Opus 4.7 sub-agents
  running in parallel (xhigh effort), (4) file-based handoff via
  `findings/{report_id}/*.json`, (5) "no agent judges another"
  defensibility claim, (6) deterministic Python synthesizer with
  weighted rubric, (7) Signal Score 0–100 → SIGNAL/UNCERTAIN/SLOP.
  Old "sixty seconds later: SIGNAL or SLOP, with receipts" line cut
  — the architecture walk-through is more credibility-dense than
  the speed claim. Net runtime + 5 s (Pod 4 now ≈ 25 s). Pod 5+
  start cues shift +20 s from original; absorb the remaining
  overrun in Pod 8 (target ≈ 15 s by trimming the Opus-trait list
  to two items, since Pod 4 already established Haiku/Opus split).
