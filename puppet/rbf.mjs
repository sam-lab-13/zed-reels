// Same as rb.mjs but reads the JSON args from a file: node rbf.mjs <tool> args.json
import fs from 'node:fs';
process.argv = [process.argv[0], process.argv[1], process.argv[2], fs.readFileSync(process.argv[3], 'utf8')];
await import('./rb.mjs');
