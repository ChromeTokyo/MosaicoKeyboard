#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enumerate_mismate_pogo_field.py —— 弹簧针触点场错位**穷举**判定

目的：关闭裁定里那条未关闭项（`DOCK_ROWS` 由 2 改 4 的电气后果），并关闭
Grok R0 的 G04（GND→5V_IN 方向论证不正确）与 G05（错位枚举不完整）。

本脚本不是「举例」，是**穷举**。穷举的完备性论证写在 §A 的 docstring 里，
并在运行时用一次独立的连续暴力扫描交叉验证（`--sweep`，默认开）。

纯 python3 标准库。有失败 → 非零退出码。

坐标与常数来源（全部自查，非转述）：
  * J2 列/行中心、触点面 Y：自己编译 claude/design-d/mech-module 的
    mechanical/module-board/module_board.scad 取 ECHO（2314 顶点 / 4768 面）。
    ⚠ 该文件行尾注释里的 DOCK_PIN_FIELD_X0 = −32.405 / Z0 = +2.95 是**过期值**，
    与 ECHO 差 2.0 / 0.2 mm。只信 ECHO。
  * DOCK_PAD_D / DOCK_PIN_TIP_D / DOCK_X_TOL / DOCK_Z_TOL / DOCK_PITCH /
    DOCK_COLS / DOCK_ROWS：module_board.scad 第 119–145 行。
  * KEY_* → H2 针号 → GPIO：module-board 分支 hardware/module-board/PINMAP.md 第 2 节。
  * H2 针号 → 主机网络：hardware/module-board/netlist.yaml 第 33–53 行 h2_contract
    （其上游为 review/chrome/D1-module-interface/LEFT_SLOT.md，BSP 392860b1）。
  * 底座侧行为（KEY_* 经轻触开关接 DOCK_GND、底座不给 KEY_*/SDA/SCL 任何上拉或电源、
    DOCK_5V 经限流与短路关断供出）：hardware/ICD-0.2-DRAFT.md 第 3.2 节末段、第 4 节硬约束 1/5/8。
  * pin 18 5V_OUT 焊盘不连铜：netlist.yaml 第 27 行、ICD EL-D-02。
  * pin 19 VCC_3V3 不跨 J3、不到 J2：netlist.yaml 第 28 行、ICD EL-D-03。
"""

import argparse
import itertools
import math
import sys
from collections import defaultdict

# =============================================================================
# §0  数据表 —— 换方案只需改这一节
# =============================================================================

# ---- 0.1 几何（module_board.scad 第 119–145 行 + ECHO 实测）----
PITCH = 2.54                      # DOCK_PITCH，scad:119
N_COLS = 4                        # DOCK_COLS，scad:120
N_ROWS = 4                        # DOCK_ROWS，scad:121
PAD_D = 2.0                       # DOCK_PAD_D，scad:123（AS-31-mb-3）
PIN_TIP_D = 0.9                   # DOCK_PIN_TIP_D，scad:129（AS-31-mm-5）
DOCK_X_TOL = 0.45                 # scad:144（AS-31-mm-6）
DOCK_Z_TOL = 0.45                 # scad:145（AS-31-mm-6）

# ECHO 原文：J2 列 1..4 中心 X = [-34.405, -31.865, -29.325, -26.785]
COL_X = [-34.405, -31.865, -29.325, -26.785]
# ECHO 原文：J2 行 A..D 中心 Z = [2.75, 0.21, -2.33, -4.87]（行 A 在 +Z 屏侧）
ROW_Z = [2.75, 0.21, -2.33, -4.87]
ROW_NAME = ["A", "B", "C", "D"]

R_TOUCH = (PAD_D + PIN_TIP_D) / 2.0   # 1.45 —— 针尖圆与焊盘圆「有任何接触」的中心距上限
R_FULL = (PAD_D - PIN_TIP_D) / 2.0    # 0.55 —— 针尖整体落在焊盘内（可靠接触）的中心距上限

# ---- 0.2 待检验的分配表（列, 行, 网名）；行用 0..3 = A..D ----
# 换方案只改这张表。
SCHEME_NAME = "可制造优先 4×4：5V×2 ＋ GND×4 ＋ 10 键（SDA/SCL 退出触点场）"
ASSIGN = {
    (0, 0): "KEY_L",     (1, 0): "KEY_R",     (2, 0): "KEY_B",     (3, 0): "KEY_A",
    (0, 1): "KEY_LEFT",  (1, 1): "KEY_RIGHT", (2, 1): "KEY_Y",     (3, 1): "KEY_X",
    (0, 2): "DOCK_GND",  (1, 2): "DOCK_GND",  (2, 2): "DOCK_GND",  (3, 2): "KEY_DOWN",
    (0, 3): "DOCK_5V",   (1, 3): "DOCK_5V",   (2, 3): "DOCK_GND",  (3, 3): "KEY_UP",
}

# ---- 0.3 对照方案：ICD 第 3.2 节现行 2 行 × 8 列（用于独立复算「现状构成」的说法）----
LEGACY_COLS, LEGACY_ROWS = 8, 2
LEGACY_ASSIGN = {
    (0, 0): "DOCK_5V",  (1, 0): "DOCK_GND", (2, 0): "KEY_UP",   (3, 0): "KEY_LEFT",
    (4, 0): "KEY_L",    (5, 0): "KEY_A",    (6, 0): "KEY_X",    (7, 0): "DOCK_SDA",
    (0, 1): "DOCK_5V",  (1, 1): "DOCK_GND", (2, 1): "KEY_DOWN", (3, 1): "KEY_RIGHT",
    (4, 1): "KEY_R",    (5, 1): "KEY_B",    (6, 1): "KEY_Y",    (7, 1): "DOCK_SCL",
}

# ---- 0.4 模块板侧：触点场网名 → (H2 针号, 主机节点, 节点类别) ----
# 类别：'gpio' = 主机 3.3 V 域 GPIO（被 5 V 碰到即打穿）
#       'vin'  = 主机 5V_IN（H2 pin 17，功率输入）
#       'gnd'  = 主机 GND
#       'none' = 模块板上不连铜，触点场上没有到主机的通路
# KEY_* → 针号/GPIO 取自 PINMAP.md 第 2 节；针号 → 主机网取自 netlist.yaml h2_contract。
MODULE_PAD_TO_HOST = {
    "DOCK_5V":   (17, "HOST_5V_IN", "vin"),
    "DOCK_GND":  (20, "HOST_GND",   "gnd"),
    "KEY_UP":    (1,  "GPIO55",     "gpio"),
    "KEY_A":     (2,  "GPIO53",     "gpio"),
    "KEY_DOWN":  (3,  "GPIO19",     "gpio"),
    "KEY_B":     (4,  "GPIO48",     "gpio"),
    "KEY_LEFT":  (5,  "GPIO18",     "gpio"),
    "KEY_X":     (6,  "GPIO13",     "gpio"),
    "KEY_RIGHT": (7,  "GPIO17",     "gpio"),
    "KEY_Y":     (8,  "GPIO12",     "gpio"),
    "KEY_L":     (9,  "GPIO16",     "gpio"),
    "KEY_R":     (11, "GPIO15",     "gpio"),
    # 2×8 对照方案才有；R_LINK 默认 DNP，故模块板上不通到主机。
    "DOCK_SDA":  (16, "GPIO0_SDA_DNP", "none"),
    "DOCK_SCL":  (14, "GPIO1_SCL_DNP", "none"),
}

# ---- 0.5 底座侧：触点场网名 → 底座节点 ----
# 'rail5v' = BOOST_5V 经限流/短路关断/防反灌供出（ICD 硬约束 1、8）
# 'gnd'    = 底座地
# 'sw'     = 轻触开关一端，另一端接底座地；默认开路（ICD 第 3.2 节末段）
DOCK_PIN_ROLE = {
    "DOCK_5V": "rail5v",
    "DOCK_GND": "gnd",
}
for _k in ("KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT", "KEY_L", "KEY_R",
           "KEY_A", "KEY_B", "KEY_X", "KEY_Y"):
    DOCK_PIN_ROLE[_k] = "sw"
DOCK_PIN_ROLE["DOCK_SDA"] = "float"   # 底座不放上拉、不接电源（硬约束 5、6）
DOCK_PIN_ROLE["DOCK_SCL"] = "float"

# ---- 0.6 结构性断言：这些 H2 针绝不允许出现在触点场 ----
FORBIDDEN_H2_PINS = {
    18: "5V_OUT，硬约束 2 / ICD EL-D-02：焊盘不连铜、绝不连接任何网络",
    19: "VCC_3V3，硬约束 3 / ICD EL-D-03：不跨 J3、不到 J2",
    10: "GPIO14 = EEPROM A0，PINMAP 第 1 节第 1 条：专用，不引到弹簧针",
    13: "GPIO33 / USJ_DN，PINMAP 第 3 节：焊盘不连铜",
    15: "GPIO34 / USJ_DP，PINMAP 第 3 节：焊盘不连铜",
}

# ---- 0.7 判定门槛 ----
SF_MIN_REQUIRED = 3.0   # 首次致损位移 ÷ 最坏定位偏差，低于此值判失败


# =============================================================================
# §A  穷举的完备性论证（这一段是本脚本的核心主张，不是注释里的客套话）
# =============================================================================
COMPLETENESS_PROOF = """
【为什么这是穷举而不是举例 —— 把连续错位空间约化成有限集】

