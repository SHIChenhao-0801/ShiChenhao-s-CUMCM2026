import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import zlib from 'node:zlib';

const root = process.cwd();
const qa = path.join(root, 'paper_output/qa/support_completion_20260913/figures');
const original = path.join(root, 'paper_output/figures/review_20260913');
const redrawn = path.join(qa, 'redrawn_png');
const hash = (data) => crypto.createHash('sha256').update(data).digest('hex');
function readPNG(file) {
  const buffer = fs.readFileSync(file);
  const chunks = [];
  for (let p = 8; p < buffer.length;) {
    const length = buffer.readUInt32BE(p);
    const type = buffer.toString('ascii', p + 4, p + 8);
    const data = buffer.subarray(p + 8, p + 8 + length);
    chunks.push({ type, length, hash: hash(data), data });
    p += length + 12;
  }
  const ihdr = chunks.find(c => c.type === 'IHDR').data;
  const info = { width: ihdr.readUInt32BE(0), height: ihdr.readUInt32BE(4), depth: ihdr[8], colorType: ihdr[9], interlace: ihdr[12] };
  if (info.depth !== 8 || info.interlace !== 0 || ![2,6].includes(info.colorType)) throw Error('Unsupported PNG layout');
  const bpp = info.colorType === 6 ? 4 : 3;
  const stride = info.width * bpp;
  const filtered = zlib.inflateSync(Buffer.concat(chunks.filter(c => c.type === 'IDAT').map(c => c.data)));
  const pixels = Buffer.alloc(info.height * stride);
  const filters = {};
  for (let y = 0; y < info.height; y++) {
    const filter = filtered[y * (stride + 1)];
    filters[filter] = (filters[filter] || 0) + 1;
    for (let x = 0; x < stride; x++) {
      const a = x < bpp ? 0 : pixels[y * stride + x - bpp];
      const b = y === 0 ? 0 : pixels[(y - 1) * stride + x];
      const c = y === 0 || x < bpp ? 0 : pixels[(y - 1) * stride + x - bpp];
      let pred;
      if (filter === 0) pred = 0;
      else if (filter === 1) pred = a;
      else if (filter === 2) pred = b;
      else if (filter === 3) pred = Math.floor((a + b) / 2);
      else if (filter === 4) { const p = a + b - c; const pa = Math.abs(p-a), pb = Math.abs(p-b), pc = Math.abs(p-c); pred = pa <= pb && pa <= pc ? a : pb <= pc ? b : c; }
      else throw Error('Unknown PNG filter');
      pixels[y * stride + x] = (filtered[y * (stride + 1) + 1 + x] + pred) & 255;
    }
  }
  return { info, fileHash: hash(buffer), filteredHash: hash(filtered), pixelHash: hash(pixels), filters, chunks: chunks.map(({ data, ...summary }) => summary), pixels };
}
const results = fs.readdirSync(redrawn).filter(name => name.endsWith('.png')).map(name => {
  const a = readPNG(path.join(original, name)), b = readPNG(path.join(redrawn, name));
  let differingChannels = 0, maxChannelDifference = 0;
  for (let i = 0; i < a.pixels.length; i++) {
    if (a.pixels[i] !== b.pixels[i]) differingChannels++;
    maxChannelDifference = Math.max(maxChannelDifference, Math.abs(a.pixels[i] - b.pixels[i]));
  }
  const { pixels: ap, ...ai } = a, { pixels: bp, ...bi } = b;
  return { name, identicalPixels: a.pixels.equals(b.pixels), differingChannels, maxChannelDifference, original: ai, redrawn: bi };
});
fs.writeFileSync(path.join(qa, 'png_pixel_comparison.json'), JSON.stringify(results, null, 2));
console.log(results.map(({ name, identicalPixels, differingChannels, maxChannelDifference, original, redrawn }) => ({ name, identicalPixels, differingChannels, maxChannelDifference, original: original.info, originalChunks: original.chunks.map(c => [c.type,c.length]), redrawnChunks: redrawn.chunks.map(c => [c.type,c.length]), originalPixelHash: original.pixelHash, redrawnPixelHash: redrawn.pixelHash })));
if (results.length !== 6) process.exitCode = 1;
