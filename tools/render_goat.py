"""AKTE VS AKTE #006 – Messi vs Ronaldo: Who is the GOAT?  (signature format v2)"""
import sys, json, math, subprocess
import render2 as R
from render2 import (W, H, FPS, GREEN, RED, WHITE, MUTED, FB, FXB, FBOLD, font, draw_text, stamp,
                     appear, pop_in, paste, asset, clamp, ease_out, ease_back, BG)
from PIL import Image, ImageDraw, ImageFilter

GREY = (120, 132, 125)
GOLD = (255, 205, 60)
XL, XR = 290, 790

ROWS = [  # label, messi, ronaldo, display strings
    ("BALLON D'OR", 8, 5),
    ("UCL TITLES", 4, 5),
    ("UCL GOALS", 129, 140),
    ("WORLD CUPS", 1, 0),
    ("HEAD-TO-HEAD", 16, 11),
]

# event times (seconds). Overwritten by timing file once the voiceover exists.
EV = dict(hook=0.0, r1=3.2, r2=6.2, r3=9.2, r4=12.4, r5=15.4, final=19.0, q=22.0, cta=23.5, closed=26.0, end=28.5)
try:
    EV.update(json.load(open("goat_timing.json")))
except FileNotFoundError:
    pass

def score_at(t):
    m = r = 0
    for i, (_, a, b) in enumerate(ROWS):
        if t >= EV[f"r{i+1}"] + 0.6:
            if a > b: m += 1
            elif b > a: r += 1
    return m, r

def scene(L, G, t):
    R.header(L, G, t, None)
    # corner ball (brand mark), always spinning
    paste(L, asset("pfp_ball", 120), W - 95, 120, 1, 1, angle=-t * 60)
    stamp(L, "AKTE VS AKTE #006", W / 2, 262, t, -1, size=50, angle=-3)
    draw_text(L, "WHO IS THE GOAT?", font(FB, 64), W / 2, 322, WHITE, 1, spacing=2)
    final_p = clamp((t - EV["final"]) / 0.35)
    # jerseys slam in at frame 0
    for i, (x, img, name) in enumerate([(XL, "j/messi_barca", "MESSI"), (XR, "j/ronaldo_rm", "RONALDO")]):
        p = clamp(t / 0.35)
        sc = 1.1 - 0.1 * ease_back(p)
        dx = (-1 if i == 0 else 1) * 80 * (1 - ease_out(p))
        paste(L, asset(img, 320), x + dx, 600, 1, sc, angle=(-1 if i == 0 else 1) * (4 + 2 * math.sin(t * 2)))
        draw_text(L, name, font(FB, 54), x, 775, WHITE, 1, spacing=2)
    draw_text(G, "VS", font(FB, int(120 * (1 + 0.08 * math.sin(t * 6)))), W / 2, 530, RED, 1)
    # live score
    m, r = score_at(t)
    sf = font(FB, 64)
    if final_p < 1:
        draw_text(L, f"{m}  :  {r}", sf, W / 2, 770, GOLD, 1 - final_p)
    # stat rows (fade out when the final verdict appears)
    rows_a = 1 - final_p
    for i, (lab, a, b) in enumerate(ROWS):
        k = f"r{i+1}"
        y = 880 + i * 118
        al, off = appear(t, EV[k], 0.3)
        al *= rows_a
        if al <= 0: continue
        draw_text(L, lab, font(FXB, 34), W / 2, y + 18 + off, MUTED, al, spacing=3)
        p = ease_out((t - EV[k] - 0.2) / 0.5)
        done = p >= 0.999
        for side, val, other, x in ((0, a, b, XL), (1, b, a, XR)):
            win = val > other
            col = WHITE if not done else (GREEN if win else GREY)
            layer = G if (done and win) else L
            draw_text(layer, str(int(round(val * p))), font(FB, 96), x, y - 18 + off, col, al * clamp(p * 3))
            if done and win:
                draw_text(L, str(val), font(FB, 96), x, y - 18 + off, col, al)
    # final verdict
    if final_p > 0:
        s = ease_back(final_p)
        draw_text(L, "FINAL SCORE", font(FXB, 46), W / 2, 880, MUTED, final_p, spacing=6)
        f = font(FB, int(260 * max(0.3, s)))
        draw_text(G, f"{m} : {r}", f, W / 2, 925, GOLD, final_p)
        draw_text(L, f"{m} : {r}", f, W / 2, 925, GOLD, final_p)
    if t >= EV["q"]:
        a, off = appear(t, EV["q"], 0.3)
        draw_text(G, "WHO'S YOUR GOAT?", font(FB, 70), W / 2, 1235 + off, GREEN, a)
        draw_text(L, "WHO'S YOUR GOAT?", font(FB, 70), W / 2, 1235 + off, GREEN, a)
    if t >= EV["cta"]:
        a, s = pop_in(t, EV["cta"], 0.4)
        pulse = 1 + 0.05 * math.sin((t - EV["cta"]) * 9)
        for x, name in ((XL, "MESSI"), (XR, "RONALDO")):
            f = font(FB, max(8, int(54 * s * pulse)))
            w = R.text_w(name, f) + 60
            d = ImageDraw.Draw(L)
            d.rounded_rectangle([x - w / 2, 1340, x + w / 2, 1340 + 95 * s], radius=48, fill=(60, 255, 133, int(255 * a)))
            draw_text(L, name, f, x, 1351, (5, 8, 6), a)
        draw_text(L, "COMMENT", font(FXB, 34), W / 2, 1375, WHITE, a, spacing=4)
    if t >= EV["closed"]:
        stamp(L, "CASE CLOSED", W / 2, 1530, t, EV["closed"], size=80, color=RED, angle=-6)

def frame(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); G = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    scene(L, G, t)
    img = BG.copy()
    glow = G.filter(ImageFilter.GaussianBlur(22))
    img = Image.alpha_composite(img, glow); img = Image.alpha_composite(img, glow)
    img = Image.alpha_composite(img, G); img = Image.alpha_composite(img, L)
    return img.convert("RGB")

def build_audio(dur, voice=None, out="goat_audio.wav"):
    stamps = [0.0, EV["closed"]]
    inputs = ["-stream_loop", "-1", "-i", "beat.wav"]
    filt = [f"[0:a]volume={0.22 if voice else 0.45},atrim=0:{dur:.2f},afade=t=out:st={dur-0.5:.2f}:d=0.5[b]"]
    mix = ["[b]"]
    idx = 1
    if voice:
        inputs += ["-i", voice]
        filt.append(f"[{idx}:a]volume=1.5,apad[v]"); mix.append("[v]"); idx += 1
    for k, st in enumerate(stamps):
        inputs += ["-i", "stamp.wav"]
        ms = int(st * 1000)
        filt.append(f"[{idx}:a]volume=0.9,adelay={ms}|{ms}[s{k}]"); mix.append(f"[s{k}]"); idx += 1
    filt.append("".join(mix) + f"amix=inputs={len(mix)}:duration=first:normalize=0[m]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", ";".join(filt),
                    "-map", "[m]", "-t", f"{dur:.2f}", "-ar", "44100", "-ac", "2", out], check=True)
    return out

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "frames":
        for ts in sys.argv[2:]:
            frame(float(ts)).save(f"/tmp/g_{ts}.png")
        sys.exit()
    voice = sys.argv[2] if len(sys.argv) > 2 else None
    outname = sys.argv[1] if len(sys.argv) > 1 else "akte006_preview.mp4"
    dur = EV["end"]
    audio = build_audio(dur, voice)
    n = int(dur * FPS)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", audio, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                          outname], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    print(outname, round(dur, 2), "s")
