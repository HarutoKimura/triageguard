 Git & Development Workflow for Stella Web

This repo is maintained by a solo developer (Haruto Kimura) collaborating with AI agents. We follow **GitHub Flow**: feature branches from master, PR review, merge, delete. The rules below exist because git mistakes are expensive and many are irreversible.

## Branch Model

- **`master`** is the canonical, always-deployable state. Never commit directly.
- Work happens on **feature branches** cut from master, one branch per concern.
- After PR merges, the branch is deleted (both local and remote).

### Branch naming

| Prefix | Use for | Example |
|---|---|---|
| `feat/` | New features | `feat/hero-section`, `feat/contact-page` |
| `fix/` | Bug fixes | `fix/mobile-nav-overflow`, `fix/font-loading` |
| `chore/` | Maintenance, deps, CI, refactors with no behavior change | `chore/upgrade-next`, `chore/optimize-images` |
| `docs/` | Documentation only | `docs/architecture-update` |
| `refactor/` | Code restructuring (no behavior change) | `refactor/extract-section-components` |

If you're not sure which prefix fits, ask the user. Do not invent new prefixes.

## Standard Workflow (GitHub Flow)

```bash
# 1. Start from a clean master
git checkout master
git pull

# 2. Cut a new branch
git checkout -b feat/my-thing

# 3. ... make changes, commit incrementally ...

# 4. Run quality gates BEFORE pushing
pnpm lint
pnpm typecheck
pnpm build

# 5. Push (requires user approval — see "Pause-and-confirm" below)
git push -u origin feat/my-thing

# 6. Open PR (requires user approval)
gh pr create --title "..." --body "..."

# 7. After merge, sync local
git checkout master
git pull
git branch -d feat/my-thing
git push origin --delete feat/my-thing  # tidy up remote
```

## Commit Messages

Format: `type: short imperative description`

- **First line**: ≤72 chars, imperative mood (`fix bug` not `fixed bug` or `fixes bug`), no trailing period.
- **Type prefix**: matches branch prefixes — `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`.
- **Body** (optional but recommended for non-trivial changes): blank line, then prose explaining **why**, not **what** (the diff already shows what). Use bullet points for multi-part changes.
- **AI-assisted commits**: always end with the `Co-Authored-By` line (see template below).
- Use **HEREDOC** (`git commit -m "$(cat <<'EOF' ... EOF)"`) for multi-line messages to avoid quoting issues.

### Commit message template

