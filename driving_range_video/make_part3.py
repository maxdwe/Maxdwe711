#!/usr/bin/env python3
"""Video animasi Part 3: Kos masuk padang - 5 barang perlu siap sebelum masuk.

Gaya "explainer kad": latar kertas krim dengan sinar & titik halftone, label mono di atas,
tajuk hitam dengan perkataan penting merah italik serif, kad-kad senget yang dibuka satu
per satu, sepanduk merah, dan hos kartun di bawah yang bercakap ikut voiceover.

1. Set golf (second hand RM1000+, kawan let go lagi murah)
2. Bola secondhand
3. Kasut golf (bundle RM40 pun ada)
4. Seluar slack
5. Baju berkolar
Lepas semua ada -> jom masuk padang!

Output: padang_part3.mp4 (1080x1920, 30fps).
Guna:  python3 make_part3.py
Voiceover dalam voiceover_part3/ (1_intro.mp3 ... 8_ayala.mp3); babak dipanjangkan
ikut panjang suara jika fail ada. Mulut hos bergerak ikut kuat suara.
"""
import math
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import make_video as mv
from make_video import W, H, FPS, clamp, prog, ease_out, ease_back, golf_ball
import shapes_part3 as sp

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "padang_part3.mp4")
WAV = os.path.join(HERE, "_audio_part3.wav")
VO_DIR = os.path.join(HERE, "voiceover_part3")
VO_START = 0.35
SR = 44100

# ---------------------------------------------------------------- warna & fon
PAPER = (236, 233, 227)
RAY = (225, 221, 214)
DOT = (212, 208, 201)
INK = (24, 24, 24)
MUTED = (120, 116, 110)
RED = (214, 52, 52)
WHITE = (255, 255, 255)
SKIN = (238, 196, 154)
SKIN_D = (205, 160, 120)

FD = "/usr/share/fonts/opentype/inter/"
F_BOLD = FD + "Inter-Bold.otf"
F_XBOLD = FD + "Inter-ExtraBold.otf"
F_MED = FD + "Inter-Medium.otf"
F_SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
F_MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf"
F_MONO_B = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-SemiBold.ttf"
_fc = {}


def fnt(path, size):
    key = (path, int(size))
    if key not in _fc:
        _fc[key] = ImageFont.truetype(path, max(4, int(size)))
    return _fc[key]


def rgba(col, a=1.0):
    return tuple(col[:3]) + (int(255 * clamp(a)),)


# ---------------------------------------------------------------- skrip babak
# nama, tempoh asal, fail suara, label kiri, label kanan, tajuk (*merah italik*),
# teks pil, teks sepanduk, nota kecil
SCENE_DEFS = [
    ("intro", 5.0, "1_intro.mp3", "// 03 · kos masuk padang", "PART 3",
     "Nak masuk *padang?* Siapkan *lima* benda ni dulu.", "part 3", "KOS MASUK PADANG", ""),
    ("set", 7.5, "2_set.mp3", "// 03 · lima barang", "BARANG 1/5",
     "Pertama, *set golf.* Second hand dari *RM1,000* ke atas.", "PERTAMA", "RM1,000++",
     "Kawan nak let go? Boleh dapat lagi murah!"),
    ("bola", 6.5, "3_bola.mp3", "// 03 · lima barang", "BARANG 2/5",
     "Kedua, bola *secondhand.* Hilang dalam lake pun *tak sakit hati.*", "KEDUA", "MURAH & JIMAT",
     "Bola terpakai pun dah cukup"),
    ("kasut", 6.0, "4_kasut.mp3", "// 03 · lima barang", "BARANG 3/5",
     "Ketiga, *kasut golf.* Kedai *bundle* pun ada!", "KETIGA", "BUNDLE RM40",
     "Tak perlu baru, asal selesa & ada grip"),
    ("seluar", 6.0, "5_seluar.mp3", "// 03 · lima barang", "BARANG 4/5",
     "Keempat, *seluar slack.* Kemas & sopan, *bukan jeans.*", "KEEMPAT", "KEMAS & SOPAN",
     "Slack yang ada kat rumah pun boleh"),
    ("baju", 6.5, "6_baju.mp3", "// 03 · lima barang", "BARANG 5/5",
     "Dan yang *terakhir,* baju *berkolar.*", "TERAKHIR", "WAJIB KOLAR!",
     "T-shirt biasa memang tak boleh masuk padang"),
    ("jom", 5.0, "7_jom.mp3", "// 03 · siap!", "5/5 ✓",
     "Semua dah ada? Jom masuk *padang!*", "SIAP", "JOM MASUK PADANG!", ""),
    ("ayala", 4.5, "8_ayala.mp3", "// 03 · next video", "FOLLOW",
     "Follow *Team Ayala* untuk part seterusnya!", "", "", ""),
]


