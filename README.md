# loteria

![PyPI version](https://img.shields.io/pypi/v/loteria.svg)
[![Documentation Status](https://readthedocs.org/projects/loteria/badge/?version=latest)](https://loteria.readthedocs.io/en/latest/?version=latest)

loteria

* PyPI package: https://pypi.org/project/loteria/
* Free software: MIT License
* Documentation: https://loteria.readthedocs.io.

## Features

* TODO

## Credits

This package was created with [Cookiecutter](https://github.com/audreyfeldroy/cookiecutter) and the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.

## 56-Card Deck Pipeline

### To generate cards (56-card deck)

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

## 36-Card Junior Deck Pipeline

### To generate cards (36-card jr deck)

uv run composite_final.py --csv jr36_composite_cards.tsv --art-dir /Users/Andrew/Documents/loteria/jrlot01 --output jr36_white --background-color 'white' --card-border-width 4 --art-border-width 4

### To generate die cut cards (36-card, no tablas)

uv run python montage_16up.py --card-dir jr36_white --background-color '#FFFFF0' -T 0 -V '0.0' -N 36 -R 42 -o jr36_white_on_ivory/cards_only_1_16.png --card-list 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16
uv run python montage_16up.py --card-dir jr36_white --background-color '#FFFFF0' -T 0 -V '0.0' -N 36 -R 42 -o jr36_white_on_ivory/cards_only_17_32.png --card-list 17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32
uv run python montage_16up.py --card-dir jr36_white --background-color '#FFFFF0' -T 0 -V '0.0' -N 36 -R 42 -o jr36_white_on_ivory/cards_only_33_36.png --card-list 33,34,35,36,1,1,1,1,1,1,1,1,1,1,1,1

### To generate tablas (36-card deck)

uv run python src/loteria/tablas/tablas.py -N 36 -K 50 -o jr36_tablas.json
uv run python montage_16up.py --card-dir jr36_white --background-color '#FFFFF0' -V '1.0' -N 36 -R 42 -T 1 -o jr36_white_on_ivory/tabla01.png --card-list [tabla_1_from_json]
...

### To paste together (36-card deck)

uv run python pngs_to_pdf.py -o jr36_white_on_ivory/all.pdf jr36_white_on_ivory/cards_only*.png jr36_white_on_ivory/tabla*.png