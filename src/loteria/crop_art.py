"""Guillotine the label band off exported Loteria cards.

Each exported card is artwork inside a thin dark frame, with a text
label in the cream margin below that frame. This script finds the
frame's lower edge per card and keeps everything above it, discarding
the label -- and, on the cards that grew a second frame or cross
hatching around their label, discarding those too.

Cropping is per card rather than at a shared constant because the
export geometry is not uniform: frame bottoms range from roughly 2050
to 2330, so no single cut line both clears every label and preserves
every artwork.

Detection rule. Frame lines are thin full-width dark runs; artwork can
also span the full width but is much thicker, so thickness filters it
out. The art frame bottom is the first thin line below the top frame
that is followed by a run of cream rows and then, further down, label
ink. That distinguishes it from lines inside the artwork (no cream gap
below) and from an outer frame drawn around the label (cream below,
but no ink beyond it).

Cards that fail detection are reported and skipped, not guessed at.
Add an entry to CROP_OVERRIDES to force a value by eye.

Usage:
    python src/loteria/crop_art.py dry    # report only, write nothing
    python src/loteria/crop_art.py        # write cropped art + manifest

Run from the repository root; paths below are relative to it.
"""

import glob
import os
import sys
import unicodedata

import numpy as np
from PIL import Image

# =====================================================================
# CONFIGURATION
# =====================================================================
INPUT_GLOB = "ddd/export/*.png"
OUTPUT_DIR = "./cropped_art"
MANIFEST_PATH = "./cropped_art/manifest.tsv"

# Cards whose source file lives outside the export folder, keyed by
# slug. Regenerated cards go here rather than being copied in.
SOURCE_OVERRIDES = {
    "diablito": "ddd/diablito/Gemini_Generated_Image_423les423les423l.png",
}

# Hand-picked crop lines for cards detection cannot resolve, keyed by
# slug. 'naranja' draws one frame with the label inside it, so there is
# no inner line to find; it needs a value chosen by eye or a rebuild.
CROP_OVERRIDES: dict[str, int] = {}

CROP_OVERRIDES["desfile"] =  2196
CROP_OVERRIDES["coyote"] =   2099
CROP_OVERRIDES["metro"] =    2176
CROP_OVERRIDES["maceta"] =   2151
CROP_OVERRIDES["vecino"] =   2114
CROP_OVERRIDES["mano"] =     2264
CROP_OVERRIDES["estrella"] = 1841
CROP_OVERRIDES["artista"] = 2223
CROP_OVERRIDES["bicicleta"] = 2140
CROP_OVERRIDES["cotorro"] = 2213
CROP_OVERRIDES["elote"] = 2146
CROP_OVERRIDES["lonchería"] = 2133
CROP_OVERRIDES["misión"] = 2191
CROP_OVERRIDES["músico"] = 2211
CROP_OVERRIDES["naranja"] = 2127
CROP_OVERRIDES["palma"] = 2281
CROP_OVERRIDES["tenis"] = 2205

# Skip cards whose output already exists.
SKIP_EXISTING = True

# --- Detection tuning ----------------------------------------------
DARK_CUTOFF = 110        # grayscale value below which a pixel is ink
FULL_ROW_FRAC = 0.60     # fraction of width a frame line must span
LINE_MIN_THICK = 4       # thinner runs are noise
LINE_MAX_THICK = 20      # thicker runs are artwork, not frame lines
ROW_INK_MIN = 15         # dark pixels for a row to count as inked
CREAM_GAP_MIN = 20       # cream rows required below the art frame
LABEL_SEARCH = 420       # how far below to look for label ink


def _runs(flags: np.ndarray, max_gap: int = 3):
    """Group True indices into (start, end) runs, merging small gaps."""
    idx = np.where(flags)[0]
    if not len(idx):
        return []
    out, start, prev = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - prev > max_gap:
            out.append((int(start), int(prev)))
            start = i
        prev = i
    out.append((int(start), int(prev)))
    return out


def find_frame_lines(dark_rows: np.ndarray, width: int):
    """Return (start, end) row ranges that look like frame lines."""
    wide = dark_rows > FULL_ROW_FRAC * width
    keep = []
    for start, end in _runs(wide):
        thickness = end - start + 1
        if LINE_MIN_THICK <= thickness <= LINE_MAX_THICK:
            keep.append((start, end))
    return keep


