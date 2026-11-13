"""FUSSBALL AKTE – Case-File format (v3): #006 The 149-0 match"""
import sys, math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
PAPER = (233, 223, 199); PAPER_D = (205, 192, 160); INK = (28, 26, 24)
RED = (214, 35, 45); GREEN = (60, 255, 133); WHITE = (245, 245, 240); BLACK = (8, 8, 8)
TYPE = "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf"
FB = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FXB = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
_fc = {}
def font(p, s):
    s = max(6, int(s))
    if (p, s) not in _fc: _fc[(p, s)] = ImageFont.truetype(p, s)
    return _fc[(p, s)]
def clamp(x, a=0, b=1): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eb(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

# ---------- background: dark desk with grain + vignette ----------
rng = np.random.default_rng(1)
g = rng.normal(0, 9, (H, W)).astype(np.float32)
yy, xx = np.mgrid[0:H, 0:W]
vig = 1 - 0.75 * np.clip(((xx - W / 2) ** 2 / (W * 0.7) ** 2 + (yy - H * 0.45) ** 2 / (H * 0.6) ** 2), 0, 1)
base = np.stack([24 + g, 20 + g, 18 + g], -1) * vig[..., None]
BG = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")

# paper texture tile
pt = rng.normal(0, 6, (900, 900)).astype(np.float32)
PAPER_TEX = Image.fromarray(np.clip(np.stack([PAPER[0] + pt, PAPER[1] + pt, PAPER[2] + pt], -1), 0, 255).astype(np.uint8)).convert("RGBA")

def card(w, h, angle=0, pin=True, tape=False):
    c = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", c.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([24, 28, w + 24, h + 28], fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    c.alpha_composite(sh)
    paper = PAPER_TEX.crop((0, 0, w, h))
    c.alpha_composite(paper, (16, 16))
    d = ImageDraw.Draw(c)
    d.rectangle([16, 16, w + 15, h + 15], outline=PAPER_D + (255,), width=3)
    return c

def put(layer, im, cx, cy, angle=0, scale=1.0, alpha=1.0):
    if alpha <= 0: return
    if scale != 1: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if angle: im = im.rotate(angle, expand=True, resample=Image.BICUBIC)
    if alpha < 1:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    layer.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def tw(txt, f): return f.getlength(txt)

def text(layer, txt, f, cx, y, col, a=1.0, anchor="c"):
    if a <= 0: return
    d = ImageDraw.Draw(layer)
    x = cx - tw(txt, f) / 2 if anchor == "c" else cx
    d.text((x, y), txt, font=f, fill=col + (int(255 * clamp(a)),))

def typed(txt, t, start, cps=28):
    n = int(max(0, t - start) * cps)
    return txt[:n]

def stamp_img(txt, size, color):
    f = font(FB, size)
    w = int(tw(txt, f)) + 60; h = size + 50
    im = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, w + 10, h + 10], radius=12, outline=color + (235,), width=9)
    d.text((40, 22), txt, font=f, fill=color + (235,))
    # worn ink: punch random holes
    a = np.array(im); m = rng.random(a.shape[:2]) < 0.06
    a[m, 3] = (a[m, 3] * 0.2).astype(np.uint8)
    return Image.fromarray(a)

_st = {}
def stamp(layer, txt, cx, cy, t, start, size=90, color=RED, angle=-8):
    p = (t - start) / 0.22
    if p <= 0: return
    k = (txt, size, color)
    if k not in _st: _st[k] = stamp_img(txt, size, color)
    sc = 2.0 - 1.0 * eo(p) if p < 1 else 1.0
    put(layer, _st[k], cx, cy, angle, sc, clamp(p * 1.4))

