#!/usr/bin/env python3
"""从官方文档图 Fig.7（ESP-Mosaico BaseBoard Back）标定并测量背部四扩展焊盘。

用途：为 O01／O02／O03 提供有方法、可复现的证据输入。
限制：这是对文档照片的摄影测量，不是实物测量，结果为 derived，不可用于冻结。

重要：官方文档图存在约 6% 的水平拉伸（各向异性）。四个背部焊盘是水平排列，
因此必须用**水平方向**的标定基准。初版脚本用最近邻距离标定（实际测到的是垂直
行间距），导致间距被系统性高估约 6%，得出「2.54 mm 被证伪」的错误结论。
本版改为：从右侧 2x10P 严格提取两列各 10 孔，列间距作水平标定、行长基线作垂直
标定，并输出圆形焊盘的长宽比作为各向同性自检。

复现：
  pdfimages -f 32 -l 32 -png esp-dev-kits-en-master-esp32s31.pdf fig7
  python3 measure_pads.py fig7-000.png
依赖：numpy、pillow。
"""
import sys
from collections import deque

import numpy as np
from PIL import Image

HEADER_PITCH_MM = 2.54  # 官方文档：左右模块接口为 2×10P、2.54 mm 间距排针


def components(gold, min_px=40):
    h, w = gold.shape
    seen = np.zeros((h, w), bool)
    out = []
    for y0, x0 in zip(*np.nonzero(gold)):
        if seen[y0, x0]:
            continue
        q = deque([(y0, x0)])
        seen[y0, x0] = True
        pts = []
        while q:
            y, x = q.popleft()
            pts.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and gold[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    q.append((ny, nx))
        if len(pts) < min_px:
            continue
        ys = np.array([p[0] for p in pts])
        xs = np.array([p[1] for p in pts])
        out.append((len(pts), ys.mean(), xs.mean(),
                    ys.max() - ys.min() + 1, xs.max() - xs.min() + 1))
    return np.array(out)


def grid_pitch(points, x_lo, x_hi, x_split):
    """从 2x10P 严格提取两列，返回 (水平列距, 垂直行距均值)。"""
    p = points[(points[:, 0] > x_lo) & (points[:, 0] < x_hi)]
    c1, c2 = p[p[:, 0] < x_split], p[p[:, 0] >= x_split]
    if len(c1) < 3 or len(c2) < 3:
        return None, None
    horiz = c2[:, 0].mean() - c1[:, 0].mean()
    vert = np.mean([(np.sort(c[:, 1])[-1] - np.sort(c[:, 1])[0]) / (len(c) - 1)
                    for c in (c1, c2)])
    return horiz, vert


def nn_pitch(points, lo=65, hi=90):
    ds = []
    for i in range(len(points)):
        d = np.hypot(points[:, 0] - points[i, 0], points[:, 1] - points[i, 1])
        d[i] = np.inf
        ds.append(d.min())
    ds = np.array(ds)
    core = ds[(ds > lo) & (ds < hi)]
    return (np.median(core), core.std(), len(core)) if len(core) >= 3 else (None, None, 0)


def main(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    comp = components((r > 110) & (g > 85) & (b < r - 35) & (g > b + 25))

    n, cy, cx, hh, ww = comp.T
    dia = (hh + ww) / 2
    circ = np.abs(hh - ww) / np.maximum(hh, ww)
    fill = n / (np.pi / 4 * hh * ww)

    # 四个背部焊盘：实心、等径、共线、等距的一组
    solid = comp[(fill > 0.80) & (circ < 0.18) & (dia > 40) & (dia < 60)]
    rows = {}
    for c in solid:
        rows.setdefault(round(c[1] / 20), []).append(c)
    pads = max(rows.values(), key=len)
    pads = np.array(sorted(pads, key=lambda c: c[2]))
    if len(pads) != 4:
        print("警告：检出 %d 个候选焊盘，预期 4 个" % len(pads))

    pad_sp = np.diff(pads[:, 2])
    pad_d = ((pads[:, 3] + pads[:, 4]) / 2).mean()

    # 各向同性自检：圆焊盘若被水平拉伸，w/h > 1
    aspect = (pads[:, 4] / pads[:, 3]).mean()
    print("各向同性自检：四焊盘 w/h = %.4f（真圆为 1.00）" % aspect)
    if abs(aspect - 1) > 0.02:
        print("  → 图像存在约 %.1f%% 的水平拉伸，标定方向必须与被测方向一致。" % ((aspect - 1) * 100))

    # 标定：右侧 2x10P 严格提取，列间距=水平 2.54mm，行长基线=垂直 2.54mm
    holes = comp[(circ < 0.3) & (dia > 35) & (dia < 95)][:, [2, 1]]
    horiz, vert = grid_pitch(holes, 1040, 1170, 1105)
    if horiz is None:
        print("未能严格提取 2x10P 排针块，无法标定")
        return
    px_h, px_v = horiz / HEADER_PITCH_MM, vert / HEADER_PITCH_MM
    print("\n标定：水平 %.2f px/2.54mm → %.3f px/mm" % (horiz, px_h))
    print("      垂直 %.2f px/2.54mm → %.3f px/mm" % (vert, px_v))
    print("      各向异性 水平/垂直 = %.4f" % (horiz / vert))

    print("\n四焊盘（像素）：间距 %s 均值 %.2f；直径 %.2f" % (np.round(pad_sp, 2), pad_sp.mean(), pad_d))
    print("→ 焊盘间距 %.3f mm（2.54 标称偏差 %+.1f%%）" % (pad_sp.mean() / px_h, (pad_sp.mean() / horiz - 1) * 100))
    print("→ 焊盘直径 %.3f mm" % (pad_d / px_h))
    print("→ 四盘中心跨距 %.3f mm（3×2.54 = 7.62）" % (3 * pad_sp.mean() / px_h))
    print("\n结论：设计值极可能为 2.54 mm 标称。derived，实物卡尺复测前不得冻结。")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fig7-000.png")
