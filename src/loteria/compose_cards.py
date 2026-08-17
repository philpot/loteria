"""Composite label text and number badges onto guillotined card art.

Three layers, bottom to top: the cropped artwork, a double-ring number
badge in the upper left, and a distressed title label centered in the
paper band below the art.

Deck coherence is the point. Every parameter here is a deck-wide
constant, and the only thing that varies per card is the random seed,
so all 56 labels are impressions from one press rather than 56
independent interpretations. Distress amounts are expressed as
fractions of cap height, so changing the output scale rescales the
texture with the type instead of coarsening it.

Cap height is derived, not chosen. The widest label in the deck sets
the limit: the script measures it, finds the largest size at which it
still fits MAX_LABEL_WIDTH, and uses that size for all 56. Picking a
size first and hoping the longest label fits is what produced the
oversized 'La Bicicleta' label in the Gemini exports.

Defaults are calibrated against the 'bandera' export, the reference
card with a good label: 136 px cap height, centered, vertical center
2265 px down a 2528 px card.

Usage:
    python src/loteria/compose_cards.py --help
    python src/loteria/compose_cards.py --sweep
    python src/loteria/compose_cards.py --only bandera
    python src/loteria/compose_cards.py

Run from the repository root.
"""

import argparse
import csv
import os
import unicodedata

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

# =====================================================================
# CONFIGURATION
# =====================================================================
CSV_PATH = "cards.tsv"
ART_DIR = "./cropped_art"
OUTPUT_DIR = "./composed_cards"

TITLE_FONT_PATH = "fonts/Clarendon Bold.otf"
NUMBER_FONT_PATH = "fonts/Arvo-Bold.ttf"

# Canvas. Matches the original export size; the art is pasted at the
# top and the label sits at a fixed y, so titles align across the deck
# even though the cropped art heights differ.
CANVAS_W = 1696
CANVAS_H = 2528

INK_RGB = (30, 27, 24)               # #1E1B18 warm carbon black

# Label geometry, measured off the 'bandera' reference.
TARGET_CAP_HEIGHT = 136              # preferred cap height in px
MAX_LABEL_WIDTH = 1400               # widest label may not exceed this
LABEL_CENTER_Y = 2265                # vertical center of the label

# Number badge. Values carried over from gen.py, which proved this
# treatment on the correcaminos card.
BADGE_CENTER_X = 180
BADGE_CENTER_Y = 180
BADGE_OUTER_RADIUS = 75
BADGE_INNER_RADIUS = 63
BADGE_STROKE_WIDTH = 4
NUMBER_FONT_SIZE = 80
BADGE_BG_RGB = (245, 240, 225)       # cream, masks the art beneath

# Render at this multiple and area-average down. Supersampling is what
# turns a hard glyph mask into smooth alpha coverage; thresholding the
# alpha instead is what gives the existing labels their stair-stepped
# dotted rim.
SUPERSAMPLE = 4

SEED = 20250814                      # per-card seed is SEED + number

# Global distress multiplier. 0.5 reads as too little and 1.0 as too
# much on Clarendon Bold, so the working value sits between them.
INTENSITY = 0.75

# --- Distress, as fractions of cap height ---------------------------
# Carved-edge wander: the impression edge is not straight.
WARP_SIGMA_FRAC = 0.10
WARP_AMP_FRAC = 0.012

# Ink bleed: strokes swell slightly and unevenly along their length.
BLEED_RADIUS_FRAC = 0.008
BLEED_MIN = 0.35
BLEED_MAX = 1.00
BLEED_FIELD_FRAC = 0.18

# Pooling where slab serifs bracket into stems.
POOL_SIGMA_FRAC = 0.035
POOL_THRESHOLD = 0.55
POOL_STRENGTH = 0.60

# Ink starvation: bites chipped out of the edges.
VOID_SCALE_FRAC = 0.045
VOID_QUANTILE = 0.986
VOID_STRENGTH = 0.85

