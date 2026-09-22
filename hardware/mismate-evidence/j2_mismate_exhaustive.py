#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
j2_mismate_exhaustive.py —— J2 触点场（底座弹簧针 ↔ 模块板焊盘）错位**穷举**判定器

提案 · 未冻结 · 不得据以制造。

目的
----
触点场由 2 行 × 8 列改为 4 行 × 4 列后，PINMAP 第 3/4 节逐针表与 ICD 第 3.3 节
后果分析全部作废。本脚本重做这件事，并正面关闭 Grok R0 的：

  G04（review/grok/R0/REPORT.md，仅存于 origin/grok/r0-design-review）
       「ICD §3.3『X−1 列无损』论证偏弱 …… 底座 GND 针落到模块 DOCK_5V／SLOT_5V_IN
         焊盘 ⇒ 主机 5V_IN 网络对底座地」
  G05  「错位枚举未覆盖对角／多列组合；ICD §3.3 仅列 ±1 列、错一行、绕 Y 180°」

本脚本与既有分析的根本差别（三条，前两条决定结论）
--------------------------------------------------
1. **接触是「针 ↔ 铜」，不是「针 ↔ 网」。** 模块侧哑位焊盘是**孤立铜**，它自己不属于
   任何网，但它是导体。两根底座针若同时压住同一块孤立铜，这块铜就是一根**导线**，
   把两根底座针短接起来。逐针对照表（一针配一焊盘）结构上看不见这类通路。
   本脚本把每块焊盘铜与每根针都建成**独立图节点**，用并查集求连通分量，
   多跳通路自动浮现。

2. **穷举靠的是引理，不是采样。** 针场与焊盘场同为间距 P = 2.54 的 4×4 方阵，
   故针 (a,b) 与焊盘 (a+u, b+v) 的接触条件只依赖偏移 (u,v)：
        接触 ⟺ |δ − L(u,v)| < R,   L(u,v) = (u·P, −v·P),  R = 1.45
   即：δ 平面上以 7×7 个格点为心、半径 R 的圆盘。于是

     **引理（本脚本运行时以 401×401 稠密网格独立复验）**：因 2R = 2.90 > P = 2.54
     而 √2·P = 3.59 > 2R，任一 δ 至多落入 **2** 个圆盘，且落入 2 个时这两个格点
     必**轴向相邻**。

   所以「所有平移」——任意方向、任意大小、对角、错多列、非整数格、半格桥接——
   被压缩成一张**有限且完备**的情形表：
        情形 A：0 个偏移（完全不接触）
        情形 B：1 个偏移，(u,v) ∈ [−3,3]²      → 49 个
        情形 C：2 个轴向相邻偏移               → 半格桥接／部分接触瞬态
   这正是 G05 要的「穷举而不是举例」。每个情形取其区域内**到原点距离最小的点**
   作为「最小触发位移」，与落入槽腔体允许的位移包络直接比较。

3. **危险分级区分「被地钳位」与否。** 5 V 节点若同时经**纯铜**连到地，
   底座限流动作、电压塌陷；若只经 1 kΩ 串阻连到 GPIO 而无地钳位，才是直击。

坐标系：屏幕朝使用者，USB-C 朝下。X 右、Y 上、Z 朝使用者，原点在 Mosaico 几何中心。
本脚本只在 XZ 平面内算（弹簧针轴向 +Y）。

用法
----
    python3 hardware/j2_mismate_exhaustive.py              # 跑 ACTIVE 方案
    python3 hardware/j2_mismate_exhaustive.py --all        # 连同全部对照方案
    python3 hardware/j2_mismate_exhaustive.py --verbose    # 打印良性事件

退出码：0 = 无可达致命事件；1 = 有可达致命事件；2 = 结构性自检失败。
纯 python3 标准库。

数值来源
--------
[ECHO-M] 本人实跑 `openscad -o mb.stl module_board.scad`，源
         `git show origin/claude/design-d/mech-module:mechanical/module-board/module_board.scad`
         （2314 顶点 / 4768 面）：
           "J2 列 1..4 中心 X = [-34.405, -31.865, -29.325, -26.785]"
           "J2 行 A..4 中心 Z = [2.75, 0.21, -2.33, -4.87]（行 A 在 +Z 屏侧）"
           "触点板 pad_board（XZ 面）：X [-36.095 , -25.095]  Z [-6.46 , 4.34]"
           "J3 双排：两排 X = -26.135 / -27.735"
           "[检查 6] …… 允许偏移 = 0.55 mm，余量 = 0.1 mm。相邻焊盘净间距 0.54 mm"
[ECHO-D] 本人实跑 `openscad -o ds.stl dock_shell.scad`，源
         `git show origin/claude/design-d/mech-dock:mechanical/dock-shell/dock_shell.scad`
         （13920 顶点 / 28472 面 —— 注：任务书转述的 14238/29152 与我实测不符，以本值为准）：
           "ICD-CONTRACT|DOCK_PAD_D|2"  "|DOCK_PIN_TIP_D|0.9"  "|DOCK_X_TOL|0.45"  "|DOCK_Z_TOL|0.45"
           "ICD-CONTRACT|BAY_X_LO|-37.845"  "|BAY_X_HI|22.945"  "|BAY_Z_LO|-8.01"  "|BAY_Z_HI|5.89"
           "落入槽模块条带：X ≤ -22.945  Z = [-8.01, 5.89]"
           "ICD-CONTRACT|DOCK_PIN_FORCE_N|0.6"
[PINMAP] /private/tmp/wt-module-board/hardware/module-board/PINMAP.md 第 2 节
         KEY_* → H2 针 → GPIO（本脚本逐条复核过，P2 未改动其中任何一行）。
[NET]    同分支 netlist.yaml `h2_contract:` 17=5V_IN 18=5V_OUT 19=VCC_3V3 20=GND。
[ICD]    hardware/ICD-0.2-DRAFT.md 第 4 节 EL-D-02（pin 18 焊盘不连铜）、
         EL-D-05（按键为无源开关接 DOCK_GND，拉高由主机内部上拉提供，禁 5 V 上拉）、
         EL-D-01/EL-D-12（DOCK_5V 为纯硬件限流输出）。
