#!/usr/bin/env python3
"""Video TikTok: "MEMBER GOLF CLUB NI BETUL-BETUL JIMAT KE?" (contoh KGRP, Terengganu).

Gaya: motion graphic sinematik - padang golf siluet ikut waktu (subuh/pagi/petang/senja),
buggy & golfer siluet, kamera push-in perlahan, grain filem, vignette, angka kos besar
yang count-up / slam masuk, peralihan whip + flash.

Output: member_vs_nonmember.mp4 (1080x1920, 30fps, 60s).
Guna:  python3 make_member_vs.py
Voiceover pilihan dalam voiceover_member/ (lihat VO_CUES); diletak pada masa tetap.
"""
import math
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "member_vs_nonmember.mp4")
WAV = os.path.join(HERE, "_audio_member.wav")
VO_DIR = os.path.join(HERE, "voiceover_member")
SR = 44100
DURATION = 60.0

# ---------------------------------------------------------------- fon & warna
FD = "/usr/share/fonts/opentype/inter/"
F_BLACK = FD + "InterDisplay-Black.otf"
F_XB = FD + "Inter-ExtraBold.otf"
F_BOLD = FD + "Inter-Bold.otf"
F_MED = FD + "Inter-Medium.otf"
F_MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-SemiBold.ttf"
_fc = {}


def fnt(path, size):
    key = (path, int(size))
    if key not in _fc:
        _fc[key] = ImageFont.truetype(path, max(4, int(size)))
    return _fc[key]


WHITE = (255, 255, 255)
GOLD = (255, 196, 60)
GREEN = (70, 210, 120)
TEAL = (60, 190, 210)
RED = (240, 70, 70)
INK = (12, 14, 16)


def rgba(c, a=1.0):
    return tuple(c[:3]) + (int(255 * max(0.0, min(1.0, a))),)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, s, d):
    return clamp((t - s) / d)


def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_io(x):
    return 3 * x * x - 2 * x * x * x


def ease_back(x):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


# ---------------------------------------------------------------- babak (ikut skrip)
SCENES = [
    ("hook", 0.0, 5.0, "dawn"),
    ("member", 5.0, 18.0, "morning"),
    ("member_pm", 18.0, 25.0, "evening"),
    ("non", 25.0, 35.0, "day"),
    ("reveal", 35.0, 48.0, None),
    ("ending", 48.0, 60.0, "sunset"),
]

# (fail, masa mula) - voiceover diletak pada masa tetap ikut skrip
VO_CUES = [
    ("1_hook.mp3", 0.3),
    ("2a_member.mp3", 6.0),
    ("2b_buggy_am.mp3", 12.3),
    ("3_member_pm.mp3", 18.3),
    ("4_non.mp3", 25.3),
    ("5a_reveal.mp3", 35.6),
    ("5b_non.mp3", 43.0),
    ("6a_setahun.mp3", 48.4),
    ("6b_akhir.mp3", 52.3),
]

# ---------------------------------------------------------------- landskap
SKY = {
    "dawn": [(40, 50, 90), (210, 120, 110), (255, 190, 140)],
    "morning": [(70, 140, 210), (150, 200, 235), (230, 235, 220)],
    "day": [(60, 130, 210), (130, 185, 235), (210, 230, 240)],
    "evening": [(60, 70, 120), (230, 140, 80), (255, 200, 120)],
    "sunset": [(35, 30, 70), (200, 80, 70), (255, 170, 80)],
}
SUN = {"dawn": (0.25, 0.36, 70), "morning": (0.8, 0.12, 60), "day": (0.7, 0.08, 55),
       "evening": (0.72, 0.33, 85), "sunset": (0.5, 0.38, 120)}
BW, BH = 1300, 2310  # latar lebih besar untuk push-in kamera
HORIZON = 0.42


def lerp(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def silhouette_col(mode, depth):
    """Warna lapisan siluet: lebih jauh = lebih pudar ke langit."""
    sky_low = SKY[mode][2]
    base = {"dawn": (30, 35, 45), "sunset": (25, 20, 30), "evening": (35, 35, 45)}.get(mode)
    if base is None:
        base = (40, 90, 55)
    return lerp(base, sky_low, depth)


def tree(d, x, y, s, col, kind):
    if kind == "palm":
        d.line((x, y, x + s * 0.15, y - s), fill=col, width=max(3, int(s * 0.06)))
        tx, ty = x + s * 0.15, y - s
        for a in range(0, 360, 45):
            r = math.radians(a)
            ex, ey = tx + math.cos(r) * s * 0.45, ty + math.sin(r) * s * 0.18 + abs(math.cos(r)) * s * 0.15
            d.line((tx, ty, ex, ey), fill=col, width=max(3, int(s * 0.07)))
    else:
        d.rectangle((x - s * 0.04, y - s * 0.5, x + s * 0.04, y), fill=col)
        d.ellipse((x - s * 0.35, y - s * 1.1, x + s * 0.35, y - s * 0.4), fill=col)
        d.ellipse((x - s * 0.25, y - s * 1.3, x + s * 0.2, y - s * 0.8), fill=col)


_BG = {}


def landscape(mode):
    if mode in _BG:
        return _BG[mode]
    img = Image.new("RGB", (BW, BH))
    d = ImageDraw.Draw(img)
    hz = int(BH * HORIZON)
    c0, c1, c2 = SKY[mode]
    for y in range(hz):
        k = y / hz
        col = lerp(c0, c1, k / 0.6) if k < 0.6 else lerp(c1, c2, (k - 0.6) / 0.4)
        d.line((0, y, BW, y), fill=col)
    # matahari + cahaya
    sx, sy, sr = SUN[mode]
    sx, sy = sx * BW, sy * BH
    glow = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for k in range(12, 0, -1):
        r = sr * (1 + k * 0.6)
        gd.ellipse((sx - r, sy - r, sx + r, sy + r), fill=(255, 230, 170, 10))
    gd.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=(255, 245, 210, 255))
    img = Image.alpha_composite(img.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(11)
    # bukit jauh (2 lapis)
    for layer, (amp, off, depth) in enumerate(((60, 90, 0.75), (40, 30, 0.55))):
        pts = [(0, hz)]
        for x in range(0, BW + 1, 20):
            pts.append((x, hz - off - amp * math.sin(x / (230 - layer * 60) + layer) - 20 * math.sin(x / 71)))
        pts.append((BW, hz))
        d.polygon(pts, fill=silhouette_col(mode, depth))
    # barisan pokok di horizon
    tcol = silhouette_col(mode, 0.3)
    x = -20
    while x < BW + 40:
        kind = "palm" if rng.random() < 0.45 else "round"
        tree(d, x, hz + 6, 70 + rng.random() * 70, tcol, kind)
        x += 40 + rng.random() * 60
    # rumput / fairway dengan jalur perspektif
    for y in range(hz, BH):
        k = (y - hz) / (BH - hz)
        band = int(((y - hz) ** 0.8) / 14) % 2
        if mode in ("dawn", "sunset", "evening"):
            base = lerp((30, 60, 40), (60, 90, 50), k) if band else lerp((26, 52, 36), (52, 80, 44), k)
            # pantulan cahaya hangat
            base = lerp(base, SKY[mode][2], 0.12 * (1 - k))
        else:
            base = lerp((70, 150, 75), (60, 160, 70), k) if band else lerp((62, 138, 66), (54, 148, 62), k)
        d.line((0, y, BW, y), fill=base)
    # fairway lebih cerah melengkung ke green
    fw = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fw)
    pts_l, pts_r = [], []
    for k in np.linspace(0, 1, 40):
        y = hz + 25 + (BH - hz) * k
        cx = BW * 0.55 + math.sin(k * 2.2) * 120 * (1 - k)
        half = 60 + 650 * k ** 1.3
        pts_l.append((cx - half, y))
        pts_r.append((cx + half, y))
    fd.polygon(pts_l + pts_r[::-1], fill=(255, 255, 220, 22))
    img = Image.alpha_composite(img, fw)
    d = ImageDraw.Draw(img)
    # green & bendera jauh
    gx, gy = BW * 0.58, hz + 40
    d.ellipse((gx - 90, gy - 14, gx + 90, gy + 14), fill=silhouette_col(mode, 0.15) if mode in ("dawn", "sunset", "evening") else (90, 185, 95))
    d.line((gx + 20, gy, gx + 20, gy - 70), fill=(235, 235, 235), width=3)
    d.polygon([(gx + 20, gy - 70), (gx + 55, gy - 60), (gx + 20, gy - 50)], fill=(220, 50, 50))
    # bunker
    d.ellipse((BW * 0.15, hz + 140, BW * 0.38, hz + 175), fill=lerp((220, 200, 150), SKY[mode][2], 0.3))
    _BG[mode] = img.convert("RGB")
    return _BG[mode]


