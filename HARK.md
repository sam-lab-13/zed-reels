# HARK.md: Zed Reels process

Football satire reels (9:16, 1080x1920, 24 fps) made by Hark and Zed. Everything runs headless on GitHub Actions (free). No paid tools, no editor clicks.

## The two pipelines in this repo
| Folder | What | Trigger | Output (Actions artifact) |
|---|---|---|---|
| `render.py` + `gags/*.json` | Still-frame reels: AI panels plus camera moves, shake, captions and CC0 SFX | push to `gags/**.json`, or run **render-reel** | `reels` |
| `puppet/` | Skeletal puppet animation: real walks, waves, talking, reactions | push to `puppet/**`, or run **puppet-test** | `puppet` |

To run from your phone: GitHub app, then repo, then **Actions**, then pick the workflow, then **Run workflow**. Download the mp4 from the run's **Artifacts**.

## Why puppets (decision 2026-11-13)
We compared two AI blueprints (both in `docs/`):
- `blueprint_chatgpt_hybrid_rig.pdf`: a skeletal rig with layered parts and a reusable action library; AI video only for special shots. **Chosen.**
- `blueprint_gemini_python_cutout.pdf`: Pillow affine transforms of cut parts. Rejected: rigid limbs, the same stiffness as our first rig test.

The tool is **Rigby2D** (open source, MIT or Apache-2.0, public beta, pinned commit in `puppet.yml`). Its AutoRig turns a layered PSD into bones, weighted meshes (a whole arm bends at the elbow) and IK. We drive its MCP tools directly from Node (`puppet/rb.mjs`), so no editor is needed.

## Walks toward camera: drawn, not rigged (decision 2026-11-13)
The puppet walk looked robotic: a stiff cut-out with a floating head. Walks now use **drawings**, the classic cartoon way (`walk/`):
1. Make an AI edit of the shot's character (e.g. `s1_A.png`) in a walking-toward-viewer pose on #00FF00 (`art/wk1.png`). `key.py` removes the green, giving `art/k1.png`.
2. `mirror_legs.py` mirrors only the legs to get the other-foot drawing (`k1m.png`). The face and props stay identical, so nothing flickers.
3. `walk_toward.py` alternates the 2 drawings each step (0.42 s), scales him up with perspective (z 2.5 to 1.0, ground line to the horizon), adds bob (high at passing), small sway and a contact shadow. It plays real CC0 footsteps on each contact, getting louder as he nears, then cuts to the standing shot.
Run: `cd walk && python3 walk_toward.py` (needs numpy, pillow, ffmpeg).

### v2 flipbook (2026-11-14), used by render.py
Two drawings snap and float, so a walk is now a **flipbook of 8 pages** (`walk/pages/`, built by `walk/flip_pages.py`):
- Reused: `k1` (contact, left foot forward) and its leg mirror (contact, right foot forward).
- New drawing: one passing pose (`art/pass_raw.png`, an AI edit of the same frame changing the legs only) and its leg mirror.
- Squash and stretch: a `down` page (0.975 tall) after each contact, an `up` page (1.02) after each passing.
- Order, 10 frames per step at 24 fps: A x3, A-down x2, Pass x3, Pass-up x2, then B, B-down, Pass-mirror, Pass-mirror-up.
- **Feet lock:** every page sits on one canvas whose bottom row is the planted foot, placed exactly on the ground line, so he never floats.
- Gag JSON: `"walk": {"flip": true, "until": 4.0, "z": [2.5, 1.0], "horizon": 0.56, "feet": 0.955, "height": 0.68}`. render.py adds one real footstep per contact, louder as he nears.
- Audio: any SFX name with a real CC0 wav in `assets/sfx/` now beats the synth version (whoosh, drumroll, ping, ding, thud). `"ambience": "birds"` adds a faded bed to a scene. `groove.level` turns the synth beat down.
- To add a new walk: reuse existing drawings, generate only the missing in-between, run flip_pages.py.