[推导]   接触阈值 R = (Ø焊盘 + Ø针尖)/2 = (2.0 + 0.9)/2 = 1.45 mm —— 铜对铜**有搭接**的
         中心距上限。注意与 scad [检查 6] 的 0.55 mm 不是一回事：0.55 是「针尖整体落在
         焊盘内」即接触**可靠**的判据。判「碰没碰上」必须用 1.45，用 0.55 会漏掉
         全部桥接情形。现有文档只有 0.55，这是缺口。
"""

import argparse
import itertools
import math
import sys
from collections import defaultdict, deque

# =============================================================================
# §0  数据表 —— 换方案只需改这一节
# =============================================================================

PITCH = 2.54            # [ECHO-M/D] DOCK_PITCH
NCOL = 4                # [ECHO-D] DOCK_COLS
NROW = 4                # [ECHO-D] DOCK_ROWS
X0 = -34.405            # [ECHO-M] 列 1 中心 X
Z0 = 2.750              # [ECHO-M] 行 A 中心 Z
PAD_D = 2.0             # [ECHO-D] DOCK_PAD_D
PIN_TIP_D = 0.9         # [ECHO-D] DOCK_PIN_TIP_D
DOCK_X_TOL = 0.45       # [ECHO-D] DOCK_X_TOL
DOCK_Z_TOL = 0.45       # [ECHO-D] DOCK_Z_TOL

R_TOUCH = (PAD_D + PIN_TIP_D) / 2.0     # 1.45 [推导] 铜对铜搭接阈值
R_RELIABLE = (PAD_D - PIN_TIP_D) / 2.0  # 0.55 [推导] 针尖整体入盘（可靠接触）

BOARD_X = (-36.095, -25.095)   # [ECHO-M] 触点板外形
BOARD_Z = (-6.460, 4.340)
BAY_X = (-37.845, -22.945)     # [ECHO-D] 落入槽模块条带（-X 端为腔体端）
BAY_Z = (-8.010, 5.890)
J3_ROW_X = (-26.135, -27.735)  # [ECHO-M] J3 两排落脚线

ROW_NAME = ["A", "B", "C", "D"]

# ---- 0.1 KEY_* → H2 针 → 主机 GPIO（[PINMAP] 第 2 节原值，逐条核对过）----
KEY_TO_H2 = {
    "KEY_UP": (1, "GPIO55"), "KEY_DOWN": (3, "GPIO19"),
    "KEY_LEFT": (5, "GPIO18"), "KEY_RIGHT": (7, "GPIO17"),
    "KEY_L": (9, "GPIO16"), "KEY_R": (11, "GPIO15"),
    "KEY_A": (2, "GPIO53"), "KEY_B": (4, "GPIO48"),
    "KEY_X": (6, "GPIO13"), "KEY_Y": (8, "GPIO12"),
}
H2_5V_IN, H2_5V_OUT, H2_3V3, H2_GND = 17, 18, 19, 20   # [NET]
I2C_NETS = {"DOCK_SDA": (16, "GPIO0_SDA"), "DOCK_SCL": (14, "GPIO1_SCL")}  # [NET]

# ---- 0.2 待检验的分配表 ----
# 键 = (列索引 0..3, 行索引 0..3=A..D)；值 = 网名。
# 同一格的底座针与模块焊盘取同名（设计意图）。
# 网名语义：DOCK_5V / DOCK_GND / KEY_* / DOCK_SDA / DOCK_SCL / DUMMY_*（孤立铜）

ALLOC_P2 = {   # 待检验的「方案 P2：角位 5V ＋ 哑位护城河」，9 键硬线、弃 I²C
    (0, 0): "DOCK_GND", (1, 0): "KEY_UP",    (2, 0): "DUMMY_1", (3, 0): "DOCK_5V",
    (0, 1): "KEY_L",    (1, 1): "KEY_DOWN",  (2, 1): "DUMMY_2", (3, 1): "DUMMY_3",
    (0, 2): "KEY_A",    (1, 2): "KEY_LEFT",  (2, 2): "KEY_B",   (3, 2): "KEY_X",
    (0, 3): "DOCK_GND", (1, 3): "KEY_RIGHT", (2, 3): "KEY_Y",   (3, 3): "DUMMY_4",
}

# 对照 1：旧 2 行 × 8 列表（ICD 3.2）朴素折成 4×4（列 1-4 放原列 1-4，行 C/D 放原列 5-8）
ALLOC_NAIVE = {
    (0, 0): "DOCK_5V",  (1, 0): "DOCK_GND", (2, 0): "KEY_UP",    (3, 0): "KEY_LEFT",
    (0, 1): "DOCK_5V",  (1, 1): "DOCK_GND", (2, 1): "KEY_DOWN",  (3, 1): "KEY_RIGHT",
    (0, 2): "KEY_L",    (1, 2): "KEY_A",    (2, 2): "KEY_X",     (3, 2): "DOCK_SDA",
    (0, 3): "KEY_R",    (1, 3): "KEY_B",    (2, 3): "KEY_Y",     (3, 3): "DOCK_SCL",
}

# 对照 2：把 P2 的四个哑位换成 DOCK_GND，其余完全不动。
# 用来回答「孤立哑位 vs 接地焊盘，哪个更安全」——提案 §5.2.4 断言哑位严格更优。
ALLOC_P2_GNDMOAT = dict(ALLOC_P2)
for _k in [(2, 0), (2, 1), (3, 1), (3, 3)]:
    ALLOC_P2_GNDMOAT[_k] = "DOCK_GND"

# 对照 3：P2 但底座侧哑位针**不装**（孔位空着，无针）。丢掉 4×0.6 = 2.4 N 压力。
ALLOC_P2_NOPIN = dict(ALLOC_P2)

# 对照 4【修正提案】：P2 但模块侧哑位**不做焊盘、整片无铜**（裸阻焊），底座侧照装弹簧针。
#   —— 针照压、9.6 N 与对称分布一个不变（MATING.md 预压链不动），
#      但那四个位置没有任何导体，无法充当「跳板」。
DUMMY_SITES = frozenset([(2, 0), (2, 1), (3, 1), (3, 3)])
ALLOC_P2_NOCOPPER = dict(ALLOC_P2)

SCHEMES = [
    ("P2：角位 5V ＋ 哑位护城河（9 键，弃 I²C）【待检验】", ALLOC_P2, set(), set()),
    ("对照 A：旧 2×8 表朴素折成 4×4（无防错）", ALLOC_NAIVE, set(), set()),
    ("对照 B：P2 但护城河改用 DOCK_GND 焊盘", ALLOC_P2_GNDMOAT, set(), set()),
    ("对照 C：P2 但底座侧哑位不装针（丢 2.4 N）", ALLOC_P2_NOPIN, set(DUMMY_SITES), set()),
    ("对照 D【修正提案】：P2 但模块侧哑位无铜、底座仍装针", ALLOC_P2_NOCOPPER, set(), set(DUMMY_SITES)),
]

# 阻抗等级：可致损的导通（≤1 kΩ）计入连通；1 MΩ 只算泄漏。
Z_HARD = "HARD"     # 纯铜 / 弹簧针接触，≈0 Ω
Z_1K = "R1K"        # R_S_KEY_* 串阻 1 kΩ（[PINMAP] 第 2 节，提案值）
Z_1M = "R1M"        # 哑位针泄放电阻 1 MΩ（P2 提案）
Z_SW = "SW"         # 底座轻触开关，按下才导通

CONDUCTING = {Z_HARD, Z_1K}   # 判「危险连通」时计入的等级


# =============================================================================
# §1  几何
# =============================================================================

def site_pos(c, r):
    """格位 (列索引, 行索引) 的 XZ 坐标。"""
    return (X0 + c * PITCH, Z0 - r * PITCH)


def _self_check_geometry():
    """把 §0 的常数与 [ECHO] 原文交叉验证，不通过直接退出 2。"""
    errs = []
    want_x = [-34.405, -31.865, -29.325, -26.785]
    want_z = [2.75, 0.21, -2.33, -4.87]
    for c in range(NCOL):
        if abs(site_pos(c, 0)[0] - want_x[c]) > 1e-9:
            errs.append("列 %d 中心 X 推算 %.3f ≠ ECHO %.3f" % (c + 1, site_pos(c, 0)[0], want_x[c]))
    for r in range(NROW):
        if abs(site_pos(0, r)[1] - want_z[r]) > 1e-9:
            errs.append("行 %s 中心 Z 推算 %.3f ≠ ECHO %.3f" % (ROW_NAME[r], site_pos(0, r)[1], want_z[r]))
    # 场心必须落在触点板中心，J3 落脚线必须偏心（这是 D4 实物防呆的唯一依据）
    field_cx = (site_pos(0, 0)[0] + site_pos(NCOL - 1, 0)[0]) / 2.0
    board_cx = sum(BOARD_X) / 2.0
    if abs(field_cx - board_cx) > 1e-9:
        errs.append("触点场心 X %.3f ≠ 触点板心 X %.3f" % (field_cx, board_cx))
    if errs:
        for e in errs:
            print("自检失败：" + e)
        sys.exit(2)
    return board_cx


def translation_envelope():
    """落入槽腔体允许的 δ（针场相对焊盘场的平移）包络，纯平移。

    板在腔内可动范围 → δ = −（板位移）。
    """
    dbx_lo = BAY_X[0] - BOARD_X[0]      # 板可向 −X 移动多少（负值）
    dbx_hi = BAY_X[1] - BOARD_X[1]      # 板可向 +X 移动多少（正值）
    dbz_lo = BAY_Z[0] - BOARD_Z[0]
    dbz_hi = BAY_Z[1] - BOARD_Z[1]
    return (-dbx_hi, -dbx_lo), (-dbz_hi, -dbz_lo)


DELTA_X_RANGE, DELTA_Z_RANGE = translation_envelope()
DELTA_MAX_NORM = math.hypot(max(abs(DELTA_X_RANGE[0]), abs(DELTA_X_RANGE[1])),
                            max(abs(DELTA_Z_RANGE[0]), abs(DELTA_Z_RANGE[1])))


def delta_reachable(dx, dz):
    eps = 1e-9
    return (DELTA_X_RANGE[0] - eps <= dx <= DELTA_X_RANGE[1] + eps and
            DELTA_Z_RANGE[0] - eps <= dz <= DELTA_Z_RANGE[1] + eps)


# =============================================================================
# §2  δ 平面的完备情形表（引理 + 运行时复验）
# =============================================================================

def lattice(u, v):
    return (u * PITCH, -v * PITCH)


def offsets_at(delta, umax=5):
    """δ 落入哪些偏移圆盘。"""
    out = []
    for u in range(-umax, umax + 1):
        for v in range(-umax, umax + 1):
            lx, lz = lattice(u, v)
            if math.hypot(delta[0] - lx, delta[1] - lz) < R_TOUCH - 1e-12:
                out.append((u, v))
    return out


def verify_lemma(n=401, span=6.0):
    """稠密复验：任一 δ 至多落入 2 个圆盘，且落 2 个时轴向相邻。"""
    worst = 0
    bad = []
    for i in range(n):
        dx = -span + 2 * span * i / (n - 1)
        for j in range(n):
            dz = -span + 2 * span * j / (n - 1)
            o = offsets_at((dx, dz))
            worst = max(worst, len(o))
            if len(o) >= 2:
                if len(o) > 2:
                    bad.append(((dx, dz), o))
                else:
                    (u1, v1), (u2, v2) = o
                    if abs(u1 - u2) + abs(v1 - v2) != 1:
                        bad.append(((dx, dz), o))
    return worst, bad


def circle_intersections(L1, L2, R):
    d = math.hypot(L2[0] - L1[0], L2[1] - L1[1])
    if d > 2 * R or d < 1e-12:
        return []
    a = d / 2.0
    h2 = R * R - a * a
    if h2 < 0:
        return []
    h = math.sqrt(h2)
    mx = (L1[0] + L2[0]) / 2.0
    mz = (L1[1] + L2[1]) / 2.0
    ux, uz = (L2[0] - L1[0]) / d, (L2[1] - L1[1]) / d
    return [(mx - uz * h, mz + ux * h), (mx + uz * h, mz - ux * h)]


def region_min_norm(Ls):
    """到原点距离最小的、落在全部给定圆盘内的点；返回 (‖δ‖, δ)。"""
    def inside_all(p):
        return all(math.hypot(p[0] - L[0], p[1] - L[1]) <= R_TOUCH + 1e-9 for L in Ls)
    if inside_all((0.0, 0.0)):
        return 0.0, (0.0, 0.0)
    cands = []
    for L in Ls:                       # 各圆边界上离原点最近的点
        n = math.hypot(L[0], L[1])
        if n > 1e-12:
            cands.append((L[0] - R_TOUCH * L[0] / n, L[1] - R_TOUCH * L[1] / n))
    for A, B in itertools.combinations(Ls, 2):   # 圆-圆交点（透镜角点）
        cands.extend(circle_intersections(A, B, R_TOUCH))
    best = None
    for p in cands:
        if inside_all(p):
            nn = math.hypot(p[0], p[1])
            if best is None or nn < best[0]:
                best = (nn, p)
    return best if best else (float("inf"), None)


def enumerate_delta_cases():
    """**完备**情形表。每项 = (标签, 偏移集合, 最小‖δ‖, 该最小点 δ)。"""
    cases = []
    lim = max(NCOL, NROW) - 1              # 超出 ±3 的偏移不产生任何接触
    # 情形 B：单偏移
    for u in range(-lim, lim + 1):
        for v in range(-lim, lim + 1):
            L = lattice(u, v)
            mn, p = region_min_norm([L])
            cases.append(("单偏移 (ΔX=%+d列, ΔZ=%+d行)" % (u, v), [(u, v)], mn, p))
    # 情形 C：两个轴向相邻偏移（半格桥接／部分接触瞬态）
    ext = lim + 1
    for u in range(-ext, ext + 1):
        for v in range(-ext, ext + 1):
            for du, dv in ((1, 0), (0, 1)):
                u2, v2 = u + du, v + dv
                if not (-ext <= u2 <= ext and -ext <= v2 <= ext):
                    continue
                if max(abs(u), abs(v)) > lim and max(abs(u2), abs(v2)) > lim:
                    continue      # 两个偏移都出场，无接触
                Ls = [lattice(u, v), lattice(u2, v2)]
                mn, p = region_min_norm(Ls)
                if mn == float("inf"):
                    continue
                cases.append(("桥接 (%+d,%+d)/(%+d,%+d)" % (u, v, u2, v2),
                              [(u, v), (u2, v2)], mn, p))
    return cases


# =============================================================================
# §3  电路模型（并查集 + 多跳通路重建）
# =============================================================================

class Graph(object):
    def __init__(self):
        self.adj = defaultdict(list)     # node -> [(other, zclass, why)]

    def add(self, a, b, z, why):
        self.adj[a].append((b, z, why))
        self.adj[b].append((a, z, why))

    def components(self, allowed):
        parent = {}

        def find(x):
            parent.setdefault(x, x)
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for a in list(self.adj):
            find(a)
            for b, z, _ in self.adj[a]:
                if z in allowed:
                    ra, rb = find(a), find(b)
                    if ra != rb:
                        parent[ra] = rb
        return find

    def path(self, src, dst, allowed):
        if src not in self.adj or dst not in self.adj:
            return None
        prev = {src: None}
        q = deque([src])
        while q:
            cur = q.popleft()
            if cur == dst:
                out = []
                node = dst
                while prev[node] is not None:
                    p, why = prev[node]
                    out.append((p, why, node))
                    node = p
                return list(reversed(out))
            for nb, z, why in self.adj[cur]:
                if z in allowed and nb not in prev:
                    prev[nb] = (cur, why)
                    q.append(nb)
        return None


def build_graph(alloc, contacts, pressed_keys, absent_pins, absent_pads=frozenset()):
    """contacts = [((pin_c,pin_r), (pad_c,pad_r)), ...]

    absent_pins : 底座侧该格位不装弹簧针
    absent_pads : 模块侧该格位**整片无铜**（连孤立焊盘都没有）——注意这与「孤立哑位焊盘」
                  是两件不同的事：孤立焊盘仍是导体，可充当跳板；无铜则不能。
    """
    g = Graph()
    # --- 模块焊盘铜 → 主机网 ---
    for (c, r), net in alloc.items():
        if (c, r) in absent_pads:
            continue
        pad = ("PAD", c, r)
        g.adj[pad]  # 建节点
        if net == "DOCK_5V":
            g.add(pad, ("HOST", "5V_IN"), Z_HARD, "J1 pin17 纯铜（硬约束 1 禁串联器件）")
        elif net == "DOCK_GND":
            g.add(pad, ("HOST", "GND"), Z_HARD, "J1 pin20 纯铜")
        elif net in KEY_TO_H2:
            pin, gpio = KEY_TO_H2[net]
            g.add(pad, ("HOST", gpio), Z_1K, "%s 经 R_S_%s 1kΩ 到 H2 pin%d" % (net, net, pin))
        elif net in I2C_NETS:
            pin, gpio = I2C_NETS[net]
            g.add(pad, ("HOST", gpio), Z_HARD, "%s 经 R_LINK（0Ω，若装）到 H2 pin%d" % (net, pin))
        elif net.startswith("DUMMY"):
            pass          # 孤立铜：本身是导体，但不连任何网
        else:
            raise SystemExit("未知模块侧网名 %r" % net)
    # --- 底座弹簧针 → 底座网 ---
    for (c, r), net in alloc.items():
        if (c, r) in absent_pins:
            continue
        pin = ("PIN", c, r)
        g.adj[pin]
        if net == "DOCK_5V":
            g.add(pin, ("DOCK", "5V_RAIL"), Z_HARD, "底座 BOOST_5V 经限流/防反灌（EL-D-01）")
        elif net == "DOCK_GND":
            g.add(pin, ("DOCK", "GND_RAIL"), Z_HARD, "底座地")
        elif net in KEY_TO_H2:
            z = Z_HARD if net in pressed_keys else Z_SW
            g.add(pin, ("DOCK", "GND_RAIL"), z, "轻触开关%s→DOCK_GND（EL-D-05）"
                  % ("【按下】" if net in pressed_keys else "【未按】"))
        elif net in I2C_NETS:
            pass          # 底座侧 I²C 器件，不接电源不接上拉（硬约束 5/6）
        elif net.startswith("DUMMY"):
            g.add(pin, ("DOCK", "GND_RAIL"), Z_1M, "哑位针经 1 MΩ 泄放到 DOCK_GND")
    # --- 接触 ---
    for (pc, pr), (dc, dr) in contacts:
        g.add(("PIN", pc, pr), ("PAD", dc, dr), Z_HARD,
              "弹簧针(列%d,行%s) 压住 焊盘(列%d,行%s)" % (pc + 1, ROW_NAME[pr], dc + 1, ROW_NAME[dr]))
    return g


def contacts_for(offsets, absent_pins, absent_pads=frozenset()):
    out = []
    for (u, v) in offsets:
        for a in range(NCOL):
            for b in range(NROW):
                c, r = a + u, b + v
                if (0 <= c < NCOL and 0 <= r < NROW
                        and (a, b) not in absent_pins and (c, r) not in absent_pads):
                    out.append(((a, b), (c, r)))
    return out


def node_label(n, alloc):
    if n[0] == "PAD":
        return "模块焊盘(列%d,行%s)=%s" % (n[1] + 1, ROW_NAME[n[2]], alloc[(n[1], n[2])])
    if n[0] == "PIN":
        return "底座针(列%d,行%s)=%s" % (n[1] + 1, ROW_NAME[n[2]], alloc[(n[1], n[2])])
    if n[0] == "HOST":
        return "主机 " + n[1]
    return "底座 " + n[1]


def fmt_path(p, alloc):
    if not p:
        return "（无）"
    s = node_label(p[0][0], alloc)
    for a, why, b in p:
        s += "\n              --[%s]--> %s" % (why, node_label(b, alloc))
    return s


# =============================================================================
# §4  判据
# =============================================================================

def assess(alloc, offsets, absent_pins, pressed_keys, absent_pads=frozenset()):
    """返回本 δ 情形下的事件列表。"""
    contacts = contacts_for(offsets, absent_pins, absent_pads)
    g = build_graph(alloc, contacts, pressed_keys, absent_pins, absent_pads)
    find = g.components(CONDUCTING)
    find_hard = g.components({Z_HARD})

    gpio_nodes = sorted({("HOST", gp) for _, gp in KEY_TO_H2.values()} |
                        {("HOST", gp) for _, gp in I2C_NETS.values()})
    gpio_nodes = [n for n in gpio_nodes if n in g.adj]
    src5v = [("DOCK", "5V_RAIL"), ("HOST", "5V_IN")]
    gnds = [("DOCK", "GND_RAIL"), ("HOST", "GND")]

    ev = []
    # 判据 1：任何 5 V 源 ↔ 任何 GPIO
    for s in src5v:
        if s not in g.adj:
            continue
        for gp in gpio_nodes:
            if find(s) == find(gp):
                clamped = any(gnd in g.adj and find_hard(s) == find_hard(gnd) for gnd in gnds)
                ev.append(("F" if not clamped else "F-钳位",
                           "5 V 源(%s) 接通主机 %s" % (s[1], gp[1]),
                           g.path(s, gp, CONDUCTING)))
    # 判据 3（G04）：主机 5V_IN ↔ 地
    if ("HOST", "5V_IN") in g.adj:
        for gnd in gnds:
            if gnd in g.adj and find(("HOST", "5V_IN")) == find(gnd):
                ev.append(("S", "主机 5V_IN 接通 %s（G04 方向）" % ("底座地" if gnd[0] == "DOCK" else "主机地"),
                           g.path(("HOST", "5V_IN"), gnd, CONDUCTING)))
    # 判据 4：GPIO ↔ GPIO
    for a, b in itertools.combinations(gpio_nodes, 2):
        if find(a) == find(b):
            ev.append(("X", "主机 %s 与 %s 互连" % (a[1], b[1]), None))
    # 良性：底座 5V → 地（限流吸收）
    if ("DOCK", "5V_RAIL") in g.adj:
        for gnd in gnds:
            if gnd in g.adj and find(("DOCK", "5V_RAIL")) == find(gnd):
                ev.append(("P", "底座 5V 输出对%s短路（限流吸收，可见）"
                           % ("底座地" if gnd[0] == "DOCK" else "主机地"), None))
    return ev, g


def assert_5v_out(alloc):
    """判据 2：H2 pin 18 (5V_OUT) 绝不可被连接到任何东西。"""
    bad = [k for k, v in alloc.items() if v in ("DOCK_5V_OUT", "SLOT_5V_OUT", "5V_OUT")]
    return bad


# =============================================================================
# §5  D4 群（EDA 里封装被旋转／镜像放置）
# =============================================================================

D4 = [
    ("e     恒等", lambda c, r: (c, r)),
    ("R90   绕 Y 轴 +90°", lambda c, r: (r, NCOL - 1 - c)),
    ("R180  绕 Y 轴 180°（前后翻转）", lambda c, r: (NCOL - 1 - c, NROW - 1 - r)),
    ("R270  绕 Y 轴 −90°", lambda c, r: (NROW - 1 - r, c)),
    ("MX    沿 X 镜像", lambda c, r: (NCOL - 1 - c, r)),
    ("MZ    沿 Z 镜像（绕 Z 轴 180°/上下颠倒）", lambda c, r: (c, NROW - 1 - r)),
    ("MD1   主对角镜像（转置）", lambda c, r: (r, c)),
    ("MD2   副对角镜像", lambda c, r: (NROW - 1 - r, NCOL - 1 - c)),
]


def transform_alloc(alloc, g):
    out = {}
    for (c, r), net in alloc.items():
        out[g(c, r)] = net
    if len(out) != len(alloc):
        raise SystemExit("D4 变换不是双射")
    return out


# =============================================================================
# §6  连续偏航（补充搜索，非穷举依据）
# =============================================================================

def yaw_reach_min_distance(alloc, want_pin_net, want_pad_pred,
                           n_yaw=81, n_t=121, yaw_max_deg=25.0):
    """裸触点板在腔内任意平移 ＋ 绕 Y 偏航，求指定底座针到指定类焊盘的最小可达中心距。

    假设模块壳体完全不存在（AS-08 一级防呆彻底失效），只要触点板四角仍在腔内就算合法。
    这是数值搜索，作为 §2 解析穷举的**补充**，不是穷举依据本身。
    """
    pins = [(site_pos(c, r), alloc[(c, r)]) for (c, r) in alloc]
    pins = [p for p, n in pins if n == want_pin_net]
    pads = [(site_pos(c, r), alloc[(c, r)]) for (c, r) in alloc]
    pads = [p for p, n in pads if want_pad_pred(n)]
    if not pins or not pads:
        return None
    bcx, bcz = sum(BOARD_X) / 2.0, sum(BOARD_Z) / 2.0
    hx, hz = (BOARD_X[1] - BOARD_X[0]) / 2.0, (BOARD_Z[1] - BOARD_Z[0]) / 2.0
    corners = [(bcx + sx * hx, bcz + sz * hz) for sx in (-1, 1) for sz in (-1, 1)]
    best = float("inf")
    best_pose = None
    for iy in range(n_yaw):
        th = math.radians(-yaw_max_deg + 2 * yaw_max_deg * iy / (n_yaw - 1))
        ct, st = math.cos(th), math.sin(th)

        def rot(p):
            x, z = p[0] - bcx, p[1] - bcz
            return (bcx + ct * x - st * z, bcz + st * x + ct * z)

        rc = [rot(p) for p in corners]
        rpads = [rot(p) for p in pads]
        # 平移窗口：旋转后四角仍须在腔内
        tx_lo = BAY_X[0] - min(p[0] for p in rc)
        tx_hi = BAY_X[1] - max(p[0] for p in rc)
        tz_lo = BAY_Z[0] - min(p[1] for p in rc)
        tz_hi = BAY_Z[1] - max(p[1] for p in rc)
        if tx_lo > tx_hi or tz_lo > tz_hi:
            continue
        for ix in range(n_t):
            tx = tx_lo + (tx_hi - tx_lo) * ix / (n_t - 1)
            for iz in range(n_t):
                tz = tz_lo + (tz_hi - tz_lo) * iz / (n_t - 1)
                for q in pins:
                    for p in rpads:
                        d = math.hypot(q[0] - (p[0] + tx), q[1] - (p[1] + tz))
                        if d < best:
                            best = d
                            best_pose = (math.degrees(th), tx, tz)
    return best, best_pose


# =============================================================================
# §7  主流程
# =============================================================================

def run_scheme(name, alloc, absent_pins, absent_pads=frozenset(), verbose=False):
    print("=" * 78)
    print("方案：%s" % name)
    print("=" * 78)
    inv = defaultdict(list)
    for (c, r), n in alloc.items():
        inv[n].append((c, r))
    print("  构成：%s" % "  ".join(
        "%s×%d" % (k, len(v)) for k, v in sorted(inv.items(), key=lambda kv: (-len(kv[1]), kv[0]))))
    if absent_pins:
        print("  底座侧未装针：%s" % ", ".join("(列%d,行%s)" % (c + 1, ROW_NAME[r]) for c, r in sorted(absent_pins)))
    if absent_pads:
        print("  模块侧整片无铜（无焊盘）：%s"
              % ", ".join("(列%d,行%s)" % (c + 1, ROW_NAME[r]) for c, r in sorted(absent_pads)))

    # ---- 判据 2 ----
    bad = assert_5v_out(alloc)
    print("\n[判据 2] H2 pin18 5V_OUT：分配表中出现 5V_OUT 网的格位 = %s → %s"
          % (bad if bad else "无", "通过" if not bad else "**失败**"))
    print("         （EL-D-02：pin 18 焊盘不连铜、无测试点；故它不可能出现在触点场，"
          "任何错位都无法把它接到任何东西。本判据为结构性判据，与 δ 无关。）")

    cases = enumerate_delta_cases()
    press_states = [("底座按键全未按下", frozenset()),
                    ("底座按键全部按下（最坏）", frozenset(KEY_TO_H2))]

    rc = 0
    all_fatal = []       # (严重度, 变换, 情形标签, 最小‖δ‖, 可达?, 描述, 通路)
    benign_x = 0

    for tname, tf in D4:
        talloc = transform_alloc(alloc, tf)
        tabsent = {tf(c, r) for (c, r) in absent_pins}
        tnopad = {tf(c, r) for (c, r) in absent_pads}
        for label, offs, mn, dpt in cases:
            for pname, pressed in press_states:
                ev, g = assess(talloc, offs, tabsent, pressed, tnopad)
                for sev, desc, path in ev:
                    if sev in ("F", "F-钳位", "S"):
                        reach = delta_reachable(dpt[0], dpt[1]) if dpt else False
                        all_fatal.append((sev, tname, label, mn, dpt, reach, pname, desc,
                                          fmt_path(path, talloc)))
                    elif sev == "X":
                        benign_x += 1

    # ---- 汇总 ----
    def key(f):
        return (0 if f[0] == "F" else (1 if f[0] == "S" else 2), not f[5], f[3])

    # 去重：同 (严重度, 变换, 情形, 描述) 只留一条
    seen = {}
    for f in sorted(all_fatal, key=key):
        k = (f[0], f[1], f[2], f[7])
        if k not in seen:
            seen[k] = f
    fatal = sorted(seen.values(), key=key)

    ident = [f for f in fatal if f[1].startswith("e ")]
    reach_ident = [f for f in ident if f[5]]

    print("\n[判据 1/3] 全域枚举结果")
    print("  δ 情形表规模：%d 个完备情形（单偏移 49 ＋ 桥接 %d）× D4 8 变换 × 按键 2 态"
          % (len(cases), len(cases) - 49))
    print("  腔体允许的平移包络：δx ∈ [%+.3f, %+.3f]  δz ∈ [%+.3f, %+.3f]（纯平移）"
          % (DELTA_X_RANGE[0], DELTA_X_RANGE[1], DELTA_Z_RANGE[0], DELTA_Z_RANGE[1]))

    print("\n  ---- 类别 A：封装正确，只发生错位（恒等变换 e）----")
    print("    说明：**只有本类是「装配正确、仅发生错位」**，因此只有本类的『腔体可达=是』")
    print("          才是真正会打坏主机的事件。未钳位的 F = 5 V 经 1 kΩ 直击 GPIO。")
    unreach = [f for f in ident if not f[5]]
    show = [f for f in ident if f[5]] + sorted(unreach, key=lambda f: f[3])[:3]
    if not ident:
        print("    致命/可疑事件：0 起。")
    else:
        if len(ident) > len(show):
            print("    （共 %d 条，下面完整列出全部『腔体可达』者，另附最小的 3 条不可达者作对照）"
                  % len(ident))
        for f in show:
            sev, _, label, mn, dpt, reach, pname, desc, path = f
            print("    [%-6s] %s" % (sev, desc))
            print("        情形：%s   %s" % (label, pname))
            print("        最小触发位移 ‖δ‖ = %.3f mm（= %.1f × 最坏定位公差 %.2f）；"
                  "δ = (%+.3f, %+.3f)" % (mn, mn / DOCK_X_TOL, DOCK_X_TOL, dpt[0], dpt[1]))
            print("        腔体可达：%s" % ("**是** —— 落入槽本身就允许这个位移" if reach
                                          else "否（超出腔体包络，需壳体与腔体同时失效）"))
            if path and path != "（无）":
                print("        通路：%s" % path)
            print("")

    print("  ---- 类别 B：EDA 里 J2 封装被旋转/镜像放置（实物做不到，EDA 挡不住）----")
    nonid = [f for f in fatal if not f[1].startswith("e ")]
    byt = defaultdict(list)
    for f in nonid:
        byt[f[1]].append(f)
    for tname, _ in D4[1:]:
        lst = byt.get(tname, [])
        nf = len([x for x in lst if x[0] == "F"])
        ns = len([x for x in lst if x[0] == "S"])
        mmin = min([x[3] for x in lst], default=float("inf"))
        print("    %-34s F=%d  S=%d   最小触发 ‖δ‖ = %s"
              % (tname, nf, ns, ("%.3f mm" % mmin) if lst else "—"))

    print("\n  ---- 判据 4：GPIO ↔ GPIO 互连（不致命，须报）----")
    print("    在全枚举中出现 %d 条次（键位错置/多键并联；后果为功能错误，"
          "不构成器件损坏）。" % benign_x)

    reach_F = sorted([f[3] for f in ident if f[5] and f[0] == "F"])
    reach_S = sorted([f[3] for f in ident if f[5] and f[0] == "S"])
    unreach_F = sorted([f[3] for f in ident if not f[5] and f[0] == "F"])
    if reach_F or reach_S:
        rc = 1
    return rc, fatal, reach_ident, (reach_F, reach_S, unreach_F)



def sensitivity_tip():
    """结论对「针尖有效搭接直径」的依赖：逐值实算，不做文字论证。"""
    global R_TOUCH
    print("\n" + "=" * 78)
    print("§ 敏感性 —— 本结论对「针尖有效搭接直径」的依赖")
    print("=" * 78)
    crit = 2 * 1.27 - PAD_D
    print("  链式通路成立的**充要几何条件**是：一根针能同时压住相邻两块铜，")
    print("  即 R = (Ø焊盘 + Ø针尖_有效)/2 > 半间距 1.27 mm")
    print("  ⇒ Ø针尖_有效 > 2×1.27 − %.1f = %.2f mm" % (PAD_D, crit))
    print("  AS-31-mm-5 定的 Ø0.9 是针尖**直径**，针头形状 unknown（平头/冠头/尖头/球头）。")
    print("  下表为逐值实算（其余一切不变，只改针尖有效直径）：")
    print("")
    print("    %-14s %-10s %-34s" % ("Ø针尖_有效", "R (mm)", "P2 类别A 腔体可达 F"))
    keep = R_TOUCH
    for tip in (0.40, 0.50, 0.54, 0.60, 0.70, 0.90, 1.00):
        R_TOUCH = (PAD_D + tip) / 2.0
        worst = []
        for label, offs, mn, dpt in enumerate_delta_cases():
            if dpt is None or not delta_reachable(dpt[0], dpt[1]):
                continue
            ev, _ = assess(ALLOC_P2, offs, set(), frozenset())
            for sev, desc, _pth in ev:
                if sev == "F":
                    worst.append(mn)
        print("    %-14.2f %-10.3f %-34s"
              % (tip, R_TOUCH,
                 ("**%d 起, 最小 %.3f mm**" % (len(worst), min(worst))) if worst else "0 起"))
    R_TOUCH = keep
    print("")
    print("  读法：只要针尖有效搭接直径 > %.2f mm，链式通路就成立。" % crit)
    print("  标称 Ø0.9 有 %.2f mm 余量，即使针头显著收窄（如球头实际接触圈 Ø0.6）仍然成立。"
          % (0.9 - crit))
    print("  换言之：**这个结论不依赖针头形状的乐观或悲观假设**，它在整个合理区间内都成立。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="连同对照方案一起跑")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    board_cx = _self_check_geometry()

    print("j2_mismate_exhaustive.py —— J2 触点场错位穷举判定")
    print("提案 · 未冻结 · 不得据以制造")
    print("")
    print("§ 几何自检（全部取自本人实跑 OpenSCAD 的 ECHO）")
    print("  列 1..4 中心 X = %s" % [round(site_pos(c, 0)[0], 3) for c in range(NCOL)])
    print("  行 A..D 中心 Z = %s" % [round(site_pos(0, r)[1], 3) for r in range(NROW)])
    print("  焊盘 Ø%.1f / 针尖 Ø%.1f → 搭接阈值 R = %.2f mm；可靠接触阈值 %.2f mm"
          % (PAD_D, PIN_TIP_D, R_TOUCH, R_RELIABLE))
    print("  触点板 %.2f × %.2f，落入槽模块条带 %.2f × %.2f → 纯平移包络 δx ∈ [%+.3f,%+.3f] δz ∈ [%+.3f,%+.3f]"
          % (BOARD_X[1] - BOARD_X[0], BOARD_Z[1] - BOARD_Z[0],
             BAY_X[1] - BAY_X[0], BAY_Z[1] - BAY_Z[0],
             DELTA_X_RANGE[0], DELTA_X_RANGE[1], DELTA_Z_RANGE[0], DELTA_Z_RANGE[1]))
    print("  触点板心 X = %.3f，J3 落脚线中面 X = %.3f → 偏心 %.3f mm"
          % (board_cx, sum(J3_ROW_X) / 2.0, abs(sum(J3_ROW_X) / 2.0 - board_cx)))
    print("  16 针 × %.1f N = %.1f N 总压力" % (0.6, 16 * 0.6))

    print("\n§ 穷举完备性引理的运行时复验")
    worst, bad = verify_lemma()
    print("  在 401×401 = %d 个 δ 采样点上：单点最多落入 %d 个偏移圆盘；违反「至多 2 且轴向相邻」的点 %d 个。"
          % (401 * 401, worst, len(bad)))
    if worst > 2 or bad:
        print("  引理复验失败 → 情形表不完备，拒绝给出结论。")
        return 2
    print("  引理成立 ⇒ §2 的情形表覆盖**全部平移**（任意方向、任意大小、对角、")
    print("  错多列多行、非整数格位移、半格桥接），G05 要求的组合情形自动全覆盖。")

    schemes = SCHEMES if args.all else SCHEMES[:1]
    rc = 0
    summary = []
    for name, alloc, absent, nopad in schemes:
        print("")
        r, fatal, reach, counts = run_scheme(name, alloc, absent, nopad, args.verbose)
        rc = max(rc, r)
        summary.append((name, counts))

    # ---- 偏航可达性补充搜索（只对待检验方案做）----
    print("\n" + "=" * 78)
    print("§ 补充：连续偏航下的可达性搜索（数值搜索，非穷举依据）")
    print("=" * 78)
    print("  假设模块壳体完全不存在（AS-08 一级防呆彻底失效），裸触点板在落入槽模块条带")
    print("  空腔内任意平移并绕 Y 偏航，只要四角仍在腔内就算合法。")
    res = yaw_reach_min_distance(ALLOC_P2, "DOCK_5V", lambda n: n in KEY_TO_H2)
    if res:
        d, pose = res
        print("  P2：底座 DOCK_5V 针到最近 KEY 焊盘的**可达最小中心距** = %.3f mm"
              % d)
        print("      最坏位姿 yaw=%.2f°, tX=%+.3f, tZ=%+.3f；搭接阈值 %.2f mm → %s"
              % (pose[0], pose[1], pose[2], R_TOUCH,
                 "够不到（直接接触不可达）" if d >= R_TOUCH else "**可接触**"))
        print("      注意：这只否定了「5V 针**直接**压上 KEY 焊盘」。经孤立哑位铜的**两跳**通路")
        print("      不受此数字约束，见类别 A 的判定。")
    res2 = yaw_reach_min_distance(ALLOC_P2, "DOCK_GND", lambda n: n == "DOCK_5V")
    if res2:
        d, pose = res2
        print("  P2：底座 DOCK_GND 针到 DOCK_5V 焊盘的可达最小中心距 = %.3f mm（G04 方向）→ %s"
              % (d, "够不到" if d >= R_TOUCH else "**可接触**"))

    sensitivity_tip()

    print("\n" + "=" * 78)
    print("§ 判决 —— 会打坏主机的事件（类别 A ∩ 腔体可达）")
    print("=" * 78)
    print("  判据 1 = 未被地钳位的 5 V → 主机 GPIO；判据 3 = 主机 5V_IN → 地（G04）。")
    print("  「腔体可达」= 该位移落在落入槽腔体本身允许的包络内，")
    print("   即**不需要**腔体或外壳破损，只需要定位失效。")
    print("")
    print("  %-44s %-24s %-24s" % ("方案", "判据1 F(5V→GPIO)", "判据3 S(G04)"))
    print("  " + "-" * 92)
    for n, (rf, rs, uf) in summary:
        fs = ("**%d 起, 最小 %.3f mm**" % (len(rf), rf[0])) if rf else ("0 起 (最近不可达 %.2f mm)" % uf[0] if uf else "0 起")
        ss = ("**%d 起, 最小 %.3f mm**" % (len(rs), rs[0])) if rs else "0 起"
        print("  %-44s %-24s %-24s" % (n[:44], fs, ss))
    print("")
    print("  判决：%s" % ("**不通过** —— 待检验方案在腔体可达的位移下会打坏主机。"
                          if rc else "在可达包络内无致命事件。"))
    print("")
    print("  本脚本**不**覆盖（不要当成已证明）：")
    print("   1. J3/J1 焊接错误造成的任意网置换（D4 只覆盖刚体错位与整体旋转镜像）。")
    print("   2. 弹簧针针头形状：AS-31-mm-5 只定了 Ø0.9、行程、压力，没定形状。")
    print("      本脚本按平头/冠头取 R = 1.45。见 §敏感性：只要有效搭接直径 > 0.54 mm")
    print("      结论就不变，故这一项**不**是本判决的软肋；但它仍是应关闭的假设。")
    print("   3. 这颗 SoC 的绝对最大额定与最大注入电流：仓库内无数据手册，unknown。")
    print("      本脚本只判「通不通」，不判「多少毫安才烧」。")
    print("   4. 主机 5V_IN 与原生 USB VBUS 的内部拓扑（AS-11，unknown）——")
    print("      G04 的最终后果悬在这上面；本脚本只报「主机 5V_IN 接通了底座地」这个事实。")
    print("   5. Y 向插入深度的先后接触次序：等长针无法保证先接地（ICD 3.3 该项仍开放）。")
    print("")
    print("退出码 %d" % rc)
    return rc


if __name__ == "__main__":
    sys.exit(main())
