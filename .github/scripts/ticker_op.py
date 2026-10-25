#!/usr/bin/env python3
"""One-tap ticker add/remove (run by .github/workflows/ticker.yml).
Env: OP (add|remove), LIST (premarket|watchlist), TICKER, SITE_PASSWORD.
Updates premarket.enc.json or static.enc.json and always writes lastop.enc.json (shown on the page)."""
import os, re, sys, json, datetime, zoneinfo, urllib.request, html, pathlib
sys.path.insert(0, os.getcwd())
import sitecrypt
ET = zoneinfo.ZoneInfo("America/New_York"); now = datetime.datetime.now(ET)
op, lst, raw = os.environ.get("OP", "").strip().lower(), os.environ.get("LIST", "").strip().lower(), os.environ.get("TICKER", "").strip().upper()
status = {"op": op, "list": lst, "ticker": raw, "at": now.isoformat(), "at_text": now.strftime("%a %b %d %I:%M %p ET")}
def done(ok, msg):
    status.update(ok=ok, msg=msg); sitecrypt.save("lastop.enc.json", status); print(("OK: " if ok else "ERROR: ") + msg); sys.exit(0)
if op not in ("add", "remove") or lst not in ("premarket", "watchlist"): done(False, "Unknown operation.")
if not re.fullmatch(r"[A-Z]{1,5}([.-][A-Z]{1,2})?", raw): done(False, f"“{raw[:12]}” isn't a valid ticker (1–5 letters, optional .X or -X).")
sym = raw.replace(".", "-"); status["ticker"] = sym
PM, ST = pathlib.Path("premarket.enc.json"), pathlib.Path("static.enc.json")
if lst == "premarket":
    cfg = sitecrypt.load(PM, {"tickers": []}); have = cfg["tickers"]
else:
    cfg = sitecrypt.load(ST); have = [p["ticker"] for p in cfg["portfolio"]]
label = "Pre-Market list" if lst == "premarket" else "Watchlist"
if op == "remove":
    if sym not in have: done(False, f"{sym} isn't on the {label}.")
    if lst == "premarket": cfg["tickers"].remove(sym); sitecrypt.save(PM, cfg)
    else: cfg["portfolio"] = [p for p in cfg["portfolio"] if p["ticker"] != sym]; sitecrypt.save(ST, cfg)
    done(True, f"Removed {sym} from the {label}.")
if sym in have: done(False, f"{sym} is already on the {label}.")
import yfinance as yf
tk = yf.Ticker(sym)
try: h = tk.history(period="5d")["Close"].dropna()
except Exception: h = None
if h is None or h.empty: done(False, f"Yahoo Finance has no price data for {sym}. Check the ticker.")
if lst == "premarket":
    cfg["tickers"].append(sym); sitecrypt.save(PM, cfg); done(True, f"Added {sym} to the Pre-Market list.")
try: info = tk.info or {}
except Exception: info = {}
m = now.hour * 60 + now.minute; wk = now.weekday() < 5
price, basis = None, None
if wk and 240 <= m < 570 and info.get("preMarketPrice"): price, basis = info["preMarketPrice"], "pre-market price"
elif wk and 570 <= m < 960:
    try: price, basis = float(tk.fast_info.last_price), "regular-session price"
    except Exception: pass
if price is None: price, basis = float(h.iloc[-1]), f"last close ({h.index[-1].date()})"
def marketbeat():
    exch = {"NMS": "NASDAQ", "NGM": "NASDAQ", "NCM": "NASDAQ", "NYQ": "NYSE", "PCX": "NYSEARCA", "ASE": "NYSEAMERICAN"}.get(info.get("exchange"))
    for ex in ([exch] if exch else []) + ["NASDAQ", "NYSE", "NYSEARCA"]:
        url = f"https://www.marketbeat.com/stocks/{ex}/{sym.replace('-', '.')}/forecast/"
        try:
            t = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=15).read().decode("utf-8", "ignore")
        except Exception: continue
        t = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)))
        r = re.search(r'consensus rating of "([^"]+?)\.?"', t); n = re.search(r"Out of the (\d+) analysts", t)
        pt = re.search(r"average price target is \$([\d,.]+)", t)
        if not (r and n): continue
        c = {k.lower(): int(v) for v, k in re.findall(r"(\d+) have given an? (strong buy|buy|hold|sell|strong sell) rating", t, re.I)}
        buy, sell = c.get("buy", 0) + c.get("strong buy", 0), c.get("sell", 0) + c.get("strong sell", 0)
        return {"rating": r.group(1), "analysts": int(n.group(1)), "breakdown": f"{buy} Buy / {c.get('hold', 0)} Hold / {sell} Sell",
                "target": round(float(pt.group(1).replace(",", "")), 2) if pt else None, "source": "MarketBeat consensus",
                "url": url, "as_of": now.strftime("%Y-%m-%d")}
    return None
try: an = marketbeat()
except Exception: an = None
row = {"ticker": sym, "name": info.get("shortName") or info.get("longName") or sym, "date_added": now.strftime("%Y-%m-%d"),
       "entry_price": round(float(price), 2), "entry_basis": basis, "units": 100}
if an: row["analyst"] = an
cfg["portfolio"].append(row); sitecrypt.save(ST, cfg)
done(True, f"Added {sym} to the Watchlist: 100 units at ${row["entry_price"]:.2f}, {basis}; analysts: {'MarketBeat' if an else 'N/A'}.")