## Puppet pipeline (`puppet/run.sh`): small gestures only, not walks
1. **Art**: an AI "parts sheet" of the character on pure green #00FF00, with head, torso, pelvis, two whole arms and two whole legs drawn separately and with rounded joint ends. There is one sheet per view: `art/parts_v1.png` (front) and `art/side_parts_v1.png` (side, facing right). Head variants (talk, shock, blink) are AI edits of the base head (`art/heads/`).
2. `extract.py`: green key, then one PNG per part. `heads.py`: talk and blink are patched onto the base head so the face does not jump.
3. `assemble.py` / `assemble_side.py`: place the parts on a 1000x1600 canvas. Limbs go behind the torso so joints hide; far limbs on the side view are darkened. `mkpsd.mjs` writes the layered PSD. **Layer names matter**: `head`, `torso`, `pelvis`, `arm_l/arm_r`, `leg_l/leg_r`, where l and r are the *character's* sides.
4. `rb.mjs autorig`: builds the rig. `patch_ik.py` sets elbow and knee bend directions (side view: knees forward with `ik_foot_*=0`, elbows back with `ik_hand_*=1`; front wave: `ik_hand_l=1`).
5. `anim.py` (front: wave, talk flaps, blinks, shock) and `anim_side.py` (walk cycle) write keys as one `batch_edit`. Front keys are on twos (12 fps, stepped). The walk uses smooth 24 fps keys with overlap: the arms and chest lag the legs slightly, so it doesn't look robotic.
   - Side view uses separate **foot** layers (shoe cut at the ankle). `patch_foot.py` makes the foot bones keep their world angle, so feet stay flat on the ground, then get heel strike, heel-off roll and toe-up keys. Only the sheet's right-pointing leg is used for both legs (the AI drew one shoe backwards).
   - The walk is a classic cycle: 1.0 s per cycle, 60% stance. The planted foot moves back exactly as fast as the body moves forward, so **no foot slide**. It has a hip bob (low at contact, high at passing), a forward lean, a head counter-bob and arms swinging opposite the legs.
   - Root motion lives in the compositor, which moves the sprite at the same speed.
6. `rb.mjs export_sprite_sheet format=frames`: headless CPU render of the frames (about 20 to 60 s per shot).
7. `comp2.py`: background, contact shadow, speech bubbles, impact shake, footsteps on each foot contact, a CC0 reaction SFX, then ffmpeg encode with a zero decode error check.

## Rules
- **Our own characters and style only.** Never copy another artist's characters or style.
- No club crests, sponsor logos or real chants baked in. Add music in Instagram's audio picker.
- Satire must read as satire. Don't present invented news as fact or show real people committing invented crimes.
- Free tools only, so no card is ever needed. Commit only files we made or that are CC0 (see `assets/sfx/CREDITS.md`).

## Known limits / next
- No hand bones yet. The torso is one rigid piece; a chest/belly split would add squash. Next: hand poses (fist, point, phone, stamp) as alternate images, and a draw-order key so hands can come in front of the face.
- There is no 3/4 view and no turn between views; we cut between front and side shots.
- Next steps: build an action library (walk, stop, wave, talk, shock, phone check, facepalm, stamp), then let gag JSON call actions per shot.

## Motion plan: every action drawn as a flipbook (decided 2026-11-14)
The walk proved it: drawn pages beat camera moves on stills and the puppet. Every action becomes a short flipbook, not just walks.

**Why still reels so far:** each action needs 4 to 8 drawings, and AI redraws drift between pages (face, kit, background), which flickers. It also costs about 2 to 3 times a still reel.

**Method (per action)**
1. **Plate:** draw the background once, with no characters. It never changes, so there's no background flicker.
2. **Key poses:** AI edits of one master character frame on #00FF00, keyed out: anticipation, extreme or contact, follow-through, settle (4 keys).
3. **In-betweens:** 1 or 2 pages only where the move is big. Small moves use a transform tween plus smear and motion lines.
4. **Timing:** on twos (12 fps), holds on keys, squash and stretch pages, impact frame (2-frame white flash and smear), SFX on contact.
5. **Consistency gate:** compare a face crop with the master and reject pages that drift (same idea as the walk's feet lock).
6. Talk and blink stay on puppet head swaps.

**Action library (reusable across reels)**
| Action | Pages |
|---|---|
| kick / penalty | run-up x2, plant, strike, follow-through, settle |
| tussle over ball (2 people) | pull left, pull right, wobble loop, break |
| stick label on back | reach, slap (impact), hold, step back |
| knee slide celebration | run, drop, slide x2 + spray, roar hold |
| facepalm, catch ball, phone check, stamp | 3-4 each |

**render.py (to build):** a scene key `"acts": [{"pages": "acts/kick", "at": 0.5, "fps": 12, "x": .., "y": .., "h": .., "loop": false}]` composites the keyed pages over the plate, with the walk's ground lock.

**First test:** Esposito v2 with kick, tussle and label as the first three library actions.