def camera(mode, lt, dur, zoom0=1.0, zoom1=1.12, pan=(0, 0)):
    """Push-in perlahan: crop landskap & skala ke 1080x1920."""
    bg = landscape(mode)
    k = ease_io(clamp(lt / dur))
    z = zoom0 + (zoom1 - zoom0) * k
    cw, ch = BW / z, BH / z
    cx = BW / 2 + pan[0] * k
    cy = BH / 2 + pan[1] * k
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return bg.resize((W, H), Image.BILINEAR, box=box)


def world_xy(x, y, lt, dur, zoom0=1.0, zoom1=1.12, pan=(0, 0)):
    """Tukar koordinat landskap ke skrin (untuk objek yang ikut kamera)."""
    k = ease_io(clamp(lt / dur))
    z = zoom0 + (zoom1 - zoom0) * k
    cw, ch = BW / z, BH / z
    cx, cy = BW / 2 + pan[0] * k, BH / 2 + pan[1] * k
    sc = W / cw
    return (x - (cx - cw / 2)) * sc, (y - (cy - ch / 2)) * sc, sc


# ---------------------------------------------------------------- siluet golfer & buggy
def limb(d, a, b, w, col):
    d.line((a, b), fill=col, width=int(w))
    r = w / 2
    for p in (a, b):
        d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=col)


def golfer(d, x, y, h, pose, col, ph=0.0, face=1):
    """Golfer siluet. (x, y) = kaki, h = tinggi. pose: stand/address/back/follow/walk."""
    s = h / 100.0
    f = face

    def P(px, py):
        return (x + px * s * f, y - py * s)

    lw = 7 * s
    if pose == "walk":
        sw = math.sin(ph)
        hip = P(0, 50)
        limb(d, hip, P(10 * sw, 26), lw * 1.2, col)
        limb(d, P(10 * sw, 26), P(14 * sw, 0), lw * 1.1, col)
        limb(d, hip, P(-10 * sw, 26), lw * 1.2, col)
        limb(d, P(-10 * sw, 26), P(-14 * sw, 0), lw * 1.1, col)
        sh = P(2, 80)
        d.polygon([P(-7, 50), P(7, 50), P(10, 82), P(-6, 82)], fill=col)
        limb(d, sh, P(-8 * sw, 62), lw, col)
        limb(d, sh, P(8 * sw + 4, 60), lw, col)
        # kayu disandang
        d.line((P(8 * sw + 4, 60), P(30, 95)), fill=col, width=max(2, int(2.2 * s)))
        head = P(3, 90)
    else:
        bend = {"stand": 0, "address": 22, "back": 20, "follow": 8}[pose]
        hip = P(-4 if pose != "stand" else 0, 50)
        stance = 0 if pose == "stand" else 9
        limb(d, hip, P(-stance, 26), lw * 1.2, col)
        limb(d, P(-stance, 26), P(-stance - 2, 0), lw * 1.1, col)
        limb(d, hip, P(stance, 26), lw * 1.2, col)
        limb(d, P(stance, 26), P(stance + 2, 0), lw * 1.1, col)
        sh = P(-4 + bend * 0.7, 80 - bend * 0.25)
        d.polygon([P(-11, 50), P(4, 50), (sh[0] + 7 * s * f, sh[1]), (sh[0] - 8 * s * f, sh[1])], fill=col)
        head = (sh[0] + 4 * s * f, sh[1] - 10 * s)
        if pose == "stand":
            hand = P(6, 52)
            club_end = P(16, 2)
        elif pose == "address":
            hand = P(10, 44)
            club_end = P(30, 1)
        elif pose == "back":
            hand = P(-18, 92)
            club_end = P(-2, 120)
        else:  # follow
            hand = P(-14, 96)
            club_end = P(-44, 78)
        limb(d, sh, hand, lw, col)
        d.line((hand, club_end), fill=col, width=max(2, int(2.4 * s)))
        if pose in ("address", "stand"):
            d.ellipse((club_end[0] - 4 * s, club_end[1] - 2 * s, club_end[0] + 6 * s, club_end[1] + 2 * s), fill=col)
    r = 7.5 * s
    d.ellipse((head[0] - r, head[1] - r, head[0] + r, head[1] + r), fill=col)
    # topi
    d.chord((head[0] - r, head[1] - r * 1.15, head[0] + r, head[1] + r * 0.4), 180, 360, fill=col)
    d.line((head[0], head[1] - r * 0.3, head[0] + r * 1.6 * f, head[1] - r * 0.2), fill=col, width=max(2, int(2.4 * s)))


