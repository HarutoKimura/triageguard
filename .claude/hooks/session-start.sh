#!/usr/bin/env bash
# TriageGuard session-start banner. Prints days-to-deadline and the judging rubric
# so every fresh session starts with the same load-bearing context.

set -euo pipefail

DEADLINE_ISO="${TRIAGEGUARD_DEADLINE:-2026-04-26T20:00:00-04:00}"
NOW_EPOCH=$(date +%s)

# Portable ISO parse. macOS date -j -f does not accept a colon in %z; strip it.
DEADLINE_CLEAN="${DEADLINE_ISO/T/ }"
DEADLINE_CLEAN="${DEADLINE_CLEAN/-04:00/-0400}"
DEADLINE_CLEAN="${DEADLINE_CLEAN/-05:00/-0500}"
if DEADLINE_EPOCH=$(date -j -f "%Y-%m-%d %H:%M:%S%z" "${DEADLINE_CLEAN}" +%s 2>/dev/null); then
  :
elif DEADLINE_EPOCH=$(date -d "${DEADLINE_ISO}" +%s 2>/dev/null); then
  :
else
  DEADLINE_EPOCH=""
fi

HOURS_LEFT="?"
if [ -n "${DEADLINE_EPOCH}" ]; then
  SECS=$((DEADLINE_EPOCH - NOW_EPOCH))
  if [ "${SECS}" -gt 0 ]; then
    HOURS_LEFT=$((SECS / 3600))
  else
    HOURS_LEFT="PAST DEADLINE"
  fi
fi

cat <<EOF
========================================================
  TriageGuard — hackathon session
  Deadline: ${DEADLINE_ISO}
  Hours left: ${HOURS_LEFT}
  Judging: Impact 30% | Demo 25% | Opus 4.7 Use 20% | Depth 20%
  North star: "Easier to demo than to explain." — Boris Cherny
--------------------------------------------------------
  Before coding, read: .claude/RULES.md §0–§3
  If stuck, read: .claude/skills/opus-4.7-playbook/SKILL.md
  To record a finding: /record-finding
  To verify: /verify-done
  To rehearse demo: /demo-dryrun
========================================================
EOF
