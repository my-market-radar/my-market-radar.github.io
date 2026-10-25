#!/usr/bin/env python3
"""Perplexity AI summaries per ticker -> summaries.json, merged into data.json/index.html.
Skips a ticker if its summary is < 3h old (unless FORCE=1). Keeps the previous summary on failure."""
import json, os, sys, datetime, pathlib, zoneinfo, urllib.request
ET = zoneinfo.ZoneInfo("America/New_York"); D = pathlib.Path(__file__).parent
key = os.environ.get("PERPLEXITY_API_KEY")
if not key: print("PERPLEXITY_API_KEY not set; skipping."); sys.exit(0)
force = os.environ.get("FORCE") in ("1", "true")
S = D/"summaries.json"; sums = json.loads(S.read_text()) if S.exists() else {}
cfg = json.loads((D/"static.json").read_text()); now = datetime.datetime.now(ET)
for p in cfg["portfolio"]:
    t = p["ticker"]; old = sums.get(t)
    if old and not force and now - datetime.datetime.fromisoformat(old["generated_iso"]) < datetime.timedelta(hours=3):
        print(t, "summary fresh; skipping"); continue
    prompt = (f"Give a concise 3-4 sentence market summary of {t} ({p['name']}) as of {now:%B %d, %Y}: what is driving it "
              "today and this week, key price levels (support/resistance), and the bull and bear case in one line each. Plain prose, no headings, no markdown.")
    body = json.dumps({"model": "sonar", "messages": [{"role": "system", "content": "You are a concise, factual markets analyst."},
                                                      {"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.perplexity.ai/chat/completions", data=body,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: res = json.load(r)
        text = res["choices"][0]["message"]["content"].strip()
        cites = res.get("citations") or [x.get("url") for x in res.get("search_results", []) if x.get("url")]
        sums[t] = {"text": text, "citations": cites[:8], "model": res.get("model", "sonar"),
                   "generated": now.strftime("%a %b %d %I:%M %p ET"), "generated_iso": now.isoformat()}
        print(t, "summary updated", len(cites), "citations")
    except Exception as e:
        print(t, "summary failed, keeping previous:", type(e).__name__, getattr(e, "code", ""))
S.write_text(json.dumps(sums, indent=1))
dp = D/"data.json"
if dp.exists():
    data = json.loads(dp.read_text())
    for r in data["rows"]:
        if r["ticker"] in sums: r["ai"] = sums[r["ticker"]]
    dp.write_text(json.dumps(data, indent=1))
    (D/"index.html").write_text((D/"template.html").read_text().replace("/*DATA*/null", json.dumps(data)))
