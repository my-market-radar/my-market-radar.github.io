#!/usr/bin/env python3
"""Handle 'premarket add: TSLA' / 'premarket remove: TSLA' issue titles. Reads the title from env ISSUE_TITLE.
Writes a result message to $GITHUB_OUTPUT (msg, changed)."""
import os, re, sys, pathlib
sys.path.insert(0, os.getcwd())
import sitecrypt  # the list is stored encrypted in premarket.enc.json (needs SITE_PASSWORD)
P = pathlib.Path("premarket.enc.json")
title = os.environ.get("ISSUE_TITLE", "").strip()
m = re.fullmatch(r"(?i)premarket\s+(add|remove)\s*:\s*([A-Za-z]{1,5}(?:[.-][A-Za-z]{1,2})?)", title)
def out(msg, changed):
    with open(os.environ["GITHUB_OUTPUT"], "a") as f: f.write(f"changed={changed}\nmsg<<EOF\n{msg}\nEOF\n")
    print(msg)
if not m: out("Couldn't parse the title. Use `premarket add: TSLA` or `premarket remove: TSLA` (1–5 letters, optional .X or -X).", "false"); raise SystemExit
act, sym = m.group(1).lower(), m.group(2).upper()
cfg = sitecrypt.load(P, {"tickers": []})
if act == "remove":
    if sym not in cfg["tickers"]: out(f"{sym} isn't on the pre-market list; nothing to remove.", "false"); raise SystemExit
    cfg["tickers"].remove(sym); sitecrypt.save(P, cfg); out(f"✅ Removed **{sym}** from the pre-market list.", "true"); raise SystemExit
if sym in cfg["tickers"]: out(f"{sym} is already on the pre-market list.", "false"); raise SystemExit
import yfinance as yf
ysym = sym.replace(".", "-")
try: h = yf.Ticker(ysym).history(period="5d")
except Exception: h = None
if h is None or h.empty: out(f"❌ Yahoo Finance has no price data for `{sym}`, so it wasn't added.", "false"); raise SystemExit
cfg["tickers"].append(ysym); sitecrypt.save(P, cfg)
out(f"✅ Added **{ysym}** to the pre-market list. Live at https://my-market-radar.github.io/ in about a minute.", "true")
