---
description: Final preflight before hitting Submit. Verifies repo is public-ready, video is uploaded, written summary is within word count, license is present, secrets are not. Run once on 2026-04-26.
---

Submission-day preflight. Do not skip any step.

## Steps

Run these checks. Mark each ✓ or ✗. Do NOT proceed past a ✗ unless
the user explicitly overrides.

### Repo

- [ ] `git status` is clean (no uncommitted changes).
- [ ] Latest commit is tagged `v1.0-submission` or similar.
- [ ] `git log --oneline -5` reads coherently.
- [ ] `LICENSE` file exists at repo root (Apache-2.0 or MIT preferred
      per hackathon rules).
- [ ] `README.md` exists, is under 400 lines, opens with a one-line
      product description and a demo video link.
- [ ] `WRITTEN_SUMMARY.md` exists, between 100 and 200 words
      (run `wc -w`).

### Secrets

- [ ] `.env` and `.env.*` are in `.gitignore`.
- [ ] `grep -rnE '(sk-ant-|sk-|ghp_|ghs_|xoxb-)' .` returns no hits
      outside `.gitignore`.
- [ ] No file matching `*.key`, `*.pem`, `id_rsa*` is tracked.

### Demo video

- [ ] `video/out/*.mp4` or equivalent final file exists.
- [ ] Duration is under 3:00 (run `ffprobe -v error -show_entries
      format=duration -of default=noprint_wrappers=1:nokey=1
      video/out/*.mp4`).
- [ ] Uploaded to YouTube or Loom. URL recorded in README.md.
- [ ] URL plays without auth in an incognito window.

### Build

- [ ] `docker build -f Dockerfile .` succeeds from clean.
- [ ] `uv sync` or `pip install -e .` succeeds from clean.
- [ ] `README` instructions, followed literally, get a stranger to
      `/run-sample s1-cve-2026-2646`.

### Samples

- [ ] `demo-inputs/` has all six samples.
- [ ] Running `/demo-dryrun` returns GO.

### Opus 4.7 narrative

- [ ] `WRITTEN_SUMMARY.md` names "Opus 4.7" explicitly.
- [ ] Names at least three capabilities leveraged (long-horizon
      autonomy, pushes back, self-verification, precise instruction
      following, tool-use reliability, vision, adaptive thinking).
- [ ] Description of how Claude was used is concrete, not
      aspirational ("Agent A runs for 12 minutes unattended" not
      "we leverage AI").

### Backup

- [ ] Repo pushed to `origin main`.
- [ ] Backup tarball `git archive` saved to `~/submissions/` (just in
      case GitHub is having a bad day at 19:59 EST).

## Output

Print the checklist with ✓/✗, ending with:

```
SHIP: YES | NO ({N} blockers)
```

If NO, list blockers in priority order. Fix the top blocker, rerun.
