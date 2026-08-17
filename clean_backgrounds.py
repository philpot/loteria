import argparse
from pathlib import Path
from PIL import Image
import numpy as np

def get_lightness(rgb):
    """Calculate perceived lightness (0-255)"""
    r, g, b = rgb[:3]
    return (0.299 * r + 0.587 * g + 0.114 * b)

def clean_background(input_path, output_path, lightness_threshold=200):
    """
    Replace all light pixels (background) with pure white (#FFFFFF).
    Keep dark pixels (text) as-is.
    """
    img = Image.open(input_path)

    # Convert to RGB if needed
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    img_array = np.array(img)

    # Replace light pixels with white
    for i in range(img_array.shape[0]):
        for j in range(img_array.shape[1]):
            r, g, b = img_array[i, j]
            lightness = get_lightness((r, g, b))
            if lightness > lightness_threshold:
                # Light pixel (background/texture) → pure white
                img_array[i, j] = [255, 255, 255]

    result = Image.fromarray(img_array.astype('uint8'))
    result.save(output_path)
    return True

def main():
    parser = argparse.ArgumentParser(description='Clean backgrounds: replace light pixels with pure white')
    parser.add_argument('--input', default='generated_labels', help='Input directory (default: generated_labels)')
    parser.add_argument('--output', default='generated_labels_clean', help='Output directory (default: generated_labels_clean)')
    parser.add_argument('--lightness-threshold', type=int, default=200, help='Lightness threshold 0-255 (default: 200)')
    parser.add_argument('--in-place', action='store_true', help='Overwrite input files instead of creating new directory')

    args = parser.parse_args()

    input_dir = Path(args.input)
    if args.in_place:
        output_dir = input_dir
    else:
        output_dir = Path(args.output)
        output_dir.mkdir(exist_ok=True)

    # Find all PNGs
    image_files = sorted(input_dir.glob('*.png'))
    if not image_files:
        print(f"No PNG files found in {input_dir}")
        return

    print(f"Found {len(image_files)} images")
    print(f"Lightness threshold: {args.lightness_threshold}")
    print(f"Output: {output_dir}")

    success_count = 0
    failed = []

    for img_path in image_files:
        output_path = output_dir / img_path.name
        try:
            clean_background(img_path, output_path, args.lightness_threshold)
            print(f"OK: {img_path.name}")
            success_count += 1
        except Exception as e:
            print(f"ERROR: {img_path.name} - {e}")
            failed.append(img_path.name)

    print(f"\n=== COMPLETE ===")
    print(f"Cleaned: {success_count}/{len(image_files)}")
    if failed:
        print(f"Failed: {', '.join(failed)}")

if __name__ == '__main__':
    main()
