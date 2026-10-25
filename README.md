# My Market Radar
A public stock watchlist page: https://my-market-radar.github.io/

## Add a ticker
Add an entry to `portfolio` in `static.json`, for example:
`{"ticker":"NVDA","name":"NVIDIA","date_added":"2026-10-26","entry_price":123.45,"units":100}`.
The `analyst` object is optional. Leave it out and the page shows N/A.
The GDX detail section lives in `gdx_detail`.

## Refresh
```
pip install yfinance
python3 refresh.py   # re-pulls prices, 20/50/200-day SMA, RSI(14), 52-week range; rewrites data.json + index.html
./publish.sh         # commits and pushes to GitHub Pages
```

## Live updates
The GitHub Actions workflow `.github/workflows/live.yml` runs `refresh.py` every 5 minutes on weekdays (cron `*/5 13-21 * * 1-5` UTC). The script skips any run outside 9:25 AM–4:10 PM ET, and the workflow commits `data.json` and `index.html` only when they change. The page re-fetches `data.json` every 60 seconds.
To run it manually: `gh workflow run live.yml -f force=true`. GitHub can delay or skip scheduled runs when it's under load.

## AI Insight cards (summaries.json)
Each ticker gets an "AI Insight by Grok Bot" card, which is driven by the committed file `summaries.json`. The page re-fetches it, cache-busted, every 60 s along with `data.json`. A ticker with no entry shows no card. `refresh.py` and the workflow never touch this file.

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

Data comes from Yahoo Finance via yfinance. A value that isn't available shows as —. The live workflow runs every 5 minutes on weekdays from 08:00 to 21:55 UTC, and the script only does work between 4:00 AM and 4:10 PM ET, which covers both EDT and EST.

**Adding or removing tickers:**
- **On the site:** type a ticker in the Pre-Market box and click **+ Add ticker**. That opens a prefilled GitHub issue (`premarket add: TSLA`, label `premarket`). Click **Submit** while signed in as traderkr. Each row's ✕ button opens a `premarket remove: TSLA` issue the same way. The `premarket-list` workflow only acts on issues opened by traderkr. It checks the ticker against Yahoo, updates `premarket.json`, refreshes the data, commits, comments the result and closes the issue. Your device shows the pending row right away until the data includes it.
- **In chat:** ask Stock Tracker, e.g. "add TSLA to my pre-market list", and it will make the change for you.
- **By hand:** edit `premarket.json`, or run `gh issue create -R my-market-radar/my-market-radar.github.io -t "premarket add: TSLA" -b ""`.

No token is embedded in the page.
