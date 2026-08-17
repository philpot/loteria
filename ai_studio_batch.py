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
    prompt = f"""A centered text graphic on a cream background.
TEXT: "{label_text}" CRITICAL: Render the text EXACTLY as shown, preserving all capitalization and accents. Do not change case.
CRITICAL: The ONLY text that should appear is exactly: "{label_text}"
CRITICAL: Do NOT copy, extract, or render any text from the reference image—especially not "El Adelantado" or any other recognizable words. The reference image is ONLY for visual STYLE (texture, ink, serif curves, edge wear). Render ONLY the TEXT field above.
CRITICAL: Render ALL characters of the text. Never truncate or omit any letters, accents, or spaces.
CRITICAL: Do NOT render tall, narrow, stretched letters. Do NOT compress width while stretching height. Letters must maintain their natural aspect ratio.
CRITICAL: No perspective distortion. Text must be flat and straight, not curved or barrel-warped.
TYPOGRAPHY & STYLE:
Clarendon slab-serif typeface, medium weight (not bold)
Solid black ink (#1E1B18) with visible interior speckle and grain
Rough, irregular edges with variable thickness
Heavy ink irregularity: gaps, breaks, and worn areas throughout
Curved serifs that appear softened by ink pooling
Authentic vintage letterpress with obvious printing texture
Do NOT render clean or digital-looking
LAYOUT: - Text centered both horizontally and vertically - Text fills 35-40% of the image height - Solid cream background (#F7EEDF) - Nothing else on the canvas - No paper texture, no shadows, no frame, no borders  REFERENCE STYLE: Match the aesthetic of authentic 19th-century woodblock print typography.
REFERENCE: Match the reference image's letterpress texture, ink pooling, serif curves,
and edge wear. Apply only these visual attributes."""

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
        system_instruction='Generate authentic letterpress character with visible ink imperfections.\nInterior grain and edge irregularity are essential. Avoid clean digital typography.',
        generation_config=generation_config,
        response_modalities=['image'],
    )

    # Extract and save image
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{label_text.replace(' ', '_').lower()}.png"

    for step in interaction.steps:
        if step.type == 'model_output' and step.content:
            for part in step.content:
                if part.type == 'image':
                    image_data = base64.b64decode(part.data)
                    with open(output_file, 'wb') as f:
                        f.write(image_data)

    return interaction.usage, output_file

REFERENCE_IMAGE = 'src/loteria/manytext/font_style_2.png'
REFERENCE_IMAGE = 'generated_labels/el_adelantado.png'

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
        output_file = Path(args.output) / f"{label.replace(' ', '_').lower()}.png"

        if args.skip_existing and output_file.exists():
            print(f"\n[{i}/{len(labels)}] Skipping '{label}' (exists)")
            continue

        print(f"\n[{i}/{len(labels)}] Generating '{label}'...", end=" ", flush=True)
        try:
            usage, _ = generate_label(label, uploaded_file, args)
            print(f"OK -> {output_file}")
            print(f"  Tokens: {usage.total_input_tokens} in + {usage.total_output_tokens} out")

            total_input_tokens += usage.total_input_tokens
            total_output_tokens += usage.total_output_tokens
            total_tokens += usage.total_tokens
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
