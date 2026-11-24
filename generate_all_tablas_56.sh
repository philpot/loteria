#!/bin/bash

# Generate all 60 tablas from loteria_matrices_60.json
# Each tabla is a 4×4 grid with 16 cards

mkdir -p builds/dfe/16up

python3 << 'PYTHON'
import json
import subprocess

# Load tabla definitions
with open("src/loteria/tablas/loteria_matrices_60.json") as f:
    tablas = json.load(f)

print(f"Generating {len(tablas)} tablas...")

for idx, tabla in enumerate(tablas, 1):
    tabla_num = idx
    card_list = ",".join(str(c) for c in tabla)

    cmd = [
        "uv", "run", "python", "montage_16up.py",
        "--card-dir", "builds/dfe/white",
        "--background-color", "#FFFFF0",
        "-T", str(tabla_num),
        "--mode", "tabla",
        "-o", f"builds/dfe/16up/tabla{tabla_num:02d}.png",
        "--card-list", card_list
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ tabla{tabla_num:02d}.png")
    else:
        print(f"✗ tabla{tabla_num:02d}.png - {result.stderr}")

print(f"\nGenerated {len(tablas)} tablas in builds/dfe/16up/")
PYTHON