错位自由度一共只有这几类，逐类处理：

(1) 平面内平移 (Δx, Δz) —— **连续**，本来是无穷的。约化方式：
    针尖圆 Ø0.9 与焊盘圆 Ø2.0 接触 ⇔ 中心距 ≤ R_TOUCH = 1.45。
    两个场都是同一个 2.54 mm 正交格，故任意 (针 i, 盘 j) 的标称偏置
    o_ij 必是格矢 (2.54a, 2.54b)。于是"某位移 Δ 下谁碰谁"完全由
    **Δ 落在哪些以格点为心、半径 1.45 的圆盘里**决定。
      - 相邻正交格点圆盘相交：2×1.45 = 2.90 > 2.54，重叠带宽 0.36 mm
        （半间距 1.27 处针尖到相邻焊盘边缘 −0.18 mm）→ 这就是"搭两个焊盘"的瞬态；
      - 对角格点圆盘不相交：2.54√2 = 3.592 > 2.90；
      - 三个圆盘不可能同时含一点：(0,0)(1,0)(0,1) 的等距点在 (1.27,1.27)，
        到三者距离 1.796 > 1.45。
    ⇒ 任意 Δ 的接触拓扑只可能是三种之一：**空集 / 恰好一个格点 / 恰好一对正交相邻格点**。
    ⇒ 完备代表元 = {无接触} ∪ {每个格点} ∪ {每对正交相邻格点的中点}。
       |a|,|b| ≥ 4 时场跨距 7.62 + 1.45 < 4×2.54，重叠恒为零，故格点取 [-4..4]²
       （取到 4 是为了**实测**边界而不是假设它）。
    这一步把"无穷"变成有限，且**没有丢任何一种接触组合**——G05 说的
    对角错位、错多列、部分接触，全部落在这个有限集内。

(2) 绕 Y 轴 180°（前后翻转放入）—— 1 例，作为独立几何变换 + 再叠加 (1) 的全部平移。
(3) 绕 X 轴 180°、绕 Z 轴 180°（上下颠倒）—— 各 1 例，触点面法向由 −Y 变 +Y。
(4) 绕 Y 轴小角偏摆（歪着落座）—— 连续，不能用格点约化，用角度扫描 + 平移扫描实算。
(5) 镜像误装 —— 不是几何变换（实体无法镜像），而是**网名映射的镜像**：
    槽板正反面弄反（AS-17 未关闭）、J3 双排 r0/r1 整体对调、EDA 顶视/底视搞混
    （本项目已有先例 D-009／D-009-R）。表现为列序反转 / 行序反转 / 两者都反。
    对每种镜像后的网名映射，再叠加 (1) 的全部平移。
(6) Y 向（插入深度）—— 只决定"接不接触"，不改变 (X,Z) 上谁碰谁的拓扑，不单独枚举。

