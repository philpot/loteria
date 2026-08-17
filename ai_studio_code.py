import base64
import os
from google import genai
from google.genai import types
from IPython.display import Image, display
from pathlib import Path

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
)

generation_config = {
    'temperature': 1,
    'max_output_tokens': 65536,
    'top_p': 0.95,
    # 'thinking_level': 'high',
    'thinking_level': 'minimal',
    'image_config': {
        'image_size': '1K',
    },
}

REFERENCE_IMAGE_PATH = "src/loteria/manytext/font_style_2.png"

ITEM = "La Palma"

BELIEVED_PROMPT_INPUT = f"""A centered text graphic on a cream background.  TEXT: "{ITEM}" CRITICAL: Render the text EXACTLY as shown, preserving all capitalization and accents. Do not change case.
TYPOGRAPHY & STYLE:
Clarendon slab-serif typeface, medium weight (not bold)
Solid black ink (#1E1B18) with visible interior speckle and grain
Rough, irregular edges with variable thickness
Heavy ink irregularity: gaps, breaks, and worn areas throughout
Curved serifs that appear softened by ink pooling
Authentic vintage letterpress with obvious printing texture
Do NOT render clean or digital-looking
LAYOUT: - Text centered both horizontally and vertically - Text fills 35-40% of the image height - Solid cream background (#F7EEDF) - Nothing else on the canvas - No paper texture, no shadows, no frame, no borders  REFERENCE STYLE: Match the aesthetic of authentic 19th-century woodblock print typography.
EXAMPLE: hew closely to attached reference image"""

# Reference image uploaded once; reuse this URI
UPLOADED_REFERENCE_FILE_URL = "https://generativelanguage.googleapis.com/v1beta/files/jmymyu74bmih"

# Reconstruct uploaded file object from URI for use with Interactions API
# (The SDK needs the object, not just the URI string)
# For now, we'll re-upload to get the object; TODO: store the full object if possible
print("Re-uploading reference image to get file object...")
uploaded_file = client.files.upload(file=REFERENCE_IMAGE_PATH)


interaction = client.interactions.create(
    model='models/gemini-3.1-flash-image',
    input=[
        {
            "type": "image",
            "uri": uploaded_file.uri,
            "mime_type": uploaded_file.mime_type
        },
        {
            "type": "text",
            "text": BELIEVED_PROMPT_INPUT
        }
    ],
    system_instruction='Generate authentic letterpress character with visible ink imperfections.\nInterior grain and edge irregularity are essential. Avoid clean digital typography.',
    generation_config=generation_config,
    response_modalities=['image'],
)

output_dir = Path("generated_labels")
output_dir.mkdir(exist_ok=True)

label_text = BELIEVED_PROMPT_INPUT.split('TEXT: "')[1].split('"')[0]
output_file = output_dir / f"{label_text.replace(' ', '_').lower()}.png"

for step in interaction.steps:
    if step.type == 'model_output' and step.content:
        for part in step.content:
            if part.type == 'text':
                print(part.text)
            elif part.type == 'image':
                image_data = base64.b64decode(part.data)
                with open(output_file, 'wb') as f:
                    f.write(image_data)
                print(f"Saved: {output_file}")
                display(Image(data=image_data))

# Print usage metadata
if interaction.usage:
    print("\n--- Usage ---")
    print(f"Input tokens: {interaction.usage.total_input_tokens}")
    print(f"Output tokens: {interaction.usage.total_output_tokens}")
    print(f"Total tokens: {interaction.usage.total_tokens}")
else:
    print("\nNo usage metadata available")
