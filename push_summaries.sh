#!/usr/bin/env bash
# Usage: ./push_summaries.sh path/to/summaries.json [repo_dir]
# Validates the JSON, then commits and pushes ONLY summaries.json to traderkr/market-radar (normal push, no force).
set -euo pipefail
SRC="${1:?usage: push_summaries.sh path/to/summaries.json [repo_dir]}"
REPO="${2:-$(cd "$(dirname "$0")" && pwd)/publish}"
python3 -c 'import json,sys;d=json.load(open(sys.argv[1]));assert isinstance(d,dict)
for t,v in d.items(): assert isinstance(v.get("summary"),str) and isinstance(v.get("citations",[]),list),t' "$SRC"
[ -d "$REPO/.git" ] || git clone -q https://github.com/traderkr/market-radar.git "$REPO"
cd "$REPO"
git pull -q --rebase origin main
cp "$SRC" summaries.json
git add summaries.json
if git diff --cached --quiet; then echo "summaries.json unchanged"; exit 0; fi
git commit -q -m "Update AI summaries $(TZ=America/New_York date '+%F %H:%M %Z')" -- summaries.json
for i in 1 2 3; do git push -q origin main && { echo "pushed"; exit 0; }; git pull -q --rebase origin main; done
echo "push failed" >&2; exit 1
