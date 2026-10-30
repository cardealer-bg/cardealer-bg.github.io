#!/usr/bin/env python3
"""Reads the dealer's ads from Polovni automobili with a real browser (Playwright/Chromium).
Usage: scrape.py out_dir        -> out_dir/list.json  {"total": N|null, "ads": [{id,url,title,price}]}
                                   out_dir/raw/<id>.json  (same shape as tools/primer_raw.json)
                                   out_dir/unread.json    [ids that could not be read]
Exit code 2 = the dealer page could not be read (blocked / empty): nothing must be changed."""
import json, os, re, sys, time
from playwright.sync_api import sync_playwright

DEALER = "https://www.polovniautomobili.com/car-dealer-bg?paAdCategory=car&paPage=adpg&paPromo=false&paSection=cndt"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

LABELS = ["Stanje", "Marka", "Model", "Godište", "Kilometraža", "Karoserija", "Gorivo", "Kubikaža", "Snaga motora",
          "Fiksna cena", "Zamena", "Broj oglasa", "Broj šasije", "Datum objave", "Emisiona klasa motora", "Pogon",
          "Menjač", "Broj vrata", "Broj sedišta", "Strana volana", "Klima", "Boja", "Materijal enterijera",
          "Boja enterijera", "Registrovan do", "Poreklo vozila", "Vlasništvo", "Oštećenje", "Zemlja uvoza", "Kredit",
          "Lizing", "Način prodaje", "Kapacitet baterije", "Atestiran", "Domet", "Snaga baterije", "Garancija",
          "Prešao", "Vrsta goriva", "Kubikaža (cm3)", "Pogonski akumulator", "Snaga (kW/KS)"]
LABELS.sort(key=len, reverse=True)
SECTION_END = {"Opšte informacije", "Dodatne informacije", "Sigurnost", "Oprema", "Stanje", "Opis", "Kontakt",
               "Prijavi oglas", "Slični oglasi", "Ostali oglasi prodavca", "Poruka prodavcu", "Lokacija", "Galerija",
               "Pošalji poruku", "Podeli oglas", "Prijavite oglas", "Pogledajte i", "Izdvojeni oglasi"}
DEALER_TEXT = re.compile(r"kredit|lizing|leasing|ovlašćen|ovlascen|legalnost|stručn|strucn|car dealer|telefon|"
                         r"\+381|\b06\d|pozovite|kontakt|najav|zakon|potrošač|potrosac|tehnički pregled|registracij|"
                         r"probne tablice|otkup|zamena|kupovin|pregledan|garantujemo|garantuje|provera|proverite|"
                         r"www\.|http|@", re.I)

def lines_of(text):
    return [l.strip() for l in text.replace("\xa0", " ").splitlines() if l.strip()]

def find_line(ls, name, start=0):
    for i in range(start, len(ls)):
        if ls[i].rstrip(":").strip().lower() == name.lower():
            return i
    return -1

def section(ls, name, start=0, info=False):
    i = find_line(ls, name, start)
    if i < 0: return [], -1
    out = []
    for l in ls[i + 1:]:
        h = l.rstrip(":").strip()
        if h in SECTION_END and not (info and h == "Stanje"): break
        out.append(l)
    return out, i

def parse_pairs(ls):
    f, i = {}, 0
    while i < len(ls):
        l = ls[i]; hit = None
        for lab in LABELS:
            if l == lab or l.startswith(lab + ":") or l.startswith(lab + "\t") or l.startswith(lab + " "):
                rest = l[len(lab):].lstrip(":\t ").strip()
                if l != lab and not rest: rest = None
                hit = (lab, rest); break
        if hit:
            lab, val = hit
            if not val and i + 1 < len(ls):
                val = ls[i + 1].lstrip(":").strip(); i += 1
            if val and lab not in f: f[lab] = val
        elif l.endswith(":") and i + 1 < len(ls):
            f.setdefault(l[:-1].strip(), ls[i + 1]); i += 1
        i += 1
    return f

def parse_list(ls):
    return [l for l in ls if len(l) <= 70 and not l.endswith(":")]

def make_note(desc_lines):
    text = " ".join(l for l in desc_lines if len(l) > 25)
    sents = re.split(r"(?<=[.!?])\s+", text)
    keep = [s.strip() for s in sents if 20 <= len(s.strip()) <= 260 and not DEALER_TEXT.search(s)]
    return " ".join(keep[:2])

