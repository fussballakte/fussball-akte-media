import sys, json, math, subprocess
import render2 as R
from render2 import (W, H, FPS, GREEN, RED, WHITE, MUTED, FB, FXB, FBOLD, font, draw_text, stamp,
                     appear, pop_in, paste, asset, clamp, ease_out, ease_back, BG)
from PIL import Image, ImageDraw, ImageFilter

SPEED = 1.12
GREY = (120, 132, 125)

REELS = {
 "002": dict(title="AT AGE 19", L=("j/yamal", "YAMAL"), Rt=("j/messi_arg", "MESSI"),
             rows=[("GAMES", 182, 43, 0), ("GOALS", 56, 11, 1), ("ASSISTS", 64, 6, 1)],
             twist="BUT MESSI WON 8 BALLON D'ORS", twist_col=RED, q="SO WHO WINS?",
             seg=(0.0, 22.59), ev=dict(hook=0, r1=5.38, r1n=6.37, r2=9.08, r2n=10.19, r3=12.49, r3n=13.58,
                                        twist=15.94, q=19.38, cta=20.88),
             caption="AKTE VS AKTE #002: Lamine Yamal vs Lionel Messi at 19 📁⚽\n\nYamal has more games, goals AND assists than Messi had at the same age. But Messi won 8 Ballon d'Ors...\n\nWho wins this? Comment YAMAL or MESSI 👇\n\n#lamineyamal #messi #barcelona #football #soccer #footballfacts #yamal #goat #fussballakte"),
 "003": dict(title="CHAMPIONS LEAGUE", L=("j/haaland", "HAALAND"), Rt=("j/mbappe", "MBAPPÉ"),
             sub="GAMES NEEDED FOR...",
             rows=[("10 GOALS", 7, 15, -1), ("30 GOALS", 25, 51, -1), ("50 GOALS", 49, 79, -1)],
             twist="FASTEST EVER", twist_col=GREEN, q="WHO'S THE BETTER STRIKER?",
             seg=(23.70, 45.59), ev=dict(hook=23.70, sub=25.68, r1=28.06, r1n=29.19, r2=31.73, r2n=32.86, r3=35.15,
                                          r3n=36.36, twist=39.14, q=41.61, cta=43.45),
             caption="AKTE VS AKTE #003: Haaland vs Mbappé 📁⚽\n\nGames needed to reach 10, 30 and 50 Champions League goals. Haaland is the fastest EVER to 50.\n\nBut who's the better striker? Comment HAALAND or MBAPPÉ 👇\n\n#haaland #mbappe #championsleague #ucl #football #soccer #footballfacts #realmadrid #mancity #fussballakte"),
 "004": dict(title="FOR BRAZIL · AT AGE 25", L=("j/neymar", "NEYMAR"), Rt=("j/vini", "VINI JR"),
             rows=[("GAMES", 75, 41, 0), ("GOALS", 51, 7, 1), ("ASSISTS", 30, 6, 1)],
             twist="SAME SHIRT.", twist2="TOTALLY DIFFERENT NUMBERS.", twist_col=RED, q="SO WHO'S BETTER?",
             seg=(46.61, 66.28), ev=dict(hook=46.61, sub=51.69, r1=52.66, r1n=53.25, r2=55.03, r2n=55.97, r3=57.87,
                                          r3n=58.92, twist=60.60, twist2=61.54, q=63.07, cta=64.25),
             caption="AKTE VS AKTE #004: Neymar vs Vinícius Jr for Brazil at 25 📁⚽🇧🇷\n\nSame shirt. Totally different numbers.\n\nSo who's better? Comment NEYMAR or VINI 👇\n\n#neymar #vinijr #vinicius #brazil #selecao #football #soccer #footballfacts #fussballakte"),
 "005": dict(title="AT AGE 19", L=("j/messi_barca", "MESSI"), Rt=("j/ronaldo", "RONALDO"),
             rows=[("GAMES", 43, 55, 0), ("GOALS", 11, 6, 1), ("ASSISTS", 6, 7, 1)],
             twist="NEITHER LOOKED LIKE A GOAT YET", twist_col=RED, q="WHO'S THE REAL GOAT?",
             seg=(67.30, 86.10), ev=dict(hook=67.30, r1=70.88, r1n=71.95, r2=74.13, r2n=75.06, r3=76.81, r3n=77.78,
                                          twist=79.89, q=82.20, cta=83.93),
             caption="AKTE VS AKTE #005: Messi vs Ronaldo at 19 📁⚽\n\nAt 19, neither looked like a GOAT yet...\n\nSo who's the real GOAT? Comment MESSI or RONALDO 👇\n\n#messi #ronaldo #cr7 #goat #football #soccer #footballfacts #barcelona #manchesterunited #fussballakte"),
}