def _vo_len(fn):
    return mv._vo_len(os.path.join(VO_DIR, fn))


SCENES, VO_CLIPS = [], []
_t = 0.0
for _def in SCENE_DEFS:
    _name, _dur, _fn = _def[:3]
    _vl = _vo_len(_fn)
    _d = max(_dur, VO_START + _vl + 0.7) if _vl else _dur
    SCENES.append(dict(name=_name, t0=round(_t, 3), t1=round(_t + _d, 3), vo=_vl,
                       left=_def[3], right=_def[4], head=_def[5], pill=_def[6], banner=_def[7], note=_def[8]))
    if _vl:
        VO_CLIPS.append((os.path.join(VO_DIR, _fn), _t + VO_START, _vl))
    _t += _d
SC = {s["name"]: s for s in SCENES}
DURATION = SCENES[-1]["t1"]
ITEM_SCENES = ["set", "bola", "kasut", "seluar", "baju"]

# ---------------------------------------------------------------- latar
_DOTS = None


def dots_layer():
    global _DOTS
    if _DOTS is None:
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for y in range(0, H, 16):
            for x in range((y // 16) % 2 * 8, W, 16):
                d.ellipse((x - 1.6, y - 1.6, x + 1.6, y + 1.6), fill=rgba(DOT, 0.9))
        _DOTS = img
    return _DOTS


def background(t):
    img = Image.new("RGBA", (W, H), rgba(PAPER))
    d = ImageDraw.Draw(img)
    cx, cy = W / 2, 820
    rot = t * 3.0
    n = 18
    for k in range(n):
        a0 = math.radians(rot + k * 360 / n)
        a1 = math.radians(rot + k * 360 / n + 360 / n * 0.5)
        R = 2400
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)),
                   (cx + R * math.cos(a1), cy + R * math.sin(a1))], fill=rgba(RAY))
    img.alpha_composite(dots_layer())
    # vignette lembut atas & bawah
    return img


# ---------------------------------------------------------------- teks
def top_labels(d, sc, a):
    f = fnt(F_MONO, 34)
    d.text((80, 150), sc["left"], font=f, fill=rgba(MUTED, a), anchor="lm")
    r = sc["right"]
    # nombor (lepas ruang terakhir) dalam merah
    if " " in r:
        head, num = r.rsplit(" ", 1)
        fb = fnt(F_MONO_B, 34)
        nw = d.textlength(num, font=fb)
        d.text((W - 80, 150), num, font=fb, fill=rgba(RED, a), anchor="rm")
        d.text((W - 80 - nw - 16, 150), head, font=f, fill=rgba(MUTED, a), anchor="rm")
    else:
        d.text((W - 80, 150), r, font=fnt(F_MONO_B, 34), fill=rgba(RED, a), anchor="rm")


def parse_head(txt):
    toks = []
    for i, part in enumerate(txt.split("*")):
        for w in part.split():
            toks.append((w, i % 2 == 1))
    return toks


def headline(layer, sc, lt, a_out=1.0):
    """Tajuk muncul perkataan demi perkataan ikut voiceover."""
    toks = parse_head(sc["head"])
    span = (sc["vo"] * 0.85) if sc["vo"] else 2.2
    d = ImageDraw.Draw(layer)
    size = 78
    x0, y, maxw, lh = 80, 260, W - 160, 100
    x = x0
    sp_w = d.textlength(" ", font=fnt(F_BOLD, size))
    n = len(toks)
    for i, (w, em) in enumerate(toks):
        f = fnt(F_SERIF, size * 1.18) if em else fnt(F_BOLD, size)
        ww = d.textlength(w, font=f)
        if x + ww > x0 + maxw:
            x = x0
            y += lh
        st = 0.15 + span * i / max(1, n)
        p = prog(lt, st, 0.18)
        if p > 0:
            col = RED if em else INK
            d.text((x, y + (1 - ease_out(p)) * 24), w, font=f, fill=rgba(col, p * a_out), anchor="ls")
        x += ww + sp_w


