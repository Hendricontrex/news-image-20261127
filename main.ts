// news-image-20261127 entry program (Node 22, standard library only).
//
// The poster itself is drawn by scripts/compose.py and committed to this
// repository as entry.png; this program's only job is to place that exact
// file at the grader's output path, deterministically, with no network.
//
// Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for /output:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, existsSync, mkdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const source = join(here, 'entry.png');
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
const target = join(outDir, 'entry.png');

if (!existsSync(source)) {
  throw new Error(`entry.png is missing next to main.ts (${source})`);
}
mkdirSync(outDir, { recursive: true });
copyFileSync(source, target);

const bytes = readFileSync(target);
const pngMagic = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
if (!bytes.subarray(0, 8).equals(pngMagic)) {
  throw new Error('copied file is not a PNG');
}
// The IHDR chunk follows the 8-byte signature: 4-byte length, "IHDR",
// then width and height as big-endian uint32s.
const width = bytes.readUInt32BE(16);
const height = bytes.readUInt32BE(20);
if (width !== 1024 || height !== 1024) {
  throw new Error(`entry.png must be 1024x1024, got ${width}x${height}`);
}
if (statSync(target).size > 1048576) {
  throw new Error('entry.png exceeds the 1 MiB limit');
}
console.log(`wrote ${target} (${bytes.length} bytes)`);