def redact_reveal(layer, txt, f, cx, y, col, t, start, dur=0.35):
    """black bar over text that gets torn away left->right"""
    w = tw(txt, f); x0 = cx - w / 2; h = f.size * 1.15
    text(layer, txt, f, cx, y, col, 1)
    p = eo((t - start) / dur)
    if p < 1:
        d = ImageDraw.Draw(layer)
        xs = x0 - 14 + (w + 28) * p
        d.rectangle([xs, y - 6, x0 + w + 14, y + h], fill=BLACK + (255,))
        if 0 < p:  # torn edge
            pts = [(xs, y - 6)] + [(xs - 10 * (i % 2), y - 6 + i * h / 8) for i in range(9)]
            d.polygon(pts + [(xs + 4, y + h), (xs + 4, y - 6)], fill=BLACK + (255,))

def pin(layer, x, y):
    d = ImageDraw.Draw(layer)
    d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=(180, 20, 30, 255))
    d.ellipse([x - 6, y - 8, x + 2, y], fill=(255, 140, 140, 255))

def string(layer, a, b, p):
    if p <= 0: return
    d = ImageDraw.Draw(layer)
    ex = (a[0] + (b[0] - a[0]) * p, a[1] + (b[1] - a[1]) * p)
    d.line([a, ex], fill=(200, 25, 35, 255), width=6)

def folder(layer, t, opening, cy=960):
    """dark green folder with tab; opening 0..1 flips the cover up"""
    fw, fh = 900, 620
    x0, y0 = W / 2 - fw / 2, cy - fh / 2
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([x0, y0 - 40, x0 + 300, y0 + 20], radius=14, fill=(20, 70, 40, 255))
    d.rounded_rectangle([x0, y0, x0 + fw, y0 + fh], radius=16, fill=(16, 58, 33, 255))
    # cover (shrinks upward as it opens)
    ch = fh * (1 - opening)
    if ch > 4:
        d.rounded_rectangle([x0 + 8, y0 + fh - ch, x0 + fw - 8, y0 + fh], radius=16, fill=(28, 92, 52, 255))
        d.rectangle([x0 + 8, y0 + fh - ch, x0 + fw - 8, y0 + fh - ch + 10], fill=(40, 120, 70, 255))
        if ch > 200:
            text(layer, "FUSSBALL AKTE", font(TYPE, 58), W / 2, y0 + fh - ch / 2 - 80, (220, 240, 225), 1)
            text(layer, "CASE #006", font(TYPE, 84), W / 2, y0 + fh - ch / 2 - 10, (240, 250, 240), 1)

# ---------- timeline (seconds) ----------
T = dict(open=1.0, hook=1.5, reveal=2.4, purpose=3.4, e1=5.6, e2=9.0, e3=12.6, motive=16.2, motive_r=17.6,
         verdict=20.8, q=24.0, closed=27.2, end=29.0)

