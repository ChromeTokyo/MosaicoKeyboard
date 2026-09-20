#!/usr/bin/env python3
"""从官方文档图 Fig.7（ESP-Mosaico BaseBoard Back）标定并测量背部四扩展焊盘。

用途：为 O01／O02／O03 提供有方法、可复现的证据输入。
限制：这是对文档照片的摄影测量，不是实物测量，结果为 derived，不可用于冻结。

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

    # 标定：排针孔（环形、近圆）最近邻距 = 2.54 mm
    holes = comp[(circ < 0.25) & (dia > 35) & (dia < 95)][:, [2, 1]]
    regions = {
        "左区 x<500": holes[:, 0] < 500,
        "右区 x>900": holes[:, 0] > 900,
        "上半 y<900": holes[:, 1] < 900,
        "下半 y>900": holes[:, 1] > 900,
    }
    scales = []
    print("标定（检查透视/畸变一致性）：")
    for label, m in regions.items():
        p, sd, k = nn_pitch(holes[m])
        if p:
            scales.append(p / HEADER_PITCH_MM)
            print("  %-12s pitch=%6.2f px (σ=%.2f, n=%d) → %.3f px/mm" % (label, p, sd, k, p / HEADER_PITCH_MM))

    lo, hi = min(scales), max(scales)
    print("\n四焊盘（像素）：间距 %s 均值 %.2f；直径 %.2f" % (np.round(pad_sp, 2), pad_sp.mean(), pad_d))
    print("标定范围 %.3f–%.3f px/mm" % (lo, hi))
    print("→ 焊盘间距 %.2f–%.2f mm" % (pad_sp.mean() / hi, pad_sp.mean() / lo))
    print("→ 焊盘直径 %.2f–%.2f mm" % (pad_d / hi, pad_d / lo))
    print("→ 四盘中心跨距 %.2f–%.2f mm" % (3 * pad_sp.mean() / hi, 3 * pad_sp.mean() / lo))
    print("\n若间距确为 2.54 mm，应测得 %.1f–%.1f px；实测 %.1f px" % (lo * 2.54, hi * 2.54, pad_sp.mean()))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fig7-000.png")
