#!/usr/bin/env python3
"""Refresh watchlist data: intraday quote + 5-min sparkline, daily SMAs/RSI/52w.
Exits early outside 4:00-16:10 ET on weekdays unless FORCE=1 (or --force)."""
import json, datetime, pathlib, os, sys, zoneinfo
ET = zoneinfo.ZoneInfo("America/New_York")
now = datetime.datetime.now(ET)
force = os.environ.get("FORCE") in ("1", "true") or "--force" in sys.argv
in_hours = now.weekday() < 5 and datetime.time(4, 0) <= now.time() <= datetime.time(16, 10)
if not (in_hours or force):
    print(f"Outside market hours ({now:%a %H:%M ET}); skipping. Use FORCE=1 to override."); sys.exit(0)
import yfinance as yf
D = pathlib.Path(__file__).parent
cfg = json.loads((D/"static.json").read_text())
def phase(t):
    if t.weekday() >= 5: return "closed"
    m = t.hour*60 + t.minute
    return "open" if 570 <= m < 960 else "pre" if 240 <= m < 570 else "after" if 960 <= m < 1200 else "closed"
rows = []
for p in cfg["portfolio"]:
    tk = yf.Ticker(p["ticker"])
    h = tk.history(period="2y")["Close"].dropna()
    bars = tk.history(period="1d", interval="5m").dropna()
    sess = bars.index[-1].date() if len(bars) else h.index[-1].date()
    prev_series = h[h.index.date < sess]
    prev = float(prev_series.iloc[-1]) if len(prev_series) else float(h.iloc[-2])
    try: price = float(tk.fast_info.last_price)
    except Exception: price = float(bars["Close"].iloc[-1]) if len(bars) else float(h.iloc[-1])
    hist = h.copy()
    if hist.index[-1].date() == sess: hist.iloc[-1] = price
    last52 = hist[hist.index >= hist.index[-1] - datetime.timedelta(days=365)]
    d = hist.diff(); g = d.clip(lower=0).ewm(alpha=1/14, adjust=False).mean(); l = (-d.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    r = dict(p, price=round(price, 2), prev_close=round(prev, 2), price_date=str(sess),
             day_chg=round(price-prev, 2), day_pct=round((price/prev-1)*100, 2),
             day_high=round(float(bars["High"].max()), 2) if len(bars) else None,
             day_low=round(float(bars["Low"].min()), 2) if len(bars) else None,
             volume=int(bars["Volume"].sum()) if len(bars) else None,
             quote_time=(bars.index[-1] + datetime.timedelta(minutes=5)).astimezone(ET).strftime("%a %b %d %I:%M %p ET") if len(bars) else None,
             spark=[round(float(x), 2) for x in bars["Close"]],
             low52=round(float(min(last52.min(), price)), 2), high52=round(float(max(last52.max(), price)), 2),
             sma20=round(float(hist.tail(20).mean()), 2), sma50=round(float(hist.tail(50).mean()), 2),
             sma200=round(float(hist.tail(200).mean()), 2), rsi14=round(float(100-100/(1+g.iloc[-1]/l.iloc[-1])), 1))
    r["ret_pct"] = round((price/p["entry_price"]-1)*100, 2); r["value"] = round(p["units"]*price, 2)
    r["pl"] = round(p["units"]*(price-p["entry_price"]), 2)
    rows.append(r)

def premarket_row(sym):
    """Pre-market / open snapshot for one ticker. Every missing value stays None ('—' on the page)."""
    tk = yf.Ticker(sym); out = {"ticker": sym}
    try: info = tk.info or {}
    except Exception: info = {}
    out["name"] = info.get("shortName") or info.get("longName")
    try: bars = tk.history(period="1d", interval="5m", prepost=True).dropna()
    except Exception: bars = None
    try: daily = tk.history(period="10d")["Close"].dropna()
    except Exception: daily = None
    if bars is not None and len(bars): sess = bars.index[-1].astimezone(ET).date()
    elif daily is not None and len(daily): sess = daily.index[-1].date()
    else: out["error"] = "no data"; return out
    out["session"] = str(sess)
    prev = None
    if daily is not None and len(daily):
        ps = daily[daily.index.date < sess]
        if len(ps): prev = float(ps.iloc[-1])
    if prev is None and info.get("regularMarketPreviousClose"): prev = float(info["regularMarketPreviousClose"])
    out["prev_close"] = round(prev, 2) if prev else None
    pre = reg = None
    if bars is not None and len(bars):
        loc = bars.index.tz_convert(ET); mins = loc.hour*60 + loc.minute
        day = loc.date == sess
        pre = bars[day & (mins >= 240) & (mins < 570)]; reg = bars[day & (mins >= 570) & (mins < 960)]
    if pre is not None and len(pre):
        out["pm_high"] = round(float(pre["High"].max()), 2); out["pm_low"] = round(float(pre["Low"].min()), 2)
        v = int(pre["Volume"].sum()); out["pm_volume"] = v if v > 0 else None
        out["pm_last"] = round(float(pre["Close"].iloc[-1]), 2)
        out["pm_time"] = (pre.index[-1] + datetime.timedelta(minutes=5)).astimezone(ET).strftime("%a %b %d %I:%M %p ET")
    pmp = info.get("preMarketPrice")
    if pmp:
        out["pm_price"] = round(float(pmp), 2)
        if info.get("preMarketTime"): out["pm_time"] = datetime.datetime.fromtimestamp(info["preMarketTime"], ET).strftime("%a %b %d %I:%M %p ET")
    elif out.get("pm_last") is not None: out["pm_price"] = out["pm_last"]
    if reg is not None and len(reg):
        out["open"] = round(float(info.get("regularMarketOpen") or reg["Open"].iloc[0]), 2)  # official open preferred over first 5m bar
        try: out["price"] = round(float(tk.fast_info.last_price), 2)
        except Exception: out["price"] = round(float(reg["Close"].iloc[-1]), 2)
        out["quote_time"] = (reg.index[-1] + datetime.timedelta(minutes=5)).astimezone(ET).strftime("%a %b %d %I:%M %p ET")
    # gap = open (once open) else pre-market price, vs previous close
    ref = out.get("open") if out.get("open") is not None else out.get("pm_price")
    if ref is not None and prev:
        out["gap"] = round(ref - prev, 2); out["gap_pct"] = round((ref/prev - 1)*100, 2); out["gap_basis"] = "open" if out.get("open") is not None else "pre-market"
    if out.get("price") is not None and prev: out["day_pct"] = round((out["price"]/prev - 1)*100, 2)
    return out
pml = json.loads((D/"premarket.json").read_text())["tickers"] if (D/"premarket.json").exists() else []
premarket = []
for sym in pml:
    try: premarket.append(premarket_row(sym))
    except Exception as e: premarket.append({"ticker": sym, "error": type(e).__name__})
data = {"updated": now.strftime("%a %b %d, %Y %I:%M:%S %p ET"), "updated_iso": now.isoformat(), "market": phase(now),
        "rows": rows, "premarket": premarket, "gdx_detail": cfg["gdx_detail"],
        "note": "Quotes: Yahoo Finance via yfinance (may be delayed). 5-min intraday bars for the sparkline. SMA/RSI(14, Wilder)/52w from daily closes incl. today's price."}
(D/"data.json").write_text(json.dumps(data, indent=1))
(D/"index.html").write_text((D/"template.html").read_text().replace("/*DATA*/null", json.dumps(data)))
print("updated", data["updated"], [(r["ticker"], r["price"], r["day_pct"]) for r in rows], [(r["ticker"], r.get("pm_price"), r.get("gap_pct")) for r in premarket])
