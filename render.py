#!/usr/bin/env python3
"""Zed Reels renderer: python render.py gags/<name>.json  ->  out/<name>.mp4

gag.json schema (times in seconds, scene-local unless noted):
{
  "name": "carrick_rollercoaster",
  "frames_dir": "assets/frames",            # holds <img>_A.png / <img>_B.png pose pairs
  "watermark": "ZED",
  "scenes": [
    {"img": "p1", "dur": 4.5, "caption": "line1\\nline2",
     "motion": "zoomin|slow|climb|drop|punch|still",
     "poses": [[0,"A"],[2.2,"B"],[4.0,"A"]],  # from time t use pose; "flip:0.2" alternates A/B every 0.2s
     "hits": [0.6],                           # squash-bounce moments
     "rain": false,                           # speed lines/rain overlay for first 2.5s
     "sfx": [{"name":"scream","at":0.2,"gain":0.8}]}   # name = assets/sfx/<name>.wav OR a synth: whoosh, ding, boing, roar, pops, trombone, clicks, screech, drumroll, sting
  ],
  "end_card": {"title":"ZED", "sub":"Man Utd 4-4 Aston Villa", "dur":2.5, "color":[200,20,30]},
  "groove": {"start":4.5, "end":25.0, "bpm":120, "duck":[[4.5,6.5],[14,16]]},   # optional beat, absolute times
  "calliope": {"start":0.1, "end":4.4}                                          # optional carnival intro, absolute
}
Songs/chants under copyright are NOT baked in: add them in Instagram's audio picker.
"""
import json, math, os, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SR = 1080, 1920, 30, 44100
ROOT = os.path.dirname(os.path.abspath(__file__))
FONT_CANDIDATES = ["/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
FONT = next(f for f in FONT_CANDIDATES if os.path.exists(f))


def ease(x): return 0.5 - 0.5 * math.cos(math.pi * max(0, min(1, x)))


def pose_at(poses, tl):
    cur = "A"
    for start, mode in poses or [[0, "A"]]:
        if tl >= start: cur = mode
    if cur.startswith("flip:"):
        r = float(cur.split(":")[1]); return "B" if int(tl / r) % 2 else "A"
    return cur


def load(path):
    im = Image.open(path).convert("RGB")
    s = max(W / im.width, H / im.height)
    return im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)


def view(img, u, motion, tl):
    zoom, ox, oy, rot = 1.0, 0.0, 0.0, 0.0
    if motion == "zoomin": zoom = 1.0 + 0.10 * ease(u)
    elif motion == "slow": zoom = 1.08 - 0.06 * ease(u)
    elif motion == "climb": zoom = 1.12; oy = 80 - 160 * ease(u)
    elif motion == "drop":
        zoom = 1.06 + 0.12 * ease(u * 2); amp = 22 * max(0, 1 - tl / 2.2)
        ox = amp * math.sin(tl * 55); oy = amp * math.cos(tl * 47)
        rot = 1.5 * math.sin(tl * 30) * max(0, 1 - tl / 2.2)
    elif motion == "punch":
        zoom = 1.25 - 0.17 * ease(tl / 0.6) + 0.04 * ease(u)
    cw, ch = W / zoom, H / zoom
    cx, cy = img.width / 2 + ox, img.height / 2 + oy
    v = img.transform((W, H), Image.EXTENT, (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2), Image.BILINEAR)
    if rot: v = v.rotate(rot, resample=Image.BILINEAR, fillcolor=(230, 110, 40))
    return v


def shake(v, tl, hits, amp0=18):
    for h in hits:
        if 0 <= tl - h < 0.25:
            k = tl - h; sq = 1 + 0.05 * math.sin(k / 0.25 * math.pi)
            v2 = v.resize((W, int(H * sq)), Image.BILINEAR); o = (v2.height - H) // 2
            v = v2.crop((0, o, W, o + H))
    return v