def scene(L, t):
    d = ImageDraw.Draw(L)
    # top brand bar (constant)
    text(L, "FUSSBALL AKTE", font(TYPE, 34), W / 2, 120, (200, 190, 170), 1)
    d.line([(W / 2 - 220, 168), (W / 2 + 220, 168)], fill=(120, 30, 35, 255), width=3)
    # red scanline sweep (signature)
    sy = (t * 520) % (H + 400) - 200
    d.rectangle([0, sy, W, sy + 3], fill=(255, 40, 50, 60))

    # ---- phase 1: folder intro ----
    if t < T["hook"] + 0.3:
        slam = eb(t / 0.3)
        op = eo((t - T["open"]) / 0.5)
        fl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        folder(fl, t, op)
        put(L, fl, W / 2, H / 2 + (1 - min(slam, 1)) * 300, 0, 1, clamp(1 - (t - T["hook"]) / 0.3))
        stamp(L, "CLASSIFIED", W / 2, 1360, t, 0.25, size=96, angle=-9)
        if t < T["hook"]: return

    # ---- phase 2: hook document ----
    if t < T["e1"]:
        a = clamp((t - T["hook"]) / 0.25)
        c = card(900, 760)
        put(L, c, W / 2, 900, -1.5, 1, a)
        text(L, "CLASSIFIED FILE", font(TYPE, 40), W / 2, 580, RED, a)
        text(L, typed("A TEAM LOST", t, T["hook"] + 0.1), font(TYPE, 70), W / 2, 680, INK, a)
        if t >= T["reveal"] - 0.5:
            redact_reveal(L, "149 - 0", font(FB, 250), W / 2, 760, RED, t, T["reveal"])
        if t >= T["purpose"]:
            stamp(L, "ON PURPOSE.", W / 2, 1180, t, T["purpose"], size=100, angle=-7)
        return

    # ---- phase 3: evidence board ----
    cards = [  # (key, x, y, angle, title, big, small)
        ("e1", 290, 620, -4, "EVIDENCE #1", "31.10.2002", "MADAGASCAR"),
        ("e2", 790, 770, 3, "EVIDENCE #2", "149", "OWN GOALS"),
        ("e3", 300, 1120, 2, "EVIDENCE #3", "36 SEC", "PER OWN GOAL"),
    ]
    board_fade = 1 - clamp((t - T["verdict"]) / 0.4) * 0.85
    pins = []
    for key, x, y, ang, title, big, small in cards:
        if t < T[key]: continue
        p = eb((t - T[key]) / 0.35)
        c = card(480, 350)
        cd = Image.new("RGBA", c.size, (0, 0, 0, 0)); cd.alpha_composite(c)
        text(cd, title, font(TYPE, 36), c.width / 2, 48, RED)
        bigtxt = big
        if key == "e2":
            bigtxt = str(int(149 * eo((t - T[key] - 0.2) / 1.6)))
        text(cd, bigtxt, font(FB, 110 if len(big) < 8 else 84), c.width / 2, 105, INK)
        text(cd, small, font(TYPE, 40), c.width / 2, 262, INK)
        put(L, cd, x, y + (1 - min(p, 1)) * 120, ang, 0.85 + 0.15 * min(p, 1), clamp(p * 2) * board_fade)
        pins.append((x, y - 150))
    for i in range(1, len(pins)):
        k = cards[i][0]
        string(L, pins[i - 1], pins[i], eo((t - T[k] - 0.2) / 0.5) * board_fade)
    for (x, y) in pins:
        pin(L, x, y)
    # motive card
    if t >= T["motive"]:
        p = eb((t - T["motive"]) / 0.35)
        c = card(560, 400)
        cd = Image.new("RGBA", c.size, (0, 0, 0, 0)); cd.alpha_composite(c)
        text(cd, "MOTIVE", font(TYPE, 40), c.width / 2, 50, RED)
        text(cd, "PROTEST AGAINST", font(TYPE, 42), c.width / 2, 120, INK)
        text(cd, "THE REFEREE", font(FB, 72), c.width / 2, 178, INK)
        if t >= T["motive_r"] - 0.3:
            lyr = Image.new("RGBA", c.size, (0, 0, 0, 0))
            redact_reveal(lyr, "A LATE PENALTY", font(TYPE, 42), c.width / 2, 300, RED, t, T["motive_r"])
            cd.alpha_composite(lyr)
        put(L, cd, 760, 1230 + (1 - min(p, 1)) * 120, -3, 0.85 + 0.15 * min(p, 1), clamp(p * 2) * board_fade)
        string(L, pins[-1], (760, 1060), eo((t - T["motive"] - 0.2) / 0.5) * board_fade)
        pin(L, 760, 1060)

    # ---- phase 4: verdict ----
    if t >= T["verdict"]:
        va = clamp((t - T["verdict"]) / 0.3)
        d.rectangle([40, 700, W - 40, 1050], fill=(10, 10, 10, int(225 * va)))
        stamp(L, "WORLD RECORD", W / 2, 810, t, T["verdict"], size=100, color=RED, angle=-6)
        a = clamp((t - T["verdict"] - 0.5) / 0.3)
        text(L, "Biggest scoreline in football history.", font(TYPE, 38), W / 2, 920, WHITE, a)
        text(L, "The team was punished.", font(TYPE, 38), W / 2, 975, WHITE, clamp((t - T["verdict"] - 1.0) / 0.3))
    if t >= T["q"]:
        a = clamp((t - T["q"]) / 0.3)
        d.rectangle([60, 1080, W - 60, 1420], fill=(10, 10, 10, int(230 * a)))
        text(L, "WOULD YOU", font(FB, 80), W / 2, 1110, WHITE, a)
        text(L, "PROTEST LIKE THIS?", font(FB, 80), W / 2, 1200, WHITE, a)
        for i, (lab, x, col) in enumerate((("YES", 360, GREEN), ("NO", 720, RED))):
            pa = clamp((t - T["q"] - 0.5 - i * 0.15) / 0.3)
            f = font(FB, 64)
            w = tw(lab, f) + 90
            d.rounded_rectangle([x - w / 2, 1305, x + w / 2, 1395], radius=45, fill=col + (int(255 * pa),))
            text(L, lab, f, x, 1313, BLACK, pa)
        text(L, "COMMENT YOUR VERDICT", font(TYPE, 34), W / 2, 1440, (200, 190, 170), a)
    if t >= T["closed"]:
        stamp(L, "CASE CLOSED", W / 2, 1560, t, T["closed"], size=96, angle=-8)