def pill(layer, cx, cy, txt, p, small="barang"):
    if p <= 0 or not txt:
        return
    s = max(0.05, ease_back(p))
    fb = fnt(F_XBOLD, 54)
    tw = int(ImageDraw.Draw(layer).textlength(txt, font=fb))
    w, h = tw + 120, 100
    im = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 14, w + 10, h + 14), 50, fill=(0, 0, 0, 50))
    d.rounded_rectangle((4, 4, w + 4, h + 4), 50, fill=rgba(WHITE), outline=rgba(INK), width=4)
    d.ellipse((34, h / 2 - 6, 50, h / 2 + 10), outline=rgba(INK), width=4)
    d.text((70, 30), small, font=fnt(F_MONO, 18), fill=rgba(MUTED), anchor="lm")
    d.text((68, h / 2 + 14), txt, font=fb, fill=rgba(RED), anchor="lm")
    im = im.rotate(4, expand=True, resample=Image.BICUBIC)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
    if p < 0.34:
        im.putalpha(im.getchannel("A").point(lambda v: int(v * p * 3)))
    layer.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def banner(layer, cy, txt, p, col=RED):
    """Sepanduk merah senget yang meluncur masuk dari kiri."""
    if p <= 0 or not txt:
        return
    fb = fnt(F_XBOLD, 84)
    tw = int(ImageDraw.Draw(layer).textlength(txt, font=fb))
    w, h = tw + 140, 140
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, h), fill=rgba(col))
    d.rectangle((0, h - 12, w, h), fill=rgba(tuple(int(c * 0.75) for c in col)))
    d.text((w / 2, h / 2 - 4), txt, font=fb, fill=rgba(WHITE), anchor="mm")
    im = im.rotate(4, expand=True, resample=Image.BICUBIC)
    e = ease_out(p)
    x = int(W / 2 - im.width / 2 - (1 - e) * (W + im.width) * 0.6)
    layer.alpha_composite(im, (x, int(cy - im.height / 2)))


def note(d, cy, txt, a):
    if txt and a > 0:
        d.text((W / 2, cy), txt, font=fnt(F_MED, 44), fill=rgba(MUTED, a), anchor="mm")


def sparkle(d, cx, cy, r, col, a):
    if a <= 0:
        return
    pts = []
    for k in range(8):
        ang = k * math.pi / 4
        rr = r if k % 2 == 0 else r * 0.28
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=rgba(col, a))


# ---------------------------------------------------------------- kad
CW, CH = 186, 244
CARDS = [
    ("01", "Set Golf", (52, 104, 214)),
    ("02", "Bola", (226, 168, 40)),
    ("03", "Kasut", (124, 82, 214)),
    ("04", "Slack", (48, 150, 104)),
    ("05", "Baju Kolar", (230, 96, 60)),
]
CARD_ROT = [-7, -3, 2, -2, 6]
_card_cache = {}


def _white_icon(draw_fn, box_w, box_h):
    """Lukis ilustrasi berwarna, tukar jadi ikon putih (bahagian gelap separa lut sinar)."""
    big = Image.new("RGBA", (700, 700), (0, 0, 0, 0))
    draw_fn(big)
    bb = big.getbbox()
    big = big.crop(bb)
    arr = np.array(big).astype(np.float32)
    lum = (arr[..., 0] * 0.3 + arr[..., 1] * 0.59 + arr[..., 2] * 0.11) / 255
    out = np.zeros_like(arr)
    out[..., :3] = 255
    out[..., 3] = arr[..., 3] * (0.62 + 0.38 * lum)
    ic = Image.fromarray(out.astype(np.uint8), "RGBA")
    k = min(box_w / ic.width, box_h / ic.height)
    return ic.resize((max(1, int(ic.width * k)), max(1, int(ic.height * k))), Image.LANCZOS)


