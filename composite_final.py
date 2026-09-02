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
LABELS_DIR = "generated_labels_clean_black_best"  # transparent PNGs
OUTPUT_DIR = "final_composite"
CSV_PATH = "composite_cards.tsv"
BACKGROUND_COLOR = None  # None = use texture, or hex string like "#FFFFFF" for solid color

# Margins and borders
MARGIN_WIDTH = 60  # space from card edge to art frame (pixels)
ART_BORDER_WIDTH = 2  # black line around art (pixels)
CARD_BORDER_WIDTH = 0  # outer border around entire card edge (pixels, 0 = none)
BORDER_COLOR = (0, 0, 0)  # black
LABEL_HEIGHT_FRACTION = 0.18  # bottom 18% for label

# Badge (number) — may be overridden by command-line args
BADGE_OUTER_RADIUS = 40
BADGE_INNER_RADIUS = 32
BADGE_STROKE_WIDTH = 2
BADGE_COLOR = (0, 0, 0)  # black
BADGE_INSET = BADGE_OUTER_RADIUS - BADGE_INNER_RADIUS  # Default: stroke width

# Number font — may be overridden by command-line args
NUMBER_FONT_SIZE = 48


# =====================================================================
# UTILITY
# =====================================================================

def trim_white_edges(img, lightness_threshold=220):
    """
    Crop border from image by sampling corner color and removing matching pixels.
    Uses color distance instead of brightness, so sky != cream even if similar brightness.
    """
    img_array = np.array(img.convert("RGB"))
    rgb = img_array[:, :, :3]
    h, w = rgb.shape[:2]

    # Sample corner color (assume all 4 corners are border)
    corner_colors = [
        rgb[0, 0],           # top-left
        rgb[0, w-1],         # top-right
        rgb[h-1, 0],         # bottom-left
        rgb[h-1, w-1],       # bottom-right
    ]
    border_color = np.mean(corner_colors, axis=0)  # Average of corners

    # Color distance tolerance (0-255 per channel)
    tolerance = 15

    # Find pixels NOT matching border color (content pixels)
    distances = np.sqrt(np.sum((rgb.astype(float) - border_color[np.newaxis, np.newaxis, :]) ** 2, axis=2))
    content_mask = distances > tolerance

    # Find rows and cols with at least one content pixel
    content_rows = np.where(content_mask.any(axis=1))[0]
    content_cols = np.where(content_mask.any(axis=0))[0]

    if len(content_rows) == 0 or len(content_cols) == 0:
        return img  # No content found, return as-is

    y_min, y_max = content_rows[0], content_rows[-1]
    x_min, x_max = content_cols[0], content_cols[-1]

    return img.crop((x_min, y_min, x_max + 1, y_max + 1))


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


def draw_badge(canvas, number, x, y, color=BADGE_COLOR, bg_color=None):
    """
    Draw number badge with optional background.
    bg_color: hex string (e.g., '#FFFFFF') or None for transparent.
    """
    draw = ImageDraw.Draw(canvas)

    # Background circle (if specified)
    if bg_color:
        # Parse hex color
        if isinstance(bg_color, str) and bg_color.startswith('#'):
            r = int(bg_color[1:3], 16)
            g = int(bg_color[3:5], 16)
            b = int(bg_color[5:7], 16)
            bg_rgb = (r, g, b, 255)
        else:
            bg_rgb = color + (255,)  # Fallback

        draw.ellipse(
            [x - BADGE_OUTER_RADIUS, y - BADGE_OUTER_RADIUS,
             x + BADGE_OUTER_RADIUS - 1, y + BADGE_OUTER_RADIUS - 1],
            fill=bg_rgb
        )

    # Outer circle (outline only)
    draw.ellipse(
        [x - BADGE_OUTER_RADIUS, y - BADGE_OUTER_RADIUS,
         x + BADGE_OUTER_RADIUS - 1, y + BADGE_OUTER_RADIUS - 1],
        outline=color + (255,),
        width=BADGE_STROKE_WIDTH
    )

    # Inner circle (outline only)
    draw.ellipse(
        [x - BADGE_INNER_RADIUS, y - BADGE_INNER_RADIUS,
         x + BADGE_INNER_RADIUS - 1, y + BADGE_INNER_RADIUS - 1],
        outline=color + (255,),
        width=BADGE_STROKE_WIDTH
    )

    # Number text
    try:
        font = ImageFont.truetype("fonts/Arvo-Bold.ttf", NUMBER_FONT_SIZE)
    except:
        font = ImageFont.load_default()

    draw.text((x, y), str(number), font=font, fill=color + (255,), anchor="mm")