def frame(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    scene(L, t)
    img = Image.alpha_composite(BG, L)
    # slight shake on stamp hits
    for s in (0.25, T["purpose"], T["verdict"], T["closed"]):
        if 0 <= t - s < 0.18:
            k = int(14 * (1 - (t - s) / 0.18))
            img = img.transform(img.size, Image.AFFINE, (1, 0, random.randint(-k, k), 0, 1, random.randint(-k, k)))
    return img.convert("RGB")

# ---------- audio ----------
SR = 44100
def sfx_track(dur):
    n = int(dur * SR); out = np.zeros(n)
    def add(sig, t):
        i = int(t * SR); j = min(n, i + len(sig))
        if i < n: out[i:j] += sig[: j - i]
    tt = np.arange(int(0.5 * SR)) / SR
    # clean, noise-free sounds (no white noise)
    thud = np.tanh(2 * np.sin(2 * np.pi * np.cumsum(55 + 150 * np.exp(-tt * 40)) / SR) * np.exp(-tt * 9)) * 0.9
    tk = np.arange(int(0.025 * SR)) / SR
    click = np.sin(2 * np.pi * 1800 * tk) * np.exp(-tk * 400) * 0.25
    rip_t = np.arange(int(0.25 * SR)) / SR
    rip = np.sin(2 * np.pi * np.cumsum(900 - 700 * rip_t / 0.25) / SR) * np.exp(-rip_t * 10) * 0.25
    for s in (0.25, T["purpose"], T["verdict"], T["closed"]): add(thud, s)
    for s in (T["e1"], T["e2"], T["e3"], T["motive"]): add(thud * 0.45, s)
    for s in (T["reveal"], T["motive_r"]): add(rip, s)
    for start, txt in ((T["hook"] + 0.1, "A TEAM LOST"),):
        for k, ch in enumerate(txt):
            if ch != " ": add(click, start + k / 28)
    return out

def build_audio(dur, out="case_audio.wav"):
    s = sfx_track(dur)
    s = s / max(1e-6, np.abs(s).max()) * 0.9
    pcm = (s * 32767).astype(np.int16)
    with wave.open("case_sfx.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-stream_loop", "-1", "-i", "beat.wav", "-i", "case_sfx.wav",
                    "-filter_complex", f"[0:a]volume=0.45,atrim=0:{dur:.2f},afade=t=out:st={dur-0.6:.2f}:d=0.6[b];[1:a]aformat=channel_layouts=stereo,volume=1.0[s];[b][s]amix=inputs=2:duration=first:normalize=0[m]",
                    "-map", "[m]", "-t", f"{dur:.2f}", "-ar", "44100", "-ac", "2", out], check=True)
    return out

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "frames":
        for ts in sys.argv[2:]: frame(float(ts)).save(f"/tmp/c_{ts}.png")
        sys.exit()
    out = sys.argv[1] if len(sys.argv) > 1 else "akte006_case_preview.mp4"
    dur = T["end"]; audio = build_audio(dur)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", audio, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)): p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait(); print(out, dur)
