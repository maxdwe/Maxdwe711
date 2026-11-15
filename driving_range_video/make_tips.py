#!/usr/bin/env python3
"""Video TikTok: 10 TIPS UNTUK FIRST TIMER NAK MASUK PADANG GOLF.

Gaya kad sama seperti Part 3 (make_part3.py): latar krim bersinar, label mono, tajuk hitam
dengan perkataan merah italik, kad besar senget yang terbalik masuk untuk setiap tip,
jalur kemajuan 10 kotak, sepanduk merah, dan hos kartun yang bercakap ikut voiceover.

Output: tips_first_timer.mp4 (1080x1920, 30fps).
Guna:  python3 make_tips.py
Voiceover dalam voiceover_tips/ (00_hook.mp3 ... 11_ending.mp3); babak dipanjangkan ikut
panjang suara jika fail ada.
"""
import math
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw

import make_part3 as p3
import make_member_vs as mm
from make_part3 import (W, H, FPS, PAPER, INK, MUTED, RED, WHITE, F_BOLD, F_XBOLD, F_MED, F_MONO,
                        F_MONO_B, fnt, rgba, clamp, prog, ease_out, ease_back)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tips_first_timer.mp4")
WAV = os.path.join(HERE, "_audio_tips.wav")
VO_DIR = os.path.join(HERE, "voiceover_tips")
VO_START = 0.35
SR = 44100

GREEN = (48, 150, 104)
BLUE = (52, 104, 214)
YELLOW = (226, 168, 40)
PURPLE = (124, 82, 214)
ORANGE = (230, 96, 60)
TEAL = (40, 150, 170)
NAVY = (35, 55, 95)
LEAF = (60, 140, 70)

# nama, tempoh asal, fail suara, tajuk (*merah italik*), teks kad, warna kad, sepanduk, nota
TIPS = [
    ("padang", "01_padang.mp3", "Pilih padang yang *beginner-friendly.*", "Padang Mesra", GREEN,
     "FAIRWAY LUAS", "Kurang kolam & hazard"),
    ("tee", "02_tee.mp3", "Pilih *tee* yang sesuai.", "Tee Sesuai", BLUE,
     "IKUT KEMAMPUAN", "Tak perlu tee belakang"),
    ("kawan", "03_kawan.mp3", "Ajak kawan yang *dah biasa* main.", "Ajak Otai", ORANGE,
     "BELAJAR RULES", "Dan etiquette atas padang"),
    ("jarak", "04_jarak.mp3", "Kenal *jarak club* sendiri.", "Jarak Club", PURPLE,
     "BUKAN 14 CLUB", "Cukup club yang selalu guna"),
    ("bola", "05_bola.mp3", "Bola hilang? *Cari kejap je.*", "Bola Hilang", TEAL,
     "TAK JUMPA? DROP", "Jangan bagi flight belakang tunggu"),
    ("slow", "06_slow.mp3", "Jangan *slow play.*", "Main Laju", YELLOW,
     "FIKIR AWAL", "Pilih club sebelum sampai bola"),
    ("laluan", "07_laluan.mp3", "Flight belakang laju? *Bagi laluan.*", "Bagi Laluan", NAVY,
     "PLAY THROUGH", "Itu etiquette"),
    ("hormat", "08_hormat.mp3", "*Hormat* golfer lain.", "Hormat", RED,
     "SHHH...", "Jangan berdiri dekat line pukulan"),
    ("jaga", "09_jaga.mp3", "*Jaga* padang.", "Jaga Padang", LEAF,
     "REPAIR & RAKE", "Kita guna padang, kita jaga"),
    ("score", "10_score.mp3", "Jangan *kejar score.*", "Enjoy Je", ORANGE,
     "ENJOY GAME", "Fokus belajar & ikut rules"),
]

SCENE_DEFS = [("hook", 6.0, "00_hook.mp3", "// 04 · first timer", "10 TIPS",
               "First time nak masuk *padang golf?* 10 benda ni kau *kena tahu.*", "")]
for i, (nm, fn, head, *_rest) in enumerate(TIPS):
    SCENE_DEFS.append((nm, 6.5, fn, "// 04 · 10 tips first timer", f"TIP {i + 1}/10", head, ""))
