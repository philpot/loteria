#!/usr/bin/env python3
"""Combine all tabla PNGs in a folder into one PDF."""

import argparse
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("builds/dfe/16up"),
        help="folder containing tabla??.png files (default: %(default)s)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="output PDF (default: <dir>/all_tablas.pdf)",
    )
    args = parser.parse_args()

    tablas = sorted(args.dir.glob("tabla??.png"))
    if not tablas:
        raise SystemExit(f"no tabla??.png files found in {args.dir}")

    output = args.output or args.dir / "all_tablas.pdf"
    cmd = ["uv", "run", "python", "pngs_to_pdf.py", "-o", str(output)] + [str(t) for t in tablas]
    subprocess.run(cmd, check=True)
    print(f"wrote {len(tablas)} tablas to {output}")


if __name__ == "__main__":
    main()
