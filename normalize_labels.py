import argparse
from pathlib import Path
from PIL import Image
import numpy as np

def get_lightness(rgb):
    """Calculate perceived lightness of RGB (0-255 scale)"""
    r, g, b = rgb[:3]
    return (0.299 * r + 0.587 * g + 0.114 * b)

def normalize_label_image(input_path, output_path, target_height=128, canvas_width=1200, canvas_height=1600, lightness_threshold=200):
    """
    Normalize a label image:
    1. Clean background (convert white/light pixels to transparent)
    2. Detect text bounding box
    3. Scale text to target height (preserving aspect ratio)
    4. Clip width to canvas_width if needed (centered crop)
    5. Center vertically on transparent canvas
    """

    img = Image.open(input_path)

    # Convert to RGBA for transparency
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    img_array = np.array(img)

    # Step 1: Clean background - convert light pixels to transparent
    for i in range(img_array.shape[0]):
        for j in range(img_array.shape[1]):
            r, g, b = img_array[i, j, :3]
            lightness = get_lightness((r, g, b))
            if lightness > lightness_threshold:
                # Light pixel (white/off-white) - make transparent
                img_array[i, j, 3] = 0

    img = Image.fromarray(img_array)

    # Step 2: Find bounding box of text (non-transparent pixels)
    alpha = np.array(img.split()[3])
    non_transparent = np.where(alpha > 0)

    if len(non_transparent[0]) == 0:
        print(f"Warning: No text found in {input_path}")
        return False

    # Get bounding box
    y_min, y_max = non_transparent[0].min(), non_transparent[0].max()
    x_min, x_max = non_transparent[1].min(), non_transparent[1].max()

    # Crop to bounding box
    text_img = img.crop((x_min, y_min, x_max + 1, y_max + 1))

    # Step 3: Scale text to target height (preserving aspect ratio)
    text_height = text_img.height
    text_width = text_img.width
    if text_height > 0:
        scale = target_height / text_height
        new_width = int(text_img.width * scale)
        text_img = text_img.resize((new_width, target_height), Image.Resampling.LANCZOS)

        # Debug: print measurements
        label = input_path.stem
        print(f"  {label}: bbox={text_width}x{text_height}px, scale={scale:.3f}, result={new_width}x{target_height}px")

    # Step 4: Clip width if it exceeds canvas_width (centered crop)
    if text_img.width > canvas_width:
        crop_left = (text_img.width - canvas_width) // 2
        text_img = text_img.crop((crop_left, 0, crop_left + canvas_width, target_height))
        clipped = True
    else:
        clipped = False

    # Step 5: Create transparent canvas and center text vertically
    canvas = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))

    # Center text horizontally and vertically
    x_pos = (canvas_width - text_img.width) // 2
    y_pos = (canvas_height - target_height) // 2

    # Paste text onto canvas using alpha channel as mask
    canvas.paste(text_img, (x_pos, y_pos), text_img)

    # Save as PNG to preserve transparency
    canvas.save(output_path)
    return True, clipped

def main():
    parser = argparse.ArgumentParser(description='Normalize label images to consistent height with white background removed')
    parser.add_argument('--input', default='generated_labels', help='Input directory (default: generated_labels)')
    parser.add_argument('--output', default='generated_labels_normalized', help='Output directory (default: generated_labels_normalized)')
    parser.add_argument('--target-height', type=int, default=128, help='Target text height in pixels (default: 128)')
    parser.add_argument('--canvas-width', type=int, default=1200, help='Canvas width in pixels (default: 1200)')
    parser.add_argument('--canvas-height', type=int, default=1600, help='Canvas height in pixels (default: 1600)')
    parser.add_argument('--lightness-threshold', type=int, default=200, help='Lightness threshold for background removal 0-255 (default: 200)')

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    # Find all PNGs
    image_files = sorted(input_dir.glob('*.png'))
    if not image_files:
        print(f"No PNG files found in {input_dir}")
        return

    print(f"Found {len(image_files)} images")
    print(f"Target: {args.target_height}px height on {args.canvas_width}x{args.canvas_height} transparent canvas")

    success_count = 0
    clipped_count = 0
    failed = []

    for img_path in image_files:
        output_path = output_dir / img_path.name
        try:
            success, clipped = normalize_label_image(
                img_path,
                output_path,
                target_height=args.target_height,
                canvas_width=args.canvas_width,
                canvas_height=args.canvas_height,
                lightness_threshold=args.lightness_threshold
            )
            if success:
                marker = " [CLIPPED]" if clipped else ""
                print(f"OK: {img_path.name}{marker}")
                success_count += 1
                if clipped:
                    clipped_count += 1
            else:
                print(f"FAIL: {img_path.name} (no text detected)")
                failed.append(img_path.name)
        except Exception as e:
            print(f"ERROR: {img_path.name} - {e}")
            failed.append(img_path.name)

    print(f"\n=== COMPLETE ===")
    print(f"Processed: {success_count}/{len(image_files)}")
    print(f"Clipped: {clipped_count} (width exceeded {args.canvas_width}px)")
    print(f"Output: {output_dir}")
    if failed:
        print(f"Failed: {', '.join(failed)}")

if __name__ == '__main__':
    main()
