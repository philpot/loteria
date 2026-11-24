Guía del Cantor / Caller's Guide -- build kit
==============================================

Contents:
  build_guide.js   The generator script (Node.js + the "docx" npm package)
  cards.json       All 56 cards: number, Spanish/English names, versos, image path
  thumbs/          The 56 resized card thumbnail images (used by build_guide.js)

Requirements:
  Node.js installed (https://nodejs.org)

Setup (one time):
  npm install docx

Run:
  node build_guide.js

This writes guia_del_cantor.docx in the same folder. Open it in Word or
LibreOffice, or convert to PDF from there for a print-safe layout (the
docx can reflow oddly in some non-Word viewers -- PDF prints reliably
everywhere).

Notes on editing:
  - Card text/order lives in cards.json -- edit it directly, or regenerate
    it from a fresh export of the source spreadsheet (columns used:
    net numbering, spanish, slug/bare-noun, english, spanish verse,
    english verse).
  - Spanish verses split into display lines using, in priority order:
    an explicit "//" marker, then an em dash "--", then a colon, then
    the last comma in the sentence.
  - English verses split only on an explicit "//" marker. Wrap a word or
    phrase in *asterisks* to italicize just that span (e.g. "Not for
    sailors, // *this* star lights the way home.").
  - SPANISH_OVERRIDES near the top of build_guide.js holds hand-tuned
    line breaks (with optional alternating indent for AABB-rhyme verses)
    for specific card numbers -- edit that object directly for one-off
    fixes rather than fighting the automatic split logic.
  - THUMB_W_PX controls the thumbnail display width; the images in
    thumbs/ are pre-resized to keep file size down, so replacing an
    image there with a much larger file will bloat the .docx again.