def buggy(d, x, y, s, col, roof_col=None, wheel_rot=0.0):
    """Buggy golf pandangan sisi. (x, y) = tanah, tengah. s = skala (1 = 300px panjang)."""
    L = 300 * s
    roof_col = roof_col or col
    # roda
    for wx in (x - L * 0.33, x + L * 0.33):
        r = 30 * s
        d.ellipse((wx - r, y - 2 * r, wx + r, y), fill=col)
        cx, cy = wx, y - r
        for k in range(3):
            a = wheel_rot + k * 2.094
            d.line((cx, cy, cx + math.cos(a) * r * 0.6, cy + math.sin(a) * r * 0.6), fill=(90, 90, 90), width=max(1, int(3 * s)))
    # badan
    d.polygon([(x - L * 0.5, y - 40 * s), (x + L * 0.42, y - 40 * s), (x + L * 0.5, y - 70 * s),
               (x + L * 0.45, y - 100 * s), (x + L * 0.1, y - 100 * s), (x - L * 0.05, y - 70 * s),
               (x - L * 0.5, y - 70 * s)], fill=col)
    # tempat duduk
    d.rectangle((x - L * 0.25, y - 120 * s, x - L * 0.05, y - 70 * s), fill=col)
    # tiang & bumbung
    d.line((x + L * 0.36, y - 100 * s, x + L * 0.25, y - 215 * s), fill=col, width=max(2, int(7 * s)))
    d.line((x - L * 0.4, y - 70 * s, x - L * 0.38, y - 215 * s), fill=col, width=max(2, int(7 * s)))
    d.rounded_rectangle((x - L * 0.48, y - 232 * s, x + L * 0.36, y - 212 * s), int(8 * s), fill=roof_col)
    # beg golf di belakang
    d.rounded_rectangle((x - L * 0.56, y - 150 * s, x - L * 0.44, y - 60 * s), int(10 * s), fill=col)
    for k in range(3):
        bx = x - L * 0.54 + k * 10 * s
        d.line((bx, y - 150 * s, bx + 3 * s, y - 175 * s), fill=col, width=max(1, int(4 * s)))


def golf_ball(d, cx, cy, r, a=1.0):
    d.ellipse((cx - r + r * 0.1, cy - r + r * 0.2, cx + r + r * 0.1, cy + r + r * 0.2), fill=(0, 0, 0, int(70 * a)))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(WHITE, a), outline=rgba((200, 205, 200), a), width=max(1, int(r * 0.05)))
    dr = max(1.5, r * 0.08)
    for i in range(-3, 4):
        for j in range(-3, 4):
            px, py = cx + i * r * 0.27 + (j % 2) * r * 0.135, cy + j * r * 0.25
            if (px - cx) ** 2 + (py - cy) ** 2 < (r * 0.82) ** 2:
                d.ellipse((px - dr, py - dr, px + dr, py + dr), fill=rgba((218, 222, 218), a))
    # kilauan
    d.ellipse((cx - r * 0.55, cy - r * 0.65, cx - r * 0.1, cy - r * 0.3), fill=rgba(WHITE, a * 0.9))


# ---------------------------------------------------------------- tipografi gerak
def text_w(d, txt, f):
    return d.textlength(txt, font=f)


def slam(layer, xy, txt, size, col, p, font=F_BLACK, stroke=0, anchor="mm", shadow=True):
    """Teks besar 'slam' - mula besar & kabur, mampat ke saiz sebenar."""
    if p <= 0:
        return
    k = ease_out(p)
    sc = 1 + 0.6 * (1 - k)
    f = fnt(font, size * sc)
    d = ImageDraw.Draw(layer)
    a = clamp(p * 2.5)
    if shadow:
        d.text((xy[0] + 6, xy[1] + 8), txt, font=f, fill=(0, 0, 0, int(140 * a)), anchor=anchor)
    d.text(xy, txt, font=f, fill=rgba(col, a), anchor=anchor, stroke_width=stroke, stroke_fill=rgba(INK, a))


def slide(layer, xy, txt, size, col, p, font=F_XB, dx=-120, anchor="mm"):
    if p <= 0:
        return
    k = ease_out(p)
    d = ImageDraw.Draw(layer)
    a = clamp(p * 2)
    x = xy[0] + dx * (1 - k)
    f = fnt(font, size)
    d.text((x + 4, xy[1] + 6), txt, font=f, fill=(0, 0, 0, int(120 * a)), anchor=anchor)
    d.text((x, xy[1]), txt, font=f, fill=rgba(col, a), anchor=anchor)


def label(layer, xy, txt, p, col=GOLD, size=34):
    """Label kecil mono dengan garisan aksen."""
    if p <= 0:
        return
    d = ImageDraw.Draw(layer)
    a = clamp(p * 2)
    f = fnt(F_MONO, size)
    tw = text_w(d, txt, f)
    x, y = xy
    lw = 60 * ease_out(p)
    d.line((x - tw / 2 - 20 - lw, y, x - tw / 2 - 20, y), fill=rgba(col, a), width=4)
    d.line((x + tw / 2 + 20, y, x + tw / 2 + 20 + lw, y), fill=rgba(col, a), width=4)
    d.text(xy, txt, font=f, fill=rgba(col, a), anchor="mm")


def equation(layer, cx, y, parts, size, gap=26):
    """Persamaan disusun ikut lebar sebenar. parts = [(teks, warna, p), ...]."""
    d = ImageDraw.Draw(layer)
    f = fnt(F_BLACK, size)
    ws = [text_w(d, tx, f) for tx, _, _ in parts]
    total = sum(ws) + gap * (len(parts) - 1)
    x = cx - total / 2
    for (tx, col, p), w in zip(parts, ws):
        slam(layer, (x + w / 2, y), tx, size, col, p)
        x += w + gap


def money(v):
    return f"RM{int(round(v)):,}"


def count_up(t, start, dur, target):
    return target * ease_out(prog(t, start, dur))


def panel(layer, box, a, col=(10, 12, 14), alpha=0.62, radius=36, border=None):
    if a <= 0:
        return
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle(box, radius, fill=rgba(col, alpha * a),
                        outline=rgba(border, a) if border else None, width=4 if border else 0)