穷举 = (1) 的有限代表元 × {(2)(3)(5) 的每种离散变换} ＋ (4) 的数值扫描。
运行时另有一遍独立的连续暴力扫描（§C-6）交叉验证 (1) 的约化没有漏掉任何接触签名。
"""


# =============================================================================
# §B  模型
# =============================================================================

def field_positions(n_cols, n_rows, col_x, row_z):
    return {(c, r): (col_x[c], row_z[r]) for c in range(n_cols) for r in range(n_rows)}


def net_of(assign, c, r):
    return assign[(c, r)]


def mirror_map(assign, n_cols, n_rows, flip_col, flip_row):
    """镜像误装：几何不动，网名映射按列序/行序反转。"""
    out = {}
    for (c, r), net in assign.items():
        cc = (n_cols - 1 - c) if flip_col else c
        rr = (n_rows - 1 - r) if flip_row else r
        out[(cc, rr)] = net
    return out


# ---- J3 接线置换群 ----------------------------------------------------------
# 分配表把 J2 的 16 个焊盘接到 J3 的「面 r0/r1」×「位 1..8」上：
#   列 1,2 ← 面 r1，列 3,4 ← 面 r0；行 D←位1,2  行 C←位3,4  行 B←位5,6  行 A←位7,8
# 于是几条**已被提案人自己点名**的接线翻转，各自对应一个置换：
#   * 「J3 面 r0/r1 整体对调」（提案人原话：走廊改开 −Z 侧就要这么做）
#       → 列 (1,2,3,4) → (3,4,1,2)  —— 是**成对交换**，不是整列反转
#   * 「J3 位 1..8 顺序反了」（槽板正反面弄反 / AS-17 翻转）
#       → 行 (A,B,C,D) → (D,C,B,A) 叠加对内交换
#   * 「同一面内两个位接反」→ 对内交换
# 这三种在列与行上各自生成一个克莱因四元群 {恒等, 对内交换, 成对交换, 整体反转}，
# 组合起来 4×4 = 16 种。全部枚举，不挑。
PERM4 = {
    "不变":       [0, 1, 2, 3],
    "对内交换":   [1, 0, 3, 2],
    "成对交换":   [2, 3, 0, 1],
    "整体反转":   [3, 2, 1, 0],
}


def permute_map(assign, cperm, rperm):
    """几何不动，只改「哪个网落在哪个焊盘」。"""
    return {(cperm[c], rperm[r]): net for (c, r), net in assign.items()}


# ---- 几何变换：把模块侧焊盘从标称位置映到底座坐标系 ----
def xf_identity(p):
    return p


def xf_rot180_y(p):
    """绕 Y 轴 180°：(x, y, z) → (−x, y, −z)。触点面法向仍为 −Y，仍朝下。"""
    x, z = p
    return (-x, -z)


GEOM_XFORMS = [
    ("正常朝向", xf_identity, True),
    ("绕 Y 轴 180°（前后翻转）", xf_rot180_y, True),
    ("绕 X 轴 180°", None, False),   # 触点面翻成朝 +Y，与朝 +Y 的针尖无法对触
    ("绕 Z 轴 180°（上下颠倒）", None, False),
]


def contacts(pin_pos, pad_pos, dx, dz, r_touch):
    """
    返回 [(pin_key, pad_key)]：位移 (dx,dz) 下所有针-盘接触对。

    ⚠ 这里**不能**直接用 ECHO 打印出的 COL_X/ROW_Z 列表做减法。
    实测：COL_X 的相邻差是 2.5400000000000027 / 2.539999999999999 / 2.539999999999999,
    彼此差 4e-15。圆盘边界上这点 ULP 噪声会把本应同时接通的 3 个针盘对拆成 1 个，
    制造出物理上不存在的「接触签名」（2026-09-22 实际踩到，暴力扫描多出 31 种假签名）。
    故一律用**整数格**做距离：同一格矢偏置的所有针盘对，其距离按位相同。
    COL_X/ROW_Z 只用于显示，并在 §D 开头断言其等距性。
    """
    out = []
    r2 = r_touch * r_touch
    for (pc, pr) in pin_pos:
        for (ac, ar) in pad_pos:
            ex = (ac - pc) * PITCH + dx
            ez = -(ar - pr) * PITCH + dz   # 行号增大 = Z 减小
            if ex * ex + ez * ez <= r2:
                out.append(((pc, pr), (ac, ar)))
    return out


def contacts_xy(pin_pos, pad_pos, dx, dz, r_touch):
    """任意（非格点）坐标下的接触判定；只用于绕 Y 180° 与偏摆这两种非格点情形。"""
    out = []
    r2 = r_touch * r_touch
    for pk, (px, pz) in pin_pos.items():
        for dk, (ax, az) in pad_pos.items():
            ex, ez = ax + dx - px, az + dz - pz
            if ex * ex + ez * ez <= r2:
                out.append((pk, dk))
    return out


class Union:
    def __init__(self):
        self.p = {}

    def find(self, a):
        self.p.setdefault(a, a)
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def judge(cts, assign_pins, assign_pads, keys_pressed):
    """
    对一组接触做判定。返回 [(等级, 文本)]。

      D1  **有损**：5 V 源出现在主机 GPIO 上，且该节点**没有**被任何地钳位
                    → 确定性打穿主机 3.3 V 域。这是本脚本的红线。
      D1T 有损（瞬态存疑）：5 V 源与主机 GPIO 同节点，但该节点同时被地钳位。
                    稳态下电位被拉到地（GPIO 只是被"按下"），
                    但滑动过程中各针盘对的**接触先后不受控**
                    （ICD 3.3 明文：「等长弹簧针无法保证 GND 先于 5V 接触」），
                    故不能判"无损"，单列一级。
      D2  可疑（G04）：主机 5V_IN 与主机 GND 之间形成外部通路（回路闭合）
      D3  良性短路：底座 5 V → 主机 GND / 底座 GND（由底座限流与短路关断吸收，硬约束 1、8）
      D4  功能错误：键位错、键被拉低、两 GPIO 互连

    ⚠ 分级的关键修正（2026-09-22）：**不能**用朴素连通性判 D1。
      弹簧针即使开关断开，针体本身仍会把它同时压住的两个焊盘短接；
      于是"底座地针搭到 5V 焊盘"会经由一串 KEY 针的桥接把一堆 GPIO
      拉进同一个连通块。那个连通块整体被钳到地，**没有任何 5 V 注入**，
      把它记成 D1 是假阳性（第一版脚本就是这么错的）。
    """
    ev = []

    # --- 判据 2（结构性）：5V_OUT 绝不可被连接 ---
    # 结构上 pin 18 就不在触点场里，这里再断言一次（数据表被改坏时会炸）。
    for net in set(assign_pads.values()) | set(assign_pins.values()):
        h2 = MODULE_PAD_TO_HOST.get(net, (None,))[0]
        if h2 in FORBIDDEN_H2_PINS:
            ev.append(("D1", "结构违规：触点场上出现 H2 pin %d（%s），网名 %s"
                       % (h2, FORBIDDEN_H2_PINS[h2], net)))

    # --- 建立"底座节点"：同网的针天然同电位；按下的键把该针并到底座地 ---
    def dock_node(pin_key):
        net = assign_pins[pin_key]
        role = DOCK_PIN_ROLE[net]
        if role == "rail5v":
            return "D_5V_RAIL"
        if role == "gnd":
            return "D_GND"
        if role == "sw":
            return "D_GND" if keys_pressed else ("D_SW_%s@%s" % (net, pin_key))
        return "D_FLOAT@%s" % (pin_key,)

    # --- 判据 1：底座 5 V 针**直接**压在通向主机 GPIO 的焊盘上 ---
    # 不走连通性，走直接接触：滑动过程中接触是**逐个先后**发生的，
    # 底座 5 V 轨即使同时被别处短到地，短路关断也有有限响应时间（阈值 unknown，
    # ICD 第 3.3 节三级：「限流不等于允许反向电压」）。故直接接触一律判 D1。
    for pk, dk in cts:
        if DOCK_PIN_ROLE[assign_pins[pk]] != "rail5v":
            continue
        pad_net = assign_pads[dk]
        h2, host, kind = MODULE_PAD_TO_HOST[pad_net]
        if kind == "gpio":
            ev.append(("D1", "底座 5V 针 %s → 模块焊盘 %s(%s) → H2 pin%d = %s"
                       % (fmt_key(pk), fmt_key(dk), pad_net, h2, host)))
        elif kind == "gnd":
            ev.append(("D3", "底座 5V 针 %s → 模块焊盘 %s(DOCK_GND) → 主机 GND："
                            "5V–GND 短路，由底座限流/短路关断吸收" % (fmt_key(pk), fmt_key(dk))))

    # --- 主机侧连通性：每个底座节点把它压到的所有焊盘短在一起 ---
    u = Union()
    by_node = defaultdict(set)
    for pk, dk in cts:
        by_node[dock_node(pk)].add(dk)
    for node, pads in by_node.items():
        pads = sorted(pads)
        for a in pads[1:]:
            u.union(("pad", pads[0]), ("pad", a))
        u.union(("node", node), ("pad", pads[0]))

    def host_group(kind_filter):
        g = defaultdict(list)
        for dk, net in assign_pads.items():
            h2, host, kind = MODULE_PAD_TO_HOST[net]
            if kind in kind_filter and ("pad", dk) in u.p:
                g[u.find(("pad", dk))].append((dk, net, host, kind))
        return g

    grp = host_group({"gpio", "vin", "gnd"})

    # 每个连通块里有哪些底座节点
    nodes_in = defaultdict(set)
    for node in by_node:
        nodes_in[u.find(("node", node))].add(node)

    for root, members in grp.items():
        kinds = {m[3] for m in members}
        dnodes = nodes_in.get(root, set())
        has_d5v = "D_5V_RAIL" in dnodes
        has_dgnd = "D_GND" in dnodes
        # 该连通块里有没有 5 V 源？底座升压轨，或主机自己的 5V_IN 轨
        #（主机经原生 USB 供电时 5V_IN 是否带电 = AS-11，unknown，保守按带电算）
        src5v = []
        if has_d5v:
            src5v.append("底座 BOOST_5V 轨")
        if "vin" in kinds:
            src5v.append("主机 5V_IN(H2 pin17)")
        # 该连通块里有没有把电位钳到 0 的地？
        clamps = []
        if has_dgnd:
            clamps.append("底座地")
        if "gnd" in kinds:
            clamps.append("主机 GND(H2 pin20)")

        gp = sorted({m[2] for m in members if m[3] == "gpio"})
        gp_where = "、".join("%s(%s)" % (m[2], fmt_key(m[0]))
                             for m in sorted(members, key=lambda t: t[0]) if m[3] == "gpio")

        if gp and src5v:
            if not clamps:
                ev.append(("D1", "【无地钳位】%s 与主机 GPIO %s 同节点 → 5 V 直灌 3.3 V 域"
                           % ("＋".join(src5v), gp_where)))
            else:
                ev.append(("D1T", "【有地钳位·瞬态存疑】%s 与主机 GPIO %s 同节点，"
                                  "同节点还含 %s（稳态被拉到地；接触先后不受控）"
                           % ("＋".join(src5v), gp_where, "＋".join(clamps))))

        # --- 判据 3 / G04：主机 5V_IN ↔ 主机 GND 外部回路闭合 ---
        if "vin" in kinds and ("gnd" in kinds or has_dgnd):
            ev.append(("D2", "主机 5V_IN(pin17) 经底座接到 %s → 外部短路回路闭合"
                             "（G04 方向；后果取决于主机 5V_IN 输入保护，AS-11/AS-33 unknown）"
                       % "＋".join(clamps)))

        # --- 判据 4：两根主机 GPIO 互相短接 ---
        if len(gp) >= 2:
            ev.append(("D4", "主机 GPIO 互连：%s（经底座同一节点）" % "、".join(gp)))
        if gp and clamps:
            ev.append(("D4", "主机 GPIO %s 被拉到 %s（等效按键按下）" % ("、".join(gp), "＋".join(clamps))))

    # 去重，保序
    seen, out = set(), []
    for e in ev:
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out


def fmt_key(k):
    c, r = k
    return "列%d行%s" % (c + 1, ROW_NAME[r] if r < len(ROW_NAME) else str(r))


# =============================================================================
# §C  枚举
# =============================================================================

def lattice_reps(n_cols, n_rows, lat_max):
    """§A(1) 的完备代表元：格点 + 正交相邻格点对的中点。"""
    reps = []
    rng = range(-lat_max, lat_max + 1)
    for a in rng:
        for b in rng:
            reps.append(("格点 Δx=%+d·p Δz=%+d·p" % (a, b), a * PITCH, b * PITCH))
    for a in rng:
        for b in rng:
            if a + 1 in rng:
                reps.append(("桥接X Δx=%+.2f Δz=%+d·p" % (a * PITCH + PITCH / 2, b),
                             a * PITCH + PITCH / 2, b * PITCH))
            if b + 1 in rng:
                reps.append(("桥接Z Δx=%+d·p Δz=%+.2f" % (a, b * PITCH + PITCH / 2),
                             a * PITCH, b * PITCH + PITCH / 2))
    reps.append(("对角半格 Δ=(+1.27,+1.27) 无接触对照", PITCH / 2, PITCH / 2))
    return reps


def run_case(tag, pin_pos, pad_pos, assign_pins, assign_pads, reps, keys_pressed):
    """跑一组代表元，返回所有事件。"""
    found = []
    for name, dx, dz in reps:
        cts = contacts(pin_pos, pad_pos, dx, dz, R_TOUCH)
        if not cts:
            continue
        ev = judge(cts, assign_pins, assign_pads, keys_pressed)
        for lvl, txt in ev:
            found.append((lvl, tag, name, dx, dz, txt, len(cts)))
    return found


def min_damage_displacement(pin_pos, pad_pos, assign_pins, assign_pads):
    """
    解析求「首次致损（D1 直接注入）所需的最小位移」。
    致损位移集合 = ∪ 以 o_ij 为心、半径 R_TOUCH 的圆盘，
    其中 i 遍历底座 5V 针、j 遍历通向主机 GPIO 的焊盘。
    故最小 ‖Δ‖ = min(‖o_ij‖) − R_TOUCH。
    """
    best = None
    for pk, (px, pz) in pin_pos.items():
        if DOCK_PIN_ROLE[assign_pins[pk]] != "rail5v":
            continue
        for dk, (ax, az) in pad_pos.items():
            if MODULE_PAD_TO_HOST[assign_pads[dk]][2] != "gpio":
                continue
            ox, oz = px - ax, pz - az
            d = math.hypot(ox, oz)
            cand = (d - R_TOUCH, d, pk, dk, ox, oz)
            if best is None or cand[0] < best[0]:
                best = cand
    return best


def min_damage_axis(pin_pos, pad_pos, assign_pins, assign_pads, axis):
    """纯 X（或纯 Z）方向的首次致损门槛。"""
    best = None
    for pk, (px, pz) in pin_pos.items():
        if DOCK_PIN_ROLE[assign_pins[pk]] != "rail5v":
            continue
        for dk, (ax, az) in pad_pos.items():
            if MODULE_PAD_TO_HOST[assign_pads[dk]][2] != "gpio":
                continue
            ox, oz = px - ax, pz - az
            off, perp = (ox, oz) if axis == "X" else (oz, ox)
            if abs(perp) > R_TOUCH:
                continue
            need = abs(off) - math.sqrt(max(0.0, R_TOUCH ** 2 - perp ** 2))
            cand = (need, pk, dk)
            if best is None or cand[0] < best[0]:
                best = cand
    return best


def yaw_scan(pin_pos, pad_pos, assign_pins, assign_pads, thetas, tr_max, step):
    """绕 Y 轴小角偏摆 + 平移：求每个角度下首次 D1 所需的最小平移量。"""
    cx = sum(p[0] for p in pad_pos.values()) / len(pad_pos)
    cz = sum(p[1] for p in pad_pos.values()) / len(pad_pos)
    gpio_pads = [k for k in pad_pos if MODULE_PAD_TO_HOST[assign_pads[k]][2] == "gpio"]
    v5_pins = [k for k in pin_pos if DOCK_PIN_ROLE[assign_pins[k]] == "rail5v"]
    out = []
    for th in thetas:
        t = math.radians(th)
        ct, st = math.cos(t), math.sin(t)
        rot = {}
        for k in gpio_pads:
            x, z = pad_pos[k]
            x -= cx
            z -= cz
            rot[k] = (cx + x * ct - z * st, cz + x * st + z * ct)
        best = None
        n = int(tr_max / step)
        for i in range(-n, n + 1):
            dx = i * step
            for j in range(-n, n + 1):
                dz = j * step
                hit = False
                for pk in v5_pins:
                    px, pz = pin_pos[pk]
                    for dk in gpio_pads:
                        ax, az = rot[dk]
                        if (ax + dx - px) ** 2 + (az + dz - pz) ** 2 <= R_TOUCH ** 2:
                            hit = True
                            break
                    if hit:
                        break
                if hit:
                    m = math.hypot(dx, dz)
                    if best is None or m < best:
                        best = m
        out.append((th, best))
    return out


def brute_sweep(pin_pos, pad_pos, lo, hi, step):
    """独立暴力扫描：收集所有出现过的接触签名，用来交叉验证 §A(1) 的有限约化。
    同样走整数格距离（见 contacts() 里那段 ULP 说明）。"""
    sigs = set()
    n_lo = int(round(lo / step))
    n_hi = int(round(hi / step))
    pins = list(pin_pos)
    pads = list(pad_pos)
    r2 = R_TOUCH ** 2
    for i in range(n_lo, n_hi + 1):
        dx = i * step
        for j in range(n_lo, n_hi + 1):
            dz = j * step
            sig = []
            for (pc, pr) in pins:
                for (ac, ar) in pads:
                    ex = (ac - pc) * PITCH + dx
                    ez = -(ar - pr) * PITCH + dz
                    if ex * ex + ez * ez <= r2:
                        sig.append(((pc, pr), (ac, ar)))
            if sig:
                sigs.add(tuple(sorted(sig)))
    return sigs


def combinatorics(n_cols, n_rows, n5, ngnd):
    """
    独立复算「某构成下，有几种排法能做到任意切比雪夫距离 1 的格点错位都不致损」。
    不致损判据：每个 5V 焊位的 8 邻域（场内部分）全是功率位（5V 或 GND）。
    注：把不可区分的同网焊盘当不可区分（否则会重复计数）。
    """
    cells = [(c, r) for c in range(n_cols) for r in range(n_rows)]
    total = 0
    good = 0
    good_sets = []
    for v5 in itertools.combinations(cells, n5):
        rest = [c for c in cells if c not in v5]
        for gn in itertools.combinations(rest, ngnd):
            total += 1
            power = set(v5) | set(gn)
            ok = True
            for (c, r) in v5:
                for dc in (-1, 0, 1):
                    for dr in (-1, 0, 1):
                        if dc == 0 and dr == 0:
                            continue
                        nb = (c + dc, r + dr)
                        if nb in cells and nb not in power:
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    break
            if ok:
                good += 1
                good_sets.append((v5, gn))
    return total, good, good_sets


# =============================================================================
# §D  主程序
# =============================================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat-max", type=int, default=4,
                    help="格点错位枚举范围 ±N（默认 4，取到 4 是为了实测重叠归零）")
    ap.add_argument("--sweep-step", type=float, default=0.025, help="暴力扫描步长 mm")
    ap.add_argument("--no-sweep", action="store_true")
    ap.add_argument("--no-combo", action="store_true")
    args = ap.parse_args()

    fail = []
    P = print

    P("=" * 78)
    P("弹簧针触点场错位穷举判定")
    P("方案：%s" % SCHEME_NAME)
    P("=" * 78)
    P(COMPLETENESS_PROOF)

    P("【几何常数】（module_board.scad:119–145 ＋ 自编译 ECHO）")
    P("  DOCK_PITCH=%.2f  DOCK_COLS=%d  DOCK_ROWS=%d" % (PITCH, N_COLS, N_ROWS))
    P("  DOCK_PAD_D=%.2f  DOCK_PIN_TIP_D=%.2f  →  接触半径 R_TOUCH=%.3f  可靠接触 R_FULL=%.3f"
      % (PAD_D, PIN_TIP_D, R_TOUCH, R_FULL))
    P("  DOCK_X_TOL=%.2f  DOCK_Z_TOL=%.2f  →  最坏合成偏差 ‖(0.45,0.45)‖=%.4f mm"
      % (DOCK_X_TOL, DOCK_Z_TOL, math.hypot(DOCK_X_TOL, DOCK_Z_TOL)))
    P("  ⚠ 焊盘直径跨文件不一致：module_board.scad:123 DOCK_PAD_D = 2.0，")
    P("    而 module-board 分支 netlist.yaml 的 AS-31-mb-3 与 PINMAP 4.4 仍写 Ø1.8。")
    P("    本脚本取 2.0（较大 → R_TOUCH 较大 → 致损门槛较低 → 偏保守）。")
    P("    取 1.8 时 R_TOUCH=%.3f，门槛会放宽到 %.3f mm。这条不一致须由 module-board 关闭。"
      % ((1.8 + PIN_TIP_D) / 2, 5.08 - (1.8 + PIN_TIP_D) / 2))
    P("  列中心 X = %s" % COL_X)
    P("  行中心 Z = %s（行 A 在 +Z 屏侧）" % ROW_Z)
    P("")

    pin_pos = field_positions(N_COLS, N_ROWS, COL_X, ROW_Z)
    pad_pos = dict(pin_pos)   # 标称同位
    assign_pins = dict(ASSIGN)
    assign_pads = dict(ASSIGN)

    P("【分配表】（俯视：+Y 向 −Y 看、+X 向右；ICD 4.1 注明此时屏幕方向是 −Z）")
    for r in range(N_ROWS):
        P("  行%s | " % ROW_NAME[r] + " | ".join("%-9s" % ASSIGN[(c, r)] for c in range(N_COLS)))
    P("")

    # ---- 结构性断言 ----
    P("【判据 2】5V_OUT(H2 pin18) 及其它禁入针不得出现在触点场")
    bad = False
    for k, net in ASSIGN.items():
        h2 = MODULE_PAD_TO_HOST[net][0]
        if h2 in FORBIDDEN_H2_PINS:
            P("  ✗ %s = %s → H2 pin%d（%s）" % (fmt_key(k), net, h2, FORBIDDEN_H2_PINS[h2]))
            bad = True
    if bad:
        fail.append("判据 2：触点场上出现禁入 H2 针")
    else:
        P("  ✓ 触点场 16 位用到的 H2 针 = %s，与禁入集合 %s 无交集"
          % (sorted({MODULE_PAD_TO_HOST[n][0] for n in ASSIGN.values()}),
             sorted(FORBIDDEN_H2_PINS)))
        P("  ✓ 几何上也够不着：pin 18 的焊盘在**槽板**上（ECHO：槽板 X[-27.735,-26.135]")
        P("    Y[-22.495,18.5]），弹簧针只压到**触点板底面** Y=-24.095。两者不在同一面，")
        P("    且 pin 18 焊盘不连铜（netlist.yaml:27 / ICD EL-D-02）。判据 2 在任何错位下恒成立。")
    P("")

    reps = lattice_reps(N_COLS, N_ROWS, args.lat_max)
    P("【枚举规模】格点 %d 例 ＋ 桥接中点 %d 例 ＋ 对角半格 1 例 = %d 个完备代表元"
      % ((2 * args.lat_max + 1) ** 2,
         len(reps) - (2 * args.lat_max + 1) ** 2 - 1, len(reps)))
    P("  （其中 |Δ列|≥2 的多列错位、Δ列≠0 且 Δ行≠0 的对角错位、半格桥接，全部在内 —— 这就是 G05 要的）")
    P("")

    # ---- C-1 正常朝向、键未按下 ----
    all_events = []
    P("=" * 78)
    P("§1  正常朝向 × 全平移空间 × 底座按键**未按下**")
    P("=" * 78)
    ev = run_case("正常朝向/键松开", pin_pos, pad_pos, assign_pins, assign_pads, reps, False)
    all_events += ev
    report_bucket(ev, P)

    # ---- C-2 正常朝向、键按下（最坏）----
    P("")
    P("=" * 78)
    P("§2  正常朝向 × 全平移空间 × 底座按键**全部按下**（最坏；按下使 KEY 针 = 底座地，")
    P("    只会增加边不会减少边，故两端极值夹住全部中间组合）")
    P("=" * 78)
    ev2 = run_case("正常朝向/键按下", pin_pos, pad_pos, assign_pins, assign_pads, reps, True)
    all_events += ev2
    report_bucket(ev2, P)

    # ---- C-3 镜像误装 ----
    P("")
    P("=" * 78)
    P("§3  镜像误装（AS-17 未关闭 / J3 双排 r0-r1 对调 / EDA 顶视底视搞混，")
    P("    本项目已有先例 D-009、D-009-R）× 全平移空间")
    P("=" * 78)
    mirror_events = []
    P("  枚举 J3 接线置换群：列 4 种 × 行 4 种 = 16 种（含恒等），逐一叠加全平移空间。")
    P("  「成对交换」就是提案人自己写的「J3 面 r0/r1 整体对调」；")
    P("  「整体反转」对应槽板正反面弄反（AS-17，PINMAP 第 7 节 P1 明写「此项在打板前完成」）。")
    P("")
    P("  列置换   行置换   Δ=(0,0) 处 D1 条数   首个致损对")
    P("  " + "-" * 82)
    zero_fail = []
    for cname, cperm in PERM4.items():
        for rname, rperm in PERM4.items():
            mp = permute_map(ASSIGN, cperm, rperm)
            z = judge(contacts(pin_pos, pad_pos, 0.0, 0.0, R_TOUCH),
                      assign_pins, mp, False)
            zd1 = sorted({x[1] for x in z if x[0] == "D1"})
            first = zd1[0][:46] if zd1 else "—"
            mark = "‼" if zd1 else "✓"
            P("  %s %-8s %-8s %3d                 %s" % (mark, cname, rname, len(zd1), first))
            if zd1 and not (cname == "不变" and rname == "不变"):
                zero_fail.append("J3 接线置换（列:%s / 行:%s）" % (cname, rname))
            e = run_case("置换 列:%s 行:%s" % (cname, rname),
                         pin_pos, pad_pos, assign_pins, mp, reps, False)
            mirror_events += e
    P("")
    if zero_fail:
        P("  ⇒ 16 种接线置换里，**%d 种在完全对正（Δ=0）时就把 5 V 直接压在主机 GPIO 上**。"
          % len(zero_fail))
        P("    这类错误不是「错位」，是接线／板面搞反，一级机械防呆对它**完全无效**，")
        P("    8.07×（或 5.70×）的定位裕度也对它完全无效。")
        for f in zero_fail:
            fail.append(f + " 在 Δ=(0,0) 即打坏主机")
    else:
        P("  ⇒ 16 种接线置换在 Δ=0 时均无 D1。")
    all_events += mirror_events

    # ---- C-4 绕轴 180° ----
    P("")
    P("=" * 78)
    P("§4  整体旋转 180°")
    P("=" * 78)
    rot_pad = {k: xf_rot180_y(v) for k, v in pad_pos.items()}
    cx_pin = sum(p[0] for p in pin_pos.values()) / 16.0
    cz_pin = sum(p[1] for p in pin_pos.values()) / 16.0
    cx_rot = sum(p[0] for p in rot_pad.values()) / 16.0
    cz_rot = sum(p[1] for p in rot_pad.values()) / 16.0
    need = math.hypot(cx_pin - cx_rot, cz_pin - cz_rot)
    P("  绕 Y 轴 180°：触点场映到 X ∈ [%.3f, %.3f]，Z ∈ [%.3f, %.3f]（+X 握把侧）"
      % (min(p[0] for p in rot_pad.values()), max(p[0] for p in rot_pad.values()),
         min(p[1] for p in rot_pad.values()), max(p[1] for p in rot_pad.values())))
    P("     底座针场在 X ∈ [%.3f, %.3f]；两场心距 %.3f mm。"
      % (min(p[0] for p in pin_pos.values()), max(p[0] for p in pin_pos.values()), need))
    ev_rot = []
    for _nm, _dx, _dz in reps:
        _c = contacts_xy(pin_pos, rot_pad, _dx, _dz, R_TOUCH)
        if _c:
            for _lv, _tx in judge(_c, assign_pins, assign_pads, True):
                ev_rot.append((_lv, "绕Y180°", _nm, _dx, _dz, _tx, len(_c)))
    P("     在 ±%d 格（±%.2f mm）的全平移枚举内，接触对总数 = %d"
      % (args.lat_max, args.lat_max * PITCH,
         sum(1 for _ in ev_rot)))
    # 直接算需要多大平移才可能首次接触
    dmin = min(math.hypot(rot_pad[dk][0] - pin_pos[pk][0], rot_pad[dk][1] - pin_pos[pk][1])
               for pk in pin_pos for dk in rot_pad)
    P("     首次出现**任何**接触所需的最小平移 = %.3f mm（= 最近针盘对距 %.3f − R_TOUCH %.3f）"
      % (dmin - R_TOUCH, dmin, R_TOUCH))
    P("     对比定位公差 0.45 mm，倍数 = %.0f×；对比整机尺寸 45.19 mm，也远超落入槽行程。"
      % ((dmin - R_TOUCH) / DOCK_X_TOL))
    P("     ✓ 与 ECHO [检查 8] 一致。注：ICD 3.3 原文「若一级失效，5V 针会落到列 8 SDA/SCL")
    P("       焊盘，有损」这句**在 4×4 下已作废**——它依赖 2×8 的场宽 17.78 mm，")
    P("       4×4 场宽只有 %.2f mm，绕 Y 180° 后两场在 X 上根本不重叠。" % ((N_COLS - 1) * PITCH))
    all_events += ev_rot
    P("")
    P("  绕 X 轴 180° / 绕 Z 轴 180°：触点面法向由 −Y 变为 +Y（焊盘朝上），")
    P("     而弹簧针针尖也朝 +Y。两个朝同向的面无法对触，接触对恒为 0。")
    P("     这是 Y 轴上的事实，与 (X,Z) 错位无关，故不进平移枚举。")

    # ---- C-5 偏摆 ----
    P("")
    P("=" * 78)
    P("§5  绕 Y 轴小角偏摆（歪着落座）＋ 平移 —— 这一条前面所有分析都没做过")
    P("=" * 78)
    ys = yaw_scan(pin_pos, pad_pos, assign_pins, assign_pads,
                  [0, 2, 5, 10, 15, 20, 30, 45], 6.0, 0.1)
    P("  θ(°) | 首次 D1 所需的最小平移 ‖Δ‖ (mm)")
    for th, m in ys:
        P("  %5.1f | %s" % (th, ("%.3f" % m) if m is not None else "> 6.0（枚举上界内不致损）"))
    P("  说明：θ 由落入槽的滑配间隙限制。槽板 Z 向宽 10.8 mm、单边滑配 0.15 mm（scad:139–143）")
    P("        ⇒ 几何可达 θ ≈ atan(2×0.15 / 10.8) = %.2f°。该角度下仍需 ≥ %.2f mm 平移才致损。"
      % (math.degrees(math.atan2(0.30, 10.8)), ys[0][1] if ys[0][1] else 0.0))

    # ---- C-6 暴力扫描交叉验证 ----
    if not args.no_sweep:
        P("")
        P("=" * 78)
        P("§6  独立暴力扫描：交叉验证 §A(1) 的有限约化没有漏掉任何接触组合")
        P("=" * 78)
        sw = brute_sweep(pin_pos, pad_pos, -9.0, 9.0, args.sweep_step)
        an = set()
        for _, dx, dz in reps:
            c = contacts(pin_pos, pad_pos, dx, dz, R_TOUCH)
            if c:
                an.add(tuple(sorted(c)))
        P("  扫描范围 Δx,Δz ∈ [−9, +9]，步长 %.3f mm，共 %d 个采样点"
          % (args.sweep_step, (int(18.0 / args.sweep_step) + 1) ** 2))
        P("  暴力扫描出现的不同接触签名：%d 种" % len(sw))
        P("  §A(1) 有限代表元给出的接触签名：%d 种" % len(an))
        missing = sw - an
        if missing:
            P("  ✗ 暴力扫描发现 %d 种代表元没覆盖的接触组合 —— 约化论证有漏" % len(missing))
            fail.append("§A(1) 的有限约化不完备：暴力扫描找到 %d 种未覆盖签名" % len(missing))
            for m in list(missing)[:3]:
                P("     漏例：%s" % (m,))
        else:
            P("  ✓ 暴力扫描没有发现任何代表元未覆盖的接触组合 → 约化成立，枚举是穷举的")
            P("    （代表元多出的 %d 种是扫描步长落不到的边界签名，方向对安全有利）"
              % (len(an) - len(sw)))

    # ---- C-7 致损门槛 ----
    P("")
    P("=" * 78)
    P("§7  连续位移下的致损门槛（判据 1）")
    P("=" * 78)
    b = min_damage_displacement(pin_pos, pad_pos, assign_pins, assign_pads)
    if b is None:
        P("  本方案在任何位移下都不存在「底座 5V 针 → 主机 GPIO」的针盘对 —— 不可能")
        fail.append("求解异常：找不到任何 5V→GPIO 针盘对")
    else:
        thr, d, pk, dk, ox, oz = b
        P("  最近的一对「底座 5V 针 → 主机 GPIO 焊盘」：")
        P("    底座针 %s (%s) → 模块焊盘 %s (%s → H2 pin%d → %s)"
          % (fmt_key(pk), assign_pins[pk], fmt_key(dk), assign_pads[dk],
             MODULE_PAD_TO_HOST[assign_pads[dk]][0], MODULE_PAD_TO_HOST[assign_pads[dk]][1]))
        P("    标称偏置 = (%.3f, %.3f) mm，模 %.3f mm" % (ox, oz, d))
        P("  ⇒ 首次致损所需的**最小欧氏位移** = %.3f − %.3f = **%.3f mm**" % (d, R_TOUCH, thr))
        bx = min_damage_axis(pin_pos, pad_pos, assign_pins, assign_pads, "X")
        bz = min_damage_axis(pin_pos, pad_pos, assign_pins, assign_pads, "Z")
        P("    纯 X 方向门槛 = %.3f mm（%s → %s）" % (bx[0], fmt_key(bx[1]), fmt_key(bx[2])))
        P("    纯 Z 方向门槛 = %.3f mm（%s → %s）" % (bz[0], fmt_key(bz[1]), fmt_key(bz[2])))
        worst = math.hypot(DOCK_X_TOL, DOCK_Z_TOL)
        sf_axis = thr / DOCK_X_TOL
        sf_vec = thr / worst
        P("  安全系数：")
        P("    对单轴公差 0.45 mm      → %.2f×" % sf_axis)
        P("    对最坏合成偏差 %.4f mm → **%.2f×**（X、Z 公差各 ±0.45 可同时取最坏，"
          % (worst, sf_vec))
        P("       故这个才是该引用的数；按单轴报 %.2f× 是高估）" % sf_axis)
        if sf_vec < SF_MIN_REQUIRED:
            fail.append("安全系数 %.2f× < 门槛 %.1f×" % (sf_vec, SF_MIN_REQUIRED))
        else:
            P("    ✓ ≥ 门槛 %.1f×" % SF_MIN_REQUIRED)

    # ---- C-8 切比雪夫距离 1 ----
    P("")
    P("=" * 78)
    P("§8  切比雪夫距离 = 1 的 8 例（含 4 个对角）逐例 —— 设计目标就是这 8 例全不致损")
    P("    （Δz>0 = 模块焊盘场相对针场向 +Z 即屏侧移动 = 朝行 A 方向；p = 2.54 mm）")
    P("=" * 78)
    ok8 = True
    for a in (-1, 0, 1):
        for bb in (-1, 0, 1):
            if a == 0 and bb == 0:
                continue
            cts = contacts(pin_pos, pad_pos, a * PITCH, bb * PITCH, R_TOUCH)
            e = judge(cts, assign_pins, assign_pads, False)
            e2 = judge(cts, assign_pins, assign_pads, True)
            def worst(evs):
                lv = set(x[0] for x in evs)
                for k in ("D1", "D1T", "D2", "D3", "D4"):
                    if k in lv:
                        return k
                return "—"
            w1, w2 = worst(e), worst(e2)
            note = "；".join(sorted({x[1][:70] for x in e if x[0] in ("D1", "D1T", "D2")})) or "—"
            P("  Δ=(%+.2f, %+.2f) mm  接触对 %2d | 键松开→%-3s | 键全按下→%-3s"
              % (a * PITCH, bb * PITCH, len(cts), w1, w2))
            P("       %s" % note)
            if "D1" in (w1, w2):
                ok8 = False
    if ok8:
        P("  ✓ 8 例中 D1 = 0 例。")
        P("    但注意：§10 实算显示 **2 行×8 列的现行排法在这 8 例里 D1 也是 0**。")
        P("    所以「改 4×4 才换来一格错位安全」这个说法不成立 —— 4×4 是几何被迫，")
        P("    构成改成 5V×2+GND×4 是**为了在 4×4 里保住 2×8 本来就有的那个性质**，")
        P("    不是净增了一层保护。真正的净变化见 §8 的 D2/D1T 列与 §11。")
    else:
        P("  ✗ 切比雪夫距离 1 内出现 D1")
        fail.append("切比雪夫距离 1 的错位内出现 D1")

    # ---- C-9 构成的组合学复算 ----
    if not args.no_combo:
        P("")
        P("=" * 78)
        P("§9  独立复算「16 针构成」的组合学（提案人给的那张表）")
        P("=" * 78)
        P("  ※ 这张表只对 **4 行×4 列** 成立。2 行×8 列里一个角位的邻域只有 3 格，")
        P("    「列 2 整列 GND」就能盖满两个 5V 的联合邻域 —— 见 §10 实算。")
        P("  判据：每个 5V 焊位的 8 邻域（场内部分）必须全是功率位，否则存在某个")
        P("        切比雪夫距离 1 的格点错位使 5V 落到信号位上。")
        P("  构成                          | 不同排法总数 | 其中 1 格错位不致损")
        for n5, ng, label in ((2, 2, "5V×2 ＋ GND×2 ＋ 12 信号（现状）"),
                              (2, 3, "5V×2 ＋ GND×3 ＋ 11 信号        "),
                              (1, 3, "5V×1 ＋ GND×3 ＋ 12 信号        "),
                              (2, 4, "5V×2 ＋ GND×4 ＋ 10 键（本方案）")):
            tot, good, gs = combinatorics(N_COLS, N_ROWS, n5, ng)
            P("  %s |   %7d   |  %d" % (label, tot, good))
            if (n5, ng) == (2, 4) and gs:
                P("      最优解（%d 个，互为对称像）中本方案所用的那个：5V 在 %s"
                  % (good, ", ".join(fmt_key(k) for k in sorted(
                      [k for k, v in ASSIGN.items() if v == "DOCK_5V"]))))
                mine = (tuple(sorted(k for k, v in ASSIGN.items() if v == "DOCK_5V")),
                        tuple(sorted(k for k, v in ASSIGN.items() if v == "DOCK_GND")))
                hit = any(tuple(sorted(a)) == mine[0] and tuple(sorted(b)) == mine[1] for a, b in gs)
                P("      本方案是否落在最优解集合内：%s" % ("是 ✓" if hit else "**否 ✗**"))
                if not hit:
                    fail.append("本方案不在「1 格错位不致损」的最优解集合内")

    # ---- C-10 对照：现行 2×8 ----
    P("")
    P("=" * 78)
    P("§10  对照组：ICD 第 3.2 节现行 2 行 × 8 列，跑同一套穷举")
    P("=" * 78)
    lcx = [COL_X[0] + i * PITCH for i in range(LEGACY_COLS)]
    lrz = [ROW_Z[0], ROW_Z[0] - PITCH]
    lp = field_positions(LEGACY_COLS, LEGACY_ROWS, lcx, lrz)
    lreps = lattice_reps(LEGACY_COLS, LEGACY_ROWS, args.lat_max)
    le = run_case("2×8 现行", lp, lp, LEGACY_ASSIGN, LEGACY_ASSIGN, lreps, False)
    lb = min_damage_displacement(lp, lp, LEGACY_ASSIGN, LEGACY_ASSIGN)
    ld1 = sorted({(x[2], x[5]) for x in le if x[0] == "D1"})
    P("  首次致损最小位移 = %.3f mm（4×4 本方案 = %.3f mm）"
      % (lb[0], b[0] if b else float("nan")))
    P("  D1 事件（去重）%d 条，最先出现在：" % len(ld1))
    for t in ld1[:4]:
        P("    %s → %s" % (t[0], t[1]))
    P("  2×8 在切比雪夫距离 1 的 8 例里的最坏等级（用来检验「现状构成一格必损」这句话）：")
    lw = []
    for a in (-1, 0, 1):
        for bb in (-1, 0, 1):
            if a == 0 and bb == 0:
                continue
            zz = judge(contacts(lp, lp, a * PITCH, bb * PITCH, R_TOUCH),
                       LEGACY_ASSIGN, LEGACY_ASSIGN, False)
            lv = set(x[0] for x in zz)
            lw.append(next((k for k in ("D1", "D1T", "D2", "D3", "D4") if k in lv), "—"))
    P("    %s" % "  ".join(lw))
    P("    ⇒ 2×8 现行排法在 4 格正交＋4 格对角的一格错位下 D1 = %d 例。"
      % lw.count("D1"))
    P("    所以「5V×2＋GND×2 无论怎么排一格错位必致损」**只在 4×4 场里成立**；")
    P("    2 行时一个角位只有 3 个邻居，整列 GND 就盖满了联合邻域。")
    P("  另：2×8 在**行序反转**误装下的表现（4×4 的痛点）：")
    for fc, fr, lab in ((False, True, "行序反转"), (True, False, "列序反转")):
        lm = mirror_map(LEGACY_ASSIGN, LEGACY_COLS, LEGACY_ROWS, fc, fr)
        z = judge(contacts(lp, lp, 0, 0, R_TOUCH), LEGACY_ASSIGN, lm, False)
        d1 = [x for x in z if x[0] == "D1"]
        P("    %s，Δ=(0,0)：D1 %d 条 %s" % (lab, len(d1), ("‼ " + d1[0][1][:60]) if d1 else "✓"))

    # ---- 汇总 ----
    P("")
    P("=" * 78)
    P("§11  全部会打坏主机的事件（D1）汇总")
    P("=" * 78)
    d1 = [x for x in all_events if x[0] == "D1"]
    d1t = [x for x in all_events if x[0] == "D1T"]
    d2 = [x for x in all_events if x[0] == "D2"]
    P("  D1（5V 源到主机 GPIO 且**无任何地钳位** → 确定性打穿）：%d 条原始记录" % len(d1))
    P("")
    P("  (a) 按变换分组，每个变换下 D1 首次出现所需的位移 ‖Δ‖：")
    first = {}
    for lvl, tag, name, dx, dz, txt, n in d1:
        m = round(math.hypot(dx, dz), 3)
        if tag not in first or m < first[tag][0]:
            first[tag] = (m, dx, dz, txt)
    P("")
    P("    变换                                首次 D1 的 ‖Δ‖   该处碰上的两个网")
    P("    " + "-" * 92)
    for tag in sorted(first, key=lambda t: first[t][0]):
        m, dx, dz, txt = first[tag]
        P("    %-34s %8.3f mm   %s" % (tag[:34], m, txt[:52]))
    P("")
    P("  (b) 正常朝向（无误装）下位移最小的 D1 事件 —— 这是真正该记进 ICD 的那几条：")
    norm = sorted({(round(math.hypot(x[3], x[4]), 3), round(x[3], 3), round(x[4], 3), x[5])
                   for x in d1 if x[1].startswith("正常朝向")})
    mmin = norm[0][0] if norm else None
    for m, dx, dz, txt in norm:
        if m > mmin + 1e-9:
            break
        P("    ‖Δ‖=%.3f  Δ=(%+.3f, %+.3f)  %s" % (m, dx, dz, txt))
    P("    （代表元集合里的最小值是 %.3f；连续位移下的**确切**门槛见 §7 = 3.630 mm，"
      % (mmin if mmin else float("nan")))
    P("      两者不矛盾：代表元只取格点与半格点，取不到圆盘边界。）")
    P("")
    P("  (c) **零位移即致损**的事件（不需要任何错位，装上就打坏）：")
    zeros = sorted({(x[1], x[5]) for x in d1
                    if abs(x[3]) < 1e-9 and abs(x[4]) < 1e-9})
    if not zeros:
        P("    （无）")
    else:
        for tag, txt in zeros:
            P("    ‼ %-26s %s" % (tag[:26], txt))
    P("")
    P("  D1T（5V 源与 GPIO 同节点、但同节点被地钳位；稳态无注入，接触先后不受控）：%d 条" % len(d1t))
    byT = defaultdict(set)
    for lvl, tag, name, dx, dz, txt, n in d1t:
        byT[(tag, round(math.hypot(dx, dz), 3))].add(name)
    near = sorted({(k[1], k[0]) for k in byT})[:6]
    for mm, tag in near:
        P("    最小 ‖Δ‖=%.3f mm  变换=%s" % (mm, tag))
    P("")
    P("  D2（G04：主机 5V_IN ↔ 主机 GND 外部短路，后果取决于 AS-11/AS-33）：%d 条原始记录" % len(d2))
    d2k = sorted({(x[1], x[2], round(x[3], 3), round(x[4], 3)) for x in d2},
                 key=lambda k: (k[0], math.hypot(k[2], k[3])))
    P("  正常朝向下、切比雪夫距离 ≤ 1 的 D2（这是 G04 真正的暴露面）：")
    n_near = 0
    for tag, name, dx, dz in d2k:
        if tag.startswith("正常朝向") and max(abs(dx), abs(dz)) <= PITCH + 1e-6:
            P("    %-28s Δ=(%+6.3f,%+6.3f)" % (tag, dx, dz))
            n_near += 1
    if n_near == 0:
        P("    （无）")

    P("")
    P("=" * 78)
    if fail:
        P("判定：**不通过**，%d 项：" % len(fail))
        for f in fail:
            P("  ✗ %s" % f)
        P("=" * 78)
        return 1
    P("判定：通过（在本脚本建模的自由度内）")
    P("=" * 78)
    return 0


def report_bucket(ev, P):
    lv = defaultdict(list)
    for x in ev:
        lv[x[0]].append(x)
    for k, name in (("D1", "有损：5V 源到主机 GPIO 且无地钳位"),
                    ("D1T", "有损存疑：5V 源与 GPIO 同节点但被地钳位（瞬态）"),
                    ("D2", "可疑：主机 5V_IN ↔ GND 外部短路（G04）"),
                    ("D3", "良性短路：底座 5V → 地，由限流吸收"),
                    ("D4", "功能错误：键位错/键被拉低/GPIO 互连")):
        rows = lv.get(k, [])
        uniq = {(x[2], round(x[3], 3), round(x[4], 3)) for x in rows}
        P("  %s %-40s 记录 %4d 条，涉及 %3d 个错位位置" % (k, name, len(rows), len(uniq)))
    d1 = lv.get("D1", [])
    if d1:
        near = sorted({(round(math.hypot(x[3], x[4]), 3), x[2], x[5]) for x in d1})[:8]
        P("  → D1 中位移最小的几条：")
        for m, name, txt in near:
            P("     ‖Δ‖=%6.3f  %-26s %s" % (m, name, txt))
    else:
        P("  → D1 = 0 例")


if __name__ == "__main__":
    sys.exit(main())
