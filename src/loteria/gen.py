import csv
import os
import random
from typing import Tuple
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops


# =====================================================================
# CONFIGURATION & ITERATIVE TUNING PARAMETERS
# =====================================================================

# File Paths
CSV_PATH = "cards.csv"               # Path to your CSV
INPUT_DIR = "./raw_art"              # Folder containing AI art images
OUTPUT_DIR = "./final_cards"         # Folder where finished cards will be saved

# Font Configuration
TITLE_FONT_PATH = "fonts/Clarendon Bold.otf"
TITLE_FONT_SIZE = 150                # Base height of centered card title
TITLE_STROKE_WIDTH = 2               # Adds extra weight/boldness to letter stems
TITLE_CONDENSE_FACTOR = 0.85         # Squeezes text horizontally (0.85 = 15% narrower)

NUMBER_FONT_PATH = "fonts/Arvo-Bold.ttf"
NUMBER_FONT_SIZE = 80               # Height of card number inside badge

# Color & Ink (Off-black carbon ink look)
INK_COLOR = (30, 27, 24)             # Dark charcoal (R, G, B)

# Double-Circle Badge (Lower-Left Corner)
BADGE_CENTER_X = 140                 # Horizontal offset from left edge
BADGE_CENTER_Y_FROM_BOTTOM = 200     # Vertical offset from bottom edge
BADGE_OUTER_RADIUS = 75              # Radius of outer circle
BADGE_INNER_RADIUS = 60              # Radius of inner circle
BADGE_STROKE_WIDTH = 4               # Ring thickness

# Centered Title Position
TITLE_CENTER_Y_FROM_BOTTOM = 200     # Vertical center of title text from bottom edge

# Programmatic Distressing Controls (Text Only)
ENABLE_DISTRESS = True
TEXT_BLUR_RADIUS = 2.8               # Controls depth of edge bite (Higher = rougher edges)
TEXT_NOISE_SCALE = 3                 # Controls chunkiness of paper fiber bites
TEXT_THRESHOLD = 125                 # Edge cut-off point (Lower = heavier ink spread)


# =====================================================================
# CORE FUNCTIONS
# =====================================================================