def make_highlights(desc_lines):
    out = []
    for l in desc_lines:
        m = re.match(r"^[-•*✓✔▪►➤–]\s*(.+)$", l)
        if m and 2 < len(m.group(1)) <= 45 and not DEALER_TEXT.search(m.group(1)):
            out.append(m.group(1).strip(" .;,"))
    return out

def parse_ad(title, text, ad_id, url):
    ls = lines_of(text)
    opste, i1 = section(ls, "Opšte informacije", info=True)
    dod, i2 = section(ls, "Dodatne informacije", info=True)
    f = parse_pairs(opste + dod)
    f.pop("Broj šasije", None)
    after = max(i1, i2, 0)
    safety, _ = section(ls, "Sigurnost", after)
    equipment, _ = section(ls, "Oprema", after)
    condition, _ = section(ls, "Stanje", after)
    desc, _ = section(ls, "Opis", after)
    price, note_p = "", ""
    for k, l in enumerate(ls):
        m = re.match(r"^(\d{1,3}(?:\.\d{3})+|\d{3,})\s*€\s*(.*)$", l)
        if m:
            price = m.group(1) + " €"; note_p = m.group(2).strip()
            if not note_p and k + 1 < len(ls) and ls[k + 1].startswith("+"): note_p = ls[k + 1]
            break
    pub = f.get("Datum objave", "")
    return {"id": str(ad_id), "url": url, "title": title.strip(), "price": price, "price_note": note_p,
            "published": pub, "f": f, "safety": parse_list(safety), "equipment": parse_list(equipment),
            "condition": parse_list(condition), "highlights": make_highlights(desc), "note": make_note(desc)}

def ok(raw):
    f = raw["f"]
    return bool(raw["price"] and f.get("Marka") and f.get("Model") and f.get("Godište") and f.get("Kilometraža"))

def main():
    out = sys.argv[1]; os.makedirs(os.path.join(out, "raw"), exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(user_agent=UA, locale="sr-RS", viewport={"width": 1366, "height": 2000})
        pg = ctx.new_page()
        ads, total = {}, None
        for n in range(1, 11):
            url = DEALER + ("" if n == 1 else f"&page={n}")
            try:
                r = pg.goto(url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(2500)
            except Exception as e:
                print("dealer page error", n, e); break
            if r and r.status >= 400: print("dealer page HTTP", r.status); break
            body = pg.inner_text("body")
            open(os.path.join(out, f"dealer_page{n}.txt"), "w").write(body)
            m = re.search(r"od ukupno\s+(\d+)", body)
            if m: total = int(m.group(1))
            new = 0
            for a in pg.query_selector_all("a[href*='/auto-oglasi/']"):
                href = a.get_attribute("href") or ""
                mm = re.search(r"/auto-oglasi/(\d+)/[^?#\"]+", href)
                if not mm or mm.group(1) in ads: continue
                full = "https://www.polovniautomobili.com" + mm.group(0)
                ads[mm.group(1)] = {"id": mm.group(1), "url": full, "title": (a.inner_text() or "").strip()}
                new += 1
            if not new or (total and len(ads) >= total): break
            time.sleep(1.5)
        json.dump({"total": total, "ads": list(ads.values())}, open(os.path.join(out, "list.json"), "w"), ensure_ascii=False, indent=1)
        print("dealer ads found:", len(ads), "total on page:", total)
        if not ads:
            b.close(); sys.exit(2)
        unread = []
        for ad in ads.values():
            raw = None
            for attempt in range(2):
                try:
                    pg.goto(ad["url"], wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(1500)
                    h1 = pg.query_selector("h1")
                    body = pg.inner_text("body")
                    os.makedirs(os.path.join(out, "text"), exist_ok=True)
                    open(os.path.join(out, "text", ad["id"] + ".txt"), "w").write(body)
                    raw = parse_ad(h1.inner_text() if h1 else ad["title"], body, ad["id"], ad["url"])
                    if ok(raw): break
                except Exception as e:
                    print("ad error", ad["id"], e)
                raw = None; time.sleep(3)
            if raw:
                json.dump(raw, open(os.path.join(out, "raw", ad["id"] + ".json"), "w"), ensure_ascii=False, indent=1)
            else:
                unread.append(ad["id"])
            time.sleep(1.2)
        json.dump(unread, open(os.path.join(out, "unread.json"), "w"))
        print("read:", len(ads) - len(unread), "unread:", unread)
        b.close()

if __name__ == "__main__":
    main()
