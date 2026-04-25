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

## Pod 1 — Hook & Self-Intro (0:00–0:20)

**Main point:** Establish who I am with one sentence and one number
that should not exist.

**Voice-over (≈55 words):**
> "I am a bug bounty hunter. In the last two months, I used AI to
> find nine real CVEs and earned sixty-five thousand dollars in
> bounties. The same AI that made me effective is also breaking the
> industry I work in. This is the story of what I built about it."

**On-screen:**
- Open on his face, half-frame. Lower-third chyron:
  **Haruto Kimura · Stella LLC · 9 CVEs across wolfSSL, NSS, PowerDNS.**
- Cut to a tasteful collage: a bounty-confirmation email (blurred
  amount, $65K visible), a HackerOne profile, GitHub commits.

**Transition:** Hard cut to black + dateline card.

---

## Pod 2 — The Crisis (0:20–0:40)

**Main point:** The industry is collapsing under AI slop, with dates
and quotes.

**Voice-over (≈55 words):**
> "March 27, 2026: HackerOne paused the Internet Bug Bounty program
> after thirteen years. curl killed its bounty in January. Google
> rejects AI-generated submissions outright. The valid-submission
> rate at major programs fell from fifteen percent to under five.
> Maintainers are drowning."

**On-screen:**
- News headlines fan in chronologically: IBB pause announcement,
  Daniel Stenberg's curl post, Google OSS VRP policy update.
- 15% → 5% counter ticker, large.

**Transition:** Slow fade. Music dips.

---

## Pod 3 — "I am part of the problem" (0:40–1:00)

**Main point:** Vulnerability moment — *I caused some of this.* The
emotional spine of the video. Read slowly.

**Voice-over (≈50 words):**
> "Maintainers I have reported to have written back to me — 'Please
> verify your PoC yourself before submitting.' Programs delisting.
> Triage queues stretching to three months. I will be honest: a
> hundred reports in two months means I sent some of that noise.
> I am part of the problem I am trying to solve."

**On-screen:**
- An anonymized real maintainer email with the line **"Please verify
  your PoC yourself before submitting"** highlighted.
- B-roll: a rejected report screen of his own.

**Transition:** A breath. Cut to product UI.

---

## Pod 4 — The Product (1:00–1:20)

**Main point:** TriageGuard one-liner + four-agent shape.

**Voice-over (≈50 words):**
> "This is TriageGuard. You drop in a vulnerability report. Four
> Claude Opus 4.7 sub-agents fan out in parallel — one rebuilds the
> proof-of-concept, one verifies the cited source, one queries CVE
> databases, one fact-checks every reference. Sixty seconds later:
> SIGNAL or SLOP, with receipts."

**On-screen:**
- TriageGuard home page: list of samples.
- Quick 4-lane diagram overlay: **Reproducibility · Root Cause ·
  Duplicate · Hallucination.**
- Logo bar: wolfSSL, NSS, PowerDNS.

**Transition:** Click on s1.

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
| 1 | "nine real CVEs", "two months", "sixty-five thousand dollars" | personal record |
| 2 | "March 27, 2026", "thirteen years", "fifteen percent to under five" | IBB / curl / public data |
| 3 | "a hundred reports in two months", "three months" (queue) | personal + maintainer feedback |
| 4 | "four Claude Opus 4.7 sub-agents", "sixty seconds" | product spec |
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
