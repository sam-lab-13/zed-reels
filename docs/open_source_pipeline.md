# Plan: self-hosted open-source drawing pipeline (2026-11-14)
Goal: make every drawing (plates, key poses, in-betweens) on free self-hosted open models, so reels don't spend Hark or Gemini quota. The Hark chat is only for finalizing ideas and scripts; GitHub holds the plan, scripts, code and outputs.

## Where to run (free, no card: hard rule)
| Option | Verdict |
|---|---|
| **Kaggle GPU kernels** (T4 x2 / P100, ~30 GPU h/week) | **Primary.** Account samz678 exists, REST push works. Blocker: phone verification for GPU + internet (still pending). |
| GitHub Actions (CPU) | Compositing, render.py, FFmpeg, QC. Free for this repo. |
| Google Colab free | Manual backup only (interactive, not headless). |
| Modal | Free monthly credit, but card terms unverified. Check before use; skip if a card is asked for. |
| Oracle Always Free | No GPU, and signup needs a card. **Rejected.** |

## Model stack (all open weights, licence to verify before public posting)
| Job | Tool |
|---|---|
| Image model | SDXL (OpenRAIL++) or FLUX.1-schnell (Apache-2.0), run headless in ComfyUI or diffusers |
| Our cartoon style | Train a small style LoRA on our approved frames (Carrick v3, Esposito) on Kaggle |
| Same character every page | IP-Adapter (face/body reference) + one LoRA per recurring character |
| Key poses | ControlNet OpenPose: we draw the stick-figure pose in code (JSON keypoints), the model draws the character in it |
| In-betweens | ToonCrafter (cartoon interpolation between two keys) or RIFE; fall back to tween + smear |
| Cutout | rembg / BiRefNet (MIT), or generate on a #00FF00 background and chroma key |
| Plates | Same model, no characters, drawn once per location |
| Consistency gate | Face-crop similarity vs the master sheet; reject drift (CPU) |

## Flow (one reel)
1. Chat: finalize the script (example: scripts/2026-11-14_esposito_v2.md).
2. `actions/*.json`: poses as keypoints per page (kick, tussle, label slap ...), reusable library.
3. Kaggle GPU kernel `zr-draw`: reads script + poses from the repo, renders plates, keys and in-betweens, gates them, pushes PNGs as a release asset.
4. GitHub Actions: render.py composites pages over plates (acts key), adds the HUD, rain, SFX and captions, outputs MP4 to a release.
5. Chat: review the result, then OK / CHANGE.

## Steps, in order (cheap first)
- [ ] User: Kaggle phone verification (unlocks GPU + internet)
- [ ] `kaggle/zr_draw.py` smoke: SDXL + OpenPose draws one Mancini pose on T4
- [ ] Style LoRA from approved frames, then a character sheet per person
- [ ] Pose library for the 8 Esposito v2 actions
- [ ] ToonCrafter in-between test on the kick
- [ ] render.py `acts` key + Actions workflow
- [ ] Build Esposito v2 fully on this stack

Budget: Hark pool 95% used (2026-11-14), resets 2026-11-30 14:31 IST. Until then Hark does only small doc and code edits; the heavy work moves to Kaggle once it's verified.
