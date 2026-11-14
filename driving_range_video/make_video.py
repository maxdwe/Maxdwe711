#!/usr/bin/env python3
"""Video animasi: Kos Driving Range Sebulan.

Jana frame dengan Pillow, muzik latar dengan numpy, gabung dengan ffmpeg.
Output: driving_range_kos_sebulan.mp4 (1080x1920, 30fps, menegak untuk TikTok/Reels).

Guna:  python3 make_video.py
"""
import math
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "driving_range_kos_sebulan.mp4")
WAV = os.path.join(HERE, "_audio.wav")

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_fc = {}


def font(size, bold=True):
    key = (size, bold)
    if key not in _fc:
        _fc[key] = ImageFont.truetype(FONT_B if bold else FONT_R, size)
    return _fc[key]


# ---------------------------------------------------------------- warna
DARK = (20, 50, 35)
GREEN = (46, 160, 67)
GREEN_D = (30, 110, 50)
YELLOW = (255, 200, 40)
ORANGE = (245, 130, 40)
RED = (220, 70, 60)
WHITE = (255, 255, 255)
CARD = (255, 255, 255)
GREY = (110, 120, 115)
BLUE = (40, 120, 200)

# ---------------------------------------------------------------- masa babak
# (nama, tempoh asal, fail voiceover). Tempoh dipanjangkan ikut panjang suara.
VO_DIR = os.path.join(HERE, "voiceover")
VO_START = 0.3  # suara mula 0.3s selepas babak bermula
SCENE_DEFS = [
    ("intro", 5.0, "1_intro.mp3"),
    ("bola", 6.5, "2_bola.mp3"),
    ("sewa", 6.0, "3_sewa.mp3"),
    ("pinjam", 7.0, "4_pinjam.mp3"),
    ("kira4", 10.0, "5_kira4.mp3"),
    ("kira8", 7.5, "6_kira8.mp3"),
    ("akhir", 5.0, "7_akhir.mp3"),
    ("ayala", 5.0, "8_ayala.mp3"),
]


def _vo_len(fn):
    path = os.path.join(VO_DIR, fn)
    if not os.path.exists(path):
        return 0.0
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


SCENES, VO_CLIPS = [], []
_t = 0.0
for _name, _dur, _fn in SCENE_DEFS:
    _vl = _vo_len(_fn)
    _d = max(_dur, VO_START + _vl + 0.8) if _vl else _dur
    SCENES.append((_name, round(_t, 3), round(_t + _d, 3)))
    if _vl:
        VO_CLIPS.append((os.path.join(VO_DIR, _fn), _t + VO_START))
    _t += _d
SCENE_T0 = {n: a for n, a, _ in SCENES}
DURATION = SCENES[-1][2]


# ---------------------------------------------------------------- utiliti
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, start, dur):
    return clamp((t - start) / dur)


def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_back(x):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def with_alpha(col, a):
    return col[:3] + (int(255 * clamp(a)),)


def text_size(txt, f):
    l, t, r, b = f.getbbox(txt)
    return r - l, b - t


def draw_text(d, xy, txt, f, fill, a=1.0, anchor="mm", stroke=0, stroke_fill=DARK):
    if a <= 0:
        return
    d.text(xy, txt, font=f, fill=with_alpha(fill, a), anchor=anchor,
           stroke_width=stroke, stroke_fill=with_alpha(stroke_fill, a))


def pop_text(layer, xy, txt, size, fill, p, stroke=6, stroke_fill=DARK):
    """Teks yang 'pop' (skala) masuk."""
    if p <= 0:
        return
    s = max(0.05, ease_back(p))
    f = font(max(4, int(size * s)))
    d = ImageDraw.Draw(layer)
    draw_text(d, xy, txt, f, fill, a=clamp(p * 3), stroke=max(1, int(stroke * s)),
              stroke_fill=stroke_fill)


def card(d, box, a=1.0, fill=CARD, radius=40, outline=None):
    if a <= 0:
        return
    x0, y0, x1, y1 = box
    # bayang
    d.rounded_rectangle((x0 + 10, y0 + 14, x1 + 10, y1 + 14), radius,
                        fill=(0, 0, 0, int(60 * a)))
    d.rounded_rectangle(box, radius, fill=with_alpha(fill, a),
                        outline=with_alpha(outline, a) if outline else None,
                        width=6 if outline else 0)


