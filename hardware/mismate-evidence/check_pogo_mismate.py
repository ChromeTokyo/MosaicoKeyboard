#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_pogo_mismate.py —— 弹簧针触点场（4 行 × 4 列）错位**穷举**判定

提案 · 未冻结 · 不得据以制造。

要回答的问题只有一个：**有没有哪一种错位会把 5 V 灌进主机的 3.3 V GPIO。**

为什么这版是「穷举」而不是「举例」
--------------------------------
Grok R0 的 G05 说旧分析「只算了错一列和错一行，没算对角错位和错多列」。
本脚本不靠补例子来堵这个口子，而是把连续的二维错位空间**约化成一个有限集合**，
并在脚本里把约化本身当作断言跑一遍（§1）：

  · 针场与焊盘场是同一个 4×4 正交格（间距 P = 2.54 mm），二者在 X/Z 上名义重合
    （两侧的 ECHO 给出同一组坐标，见 §0 来源）。
  · 针尖 Ø d_pin 与焊盘 Ø d_pad 搭上铜的充要条件是中心距 ≤ R = (d_pad + d_pin)/2。
  · 于是「某根针压住某个焊盘」只取决于二者的格差 g = (k, l)（k, l ∈ [-3..3]，
    |k| 或 |l| ≥ 4 时场已完全错开）与连续位移 Δ 的关系：|Δ − P·g| ≤ R。
  · 记 S(Δ) = { g : |Δ − P·g| ≤ R }。**接触图只由 S(Δ) 决定**，与 Δ 在同一
    S 的胞腔内怎么动无关。
  · R = 1.45 < P·√2/2 · … ：脚本实算出「任意三个格点不可能同时落在半径 R 内」，
    且「能同时落在半径 R 内的两个格点必定正交相邻」。因此 |S| ∈ {0, 1, 2}。
  · 所以整个 **R² 平面**上，接触图只有 49 个单点构型 + 84 个相邻对（桥接）构型
    = **133 种**，一个不多一个不少。全部跑掉 = 穷举完成。

  「错一列」「错一行」「对角」「错多列」「错位到一半同时搭两个焊盘」全部是这 133 种
  里的元素，不需要单独列，也不可能漏。脚本另做一次 0.05 mm 步长的连续扫描做交叉
  验证（§1.4），断言扫到的每一个 S 都在这 133 种里。

平移之外的自由度（§5）：绕 Y / X / Z 轴 180°、X 镜像误装、Z 镜像误装、
J3 两排对调（AS-17 一翻就会发生）、倾斜/半插入。倾斜在 §5.5 里被算成一个
横向等效偏移量并入平移，不单列。

判据（每条在 §6 显式断言）
-------------------------
  C1  任何情形下，底座 5 V 源不得与任何通向主机 GPIO 的网同处一个连通分量   → 致命
  C2  H2 pin 18 = 5V_OUT 绝不可被连接到任何东西                              → 结构性断言
  C3  GND → 5V_IN 方向（Grok G04）：主机 5V_IN 与主机 GND 是否被外部短接      → 可疑
  C4  两根主机 GPIO 互相短接 / GPIO 被永久拉低 / 键位错                       → 功能

模型是**连通分量**而不是逐针对照表：底座的按键针在开关断开时是一段浮空铜，
它可以同时压住两个焊盘，把两个主机网桥接起来。这种「5V 针 → 哑焊盘 → 另一根针
→ 按键焊盘」的多跳通路，逐针表抓不到，并查集抓得到。

纯 python3 标准库。退出码：0 = 全部判据通过；1 = 有判据失败；2 = 自检/用法错误。

