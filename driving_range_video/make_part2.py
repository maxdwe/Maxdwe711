#!/usr/bin/env python3
"""Video animasi Part 2: Nak jimat lagi? Amik bola kawan 10 biji (gurau je!).

Guna semula gaya & fungsi lukisan dari make_video.py (Part 1).
Output: driving_range_part2.mp4 (1080x1920, 30fps).

Guna:  python3 make_part2.py
Voiceover pilihan dalam voiceover_part2/ (1_intro.mp3 ... 5_ketawa.mp3); babak
dipanjangkan ikut panjang suara jika fail ada.
"""
import math
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw

import make_video as mv
from make_video import (W, H, FPS, DARK, GREEN, GREEN_D, YELLOW, ORANGE, RED, WHITE, GREY, BLUE,
                        font, clamp, prog, ease_out, ease_back, with_alpha, draw_text, pop_text,
                        card, golf_ball, handshake_icon)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "driving_range_part2.mp4")
WAV = os.path.join(HERE, "_audio_part2.wav")
VO_DIR = os.path.join(HERE, "voiceover_part2")
VO_START = 0.3

SCENE_DEFS = [
    ("intro", 4.5, "1_intro.mp3"),
    ("kawan", 6.0, "2_kawan.mp3"),
    ("amik", 8.0, "3_amik.mp3"),
    ("jimat", 7.5, "4_jimat.mp3"),
    ("ketawa", 6.0, "5_ketawa.mp3"),
    ("ayala", 5.0, None),
]

SCENES, VO_CLIPS = [], []
_t = 0.0
for _name, _dur, _fn in SCENE_DEFS:
    _vl = mv._vo_len(os.path.join(VO_DIR, _fn)) if _fn else 0.0
    _d = max(_dur, VO_START + _vl + 0.8) if _vl else _dur
    SCENES.append((_name, round(_t, 3), round(_t + _d, 3)))
    if _vl:
        VO_CLIPS.append((os.path.join(VO_DIR, _fn), _t + VO_START, _vl))
    _t += _d
T0 = {n: a for n, a, _ in SCENES}
DURATION = SCENES[-1][2]

# masa bola-bola "diambil" dalam babak amik (relatif kepada mula babak)
STEAL_START, STEAL_GAP = 1.2, 0.42


# ---------------------------------------------------------------- lukisan tambahan
def person(d, cx, cy, s, col, a=1.0, face="happy"):
    """Orang ringkas: kepala + badan + muka."""
    d.rounded_rectangle((cx - s * 0.6, cy, cx + s * 0.6, cy + s * 1.5), int(s * 0.35),
                        fill=with_alpha(col, a))
    d.ellipse((cx - s * 0.45, cy - s, cx + s * 0.45, cy - s * 0.1),
              fill=with_alpha((245, 205, 160), a))
    ey = cy - s * 0.6
    if face == "sly":  # mata senget nakal
        for ex in (-s * 0.17, s * 0.17):
            d.line((cx + ex - 9, ey, cx + ex + 9, ey - 4), fill=with_alpha(DARK, a), width=5)
        d.arc((cx - s * 0.2, cy - s * 0.5, cx + s * 0.25, cy - s * 0.25), 0, 140,
              fill=with_alpha(DARK, a), width=5)
    else:
        for ex in (-s * 0.17, s * 0.17):
            d.ellipse((cx + ex - 6, ey - 6, cx + ex + 6, ey + 6), fill=with_alpha(DARK, a))
        d.arc((cx - s * 0.2, cy - s * 0.55, cx + s * 0.2, cy - s * 0.25), 20, 160,
              fill=with_alpha(DARK, a), width=5)


def bucket(d, cx, cy, s, n_balls, a=1.0, col=ORANGE):
    """Bakul bola. (cx, cy) = tengah bibir atas. n_balls = isi 0..100 (nampak bertimbun)."""
    top_w, bot_w, h = s, s * 0.75, s * 0.8
    # bola bertimbun di atas
    rng = np.random.default_rng(5)
    heap = int(min(n_balls, 100) / 100 * 22)
    r = s * 0.11
    for i in range(heap):
        row = i // 7
        k = i % 7
        bx = cx - top_w / 2 + r * 1.3 + k * (top_w - r * 2.6) / 6 + (row % 2) * r * 0.6
        by = cy - r * 0.4 - row * r * 1.25 + rng.random() * 4
        golf_ball(d, bx, by, r, a)
    poly = [(cx - top_w / 2, cy), (cx + top_w / 2, cy), (cx + bot_w / 2, cy + h), (cx - bot_w / 2, cy + h)]
    d.polygon(poly, fill=with_alpha(col, a))
    d.rectangle((cx - top_w / 2 - 8, cy - 6, cx + top_w / 2 + 8, cy + 16), fill=with_alpha(DARK, a))
    for k in range(1, 3):
        y = cy + h * k / 3
        w = top_w - (top_w - bot_w) * k / 3
        d.line((cx - w / 2 + 6, y, cx + w / 2 - 6, y), fill=with_alpha((0, 0, 0), a * 0.25), width=4)