def golf_ball(d, cx, cy, r, a=1.0):
    if a <= 0:
        return
    d.ellipse((cx - r + r * 0.12, cy - r + r * 0.18, cx + r + r * 0.12, cy + r + r * 0.18),
              fill=(0, 0, 0, int(50 * a)))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=with_alpha(WHITE, a),
              outline=with_alpha((200, 205, 200), a), width=max(1, int(r * 0.06)))
    if r >= 14:
        dr = max(1.5, r * 0.09)
        for i in range(-2, 3):
            for j in range(-2, 3):
                px, py = cx + i * r * 0.36 + (j % 2) * r * 0.18, cy + j * r * 0.34
                if (px - cx) ** 2 + (py - cy) ** 2 < (r * 0.78) ** 2:
                    d.ellipse((px - dr, py - dr, px + dr, py + dr),
                              fill=with_alpha((215, 220, 215), a))


def iron_club(layer, cx, cy, length, angle_deg, a=1.0):
    """Kayu golf jenis iron. (cx, cy) = genggaman, berputar mengikut angle."""
    if a <= 0:
        return
    d = ImageDraw.Draw(layer)
    ang = math.radians(angle_deg)
    dx, dy = math.sin(ang), math.cos(ang)
    hx, hy = cx + dx * length, cy + dy * length
    # grip
    gx, gy = cx + dx * length * 0.25, cy + dy * length * 0.25
    d.line((cx, cy, hx, hy), fill=with_alpha((190, 195, 200), a), width=14)
    d.line((cx, cy, gx, gy), fill=with_alpha((30, 30, 30), a), width=26)
    # kepala iron (poligon berputar)
    px, py = -dy, dx  # serenjang
    head = [
        (hx, hy),
        (hx + px * 95, hy + py * 95),
        (hx + px * 105 + dx * 45, hy + py * 105 + dy * 45),
        (hx + px * 10 + dx * 55, hy + py * 10 + dy * 55),
        (hx - px * 12 + dx * 15, hy - py * 12 + dy * 15),
    ]
    d.polygon(head, fill=with_alpha((170, 178, 186), a), outline=with_alpha((90, 95, 100), a))
    for k in range(1, 4):
        y0 = 12 * k
        d.line((hx + px * 20 + dx * y0, hy + py * 20 + dy * y0,
                hx + px * 90 + dx * (y0 + 6), hy + py * 90 + dy * (y0 + 6)),
               fill=with_alpha((120, 128, 135), a), width=3)


def bag_icon(d, cx, cy, s, a=1.0):
    """Ikon beg/kedai (untuk JJJ)."""
    d.rounded_rectangle((cx - s, cy - s * 0.6, cx + s, cy + s), int(s * 0.2),
                        fill=with_alpha(ORANGE, a))
    d.arc((cx - s * 0.5, cy - s * 1.2, cx + s * 0.5, cy - s * 0.1), 180, 360,
          fill=with_alpha(DARK, a), width=int(s * 0.14))


def handshake_icon(d, cx, cy, s, a=1.0):
    """Ikon dua orang (kawan)."""
    for off, col in ((-s * 0.55, BLUE), (s * 0.55, GREEN)):
        d.ellipse((cx + off - s * 0.35, cy - s * 0.9, cx + off + s * 0.35, cy - s * 0.2),
                  fill=with_alpha(col, a))
        d.rounded_rectangle((cx + off - s * 0.55, cy - s * 0.1, cx + off + s * 0.55, cy + s),
                            int(s * 0.3), fill=with_alpha(col, a))


