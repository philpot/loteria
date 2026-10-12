#!/bin/bash

# Convert all 56-card montages to PDFs

python3 << 'PYTHON'
import subprocess
from pathlib import Path
import os

# Convert all tablas to PDF
tablas = sorted(Path("16up_white_on_ivory").glob("tabla??.png"))
print(f"Converting {len(tablas)} tabla PNGs to PDFs...")

for tabla in tablas:
    pdf = tabla.with_suffix(".pdf")
    cmd = ["uv", "run", "python", "pngs_to_pdf.py", str(tabla), "--fit-to-page", "letter", "-o", str(pdf)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ {pdf.name}")

# Convert poster to PDF
print("\nConverting poster...")
cmd = ["uv", "run", "python", "pngs_to_pdf.py", "poster_output/poster_56_transparent.png", "-o", "poster_output/poster_56_transparent.pdf"]
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode == 0:
    print("✓ poster_56_transparent.pdf")

# Combine all tablas into one PDF
print("\nCombining all tablas into single PDF...")
tablas_list = " ".join(str(t) for t in tablas)
cmd_str = f"uv run python pngs_to_pdf.py -o 16up_white_on_ivory/all_tablas.pdf {tablas_list}"
result = subprocess.run(cmd_str, shell=True, capture_output=True, text=True)
if result.returncode == 0:
    print("✓ all_tablas.pdf (50 tablas combined)")

# Combine all dealer sheets into one PDF (from PNG sources, not PDFs)
print("\nCombining all dealer sheets into single PDF...")
sheets_png = sorted(Path("dealer_deck_56").glob("sheet_??.png"))
sheets_list = " ".join(str(s) for s in sheets_png)
cmd_str = f"uv run python pngs_to_pdf.py -o dealer_deck_56/all_dealer_sheets.pdf {sheets_list}"
result = subprocess.run(cmd_str, shell=True, capture_output=True, text=True)
if result.returncode == 0:
    print("✓ all_dealer_sheets.pdf (7 sheets combined)")

print("\nDone!")
PYTHON