# Interior mottling: the speckle inside the strokes on the 'bandera'
# reference. Grain must stay coarse enough to survive print -- below
# about 0.005 in it averages to flat gray instead of reading as
# texture. Set MOTTLE_STRENGTH to 0.0 for solid ink.
MOTTLE_SCALE_FRAC = 0.030
MOTTLE_QUANTILE = 0.93
MOTTLE_STRENGTH = 0.30

# Edge grain, confined to a band along the boundary.
GRAIN_SIGMA_SS = 1.6
GRAIN_STRENGTH = 0.30
GRAIN_BAND_FRAC = 0.012

EDGE_CONTRAST = 3.0                  # firm the boundary back up

# Sweep renders every face against every level, so weight and distress
# can be judged together. Bold and Regular respond differently to the
# same intensity: the amplitudes scale with cap height, not stroke
# width, so a lighter face loses proportionally more of each stem.
SWEEP_FONTS = (
    "fonts/Clarendon Bold.otf",
    "fonts/Clarendon Regular.otf",
)
SWEEP_LEVELS = (0.75, 0.85, 1.0)

# Two phrases, because they fail differently. The longest label sets
# the width limit; the diacritics are the deck's most fragile marks,
# and ten cards carry them. A tilde or acute is far thinner than a
# stem, so it breaks up long before the letterforms do.
SWEEP_PHRASES = ("El Correcaminos", "La Piñata Güey Misión")


# =====================================================================
# TYPE METRICS
# =====================================================================

def _cap_height(font):
    """Inked height of 'H' in pixels at this font size."""
    ascent, descent = font.getmetrics()
    canvas = Image.new("L", (font.size * 3, ascent + descent + 8), 0)
    draw = ImageDraw.Draw(canvas)
    draw.text((4, ascent + 4), "H", font=font, fill=255, anchor="ls")
    bbox = canvas.getbbox()
    if bbox is None:
        raise ValueError("font rendered no ink for 'H'")
    return bbox[3] - bbox[1]


def font_for_cap_height(path, target_px):
    """Return the font whose cap height is closest to target_px."""
    probe_size = 200
    measured = _cap_height(ImageFont.truetype(path, probe_size))
    size = max(1, round(probe_size * target_px / measured))
    for _ in range(8):
        font = ImageFont.truetype(path, size)
        got = _cap_height(font)
        if got == target_px:
            return font
        size = max(1, size + (1 if got < target_px else -1))
    return ImageFont.truetype(path, size)


def text_width(text, font):
    """Advance width of a string at this font size."""
    return ImageDraw.Draw(Image.new("L", (1, 1))).textlength(text, font=font)


def deck_cap_height(labels, font_path, max_width, preferred):
    """Largest cap height <= preferred at which every label fits.

    Returns (cap_height, widest_label). Because one size is used for
    the whole deck, the widest label is the binding constraint.
    """
    widest = max(labels, key=lambda s: text_width(
        s, font_for_cap_height(font_path, preferred)))
    cap = preferred
    while cap > 8:
        font = font_for_cap_height(font_path, cap)
        if text_width(widest, font) <= max_width:
            return cap, widest
        cap -= 2
    return cap, widest


# =====================================================================
# DISTRESS
# =====================================================================

def _smooth_noise(rng, shape, sigma):
    """Zero-mean unit-variance noise at a given correlation length."""
    field = ndimage.gaussian_filter(
        rng.standard_normal(shape), sigma, mode="reflect")
    spread = field.std()
    return field if spread < 1e-9 else field / spread


def _disk(radius):
    """Boolean disk footprint for morphological operations."""
    r = max(1, int(round(radius)))
    ys, xs = np.mgrid[-r:r + 1, -r:r + 1]
    return (xs * xs + ys * ys) <= (r * r + 0.5)