SCENE_DEFS.append(("ending", 6.5, "11_ending.mp3", "// 04 · welcome", "10/10 ✓",
                   "Semua golfer pernah jadi *beginner.*", ""))
SCENE_DEFS.append(("welcome", 4.5, None, "// 04 · welcome to golf", "TEAM AYALA",
                   "", ""))

SCENES, VO_CLIPS = [], []
_t = 0.0
for _name, _dur, _fn, _l, _r, _head, _ in SCENE_DEFS:
    _vl = p3.mv._vo_len(os.path.join(VO_DIR, _fn)) if _fn else 0.0
    _d = max(_dur, VO_START + _vl + 0.7) if _vl else _dur
    SCENES.append(dict(name=_name, t0=round(_t, 3), t1=round(_t + _d, 3), vo=_vl, left=_l, right=_r, head=_head))
    if _vl:
        VO_CLIPS.append((os.path.join(VO_DIR, _fn), _t + VO_START, _vl))
    _t += _d
SC = {s["name"]: s for s in SCENES}
DURATION = SCENES[-1]["t1"]
TIP_NAMES = [t[0] for t in TIPS]


# ---------------------------------------------------------------- ilustrasi kad (kawasan 600x330)
def ill_padang(d, ox, oy, w, h, t):
    d.rectangle((ox, oy, ox + w, oy + h * 0.38), fill=(175, 215, 240))
    d.polygon([(ox + w * 0.42, oy + h * 0.38), (ox + w * 0.58, oy + h * 0.38), (ox + w * 0.98, oy + h),
               (ox + w * 0.02, oy + h)], fill=(120, 200, 110))
    d.rectangle((ox, oy + h * 0.38, ox + w, oy + h * 0.42), fill=(70, 150, 70))
    fx, fy = ox + w * 0.5, oy + h * 0.4
    d.line((fx, fy, fx, fy - 70), fill=WHITE, width=5)
    d.polygon([(fx, fy - 70), (fx + 40, fy - 58 + math.sin(t * 6) * 4), (fx, fy - 46)], fill=RED)
    # anak panah "luas"
    ay = oy + h * 0.78
    a = 0.5 + 0.5 * math.sin(t * 4)
    for sgn in (-1, 1):
        x0 = ox + w / 2 + sgn * 60
        x1 = ox + w / 2 + sgn * (200 + 20 * a)
        d.line((x0, ay, x1, ay), fill=WHITE, width=10)
        d.polygon([(x1 + sgn * 22, ay), (x1, ay - 18), (x1, ay + 18)], fill=WHITE)
    d.text((ox + w / 2, ay), "LUAS", font=fnt(F_XBOLD, 34), fill=rgba(INK), anchor="mm")


def ill_tee(d, ox, oy, w, h, t):
    d.rectangle((ox, oy, ox + w, oy + h), fill=(110, 190, 110))
    cols = [(30, 30, 30), BLUE, WHITE, RED]
    names = ["PRO", "", "", "BEGINNER"]
    for i, c in enumerate(cols):
        x = ox + 90 + i * 140
        y = oy + h * 0.62
        bob = -abs(math.sin(t * 5)) * 18 if i == 3 else 0
        d.ellipse((x - 28, y - 28 + bob, x + 28, y + 28 + bob), fill=rgba(c), outline=rgba(INK), width=3)
        if names[i]:
            d.text((x, y + 60), names[i], font=fnt(F_BOLD, 22), fill=rgba(INK), anchor="mm")
    x = ox + 90 + 3 * 140
    y0 = oy + 50 + abs(math.sin(t * 5)) * 10
    d.polygon([(x - 22, y0), (x + 22, y0), (x, y0 + 36)], fill=rgba(YELLOW), outline=rgba(INK))


def ill_kawan(d, ox, oy, w, h, t):
    d.rectangle((ox, oy, ox + w, oy + h), fill=(250, 220, 190))
    mm.golfer(d, ox + w * 0.33, oy + h - 10, 260, "stand", INK, face=1)
    mm.golfer(d, ox + w * 0.62, oy + h - 10, 220, "stand", (90, 90, 90), face=-1)
    bx, by = ox + w * 0.1, oy + 30
    d.rounded_rectangle((bx, by, bx + 210, by + 70), 30, fill=WHITE, outline=INK, width=3)
    d.polygon([(bx + 120, by + 70), (bx + 150, by + 70), (bx + 150, by + 98)], fill=WHITE)
    d.text((bx + 105, by + 35), "ikut aku!", font=fnt(F_BOLD, 30), fill=rgba(INK), anchor="mm")


