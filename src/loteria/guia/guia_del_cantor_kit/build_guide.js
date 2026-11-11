const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, BorderStyle, AlignmentType, PageBreak, ShadingType, VerticalAlign,
  ImageRun,
} = require('docx');

const cards = JSON.parse(fs.readFileSync('cards.json', 'utf-8'));

const PAGE_W = 12240, PAGE_H = 15840; // US Letter, twips
const MARGIN = 620; // ~0.43in
const USABLE_W = PAGE_W - MARGIN * 2;
const COL_W = Math.floor(USABLE_W / 2);

const CELL_BORDER = {
  top: { style: BorderStyle.SINGLE, size: 4, color: "BBBBBB" },
  bottom: { style: BorderStyle.SINGLE, size: 4, color: "BBBBBB" },
  left: { style: BorderStyle.SINGLE, size: 4, color: "BBBBBB" },
  right: { style: BorderStyle.SINGLE, size: 4, color: "BBBBBB" },
};

const NO_BORDER = {
  top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
  bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
  left: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
  right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
};

const THUMB_W_PX = 92; // display width of the card thumbnail, in pixels

// Manual overrides where the automatic split doesn't do the verse justice —
// either because it needs a 4-line treatment (long verse, AABB-style rhyme)
// or because the natural break sits at a different comma than "the last one".
// indent[i] = true means that line gets a slight left indent (the "answer"
// line in an AABB couplet, or the second half of an explicit override).
const SPANISH_OVERRIDES = {
  12: { lines: ["Dale, dale, dale —", "no pierdas el tino,", "tu teléfono es piñata —", "ese es el destino."], indent: [false, true, false, true] },
  18: { lines: ["Palomitas, oscuridad,", "y la pantalla encendida,", "el cine de antes —", "qué buena era la vida."], indent: [false, true, false, true] },
  22: { lines: ["Una copa de helado", "y todo se curaba,", "la botica del barrio", "que a todos nos sanaba."], indent: [false, true, false, true] },
  21: { lines: ["La mano de una señora,", "ni roba, ni lastima, ni llora."], indent: [false, false] },
  34: { lines: ["Más vieja que todo lo que mira,", "la montaña calla, observa, respira."], indent: [false, false] },
  37: { lines: ["Este mundo es una bola,", "juntos la cargamos — no hay carga sola."], indent: [false, false] },
};

const LINE_INDENT = 260; // DXA, applied to "answer" lines in overridden verses

// Split a Spanish verse into display lines using whatever break signal the
// text already gives us: an em dash or colon (explicit pause) takes priority;
// otherwise fall back to the last comma, which in these dicho/refrán-style
// verses usually separates the setup from the punchline.
function splitSpanish(verse) {
  const v = verse.trim();
  if (v.includes("//")) {
    return v.split("//").map((s) => s.trim()).filter(Boolean);
  }
  if (v.includes("—")) {
    const parts = v.split("—").map((s) => s.trim()).filter(Boolean);
    return parts.map((p, i) => (i < parts.length - 1 ? `${p} —` : p));
  }
  if (v.includes(":")) {
    const parts = v.split(":").map((s) => s.trim()).filter(Boolean);
    return parts.map((p, i) => (i < parts.length - 1 ? `${p}:` : p));
  }
  const lastComma = v.lastIndexOf(",");
  if (lastComma === -1) return [v];
  return [v.slice(0, lastComma + 1).trim(), v.slice(lastComma + 1).trim()];
}

function spanishLinesFor(card) {
  const override = SPANISH_OVERRIDES[card.num];
  if (override) return override;
  return { lines: splitSpanish(card.sp_verse), indent: splitSpanish(card.sp_verse).map(() => false) };
}

// English verses already mark their intended break with "//". Emphasis
// within a line can be marked with *asterisks*, which we render as italics
// against an otherwise upright line — so the emphasis actually stands out,
// rather than disappearing into an all-italic block.
function splitEnglish(verse) {
  return verse.split("//").map((s) => s.trim()).filter(Boolean);
}

