import fs from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
const require_path = () => path.resolve(process.env.RIGBY || '../.rigby2d', 'package.json');
const require = createRequire(require_path());
const { writePsdBuffer, initializeCanvas } = require('ag-psd');
import { PNG } from 'pngjs';
const dir = process.argv[2], out = process.argv[3];
const order = JSON.parse(fs.readFileSync(dir + '/' + (process.argv[4]||'order.json')));
let W, H; const children = [];
for (const n of order) {
  const p = PNG.sync.read(fs.readFileSync(`${dir}/${n}.png`)); W = p.width; H = p.height;
  children.push({ name: n, left: 0, top: 0, imageData: { width: p.width, height: p.height, data: new Uint8ClampedArray(p.data) } });
}
fs.writeFileSync(out, writePsdBuffer({ width: W, height: H, children }, { noBackground: true }));
console.log('wrote', out, children.length);
