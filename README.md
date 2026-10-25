# My Market Radar
A password-protected personal watchlist: https://my-market-radar.github.io/

## How it's protected
The published page carries no readable prices or positions. `refresh.py` encrypts the page data (AES-256-GCM, key from PBKDF2-SHA256 of the site password, see `sitecrypt.py`), and the browser decrypts it after you enter the password. "Remember on this device" stores the derived key, not the password; the 🔒 Lock button forgets it.

Two repository secrets (Settings → Secrets and variables → Actions):
- `SITE_PASSWORD`: the password for the page. Changing it locks out every device until the new password is entered.
- `POSITIONS_JSON`: your entry price, units and date added per ticker, kept out of the public repo, e.g. `{"GDX":{"entry_price":80.20,"units":100,"date_added":"2026-10-25"}}`. Without it the page shows prices and technicals with — for P/L.

Pages must be set to deploy from **GitHub Actions** (Settings → Pages → Source).

## Add a ticker
Add an entry to `portfolio` in `static.json` (ticker, name, optional `analyst`), and add its position to the `POSITIONS_JSON` secret. The GDX detail section lives in `gdx_detail`.

## Live updates
`.github/workflows/live.yml` runs `refresh.py` every 5 minutes on weekdays (cron `*/5 8-21 * * 1-5` UTC; the script only works 4:00 AM–4:10 PM ET) and deploys the built `_site/` straight to Pages. Nothing is committed, so repo history stays clean and the Pages build limit doesn't apply. A push that changes the template, script, `static.json`, `premarket.json` or `summaries.json` also rebuilds and deploys. The page re-fetches its data every 60 seconds while the tab is visible.
Run it manually: `gh workflow run live.yml -f force=true`. GitHub can delay or skip scheduled runs when it's under load.

To test locally: `SITE_PASSWORD=x FORCE=1 python3 refresh.py`, then serve `_site/` (e.g. `python3 -m http.server -d _site`).

## AI Insight cards (summaries.json)
Each ticker gets an "AI Insight by Grok Bot" card, which is driven by the committed file `summaries.json`. The page re-fetches it, cache-busted, every 60 s along with the page data. A ticker with no entry shows no card. The build copies it into the site but never edits it.

```json
{"GDX": {"summary": "3-4 sentences...", "bullets": ["optional", "..."],
         "citations": [{"title": "Source title", "url": "https://..."}],
         "generated_at": "2026-10-26T09:45:00-04:00"}}
```
To update it, run `./push_summaries.sh /path/to/summaries.json`. It validates the file, runs `pull --rebase`, commits only summaries.json and does a normal push.

## Pre-Market list
This is a separate list of tickers, stored in `premarket.json` and kept apart from the 100-unit watchlist. During pre-market (4:00–9:30 AM ET) and regular hours, `refresh.py` records for each ticker:
- the pre-market price, high, low and volume
- the gap ($ and %) vs the previous close
- the previous close
- the open, once the market opens
- the regular price
- the last quote time in ET

Data comes from Yahoo Finance via yfinance. A value that isn't available shows as —. Yahoo pads quiet pre-market slots with flat, zero-volume bars at the previous close; those are ignored, and a ticker with no real pre-market trades says so. The live workflow runs every 5 minutes on weekdays from 08:00 to 21:55 UTC, and the script only does work between 4:00 AM and 4:10 PM ET, which covers both EDT and EST.

**Adding or removing tickers:**
- **On the site:** type a ticker in the Pre-Market box and click **+ Add ticker**. That opens a prefilled GitHub issue (`premarket add: TSLA`, label `premarket`). Click **Submit** while signed in as traderkr. Each row's ✕ button opens a `premarket remove: TSLA` issue the same way. The `premarket-list` workflow only acts on issues opened by traderkr. It checks the ticker against Yahoo, commits `premarket.json`, starts the `live` build, comments the result and closes the issue. Your device shows the pending row right away until the data includes it.
- **In chat:** ask Stock Tracker, e.g. "add TSLA to my pre-market list", and it will make the change for you.
- **By hand:** edit `premarket.json`, or run `gh issue create -R my-market-radar/my-market-radar.github.io -t "premarket add: TSLA" -b ""`.

No token is embedded in the page.