def ill_jarak(d, ox, oy, w, h, t):
    d.rectangle((ox, oy, ox + w, oy + h), fill=(225, 215, 245))
    # pembaris
    ry = oy + h * 0.72
    d.rectangle((ox + 40, ry - 24, ox + w - 40, ry + 24), fill=YELLOW, outline=INK, width=3)
    for k in range(21):
        x = ox + 40 + k * (w - 80) / 20
        d.line((x, ry - 24, x, ry - (6 if k % 5 else 0)), fill=INK, width=3)
    # bola bergerak sepanjang pembaris
    q = (t * 0.6) % 1
    mm.golf_ball(d, ox + 60 + q * (w - 120), ry - 50, 18)
    # kayu iron
    if _LAYER[0] is not None:
        p3.mv.iron_club(_LAYER[0], ox + 110, oy + 20, 140, -35, 1.0)
    d.text((ox + w * 0.68, oy + h * 0.32), "??? m", font=fnt(F_XBOLD, 64), fill=rgba(INK), anchor="mm")


def ill_bola(d, ox, oy, w, h, t):
    d.rectangle((ox, oy, ox + w, oy + h), fill=(190, 225, 200))
    for (bx, by, r) in ((ox + 120, oy + 220, 90), (ox + 220, oy + 200, 110), (ox + 330, oy + 230, 85)):
        d.ellipse((bx - r, by - r, bx + r, by + r), fill=(40, 110, 50))
    peek = 0.5 + 0.5 * math.sin(t * 3)
    mm.golf_ball(d, ox + 250, oy + 190 - peek * 20, 22)
    # jam randik
    cx, cy, r = ox + w * 0.78, oy + h * 0.45, 80
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE, outline=INK, width=6)
    d.rectangle((cx - 14, cy - r - 24, cx + 14, cy - r), fill=INK)
    ang = t * 3
    d.line((cx, cy, cx + math.sin(ang) * r * 0.75, cy - math.cos(ang) * r * 0.75), fill=RED, width=7)
    d.text((cx, cy + r + 30), "kejap je", font=fnt(F_BOLD, 28), fill=rgba(INK), anchor="mm")


def ill_slow(d, ox, oy, w, h, t):
    d.rectangle((ox, oy, ox + w, oy + h), fill=(250, 235, 180))
    # siput dipangkah
    sx, sy = ox + 170, oy + 200
    d.ellipse((sx - 70, sy - 80, sx + 70, sy + 60), fill=(200, 140, 90), outline=INK, width=4)
    d.arc((sx - 40, sy - 50, sx + 40, sy + 30), 0, 300, fill=INK, width=5)
    d.rounded_rectangle((sx - 120, sy + 30, sx + 110, sy + 70), 20, fill=(150, 190, 120), outline=INK, width=4)
    for sgn in (-1, 1):
        d.line((sx - 120 + 20, sy + 30, sx - 140 + sgn * 15, sy - 20), fill=INK, width=4)
    d.line((sx - 140, sy - 110, sx + 140, sy + 110), fill=RED, width=14)
    d.line((sx - 140, sy + 110, sx + 140, sy - 110), fill=RED, width=14)
    # otak + kayu (fikir awal)
    cx, cy = ox + w * 0.75, oy + h * 0.45
    d.ellipse((cx - 85, cy - 70, cx + 85, cy + 70), fill=WHITE, outline=INK, width=4)
    for k in range(3):
        d.ellipse((cx - 40 + k * 30 - 6, cy + 90 + k * 12, cx - 40 + k * 30 + 6, cy + 102 + k * 12), fill=WHITE)
    d.text((cx, cy), "7 iron?", font=fnt(F_XBOLD, 36), fill=rgba(INK), anchor="mm")


