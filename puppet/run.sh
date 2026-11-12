#!/usr/bin/env bash
# Zed Reels puppet pipeline: AI parts sheet -> layered PSD -> Rigby2D AutoRig -> keys -> headless frames -> reel.
# Usage: cd puppet && RIGBY=../.rigby2d bash run.sh   (CI: .github/workflows/puppet.yml)
set -euo pipefail
cd "$(dirname "$0")"; mkdir -p ../out
rb(){ node rb.mjs "$@"; }
echo "== front rig"
python3 extract.py art/parts_v1.png parts1 >/dev/null
python3 heads.py
python3 assemble.py >/dev/null
python3 heads_layers.py
node mkpsd.mjs layers mgr2.psd order2.json
rb autorig '{"psd_file":"mgr2.psd","output":"mgr2.rigby","overwrite":true}' >/dev/null
python3 patch_ik.py mgr2.rigby ik_hand_l=1 ik_hand_r=0
for s in head_talk head_shock head_blink; do rb set_slot "{\"path\":\"mgr2.rigby\",\"slot\":\"$s\",\"hide\":true}" >/dev/null; done
python3 anim.py; node rbf.mjs batch_edit ops.json >/dev/null
rm -rf fr && mkdir fr && rb export_sprite_sheet '{"input":"mgr2.rigby","output_folder":"fr","format":"frames","animations":["test"],"fps":24,"scale":0.75,"loop":false}' >/dev/null
echo "== side rig"
python3 extract.py art/side_parts_v1.png side1 >/dev/null
python3 assemble_side.py >/dev/null
node mkpsd.mjs layers_side side.psd order.json
rb autorig '{"psd_file":"side.psd","output":"side_w.rigby","overwrite":true}' >/dev/null
python3 patch_ik.py side_w.rigby ik_foot_l=0 ik_foot_r=0 ik_hand_l=1 ik_hand_r=1
python3 patch_foot.py side_w.rigby
python3 anim_side.py; node rbf.mjs batch_edit ops_side.json >/dev/null
rm -rf frs && mkdir frs && rb export_sprite_sheet '{"input":"side_w.rigby","output_folder":"frs","format":"frames","animations":["walk"],"fps":24,"scale":0.75,"loop":false}' >/dev/null
echo "== composite"
python3 comp2.py
ffmpeg -v error -i ../out/puppet_test.mp4 -f null - && echo "decode OK: out/puppet_test.mp4"
