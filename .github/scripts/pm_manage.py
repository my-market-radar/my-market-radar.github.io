#!/usr/bin/env python3
"""Handle 'premarket add: TSLA' / 'premarket remove: TSLA' issue titles. Reads the title from env ISSUE_TITLE.
Writes a result message to $GITHUB_OUTPUT (msg, changed)."""
import os, re, json, pathlib
P = pathlib.Path("premarket.json")
title = os.environ.get("ISSUE_TITLE", "").strip()
m = re.fullmatch(r"(?i)premarket\s+(add|remove)\s*:\s*([A-Za-z]{1,5}(?:[.-][A-Za-z]{1,2})?)", title)
def out(msg, changed):
    with open(os.environ["GITHUB_OUTPUT"], "a") as f: f.write(f"changed={changed}\nmsg<<EOF\n{msg}\nEOF\n")
    print(msg)
if not m: out("Couldn't parse the title. Use `premarket add: TSLA` or `premarket remove: TSLA` (1–5 letters, optional .X or -X).", "false"); raise SystemExit
act, sym = m.group(1).lower(), m.group(2).upper()
cfg = json.loads(P.read_text()) if P.exists() else {"tickers": []}
if act == "remove":
    if sym not in cfg["tickers"]: out(f"{sym} isn't on the pre-market list; nothing to remove.", "false"); raise SystemExit
    cfg["tickers"].remove(sym); P.write_text(json.dumps(cfg, indent=1)+"\n"); out(f"✅ Removed **{sym}** from the pre-market list.", "true"); raise SystemExit
if sym in cfg["tickers"]: out(f"{sym} is already on the pre-market list.", "false"); raise SystemExit
import yfinance as yf
ysym = sym.replace(".", "-")
try: h = yf.Ticker(ysym).history(period="5d")
except Exception: h = None
if h is None or h.empty: out(f"❌ Yahoo Finance has no price data for `{sym}`, so it wasn't added.", "false"); raise SystemExit
cfg["tickers"].append(ysym); P.write_text(json.dumps(cfg, indent=1)+"\n")
out(f"✅ Added **{ysym}** to the pre-market list (last Yahoo close {h['Close'].iloc[-1]:.2f} on {h.index[-1].date()}). Live at https://my-market-radar.github.io/ in about a minute.", "true")
