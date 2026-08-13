import csv
import os
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# =====================================================================
# CONFIGURATION & ITERATIVE TUNING PARAMETERS
# Adjust these values to fine-tune font sizes, positioning, and aging
# =====================================================================

# File Paths
CSV_PATH = "cards.csv"               # Path to your CSV
INPUT_DIR = "./raw_art"              # Folder containing AI art images
OUTPUT_DIR = "./final_cards"          # Folder where finished cards will be saved

# Font Configuration
# Pass the filename or full path to Playfair (e.g., 'PlayfairDisplay-SemiBold.ttf' for weight 600)
TITLE_FONT_PATH = "PlayfairDisplay-SemiBold.ttf"
TITLE_FONT_PATH = "fonts/Playfair_144pt-SemiBold.ttf"
TITLE_FONT_PATH = "fonts/Clarendon Bold.otf"
TITLE_FONT_PATH = "fonts/Clarendon Regular.otf"
TITLE_FONT_SIZE = 160                 # Adjust height of centered card title
NUMBER_FONT_PATH = "fonts/Arvo-Bold.ttf"
NUMBER_FONT_SIZE = 128                # Adjust height of card number inside badge

# Color & Ink (Off-black carbon ink look)
INK_COLOR = (30, 27, 24)             # Dark charcoal (R, G, B)

# Double-Circle Badge (Lower-Left Corner)
BADGE_CENTER_X = 150                  # Horizontal offset from left edge
BADGE_CENTER_Y_FROM_BOTTOM = 200      # Vertical offset from bottom edge
BADGE_OUTER_RADIUS = 96              # Radius of outer circle
BADGE_INNER_RADIUS = 84              # Radius of inner circle
BADGE_STROKE_WIDTH = 3               # Ring thickness

# Centered Title Position
TITLE_CENTER_Y_FROM_BOTTOM = 200      # Vertical center of title text from bottom edge

# Programmatic Distressing / Aging Controls
ENABLE_DISTRESS = True
INK_BLEED_BLUR = 1.2                 # Softens razor-sharp vector edges (0.3 to 1.0)
NOISE_SPECKLE_DENSITY = 0.15         # Chips tiny microscopic spots out of ink (0.0 to 0.15)


# =====================================================================
# CORE FUNCTIONS
# =====================================================================

def load_playfair_font(font_path, size, weight=600):
    """Loads Playfair font with fallback handling for variable fonts."""
    try:
        font = ImageFont.truetype(font_path, size)
        # Handle variable font weight setting if applicable
        if hasattr(font, "set_variation_by_axes"):
            try:
                font.set_variation_by_axes([weight])
            except Exception:
                pass
        return font
    except OSError:
        print(f"Warning: Could not find '{font_path}'. Falling back to default font.")
        return ImageFont.load_default()


def load_arvo_font(font_path, size, weight=600):
    """Loads Arvo font with fallback handling for variable fonts."""
    try:
        font = ImageFont.truetype(font_path, size)
        # Handle variable font weight setting if applicable
        if hasattr(font, "set_variation_by_axes"):
            try:
                font.set_variation_by_axes([weight])
            except Exception:
                pass
        return font
    except OSError:
        print(f"Warning: Could not find '{font_path}'. Falling back to default font.")
        return ImageFont.load_default()



def create_distressed_overlay(image_size, card_number, card_label):
    """Renders typography and badge onto a distressed transparent overlay."""
    width, height = image_size

    # Create transparent layer for ink drawing
    ink_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ink_layer)

    # Load fonts
    title_font = load_playfair_font(TITLE_FONT_PATH, TITLE_FONT_SIZE, weight=800)
    number_font = load_arvo_font(NUMBER_FONT_PATH, NUMBER_FONT_SIZE, weight=600)

    ink_rgba = INK_COLOR + (255,)  # Solid off-black

    # --- 1. DRAW DOUBLE-CIRCLE BADGE (Lower-Left) ---
    cx = BADGE_CENTER_X
    cy = height - BADGE_CENTER_Y_FROM_BOTTOM

    # Outer ring
    r_out = BADGE_OUTER_RADIUS
    draw.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out],
                 outline=ink_rgba, width=BADGE_STROKE_WIDTH)

    # Inner ring
    r_in = BADGE_INNER_RADIUS
    draw.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in],
                 outline=ink_rgba, width=BADGE_STROKE_WIDTH)

    # Card Number inside badge
    num_str = str(card_number)
    draw.text((cx, cy), num_str, font=number_font, fill=ink_rgba, anchor="mm")

    # --- 2. DRAW CENTERED TITLE ---
    title_y = height - TITLE_CENTER_Y_FROM_BOTTOM
    title_x = width // 2
    draw.text((title_x, title_y), card_label, font=title_font, fill=ink_rgba, anchor="mm")

    # --- 3. APPLY DISTRESS / AGING EFFECT ---
    if ENABLE_DISTRESS:
        # A. Ink Spread / Edge Bleed (Micro Gaussian Blur)
        ink_layer = ink_layer.filter(ImageFilter.GaussianBlur(radius=INK_BLEED_BLUR))

        # B. Letterpress Erosion (Microscopic noise chips out of the alpha channel)
        r, g, b, alpha = ink_layer.split()
        alpha_pixels = alpha.load()

        for x in range(width):
            for y in range(height):
                if alpha_pixels[x, y] > 0:  # Only affect drawn ink
                    if random.random() < NOISE_SPECKLE_DENSITY:
                        # Reduce opacity randomly to simulate worn woodblock ink
                        alpha_pixels[x, y] = int(alpha_pixels[x, y] * random.uniform(0.2, 0.7))

        ink_layer = Image.merge("RGBA", (r, g, b, alpha))

    return ink_layer


def process_card(image_filename, card_number, card_label):
    """Composites typography onto an art image and saves the output."""
    input_path = os.path.join(INPUT_DIR, image_filename)
    if not os.path.exists(input_path):
        print(f"Skipping: {input_path} not found.")
        return

    base_image = Image.open(input_path).convert("RGBA")

    # Create typography overlay matching base image size
    overlay = create_distressed_overlay(base_image.size, card_number, card_label)

    # Composite overlay onto base card
    final_card = Image.alpha_composite(base_image, overlay)

    # Save output
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{card_number:02d}_{image_filename}")
    final_card.convert("RGB").save(output_path, quality=95)
    print(f"Generated: {output_path}")


def main():
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