def ill_laluan(d, ox, oy, w, h, t):
    d.rectangle((ox, oy, ox + w, oy + h), fill=(170, 210, 160))
    d.rectangle((ox, oy + h * 0.55, ox + w, oy + h), fill=(150, 195, 140))
    mm.buggy(d, ox + 150, oy + h - 40, 0.8, (60, 60, 70), roof_col=(200, 200, 200))
    q = (t * 0.5) % 1
    bx = ox + 100 + q * (w - 50)
    mm.buggy(d, bx, oy + h - 150, 0.65, (30, 120, 70), roof_col=WHITE, wheel_rot=-t * 10)
    d.arc((ox + 120, oy + 30, ox + w - 60, oy + 230), 200, 340, fill=WHITE, width=10)
    d.polygon([(ox + w - 90, oy + 85), (ox + w - 50, oy + 70), (ox + w - 70, oy + 115)], fill=WHITE)


def ill_hormat(d, ox, oy, w, h, t):
    d.rectangle((ox, oy, ox + w, oy + h), fill=(250, 210, 205))
    cx, cy, r = ox + w * 0.32, oy + h * 0.5, 115
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(240, 200, 160), outline=INK, width=5)
    for ex in (-40, 40):
        d.arc((cx + ex - 18, cy - 30, cx + ex + 18, cy - 5), 200, 340, fill=INK, width=6)
    d.ellipse((cx - 18, cy + 35, cx + 18, cy + 60), fill=(150, 60, 60))
    d.rounded_rectangle((cx - 12, cy + 10, cx + 12, cy + 110), 12, fill=(240, 200, 160), outline=INK, width=4)
    s = 1 + 0.08 * math.sin(t * 6)
    d.text((ox + w * 0.75, oy + h * 0.35), "SHHH", font=fnt(F_XBOLD, int(64 * s)), fill=rgba(INK), anchor="mm")
    mm.golfer(d, ox + w * 0.75, oy + h - 15, 150, "back", INK, face=-1)


def ill_jaga(d, ox, oy, w, h, t):
    d.rectangle((ox, oy, ox + w, oy + h), fill=(205, 230, 190))
    # bunker + rake
    d.ellipse((ox + 30, oy + 170, ox + 300, oy + 300), fill=(235, 215, 160), outline=(200, 180, 120), width=4)
    rx = ox + 160 + math.sin(t * 4) * 30
    d.line((rx, oy + 230, rx + 120, oy + 40), fill=(140, 90, 50), width=12)
    d.rectangle((rx - 70, oy + 225, rx + 70, oy + 245), fill=(90, 90, 90))
    for k in range(8):
        d.line((rx - 65 + k * 19, oy + 245, rx - 65 + k * 19, oy + 270), fill=(90, 90, 90), width=5)
    # divot + tanda bola
    d.rounded_rectangle((ox + 360, oy + 120, ox + 520, oy + 170), 20, fill=(120, 90, 60))
    d.text((ox + 440, oy + 95), "divot", font=fnt(F_BOLD, 26), fill=rgba(INK), anchor="mm")
    d.ellipse((ox + 400, oy + 220, ox + 480, oy + 260), fill=(140, 200, 120), outline=INK, width=3)
    d.text((ox + 440, oy + 290), "ball mark", font=fnt(F_BOLD, 26), fill=rgba(INK), anchor="mm")


def ill_score(d, ox, oy, w, h, t):
    d.rectangle((ox, oy, ox + w, oy + h), fill=(250, 225, 200))
    cx0, cy0 = ox + 40, oy + 40
    d.rectangle((cx0, cy0, cx0 + 300, cy0 + 250), fill=WHITE, outline=INK, width=4)
    for k in range(1, 5):
        d.line((cx0, cy0 + k * 50, cx0 + 300, cy0 + k * 50), fill=(180, 180, 180), width=2)
    d.line((cx0 + 150, cy0, cx0 + 150, cy0 + 250), fill=(180, 180, 180), width=2)
    for k, sc in enumerate(["7", "8", "6", "9", "8"]):
        d.text((cx0 + 225, cy0 + 25 + k * 50), sc, font=fnt(F_BOLD, 32), fill=rgba(INK), anchor="mm")
        d.text((cx0 + 75, cy0 + 25 + k * 50), f"H{k + 1}", font=fnt(F_MONO, 26), fill=rgba(MUTED), anchor="mm")
    d.line((cx0 - 10, cy0 - 10, cx0 + 310, cy0 + 260), fill=RED, width=10)
    # smiley
    cx, cy, r = ox + w * 0.78, oy + h * 0.5, 95 * (1 + 0.05 * math.sin(t * 5))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 205, 60), outline=INK, width=5)
    for ex in (-32, 32):
        d.ellipse((cx + ex - 9, cy - 30, cx + ex + 9, cy - 8), fill=INK)
    d.arc((cx - 55, cy - 30, cx + 55, cy + 55), 20, 160, fill=INK, width=8)


