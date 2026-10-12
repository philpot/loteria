# loteria

![PyPI version](https://img.shields.io/pypi/v/loteria.svg)
[![Documentation Status](https://readthedocs.org/projects/loteria/badge/?version=latest)](https://loteria.readthedocs.io/en/latest/?version=latest)

loteria

* PyPI package: https://pypi.org/project/loteria/
* Free software: MIT License
* Documentation: https://loteria.readthedocs.io.

## Features

* TODO

## Workflows

### Regenerate 56-card deck (standard Lotería)

When source art in `fully_cropped_art/` is updated:

```bash
# Step 1: Generate composite cards
uv run composite_final.py --csv composite_cards.tsv --art-dir fully_cropped_art \
  --output white --background-color white --card-border-width 4 --art-border-width 4

# Step 2: Generate all 50 tablas from pre-defined layouts (src/loteria/tablas/loteria_matrices.json)
bash generate_all_tablas_56.sh

# Step 3: Generate poster (56 cards, 7×8 grid, transparent background)
bash generate_poster.sh

# Step 4: Generate dealer deck (7 sheets of 9 cards per letter page)
bash generate_dealer_deck_56.sh

# Step 5: Convert all to PDF
bash generate_all_pdfs_56.sh
for sheet in dealer_deck_56/sheet_*.png; do
  uv run python pngs_to_pdf.py "$sheet" --fit-to-page letter -o "${sheet%.png}.pdf"
done
```

**Output:**
- `white/` — 56 composite cards
- `16up_white_on_ivory/` — 50 individual tabla PDFs
- `16up_white_on_ivory/all_tablas.pdf` — Single concatenated PDF (all 50 tablas)
- `dealer_deck_56/` — 7 individual dealer sheet PDFs
- `dealer_deck_56/all_dealer_sheets.pdf` — Single concatenated PDF (all 7 sheets)
- `poster_output/poster_56_transparent.pdf` — Poster PDF (transparent background)

### Regenerate 36-card junior deck (jr36)

On branch `jr-36-final-pipeline`:

```bash
# Generate composites with on-the-fly labels
uv run composite_final.py --csv jr36_composite_cards.tsv --art-dir ../../loteria/jrlot01 \
  --output jr36_white --background-color white --card-border-width 4 --art-border-width 4

# Generate tablas and dealer deck
bash generate_jr36_tablas.sh
bash generate_jr36_dealer_deck.sh

# Generate PDFs
python3 << 'PY'
import subprocess
from pathlib import Path
for f in sorted(Path("jr36_white_on_ivory").glob("tabla??.png")) + sorted(Path("jr36_white_on_ivory").glob("dealer_sheet_??.png")):
  subprocess.run(["uv", "run", "python", "pngs_to_pdf.py", str(f), "--fit-to-page", "letter", "-o", str(f.with_suffix(".pdf"))], capture_output=True)
PY
```

## Credits

This package was created with [Cookiecutter](https://github.com/audreyfeldroy/cookiecutter) and the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.

To generate cards

uv run composite_final.py --csv composite_cards.tsv --art-dir fully_cropped_art --output white --background-color 'white'  --card-border-width 4 --art-border-width 4


To generate die cut cards (not tablas)
Use -T 0
Use -V 0.0

uv run python montage_16up.py --card-dir white --background-color '#FFFFF0' -T 0 -V '0.0' -N 56 -R 42 -o 16up_white_on_ivory/cards_only_1_16.png --card-list 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16
uv run python montage_16up.py --card-dir white --background-color '#FFFFF0' -T 0 -V '0.0' -N 56 -R 42 -o 16up_white_on_ivory/cards_only_17_32.png --card-list 17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32
uv run python montage_16up.py --card-dir white --background-color '#FFFFF0' -T 0 -V '0.0' -N 56 -R 42 -o 16up_white_on_ivory/cards_only_33_48.png --card-list 33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48
uv run python montage_16up.py --card-dir white --background-color '#FFFFF0' -T 0 -V '0.0' -N 56 -R 42 -o 16up_white_on_ivory/cards_only_49_56.png --card-list 48,49,50,51,52,53,54,55,56,15,15,15,15,15,15,15,15

To generate tablas

uv run python montage_16up.py --card-dir white --background-color '#FFFFF0' -V '1.0' -N 56 -R 42 -T 1 -o 16up_white_on_ivory/tabla01.png --card-list 30,39,28,3,5,37,51,35,45,50,23,24,20,44,15,8
uv run python montage_16up.py --card-dir white --background-color '#FFFFF0' -V '1.0' -N 56 -R 42 -T 2 -o 16up_white_on_ivory/tabla02.png --card-list 46,7,47,40,9,39,37,4,53,14,52,28,21,41,50,2
...

To paste together

uv run python pngs_to_pdf.py -o 16up_white_on_ivory/all.pdf 16up_white_on_ivory/cards_only*.png 16up_white_on_ivory/tabla*.png

To paste fitting letter size

python pngs_to_pdf.py 16up_white_on_ivory/tabla01.png --fit-to-page letter -o 16up_white_on_ivory/tabla01.pdf



 3896  uv run composite_final.py --csv composite_cards.tsv --art-dir fully_cropped_art --output wheat --background-color '#E8D4B0'  --card-border-width 4 --art-border-width 4
 3899  uv run python montage_16up.py --card-dir wheat --background-color '#FFFFFF' -T 0 -V '0.0' -N 56 -R 42 -o 16up_wheat_on_white/sampler.png --card-list 3,8,26,30,28,22,40,21,14,2,27,31,42,52,15,33
 3901  uv run python montage_16up.py --card-dir wheat --background-color '#FFFFFF' -T 0 -V '0.0' -N 56 -R 42 -o 16up_wheat_on_white/sampler.png --card-list 3,8,26,30,28,22,40,21,14,2,27,31,42,52,15,33
 3904  uv run python pngs_to_pdf.py -h
 3905  uv run python pngs_to_pdf.py 16up_wheat_on_white/sampler.png --fit-to-page letter