#!/usr/bin/env python3
"""Merge per-car A4 PDFs into one print file. Usage: merge_all.py out.pdf a.pdf b.pdf ..."""
import sys
from pypdf import PdfWriter
w = PdfWriter()
for f in sys.argv[2:]: w.append(f)
w.write(sys.argv[1]); print("ok", sys.argv[1], len(sys.argv) - 2, "pages")