ILLS = [ill_padang, ill_tee, ill_kawan, ill_jarak, ill_bola, ill_slow, ill_laluan, ill_hormat, ill_jaga,
        ill_score]
_LAYER = [None]

# ---------------------------------------------------------------- kad besar
BCW, BCH, TOP_H = 620, 560, 340


def big_card(i, t, revealed):
    pad = 30
    im = Image.new("RGBA", (BCW + pad * 2, BCH + pad * 2), (0, 0, 0, 0))
    im.alpha_composite(p3._halftone_shadow(BCW, BCH, 30), (pad + 16, pad + 18))
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = pad, pad, pad + BCW, pad + BCH
    if revealed:
        _nm, _fn, _head, title, col, _b, _n = TIPS[i]
        d.rounded_rectangle((x0, y0, x1, y1), 30, fill=rgba(WHITE))
        ill = Image.new("RGBA", (BCW, TOP_H), (0, 0, 0, 0))
        _LAYER[0] = ill
        ILLS[i](ImageDraw.Draw(ill), 0, 0, BCW, TOP_H, t)
        _LAYER[0] = None
        mask = Image.new("L", (BCW, TOP_H), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, BCW - 1, TOP_H + 40), 30, fill=255)
        im.paste(ill, (x0, y0), mask)
        d.rectangle((x0, y0 + TOP_H - 8, x1, y0 + TOP_H), fill=rgba(col))
        d.text((x0 + 34, y0 + TOP_H + 60), f"tip {i + 1:02d}", font=fnt(F_MONO, 30), fill=rgba(MUTED), anchor="lm")
        d.text((x0 + 34, y0 + TOP_H + 140), title, font=fnt(F_XBOLD, 70), fill=rgba(INK), anchor="lm")
        d.rounded_rectangle((x1 - 130, y0 + TOP_H + 40, x1 - 34, y0 + TOP_H + 80), 20, fill=rgba(col))
        d.text((x1 - 82, y0 + TOP_H + 60), f"{i + 1}/10", font=fnt(F_MONO_B, 24), fill=rgba(WHITE), anchor="mm")
    else:
        d.rounded_rectangle((x0, y0, x1, y1), 30, fill=rgba((30, 30, 32)))
        d.text(((x0 + x1) / 2, y0 + 200), "?", font=fnt(F_XBOLD, 200), fill=rgba(WHITE), anchor="mm")
        d.text((x0 + 34, y0 + TOP_H + 60), f"tip {i + 1:02d}", font=fnt(F_MONO, 30), fill=rgba((170, 170, 170)), anchor="lm")
        d.text((x0 + 34, y0 + TOP_H + 140), "rahsia", font=fnt(F_XBOLD, 70), fill=rgba(WHITE), anchor="lm")
    d.rounded_rectangle((x0, y0, x1, y1), 30, outline=rgba(INK), width=6)
    return im


def draw_big_card(layer, i, lt, t, cy=770):
    appear = prog(lt, 0.0, 0.35)
    flip = prog(lt, 0.45, 0.5)
    revealed = flip >= 0.5
    sx = abs(1 - 2 * flip) if 0 < flip < 1 else 1.0
    base = big_card(i, t, revealed)
    s = max(0.05, ease_back(appear))
    w = max(1, int(base.width * s * max(0.02, sx)))
    h = max(1, int(base.height * s))
    im = base.resize((w, h), Image.BICUBIC)
    rot = (-4 if i % 2 == 0 else 4) + math.sin(t * 1.5) * 1.0
    im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    drop = (1 - ease_out(appear)) * -300
    if appear < 0.34:
        im.putalpha(im.getchannel("A").point(lambda v: int(v * appear * 3)))
    layer.alpha_composite(im, (int(W / 2 - im.width / 2), int(cy + drop - im.height / 2)))