def find_art_bottom(dark_rows: np.ndarray, width: int, height: int):
    """Find the lower edge of the frame enclosing the artwork.

    Returns (bottom_y, frame_top_y) or (None, frame_top_y) when no
    candidate qualifies.
    """
    candidates = find_frame_lines(dark_rows, width)
    if len(candidates) < 2:
        return None, None

    frame_top = candidates[0][1]

    for start, end in candidates[1:]:
        gap_stop = min(height, end + 1 + CREAM_GAP_MIN)
        gap = dark_rows[end + 1:gap_stop]
        if len(gap) < CREAM_GAP_MIN or (gap >= ROW_INK_MIN).any():
            continue  # artwork continues below: not the frame bottom

        seek_stop = min(height, end + 1 + LABEL_SEARCH)
        beyond = dark_rows[gap_stop:seek_stop]
        if not (beyond >= ROW_INK_MIN).any():
            continue  # nothing below: an outer frame around the label

        return end, frame_top

    return None, frame_top


def find_frame_sides(dark: np.ndarray, top: int, bottom: int):
    """Return (left, right) columns of the frame within a row band."""
    band = dark[top:bottom + 1]
    if not band.size:
        return None, None
    cols = band.sum(axis=0)
    hits = np.where(cols > FULL_ROW_FRAC * band.shape[0])[0]
    if not len(hits):
        return None, None
    return int(hits.min()), int(hits.max())


def slug_for(path: str) -> str:
    """Card slug from an export filename, normalized to NFC.

    macOS stores accented names decomposed; normalizing here keeps the
    manifest joinable against a hand-authored cards.tsv.
    """
    base = os.path.basename(path)
    stem = base.split("_Gemini")[0]
    return unicodedata.normalize("NFC", stem)


def analyze(path: str):
    """Measure one card. Returns a dict of geometry and status."""
    gray = np.asarray(Image.open(path).convert("L"))
    height, width = gray.shape
    dark = gray < DARK_CUTOFF
    dark_rows = dark.sum(axis=1)

    bottom, frame_top = find_art_bottom(dark_rows, width, height)
    slug = slug_for(path)
    status = "detected"

    if slug in CROP_OVERRIDES:
        bottom = CROP_OVERRIDES[slug]
        status = "override"
    elif bottom is None:
        status = "FAILED"

    left = right = None
    if bottom is not None and frame_top is not None:
        left, right = find_frame_sides(dark, frame_top, bottom)

    return {
        "slug": slug,
        "source": path,
        "width": width,
        "height": height,
        "frame_top": frame_top,
        "frame_bottom": bottom,
        "frame_left": left,
        "frame_right": right,
        "status": status,
    }


def main(dry_run: bool = False) -> None:
    paths = sorted(glob.glob(INPUT_GLOB))
    if not paths:
        print(f"[FAIL] No inputs matched {INPUT_GLOB}")
        return

    # Swap in regenerated sources, keyed by slug.
    by_slug = {slug_for(p): p for p in paths}
    for slug, replacement in SOURCE_OVERRIDES.items():
        if not os.path.exists(replacement):
            print(f"[WARN] Override source missing: {replacement}")
            continue
        by_slug[unicodedata.normalize("NFC", slug)] = replacement

    if not dry_run:
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    records, failed, written, skipped = [], [], 0, 0

    for slug in sorted(by_slug):
        info = analyze(by_slug[slug])
        records.append(info)

        if info["status"] == "FAILED":
            failed.append(slug)
            print(f"  [FAIL] {slug:14s} no frame bottom found")
            continue

        bottom = info["frame_bottom"]
        keep = bottom + 1
        tag = "override" if info["status"] == "override" else ""
        print(f"  [OK]   {slug:14s} crop 0..{bottom}  "
              f"keep {keep}px of {info['height']}  {tag}")

        if dry_run:
            continue

        out_path = os.path.join(OUTPUT_DIR, f"{slug}.png")
        if SKIP_EXISTING and os.path.exists(out_path):
            skipped += 1
            continue

        img = Image.open(by_slug[slug])
        img.crop((0, 0, info["width"], keep)).save(out_path, "PNG")
        written += 1

    if not dry_run:
        with open(MANIFEST_PATH, "w", encoding="utf-8") as handle:
            cols = ["slug", "source", "width", "height", "frame_top",
                    "frame_bottom", "frame_left", "frame_right", "status"]
            handle.write("\t".join(cols) + "\n")
            for r in records:
                handle.write(
                    "\t".join("" if r[c] is None else str(r[c])
                              for c in cols) + "\n"
                )

    print(f"\n{len(records)} cards examined, {len(failed)} failed")
    if failed:
        print("Add CROP_OVERRIDES entries for: " + ", ".join(failed))
    if dry_run:
        print("Dry run: nothing written.")
    else:
        print(f"Wrote {written}, skipped {skipped} existing.")
        print(f"Manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main(dry_run=len(sys.argv) > 1 and sys.argv[1] == "dry")
