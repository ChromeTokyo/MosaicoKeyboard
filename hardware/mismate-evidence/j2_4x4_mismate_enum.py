#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
j2_4x4_mismate_enum.py —— J2 触点场错位**穷举**判定（方案 J / 4 行 × 4 列）

提案 · 未冻结 · 不得据以制造。

审的是哪张表
------------
「GND 环抱 5V ＋ 砍掉 SDA/SCL」：5V×2 + GND×4 + 10 键，见 §0.2 的 PROPOSAL。
换方案只改 §0.2 那张表。

⚠ 同目录下 `j2_mismate_exhaustive.py` / `check_pogo_mismate.py` 是**另一路并行工作**
  在审别的分配（P2「角位 5V ＋ 哑位护城河」，9 键弃 I²C）。两者结论不可互相引用。

要关闭的三条
------------
1. 裁定未关闭项：「`DOCK_ROWS` 由 2 改 4 的电气后果完全没做」。
2. Grok G04：ICD 第 3.3 节「X−1 列无损」对 `GND → 5V_IN` 方向覆盖不正确。
3. Grok G05：错位枚举不完整，只算了「错一列」「错一行」，没算对角错位和错多列。

对 G05 的正面回答（为什么这是穷举而不是举例）
---------------------------------------------
平移这一维**不采样**，是精确求解的：

  固定朝向 A。底座针 i 名义位置 p_i、模块焊盘 j 在 q_j，平移 t。
  「针 i 与盘 j 接触」⟺ ‖(A·p_i + t) − q_j‖ ≤ r ⟺ t 落在以 c_ij = q_j − A·p_i
  为心、半径 r 的圆盘内。

  于是**接触集只是 t 的函数，且只在这 256 个等半径圆的边界上变化**。
  这些圆把 t 平面切成若干「面」，同一面内接触集恒定 ⇒ 电气结论恒定。
  只要每个面取一个代表点，就等价于把连续的 t 平面枚举完了。

  代表点的完备性论证：**256 个圆半径全相等**，等半径圆不可能严格内含，
  故任何有界面的边界上必有至少一个圆–圆交点。所以
      {全部圆–圆交点各向 8 个方向偏 ε} ∪ {全部圆心}
  必然命中每一个面。又因 A ∈ D4 时 c_ij 全落在 2.54 的格上，
  256 个圆心只有 ≤49 个互异值 ⇒ 交点数很小，可以真的跑完。

  对角、错多列、错多行、半格桥接、任意方向任意大小 —— 一次性全覆盖，
  没有「步长」这个概念，也就没有漏网的缝。§7 另用 0.05 mm 稠密扫描独立复验。

坐标系
------
屏幕朝使用者，USB-C 朝下。X 右、Y 上、Z 朝使用者，原点在 Mosaico 几何中心。
弹簧针轴向 +Y，触点面法向 −Y。全部计算在 XZ 平面内。

用法
----
    python3 hardware/j2_4x4_mismate_enum.py                # 审 proposal，flat+sharp 两档针头
    python3 hardware/j2_4x4_mismate_enum.py --all-schemes  # 连对照基线一起跑
    python3 hardware/j2_4x4_mismate_enum.py --tip flat
    python3 hardware/j2_4x4_mismate_enum.py --no-dense     # 跳过 §7 稠密复验
    python3 hardware/j2_4x4_mismate_enum.py --verbose

退出码（位标志，可叠加）
    0 = 无致命事件、结构断言全过
    1 = 存在会打坏主机的事件
    2 = 结构性/跨分支一致性断言失败

