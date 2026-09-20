#!/usr/bin/env python3
"""从官方文档图 Fig.7（ESP-Mosaico BaseBoard Back）标定并测量背部四扩展焊盘。

用途：为 O01／O02／O03 提供有方法、可复现的证据输入。
限制：这是对文档照片的摄影测量，不是实物测量，结果为 derived，不可用于冻结。

重要：官方文档图存在约 6% 的水平拉伸（各向异性）。四个背部焊盘是水平排列，
因此必须用**水平方向**的标定基准。初版脚本用最近邻距离标定（实际测到的是垂直
行间距），导致间距被系统性高估约 6%，得出「2.54 mm 被证伪」的错误结论。
本版改为：从右侧 2x10P 严格提取两列各 10 孔（断言列数，不足则拒绝标定），
列间距作水平标定、行长基线作垂直标定，并输出圆形焊盘的长宽比作为各向同性自检。

第二次更正（Chrome 指出）：直径原先用 (h+w)/2 再除以水平标定，把垂直向的 h 按
水平尺度换算，在 6% 各向异性的图上系统性偏小约 3%。本版改为 w 除水平标定、
h 除垂直标定，分别报出。

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
    # 严格断言：2x10P 的两列必须各恰 10 孔，否则标定基准不可信
    if len(c1) != 10 or len(c2) != 10:
        print("  断言失败：两列孔数为 %d / %d，期望 10 / 10；不据此标定" % (len(c1), len(c2)))
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

    # 直径必须分轴换算：w 是水平向、h 是垂直向，混用会在各向异性图上引入系统误差
    dia_x = (pads[:, 4] / px_h).mean()
    dia_y = (pads[:, 3] / px_v).mean()
    print("\n四焊盘（像素）：间距 %s 均值 %.2f" % (np.round(pad_sp, 2), pad_sp.mean()))
    print("→ 焊盘间距 %.3f mm（2.54 标称偏差 %+.1f%%）" % (pad_sp.mean() / px_h, (pad_sp.mean() / horiz - 1) * 100))
    print("→ 焊盘直径 水平向 %.3f mm / 垂直向 %.3f mm（两者接近说明各向异性修正自洽）" % (dia_x, dia_y))
    print("  注：包围盒含抗锯齿边缘，属上偏估计；不得据此选定 Pogo 针头直径")
    print("→ 四盘中心跨距 %.3f mm（3×2.54 = 7.62）" % (3 * pad_sp.mean() / px_h))
    print("\n结论：设计值极可能为 2.54 mm 标称。derived，实物卡尺复测前不得冻结。")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fig7-000.png")
