import argparse
from pathlib import Path
from PIL import Image

def composite_on_magenta(input_path, output_path):
    """Composite transparent image onto magenta background for artifact inspection"""
    img = Image.open(input_path)

    # Convert to RGBA if needed
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Create magenta background
    magenta = Image.new('RGB', img.size, (255, 0, 255))  # #FF00FF

    # Composite image onto magenta using alpha as mask
    magenta.paste(img, (0, 0), img)

    magenta.save(output_path)
    print(f"Composited: {input_path.name} -> {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Composite transparent labels onto magenta background for inspection')
    parser.add_argument('--input', default='generated_labels_transparent', help='Input directory')
    parser.add_argument('--output', default='magenta_test', help='Output directory')
    parser.add_argument('--labels', nargs='+', help='Specific labels to composite (default: all)')

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    if args.labels:
        # Composite specific labels
        for label in args.labels:
            img_path = input_dir / f"{label}.png"
            if not img_path.exists():
                print(f"Not found: {img_path}")
                continue
            output_path = output_dir / img_path.name
            composite_on_magenta(img_path, output_path)
    else:
        # Composite all
        image_files = sorted(input_dir.glob('*.png'))
        if not image_files:
            print(f"No PNG files found in {input_dir}")
            return

        for img_path in image_files:
            output_path = output_dir / img_path.name
            composite_on_magenta(img_path, output_path)

        print(f"Composited {len(image_files)} images to {output_dir}")

if __name__ == '__main__':
    main()
