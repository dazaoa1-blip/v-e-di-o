#!/usr/bin/env python3
"""EP04《打击感先改哪？》封面生成器 —— 8bit 像素风，35/65 非对称左右对比。

所有元素先在低分辨率“像素格”上绘制，再按整数倍最近邻放大，
保证输出图边缘锐利、无任何抗锯齿模糊。

用法：python3 cover/make_cover.py         # 输出全部比例到 cover/
依赖：Pillow、numpy；字体使用文泉驿点阵正黑（fonts-wqy-zenhei）内嵌的 12px 位图字形。
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
FONT_INDEX = 2  # WenQuanYi Zen Hei Sharp（带位图点阵）


def hexc(s):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


# ---------------------------------------------------------------- 调色板
INK = hexc("#120c1c")          # 统一描边黑
CHAR_BG = hexc("#25252b")      # 左侧深炭灰
CHAR_FLOOR = hexc("#1a1a1f")
YELLOW = hexc("#ffe03a")
ORANGE = hexc("#ff8a1c")
DEEP_ORANGE = hexc("#ff5a1f")
WHITE = hexc("#ffffff")
PINK = hexc("#ff3d8e")
CYAN = hexc("#38f2ff")
MAGENTA = hexc("#ff3cf0")
RED = hexc("#ff2b4a")
EYE = hexc("#2a1420")

HERO_PAL = {
    "H": "#ffd23f", "h": "#e89a1a", "L": "#fff3a8",   # 金发
    "S": "#ffe9c9", "s": "#f2b98f", "E": "#2a1420",   # 皮肤 / 眼睛
    "P": "#ff5fa8", "p": "#d83a83",                    # 粉色上衣
    "B": "#5a8cff", "b": "#3a5fd0",                    # 蓝色裤子
    "O": "#8a4a22",                                    # 靴子
}
HERO = [
    "...HHHHHH.....",
    "..HLLHHHHH....",
    ".HHLHHHHHHH...",
    "HHHHHHHHHHH...",
    "HHhHHSSSSSS...",
    "HHhHSSSSESS.SS",
    "HHhHSSSSESS.SS",
    "HhhHSSSSSSsP..",
    ".hhhsSSSSsPP..",
    "...PPPPPPPP...",
    "...PPPPPPp....",
    "...BBBBBBb....",
    "...BBBBBBb....",
    "...BBb.BBb....",
    "..OOO..OOO....",
]
HERO_HAND = (13.0, 6.0)      # 握剑点（精灵内连续坐标）
HERO_SHOULDER = (9.0, 9.0)   # 剑气圆弧圆心

MASCOT_PAL = {
    "G": "#62e83a", "g": "#3cb52a", "L": "#c4ff8e",
    "D": "#2c7d1e", "M": "#7d8a1e", "E": "#0f3d14",
}
MASCOT = [
    "......LL........",
    ".....LGGL.......",
    "......Gg........",
    ".......g........",
    "..gG.......LG...",
    ".GGGGGGGGGGGGG..",
    ".GGLLGGGGGGGLGG.",
    "GGLGGGGGGGGGGGGG",
    "GGGGGEGGGGEGGGGG",
    "GGGGGEGGGGEGGGGG",
    "GGGGGGGGgGGGGGGG",
    "GMDGGGGGGGGGGMDG",
    ".gMDgGGGGGGgDMg.",
    "..gggggggggggg..",
]
MASCOT_INK = hexc("#0f3d14")

# ---------------------------------------------------------------- 字体
_FONT = ImageFont.truetype(FONT_PATH, 12, index=FONT_INDEX)


def text_mask(text, k=1):
    """12px 点阵字 → 2k 倍子像素，并向右下各加粗 k 格，得到“粗像素字”。

    逐字排版：全角标点只保留字形本身，避免“哪 ？”之间出现大空洞。
    """
    cols = []
    for ch in text:
        w = int(math.ceil(_FONT.getlength(ch)))
        im = Image.new("1", (w + 2, 14), 0)
        d = ImageDraw.Draw(im)
        d.fontmode = "1"
        d.text((0, 0), ch, font=_FONT, fill=1)
        g = np.array(im)
        if ch in "？！，。·" or ord(ch) < 128:
            xs = np.where(g.any(0))[0]
            g = g[:, max(xs.min() - 1, 0):xs.max() + 2] if len(xs) else g[:, :3]
        else:
            g = g[:, :w]
        cols.append(g)
    m = np.hstack(cols)
    ys, xs = np.where(m)
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    u = m.repeat(2 * k, 0).repeat(2 * k, 1)
    b = u.copy()
    for i in range(1, k + 1):
        b[:, i:] |= u[:, :-i]
    b2 = b.copy()
    for i in range(1, k + 1):
        b2[i:, :] |= b[:-i, :]
    return b2


# ---------------------------------------------------------------- 位图工具
def layer(w, h):
    return np.zeros((h, w, 4), np.uint8)


def shift(mask, dx, dy):
    out = np.zeros_like(mask)
    h, w = mask.shape
    out[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = \
        mask[max(-dy, 0):h + min(-dy, 0), max(-dx, 0):w + min(-dx, 0)]
    return out


def dilate(mask, r=1, diag=True):
    out = mask.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if diag or abs(dx) + abs(dy) <= r:
                out |= shift(mask, dx, dy)
    return out


def add_outline(lay, color=INK, r=1, diag=False):
    m = lay[..., 3] > 0
    lay[dilate(m, r, diag) & ~m] = color
    return lay


def sprite(rows, pal, outline=INK, tint=None):
    tint = tint or (lambda c: c)
    h, w = len(rows), max(len(r) for r in rows)
    lay = layer(w + 2, h + 2)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in pal:
                lay[y + 1, x + 1] = tint(hexc(pal[ch]))
    return add_outline(lay, tint(outline))


def paste(canvas, lay, x, y, k=1):
    """把 lay 放大 k 倍（最近邻）贴到 canvas 的 (x, y)，alpha 为 0 的格子透明。"""
    if k != 1:
        lay = lay.repeat(k, 0).repeat(k, 1)
    h, w = lay.shape[:2]
    H, W = canvas.shape[:2]
    x, y = int(x), int(y)
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1:
        return
    src = lay[y0 - y:y1 - y, x0 - x:x1 - x]
    m = src[..., 3] > 0
    canvas[y0:y1, x0:x1][m] = src[m]


def put(lay, x, y, c):
    x, y = int(math.floor(x)), int(math.floor(y))
    if 0 <= y < lay.shape[0] and 0 <= x < lay.shape[1]:
        lay[y, x] = c


def line_cells(lay, x0, y0, x1, y1, color):
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        t = i / n
        put(lay, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, color)


def poly_mask(w, h, pts):
    im = Image.new("1", (w, h), 0)
    ImageDraw.Draw(im).polygon(pts, fill=1)
    return np.array(im)


def star_points(cx, cy, n, r_out, r_in, rng, jitter=0.0, rot=0.0, sx=1.0, sy=1.0):
    pts = []
    for i in range(n * 2):
        a = rot + math.pi * i / n
        r = r_out * (1 + rng.uniform(-jitter, jitter)) if i % 2 == 0 else r_in
        pts.append((cx + math.cos(a) * r * sx, cy + math.sin(a) * r * sy))
    return pts


def round_rect_mask(w, h, r):
    m = np.ones((h, w), bool)
    for y in range(r):
        for x in range(r):
            if (r - x - 0.5) ** 2 + (r - y - 0.5) ** 2 > r * r:
                m[y, x] = m[y, w - 1 - x] = m[h - 1 - y, x] = m[h - 1 - y, w - 1 - x] = False
    return m


BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def desat(c, amount=0.78, dark=0.72):
    g = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
    return tuple(int((c[i] * (1 - amount) + g * amount) * dark) for i in range(3)) + (c[3],)


def text_layer(text, fill, outline=INK, ow=2, shadow=0, k=1):
    """粗像素字 + 外描边 + 向右下的硬投影（全部在子像素格上）。"""
    m = text_mask(text, k)
    m = np.pad(m, ow + shadow + 1)
    lay = layer(m.shape[1], m.shape[0])
    body = dilate(m, ow) if ow else m
    if shadow:
        sh = body.copy()
        for i in range(1, shadow + 1):
            sh |= shift(body, i, i)
        lay[sh] = outline
    lay[body] = outline
    lay[m] = fill
    return lay


def bbox(lay):
    ys, xs = np.where(lay[..., 3] > 0)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


# ---------------------------------------------------------------- 角色与特效
def slime_layer(squash=False, dim=False):
    rx, ry, n = (7.2, 3.3, 2.6) if squash else (5.2, 4.4, 2.8)
    w, h = int(rx * 2) + 6, int(ry * 2) + 5
    lay = layer(w, h)
    cx, base = w / 2, h - 2
    cy = base - ry
    body = np.zeros((h, w), bool)
    for y in range(h):
        for x in range(w):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            if squash:
                dx -= (base - y) * 0.22   # 被剑从左上方压扁并推向右侧
            if y < base and abs(dx / rx) ** n + abs(dy / ry) ** n <= 1:
                body[y, x] = True
    if squash:
        body[base - 1] |= dilate(body[base - 1][None], 1)[0]  # 底部被砸得摊开
    fill = (206, 206, 212, 255) if dim else WHITE
    shade = (150, 150, 160, 255) if dim else hexc("#cdc4f2")
    lay[body] = fill
    lay[body & ~shift(body, -1, -1)] = shade
    ys, xs = np.where(body)
    top, bot, left, right = ys.min(), ys.max(), xs.min(), xs.max()
    if squash:
        # >  <  眼 + 小嘴 + 腮红
        ey = top + 2
        exl, exr = left + 4, right - 4
        for ex, d in ((exl, 1), (exr, -1)):
            lay[ey - 1, ex] = EYE
            lay[ey, ex + d] = EYE
            lay[ey + 1, ex] = EYE
        mx = (exl + exr) // 2
        lay[ey + 1, mx:mx + 2] = EYE
        lay[ey + 2, exl] = hexc("#ff8fb8")
        lay[ey + 2, exr] = hexc("#ff8fb8")
    else:
        ey = top + (bot - top) // 2
        for ex in (left + 3, right - 3):
            lay[ey:ey + 2, ex] = (90, 80, 86, 255) if dim else EYE
    add_outline(lay, (64, 64, 72, 255) if dim else INK)
    return lay


def draw_sword(lay, hx, hy, ang, length, dim=False):
    ca, sa = math.cos(ang), math.sin(ang)
    blade = (140, 140, 148, 255) if dim else hexc("#f4f8ff")
    edge = (104, 104, 112, 255) if dim else hexc("#9fb2d8")
    guard = (112, 112, 118, 255) if dim else YELLOW
    grip = (84, 84, 90, 255) if dim else hexc("#8a4a22")
    tmp = layer(lay.shape[1], lay.shape[0])
    line_cells(tmp, hx - ca * 1.2, hy - sa * 1.2, hx + ca * 0.8, hy + sa * 0.8, grip)
    line_cells(tmp, hx + ca * 2.2, hy + sa * 2.2, hx + ca * length, hy + sa * length, blade)
    line_cells(tmp, hx + ca * 2.2 - sa * 0.9, hy + sa * 2.2 + ca * 0.9,
               hx + ca * (length - 0.8) - sa * 0.9, hy + sa * (length - 0.8) + ca * 0.9, edge)
    gx, gy = hx + ca * 1.5, hy + sa * 1.5
    line_cells(tmp, gx + sa * 1.6, gy - ca * 1.6, gx - sa * 1.6, gy + ca * 1.6, guard)
    add_outline(tmp, (40, 40, 46, 255) if dim else INK)
    m = tmp[..., 3] > 0
    lay[m] = tmp[m]


def smear(lay, cx, cy, r_out, a0, a1, palette, width, tail=0.3, ghost=False):
    h, w = lay.shape[:2]
    for y in range(h):
        for x in range(w):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            a = math.atan2(dy, dx)
            if a < a0 - 0.5:
                a += 2 * math.pi
            if not a0 <= a <= a1:
                continue
            p = (a - a0) / (a1 - a0)
            thick = width[0] + (width[1] - width[0]) * p
            depth = r_out - math.hypot(dx, dy)
            if not 0 <= depth <= thick:
                continue
            if p < tail and BAYER4[y % 4, x % 4] > p / tail:
                continue
            if ghost and (x + y) % 2:
                continue
            lay[y, x] = palette[min(int(depth / thick * len(palette)), len(palette) - 1)]


SCENE_W, SCENE_H = 50, 34
GROUND = SCENE_H - 3


def build_scene(hit, seed=4):
    """“小人挥剑 + 史莱姆”。hit=False 为痛点版，hit=True 为效果版（同一套动作）。"""
    rng = random.Random(seed)
    lay = layer(SCENE_W, SCENE_H)
    kx, ky = 4, GROUND - len(HERO)
    hand = (kx + HERO_HAND[0], ky + HERO_HAND[1])
    shoulder = (kx + HERO_SHOULDER[0], ky + HERO_SHOULDER[1])
    ang = math.radians(16)
    blade = 9.0
    tip = (hand[0] + math.cos(ang) * blade, hand[1] + math.sin(ang) * blade)

    sl = slime_layer(squash=hit, dim=not hit)
    bx0, by0, bx1, by1 = bbox(sl)
    pen = 3.0 if hit else 1.0                       # 剑尖压入史莱姆的深度
    sx = int(round(tip[0] - pen)) - bx0
    sy = GROUND - by1
    slime_box = (sx + bx0, sy + by0, sx + bx1, sy + by1)

    # 地面投影
    floor = hexc("#1b1338") if hit else CHAR_FLOOR
    for x0, x1 in ((kx + 1, kx + 12), (slime_box[0] + 1, slime_box[2] - 1)):
        lay[GROUND, x0:x1] = floor

    r_out = math.hypot(tip[0] - shoulder[0], tip[1] - shoulder[1]) + 0.8
    a1 = math.atan2(tip[1] - shoulder[1], tip[0] - shoulder[0]) + 0.04
    a0 = a1 - math.radians(150)
    C = (tip[0], tip[1] - 0.5)
    if hit:
        # 冲击波：橙黄相间的破碎圆环 + 放射速度线
        for ring_r, col, n in ((12.0, YELLOW, 30), (10.0, ORANGE, 26)):
            for k in range(n):
                if k % 4 == 3:
                    continue
                a = k * 2 * math.pi / n
                y = C[1] + math.sin(a) * ring_r * 0.9
                if y < GROUND:
                    put(lay, C[0] + math.cos(a) * ring_r, y, col)
        for k in range(14):
            a = (k + 0.5) * 2 * math.pi / 14 + rng.uniform(-0.08, 0.08)
            r0 = 13.5 + rng.uniform(0, 1.5)
            r1 = r0 + rng.choice((2.5, 3.5, 4.5))
            if C[1] + math.sin(a) * r1 < GROUND - 1:
                line_cells(lay, C[0] + math.cos(a) * r0, C[1] + math.sin(a) * r0,
                           C[0] + math.cos(a) * r1, C[1] + math.sin(a) * r1,
                           WHITE if k % 2 else YELLOW)
        # 黄橙爆炸星芒（垫在史莱姆后面）
        big = poly_mask(SCENE_W, SCENE_H, star_points(*C, 10, 8.4, 4.2, rng, jitter=0.2, rot=0.15))
        mid = poly_mask(SCENE_W, SCENE_H, star_points(*C, 10, 5.8, 3.0, rng, jitter=0.15, rot=0.45))
        big[GROUND:] = mid[GROUND:] = False
        lay[dilate(big, 1, diag=False) & ~big] = hexc("#7a1030")
        lay[big] = DEEP_ORANGE
        lay[dilate(mid, 1, diag=False) & ~mid & big] = ORANGE
        lay[mid] = YELLOW
        # 剑气拖尾（外白 → 黄 → 橙）
        smear(lay, *shoulder, r_out, a0, a1, [WHITE, WHITE, YELLOW, ORANGE], width=(1.0, 5.5))
        # 史莱姆：品红 / 青色错位重影 = 受击震动
        g = sl[..., 3] > 0
        for dx, col in ((-1, MAGENTA), (1, CYAN)):
            gl = layer(*sl.shape[1::-1])
            gl[g] = col
            paste(lay, gl, sx + dx, sy)
        paste(lay, sl, sx, sy)
        # 震动线 + 落地扬尘
        rx_ = slime_box[2] + 1
        for dy in (1, 4):
            lay[slime_box[1] + dy:slime_box[1] + dy + 2, rx_] = WHITE
            lay[slime_box[1] + dy + 1:slime_box[1] + dy + 3, rx_ + 2] = WHITE
        for x, y in ((slime_box[2] + 1, GROUND - 1), (slime_box[2] + 2, GROUND - 2),
                     (slime_box[2] + 4, GROUND - 1)):
            put(lay, x, y, hexc("#e8e2ff"))
    else:
        # 只有一道淡灰色残影（棋盘格抖动，若有若无）
        smear(lay, *shoulder, r_out, a0, a1, [(98, 98, 108, 255), (80, 80, 90, 255)],
              width=(1.0, 3.5), tail=0.5, ghost=True)
        for da in (-75, -40):
            a = ang + math.radians(da)
            g = layer(SCENE_W, SCENE_H)
            line_cells(g, hand[0] + math.cos(a) * 2, hand[1] + math.sin(a) * 2,
                       hand[0] + math.cos(a) * blade, hand[1] + math.sin(a) * blade,
                       (72, 72, 80, 255))
            m = (g[..., 3] > 0) & (lay[..., 3] == 0)
            lay[m] = g[m]
        paste(lay, sl, sx, sy)

    draw_sword(lay, *hand, ang, blade, dim=not hit)
    paste(lay, sprite(HERO, HERO_PAL, tint=None if hit else desat), kx - 1, ky - 1)
    if hit:
        # 命中点白色爆闪 + 飞溅颗粒
        cm = poly_mask(SCENE_W, SCENE_H, star_points(*C, 4, 3.0, 1.0, rng, rot=-math.pi / 4))
        lay[dilate(cm, 1, diag=False) & ~cm] = YELLOW
        lay[cm] = WHITE
        for _ in range(16):
            a = rng.uniform(-math.pi * 0.95, math.pi * 0.1)
            r = rng.uniform(5.0, 10.0)
            x, y = C[0] + math.cos(a) * r, C[1] + math.sin(a) * r
            col = rng.choice((WHITE, YELLOW, WHITE, ORANGE))
            put(lay, x, y, col)
            if rng.random() < 0.35:
                put(lay, x + 1, y, col)
    return lay, dict(hero=(kx - 1, ky - 1, kx + 15, GROUND), slime=slime_box, hit=C)


def mascot_with_bubble():
    body = sprite(MASCOT, MASCOT_PAL, outline=MASCOT_INK)
    bh, bw = body.shape[:2]
    bub_w, bub_h = 9, 11
    lay = layer(bw + 10, bh + bub_h)
    bub = layer(bub_w + 2, bub_h + 5)
    bub[1:bub_h + 1, 1:bub_w + 1][round_rect_mask(bub_w, bub_h, 2)] = WHITE
    bub[bub_h + 1, 2:4] = WHITE
    bub[bub_h + 2, 2] = WHITE
    ex = bub_w // 2
    bub[3:8, ex:ex + 2] = RED
    bub[9, ex:ex + 2] = RED
    add_outline(bub, INK)
    paste(lay, body, 0, bub_h)
    arm = layer(4, 6)
    arm[1:5, 1] = hexc(MASCOT_PAL["G"])
    arm[1, 2] = hexc(MASCOT_PAL["L"])
    add_outline(arm, MASCOT_INK)
    paste(lay, arm, bw - 3, bub_h - 1)
    paste(lay, bub, bw - 2, 0)
    return lay


def ep_badge(rng):
    t = text_layer("EP.04", WHITE, INK, ow=2)
    th, tw = t.shape[:2]
    w, h = tw + 20, th + 20
    lay = layer(w + 6, h + 6)
    pts = star_points((w + 6) / 2, (h + 6) / 2, 16, 1.0, 0.82, rng, rot=0.1, sx=w / 2, sy=h / 2)
    m = poly_mask(w + 6, h + 6, pts)
    lay[dilate(m, 2) & ~m] = INK
    lay[m] = PINK
    paste(lay, t, (w + 6 - tw) // 2, (h + 6 - th) // 2)
    return lay


def bubble_round(text, fill, txt_fill):
    """圆角像素对话气泡，尾巴朝左下指向小人。"""
    t = text_layer(text, txt_fill, INK, ow=2)
    th, tw = t.shape[:2]
    w, h = tw + 16, th + 10
    tail = 9
    lay = layer(w + 9, h + tail + 9)
    full = np.zeros(lay.shape[:2], bool)
    full[2:2 + h, 2:2 + w][round_rect_mask(w, h, 6)] = True
    for i in range(tail):
        x0 = 14 - i // 2
        full[2 + h + i, x0:x0 + max(1, (tail - i))] = True
    ol = dilate(full, 2) & ~full
    sh = shift(full | ol, 4, 4) & ~(full | ol)
    lay[sh] = (12, 12, 16, 255)
    lay[ol] = INK
    lay[full] = fill
    paste(lay, t, 2 + (w - tw) // 2, 2 + (h - th) // 2)
    return lay, (12, 2 + h + tail)


def bubble_boom(rng):
    """爆炸形气泡：小字“有分量！”+ 双倍大的“咚！”。"""
    t1 = text_layer("有分量！", WHITE, INK, ow=2)
    t2 = text_layer("咚！", RED, INK, ow=3, k=2)
    gap = 2
    tw = max(t1.shape[1], t2.shape[1])
    th = t1.shape[0] + t2.shape[0] + gap
    w, h = int(tw * 1.5) + 10, int(th * 1.6) + 10
    lay = layer(w, h)
    pts = star_points(w / 2, h / 2, 12, 1.0, 0.74, rng, jitter=0.08, rot=-0.25,
                      sx=w / 2 - 5, sy=h / 2 - 5)
    m = poly_mask(w, h, pts)
    ol = dilate(m, 3) & ~m
    sh = shift(m | ol, 5, 5) & ~(m | ol)
    lay[sh] = hexc("#0d0820")
    lay[ol] = INK
    lay[m] = YELLOW
    y = (h - th) // 2
    for t in (t1, t2):
        paste(lay, t, (w - t.shape[1]) // 2, y)
        y += t.shape[0] + gap
    return lay


def tag_layer(lines):
    col = hexc("#bdbdc8")
    parts = [text_layer(s, col, INK, ow=0) for s in lines]
    tw = max(p.shape[1] for p in parts)
    th = sum(p.shape[0] for p in parts) + 3 * (len(parts) - 1)
    lay = layer(tw + 16, th + 12)
    full = np.zeros(lay.shape[:2], bool)
    full[2:th + 10, 2:tw + 14][round_rect_mask(tw + 12, th + 8, 3)] = True
    lay[dilate(full, 2) & ~full] = hexc("#55555f")
    lay[full] = hexc("#16161b")
    y = 6
    for p in parts:
        paste(lay, p, 8 + (tw - p.shape[1]) // 2, y)
        y += p.shape[0] + 3
    return lay


# ---------------------------------------------------------------- 背景
def background(W, H, split, cell, rng):
    img = np.zeros((H, W, 4), np.uint8)
    gh, gw = H // cell + 2, W // cell + 2
    sc = split // cell
    top, bot = np.array(hexc("#2b0a56")[:3]), np.array(hexc("#3a3acb")[:3])
    levels = 7
    bg = layer(gw, gh)
    for y in range(gh):
        for x in range(gw):
            t = min(1.0, (y / gh) * 0.85 + ((x - sc) / (gw - sc)) * 0.15)
            q = t * (levels - 1)
            lvl = int(q) + (1 if (q - int(q)) > BAYER4[y % 4, x % 4] else 0)
            c = top + (bot - top) * (min(lvl, levels - 1) / (levels - 1))
            bg[y, x] = (*c.astype(int), 255)
    # 细碎像素星光
    for _ in range(int((gw - sc) * gh / 55)):
        x, y = rng.randrange(sc + 3, gw - 2), rng.randrange(2, gh - 2)
        r = rng.random()
        if r < 0.7:
            bg[y, x] = rng.choice((hexc("#7d72f0"), hexc("#a49bff")))
        elif r < 0.93:
            bg[y, x] = WHITE
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                bg[y + dy, x + dx] = hexc("#9d93ff")
        else:
            bg[y, x] = YELLOW
    # 锯齿分割线：左边沉闷，右边炸开
    for y in range(gh):
        off = (0, 1, 2, 1)[y % 4]
        bg[y, :sc + off] = CHAR_BG
        bg[y, sc + off:sc + off + 2] = INK
    paste(img, bg, 0, 0, cell)
    return img


# ---------------------------------------------------------------- 版式
FORMATS = {
    "3x4": dict(W=1080, H=1440, title=["打击感", "先改哪？"], tu=9, bdk=4, lc=11, rc=16,
                bu=3, boom=3, lu=2, mu=8, ground=1150),
    "4x3": dict(W=1440, H=1080, title=["打击感先改哪？"], tu=6, bdk=4, lc=13, rc=19,
                bu=3, boom=3, lu=2, mu=8, ground=850),
    "16x9": dict(W=1920, H=1080, title=["打击感先改哪？"], tu=7, bdk=4, lc=17, rc=22,
                 bu=3, boom=3, lu=2, mu=9, ground=870),
    "16x10": dict(W=1600, H=1000, title=["打击感先改哪？"], tu=6, bdk=4, lc=14, rc=20,
                  bu=3, boom=3, lu=2, mu=8, ground=800),
}


def render(name, f):
    W, H = f["W"], f["H"]
    rng = random.Random(404)
    cell = 6
    split = int(round(W * 0.35)) // cell * cell
    img = background(W, H, split, cell, rng)

    # ---- 场景（地平线左右对齐，方便一眼比较）
    gy = f["ground"]
    left, la = build_scene(False)
    right, ra = build_scene(True)
    lc, rc = f["lc"], f["rc"]
    lx0, lx1 = la["hero"][0], la["slime"][2] + 1
    lx = (split - (lx1 - lx0) * lc) // 2 - lx0 * lc
    paste(img, left, lx, gy - GROUND * lc, lc)
    rb = bbox(right)
    rx = split + int((W - split) * 0.44) - int(ra["hit"][0] * rc)
    rx = max(rx, split + 3 * cell - rb[0] * rc)
    ry = gy - GROUND * rc
    paste(img, right, rx, ry, rc)

    # ---- 标题（+ 右上角粉色锯齿徽章，作为一组居中）
    tu = f["tu"]
    badge = ep_badge(rng)
    bdk = f["bdk"]
    bw, bh = badge.shape[1] * bdk, badge.shape[0] * bdk
    y = int(H * 0.03) + bh // 4
    title_rects = []
    for i, s in enumerate(f["title"]):
        tl = text_layer(s, YELLOW, INK, ow=2, shadow=3)
        th, tw = tl.shape[0] * tu, tl.shape[1] * tu
        if len(f["title"]) == 1:
            x = (W - tw - int(bw * 0.7)) // 2
        else:
            x = int(W * 0.04) if i == 0 else W - tw - int(W * 0.03)
        title_rects.append((x, y, tw, th))
        paste(img, tl, x, y, tu)
        y += th - 6 * tu
    title_bottom = y + 6 * tu

    # ---- 左：圆角气泡（尾巴指向小人头顶）
    bu = f["bu"]
    lb, tail = bubble_round("砍空气？", hexc("#4b4b57"), WHITE)
    head_x = lx + (la["hero"][0] + 8) * lc
    head_y = gy - (GROUND - la["hero"][1]) * lc
    bx = min(max(head_x - tail[0] * bu, int(W * 0.015)), split + 4 * cell - lb.shape[1] * bu)
    by = head_y - tail[1] * bu - lc
    by = max(by, title_bottom + int(H * 0.01))
    paste(img, lb, bx, by, bu)

    # ---- 左：底部标签
    lu = f["lu"]
    one = text_layer("同一套动作 · 不加特效", WHITE, ow=0).shape[1] + 16
    lines = ["同一套动作 · 不加特效"] if one * lu < split * 0.92 else ["同一套动作", "不加特效"]
    tg = tag_layer(lines)
    paste(img, tg, (split - tg.shape[1] * lu) // 2, H - tg.shape[0] * lu - int(H * 0.03), lu)

    # ---- 右：爆炸气泡（贴在命中点右上方）
    bk = f["boom"]
    boom = bubble_boom(rng)
    hx, hy = rx + ra["hit"][0] * rc, ry + ra["hit"][1] * rc
    bbx = int(hx + 4 * rc)
    bbx = min(bbx, W - boom.shape[1] * bk - int(W * 0.015))
    bby = int(hy - boom.shape[0] * bk - 2 * rc)
    bby = max(bby, title_bottom - int(H * 0.02))
    paste(img, boom, bbx, bby, bk)

    # ---- 标题右上角：粉色锯齿徽章（只压住描边，不挡字）
    x, y0, tw0, th0 = title_rects[0]
    gx = min(x + tw0 - int(bw * 0.12), W - bw - int(W * 0.012))
    paste(img, badge, gx, y0 - bh // 3, bdk)

    # ---- 右下角：系列吉祥物
    mk = f["mu"]
    ms = mascot_with_bubble()
    paste(img, ms, W - ms.shape[1] * mk - int(W * 0.015), H - ms.shape[0] * mk - int(H * 0.012), mk)

    path = os.path.join(HERE, f"EP04_打击感_封面_{name}.png")
    Image.fromarray(img[..., :3], "RGB").save(path, optimize=True)
    return path


if __name__ == "__main__":
    for name, f in FORMATS.items():
        print(render(name, f))
