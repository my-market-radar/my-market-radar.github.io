#!/usr/bin/env bash
# Usage: ./push_summaries.sh path/to/summaries.json [repo_dir]
# Validates the plaintext JSON, encrypts it with WATCHLIST_SITE_PASSWORD (read from a login shell; never printed)
# into summaries.enc.json, then commits and pushes ONLY that file (normal push, no force).
set -euo pipefail
SRC="$(realpath "${1:?usage: push_summaries.sh path/to/summaries.json [repo_dir]}")"
REPO="${2:-$(cd "$(dirname "$0")" && pwd)/publish}"
python3 -c 'import json,sys;d=json.load(open(sys.argv[1]));assert isinstance(d,dict)
for t,v in d.items(): assert isinstance(v.get("summary"),str) and isinstance(v.get("citations",[]),list),t' "$SRC"
[ -d "$REPO/.git" ] || git clone -q https://github.com/my-market-radar/my-market-radar.github.io.git "$REPO"
cd "$REPO"
git pull -q --rebase origin main
export SITE_PASSWORD="${WATCHLIST_SITE_PASSWORD:-$(bash -lc 'printf %s "$WATCHLIST_SITE_PASSWORD"')}"
[ -n "$SITE_PASSWORD" ] || { echo "WATCHLIST_SITE_PASSWORD is not set" >&2; exit 1; }
python3 - "$SRC" <<'PY'
import json, sys, pathlib, sitecrypt
new = json.loads(pathlib.Path(sys.argv[1]).read_text())
p = pathlib.Path("summaries.enc.json")
if p.exists() and sitecrypt.load(p) == new: print("summaries unchanged"); sys.exit(0)
sitecrypt.save(p, new)
PY
unset SITE_PASSWORD
git add summaries.enc.json
if git diff --cached --quiet; then exit 0; fi
git -c user.name=traderkr -c user.email=traderkr@users.noreply.github.com commit -q -m "Update AI summaries (encrypted) $(TZ=America/New_York date '+%F %H:%M %Z')" -- summaries.enc.json
for i in 1 2 3; do git push -q origin main && { echo "pushed"; exit 0; }; git pull -q --rebase origin main; done
echo "push failed" >&2; exit 1
