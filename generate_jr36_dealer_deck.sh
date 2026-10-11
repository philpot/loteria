#!/bin/bash

# Generate 4 sheets of 9 cards for dealer deck (all 36 cards in order, 3x3 grid)
mkdir -p jr36_white_on_ivory

# Dealer Sheet 1: Cards 01-09
uv run python montage_9up.py --card-dir jr36_white --background-color '#FFFFF0' -T 0 -V '0.0' -N 36 -R 42 -o jr36_white_on_ivory/dealer_sheet_01.png --card-list 01,02,03,04,05,06,07,08,09

# Dealer Sheet 2: Cards 10-18
uv run python montage_9up.py --card-dir jr36_white --background-color '#FFFFF0' -T 0 -V '0.0' -N 36 -R 42 -o jr36_white_on_ivory/dealer_sheet_02.png --card-list 10,11,12,13,14,15,16,17,18

# Dealer Sheet 3: Cards 19-27
uv run python montage_9up.py --card-dir jr36_white --background-color '#FFFFF0' -T 0 -V '0.0' -N 36 -R 42 -o jr36_white_on_ivory/dealer_sheet_03.png --card-list 19,20,21,22,23,24,25,26,27

# Dealer Sheet 4: Cards 28-36
uv run python montage_9up.py --card-dir jr36_white --background-color '#FFFFF0' -T 0 -V '0.0' -N 36 -R 42 -o jr36_white_on_ivory/dealer_sheet_04.png --card-list 28,29,30,31,32,33,34,35,36

echo "Generated 4 dealer deck sheets (9 cards each, 3x3 grid) in jr36_white_on_ivory/"
