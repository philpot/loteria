import argparse
import base64
import os
import sys
from google import genai
from pathlib import Path

def read_labels_from_tsv(tsv_path):
    """Extract labels from cards.tsv"""
    labels = []
    with open(tsv_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i == 0:  # skip header
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                label = parts[1].strip()
                if label:
                    labels.append(label)
    return labels

def generate_label(label_text, uploaded_file, args):
    """Generate a single label image"""
    prompt = f"""Render a centered text graphic.

TEXT TO RENDER: "{label_text}"
- Render EXACTLY this text, preserving all capitalization and accents
- Do NOT change case, truncate, or omit any letters
- This is the ONLY text that should appear in the image

DO NOT COPY FROM REFERENCE: The reference image is for STYLE ONLY.
Do NOT extract or render any text from the reference image.

CANVAS: 1800px wide × 200px tall
- Solid white background (#FFFFFF)
- Text centered horizontally and vertically
- Nothing else on the canvas (no padding, borders, shadows, or extra elements)

TYPOGRAPHY:
- Clarendon slab-serif typeface, medium weight (not bold)
- Black ink (#1E1B18)
- Visible interior speckle and grain
- Rough, irregular edges with variable thickness
- Heavy ink irregularity: gaps, breaks, worn areas
- Curved serifs softened by ink pooling
- Authentic vintage letterpress appearance
- Do NOT render clean or digital-looking text

PROPORTIONS:
- Text should be a horizontal line, not compressed or stretched
- Preserve natural letter proportions (each letter should have its authentic width-to-height ratio from the Clarendon font)
- Do NOT render tall, narrow, stretched letters
- Do NOT apply perspective distortion, barrel curves, or warping

REFERENCE IMAGE:
- Study the reference image's visual characteristics: letterpress texture, ink pooling, serif curves, edge wear
- Apply only these VISUAL CHARACTERISTICS to your rendering
- Do NOT copy text or modify the Clarendon font's natural proportions"""

    generation_config = {
        'temperature': 1,
        'max_output_tokens': 65536,
        'top_p': 0.95,
        'thinking_level': args.thinking_level,
        'image_config': {'image_size': '1K'},
    }

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    interaction = client.interactions.create(
        model=args.model,
        input=[
            {
                "type": "image",
                "uri": uploaded_file.uri,
                "mime_type": uploaded_file.mime_type
            },
            {
                "type": "text",
                "text": prompt
            }
        ],
        system_instruction='Generate authentic letterpress text with visible ink imperfections, interior grain, and edge irregularity. Match the reference image\'s visual style exactly.',
        generation_config=generation_config,
        response_modalities=['image'],
    )

    # Extract and save image
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_files = []
    for step in interaction.steps:
        if step.type == 'model_output' and step.content:
            for part in step.content:
                if part.type == 'image':
                    image_data = base64.b64decode(part.data)
                    output_files.append(image_data)

    return interaction.usage, output_files

REFERENCE_IMAGE = 'font_style_gold.png'

def main():
    parser = argparse.ArgumentParser(description='Generate distressed Lotería label images using Gemini')
    parser.add_argument('--labels-file', default='cards.tsv', help='TSV file with labels (default: cards.tsv)')
    parser.add_argument('--reference-image', default=REFERENCE_IMAGE, help='Reference image path')
    parser.add_argument('--output', default='generated_labels', help='Output directory (default: generated_labels)')
    parser.add_argument('--model', default='models/gemini-3.1-flash-image', help='Gemini model to use')
    parser.add_argument('--thinking-level', default='minimal', choices=['minimal', 'low', 'medium', 'high'], help='Thinking level for model')
    parser.add_argument('--limit', type=int, help='Limit to N labels (useful for testing)')
    parser.add_argument('--start', type=int, default=0, help='Start index (0-based)')
    parser.add_argument('--labels', nargs='+', help='Generate only specific labels (space-separated)')
    parser.add_argument('--skip-existing', action='store_true', help='Skip labels that already have output files')
    parser.add_argument('--variants', type=int, default=1, help='Generate N variants per label (default: 1)')

    args = parser.parse_args()

    # Read all labels
    print(f"Reading labels from {args.labels_file}...")
    all_labels = read_labels_from_tsv(args.labels_file)
    print(f"Found {len(all_labels)} total labels")

    # Filter labels based on arguments
    if args.labels:
        # Normalize requested labels for flexible matching
        requested_normalized = [r.lower().replace('_', ' ') for r in args.labels]
        labels = [l for l in all_labels if l.lower() in requested_normalized]
        print(f"Filtering to {len(labels)} specified labels")
    else:
        labels = all_labels[args.start:]
        if args.limit:
            labels = labels[:args.limit]
            print(f"Limiting to {args.limit} labels (starting at index {args.start})")

    if not labels:
        print("No labels to generate")
        sys.exit(1)

    print(f"Uploading reference image from {args.reference_image}...")
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    uploaded_file = client.files.upload(file=args.reference_image)

    total_input_tokens = 0
    total_output_tokens = 0
    total_tokens = 0
    failed_labels = []

    for i, label in enumerate(labels, 1):
        label_slug = label.replace(' ', '_').lower()

        # Check if any variants exist
        existing_variants = list(Path(args.output).glob(f"{label_slug}*.png"))
        if args.skip_existing and existing_variants:
            print(f"\n[{i}/{len(labels)}] Skipping '{label}' ({len(existing_variants)} variants exist)")
            continue

        print(f"\n[{i}/{len(labels)}] Generating '{label}' ({args.variants} variant{'s' if args.variants > 1 else ''})...", end=" ", flush=True)
        try:
            variant_count = 0
            for v in range(args.variants):
                usage, image_data_list = generate_label(label, uploaded_file, args)

                # Save each image from this API call
                for image_data in image_data_list:
                    variant_count += 1
                    if args.variants > 1:
                        output_file = Path(args.output) / f"{label_slug}_v{variant_count}.png"
                    else:
                        output_file = Path(args.output) / f"{label_slug}.png"

                    with open(output_file, 'wb') as f:
                        f.write(image_data)

                    total_input_tokens += usage.total_input_tokens
                    total_output_tokens += usage.total_output_tokens
                    total_tokens += usage.total_tokens

            print(f"OK -> {variant_count} file(s)")
        except Exception as e:
            print(f"FAIL: {e}")
            failed_labels.append(label)

    print(f"\n=== BATCH COMPLETE ===")
    print(f"Generated: {len(labels) - len(failed_labels)}/{len(labels)}")
    print(f"Total input tokens: {total_input_tokens}")
    print(f"Total output tokens: {total_output_tokens}")
    print(f"Total tokens: {total_tokens}")
    if failed_labels:
        print(f"Failed labels: {', '.join(failed_labels)}")

if __name__ == '__main__':
    main()
