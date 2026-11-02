#!/usr/bin/env python3
"""Regenerate all active A4 PDFs (e.g. after a new NBS rate in data/kurs.json) and the combined PDF.
Usage (from repo root): refresh_all.py"""
import json, os, subprocess, sys, tempfile
T = os.path.dirname(os.path.abspath(__file__))
cars = json.load(open("data/cars.json", encoding="utf-8"))
act = sorted([c for c in cars if not c.get("sold")], key=lambda c: (c["make"], c["model"]))
bad = []
for c in act:
    keep = {k: v for k, v in c.items() if k not in ("changes", "added_at", "changed_at", "sold", "sold_at", "pdf_file")}
    fd, js = tempfile.mkstemp(suffix=".json"); os.close(fd)
    json.dump(keep, open(js, "w"), ensure_ascii=False)
    o = subprocess.run(["python3", os.path.join(T, "make_sheet.py"), js, c["pdf_file"]], capture_output=True, text=True)
    if "'fits': True" not in o.stdout: bad.append(c["id"])
    os.remove(js)
subprocess.run(["python3", os.path.join(T, "merge_all.py"), "pdf/CAR_DEALER_sve_liste_A4.pdf"] + [c["pdf_file"] for c in act], check=True)
print("ok", len(act), "not fitting:", bad)