function segmentEmphasis(text) {
  const regex = /\*(.+?)\*/g;
  const segments = [];
  let lastIndex = 0;
  let m;
  while ((m = regex.exec(text)) !== null) {
    if (m.index > lastIndex) segments.push({ text: text.slice(lastIndex, m.index), em: false });
    segments.push({ text: m[1], em: true });
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < text.length) segments.push({ text: text.slice(lastIndex), em: false });
  return segments.filter((s) => s.text.length > 0);
}

function englishRuns(lines, baseOpts) {
  const runs = [];
  lines.forEach((line, lineIdx) => {
    const segments = segmentEmphasis(line);
    segments.forEach((seg, segIdx) => {
      const opts = { ...baseOpts, italics: seg.em };
      if (lineIdx > 0 && segIdx === 0) {
        runs.push(new TextRun({ text: seg.text, break: 1, ...opts }));
      } else {
        runs.push(new TextRun({ text: seg.text, ...opts }));
      }
    });
  });
  return runs;
}

function linesToRuns(lines, opts) {
  return lines.map((line, idx) =>
    idx === 0
      ? new TextRun({ text: line, ...opts })
      : new TextRun({ text: line, break: 1, ...opts })
  );
}

// One Paragraph per line so each line can carry its own indent — needed for
// the AABB "answer line" treatment. spacingAfter only applies to the last line.
function verseParagraphs(lines, indentFlags, opts, spacingAfter) {
  return lines.map((line, idx) =>
    new Paragraph({
      spacing: { after: idx === lines.length - 1 ? spacingAfter : 0 },
      indent: indentFlags[idx] ? { left: LINE_INDENT } : undefined,
      children: [new TextRun({ text: line, ...opts })],
    })
  );
}

function cardCell(card) {
  if (!card) {
    return new TableCell({
      width: { size: COL_W, type: WidthType.DXA },
      borders: CELL_BORDER,
      margins: { top: 100, bottom: 100, left: 220, right: 220 },
      children: [new Paragraph({ children: [new TextRun("")] })],
    });
  }
  const num = String(card.num);
  const spanishVerse = spanishLinesFor(card);
  const enLines = splitEnglish(card.en_verse);

  const textParagraphs = [
    // Spanish name line
    new Paragraph({
      spacing: { after: 60 },
      children: [
        new TextRun({ text: `${num}  `, bold: true, size: 26, color: "8A2E12" }),
        new TextRun({ text: card.spanish.toUpperCase(), bold: true, size: 26, color: "1A1A1A" }),
      ],
    }),
    // Spanish verse (line breaks where implied, alternating indent where overridden)
    ...verseParagraphs(spanishVerse.lines, spanishVerse.indent, { size: 21, color: "1A1A1A" }, 140),
    // English name line (second beat, muted, no number repeated)
    new Paragraph({
      spacing: { after: 40 },
      children: [
        new TextRun({ text: card.english.toUpperCase(), bold: true, size: 19, color: "6B6B6B" }),
      ],
    }),
    // English verse (line breaks at "//")
    new Paragraph({
      children: englishRuns(enLines, { size: 18, color: "5A5A5A" }),
    }),
  ];

  const thumbW = THUMB_W_PX;
  const thumbH = Math.round(THUMB_W_PX * (card.img_h / card.img_w));
  const imgBuffer = fs.readFileSync(card.image);
  const thumbCol = 1500; // DXA width reserved for the thumbnail sub-column
  const textCol = COL_W - 440 - thumbCol; // remaining width for text sub-column

  const innerTable = new Table({
    width: { size: COL_W - 440, type: WidthType.DXA },
    columnWidths: [thumbCol, textCol],
    rows: [
      new TableRow({
        children: [
          new TableCell({
            width: { size: thumbCol, type: WidthType.DXA },
            borders: NO_BORDER,
            verticalAlign: VerticalAlign.TOP,
            margins: { top: 0, bottom: 0, left: 0, right: 120 },
            children: [
              new Paragraph({
                children: [
                  new ImageRun({
                    data: imgBuffer,
                    type: "jpg",
                    transformation: { width: thumbW, height: thumbH },
                  }),
                ],
              }),
            ],
          }),
          new TableCell({
            width: { size: textCol, type: WidthType.DXA },
            borders: NO_BORDER,
            verticalAlign: VerticalAlign.TOP,
            margins: { top: 0, bottom: 0, left: 0, right: 0 },
            children: textParagraphs,
          }),
        ],
      }),
    ],
  });

  return new TableCell({
    width: { size: COL_W, type: WidthType.DXA },
    borders: CELL_BORDER,
    verticalAlign: VerticalAlign.TOP,
    margins: { top: 100, bottom: 100, left: 220, right: 220 },
    children: [innerTable],
  });
}

