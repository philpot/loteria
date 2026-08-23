import fal_client

# 1. Upload your local reference image (e.g., 'raw_art/calavera_draft.jpg')
print("Uploading reference image...")
# image_url = fal_client.upload_file("raw_art/calavera_draft.jpg")
image_url = fal_client.upload_file("Web-Calavera2.png")
print(f"Uploaded to: {image_url}")

# 2. Define the positive prompt (No "don'ts" or negative words)
prompt_text = """
A 19th-century commercial lithography relief woodcut print of a sugar skull.
Centered composition on an aged cream textured paper background.
Solid mustard-yellow inner background field with clean black line border.
A wide, completely plain, solid cream paper margin fills the lower 20% of the canvas.
Flat muted colors (sage green, dusty pink, mustard yellow), bold black ink outlines, clean line shading.
"""

# 3. Run FLUX Image-to-Image
result = fal_client.subscribe(
    "fal-ai/flux/dev/image-to-image",
    arguments={
        "image_url": image_url,
        "prompt": prompt_text.strip(),
        "strength": 0.65,  # 0.1 = keep almost everything, 0.95 = rewrite almost everything
        "image_size": {"width": 896, "height": 1344},  # 2:3 ratio
        "num_inference_steps": 28,
        "guidance_scale": 3.5,
    },
)

print("Generated Image URL:", result["images"][0]["url"])