def distress(mask, cap_ss, rng, intensity):
    """Apply ink behavior to a supersampled glyph mask.

    Stages follow the physical order of an impression: the carved edge
    wanders, ink spreads, ink pools in concave corners, some ink fails
    to transfer at the edges, the interior mottles, and paper grain
    roughens the boundary.
    """
    m = mask.astype(np.float32)

    amp = WARP_AMP_FRAC * cap_ss * intensity
    if amp > 0.01:
        sigma = max(1.0, WARP_SIGMA_FRAC * cap_ss)
        dy = _smooth_noise(rng, m.shape, sigma) * amp
        dx = _smooth_noise(rng, m.shape, sigma) * amp
        ys, xs = np.indices(m.shape, dtype=np.float32)
        m = ndimage.map_coordinates(
            m, [ys + dy, xs + dx], order=1, mode="constant", cval=0.0)

    radius = BLEED_RADIUS_FRAC * cap_ss * intensity
    if radius >= 1.0:
        bled = ndimage.grey_dilation(m, footprint=_disk(radius))
        field = _smooth_noise(
            rng, m.shape, max(1.0, BLEED_FIELD_FRAC * cap_ss))
        field = np.clip(field * 0.5 + 0.5, 0.0, 1.0)
        m = m + (bled - m) * (BLEED_MIN + (BLEED_MAX - BLEED_MIN) * field)

    # Just outside a concave junction the blurred mask is high because
    # ink surrounds it on two sides; outside a convex corner it is low.
    # Adding ink where the blur is high fills serif brackets only.
    blurred = ndimage.gaussian_filter(
        m, max(1.0, POOL_SIGMA_FRAC * cap_ss), mode="constant")
    lift = np.clip(
        (blurred - POOL_THRESHOLD) / max(1e-6, 1.0 - POOL_THRESHOLD), 0, 1)
    m = np.clip(m + POOL_STRENGTH * intensity * lift * (1.0 - m), 0, 1)

    solid = m > 0.5
    if solid.any():
        dist_in = ndimage.distance_transform_edt(solid)
        dist_out = ndimage.distance_transform_edt(~solid)
        band_px = max(1.0, GRAIN_BAND_FRAC * cap_ss)
        edge_band = np.exp(-((dist_in + dist_out) ** 2) / (2 * band_px ** 2))
    else:
        dist_in = np.zeros_like(m)
        edge_band = np.zeros_like(m)

    void_field = ndimage.gaussian_filter(
        rng.standard_normal(m.shape),
        max(1.0, VOID_SCALE_FRAC * cap_ss), mode="reflect")
    cut = np.quantile(void_field, VOID_QUANTILE)
    span = max(1e-6, void_field.max() - cut)
    voids = np.clip((void_field - cut) / span, 0, 1)
    m = np.clip(m - VOID_STRENGTH * intensity * voids * edge_band, 0, 1)

    # Interior mottling, kept away from the boundary so it reads as
    # uneven ink rather than as a ragged edge.
    if MOTTLE_STRENGTH > 0:
        grain = ndimage.gaussian_filter(
            rng.standard_normal(m.shape),
            max(1.0, MOTTLE_SCALE_FRAC * cap_ss), mode="reflect")
        cut = np.quantile(grain, MOTTLE_QUANTILE)
        span = max(1e-6, grain.max() - cut)
        speck = np.clip((grain - cut) / span, 0, 1)
        interior = np.clip(dist_in / max(1.0, 2 * band_px), 0, 1)
        m = np.clip(m - MOTTLE_STRENGTH * intensity * speck * interior, 0, 1)

    grain = _smooth_noise(rng, m.shape, GRAIN_SIGMA_SS)
    m = np.clip(m + GRAIN_STRENGTH * intensity * grain * edge_band, 0, 1)

    return np.clip((m - 0.5) * EDGE_CONTRAST + 0.5, 0.0, 1.0)