function pageOfCards(pageCards) {
  const rows = [];
  for (let i = 0; i < pageCards.length; i += 2) {
    rows.push(new TableRow({
      children: [
        cardCell(pageCards[i]),
        cardCell(pageCards[i + 1]),
      ],
    }));
  }
  return new Table({
    width: { size: USABLE_W, type: WidthType.DXA },
    columnWidths: [COL_W, COL_W],
    rows,
  });
}

// Cover page
const coverChildren = [
  new Paragraph({
    spacing: { before: 1200, after: 200 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Guía del Cantor", bold: true, size: 64, color: "8A2E12" })],
  }),
  new Paragraph({
    spacing: { after: 500 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Caller's Guide — Lotería de South Pasadena", size: 30, color: "4A4A4A", italics: true })],
  }),
  new Paragraph({
    spacing: { after: 160 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Cómo cantar cada carta / How to call each card", bold: true, size: 24, color: "1A1A1A" })],
  }),
  new Paragraph({
    spacing: { after: 100 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({
      text: "Primero en español — número, nombre y dicho. Una breve pausa. Luego en inglés — número, nombre y dicho.",
      size: 22, color: "1A1A1A",
    })],
  }),
  new Paragraph({
    spacing: { after: 500 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({
      text: "Call it first in Spanish — number, name, and dicho. A brief pause. Then in English — number, name, and dicho.",
      size: 20, italics: true, color: "5A5A5A",
    })],
  }),
  new Paragraph({
    spacing: { after: 60 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Ejemplo / Example", bold: true, size: 20, color: "6B6B6B" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 40 },
    children: [new TextRun({ text: "14  LA MUERTE", bold: true, size: 24, color: "8A2E12" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 140 },
    children: [
      new TextRun({ text: "“La muerte siriquiflaca,", size: 22, color: "1A1A1A" }),
      new TextRun({ text: "de película pero flaca.”", break: 1, size: 22, color: "1A1A1A" }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 40 },
    children: [new TextRun({ text: "DEATH", bold: true, size: 19, color: "6B6B6B" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [
      new TextRun({ text: "“It takes us all eventually.", italics: true, size: 18, color: "5A5A5A" }),
      new TextRun({ text: "No rush.”", break: 1, italics: true, size: 18, color: "5A5A5A" }),
    ],
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

const body = [...coverChildren];
for (let i = 0; i < cards.length; i += 10) {
  const pageCards = cards.slice(i, i + 10);
  body.push(pageOfCards(pageCards));
  if (i + 10 < cards.length) {
    body.push(new Paragraph({ children: [new PageBreak()] }));
  }
}

const doc = new Document({
  sections: [{
    properties: {
      page: {
        size: { width: PAGE_W, height: PAGE_H },
        margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN },
      },
    },
    children: body,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync('guia_del_cantor.docx', buf);
  console.log('written');
});