def composite_card(texture_path, art_path, label_path, number, seed, trim_threshold=220, badge_inset=8, shield_bg=None):
    """
    Composite one card:
    1. Crop random rectangle from aged paper texture (for background)
    2. Place art with black border (60px margins)
    3. Add badge
    4. Add label below art
    Returns RGBA PIL Image.
    """
    rng = random.Random(seed)

    # Create canvas with background (texture or solid color)
    if BACKGROUND_COLOR:
        # Solid color background
        if BACKGROUND_COLOR.lower() == "white":
            bg_color = (255, 255, 255, 255)
        elif BACKGROUND_COLOR.lower() == "cream":
            bg_color = (245, 240, 225, 255)
        elif BACKGROUND_COLOR.startswith("#"):
            # Parse hex color
            r = int(BACKGROUND_COLOR[1:3], 16)
            g = int(BACKGROUND_COLOR[3:5], 16)
            b = int(BACKGROUND_COLOR[5:7], 16)
            bg_color = (r, g, b, 255)
        else:
            bg_color = (255, 255, 255, 255)  # Default to white if unrecognized
        canvas = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), bg_color)
    else:
        # Texture background (default)
        canvas = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT))
        texture = Image.open(texture_path).convert("RGB")
        bg = crop_random_rectangle(texture, CARD_WIDTH, CARD_HEIGHT, rng)
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
    # Trim disabled: source JPEGs are already manually cleaned
    # art = trim_white_edges(art, trim_threshold)

    # Scale to fit width, then crop excess height equally from top/bottom
    art_aspect = art.width / art.height
    new_w = art_w
    new_h = int(new_w / art_aspect)
    art = art.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Crop excess height if taller than available space
    if new_h > art_h:
        excess = new_h - art_h
        top_crop = excess // 2
        bottom_crop = excess - top_crop
        art = art.crop((0, top_crop, new_w, new_h - bottom_crop))
        new_h = art_h

    # Align art to top-left of available space (no centering — margins are predictable)
    art_x = art_left
    art_y = art_top

    # Draw solid border background FIRST (art will sit on top)
    # PIL rectangle is inclusive of [x1,y1] but exclusive of [x2,y2], so adjust coordinates
    draw = ImageDraw.Draw(canvas)
    border_left = art_x - ART_BORDER_WIDTH
    border_top = art_y - ART_BORDER_WIDTH
    border_right = art_x + new_w + ART_BORDER_WIDTH
    border_bottom = art_y + new_h + ART_BORDER_WIDTH
    draw.rectangle(
        [border_left, border_top, border_right - 1, border_bottom - 1],
        fill=BORDER_COLOR + (255,)
    )

    # Composite art on top of border
    canvas.alpha_composite(art, (art_x, art_y))

    # Draw outer border around entire card (if specified) as four filled rectangles
    if CARD_BORDER_WIDTH > 0:
        # Left edge
        draw.rectangle([0, 0, CARD_BORDER_WIDTH, CARD_HEIGHT], fill=BORDER_COLOR + (255,))
        # Right edge
        draw.rectangle([CARD_WIDTH - CARD_BORDER_WIDTH, 0, CARD_WIDTH, CARD_HEIGHT], fill=BORDER_COLOR + (255,))
        # Top edge
        draw.rectangle([0, 0, CARD_WIDTH, CARD_BORDER_WIDTH], fill=BORDER_COLOR + (255,))
        # Bottom edge
        draw.rectangle([0, CARD_HEIGHT - CARD_BORDER_WIDTH, CARD_WIDTH, CARD_HEIGHT], fill=BORDER_COLOR + (255,))

    # Draw number badge at upper-left corner of art (inset by badge_inset)
    badge_x = art_x + BADGE_OUTER_RADIUS + badge_inset
    badge_y = art_y + BADGE_OUTER_RADIUS + badge_inset
    draw_badge(canvas, number, badge_x, badge_y, bg_color=shield_bg)

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
    """Read composite_cards.tsv: [number, label_text, cropped_art_filename, shield_bg]"""
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            shield_bg_val = row.get("shield_bg", "") or ""
            shield_bg = shield_bg_val.strip() if shield_bg_val else None
            rows.append({
                "number": int(row["number"].strip()),
                "label_text": row["label"].strip(),
                "art_filename": row["image_filename"].strip(),
                "shield_bg": shield_bg,  # None or hex string = transparent or colored
            })
    return rows


