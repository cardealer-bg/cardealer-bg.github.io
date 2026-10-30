#!/usr/bin/env python3
"""Daily check of the ads -> data/*.json, pdf/*.pdf and the site, all inside this repository.
Usage: update.py work_dir      (work_dir has list.json, raw/<id>.json, unread.json from scrape.py)
Run from the repository root. Writes report.md (Serbian) into work_dir."""
import json, os, re, subprocess, sys, unicodedata, shutil, datetime

T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, T)
from build_car import build  # noqa: E402

def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()).strip("_")

def norm(x):
    x = unicodedata.normalize("NFKD", x.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", x).strip()

def list_diff(label, old, new):
    o = {norm(x): x for x in old or []}; n = {norm(x): x for x in new or []}
    d = [{"field": label, "old": "", "new": "+ " + n[k]} for k in n if k not in o]
    d += [{"field": label, "old": o[k], "new": ""} for k in o if k not in n]
    return d

def main():
    work = sys.argv[1]
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lst = json.load(open(os.path.join(work, "list.json")))
    unread = set(json.load(open(os.path.join(work, "unread.json"))))
    cars = json.load(open("data/cars.json", encoding="utf-8"))
    changes = json.load(open("data/changes.json", encoding="utf-8"))
    by = {c["id"]: c for c in cars}
    active = {a["id"]: a for a in lst["ads"]}
    full_list = lst.get("total") is not None and len(active) >= lst["total"]
    rep = {"Novi": [], "Promena cene": [], "Izmene podataka": [], "Uklonjeni": [], "Vraćeni": [], "Nije pročitano": []}
    new_pdfs = []

    def log(c, typ, details):
        rec = {"at": now, "type": typ, "details": details}
        c["changes"] = (c.get("changes", []) + [rec])[-20:]
        changes.append({"at": now, "id": c["id"], "car": f'{c["make"]} {c["model"]} {c.get("variant", "")}'.strip(),
                        "type": typ, "details": details})

    for i, ad in active.items():
        if i in unread or not os.path.exists(os.path.join(work, "raw", i + ".json")):
            rep["Nije pročitano"].append(f'{ad.get("title") or i} (#{i})'); continue
        n = build(json.load(open(os.path.join(work, "raw", i + ".json"), encoding="utf-8")))
        o = by.get(i)
        if o is None:
            typ_list = [("nov", [])]
        else:
            typ_list = []
            if o.get("price") != n["price"]:
                typ_list.append(("cena", [{"field": "Cena", "old": o.get("price", ""), "new": n["price"]}]))
            d = []
            if norm(o.get("variant", "")) != norm(n["variant"]):
                d.append({"field": "Varijanta", "old": o.get("variant", ""), "new": n["variant"]})
            os_ = dict(o.get("specs", []))
            for k, v in n["specs"]:
                if k in os_ and norm(os_[k]) != norm(v):
                    d.append({"field": k, "old": os_[k], "new": v})
            # empty list on the page = probably not loaded; never count that as "everything removed"
            for fld, lab in (("equipment", "Oprema"), ("safety", "Sigurnost"), ("condition", "Stanje")):
                if n[fld]: d += list_diff(lab, o.get(fld), n[fld])
            if d: typ_list.append(("izmena", d))
            if o.get("sold"):
                typ_list.insert(0, ("vracen", []))
        if not typ_list: continue
        pdf = f'pdf/{slug(n["make"])}_{slug(n["model"])}_{i}.pdf'
        if o is not None and o.get("pdf_file"): pdf = o["pdf_file"]
        js = os.path.join(work, "new_" + i + ".json"); json.dump(n, open(js, "w"), ensure_ascii=False)
        out = subprocess.run(["python3", os.path.join(T, "make_sheet.py"), js, pdf], capture_output=True, text=True)
        print(out.stdout.strip(), out.stderr.strip()[-500:])
        if "'fits': True" not in out.stdout:
            rep["Nije pročitano"].append(f'{n["make"]} {n["model"]} (#{i}) – lista ne staje na A4'); continue
        n = json.load(open(js, encoding="utf-8"))
        n.update(pdf_file=pdf, sold=False)
        if o is None:
            n.update(added_at=now, changes=[]); cars.append(n); by[i] = n
        else:
            n.update(added_at=o.get("added_at", now), changes=o.get("changes", []))
            if o.get("changed_at"): n["changed_at"] = o["changed_at"]
            cars[cars.index(o)] = n; by[i] = n
        name = f'{n["make"]} {n["model"]} {n["variant"]}'.strip()
        for typ, det in typ_list:
            log(n, typ, det)
            if typ in ("cena", "izmena"): n["changed_at"] = now
            if typ == "nov": rep["Novi"].append(f'{name} – {n["price"]}')
            if typ == "cena": rep["Promena cene"].append(f'{name}: {det[0]["old"]} → {det[0]["new"]}')
            if typ == "izmena": rep["Izmene podataka"].append(name + ": " + "; ".join(
                (f'{x["field"]} {x["new"]}' if not x["old"] else f'{x["field"]} − {x["old"]}' if not x["new"]
                 else f'{x["field"]} {x["old"]} → {x["new"]}') for x in det[:6]))
            if typ == "vracen": rep["Vraćeni"].append(name)
        new_pdfs.append(pdf)

    # removed: only when the dealer list was read completely
    if full_list:
        for c in cars:
            if not c.get("sold") and c["id"] not in active:
                c.update(sold=True, sold_at=now); log(c, "uklonjen", [])
                rep["Uklonjeni"].append(f'{c["make"]} {c["model"]} {c.get("variant", "")}'.strip())
    elif lst.get("total") is not None:
        print("dealer list incomplete:", len(active), "of", lst["total"], "- nothing marked removed")

    # safety net: if many existing cars suddenly "changed", the page layout was probably misread
    n_old = sum(1 for c in cars if not c.get("sold"))
    if len(rep["Izmene podataka"]) > max(5, n_old * 0.3):
        open(os.path.join(work, "report.md"), "w").write(
            "Previše izmena odjednom (" + str(len(rep["Izmene podataka"])) + ") – verovatno se promenio izgled stranice "
            "oglasa. Ništa nije objavljeno.\n\n" + "\n".join("- " + x for x in rep["Izmene podataka"][:15]) + "\n")
        print(open(os.path.join(work, "report.md")).read()); sys.exit(3)
    changed = any(rep[k] for k in ("Novi", "Promena cene", "Izmene podataka", "Uklonjeni", "Vraćeni"))
    if changed:
        json.dump(cars, open("data/cars.json", "w", encoding="utf-8"), ensure_ascii=False)
        json.dump(changes[-500:], open("data/changes.json", "w", encoding="utf-8"), ensure_ascii=False)
        act = sorted([c for c in cars if not c.get("sold")], key=lambda c: (c["make"], c["model"]))
        files = [c["pdf_file"] for c in act if os.path.exists(c["pdf_file"])]
        subprocess.run(["python3", os.path.join(T, "merge_all.py"), "pdf/CAR_DEALER_sve_liste_A4.pdf"] + files, check=True)
        json.dump({"all_pdf": "pdf/CAR_DEALER_sve_liste_A4.pdf", "count": len(files), "updated_at": now},
                  open("data/meta.json", "w"))
    # site (always, refreshes "poslednja provera")
    tmp = os.path.join(work, "sajt")
    subprocess.run(["python3", os.path.join(T, "make_site.py"), "data/cars.json", "data/changes.json", "pdf", tmp], check=True)
    for f in os.listdir(tmp):
        if f != "pdf": shutil.copy(os.path.join(tmp, f), f)

    lines = []
    for k, v in rep.items():
        if v: lines.append(f"**{k}**\n" + "\n".join("- " + x for x in v))
    text = "\n\n".join(lines) if changed or rep["Nije pročitano"] else "Nema izmena u oglasima."
    open(os.path.join(work, "report.md"), "w").write(text + "\n")
    open(os.path.join(work, "changed.txt"), "w").write("1" if changed else "0")
    print(text)

if __name__ == "__main__":
    main()