def build(key):
    c = REELS[key]
    s0, s1 = c["seg"]
    ev = {k: max(0.0, (v - s0) / SPEED) for k, v in c["ev"].items()}
    dur = (s1 - s0 + 0.2) / SPEED + 0.8
    XL, XR = 290, 790

    def scene(L, G, t):
        R.header(L, G, t, None)
        stamp(L, f"AKTE VS AKTE #{key}", W / 2, 262, t, -1, size=50, angle=-3)
        draw_text(L, c["title"], font(FXB, 56), W / 2, 330, WHITE, 1, spacing=3)
        if "sub" in ev and "sub" in c:
            a, off = appear(t, ev["sub"])
            draw_text(L, c["sub"], font(FBOLD, 34), W / 2, 396 + off, MUTED, a, spacing=3)
        # jerseys slam in at frame 0
        for i, (x, (img, name)) in enumerate([(XL, c["L"]), (XR, c["Rt"])]):
            p = clamp(t / 0.35)
            sc = 1.1 - 0.1 * ease_back(p)
            dx = (-1 if i == 0 else 1) * 80 * (1 - ease_out(p))
            paste(L, asset(img, 330), x + dx, 610, 1, sc, angle=(-1 if i == 0 else 1) * (4 + 2 * math.sin(t * 2)))
            draw_text(L, name, font(FB, 56), x, 790, WHITE, 1, spacing=2)
        vs_s = 1 + 0.08 * math.sin(t * 6)
        draw_text(G, "VS", font(FB, int(120 * vs_s)), W / 2, 540, RED, 1)
        # stat rows
        for i, (lab, lv, rv, better) in enumerate(c["rows"]):
            k = f"r{i+1}"
            y = 890 + i * 130
            a, off = appear(t, ev[k], 0.3)
            if a <= 0: continue
            draw_text(L, lab, font(FXB, 40), W / 2, y + 10 + off, MUTED, a, spacing=4)
            tn = ev[k + "n"]
            if t >= tn:
                p = ease_out((t - tn) / 0.55)
                done = p >= 0.999
                for side, val, x in ((0, lv, XL), (1, rv, XR)):
                    win = (better == 1 and ((val > (rv if side == 0 else lv)))) or (better == -1 and (val < (rv if side == 0 else lv)))
                    col = WHITE if not done or better == 0 else (GREEN if win else GREY)
                    layer = G if (done and win) else L
                    draw_text(layer, str(int(round(val * p))), font(FB, 120), x, y - 30, col, clamp(p * 3))
        if t >= ev["twist"]:
            stamp(L, c["twist"], W / 2, 1352, t, ev["twist"], size=46 if len(c["twist"]) > 18 else 64,
                  color=c["twist_col"], angle=-3)
        if "twist2" in ev:
            a, off = appear(t, ev["twist2"])
            draw_text(L, c["twist2"], font(FXB, 46), W / 2, 1408 + off, WHITE, a)
        # question + CTA overlays the rows area bottom
        if t >= ev["q"]:
            a, off = appear(t, ev["q"], 0.3)
            qf = font(FB, 62 if len(c["q"]) < 18 else 50)
            draw_text(G, c["q"], qf, W / 2, 1462 + off, GREEN, a)
            draw_text(L, c["q"], qf, W / 2, 1462 + off, GREEN, a)
        if t >= ev["cta"]:
            a, s = pop_in(t, ev["cta"], 0.4)
            pulse = 1 + 0.05 * math.sin((t - ev["cta"]) * 9)
            for x, (_, name) in ((XL, c["L"]), (XR, c["Rt"])):
                f = font(FB, int(54 * s * pulse))
                w = R.text_w(name, f) + 60
                d = ImageDraw.Draw(L)
                d.rounded_rectangle([x - w / 2, 1540, x + w / 2, 1540 + 95 * s], radius=48, fill=(60, 255, 133, int(255 * a)))
                draw_text(L, name, f, x, 1551, (5, 8, 6), a)
            draw_text(L, "COMMENT", font(FXB, 34), W / 2, 1575, WHITE, a, spacing=4)

    R.SCENES[:] = [(scene, dur)]
    R.TOTAL = dur
    return c, dur, s0, s1

def frame(t, scene_fn):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); G = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    scene_fn(L, G, t)
    img = BG.copy()
    glow = G.filter(ImageFilter.GaussianBlur(22))
    img = Image.alpha_composite(img, glow); img = Image.alpha_composite(img, glow)
    img = Image.alpha_composite(img, G); img = Image.alpha_composite(img, L)
    return img.convert("RGB")

if __name__ == "__main__":
    key = sys.argv[1]
    c, dur, s0, s1 = build(key)
    fn = R.SCENES[0][0]
    if len(sys.argv) > 2:
        for ts in sys.argv[2:]:
            frame(float(ts), fn).save(f"/tmp/d{key}_{ts}.png")
        sys.exit()
    # audio: cut segment, speed up, mix with beat
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(max(0, s0 - 0.05)), "-to", str(s1 + 0.15), "-i", "batch1.mp3",
                    "-filter:a", f"atempo={SPEED}", "-ar", "44100", "-ac", "2", f"v{key}.wav"], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"v{key}.wav", "-stream_loop", "-1", "-i", "beat.wav",
                    "-filter_complex", f"[1:a]volume=0.22,atrim=0:{dur:.2f},afade=t=out:st={dur-0.4:.2f}:d=0.4[b];[0:a]volume=1.5,apad[v];[v][b]amix=inputs=2:duration=shortest:normalize=0[m]",
                    "-map", "[m]", "-t", f"{dur:.2f}", f"a{key}.wav"], check=True)
    n = int(dur * FPS)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-i", f"a{key}.wav", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", f"akte{key}.mp4"], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame(i / FPS, fn).tobytes())
    p.stdin.close(); p.wait()
    json.dump({"caption": c["caption"], "duration": dur}, open(f"akte{key}.json", "w"))
    print(key, "seconds", round(dur, 2))
