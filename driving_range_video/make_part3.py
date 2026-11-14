#!/usr/bin/env python3
"""Video animasi Part 3: Kos masuk padang - persiapan sebelum masuk.

1. Set golf (second hand RM1000+, kawan let go lagi murah)
2. Bola secondhand
3. Kasut golf (bundle RM40 pun ada)
4. Seluar slack
5. Baju berkolar
Lepas semua ada -> jom masuk padang!

Guna semula gaya & fungsi lukisan dari make_video.py (Part 1).
Output: padang_part3.mp4 (1080x1920, 30fps).

Guna:  python3 make_part3.py
Voiceover pilihan dalam voiceover_part3/ (1_intro.mp3 ... 8_jom.mp3); babak
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
                        card, golf_ball, iron_club)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "padang_part3.mp4")
WAV = os.path.join(HERE, "_audio_part3.wav")
VO_DIR = os.path.join(HERE, "voiceover_part3")
VO_START = 0.3

SCENE_DEFS = [
    ("intro", 5.0, "1_intro.mp3"),
    ("set", 7.0, "2_set.mp3"),
    ("bola", 6.0, "3_bola.mp3"),
    ("kasut", 6.0, "4_kasut.mp3"),
    ("seluar", 5.5, "5_seluar.mp3"),
    ("baju", 6.0, "6_baju.mp3"),
    ("semak", 6.5, "7_semak.mp3"),
    ("jom", 5.5, "8_jom.mp3"),
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

NAVY = (35, 55, 95)
KHAKI = (195, 170, 120)
BROWN = (120, 80, 45)
PINK = (235, 95, 130)

# masa tick dalam babak semak (relatif)
TICK_START, TICK_GAP = 0.6, 0.45
ITEMS = [
    ("Set golf", "RM1,000+"),
    ("Bola secondhand", ""),
    ("Kasut golf", "RM40++"),
    ("Seluar slack", ""),
    ("Baju berkolar", ""),
]


# ---------------------------------------------------------------- lukisan tambahan
def scene_title(layer, lt, num, txt, size=90):
    pop_text(layer, (W // 2, 250), f"{num}. {txt}" if num else txt, size, YELLOW,
             prog(lt, 0, 0.5), stroke=8)


def price_tag(layer, cx, cy, txt, p, col=RED, size=96):
    """Tanda harga senget yang pop masuk."""
    if p <= 0:
        return
    s = max(0.05, ease_back(p))
    f = font(max(4, int(size * s)))
    tw, th = mv.text_size(txt, f)
    tag = Image.new("RGBA", (tw + 140, th + 90), (0, 0, 0, 0))
    td = ImageDraw.Draw(tag)
    a = clamp(p * 3)
    tw2, th2 = tag.size
    td.polygon([(0, th2 / 2), (50, 0), (tw2, 0), (tw2, th2), (50, th2)], fill=with_alpha(col, a))
    td.ellipse((26, th2 / 2 - 12, 50, th2 / 2 + 12), fill=with_alpha(WHITE, a))
    draw_text(td, (50 + (tw2 - 50) / 2, th2 / 2), txt, f, WHITE, a)
    tag = tag.rotate(-8, expand=True, resample=Image.BICUBIC)
    layer.alpha_composite(tag, (int(cx - tag.width / 2), int(cy - tag.height / 2)))


def golf_bag(layer, cx, cy, s, a=1.0, wob=0.0):
    """Beg golf berdiri dengan kayu-kayu terkeluar. (cx, cy) = tengah badan."""
    if a <= 0:
        return
    d = ImageDraw.Draw(layer)
    top = cy - s * 1.1
    # kepala kayu terkeluar dari atas
    heads = [(-0.32, -0.55, "wood", NAVY), (-0.1, -0.75, "iron", None), (0.12, -0.65, "iron", None),
             (0.32, -0.5, "wood", RED)]
    for i, (ox, oy, kind, col) in enumerate(heads):
        x = cx + ox * s + math.sin(wob + i) * 4
        y = top + oy * s
        d.line((x, top + 20, x, y), fill=with_alpha((190, 195, 200), a), width=10)
        if kind == "wood":
            d.ellipse((x - s * 0.13, y - s * 0.13, x + s * 0.13, y + s * 0.09), fill=with_alpha(col, a))
            d.ellipse((x - s * 0.05, y - s * 0.07, x + s * 0.05, y - s * 0.01), fill=with_alpha(WHITE, a * 0.6))
        else:
            d.polygon([(x - 6, y + 10), (x + s * 0.16, y - 2), (x + s * 0.18, y + s * 0.07), (x - 4, y + s * 0.08)],
                      fill=with_alpha((175, 182, 190), a), outline=with_alpha((90, 95, 100), a))
    # badan beg
    d.rounded_rectangle((cx - s * 0.48 + 10, top + 14, cx + s * 0.48 + 10, cy + s * 1.1 + 14), int(s * 0.25),
                        fill=(0, 0, 0, int(60 * a)))
    d.rounded_rectangle((cx - s * 0.48, top, cx + s * 0.48, cy + s * 1.1), int(s * 0.25),
                        fill=with_alpha(GREEN_D, a))
    d.rectangle((cx - s * 0.52, top - 4, cx + s * 0.52, top + s * 0.14), fill=with_alpha(DARK, a))
    # poket & jalur
    d.rounded_rectangle((cx - s * 0.3, cy - s * 0.1, cx + s * 0.3, cy + s * 0.6), int(s * 0.12),
                        fill=with_alpha(GREEN, a), outline=with_alpha(DARK, a), width=4)
    d.line((cx - s * 0.2, cy + s * 0.05, cx + s * 0.2, cy + s * 0.05), fill=with_alpha(DARK, a), width=5)
    d.rectangle((cx - s * 0.48, cy + s * 0.85, cx + s * 0.48, cy + s * 0.95), fill=with_alpha(YELLOW, a))
    # tali
    d.arc((cx - s * 0.9, top + s * 0.1, cx - s * 0.2, cy + s * 0.5), 100, 260, fill=with_alpha(DARK, a), width=10)


def golf_shoe(d, cx, cy, s, a=1.0):
    """Kasut golf pandangan sisi (hujung ke kanan)."""
    if a <= 0:
        return
    # tapak + paku
    d.rounded_rectangle((cx - s, cy + s * 0.25, cx + s * 1.05, cy + s * 0.42), int(s * 0.08),
                        fill=with_alpha(DARK, a))
    for k in range(6):
        x = cx - s * 0.85 + k * s * 0.35
        d.polygon([(x - 10, cy + s * 0.42), (x + 10, cy + s * 0.42), (x, cy + s * 0.55)], fill=with_alpha(GREY, a))
    # badan kasut
    body = [(cx - s, cy + s * 0.27), (cx - s, cy - s * 0.35), (cx - s * 0.75, cy - s * 0.5),
            (cx - s * 0.25, cy - s * 0.45), (cx + s * 0.25, cy - s * 0.15), (cx + s * 0.85, cy - s * 0.02),
            (cx + s * 1.05, cy + s * 0.15), (cx + s * 1.05, cy + s * 0.27)]
    d.polygon(body, fill=with_alpha(WHITE, a), outline=with_alpha((80, 80, 80), a))
    d.line(body + [body[0]], fill=with_alpha((80, 80, 80), a), width=5)
    # saddle (warna) + tali
    d.polygon([(cx - s * 0.5, cy - s * 0.47), (cx - s * 0.2, cy - s * 0.44), (cx + s * 0.2, cy + s * 0.27),
               (cx - s * 0.4, cy + s * 0.27)], fill=with_alpha(BROWN, a))
    for k in range(4):
        x = cx - s * 0.32 + k * s * 0.12
        d.line((x, cy - s * 0.38 + k * s * 0.06, x + s * 0.18, cy - s * 0.3 + k * s * 0.08),
               fill=with_alpha(WHITE, a), width=6)


def slack_pants(d, cx, cy, s, a=1.0, col=NAVY):
    """Seluar slack. (cx, cy) = tengah pinggang."""
    if a <= 0:
        return
    wb = s * 0.55
    d.polygon([(cx - wb, cy), (cx + wb, cy), (cx + wb * 1.08, cy + s * 2.2), (cx + s * 0.08, cy + s * 2.2),
               (cx, cy + s * 0.7), (cx - s * 0.08, cy + s * 2.2), (cx - wb * 1.08, cy + s * 2.2)],
              fill=with_alpha(col, a))
    d.rectangle((cx - wb, cy, cx + wb, cy + s * 0.16), fill=with_alpha(tuple(int(c * 0.7) for c in col), a))
    # tali pinggang
    d.rectangle((cx - wb, cy + s * 0.03, cx + wb, cy + s * 0.12), fill=with_alpha(BROWN, a))
    d.rectangle((cx - s * 0.08, cy + s * 0.01, cx + s * 0.08, cy + s * 0.14), outline=with_alpha(YELLOW, a), width=5)
    lt_ = tuple(int(c + (255 - c) * 0.25) for c in col)
    # garis lipatan (crease)
    for sx in (-1, 1):
        x0 = cx + sx * wb * 0.5
        d.line((x0, cy + s * 0.25, x0 + sx * s * 0.05, cy + s * 2.15), fill=with_alpha(lt_, a), width=4)
    # poket
    d.line((cx - wb * 0.85, cy + s * 0.18, cx - wb * 0.55, cy + s * 0.5), fill=with_alpha(lt_, a), width=4)
    d.line((cx + wb * 0.85, cy + s * 0.18, cx + wb * 0.55, cy + s * 0.5), fill=with_alpha(lt_, a), width=4)


def polo_shirt(d, cx, cy, s, a=1.0, col=PINK):
    """Baju polo berkolar. (cx, cy) = tengah leher."""
    if a <= 0:
        return
    sh = s * 0.75
    body = [(cx - s * 0.25, cy), (cx - sh, cy + s * 0.15), (cx - s * 1.15, cy + s * 0.65), (cx - s * 0.85, cy + s * 0.9),
            (cx - s * 0.62, cy + s * 0.72), (cx - s * 0.62, cy + s * 1.8), (cx + s * 0.62, cy + s * 1.8),
            (cx + s * 0.62, cy + s * 0.72), (cx + s * 0.85, cy + s * 0.9), (cx + s * 1.15, cy + s * 0.65),
            (cx + sh, cy + s * 0.15), (cx + s * 0.25, cy)]
    d.polygon(body, fill=with_alpha(col, a))
    # hujung lengan
    dk = tuple(int(c * 0.8) for c in col)
    d.line((cx - s * 1.15, cy + s * 0.65, cx - s * 0.85, cy + s * 0.9), fill=with_alpha(dk, a), width=14)
    d.line((cx + s * 1.15, cy + s * 0.65, cx + s * 0.85, cy + s * 0.9), fill=with_alpha(dk, a), width=14)
    # placket + butang
    d.rectangle((cx - s * 0.07, cy + s * 0.05, cx + s * 0.07, cy + s * 0.5), fill=with_alpha(dk, a))
    for k in range(3):
        y = cy + s * 0.15 + k * s * 0.13
        d.ellipse((cx - 7, y - 7, cx + 7, y + 7), fill=with_alpha(WHITE, a))
    # KOLAR (putih supaya menonjol)
    d.polygon([(cx - s * 0.3, cy - s * 0.08), (cx, cy + s * 0.12), (cx - s * 0.1, cy + s * 0.32),
               (cx - s * 0.42, cy + s * 0.12)], fill=with_alpha(WHITE, a), outline=with_alpha(GREY, a))
    d.polygon([(cx + s * 0.3, cy - s * 0.08), (cx, cy + s * 0.12), (cx + s * 0.1, cy + s * 0.32),
               (cx + s * 0.42, cy + s * 0.12)], fill=with_alpha(WHITE, a), outline=with_alpha(GREY, a))


def tick(d, cx, cy, r, p, col=GREEN):
    """Bulatan dengan tanda ✓ dilukis mengikut p."""
    if p <= 0:
        return
    rr = r * max(0.05, ease_back(min(1, p * 2)))
    d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=with_alpha(col, clamp(p * 3)))
    q = clamp((p - 0.3) / 0.7)
    a1, a2, a3 = (cx - r * 0.45, cy), (cx - r * 0.1, cy + r * 0.38), (cx + r * 0.5, cy - r * 0.35)
    if q > 0:
        k = min(1, q * 2)
        d.line((a1, (a1[0] + (a2[0] - a1[0]) * k, a1[1] + (a2[1] - a1[1]) * k)), fill=WHITE + (255,), width=int(r * 0.22))
    if q > 0.5:
        k = (q - 0.5) * 2
        d.line((a2, (a2[0] + (a3[0] - a2[0]) * k, a2[1] + (a3[1] - a2[1]) * k)), fill=WHITE + (255,), width=int(r * 0.22))


def cross(d, cx, cy, r, a):
    if a <= 0:
        return
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=with_alpha(RED, a))
    for sx in (-1, 1):
        d.line((cx - r * 0.42, cy - sx * r * 0.42, cx + r * 0.42, cy + sx * r * 0.42), fill=with_alpha(WHITE, a),
               width=int(r * 0.22))


def flag(d, x, y, h, t, a=1.0):
    """Bendera lubang golf berkibar. (x, y) = dasar tiang."""
    if a <= 0:
        return
    d.ellipse((x - 70, y - 18, x + 70, y + 18), fill=with_alpha((30, 90, 40), a))
    d.ellipse((x - 26, y - 9, x + 26, y + 9), fill=with_alpha((15, 25, 15), a))
    d.line((x, y, x, y - h), fill=with_alpha(WHITE, a), width=10)
    pts = []
    for k in range(11):
        u = k / 10
        pts.append((x + u * h * 0.45, y - h + u * 0 + math.sin(t * 6 - u * 4) * 14 * u))
    for k in range(10, -1, -1):
        u = k / 10
        pts.append((x + u * h * 0.45, y - h + h * 0.28 - u * h * 0.06 + math.sin(t * 6 - u * 4) * 14 * u))
    d.polygon(pts, fill=with_alpha(RED, a))


# ---------------------------------------------------------------- babak
def scene_intro(layer, t, t0, t1):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    pop_text(layer, (W // 2, 520), "PART 3", 180, YELLOW, prog(lt, 0.2, 0.5), stroke=12)
    pop_text(layer, (W // 2, 720), "KOS MASUK", 130, WHITE, prog(lt, 0.7, 0.5), stroke=10)
    pop_text(layer, (W // 2, 870), "PADANG", 160, WHITE, prog(lt, 1.0, 0.5), stroke=10)
    a = prog(lt, 1.7, 0.5)
    card(d, (120, 1030, 960, 1250), a, fill=DARK, radius=65)
    draw_text(d, (W // 2, 1100), "Sebelum masuk padang,", font(52), WHITE, a)
    draw_text(d, (W // 2, 1180), "kena siap ni dulu!", font(52), YELLOW, a)
    # bendera muncul di bawah
    p = ease_out(prog(lt, 2.2, 0.6))
    flag(d, W // 2, 1720, 360 * p, lt, p)
    golf_ball(d, W // 2 - 150, 1712, 22, p)


def scene_set(layer, t, t0, t1):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    scene_title(layer, lt, 1, "SET GOLF")
    a = prog(lt, 0.3, 0.5)
    card(d, (70, 380, 1010, 1500), a)
    p = ease_out(prog(lt, 0.5, 0.6))
    golf_bag(layer, 330, 900 + (1 - p) * 300, 260, p, wob=lt * 2)
    draw_text(d, (720, 620), "Second hand", font(58), DARK, prog(lt, 1.0, 0.4))
    draw_text(d, (720, 700), "bermula", font(50, False), GREY, prog(lt, 1.2, 0.4))
    price_tag(layer, 720, 850, "RM1,000+", prog(lt, 1.5, 0.5), col=RED, size=78)
    draw_text(d, (720, 1060), "& ke atas", font(48, False), GREY, prog(lt, 1.8, 0.4))
    a2 = prog(lt, 2.8, 0.5)
    card(d, (70, 1560, 1010, 1790), a2, fill=DARK, radius=60)
    draw_text(d, (W // 2, 1630), "Ada kawan nak let go?", font(54), WHITE, a2)
    draw_text(d, (W // 2, 1720), "Boleh dapat LAGI MURAH!", font(54), YELLOW, a2)


def scene_bola(layer, t, t0, t1):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    scene_title(layer, lt, 2, "BOLA SECONDHAND", size=80)
    a = prog(lt, 0.3, 0.5)
    card(d, (70, 380, 1010, 1500), a)
    # bola-bola jatuh ke dalam kotak (pelbagai warna = bola terpakai campur jenama)
    n = 18
    for i in range(n):
        st = 0.5 + i * 0.08
        q = ease_out(prog(lt, st, 0.45))
        if q <= 0:
            continue
        r_, c_ = divmod(i, 6)
        tx, ty = 270 + c_ * 108, 1010 - r_ * 95
        y = ty - (1 - q) * 500
        golf_ball(d, tx + (r_ % 2) * 30, y, 44, q)
    # kotak
    d.rounded_rectangle((200, 1060, 880, 1200), 24, fill=with_alpha(BROWN, a))
    draw_text(d, (540, 1130), "BOLA TERPAKAI", font(50), WHITE, a)
    pop_text(layer, (W // 2, 1330), "Murah & jimat!", 84, GREEN_D, prog(lt, 2.2, 0.5), stroke=0)
    a2 = prog(lt, 3.0, 0.5)
    card(d, (70, 1560, 1010, 1790), a2, fill=DARK, radius=60)
    draw_text(d, (W // 2, 1630), "Bola masuk lake / semak?", font(52), WHITE, a2)
    draw_text(d, (W // 2, 1720), "Tak sakit hati sangat :)", font(52), YELLOW, a2)


def scene_kasut(layer, t, t0, t1):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    scene_title(layer, lt, 3, "KASUT GOLF")
    a = prog(lt, 0.3, 0.5)
    card(d, (70, 380, 1010, 1500), a)
    p = ease_out(prog(lt, 0.5, 0.7))
    golf_shoe(d, 480 + (1 - p) * -600, 760 - abs(math.sin(lt * 4)) * 20 * p, 300, p)
    draw_text(d, (W // 2, 1050), "Kedai bundle pun ada!", font(60), DARK, prog(lt, 1.2, 0.4))
    price_tag(layer, W // 2, 1250, "RM40", prog(lt, 1.7, 0.5), col=ORANGE, size=120)
    a2 = prog(lt, 2.8, 0.5)
    card(d, (70, 1560, 1010, 1790), a2, fill=DARK, radius=60)
    draw_text(d, (W // 2, 1630), "Tak perlu baru,", font(54), WHITE, a2)
    draw_text(d, (W // 2, 1720), "asalkan selesa & ada grip", font(50), YELLOW, a2)


def scene_seluar(layer, t, t0, t1):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    scene_title(layer, lt, 4, "SELUAR SLACK")
    a = prog(lt, 0.3, 0.5)
    card(d, (70, 380, 1010, 1500), a)
    cols = [NAVY, KHAKI, (60, 60, 65)]
    for i, col in enumerate(cols):
        p = ease_out(prog(lt, 0.5 + i * 0.25, 0.5))
        slack_pants(d, 260 + i * 280, 520 + (1 - p) * 200, 230, p, col)
    a2 = prog(lt, 1.8, 0.4)
    draw_text(d, (W // 2, 1150), "Kemas & sopan", font(66), DARK, a2)
    cross(d, 290, 1330, 50, prog(lt, 2.4, 0.4))
    draw_text(d, (370, 1330), "Jeans / seluar sukan", font(50, False), GREY, prog(lt, 2.4, 0.4), anchor="lm")
    a3 = prog(lt, 3.0, 0.5)
    card(d, (70, 1560, 1010, 1790), a3, fill=DARK, radius=60)
    draw_text(d, (W // 2, 1630), "Slack yang ada kat rumah", font(52), WHITE, a3)
    draw_text(d, (W // 2, 1720), "pun dah boleh pakai!", font(52), YELLOW, a3)


def scene_baju(layer, t, t0, t1):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    scene_title(layer, lt, 5, "BAJU BERKOLAR")
    a = prog(lt, 0.3, 0.5)
    card(d, (70, 380, 1010, 1500), a)
    p = ease_out(prog(lt, 0.5, 0.6))
    s = 260 * max(0.05, ease_back(p))
    polo_shirt(d, W // 2, 520, s, clamp(p * 2))
    # kolar ditunjuk dengan anak panah berdenyut
    ap = prog(lt, 1.4, 0.4)
    if ap > 0:
        k = math.sin(lt * 8) * 10
        d.polygon([(W // 2 + 170 + k, 520), (W // 2 + 240 + k, 480), (W // 2 + 240 + k, 560)], fill=with_alpha(RED, ap))
        d.rectangle((W // 2 + 240 + k, 505, W // 2 + 330 + k, 535), fill=with_alpha(RED, ap))
        draw_text(d, (W // 2 + 360 + k, 445), "KOLAR!", font(46), RED, ap, anchor="mm")
    pop_text(layer, (W // 2, 1100), "Wajib ada kolar", 76, DARK, prog(lt, 1.8, 0.5), stroke=0)
    tick(d, 290, 1290, 50, prog(lt, 2.3, 0.5))
    draw_text(d, (370, 1290), "Baju polo", font(52), DARK, prog(lt, 2.3, 0.4), anchor="lm")
    cross(d, 290, 1410, 50, prog(lt, 2.7, 0.4))
    draw_text(d, (370, 1410), "T-shirt biasa", font(52, False), GREY, prog(lt, 2.7, 0.4), anchor="lm")
    a2 = prog(lt, 3.2, 0.5)
    card(d, (70, 1560, 1010, 1790), a2, fill=DARK, radius=60)
    draw_text(d, (W // 2, 1630), "Ikut dress code padang,", font(52), WHITE, a2)
    draw_text(d, (W // 2, 1720), "nanti kena tegur!", font(52), YELLOW, a2)


def scene_semak(layer, t, t0, t1):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    scene_title(layer, lt, None, "SENARAI SEMAK", size=96)
    a = prog(lt, 0.2, 0.5)
    card(d, (70, 380, 1010, 1560), a)
    y = 500
    for i, (name, note) in enumerate(ITEMS):
        st = TICK_START + i * TICK_GAP
        ap = prog(lt, st - 0.2, 0.3)
        d.rounded_rectangle((140, y - 70, 940, y + 70), 30, fill=with_alpha((238, 244, 240), ap))
        tick(d, 220, y, 48, prog(lt, st, 0.45))
        draw_text(d, (300, y), name, font(54), DARK, ap, anchor="lm")
        if note:
            draw_text(d, (910, y), note, font(46), RED, ap, anchor="rm")
        y += 190
    pop_text(layer, (W // 2, 1660), "SEMUA DAH ADA?", 90, WHITE, prog(lt, TICK_START + 5 * TICK_GAP + 0.3, 0.5),
             stroke=8)


def scene_jom(layer, t, t0, t1):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    # green padang bulat dengan bendera
    p = ease_out(prog(lt, 0.0, 0.6))
    gw, gh = 900 * p, 320 * p
    d.ellipse((W // 2 - gw / 2, 1450 - gh / 2, W // 2 + gw / 2, 1450 + gh / 2), fill=with_alpha((80, 200, 95), p))
    flag(d, W // 2 + 150, 1460, 320 * p, lt, p)
    # bola bergolek masuk lubang
    q = prog(lt, 1.6, 1.4)
    if 0 < q < 1:
        bx = 150 + (W // 2 + 150 - 150) * ease_out(q)
        golf_ball(d, bx, 1450 - 8, 26)
    if q >= 1:
        pop_text(layer, (W // 2 - 120, 1330), "MASUK!", 64, YELLOW, prog(lt, 3.0, 0.4), stroke=6)
    pop_text(layer, (W // 2, 520), "DAH SIAP?", 130, WHITE, prog(lt, 0.3, 0.5), stroke=10)
    pop_text(layer, (W // 2, 700), "JOM MASUK", 140, YELLOW, prog(lt, 0.7, 0.5), stroke=10)
    pop_text(layer, (W // 2, 860), "PADANG!", 170, YELLOW, prog(lt, 1.0, 0.5), stroke=12)
    a = prog(lt, 1.8, 0.5)
    card(d, (170, 1000, 910, 1120), a, fill=DARK, radius=60)
    draw_text(d, (W // 2, 1060), "Kos green fee? Next video!", font(46), WHITE, a)


DISPATCH = {
    "intro": scene_intro, "set": scene_set, "bola": scene_bola, "kasut": scene_kasut,
    "seluar": scene_seluar, "baju": scene_baju, "semak": scene_semak, "jom": scene_jom,
    "ayala": mv.scene_ayala,
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
    bpm = 108
    beat = 60 / bpm

    def note(buf, freq, start, dur, vol, kind="pluck"):
        s = int(start * SR)
        m = min(int(dur * SR), n - s)
        if m <= 0 or s < 0:
            return
        tt = np.arange(m) / SR
        if kind == "pluck":
            env = np.exp(-tt * 6) * np.minimum(1, tt * 200)
            w = np.sin(2 * np.pi * freq * tt) + 0.3 * np.sin(4 * np.pi * freq * tt)
        else:
            env = np.minimum(1, tt * 4) * np.minimum(1, (dur - tt) * 4)
            w = np.sin(2 * np.pi * freq * tt) + 0.5 * np.sin(2 * np.pi * freq * 1.005 * tt)
        buf[s:s + m] += vol * env * w

    def hz(midi):
        return 440 * 2 ** ((midi - 69) / 12)

    # muzik ceria: G - Em - C - D
    chords = [(43, [67, 71, 74]), (40, [64, 67, 71]), (48, [64, 67, 72]), (50, [66, 69, 74])]
    t, i, bar = 0.0, 0, 4 * beat
    while t < DURATION:
        root, tri = chords[i % 4]
        note(music, hz(root), t, bar, 0.09, "pad")
        arp = [0, 1, 2, 1, 0, 2, 1, 2]
        for k in range(8):
            note(music, hz(tri[arp[k]] + 12), t + k * beat / 2, beat * 0.8, 0.065)
        for k in range(4):
            s = int((t + k * beat) * SR)
            m = min(int(0.15 * SR), n - s)
            if m > 0:
                tt = np.arange(m) / SR
                music[s:s + m] += 0.22 * np.sin(2 * np.pi * (110 * np.exp(-tt * 25) + 40) * tt) * np.exp(-tt * 18)
            s2 = int((t + k * beat + beat / 2) * SR)
            m2 = min(int(0.05 * SR), n - s2)
            if m2 > 0:
                music[s2:s2 + m2] += 0.035 * np.random.default_rng(k).standard_normal(m2) * np.exp(-np.arange(m2) / SR * 80)
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

    def cash(at):  # ka-ching untuk harga
        note(sfx, hz(88), at, 0.4, 0.15)
        note(sfx, hz(93), at + 0.06, 0.7, 0.15)
        s = int(at * SR)
        m = min(int(0.08 * SR), n - s)
        sfx[s:s + m] += 0.2 * np.random.default_rng(9).standard_normal(m) * np.exp(-np.arange(m) / SR * 60)

    def plop(at):  # bola masuk lubang
        s = int(at * SR)
        m = min(int(0.3 * SR), n - s)
        tt = np.arange(m) / SR
        f = 320 * np.exp(-tt * 6) + 120
        sfx[s:s + m] += 0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 12)

    for _, t0, _ in SCENES[1:]:
        whoosh(t0)
    ding(T0["intro"] + 0.25)
    cash(T0["set"] + 1.5)
    for k in range(18):
        pop(T0["bola"] + 0.5 + k * 0.08 + 0.45, 600 + (k % 6) * 70)
    cash(T0["kasut"] + 1.7)
    ding(T0["seluar"] + 1.8)
    ding(T0["baju"] + 1.8)
    for k in range(5):
        pop(T0["semak"] + TICK_START + k * TICK_GAP + 0.15, 700 + k * 90)
    ding(T0["semak"] + TICK_START + 5 * TICK_GAP + 0.3)
    plop(T0["jom"] + 3.0)
    ding(T0["jom"] + 3.0)

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
            render_frame(bg, float(ts)).save(os.path.join(HERE, f"_p3_{ts}.png"))
    else:
        main()
