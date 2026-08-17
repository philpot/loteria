import sys

sys.path.append("/opt/homebrew/Cellar/fontforge/20251009_1/lib/python3.14/site-packages")

import fontforge
import psMat

# Input and Output paths
INPUT_FONT = "fonts/Clarendon Bold.otf"
OUTPUT_FONT = "fonts/Clarendon-Bold-Loteria.ttf"
# INPUT_FONT = "fonts/Clarendon Regular.otf"
# OUTPUT_FONT = "fonts/Clarendon-Regular-Loteria.ttf"


def mutate_font():
    print(f"Opening {INPUT_FONT}...")
    font = fontforge.open(INPUT_FONT)

    # 1. Convert to TrueType quadratic curves (Fixes 'Internal Error (overlap)' on OTF files)
    font.layers["Fore"].is_quadratic = True

    # 2. Update font metadata
    font.fontname = "ClarendonLoteria-Custom"
    font.familyname = "Clarendon Loteria"
    font.fullname = "Clarendon Loteria Custom Distressed"

    print("Swelling glyph stems and applying woodblock edge distortion...")
    for glyph in font.glyphs():
        if glyph.unicode == -1:
            continue

        # Save the original solid filled shape
        original_fill = glyph.foreground

        # Generate an outer stroke around the glyph outline
        # Increase 20 to 25-30 for heavier ink, decrease to 10-15 for lighter
        glyph.stroke("circular", 20, "round", "round")

        # Combine original solid fill back with the outer stroke
        glyph.foreground += original_fill

        # Merge stroke + fill into a single, solid emboldened shape
        glyph.removeOverlap()

        # Simplify vector points to soften razor-sharp serifs into woodblock-pressed edges
        glyph.simplify(2.5)
        glyph.round()



    # 3. Generate clean TrueType font file
    font.generate(OUTPUT_FONT)
    print(f"\nSuccess! Saved mutated solid font to: {OUTPUT_FONT}")


if __name__ == "__main__":
    mutate_font()