def laugh_face(d, cx, cy, r, a=1.0, wob=0.0):
    """Muka ketawa berair mata."""
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=with_alpha(YELLOW, a),
              outline=with_alpha((200, 140, 20), a), width=8)
    # mata ^ ^
    for ex in (-r * 0.38, r * 0.38):
        d.line((cx + ex - r * 0.2, cy - r * 0.18, cx + ex, cy - r * 0.38), fill=with_alpha(DARK, a), width=12)
        d.line((cx + ex, cy - r * 0.38, cx + ex + r * 0.2, cy - r * 0.18), fill=with_alpha(DARK, a), width=12)
    # mulut D besar
    mo = r * (0.05 + 0.05 * wob)
    d.chord((cx - r * 0.55, cy - r * 0.05 - mo, cx + r * 0.55, cy + r * 0.75 + mo), 0, 180,
            fill=with_alpha((120, 30, 30), a))
    d.chord((cx - r * 0.3, cy + r * 0.35, cx + r * 0.3, cy + r * 0.72 + mo), 180, 360,
            fill=with_alpha((230, 90, 100), a))
    # air mata
    for sgn in (-1, 1):
        tx = cx + sgn * r * 0.72
        ty = cy - r * 0.05 + (wob * 20) % 40
        d.ellipse((tx - r * 0.1, ty - r * 0.08, tx + r * 0.1, ty + r * 0.18), fill=with_alpha((90, 180, 250), a))