# ---------------------------------------------------------------- latar belakang
def make_background():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    horizon = 760
    for y in range(horizon):
        k = y / horizon
        col = (int(110 + 80 * k), int(185 + 45 * k), int(245 - 10 * k))
        d.line((0, y, W, y), fill=col)
    # bukit jauh
    pts = [(0, horizon)]
    for x in range(0, W + 1, 20):
        pts.append((x, horizon - 60 - 40 * math.sin(x / 170) - 25 * math.sin(x / 61)))
    pts.append((W, horizon))
    d.polygon(pts, fill=(90, 160, 100))
    # rumput dengan jalur perspektif
    for y in range(horizon, H):
        k = (y - horizon) / (H - horizon)
        band = int(((y - horizon) ** 0.75) / 9) % 2
        base = (60, 170, 75) if band else (52, 155, 66)
        col = tuple(int(c * (0.9 + 0.15 * k)) for c in base)
        d.line((0, y, W, y), fill=col)
    # papan jarak
    for x, y, lab, s in ((220, 820, "200m", 0.6), (840, 880, "150m", 0.8), (330, 1000, "100m", 1.0)):
        d.line((x, y, x, y - 90 * s), fill=(240, 240, 240), width=int(6 * s) + 1)
        d.polygon([(x, y - 90 * s), (x + 60 * s, y - 75 * s), (x, y - 60 * s)], fill=RED)
        d.text((x, y + 18 * s), lab, font=font(int(30 * s)), fill=WHITE, anchor="mm")
    # bola-bola bertaburan di padang
    rng = np.random.default_rng(7)
    for _ in range(140):
        y = horizon + 40 + (H - horizon - 40) * rng.random() ** 1.6
        x = rng.random() * W
        r = 2 + 9 * (y - horizon) / (H - horizon)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(245, 245, 245))
    return img


CLOUDS = [(120, 180, 1.0, 18), (650, 120, 0.8, 12), (900, 330, 1.2, 22), (350, 420, 0.7, 9)]


def draw_clouds(d, t):
    for x0, y, s, sp in CLOUDS:
        x = (x0 + t * sp) % (W + 400) - 200
        for ox, oy, r in ((0, 0, 55), (60, -25, 65), (125, 0, 55), (60, 15, 60)):
            rr = r * s
            d.ellipse((x + ox * s - rr, y + oy * s - rr, x + ox * s + rr, y + oy * s + rr),
                      fill=(255, 255, 255, 230))


