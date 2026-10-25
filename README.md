# My Market Radar
A public stock watchlist page: https://traderkr.github.io/market-radar/

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

## AI summaries (Perplexity)
`summarize.py` asks the Perplexity `sonar` model for a 3–4 sentence summary of each ticker, with citations. It writes them to `summaries.json`, and the page shows each one as an "AI Insight" card. The `summaries.yml` workflow runs it at about 9:45 AM, 12:30 PM and 4:15 PM ET on weekdays and skips a ticker whose summary is under 3 hours old. You can also run it by hand. It needs the `PERPLEXITY_API_KEY` repo secret. AI-generated summaries are not investment advice.
