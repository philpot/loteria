#!/usr/bin/env python3
"""
Create a 56-card poster (8×7 grid) at full resolution for printing.
Target: 24"×36" poster (36"W × 24"H landscape)
Output: 6000×7350px at ~166 DPI
"""

import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def create_poster_56up(card_paths, background_color, output_path, hs=70, vs=70, lm=None, tm=None, bm=None, title_height=1050, title_text="Vecinos Lotería", mode="card"):
    """
    Arrange 56 cards in a 7×8 grid on a background with title area.

    Parameters:
    - hs: horizontal spacing between cards (default 70px)
    - vs: vertical spacing between cards (default 70px)
    - lm: left margin (default hs/2)
    - tm: top margin (default vs/2)
    - bm: bottom margin (default vs/2)
    - title_height: height of title area (default 1050px = 1 card height)
    - title_text: text to display in title area (default "Vecinos Lotería")
    """
    # Card dimensions
    CARD_WIDTH = 750
    CARD_HEIGHT = 1050

    # Grid layout: 7 columns × 8 rows
    COLS = 7
    ROWS = 8

    # Margins (defaults if not specified)
    if lm is None:
        lm = hs // 2
    if tm is None:
        tm = vs // 2
    if bm is None:
        bm = vs // 2

    # Calculate poster dimensions
    poster_width = lm + COLS * CARD_WIDTH + (COLS - 1) * hs + lm
    poster_height = tm + title_height + vs + ROWS * CARD_HEIGHT + (ROWS - 1) * vs + bm

    # Parse background color (or use transparent)
    if background_color.lower() == "transparent":
        # Transparent background
        poster = Image.new("RGBA", (poster_width, poster_height), (0, 0, 0, 0))
    else:
        if isinstance(background_color, str) and background_color.startswith("#"):
            r = int(background_color[1:3], 16)
            g = int(background_color[3:5], 16)
            b = int(background_color[5:7], 16)
            bg_rgb = (r, g, b)
        elif background_color.lower() == "cream":
            bg_rgb = (239, 233, 219)  # #EFE9DB
        elif background_color.lower() == "white":
            bg_rgb = (255, 255, 255)
        else:
            bg_rgb = (255, 255, 255)

        # Create poster with RGB background
        poster = Image.new("RGB", (poster_width, poster_height), bg_rgb)

    # Load and place cards (skip first row which is title area)
    for idx, card_path in enumerate(card_paths[:56]):  # Only 56 cards max
        if not Path(card_path).exists():
            print(f"Warning: {card_path} not found, skipping")
            continue

        card = Image.open(card_path).convert("RGB")

        # Convert card to match poster mode
        if poster.mode == "RGBA":
            card = card.convert("RGBA")

        row = idx // COLS
        col = idx % COLS

        x = lm + col * (CARD_WIDTH + hs)
        y = tm + title_height + vs + row * (CARD_HEIGHT + vs)

        poster.paste(card, (x, y))

    # Draw title if provided
    if title_text:
        draw = ImageDraw.Draw(poster)
        try:
            title_font = ImageFont.truetype("fonts/Arvo-Bold.ttf", 600)
        except:
            title_font = ImageFont.load_default()

        # Center title text in title area
        bbox = draw.textbbox((0, 0), title_text, font=title_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        title_x = (poster_width - text_width) // 2
        title_y = tm + (title_height - text_height) // 2

        draw.text((title_x, title_y), title_text, font=title_font, fill=(0, 0, 0))

    # Save
    poster.save(output_path)
    print(f"Saved 56-card poster to {output_path}")
    print(f"  Dimensions: {poster_width}×{poster_height} pixels")
    print(f"  Aspect ratio: {poster_width/poster_height:.3f}")
    print(f"  Cards: {len([p for p in card_paths[:56] if Path(p).exists()])}/56")
    print(f"  Layout: {COLS} cols × {ROWS} rows + title area")
    print(f"  Spacing: hs={hs}px, vs={vs}px")
    print(f"  Margins: lm={lm}px, tm={tm}px, bm={bm}px")
    print(f"  DPI at 24in width: {poster_width / 24:.1f}")
    print(f"  Print size (at 150 DPI): {poster_width/150:.1f}\" × {poster_height/150:.1f}\"")


def main():
    parser = argparse.ArgumentParser(
        description="Create a 56-card poster (8×7 grid) at full resolution"
    )
    parser.add_argument(
        "--card-dir", type=str, default="white",
        help="Directory containing card PNG files (default: white)"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="poster_56up.png",
        help="Output file (default: poster_56up.png)"
    )
    parser.add_argument(
        "--background-color", type=str, default="white",
        help="Background color: 'white', 'cream', or hex '#RRGGBB' (default: white)"
    )
    parser.add_argument(
        "--first-card", type=int, default=1,
        help="First card number to include (default: 1)"
    )
    parser.add_argument(
        "--card-list", type=str, default=None,
        help="Comma-separated card numbers (e.g., '1,2,3,...,56'). Overrides --first-card."
    )
    parser.add_argument(
        "--hs", type=int, default=70,
        help="Horizontal spacing between cards (default: 70px)"
    )
    parser.add_argument(
        "--vs", type=int, default=70,
        help="Vertical spacing between cards (default: 70px)"
    )
    parser.add_argument(
        "--lm", type=int, default=None,
        help="Left margin (default: hs/2)"
    )
    parser.add_argument(
        "--tm", type=int, default=None,
        help="Top margin (default: vs/2)"
    )
    parser.add_argument(
        "--bm", type=int, default=None,
        help="Bottom margin (default: vs/2)"
    )
    parser.add_argument(
        "--title-height", type=int, default=1050,
        help="Title area height in pixels (default: 1050 = 1 card height)"
    )
    parser.add_argument(
        "--title-text", type=str, default="Vecinos Lotería",
        help="Title text to display (default: 'Vecinos Lotería')"
    )

    args = parser.parse_args()

    # Build card paths
    card_dir = Path(args.card_dir)
    if not card_dir.exists():
        print(f"Error: {card_dir} not found")
        return

    card_paths = []

    # Determine which card numbers to load
    if args.card_list:
        # Explicit card numbers
        card_numbers = [int(x.strip()) for x in args.card_list.split(",")]
    else:
        # Sequential range
        card_numbers = list(range(args.first_card, args.first_card + 56))

    for card_num in card_numbers:
        # Find matching card file (handles _el_*, _la_* naming)
        matching = list(card_dir.glob(f"{card_num:02d}_*.png"))
        if matching:
            card_paths.append(str(matching[0]))
        else:
            print(f"Warning: No card found for #{card_num:02d}")

    if not card_paths:
        print("No cards found!")
        return

    create_poster_56up(
        card_paths,
        args.background_color,
        args.output,
        hs=args.hs,
        vs=args.vs,
        lm=args.lm,
        tm=args.tm,
        bm=args.bm,
        title_height=args.title_height,
        title_text=args.title_text,
        mode="card"
    )


if __name__ == "__main__":
    main()
