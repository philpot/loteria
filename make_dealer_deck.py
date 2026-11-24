#!/usr/bin/env python3
"""Build the 56-card dealer deck as 9-up letter sheets (7 sheets, 3x3 each)."""

import argparse
import subprocess
from pathlib import Path

SHEETS = [
    ("01", list(range(1, 10))),
    ("02", list(range(10, 19))),
    ("03", list(range(19, 28))),
    ("04", list(range(28, 37))),
    ("05", list(range(37, 46))),
    ("06", list(range(46, 55))),
    ("07", [55, 56]),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cards",
        type=Path,
        default=Path("builds/dfe/white"),
        help="folder of composite cards (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("builds/dfe/dealer_deck"),
        help="folder for sheet_NN.png files (default: %(default)s)",
    )
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    for sheet_num, numbers in SHEETS:
        cmd = [
            "uv", "run", "python", "montage_9up.py",
            "--card-dir", str(args.cards),
            "--background-color", "#FFFFF0",
            "-T", "0",
            "-V", "0.0",
            "-N", "56",
            "-R", "42",
            "--mode", "tabla",
            "-o", str(args.output / f"sheet_{sheet_num}.png"),
            "--card-list", ",".join(str(n) for n in numbers),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"wrote sheet_{sheet_num}.png ({len(numbers)} cards)")


if __name__ == "__main__":
    main()