def progress(d, done, cur, a):
    """10 kotak kecil di bawah label atas."""
    if a <= 0:
        return
    bw, gap = 74, 10
    x0 = W / 2 - (10 * bw + 9 * gap) / 2
    y = 92
    for k in range(10):
        x = x0 + k * (bw + gap)
        if k < done:
            fill = INK
        elif k == cur:
            fill = RED
        else:
            fill = (215, 211, 204)
        d.rounded_rectangle((x, y, x + bw, y + 14), 7, fill=rgba(fill, a))


# ---------------------------------------------------------------- babak khas
def hook_cards(layer, lt, t):
    """10 kad 'rahsia' kecil dalam 2 baris."""
    cw, ch = 170, 210
    for k in range(10):
        r, c = divmod(k, 5)
        x = W / 2 + (c - 2) * (cw + 16)
        y = 700 + r * (ch + 24)
        p = prog(lt, 1.2 + k * 0.08, 0.4)
        if p <= 0:
            continue
        s = max(0.05, ease_back(p))
        im = Image.new("RGBA", (cw + 20, ch + 20), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((12, 14, cw + 12, ch + 14), 18, fill=(0, 0, 0, 60))
        d.rounded_rectangle((4, 4, cw + 4, ch + 4), 18, fill=rgba((30, 30, 32)), outline=rgba(INK), width=4)
        d.text((cw / 2 + 4, 80), str(k + 1), font=fnt(F_XBOLD, 80), fill=rgba(WHITE), anchor="mm")
        d.text((cw / 2 + 4, 170), "tip", font=fnt(F_MONO, 24), fill=rgba((170, 170, 170)), anchor="mm")
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
        im = im.rotate(((k * 37) % 11) - 5, expand=True, resample=Image.BICUBIC)
        layer.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))


def welcome_card(layer, lt):
    p = prog(lt, 0.2, 0.6)
    if p <= 0:
        return
    s = max(0.05, ease_back(p))
    cw, ch = int(880 * s), int(620 * s)
    cx, cy = W // 2, 800
    sh = p3._halftone_shadow(max(1, cw), max(1, ch), 40)
    layer.alpha_composite(sh, (cx - cw // 2 + 16, cy - ch // 2 + 18))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2), int(40 * s),
                        fill=rgba(WHITE), outline=rgba(INK), width=6)
    if p > 0.6:
        a = clamp((p - 0.6) * 3)
        d.text((cx, cy - 200), "WELCOME", font=fnt(F_XBOLD, 120), fill=rgba(INK, a), anchor="mm")
        d.text((cx, cy - 70), "TO GOLF", font=fnt(F_XBOLD, 120), fill=rgba(RED, a), anchor="mm")
        d.line((cx - 330, cy + 40, cx + 330, cy + 40), fill=rgba(INK, a * 0.3), width=3)
        d.text((cx, cy + 120), "Enjoy dulu.", font=fnt(p3.F_SERIF, 76), fill=rgba(RED, a), anchor="mm")
        d.text((cx, cy + 210), "Skill datang kemudian.", font=fnt(F_BOLD, 58), fill=rgba(INK, a), anchor="mm")


# ---------------------------------------------------------------- render
def render_frame(t):
    frame = p3.background(t)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cur = next((s for s in SCENES if s["t0"] <= t < s["t1"]), SCENES[-1])
    lt = t - cur["t0"]
    last = cur is SCENES[-1]
    out_a = 1.0 if last else 1 - prog(t, cur["t1"] - 0.3, 0.3)
    p3.top_labels(d, cur, prog(lt, 0, 0.3) * out_a)
    name = cur["name"]
    if cur["head"]:
        p3.headline(layer, cur, lt, out_a)

    if name == "hook":
        progress(d, 0, -1, prog(lt, 0.8, 0.4) * out_a)
        hook_cards(layer, lt, t)
        if out_a > 0.5:
            p3.banner(layer, 1260 - 120, "JANGAN TERUS TURUN!", prog(lt, 2.4, 0.5))
        p3.host(layer, t, "point")
    elif name in TIP_NAMES:
        i = TIP_NAMES.index(name)
        _nm, _fn, _head, _title, col, ban, nt = TIPS[i]
        progress(d, i, i, out_a)
        draw_big_card(layer, i, lt, t)
        p3.pill(layer, 230, 510, f"TIP {i + 1}", prog(lt, 0.8, 0.4) * out_a, small="first timer")
        p3.sparkle(d, W / 2 + 330, 560 + math.sin(t * 5) * 8, 28, RED, prog(lt, 1.0, 0.3) * out_a)
        p3.sparkle(d, W / 2 - 330, 1030, 18, INK, prog(lt, 1.2, 0.3) * out_a)
        if out_a > 0.5:
            p3.banner(layer, 1120, ban, prog(lt, 1.3, 0.5), col=RED)
        p3.note(d, 1245, nt, prog(lt, 1.8, 0.4) * out_a)
        p3.host(layer, t, "point")
    elif name == "ending":
        progress(d, 10, -1, out_a)
        # 10 kad kecil semua dah ✓
        cw, ch = 170, 120
        for k in range(10):
            r, c = divmod(k, 5)
            x = W / 2 + (c - 2) * (cw + 16)
            y = 560 + r * (ch + 22)
            p = prog(lt, 0.2 + k * 0.06, 0.35) * out_a
            if p <= 0:
                continue
            col = TIPS[k][4]
            d.rounded_rectangle((x - cw / 2 + 8, y - ch / 2 + 10, x + cw / 2 + 8, y + ch / 2 + 10), 16, fill=(0, 0, 0, int(50 * p)))
            d.rounded_rectangle((x - cw / 2, y - ch / 2, x + cw / 2, y + ch / 2), 16, fill=rgba(col, p),
                                outline=rgba(INK, p), width=4)
            d.text((x - 30, y), str(k + 1), font=fnt(F_XBOLD, 56), fill=rgba(WHITE, p), anchor="mm")
            d.ellipse((x + 22, y - 22, x + 66, y + 22), fill=rgba(WHITE, p))
            d.line(((x + 32, y), (x + 41, y + 10), (x + 57, y - 10)), fill=rgba(GREEN, p), width=6)
        if out_a > 0.5:
            p3.banner(layer, 1000, "JANGAN SUSAHKAN", prog(lt, 2.5, 0.5))
        p3.note(d, 1130, "…satu flight! Tak tahu tak apa", prog(lt, 2.8, 0.4) * out_a)
        p3.host(layer, t, "point")
    else:  # welcome
        welcome_card(layer, lt)
        p3.host(layer, t, "wave")
    frame.alpha_composite(layer)
    k = prog(t, 0, 0.35)
    if k < 1:
        frame = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), frame, k)
    return frame.convert("RGB")


