import argparse
from pathlib import Path
from PIL import Image
import numpy as np

def measure_line_height(img_path):
    """
    Measure the line height of the first letter by finding the leftmost character.
    Returns: (label, line_height) or (label, None) if measurement fails
    """
    img = Image.open(img_path)

    # Convert to RGB
    if img.mode == 'RGBA':
        rgb = img.convert('RGB')
    else:
        rgb = img.convert('RGB')

    img_array = np.array(rgb)

    # Define "off-black" (text color) - should be around #1E1B18
    # Allow some variation: darker than gray (< 150)
    text_threshold = 150

    # Find leftmost column with text
    leftmost_col = None
    for col in range(img_array.shape[1]):
        column = img_array[:, col, :]
        # Check if any pixel in this column is dark (text)
        brightness = np.mean(column, axis=1)  # average RGB
        if np.any(brightness < text_threshold):
            leftmost_col = col
            break

    if leftmost_col is None:
        return None  # No text found

    # In the leftmost column, find the vertical span of text
    column = img_array[:, leftmost_col, :]
    brightness = np.mean(column, axis=1)
    dark_pixels = np.where(brightness < text_threshold)[0]

    if len(dark_pixels) == 0:
        return None

    top = dark_pixels[0]
    bottom = dark_pixels[-1]
    line_height = bottom - top + 1

    return line_height

def main():
    parser = argparse.ArgumentParser(description='Measure line height of first letter in transparent labels')
    parser.add_argument('--input', default='generated_labels_transparent', help='Input directory (default: generated_labels_transparent)')

    args = parser.parse_args()

    input_dir = Path(args.input)
    image_files = sorted(input_dir.glob('*.png'))

    if not image_files:
        print(f"No PNG files found in {input_dir}")
        return

    print(f"Found {len(image_files)} images\n")

    measurements = []
    failed = []

    for img_path in image_files:
        label = img_path.stem
        try:
            height = measure_line_height(img_path)
            if height is not None:
                measurements.append((label, height))
                print(f"{label:30s}  {height:3d}px")
            else:
                print(f"{label:30s}  FAILED (no text detected)")
                failed.append(label)
        except Exception as e:
            print(f"{label:30s}  ERROR: {e}")
            failed.append(label)

    # Statistics
    if measurements:
        heights = [h for _, h in measurements]
        min_h = min(heights)
        max_h = max(heights)
        avg_h = sum(heights) / len(heights)
        print(f"\n=== STATS ===")
        print(f"Min: {min_h}px")
        print(f"Max: {max_h}px")
        print(f"Avg: {avg_h:.0f}px")
        print(f"Range: {max_h - min_h}px")

if __name__ == '__main__':
    main()
