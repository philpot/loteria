import fal_client

#



# Line Work: Bold, uniform, heavy black ink outlines. Simple, repetitive cross-hatching and fine line hatching are used for shading and texture, not smooth gradients.

# Color & Background: Especially in the background, flat, slightly desaturated, vintage primary color palette (dusty black and white, terra cotta, dusty pink, terra cotta).  Maintain the floral and greenery in the current location.  A very soft blue or yellow background can be used, but the contrast should not be jarring.

# Framing & Text: Result must be in portait orientation, not landscape.  The illustration is enclosed in a crisp grid box without border. Below the art, centered in an aged serif block typeface, are the words "La Calavera" in title case.   Use the attached font_style.png, believed to be Clarendon, Egyptienne or similar for font styling details for the card title.

# prompt_text = """

# Full-bleed 2:3 vertical canvas on an aged cream textured paper background.
# The central artwork is entirely enclosed inside a single thin black rectangular frame line.
# A wide, completely blank, solid plain cream paper margin fills the bottom 20% of the canvas below the frame line.
# Style features bold black ink outlines, flat muted colors (sage green, dusty pink, mustard yellow), and clean unidirectional line shading.
# """



# Load your master prompt template
prompt_text = """
MAIN SUBJECT: A 19th-century commercial lithography relief print of a calavera/sugar skull in Mexican folk art
ARTISTIC STYLE: Bold black ink outlines, unidirectional line shading, flat muted palette (sage green, dusty pink, mustard yellow, medium dusty blue, off-black).
CARD FRAMING: Full-bleed 2:3 vertical card on aged cream paper, wide blank margin on the bottom 18%.
"""

result = fal_client.subscribe(
    "fal-ai/flux/dev",
    arguments={
        "prompt": prompt_text.strip(),
        "image_size": {"width": 896, "height": 1344},  # 2:3 aspect ratio
        "num_inference_steps": 28,
        "guidance_scale": 3.5,
        "num_images": 1,
    },
)

print("Generated Image URL:", result["images"][0]["url"])
