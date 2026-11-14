"""Lukisan barang golf (beg, kasut, seluar, baju polo, tick, bendera) untuk Part 3."""
import math

from PIL import Image, ImageDraw

from make_video import (DARK, GREEN, GREEN_D, YELLOW, RED, WHITE, GREY, clamp, ease_back, with_alpha)

NAVY = (35, 55, 95)
KHAKI = (195, 170, 120)
BROWN = (120, 80, 45)
PINK = (235, 95, 130)


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


