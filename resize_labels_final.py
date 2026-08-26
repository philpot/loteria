"""
Resize label PNGs for final compositing:
1. Crop to bounding box (remove transparent padding)
2. Scale by descender status:
   - No descenders: height = 200px
   - Has descenders: total height = 200 / descender_factor
3. Save to generated_labels_clean_black/ with suffix indicating descender handling
"""

import argparse
import os
from pathlib import Path
from PIL import Image
import numpy as np

DESCENDER_LETTERS = set('gjpqy')
DESCENDER_FACTOR = 0.85  # cap height is 85% of total height for descender strings

def has_descenders(label_text):
    """Check if label contains lowercase letters with descenders (g,j,p,q,y)"""
    return any(c in DESCENDER_LETTERS for c in label_text)

def crop_to_bounding_box(img):
    """Crop image to bounding box of non-transparent pixels"""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    alpha = np.array(img.split()[3])
    non_transparent = np.where(alpha > 0)

    if len(non_transparent[0]) == 0:
        return img  # All transparent, return as-is

    y_min, y_max = non_transparent[0].min(), non_transparent[0].max()
    x_min, x_max = non_transparent[1].min(), non_transparent[1].max()

    return img.crop((x_min, y_min, x_max + 1, y_max + 1))

def resize_label(img, label_text, target_cap_height=200):
    """
    Resize label to target height:
    - No descenders: height = target_cap_height
    - Has descenders: height = target_cap_height / descender_factor
    Preserves aspect ratio.
    """
    has_desc = has_descenders(label_text)

    if has_desc:
        target_height = int(target_cap_height / DESCENDER_FACTOR)
    else:
        target_height = target_cap_height

    # Scale preserving aspect ratio
    scale = target_height / img.height
    new_width = int(img.width * scale)
    resized = img.resize((new_width, target_height), Image.Resampling.LANCZOS)

    return resized, has_desc, target_height

def label_text_from_filename(filename):
    """Derive label text from filename. E.g., 'el_cine.png' -> 'El Cine'"""
    stem = filename.replace('.png', '')
    words = stem.split('_')
    return ' '.join(w.capitalize() for w in words)

def main(args):
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_files = sorted(input_dir.glob('*.png'))
    if not image_files:
        print(f"No PNG files found in {input_dir}")
        return

    print(f"Found {len(image_files)} images")
    print(f"Target cap height: {args.target_cap_height}px")
    print(f"Descender factor: {DESCENDER_FACTOR}")

    success = 0
    failed = []

    for img_path in image_files:
        filename = img_path.name
        label_text = label_text_from_filename(filename)

        try:
            img = Image.open(img_path).convert('RGBA')

            # Crop to bounding box
            cropped = crop_to_bounding_box(img)

            # Resize
            resized, has_desc, final_height = resize_label(
                cropped, label_text, args.target_cap_height
            )

            # Output filename with descender indicator
            suffix = "_desc" if has_desc else "_noDesc"
            output_name = filename.replace('.png', f'{suffix}.png')
            output_path = output_dir / output_name

            resized.save(output_path)

            desc_str = "desc" if has_desc else "no desc"
            print(f"OK: {filename:35s} -> {output_name:45s} ({resized.width}x{final_height}px, {desc_str})")
            success += 1

        except Exception as e:
            print(f"ERROR: {filename} - {e}")
            failed.append(filename)

    print(f"\n=== COMPLETE ===")
    print(f"Processed: {success}/{len(image_files)}")
    if failed:
        print(f"Failed: {', '.join(failed)}")

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Resize label PNGs: crop to bbox and scale by descender status"
    )
    parser.add_argument(
        '--input', default='generated_labels_transparent',
        help='Input directory (default: generated_labels_transparent)'
    )
    parser.add_argument(
        '--output', default='generated_labels_clean_black',
        help='Output directory (default: generated_labels_clean_black)'
    )
    parser.add_argument(
        '--target-cap-height', type=int, default=200,
        help='Target cap height in pixels (default: 200)'
    )
    return parser.parse_args(argv)

if __name__ == '__main__':
    args = parse_args()
    main(args)
