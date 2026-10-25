#!/usr/bin/env python3
"""EP05《商店页先改哪？》封面生成器 —— 沿用 EP04 的 8bit 像素风组件。

左 35%：灰暗的 Steam 商店胶囊图墙（像素化 + 去色，示意“缩略图认不出”）
右 65%：放射光芒中的《吸血鬼幸存者》真实胶囊图 + 点击光标，“一眼认出”
中间：“只换一张图”粗像素箭头跨过分割线，3 秒讲清主题与价值。

用法：python3 cover/make_cover_ep05.py
素材：cover/src/ep05/（从往期 EP05 封面中截取的胶囊图）
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageEnhance

from make_cover import (BAYER4, CYAN, INK, RED, WHITE, YELLOW, add_outline, background,
                        bubble_boom, bubble_round, dilate, ep_badge, hexc, layer,
                        mascot_with_bubble, paste, round_rect_mask, shift, sprite,
                        tag_layer, text_layer)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src", "ep05")

GRAY_TILES = ["balatro", "celeste", "dome_keeper", "dead_cells", "cult_of_the_lamb",
              "dave_the_diver", "dredge", "halls_of_torment", "slay_the_spire"]
GRAY_RAMP = [hexc(c) for c in ("#2c2c32", "#3e3e45", "#515158", "#66666e", "#7c7c84", "#94949c")]
GREEN = hexc("#38e86a")
SHADOW = hexc("#0d0820")

CURSOR = [
    "X...........",
    "XX..........",
    "XWX.........",
    "XWWX........",
    "XWWWX.......",
    "XWWWWX......",
    "XWWWWWX.....",
    "XWWWWWWX....",
    "XWWWWWWWX...",
    "XWWWWWWWWX..",
    "XWWWWWWWWWX.",
    "XWWWWWWXXXXX",
    "XWWWXWWX....",
    "XWWXXWWX....",
    "XWX..XWWX...",
    "XX...XWWX...",
    "X.....XWWX..",
    "......XWWX..",
    ".......XX...",
]


def cover_fit(im, w, h):
    """等比裁切到 w:h 再缩放（box 采样 = 干净的马赛克）。"""
    sw, sh = im.size
    r = w / h
    if sw / sh > r:
        nw = int(sh * r)
        im = im.crop(((sw - nw) // 2, 0, (sw - nw) // 2 + nw, sh))
    else:
        nh = int(sw / r)
        im = im.crop((0, (sh - nh) // 2, sw, (sh - nh) // 2 + nh))
    return im.resize((w, h), Image.BOX)


def gray_tile(name, w, h):
    """去色 + 压暗压平 + 只留 6 级灰：缩略图挤在一起，谁也认不出谁。"""
    fn = "vampire_survivors.png" if name == "vampire_survivors" else f"gray_{name}.png"
    im = cover_fit(Image.open(os.path.join(SRC, fn)).convert("L"), w, h)
    a = np.asarray(im, float) / 255.0
    a = 0.42 + (a - a.mean()) * 0.8
    idx = np.clip((a * len(GRAY_RAMP)).astype(int), 0, len(GRAY_RAMP) - 1)
    lay = layer(w, h)
    for i, c in enumerate(GRAY_RAMP):
        lay[idx == i] = c
    return lay


def color_capsule(w, h, colors=40):
    """真实胶囊图：降采样 + 提饱和 + 调色板量化，变成像素画但仍一眼可认。"""
    im = cover_fit(Image.open(os.path.join(SRC, "vampire_survivors.png")).convert("RGB"), w, h)
    im = ImageEnhance.Color(im).enhance(1.35)
    im = ImageEnhance.Contrast(im).enhance(1.12)
    im = im.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return np.array(im.convert("RGBA"))


def tile_grid(cols, rows, tw, th, gap, mock_at):
    """商店列表：深色底板 + 灰色胶囊格；mock_at 处放去色版《吸血鬼幸存者》（示意）。"""
    W = cols * tw + (cols + 1) * gap
    H = rows * th + (rows + 1) * gap
    lay = layer(W + 4, H + 4)
    full = np.zeros(lay.shape[:2], bool)
    full[2:2 + H, 2:2 + W][round_rect_mask(W, H, 3)] = True
    lay[dilate(full, 1) & ~full] = INK
    lay[full] = hexc("#141418")
    names = iter(GRAY_TILES * 2)
    for r in range(rows):
        for c in range(cols):
            name = "vampire_survivors" if (r, c) == mock_at else next(names)
            paste(lay, gray_tile(name, tw, th), 2 + gap + c * (tw + gap), 2 + gap + r * (th + gap))
    return lay


def shadowed(full, fill, lay, ow=2, sh=4):
    ol = dilate(full, ow) & ~full
    s = shift(full | ol, sh, sh) & ~(full | ol)
    lay[s] = SHADOW
    lay[ol] = INK
    lay[full] = fill


def chunky_arrow(lines):
    """青色粗像素箭头，箭身内两行黑字。"""
    ts = [text_layer(s, INK, INK, ow=0) for s in lines]
    gap = 3
    tw = max(t.shape[1] for t in ts)
    th = sum(t.shape[0] for t in ts) + gap * (len(ts) - 1)
    bw, bh = tw + 14, th + 12
    head = bh // 2 + 8
    W, H = bw + head + 10, bh + 26
    lay = layer(W, H)
    full = np.zeros((H, W), bool)
    by = (H - bh) // 2
    full[by:by + bh, 3:3 + bw][round_rect_mask(bw, bh, 3)] = True
    cy = H / 2
    for i in range(head):
        half = (H / 2 - 3) * (1 - i / head)
        full[int(cy - half):int(cy + half) + 1, 3 + bw - 2 + i] = True
    shadowed(full, CYAN, lay)
    y = by + 6
    for t in ts:
        paste(lay, t, 3 + (bw - t.shape[1]) // 2, y)
        y += t.shape[0] + gap
    return lay


def up_tag(text):
    """绿色价值贴纸：点击率 + 像素上箭头。"""
    t = text_layer(text, WHITE, INK, ow=2)
    th, tw = t.shape[:2]
    aw = th
    w, h = tw + aw + 12, th + 8
    lay = layer(w + 10, h + 10)
    full = np.zeros(lay.shape[:2], bool)
    full[2:2 + h, 2:2 + w][round_rect_mask(w, h, 4)] = True
    shadowed(full, GREEN, lay)
    paste(lay, t, 2 + 4, 2 + (h - th) // 2)
    arr = layer(aw, th)
    cx, headh = aw // 2, th // 2
    for i in range(headh):
        arr[3 + i, max(cx - i, 0):cx + i + 1] = WHITE
    arr[3 + headh:th - 3, cx - th // 7:cx + th // 7 + 1] = WHITE
    add_outline(arr, INK, r=2, diag=True)
    paste(lay, arr, 2 + 4 + tw, 2 + (h - th) // 2)
    return lay


def framed_capsule(cap, b=2):
    """黄色像素描边 + 黑边 + 硬投影的高亮胶囊。"""
    h, w = cap.shape[:2]
    lay = layer(w + 2 * b + 8, h + 2 * b + 8)
    o = 2
    lay[o + 4:o + h + 2 * b + 6, o + 4:o + w + 2 * b + 6] = SHADOW
    lay[o - 1:o + h + 2 * b + 1, o - 1:o + w + 2 * b + 1] = INK
    lay[o:o + h + 2 * b, o:o + w + 2 * b] = YELLOW
    lay[o + b - 1:o + b + h + 1, o + b - 1:o + b + w + 1] = INK
    paste(lay, cap, o + b, o + b)
    return lay


def sparkle(s):
    lay = layer(2 * s + 1, 2 * s + 1)
    lay[s, :] = WHITE
    lay[:, s] = WHITE
    lay[s - 1:s + 2, s - 1:s + 2] = WHITE
    lay[s, 0] = lay[s, -1] = lay[0, s] = lay[-1, s] = YELLOW
    return lay


def sunburst(img, cx, cy, x0, cell, n=18, lift=(28, 20, 64)):
    """以胶囊为中心的放射光芒：在背景上提亮相间的扇区（保留星光）。"""
    H, W = img.shape[:2]
    gy, gx = np.mgrid[0:H // cell + 1, 0:W // cell + 1]
    px, py = gx * cell + cell / 2, gy * cell + cell / 2
    ang = np.arctan2(py - cy, px - cx) + math.pi
    sector = (ang / (2 * math.pi) * n * 2).astype(int) % 2 == 0
    fade = np.hypot(px - cx, py - cy) / max(W, H)
    keep = sector & (fade * 1.5 < 1 - BAYER4[gy % 4, gx % 4] * 0.5) & (px > x0 + 3 * cell)
    m = keep.repeat(cell, 0).repeat(cell, 1)[:H, :W]
    body = img[..., :3].astype(int)
    body[m] = np.minimum(body[m] + np.array(lift), 255)
    img[..., :3] = body.astype(np.uint8)


def small_label(text, fill, txt):
    t = text_layer(text, txt, INK, ow=1)
    lay = layer(t.shape[1] + 8, t.shape[0] + 6)
    lay[:, :] = INK
    lay[1:-1, 1:-1] = fill
    paste(lay, t, 4, 3)
    return lay


# ---------------------------------------------------------------- 版式
# grid: (列, 行)  tile: 灰色胶囊原生像素  cap: 彩色胶囊原生像素
# cap_c: 胶囊中心 (x 占右区比例, y 像素)  boom_dx: 爆炸气泡中心相对胶囊中心的偏移（胶囊宽度比例）
FORMATS = {
    "3x4": dict(W=1080, H=1440, title=["商店页", "先改哪？"], tu=9, bdk=4,
                grid=(2, 5), tile=(26, 12), gk=5, grid_y=780,
                cap=(180, 79), ck=3, cap_c=(0.56, 1020), boom=3, boom_dx=0.12,
                arrow_k=2, bu=3, uk=2, lu=2, mu=8, sticker="bl"),
    "4x3": dict(W=1440, H=1080, title=["商店页先改哪？"], tu=6, bdk=4,
                grid=(2, 4), tile=(34, 16), gk=5, grid_y=430,
                cap=(180, 79), ck=4, cap_c=(0.53, 690), boom=3, boom_dx=0.18,
                arrow_k=2, bu=3, uk=2, lu=2, mu=8, sticker="tl"),
    "16x9": dict(W=1920, H=1080, title=["商店页先改哪？"], tu=7, bdk=4,
                 grid=(3, 4), tile=(32, 15), gk=5, grid_y=440,
                 cap=(200, 88), ck=4, cap_c=(0.47, 700), boom=3, boom_dx=0.18,
                 arrow_k=2, bu=3, uk=2, lu=2, mu=8, sticker="tl"),
    "16x10": dict(W=1600, H=1000, title=["商店页先改哪？"], tu=6, bdk=4,
                  grid=(3, 4), tile=(26, 12), gk=5, grid_y=420,
                  cap=(180, 79), ck=4, cap_c=(0.49, 650), boom=3, boom_dx=0.18,
                  arrow_k=2, bu=3, uk=2, lu=2, mu=8, sticker="tl"),
}


def render(name, f):
    W, H = f["W"], f["H"]
    rng = random.Random(505)
    cell = 6
    split = int(round(W * 0.35)) // cell * cell
    img = background(W, H, split, cell, rng)

    # ---- 右：胶囊位置先定，放射光芒垫底
    ck = f["ck"]
    fc = framed_capsule(color_capsule(*f["cap"]))
    fw, fh = fc.shape[1] * ck, fc.shape[0] * ck
    cx = split + int((W - split) * f["cap_c"][0])
    cy = f["cap_c"][1]
    fx, fy = cx - fw // 2, cy - fh // 2
    sunburst(img, cx, cy, split, cell)

    # ---- 标题 + EP.05 徽章
    tu = f["tu"]
    badge = ep_badge(rng, "EP.05")
    bdk = f["bdk"]
    bw, bh = badge.shape[1] * bdk, badge.shape[0] * bdk
    y = int(H * 0.03) + bh // 4
    rects = []
    for i, s in enumerate(f["title"]):
        tl = text_layer(s, YELLOW, INK, ow=2, shadow=3)
        th, tw = tl.shape[0] * tu, tl.shape[1] * tu
        if len(f["title"]) == 1:
            x = (W - tw - int(bw * 0.7)) // 2
        else:
            x = int(W * 0.04) if i == 0 else W - tw - int(W * 0.03)
        rects.append((x, y, tw, th))
        paste(img, tl, x, y, tu)
        y += th - 6 * tu
    title_bottom = y + 6 * tu
    x, y0, tw0, _ = rects[0]
    paste(img, badge, min(x + tw0 - int(bw * 0.12), W - bw - int(W * 0.012)), y0 - bh // 3, bdk)

    # ---- 左：灰色胶囊墙 + “示意”角标
    cols, rows = f["grid"]
    gk = f["gk"]
    grid = tile_grid(cols, rows, *f["tile"], 2, (1, cols - 1))
    gw, gh = grid.shape[1] * gk, grid.shape[0] * gk
    gx = max(int(W * 0.018), (split - gw) // 2 - int(split * 0.06))
    gy = f["grid_y"]
    paste(img, grid, gx, gy, gk)
    note = small_label("示意", RED, WHITE)
    paste(img, note, gx + 3 * gk, gy + gh - note.shape[0] * 2 - 3 * gk, 2)

    # ---- 左：“认不出？”气泡（尾巴指向图墙）
    bu = f["bu"]
    lb, _ = bubble_round("认不出？", hexc("#4b4b57"), WHITE)
    lby = max(title_bottom + int(H * 0.005), gy - lb.shape[0] * bu + 6 * gk)
    paste(img, lb, gx - gk, lby, bu)

    # ---- 右：胶囊 + 角落闪光 + 点击光标
    paste(img, fc, fx, fy, ck)
    sk = 5
    sp = sparkle(3)
    paste(img, sp, fx - 4 * sk, fy - 4 * sk, sk)
    paste(img, sp, fx + fw - 4 * sk, fy + fh - 6 * sk, sk)
    curk = ck + 1
    tipx, tipy = fx + int(fw * 0.72), fy + int(fh * 0.66)
    click = layer(17, 17)
    for a in (-165, -125, -85):
        for t in np.linspace(4.5, 7.5, 7):
            click[int(8 + math.sin(math.radians(a)) * t), int(8 + math.cos(math.radians(a)) * t)] = YELLOW
    add_outline(click, INK)
    paste(img, click, tipx - 8 * curk, tipy - 8 * curk, curk)
    cur = sprite(CURSOR, {"W": "#ffffff", "X": "#120c1c"}, outline=YELLOW)
    paste(img, cur, tipx - curk, tipy - curk, curk)

    # ---- 中：“只换 / 一张图”粗箭头跨过分割线，箭尖顶到胶囊
    ak = f["arrow_k"]
    arr = chunky_arrow(["只换", "一张图"])
    aw, ah = arr.shape[1] * ak, arr.shape[0] * ak
    ax = min(split - aw // 2, fx - aw + 6 * ak)
    paste(img, arr, ax, cy - ah // 2, ak)

    # ---- 右：爆炸气泡“一眼认出！”（悬在胶囊上方）
    bk = f["boom"]
    boom = bubble_boom(rng, None, "一眼认出！", big_k=1, pad=(1.3, 2.9))
    bwid, bhei = boom.shape[1] * bk, boom.shape[0] * bk
    bbx = min(cx + int(fw * f["boom_dx"]) - bwid // 2, W - bwid - int(W * 0.01))
    bby = max(title_bottom - int(H * 0.012), fy - bhei + int(bhei * 0.16))
    paste(img, boom, bbx, bby, bk)

    # ---- 右：价值贴纸“点击率↑” + 真实素材说明
    uk = f["uk"]
    ut = up_tag("点击率")
    uw, uh = ut.shape[1] * uk, ut.shape[0] * uk
    cap_note = text_layer("《吸血鬼幸存者》真实胶囊图", hexc("#c9c3ff"), INK, ow=1)
    if f["sticker"] == "tl":
        paste(img, ut, fx - uw // 4, fy - uh // 2, uk)
        paste(img, cap_note, fx + 2 * ck, fy + fh + ck, 1 if W < 1200 else 2)
    else:
        paste(img, ut, fx, fy + fh + ck, uk)
        paste(img, cap_note, fx + 2 * ck, fy + fh + ck + uh + 2 * ck, 1)

    # ---- 左下标签 + 右下吉祥物
    lu = f["lu"]
    tg = tag_layer(["真实商店页案例"])
    paste(img, tg, (split - tg.shape[1] * lu) // 2, H - tg.shape[0] * lu - int(H * 0.03), lu)
    mk = f["mu"]
    ms = mascot_with_bubble()
    paste(img, ms, W - ms.shape[1] * mk - int(W * 0.015), H - ms.shape[0] * mk - int(H * 0.012), mk)

    path = os.path.join(HERE, f"EP05_商店页_封面_{name}.png")
    Image.fromarray(img[..., :3], "RGB").save(path, optimize=True)
    return path


if __name__ == "__main__":
    for name, f in FORMATS.items():
        print(render(name, f))
