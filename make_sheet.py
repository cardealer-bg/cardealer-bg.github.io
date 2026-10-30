#!/usr/bin/env python3
"""car.json -> A4 PDF.  Usage: make_sheet.py car.json out.pdf
Needs, next to this file: sheet.js, logo_data.js, qr.js (node). Uses Playwright's Chromium."""
import json, os, subprocess, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
# QR "CELA PONUDA" - all of the dealer's ads
DEALER_URL = "https://www.polovniautomobili.com/car-dealer-bg?paPage=adpg&paSection=cndt&paPromo=false&paAdCategory=car"

def main():
    car = json.load(open(sys.argv[1])); out = sys.argv[2]
    qr = lambda u: subprocess.check_output(["node", os.path.join(HERE, "qr.js"), u]).decode()
    if car.get("url"):
        car["qr_svg"] = qr(car["url"])
    car["qr_dealer_svg"] = qr(DEALER_URL)
    js = open(os.path.join(HERE, "logo_data.js")).read() + "\n" + open(os.path.join(HERE, "sheet.js")).read()
    html = ("<!doctype html><html><head><meta charset='utf-8'><style>@page{size:A4;margin:0}html,body{margin:0}</style>"
            f"<script>{js}</script></head><body><div id='root'></div><script>"
            f"var car={json.dumps(car, ensure_ascii=False)};"
            "var st=document.createElement('style');st.textContent=SHEET_CSS;document.head.appendChild(st);"
            "document.getElementById('root').innerHTML=renderSheet(car);document.fonts.ready.then(function(){fitSheet(document);});</script></body></html>")
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page()
        pg.set_content(html, wait_until="load")
        fit = pg.evaluate("document.fonts.ready.then(()=>fitSheet(document))")
        pg.pdf(path=out, format="A4", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        if len(sys.argv) > 3:  # optional PNG preview
            pg.set_viewport_size({"width": 794, "height": 1123}); pg.screenshot(path=sys.argv[3], full_page=False)
        b.close()
    # keep the QR in the json so the web page can show it too
    json.dump(car, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
    print("ok", out, "fit", fit)

if __name__ == "__main__":
    main()
