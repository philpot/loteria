#!/usr/bin/env python3
"""
Scan regenerated cards for low contrast between art background and card background.
Identifies cards where the art background is too similar to the card background color.
"""

import argparse
from pathlib import Path
from PIL import Image
import numpy as np


def get_art_region(img_array, card_width, card_height, margin_width=60, label_height_fraction=0.18):
    """
    Extract the art region from a card image.
    Returns the art pixels (excluding margins and label area).
    """
    # Define art area (from composite_final.py dimensions)
    art_left = margin_width
    art_right = card_width - margin_width
    art_top = margin_width
    art_bottom = card_height - int(card_height * label_height_fraction)

    # Extract art region
    art_region = img_array[art_top:art_bottom, art_left:art_right, :3]
    return art_region


def get_dominant_color(region):
    """
    Get the lightest (most likely background) color in the art region.
    Samples the 95th percentile brightness to find background tone.
    """
    # Calculate brightness for each pixel
    brightness = region.mean(axis=2)  # Average of R,G,B

    # Find pixels in the brightest 10% (likely background/sky)
    threshold = np.percentile(brightness, 90)
    light_pixels = region[brightness > threshold]

    if len(light_pixels) == 0:
        # Fallback: use the brightest pixel
        brightest_idx = np.unravel_index(np.argmax(brightness), brightness.shape)
        return tuple(region[brightest_idx].astype(int))

    # Average of light pixels (background color)
    bg_color = light_pixels.mean(axis=0).astype(int)
    return tuple(bg_color)


def color_distance(rgb1, rgb2):
    """
    Calculate Euclidean distance between two RGB colors (0-255 scale).
    Returns distance (0-441.67).
    """
    return np.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))


def check_contrast(card_path, card_bg_rgb, distance_threshold=50):
    """
    Check if a card has sufficient contrast between art background and card background.
    Returns (card_name, art_color, distance, passes_threshold).
    """
    card_name = Path(card_path).stem

    try:
        img = Image.open(card_path).convert("RGB")
        img_array = np.array(img)

        # Extract art region
        art_region = get_art_region(img_array, img.width, img.height)

        # Get dominant color in art area
        art_bg_color = get_dominant_color(art_region)

        # Calculate distance
        distance = color_distance(art_bg_color, card_bg_rgb)

        # Check if contrast is sufficient
        passes = distance >= distance_threshold

        return card_name, art_bg_color, distance, passes
    except Exception as e:
        print(f"Error processing {card_path}: {e}")
        return card_name, None, None, False


def main():
    parser = argparse.ArgumentParser(
        description="Check card contrast between art background and card background"
    )
    parser.add_argument(
        "--card-dir", type=str, default="wheat",
        help="Directory containing regenerated cards (default: wheat)"
    )
    parser.add_argument(
        "--card-bg", type=str, default="#ECD8BC",
        help="Card background color in hex (default: #ECD8BC)"
    )
    parser.add_argument(
        "--threshold", type=int, default=50,
        help="Minimum color distance for acceptable contrast (default: 50)"
    )

    args = parser.parse_args()

    # Parse card background color
    card_bg_str = args.card_bg.lstrip("#")
    card_bg_rgb = (
        int(card_bg_str[0:2], 16),
        int(card_bg_str[2:4], 16),
        int(card_bg_str[4:6], 16)
    )
    print(f"Card background: #{args.card_bg} = RGB{card_bg_rgb}")
    print(f"Threshold: {args.threshold} (colors farther apart are OK)\n")

    # Find all cards
    card_dir = Path(args.card_dir)
    if not card_dir.exists():
        print(f"Error: {card_dir} not found")
        return

    card_files = sorted(card_dir.glob("*.png"))
    if not card_files:
        print(f"No PNG files in {card_dir}")
        return

    # Check contrast for each card
    low_contrast = []
    results = []

    for card_path in card_files:
        card_name, art_color, distance, passes = check_contrast(
            card_path, card_bg_rgb, args.threshold
        )

        if art_color is None:
            continue

        results.append((card_name, art_color, distance, passes))

        if not passes:
            low_contrast.append((card_name, art_color, distance))
            status = "LOW CONTRAST"
        else:
            status = "OK"

        print(f"  {card_name:35s}  Art: RGB{art_color}  Distance: {distance:6.1f}  [{status}]")

    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY: {len(low_contrast)}/{len(results)} cards have low contrast\n")

    if low_contrast:
        print("Cards needing regeneration/editing:")
        for card_name, art_color, distance in sorted(low_contrast, key=lambda x: x[2]):
            print(f"  {card_name:35s}  Distance: {distance:6.1f}  Art: RGB{art_color}")


if __name__ == "__main__":
    main()