换方案只需改 §0 的数据表。
"""

import argparse
import itertools
import math
import sys
from collections import defaultdict

# =============================================================================
# §0  数据表 —— 换方案只改这一节
# =============================================================================
#
# 数值来源（全部由本脚本作者亲自编译/grep 取得，非转述）：
#
# [E1] openscad -o mb.stl <claude/design-d/mech-module>:mechanical/module-board/module_board.scad
#      实测 manifold，Vertices 2314 / Facets 4768。ECHO 原文：
#        "J2 列 1..4 中心 X = [-34.405, -31.865, -29.325, -26.785]"
#        "J2 行 A..4 中心 Z = [2.75, 0.21, -2.33, -4.87]（行 A 在 +Z 屏侧）"
#        "触点板 pad_board（XZ 面）：X [-36.095 , -25.095]  Z [-6.46 , 4.34]  底面 Y = -24.095"
#        "[检查 6] 定位公差 ±0.45 mm 对 Ø2 焊盘／Ø0.9 针尖：允许偏移 = 0.55 mm，余量 = 0.1 mm。
#          相邻焊盘净间距 0.54 mm"
#      ⚠ 该文件行尾注释里的 PAD_X_MAX / PAD_Z_MAX / DOCK_PIN_FIELD_X0 是过期值，只信 ECHO。
# [E2] module_board.scad 第 119–145 行（grep 实读）：
#      DOCK_PITCH=2.54  DOCK_COLS=4  DOCK_ROWS=4  DOCK_PAD_D=2.0
#      DOCK_PIN_TIP_D=0.9  DOCK_PIN_FORCE_N=0.6  DOCK_X_TOL=0.45  DOCK_Z_TOL=0.45
# [E3] openscad -o ds.stl <claude/design-d/mech-dock>:mechanical/dock-shell/dock_shell.scad
#      实测 Vertices 13920 / Facets 28472。ECHO 原文：
#        "弹簧针场：列 1..4 X = [-34.405, -31.865, -29.325, -26.785]
#          行 A..4 Z = [2.75, 0.21, -2.33, -4.87]  配合面 Y = -24.095"   ← 与 [E1] 逐位相同
#        "落入槽内腔 X = [-37.845, 22.945]  Y_floor = -25.395"
#        "落入槽模块条带：X ≤ -22.945  Z = [-8.01, 5.89]"
#        ICD-CONTRACT|DOCK_PIN_TRAVEL|1.2   ICD-CONTRACT|DOCK_PIN_STROKE|2
# [E4] openscad <claude/design-d/mech-module>:mechanical/module-board/module_shell.scad
#      实测 Vertices 3603 / Facets 7362。ECHO：
#        "壳体包络：X [-37.695 , -19.595]  Y [-24.195 , 24.295]  Z [-7.86 , 5.74]"
# [F1] <claude/design-d/module-board>:hardware/module-board/PINMAP.md 第 2 节表
#      （工作树 /private/tmp/wt-module-board/hardware/module-board/PINMAP.md:36–46）
#      KEY_* → H2 针号 → GPIO。本脚本逐行照抄，未改。
# [F2] 同目录 netlist.yaml 第 33–53 行 h2_contract：H2 针号 → 主机网络。
# [F3] hardware/ICD-0.2-DRAFT.md:96（pin 18 5V_OUT「NC，绝不连接任何网络」，硬约束 2）
#      :97（pin 19 3V3 不引到弹簧针，硬约束 3）
#      :129（底座对 KEY_*/SDA/SCL 不放上拉、不接电源，硬约束 5、6；DOCK_5V 经限流与短路关断）
# [F4] hardware/ICD-0.2-DRAFT.md:73–103 第 2 节 H2 合同，约束行：
#      「11 根可用 GPIO 集合 {55,53,19,48,18,13,17,12,16,15,4}」 ← 是 11 根不是 12 根，
#      GPIO14 是 EEPROM A0 专用。任务书里写的「12 个」含 GPIO14，与 ICD 第 2 节冲突。
# [F5] review/grok/R0/REPORT.md（提交 d6cbca3，当前检出分支上没有该文件）:162 G04 / :168 G05。
#
# 未知项，本脚本不替它编数：
#   AS-26 弹簧针单针额定电流 = unknown；AS-11 主机 5V_IN 内部合并拓扑 = unknown；
#   主机 GPIO 钳位二极管额定 = unknown。本脚本只判「碰没碰上」，不判「扛不扛得住」。

# ---- 0.1 几何 [E1][E2][E3] ----
PITCH       = 2.54     # mm
COLS        = 4
ROWS        = 4
PAD_D       = 2.0      # 模块板焊盘直径
PIN_TIP_D   = 0.9      # 弹簧针针尖直径
FIELD_X0    = -34.405  # 列 1 中心 X
FIELD_Z0    = 2.75     # 行 A 中心 Z
MATE_Y      = -24.095  # 配合面
DOCK_X_TOL  = 0.45
DOCK_Z_TOL  = 0.45
PIN_TRAVEL  = 1.2      # 名义压缩量
# 落入槽与总成外形（用于算「机械上到底能错多少」）
BAY_X       = (-37.845, 22.945)
BAY_MOD_Z   = (-8.01, 5.89)      # 模块条带（X ≤ -22.945）
BAY_MOS_Z   = (-6.09, 6.09)      # Mosaico 条带
MOSAICO_W   = 45.19
MOSAICO_T   = 11.48
MODULE_ENV_X = (-37.695, -19.595)
MODULE_ENV_Z = (-7.86, 5.74)
MODULE_ENV_Y = (-24.195, 24.295)

# ---- 0.2 H2 针号 → 主机网络 [F2] ----
H2_CONTRACT = {
    1: "GPIO55", 2: "GPIO53", 3: "GPIO19", 4: "GPIO48", 5: "GPIO18",
    6: "GPIO13", 7: "GPIO17", 8: "GPIO12", 9: "GPIO16", 10: "GPIO14_EEPROM_A0",
    11: "GPIO15", 12: "GPIO4", 13: "GPIO33_USJ_DN", 14: "GPIO1_SCL",
    15: "GPIO34_USJ_DP", 16: "GPIO0_SDA", 17: "5V_IN", 18: "5V_OUT",
    19: "VCC_3V3", 20: "GND",
}
# 主机侧「一碰 5 V 就完蛋」的网：3.3 V 域的 GPIO。
HOST_GPIO_PINS = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16}

# ---- 0.3 待检验的 16 位分配表（本次要审的那一版）----
#   位号, 列(1..4), 行(0=A 在 +Z 屏侧 … 3=D), 网名, H2 针号(None = 不通主机)
#   网名同时是底座侧网名与模块侧网名：同一位上两边同网，这是设计本意。
ALLOC_PROPOSAL = [
    ( 1, 1, 0, "KEY_L",     9),
    ( 2, 2, 0, "KEY_R",    11),
    ( 3, 3, 0, "KEY_B",     4),
    ( 4, 4, 0, "KEY_A",     2),
    ( 5, 1, 1, "KEY_LEFT",  5),
    ( 6, 2, 1, "KEY_RIGHT", 7),
    ( 7, 3, 1, "KEY_Y",     8),
    ( 8, 4, 1, "KEY_X",     6),
    ( 9, 1, 2, "DOCK_GND", 20),
    (10, 2, 2, "DOCK_GND", 20),
    (11, 3, 2, "DOCK_GND", 20),
    (12, 4, 2, "KEY_DOWN",  3),
    (13, 1, 3, "DOCK_5V",  17),
    (14, 2, 3, "DOCK_5V",  17),
    (15, 3, 3, "DOCK_GND", 20),
    (16, 4, 3, "KEY_UP",    1),
]

# 对照方案：ICD 第 3.2 节现行 2×8 表按「列 1..8 → (列 1..4, 行 A/B) 折两折」落到 4×4。
# 折法：原列 c（1..8）→ 新列 ((c-1) mod 4)+1，新行 = A/B 行 + 4*(c>4)。只作对照，不是提案。
ALLOC_BASELINE_2x8_FOLDED = [
    ( 1, 1, 0, "DOCK_5V",  17),
    ( 2, 2, 0, "DOCK_GND", 20),
    ( 3, 3, 0, "KEY_UP",    1),
    ( 4, 4, 0, "KEY_LEFT",  5),
    ( 5, 1, 1, "DOCK_5V",  17),
    ( 6, 2, 1, "DOCK_GND", 20),
    ( 7, 3, 1, "KEY_DOWN",  3),
    ( 8, 4, 1, "KEY_RIGHT", 7),
    ( 9, 1, 2, "KEY_L",     9),
    (10, 2, 2, "KEY_A",     2),
    (11, 3, 2, "KEY_X",     6),
    (12, 4, 2, "DOCK_SDA", 16),
    (13, 1, 3, "KEY_R",    11),
    (14, 2, 3, "KEY_B",     4),
    (15, 3, 3, "KEY_Y",     8),
    (16, 4, 3, "DOCK_SCL", 14),
]

SCHEMES = {
    "proposal": ("4×4 提案：5V×2 ＋ GND×4 ＋ 10 键（SDA/SCL 退出触点场）", ALLOC_PROPOSAL),
    "baseline": ("对照：ICD 3.2 现行 2×8 表折成 4×4（5V×2 ＋ GND×2 ＋ 10 键 ＋ SDA/SCL）",
                 ALLOC_BASELINE_2x8_FOLDED),
}

# =============================================================================
# §1  几何与完备性
# =============================================================================

R_TOUCH = (PAD_D + PIN_TIP_D) / 2.0          # 铜搭铜阈值
R_RELIABLE = (PAD_D - PIN_TIP_D) / 2.0       # 针尖完全落在焊盘内
GRID = [(k, l) for k in range(-(COLS - 1), COLS) for l in range(-(ROWS - 1), ROWS)]
EPS = 1e-9


def cell_xz(col, row):
    """位号(列, 行) → 名义中心坐标 (X, Z)。行 0 = 行 A，在 +Z。"""
    return (FIELD_X0 + (col - 1) * PITCH, FIELD_Z0 - row * PITCH)


def contacts_for_offsets(offsets, alloc):
    """给定格差集合 S，返回接触边 [(针位号, 焊盘位号)]。

    针位 (c, r) 压住焊盘 (c - k, r - l)：Δ 是焊盘场相对针场的位移，
    焊盘 (c', r') 被移到 (c'+k, r'+l)，与针 (c, r) 重合 ⟺ c' = c - k, r' = r - l。
    """
    by_cr = {(c, r): pos for pos, c, r, _n, _p in alloc}
    out = []
    for (k, l) in offsets:
        for pos, c, r, _n, _p in alloc:
            tgt = by_cr.get((c - k, r - l))
            if tgt is not None:
                out.append((pos, tgt))
    return out


def enumerate_configurations():
    """把整个 R² 平面上的接触构型约化成有限集合，并把约化本身断言一遍。"""
    log = []
    # (a) |k| 或 |l| ≥ COLS/ROWS 时不可能接触：最小可能中心距 = P*COLS - P*(COLS-1) = P > R
    assert PITCH > R_TOUCH + EPS, "间距必须大于搭接阈值，否则格差集合不封闭"
    log.append("  [1.1] 格差范围 k,l ∈ [%d..%d]：再外一格时任意针-盘最小中心距 = %.3f > R = %.3f，"
               "不可能接触 → 格差集合封闭，共 %d 个"
               % (-(COLS - 1), COLS - 1, PITCH, R_TOUCH, len(GRID)))

    # (b) 能同时被压住的两个格点必定正交相邻
    pairs = []
    for g1, g2 in itertools.combinations(GRID, 2):
        d = math.hypot((g1[0] - g2[0]) * PITCH, (g1[1] - g2[1]) * PITCH)
        if d <= 2 * R_TOUCH + EPS:
            pairs.append((g1, g2, d))
    for g1, g2, d in pairs:
        assert abs(d - PITCH) < 1e-9, "出现了非正交相邻的可共存格点对，完备性论证失效"
    log.append("  [1.2] 任意两格点若能同时落在半径 R 内则中心距 ≤ 2R = %.3f；"
               "格上只有正交相邻的 %.3f 满足（对角 %.3f > 2R）→ 共 %d 对"
               % (2 * R_TOUCH, PITCH, PITCH * math.sqrt(2), len(pairs)))

    # (c) 任意三个格点不可能同时落在半径 R 内
    triples = 0
    for g1, g2, g3 in itertools.combinations(GRID, 3):
        ds = [math.hypot((a[0] - b[0]) * PITCH, (a[1] - b[1]) * PITCH)
              for a, b in itertools.combinations((g1, g2, g3), 2)]
        if all(d <= 2 * R_TOUCH + EPS for d in ds):
            triples += 1
    assert triples == 0, "存在三格点共存的可能，|S| ≤ 2 不成立"
    log.append("  [1.3] 穷举 C(%d,3) = %d 个三元组：两两距离全 ≤ 2R 的一个也没有 → |S| ≤ 2"
               % (len(GRID), len(list(itertools.combinations(GRID, 3)))))

    configs = [frozenset([g]) for g in GRID]
    configs += [frozenset([g1, g2]) for g1, g2, _d in pairs]
    # (d) 每个构型都可实现：给出见证点并验算 S(见证点) 恰好等于它
    for cfg in configs:
        w = witness(cfg)
        assert set(S_of(w)) == set(cfg), "构型 %s 不可实现" % (sorted(cfg),)
    log.append("  [1.4] %d 个单点构型 + %d 个桥接构型 = **%d 种**，逐个给出见证 Δ 并验算 S(Δ) 相符"
               % (len(GRID), len(pairs), len(configs)))
    return configs, log


def witness(cfg):
    xs = [g[0] * PITCH for g in cfg]
    zs = [g[1] * PITCH for g in cfg]
    return (sum(xs) / len(xs), sum(zs) / len(zs))


def S_of(delta):
    dx, dz = delta
    return [g for g in GRID
            if math.hypot(dx - g[0] * PITCH, dz - g[1] * PITCH) <= R_TOUCH + 1e-12]


def region_bounds(cfg):
    """构型 cfg 的闭包区域（∩ 各圆盘）上的 min|Δ|、min|ΔX|、min|ΔZ|。解析解，不采样。

    返回值是**下界**（用闭包而不是开胞腔），因此「低于此位移不可能发生」这句话成立。
    """
    cs = [(g[0] * PITCH, g[1] * PITCH) for g in cfg]
    if len(cs) == 1:
        (a, b) = cs[0]
        return (max(0.0, math.hypot(a, b) - R_TOUCH),
                max(0.0, abs(a) - R_TOUCH),
                max(0.0, abs(b) - R_TOUCH))
    (a1, b1), (a2, b2) = cs
    half = PITCH / 2.0
    perp = math.sqrt(max(0.0, R_TOUCH ** 2 - half ** 2))   # 垂直于配对轴的半宽
    if abs(b1 - b2) < 1e-9:      # 水平配对
        lo_x, hi_x = max(a1, a2) - R_TOUCH, min(a1, a2) + R_TOUCH
        lo_z, hi_z = b1 - perp, b1 + perp
    else:                        # 垂直配对
        lo_x, hi_x = a1 - perp, a1 + perp
        lo_z, hi_z = max(b1, b2) - R_TOUCH, min(b1, b2) + R_TOUCH
    min_ax = 0.0 if lo_x <= 0 <= hi_x else min(abs(lo_x), abs(hi_x))
    min_az = 0.0 if lo_z <= 0 <= hi_z else min(abs(lo_z), abs(hi_z))
    # min|Δ|：透镜到原点的最近点。候选 = 两圆上离原点最近的点（若在另一圆内）＋ 两个透镜角点。
    cands = []
    for (a, b) in cs:
        n = math.hypot(a, b)
        if n > EPS:
            cands.append(((a - a * R_TOUCH / n), (b - b * R_TOUCH / n)))
        else:
            cands.append((0.0, 0.0))
    d = math.hypot(a2 - a1, b2 - b1)
    if d < 2 * R_TOUCH:
        m = ((a1 + a2) / 2.0, (b1 + b2) / 2.0)
        h = math.sqrt(max(0.0, R_TOUCH ** 2 - (d / 2.0) ** 2))
        ux, uz = (a2 - a1) / d, (b2 - b1) / d
        cands.append((m[0] - uz * h, m[1] + ux * h))
        cands.append((m[0] + uz * h, m[1] - ux * h))
    best = None
    for p in cands:
        if all(math.hypot(p[0] - a, p[1] - b) <= R_TOUCH + 1e-9 for (a, b) in cs):
            n = math.hypot(*p)
            best = n if best is None else min(best, n)
    if best is None:
        best = min(math.hypot(*p) for p in cands)
    return (best, min_ax, min_az)


# =============================================================================
# §2  电气模型：并查集连通分量
# =============================================================================

class DSU:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def host_net_of(pin):
    return "HOST_" + H2_CONTRACT[pin] if pin is not None else None


def analyze(alloc_pin, alloc_pad, contacts, pressed_keys=(), host_5v_in_live=False):
    """建图、求连通分量、判事件。

    alloc_pin：底座针位号 → (网名, H2 针号)；alloc_pad：模块焊盘位号 → 同。
    contacts：[(针位号, 焊盘位号)]。
    返回 (事件列表, dsu, 节点集)。事件 = (等级, 类型, 说明)。

    D1 与 D1S 的分界（本脚本最关键的一处判断，写清楚以便被推翻）
    ------------------------------------------------------------
    「底座 5 V 与某根主机 GPIO 连通」本身还不足以断定打坏主机：如果通路上必然
    经过一个已经被接到 GND 的网，那么在同一瞬间底座 5 V 输出已被自己短路，
    按硬约束 1/8 会进限流/短路关断，节点电压塌掉，GPIO 看到的不是 5 V。
    但如果**存在一条完全避开 GND 的通路**，那么无论限流做得多好，
    这条路上的 5 V 就是实打实加在 GPIO 上——而且落入是个连续过程，
    接触是一个一个建立的，只要存在这样一个接触子集，就存在一个致损时间窗。

    所以：
      D1  （致命）  = 在把所有「已接 GND 的节点」删掉之后，5 V 源仍能走到某个 GPIO
      D1S（条件）   = 全图连通但每条通路都经过 GND 节点；后果取决于底座限流的
                      响应时间与恢复方式（迟滞/打嗝式重启会给出重复的 5 V 前沿），
                      AS-11/AS-24/AS-26 未关闭前不得判为无损
    """
    d = DSU()
    dw = DSU()                       # 只含**接线边**的并查集：用来判「这个节点本身就是地」
    pin_net, pad_net = {}, {}
    adj = defaultdict(set)

    def wire(a, b, is_wire=True):
        d.union(a, b)
        if is_wire:
            dw.union(a, b)
        adj[a].add(b)
        adj[b].add(a)

    for pos, net, pin in alloc_pin:
        pin_net[pos] = net
        wire(("pin", pos), ("dnet", net if net.startswith("DOCK_") else "SW_" + net))
    for pos, net, pin in alloc_pad:
        pad_net[pos] = net
        hn = host_net_of(pin)
        wire(("pad", pos), ("hnet", hn) if hn is not None else ("padnet", net))
    # 底座轻触开关：按下 = KEY 针接 DOCK_GND
    for k in pressed_keys:
        wire(("dnet", "SW_" + k), ("dnet", "DOCK_GND"))
    for (i, j) in contacts:
        wire(("pin", i), ("pad", j), is_wire=False)

    nodes = set(adj)
    comp = defaultdict(set)
    for n in nodes:
        comp[d.find(n)].add(n)

    gpio_nodes = [("hnet", "HOST_" + H2_CONTRACT[p]) for p in HOST_GPIO_PINS]
    gpio_nodes = [g for g in gpio_nodes if g in nodes]
    src_nodes = [("dnet", "DOCK_5V")]
    if host_5v_in_live:
        src_nodes.append(("hnet", "HOST_5V_IN"))
    gnd_nodes = [n for n in (("dnet", "DOCK_GND"), ("hnet", "HOST_GND")) if n in nodes]

    # 「本身就是地」的节点集合：只用**接线边**算。
    # 不能把「因为别处有一个接触而被接到地」的节点也算进来 —— 落入是个连续过程，
    # 接触一个一个建立，那个别处的接触可能还没发生，或者已经被磨断。
    # 判据要问的是「存不存在一个接触子集使 5 V 走到 GPIO 而通路上不带地」，
    # 所以只有通路上的节点算数，别处的接触不算。
    tainted = set()
    for gn in gnd_nodes:
        r = dw.find(gn)
        tainted |= {n for n in nodes if dw.find(n) == r}

    def gnd_free_path(src):
        """在删去全部「本身就是地」的节点后，从 src 找到任一 GPIO；返回通路或 None。"""
        if src in tainted:
            return None
        seen, par = {src}, {src: None}
        q = [src]
        while q:
            cur = q.pop(0)
            if cur in gpio_nodes:
                path = []
                while cur is not None:
                    path.append(cur)
                    cur = par[cur]
                return list(reversed(path))
            for nb in sorted(adj[cur], key=repr):   # 固定遍历序，保证同一输入每次输出一致
                if nb not in seen and nb not in tainted:
                    seen.add(nb)
                    par[nb] = cur
                    q.append(nb)
        return None

    def show(n):
        kind, v = n
        if kind == "pin":
            pos = v
            c, r = next((c, r) for p, c, r, _n, _pi in ALLOC_GEOM if p == pos)
            return "底座针%d(列%d,行%s)=%s" % (pos, c, "ABCD"[r], pin_net[pos])
        if kind == "pad":
            pos = v
            c, r = next((c, r) for p, c, r, _n, _pi in ALLOC_GEOM if p == pos)
            return "焊盘%d(列%d,行%s)=%s" % (pos, c, "ABCD"[r], pad_net[pos])
        return v

    ev = []
    for s in src_nodes:
        if s not in nodes:
            continue
        p = gnd_free_path(s)
        if p is not None:
            ev.append(("D1", "5V→GPIO(避开 GND 的通路)",
                       "%s：%s" % (s[1], " → ".join(show(n) for n in p[1:]))))
        for g in gpio_nodes:
            if d.find(s) == d.find(g) and p is None:
                ev.append(("D1S", "5V→GPIO(仅经已短路网)",
                           "%s 与 %s 连通，但每条通路都经过已接 GND 的网" % (s[1], g[1])))
                break
    # C3 / G04：主机 5V_IN 与主机 GND 被外部短接
    if ("hnet", "HOST_5V_IN") in nodes and ("hnet", "HOST_GND") in nodes:
        if d.find(("hnet", "HOST_5V_IN")) == d.find(("hnet", "HOST_GND")):
            ev.append(("D2", "5V_IN↔GND", "主机 5V_IN 与主机 GND 之间形成外部短路（G04 方向）"))
    # D3：底座 5V 被短到地（由底座限流/短路关断吸收）
    if ("dnet", "DOCK_5V") in nodes:
        for g in gnd_nodes:
            if d.find(("dnet", "DOCK_5V")) == d.find(g):
                ev.append(("D3", "5V→GND", "DOCK_5V 与 %s 短接（底座限流吸收）" % g[1]))
                break
    # D4：GPIO 互短 / GPIO 被永久拉低
    for g1, g2 in itertools.combinations(gpio_nodes, 2):
        if d.find(g1) == d.find(g2):
            ev.append(("D4", "GPIO↔GPIO", "%s 与 %s 互相短接" % (g1[1], g2[1])))
    for g in gpio_nodes:
        for gn in gnd_nodes:
            if d.find(g) == d.find(gn):
                ev.append(("D4", "GPIO→GND", "%s 被 %s 永久拉低" % (g[1], gn[1])))
                break
    return ev, d, comp


SEVERITY = ["D0", "D4", "D3", "D2", "D1S", "D1"]
ALLOC_GEOM = []          # 由 run() 填入：[(位号, 列, 行, 网名, H2针)]


def worst(ev):
    order = ["D1", "D1S", "D2", "D3", "D4"]
    for k in order:
        if any(e[0] == k for e in ev):
            return k
    return "D0"


# =============================================================================
# §3  变体：镜像、翻转、J3 两排对调
# =============================================================================

def variant_alloc(alloc, kind):
    """返回 (针侧分配, 焊盘侧分配)，两者都是 [(位号, 网名, H2针号)]。

    底座侧永远是名义的；变体只作用在模块（焊盘）侧——两侧同时镜像等于没镜像。
    """
    pin_side = [(pos, net, pin) for pos, c, r, net, pin in alloc]
    by_cr = {(c, r): (net, pin) for pos, c, r, net, pin in alloc}
    pad_side = []
    for pos, c, r, net, pin in alloc:
        if kind == "nominal":
            src = (c, r)
        elif kind == "mirror_x":
            src = (COLS + 1 - c, r)
        elif kind == "mirror_z":
            src = (c, ROWS - 1 - r)
        elif kind == "mirror_xz":
            src = (COLS + 1 - c, ROWS - 1 - r)
        elif kind == "j3_row_swap":
            # J3 双排 r0/r1 对调。由提案表读出：位号 1↔3, 2↔4, 5↔7, 6↔8, 9↔11,
            # 10↔12, 13↔15, 14↔16，即「列 1,2 组」与「列 3,4 组」互换，行不变。
            src = (c + 2, r) if c <= 2 else (c - 2, r)
        else:
            raise ValueError(kind)
        n, p = by_cr[src]
        pad_side.append((pos, n, p))
    return pin_side, pad_side


VARIANTS = [
    ("nominal",     "名义（两侧按表装配）"),
    ("mirror_x",    "模块侧 X 镜像误装（列 1↔4、2↔3）"),
    ("mirror_z",    "模块侧 Z 镜像误装（行 A↔D、B↔C）"),
    ("mirror_xz",   "模块侧 X＋Z 双镜像（等价于绕 −Y 法向转 180°）"),
    ("j3_row_swap", "J3 两排对调（AS-17 一翻就会发生；提案自己写明「J3 面 r0/r1 要整体对调」）"),
]


# =============================================================================
# §4  可达包络
# =============================================================================

def envelopes():
    """算出「机械上到底能错多少」。全部由 §0 的 ECHO 数字推出，推导写在返回的说明里。"""
    out = []
    # (a) 名义腔体滑配：零件全按名义尺寸，只有配合间隙
    dx_lo = BAY_X[0] - MODULE_ENV_X[0]                      # 模块壳 −X 外表面 vs 槽壁
    dx_hi = BAY_X[1] - MOSAICO_W / 2.0                      # Mosaico +X 面 vs 槽壁
    dz_lo_mod = BAY_MOD_Z[0] - MODULE_ENV_Z[0]
    dz_hi_mod = BAY_MOD_Z[1] - MODULE_ENV_Z[1]
    dz_lo_mos = BAY_MOS_Z[0] + MOSAICO_T / 2.0
    dz_hi_mos = BAY_MOS_Z[1] - MOSAICO_T / 2.0
    dz_lo = max(dz_lo_mod, dz_lo_mos)
    dz_hi = min(dz_hi_mod, dz_hi_mos)
    out.append(("E1 名义腔体滑配", (dx_lo, dx_hi), (dz_lo, dz_hi),
                "ΔX 下限 = 槽 X_min(%.3f) − 模块壳 X_lo(%.3f)；上限 = 槽 X_max(%.3f) − Mosaico +X 面(%.3f)。"
                "ΔZ 取模块条带(%.3f/%.3f) 与 Mosaico 条带(±%.3f) 两者更紧的一个。"
                % (BAY_X[0], MODULE_ENV_X[0], BAY_X[1], MOSAICO_W / 2.0,
                   dz_lo_mod, dz_hi_mod, BAY_MOS_Z[1] - MOSAICO_T / 2.0)))
    # (b) 设计公差包络：DOCK_X_TOL / DOCK_Z_TOL（AS-31-mm-6：滑配 0.15 ＋ 两件各 ±0.15）
    out.append(("E2 设计公差包络 (DOCK_*_TOL)", (-DOCK_X_TOL, DOCK_X_TOL),
                (-DOCK_Z_TOL, DOCK_Z_TOL),
                "module_board.scad:144–145 的 DOCK_X_TOL = DOCK_Z_TOL = %.2f。" % DOCK_X_TOL))
    # (c) 无约束
    span = (COLS - 1) * PITCH + 2 * R_TOUCH
    out.append(("E3 无机械约束（假设一级防呆全失效）", (-span, span), (-span, span),
                "场跨 %.2f mm ＋ 两侧各 R = %.2f，再远一定零接触。" % ((COLS - 1) * PITCH, R_TOUCH)))
    return out


def in_env(bounds, env):
    """构型闭包区域与包络矩形是否有交（bounds 是 min|Δ|, min|ΔX|, min|ΔZ| 下界）。

    保守判定：只要 min|ΔX| 与 min|ΔZ| 两个下界都落在包络内，就算「可能可达」。
    """
    (_mn, mx, mz) = bounds
    (xlo, xhi), (zlo, zhi) = env
    return mx <= max(abs(xlo), abs(xhi)) + 1e-9 and mz <= max(abs(zlo), abs(zhi)) + 1e-9


# =============================================================================
# §5  主流程
# =============================================================================

def fmt_cfg(cfg):
    gs = sorted(cfg)
    if len(gs) == 1:
        return "错位 (m,n) = (%+d,%+d)" % gs[0]
    return "桥接 (%+d,%+d)|(%+d,%+d)" % (gs[0][0], gs[0][1], gs[1][0], gs[1][1])


def run(scheme_key, verbose, dense_step):
    global ALLOC_GEOM
    title, alloc = SCHEMES[scheme_key]
    ALLOC_GEOM = list(alloc)
    fail = []
    print("=" * 78)
    print("check_pogo_mismate.py —— 弹簧针触点场错位穷举判定")
    print("方案：%s" % title)
    print("场：%d 列 × %d 行 = %d 位，间距 %.2f mm；焊盘 Ø%.1f，针尖 Ø%.1f"
          % (COLS, ROWS, COLS * ROWS, PITCH, PAD_D, PIN_TIP_D))
    print("搭接阈值 R = (Ø%.1f + Ø%.1f)/2 = %.3f mm；可靠接触阈值 = %.3f mm"
          % (PAD_D, PIN_TIP_D, R_TOUCH, R_RELIABLE))
    print("配合面 Y = %.3f；针场与焊盘场 X/Z 名义重合（两侧 ECHO 逐位相同）" % MATE_Y)
    print("=" * 78)

    # ---------- §1 完备性 ----------
    print("\n§1 把连续错位空间约化成有限集合（穷举的完备性论证，逐条实算）")
    configs, log = enumerate_configurations()
    for line in log:
        print(line)

    # 连续扫描交叉验证
    print("  [1.5] 连续扫描交叉验证：步长 %.3f mm，范围 ΔX,ΔZ ∈ [%.2f, %.2f]"
          % (dense_step, -((COLS - 1) * PITCH + R_TOUCH + 0.2), (COLS - 1) * PITCH + R_TOUCH + 0.2))
    lim = (COLS - 1) * PITCH + R_TOUCH + 0.2
    n = int(round(2 * lim / dense_step)) + 1
    known = set(configs)
    seen = set()
    bad = 0
    for i in range(n):
        dx = -lim + i * dense_step
        for j in range(n):
            dz = -lim + j * dense_step
            s = frozenset(S_of((dx, dz)))
            if not s:
                continue
            seen.add(s)
            if s not in known:
                bad += 1
                if bad <= 3:
                    print("      !! 扫到枚举之外的构型 %s @ (%.3f, %.3f)" % (sorted(s), dx, dz))
    print("      扫了 %d 个点，遇到 %d 种不同构型，全部落在上面那 %d 种之内（越界 %d 个）"
          % (n * n, len(seen), len(configs), bad))
    if bad:
        fail.append("连续扫描扫到枚举之外的接触构型，完备性论证失效")

    # ---------- §2 可达包络 ----------
    print("\n§2 可达包络（机械上到底能错多少，全部由 ECHO 数字推出）")
    envs = envelopes()
    for name, ex, ez, why in envs:
        print("  %-28s ΔX ∈ [%+.3f, %+.3f]  ΔZ ∈ [%+.3f, %+.3f]" % (name, ex[0], ex[1], ez[0], ez[1]))
        print("      %s" % why)
    # 倾斜自由度折算
    x_slack = (envs[0][1][1] - envs[0][1][0])
    height = MODULE_ENV_Y[1] - MODULE_ENV_Y[0]
    theta = math.atan2(x_slack, height)
    tilt_lat = PIN_TRAVEL * math.tan(theta)
    print("  倾斜/半插入：总成 Y 高 %.3f mm，X 向总松动 %.3f mm → 最大倾角 %.4f°；"
          % (height, x_slack, math.degrees(theta)))
    print("      针压缩量差最大 = DOCK_PIN_TRAVEL %.2f mm → 接触点附加横向偏移 ≤ %.4f mm，"
          "已远小于 E2 的 %.2f，**并入平移处理，不单列**。" % (PIN_TRAVEL, tilt_lat, DOCK_X_TOL))
    print("  ⚠ E1/E2 只覆盖「装对了但没对准」。**整格级别的错位不是公差问题**："
          "弹簧针小板在底座主板上贴错一个间距、触点焊盘阵列在 PCB 上画错一格、"
          "或 AS-17 翻盘导致的镜像，都直接落在 (±1,0)/(0,±1) 乃至镜像变体上，")
    print("      一步跨过 E2 的 %.2f 直达 %.2f 以上。这类错误只能靠打板前的 AS-17 关闭、"
          "首件导通表与丝印防呆挡，挡不住就是 §4/§5 里那些事件。" % (DOCK_X_TOL, PITCH - R_TOUCH))

    # ---------- §3 133 种平移构型全量普查 ----------
    print("\n§3 %d 种平移构型 × 4 种工况全量普查" % len(configs))
    pin_side, pad_side = variant_alloc(alloc, "nominal")
    all_keys = tuple(sorted({n for _p, _c, _r, n, _pin in alloc if n.startswith("KEY_")}))
    CASES = [((), False, "开关全断、主机 5V_IN 不带电（名义）"),
             (all_keys, False, "十键全按下"),
             ((), True, "主机 5V_IN 带电（原生 USB 供电，AS-11 unknown）"),
             (all_keys, True, "十键全按下 ＋ 主机 5V_IN 带电")]
    census = {}
    table = {}          # (case_idx, cfg) -> (等级, 事件)
    for ci, (pressed, live, _name) in enumerate(CASES):
        c = defaultdict(int)
        for cfg in configs:
            cts = contacts_for_offsets(cfg, alloc)
            ev, _d, _cm = analyze(pin_side, pad_side, cts,
                                  pressed_keys=pressed, host_5v_in_live=live)
            w = worst(ev)
            c[w] += 1
            table[(ci, cfg)] = (w, ev)
        census[ci] = c
    print("  等级：D1 致命（存在一条避开 GND 的 5V→GPIO 通路，接触是逐个建立的，"
          "只要存在这样的接触子集就存在致损时间窗）")
    print("        D1S 条件致命（5V 与 GPIO 连通，但每条通路都经过已被短路到 GND 的网 —— "
          "后果取决于底座限流/短路关断的响应与恢复方式，AS-11/AS-24/AS-26 未关闭）")
    print("        D2 可疑（主机 5V_IN 对 GND 外部短路，Grok G04 那一条）｜"
          "D3 良性短路（底座 5V 对地）｜D4 功能错误｜D0 无接触")
    print("  %-46s %5s %5s %5s %5s %5s %5s" % ("工况", "D1", "D1S", "D2", "D3", "D4", "D0"))
    for ci, (_p, _l, name) in enumerate(CASES):
        c = census[ci]
        print("  %-46s %5d %5d %5d %5d %5d %5d"
              % (name, c["D1"], c["D1S"], c["D2"], c["D3"], c["D4"], c["D0"]))

    # 切比雪夫距离 1 的 8 例（含 4 个对角）逐例
    print("\n  切比雪夫距离 = 1 的 8 个单格错位（含 4 个对角），名义工况逐例：")
    for (k, l) in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
        w, ev = table[(0, frozenset([(k, l)]))]
        note = "；".join(e[2] for e in ev[:2]) if ev else "无事件"
        print("    (%+d,%+d)  %-4s %s" % (k, l, w, note))
    print("    → 8 例里 D1（确定致命）%d 例。提案说「0 例」，就**直接注入**这个机制而言是对的；"
          % sum(1 for (k, l) in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
                if table[(0, frozenset([(k, l)]))][0] == "D1"))
    print("      但提案的脚本只判「5V 针有没有落到 GPIO 焊盘上」，没建多跳模型，"
          "因而漏掉了下面这些 D1S。")

    # ---------- §4 致命事件清单 ----------
    print("\n§4 会打坏主机的事件清单")
    rows = [(cfg, table[(0, cfg)][0], table[(0, cfg)][1],
             contacts_for_offsets(cfg, alloc)) for cfg in configs]

    def onsets(sel):
        """sel(cfg, case) → bool。返回 (min|Δ|, 纯 X 门槛, 纯 Z 门槛, 命中清单)。"""
        hit = []
        for ci in range(len(CASES)):
            for cfg in configs:
                if sel(cfg, ci):
                    hit.append((cfg, ci, region_bounds(cfg), table[(ci, cfg)][1]))
        if not hit:
            return (float("inf"), float("inf"), float("inf"), [])
        g = min(h[2][0] for h in hit)
        xs = [h[2][1] for h in hit if h[2][2] < 1e-9]
        zs = [h[2][2] for h in hit if h[2][1] < 1e-9]
        return (g, min(xs) if xs else float("inf"), min(zs) if zs else float("inf"), hit)

    d1_all = onsets(lambda cfg, ci: table[(ci, cfg)][0] == "D1")
    d1_nom = onsets(lambda cfg, ci: ci == 0 and table[(ci, cfg)][0] == "D1")
    d1s_nom = onsets(lambda cfg, ci: ci == 0 and table[(ci, cfg)][0] == "D1S")

    print("\n  [D1 确定致命] 名义工况共 %d 种构型；四种工况合计 %d 种（去重 %d）"
          % (len(d1_nom[3]), len(d1_all[3]), len({h[0] for h in d1_all[3]})))
    seen = set()
    for cfg, ci, b, ev in sorted(d1_all[3], key=lambda t: (t[2][0], sorted(t[0]))):
        if cfg in seen:
            continue
        seen.add(cfg)
        print("    %-26s |Δ| ≥ %6.3f  |ΔX| ≥ %6.3f  |ΔZ| ≥ %6.3f  [%s]"
              % (fmt_cfg(cfg), b[0], b[1], b[2], CASES[ci][2].split("（")[0]))
        print("        通路：%s" % ev[0][2])
    print("\n  [D1S 条件致命] 名义工况共 %d 种构型，最早出现在 |Δ| ≥ %.3f mm。"
          % (len(d1s_nom[3]), d1s_nom[0]))
    for cfg, ci, b, ev in sorted(d1s_nom[3], key=lambda t: t[2][0])[:8]:
        print("    %-26s |Δ| ≥ %6.3f  %s" % (fmt_cfg(cfg), b[0], ev[0][2]))
    if len(d1s_nom[3]) > 8:
        print("    …… 其余 %d 种见 --verbose" % (len(d1s_nom[3]) - 8))

    print("\n  连续位移下的致损门槛（解析解，非采样；用构型闭包求下界，故「低于此值不可能」成立）：")
    for label, o in (("D1 确定致命", d1_all), ("D1S 条件致命", d1s_nom)):
        print("    %-12s 任意方向 |Δ| ≥ %6.3f ｜ 纯 X 向 |ΔX| ≥ %6.3f ｜ 纯 Z 向 |ΔZ| ≥ %6.3f mm"
              % (label, o[0], o[1], o[2]))
    for nm, ex, ez, _w in envs[:2]:
        m = max(abs(ex[0]), abs(ex[1]), abs(ez[0]), abs(ez[1]))
        print("    对 %s（最大 %.3f mm）：D1 安全系数 %.2f 倍，D1S 安全系数 %.2f 倍"
              % (nm, m, d1_all[0] / m, d1s_nom[0] / m))
    fatal_rows = [(cfg, ev, b, CASES[ci][0] != (), CASES[ci][1], None)
                  for cfg, ci, b, ev in d1_all[3]]

    # ---------- §5 姿态与镜像变体 ----------
    print("\n§5 平移之外的自由度")
    # 绕 Y 180°
    pads_rot = [(-x, -z) for (x, z) in (cell_xz(c, r) for _p, c, r, _n, _pin in alloc)]
    pins = [cell_xz(c, r) for _p, c, r, _n, _pin in alloc]
    dmin = min(math.hypot(px - qx, pz - qz) for (px, pz) in pins for (qx, qz) in pads_rot)
    need = dmin - R_TOUCH
    print("  绕 Y 轴 180°（前后翻转放入）：焊盘场映到 X ∈ [%+.3f, %+.3f]，底座针场在 X ∈ [%+.3f, %+.3f]；"
          % (-cell_xz(COLS, 0)[0], -cell_xz(1, 0)[0], cell_xz(1, 0)[0], cell_xz(COLS, 0)[0]))
    print("      最近一对针-盘中心距 %.3f mm，要接触还需再平移 %.3f mm，"
          "而 E1 给的最大平移只有 %.3f mm → **零接触**，无事件。"
          % (dmin, need, max(abs(envs[0][1][0]), abs(envs[0][1][1]))))
    print("  绕 X 轴 180° / 绕 Z 轴 180°：触点面法向由 −Y 翻成 +Y，焊盘朝上，"
          "几何上与朝上的针不可能配合 → 零接触，无事件。")
    print("  装到右侧模块槽：本 ICD 只定义左槽 H2；右槽针脚合同 unknown，**本脚本不判**，不编。")
    print("\n  镜像/错排变体（这一类不是用户插歪，是板子做错或 AS-17 翻盘；在 Δ = 0 就生效）：")
    variant_fatal = []
    for kind, desc in VARIANTS:
        ps, pd = variant_alloc(alloc, kind)
        worst_v, first = "D0", None
        for cfg in configs:
            cts = contacts_for_offsets(cfg, alloc)
            ev, _d, _c = analyze(ps, pd, cts)
            w = worst(ev)
            if SEVERITY.index(w) > SEVERITY.index(worst_v):
                worst_v, first = w, (cfg, ev)
            if w in ("D1", "D1S") and frozenset([(0, 0)]) == cfg and kind != "nominal":
                variant_fatal.append((kind, desc, ev))
        z = frozenset([(0, 0)])
        ev0, _d, _c = analyze(ps, pd, contacts_for_offsets(z, alloc))
        print("    %-14s %-52s Δ=0 时：%s" % (kind, desc, worst(ev0)))
        for e in ev0:
            if e[0] in ("D1", "D1S"):
                print("        %s：%s" % ("致命" if e[0] == "D1" else "条件致命", e[2]))

    # ---------- §6 判据断言 ----------
    print("\n§6 判据断言")
    # C1
    reach_fatal = []
    for cfg, ev, b, pr, lv, cts in fatal_rows:
        for nm, ex, ez, _w in envs[:2]:
            if in_env(b, (ex, ez)):
                reach_fatal.append((nm, cfg, ev, pr, lv))
    if reach_fatal:
        print("  C1 5V→GPIO：**不通过**，可达包络内有致命事件：")
        for nm, cfg, ev, pr, lv in reach_fatal[:20]:
            print("      %s / %s / 开关%s / 5V_IN%s：%s"
                  % (nm, fmt_cfg(cfg), "按下" if pr else "断开", "带电" if lv else "不带电", ev[0][2]))
        fail.append("C1：可达包络内存在 5V→GPIO 致命事件")
    else:
        print("  C1 5V→GPIO：通过。可达包络 E1(±%.2f/±%.2f)、E2(±%.2f/±%.2f) 内没有任何 D1 事件；"
              % (max(abs(envs[0][1][0]), abs(envs[0][1][1])), max(abs(envs[0][2][0]), abs(envs[0][2][1])),
                 DOCK_X_TOL, DOCK_Z_TOL))
        print("      D1 最早出现在 |Δ| ≥ %.3f mm，D1S 最早出现在 |Δ| ≥ %.3f mm。"
              % (d1_all[0], d1s_nom[0]))
    # C1b：条件致命
    d1s_reach = [c for c, ci, b, ev in d1s_nom[3] if in_env(b, (envs[1][1], envs[1][2]))]
    if d1s_reach:
        print("  C1b D1S：**不通过**，E2 内有 %d 种构型出现条件致命。" % len(d1s_reach))
        fail.append("C1b：设计公差包络内存在 D1S 条件致命事件")
    else:
        print("  C1b D1S：E2 设计公差包络内无 D1S；但它只比 E2 大 %.2f 倍，"
              "而 E2 本身的最坏值 0.45 「正好等于允许偏移 0.55 减 0.10 余量」，"
              "这一层裕度全靠一级机械防呆。" % (d1s_nom[0] / DOCK_X_TOL))
    # C2
    field_pins = {p for _pos, _c, _r, _n, p in alloc}
    c2_ok = (18 not in field_pins) and (19 not in field_pins) and (10 not in field_pins) \
        and (13 not in field_pins) and (15 not in field_pins)
    print("  C2 5V_OUT（H2 pin 18）：触点场用到的 H2 针 = %s；"
          % sorted(x for x in field_pins if x))
    print("      pin 18 不在其中，且 netlist.yaml:364–366 与 ICD:96 要求该焊盘不连铜、无测试点 → "
          "场内没有任何导体属于 5V_OUT，**任何错位都不可能连上它**。%s"
          % ("通过" if c2_ok else "**不通过**"))
    if not c2_ok:
        fail.append("C2：5V_OUT/3V3/EEPROM_A0/USJ 之一被引入了触点场")
    # C3
    d2_cfgs = [(cfg, ev) for cfg, w, ev, _ in rows if any(e[0] == "D2" for e in ev)]
    print("  C3 GND→5V_IN（Grok G04）：名义工况下 %d 种构型出现「主机 5V_IN 对 GND 外部短路」这个**事件**"
          "（按最严重等级归类时只有 %d 种落在 D2，其余被同构型里更严重的 D1/D1S 盖住）。"
          % (len(d2_cfgs), census[0]["D2"]))
    if d2_cfgs:
        d2_reach = [c for c, _e in d2_cfgs if in_env(region_bounds(c), (envs[1][1], envs[1][2]))]
        print("      其中落在 E2 设计公差包络内的：%d 种。" % len(d2_reach))
        for c, _e in sorted(d2_cfgs, key=lambda t: region_bounds(t[0])[0])[:8]:
            b = region_bounds(c)
            print("        %-26s 最小 |Δ| ≥ %.3f mm" % (fmt_cfg(c), b[0]))
        print("      G04 的结论：这一级**不能靠排法消掉**，只能写成条件 —— 后果取决于主机 5V_IN "
              "对外部短路的耐受（AS-11、AS-24 unknown）。ICD 3.3 二级表里的「无损」必须加前提。")
    # C4
    d4 = [(cfg, ev) for cfg, w, ev, _ in rows if any(e[0] == "D4" for e in ev)]
    gsh = [(cfg, e) for cfg, w, ev, _ in rows for e in ev if e[1] == "GPIO↔GPIO"]
    print("  C4 功能错误：%d 种构型出现 D4 事件；其中「两根主机 GPIO 互相短接」共 %d 条，"
          "分布在 %d 种构型里（不致命，但必须报）。"
          % (len(d4), len(gsh), len({c for c, _e in gsh})))
    for cfg, e in gsh[:6]:
        print("        %-26s %s" % (fmt_cfg(cfg), e[2]))

    # 变体裁决
    if variant_fatal:
        print("\n  变体裁决：以下变体在 **Δ = 0（完美对位）** 就产生 D1，"
              "说明本分配表对这一类装配/制造错误没有任何几何冗余：")
        for kind, desc, ev in variant_fatal:
            print("      %-14s %s" % (kind, ev[0][2]))
        fail.append("变体：%s 在 Δ=0 即出现 5V→GPIO（AS-17 未关闭前不能放行）"
                    % "、".join(sorted({k for k, _d, _e in variant_fatal})))

    if verbose:
        print("\n§7 全量普查明细（名义工况）")
        for cfg, w, ev, cts in sorted(rows, key=lambda t: (t[1], sorted(t[0]))):
            print("  %-26s %s  接触 %2d 处  %s"
                  % (fmt_cfg(cfg), w, len(cts), "；".join(e[2] for e in ev[:3]) or "—"))

    print("\n" + "=" * 78)
    if fail:
        print("裁决：**不通过**，%d 条（分两类：提案本身的阻断 / 依赖未关闭假设的条件阻断）：" % len(fail))
        for f in fail:
            print("  - %s" % f)
        print("=" * 78)
        return 1
    print("裁决：通过。可达包络内无致命事件。")
    print("=" * 78)
    return 0


def main():
    ap = argparse.ArgumentParser(description="弹簧针触点场错位穷举判定")
    ap.add_argument("--scheme", default="proposal", choices=sorted(SCHEMES))
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--step", type=float, default=0.05, help="连续扫描交叉验证步长 (mm)")
    ap.add_argument("--pad-d", type=float, default=None,
                    help="改焊盘直径做敏感性（PINMAP.md:119 AS-31-mb-3 写 Ø1.8，"
                         "module_board.scad:123 写 2.0，两者不一致，未关闭）")
    a = ap.parse_args()
    if a.pad_d is not None:
        global PAD_D, R_TOUCH, R_RELIABLE
        PAD_D = a.pad_d
        R_TOUCH = (PAD_D + PIN_TIP_D) / 2.0
        R_RELIABLE = (PAD_D - PIN_TIP_D) / 2.0
    try:
        return run(a.scheme, a.verbose, a.step)
    except AssertionError as e:
        print("自检失败（完备性论证不成立）：%s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
