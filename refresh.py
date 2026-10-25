#!/usr/bin/env python3
"""Re-pull prices/MAs/52w/RSI for every ticker in static.json, write data.json, rebuild index.html."""
import json, datetime, pathlib, zoneinfo
import yfinance as yf
D = pathlib.Path(__file__).parent
cfg = json.loads((D/"static.json").read_text())
rows = []
for p in cfg["portfolio"]:
    h = yf.Ticker(p["ticker"]).history(period="2y")["Close"].dropna()
    c = float(h.iloc[-1]); prev = float(h.iloc[-2])
    last52 = h[h.index >= h.index[-1] - datetime.timedelta(days=365)]
    d = h.diff(); g = d.clip(lower=0).ewm(alpha=1/14, adjust=False).mean(); l = (-d.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rsi = float(100 - 100/(1 + g.iloc[-1]/l.iloc[-1]))
    r = dict(p, price=round(c,2), price_date=str(h.index[-1].date()), day_chg=round(c-prev,2), day_pct=round((c/prev-1)*100,2),
             low52=round(float(last52.min()),2), high52=round(float(last52.max()),2),
             sma20=round(float(h.tail(20).mean()),2), sma50=round(float(h.tail(50).mean()),2), sma200=round(float(h.tail(200).mean()),2), rsi14=round(rsi,1))
    r["ret_pct"] = round((c/p["entry_price"]-1)*100,2); r["value"] = round(p["units"]*c,2); r["pl"] = round(p["units"]*(c-p["entry_price"]),2)
    rows.append(r)
now = datetime.datetime.now(zoneinfo.ZoneInfo("America/New_York")).strftime("%a %b %d, %Y %I:%M %p ET")
data = {"updated": now, "rows": rows, "gdx_detail": cfg["gdx_detail"],
        "note": "Prices: Yahoo Finance daily closes via yfinance (52w range from closing prices). SMA = simple MA of closes; RSI(14) Wilder."}
(D/"data.json").write_text(json.dumps(data, indent=1))
tpl = (D/"template.html").read_text()
(D/"index.html").write_text(tpl.replace("/*DATA*/null", json.dumps(data)))
print(json.dumps(rows, indent=1)); print("updated", now)