```bash
git commit -m "$(cat <<'EOF'
type: short imperative description

Optional multi-paragraph body explaining the WHY:
- What problem does this solve?
- What alternative approaches were considered?
- Any non-obvious tradeoffs or constraints?

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

### Good vs bad commit messages

| Bad | Good |
|---|---|
| `fix bug` | `fix: mobile nav overflow on small viewports` |
| `update files` | `refactor: extract hero section into standalone component` |
| `WIP` | `feat: add stats counter section with animated numbers` |
| `asdf` | `chore: bump next.js to 15.2` |

## One PR = One Concern

If you can't describe the PR's purpose in one sentence, it's two PRs. Don't mix:
- Bug fix + new feature (split into 2 PRs)
- Refactor + behavior change (refactor first, then change behavior — easier to review)
- Documentation + code change (unless the doc IS the change)

**Exception**: small follow-up fixes discovered while working on the main change can be bundled if they're tightly related and the reviewer can understand both in one read. Use judgment.

## Pre-Commit Quality Gates

Before every commit:

1. **`pnpm lint`** — no lint errors on modified files
2. **`pnpm typecheck`** — no TypeScript errors
3. **`pnpm build`** — production build succeeds (for significant changes)
4. Read your own diff (`git diff --cached`) — does it actually do what the commit message says?

If any of these fail, fix the issue before committing. Do NOT use `--no-verify` to skip pre-commit hooks.

## Pause-and-Confirm: Visible / Destructive Actions

The cost of pausing to confirm is low. The cost of an unwanted action can be very high. **Always confirm with the user before:**

- `git push` to ANY branch (visible to others)
- `gh pr create` (visible — creates a public PR)
- `gh pr merge` (irreversible — once merged, the change is in master)
- `gh pr close` (cancels work the user may want to revisit)
- `git push --force` / `git push -f` (rewrites public history — never to master)
- `git reset --hard` (destroys uncommitted work)
- `git checkout -- <file>` / `git restore <file>` (discards local changes)
- `git clean -fd` (deletes untracked files)
- `git branch -D <branch>` (force-delete unmerged branch)
- `git rebase -i` on a pushed branch (rewrites public history)
- `git commit --amend` on a pushed commit (rewrites public history)
- `--no-verify` flag (bypasses pre-commit hooks — never use unless user explicitly requests it)
- Changing `git config` (affects future commits)
- `gh release create` (publishes a release tag)

When you're about to do one of these, **STOP and ask the user first**. State exactly what you're about to run and why, then wait for explicit approval.

## Standard Things You CAN Do Without Asking

These are local and reversible:

- `git status`, `git diff`, `git log`, `git show`, `git blame`
- `git add <specific-files>` (named files only — see next rule)
- `git commit` (local only — push needs approval)
- `git checkout <existing-branch>` (switch branches, no destructive effect)
- `git checkout -b <new-branch>` (cut a new branch from current HEAD)
- `git stash` / `git stash pop` (temporary save)
- `git fetch --prune` (sync remote refs, no working-tree changes)
- `git branch -d <merged-branch>` (safe delete — git refuses if not merged)
- `git tag <name>` (local tag only — `git push --tags` needs approval)
- `gh pr list`, `gh pr view`, `gh issue list`, `gh issue view` (read-only)

## NEVER use `git add .` or `git add -A`

These are the leading cause of accidental secret leaks and bloated commits. They can:
- Accidentally include `.env` files with API keys
- Stage large binaries you didn't mean to commit
- Pull in editor temp files (`.swp`, `.DS_Store`)
- Stage files from other branches you didn't realize were modified

**Always list specific files**: `git add path/to/file1.tsx path/to/file2.ts`

If you have many files to stage, list them explicitly or use a pattern that excludes secrets:
```bash
git add src/components/sections/*.tsx src/app/page.tsx
```

## After a PR Merges

```bash
git checkout master
git pull                                    # pull merged changes
git branch -d feat/my-feature               # delete local branch
git push origin --delete feat/my-feature    # delete remote branch (tidy)
```

For solo work, **squash-and-merge** is the preferred merge strategy on GitHub.

## Branch Protection: Never Push to Master Directly

`master` is the canonical state. To change it:

1. Cut a feature branch
2. Make changes there
3. Open a PR
4. Merge via the GitHub UI (or `gh pr merge` with explicit user approval)

Direct pushes to master bypass review and break the audit trail.

## When Things Go Wrong

### "I committed to the wrong branch"

```bash
git log --oneline -1
git reset --hard HEAD~1
git checkout <correct-branch>
git cherry-pick <commit-sha>
```

Ask the user before running `git reset --hard`.

### "I made a typo in the commit message"

If not yet pushed: `git commit --amend`
If already pushed: leave it.

### "I have merge conflicts"

```bash
git fetch origin
git rebase origin/master
# resolve conflicts
git add <resolved-files>
git rebase --continue
```

If the conflict is non-trivial, ask the user before resolving.

## Project Context: Solo Developer + AI Agents

- One reviewer reviews their own PRs. Be rigorous about quality.
- Bundling related changes in one PR is OK. Use judgment.
- Always confirm before visible actions. Trust is earned by checking in.
- Use `gh` CLI for all GitHub operations.

## Reference: Common `gh` CLI Commands

```bash
gh pr create --title "..." --body "..."
gh pr list
gh pr view <number>
gh pr merge <number> --squash
gh issue create --title "..." --body "..."
gh issue list
```

Use HEREDOC for multi-line `--body`:

```bash
gh pr create --title "..." --body "$(cat <<'EOF'
## Summary
- Bullet 1

## Test plan
- [x] pnpm build passing
EOF
)"
```