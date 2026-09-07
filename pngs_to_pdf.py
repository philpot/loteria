#!/usr/bin/env python3
"""
Combine multiple PNG files into a single PDF document.
Each PNG becomes one page in the PDF.
Supports fitting to standard paper sizes for 100% print size.
"""

import argparse
from pathlib import Path
from PIL import Image


# Paper size definitions at 300 DPI (imageable area in pixels)
PAPER_SIZES = {
    "letter": (2400, 3113),      # 8" × 10.375" @ 300 DPI
    "a4": (2338, 3307),          # 7.79" × 11.02" @ 300 DPI
    "tabloid": (3600, 4800),     # 12" × 16" @ 300 DPI
}


def pngs_to_pdf(png_files, output_path, fit_to_page=None):
    """
    Combine multiple PNG files into a single PDF.
    Each PNG becomes one page.
    If fit_to_page is specified, downscale to fit within page bounds.
    """
    if not png_files:
        print("No PNG files to process")
        return

    # Get page bounds if requested
    page_width, page_height = None, None
    if fit_to_page:
        if fit_to_page.lower() not in PAPER_SIZES:
            print(f"Unknown paper size: {fit_to_page}")
            print(f"Available: {', '.join(PAPER_SIZES.keys())}")
            return
        page_width, page_height = PAPER_SIZES[fit_to_page.lower()]
        print(f"Fitting to {fit_to_page}: {page_width}×{page_height}px @ 300 DPI")

    # Load and convert all images to RGB
    images = []
    for png_file in png_files:
        path = Path(png_file)
        if not path.exists():
            print(f"Warning: {png_file} not found, skipping")
            continue

        try:
            img = Image.open(path).convert("RGB")
            orig_size = (img.width, img.height)

            # Downscale if needed
            if fit_to_page:
                scale = min(page_width / img.width, page_height / img.height)
                if scale < 1.0:
                    new_w = int(img.width * scale)
                    new_h = int(img.height * scale)
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    print(f"  Scaled: {png_file} {orig_size} -> {img.size}")
                else:
                    print(f"  Loaded: {png_file} {orig_size} (fits on page)")
            else:
                print(f"  Loaded: {png_file} {orig_size}")

            images.append(img)
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
    parser.add_argument(
        "--fit-to-page", type=str, choices=list(PAPER_SIZES.keys()),
        help=f"Fit to paper size for 100%% print (options: {', '.join(PAPER_SIZES.keys())})"
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
    pngs_to_pdf(all_files, args.output, args.fit_to_page)


if __name__ == "__main__":
    main()
