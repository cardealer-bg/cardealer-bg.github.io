#!/usr/bin/env python3
"""Raw ad data (as read from a Polovni automobili ad page) -> car JSON for the A4 sheet.
Usage: build_car.py raw.json out.json      (raw may also be a .jsonl with one ad per line -> out is a folder)
Raw keys: id, url, title, price, price_note, published, f{label:value}, safety[], equipment[], condition[], highlights[], note."""
import json, os, re, sys

MAKE_FIX = {"Mercedes Benz": "Mercedes-Benz", "Citroen": "Citroën", "Skoda": "Škoda"}
FUEL_FIX = {"Benzin + Gas (TNG)": "Benzin + TNG", "Benzin + Metan (CNG)": "Benzin + CNG", "Električni pogon": "Električni"}
EQ_FIX = {"Radio/Kasetofon": "Radio", "Ekran na dodiru": "Ekran na dodir", "Ekran na dodirom": "Ekran na dodir", "Naslon za ruke": "Naslon za ruku"}
WORD_FIX = [(r"\bpracenj", "praćenj"), (r"\bkocenj", "kočenj"), (r"\bvucu\b", "vuču"), (r"\bsedista\b", "sedišta"),
            (r"\bhladjenj", "hlađenj"), (r"\bsaltanje\b", "šaltanje"), (r"\bvozaca\b", "vozača"), (r"\bmasaza\b", "masaža"),
            (r"\bvoznje\b", "vožnje"), (r"\bDistronik\b", "Distronic"), (r"\bdistronik\b", "Distronic"), (r"\bVirtualna\b", "Virtuelna"),
            (r"\bvirtualna\b", "virtuelna"), (r"\bHeadup\b", "Head-up"), (r"\bheadup\b", "head-up"), (r"\bKeyles\b", "Keyless"),
            (r"\bpunjac\b", "punjač"), (r"\bWifi punjač\b", "Bežični punjač"), (r"\bsvetleci\b", "svetleći"), (r"\bSvetleci\b", "Svetleći"),
            (r"\bLed\b", "LED"), (r"\bled\b", "LED"), (r"\bIq\b", "IQ"), (r"\bkozom\b", "kožom"), (r"\bpresvucena\b", "presvučena")]

def fix_words(s):
    for a, b in WORD_FIX: s = re.sub(a, b, s)
    s = s.strip()
    return s[:1].upper() + s[1:] if s else s

def dedupe(xs):
    out, seen = [], set()
    for x in xs:
        k = x.lower()
        if x and k not in seen: seen.add(k); out.append(x)
    return out

def build(r):
    f = r.get("f", {})
    g = lambda k: (f.get(k) or "").strip()
    make_raw, model = g("Marka"), g("Model")
    make = MAKE_FIX.get(make_raw, make_raw)
    title = re.sub(r"\s*\d{4}\.\s*godište.*$", "", r.get("title", "")).strip()
    title = re.sub(r"\s*\|.*$", "", title).replace("(može zamena)", "").strip()
    variant = title
    for p in (make_raw, make, model):
        if p and variant.lower().startswith(p.lower()): variant = variant[len(p):].strip()
    variant = re.sub(r"\s*/\s*", " · ", variant).strip(" ·")
    m = re.match(r"(\d+)/(\d+)", g("Snaga motora"))
    power = f"{m.group(1)} kW / {m.group(2)} KS" if m else g("Snaga motora")
    gear = g("Menjač").replace("Automatski / poluautomatski", "Automatski")
    gear = re.sub(r"Manuelni (\d) brzin\w*", r"Manuelni, \1 brzina", gear)
    ccm = g("Kubikaža").replace("cm3", "cm³")
    slot4 = ("Kubikaža", ccm) if ccm else (("Baterija", g("Kapacitet baterije")) if g("Kapacitet baterije") else ("Kubikaža", ""))
    doors = " · ".join(x for x in (g("Broj vrata"), g("Broj sedišta")) if x)
    interior = ", ".join(x for x in (g("Materijal enterijera").replace("Kombinovana koža", "Komb. koža"), g("Boja enterijera").lower()) if x)
    atest = g("Atestiran").replace("do:", "").strip()
    slot12 = ("Atestiran do", atest) if atest else ("Oštećenje", g("Oštećenje"))
    specs = [("Godište", g("Godište")), ("Kilometraža", g("Kilometraža")), ("Gorivo", FUEL_FIX.get(g("Gorivo"), g("Gorivo"))), slot4,
             ("Snaga", power), ("Menjač", gear), ("Pogon", g("Pogon")), ("Karoserija", g("Karoserija").replace(" (MiniVan)", "")),
             ("Boja", g("Boja")), ("Klima", g("Klima").replace(" klima", "")), ("Emisiona klasa", g("Emisiona klasa motora")), slot12,
             ("Vrata / sedišta", doors), ("Enterijer", interior), ("Registrovan do", g("Registrovan do").rstrip(".")), ("Poreklo", g("Poreklo vozila"))]
    specs = [[k, v or "—"] for k, v in specs]
    hl = dedupe([fix_words(h) for h in r.get("highlights") or []])
    eq = dedupe([EQ_FIX.get(e, fix_words(e)) for e in r.get("equipment") or []])
    if not eq: eq = hl[:]
    cond = [c for c in (r.get("condition") or []) if c and c != "Polovno vozilo"]
    if g("Oštećenje") == "Nije oštećen" and "Nije oštećen" not in cond: cond.append("Nije oštećen")
    trade = g("Zamena")
    trade = {"DA (Svejedno)": "DA", "DA (Zamena za jeftinije)": "DA, za jeftinije"}.get(trade, trade)
    pn = (r.get("price_note") or "").strip()
    pn = re.sub(r"^\+\s*", "+ ", pn) if pn else ""
    return {"id": str(r["id"]), "url": r.get("url", ""), "make": make, "model": model, "variant": variant,
            "price": r.get("price", ""), "price_note": pn, "published": (r.get("published") or "").rstrip("."),
            "fixed_price": g("Fiksna cena"), "trade_in": trade, "specs": specs, "highlights": hl[:6],
            "safety": dedupe(r.get("safety") or []), "equipment": eq, "condition": cond, "note": (r.get("note") or "").strip()}

if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    if src.endswith(".jsonl"):
        os.makedirs(out, exist_ok=True)
        for line in open(src, encoding="utf-8"):
            if line.strip():
                c = build(json.loads(line)); json.dump(c, open(os.path.join(out, c["id"] + ".json"), "w"), ensure_ascii=False, indent=1)
    else:
        json.dump(build(json.load(open(src))), open(out, "w"), ensure_ascii=False, indent=1)
