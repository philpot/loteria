#!/usr/bin/env python3
"""
Combine multiple PNG files into a single PDF document.
Each PNG becomes one page in the PDF.
"""

import argparse
from pathlib import Path
from PIL import Image


def pngs_to_pdf(png_files, output_path):
    """
    Combine multiple PNG files into a single PDF.
    Each PNG becomes one page.
    """
    if not png_files:
        print("No PNG files to process")
        return

    # Load and convert all images to RGB
    images = []
    for png_file in png_files:
        path = Path(png_file)
        if not path.exists():
            print(f"Warning: {png_file} not found, skipping")
            continue

        try:
            img = Image.open(path).convert("RGB")
            images.append(img)
            print(f"  Loaded: {png_file} ({img.width}×{img.height})")
        except Exception as e:
            print(f"Error loading {png_file}: {e}")
            continue

    if not images:
        print("No valid images to process")
        return

    # Save as PDF (first image + list of remaining images)
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:] if len(images) > 1 else [],
        format="PDF"
    )

    print(f"\nSaved {len(images)} pages to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Combine multiple PNG files into a single PDF document"
    )
    parser.add_argument(
        "png_files", nargs="+",
        help="PNG files to combine (glob patterns supported)"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="output.pdf",
        help="Output PDF file (default: output.pdf)"
    )

    args = parser.parse_args()

    # Expand glob patterns
    all_files = []
    for pattern in args.png_files:
        matching = list(Path(".").glob(pattern))
        if matching:
            all_files.extend([str(f) for f in matching])
        else:
            # If no glob match, treat as literal path
            all_files.append(pattern)

    # Sort for consistent ordering
    all_files.sort()

    print(f"Processing {len(all_files)} file(s)...")
    pngs_to_pdf(all_files, args.output)


if __name__ == "__main__":
    main()
