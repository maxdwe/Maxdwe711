#!/usr/bin/env python3
"""Video TikTok Part 2 (lawak): MEMBER VS NON-MEMBER VS... NON-PLAYER!

Sambungan make_member_vs.py. Orang yang tak main golf langsung = RM0, paling jimat. Hahaa.
Gaya sinematik sama (padang siluet, grain, angka slam), guna semula fungsi dari make_member_vs.

Output: member_vs_part2.mp4 (1080x1920, 30fps).
Guna:  python3 make_member_vs2.py
Voiceover dalam voiceover_member2/ (1_hook.mp3 ... 6_ending.mp3); babak dipanjangkan ikut
panjang suara jika fail ada.
"""
import math
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import make_member_vs as mm
from make_member_vs import (W, H, FPS, WHITE, GOLD, GREEN, TEAL, RED, INK, F_BLACK, F_XB, F_BOLD, F_MED,
                            F_MONO, fnt, rgba, clamp, prog, ease_out, ease_io, ease_back, slam, slide, label,
                            panel, underline, darken, money, count_up, golfer, camera, world_xy, whip_in,
                            down_arrow)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "member_vs_part2.mp4")
WAV = os.path.join(HERE, "_audio_member2.wav")
VO_DIR = os.path.join(HERE, "voiceover_member2")
VO_START = 0.35
SR = 44100
GREY = (150, 150, 150)

# nama, tempoh asal, fail suara
SCENE_DEFS = [
    ("hook", 6.0, "1_hook.mp3"),
    ("recap", 7.5, "2_recap.mp3"),
    ("reveal", 9.0, "3_reveal.mp3"),
    ("setahun", 7.5, "4_setahun.mp3"),
    ("twist", 9.0, "5_twist.mp3"),
    ("ending", 9.0, "6_ending.mp3"),
]

SCENES, VO_CLIPS = [], []
_t = 0.0
for _n, _d, _fn in SCENE_DEFS:
    _vl = 0.0
    _p = os.path.join(VO_DIR, _fn)
    if os.path.exists(_p):
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", _p],
                           capture_output=True, text=True)
        _vl = float(r.stdout.strip() or 0)
    _dd = max(_d, VO_START + _vl + 0.8) if _vl else _d
    SCENES.append((_n, round(_t, 3), round(_t + _dd, 3)))
    if _vl:
        VO_CLIPS.append((_p, _t + VO_START, _vl))
    _t += _dd
SC = {n: (a, b) for n, a, b in SCENES}
DURATION = SCENES[-1][2]


