// Turns media/icons/*.svg into media/sail-icons.woff, the icon font VS Code loads for the "sail-logo"
// icon contributed in package.json (used in the status bar and the editor title button).
// Run with `npm run build:icons`. The generated .woff is committed, so normal builds don't need this.
const fs = require('fs');
const path = require('path');
const SVGIcons2SVGFontStream = require('svgicons2svgfont');
const svg2ttf = require('svg2ttf');
const ttf2woff = require('ttf2woff');

const iconsDir = path.join(__dirname, '..', 'media', 'icons');
const out = path.join(__dirname, '..', 'media', 'sail-icons.woff');

// One glyph per file, in the private-use area starting at U+E900. package.json refers to these code points.
const glyphs = [{ file: 'sail-logo.svg', name: 'sail-logo', codepoint: 0xe900 }];

const stream = new SVGIcons2SVGFontStream({
  fontName: 'sail-icons',
  fontHeight: 1000,
  normalize: true,
  descent: 0,
});

let svgFont = '';
stream.on('data', (chunk) => (svgFont += chunk));
stream.on('end', () => {
  const ttf = svg2ttf(svgFont, {});
  const woff = ttf2woff(Buffer.from(ttf.buffer));
  fs.writeFileSync(out, Buffer.from(woff.buffer));
  console.log(`wrote ${path.relative(process.cwd(), out)} (${fs.statSync(out).size} bytes)`);
});
stream.on('error', (err) => {
  console.error(err);
  process.exit(1);
});

for (const g of glyphs) {
  const glyph = fs.createReadStream(path.join(iconsDir, g.file));
  glyph.metadata = { unicode: [String.fromCodePoint(g.codepoint)], name: g.name };
  stream.write(glyph);
}
stream.end();