# ---------------------------------------------------------------- babak
def scene_intro(layer, t, t0, t1):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    pop_text(layer, (W // 2, 600), "PART 2", 190, YELLOW, prog(lt, 0.2, 0.5), stroke=12)
    pop_text(layer, (W // 2, 800), "NAK JIMAT", 120, WHITE, prog(lt, 0.7, 0.5), stroke=10)
    pop_text(layer, (W // 2, 940), "LAGI?", 140, WHITE, prog(lt, 1.0, 0.5), stroke=10)
    a = prog(lt, 1.6, 0.5)
    card(d, (170, 1090, 910, 1220), a, fill=DARK, radius=65)
    draw_text(d, (W // 2, 1155), "Tips rahsia driving range", font(52), WHITE, a)
    # bola berpusing kecil di bawah
    for i in range(3):
        p = prog(lt, 1.9 + i * 0.15, 0.4)
        golf_ball(d, W // 2 + (i - 1) * 140, 1400 - 30 * abs(math.sin(lt * 5 + i)), 40, p)


def scene_kawan(layer, t, t0, t1):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    pop_text(layer, (W // 2, 250), "1. TUNGGU KAWAN", 92, YELLOW, prog(lt, 0, 0.5), stroke=8)
    a = prog(lt, 0.3, 0.5)
    card(d, (70, 380, 1010, 1480), a)
    # kau (kiri) tunggu
    person(d, 300, 820, 150, BLUE, a, face="sly")
    draw_text(d, (300, 1110), "KAU", font(54), BLUE, a)
    # kawan berjalan masuk dari kanan
    p = ease_out(prog(lt, 0.8, 1.2))
    fx = 1250 - (1250 - 780) * p
    bob = abs(math.sin(lt * 8)) * 12 * (1 - prog(lt, 1.9, 0.2))
    person(d, fx, 820 - bob, 150, GREEN, a)
    bucket(d, fx + 30, 1190 - bob, 170, 100, a)
    draw_text(d, (fx, 1420), "KAWAN", font(54), GREEN_D, a * prog(lt, 1.8, 0.4))
    # gelembung fikiran "hehe"
    bp = prog(lt, 2.2, 0.4)
    if bp > 0:
        for i, (ox, oy, rr) in enumerate(((330, 600, 14), (360, 560, 22))):
            d.ellipse((ox - rr, oy - rr, ox + rr, oy + rr), fill=with_alpha((235, 240, 238), bp))
        d.rounded_rectangle((280, 430, 560, 530), 50, fill=with_alpha((235, 240, 238), bp))
        draw_text(d, (420, 480), "hehehe...", font(46), DARK, bp)
    a2 = prog(lt, 2.8, 0.5)
    card(d, (120, 1560, 960, 1700), a2, fill=DARK, radius=60)
    draw_text(d, (W // 2, 1630), "Pastikan dia beli bola dulu!", font(48), WHITE, a2)


def scene_amik(layer, t, t0, t1):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    pop_text(layer, (W // 2, 250), "2. AMIK BOLA DIA", 88, YELLOW, prog(lt, 0, 0.5), stroke=8)
    a = prog(lt, 0.2, 0.5)
    card(d, (70, 380, 1010, 1480), a)
    taken = 0
    flying = []
    for i in range(10):
        st = STEAL_START + i * STEAL_GAP
        q = prog(lt, st, 0.38)
        if q >= 1:
            taken += 1
        elif q > 0:
            flying.append(q)
    # bakul kawan (kanan) - tetap nampak penuh, dia tak perasan
    person(d, 800, 640, 120, GREEN, a)
    # kawan sedang hayun, pandang depan
    bucket(d, 800, 1050, 200, 100 - taken, a)
    draw_text(d, (800, 1300), "Bakul kawan", font(40, False), GREY, a)
    # bakul kau (kiri)
    person(d, 280, 640, 120, BLUE, a, face="sly")
    bucket(d, 280, 1050, 200, 0, a, col=BLUE)
    # bola dalam bakul kau
    for i in range(taken):
        r, c = divmod(i, 5)
        golf_ball(d, 205 + c * 38, 1030 - r * 36, 18, a)
    draw_text(d, (280, 1300), "Bakul kau", font(40, False), GREY, a)
    # bola terbang melengkung kanan -> kiri
    for q in flying:
        bx = 780 - q * 500
        by = 1020 - math.sin(q * math.pi) * 320
        golf_ball(d, bx, by, 20, a)
    # kaunter
    if lt > STEAL_START:
        pop_text(layer, (W // 2, 520), f"{taken} biji", 90, ORANGE, prog(lt, STEAL_START, 0.3), stroke=0)
    a2 = prog(lt, 0.8, 0.5)
    card(d, (70, 1530, 1010, 1790), a2, fill=DARK, radius=60)
    draw_text(d, (W // 2, 1610), 'Cakap kat kawan: "Nak try je!"', font(48), WHITE, a2)
    a3 = prog(lt, STEAL_START + 10 * STEAL_GAP, 0.5)
    draw_text(d, (W // 2, 1710), "Jangan lupa senyum & terima kasih!", font(39), YELLOW, a3)


def scene_jimat(layer, t, t0, t1):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    pop_text(layer, (W // 2, 250), "JIMAT BERAPA?", 96, YELLOW, prog(lt, 0, 0.5), stroke=8)
    a = prog(lt, 0.2, 0.5)
    card(d, (70, 380, 1010, 1560), a)
    # 10 bola sebaris
    for i in range(10):
        golf_ball(d, 180 + i * 80, 500, 28, prog(lt, 0.4 + i * 0.05, 0.3))
    draw_text(d, (W // 2, 620), "10 biji bola", font(66), DARK, prog(lt, 0.9, 0.4))
    pop_text(layer, (W // 2, 740), "= RM1.20 – RM1.50", 84, GREEN_D, prog(lt, 1.3, 0.5), stroke=0)
    draw_text(d, (W // 2, 880), "x 4 sesi sebulan", font(60), GREY, prog(lt, 2.4, 0.4))
    d.line((160, 960, 920, 960), fill=with_alpha((210, 215, 212), prog(lt, 2.4, 0.4)), width=4)
    pop_text(layer, (W // 2, 1060), "JIMAT", 80, DARK, prog(lt, 3.2, 0.5), stroke=0)
    pop_text(layer, (W // 2, 1200), "RM4.80 – RM6!", 104, RED, prog(lt, 3.5, 0.5), stroke=0)
    a2 = prog(lt, 4.4, 0.5)
    draw_text(d, (W // 2, 1360), "Boleh beli air teh ais", font(50, False), GREY, a2)
    draw_text(d, (W // 2, 1430), "sebungkus!", font(50, False), GREY, a2)


def scene_ketawa(layer, t, t0, t1):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    d.rectangle((0, 0, W, H), fill=(255, 222, 110, int(240 * prog(lt, 0, 0.3))))
    # HAHAHA dengan huruf melompat
    word = "HAHAHA"
    cols = [RED, ORANGE, GREEN, BLUE, RED, ORANGE]
    f = font(150)
    total_w = sum(mv.text_size(ch, f)[0] + 10 for ch in word)
    x = W // 2 - total_w // 2
    for i, ch in enumerate(word):
        p = prog(lt, 0.1 + i * 0.07, 0.35)
        if p <= 0:
            x += mv.text_size(ch, f)[0] + 10
            continue
        jump = abs(math.sin(lt * 9 + i * 0.9)) * 45
        cw = mv.text_size(ch, f)[0]
        draw_text(d, (x + cw // 2, 380 - jump), ch, font(int(150 * max(0.05, ease_back(p)))),
                  cols[i], clamp(p * 3), stroke=8)
        x += cw + 10
    # muka ketawa bergoyang
    p = prog(lt, 0.3, 0.5)
    if p > 0:
        wob = math.sin(lt * 14)
        r = int(230 * max(0.05, ease_back(p)))
        laugh_face(d, W // 2 + wob * 12, 780, r, clamp(p * 3), wob)
    pop_text(layer, (W // 2, 1140), "GURAU JE!", 130, WHITE, prog(lt, 1.0, 0.5), stroke=10)
    a = prog(lt, 1.7, 0.5)
    card(d, (110, 1290, 970, 1440), a, fill=DARK, radius=75)
    draw_text(d, (W // 2, 1365), "Jangan marah ye geng!", font(60), WHITE, a)
    a3 = prog(lt, 2.5, 0.5)
    draw_text(d, (W // 2, 1540), "(Pulangkan balik bola kawan tu)", font(42, False), DARK, a3)
    # bola-bola melompat gembira di bawah
    for i in range(5):
        golf_ball(d, 160 + i * 190, 1760 - abs(math.sin(lt * 6 + i)) * 110, 34, prog(lt, 0.6, 0.4))


DISPATCH = {
    "intro": scene_intro, "kawan": scene_kawan, "amik": scene_amik,
    "jimat": scene_jimat, "ketawa": scene_ketawa, "ayala": mv.scene_ayala,
}


def render_frame(bg, t):
    frame = bg.copy().convert("RGBA")
    cl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mv.draw_clouds(ImageDraw.Draw(cl), t)
    frame = Image.alpha_composite(frame, cl)
    for name, t0, t1 in SCENES:
        if not (t0 - 0.01 <= t < t1 + 0.4):
            continue
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        DISPATCH[name](layer, t, t0, t1)
        if name != SCENES[-1][0] and t > t1 - 0.01:
            fade = 1 - prog(t, t1, 0.4)
            layer.putalpha(layer.getchannel("A").point(lambda v: int(v * fade)))
        frame = Image.alpha_composite(frame, layer)
    k = min(prog(t, 0, 0.4), 1 - prog(t, DURATION - 0.6, 0.6))
    if k < 1:
        frame = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), frame, k)
    return frame.convert("RGB")


# ---------------------------------------------------------------- audio
SR = 44100


def make_audio(path):
    n = int(SR * DURATION)
    music = np.zeros(n)
    sfx = np.zeros(n)
    bpm = 112
    beat = 60 / bpm

    def note(buf, freq, start, dur, vol, kind="pluck"):
        s = int(start * SR)
        m = min(int(dur * SR), n - s)
        if m <= 0 or s < 0:
            return
        tt = np.arange(m) / SR
        if kind == "pluck":
            env = np.exp(-tt * 7) * np.minimum(1, tt * 200)
            w = np.sin(2 * np.pi * freq * tt) + 0.3 * np.sin(4 * np.pi * freq * tt)
        else:
            env = np.minimum(1, tt * 4) * np.minimum(1, (dur - tt) * 4)
            w = np.sin(2 * np.pi * freq * tt) + 0.5 * np.sin(2 * np.pi * freq * 1.005 * tt)
        buf[s:s + m] += vol * env * w

    def hz(midi):
        return 440 * 2 ** ((midi - 69) / 12)

    # muzik nakal/lucu: F - Dm - Bb - C dengan lompatan staccato
    chords = [(41, [65, 69, 72]), (38, [62, 65, 69]), (46, [62, 65, 70]), (48, [64, 67, 72])]
    t, i, bar = 0.0, 0, 4 * beat
    while t < DURATION:
        root, tri = chords[i % 4]
        note(music, hz(root), t, bar, 0.09, "pad")
        pattern = [0, 2, 1, 2, 0, 2, 1, 3]
        for k in range(8):
            mid = tri[pattern[k] % 3] + (12 if pattern[k] == 3 else 0) + 12
            note(music, hz(mid), t + k * beat / 2, beat * 0.4, 0.07)
        for k in range(4):
            s = int((t + k * beat) * SR)
            m = min(int(0.15 * SR), n - s)
            if m > 0:
                tt = np.arange(m) / SR
                music[s:s + m] += 0.22 * np.sin(2 * np.pi * (110 * np.exp(-tt * 25) + 40) * tt) * np.exp(-tt * 18)
        t += bar
        i += 1

    def whoosh(at):
        s = int(at * SR)
        m = min(int(0.35 * SR), n - s)
        tt = np.arange(m) / SR
        sfx[s:s + m] += 0.12 * np.random.default_rng(3).standard_normal(m) * np.sin(np.pi * tt / 0.35)

    def ding(at):
        note(sfx, hz(84), at, 0.6, 0.18)
        note(sfx, hz(91), at + 0.08, 0.6, 0.12)

    def pop(at, pitch):
        s = int(at * SR)
        m = min(int(0.12 * SR), n - s)
        tt = np.arange(m) / SR
        f = pitch * (1 + 2 * np.exp(-tt * 40))
        sfx[s:s + m] += 0.25 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 30)

    def boing(at):
        s = int(at * SR)
        m = min(int(0.5 * SR), n - s)
        tt = np.arange(m) / SR
        f = 180 + 120 * np.sin(2 * np.pi * 9 * tt) * np.exp(-tt * 4)
        sfx[s:s + m] += 0.3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 5)

    for _, t0, _ in SCENES[1:]:
        whoosh(t0)
    ding(T0["intro"] + 0.25)
    boing(T0["kawan"] + 2.2)
    for k in range(10):
        pop(T0["amik"] + STEAL_START + k * STEAL_GAP + 0.38, 500 + k * 60)
    for at in (T0["jimat"] + 1.3, T0["jimat"] + 3.5):
        ding(at)
    boing(T0["ketawa"] + 0.1)
    boing(T0["ketawa"] + 1.0)

    # ducking muzik bila ada suara
    env = np.ones(n)
    for _, at, ln in VO_CLIPS:
        s, e = int(at * SR), min(n, int((at + ln) * SR))
        env[max(0, s - 4000):e + 4000] = 0.35
    env = np.convolve(env, np.ones(4000) / 4000, mode="same")
    out = (music * env + sfx) * 0.5
    for vo_path, at, _ in VO_CLIPS:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", vo_path, "-f", "s16le", "-ac", "1",
                              "-ar", str(SR), "-"], capture_output=True).stdout
        v = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768
        s0 = int(at * SR)
        m = min(len(v), n - s0)
        out[s0:s0 + m] += v[:m] * 1.0
    # TING untuk follow
    at = int((T0["ayala"] + 1.0) * SR)
    m = min(int(1.6 * SR), n - at)
    tt = np.arange(m) / SR
    ting = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * dk)
               for f, a, dk in ((1568, 1.0, 3.0), (3136, 0.45, 5.0), (4704, 0.2, 8.0), (2349, 0.3, 4.0)))
    out[at:at + m] += 0.45 * ting * np.minimum(1, tt * 400)
    fade = int(1.0 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)
    out /= max(1e-9, np.abs(out).max()) / 0.9
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    make_audio(WAV)
    bg = mv.make_background()
    total = int(DURATION * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", WAV,
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(total):
        proc.stdin.write(render_frame(bg, f / FPS).tobytes())
        if f % 150 == 0:
            print(f"frame {f}/{total}", flush=True)
    proc.stdin.close()
    proc.wait()
    os.remove(WAV)
    print("Siap:", OUT)


if __name__ == "__main__":
    if os.environ.get("PREVIEW"):
        bg = mv.make_background()
        for ts in os.environ["PREVIEW"].split(","):
            render_frame(bg, float(ts)).save(os.path.join(HERE, f"_p2_{ts}.png"))
    else:
        main()