纯 python3 标准库。
"""

import argparse
import itertools
import math
import os
import re
import subprocess
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# =============================================================================
# §0  数据表 —— **换方案只改这一节**
# =============================================================================

# ---- 0.1 几何 ---------------------------------------------------------------
# 来源：本脚本作者亲自编译 claude/design-d/mech-module 的
#       mechanical/module-board/module_board.scad 取 ECHO
#       （openscad -o mb.stl module_board.scad；Status NoError / Vertices 2314 / Facets 4768）
#   ECHO: "ICD 第 1 节待填参数 → DOCK_PIN_FIELD_X0 = -34.405
#          DOCK_PIN_FIELD_Z0 = 2.75  DOCK_PIN_FIELD_Y = -24.095"
#   ECHO: "J2 列 1..4 中心 X = [-34.405, -31.865, -29.325, -26.785]"
#   ECHO: "J2 行 A..4 中心 Z = [2.75, 0.21, -2.33, -4.87]（行 A 在 +Z 屏侧）"
#   ECHO: "[检查 6] 允许偏移 = 0.55 mm，余量 = 0.1 mm。相邻焊盘净间距 0.54 mm"
#   ECHO: "[检查 8] 绕 Y 轴 180° 错放时触点场映射到 X [26.785 , 34.405]"
# ⚠ module_board.scad 第 270/271 行**行尾注释**写的「列 1 中心 X = −32.405 /
#   行 A 中心 Z = +2.95」是过期值（修订 d 触点板整体 −X 移 2.00 后注释没跟着改）；
#   mech-dock 分支 dock_shell.scad 第 288 行注释「DOCK_FIELD_XC = −28.595」同样过期
#   （由它自己的 X0 = −34.405 推出应为 −30.595）。**只信 ECHO，不信行尾注释。**
PITCH     = 2.54      # module_board.scad:119 DOCK_PITCH
N_COLS    = 4         # module_board.scad:120 DOCK_COLS（dock_shell.scad:86 同）
N_ROWS    = 4         # module_board.scad:121 DOCK_ROWS（dock_shell.scad:87 同）
FIELD_X0  = -34.405   # [ECHO] 列 1 中心 X
FIELD_Z0  = 2.75      # [ECHO] 行 A 中心 Z
FIELD_Y   = -24.095   # [ECHO] 配合面 Y
PAD_D     = 2.0       # module_board.scad:123 DOCK_PAD_D
PIN_TIP_D = 0.9       # module_board.scad:129 DOCK_PIN_TIP_D
TOL_X     = 0.45      # module_board.scad:144 DOCK_X_TOL
TOL_Z     = 0.45      # module_board.scad:145 DOCK_Z_TOL

ROW_LETTER = ["A", "B", "C", "D"]   # 行 A 靠 +Z（屏侧），行 D 靠 −Z（背侧）；ICD 第 3.1 节口径

# ---- 0.2 模块板 J2 焊盘逐位分配（**待检验的提案**） --------------------------
# 格式：(列 1..4, 行索引 0..3) -> 网名
PROPOSAL = {
    (1, 0): "DOCK_5V",   (2, 0): "DOCK_GND",  (3, 0): "KEY_UP",    (4, 0): "KEY_A",
    (1, 1): "DOCK_5V",   (2, 1): "DOCK_GND",  (3, 1): "KEY_DOWN",  (4, 1): "KEY_B",
    (1, 2): "DOCK_GND",  (2, 2): "DOCK_GND",  (3, 2): "KEY_LEFT",  (4, 2): "KEY_X",
    (1, 3): "KEY_L",     (2, 3): "KEY_R",     (3, 3): "KEY_RIGHT", (4, 3): "KEY_Y",
}

# 对照基线：旧 2×8 逐针表（ICD 第 3.2 节 = dock-board netlist.yaml j2_contract）
# 按 A1,B1,A2,B2,…,A8,B8 十六个网依次列优先填进 4×4 —— 裁定说的「直接折成 4×4」。
_OLD_2x8 = ["DOCK_5V", "DOCK_5V", "DOCK_GND", "DOCK_GND",
            "KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT",
            "KEY_L", "KEY_R", "KEY_A", "KEY_B",
            "KEY_X", "KEY_Y", "DOCK_SDA", "DOCK_SCL"]
BASELINE = {(c, r): _OLD_2x8[(c - 1) * 4 + r] for c in range(1, 5) for r in range(4)}

SCHEMES = {"proposal": PROPOSAL, "baseline": BASELINE}

# ---- 0.3 底座弹簧针场 -------------------------------------------------------
# dock-board netlist.yaml 第 73–74 行原文：
#   「底座弹簧针针尖朝 +Y，与模块板焊盘用**相同 (X, Z)**，两板之间不做镜像」
# 故底座针场 = 模块焊盘场的同名副本。这不是自由度，是合同。
def dock_field_from(module_field):
    return dict(module_field)

# ---- 0.4 网 → 电气身份 ------------------------------------------------------
# KEY_* → H2 针号 → GPIO：module-board 分支 PINMAP.md 第 2 节（逐行核过 10 行，
# 与 ICD 第 2 节、dock-board netlist.yaml key_map 三处一致）。
KEY_TO_H2_GPIO = {
    "KEY_UP":    (1,  55), "KEY_DOWN":  (3,  19), "KEY_LEFT":  (5,  18),
    "KEY_RIGHT": (7,  17), "KEY_L":     (9,  16), "KEY_R":     (11, 15),
    "KEY_A":     (2,  53), "KEY_B":     (4,  48), "KEY_X":     (6,  13),
    "KEY_Y":     (8,  12),
}
H2_5V_IN, H2_5V_OUT, H2_3V3, H2_GND = 17, 18, 19, 20
ALLOWED_GPIO = {55, 53, 19, 48, 18, 13, 17, 12, 16, 15, 4}   # ICD 第 2 节：11 根，**不含 GPIO14**
FORBIDDEN_H2_PINS = {10, 13, 15, 18}                          # ICD 第 2 节：KEY_* 不得落在这些针
R_S_KEY_OHM = 1000.0                 # netlist.yaml:162-171，提案 1 kΩ（备选 0 Ω）
U_LIM_IOS_MA = (1215, 1308, 1415)    # POWER_TOPOLOGY.md 第 2.6 节 Table 2（TPS2553 + 19.6 kΩ）

# ---- 0.5 针头形状（AS-31-mm-5 只定了 Ø0.9、行程、压力，**没定形状**）--------
TIP_CRITERIA = {
    "flat":  (PAD_D + PIN_TIP_D) / 2.0,   # 1.45 平头/冠头：铜搭上铜就算接触
    "sharp": PAD_D / 2.0,                 # 1.00 尖头/球头：针心落进盘内才算
}
R_RELIABLE = (PAD_D - PIN_TIP_D) / 2.0    # 0.55 针尖整体入盘 = scad [检查 6] 的「接触可靠」判据
                                          # 判「碰没碰上」必须用 1.45，用 0.55 会漏掉全部桥接

# =============================================================================
# §1  几何
# =============================================================================

def pad_xz(col, row):
    return (FIELD_X0 + (col - 1) * PITCH, FIELD_Z0 - row * PITCH)

FIELD_SPAN = (N_COLS - 1) * PITCH            # 7.62
FIELD_CX   = FIELD_X0 + FIELD_SPAN / 2.0     # −30.595
FIELD_CZ   = FIELD_Z0 - FIELD_SPAN / 2.0     # −1.06

# =============================================================================
# §2  变换群 —— 完备性论证
# =============================================================================
#
# 任何一次「模块相对底座针场放错」都是 XZ 平面内的等距变换 T(v) = A·v + t，A ∈ O(2)。
#
# (一) 线性部分 A。任务书点名要覆盖的四项在 O(2) 里分别是：
#      * 绕 Y 轴转 θ   → XZ 平面内转 θ（θ=180° 即「前后翻转放入」）
#      * 绕 Z 轴 180°  → (x,y,z)→(−x,−y,z)，触点面法向由 −Y 翻成 +Y。
#                        **实物触点面朝上、无法与朝上的弹簧针配合**，但它在 XZ 平面内
#                        诱导的映射恰是镜像 MX(x→−x)；而「EDA 里 J2 封装被镜像/底层
#                        放置」是真实可发生的，故必须枚举。
#      * 绕 X 轴 180°  → 同理诱导 MZ(z→−z)
#      * 镜像误装      → MX / MZ / MD1 / MD2
#      ⇒ 至少要枚举正方形网格的对称群 D4（8 个元素）。
#        θ ∉ {0,90,180,270}° 由 §6d 连续扫描单独处理，不靠「转歪了就配合不上」搪塞。
#
# (二) A 绕哪个点转 —— 这一条以前的分析没说清，两种约定结论完全不同：
#      * 绕**触点场中心**转：场转完还压在原地 ⇒ 对应「EDA 封装被旋转/镜像放置」，
#        以及「机械防呆失效、整机在槽里被转过来但仍落在针场上」。
#      * 绕**Mosaico 几何中心（原点）**转：对应「整机真的被翻过来放进槽」，场被甩到别处。
#      本脚本统一**绕触点场中心**做 A，再对 t 做全平面穷举 ⇒「绕原点转」只是该朝向下
#      的某一个特定 t，被自动包含。§6e 把那个 t 算出来单独报，并与 ECHO [检查 8] 对账。
#
D4 = {
    "R0":   ((1, 0), (0, 1)),
    "R90":  ((0, -1), (1, 0)),
    "R180": ((-1, 0), (0, -1)),
    "R270": ((0, 1), (-1, 0)),
    "MX":   ((-1, 0), (0, 1)),
    "MZ":   ((1, 0), (0, -1)),
    "MD1":  ((0, 1), (1, 0)),
    "MD2":  ((0, -1), (-1, 0)),
}
D4_NOTE = {
    "R0":   "正确朝向",
    "R90":  "绕 Y 轴 +90°（场绕自身中心）",
    "R180": "绕 Y 轴 180°（任务书点名：前后翻转放入）",
    "R270": "绕 Y 轴 −90°（场绕自身中心）",
    "MX":   "镜像 x→−x（= 绕 Z 轴 180°「上下颠倒」的 XZ 诱导；实物触点面朝上，EDA 镜像放置可发生）",
    "MZ":   "镜像 z→−z（= 绕 X 轴 180° 的 XZ 诱导；同上）",
    "MD1":  "对角镜像（EDA 封装误放）",
    "MD2":  "对角镜像（EDA 封装误放）",
}

def apply_A(A, v):
    (a, b), (c, d) = A
    return (a * v[0] + b * v[1], c * v[0] + d * v[1])

def pin_nominal(A, key):
    """底座针 key 在朝向 A 下、平移为 0 时的位置（A 绕触点场中心作用）。"""
    x, z = pad_xz(*key)
    dx, dz = apply_A(A, (x - FIELD_CX, z - FIELD_CZ))
    return (FIELD_CX + dx, FIELD_CZ + dz)

def rot_matrix(deg):
    t = math.radians(deg)
    return ((math.cos(t), -math.sin(t)), (math.sin(t), math.cos(t)))

# =============================================================================
# §3  电气模型（并查集，支持多跳桥接）
# =============================================================================
#
# 为什么不做「逐针对照表」：相邻焊盘净间距只有 2.54 − 2.0 = 0.54 mm，小于针尖 Ø0.9，
# 一根平头针在半格处会同时压住两个盘。于是
#     5V 针 → 盘X →（同网铜）→ 盘Y → 另一根针 → 盘Z …
# 这种**多跳**通路真实存在，逐针对照表抓不到。故建图 + 并查集。
#
class DSU:
    __slots__ = ("p",)
    def __init__(self):
        self.p = {}
    def find(self, x):
        p = self.p
        if x not in p:
            p[x] = x
            return x
        r = x
        while p[r] != r:
            r = p[r]
        while p[x] != r:
            p[x], x = r, p[x]
        return r
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb

N_5V_RAIL  = ('DOCKNET', '5V_RAIL')
N_GND_RAIL = ('DOCKNET', 'GND_RAIL')
N_H5V      = ('HOST', H2_5V_IN)
N_HGND     = ('HOST', H2_GND)

def build_graph(contacts, module_field, dock_field, keys_pressed):
    d = DSU()
    edges = []
    def link(a, b, why):
        d.union(a, b)
        edges.append((a, b, why))

    # (a) 模块板内部：同网焊盘同铜
    by_net = defaultdict(list)
    for k, net in module_field.items():
        by_net[net].append(k)
    for net, ks in by_net.items():
        for k in ks[1:]:
            link(('PAD',) + ks[0], ('PAD',) + k, f"模块板 {net} 同网铜 ≈0Ω")

    # (b) 模块板 → 主机 H2
    for k, net in module_field.items():
        if net == "DOCK_5V":
            link(('PAD',) + k, N_H5V, "J1 pin17 纯铜（硬约束 1 禁串联器件）≈0Ω")
        elif net == "DOCK_GND":
            link(('PAD',) + k, N_HGND, "J1 pin20 ≈0Ω")
        elif net in KEY_TO_H2_GPIO:
            h2, _ = KEY_TO_H2_GPIO[net]
            link(('PAD',) + k, ('HOST', h2), f"R_S_{net} {R_S_KEY_OHM:.0f}Ω")
        # DOCK_SDA/SCL：模块板侧经 **DNP 0Ω** R_LINK_* 才到主机，默认不装 ⇒ 不连 HOST。

    # (c) 底座内部
    for k, net in dock_field.items():
        if net == "DOCK_5V":
            link(('PIN',) + k, N_5V_RAIL, "底座 DOCK_5V 轨 ≈0Ω")
        elif net == "DOCK_GND":
            link(('PIN',) + k, N_GND_RAIL, "底座 DOCK_GND 轨 ≈0Ω")
    if keys_pressed:
        # 硬约束 5：底座对 KEY_* 不放任何上拉、不接任何电源；开关另一端接 DOCK_GND
        for k, net in dock_field.items():
            if net in KEY_TO_H2_GPIO:
                link(('PIN',) + k, N_GND_RAIL, f"底座 SW_{net[4:]} 闭合 ≈0Ω")

    # (d) 针-盘接触
    for pk, qk in contacts:
        link(('PIN',) + pk, ('PAD',) + qk, "弹簧针接触 ≈0Ω")

    return d, edges

# =============================================================================
# §4  判据 —— 每一条显式断言
# =============================================================================
#
# 判据 1（致命）：任何情形下 5V_IN 不得接触到任何 GPIO 网。
#   **精确表述**：某个 5 V 源（底座 DOCK_5V 轨 或 主机 H2 pin17）与某根主机 GPIO
#   低阻连通，**且该连通分量里没有地**。
#   为什么必须加后半句：若同一分量里同时有地，该节点被底座 U_LIM（TPS2553 恒流型，
#   IOS 1215/1308/1415 mA）拖成对地短路，节点电位塌到 ≈0 V，GPIO 看到 0 V 而不是 5 V
#   —— 那是「电源短路 + 假按键」，不是打穿 SoC。这正是本提案的核心论证，
#   所以必须把两类分开判，不能混成一个「同一分量」了事。
#   （2026-09-22：本脚本第一版没加后半句，把 8 个单步全报成致命，是误报，已改。）
#
# 判据 2（致命）：5V_OUT（H2 pin18）绝不可被连接到任何东西 —— §8 静态断言。
# 判据 3（G04）：GND → 5V_IN 方向（5V_IN 与地低阻连通）。
# 判据 4（非致命但要报）：两根主机 GPIO 互相短接。
#
# 判据 1 的开关态论证（为什么不必枚举 2^10 种按键组合）：
#   闭合一个开关 = 加一条边（底座 KEY 针 → DOCK_GND 轨）。并查集里加边只会合并分量。
#   这条边有一端是**地节点**，所以任何由它引发的合并都会把地并进去。
#   ⇒ 闭合开关只能把「判据 1」降级成「判据 3」，**绝不可能凭空造出判据 1**。
#   故「全部开关松开」是判据 1 的精确最坏情形。脚本仍两态都跑，用于报判据 3/4。
#
F_5V_TO_GPIO = "F1"
F_5V_TO_GND  = "F3"
F_GPIO_SHORT = "F4"

def classify(dsu):
    hits = defaultdict(list)
    f5, fg = dsu.find(N_5V_RAIL), dsu.find(N_GND_RAIL)
    fh5, fhg = dsu.find(N_H5V), dsu.find(N_HGND)
    gnd_roots = {fg, fhg}
    src = {"底座 DOCK_5V 轨": f5, "主机 H2 pin17 5V_IN": fh5}

    for sname, sroot in src.items():
        grounded = sroot in gnd_roots
        for net, (h2, gpio) in KEY_TO_H2_GPIO.items():
            if dsu.find(('HOST', h2)) == sroot:
                if grounded:
                    hits[F_5V_TO_GND].append(
                        f"{sname} ↔ {net}(H2 pin{h2}, GPIO{gpio})：该分量同时含地 ⇒ 对地短路+假按键")
                else:
                    hits[F_5V_TO_GPIO].append(f"{sname} ↔ {net}(H2 pin{h2}, GPIO{gpio})")

    if fh5 in gnd_roots:
        hits[F_5V_TO_GND].append("主机 5V_IN ↔ 地（G04 方向）")
    if f5 in gnd_roots:
        hits[F_5V_TO_GND].append("底座 5V 轨 ↔ 地（由 U_LIM 限流吸收）")

    gh = [(('HOST', h2), net) for net, (h2, _) in KEY_TO_H2_GPIO.items()]
    for (na, a), (nb, b) in itertools.combinations(gh, 2):
        if dsu.find(na) == dsu.find(nb):
            hits[F_GPIO_SHORT].append(f"{a} ↔ {b}")
    return hits

def contacts_at(A, t, dock_field, r_contact):
    out = []
    r2 = r_contact ** 2 + 1e-12
    for pk in dock_field:
        px, pz = pin_nominal(A, pk)
        px += t[0]; pz += t[1]
        c0 = math.floor((px - FIELD_X0) / PITCH)
        r0 = math.floor((FIELD_Z0 - pz) / PITCH)
        for cc in (c0, c0 + 1):
            for rr in (r0, r0 + 1):
                col, row = int(cc) + 1, int(rr)
                if not (1 <= col <= N_COLS and 0 <= row < N_ROWS):
                    continue
                qx, qz = pad_xz(col, row)
                if (px - qx) ** 2 + (pz - qz) ** 2 <= r2:
                    out.append((pk, (col, row)))
    return out

def evaluate(A, t, module_field, dock_field, r_contact, pressed):
    ct = contacts_at(A, t, dock_field, r_contact)
    dsu, edges = build_graph(ct, module_field, dock_field, pressed)
    return classify(dsu), ct, dsu, edges

# =============================================================================
# §5  解析最小危险位移（闭式精确解）
# =============================================================================

def analytic_min_shift(A, module_field, dock_field, r_contact, kind):
    if kind == "5V->KEY":
        src = [k for k, n in dock_field.items() if n == "DOCK_5V"]
        dst = [k for k, n in module_field.items() if n in KEY_TO_H2_GPIO]
    else:  # "GND->5V"
        src = [k for k, n in dock_field.items() if n == "DOCK_GND"]
        dst = [k for k, n in module_field.items() if n == "DOCK_5V"]
    best = None
    for pk in src:
        px, pz = pin_nominal(A, pk)
        for qk in dst:
            qx, qz = pad_xz(*qk)
            need = max(0.0, math.hypot(qx - px, qz - pz) - r_contact)
            if best is None or need < best[0]:
                best = (need, pk, qk)
    return best

# =============================================================================
# §6  枚举
# =============================================================================

def arrangement_probes(A, dock_field, r_contact, eps=1e-4):
    """圆排列每个面取一个代表点 —— §2 说的「穷举而非采样」的落地。"""
    centers = set()
    for pk in dock_field:
        px, pz = pin_nominal(A, pk)
        for qk in dock_field:
            qx, qz = pad_xz(*qk)
            centers.add((round(qx - px, 9), round(qz - pz, 9)))
    centers = sorted(centers)
    probes = set(centers)
    R2 = (2 * r_contact) ** 2
    for i in range(len(centers)):
        x1, z1 = centers[i]
        for j in range(i + 1, len(centers)):
            x2, z2 = centers[j]
            dx, dz = x2 - x1, z2 - z1
            d2 = dx * dx + dz * dz
            if d2 <= 1e-18 or d2 > R2:
                continue                       # 不相交（等半径 ⇒ 无内含情形）
            d = math.sqrt(d2)
            h2 = r_contact * r_contact - (d / 2) ** 2
            if h2 < 0:
                continue
            h = math.sqrt(h2)
            mx, mz = x1 + dx / 2, z1 + dz / 2
            ux, uz = -dz / d, dx / d
            for s in (+1, -1):
                vx, vz = mx + s * h * ux, mz + s * h * uz
                for ox, oz in ((eps, 0), (-eps, 0), (0, eps), (0, -eps),
                               (eps, eps), (eps, -eps), (-eps, eps), (-eps, -eps)):
                    probes.add((round(vx + ox, 9), round(vz + oz, 9)))
    return sorted(probes), len(centers)

def fmt_pose(name, t):
    return f"{name} Δ=({t[0]:+.3f}, {t[1]:+.3f}) mm = ({t[0]/PITCH:+.2f}, {t[1]/PITCH:+.2f}) 格"

def describe_contact(pk, qk, dock_field, module_field):
    return (f"针(列{pk[0]},行{ROW_LETTER[pk[1]]})={dock_field[pk]}"
            f" → 盘(列{qk[0]},行{ROW_LETTER[qk[1]]})={module_field[qk]}")

def reachable_tag(name, t):
    if name != "R0":
        return "朝向本身已错（见可达性分层）"
    if abs(t[0]) <= TOL_X and abs(t[1]) <= TOL_Z:
        return "**定位公差 ±0.45 内可达**"
    if max(abs(t[0]), abs(t[1])) <= PITCH / 2:
        return "超公差但不足半格"
    return "超出定位公差（需槽壁失效）"


def run(scheme_name, tip, args, P):
    module_field = SCHEMES[scheme_name]
    dock_field = dock_field_from(module_field)
    r = TIP_CRITERIA[tip]

    P("=" * 78)
    P(f"方案 = {scheme_name}    针头判据 = {tip} (r_contact = {r:.3f} mm)")
    P(f"几何 [ECHO] 列 X = {[round(pad_xz(c,0)[0],3) for c in range(1,5)]}")
    P(f"           行 Z = {[round(pad_xz(1,rr)[1],3) for rr in range(4)]}   配合面 Y = {FIELD_Y}")
    P(f"           间距 {PITCH}  焊盘 Ø{PAD_D}  针尖 Ø{PIN_TIP_D}  定位公差 ±{TOL_X}/±{TOL_Z}")
    P(f"           相邻焊盘净间距 = {PITCH-PAD_D:.2f} mm < 针尖 Ø{PIN_TIP_D} ⇒ 平头针半格必桥接")
    P("=" * 78)
    P("")
    P("版图（自 +Y 俯视；+X 向右，行 A 在 +Z 屏侧）")
    P("        " + "".join(f"{'列'+str(c):<12}" for c in range(1, 5)))
    for rr in range(4):
        P(f"  行{ROW_LETTER[rr]}  " + "".join(f"{module_field[(c,rr)]:<12}" for c in range(1, 5)))

    # ---- §6a 解析最小危险位移 ---------------------------------------------
    P("")
    P("-" * 78)
    P("§6a  解析最小危险位移（闭式精确解，非采样）—— 只覆盖「直接单跳」这一路")
    P("-" * 78)
    P(f"{'朝向':<6}{'最小 5V针→KEY盘':<24}{'配对':<48}{'最小 GND针→5V盘'}")
    r0_direct = None
    for name, A in D4.items():
        h1 = analytic_min_shift(A, module_field, dock_field, r, "5V->KEY")
        h2 = analytic_min_shift(A, module_field, dock_field, r, "GND->5V")
        if name == "R0":
            r0_direct = h1[0]
        P(f"{name:<6}{h1[0]:>8.3f} mm ={h1[0]/PITCH:>6.2f} 格  "
          f"{describe_contact(h1[1], h1[2], dock_field, module_field):<48}"
          f"{h2[0]:>8.3f} mm ={h2[0]/PITCH:>6.2f} 格")
    P("")
    P(f"  ⇒ 正确朝向 R0 下，「5V 针铜面直接搭上 KEY 盘铜面」最小位移 = {r0_direct:.3f} mm "
      f"= {r0_direct/PITCH:.2f} 格；对定位公差 ±{TOL_X} 的余量 = {r0_direct/TOL_X:.2f}×")
    P("  ⚠ 这只是**直接单跳**。5V 还能经「底座 KEY 针当跳板」多跳到 GPIO，")
    P("    那条路不在本式覆盖内，由 §6c 的圆排列穷举负责。")

    # ---- §6b 单步八邻域 ----------------------------------------------------
    P("")
    P("-" * 78)
    P("§6b  正确朝向下的 8 个单步错位（±1 格八邻域）")
    P("     Δ列>0 = 针场向 +X（朝 Mosaico 中央）；Δ行>0 = 针场向 −Z（朝背侧，行号增大）")
    P("-" * 78)
    n_fatal_step = n_g04_step = 0
    for dcol in (-1, 0, 1):
        for drow in (-1, 0, 1):
            if dcol == 0 and drow == 0:
                continue
            t = (dcol * PITCH, -drow * PITCH)
            hits, ct, _, _ = evaluate(D4["R0"], t, module_field, dock_field, r, False)
            if F_5V_TO_GPIO in hits:
                n_fatal_step += 1
                tag, det = "**致命**", "  ← " + "; ".join(sorted(set(hits[F_5V_TO_GPIO]))[:3])
            elif F_5V_TO_GND in hits:
                n_g04_step += 1
                tag, det = "电源短路", "  ← 5V 与地同分量，U_LIM 限流吸收；GPIO 被拉到 ≈0 V = 假按键"
            else:
                tag, det = "无害", ""
            P(f"  Δ列{dcol:+d} Δ行{drow:+d}  接触 {len(ct):>2} 对   {tag:<9}{det}")
    P(f"  小计：8 个单步里 致命 {n_fatal_step} 个、电源短路 {n_g04_step} 个、"
      f"无害 {8-n_fatal_step-n_g04_step} 个")

    # ---- §6c 圆排列穷举 ----------------------------------------------------
    P("")
    P("-" * 78)
    P("§6c  平移维穷举（圆排列每面取代表点；等半径 ⇒ 每个有界面必有圆–圆交点）")
    P("-" * 78)
    fatal = []
    g04 = defaultdict(int)
    shorts = defaultdict(int)
    index = {}
    grand = 0
    for name, A in D4.items():
        probes, ncent = arrangement_probes(A, dock_field, r)
        nf = ng = ns = 0
        for t in probes:
            for pressed in (False, True):
                grand += 1
                hits, ct, _, _ = evaluate(A, t, module_field, dock_field, r, pressed)
                if F_5V_TO_GPIO in hits:
                    nf += 1
                    sig = (name, tuple(sorted(set(hits[F_5V_TO_GPIO]))))
                    cur = index.get(sig)
                    if cur is None:
                        e = {"orient": name, "t": t, "pressed": pressed,
                             "what": sorted(set(hits[F_5V_TO_GPIO])), "contacts": ct}
                        index[sig] = e
                        fatal.append(e)
                    elif math.hypot(*t) < math.hypot(*cur["t"]):
                        cur["t"], cur["pressed"], cur["contacts"] = t, pressed, ct
                if F_5V_TO_GND in hits:
                    ng += 1
                if F_GPIO_SHORT in hits:
                    ns += 1
        g04[name], shorts[name] = ng, ns
        P(f"  {name:<6}圆心 {ncent:>3} 个 / 代表点 {len(probes):>6} 个  "
          f"致命 {nf:>6}   电源短路 {ng:>6}   GPIO互短 {ns:>6}")
    P(f"  合计求值 {grand} 次（代表点 × 开关两态）")

    # ---- §6d 连续偏航角 ----------------------------------------------------
    P("")
    P("-" * 78)
    P("§6d  连续偏航角扫描（θ 每 0.5°，绕触点场中心）—— 不靠「转歪了就配合不上」搪塞")
    P("-" * 78)
    ys = []
    for i in range(720):
        deg = i * 0.5
        h1 = analytic_min_shift(rot_matrix(deg), module_field, dock_field, r, "5V->KEY")
        ys.append((h1[0], deg))
    ys.sort()
    non90 = [w for w in ys if abs(w[1] % 90) > 1e-9]
    small = sorted(w for w in ys if w[1] <= 15 or w[1] >= 345)
    P(f"  720 个角中最小 5V→KEY 位移的最小值 = {ys[0][0]:.3f} mm（θ={ys[0][1]}°）")
    P(f"  非 90° 倍数角中最危险：θ={non90[0][1]}°，最小位移 {non90[0][0]:.3f} mm")
    P(f"  小偏航（|θ| ≤ 15°，装配现实中可能发生）中最危险："
      f"θ={small[0][1]}°，最小位移 {small[0][0]:.3f} mm = {small[0][0]/PITCH:.2f} 格")

    # ---- §6e 整机刚体翻转对应的平移 ---------------------------------------
    P("")
    P("-" * 78)
    P("§6e 「整机绕 Mosaico 几何中心翻转」落在本枚举的哪个 t 上（与 ECHO [检查 8] 对账）")
    P("-" * 78)
    for name in ("R90", "R180", "R270"):
        A = D4[name]
        ax, az = apply_A(A, (FIELD_CX, FIELD_CZ))
        t = (ax - FIELD_CX, az - FIELD_CZ)
        xs = [pin_nominal(A, (c, 0))[0] + t[0] for c in range(1, 5)]
        hits, ct, _, _ = evaluate(A, t, module_field, dock_field, r, False)
        P(f"  {name}: t = ({t[0]:+.3f}, {t[1]:+.3f}) mm，‖t‖ = {math.hypot(*t):.3f} mm；"
          f"场落到 X ∈ [{min(xs):.3f}, {max(xs):.3f}]；接触 {len(ct)} 对；"
          f"致命 = {'是' if F_5V_TO_GPIO in hits else '否'}")
    P("  对账：ECHO [检查 8] 原文「绕 Y 轴 180° 错放时触点场映射到 X [26.785 , 34.405]」")
    P("  ⇒ 整机 180° 翻转靠的是「底座那里根本没有针」这个**缺席**，不是阻挡。")
    P("    AS-08 一天不关，这条就不算防呆。")

    # ---- §6f 可达包络内的余量（把「几格」换算成真实 mm） -------------------
    P("")
    P("-" * 78)
    P("§6f  可达包络内的余量 —— 不要用「差几格」冒充余量")
    P("-" * 78)
    r0_fat = [e for e in fatal if e["orient"] == "R0"]
    nearest = min((math.hypot(*e["t"]) for e in r0_fat), default=float("inf"))
    diag = math.hypot(TOL_X, TOL_Z)
    P(f"  定位公差盒 ±{TOL_X}/±{TOL_Z} ⇒ 最大位移 ‖Δ‖ = {diag:.3f} mm（对角）")
    P(f"  R0 下最近的**致命**姿态          ‖Δ‖ = {nearest:.3f} mm")
    P(f"  R0 下最近的 5V针↔KEY盘 直接接触  ‖Δ‖ = {r0_direct:.3f} mm")
    P(f"  ⇒ 逐轴余量 = {r0_direct/TOL_X:.2f}×；**最坏方向（对角）余量 = {nearest/diag:.2f}×**")
    P("  ⚠ 常见错误：拿「5V 盘与 KEY 盘相隔 2 格 = 5.08 mm」当余量。")
    P(f"    接触在中心距 ≤ r_contact = {r:.2f} mm 时就发生，故真实触发位移是")
    P(f"    2×{PITCH} − {r:.2f} = {2*PITCH-r:.3f} mm，不是 {2*PITCH:.2f} mm。差 {r/ (2*PITCH):.0%}。")
    if nearest > r0_direct + 1e-9:
        P(f"  ⇒ 在 ‖Δ‖ < {r0_direct:.3f} mm 的整个圆盘内，**没有任何 5V 针碰到任何 KEY 盘**，")
        P("    也没有任何多跳致命通路。因此该包络内的结论**不依赖**「分量里有地所以安全」")
        P("    这条推理，也就对 §「不覆盖」第 4 条的插入瞬态免疫。")

    # ---- §7 稠密交叉验证 ---------------------------------------------------
    if not args.no_dense:
        P("")
        P("-" * 78)
        P("§7  稠密交叉验证（R0，均匀步长 0.05 mm，‖Δ‖∞ ≤ 6 mm）—— 独立复验 §6c 有没有漏面")
        P("-" * 78)
        step, lim = 0.05, 6.0
        n = int(lim / step)
        best = None
        cnt = 0
        A = D4["R0"]
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                t = (i * step, j * step)
                hits, _, _, _ = evaluate(A, t, module_field, dock_field, r, False)
                cnt += 1
                if F_5V_TO_GPIO in hits:
                    d = math.hypot(*t)
                    if best is None or d < best[0]:
                        best = (d, t, sorted(set(hits[F_5V_TO_GPIO])))
        c6 = [e for e in fatal if e["orient"] == "R0"]
        c6min = min((math.hypot(*e["t"]) for e in c6), default=None)
        P(f"  扫了 {cnt} 个平移点")
        P(f"  稠密扫描最近致命：" + ("无" if best is None else
          f"‖Δ‖ = {best[0]:.3f} mm，Δ={best[1]}，{best[2][:2]}"))
        P(f"  圆排列穷举最近致命：" + ("无" if c6min is None else f"‖Δ‖ = {c6min:.3f} mm"))
        if (best is None) != (c6min is None):
            P("  两法对账：**不一致，须查** —— 一法有致命、另一法无")
        elif best is None:
            P("  两法对账：一致（都为空）")
        else:
            P("  两法对账：" + ("一致（圆排列 ≤ 稠密，符合预期）"
                                if c6min <= best[0] + 1e-6 else "**不一致，须查**"))

    # ---- 事件清单 ----------------------------------------------------------
    P("")
    P("=" * 78)
    P("会打坏主机的事件清单（判据 1：5 V 源低阻连通主机 GPIO，且该分量内无地）")
    P("=" * 78)
    if not fatal:
        P("  0 起。")
    else:
        fatal.sort(key=lambda e: (e["orient"] != "R0", math.hypot(*e["t"])))
        P(f"  共 {len(fatal)} 起（按「朝向 × 受害 GPIO 集合」去重，各取 ‖Δ‖ 最小代表）")
        P("")
        for i, e in enumerate(fatal):
            if i >= args.show and not args.verbose:
                P(f"  …… 其余 {len(fatal)-i} 起省略（--verbose 全打）")
                break
            P(f"  [{i+1}] {fmt_pose(e['orient'], e['t'])}  ‖Δ‖={math.hypot(*e['t']):.3f} mm  "
              f"开关{'按下' if e['pressed'] else '松开'}")
            P(f"       可达性：{reachable_tag(e['orient'], e['t'])}")
            P(f"       朝向：{D4_NOTE[e['orient']]}")
            for w in e["what"]:
                P(f"       碰上的两个网：{w}")
            for pk, qk in e["contacts"]:
                dn, mn = dock_field[pk], module_field[qk]
                if (dn == "DOCK_5V" and mn in KEY_TO_H2_GPIO) or \
                   (dn in KEY_TO_H2_GPIO and mn == "DOCK_5V"):
                    P(f"       关键接触：{describe_contact(pk, qk, dock_field, module_field)}")

    P("")
    P("-" * 78)
    P("判据 3（G04：GND → 5V_IN 方向 / 5V 与地同分量）")
    P("-" * 78)
    P(f"  R0 朝向下命中代表点 {g04['R0']} 个；8 个单步错位里 {n_g04_step} 个把主机 5V_IN 接到地。")
    P("  ⇒ ICD 第 3.3 节「X−1 列 …… 无损」必须降级为")
    P("    「后果取决于 AS-11（主机 5V_IN 与原生 USB VBUS 的内部拓扑），unknown，不得宣称无损」。")
    P("    **G04 成立。**")

    P("")
    P("-" * 78)
    P("判据 4（两根主机 GPIO 互相短接；非致命，但要报）")
    P("-" * 78)
    P(f"  R0 朝向下命中代表点 {shorts['R0']} 个。")
    P("  后果：主机把两根输入同时看成低电平 = 两个键同时被按住。无损，但会掩盖错位；")
    P("  可被固件用作「物理互斥键同时为低 ⇒ 未正确落座」的判据")
    P("  （只读不写、不参与供电决策，不违反不变量 ③）。")

    return fatal, g04, shorts

# =============================================================================
# §8  静态断言
# =============================================================================

def static_checks(module_field):
    fails, oks = [], []

    used = {KEY_TO_H2_GPIO[n][0] for n in module_field.values() if n in KEY_TO_H2_GPIO}
    if H2_5V_OUT in used:
        fails.append("判据 2：分配表把某个 KEY_* 落在了 H2 pin18（5V_OUT）")
    else:
        oks.append("判据 2：分配表未使用 H2 pin18（5V_OUT），也未把它引到 J2/J3")

    try:
        o = subprocess.run(["git", "-C", REPO, "show",
                            "claude/design-d/module-board:hardware/module-board/netlist.yaml"],
                           capture_output=True, text=True, timeout=30)
        if o.returncode == 0:
            h = re.findall(r"\[\s*J1\s*,\s*18\s*\]", o.stdout)
            if len(h) != 1:
                fails.append(f"判据 2b：module-board netlist.yaml 中 [J1, 18] 出现 {len(h)} 次，"
                             f"应恰好 1 次（孤立网）")
            else:
                oks.append("判据 2b：module-board 分支 netlist.yaml 中 [J1, 18] 恰好 1 次"
                           "（SLOT_5V_OUT_NC 孤立网，硬约束 2 成立）")
        else:
            oks.append("判据 2b 跳过（取不到 module-board 分支）")
    except Exception as ex:
        oks.append(f"判据 2b 跳过（{ex}）")

    bad = False
    for net in module_field.values():
        if net in KEY_TO_H2_GPIO:
            h2, gpio = KEY_TO_H2_GPIO[net]
            if h2 in FORBIDDEN_H2_PINS:
                fails.append(f"{net} 落在禁用 H2 针 {h2}（ICD 第 2 节）"); bad = True
            if gpio not in ALLOWED_GPIO:
                fails.append(f"{net} 的 GPIO{gpio} 不在仓库口径的 11 根可用集合内"); bad = True
    if not bad:
        oks.append("GPIO 集合：10 个 KEY_* 全在 ICD 第 2 节的 11 根可用 GPIO 内，"
                   "未碰 GPIO14（EEPROM A0）、未碰 H2 pin 13/15/18")

    cnt = defaultdict(int)
    for net in module_field.values():
        cnt[net] += 1
    nkey = sum(1 for n in module_field.values() if n in KEY_TO_H2_GPIO)
    oks.append(f"构成：5V×{cnt.get('DOCK_5V',0)} + GND×{cnt.get('DOCK_GND',0)} + 键×{nkey}"
               f" + I²C×{cnt.get('DOCK_SDA',0)+cnt.get('DOCK_SCL',0)} = {len(module_field)} 位")
    if nkey != 10:
        fails.append(f"只排下 {nkey} 个键，方案 J 要 10 个")

    try:
        o = subprocess.run(["git", "-C", REPO, "show",
                            "claude/design-d/dock-board:hardware/dock-board/netlist.yaml"],
                           capture_output=True, text=True, timeout=30)
        if o.returncode == 0:
            m = re.search(r"^j2_contract:\n((?:  \S.*\n)+)", o.stdout, re.M)
            keys = re.findall(r"^  ([AB]\d):", m.group(1), re.M) if m else []
            if keys:
                fails.append(
                    f"跨分支不一致：dock-board 分支 netlist.yaml 的 j2_contract 仍是旧 2×8 —— "
                    f"{len(keys)} 个 A1…B8 位号（{keys[:4]}…），**没有跟进 4 行×4 列**。"
                    f"底座针场与模块焊盘场的逐针合同现在对不上，其 check_netlist.py 的 CK-02"
                    f"（「J2 的 16 个针与 j2_contract 完全一致」）形同虚设。")
            else:
                oks.append("跨分支：dock-board j2_contract 已非 A1…B8 形式")
        else:
            oks.append("跨分支检查跳过（取不到 dock-board 分支）")
    except Exception as ex:
        oks.append(f"跨分支检查跳过（{ex}）")

    return oks, fails

# =============================================================================
# main
# =============================================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scheme", default="proposal", choices=sorted(SCHEMES))
    ap.add_argument("--tip", default=None, choices=sorted(TIP_CRITERIA))
    ap.add_argument("--show", type=int, default=10)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--no-dense", action="store_true")
    ap.add_argument("--all-schemes", action="store_true")
    args = ap.parse_args()

    out = []
    P = lambda *a: out.append(" ".join(str(x) for x in a))

    code = 0
    schemes = sorted(SCHEMES, reverse=True) if args.all_schemes else [args.scheme]
    tips = [args.tip] if args.tip else ["flat", "sharp"]

    summary = {}
    for sc in schemes:
        for tip in tips:
            fe, ge, se = run(sc, tip, args, P)
            summary[(sc, tip)] = fe
            if fe and sc == "proposal":
                code |= 1
            P("")

    P("=" * 78)
    P("§8  静态断言")
    P("=" * 78)
    for sc in schemes:
        oks, fails = static_checks(SCHEMES[sc])
        P(f"\n[{sc}]")
        for o in oks:
            P(f"  OK   {o}")
        for f in fails:
            P(f"  FAIL {f}")
        if fails and sc == "proposal":
            code |= 2

    P("")
    P("=" * 78)
    P("总表")
    P("=" * 78)
    P(f"{'方案':<12}{'针头':<8}{'致命总数':<12}{'R0 且公差内':<14}{'R0 全部':<10}")
    for (sc, tip), fe in sorted(summary.items()):
        r0 = [e for e in fe if e["orient"] == "R0"]
        r0tol = [e for e in r0 if abs(e["t"][0]) <= TOL_X and abs(e["t"][1]) <= TOL_Z]
        P(f"{sc:<12}{tip:<8}{len(fe):<12}{len(r0tol):<14}{len(r0):<10}")

    key = ("proposal", "flat")
    if key in summary:
        fe = summary[key]
        in_tol = [e for e in fe if e["orient"] == "R0"
                  and abs(e["t"][0]) <= TOL_X and abs(e["t"][1]) <= TOL_Z]
        r0 = [e for e in fe if e["orient"] == "R0"]
        rot = [e for e in fe if e["orient"] in ("R90", "R180", "R270")]
        mir = [e for e in fe if e["orient"] in ("MX", "MZ", "MD1", "MD2")]
        P("")
        P("可达性分层（proposal / flat 针头）：")
        P(f"  A 类 正确朝向 + 定位公差 ±0.45 内 ：{len(in_tol)} 起  ← 装配正确也会发生")
        P(f"  B 类 正确朝向 + 超公差错位       ：{len(r0)-len(in_tol)} 起  ← 需槽壁失效")
        P(f"  C 类 场绕自身中心转 90/180/270°  ：{len(rot)} 起  ← 靠 Mosaico 45.19×11.48 外形"
          f"与 AS-08 偏置阻挡，**不是触点场自己的防呆**")
        P(f"  D 类 镜像 / EDA 封装误放         ：{len(mir)} 起  ← 实物做不到，EDA 挡不住，"
          f"闸门只能是上电前导通检验")

    P("")
    P("=" * 78)
    P("本脚本**不**覆盖什么（不要当成已证明）")
    P("=" * 78)
    P("""  1. 这颗 SoC（BSP 里叫 esp32s31）的绝对最大额定与最大注入电流：仓库内无数据手册，
     unknown。本脚本只判「碰没碰上」「电位被谁决定」，不判「多少毫安才烧」。
  2. 主机 5V_IN 与原生 USB VBUS 的内部拓扑（AS-11，unknown）—— G04 的后果悬在这上面。
  3. 弹簧针针头形状未定（AS-31-mm-5 只定了 Ø0.9、行程、压力）。flat/sharp 两档都跑了，
     但「到底是哪一档」还没定 —— 这是必须补的选型约束。
  4. Y 向（插入深度）的**先后接触次序**：等长针无法保证先接地。本脚本是准静态的，
     只判「全部接触都已建立」的终态；插入过程中「5V 已接、地未接」的瞬态没建模。
     ICD 第 3.3 节该项仍开放。判据 1 的「有地即安全」结论对那段瞬态**不成立**。
  5. 焊接/布线错误造成的任意网置换（D4 只覆盖刚体错位与镜像，不覆盖 J3 单点错焊）。
  6. 时间尺度：U_LIM（TPS2553 恒流型，IOS 1215/1308/1415 mA）在 GPIO 钳位二极管被
     击穿前来不来得及动作，本脚本不建模。""")

    P("")
    P(f"退出码 {code}")
    print("\n".join(out))
    return code

if __name__ == "__main__":
    sys.exit(main())