def underline(layer, x0, x1, y, p, col=GOLD, w=10):
    if p <= 0:
        return
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((x0, y - w / 2, x0 + (x1 - x0) * ease_out(p), y + w / 2), int(w / 2), fill=rgba(col))


def darken(layer, top, bottom, a):
    """Gradien gelap di atas/bawah supaya teks jelas."""
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    for y in range(0, top):
        d.line((0, y, W, y), fill=(0, 0, 0, int(a * 200 * (1 - y / top) ** 1.2)))
    for y in range(H - bottom, H):
        k = (y - (H - bottom)) / bottom
        d.line((0, y, W, y), fill=(0, 0, 0, int(a * 210 * k ** 1.2)))
    under = layer.copy()
    layer.paste((0, 0, 0, 0), (0, 0, W, H))
    layer.alpha_composite(g)
    layer.alpha_composite(under)


# ---------------------------------------------------------------- kesan sinematik
_GRAIN = None
_VIG = None


def grain(f):
    global _GRAIN
    if _GRAIN is None:
        rng = np.random.default_rng(3)
        _GRAIN = []
        for _ in range(6):
            n = rng.normal(128, 40, (H // 2, W // 2)).clip(0, 255).astype(np.uint8)
            g = Image.fromarray(n, "L").resize((W, H), Image.NEAREST)
            _GRAIN.append(g)
    return _GRAIN[f % 6]


def vignette():
    global _VIG
    if _VIG is None:
        yy, xx = np.mgrid[0:H, 0:W]
        r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2)
        a = (np.clip(r - 0.45, 0, 1) ** 1.5 * 320).clip(0, 200).astype(np.uint8)
        _VIG = Image.fromarray(np.dstack([np.zeros_like(a)] * 3 + [a]), "RGBA")
    return _VIG


def finish(frame, t):
    f = int(t * FPS)
    frame = frame.convert("RGB")
    # grain filem (overlay ringan)
    arr = np.asarray(frame).astype(np.int16)
    g = np.asarray(grain(f)).astype(np.int16) - 128
    arr = np.clip(arr + (g[..., None] * 0.09), 0, 255).astype(np.uint8)
    frame = Image.fromarray(arr, "RGB").convert("RGBA")
    frame.alpha_composite(vignette())
    # flash putih + whip pada pertukaran babak
    for _, t0, _, _ in SCENES[1:]:
        dt = t - t0
        if -0.12 < dt < 0.22:
            a = (1 - abs(dt) / 0.22) * 0.75 if dt >= 0 else (1 + dt / 0.12) * 0.4
            frame = Image.blend(frame, Image.new("RGBA", (W, H), (255, 250, 240, 255)), clamp(a))
    k = min(prog(t, 0, 0.3), 1 - prog(t, DURATION - 0.6, 0.6))
    if k < 1:
        frame = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), frame, k)
    return frame.convert("RGB")


def whip_in(layer, lt):
    """Gelincir masuk mendatar dengan motion blur di awal babak."""
    p = prog(lt, 0, 0.22)
    if p >= 1:
        return layer
    off = int((1 - ease_out(p)) * W * 0.5)
    shifted = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shifted.alpha_composite(layer, (off, 0))
    return shifted.filter(ImageFilter.BoxBlur(int(18 * (1 - p)) + 1)) if p < 0.9 else shifted


# ---------------------------------------------------------------- babak
def scene_hook(t, lt, dur):
    Z = dict(zoom0=1.05, zoom1=1.2, pan=(60, 120))
    frame = camera("dawn", lt, dur, **Z).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    gy = BH * 0.66
    # buggy masuk & berhenti
    bp = ease_out(prog(lt, 0, 1.4))
    bx = -300 + (BW * 0.28 + 300) * bp
    sx, sy, sc = world_xy(bx, gy, lt, dur, **Z)
    col = (18, 20, 26)
    buggy(d, sx, sy, sc * 1.25, col, wheel_rot=-bx / 30)
    # golfer turun & berjalan ke tee, kemudian address
    gp = prog(lt, 1.5, 1.4)
    if lt > 1.4:
        wx = BW * 0.36 + (BW * 0.66 - BW * 0.36) * ease_io(gp)
        gx, gyy, gsc = world_xy(wx, gy + 10, lt, dur, **Z)
        pose = "walk" if gp < 1 else ("address" if lt < 4.2 else "back")
        golfer(d, gx, gyy, 330 * gsc, pose, col, ph=lt * 9, face=1)
        if gp >= 1:
            tx, ty, tsc = world_xy(BW * 0.66 + 115, gy + 10, lt, dur, **Z)
            d.line((tx, ty, tx, ty - 10 * tsc), fill=(240, 240, 240), width=max(2, int(4 * tsc)))
            golf_ball(d, tx, ty - 10 * tsc - 9 * tsc, 9 * tsc)
    darken(lay, 900, 300, 1.0)
    slam(lay, (W / 2, 330), "MEMBER", 150, WHITE, prog(lt, 0.9, 0.35))
    slam(lay, (W / 2, 470), "VS", 110, GOLD, prog(lt, 1.15, 0.35))
    slam(lay, (W / 2, 600), "NON-MEMBER", 130, WHITE, prog(lt, 1.4, 0.35))
    p = prog(lt, 2.4, 0.4)
    if p > 0:
        panel(lay, (150, 700, 930, 820), p, col=GOLD, alpha=0.95, radius=20)
        slam(lay, (W / 2, 760), "SIAPA LEBIH JIMAT?", 66, INK, p, font=F_BLACK, shadow=False)
    frame.alpha_composite(lay)
    return frame


def membership_card(lay, cx, cy, w, p, tilt, t):
    """Kad keahlian emas berkilat."""
    if p <= 0:
        return
    h = w * 0.62
    card = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    for y in range(int(h)):
        k = y / h
        cd.line((0, y, w, y), fill=lerp((60, 50, 25), (25, 22, 14), k) + (255,))
    cd.rounded_rectangle((0, 0, w - 1, h - 1), 34, outline=(220, 180, 80, 255), width=5)
    m = Image.new("L", card.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), 34, fill=255)
    card.putalpha(m)
    # kilauan bergerak
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sxp = (t * 500) % (w * 2.5) - w * 0.5
    sd.polygon([(sxp, 0), (sxp + 80, 0), (sxp - 60, h), (sxp - 140, h)], fill=(255, 240, 200, 60))
    card.alpha_composite(Image.composite(sh, Image.new("RGBA", card.size, (0, 0, 0, 0)), m))
    cd = ImageDraw.Draw(card)
    cd.text((44, 60), "GOLF CLUB", font=fnt(F_MONO, 30), fill=(230, 195, 110, 255), anchor="lm")
    cd.text((44, 130), "MEMBERSHIP", font=fnt(F_BLACK, 72), fill=(255, 225, 150, 255), anchor="lm")
    # cip
    cd.rounded_rectangle((44, 190, 134, 255), 12, fill=(210, 170, 80, 255))
    cd.line((44, 222, 134, 222), fill=(150, 115, 40, 255), width=3)
    cd.line((89, 190, 89, 255), fill=(150, 115, 40, 255), width=3)
    cd.text((44, h - 60), "•••• •••• 2026", font=fnt(F_MONO, 34), fill=(230, 210, 160, 255), anchor="lm")
    # bola golf kecil
    golf_ball(cd, w - 100, h - 100, 50)
    s = max(0.05, ease_back(p))
    card = card.resize((max(1, int(w * s)), max(1, int(h * s))), Image.BICUBIC).rotate(tilt, expand=True, resample=Image.BICUBIC)
    lay.alpha_composite(card, (int(cx - card.width / 2), int(cy - card.height / 2)))


