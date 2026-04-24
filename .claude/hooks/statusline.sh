#!/usr/bin/env bash
# TriageGuard status line. Shows hours-to-deadline + current git branch.

set -euo pipefail

DEADLINE_ISO="${TRIAGEGUARD_DEADLINE:-2026-04-26T20:00:00-04:00}"
NOW_EPOCH=$(date +%s)

DEADLINE_CLEAN="${DEADLINE_ISO/T/ }"
DEADLINE_CLEAN="${DEADLINE_CLEAN/-04:00/-0400}"
DEADLINE_CLEAN="${DEADLINE_CLEAN/-05:00/-0500}"
if DEADLINE_EPOCH=$(date -j -f "%Y-%m-%d %H:%M:%S%z" "${DEADLINE_CLEAN}" +%s 2>/dev/null); then
  :
elif DEADLINE_EPOCH=$(date -d "${DEADLINE_ISO}" +%s 2>/dev/null); then
  :
else
  DEADLINE_EPOCH=0
fi

if [ "${DEADLINE_EPOCH}" -gt 0 ]; then
  SECS=$((DEADLINE_EPOCH - NOW_EPOCH))
  if [ "${SECS}" -gt 0 ]; then
    H=$((SECS / 3600))
    M=$(((SECS % 3600) / 60))
    DEADLINE_TAG="⏳ ${H}h${M}m"
  else
    DEADLINE_TAG="⌛ PAST"
  fi
else
  DEADLINE_TAG="⏳ ?"
fi

BRANCH=$(git -C "$(pwd)" branch --show-current 2>/dev/null || echo "no-git")

printf 'TriageGuard · %s · %s' "${DEADLINE_TAG}" "${BRANCH}"
