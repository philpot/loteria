#!/usr/bin/env python3
"""
Create a 16-up montage of Lotería cards on a background, with footer metadata.
"""

import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def create_montage_16up(card_paths, background_color, output_path, tabla_num, version, n_cards, run_id):
    """
    Arrange 16 cards in a 4×4 grid on a background.
    Add a small footer with metadata.
    """
    # Card dimensions (from composite_final.py)
    CARD_WIDTH = 750
    CARD_HEIGHT = 1050

    # Grid layout
    COLS = 4
    ROWS = 4
    SPACING = 20
    MARGIN = 30
    FOOTER_HEIGHT = 60

    # Calculate montage dimensions
    montage_width = MARGIN * 2 + COLS * CARD_WIDTH + (COLS - 1) * SPACING
    montage_height = MARGIN * 2 + ROWS * CARD_HEIGHT + (ROWS - 1) * SPACING + FOOTER_HEIGHT

    # Parse background color
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

    # Create montage
    montage = Image.new("RGB", (montage_width, montage_height), bg_rgb)

    # Load and place cards
    for idx, card_path in enumerate(card_paths[:16]):  # Only 16 cards max
        if not Path(card_path).exists():
            print(f"Warning: {card_path} not found, skipping")
            continue

        card = Image.open(card_path).convert("RGB")
        row = idx // COLS
        col = idx % COLS

        x = MARGIN + col * (CARD_WIDTH + SPACING)
        y = MARGIN + row * (CARD_HEIGHT + SPACING)

        montage.paste(card, (x, y))

    # Add footer (unless suppressed)
    if tabla_num != 0 and version != "0.0":
        draw = ImageDraw.Draw(montage)
        footer_y = montage_height - FOOTER_HEIGHT + 20

        # Load font (36pt for all footer elements)
        try:
            footer_font = ImageFont.truetype("fonts/Arvo-Bold.ttf", 36)
        except:
            footer_font = ImageFont.load_default()

        # A. Left: TABLA NN
        tabla_text = f"TABLA {tabla_num:02d}"
        draw.text((MARGIN, footer_y), tabla_text, font=footer_font, fill=(0, 0, 0))

        # B. Center: Copyright info
        copyright_text = "© 2026 Vecinos de South Pasadena"
        bbox = draw.textbbox((0, 0), copyright_text, font=footer_font)
        text_width = bbox[2] - bbox[0]
        center_x = (montage_width - text_width) // 2
        draw.text((center_x, footer_y), copyright_text, font=footer_font, fill=(0, 0, 0))

        # C. Right: Metadata (36pt)
        card_dir = Path(card_paths[0]).parent.name if card_paths else "?"
        metadata_text = f"V={version} N={n_cards} R={run_id} Dir={card_dir} BG={background_color}"
        bbox = draw.textbbox((0, 0), metadata_text, font=footer_font)
        text_width = bbox[2] - bbox[0]
        right_x = montage_width - MARGIN - text_width
        draw.text((right_x, footer_y + 5), metadata_text, font=footer_font, fill=(64, 64, 64))

    # Save
    montage.save(output_path)
    print(f"Saved 16-up montage to {output_path}")
    print(f"  Dimensions: {montage_width}×{montage_height}")
    print(f"  Cards: {len([p for p in card_paths[:16] if Path(p).exists()])}/16")


def main():
    parser = argparse.ArgumentParser(
        description="Create a 16-up montage of Lotería cards"
    )
    parser.add_argument(
        "--card-dir", type=str, default="final_composite",
        help="Directory containing card PNG files (default: final_composite)"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="montage_16up.png",
        help="Output file (default: montage_16up.png)"
    )
    parser.add_argument(
        "--background-color", type=str, default="cream",
        help="Background color: 'white', 'cream', or hex '#RRGGBB' (default: cream)"
    )
    parser.add_argument(
        "-T", "--tabla", type=int, default=1,
        help="Tabla number for footer (default: 1)"
    )
    parser.add_argument(
        "-V", "--version", type=str, default="1.0",
        help="Baraja version for footer (default: 1.0)"
    )
    parser.add_argument(
        "-N", "--cards", type=int, default=56,
        help="Number of cards for footer (default: 56)"
    )
    parser.add_argument(
        "-R", "--run-id", type=str, default="0",
        help="Run ID/seed for footer (default: 0)"
    )
    parser.add_argument(
        "--first-card", type=int, default=1,
        help="First card number to include (default: 1, so cards 01-16). Ignored if --cards is provided."
    )
    parser.add_argument(
        "--card-list", type=str, default=None,
        help="Comma-separated card numbers (e.g., '1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31'). Overrides --first-card."
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
        card_numbers = list(range(args.first_card, args.first_card + 16))

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

    create_montage_16up(
        card_paths,
        args.background_color,
        args.output,
        args.tabla,
        args.version,
        args.cards,
        args.run_id
    )


if __name__ == "__main__":
    main()