# ---------------------------------------------------------------- audio
def build_vo():
    n = int(SR * DURATION)
    vo = np.zeros(n)
    for path, at, _ in VO_CLIPS:
        v = p3.load_vo(path)
        s0 = int(at * SR)
        m = min(len(v), n - s0)
        vo[s0:s0 + m] += v[:m]
    return vo


def set_vo_env(vo):
    spf = SR // FPS
    nf = int(DURATION * FPS) + 1
    env = np.zeros(nf)
    for f in range(nf):
        seg = vo[f * spf:(f + 1) * spf]
        env[f] = np.sqrt(np.mean(seg ** 2)) if len(seg) else 0
    if env.max() > 0:
        env = np.clip(env / (np.percentile(env[env > 0], 90) + 1e-9), 0, 1)
    p3.VO_ENV = np.convolve(env, [0.25, 0.5, 0.25], mode="same")


def make_audio(path, vo):
    n = int(SR * DURATION)
    music = np.zeros(n)
    sfx = np.zeros(n)
    rng = np.random.default_rng(2)
    beat = 60 / 100

    def note(buf, freq, start, dur, vol, kind="pluck"):
        s = int(start * SR)
        m = min(int(dur * SR), n - s)
        if m <= 0 or s < 0:
            return
        tt = np.arange(m) / SR
        if kind == "pluck":
            env = np.exp(-tt * 5) * np.minimum(1, tt * 200)
            w = np.sin(2 * np.pi * freq * tt) + 0.25 * np.sin(4 * np.pi * freq * tt)
        else:
            env = np.minimum(1, tt * 3) * np.minimum(1, (dur - tt) * 3)
            w = np.sin(2 * np.pi * freq * tt) + 0.4 * np.sin(2 * np.pi * freq * 1.004 * tt)
        buf[s:s + m] += vol * env * w

    def hz(m):
        return 440 * 2 ** ((m - 69) / 12)

    # ceria: C - Am - F - G
    chords = [(48, [60, 64, 67, 72]), (45, [57, 60, 64, 69]), (41, [57, 60, 65, 69]), (43, [55, 59, 62, 67])]
    t, i, bar = 0.0, 0, 4 * beat
    while t < DURATION:
        root, tri = chords[i % 4]
        note(music, hz(root), t, bar, 0.08, "pad")
        for k, step in enumerate([0, 2, 1, 3, 2, 1, 3, 2]):
            note(music, hz(tri[step] + 12), t + k * beat / 2, beat, 0.05)
        for k in range(4):
            s = int((t + k * beat) * SR)
            m = min(int(0.15 * SR), n - s)
            if m > 0:
                tt = np.arange(m) / SR
                music[s:s + m] += 0.2 * np.sin(2 * np.pi * (100 * np.exp(-tt * 25) + 40) * tt) * np.exp(-tt * 18)
            s2 = int((t + k * beat + beat / 2) * SR)
            m2 = min(int(0.04 * SR), n - s2)
            if m2 > 0:
                music[s2:s2 + m2] += 0.03 * rng.standard_normal(m2) * np.exp(-np.arange(m2) / SR * 90)
        t += bar
        i += 1

    def whoosh(at):
        s = int(at * SR)
        m = min(int(0.3 * SR), n - s)
        if m <= 0:
            return
        tt = np.arange(m) / SR
        sfx[s:s + m] += 0.1 * rng.standard_normal(m) * np.sin(np.pi * tt / 0.3)

    def pop(at, pitch, vol=0.22):
        s = int(at * SR)
        m = min(int(0.12 * SR), n - s)
        if m <= 0:
            return
        tt = np.arange(m) / SR
        f = pitch * (1 + 2 * np.exp(-tt * 40))
        sfx[s:s + m] += vol * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 30)

    def flip(at):
        s = int(at * SR)
        m = min(int(0.09 * SR), n - s)
        sfx[s:s + m] += 0.18 * rng.standard_normal(m) * np.exp(-np.arange(m) / SR * 50)

    for s in SCENES[1:]:
        whoosh(s["t0"])
    for k in range(10):
        pop(SC["hook"]["t0"] + 1.2 + k * 0.08 + 0.2, 500 + k * 60)
    for nm in TIP_NAMES:
        flip(SC[nm]["t0"] + 0.7)
        pop(SC[nm]["t0"] + 0.9, 900)
        whoosh(SC[nm]["t0"] + 1.3)
    for k in range(10):
        pop(SC["ending"]["t0"] + 0.4 + k * 0.06, 700 + k * 50, 0.15)
    at = int((SC["welcome"]["t0"] + 0.8) * SR)
    m = min(int(1.6 * SR), n - at)
    tt = np.arange(m) / SR
    ting = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * dk)
               for f, a, dk in ((1568, 1.0, 3.0), (3136, 0.45, 5.0), (4704, 0.2, 8.0), (2349, 0.3, 4.0)))
    sfx[at:at + m] += 0.3 * ting * np.minimum(1, tt * 400)

    env = np.ones(n)
    for _, a0, ln in VO_CLIPS:
        s, e = int(a0 * SR), min(n, int((a0 + ln) * SR))
        env[max(0, s - 4000):e + 4000] = 0.3
    env = np.convolve(env, np.ones(4000) / 4000, mode="same")
    out = (music * env + sfx * 0.8) * 0.5 + vo
    fade = int(1.0 * SR)
    out[-fade:] *= np.linspace(1, 0.3, fade)
    out /= max(1e-9, np.abs(out).max()) / 0.9
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    vo = build_vo()
    set_vo_env(vo)
    make_audio(WAV, vo)
    total = int(DURATION * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", WAV,
           "-c:v", "libx264", "-preset", "slow", "-crf", "26", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", OUT]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(total):
        proc.stdin.write(render_frame(f / FPS).tobytes())
        if f % 300 == 0:
            print(f"frame {f}/{total}", flush=True)
    proc.stdin.close()
    proc.wait()
    os.remove(WAV)
    print("Siap:", OUT, f"({DURATION:.1f}s)")


if __name__ == "__main__":
    if os.environ.get("PREVIEW"):
        set_vo_env(build_vo())
        for ts in os.environ["PREVIEW"].split(","):
            render_frame(float(ts)).save(os.path.join(HERE, f"_t_{ts}.png"))
    else:
        main()
