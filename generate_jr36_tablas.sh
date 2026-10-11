#!/bin/bash

# Generate 12 printable tablas from jr36_tablas.json
mkdir -p jr36_white_on_ivory

# Tabla 01
uv run python montage_16up.py --card-dir jr36_white --background-color '#FFFFF0' -V '1.0' -N 36 -R 42 -T 1 --mode tabla -o jr36_white_on_ivory/tabla01.png --card-list 03,35,04,31,13,08,15,19,34,12,30,06,23,10,27,11

# Tabla 02
uv run python montage_16up.py --card-dir jr36_white --background-color '#FFFFF0' -V '1.0' -N 36 -R 42 -T 2 --mode tabla -o jr36_white_on_ivory/tabla02.png --card-list 16,13,29,04,27,20,12,17,05,03,25,02,01,07,32,14

# Tabla 03
uv run python montage_16up.py --card-dir jr36_white --background-color '#FFFFF0' -V '1.0' -N 36 -R 42 -T 3 --mode tabla -o jr36_white_on_ivory/tabla03.png --card-list 33,29,23,20,16,30,17,10,18,01,11,02,06,15,22,19

# Tabla 04
uv run python montage_16up.py --card-dir jr36_white --background-color '#FFFFF0' -V '1.0' -N 36 -R 42 -T 4 --mode tabla -o jr36_white_on_ivory/tabla04.png --card-list 21,18,36,07,26,33,01,12,20,17,16,35,25,28,02,24

# Tabla 05
uv run python montage_16up.py --card-dir jr36_white --background-color '#FFFFF0' -V '1.0' -N 36 -R 42 -T 5 --mode tabla -o jr36_white_on_ivory/tabla05.png --card-list 06,10,11,34,03,08,16,36,35,21,26,09,07,29,24,32

# Tabla 06
uv run python montage_16up.py --card-dir jr36_white --background-color '#FFFFF0' -V '1.0' -N 36 -R 42 -T 6 --mode tabla -o jr36_white_on_ivory/tabla06.png --card-list 34,07,02,18,09,25,13,19,23,08,03,22,30,33,27,32

# Tabla 07
uv run python montage_16up.py --card-dir jr36_white --background-color '#FFFFF0' -V '1.0' -N 36 -R 42 -T 7 --mode tabla -o jr36_white_on_ivory/tabla07.png --card-list 14,27,08,30,06,04,24,28,29,33,31,03,02,23,01,32

# Tabla 08
uv run python montage_16up.py --card-dir jr36_white --background-color '#FFFFF0' -V '1.0' -N 36 -R 42 -T 8 --mode tabla -o jr36_white_on_ivory/tabla08.png --card-list 28,04,36,14,26,09,22,08,05,30,21,11,15,01,12,19

# Tabla 09
uv run python montage_16up.py --card-dir jr36_white --background-color '#FFFFF0' -V '1.0' -N 36 -R 42 -T 9 --mode tabla -o jr36_white_on_ivory/tabla09.png --card-list 04,11,12,31,10,15,28,36,20,33,01,05,13,14,34,25

# Tabla 10
uv run python montage_16up.py --card-dir jr36_white --background-color '#FFFFF0' -V '1.0' -N 36 -R 42 -T 10 --mode tabla -o jr36_white_on_ivory/tabla10.png --card-list 22,21,24,19,06,32,09,04,29,16,31,35,05,10,36,34

# Tabla 11
uv run python montage_16up.py --card-dir jr36_white --background-color '#FFFFF0' -V '1.0' -N 36 -R 42 -T 11 --mode tabla -o jr36_white_on_ivory/tabla11.png --card-list 26,07,22,35,28,17,14,13,02,09,12,27,31,06,05,18

# Tabla 12
uv run python montage_16up.py --card-dir jr36_white --background-color '#FFFFF0' -V '1.0' -N 36 -R 42 -T 12 --mode tabla -o jr36_white_on_ivory/tabla12.png --card-list 21,09,20,17,15,11,07,23,18,03,10,24,08,26,05,25

echo "Generated 12 tablas in jr36_white_on_ivory/"