# ---------------------------------------------------------------- lukisan lawak
def sofa_guy(d, cx, cy, s, t, a=1.0):
    """Orang baring atas sofa tengok TV, pegang remote. (cx, cy) = tengah sofa."""
    # TV
    tx, ty = cx + 330 * s, cy - 120 * s
    d.rounded_rectangle((tx - 150 * s, ty - 100 * s, tx + 150 * s, ty + 90 * s), int(14 * s), fill=rgba((25, 25, 30), a))
    flick = 0.6 + 0.4 * math.sin(t * 11)
    d.rectangle((tx - 135 * s, ty - 86 * s, tx + 135 * s, ty + 76 * s), fill=rgba((70, 140, 210), a * flick))
    d.text((tx, ty - 5 * s), "GOLF TV", font=fnt("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(40 * s)),
           fill=rgba(WHITE, a * flick), anchor="mm")
    d.rectangle((tx - 10 * s, ty + 90 * s, tx + 10 * s, ty + 150 * s), fill=rgba((25, 25, 30), a))
    # sofa
    sofa = (180, 70, 60)
    d.rounded_rectangle((cx - 300 * s, cy - 40 * s, cx + 160 * s, cy + 90 * s), int(30 * s), fill=rgba(sofa, a))
    d.rounded_rectangle((cx - 300 * s, cy - 150 * s, cx + 160 * s, cy - 20 * s), int(30 * s), fill=rgba((150, 55, 50), a))
    d.rounded_rectangle((cx - 340 * s, cy - 90 * s, cx - 250 * s, cy + 90 * s), int(25 * s), fill=rgba((150, 55, 50), a))
    d.rounded_rectangle((cx + 110 * s, cy - 90 * s, cx + 200 * s, cy + 90 * s), int(25 * s), fill=rgba((150, 55, 50), a))
    # orang baring (kepala kiri, kaki kanan)
    body = (60, 110, 190)
    d.rounded_rectangle((cx - 210 * s, cy - 85 * s, cx + 130 * s, cy - 25 * s), int(30 * s), fill=rgba(body, a))
    hx, hy = cx - 240 * s, cy - 80 * s
    d.ellipse((hx - 45 * s, hy - 45 * s, hx + 45 * s, hy + 45 * s), fill=rgba((240, 200, 160), a))
    # muka puas hati (mata tutup)
    for ex in (-14, 14):
        d.arc((hx + ex * s - 9 * s, hy - 12 * s, hx + ex * s + 9 * s, hy + 2 * s), 200, 340, fill=rgba(INK, a), width=max(2, int(4 * s)))
    d.arc((hx - 16 * s, hy + 2 * s, hx + 16 * s, hy + 24 * s), 20, 160, fill=rgba(INK, a), width=max(2, int(4 * s)))
    # tangan pegang remote
    rx = cx - 60 * s + math.sin(t * 3) * 6
    d.line((cx - 120 * s, cy - 60 * s, rx, cy - 130 * s), fill=rgba(body, a), width=int(26 * s))
    d.rounded_rectangle((rx - 14 * s, cy - 175 * s, rx + 14 * s, cy - 115 * s), int(8 * s), fill=rgba((30, 30, 30), a))
    # zzz
    for k in range(3):
        q = (t * 0.8 + k * 0.33) % 1
        d.text((hx + 40 * s + q * 80 * s, hy - 70 * s - q * 120 * s), "z", font=fnt(F_BLACK, int((30 + k * 8) * s)),
               fill=rgba(WHITE, a * (1 - q)), anchor="mm")


def gold_bar(lay, cx, cy, s, p, t, k):
    """Jongkong emas 1g bersinar (pop masuk dengan p)."""
    if p <= 0:
        return
    sc = s * max(0.05, ease_back(p))
    w, h, dep = 190 * sc, 95 * sc, 40 * sc
    im = Image.new("RGBA", (int(w + 140 * sc) + 4, int(h + dep + 140 * sc) + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = 70 * sc, 70 * sc
    a = clamp(p * 3)
    # muka atas (trapezium)
    top = [(ox + 25 * sc, oy), (ox + w - 25 * sc, oy), (ox + w, oy + dep), (ox, oy + dep)]
    d.polygon(top, fill=rgba((255, 226, 120), a))
    # muka depan
    d.polygon([(ox, oy + dep), (ox + w, oy + dep), (ox + w - 12 * sc, oy + dep + h), (ox + 12 * sc, oy + dep + h)],
              fill=rgba((232, 176, 40), a))
    d.line((ox, oy + dep, ox + w, oy + dep), fill=rgba((255, 245, 200), a), width=max(1, int(3 * sc)))
    d.text((ox + w / 2, oy + dep + h * 0.38), "GOLD", font=fnt(F_BLACK, int(30 * sc)), fill=rgba((150, 100, 10), a), anchor="mm")
    d.text((ox + w / 2, oy + dep + h * 0.72), "999.9 · 1g", font=fnt(F_MONO, int(18 * sc)), fill=rgba((150, 100, 10), a), anchor="mm")
    # kilauan menyapu
    q = ((t * 0.7 + k * 0.13) % 1.6) - 0.3
    sx = ox + q * w
    shine = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(shine).polygon([(sx, oy), (sx + 30 * sc, oy), (sx - 10 * sc, oy + dep + h), (sx - 40 * sc, oy + dep + h)],
                                  fill=(255, 255, 255, int(150 * a)))
    mask = Image.new("L", im.size, 0)
    md = ImageDraw.Draw(mask)
    md.polygon(top, fill=255)
    md.polygon([(ox, oy + dep), (ox + w, oy + dep), (ox + w - 12 * sc, oy + dep + h), (ox + 12 * sc, oy + dep + h)], fill=255)
    im.alpha_composite(Image.composite(shine, Image.new("RGBA", im.size, (0, 0, 0, 0)), mask))
    # cahaya lembut di belakang
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((ox - 20 * sc, oy - 20 * sc, ox + w + 20 * sc, oy + dep + h + 20 * sc), fill=(255, 210, 90, int(80 * a)))
    glow = glow.filter(ImageFilter.GaussianBlur(int(18 * sc) + 1))
    glow.alpha_composite(im)
    lay.alpha_composite(glow, (int(cx - glow.width / 2), int(cy - glow.height / 2)))
    # bintang berkelip
    dl = ImageDraw.Draw(lay)
    tw = 0.5 + 0.5 * math.sin(t * 6 + k * 1.7)
    r = (10 + 14 * tw) * sc
    stx, sty = cx + w * 0.42, cy - h * 0.55
    pts = []
    for j in range(8):
        ang = j * math.pi / 4
        rr = r if j % 2 == 0 else r * 0.25
        pts.append((stx + rr * math.cos(ang), sty + rr * math.sin(ang)))
    dl.polygon(pts, fill=rgba(WHITE, a * (0.4 + 0.6 * tw)))


def teh_tarik(d, cx, cy, s, a=1.0):
    d.polygon([(cx - 40 * s, cy - 90 * s), (cx + 40 * s, cy - 90 * s), (cx + 30 * s, cy + 50 * s), (cx - 30 * s, cy + 50 * s)],
              fill=rgba((235, 235, 240), a * 0.5), outline=rgba(WHITE, a))
    d.polygon([(cx - 37 * s, cy - 60 * s), (cx + 37 * s, cy - 60 * s), (cx + 30 * s, cy + 46 * s), (cx - 30 * s, cy + 46 * s)],
              fill=rgba((190, 130, 70), a))
    d.polygon([(cx - 39 * s, cy - 82 * s), (cx + 39 * s, cy - 82 * s), (cx + 37 * s, cy - 60 * s), (cx - 37 * s, cy - 60 * s)],
              fill=rgba((245, 225, 190), a))


def big_x(d, cx, cy, r, a):
    if a <= 0:
        return
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(RED, a))
    for sgn in (-1, 1):
        d.line((cx - r * 0.42, cy - sgn * r * 0.42, cx + r * 0.42, cy + sgn * r * 0.42), fill=rgba(WHITE, a), width=int(r * 0.22))


# ---------------------------------------------------------------- babak
def bars(lay, lt, show_third, third_p, third_label_p):
    d = ImageDraw.Draw(lay)
    base_y, top_y, maxv = 1250, 520, 460
    items = [("MEMBER", "PAGI", 228, GREEN, 0.3), ("NON-", "MEMBER", 436, RED, 0.7)]
    for i, (l1, l2, v, col, st) in enumerate(items):
        x = 230 + i * 310
        p = prog(lt, st, 0.8)
        if p <= 0:
            continue
        hh = (base_y - top_y) * (v / maxv) * ease_out(p)
        d.rounded_rectangle((x - 110, base_y - hh, x + 110, base_y), 22, fill=rgba(col, 0.92))
        d.text((x, base_y - hh - 55), money(v * ease_out(p)), font=fnt(F_BLACK, 70), fill=rgba(WHITE), anchor="mm")
        d.text((x, base_y + 55), l1, font=fnt(F_XB, 40), fill=rgba(col), anchor="mm")
        d.text((x, base_y + 102), l2, font=fnt(F_XB, 40), fill=rgba(col), anchor="mm")
    if show_third:
        x = 230 + 2 * 310
        if third_p <= 0:
            d.rounded_rectangle((x - 110, base_y - 300, x + 110, base_y), 22, outline=rgba(GOLD, 0.9), width=5)
            d.text((x, base_y - 150), "???", font=fnt(F_BLACK, 80), fill=rgba(GOLD), anchor="mm")
        else:
            d.line((x - 110, base_y - 4, x + 110, base_y - 4), fill=rgba(GOLD), width=10)
            s = max(0.05, ease_back(third_p))
            slam(lay, (x, base_y - 90), "RM0", 110 * s, GOLD, third_p)
        if third_label_p > 0:
            d.text((x, base_y + 55), "NON-", font=fnt(F_XB, 40), fill=rgba(GOLD, third_label_p), anchor="mm")
            d.text((x, base_y + 102), "PLAYER", font=fnt(F_XB, 40), fill=rgba(GOLD, third_label_p), anchor="mm")
    d.line((80, base_y, W - 80, base_y), fill=rgba((200, 200, 200), prog(lt, 0.2, 0.3)), width=4)


def scene_hook(t, lt, dur):
    Z = dict(zoom0=1.05, zoom1=1.18, pan=(40, 100))
    fr = camera("sunset", lt, dur, **Z).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    gx, gy, gsc = world_xy(mm.BW * 0.6, mm.BH * 0.82, lt, dur, **Z)
    golfer(d, gx, gy, 420 * gsc, "address" if lt < 3 else "back", (14, 12, 18), face=-1)
    darken(lay, 1000, 400, 1.0)
    label(lay, (W / 2, 200), "PART 2", prog(lt, 0.1, 0.4))
    slam(lay, (W / 2, 340), "MEMBER", 140, GREEN, prog(lt, 0.5, 0.3))
    slam(lay, (W / 2, 470), "VS NON-MEMBER", 100, RED, prog(lt, 0.9, 0.3))
    p = prog(lt, 1.6, 0.35)
    shake = math.sin(lt * 50) * 12 * (1 - prog(lt, 2.0, 0.6)) if p > 0 else 0
    slam(lay, (W / 2 + shake, 640), "VS ???", 150, GOLD, p)
    a = prog(lt, 2.8, 0.4)
    if a > 0:
        panel(lay, (120, 760, 960, 870), a, col=WHITE, alpha=0.95, radius=20)
        slam(lay, (W / 2, 815), "PALING JIMAT RUPANYA...", 56, INK, a, shadow=False)
    fr.alpha_composite(lay)
    return fr


def scene_recap(t, lt, dur):
    fr = Image.blend(Image.new("RGBA", (W, H), (12, 16, 20, 255)), camera("sunset", lt, dur, 1.2, 1.3).convert("RGBA"), 0.28)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    label(lay, (W / 2, 190), "PART 1 RECAP · 4 ROUND SEBULAN", prog(lt, 0.1, 0.4))
    slam(lay, (W / 2, 310), "SIAPA PALING JIMAT?", 84, WHITE, prog(lt, 0.2, 0.3))
    bars(lay, lt, show_third=lt > 2.0, third_p=0, third_label_p=0)
    fr.alpha_composite(whip_in(lay, lt))
    return fr


def scene_reveal(t, lt, dur):
    fr = Image.blend(Image.new("RGBA", (W, H), (12, 16, 20, 255)), camera("sunset", lt, dur, 1.3, 1.35).convert("RGBA"), 0.25)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    out1 = 1 - prog(lt, 4.2, 0.3)
    if out1 > 0:
        label(lay, (W / 2, 190), "4 ROUND SEBULAN", out1)
        slam(lay, (W / 2, 310), "SIAPA PALING JIMAT?", 84, WHITE, out1)
        tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bars(tmp, lt + 5, show_third=True, third_p=prog(lt, 1.2, 0.4), third_label_p=prog(lt, 1.5, 0.3))
        if out1 < 1:
            tmp.putalpha(tmp.getchannel("A").point(lambda v: int(v * out1)))
        lay.alpha_composite(tmp)
        # sinar emas pada bar ke-3
        if lt > 1.2:
            for k in range(10):
                ang = math.radians(k * 36 + lt * 40)
                x0, y0 = 850, 1100
                d.line((x0 + math.cos(ang) * 120, y0 + math.sin(ang) * 120, x0 + math.cos(ang) * 190,
                        y0 + math.sin(ang) * 190), fill=rgba(GOLD, 0.7 * out1), width=6)
    if lt > 4.3:
        q = lt - 4.3
        slam(lay, (W / 2, 260), "NON-PLAYER", 120, GOLD, prog(q, 0.0, 0.3))
        slam(lay, (W / 2, 390), "(TAK MAIN GOLF)", 60, WHITE, prog(q, 0.3, 0.3))
        sofa_guy(d, W / 2 - 80, 900, 1.15, t, prog(q, 0.2, 0.4))
        p = prog(q, 1.0, 0.35)
        if p > 0:
            panel(lay, (90, 1250, 990, 1500), p, col=GOLD, alpha=0.96, radius=30)
            slam(lay, (W / 2, 1320), "JIMAT", 60, INK, p, shadow=False)
            slam(lay, (W / 2, 1425), "RM436 / BULAN", 96, INK, p, shadow=False)
        slam(lay, (W / 2, 1620), "HAHAHA", 90, WHITE, prog(q, 2.0, 0.3))
    fr.alpha_composite(whip_in(lay, lt))
    return fr


def scene_setahun(t, lt, dur):
    fr = camera("evening", lt, dur, 1.0, 1.1, (0, 40)).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rectangle((0, 0, W, H), fill=(0, 0, 0, 120))
    darken(lay, 800, 600, 1.0)
    label(lay, (W / 2, 200), "KALAU SETAHUN?", prog(lt, 0.1, 0.4))
    slam(lay, (W / 2, 330), "NON-PLAYER JIMAT", 80, WHITE, prog(lt, 0.3, 0.3))
    slam(lay, (W / 2, 490), "±" + money(count_up(lt, 0.8, 1.2, 5232)), 170, GOLD, prog(lt, 0.8, 0.35))
    slam(lay, (W / 2, 620), "SETAHUN", 70, WHITE, prog(lt, 1.3, 0.3))
    a = prog(lt, 2.2, 0.4)
    if a > 0:
        d.text((W / 2, 760), "Boleh beli 8 gram gold bar setahun!", font=fnt(F_BOLD, 54), fill=rgba(GOLD, a), anchor="mm")
    for k in range(8):
        r, c = divmod(k, 4)
        gold_bar(lay, 165 + c * 250, 1010 + r * 230, 1.0, prog(lt, 2.6 + k * 0.25, 0.4), t, k)
    slam(lay, (W / 2, 1520), "RM5,232 ÷ RM650 = 8 GRAM", 62, GOLD, prog(lt, 2.6 + 8 * 0.25 + 0.2, 0.3))
    fr.alpha_composite(whip_in(lay, lt))
    return fr


def scene_twist(t, lt, dur):
    fr = camera("day", lt, dur, 1.0, 1.08, (0, 0)).convert("L").convert("RGBA")  # kelabu: sedih
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rectangle((0, 0, W, H), fill=(20, 25, 35, 150))
    # hujan
    rng = np.random.default_rng(int(t * 30))
    for _ in range(90):
        x = rng.random() * W
        y = rng.random() * H
        d.line((x, y, x - 12, y + 45), fill=(180, 200, 230, 110), width=3)
    slam(lay, (W / 2, 300), "TAPI...", 150, WHITE, prog(lt, 0.2, 0.35))
    items = ["Tak rasa bola masuk lubang", "Tak lepak dengan geng golf", "Tak dapat story atas padang"]
    for i, txt in enumerate(items):
        st = 1.5 + i * 1.6
        p = prog(lt, st, 0.35)
        y = 560 + i * 200
        panel(lay, (80, y - 70, 1000, y + 70), p, alpha=0.7, radius=28)
        big_x(d, 170, y, 46, p)
        slide(lay, (250, y), txt, 50, WHITE, p, font=F_XB, anchor="lm", dx=80)
    a = prog(lt, 1.5 + 3 * 1.6 + 0.2, 0.4)
    if a > 0:
        slam(lay, (W / 2, 1290), "SEDIH WEH...", 90, (170, 190, 230), a)
    fr.alpha_composite(whip_in(lay, lt))
    return fr


def scene_ending(t, lt, dur):
    fr = mm.montage(lt)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    darken(lay, 1100, 500, 1.0)
    out1 = 1 - prog(lt, 3.8, 0.25)
    if out1 > 0:
        panel(lay, (70, 300, 1010, 760), prog(lt, 0.0, 0.25) * out1, alpha=0.62, border=GOLD)
        slam(lay, (W / 2, 400), "JIMAT DUIT", 100, GOLD, prog(lt, 0.1, 0.3) * out1)
        slam(lay, (W / 2, 520), "ATAU", 64, WHITE, prog(lt, 0.5, 0.3) * out1)
        slam(lay, (W / 2, 640), "JIMAT STRESS?", 100, GREEN, prog(lt, 0.8, 0.3) * out1)
        slam(lay, (W / 2, 880), "KAMI TETAP PILIH GOLF!", 70, WHITE, prog(lt, 2.0, 0.3) * out1)
    if lt > 3.9:
        r = lt - 3.9
        slam(lay, (W / 2, 330), "KORANG", 110, WHITE, prog(r, 0.0, 0.25))
        slam(lay, (W / 2, 450), "TEAM MANA?", 110, GOLD, prog(r, 0.2, 0.25))
        for i, (txt, col) in enumerate((("MEMBER", GREEN), ("NON-MEMBER", RED), ("NON-PLAYER", GOLD))):
            p = prog(r, 0.5 + i * 0.2, 0.25)
            panel(lay, (200, 545 + i * 105, 880, 635 + i * 105), p, col=col, alpha=0.9, radius=45)
            slam(lay, (W / 2, 590 + i * 105), txt, 56, WHITE, p, shadow=False)
        p = prog(r, 1.3, 0.3)
        if p > 0:
            panel(lay, (330, 890, 750, 990), p, col=WHITE, alpha=0.96, radius=50)
            slam(lay, (W / 2, 940), "COMMENT", 62, INK, p, shadow=False)
            down_arrow(d, W / 2, 1060 + abs(math.sin(lt * 5)) * 22, 1.0, p)
    a = prog(lt, 0.3, 0.4)
    if a > 0:
        d.text((W / 2, H - 120), "*Harga membership bergantung kepada kelab di kawasan masing-masing.",
               font=fnt(F_MED, 28), fill=rgba((230, 230, 230), a * 0.9), anchor="mm")
    fr.alpha_composite(lay)
    return fr


DISPATCH = {"hook": scene_hook, "recap": scene_recap, "reveal": scene_reveal, "setahun": scene_setahun,
            "twist": scene_twist, "ending": scene_ending}


def finish(frame, t):
    f = int(t * FPS)
    arr = np.asarray(frame.convert("RGB")).astype(np.int16)
    g = np.asarray(mm.grain(f)).astype(np.int16) - 128
    frame = Image.fromarray(np.clip(arr + g[..., None] * 0.09, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    frame.alpha_composite(mm.vignette())
    for _, t0, _ in SCENES[1:]:
        dt = t - t0
        if -0.12 < dt < 0.22:
            a = (1 - abs(dt) / 0.22) * 0.75 if dt >= 0 else (1 + dt / 0.12) * 0.4
            frame = Image.blend(frame, Image.new("RGBA", (W, H), (255, 250, 240, 255)), clamp(a))
    k = prog(t, 0, 0.3)  # fade masuk sahaja, babak akhir kekal
    if k < 1:
        frame = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), frame, k)
    return frame.convert("RGB")


def render_frame(t):
    for name, t0, t1 in SCENES:
        if t0 <= t < t1 or (name == SCENES[-1][0] and t >= t1):
            return finish(DISPATCH[name](t, t - t0, t1 - t0), t)


# ---------------------------------------------------------------- audio
def make_audio(path):
    n = int(SR * DURATION)
    music = np.zeros(n)
    sfx = np.zeros(n)
    rng = np.random.default_rng(4)

    def tone(buf, freq, start, dur, vol, kind="pad"):
        s = int(start * SR)
        m = min(int(dur * SR), n - s)
        if m <= 0 or s < 0:
            return
        tt = np.arange(m) / SR
        if kind == "pad":
            env = np.minimum(1, tt * 1.5) * np.minimum(1, (dur - tt) * 1.5)
            w = sum(np.sin(2 * np.pi * freq * dt * tt) for dt in (1, 1.003, 0.997)) / 3
        else:
            env = np.exp(-tt * 4) * np.minimum(1, tt * 300)
            w = np.sin(2 * np.pi * freq * tt) + 0.2 * np.sin(6 * np.pi * freq * tt)
        buf[s:s + m] += vol * env * w

    def hz(m):
        return 440 * 2 ** ((m - 69) / 12)

    beat = 60 / 104
    bar = 4 * beat
    prog_ = [(45, [57, 60, 64]), (41, [57, 60, 65]), (48, [55, 60, 64]), (43, [55, 59, 62])]
    t, i = 0.0, 0
    tw0, tw1 = SC["twist"]
    while t < DURATION:
        root, tri = prog_[i % 4]
        sad = tw0 <= t < tw1
        if sad:  # versi minor perlahan semasa babak sedih
            tri = [x - 1 if k == 1 else x for k, x in enumerate(tri)]
        tone(music, hz(root - 12), t, bar, 0.12, "pad")
        for nn in tri:
            tone(music, hz(nn), t, bar, 0.035, "pad")
        if not sad:
            for k in range(8):
                tone(music, hz(tri[k % 3] + 12), t + k * beat / 2, beat * 0.5, 0.04, "pluck")
            for k in range(4):
                s = int((t + k * beat) * SR)
                m = min(int(0.2 * SR), n - s)
                if m > 0:
                    tt = np.arange(m) / SR
                    music[s:s + m] += 0.26 * np.sin(2 * np.pi * (90 * np.exp(-tt * 22) + 38) * tt) * np.exp(-tt * 14)
        t += bar
        i += 1

    def impact(at, vol=0.5):
        s = int(at * SR)
        m = min(int(0.9 * SR), n - s)
        if m <= 0:
            return
        tt = np.arange(m) / SR
        sfx[s:s + m] += vol * np.sin(2 * np.pi * (60 * np.exp(-tt * 6) + 32) * tt) * np.exp(-tt * 4)

    def whoosh(at):
        s = int(at * SR)
        m = min(int(0.4 * SR), n - s)
        tt = np.arange(m) / SR
        nz = np.convolve(rng.standard_normal(m), np.ones(8) / 8, mode="same")
        sfx[s:s + m] += 0.5 * nz * np.sin(np.pi * tt / 0.4) ** 2

    def boing(at):
        s = int(at * SR)
        m = min(int(0.5 * SR), n - s)
        tt = np.arange(m) / SR
        f = 180 + 120 * np.sin(2 * np.pi * 9 * tt) * np.exp(-tt * 4)
        sfx[s:s + m] += 0.35 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 5)

    def sad_trombone(at):
        for k, f in enumerate((311, 294, 277, 262)):
            dur = 0.45 if k < 3 else 1.0
            s = int((at + k * 0.45) * SR)
            m = min(int(dur * SR), n - s)
            tt = np.arange(m) / SR
            vib = 1 + (0.02 * np.sin(2 * np.pi * 6 * tt) if k == 3 else 0)
            w = sum(np.sin(2 * np.pi * f * h * vib * tt) / h for h in (1, 2, 3))
            sfx[s:s + m] += 0.15 * w * np.minimum(1, tt * 30) * np.minimum(1, (dur - tt) * 8)

    for _, t0, _ in SCENES[1:]:
        whoosh(t0 - 0.15)
    h0 = SC["hook"][0]
    impact(h0 + 0.5, 0.35)
    impact(h0 + 0.9, 0.35)
    impact(h0 + 1.6, 0.6)
    r0 = SC["reveal"][0]
    impact(r0 + 1.2, 0.7)
    boing(r0 + 4.3)
    impact(r0 + 5.3, 0.5)
    boing(r0 + 6.3)
    s0 = SC["setahun"][0]
    impact(s0 + 0.8, 0.5)
    sad_trombone(SC["twist"][0] + 0.2)
    e0 = SC["ending"][0]
    impact(e0 + 0.1, 0.4)
    impact(e0 + 3.9, 0.5)

    vo = np.zeros(n)
    for vo_path, at, _ in VO_CLIPS:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", vo_path, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                             capture_output=True).stdout
        v = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768
        s0_ = int(at * SR)
        m = min(len(v), n - s0_)
        vo[s0_:s0_ + m] += v[:m]
    duck = np.where(np.convolve(np.abs(vo) > 0.01, np.ones(8000), mode="same") > 0, 0.35, 1.0)
    duck = np.convolve(duck, np.ones(6000) / 6000, mode="same")
    out = music * duck * 0.55 + sfx * 0.6 + vo * 1.1
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
    make_audio(WAV)
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
        for ts in os.environ["PREVIEW"].split(","):
            render_frame(float(ts)).save(os.path.join(HERE, f"_m2_{ts}.png"))
    else:
        main()
