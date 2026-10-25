# My Market Radar
A password-protected personal watchlist: https://my-market-radar.github.io/

## How it's protected
Nothing in this repo or on the site is readable without the password. Every data file is stored and served only as an encrypted blob:
- `static.enc.json`: watchlist config (tickers, positions, analyst data, detail section)
- `premarket.enc.json`: the pre-market ticker list
- `summaries.enc.json`: AI Insight cards
- `data.enc.json`: live data, built by `refresh.py` and deployed straight to Pages (never committed)

Format (`sitecrypt.py`, mirrored in WebCrypto in `template.html`): master key = PBKDF2-SHA256(password, fixed public site salt, 310,000 iterations); each file and each write gets a random 16-byte salt and a 12-byte IV, file key = HKDF-SHA256(master, salt), and the JSON is encrypted with AES-256-GCM. The page HTML/JS is plaintext but carries no data. The lock screen derives the key in the browser and keeps it in memory only. **Remember on this device** is off by default; when ticked it stores the derived master key (never the password) in localStorage. The 🔒 Lock button forgets it. A wrong password shows an error.

Secret: `SITE_PASSWORD` (Settings → Secrets and variables → Actions). Workflows use it to decrypt config and encrypt output. If you change it, re-encrypt the three `.enc.json` files with the new password (`SITE_PASSWORD=old python3 sitecrypt.py dec f.enc.json > f.json`, then `SITE_PASSWORD=new python3 sitecrypt.py enc f.json f.enc.json`, delete the plaintext). Every device will then need the new password. `POSITIONS_JSON` is an optional override for positions; they're normally kept in `static.enc.json`.

Pages deploys from **GitHub Actions**, so only the built `_site/` is served (not the repo files).

**Caveats:** commits before the encryption change still hold the old plaintext data (git history was not rewritten). Issue titles used by the pre-market flow (e.g. `premarket add: TSLA`) are public.

## Edit the watchlist
`SITE_PASSWORD=... python3 sitecrypt.py dec static.enc.json > /tmp/s.json`, edit, then `python3 sitecrypt.py enc /tmp/s.json static.enc.json`, delete the plaintext and commit only the `.enc.json`.

## Live updates
`.github/workflows/live.yml` runs `refresh.py` every 5 minutes on weekdays (cron `*/5 8-21 * * 1-5` UTC; the script only works 4:00 AM–4:10 PM ET) and deploys the built `_site/` straight to Pages. Nothing is committed, so repo history stays clean and the Pages build limit doesn't apply. A push that changes the template, script, `sitecrypt.py` or any `.enc.json` file also rebuilds and deploys. The page re-fetches its data every 60 seconds while the tab is visible.
Run it manually: `gh workflow run live.yml -f force=true`. GitHub can delay or skip scheduled runs when it's under load.

To test locally: `SITE_PASSWORD=<site password> FORCE=1 python3 refresh.py`, then serve `_site/` (e.g. `python3 -m http.server -d _site`).

## AI Insight cards (summaries.enc.json)
Each ticker gets an "AI Insight by Grok Bot" card, which is driven by the committed, encrypted file `summaries.enc.json`. The page re-fetches and decrypts it every 60 s along with the page data. A ticker with no entry shows no card. Plaintext format before encryption:

```json
{"GDX": {"summary": "3-4 sentences...", "bullets": ["optional", "..."],
         "citations": [{"title": "Source title", "url": "https://..."}],
         "generated_at": "2026-10-26T09:45:00-04:00"}}
```
To update it, run `./push_summaries.sh /path/to/summaries.json`. It validates the file, encrypts it with `WATCHLIST_SITE_PASSWORD` (read from a login shell, never printed), commits only `summaries.enc.json` and does a normal push. Keep the plaintext file outside the repo.

## Pre-Market list
This is a separate list of tickers, stored encrypted in `premarket.enc.json` and kept apart from the 100-unit watchlist. During pre-market (4:00–9:30 AM ET) and regular hours, `refresh.py` records for each ticker:
- the pre-market price, high, low and volume
- the gap ($ and %) vs the previous close
- the previous close
- the open, once the market opens
- the regular price
- the last quote time in ET

Data comes from Yahoo Finance via yfinance. A value that isn't available shows as —. Yahoo pads quiet pre-market slots with flat, zero-volume bars at the previous close; those are ignored, and a ticker with no real pre-market trades says so. The live workflow runs every 5 minutes on weekdays from 08:00 to 21:55 UTC, and the script only does work between 4:00 AM and 4:10 PM ET, which covers both EDT and EST.

**Adding or removing tickers (one tap):**
- **On the site:** after unlocking, type a ticker, pick **Pre-Market** or **Watchlist (100 units)**, and tap **+ Add**. Each row's ✕ (on both lists) removes it after a confirm. The page calls the GitHub API (`POST /repos/my-market-radar/my-market-radar.github.io/actions/workflows/ticker.yml/dispatches`) with a fine-grained token, shows a pending row with a spinner, polls every 15 s while an op is pending, and swaps in the real row when the data arrives. Errors (bad ticker, API failure, expired key) show as a red toast.
- **The workflow** `.github/workflows/ticker.yml` (inputs `op` add|remove, `list` premarket|watchlist, `ticker`) runs `.github/scripts/ticker_op.py`: regex check, Yahoo lookup, then it updates `premarket.enc.json` or `static.enc.json`. A watchlist add records today's date (ET), 100 units, and an entry price equal to the pre-market price (4:00–9:30 ET), the regular price (9:30–16:00), or else the last close. It fills analyst consensus from MarketBeat when reachable (TipRanks blocks scripts), else N/A. It writes an encrypted status, `lastop.enc.json`, exposed as `last_op` in `data.enc.json`, then commits, refreshes and deploys Pages. It shares the `live` concurrency group with `live.yml`.
- **The key:** a fine-grained PAT scoped only to this repo (Actions read/write and Metadata read; expires Oct 26, 2027), stored encrypted with the site password in `token.enc.json` and served by Pages. The page decrypts it in memory after unlock and never stores it, even with "remember" on (it's re-decrypted from the remembered key on load). Anyone with the site password can therefore run this repo's workflows. To rotate it, re-encrypt a new token into `token.enc.json` (`{"token": "..."}`) and revoke the old one on GitHub.
- **In chat:** ask Stock Tracker, e.g. "add TSLA to my pre-market list".
- **By hand:** `gh workflow run ticker.yml -R my-market-radar/my-market-radar.github.io -f op=add -f list=premarket -f ticker=TSLA`.

The old GitHub-issue flow (`premarket.yml`) has been removed. Past issue titles like `premarket add: NEM` remain public.
