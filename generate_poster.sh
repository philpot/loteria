#!/bin/bash

# Generate 56-card poster (7×8 grid with title area) at full resolution
# Layout: 7 columns × 8 rows with 70px spacing
# Margins: 35px (left), 35px (top), 35px (bottom)
# Target: portrait aspect ratio ~0.6 (fits 24"×36")

mkdir -p builds/loteria-56/poster

# Poster with transparent background (for layering)
uv run python poster_56up.py \
  --card-dir builds/loteria-56/white \
  --background-color transparent \
  --hs 70 \
  --vs 70 \
  --title-height 1050 \
  -o builds/loteria-56/poster/poster_56_transparent.png

echo "Generated poster in builds/loteria-56/poster/"