def render_label(text, font, cap_ss, seed, intensity=None):
    """Render one label to RGBA with distress carried in the alpha.

    intensity defaults to the module INTENSITY, read at call time so a
    command-line override takes effect.
    """
    if intensity is None:
        intensity = INTENSITY
    rng = np.random.default_rng(seed)
    ascent, descent = font.getmetrics()
    slack = int(round(0.08 * cap_ss))
    width = int(text_width(text, font)) + 2 * slack
    height = ascent + descent + 2 * slack

    sheet = Image.new("L", (width, height), 0)
    ImageDraw.Draw(sheet).text(
        (slack, slack + ascent), text, font=font, fill=255, anchor="ls")

    coverage = distress(
        np.asarray(sheet, dtype=np.float32) / 255.0, cap_ss, rng, intensity)

    alpha = Image.fromarray(
        (coverage * 255.0 + 0.5).astype(np.uint8), mode="L"
    ).resize((width // SUPERSAMPLE, height // SUPERSAMPLE), Image.BOX)

    out = Image.new("RGBA", alpha.size, INK_RGB + (0,))
    out.putalpha(alpha)
    return out.crop(alpha.getbbox()) if alpha.getbbox() else out


# =====================================================================
# COMPOSITING
# =====================================================================

def draw_badge(canvas, number):
    """Draw the double-ring number badge in the upper left."""
    draw = ImageDraw.Draw(canvas)
    cx, cy = BADGE_CENTER_X, BADGE_CENTER_Y
    ink = INK_RGB + (255,)

    draw.ellipse(
        [cx - BADGE_OUTER_RADIUS, cy - BADGE_OUTER_RADIUS,
         cx + BADGE_OUTER_RADIUS, cy + BADGE_OUTER_RADIUS],
        fill=BADGE_BG_RGB + (255,), outline=ink, width=BADGE_STROKE_WIDTH)
    draw.ellipse(
        [cx - BADGE_INNER_RADIUS, cy - BADGE_INNER_RADIUS,
         cx + BADGE_INNER_RADIUS, cy + BADGE_INNER_RADIUS],
        outline=ink, width=BADGE_STROKE_WIDTH)

    font = ImageFont.truetype(NUMBER_FONT_PATH, NUMBER_FONT_SIZE)
    draw.text((cx, cy), str(number), font=font, fill=ink, anchor="mm")


def compose_card(art_path, number, label, font, cap_ss):
    """Build one finished card: art, badge, label."""
    art = Image.open(art_path).convert("RGBA")

    # Fill the canvas with the card's own paper tone sampled from its
    # top-left corner, so the band below the art shows no seam.
    paper = art.getpixel((4, 4))[:3]
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), paper + (255,))
    canvas.paste(art, (0, 0))

    draw_badge(canvas, number)

    title = render_label(label, font, cap_ss, SEED + number)
    x = (CANVAS_W - title.width) // 2
    y = LABEL_CENTER_Y - title.height // 2
    canvas.alpha_composite(title, (x, y))
    return canvas


