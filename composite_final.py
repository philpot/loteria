"""
Composite final cards: aged paper texture background + art + badge + label.

Structure:
- Crop random rectangle from aged paper texture (with random rotation)
- Composite base art with margins (border + top/bottom space for label)
- Draw number badge (upper left, double circles)
- Composite transparent label PNG (centered in bottom area)
- Output to final_composite/
"""

import argparse
import csv
import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import numpy as np


# =====================================================================
# CONFIGURATION
# =====================================================================
CARD_WIDTH = 750   # 2.5in @ 300 DPI
CARD_HEIGHT = 1050  # 3.5in @ 300 DPI

TEXTURE_DIR = "textures"
DEFAULT_TEXTURE = "safwan-thottoli-_YgmNICHdss-unsplash.jpg"
CROPPED_ART_DIR = "fully_cropped_art"
LABELS_DIR = "generated_labels_clean_black"  # transparent PNGs
OUTPUT_DIR = "final_composite"
CSV_PATH = "composite_cards.tsv"

# Margins and borders
MARGIN_WIDTH = 60  # space from card edge to art frame (pixels)
ART_BORDER_WIDTH = 2  # black line around art (pixels)
BORDER_COLOR = (0, 0, 0)  # black
LABEL_HEIGHT_FRACTION = 0.18  # bottom 18% for label

# Badge (number)
BADGE_CENTER_X = 80
BADGE_CENTER_Y = 80
BADGE_OUTER_RADIUS = 40
BADGE_INNER_RADIUS = 32
BADGE_STROKE_WIDTH = 2
BADGE_COLOR = (0, 0, 0)  # black
BADGE_BG_COLOR = (245, 240, 225)  # cream

# Number font
NUMBER_FONT_SIZE = 48


# =====================================================================
# UTILITY
# =====================================================================

def crop_random_rectangle(texture_img, target_w, target_h, rng):
    """
    Crop a random rectangle from texture_img that fits target_w x target_h.
    Returns cropped image. Texture must be at least as large as target.
    """
    tex_w, tex_h = texture_img.size
    if tex_w < target_w or tex_h < target_h:
        raise ValueError(f"Texture {tex_w}x{tex_h} too small for {target_w}x{target_h}")

    x = rng.randint(0, tex_w - target_w + 1)
    y = rng.randint(0, tex_h - target_h + 1)
    return texture_img.crop((x, y, x + target_w, y + target_h))


def draw_badge(canvas, number, x, y, color=BADGE_COLOR, bg_color=BADGE_BG_COLOR):
    """Draw double-ring number badge with transparent background (art shows through)."""
    draw = ImageDraw.Draw(canvas)

    # Outer circle (outline only, no fill - art/texture shows through)
    draw.ellipse(
        [x - BADGE_OUTER_RADIUS, y - BADGE_OUTER_RADIUS,
         x + BADGE_OUTER_RADIUS, y + BADGE_OUTER_RADIUS],
        outline=color + (255,),
        width=BADGE_STROKE_WIDTH
    )

    # Inner circle (outline only)
    draw.ellipse(
        [x - BADGE_INNER_RADIUS, y - BADGE_INNER_RADIUS,
         x + BADGE_INNER_RADIUS, y + BADGE_INNER_RADIUS],
        outline=color + (255,),
        width=BADGE_STROKE_WIDTH
    )

    # Number text
    try:
        font = ImageFont.truetype("fonts/Arvo-Bold.ttf", NUMBER_FONT_SIZE)
    except:
        font = ImageFont.load_default()

    draw.text((x, y), str(number), font=font, fill=color + (255,), anchor="mm")


def composite_card(texture_path, art_path, label_path, number, seed):
    """
    Composite one card:
    1. Crop random rectangle from aged paper texture (for background)
    2. Place art with black border (60px margins)
    3. Add badge
    4. Add label below art
    Returns RGBA PIL Image.
    """
    rng = random.Random(seed)

    # Load texture and crop random rectangle for background
    texture = Image.open(texture_path).convert("RGB")
    bg = crop_random_rectangle(texture, CARD_WIDTH, CARD_HEIGHT, rng)

    # Create canvas with texture background
    canvas = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT))
    canvas.paste(bg)

    # Define art area (with margins and label space)
    art_left = MARGIN_WIDTH
    art_right = CARD_WIDTH - MARGIN_WIDTH
    art_top = MARGIN_WIDTH
    art_bottom = CARD_HEIGHT - int(CARD_HEIGHT * LABEL_HEIGHT_FRACTION)
    art_w = art_right - art_left
    art_h = art_bottom - art_top

    # Load and resize art to fit
    art = Image.open(art_path).convert("RGBA")
    art_aspect = art.width / art.height
    if art_w / art_h > art_aspect:
        # Art is narrower; fit by height
        new_h = art_h
        new_w = int(new_h * art_aspect)
    else:
        # Art is wider; fit by width
        new_w = art_w
        new_h = int(new_w / art_aspect)
    art = art.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Center art in the available space
    art_x = art_left + (art_w - new_w) // 2
    art_y = art_top + (art_h - new_h) // 2
    canvas.alpha_composite(art, (art_x, art_y))

    # Draw border around art
    draw = ImageDraw.Draw(canvas)
    draw.rectangle(
        [art_x - ART_BORDER_WIDTH, art_y - ART_BORDER_WIDTH,
         art_x + new_w + ART_BORDER_WIDTH, art_y + new_h + ART_BORDER_WIDTH],
        outline=BORDER_COLOR + (255,),
        width=ART_BORDER_WIDTH
    )

    # Draw number badge at upper-left corner of art (overlay)
    badge_x = art_x + BADGE_OUTER_RADIUS
    badge_y = art_y + BADGE_OUTER_RADIUS
    draw_badge(canvas, number, badge_x, badge_y)

    # Load and composite label (with scaling)
    if label_path and os.path.exists(label_path):
        label = Image.open(label_path).convert("RGBA")

        # Scale label (all labels saved at 200px height; scale so longest fits)
        # Scale factor is passed in or calculated globally
        if hasattr(composite_card, 'label_scale'):
            scale = composite_card.label_scale
            new_width = int(label.width * scale)
            new_height = int(label.height * scale)
            label = label.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Center label horizontally in the bottom area
        label_y = art_bottom + (CARD_HEIGHT - art_bottom - label.height) // 2
        label_x = (CARD_WIDTH - label.width) // 2
        canvas.alpha_composite(label, (label_x, label_y))

    return canvas


