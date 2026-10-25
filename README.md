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