# ---------------------------------------------------------------- babak
def header(layer, t0, t, txt, y=250, color=YELLOW, size=92):
    pop_text(layer, (W // 2, y), txt, size, color, prog(t, t0, 0.5), stroke=8)


def scene_intro(layer, t, t0, t1):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    # bola terbang mengikut parabola
    p = prog(lt, 0.2, 2.2)
    if 0 < p < 1:
        bx = 120 + p * 900
        by = 1650 - math.sin(p * math.pi) * 1250 - p * 300
        r = 46 - 30 * p
        for k in range(1, 8):  # ekor
            q = max(0, p - k * 0.02)
            tx = 120 + q * 900
            ty = 1650 - math.sin(q * math.pi) * 1250 - q * 300
            rr = r * (1 - k * 0.1)
            d.ellipse((tx - rr, ty - rr, tx + rr, ty + rr), fill=(255, 255, 255, int(110 - k * 14)))
        golf_ball(d, bx, by, r)
    # kayu hayun
    sw = prog(lt, 0.0, 0.35)
    iron_club(layer, 60, 1350, 300, 60 - 110 * ease_out(sw), a=1 - prog(lt, 0.9, 0.4))

    pop_text(layer, (W // 2, 620), "KOS", 150, YELLOW, prog(lt, 0.8, 0.5), stroke=10)
    pop_text(layer, (W // 2, 800), "DRIVING RANGE", 112, WHITE, prog(lt, 1.1, 0.5), stroke=10)
    pop_text(layer, (W // 2, 970), "SEBULAN", 150, YELLOW, prog(lt, 1.4, 0.5), stroke=10)
    a = prog(lt, 2.3, 0.6)
    card(d, (190, 1120, 890, 1250), a, fill=DARK, radius=65)
    draw_text(d, (W // 2, 1185), "Berapa sebenarnya?", font(58), WHITE, a)


def scene_bola(layer, t, t0, t1):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    header(layer, t0, t, "1. BELI BOLA")
    a = prog(lt, 0.3, 0.5)
    card(d, (90, 360, 990, 1560), a)
    draw_text(d, (W // 2, 450), "100 biji bola", font(76), DARK, a)
    # grid 10x10 bola yang terisi
    n = int(100 * ease_out(prog(lt, 0.7, 2.0)))
    gx0, gy0, step = 225, 540, 70
    for i in range(n):
        r, c = divmod(i, 10)
        golf_ball(d, gx0 + c * step, gy0 + r * step, 26)
    draw_text(d, (W // 2, 1290), "=", font(70), GREY, prog(lt, 2.6, 0.3))
    # harga kiraan naik
    pp = ease_out(prog(lt, 2.8, 1.2))
    lo, hi = round(12 * pp), round(15 * pp)
    if pp > 0:
        pop_text(layer, (W // 2, 1400), f"RM{lo} – RM{hi}", 110, GREEN_D, prog(lt, 2.8, 0.5),
                 stroke=0, stroke_fill=WHITE)
    a2 = prog(lt, 4.0, 0.5)
    card(d, (140, 1620, 940, 1740), a2, fill=DARK, radius=60)
    draw_text(d, (W // 2, 1680), "*harga bergantung kepada tempat", font(42, False), WHITE, a2)


def scene_sewa(layer, t, t0, t1):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    header(layer, t0, t, "2. TAKDE IRON?")
    a = prog(lt, 0.3, 0.5)
    card(d, (90, 380, 990, 1500), a)
    # iron berayun ke depan-belakang
    swing = math.sin(lt * 3.0) * 25
    iron_club(layer, W // 2 - 40, 470, 520, swing, a)
    draw_text(d, (W // 2, 1180), "Sewa di range", font(70), DARK, prog(lt, 0.9, 0.4))
    pop_text(layer, (W // 2, 1340), "RM5 / iron", 130, ORANGE, prog(lt, 1.4, 0.5),
             stroke=0)
    a2 = prog(lt, 2.6, 0.5)
    card(d, (140, 1580, 940, 1720), a2, fill=DARK, radius=60)
    draw_text(d, (W // 2, 1650), "Senang, tak payah beli dulu", font(46, False), WHITE, a2)


def scene_pinjam(layer, t, t0, t1):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    header(layer, t0, t, "3. NAK LAGI JIMAT?", size=84)
    # pilihan 1
    p1 = ease_out(prog(lt, 0.5, 0.6))
    x = (1 - p1) * -W
    a1 = p1
    card(d, (90 + x, 400, 990 + x, 940), a1, outline=GREEN)
    handshake_icon(d, 250 + x, 640, 90, a1)
    draw_text(d, (400 + x, 560), "Pinjam iron", font(64), DARK, a1, anchor="lm")
    draw_text(d, (400 + x, 650), "dengan kawan", font(64), DARK, a1, anchor="lm")
    draw_text(d, (400 + x, 780), "RM0", font(110), GREEN_D, a1, anchor="lm")

    draw_text(d, (W // 2, 1020), "ATAU", font(70), WHITE, prog(lt, 1.6, 0.4), stroke=6)

    # pilihan 2
    p2 = ease_out(prog(lt, 2.0, 0.6))
    x = (1 - p2) * W
    a2 = p2
    card(d, (90 + x, 1100, 990 + x, 1640), a2, outline=ORANGE)
    bag_icon(d, 250 + x, 1330, 90, a2)
    draw_text(d, (250 + x, 1360), "JJJ", font(54), WHITE, a2)
    draw_text(d, (400 + x, 1250), "Cari iron", font(64), DARK, a2, anchor="lm")
    draw_text(d, (400 + x, 1340), "terpakai di JJJ", font(60), DARK, a2, anchor="lm")
    draw_text(d, (400 + x, 1460), "Beli sekali,", font(50, False), GREY, a2, anchor="lm")
    draw_text(d, (400 + x, 1530), "guna lama!", font(50, False), GREY, a2, anchor="lm")


def bar_row(layer, y, label, lo, hi, maxv, p, col, a):
    """Satu baris carta bar: julat lo..hi."""
    d = ImageDraw.Draw(layer)
    draw_text(d, (140, y), label, font(48), DARK, a, anchor="lm")
    bx0, bx1, by0, by1 = 140, 940, y + 45, y + 135
    d.rounded_rectangle((bx0, by0, bx1, by1), 25, fill=with_alpha((230, 235, 232), a))
    span = bx1 - bx0
    hi_w = span * (hi / maxv) * ease_out(p)
    lo_w = span * (lo / maxv) * ease_out(p)
    if hi_w > 50:
        d.rounded_rectangle((bx0, by0, bx0 + hi_w, by1), 25, fill=with_alpha(tuple(int(c + (255 - c) * 0.55) for c in col), a))
    if lo_w > 50:
        d.rounded_rectangle((bx0, by0, bx0 + lo_w, by1), 25, fill=with_alpha(col, a))
    v_lo, v_hi = round(lo * ease_out(p)), round(hi * ease_out(p))
    draw_text(d, (bx0 + 30, (by0 + by1) // 2), f"RM{v_lo} – RM{v_hi}", font(54), WHITE,
              a * clamp(p * 4), anchor="lm", stroke=4, stroke_fill=DARK)


def scene_kira(layer, t, t0, t1, sesi, title, sub):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    header(layer, t0, t, title, size=84)
    a = prog(lt, 0.2, 0.5)
    card(d, (60, 340, 1020, 1760), a)
    draw_text(d, (W // 2, 420), sub, font(46, False), GREY, a)

    bola_lo, bola_hi = 12 * sesi, 15 * sesi
    sewa = 5 * sesi
    rows = [
        (0.8, f"Bola: {sesi} x RM12–15", f"= RM{bola_lo} – RM{bola_hi}"),
        (1.6, f"Sewa iron: {sesi} x RM5", f"= RM{sewa}"),
    ]
    y = 520
    for st, l1, l2 in rows:
        ap = prog(lt, st, 0.4)
        draw_text(d, (140, y), l1, font(52), DARK, ap, anchor="lm")
        draw_text(d, (940, y + 70), l2, font(52), GREEN_D, ap, anchor="rm")
        y += 170
    d.line((140, 860, 940, 860), fill=with_alpha((210, 215, 212), a), width=4)

    maxv = (bola_hi + sewa) * 1.08
    bar_row(layer, 920, "Ada iron / pinjam kawan", bola_lo, bola_hi, maxv,
            prog(lt, 2.6, 1.3), GREEN, prog(lt, 2.4, 0.4))
    bar_row(layer, 1130, "Sewa iron di range", bola_lo + sewa, bola_hi + sewa, maxv,
            prog(lt, 3.8, 1.3), ORANGE, prog(lt, 3.6, 0.4))

    ap = prog(lt, 5.4, 0.5)
    pop_text(layer, (W // 2, 1420), "BAJET SEBULAN", 60, DARK, ap, stroke=0)
    pop_text(layer, (W // 2, 1540), f"RM{bola_lo} – RM{bola_hi + sewa}", 108, RED,
             prog(lt, 5.8, 0.5), stroke=0)
    draw_text(d, (W // 2, 1660), "(100 bola setiap sesi)", font(40, False), GREY, prog(lt, 6.2, 0.4))


def scene_akhir(layer, t, t0, t1):
    d = ImageDraw.Draw(layer)
    lt = t - t0
    header(layer, t0, t, "TIPS JIMAT", y=330, size=110)
    tips = [
        (GREEN, "Bandingkan harga bola", "setiap range"),
        (ORANGE, "Pinjam iron kawan", "dulu masa belajar"),
        (BLUE, "Dah serius? Cari iron", "terpakai di JJJ"),
    ]
    y = 520
    for i, (col, l1, l2) in enumerate(tips):
        p = ease_out(prog(lt, 0.4 + i * 0.5, 0.5))
        x = (1 - p) * 300
        card(d, (90 + x, y, 990 + x, y + 230), p)
        d.ellipse((130 + x, y + 55, 250 + x, y + 175), fill=with_alpha(col, p))
        draw_text(d, (190 + x, y + 115), str(i + 1), font(70), WHITE, p)
        draw_text(d, (290 + x, y + 80), l1, font(50), DARK, p, anchor="lm")
        draw_text(d, (290 + x, y + 150), l2, font(50, False), GREY, p, anchor="lm")
        y += 280
    pop_text(layer, (W // 2, 1480), "JOM KE", 100, WHITE, prog(lt, 2.2, 0.5), stroke=8)
    pop_text(layer, (W // 2, 1610), "DRIVING RANGE!", 110, YELLOW, prog(lt, 2.5, 0.5), stroke=8)
    # bola melantun di bawah
    bt = max(0, lt - 2.8)
    if bt > 0:
        bx = 140 + (bt * 260) % 800
        by = 1790 - abs(math.sin(bt * 4)) * 90
        golf_ball(d, bx, by, 32)


_LOGO = None


def scene_ayala(layer, t, t0, t1):
    """Babak penutup: logo Team Ayala + ajakan follow."""
    global _LOGO
    if _LOGO is None:
        _LOGO = Image.open(os.path.join(HERE, "logo_ayala.png")).convert("RGBA")
    d = ImageDraw.Draw(layer)
    lt = t - t0
    # latar gelap menutup padang
    d.rectangle((0, 0, W, H), fill=(15, 30, 22, int(235 * prog(lt, 0, 0.4))))
    # kad putih dengan logo (pop masuk)
    p = prog(lt, 0.2, 0.6)
    if p > 0:
        s = max(0.05, ease_back(p))
        cw, ch = int(820 * s), int(740 * s)
        cx, cy = W // 2, 760
        card(d, (cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2), clamp(p * 3), radius=int(60 * s))
        lw = int(720 * s)
        lh = int(lw * _LOGO.height / _LOGO.width)
        logo = _LOGO.resize((max(1, lw), max(1, lh)), Image.LANCZOS)
        if p < 0.34:
            logo.putalpha(logo.getchannel("A").point(lambda v: int(v * p * 3)))
        layer.alpha_composite(logo, (cx - lw // 2, cy - lh // 2))
    # teks follow, berdenyut sedikit
    pulse = 1 + 0.04 * math.sin(max(0, lt - 1.6) * 6)
    pop_text(layer, (W // 2, 1300), "FOLLOW", int(120 * pulse), WHITE, prog(lt, 0.9, 0.5), stroke=8)
    pop_text(layer, (W // 2, 1450), "TEAM AYALA", int(130 * pulse), YELLOW, prog(lt, 1.2, 0.5), stroke=8)


def render_frame(bg, t):
    frame = bg.copy().convert("RGBA")
    cl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_clouds(ImageDraw.Draw(cl), t)
    frame = Image.alpha_composite(frame, cl)
    for name, t0, t1 in SCENES:
        if not (t0 - 0.01 <= t < t1 + 0.4):
            continue
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if name == "intro":
            scene_intro(layer, t, t0, t1)
        elif name == "bola":
            scene_bola(layer, t, t0, t1)
        elif name == "sewa":
            scene_sewa(layer, t, t0, t1)
        elif name == "pinjam":
            scene_pinjam(layer, t, t0, t1)
        elif name == "kira4":
            scene_kira(layer, t, t0, t1, 4, "KIRAAN SEBULAN",
                       "Main seminggu sekali = 4 sesi")
        elif name == "kira8":
            scene_kira(layer, t, t0, t1, 8, "KALAU 2X SEMINGGU?",
                       "Main 2 kali seminggu = 8 sesi")
        elif name == "akhir":
            scene_akhir(layer, t, t0, t1)
        elif name == "ayala":
            scene_ayala(layer, t, t0, t1)
        # fade keluar di hujung babak (kecuali babak terakhir)
        if name != SCENES[-1][0] and t > t1 - 0.01:
            fade = 1 - prog(t, t1, 0.4)
            alpha = layer.getchannel("A").point(lambda v: int(v * fade))
            layer.putalpha(alpha)
        frame = Image.alpha_composite(frame, layer)
    # fade masuk/keluar keseluruhan
    k = min(prog(t, 0, 0.4), 1 - prog(t, DURATION - 0.6, 0.6))
    if k < 1:
        frame = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), frame, k)
    return frame.convert("RGB")


# ---------------------------------------------------------------- audio
SR = 44100


def make_audio(path):
    n = int(SR * DURATION)
    out = np.zeros(n)
    bpm = 104
    beat = 60 / bpm

    def note(freq, start, dur, vol, kind="pluck"):
        s = int(start * SR)
        m = min(int(dur * SR), n - s)
        if m <= 0:
            return
        tt = np.arange(m) / SR
        if kind == "pluck":
            env = np.exp(-tt * 6) * np.minimum(1, tt * 200)
            w = np.sin(2 * np.pi * freq * tt) + 0.3 * np.sin(4 * np.pi * freq * tt)
        else:  # pad
            env = np.minimum(1, tt * 4) * np.minimum(1, (dur - tt) * 4)
            w = np.sin(2 * np.pi * freq * tt) + 0.5 * np.sin(2 * np.pi * freq * 1.005 * tt)
        out[s:s + m] += vol * env * w

    def hz(midi):
        return 440 * 2 ** ((midi - 69) / 12)

    # progresi C - G - Am - F
    chords = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69])]
    t = 0.0
    bar = 4 * beat
    i = 0
    while t < DURATION:
        root, tri = chords[i % 4]
        note(hz(root), t, bar, 0.10, "pad")
        arp = tri + [tri[1] + 12, tri[2], tri[1] + 12, tri[0] + 12, tri[2]]
        for k in range(8):
            note(hz(arp[k % len(arp)] + 12), t + k * beat / 2, beat * 0.9, 0.07)
        # dram ringan: kick + hi-hat
        for k in range(4):
            s = int((t + k * beat) * SR)
            m = min(int(0.15 * SR), n - s)
            if m > 0:
                tt = np.arange(m) / SR
                out[s:s + m] += 0.25 * np.sin(2 * np.pi * (110 * np.exp(-tt * 25) + 40) * tt) * np.exp(-tt * 18)
            s2 = int((t + k * beat + beat / 2) * SR)
            m2 = min(int(0.05 * SR), n - s2)
            if m2 > 0:
                out[s2:s2 + m2] += 0.04 * np.random.default_rng(k).standard_normal(m2) * np.exp(-np.arange(m2) / SR * 80)
        t += bar
        i += 1

    def sfx_hit(at):
        s = int(at * SR)
        m = int(0.12 * SR)
        tt = np.arange(m) / SR
        out[s:s + m] += 0.6 * np.random.default_rng(1).standard_normal(m) * np.exp(-tt * 60)
        out[s:s + m] += 0.4 * np.sin(2 * np.pi * 900 * tt) * np.exp(-tt * 40)

    def sfx_ding(at):
        note(hz(84), at, 0.6, 0.18)
        note(hz(91), at + 0.08, 0.6, 0.12)

    def sfx_whoosh(at):
        s = int(at * SR)
        m = int(0.35 * SR)
        tt = np.arange(m) / SR
        nz = np.random.default_rng(3).standard_normal(m)
        out[s:s + m] += 0.12 * nz * np.sin(np.pi * tt / 0.35)

    sfx_hit(0.25)
    for _, t0, _ in SCENES[1:]:
        sfx_whoosh(t0)
    T = SCENE_T0
    for at in (T["bola"] + 2.8, T["sewa"] + 1.4, T["pinjam"] + 0.5, T["pinjam"] + 2.0,
               T["kira4"] + 2.6, T["kira4"] + 3.8, T["kira4"] + 5.8,
               T["kira8"] + 2.6, T["kira8"] + 3.8, T["kira8"] + 5.8, T["akhir"] + 2.5, T["ayala"] + 0.4, T["ayala"] + 1.2):
        sfx_ding(at)

    # fade
    fade = int(1.0 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)
    out /= max(1e-9, np.abs(out).max())
    if VO_CLIPS:
        out *= 0.28  # muzik & efek jadi latar bila ada suara
        for vo_path, at in VO_CLIPS:
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", vo_path, "-f", "s16le", "-ac", "1",
                                  "-ar", str(SR), "-"], capture_output=True).stdout
            v = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768
            s0 = int(at * SR)
            m = min(len(v), n - s0)
            out[s0:s0 + m] += v[:m] * 1.1
    out /= max(1e-9, np.abs(out).max()) / 0.9
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- utama
def main():
    make_audio(WAV)
    bg = make_background()
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
        bg = make_background()
        for ts in os.environ["PREVIEW"].split(","):
            render_frame(bg, float(ts)).save(os.path.join(HERE, f"_preview_{ts}.png"))
    else:
        main()
