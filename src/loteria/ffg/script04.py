import fal_client
import os
import urllib.parse
import urllib.request

INPUT_FILE = "raw_art/calavera_draft.jpg"
OUTPUT_DIR = "raw_art"
BASE_NAME = "calavera_flux"

# 1. Upload your local reference image (e.g., 'raw_art/calavera_draft.jpg')
print("Uploading reference image...")
# image_url = fal_client.upload_file("raw_art/calavera_draft.jpg")
# image_url = fal_client.upload_file("Web-Calavera2.png")
image_url = "https://v3b.fal.media/files/b/0aa76fae/g2wjDk1QYKVlK2D1axfSg_Web-Calavera2.png"
print(f"Uploaded to: {image_url}")

OUTPUT_DIR = "flux_art"
CARD="calavera"

# 2. Define the positive prompt (No "don'ts" or negative words)
prompt_text = """
A 19th-century vintage copperplate etching of a sugar skull.
Style: Authentic woodcut printmaking, black line engraving.
Shading Technique: Every single shadow and contour is rendered using dense black parallel line hatching, cross-hatching, and fine pen-and-ink line work.
Colors: Flat muted antique colors (sage green, dusty pink, mustard yellow) placed behind the black line shading.
Composition: Central sugar skull isolated on a solid mustard-yellow background.
"""

result = fal_client.subscribe(
    "fal-ai/flux/dev",  # Standard text-to-image
    arguments={
        "prompt": prompt_text.strip(),
        "image_size": {"width": 896, "height": 1344},
        "num_inference_steps": 40,  # Bumping to 40 forces FLUX to render fine line detail
        "guidance_scale": 4.5,  # Higher guidance forces strict adherence to hatching
    },
)


# 3A. Get remote URL and download locally
generated_url = result["images"][0]["url"]

# 4. Extract unique file ID or filename from the URL (e.g., 'a-tKP8h4fChrDN8rh7W_I.jpg')
url_path = urllib.parse.urlparse(generated_url).path
url_filename = os.path.basename(url_path)  # Gets the remote filename/ID
url_id, _ = os.path.splitext(url_filename)  # Gets just the ID without extension

# 5. Construct local output path containing the remote URL ID
output_filename = f"{CARD}_{url_id}.jpg"
output_file_path = os.path.join(OUTPUT_DIR, output_filename)

# 6. Download image to local path
print(f"Downloading from: {generated_url}")
urllib.request.urlretrieve(generated_url, output_file_path)

print(f"Saved to: {output_file_path}")
