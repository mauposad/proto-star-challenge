#!/usr/bin/env bash
# Create an agent worktree that shares the main checkout's .venv and data.
#
# Usage: scripts/new_worktree.sh <track> [base-branch]
#   -> .claude/worktrees/<track> on branch agent/<track>
#
# The worktree gets no venv of its own: `.venv` is a symlink to main's, and
# .claude/settings.local.json sets UV_PROJECT_ENVIRONMENT + UV_NO_SYNC=1 so
# `uv run` never re-syncs. PYTHONPATH=src makes imports resolve to the
# worktree's own src (the editable install points at main's src).
# Remove with: git worktree remove .claude/worktrees/<track>
set -euo pipefail

track="${1:?usage: $0 <track> [base-branch]}"
base="${2:-HEAD}"
main="$(git rev-parse --show-toplevel)"
wt="$main/.claude/worktrees/$track"

git -C "$main" worktree add -b "agent/$track" "$wt" "$base"

ln -s "$main/.venv" "$wt/.venv"
for d in raw external interim; do
  # fresh checkout holds only .gitkeep; rmdir fails loudly if anything else is there
  if [ -d "$wt/data/$d" ]; then rm -f "$wt/data/$d/.gitkeep"; rmdir "$wt/data/$d"; fi
  ln -s "$main/data/$d" "$wt/data/$d"
done
# keep git status clean: hide the replaced .gitkeep files and the .venv symlink
git -C "$wt" update-index --skip-worktree data/raw/.gitkeep data/external/.gitkeep data/interim/.gitkeep
exclude="$(git -C "$main" rev-parse --path-format=absolute --git-common-dir)/info/exclude"
grep -qxF '/.venv' "$exclude" 2>/dev/null || echo '/.venv' >> "$exclude"
mkdir -p "$wt/data/processed"
for d in external protostar; do
  [ -e "$main/data/processed/$d" ] && ln -sfn "$main/data/processed/$d" "$wt/data/processed/$d"
done

cat <<EOF
Worktree ready: $wt (branch agent/$track)
Run commands there with the shared env, e.g.:
  cd $wt && UV_PROJECT_ENVIRONMENT=$main/.venv UV_NO_SYNC=1 PYTHONPATH=src OMP_NUM_THREADS=3 make check
EOF