def _icon(i):
    fns = [
        lambda im: sp.golf_bag(im, 350, 400, 200),
        lambda im: [golf_ball(ImageDraw.Draw(im), 260 + dx, 380 + dy, 90)
                    for dx, dy in ((0, 0), (190, 0), (95, -150))],
        lambda im: sp.golf_shoe(ImageDraw.Draw(im), 330, 350, 260),
        lambda im: sp.slack_pants(ImageDraw.Draw(im), 350, 100, 230, col=(60, 60, 60)),
        lambda im: sp.polo_shirt(ImageDraw.Draw(im), 350, 150, 250, col=(90, 90, 90)),
    ]
    return _white_icon(fns[i], CW - 70, 92)


def _halftone_shadow(w, h, r):
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    dd = ImageDraw.Draw(sh)
    for y in range(0, h, 9):
        for x in range((y // 9) % 2 * 4, w, 9):
            dd.ellipse((x - 2.2, y - 2.2, x + 2.2, y + 2.2), fill=(60, 56, 50, 200))
    sh.putalpha(Image.fromarray(np.minimum(np.array(sh.getchannel("A")), np.array(m))))
    return sh


def card_image(i, revealed, done=False):
    key = (i, revealed, done)
    if key in _card_cache:
        return _card_cache[key]
    pad = 24
    im = Image.new("RGBA", (CW + pad * 2, CH + pad * 2), (0, 0, 0, 0))
    im.alpha_composite(_halftone_shadow(CW, CH, 22), (pad + 12, pad + 14))
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = pad, pad, pad + CW, pad + CH
    num, name, col = CARDS[i]
    if revealed:
        d.rounded_rectangle((x0, y0, x1, y1), 22, fill=rgba(WHITE))
        d.rounded_rectangle((x0, y0, x1, y0 + 120), 22, fill=rgba(col))
        d.rectangle((x0, y0 + 90, x1, y0 + 120), fill=rgba(col))
        ic = _icon(i)
        im.alpha_composite(ic, (int((x0 + x1) / 2 - ic.width / 2), int(y0 + 62 - ic.height / 2)))
        d.text((x0 + 18, y0 + 150), f"barang {num}", font=fnt(F_MONO, 18), fill=rgba(MUTED), anchor="lm")
        nf = fnt(F_BOLD, 32 if len(name) < 9 else 27)
        d.text((x0 + 18, y0 + 192), name, font=nf, fill=rgba(INK), anchor="lm")
        if done:
            cx_, cy_ = x1 - 34, y0 + 150
            d.ellipse((cx_ - 22, cy_ - 22, cx_ + 22, cy_ + 22), fill=rgba((48, 150, 104)))
            d.line(((cx_ - 11, cy_), (cx_ - 3, cy_ + 9), (cx_ + 12, cy_ - 10)), fill=rgba(WHITE), width=6)
    else:
        d.rounded_rectangle((x0, y0, x1, y1), 22, fill=rgba((30, 30, 32)))
        d.text(((x0 + x1) / 2, y0 + 80), "?", font=fnt(F_XBOLD, 84), fill=rgba(WHITE), anchor="mm")
        d.text((x0 + 18, y0 + 160), f"barang {num}", font=fnt(F_MONO, 18), fill=rgba((170, 170, 170)), anchor="lm")
        d.text((x0 + 18, y0 + 196), "rahsia", font=fnt(F_BOLD, 30), fill=rgba(WHITE), anchor="lm")
        # ikon mangga
        lx, ly = x1 - 46, y0 + 196
        d.arc((lx - 13, ly - 30, lx + 13, ly - 4), 180, 360, fill=rgba(WHITE), width=5)
        d.rounded_rectangle((lx - 18, ly - 16, lx + 18, ly + 14), 5, fill=rgba(WHITE))
    d.rounded_rectangle((x0, y0, x1, y1), 22, outline=rgba(INK), width=5)
    _card_cache[key] = im
    return im


def card_state(i, t):
    """Kembalikan (muncul_p, flip_p, aktif_p) untuk kad i pada masa t."""
    intro = SC["intro"]
    appear = prog(t, intro["t0"] + 1.4 + i * 0.12, 0.45)
    sc = SC[ITEM_SCENES[i]]
    flip = prog(t, sc["t0"] + 0.25, 0.5)
    active = prog(t, sc["t0"] + 0.1, 0.35) * (1 - prog(t, sc["t1"] - 0.2, 0.35))
    return appear, flip, active


def draw_cards(layer, t, row_y=830):
    gap = 10
    total = 5 * CW + 4 * gap
    xs = [W / 2 - total / 2 + CW / 2 + k * (CW + gap) for k in range(5)]
    jom = SC["jom"]
    done_p = prog(t, jom["t0"] + 0.3, 0.1)
    order = list(range(5))
    states = [card_state(i, t) for i in order]
    order.sort(key=lambda i: states[i][2])  # kad aktif dilukis paling atas
    for i in order:
        appear, flip, active = states[i]
        if appear <= 0:
            continue
        revealed = flip >= 0.5
        sx = abs(1 - 2 * flip) if 0 < flip < 1 else 1.0
        base = card_image(i, revealed, done=revealed and done_p > 0)
        s = max(0.05, ease_back(appear)) * (1 + 0.22 * ease_out(active))
        wave = math.sin(t * 5 + i * 0.9) * 14 * prog(t, jom["t0"] + 0.5, 0.4) * (1 - prog(t, jom["t1"] - 0.3, 0.3))
        w = max(1, int(base.width * s * max(0.02, sx)))
        h = max(1, int(base.height * s))
        im = base.resize((w, h), Image.BICUBIC)
        im = im.rotate(CARD_ROT[i] * (1 - 0.7 * active), expand=True, resample=Image.BICUBIC)
        drop = (1 - ease_out(appear)) * -260
        cx = xs[i]
        cy = row_y + drop - 40 * ease_out(active) + wave
        if appear < 0.34:
            im.putalpha(im.getchannel("A").point(lambda v: int(v * appear * 3)))
        layer.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
    return xs


# ---------------------------------------------------------------- hos kartun
VO_ENV = None  # kuat suara bagi setiap frame (0..1)


def mouth_open(t):
    if VO_ENV is None:
        return 0.0
    f = int(t * FPS)
    return float(VO_ENV[f]) if 0 <= f < len(VO_ENV) else 0.0


def host(layer, t, mode="point"):
    d = ImageDraw.Draw(layer)
    mo = mouth_open(t)
    cx = W / 2
    bob = math.sin(t * 2.2) * 6 + mo * 8
    hy = 1555 + bob  # tengah kepala
    # garis "burst" di belakang kepala
    for k in range(11):
        ang = math.radians(195 + k * 15)
        pulse = 0.5 + 0.5 * math.sin(t * 4 + k)
        r0, r1 = 225, 262 + 14 * pulse
        d.line((cx + r0 * math.cos(ang), hy - 20 + r0 * math.sin(ang),
                cx + r1 * math.cos(ang), hy - 20 + r1 * math.sin(ang)), fill=rgba(INK, 0.75), width=6)
    # badan: baju polo hijau berkolar
    body_y = hy + 150
    shirt = (36, 120, 70)
    d.polygon([(cx - 250, H + 10), (cx - 215, body_y + 40), (cx - 90, body_y), (cx + 90, body_y),
               (cx + 215, body_y + 40), (cx + 250, H + 10)], fill=rgba(shirt))
    d.rectangle((cx - 45, body_y - 30, cx + 45, body_y + 10), fill=rgba(SKIN_D))
    d.polygon([(cx - 95, body_y - 4), (cx, body_y + 40), (cx - 30, body_y + 85), (cx - 120, body_y + 30)],
              fill=rgba(WHITE), outline=rgba(INK))
    d.polygon([(cx + 95, body_y - 4), (cx, body_y + 40), (cx + 30, body_y + 85), (cx + 120, body_y + 30)],
              fill=rgba(WHITE), outline=rgba(INK))
    d.rectangle((cx - 12, body_y + 40, cx + 12, body_y + 170), fill=rgba((28, 95, 55)))
    for k in range(2):
        d.ellipse((cx - 6, body_y + 80 + k * 45, cx + 6, body_y + 92 + k * 45), fill=rgba(WHITE))
    # lengan menunjuk ke atas-kiri (atau melambai)
    sx, sy = cx - 220, body_y + 70
    if mode == "wave":
        ang = math.radians(-115 + 18 * math.sin(t * 9))
        L = 230
        hx, hy2 = sx + L * math.cos(ang) - 40, sy + L * math.sin(ang)
    else:
        hx, hy2 = sx - 150 + math.sin(t * 3) * 6, sy - 230 + math.sin(t * 3) * 8
    d.line((sx, sy, hx, hy2), fill=rgba(shirt), width=70)
    d.ellipse((sx - 35, sy - 35, sx + 35, sy + 35), fill=rgba(shirt))
    d.ellipse((hx - 34, hy2 - 34, hx + 34, hy2 + 34), fill=rgba(SKIN), outline=rgba(SKIN_D), width=3)
    if mode == "wave":
        for k in range(4):
            fx = hx - 24 + k * 16
            d.rounded_rectangle((fx - 7, hy2 - 70, fx + 7, hy2 - 20), 7, fill=rgba(SKIN))
    else:  # jari telunjuk
        d.line((hx, hy2, hx - 38, hy2 - 52), fill=rgba(SKIN), width=20)
        d.ellipse((hx - 48, hy2 - 62, hx - 28, hy2 - 42), fill=rgba(SKIN))
    # kepala
    d.ellipse((cx - 128, hy - 20, cx - 92, hy + 40), fill=rgba(SKIN_D))
    d.ellipse((cx + 92, hy - 20, cx + 128, hy + 40), fill=rgba(SKIN_D))
    d.ellipse((cx - 115, hy - 135, cx + 115, hy + 140), fill=rgba(SKIN))
    # topi golf
    cap = (30, 45, 80)
    d.chord((cx - 122, hy - 165, cx + 122, hy + 20), 180, 360, fill=rgba(cap))
    d.polygon([(cx - 20, hy - 72), (cx + 190, hy - 60), (cx + 205, hy - 42), (cx - 10, hy - 50)], fill=rgba(cap))
    d.ellipse((cx - 10, hy - 155, cx + 10, hy - 140), fill=rgba(cap))
    d.text((cx - 20, hy - 110), "A", font=fnt(F_XBOLD, 46), fill=rgba((255, 200, 40)), anchor="mm")
    # rambut tepi
    d.polygon([(cx - 118, hy - 60), (cx - 95, hy - 60), (cx - 105, hy - 10)], fill=rgba(INK))
    # mata (berkelip)
    blink = (t % 3.3) < 0.12
    for ex in (-46, 46):
        if blink:
            d.line((cx + ex - 16, hy - 5, cx + ex + 16, hy - 5), fill=rgba(INK), width=6)
        else:
            d.ellipse((cx + ex - 13, hy - 22, cx + ex + 13, hy + 10), fill=rgba(INK))
            d.ellipse((cx + ex - 3, hy - 16, cx + ex + 5, hy - 8), fill=rgba(WHITE))
        d.line((cx + ex - 22, hy - 48, cx + ex + 22, hy - 52), fill=rgba(INK), width=8)
    # pipi
    for ex in (-72, 72):
        d.ellipse((cx + ex - 20, hy + 22, cx + ex + 20, hy + 40), fill=rgba((240, 150, 140), 0.8))
    # mulut: senyum, terbuka ikut suara
    mh = 8 + 46 * mo
    if mo > 0.06:
        d.chord((cx - 40, hy + 40 - mh * 0.2, cx + 40, hy + 40 + mh), 0, 180, fill=rgba((110, 30, 30)))
        d.chord((cx - 22, hy + 40 + mh * 0.45, cx + 22, hy + 40 + mh), 180, 360, fill=rgba((225, 95, 105)))
    else:
        d.arc((cx - 38, hy + 14, cx + 38, hy + 56), 20, 160, fill=rgba(INK), width=7)


# ---------------------------------------------------------------- render
_LOGO = None


def ayala_card(layer, lt):
    global _LOGO
    if _LOGO is None:
        _LOGO = Image.open(os.path.join(HERE, "logo_ayala.png")).convert("RGBA")
    p = prog(lt, 0.3, 0.6)
    if p <= 0:
        return
    s = max(0.05, ease_back(p))
    cw, ch = int(700 * s), int(640 * s)
    cx, cy = W // 2, 820
    d = ImageDraw.Draw(layer)
    sh = _halftone_shadow(max(1, cw), max(1, ch), 40)
    layer.alpha_composite(sh, (cx - cw // 2 + 16, cy - ch // 2 + 18))
    d.rounded_rectangle((cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2), int(40 * s),
                        fill=rgba(WHITE), outline=rgba(INK), width=6)
    lw = int(600 * s)
    lh = int(lw * _LOGO.height / _LOGO.width)
    logo = _LOGO.resize((max(1, lw), max(1, lh)), Image.LANCZOS)
    layer.alpha_composite(logo, (cx - lw // 2, cy - lh // 2))


def flag_badge(layer, lt):
    """Bendera padang + lubang untuk babak jom."""
    d = ImageDraw.Draw(layer)
    p = ease_out(prog(lt, 0.4, 0.6))
    if p <= 0:
        return
    x, y = W - 140, 1520
    d.ellipse((x - 110, y - 26, x + 110, y + 26), fill=rgba((80, 190, 95), p), outline=rgba(INK, p), width=4)
    d.ellipse((x - 26, y - 9, x + 26, y + 9), fill=rgba(INK, p))
    sp.flag(d, x, y, 210 * p, lt, p)


def render_frame(t):
    frame = background(t)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cur = next((s for s in SCENES if s["t0"] <= t < s["t1"]), SCENES[-1])
    lt = t - cur["t0"]
    out_a = 1 - prog(t, cur["t1"] - 0.3, 0.3) if cur is not SCENES[-1] else 1.0
    top_labels(d, cur, prog(lt, 0, 0.3) * out_a)
    headline(layer, cur, lt, out_a)

    name = cur["name"]
    if name != "ayala":
        xs = draw_cards(layer, t)
        # pil di atas kad aktif / kiri
        if name in ITEM_SCENES:
            i = ITEM_SCENES.index(name)
            px = min(max(xs[i], 230), W - 230)
            pill(layer, px, 625, cur["pill"], prog(lt, 0.5, 0.45) * out_a)
            sparkle(d, xs[i] + 110, 705 + math.sin(t * 5) * 8, 26, RED, prog(lt, 0.8, 0.3) * out_a)
            sparkle(d, xs[i] - 105, 975, 16, INK, prog(lt, 1.0, 0.3) * out_a)
        else:
            pill(layer, 250, 625, cur["pill"], prog(lt, 1.0, 0.45) * out_a, small="team ayala")
        if out_a > 0.5:
            banner(layer, 1110, cur["banner"], prog(lt, 1.0, 0.5))
        note(d, 1235, cur["note"], prog(lt, 1.6, 0.4) * out_a)
        if name == "jom":
            flag_badge(layer, lt)
        host(layer, t, "point")
    else:
        ayala_card(layer, lt)
        host(layer, t, "wave")
    frame.alpha_composite(layer)
    k = min(prog(t, 0, 0.35), 1 - prog(t, DURATION - 0.5, 0.5))
    if k < 1:
        frame = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), frame, k)
    return frame.convert("RGB")


# ---------------------------------------------------------------- audio
def load_vo(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1",
                          "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768


def build_vo_track():
    n = int(SR * DURATION)
    vo = np.zeros(n)
    for path, at, _ in VO_CLIPS:
        v = load_vo(path)
        s0 = int(at * SR)
        m = min(len(v), n - s0)
        vo[s0:s0 + m] += v[:m]
    return vo


def compute_vo_env(vo):
    global VO_ENV
    spf = SR // FPS
    nf = int(DURATION * FPS) + 1
    env = np.zeros(nf)
    for f in range(nf):
        seg = vo[f * spf:(f + 1) * spf]
        env[f] = np.sqrt(np.mean(seg ** 2)) if len(seg) else 0
    if env.max() > 0:
        env = np.clip(env / (np.percentile(env[env > 0], 90) + 1e-9), 0, 1)
    # licinkan sedikit
    env = np.convolve(env, [0.25, 0.5, 0.25], mode="same")
    VO_ENV = env


def make_audio(path, vo):
    n = int(SR * DURATION)
    music = np.zeros(n)
    sfx = np.zeros(n)
    beat = 60 / 96

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

    def hz(midi):
        return 440 * 2 ** ((midi - 69) / 12)

    # muzik lo-fi santai: Fmaj7 - Em7 - Dm7 - Cmaj7
    chords = [(41, [64, 69, 72, 76]), (40, [62, 67, 71, 74]), (38, [60, 65, 69, 72]), (36, [59, 64, 67, 71])]
    t, i, bar = 0.0, 0, 4 * beat
    while t < DURATION:
        root, tri = chords[i % 4]
        note(music, hz(root), t, bar, 0.08, "pad")
        for k, step in enumerate([0, 2, 1, 3, 2, 1, 3, 2]):
            note(music, hz(tri[step] + 12), t + k * beat / 2, beat, 0.05)
        for k in range(4):
            s = int((t + k * beat) * SR)
            m = min(int(0.15 * SR), n - s)
            if m > 0 and k % 2 == 0:
                tt = np.arange(m) / SR
                music[s:s + m] += 0.2 * np.sin(2 * np.pi * (100 * np.exp(-tt * 25) + 40) * tt) * np.exp(-tt * 18)
            s2 = int((t + k * beat + beat / 2) * SR)
            m2 = min(int(0.04 * SR), n - s2)
            if m2 > 0:
                music[s2:s2 + m2] += 0.03 * np.random.default_rng(k).standard_normal(m2) * np.exp(-np.arange(m2) / SR * 90)
        t += bar
        i += 1

    def whoosh(at):
        s = int(at * SR)
        m = min(int(0.3 * SR), n - s)
        tt = np.arange(m) / SR
        sfx[s:s + m] += 0.1 * np.random.default_rng(3).standard_normal(m) * np.sin(np.pi * tt / 0.3)

    def pop(at, pitch, vol=0.22):
        s = int(at * SR)
        m = min(int(0.12 * SR), n - s)
        tt = np.arange(m) / SR
        f = pitch * (1 + 2 * np.exp(-tt * 40))
        sfx[s:s + m] += vol * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 30)

    def flip(at):
        s = int(at * SR)
        m = min(int(0.09 * SR), n - s)
        sfx[s:s + m] += 0.18 * np.random.default_rng(5).standard_normal(m) * np.exp(-np.arange(m) / SR * 50)

    def ding(at):
        note(sfx, hz(84), at, 0.6, 0.15)
        note(sfx, hz(91), at + 0.08, 0.6, 0.1)

    for s in SCENES[1:]:
        whoosh(s["t0"])
    for k in range(5):
        pop(SC["intro"]["t0"] + 1.4 + k * 0.12 + 0.2, 500 + k * 80)
    for nm in ITEM_SCENES:
        flip(SC[nm]["t0"] + 0.5)
        pop(SC[nm]["t0"] + 0.75, 900)
        whoosh(SC[nm]["t0"] + 1.0)
    ding(SC["jom"]["t0"] + 0.4)
    # TING follow
    at = int((SC["ayala"]["t0"] + 0.6) * SR)
    m = min(int(1.6 * SR), n - at)
    tt = np.arange(m) / SR
    ting = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * dk)
               for f, a, dk in ((1568, 1.0, 3.0), (3136, 0.45, 5.0), (4704, 0.2, 8.0), (2349, 0.3, 4.0)))
    sfx[at:at + m] += 0.3 * ting * np.minimum(1, tt * 400)

    env = np.ones(n)
    for _, at_, ln in VO_CLIPS:
        s, e = int(at_ * SR), min(n, int((at_ + ln) * SR))
        env[max(0, s - 4000):e + 4000] = 0.3
    env = np.convolve(env, np.ones(4000) / 4000, mode="same")
    out = (music * env + sfx * 0.8) * 0.5 + vo * 1.0
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
    vo = build_vo_track()
    compute_vo_env(vo)
    make_audio(WAV, vo)
    total = int(DURATION * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", WAV,
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(total):
        proc.stdin.write(render_frame(f / FPS).tobytes())
        if f % 150 == 0:
            print(f"frame {f}/{total}", flush=True)
    proc.stdin.close()
    proc.wait()
    os.remove(WAV)
    print("Siap:", OUT, f"({DURATION:.1f}s)")


if __name__ == "__main__":
    if os.environ.get("PREVIEW"):
        compute_vo_env(build_vo_track())
        for ts in os.environ["PREVIEW"].split(","):
            render_frame(float(ts)).save(os.path.join(HERE, f"_p3_{ts}.png"))
    else:
        main()