def load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Loads font file with graceful fallback."""
    try:
        return ImageFont.truetype(font_path, size)
    except OSError:
        print(f"Warning: Could not find '{font_path}'. Falling back to default font.")
        return ImageFont.load_default()


def apply_edge_distress(
    alpha_channel: Image.Image,
    blur_radius: float = 2.8,
    noise_scale: int = 3,
    threshold: int = 125
) -> Image.Image:
    """
    Distorts ONLY the outer edges of typography while keeping the interior 100% solid black.
    Prevents interior graying / salt-and-pepper artifacts.
    """
    w, h = alpha_channel.size

    # 1. Blur the crisp vector mask to create a soft edge gradient
    blurred = alpha_channel.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # 2. Generate coarse, organic noise for chunky fiber texture
    small_w, small_h = max(1, w // noise_scale), max(1, h // noise_scale)
    noise = Image.effect_noise((small_w, small_h), sigma=128).resize((w, h), Image.Resampling.BILINEAR)

    # 3. Blend noise directly into the edge gradient band
    distorted_gradient = ImageChops.overlay(blurred, noise)

    # 4. Hard Threshold: Force back to binary (0 or 255)
    # Interior stays solid black; exterior stays clear; edge becomes jagged!
    thresholded_alpha = distorted_gradient.point(lambda p: 255 if p > threshold else 0)

    return thresholded_alpha


def render_narrow_title(
    title_text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    ink_rgba: Tuple[int, int, int, int],
    condense_factor: float = 0.85,
    stroke_width: int = 2
) -> Image.Image:
    """Renders text on a temporary canvas and scales width horizontally to narrow the font."""
    # Measure native text bounding box
    dummy_img = Image.new("RGBA", (1, 1))
    draw_dummy = ImageDraw.Draw(dummy_img)
    bbox = draw_dummy.textbbox((0, 0), title_text, font=font, stroke_width=stroke_width)

    native_w = bbox[2] - bbox[0] + 40
    native_h = bbox[3] - bbox[1] + 40

    # Draw native resolution text
    temp_img = Image.new("RGBA", (native_w, native_h), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_img)
    temp_draw.text(
        (native_w // 2, native_h // 2),
        title_text,
        font=font,
        fill=ink_rgba,
        anchor="mm",
        stroke_width=stroke_width,
        stroke_fill=ink_rgba
    )

    # Compress horizontally
    condensed_w = max(1, int(native_w * condense_factor))
    narrow_img = temp_img.resize((condensed_w, native_h), Image.Resampling.LANCZOS)

    return narrow_img


def create_distressed_overlay(image_size: Tuple[int, int], card_number: int, card_label: str) -> Image.Image:
    """Composites narrow, distressed title text with a crisp, clean double-ring badge."""
    width, height = image_size
    ink_rgba = INK_COLOR + (255,)

    # Load fonts
    title_font = load_font(TITLE_FONT_PATH, TITLE_FONT_SIZE)
    number_font = load_font(NUMBER_FONT_PATH, NUMBER_FONT_SIZE)

    # ------------------------------------------------------------------
    # 1. RENDER TITLE TEXT & APPLY EDGE DISTRESS
    # ------------------------------------------------------------------
    text_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    # Generate narrowed title image
    title_img = render_narrow_title(
        card_label,
        title_font,
        ink_rgba,
        condense_factor=TITLE_CONDENSE_FACTOR,
        stroke_width=TITLE_STROKE_WIDTH
    )

    # Calculate title center in the remaining horizontal space right of badge
    badge_right_edge = BADGE_CENTER_X + BADGE_OUTER_RADIUS
    remaining_space_center = badge_right_edge + ((width - badge_right_edge) // 2)
    title_y = height - TITLE_CENTER_Y_FROM_BOTTOM

    # Paste title onto text layer
    paste_x = remaining_space_center - (title_img.width // 2)
    paste_y = title_y - (title_img.height // 2)
    text_layer.paste(title_img, (paste_x, paste_y), title_img)

    # Apply edge distress ONLY to text
    if ENABLE_DISTRESS:
        r, g, b, alpha = text_layer.split()
        distressed_alpha = apply_edge_distress(
            alpha,
            blur_radius=TEXT_BLUR_RADIUS,
            noise_scale=TEXT_NOISE_SCALE,
            threshold=TEXT_THRESHOLD
        )
        distressed_text_layer = Image.merge("RGBA", (r, g, b, distressed_alpha))
    else:
        distressed_text_layer = text_layer

    # ------------------------------------------------------------------
    # 2. RENDER CRISP BADGE & NUMBER (Undistressed)
    # ------------------------------------------------------------------
    badge_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw_badge = ImageDraw.Draw(badge_layer)

    cx = BADGE_CENTER_X
    cy = height - BADGE_CENTER_Y_FROM_BOTTOM

    # Outer and inner rings
    r_out, r_in = BADGE_OUTER_RADIUS, BADGE_INNER_RADIUS
    draw_badge.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], outline=ink_rgba, width=BADGE_STROKE_WIDTH)
    draw_badge.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], outline=ink_rgba, width=BADGE_STROKE_WIDTH)

    # Number inside badge
    draw_badge.text((cx, cy), str(card_number), font=number_font, fill=ink_rgba, anchor="mm")

    # ------------------------------------------------------------------
    # 3. COMBINE LAYERS
    # ------------------------------------------------------------------
    return Image.alpha_composite(distressed_text_layer, badge_layer)


def process_card(image_filename: str, card_number: int, card_label: str) -> None:
    """Composites typography onto an art image and saves the output."""
    input_path = os.path.join(INPUT_DIR, image_filename)
    if not os.path.exists(input_path):
        print(f"Skipping: '{input_path}' not found.")
        return

    base_image = Image.open(input_path).convert("RGBA")
    overlay = create_distressed_overlay(base_image.size, card_number, card_label)

    final_card = Image.alpha_composite(base_image, overlay)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{card_number:02d}_{image_filename}")
    final_card.convert("RGB").save(output_path, quality=95)
    print(f"Generated: {output_path}")


def main() -> None:
    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV file '{CSV_PATH}' not found.")
        return

    with open(CSV_PATH, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            process_card(
                image_filename=row["image_filename"].strip(),
                card_number=int(row["number"].strip()),
                card_label=row["label"].strip()
            )


if __name__ == "__main__":
    main()
