#!/usr/bin/env python3
"""Build the CAR DEALER print site (plain static files for any web hosting).
Usage: make_site.py cars.json changes.json pdf_dir out_dir
Output: out_dir/index.html (all data inline, works on any host and from a USB stick),
        out_dir/pdf/*.pdf (copied), out_dir/logo.png."""
import json, os, shutil, sys, html, base64, unicodedata, re
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))

def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()).strip("_")

def main():
    cars = json.load(open(sys.argv[1], encoding="utf-8"))
    changes = json.load(open(sys.argv[2], encoding="utf-8")) if os.path.exists(sys.argv[2]) else []
    pdf_dir, out = sys.argv[3], sys.argv[4]
    os.makedirs(os.path.join(out, "pdf"), exist_ok=True)
    slim = []
    for c in cars:
        src = c.get("pdf_file", "")
        name = os.path.basename(src) if src else f"{slug(c['make'])}_{slug(c['model'])}_{c['id']}.pdf"
        p = os.path.join(pdf_dir, name)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(out, "pdf", name))
        spec = {k: v for k, v in c.get("specs", [])}
        slim.append({"id": c["id"], "make": c["make"], "model": c["model"], "variant": c.get("variant", ""),
                     "price": c.get("price", ""), "year": spec.get("Godište", "").rstrip("."), "km": spec.get("Kilometraža", ""),
                     "fuel": spec.get("Gorivo", ""), "gear": spec.get("Menjač", ""), "power": spec.get("Snaga", ""),
                     "pdf": "pdf/" + name, "url": c.get("url", ""), "sold": bool(c.get("sold")),
                     "added": c.get("added_at", ""), "changed": c.get("changed_at", "")})
    all_pdf = os.path.join(pdf_dir, "CAR_DEALER_sve_liste_A4.pdf")
    if os.path.exists(all_pdf):
        shutil.copy(all_pdf, os.path.join(out, "pdf", "CAR_DEALER_sve_liste_A4.pdf"))
    for f in ("manifest.webmanifest", "sw.js", "icon-192.png", "icon-512.png", "favicon.ico"):
        src = os.path.join(HERE, f) if os.path.exists(os.path.join(HERE, f)) else os.path.join(HERE, "app", f)
        if os.path.exists(src): shutil.copy(src, os.path.join(out, f))
    logo = os.path.join(HERE, "logo_white.png")
    shutil.copy(logo, os.path.join(out, "logo.png"))
    chg = sorted(changes, key=lambda x: x.get("at", ""), reverse=True)[:60]
    stamp = datetime.now(timezone.utc).astimezone().strftime("%d.%m.%Y. %H:%M")
    tpl = open(os.path.join(HERE, "site_template.html"), encoding="utf-8").read()
    page = (tpl.replace("/*CARS*/[]", json.dumps(slim, ensure_ascii=False))
               .replace("/*CHANGES*/[]", json.dumps(chg, ensure_ascii=False))
               .replace("{{UPDATED}}", html.escape(stamp))
               .replace("{{COUNT}}", str(sum(1 for c in slim if not c["sold"]))))
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(page)
    print("ok", out, len(slim), "cars")

if __name__ == "__main__":
    main()
