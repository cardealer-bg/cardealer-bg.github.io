#!/usr/bin/env python3
"""Merge per-car A4 PDFs into one print file. Usage: merge_all.py out.pdf a.pdf b.pdf ...
Also writes out_bez_lizinga.pdf from the a_bez_lizinga.pdf versions when they all exist."""
import os, sys
from pypdf import PdfWriter
def merge(out, files):
    w = PdfWriter()
    for f in files: w.append(f)
    w.write(out); print("ok", out, len(files), "pages")
merge(sys.argv[1], sys.argv[2:])
bez = [f[:-4] + "_bez_lizinga.pdf" for f in sys.argv[2:]]
if not sys.argv[1].endswith("_bez_lizinga.pdf") and bez and all(os.path.exists(f) for f in bez):
    merge(sys.argv[1][:-4] + "_bez_lizinga.pdf", bez)