def scene_member(t, lt, dur):
    frame = camera("morning", lt, dur, 1.0, 1.15, (-80, 60)).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rectangle((0, 0, W, H), fill=(0, 0, 0, 90))
    darken(lay, 700, 700, 1.0)
    label(lay, (W / 2, 200), "CONTOH: KGRP, TERENGGANU", prog(lt, 0.2, 0.4))

    # bahagian 1: kad keahlian + RM140/bulan (0 - 4.5)
    p1_out = 1 - prog(lt, 6.8, 0.3)
    if p1_out > 0:
        membership_card(lay, W / 2 + (1 - p1_out) * -W, 640, 760, prog(lt, 0.3, 0.6), -6 + math.sin(lt * 1.5) * 2, t)
        v = count_up(t, 5.0 + 1.4, 1.0, 140)
        slide(lay, (W / 2 + (1 - p1_out) * -W, 1060), "MEMBERSHIP", 70, WHITE, prog(lt, 1.2, 0.4))
        slam(lay, (W / 2 + (1 - p1_out) * -W, 1200), money(v), 190, GOLD, prog(lt, 1.4, 0.3))
        slide(lay, (W / 2 + (1 - p1_out) * -W, 1340), "/ BULAN", 64, WHITE, prog(lt, 2.0, 0.4), dx=120)

    # bahagian 2: buggy pagi RM22 x 4 (4.5 - 9)
    if 6.9 < lt:
        q = lt - 7.0
        out2 = 1 - prog(lt, 10.3, 0.3)
        ox = (1 - ease_out(prog(q, 0, 0.4))) * W + (1 - out2) * -W
        if out2 > 0:
            # buggy kecil bergerak merentasi
            bxx = -200 + ((q * 260) % (W + 400))
            buggy(d, bxx, 900, 1.0, (250, 250, 250), roof_col=(30, 120, 70), wheel_rot=-q * 8)
            label(lay, (W / 2 + ox, 520), "MAIN PAGI · BUGGY SHARING", prog(q, 0.1, 0.4), col=WHITE)
            slam(lay, (W / 2 + ox, 660), "RM22 / ORANG", 96, WHITE, prog(q, 0.4, 0.3))
            slide(lay, (W / 2 + ox, 760), "18 hole", 52, (200, 200, 200), prog(q, 0.7, 0.3))
            # persamaan
            equation(lay, W / 2 + ox, 1180, [("RM22", WHITE, prog(q, 1.4, 0.3)), ("×", GOLD, prog(q, 1.8, 0.3)),
                                             ("4", GOLD, prog(q, 1.8, 0.3)), ("=", WHITE, prog(q, 2.3, 0.3)),
                                             (money(count_up(lt, 9.5, 0.7, 88)), GREEN, prog(q, 2.5, 0.3))], 112)
            slide(lay, (W / 2 + ox, 1300), "4 ROUND SEBULAN", 44, (210, 210, 210), prog(q, 2.0, 0.3))

    # bahagian 3: jumlah RM228 (9 - 13)
    if lt > 10.3:
        q = lt - 10.4
        panel(lay, (90, 560, 990, 1420), prog(q, 0, 0.3), border=GREEN, alpha=0.55)
        label(lay, (W / 2, 640), "MEMBER · PAGI", prog(q, 0.1, 0.3), col=GREEN)
        equation(lay, W / 2, 820, [("RM140", WHITE, prog(q, 0.3, 0.3)), ("+", GOLD, prog(q, 0.6, 0.3)),
                                   ("RM88", WHITE, prog(q, 0.8, 0.3))], 116)
        underline(lay, 180, 900, 920, prog(q, 1.2, 0.4), col=GREEN)
        slam(lay, (W / 2, 1110), money(count_up(lt, 11.8, 0.8, 228)), 230, GREEN, prog(q, 1.4, 0.35))
        slam(lay, (W / 2, 1290), "/ BULAN", 70, WHITE, prog(q, 1.8, 0.3))
    frame.alpha_composite(whip_in(lay, lt))
    return frame


def scene_member_pm(t, lt, dur):
    Z = dict(zoom0=1.08, zoom1=1.2, pan=(40, 80))
    frame = camera("evening", lt, dur, **Z).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    # golfer siluet hayun di kanan bawah
    gx, gy, gsc = world_xy(BW * 0.72, BH * 0.8, lt, dur, **Z)
    pose = "address" if lt < 2.5 else ("back" if lt < 3.2 else "follow")
    golfer(d, gx, gy, 380 * gsc, pose, (16, 16, 22), face=-1)
    darken(lay, 1000, 500, 1.0)
    label(lay, (W / 2, 200), "MEMBER · MAIN PETANG", prog(lt, 0.1, 0.4), col=GOLD)
    slam(lay, (W / 2, 340), "BUGGY RM28 / ORANG", 80, WHITE, prog(lt, 0.4, 0.3))
    equation(lay, W / 2, 540, [("RM28", WHITE, prog(lt, 1.4, 0.3)), ("×", GOLD, prog(lt, 1.7, 0.3)),
                               ("4", GOLD, prog(lt, 1.7, 0.3)), ("=", WHITE, prog(lt, 2.0, 0.3)),
                               (money(count_up(t, 18 + 2.2, 0.6, 112)), TEAL, prog(lt, 2.2, 0.3))], 112)
    p = prog(lt, 3.4, 0.3)
    panel(lay, (110, 680, 970, 1080), p, border=TEAL, alpha=0.55)
    slam(lay, (W / 2, 770), "RM140 + RM112", 84, WHITE, prog(lt, 3.5, 0.3))
    slam(lay, (W / 2, 920), money(count_up(t, 18 + 4.0, 0.7, 252)), 190, TEAL, prog(lt, 4.0, 0.35))
    slam(lay, (W / 2, 1035), "/ BULAN", 56, WHITE, prog(lt, 4.3, 0.3))
    frame.alpha_composite(whip_in(lay, lt))
    return frame


