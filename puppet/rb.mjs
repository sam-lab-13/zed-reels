// Direct driver for the Rigby2D MCP tools, no editor: node rb.mjs <tool> '<json args>' | node rb.mjs list
import path from 'node:path';
const R = path.resolve(process.env.RIGBY || '../.rigby2d');
const m = async (f) => import(path.join(R, 'src/mcp', f));
const { Workspace, createTools } = await m('tools.js');
const fns = [createTools, (await m('edits.js')).createEditTools, (await m('film.js')).createFilmTools,
  (await m('rigging.js')).createRiggingTools, (await m('scripting.js')).createScriptTools, (await m('scene.js')).createSceneTools];
const ws = new Workspace([process.cwd()]);
const all = fns.flatMap((f) => { try { return f(ws); } catch (e) { console.error(e.message); return []; } });
const [tool, a = '{}'] = process.argv.slice(2);
if (tool === 'list') { for (const t of all) console.log(t.name, '-', (t.description || '').slice(0, 160)); process.exit(0); }
const t = all.find((t) => t.name === tool); if (!t) throw new Error('no tool ' + tool);
const r = await t.handler(JSON.parse(a));
console.log(typeof r === 'string' ? r : JSON.stringify(r, null, 1).slice(0, 6000));
