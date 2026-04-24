#!/usr/bin/env bash
# Block destructive git flags that can lose hackathon work.
# Reads the PreToolUse payload from stdin; exits non-zero + prints a message
# to deny the tool call.

set -euo pipefail

PAYLOAD=$(cat)

# Extract the Bash command string. Accept any JSON shape — fall back to string search.
CMD=$(printf '%s' "${PAYLOAD}" | python3 -c 'import json,sys
try:
  d=json.load(sys.stdin)
  print((d.get("tool_input") or {}).get("command",""))
except Exception:
  pass' 2>/dev/null || true)

if [ -z "${CMD}" ]; then
  # Not a parseable Bash call — allow.
  exit 0
fi

deny() {
  echo "BLOCKED by .claude/hooks/guard-destructive-git.sh: $1" >&2
  exit 2
}

case "${CMD}" in
  *"git push --force"*|*"git push -f"*|*"git push --force-with-lease"*)
    deny "destructive push. Ask the user first." ;;
  *"git reset --hard"*)
    deny "git reset --hard can drop uncommitted work. Stash or commit first." ;;
  *"git clean -f"*|*"git clean -fd"*)
    deny "git clean -f destroys untracked files." ;;
  *"git branch -D"*)
    deny "force-deleting a branch. Confirm with the user." ;;
  *"git checkout -- ."*|*"git restore ."*)
    deny "wholesale discard of working tree. Narrow the scope." ;;
esac

exit 0
