import subprocess, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
GREEN = (60, 255, 133)
RED = (255, 45, 61)
WHITE = (245, 245, 240)
MUTED = (150, 165, 155)
BG0 = (5, 8, 6)

FB = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FXB = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
FBOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
_fc = {}
def font(path, size):
    k = (path, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]

def clamp(x, a=0, b=1): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_back(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

# ---------- background (static) ----------
def make_bg():
    bg = Image.new("RGB", (W, H), BG0)
    d = ImageDraw.Draw(bg)
    for y in range(H):
        f = abs(y - H * 0.45) / (H * 0.6)
        c = tuple(int(BG0[i] + (14, 30, 20)[i] * clamp(1 - f)) for i in range(3))
        d.line([(0, y), (W, y)], fill=c)
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(grid)
    for x in range(0, W, 60):
        g.line([(x, 0), (x, H)], fill=(60, 255, 133, 14))
    for y in range(0, H, 60):
        g.line([(0, y), (W, y)], fill=(60, 255, 133, 14))
    bg = Image.alpha_composite(bg.convert("RGBA"), grid)
    return bg
BG = make_bg()

# ---------- drawing helpers ----------
def text_w(txt, f, spacing=0):
    return f.getlength(txt) + spacing * max(0, len(txt) - 1)

def draw_text(layer, txt, f, cx, y, color, alpha=1.0, spacing=0, anchor="c"):
    if alpha <= 0: return
    d = ImageDraw.Draw(layer)
    w = text_w(txt, f, spacing)
    x = cx - w / 2 if anchor == "c" else cx
    col = color + (int(255 * clamp(alpha)),)
    if spacing == 0:
        d.text((x, y), txt, font=f, fill=col)
    else:
        for ch in txt:
            d.text((x, y), ch, font=f, fill=col)
            x += f.getlength(ch) + spacing

def appear(t, start, dur=0.45):
    """returns (alpha, y-offset) for a slide-up entrance"""
    p = ease_out((t - start) / dur)
    return p, (1 - p) * 60

def stamp(layer, txt, cx, cy, t, start, size=74, color=RED, angle=-10):
    p = (t - start) / 0.28
    if p <= 0: return
    scale = 1.8 - 0.8 * ease_out(p) if p < 1 else 1.0
    f = font(FB, size)
    tw = int(text_w(txt, f, 6)); th = size
    pad = 26
    box = Image.new("RGBA", (tw + pad * 2 + 20, th + pad * 2 + 30), (0, 0, 0, 0))
    bd = ImageDraw.Draw(box)
    a = int(255 * clamp(p * 1.5))
    bd.rounded_rectangle([6, 6, box.width - 6, box.height - 6], radius=14, outline=color + (a,), width=9)
    draw_text(box, txt, f, box.width / 2, pad - 2, color, a / 255, spacing=6)
    box = box.resize((max(1, int(box.width * scale)), max(1, int(box.height * scale))))
    box = box.rotate(angle, expand=True, resample=Image.BICUBIC)
    layer.alpha_composite(box, (int(cx - box.width / 2), int(cy - box.height / 2)))

def header(layer, glow, t, fact_idx, total=5):
    # brand line
    draw_text(layer, "FUSSBALL AKTE", font(FXB, 34), W / 2, 150, MUTED, 1, spacing=10)
    if fact_idx is None: return
    # progress segments
    seg_w, gap = 150, 14
    x0 = W / 2 - (total * seg_w + (total - 1) * gap) / 2
    d = ImageDraw.Draw(layer); dg = ImageDraw.Draw(glow)
    for i in range(total):
        x = x0 + i * (seg_w + gap)
        d.rounded_rectangle([x, 215, x + seg_w, 225], radius=5, fill=(60, 80, 68, 255))
        if i <= fact_idx:
            d.rounded_rectangle([x, 215, x + seg_w, 225], radius=5, fill=GREEN + (255,))
            dg.rounded_rectangle([x, 215, x + seg_w, 225], radius=5, fill=GREEN + (255,))
    draw_text(layer, f"FACT {fact_idx + 1}/{total}", font(FBOLD, 32), W / 2, 250, GREEN, 1, spacing=6)

def wrap_lines(layer, lines, f, y, color, t, start, step=0.12, lh=None, spacing=0):
    lh = lh or int(f.size * 1.2)
    for i, ln in enumerate(lines):
        a, off = appear(t, start + i * step)
        draw_text(layer, ln, f, W / 2, y + i * lh + off, color, a, spacing=spacing)

def count(t, start, dur, value):
    return int(round(value * ease_out((t - start) / dur)))

# ---------- assets ----------
A = {}
def asset(name, w):
    k = (name, w)
    if k not in A:
        im = Image.open(f"assets/{name}.png").convert("RGBA")
        A[k] = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    return A[k]

def paste(layer, im, cx, cy, alpha=1.0, scale=1.0, angle=0):
    if alpha <= 0 or scale <= 0: return
    if scale != 1: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if angle: im = im.rotate(angle, expand=True, resample=Image.BICUBIC)
    if alpha < 1:
        im = im.copy(); a = im.getchannel("A").point(lambda v: int(v * alpha)); im.putalpha(a)
    layer.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def pop_in(t, start, dur=0.5):
    p = (t - start) / dur
    return clamp(p * 2), (ease_back(p) if p < 1 else 1.0) if p > 0 else 0

def arrow(layer, x0, x1, y, a):
    d = ImageDraw.Draw(layer); c = GREEN + (int(255 * a),)
    d.line([(x0, y), (x1, y)], fill=c, width=8)
    d.polygon([(x1 + 18, y), (x1 - 6, y - 18), (x1 - 6, y + 18)], fill=c)

# ---------- scenes ----------
def s_intro(L, G, t):
    header(L, G, t, None)
    stamp(L, "AKTE #001", W / 2, 360, t, 1.6, size=88)
    a, s = pop_in(t, 0.0, 0.6)
    paste(L, asset("arg", 560), W / 2, 780, a, s, angle=4 * math.sin(t * 1.5))
    a, off = appear(t, 0.1)
    draw_text(G, "DIEGO", font(FB, 150), W / 2, 1100 + off, GREEN, a)
    a, off = appear(t, 0.3)
    draw_text(G, "MARADONA", font(FB, 134), W / 2, 1255 + off, GREEN, a)
    wrap_lines(L, ["5 facts most fans don't know"], font(FXB, 60), 1450, WHITE, t, 1.9)

def s_transfer(L, G, t):
    header(L, G, t, 0)
    wrap_lines(L, ["He broke the", "world transfer record"], font(FXB, 72), 400, WHITE, t, 0.1)
    p = ease_back((t - 3.1) / 0.5)
    if p > 0:
        draw_text(G, "2×", font(FB, int(260 * max(0.2, p))), W / 2, 590 + (1 - min(p, 1)) * 60, GREEN, clamp(p))
    xs = [190, 540, 890]; names = ["BOCA", "BARCELONA", "NAPOLI"]
    for i, (x, n) in enumerate(zip(xs, ["boca_s", "barca_s", "napoli_s"])):
        st = 0.7 + i * 0.7
        a, s = pop_in(t, st, 0.45)
        paste(L, asset(n, 250), x, 1060, a, s)
        a2, off = appear(t, st + 0.1)
        draw_text(L, names[i], font(FXB, 40), x, 1220 + off, WHITE, a2, spacing=4)
        if i > 0:
            pa = clamp((t - st + 0.4) / 0.3)
            arrow(G, xs[i - 1] + 115, x - 135, 1060, pa)
            draw_text(L, ["1982", "1984"][i - 1], font(FB, 44), (xs[i - 1] + x) / 2, 980, GREEN, pa)

def s_hand(L, G, t):
    header(L, G, t, 1)
    wrap_lines(L, ["June 22, 1986", "Argentina vs England"], font(FBOLD, 54), 380, MUTED, t, 1.2, lh=76)
    if t > 1.6:
        draw_text(G, f"{count(t, 1.6, 0.9, 51)}'", font(FB, 280), W / 2, 540, GREEN, ease_out((t - 1.6) / 0.3))
    # ball rolls in from the right
    p = ease_out((t - 3.0) / 0.9)
    if p > 0:
        paste(L, asset("ball", 300), 1300 - 760 * p, 1150, clamp(p * 2), 1, angle=360 * (1 - p) * 1.5)
    stamp(L, "HAND OF GOD", W / 2, 940, t, 7.3, size=92, angle=-6)
    wrap_lines(L, ["He scored with his hand.", "The referee gave the goal."], font(FXB, 56), 1360, WHITE, t, 4.2, step=1.3, lh=78)

def pitch(L, G, t, t0):
    x0, x1, y0, y1 = 150, 930, 640, 1460
    d = ImageDraw.Draw(L)
    for i in range(8):
        yy = y0 + i * (y1 - y0) / 8
        d.rectangle([x0, yy, x1, yy + (y1 - y0) / 8], fill=(24, 92, 48, 255) if i % 2 else (28, 104, 55, 255))
    lw = (235, 245, 238, 230)
    d.rectangle([x0, y0, x1, y1], outline=lw, width=6)
    d.rectangle([330, y0, 750, y0 + 230], outline=lw, width=5)
    d.rectangle([440, y0, 640, y0 + 90], outline=lw, width=5)
    d.rectangle([480, y0 - 26, 600, y0], outline=lw, width=5)
    d.line([(x0, y1 - 80), (x1, y1 - 80)], fill=lw, width=5)
    d.arc([400, y1 - 220, 680, y1 + 60], 180, 360, fill=lw, width=5)
    path = [(470, 1430), (430, 1300), (600, 1190), (500, 1060), (660, 930), (590, 800), (540, 700), (540, 655)]
    defs = [(400, 1250, "1"), (640, 1140, "2"), (450, 1010, "3"), (700, 880, "4"), (630, 760, "5"), (500, 735, "GK")]
    for i, (x, y, lab) in enumerate(defs):
        a = clamp((t - t0 - 0.1 * i) / 0.3)
        if a > 0:
            d.ellipse([x - 24, y - 24, x + 24, y + 24], fill=RED + (int(255 * a),), outline=(255, 255, 255, int(255 * a)), width=4)
    # animate run
    p = clamp((t - t0 - 0.8) / 4.0)
    segs = list(zip(path[:-1], path[1:]))
    lens = [math.dist(a, b) for a, b in segs]; total = sum(lens); target = total * p
    dg = ImageDraw.Draw(G); dl = ImageDraw.Draw(L); head = path[0]; acc = 0
    for (a, b), ln in zip(segs, lens):
        if acc >= target: break
        f = min(1, (target - acc) / ln)
        e = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        # dashed line
        steps = int(ln * f / 22)
        for k in range(steps):
            if k % 2 == 0:
                q0 = k / max(1, ln * f / 22); q1 = (k + 1) / max(1, ln * f / 22)
                dg.line([(a[0] + (e[0] - a[0]) * q0, a[1] + (e[1] - a[1]) * q0),
                         (a[0] + (e[0] - a[0]) * min(1, q1), a[1] + (e[1] - a[1]) * min(1, q1))], fill=GREEN + (255,), width=9)
                dl.line([(a[0] + (e[0] - a[0]) * q0, a[1] + (e[1] - a[1]) * q0),
                         (a[0] + (e[0] - a[0]) * min(1, q1), a[1] + (e[1] - a[1]) * min(1, q1))], fill=GREEN + (255,), width=9)
        head = e; acc += ln
    if t > t0 + 0.8:
        paste(L, asset("ball", 60), head[0], head[1], 1, 1, angle=-t * 400)

def s_century(L, G, t):
    header(L, G, t, 2)
    wrap_lines(L, ["4 minutes later..."], font(FXB, 66), 340, WHITE, t, 1.3)
    if t > 5.8:
        n = count(t, 5.8, 1.0, 11)
        draw_text(G, f"{n} SECONDS", font(FB, 110), W / 2, 450, GREEN, ease_out((t - 5.8) / 0.3))
    pitch(L, G, t, 2.0)
    stamp(L, "GOAL OF THE CENTURY", W / 2, 1560, t, 7.9, size=56, angle=-4)

def s_napoli(L, G, t):
    header(L, G, t, 3)
    wrap_lines(L, ["Napoli had", "NEVER won Serie A"], font(FXB, 80), 390, WHITE, t, 1.3, lh=100)
    a, s = pop_in(t, 1.6, 0.6)
    paste(L, asset("napoli", 480), W / 2, 900, a, s, angle=3 * math.sin(t * 1.4))
    for i, x in enumerate([430, 650]):
        a, s = pop_in(t, 3.8 + i * 0.35, 0.4)
        d = ImageDraw.Draw(G)
        if a > 0:
            r = 46 * s; cy = 610
            pts = [(x + r * math.cos(math.radians(-90 + k * 36)) * (1 if k % 2 == 0 else 0.45),
                    cy + r * math.sin(math.radians(-90 + k * 36)) * (1 if k % 2 == 0 else 0.45)) for k in range(10)]
            d.polygon(pts, fill=(255, 205, 60, int(255 * a)))
    wrap_lines(L, ["He won them two."], font(FXB, 74), 1220, GREEN, t, 3.7)
    wrap_lines(L, ["1987  ·  1990"], font(FBOLD, 54), 1330, MUTED, t, 4.2, spacing=6)

def s_church(L, G, t):
    header(L, G, t, 4)
    wrap_lines(L, ["Fans founded", "a church in his name"], font(FXB, 80), 400, WHITE, t, 0.9, lh=100)
    a, s = pop_in(t, 1.5, 0.6)
    if a > 0:
        d = ImageDraw.Draw(G); cy = 820
        r = 230 * s
        d.ellipse([W / 2 - r, cy - 40 * s - r * 0.28, W / 2 + r, cy - 40 * s + r * 0.28], outline=(255, 215, 90, int(255 * a)), width=14)
        draw_text(G, "10", font(FB, int(380 * s)), W / 2, cy - 10 + (1 - s) * 100, (255, 215, 90), a)
    stamp(L, "IGLESIA MARADONIANA", W / 2, 1290, t, 2.3, size=58, color=GREEN, angle=-4)
    wrap_lines(L, ["Founded in 1998."], font(FXB, 58), 1440, WHITE, t, 2.7)

def s_outro(L, G, t):
    header(L, G, t, None)
    paste(L, asset("ball", 320), W / 2, 560, clamp(t / 0.3), 1, angle=-t * 90)
    wrap_lines(L, ["Which footballer", "should we open next?"], font(FXB, 76), 800, WHITE, t, 0.3, lh=98)
    stamp(L, "AKTE #002", W / 2, 1110, t, 1.3, size=96)
    wrap_lines(L, ["Tell us in the comments"], font(FXB, 60), 1290, GREEN, t, 2.3)
    wrap_lines(L, ["Follow @fussball.akte"], font(FBOLD, 50), 1400, MUTED, t, 2.8)

import json, os
_d = json.load(open("timing.json")) if os.path.exists("timing.json") else [3.0, 4.0, 4.6, 5.0, 4.2, 4.6, 3.6]
SCENES = list(zip([s_intro, s_transfer, s_hand, s_century, s_napoli, s_church, s_outro], _d))
TOTAL = sum(d for _, d in SCENES)

def glitch(img, strength):
    if strength <= 0: return img
    out = img.copy()
    rnd = random.Random(int(strength * 1000))
    for _ in range(int(10 * strength) + 2):
        y = rnd.randint(0, H - 80); h = rnd.randint(10, 80)
        dx = rnd.randint(-60, 60)
        band = img.crop((0, y, W, y + h))
        out.paste(band, (dx, y))
    return out

def frame(i):
    t = i / FPS
    acc = 0
    for fn, dur in SCENES:
        if t < acc + dur or fn is SCENES[-1][0]:
            lt = t - acc
            break
        acc += dur
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    G = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fn(L, G, lt)
    img = BG.copy()
    glow = G.filter(ImageFilter.GaussianBlur(22))
    img = Image.alpha_composite(img, glow)
    img = Image.alpha_composite(img, glow)
    img = Image.alpha_composite(img, G)
    img = Image.alpha_composite(img, L)
    # fade out at scene end, glitch at scene start
    fade = clamp((dur - lt) / 0.22) if fn is not SCENES[-1][0] else 1
    if fade < 1:
        img = Image.blend(BG, img, fade)
    if lt < 0.12 and acc > 0:
        img = glitch(img, 1 - lt / 0.12)
    # scanlines
    return img.convert("RGB")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:  # preview frames
        for ts in sys.argv[1:]:
            frame(int(float(ts) * FPS)).save(f"prev_{ts}.png")
        sys.exit()
    n = int(TOTAL * FPS)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                          "-movflags", "+faststart", "video_only.mp4"], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame(i).tobytes())
    p.stdin.close(); p.wait()
    print("frames", n, "seconds", TOTAL)