def receipt(lay, cx, top, w, lt, start):
    """Resit kaunter yang 'dicetak' keluar."""
    lines = [("GREEN FEE", "✓"), ("BUGGY", "✓"), ("INSURANCE", "✓")]
    full_h = 520
    h = full_h * ease_out(prog(lt, start, 1.0))
    if h <= 4:
        return
    rc = Image.new("RGBA", (int(w), full_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(rc)
    d.rectangle((0, 0, w, full_h), fill=(250, 248, 240, 255))
    # tepi bergerigi bawah
    for x in range(0, int(w), 30):
        d.polygon([(x, full_h), (x + 15, full_h - 14), (x + 30, full_h)], fill=(0, 0, 0, 0))
    d.text((w / 2, 60), "VISITOR", font=fnt(F_MONO, 40), fill=(40, 40, 40, 255), anchor="mm")
    d.line((40, 100, w - 40, 100), fill=(150, 150, 150, 255), width=2)
    y = 150
    for i, (a, b) in enumerate(lines):
        d.text((50, y), a, font=fnt(F_MONO, 36), fill=(40, 40, 40, 255), anchor="lm")
        d.text((w - 50, y), "✓", font=fnt("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40),
               fill=(40, 140, 70, 255), anchor="rm")
        y += 70
    d.line((40, y - 10, w - 40, y - 10), fill=(150, 150, 150, 255), width=2)
    d.text((50, y + 50), "1 ROUND", font=fnt(F_MONO, 40), fill=(20, 20, 20, 255), anchor="lm")
    d.text((w - 50, y + 50), "±RM109", font=fnt(F_BLACK, 56), fill=(200, 40, 40, 255), anchor="rm")
    crop = rc.crop((0, full_h - int(h), int(w), full_h))
    # bayang
    lay.alpha_composite(Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 90)), (int(cx - w / 2 + 14), int(top + 16)))
    lay.alpha_composite(crop, (int(cx - w / 2), int(top)))


def clubhouse(d, x, y, s, col):
    d.rectangle((x - 260 * s, y - 160 * s, x + 260 * s, y), fill=col)
    d.polygon([(x - 300 * s, y - 160 * s), (x, y - 300 * s), (x + 300 * s, y - 160 * s)], fill=col)
    for k in range(5):
        wx = x - 200 * s + k * 100 * s
        d.rectangle((wx - 25 * s, y - 120 * s, wx + 25 * s, y - 40 * s), fill=(255, 220, 150, 200))


def scene_non(t, lt, dur):
    Z = dict(zoom0=1.0, zoom1=1.1, pan=(-40, 40))
    frame = camera("day", lt, dur, **Z).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx, cy, csc = world_xy(BW * 0.3, BH * 0.47, lt, dur, **Z)
    clubhouse(d, cx, cy, csc * 1.1, (235, 230, 220, 255))
    d.rectangle((0, 0, W, H), fill=(0, 0, 0, 110))
    darken(lay, 700, 600, 1.0)
    label(lay, (W / 2, 200), "NON-MEMBER · VISITOR", prog(lt, 0.1, 0.4), col=RED)
    slam(lay, (W / 2, 330), "BAYAR SETIAP ROUND", 76, WHITE, prog(lt, 0.4, 0.3))
    out1 = 1 - prog(lt, 4.6, 0.3)
    if out1 > 0:
        receipt(lay, W / 2 + (1 - out1) * -W, 440, 640, lt, 0.8)
        slide(lay, (W / 2, 1060), "buggy + green fee + insurance", 44, (230, 230, 230), prog(lt, 2.4, 0.4) * out1)
    if lt > 4.6:
        q = lt - 4.6
        slam(lay, (W / 2, 640), "RM109 × 4 ROUND", 96, WHITE, prog(q, 0.1, 0.3))
        underline(lay, 160, 920, 730, prog(q, 0.8, 0.4), col=RED)
        p = prog(q, 1.4, 0.35)
        shake = math.sin(lt * 60) * 10 * (1 - prog(q, 1.6, 0.5)) if p > 0 else 0
        slam(lay, (W / 2 + shake, 960), money(count_up(lt, 6.0, 0.9, 436)), 260, RED, p)
        slam(lay, (W / 2, 1140), "/ BULAN", 76, WHITE, prog(q, 1.9, 0.3))
    frame.alpha_composite(whip_in(lay, lt))
    return frame


def scene_reveal(t, lt, dur):
    frame = Image.new("RGBA", (W, H), (12, 16, 20, 255))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    # latar: padang sangat gelap di belakang
    bg = camera("sunset", lt, dur, 1.2, 1.3).convert("RGBA")
    frame = Image.blend(frame, bg, 0.28)
    label(lay, (W / 2, 190), "4 ROUND SEBULAN", prog(lt, 0.1, 0.4), col=GOLD)
    slam(lay, (W / 2, 300), "SIAPA MENANG?", 92, WHITE, prog(lt, 0.3, 0.3))
    bars = [("MEMBER", "PAGI", 228, GREEN, 0.9), ("MEMBER", "PETANG", 252, TEAL, 2.0), ("NON-", "MEMBER", 436, RED, 8.0)]
    base_y, top_y = 1350, 560
    maxv = 460
    for i, (l1, l2, v, col, st) in enumerate(bars):
        x = 220 + i * 320
        p = prog(lt, st, 0.9)
        if p <= 0:
            continue
        hh = (base_y - top_y) * (v / maxv) * ease_out(p)
        d.rounded_rectangle((x - 110, base_y - hh, x + 110, base_y), 22, fill=rgba(col, 0.92))
        d.text((x, base_y - hh - 60), money(v * ease_out(p)), font=fnt(F_BLACK, 74), fill=rgba(WHITE), anchor="mm")
        d.text((x, base_y + 55), l1, font=fnt(F_XB, 42), fill=rgba(col), anchor="mm")
        d.text((x, base_y + 105), l2, font=fnt(F_XB, 42), fill=rgba(col), anchor="mm")
    d.line((80, base_y, W - 80, base_y), fill=rgba((200, 200, 200), prog(lt, 0.6, 0.3)), width=4)
    # jimat
    p = prog(lt, 9.8, 0.4)
    if p > 0:
        # anak panah perbandingan
        panel(lay, (90, 1530, 990, 1780), p, col=GOLD, alpha=0.96, radius=30)
        s = max(0.05, ease_back(p))
        slam(lay, (W / 2, 1600), "JIMAT", 62 * s, INK, p, shadow=False)
        slam(lay, (W / 2, 1705), "±RM208 SEBULAN", 90 * s, INK, p, shadow=False)
    frame.alpha_composite(whip_in(lay, lt))
    return frame


def down_arrow(d, cx, cy, s, a, col=GOLD):
    d.rectangle((cx - 14 * s, cy - 50 * s, cx + 14 * s, cy + 5 * s), fill=rgba(col, a))
    d.polygon([(cx - 45 * s, cy), (cx + 45 * s, cy), (cx, cy + 50 * s)], fill=rgba(col, a))


def scene_ending(t, lt, dur):
    Z = dict(zoom0=1.0, zoom1=1.18, pan=(0, -60))
    frame = camera("sunset", lt, dur, **Z).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    # golfer berjalan menuju green (makin kecil = makin jauh)
    k = prog(lt, 0, dur)
    wx = BW * 0.52 + 30 * k
    wy = BH * 0.86 - BH * 0.12 * ease_io(k)
    gx, gy, gsc = world_xy(wx, wy, lt, dur, **Z)
    size = 640 * (1 - 0.4 * ease_io(k))
    # cahaya tepi (rim light) senja supaya siluet nampak
    rim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    golfer(ImageDraw.Draw(rim), gx - 5, gy - 4, size * gsc, "walk", (255, 170, 90, 255), ph=lt * 6, face=1)
    lay.alpha_composite(rim.filter(ImageFilter.GaussianBlur(3)))
    golfer(d, gx, gy, size * gsc, "walk", (14, 12, 18), ph=lt * 6, face=1)
    darken(lay, 1150, 700, 1.0)
    out1 = 1 - prog(lt, 7.2, 0.3)
    if out1 > 0:
        label(lay, (W / 2, 200), "KALAU SETAHUN?", prog(lt, 0.1, 0.4) * out1)
        slam(lay, (W / 2, 330), "48 ROUND SETAHUN", 92, WHITE, prog(lt, 0.8, 0.3) * out1)
        panel(lay, (90, 430, 990, 860), prog(lt, 2.0, 0.3) * out1, alpha=0.6)
        slide(lay, (150, 510), "MEMBER AM", 54, GREEN, prog(lt, 2.2, 0.3) * out1, anchor="lm")
        slide(lay, (930, 510), "±" + money(count_up(lt, 2.4, 0.8, 2736)), 64, WHITE, prog(lt, 2.4, 0.3) * out1, anchor="rm", dx=120)
        slide(lay, (150, 630), "NON-MEMBER", 54, RED, prog(lt, 3.3, 0.3) * out1, anchor="lm")
        slide(lay, (930, 630), "±" + money(count_up(lt, 3.5, 0.8, 5232)), 64, WHITE, prog(lt, 3.5, 0.3) * out1, anchor="rm", dx=120)
        underline(lay, 150, 930, 700, prog(lt, 4.4, 0.4) * out1, col=GOLD, w=6)
        slam(lay, (W / 2, 790), "BEZA ±RM2,496", 100, GOLD, prog(lt, 4.8, 0.35) * out1)
    if lt > 7.3:
        q = lt - 7.3
        slam(lay, (W / 2, 330), "KORANG", 110, WHITE, prog(q, 0.0, 0.3))
        slam(lay, (W / 2, 460), "MEMBER", 120, GREEN, prog(q, 0.3, 0.3))
        slam(lay, (W / 2, 570), "ATAU", 70, WHITE, prog(q, 0.55, 0.3))
        slam(lay, (W / 2, 690), "NON-MEMBER?", 120, RED, prog(q, 0.8, 0.3))
        p = prog(q, 1.3, 0.35)
        if p > 0:
            panel(lay, (260, 790, 820, 900), p, col=GOLD, alpha=0.96, radius=55)
            slam(lay, (W / 2, 845), "COMMENT", 70, INK, p, shadow=False)
            down_arrow(d, W / 2, 970 + abs(math.sin(lt * 5)) * 22, 1.0, p)
    # nota kecil
    a = prog(lt, 7.6, 0.5)
    if a > 0:
        f = fnt(F_MED, 32)
        d.text((W / 2, H - 150), "*Anggaran berdasarkan 4 kali bermain sebulan.", font=f, fill=rgba((230, 230, 230), a * 0.9), anchor="mm")
        d.text((W / 2, H - 105), "Harga sebenar tertakluk kepada kadar semasa kelab.", font=f, fill=rgba((230, 230, 230), a * 0.9), anchor="mm")
    frame.alpha_composite(whip_in(lay, lt))
    return frame


DISPATCH = {"hook": scene_hook, "member": scene_member, "member_pm": scene_member_pm,
            "non": scene_non, "reveal": scene_reveal, "ending": scene_ending}


def render_frame(t):
    for name, t0, t1, _ in SCENES:
        if t0 <= t < t1 or (name == "ending" and t >= t1):
            return finish(DISPATCH[name](t, t - t0, t1 - t0), t)


# ---------------------------------------------------------------- audio
def make_audio(path):
    n = int(SR * DURATION)
    music = np.zeros(n)
    sfx = np.zeros(n)
    rng = np.random.default_rng(1)

    def tone(buf, freq, start, dur, vol, kind="pad"):
        s = int(start * SR)
        m = min(int(dur * SR), n - s)
        if m <= 0 or s < 0:
            return
        tt = np.arange(m) / SR
        if kind == "pad":
            env = np.minimum(1, tt * 1.5) * np.minimum(1, (dur - tt) * 1.5)
            w = sum(np.sin(2 * np.pi * freq * dt * tt) for dt in (1, 1.003, 0.997, 2.001)) / 3
        elif kind == "pluck":
            env = np.exp(-tt * 4) * np.minimum(1, tt * 300)
            w = np.sin(2 * np.pi * freq * tt) + 0.2 * np.sin(6 * np.pi * freq * tt)
        else:  # sub
            env = np.exp(-tt * 3) * np.minimum(1, tt * 200)
            w = np.sin(2 * np.pi * freq * tt)
        buf[s:s + m] += vol * env * w

    def hz(m):
        return 440 * 2 ** ((m - 69) / 12)

    # muzik sinematik: Am - F - C - G, tempo 100, pulse 1/8 + kick
    bpm = 100
    beat = 60 / bpm
    bar = 4 * beat
    prog_ = [(45, [57, 60, 64]), (41, [57, 60, 65]), (48, [55, 60, 64]), (43, [55, 59, 62])]
    t, i = 0.0, 0
    while t < DURATION:
        root, tri = prog_[i % 4]
        tone(music, hz(root - 12), t, bar, 0.12, "pad")
        for nn in tri:
            tone(music, hz(nn), t, bar, 0.035, "pad")
        intensity = 0.5 if t < 5 else 1.0
        for k in range(8):
            tone(music, hz(tri[k % 3] + 12), t + k * beat / 2, beat * 0.5, 0.04 * intensity, "pluck")
        for k in range(4):
            s = int((t + k * beat) * SR)
            m = min(int(0.2 * SR), n - s)
            if m > 0 and t >= 1.0:
                tt = np.arange(m) / SR
                music[s:s + m] += 0.28 * intensity * np.sin(2 * np.pi * (90 * np.exp(-tt * 22) + 38) * tt) * np.exp(-tt * 14)
            s2 = int((t + k * beat + beat / 2) * SR)
            m2 = min(int(0.04 * SR), n - s2)
            if m2 > 0 and t >= 5:
                music[s2:s2 + m2] += 0.04 * rng.standard_normal(m2) * np.exp(-np.arange(m2) / SR * 90)
        t += bar
        i += 1

    def whoosh(at, dur=0.35, vol=0.18):
        s = int(at * SR)
        m = min(int(dur * SR), n - s)
        if m <= 0 or s < 0:
            return
        tt = np.arange(m) / SR
        nz = rng.standard_normal(m)
        # tapis ringkas: purata bergerak berubah
        nz = np.convolve(nz, np.ones(8) / 8, mode="same")
        sfx[s:s + m] += vol * nz * np.sin(np.pi * tt / dur) ** 2 * 3

    def impact(at, vol=0.5):
        s = int(at * SR)
        m = min(int(0.9 * SR), n - s)
        if m <= 0:
            return
        tt = np.arange(m) / SR
        sfx[s:s + m] += vol * np.sin(2 * np.pi * (60 * np.exp(-tt * 6) + 32) * tt) * np.exp(-tt * 4)
        k = min(int(0.05 * SR), m)
        sfx[s:s + k] += vol * 0.5 * rng.standard_normal(k) * np.exp(-np.arange(k) / SR * 60)

    def tick_run(at, dur, vol=0.07):
        k = 0
        while k * 0.05 < dur:
            s = int((at + k * 0.05) * SR)
            m = min(int(0.02 * SR), n - s)
            if m > 0:
                tt = np.arange(m) / SR
                sfx[s:s + m] += vol * np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 250)
            k += 1

    def riser(at, dur, vol=0.12):
        s = int(at * SR)
        m = min(int(dur * SR), n - s)
        tt = np.arange(m) / SR
        f = 200 + 1200 * (tt / dur) ** 2
        sfx[s:s + m] += vol * (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4 + 0.6 * np.convolve(
            rng.standard_normal(m), np.ones(4) / 4, mode="same")) * (tt / dur) ** 2

    def swing(at):  # bunyi hayunan + pukulan bola
        whoosh(at, 0.25, 0.25)
        s = int((at + 0.25) * SR)
        m = int(0.15 * SR)
        tt = np.arange(m) / SR
        sfx[s:s + m] += 0.5 * np.sin(2 * np.pi * 1800 * tt) * np.exp(-tt * 70) + 0.3 * rng.standard_normal(m) * np.exp(-tt * 120)

    for _, t0, _, _ in SCENES[1:]:
        whoosh(t0 - 0.15, 0.4, 0.22)
    # hook
    impact(0.9)
    impact(1.4, 0.35)
    impact(2.4, 0.3)
    swing(4.15)
    # member
    impact(5 + 1.4, 0.4)
    tick_run(5 + 1.4, 1.0)
    impact(5 + 7.0 + 2.5, 0.35)
    tick_run(14.5, 0.7)
    riser(14.8, 1.0)
    impact(5 + 10.4 + 1.4, 0.55)
    tick_run(16.8, 0.8)
    # pm
    swing(18 + 3.0)
    impact(18 + 2.2, 0.35)
    impact(18 + 4.0, 0.5)
    tick_run(22.0, 0.7)
    # non
    impact(25 + 4.7, 0.35)
    riser(29.6, 1.4)
    impact(25 + 6.0, 0.7)
    tick_run(31.0, 0.9)
    # reveal
    for st in (0.9, 2.0, 8.0):
        whoosh(35 + st, 0.6, 0.12)
    impact(35 + 8.9, 0.5)
    riser(43.4, 1.4, 0.14)
    impact(44.8, 0.8)
    # ending
    impact(48 + 0.8, 0.35)
    tick_run(50.4, 0.8)
    tick_run(51.5, 0.8)
    impact(48 + 4.8, 0.55)
    impact(55.3, 0.4)
    impact(56.1, 0.5)

    vo = np.zeros(n)
    have_vo = False
    for fn, at in VO_CUES:
        pth = os.path.join(VO_DIR, fn)
        if not os.path.exists(pth):
            continue
        have_vo = True
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", pth, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                             capture_output=True).stdout
        v = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768
        s0 = int(at * SR)
        m = min(len(v), n - s0)
        vo[s0:s0 + m] += v[:m]
    duck = np.where(np.convolve(np.abs(vo) > 0.01, np.ones(8000), mode="same") > 0, 0.35, 1.0)
    duck = np.convolve(duck, np.ones(6000) / 6000, mode="same")
    out = music * duck * 0.55 + sfx * 0.6 + vo * (1.1 if have_vo else 0)
    fade = int(1.2 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)
    out[:int(0.2 * SR)] *= np.linspace(0, 1, int(0.2 * SR))
    out /= max(1e-9, np.abs(out).max()) / 0.9
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    make_audio(WAV)
    total = int(DURATION * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", WAV,
           "-c:v", "libx264", "-preset", "slow", "-crf", "26", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(total):
        proc.stdin.write(render_frame(f / FPS).tobytes())
        if f % 300 == 0:
            print(f"frame {f}/{total}", flush=True)
    proc.stdin.close()
    proc.wait()
    os.remove(WAV)
    print("Siap:", OUT)


if __name__ == "__main__":
    if os.environ.get("PREVIEW"):
        for ts in os.environ["PREVIEW"].split(","):
            render_frame(float(ts)).save(os.path.join(HERE, f"_m_{ts}.png"))
    else:
        main()
