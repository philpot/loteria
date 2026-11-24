import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

def composite_labels(input_dir, output_path, cols=4, dpi=150, include_labels=True, label_size=12):
    """Composite all label images into a single printable sheet"""

    # Find all PNG files
    label_files = sorted(Path(input_dir).glob("*.png"))
    if not label_files:
        print(f"No PNG files found in {input_dir}")
        return

    print(f"Found {len(label_files)} label images")

    # Load images
    images = []
    labels = []
    for img_path in label_files:
        try:
            img = Image.open(img_path)
            images.append(img)
            labels.append(img_path.stem.replace('_', ' ').title())
        except Exception as e:
            print(f"Error loading {img_path}: {e}")

    if not images:
        print("No images loaded")
        return

    # Calculate grid dimensions
    rows = math.ceil(len(images) / cols)
    print(f"Grid: {rows} rows x {cols} columns")

    # Get image dimensions (assume all are same size)
    img_width, img_height = images[0].size

    # Calculate canvas size (8.5x11 inches at dpi)
    canvas_width_inches = 8.5
    canvas_height_inches = 11
    canvas_width = int(canvas_width_inches * dpi)
    canvas_height = int(canvas_height_inches * dpi)

    # Calculate cell size to fit grid on canvas with margin
    margin = 20
    available_width = canvas_width - (2 * margin)
    available_height = canvas_height - (2 * margin)

    cell_width = available_width // cols
    cell_height = available_height // rows

    # Scale images to fit cells
    scale = min(cell_width / img_width, cell_height / img_height)
    if include_labels:
        scale = min(scale, (cell_height - label_size - 5) / img_height)

    scaled_width = int(img_width * scale)
    scaled_height = int(img_height * scale)

    print(f"Scaling images to {scaled_width}x{scaled_height}")

    # Create canvas
    canvas = Image.new('RGB', (canvas_width, canvas_height), color='white')
    draw = ImageDraw.Draw(canvas)

    # Try to load a font for labels
    font = None
    if include_labels:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", label_size)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", label_size)
            except:
                font = ImageFont.load_default()

    # Composite images
    for idx, (img, label) in enumerate(zip(images, labels)):
        row = idx // cols
        col = idx % cols

        # Scale image
        scaled_img = img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

        # Calculate position
        x = margin + col * cell_width + (cell_width - scaled_width) // 2
        y = margin + row * cell_height + (cell_height - scaled_height) // 2

        if include_labels:
            y += label_size // 2

        # Paste image
        if scaled_img.mode == 'RGBA':
            canvas.paste(scaled_img, (x, y), scaled_img)
        else:
            canvas.paste(scaled_img, (x, y))

        # Add label
        if include_labels and font:
            label_y = margin + row * cell_height + 5
            # Center label text
            bbox = draw.textbbox((0, 0), label, font=font)
            label_width = bbox[2] - bbox[0]
            label_x = margin + col * cell_width + (cell_width - label_width) // 2
            draw.text((label_x, label_y), label, fill='black', font=font)

    # Save
    canvas.save(output_path)
    print(f"Saved: {output_path}")
    print(f"Size: {canvas_width}x{canvas_height} pixels ({canvas_width/dpi:.1f}x{canvas_height/dpi:.1f} inches)")

def main():
    parser = argparse.ArgumentParser(description='Composite label images into a single printable sheet')
    parser.add_argument('--input', default='generated_labels', help='Input directory (default: generated_labels)')
    parser.add_argument('--output', default='labels_contact_sheet.png', help='Output image path')
    parser.add_argument('--cols', type=int, default=4, help='Number of columns (default: 4)')
    parser.add_argument('--dpi', type=int, default=150, help='DPI for printable output (default: 150)')
    parser.add_argument('--no-labels', action='store_true', help='Do not include label names')
    parser.add_argument('--label-size', type=int, default=12, help='Label font size (default: 12)')

    args = parser.parse_args()

    composite_labels(
        args.input,
        args.output,
        cols=args.cols,
        dpi=args.dpi,
        include_labels=not args.no_labels,
        label_size=args.label_size
    )

if __name__ == '__main__':
    main()
