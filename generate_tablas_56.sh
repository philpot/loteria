#!/bin/bash

# Generate tablas for 56-card deck
# Using montage_16up.py with --mode tabla (no debug metadata)

mkdir -p 16up_white_on_ivory

# Example: Generate one tabla with first 16 cards
uv run python montage_16up.py \
  --card-dir white \
  --background-color '#FFFFF0' \
  -T 1 \
  --mode tabla \
  -o 16up_white_on_ivory/tabla01.png \
  --first-card 1

echo "Generated tabla in 16up_white_on_ivory/"
