import numpy as np, wave
SR = 44100
BPM = 130
beat = 60 / BPM
step = beat / 4            # 16th notes
BARS = 12
n = int(SR * step * 16 * BARS)
out = np.zeros(n)
rng = np.random.default_rng(7)

def add(sig, t):
    i = int(t * SR)
    j = min(n, i + len(sig))
    if i < n: out[i:j] += sig[: j - i]

def env(d, a=0.002, r=None):
    t = np.arange(int(d * SR)) / SR
    e = np.minimum(1, t / a)
    return e * np.exp(-t / (r or d / 4)), t

def kick():
    e, t = env(0.45, r=0.12)
    f = 50 + 110 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * e * 0.9

def snare():
    e, t = env(0.22, r=0.05)
    return (rng.normal(0, 1, len(t)) * 0.5 + np.sin(2 * np.pi * 190 * t) * 0.4) * e * 0.55

def hat(open_=False):
    e, t = env(0.12 if open_ else 0.04, r=0.03 if open_ else 0.008)
    s = rng.normal(0, 1, len(t))
    s = np.diff(np.concatenate([[0], s]))  # crude highpass
    return s * e * 0.18

def cowbell(freq):
    e, t = env(0.28, r=0.09)
    s = np.sign(np.sin(2 * np.pi * freq * t)) + np.sign(np.sin(2 * np.pi * freq * 1.48 * t))
    return s * e * 0.07

def bass808(freq, d):
    e, t = env(d, a=0.005, r=d / 1.5)
    s = np.tanh(2.5 * np.sin(2 * np.pi * freq * t))
    return s * e * 0.38

# A minor phonk-ish cowbell riff (16 steps)
riff = {0: 880, 3: 880, 6: 784, 8: 659, 10: 698, 12: 659, 14: 587}
bassline = [(0, 55.0, 6), (6, 55.0, 2), (8, 49.0, 4), (12, 65.4, 4)]
for bar in range(BARS):
    b0 = bar * 16 * step
    for k in (0, 7, 10):
        add(kick(), b0 + k * step)
    for k in (4, 12):
        add(snare(), b0 + k * step)
    for k in range(16):
        add(hat(open_=(k % 8 == 6)), b0 + k * step)
    if bar >= 1:
        for k, f in riff.items():
            add(cowbell(f), b0 + k * step)
    for k, f, d in bassline:
        add(bass808(f, d * step), b0 + k * step)

out = out / np.max(np.abs(out)) * 0.9
pcm = (out * 32767).astype(np.int16)
st = np.stack([pcm, pcm], axis=1)
with wave.open("beat.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
print("beat seconds", n / SR)
