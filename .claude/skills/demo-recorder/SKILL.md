---
name: demo-recorder
description: 3-minute demo video protocol for TriageGuard — shot list, Remotion setup, rehearsal checklist, common failure modes. Use when planning, recording, editing, or rehearsing the submission demo video, or when designing any UI element that must read well on screen capture.
---

# Demo Recorder

The demo is 25% of the score. A fragile demo can only lose. This
skill enforces a fixed protocol so rehearsal is mechanical and the
final take is confidence-building.

Target: **3:00 max, 2:45 ideal**. Platform: YouTube unlisted or Loom.
Resolution: 1920×1080 at 60 fps. Audio: levels normalized, no music.

---

## 1 · Shot list (timestamps are cues, not hard)

| Time | Shot | Notes |
|------|------|-------|
| 0:00–0:15 | **Cold open — problem headline.** Full-screen card: "HackerOne paused the Internet Bug Bounty program. Valid submission rate: 15% → <5%. AI slop is DDoSing OSS." Narration: "Last month, the Internet Bug Bounty shut down after 13 years." | Hook. No logo yet. |
| 0:15–0:30 | **Who I am.** Card: "I publish CVEs in wolfSSL, NSS, PowerDNS. I use AI to find them. I helped create this crisis." | Credibility. Pitch framing. |
| 0:30–0:40 | **What this is.** Card: "TriageGuard — autonomous validator for vulnerability reports. Signal or slop in 12 minutes." Cut to web UI landing page. | Product reveal. |
| 0:40–1:15 | **Sample 1 — real CVE.** Paste CVE-2026-2646 report. Click Triage. UI shows four sub-agents firing in parallel. Agent A builds wolfSSL, runs PoC, ASan trace appears. Signal bar animates to 85. Final card: "SIGNAL 85/100 — ACCEPT." | The money shot. |
| 1:15–1:40 | **Sample 4 — public curl slop.** Paste known slop report. Sub-agents fire. Agent D surfaces 3 invalid references. Agent A fails to build. Signal bar lands at 12. Card: "SLOP 12/100 — REJECT." | Negative case. Makes the positive case real. |
| 1:40–2:05 | **Live slop.** Narration: "Let's manufacture one." Click a "Generate Fresh Slop" button (pre-wired to GPT-4o API with a canned prompt). Paste output into TriageGuard. Signal bar lands <25. | Theatrical. Memorable. |
| 2:05–2:30 | **Architecture card.** 4 Opus 4.7 sub-agents + Haiku 4.5 glue + synthesizer. Callouts: "long-horizon autonomy", "pushes back on hallucinations", "honest failure." | Opus 4.7 Use (20%). |
| 2:30–2:50 | **Close.** Back to builder: "I helped create this crisis. TriageGuard is my contribution to solving it." URL card. | Impact. Pitch-lands. |
| 2:50–3:00 | **Logo + open-source notice + URL.** | Hackathon compliance. |

---

## 2 · Why this order

- **Pain before product.** Judges have seen 500 submissions. You have
  15 seconds to matter.
- **Real CVE before slop.** Prove the positive case first. If you show
  slop rejection first, the viewer has no "correct" reference frame.
- **Live-generated slop last.** The sticky moment. Boris: *"Easier to
  demo than to explain."*
- **Architecture after demo, not before.** Judges who want depth see
  it; judges who bounce early still got the demo.

---

## 3 · Remotion setup

Tariq (Session 1) built videos with a design-system-in-HTML approach.
Copy that. Steps:

1. Create `video/` at project root.
2. `npx create-video@latest` — pick the Remotion starter template.
3. Write `video/src/DesignSystem.tsx` — palette, type scale, spacing
   tokens matching the web UI.
4. One scene per shot above; compose in `video/src/Video.tsx`.
5. Screen-capture the actual product runs (OBS, 60 fps, no zoom).
   Save clips into `video/public/captures/`.
6. Use Remotion's `<OffthreadVideo src="..." />` to inline the
   captures; overlay narration cards via `<AbsoluteFill>`.
7. Export: `npx remotion render Video out/triageguard-demo.mp4 --fps=60 --concurrency=4`.

Keep the TypeScript under `video/src/`. Do not mix with the Next.js
frontend. The Remotion project is ephemeral — discard it after
submission.

---

## 4 · Pre-rehearsal checklist

Run this list before every take. Rehearsing without it is how
mistakes creep in.

- [ ] Fresh browser profile. No autofill, no extensions, no cookies.
- [ ] Notifications silenced (macOS Focus → Do Not Disturb).
- [ ] Terminal font size 18pt or larger. Light theme for web UI.
- [ ] All six sample inputs preloaded as files in `demo-inputs/`.
- [ ] Backend running, connected, latency under 300 ms.
- [ ] Docker images pre-pulled (no first-time pull during take).
- [ ] Six sample runs have warm cache hits ready.
- [ ] Demo video microphone levels: peak −6 dB, floor −40 dB.
- [ ] Screen recorder at 1920×1080 @ 60 fps.
- [ ] Browser window pinned to 1920×1080 without tab bar decorations.

---

## 5 · Common failure modes

| Failure | Fix |
|---------|-----|
| Live triage takes 14 minutes — too long for video | Time-lapse the middle; full fidelity for open/close |
| Sub-agent streams too fast to read | Pause video, zoom-cut to one of the JSON files on disk |
| Build log overflows the UI card | Truncate to last 200 lines in the UI itself |
| Voice-over sounds robotic | Do not read cards verbatim; paraphrase. |
| Music overpowers narration | No music. This is not a pitch deck. |
| "Generate Slop" button fails live | Pre-record the button's happy path; demo the replay |

---

## 6 · The written submission (100–200 words)

Freeze by 18:00 EST on 2026-04-26. Template:

> **TriageGuard — autonomous validator for vulnerability reports.**
>
> The bug bounty industry is collapsing under AI slop. HackerOne
> paused the Internet Bug Bounty in March 2026 after 13 years; curl
> ended its program; Google rejects AI-generated submissions outright.
> The new bottleneck is validation, not discovery.
>
> TriageGuard runs four parallel Opus 4.7 sub-agents — Reproducibility,
> Root Cause, Duplicate, Hallucination — that together verify whether
> a report is signal or slop. A synthesizer applies a deterministic
> rubric and emits a 0–100 Signal Score with reasoning.
>
> We lean on Opus 4.7's long-horizon autonomy (Agent A spends 10+
> minutes building wolfSSL and running PoCs without supervision),
> its willingness to push back on hallucinated references, and its
> precise instruction-following for strict verdict schemas.
>
> I publish CVEs in wolfSSL, NSS, and PowerDNS. I helped create the
> crisis. TriageGuard is my contribution to solving it.

191 words. Edit, do not rewrite.

---

## 7 · Submission day timeline (2026-04-26)

| Time (EST) | Task |
|------------|------|
| 09:00 | `/ship-check` — final preflight |
| 10:00 | Record take 1 |
| 11:00 | Watch take 1, list fixes |
| 12:00 | Fix UI bugs surfaced by take 1 |
| 14:00 | Record take 2 |
| 15:00 | Edit take 2 in Remotion |
| 16:00 | Upload to YouTube unlisted; verify playback |
| 17:00 | Freeze WRITTEN_SUMMARY.md |
| 18:00 | Tag `v1.0-submission`, push to GitHub public |
| 19:00 | Submit via the hackathon portal |
| 19:30 | Buffer for portal flakiness |
| 20:00 | Hard deadline |

One hour of slack at 19:00 is not optional. It is the deadline.
