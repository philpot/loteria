import csv
import io
import os
from google import genai
from google.genai import types
from PIL import Image

# =====================================================================
# CONFIGURATION
# =====================================================================
CSV_PATH = "cards.csv"                 # CSV containing 'number' and 'label'
OUTPUT_RAW_DIR = "./raw_titles"        # Raw AI outputs
OUTPUT_CLEAN_DIR = "./transparent_titles" # Processed transparent PNGs
STYLE_REF_PATH = "font_style_2.png"   # Path to 'El Cine' reference image

# Model Selection (imagen-3.0-generate-002 or imagen-3.0-fast-generate-001)
MODEL_NAME = "imagen-3.0-generate-002"

# Initialize Google GenAI Client
client = genai.Client()

# System prompt forcing uniform cap-height and woodblock style
PROMPT_TEMPLATE = """
A high-resolution single-line vintage text graphic centered on a flat solid white (#FFFFFF) background featuring the words: "{label}"

TYPOGRAPHY & DISTRESS STYLE:
- Style: Heavy-inked, bold Clarendon slab-serif print with authentic 19th-century hand-carved woodblock character, matching the style of the reference image.
- SIZING CONSTRAINT: All letters must maintain a UNIFORM CAP-HEIGHT and natural, uncompressed, wide letter proportions. Do NOT scale up short words to fill the image.
- Edge Distortion: Heavy hand-carved edge wobble, variable stem thickness, organic ink bleed, and soft ink-pooled inner corners.
- Color & Ink: 100% solid off-black carbon ink (#1E1B18).

CANVAS & LAYOUT:
- Single horizontal line centered on a clean, pure flat solid white (#FFFFFF) background.
- Zero paper texture, zero shadows, zero borders or framing lines.
"""


def make_transparent_and_trim(img: Image.Image, threshold: int = 230) -> Image.Image:
    """
    Converts pure white background to 100% transparent alpha channel
    and crops tightly to the ink bounding box.
    """
    img = img.convert("RGBA")
    datas = img.getdata()

    new_data = []
    for item in datas:
        # Check if pixel is close to pure white background
        if item[0] > threshold and item[1] > threshold and item[2] > threshold:
            new_data.append((255, 255, 255, 0))  # Fully transparent
        else:
            new_data.append((item[0], item[1], item[2], 255))  # Solid ink

    img.putdata(new_data)

    # Crop tightly around the text glyphs
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    return img


def generate_title(card_number: int, label: str):
    """Calls Gemini API via generate_content to generate a single title graphic."""
    os.makedirs(OUTPUT_RAW_DIR, exist_ok=True)
    os.makedirs(OUTPUT_CLEAN_DIR, exist_ok=True)

    raw_path = os.path.join(OUTPUT_RAW_DIR, f"{card_number:02d}_{label}.jpg")
    clean_path = os.path.join(OUTPUT_CLEAN_DIR, f"{card_number:02d}_{label}.png")

    if os.path.exists(clean_path):
        print(f"Skipping [{card_number:02d} {label}] - Already generated.")
        return

    print(f"Generating title [{card_number:02d}]: '{label}'...")

    prompt = PROMPT_TEMPLATE.format(label=label)

    contents = [prompt]
    if os.path.exists(STYLE_REF_PATH):
        ref_image = Image.open(STYLE_REF_PATH)
        contents.append(ref_image)

    try:
        # Using generate_content for unified model calls
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="image/jpeg",
            )
        )

        # Extract image bytes from returned content parts
        image_bytes = None
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    break

        if image_bytes:
            image = Image.open(io.BytesIO(image_bytes))
            image.save(raw_path, "JPEG", quality=95)

            # Process transparency & crop bounding box
            transparent_img = make_transparent_and_trim(image)
            transparent_img.save(clean_path, "PNG")
            print(f"  ✓ Saved clean transparent title to {clean_path}")
        else:
            print(f"  ❌ No image bytes returned in response for '{label}'")

    except Exception as e:
        print(f"  ❌ Error generating '{label}': {e}")


def main():
    if not os.path.exists(CSV_PATH):
        print(f"Error: Could not find '{CSV_PATH}'.")
        return

    with open(CSV_PATH, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            num = int(row["number"].strip())
            label = row["label"].strip()
            generate_title(num, label)


if __name__ == "__main__":
    main()
