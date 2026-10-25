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