def read_cards():
    """Read cards.tsv into (number, label, filename) tuples."""
    with open(CSV_PATH, encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = []
        for row in reader:
            rows.append((
                int(row["number"].strip()),
                unicodedata.normalize("NFC", row["label"].strip()),
                unicodedata.normalize("NFC", row["image_filename"].strip()),
            ))
    return rows


def main(only=None):
    rows = read_cards()
    cap, widest = deck_cap_height(
        [r[1] for r in rows], TITLE_FONT_PATH,
        MAX_LABEL_WIDTH, TARGET_CAP_HEIGHT)
    print(f"Deck cap height {cap}px, set by {widest!r} "
          f"(limit {MAX_LABEL_WIDTH}px)")
    if cap < TARGET_CAP_HEIGHT:
        print(f"  reduced from {TARGET_CAP_HEIGHT}px to fit")

    font = font_for_cap_height(TITLE_FONT_PATH, cap * SUPERSAMPLE)
    cap_ss = float(cap * SUPERSAMPLE)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for number, label, filename in rows:
        if only and unicodedata.normalize("NFC", only) not in filename:
            continue
        art_path = os.path.join(ART_DIR, filename)
        if not os.path.exists(art_path):
            print(f"  [FAIL] {label:20s} missing art {art_path}")
            continue
        card = compose_card(art_path, number, label, font, cap_ss)
        out = os.path.join(OUTPUT_DIR, f"{number:02d}_{filename}")
        card.convert("RGB").save(out)
        print(f"  [OK]   {number:02d} {label}")

    print(f"\nWrote to {OUTPUT_DIR}")


def _face_tag(font_path):
    """Short name for a font file, used in sweep output filenames."""
    stem = os.path.splitext(os.path.basename(font_path))[0]
    return stem.replace("Clarendon", "").strip().lower() or "face"


def sweep():
    """Render the sweep phrase across every face and intensity.

    Cap height is held at TARGET_CAP_HEIGHT rather than derived, so the
    faces are compared at identical cap height and only weight and
    distress differ.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    cap_ss = float(TARGET_CAP_HEIGHT * SUPERSAMPLE)

    for font_path in SWEEP_FONTS:
        if not os.path.exists(font_path):
            print(f"  [WARN] missing font {font_path}")
            continue
        tag = _face_tag(font_path)
        font = font_for_cap_height(font_path, TARGET_CAP_HEIGHT * SUPERSAMPLE)

        for phrase_index, phrase in enumerate(SWEEP_PHRASES):
            width = int(text_width(phrase, font)) // SUPERSAMPLE
            print(f"{tag}: {phrase!r} is {width}px wide at "
                  f"{TARGET_CAP_HEIGHT}px cap")

            for level in SWEEP_LEVELS:
                title = render_label(
                    phrase, font, cap_ss, SEED + phrase_index, level)
                sheet = Image.new(
                    "RGB", (title.width + 80, title.height + 80),
                    (247, 238, 223))
                sheet.paste(title, (40, 40), title)
                path = os.path.join(
                    OUTPUT_DIR,
                    f"sweep_{tag}_p{phrase_index}_{level:.2f}x.png")
                sheet.save(path)
                print(f"  [OK] {path}  {title.width}x{title.height}")


def parse_args(argv=None):
    """Build the command line. Tuning knobs are exposed as options so
    the distress can be adjusted without editing module constants."""
    parser = argparse.ArgumentParser(
        prog="compose_cards",
        description=("Composite distressed title labels and number "
                     "badges onto guillotined Loteria card art."),
        epilog=("Examples:\n"
                "  compose_cards.py --sweep\n"
                "  compose_cards.py --only bandera --intensity 0.85\n"
                "  compose_cards.py --font 'fonts/Clarendon Regular.otf'\n"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--sweep", action="store_true",
        help="render the sweep phrases across every face and intensity "
             "instead of composing cards")
    parser.add_argument(
        "--only", metavar="SLUG",
        help="compose only cards whose art filename contains SLUG")
    parser.add_argument(
        "--intensity", type=float, metavar="X",
        help=f"global distress multiplier (default {INTENSITY})")
    parser.add_argument(
        "--font", metavar="PATH",
        help=f"title font (default {TITLE_FONT_PATH!r})")
    parser.add_argument(
        "--cap", type=int, metavar="PX",
        help=f"preferred cap height before width fitting "
             f"(default {TARGET_CAP_HEIGHT})")
    parser.add_argument(
        "--max-width", type=int, metavar="PX",
        help=f"widest label may not exceed this "
             f"(default {MAX_LABEL_WIDTH}); lowering it lowers the "
             f"whole deck's cap height")
    parser.add_argument(
        "--out", metavar="DIR",
        help=f"output directory (default {OUTPUT_DIR!r})")
    return parser.parse_args(argv)


def apply_overrides(args):
    """Push command-line values onto the module constants."""
    global INTENSITY, TITLE_FONT_PATH, TARGET_CAP_HEIGHT
    global MAX_LABEL_WIDTH, OUTPUT_DIR

    if args.intensity is not None:
        INTENSITY = args.intensity
    if args.font is not None:
        TITLE_FONT_PATH = args.font
    if args.cap is not None:
        TARGET_CAP_HEIGHT = args.cap
    if args.max_width is not None:
        MAX_LABEL_WIDTH = args.max_width
    if args.out is not None:
        OUTPUT_DIR = args.out


if __name__ == "__main__":
    args = parse_args()
    apply_overrides(args)
    if args.sweep:
        sweep()
    else:
        main(only=args.only)
