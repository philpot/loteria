import argparse
from pathlib import Path
from PIL import Image
import numpy as np

DESCENDER_LETTERS = set('gjpqy')

def measure_text_box(img_path):
    """
    Measure the bounding box of text in a transparent image.
    Returns: (width, raw_height, has_descenders) or None if measurement fails
    """
    img = Image.open(img_path)

    # Must be RGBA (transparent background)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    img_array = np.array(img)
    alpha = img_array[:, :, 3]

    # Find all non-transparent pixels
    non_transparent = np.where(alpha > 0)

    if len(non_transparent[0]) == 0:
        return None  # No text found

    # Get bounding box
    y_min, y_max = non_transparent[0].min(), non_transparent[0].max()
    x_min, x_max = non_transparent[1].min(), non_transparent[1].max()

    width = x_max - x_min + 1
    raw_height = y_max - y_min + 1

    return width, raw_height

def has_descenders(label_text):
    """Check if label contains letters with descenders"""
    return any(c.lower() in DESCENDER_LETTERS for c in label_text)

def main():
    parser = argparse.ArgumentParser(description='Measure text dimensions (width, height) with descender detection')
    parser.add_argument('--input', default='generated_labels_transparent', help='Input directory')
    parser.add_argument('--descender-adjust', type=float, default=0.85, help='Multiplier for labels with descenders (default: 0.85)')

    args = parser.parse_args()

    input_dir = Path(args.input)
    image_files = sorted(input_dir.glob('*.png'))

    if not image_files:
        print(f"No PNG files found in {input_dir}")
        return

    print(f"Found {len(image_files)} images")
    print(f"Descender adjustment: {args.descender_adjust}px\n")
    print(f"{'Label':<30} {'Width':>6} {'Raw Height':>12} {'Has Desc':>9} {'Adj Height':>11}")
    print("-" * 75)

    measurements = []
    failed = []

    for img_path in image_files:
        label = img_path.stem
        try:
            result = measure_text_box(img_path)
            if result is not None:
                width, raw_height = result
                has_desc = has_descenders(label)
                adj_height = int(raw_height * args.descender_adjust) if has_desc else raw_height

                measurements.append((label, width, raw_height, has_desc, adj_height))
                desc_str = "yes" if has_desc else "no"
                print(f"{label:<30} {width:>6}px {raw_height:>12}px {desc_str:>9} {adj_height:>11}px")
            else:
                print(f"{label:<30} FAILED (no text detected)")
                failed.append(label)
        except Exception as e:
            print(f"{label:<30} ERROR: {e}")
            failed.append(label)

    # Statistics
    if measurements:
        print("\n" + "=" * 75)
        heights = [h for _, _, _, _, h in measurements]
        raw_heights = [h for _, _, h, _, _ in measurements]
        widths = [w for _, w, _, _, _ in measurements]

        print(f"\nADJUSTED HEIGHT STATS:")
        print(f"  Min: {min(heights)}px")
        print(f"  Max: {max(heights)}px")
        print(f"  Avg: {sum(heights) / len(heights):.0f}px")
        print(f"  Range: {max(heights) - min(heights)}px")

        print(f"\nRAW HEIGHT STATS:")
        print(f"  Min: {min(raw_heights)}px")
        print(f"  Max: {max(raw_heights)}px")
        print(f"  Avg: {sum(raw_heights) / len(raw_heights):.0f}px")

        print(f"\nWIDTH STATS:")
        print(f"  Min: {min(widths)}px")
        print(f"  Max: {max(widths)}px")
        print(f"  Avg: {sum(widths) / len(widths):.0f}px")

        # Count descenders
        with_desc = sum(1 for _, _, _, has_desc, _ in measurements if has_desc)
        print(f"\nLabels with descenders: {with_desc}/{len(measurements)}")

    if failed:
        print(f"\nFailed: {len(failed)} - {', '.join(failed)}")

if __name__ == '__main__':
    main()
