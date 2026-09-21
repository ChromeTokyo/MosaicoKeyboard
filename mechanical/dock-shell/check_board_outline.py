#!/usr/bin/env python3
# 提案 · 未冻结 · 由 Claude 主控（claude-opus-5）起草 · 待 Chrome 采纳、Hiro／Grok 复核
#
# check_board_outline.py —— 校验 dock_shell.scad 导出的主板外形
#
# 为什么需要：板外形是从外壳内腔**几何减出来**的，不是画出来的。这种做法的好处是
# 外壳一改板框自动跟着改，坏处是「减完之后还剩不剩得下元件」没人保证——比如固定孔
# 落在圆角上会被切掉一块，开关落在落入槽开窗边上会悬空。这些错误如果等到 PCB 布局
# 阶段才发现，就得回头改外壳再重打，正是要避免的往返。本脚本在出 DXF 之后立刻查。
#
# 用法：
#   openscad -o /tmp/b.dxf -D 'PART="board_dxf"' dock_shell.scad
#   python3 check_board_outline.py /tmp/b.dxf
#
# 判据全部来自 dock_shell.scad 的 ASSUMPTION，改那边要同步改这里的 EXPECT 表。
import sys, math

# ---- 期望值（与 dock_shell.scad 的 echo 对齐；改模型须同步改这里）----
EXPECT = {
    'mount_holes': [(-75.10, 24.50), (75.10, 24.50), (-75.10, -60.10), (75.10, -60.10)],
    'mount_d': 2.20,
    'mount_keepout_d': 5.00,
    'dpad': [(-54.0, 5.5), (-63.5, -4.0), (-54.0, -13.5), (-44.5, -4.0)],
    'abxy': [(54.0, 9.0), (41.0, -4.0), (54.0, -17.0), (67.0, -4.0)],
    'lr':   [(-58.0, 26.5), (58.0, 26.5)],   # 键条中心 27.5，开关下移 1.0
    'sw_size': 6.00,
    'sw_keepout': 7.00,        # 开关体 6 见方 + 每边 0.5 焊盘/阻焊
    'bay_x': (-30.545, 25.545),
    'bay_y_floor': -28.395,
    'board_top_y': 30.50,
}

def read_lwpolylines(path):
    """返回 [[(x,y), ...], ...]，每条 LWPOLYLINE 一个点列。"""
    lines = open(path, encoding='utf-8', errors='replace').read().split('\n')
    polys, cur, in_poly = [], None, False
    i = 0
    while i < len(lines) - 1:
        code, val = lines[i].strip(), lines[i + 1].strip()
        if code == '0':
            if in_poly and cur:
                polys.append(cur)
            in_poly = (val == 'LWPOLYLINE')
            cur = [] if in_poly else None
        elif in_poly and code == '10':
            try:
                x = float(val)
                # 紧随其后的 20 是 y
                if lines[i + 2].strip() == '20':
                    cur.append((x, float(lines[i + 3].strip())))
            except (ValueError, IndexError):
                pass
        i += 2
    if in_poly and cur:
        polys.append(cur)
    return polys

def area(poly):
    a = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        a += x1 * y2 - x2 * y1
    return a / 2.0

def point_in(poly, pt):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xin = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xin:
                inside = not inside
    return inside

def dist_to_edges(poly, pt):
    """点到多边形边界的最小距离。"""
    x, y = pt
    best = float('inf')
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L2))
        px, py = x1 + t * dx, y1 + t * dy
        best = min(best, math.hypot(x - px, y - py))
    return best