def render(gag_path):
    g = json.load(open(gag_path))
    name = g.get("name") or os.path.splitext(os.path.basename(gag_path))[0]
    fdir = os.path.join(ROOT, g.get("frames_dir", "assets/frames"))
    font = ImageFont.truetype(FONT, 58); font_mid = ImageFont.truetype(FONT, 56)
    scenes, t0 = [], 0.0
    for s in g["scenes"]:
        s = dict(s); s["a"] = t0; s["b"] = t0 + s["dur"]; t0 = s["b"]; scenes.append(s)
    ec = g.get("end_card"); end_a = t0; total = t0 + (ec["dur"] if ec else 0)
    imgs = {}
    for s in scenes:
        for k in "AB":
            p = os.path.join(fdir, f"{s['img']}_{k}.png")
            if not os.path.exists(p): p = os.path.join(fdir, f"{s['img']}_A.png")
            imgs[s["img"] + k] = imgs.get(s["img"] + k) or load(p)

    def caption(v, text, appear):
        if appear <= 0 or not text: return v
        d = ImageDraw.Draw(v); lines = text.split("\n")
        bw = max(d.textbbox((0, 0), l, font=font)[2] for l in lines) + 60; bh = 70 * len(lines) + 34
        x0, y0 = 40, 110 - int(30 * max(0, 1 - appear))
        d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=26, fill=(255, 255, 255), outline=(20, 20, 20), width=5)
        for i, l in enumerate(lines): d.text((x0 + 30, y0 + 17 + i * 70), l, font=font, fill=(15, 15, 15))
        return v

    def end_card(t):
        v = Image.new("RGB", (W, H), tuple(ec.get("color", [200, 20, 30]))); d = ImageDraw.Draw(v)
        dark = tuple(max(0, c - 20) for c in ec.get("color", [200, 20, 30]))
        for i in range(0, H, 40): d.line((0, i, W, i - 300), fill=dark, width=14)
        f = ImageFont.truetype(FONT, int(220 * (0.6 + 0.4 * ease(t / 0.4))))
        title = ec.get("title", g.get("watermark", "ZED")); tb = d.textbbox((0, 0), title, font=f)
        d.text(((W - tb[2]) // 2, 760), title, font=f, fill=(255, 255, 255), stroke_width=8, stroke_fill=(0, 0, 0))
        sub = ec.get("sub", "")
        if sub:
            tb = d.textbbox((0, 0), sub, font=font_mid)
            d.text(((W - tb[2]) // 2, 1060), sub, font=font_mid, fill=(255, 230, 120))
        return v

    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    tmpv = os.path.join(ROOT, "out", f".{name}_v.mp4"); tmpa = os.path.join(ROOT, "out", f".{name}_a.wav")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                          "-pix_fmt", "yuv420p", tmpv], stdin=subprocess.PIPE)
    wm = g.get("watermark", "ZED")
    for n in range(int(total * FPS)):
        t = n / FPS
        if t >= end_a:
            v = end_card(t - end_a)
        else:
            i = next(i for i, s in enumerate(scenes) if s["a"] <= t < s["b"]); s = scenes[i]
            tl = t - s["a"]; u = tl / s["dur"]; mot = s.get("motion", "still")
            v = view(imgs[s["img"] + pose_at(s.get("poses"), tl)], u, mot, tl)
            v = shake(v, tl, s.get("hits", []))
            if s.get("rain", mot == "drop") and tl < 2.5:
                d0 = ImageDraw.Draw(v); r = random.Random(int(t * FPS))
                for _ in range(10):
                    x, y, ln = r.randint(0, W), r.randint(300, H), r.randint(120, 300)
                    d0.line((x, y, x - ln * 0.35, y - ln), fill=(255, 255, 255), width=4)
            v = caption(v, s.get("caption", ""), (tl - 0.25) / 0.2)
            if wm: ImageDraw.Draw(v).text((40, 1820), wm, font=font_mid, fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))
            if tl < 0.12 and i > 0: v = Image.blend(v, Image.new("RGB", (W, H), (255, 255, 255)), 0.85 * (1 - tl / 0.12))
            if mot == "punch" and tl < 0.1: v = Image.blend(v, Image.new("RGB", (W, H), (255, 240, 200)), 0.9)
            if ec and t > end_a - 0.3: v = Image.blend(v, Image.new("RGB", (W, H), (0, 0, 0)), (t - (end_a - 0.3)) / 0.3)
        p.stdin.write(v.tobytes())
    p.stdin.close(); p.wait()

    # ---------------- audio ----------------
    L = int(total * SR) + SR; A = np.zeros(L); rng = np.random.default_rng(3)
    def add(sig, at, gn=1.0):
        i = int(at * SR); j = min(L, i + len(sig))
        if i < L: A[i:j] += gn * sig[:j - i]
    def tt(d): return np.arange(int(d * SR)) / SR
    def env(n, a=0.01, r=0.1):
        e = np.ones(n); ai = max(1, min(n, int(a * SR))); ri = max(1, min(n, int(r * SR)))
        e[:ai] = np.linspace(0, 1, ai); e[-ri:] *= np.linspace(1, 0, ri); return e
    def tone(f, d, kind="sq"):
        x = tt(d); ph = 2 * np.pi * np.cumsum(np.full(len(x), f) if np.isscalar(f) else f) / SR
        s = np.sign(np.sin(ph)) * 0.5 + 0.5 * np.sin(ph) if kind == "sq" else np.sin(ph)
        return s * env(len(x))
    def lp(x, k): return np.convolve(x, np.ones(k) / k, mode="same")
    def noise(d): return rng.standard_normal(int(d * SR))
    def sweep(a, b, d): return np.linspace(a, b, int(d * SR))
    def kick(): x = tt(0.25); return np.sin(2 * np.pi * np.cumsum(np.linspace(140, 45, len(x))) / SR) * np.exp(-x * 14)
    def snare(): return lp(noise(0.18), 2) * np.exp(-tt(0.18) * 22)
    def hat(): n_ = noise(0.05); return (n_ - lp(n_, 4)) * np.exp(-tt(0.05) * 60)

    SYN = {
        "whoosh": lambda: lp(noise(1.2), 6) * np.sin(np.linspace(0, np.pi, int(1.2 * SR))) * 0.35,
        "ding": lambda: np.concatenate([tone(1568, 0.8, "sine") * np.exp(-tt(0.8) * 5) * 0.4]),
        "boing": lambda: tone(sweep(150, 600, 0.5) * (1 + 0.15 * np.sin(2 * np.pi * 14 * tt(0.5))), 0.5, "sine") * 0.45,
        "roar": lambda: lp(noise(3.6), 12) * env(int(3.6 * SR), 0.3, 1.2) * 0.55,
        "screech": lambda: tone(sweep(2400, 1900, 1.0), 1.0, "sine") * 0.12,
        "sting": None, "trombone": None, "pops": None, "clicks": None, "drumroll": None, "calliope": None,
    }
    def synth(nm, at, gn):
        if nm == "sting":
            for k, f in enumerate([392, 523, 659, 784]): add(tone(f, 0.18 if k < 3 else 0.6), at + k * 0.14, 0.14 * gn)
        elif nm == "trombone":
            for k, f in enumerate([294, 277, 262]): add(tone(f, 0.45), at + k * 0.45, 0.16 * gn)
            add(tone(sweep(247, 220, 1.0) * (1 + 0.02 * np.sin(2 * np.pi * 6 * tt(1.0))), 1.0), at + 1.35, 0.16 * gn)
        elif nm == "pops":
            for k in range(8): add(lp(noise(0.08), 2) * np.exp(-tt(0.08) * 40), at + k * 0.33 + random.random() * 0.1, 0.6 * gn)
        elif nm == "clicks":
            for k in range(14): add(lp(noise(0.03), 3) * env(int(0.03 * SR), 0.001, 0.02), at + k * 0.22, 0.5 * gn)
        elif nm == "drumroll":
            for k in range(12): add(snare(), at + k * 0.05, (0.25 + k * 0.02) * gn)
        else:
            add(SYN[nm](), at, gn)

    def load_wav(nm):
        path = os.path.join(ROOT, "assets", "sfx", nm + ".wav")
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                             capture_output=True, check=True).stdout
        return np.frombuffer(raw, np.int16).astype(float) / 32768

    cache = {}
    for s in scenes:
        for e in s.get("sfx", []):
            nm, at, gn = e["name"], s["a"] + e.get("at", 0), e.get("gain", 0.7)
            if nm in SYN: synth(nm, at, gn)
            else:
                if nm not in cache: cache[nm] = load_wav(nm)
                add(cache[nm], at, gn)
    if ec: synth("sting", end_a + 0.1, 1.0)
    cal = g.get("calliope")
    if cal:
        notes = [523, 659, 784, 659, 698, 880, 784, 0, 523, 659, 784, 1047, 988, 784, 659, 0]; k = 0; tb = cal["start"]
        while tb < cal["end"] - 0.2:
            f = notes[k % 16]
            if f: add(tone(f, 0.24), tb, 0.10)
            if k % 4 == 0: add(tone(131, 0.25, "sine"), tb, 0.25)
            tb += 0.27; k += 1
    gr = g.get("groove")
    if gr:
        beat = 60 / gr.get("bpm", 120); tb = gr["start"]; i = 0; bass = [55, 55, 65.4, 49]
        while tb < gr["end"] - 0.1:
            gain = 0.15 if any(a <= tb < b for a, b in gr.get("duck", [])) else 0.35
            add(kick(), tb, 0.9 * gain); add(hat(), tb + beat / 2, 0.25 * gain)
            if i % 2: add(snare(), tb, 0.6 * gain)
            add(tone(bass[(i // 4) % 4] * 2, beat * 0.9), tb, 0.35 * gain)
            tb += beat; i += 1
    A = A[:int(total * SR)]; A = A / (np.max(np.abs(A)) + 1e-9) * 0.9
    with wave.open(tmpa, "w") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes((A * 32767).astype(np.int16).tobytes())
    out = os.path.join(ROOT, "out", name + ".mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmpv, "-i", tmpa, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    os.remove(tmpv); os.remove(tmpa)
    print(out)


if __name__ == "__main__":
    for gp in sys.argv[1:]: render(gp)
