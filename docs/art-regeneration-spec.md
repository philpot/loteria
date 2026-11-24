# Art regeneration spec

Notes for the next art generation pass. Everything here comes from measuring the 56 Gemini exports in `ddd/export/` and from the constraints of printing at playing-card size. The headline is that the current exports carry defects that no post-processing can fully remove, and all of them are avoidable by changing what we ask for.

## The single most important change

Generate ARTWORK ONLY. No frame, no keyline, no label text, no number badge, no paper margins, no drop shadow.

Everything except the artwork is composited programmatically, which makes it identical on all 56 cards by construction. The current exports bake the frame and label into the image, and because each card was generated independently, none of that furniture matches card to card. Measured spread across the 56 exports: frame widths 1378 to 1612 px, frame heights 1529 to 2409 px, left edges wandering 42 to 162, top edges 34 to 312. That variation is unfixable downstream without rescaling each card by a different factor, which would then vary line weight across the deck.

## Target geometry

Final trim size is a conventional playing card, 2.5 x 3.5 inches, aspect ratio 0.7143.

```
300 dpi    750 x 1050     minimum for print
600 dpi   1500 x 2100     master resolution, use this
600 dpi   1650 x 2250     with 1/8 in bleed on all sides
```

Generate at 1650 x 2250 or larger, at aspect 0.7333 including bleed, or at 1500 x 2100 (aspect 0.7143) if bleed is added later.

The current exports are 1696 x 2528, aspect 0.671. That is narrower than a playing card, so fitting them to the trim size requires cropping about 6 percent off the height or padding about 6 percent of width. Specifying the aspect up front removes that decision.

Keep important subject matter inside a 1/8 in safe margin, and expect the outer 1/8 in to be trimmed away.

## Detail budget -- the constraint most likely to be violated

At 600 dpi one pixel is 0.0017 in. Commercial printing resolves roughly 0.005 in reliably, which is 3 px at 600 dpi.

Any feature thinner than 3 px at master resolution will not print as a feature. It averages into flat gray. This applies to line weights, hatch spacing, stipple grains, and the gaps between parallel lines.

The current art violates this repeatedly. Dense cross-hatching in foliage, bicycle spokes, and decorative scrollwork sits near or below the floor. At 2.5 inches those areas turn to mud, and they do so well before the typography does.

Direction for the next pass: bold, open line work with generous spacing. Minimum stroke weight 4 px at 1500 px wide. No fine stipple, no hairlines, no hatching finer than about 8 px pitch. Think woodblock poster, not etching.

## Downsampling

The art will be reduced from generation resolution to print resolution. Design for the final size and judge it at 100 percent of 2.5 x 3.5 in, never zoomed in.

Detail that only reads when zoomed is detail that costs file size and prints as noise.

## Deck constants

```
paper cream   #F7EEDF
ink           #1E1B18
```

Art palette should be chosen to sit on the cream paper, since the composited card shows cream in the margins and label band.

## No text of any kind in the artwork

The current exports contain generated label text, and several also picked up stray glyph and sparkle artifacts in the bottom right corner -- visible on `bicicleta` and `mano`. All text is composited from the font, never generated.

## Specific failures to avoid, observed in the current 56

- `diablito` -- colored background extended too far down, past where the frame should end.
- `desfile`, `coyote`, `metro`, `vecino`, `maceta` -- drew a second frame around the label band.
- `maceta` -- added cross-hatching around the label in addition to the second frame.
- `naranja`, `vecino` -- extended the main image frame below the label rather than above it.
- `estrella` -- square art box, aspect 1.007 against a deck median of 1.414. This one was deliberate, to avoid warping a radially symmetric subject. If a square composition is wanted again, decide the canvas policy explicitly rather than letting the generator choose.
- Seven cards produced nested frames that made automated cropping fail and required hand-picked crop lines.

## File naming

One file per card, named `<slug>.png`, where slug is the bare noun without the article: `bandera`, `mano`, `correcaminos`.

Normalize accented names to NFC. macOS stores filenames decomposed, so a hand-authored `cards.tsv` will not join against raw decomposed filenames without normalization on both sides. Ten cards are affected: `árbol`, `béisbol`, `cempasúchil`, `fútbol`, `güey`, `lonchería`, `misión`, `montaña`, `músico`, `piñata`.

## Why deck coherence needs a parametric compositor

Asking a generative model for 56 cards produces 56 independent interpretations of the same instruction. Measured on the current labels alone, the deck varies in stroke weight, distress mechanism (granular speckle vs outline dots vs soft blur), letterform, cap height, scale relative to card width, and casing -- `mano` came back as "La mano" with a lowercase m.

A model has no parameters to hold constant across invocations. A compositing script does. So the division of labor is: the model supplies artwork, the script supplies everything that must match.