def main():
    path = sys.argv[1]
    polys = read_lwpolylines(path)
    if not polys:
        print('FAIL: DXF 里没有 LWPOLYLINE'); return 1

    # 面积绝对值最大的那条是板外轮廓，其余是孔与开窗
    polys.sort(key=lambda p: abs(area(p)), reverse=True)
    outer, holes = polys[0], polys[1:]
    xs = [p[0] for p in outer]; ys = [p[1] for p in outer]
    print(f'DXF 轮廓数 = {len(polys)}（外轮廓 1 + 内孔/开窗 {len(holes)}）')
    print(f'板外形 X [{min(xs):.3f}, {max(xs):.3f}]  Y [{min(ys):.3f}, {max(ys):.3f}]'
          f'  → {max(xs)-min(xs):.2f} x {max(ys)-min(ys):.2f} mm，面积上限 {abs(area(outer))/100:.1f} cm²')

    fails = []

    def centroid(poly):
        return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))

    def inside_board(pt, clearance, what, own_hole_r=0.0):
        """点必须在外轮廓内、且到外轮廓与任一内孔边界的距离 ≥ clearance。

        own_hole_r > 0 时，跳过「以 pt 为中心的那个孔」本身——固定孔的中心当然
        落在它自己的孔轮廓里，那不是错误。判据是它的**禁布圆**不碰别的东西。
        """
        if not point_in(outer, pt):
            fails.append(f'{what} {pt} 不在板外形内'); return
        d = dist_to_edges(outer, pt)
        if d < clearance:
            fails.append(f'{what} {pt} 到板边 {d:.3f} mm < 要求 {clearance:.3f}')
        for h in holes:
            cx, cy = centroid(h)
            if own_hole_r > 0 and math.hypot(cx - pt[0], cy - pt[1]) < own_hole_r:
                continue          # 这是它自己的孔
            if point_in(h, pt):
                fails.append(f'{what} {pt} 落在开窗/孔内'); continue
            dh = dist_to_edges(h, pt)
            if dh < clearance:
                fails.append(f'{what} {pt} 到开窗/孔边 {dh:.3f} mm < 要求 {clearance:.3f}')

    def rect_inside_board(pt, half, what):
        """轴对齐方形元件（轻触开关）：判四个角，而不是用外接圆。
        外接圆把方形当成 R = half*√2 的圆，对贴近直边的元件过于保守。"""
        cx, cy = pt
        for dx in (-half, half):
            for dy in (-half, half):
                c = (cx + dx, cy + dy)
                if not point_in(outer, c):
                    fails.append(f'{what} 中心 {pt} 的角 ({c[0]:.2f}, {c[1]:.2f}) 超出板外形')
                    continue
                for h in holes:
                    if point_in(h, c):
                        fails.append(f'{what} 中心 {pt} 的角 ({c[0]:.2f}, {c[1]:.2f}) 落在开窗内')

    # 1) 固定孔：禁布圆必须完整落在板内
    r = EXPECT['mount_keepout_d'] / 2
    for m in EXPECT['mount_holes']:
        inside_board(m, r, f'固定孔禁布圆 Ø{EXPECT["mount_keepout_d"]}',
                     own_hole_r=EXPECT['mount_d'])

    # 2) 按键开关：7 x 7 禁布方（开关体 6 见方 + 每边 0.5）四角须落在板内、不压开窗
    half = EXPECT['sw_keepout'] / 2
    swr = half * math.sqrt(2)      # 供第 3 项的重叠判定用
    for name, pts in (('D-pad', EXPECT['dpad']), ('ABXY', EXPECT['abxy']), ('L/R', EXPECT['lr'])):
        for p in pts:
            rect_inside_board(p, half, f'{name} 开关禁布方 {EXPECT["sw_keepout"]}见方')

    # 3) 固定孔彼此、以及与开关之间不得重叠
    allpts = ([(p, '固定孔', r) for p in EXPECT['mount_holes']]
              + [(p, '开关', half) for p in EXPECT['dpad'] + EXPECT['abxy'] + EXPECT['lr']])
    for i in range(len(allpts)):
        for j in range(i + 1, len(allpts)):
            (p1, n1, r1), (p2, n2, r2) = allpts[i], allpts[j]
            d = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
            if d < r1 + r2 - 1e-9:
                fails.append(f'{n1}{p1} 与 {n2}{p2} 重叠：中心距 {d:.3f} < {r1+r2:.3f}')

    print()
    if fails:
        print(f'✗ 不通过，{len(fails)} 项：')
        for f in fails:
            print(f'  - {f}')
        return 1
    print(f'✓ 全部通过：{len(EXPECT["mount_holes"])} 个固定孔禁布圆、'
          f'{len(EXPECT["dpad"])+len(EXPECT["abxy"])+len(EXPECT["lr"])} 个开关禁布方'
          f'均完整落在板内、不压开窗、互不重叠')
    return 0

if __name__ == '__main__':
    sys.exit(main())