def label_filename_from_text(label_text):
    """Derive label PNG filename from label text. E.g., 'El Cine' -> 'el_cine.png'"""
    return label_text.replace(" ", "_").lower() + ".png"


def calculate_label_scale(labels_dir, available_width):
    """
    Calculate scale factor so the longest label fits in available width.
    All labels are saved at 200px height; scale them proportionally for composite.
    """
    reference_label = "la_carretera.png"
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
    global MARGIN_WIDTH, ART_BORDER_WIDTH, CARD_BORDER_WIDTH, BACKGROUND_COLOR, BADGE_OUTER_RADIUS, BADGE_INNER_RADIUS, NUMBER_FONT_SIZE
    if args.margin_width is not None:
        MARGIN_WIDTH = args.margin_width
    if args.art_border_width is not None:
        ART_BORDER_WIDTH = args.art_border_width
    if args.card_border_width is not None:
        CARD_BORDER_WIDTH = args.card_border_width
    if args.background_color is not None:
        BACKGROUND_COLOR = args.background_color
    if args.badge_outer_radius is not None:
        BADGE_OUTER_RADIUS = args.badge_outer_radius
    if args.badge_inner_radius is not None:
        BADGE_INNER_RADIUS = args.badge_inner_radius
    if args.number_font_size is not None:
        NUMBER_FONT_SIZE = args.number_font_size

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

    # Limit cards if requested
    if args.limit:
        cards = cards[:args.limit]

    for card in cards:
        number = card["number"]
        label_text = card["label_text"]
        art_filename = card["art_filename"]
        shield_bg = card.get("shield_bg")

        art_path = os.path.join(args.art_dir, art_filename)
        label_filename = label_filename_from_text(label_text)
        label_path = os.path.join(args.labels_dir, label_filename)

        if not os.path.exists(art_path):
            print(f"  [SKIP] {number:02d} {label_text:30s} (art not found)")
            continue

        try:
            card_img = composite_card(
                texture_path, art_path, label_path, number, seed + number,
                args.trim_threshold, args.badge_inset, shield_bg
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
    parser.add_argument(
        "--card-border-width", type=int, default=None,
        help=f"Black line thickness around entire card edge (pixels, default: {CARD_BORDER_WIDTH})"
    )
    parser.add_argument(
        "--background-color", type=str, default=None,
        help="Background color: 'white', 'cream', or hex '#RRGGBB' (default: texture)"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limit to first N cards (for testing)"
    )
    parser.add_argument(
        "--trim-threshold", type=int, default=220,
        help="Lightness threshold for background trimming (0-255, lower=more aggressive, default: 220)"
    )
    parser.add_argument(
        "--badge-inset", type=int, default=BADGE_INSET,
        help=f"How far inside the border to place badge (pixels, default: {BADGE_INSET})"
    )
    parser.add_argument(
        "--badge-outer-radius", type=int, default=None,
        help=f"Badge outer circle radius (pixels, default: {BADGE_OUTER_RADIUS})"
    )
    parser.add_argument(
        "--badge-inner-radius", type=int, default=None,
        help=f"Badge inner circle radius (pixels, default: {BADGE_INNER_RADIUS})"
    )
    parser.add_argument(
        "--number-font-size", type=int, default=None,
        help=f"Number font size (points, default: {NUMBER_FONT_SIZE})"
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    main(args)
