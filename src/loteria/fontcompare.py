"""Render test variants of a single card with different fonts and distress.

Reads a TSV specifying font family, weight, and distress level for each
variant, renders each onto the same card art, and outputs PNGs with
watermark labels for printing comparison.

Watermarks appear in the top right corner of each output, naming the
font/weight/distress combo so you can identify variants after printing.

Usage:
    python src/loteria/fontcompare.py [--input FILE] [--output DIR]
    python src/loteria/fontcompare.py --watermark-color green

Input TSV columns:
    number, label, image_filename, font_family, font_weight, distress

Example:
    17  El Adelantado  adelantado.png  clarendon  regular  0.75

Run from the repository root.
"""

import argparse
import csv
import os
import unicodedata

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

# Import the distress pipeline from compose_cards
import sys
sys.path.insert(0, os.path.dirname(__file__))
from compose_cards import (
    distress, font_for_cap_height, text_width, TARGET_CAP_HEIGHT,
    SUPERSAMPLE, SEED, INK_RGB, CANVAS_W, CANVAS_H
)

# =====================================================================
# CONFIGURATION
# =====================================================================
INPUT_TSV = "fontcompare.tsv"
OUTPUT_DIR = "./fontcompare_output"
WATERMARK_COLOR_DEFAULT = (255, 0, 0)  # neon red (R, G, B)
# WATERMARK_FONT_SIZE = 10
WATERMARK_FONT_SIZE = 50

# Map (family, weight) -> file path
FONT_PATHS = {
    ("clarendon", "regular"): "fonts/Clarendon Regular.otf",
    ("clarendon", "bold"): "fonts/Clarendon Bold.otf",
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="fontcompare",
        description=("Render test variants of a single card with different "
                     "fonts and distress levels for printing comparison."),
    )
    parser.add_argument(
        "--input", metavar="FILE", default=INPUT_TSV,
        help=f"TSV with variants (default {INPUT_TSV!r})")
    parser.add_argument(
        "--output", metavar="DIR", default=OUTPUT_DIR,
        help=f"output directory (default {OUTPUT_DIR!r})")
    parser.add_argument(
        "--watermark-color", metavar="COLOR",
        help="watermark color: red, green, or RGB triple like '255,0,0' "
             "(default red)")
    parser.add_argument(
        "--bg-color", metavar="COLOR",
        help="background color: RGB triple like '247,233,217' "
             "(default: sampled from top-left of art)")
    return parser.parse_args(argv)


def parse_color(color_str):
    """Parse a color name or RGB triple to (R, G, B)."""
    if color_str is None:
        return WATERMARK_COLOR_DEFAULT
    color_str = color_str.lower()
    if color_str == "red":
        return (255, 0, 0)
    if color_str == "green":
        return (0, 255, 0)
    if color_str == "blue":
        return (0, 0, 255)
    if "," in color_str:
        try:
            return tuple(int(x.strip()) for x in color_str.split(",")[:3])
        except ValueError:
            raise ValueError(f"invalid color triple: {color_str}")
    raise ValueError(f"unknown color: {color_str}")


def render_label(text, font_path, cap_height, distress_level, seed):
    """Render a label with the specified font and distress."""
    font = font_for_cap_height(font_path, cap_height * SUPERSAMPLE)
    cap_ss = float(cap_height * SUPERSAMPLE)

    # Render at the supersampled resolution
    ascent, descent = font.getmetrics()
    slack = int(round(0.08 * cap_ss))
    width = int(text_width(text, font)) + 2 * slack
    height = ascent + descent + 2 * slack

    sheet = Image.new("L", (width, height), 0)
    ImageDraw.Draw(sheet).text(
        (slack, slack + ascent), text, font=font, fill=255, anchor="ls")

    rng = np.random.default_rng(seed)
    coverage = distress(
        np.asarray(sheet, dtype=np.float32) / 255.0, cap_ss, rng,
        distress_level)

    alpha = Image.fromarray(
        (coverage * 255.0 + 0.5).astype(np.uint8), mode="L"
    ).resize((width // SUPERSAMPLE, height // SUPERSAMPLE), Image.BOX)

    out = Image.new("RGBA", alpha.size, INK_RGB + (0,))
    out.putalpha(alpha)
    return out.crop(alpha.getbbox()) if alpha.getbbox() else out


def add_watermark(canvas, text, color):
    """Add a watermark label in the top right corner."""
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",
                                  WATERMARK_FONT_SIZE)
    except (OSError, IOError):
        font = ImageFont.load_default()

    draw = ImageDraw.Draw(canvas)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width_px = bbox[2] - bbox[0]
    text_height_px = bbox[3] - bbox[1]

    x = CANVAS_W - text_width_px - 8
    y = 8
    draw.text((x, y), text, font=font, fill=color, anchor="lt")


def compose_variant(art_path, number, label, font_family, font_weight,
                    distress_level, watermark_color, bg_color=None):
    """Render one variant card."""
    art = Image.open(art_path).convert("RGBA")
    paper = bg_color if bg_color else art.getpixel((4, 4))[:3]
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), paper + (255,))
    canvas.paste(art, (0, 0))

    font_key = (font_family.lower(), font_weight.lower())
    if font_key not in FONT_PATHS:
        raise ValueError(f"unknown font: {font_key}")
    font_path = FONT_PATHS[font_key]

    if not os.path.exists(font_path):
        raise FileNotFoundError(f"font not found: {font_path}")

    title = render_label(label, font_path, TARGET_CAP_HEIGHT,
                         distress_level, SEED + number)
    x = (CANVAS_W - title.width) // 2
    y = 2265 - title.height // 2
    canvas.alpha_composite(title, (x, y))

    watermark_text = (
        f"{font_family} {font_weight} {distress_level:.2f}".lower())
    add_watermark(canvas, watermark_text, watermark_color)

    return canvas


def main(args):
    if not os.path.exists(args.input):
        print(f"[FAIL] Input TSV not found: {args.input}")
        return

    watermark_color = parse_color(args.watermark_color)
    bg_color = parse_color(args.bg_color) if args.bg_color else None
    os.makedirs(args.output, exist_ok=True)

    with open(args.input, encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row_num, row in enumerate(reader, start=1):
            number = int(row["number"].strip())
            label = unicodedata.normalize("NFC", row["label"].strip())
            image_filename = unicodedata.normalize(
                "NFC", row["image_filename"].strip())
            font_family = row["font_family"].strip().lower()
            font_weight = row["font_weight"].strip().lower()
            distress = float(row["distress"].strip())

            art_path = os.path.join("./cropped_art", image_filename)
            if not os.path.exists(art_path):
                print(f"  [FAIL] art not found: {art_path}")
                continue

            try:
                canvas = compose_variant(art_path, number, label,
                                         font_family, font_weight, distress,
                                         watermark_color, bg_color)
            except Exception as e:
                print(f"  [FAIL] row {row_num}: {e}")
                continue

            out_filename = (
                f"fontcompare_{number:03d}_{font_family}_{font_weight}"
                f"_{distress:.2f}.png".replace(" ", "_"))
            out_path = os.path.join(args.output, out_filename)
            canvas.convert("RGB").save(out_path)
            print(f"  [OK] {out_filename}")

    print(f"\nWrote to {args.output}")


if __name__ == "__main__":
    args = parse_args()
    main(args)