def read_cards(csv_path):
    """Read composite_cards.tsv: [number, label_text, cropped_art_filename]"""
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append({
                "number": int(row["number"].strip()),
                "label_text": row["label"].strip(),
                "art_filename": row["image_filename"].strip(),
            })
    return rows


def label_filename_from_text(label_text):
    """Derive label PNG filename from label text. E.g., 'El Cine' -> 'el_cine.png'"""
    return label_text.replace(" ", "_").lower() + ".png"


def calculate_label_scale(labels_dir, available_width):
    """
    Calculate scale factor so 'El Correcaminos' (longest label) fits in available width.
    All labels are saved at 200px height; scale them proportionally for composite.
    """
    reference_label = "el_correcaminos.png"
    reference_path = os.path.join(labels_dir, reference_label)

    try:
        img = Image.open(reference_path)
        reference_width = img.width
        scale = available_width / reference_width
        return scale
    except Exception as e:
        print(f"Warning: couldn't measure {reference_label}: {e}")
        return 1.0  # No scaling if reference not found


def main(args):
    global MARGIN_WIDTH, ART_BORDER_WIDTH
    if args.margin_width is not None:
        MARGIN_WIDTH = args.margin_width
    if args.art_border_width is not None:
        ART_BORDER_WIDTH = args.art_border_width

    os.makedirs(args.output, exist_ok=True)

    # Calculate label scale factor (all labels at 200px height; scale to fit)
    art_area_width = CARD_WIDTH - (2 * MARGIN_WIDTH)
    label_scale = calculate_label_scale(args.labels_dir, art_area_width)
    composite_card.label_scale = label_scale
    print(f"Label scale factor: {label_scale:.3f}")

    # Load texture
    texture_path = os.path.join(args.texture_dir, args.texture)
    if not os.path.exists(texture_path):
        print(f"Texture not found: {texture_path}")
        return

    # Read cards
    cards = read_cards(args.csv)
    print(f"Read {len(cards)} cards from {args.csv}")

    # Seed for reproducibility
    seed = args.seed

    for card in cards:
        number = card["number"]
        label_text = card["label_text"]
        art_filename = card["art_filename"]

        art_path = os.path.join(args.art_dir, art_filename)
        label_filename = label_filename_from_text(label_text)
        label_path = os.path.join(args.labels_dir, label_filename)

        if not os.path.exists(art_path):
            print(f"  [SKIP] {number:02d} {label_text:30s} (art not found)")
            continue

        try:
            card_img = composite_card(
                texture_path, art_path, label_path, number, seed + number
            )
            output_path = os.path.join(args.output, f"{number:02d}_{label_filename}")
            card_img.convert("RGB").save(output_path)
            print(f"  [OK]   {number:02d} {label_text:30s}")
        except Exception as e:
            print(f"  [FAIL] {number:02d} {label_text:30s} - {e}")

    print(f"\nWrote to {args.output}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Composite final cards: texture + art + badge + label"
    )
    parser.add_argument(
        "--csv", default=CSV_PATH,
        help=f"Card manifest (default: {CSV_PATH})"
    )
    parser.add_argument(
        "--art-dir", default=CROPPED_ART_DIR,
        help=f"Cropped art directory (default: {CROPPED_ART_DIR})"
    )
    parser.add_argument(
        "--labels-dir", default=LABELS_DIR,
        help=f"Label PNG directory (default: {LABELS_DIR})"
    )
    parser.add_argument(
        "--texture-dir", default=TEXTURE_DIR,
        help=f"Texture directory (default: {TEXTURE_DIR})"
    )
    parser.add_argument(
        "--texture", default=DEFAULT_TEXTURE,
        help=f"Texture filename (default: {DEFAULT_TEXTURE})"
    )
    parser.add_argument(
        "--output", default=OUTPUT_DIR,
        help=f"Output directory (default: {OUTPUT_DIR})"
    )
    parser.add_argument(
        "--seed", type=int, default=20260818,
        help=f"Random seed (default: 20260818)"
    )
    parser.add_argument(
        "--margin-width", type=int, default=None,
        help=f"Margin from card edge to art frame (pixels, default: {MARGIN_WIDTH})"
    )
    parser.add_argument(
        "--art-border-width", type=int, default=None,
        help=f"Black line thickness around art (pixels, default: {ART_BORDER_WIDTH})"
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    main(args)
