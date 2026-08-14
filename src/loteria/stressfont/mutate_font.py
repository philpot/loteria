import sys

sys.path.append("/opt/homebrew/Cellar/fontforge/20251009_1/lib/python3.14/site-packages")

import fontforge
import psMat

# Input and Output paths
INPUT_FONT = "fonts/Clarendon Bold.otf"
OUTPUT_FONT = "fonts/Clarendon-Bold-Loteria.ttf"
INPUT_FONT = "fonts/Clarendon Regular.otf"
OUTPUT_FONT = "fonts/Clarendon-Regular-Loteria.ttf"

def mutate_font():
    print(f"Opening {INPUT_FONT}...")
    font = fontforge.open(INPUT_FONT)

    # Update font metadata so macOS recognizes it as a new font
    font.fontname = "ClarendonLoteria-Custom"
    font.familyname = "Clarendon Loteria"
    font.fullname = "Clarendon Loteria Custom Distressed"

    # Iterate through all printable glyphs (letters, numbers, accents)
    for glyph in font.glyphs():
        if glyph.unicode == -1:
            continue

        # 1. Expand strokes slightly to simulate heavy ink impression
        glyph.stroke("circular", 12, "round", "round")

        # 2. Add subtle organic outline noise/distortion
        # (Distorts vector control points slightly to give the 'wobbly' woodblock feel)
        glyph.addExtrema()
        glyph.simplify(1.5)

        # 3. Round sharp corners (softens the serifs like in 'El Cine')
        glyph.round()

    # Generate the new font file
    font.generate(OUTPUT_FONT)
    print(f"Success! Saved mutated font to: {OUTPUT_FONT}")

if __name__ == "__main__":
    mutate_font()
