#!/bin/bash

# Generate dealer deck for 56-card deck
# 9 cards per sheet (3×3 grid), 56 cards = 7 sheets (6 full + 1 partial)

mkdir -p dealer_deck_56

python3 << 'PYTHON'
import subprocess

# 56 cards / 9 per sheet = 6.22 sheets, so 7 sheets total
sheets = [
    ("01", "01,02,03,04,05,06,07,08,09"),
    ("02", "10,11,12,13,14,15,16,17,18"),
    ("03", "19,20,21,22,23,24,25,26,27"),
    ("04", "28,29,30,31,32,33,34,35,36"),
    ("05", "37,38,39,40,41,42,43,44,45"),
    ("06", "46,47,48,49,50,51,52,53,54"),
    ("07", "55,56"),  # Last 2 cards
]

print("Generating dealer deck sheets (9 cards per sheet)...\n")

for sheet_num, card_list in sheets:
    cmd = [
        "uv", "run", "python", "montage_9up.py",
        "--card-dir", "white",
        "--background-color", "#FFFFF0",
        "-T", "0",
        "-V", "0.0",
        "-N", "56",
        "-R", "42",
        "--mode", "tabla",
        "-o", f"dealer_deck_56/sheet_{sheet_num}.png",
        "--card-list", card_list
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ sheet_{sheet_num}.png ({len(card_list.split(','))} cards)")
    else:
        print(f"✗ sheet_{sheet_num}.png - {result.stderr}")

print(f"\nGenerated dealer deck in dealer_deck_56/")
PYTHON
