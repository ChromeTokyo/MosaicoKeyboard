#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pogo_misalign_enum.py —— 弹簧针触点场错位**穷举**枚举器（方案 J / 4 行 × 4 列）

目的
----
把「触点场错位会不会打坏主机」从「举几个例子」变成「穷举」。
正面关闭 Grok R0 的 G04（GND → 5V_IN 方向论证不正确）与 G05（只算了错一列/错一行，
没算对角错位和错多列）。

本脚本做四件旧分析没做的事：
  1. **连通性建模，不是成对比较。** 把 16 根底座弹簧针、16 个模块焊盘、主机侧网络、
     底座侧网络建成一张带电阻的图，用并查集求「低阻连通分量」。于是
     「5V 针 → 哑焊盘 → 另一根针 → 按键焊盘」这种**多跳**通路会被自动抓到；
     逐针对照表抓不到它。
  2. **接触判据用铜对铜搭接阈值 R = (Ø焊盘 + Ø针尖)/2，不是「针尖完全落在焊盘内」。**
     后者（0.55 mm）只回答「接触可靠不可靠」，前者才回答「碰没碰上」。
     半格错位时一根针同时压住两个相邻焊盘（桥接）因此被自动覆盖。
  3. **连续平移用解析最小触发位移，不用采样。** 每一类危险的「最早在多大位移发生」
     等于该类网对之间的最小中心距减 R（单接触），或两圆盘交集的最小范数点（桥接）。
     对角、多列、多行、非整数格位移**自动全覆盖**——这正是 G05 要的穷举。
  4. **可达性判定。** 算出来的位移还要问「落入槽腔体给不给得了这么多」。
     不可达的危险和可达的危险必须分开写。

坐标系：屏幕朝使用者，USB-C 朝下。X 右、Y 上、Z 朝使用者，原点在 Mosaico 几何中心。
弹簧针轴向 +Y；触点面法向 −Y。本脚本只在 XZ 平面内算。

数值来源：凡标「[ECHO]」者为本文件作者亲自编译 OpenSCAD 取得，命令写在 PROVENANCE 里；
凡标「[推导]」者给出推导；分不清的写 unknown，不编。

用法：
    python3 hardware/pogo_misalign_enum.py            # 跑当前方案（ACTIVE_ALLOCATION）
    python3 hardware/pogo_misalign_enum.py --all      # 连同对照方案一起跑
    python3 hardware/pogo_misalign_enum.py --verbose  # 打印每一条良性事件

退出码：0 = 在可达包络内没有致命事件；1 = 有可达的致命事件；2 = 结构性断言失败。

纯 python3 标准库。
"""

import sys
import math
import itertools
from collections import defaultdict

# =============================================================================
# PROVENANCE —— 每个数从哪来
# =============================================================================
PROVENANCE = """
[ECHO-1] openscad -o /tmp/mb.stl module_board.scad   （源：git show origin/claude/design-d/mech-module:mechanical/module-board/module_board.scad）
         "J2 列 1..4 中心 X = [-34.405, -31.865, -29.325, -26.785]"
         "J2 行 A..4 中心 Z = [2.75, 0.21, -2.33, -4.87]（行 A 在 +Z 屏侧）"
         "触点板 pad_board（XZ 面）：X [-36.095 , -25.095]  Z [-6.46 , 4.34]  底面 Y = -24.095"
         "[检查 6] 定位公差 ±0.45 mm 对 Ø2 焊盘／Ø0.9 针尖：允许偏移 = 0.55 mm，余量 = 0.1 mm。相邻焊盘净间距 0.54 mm"
[ECHO-2] openscad -o /tmp/ds.stl dock_shell.scad     （源：git show origin/claude/design-d/mech-dock:mechanical/dock-shell/dock_shell.scad）
         "弹簧针场：列 1..4 X = [-34.405, -31.865, -29.325, -26.785]  行 A..4 Z = [2.75, 0.21, -2.33, -4.87]"
         "落入槽内腔 X = [-37.845, 22.945]"
         "落入槽模块条带：X <= -22.945  Z = [-8.01, 5.89]"
         "ICD-CONTRACT|DOCK_PAD_D|2"   "ICD-CONTRACT|DOCK_PIN_TIP_D|0.9"
         "ICD-CONTRACT|DOCK_X_TOL|0.45"  "ICD-CONTRACT|DOCK_Z_TOL|0.45"
         "ICD-CONTRACT|DOCK_PITCH|2.54"  "ICD-CONTRACT|DOCK_COLS|4"  "ICD-CONTRACT|DOCK_ROWS|4"
         "ICD-CONTRACT|DOCK_PIN_FORCE_N|0.6"
[FILE-1] hardware/ICD-0.2-DRAFT.md:96   pin 18 = 5V_OUT，「NC，绝不连接任何网络」（硬约束 2 / EL-D-02）
[FILE-2] hardware/ICD-0.2-DRAFT.md:161  EL-D-02；:163 EL-D-03（弹簧针接口无 3V3 针）
[FILE-3] /private/tmp/wt-module-board/hardware/module-board/PINMAP.md:36-46
         KEY_* → H2 针 → GPIO 映射（修订 b 第 2 节）。本表沿用未改。
[FILE-4] /private/tmp/wt-module-board/hardware/module-board/netlist.yaml:364-367
         SLOT_5V_OUT_NC「绝不连接任何网络；焊盘不连铜、无测试点」
[FILE-5] PINMAP.md:162-171  R_S_KEY_* 提案值 1 kΩ
[FILE-6] git show origin/grok/r0-design-review:review/grok/R0/REPORT.md:162(G04) :168(G05)
[NOTE-1] PINMAP.md:119 仍写焊盘 Ø1.8（AS-31-mb-3），与 [ECHO-2] 的 DOCK_PAD_D = 2.0 不符。
         本脚本取 2.0（OpenSCAD 契约值，check_cross_branch.py 强制一致的那个）。
         Ø1.8 会让 R 降到 1.35，各项最小触发位移**各加 0.10 mm**，结论方向不变。
[NOTE-2] 单针额定电流 AS-26 = unknown；主机 GPIO 钳位二极管连续额定 = unknown。
         本脚本**不判定「扛得住」**，只判定「碰没碰上」。
"""

# =============================================================================
# 1. 几何常量
# =============================================================================
COLS_X = [-34.405, -31.865, -29.325, -26.785]   # 列 1..4，列 4 最靠 Mosaico  [ECHO-1]
ROWS_Z = [2.750,     0.210,   -2.330,   -4.870]  # 行 A..D，行 A 在 +Z 屏侧    [ECHO-1]
ROW_NAME = ["A", "B", "C", "D"]

PAD_D = 2.0     # 模块侧焊盘直径 mm   [ECHO-2] DOCK_PAD_D
TIP_D = 0.9     # 弹簧针针尖直径 mm   [ECHO-2] DOCK_PIN_TIP_D
PITCH = 2.54    # [ECHO-2] DOCK_PITCH

# [推导] 铜对铜搭接阈值：针尖圆与焊盘圆外切时中心距 = (PAD_D + TIP_D)/2。
# 小于它就有铜搭上。注意这和「针尖完全落入焊盘」的判据 (PAD_D-TIP_D)/2 = 0.55 是两回事：
# 0.55 回答「接触可靠吗」，1.45 回答「碰没碰上」。现有文档只有 0.55，这是缺口。
R_CONTACT = (PAD_D + TIP_D) / 2.0               # 1.45 mm
# [推导] 一根针能同时搭上两个焊盘的充要条件：两焊盘中心距 < 2R = 2.90 mm。
R_BRIDGE_MAX = 2.0 * R_CONTACT                  # 2.90 mm

TOL_X = 0.45    # [ECHO-2] DOCK_X_TOL（最坏值）
TOL_Z = 0.45    # [ECHO-2] DOCK_Z_TOL

# 触点板外形 [ECHO-1]
PAD_BOARD_X = (-36.095, -25.095)
PAD_BOARD_Z = (-6.460,    4.340)
# 落入槽模块条带腔体 [ECHO-2]
CAVITY_X = (-37.845, -22.945)
CAVITY_Z = (-8.010,    5.890)

# [推导] 纯平移可达范围 = 腔体减板外形
REACH_DX = (CAVITY_X[0] - PAD_BOARD_X[0], CAVITY_X[1] - PAD_BOARD_X[1])   # (-1.75, +2.15)
REACH_DZ = (CAVITY_Z[0] - PAD_BOARD_Z[0], CAVITY_Z[1] - PAD_BOARD_Z[1])   # (-1.55, +1.55)

# =============================================================================
# 2. 分配表 —— 换方案只改这一段
# =============================================================================
# 每条：(列 1..4, 行 'A'..'D', 模块侧焊盘网名, 底座侧弹簧针网名)
# 模块侧网名前缀决定电气类别（见 module_pad_class）：
#   SLOT_5V_IN / DOCK_5V  -> 主机 5V_IN（纯铜直连 H2 pin 17，硬约束 1 禁止串联器件）
#   DOCK_GND              -> 主机 GND（H2 pin 20）
#   KEY_*                 -> 经 R_S_KEY_* 1 kΩ 到主机 GPIO
#   DOCK_SDA / DOCK_SCL   -> 经 R_LINK（0 Ω，DNP）到主机 GPIO0/1，**无串阻**
#   DUMMY_*               -> 孤立焊盘，不连任何铜、不打过孔
#   NC_*                  -> 该位无焊盘
# 底座侧网名：
#   DOCK_5V   -> 底座 5V 输出轨（限流/短路关断/防反灌）
#   DOCK_GND  -> 底座地
#   SW_*      -> 轻触开关一端，另一端接 DOCK_GND（常开）
#   DPIN_1M_* -> 装针但经 1 MΩ 泄放电阻接 DOCK_GND
#   NOPIN_*   -> 该位不装针

ALLOC_P2 = {
    "name": "P2：角位 5V ＋ 哑位护城河（9 键硬线，弃 I²C）",
    "pins": [
        (1, "A", "DOCK_GND",  "DOCK_GND"),
        (2, "A", "KEY_UP",    "SW_UP"),
        (3, "A", "DUMMY_1",   "DPIN_1M_1"),
        (4, "A", "DOCK_5V",   "DOCK_5V"),
        (1, "B", "KEY_L",     "SW_L"),
        (2, "B", "KEY_DOWN",  "SW_DOWN"),
        (3, "B", "DUMMY_2",   "DPIN_1M_2"),
        (4, "B", "DUMMY_3",   "DPIN_1M_3"),
        (1, "C", "KEY_A",     "SW_A"),
        (2, "C", "KEY_LEFT",  "SW_LEFT"),
        (3, "C", "KEY_B",     "SW_B"),
        (4, "C", "KEY_X",     "SW_X"),
        (1, "D", "DOCK_GND",  "DOCK_GND"),
        (2, "D", "KEY_RIGHT", "SW_RIGHT"),
        (3, "D", "KEY_Y",     "SW_Y"),
        (4, "D", "DUMMY_4",   "DPIN_1M_4"),
    ],
    # KEY_* -> H2 针 -> GPIO，沿用 PINMAP 修订 b 第 2 节 [FILE-3]
    "key_gpio": {
        "KEY_UP": (1, 55), "KEY_DOWN": (3, 19), "KEY_LEFT": (5, 18), "KEY_RIGHT": (7, 17),
        "KEY_L": (9, 16), "KEY_A": (2, 53), "KEY_B": (4, 48), "KEY_X": (6, 13), "KEY_Y": (8, 12),
    },
}

# 对照 1：旧 2 行 × 8 列（ICD 3.2 / PINMAP 4.2，已作废）。列 1..8，行 A/B。
ALLOC_OLD_2x8 = {
    "name": "对照：旧 2 行 × 8 列（ICD 第 3.2 节，已作废）",
    "geometry": "2x8",
    "pins": [
        (1, "A", "DOCK_5V",  "DOCK_5V"),  (1, "B", "DOCK_5V",  "DOCK_5V"),
        (2, "A", "DOCK_GND", "DOCK_GND"), (2, "B", "DOCK_GND", "DOCK_GND"),
        (3, "A", "KEY_UP",   "SW_UP"),    (3, "B", "KEY_DOWN", "SW_DOWN"),
        (4, "A", "KEY_LEFT", "SW_LEFT"),  (4, "B", "KEY_RIGHT","SW_RIGHT"),
        (5, "A", "KEY_L",    "SW_L"),     (5, "B", "KEY_R",    "SW_R"),
        (6, "A", "KEY_A",    "SW_A"),     (6, "B", "KEY_B",    "SW_B"),
        (7, "A", "KEY_X",    "SW_X"),     (7, "B", "KEY_Y",    "SW_Y"),
        (8, "A", "DOCK_SDA", "DPIN_SDA"), (8, "B", "DOCK_SCL", "DPIN_SCL"),
    ],
    "key_gpio": {
        "KEY_UP": (1, 55), "KEY_DOWN": (3, 19), "KEY_LEFT": (5, 18), "KEY_RIGHT": (7, 17),
        "KEY_L": (9, 16), "KEY_R": (11, 15), "KEY_A": (2, 53), "KEY_B": (4, 48),
        "KEY_X": (6, 13), "KEY_Y": (8, 12),
    },
}

# 对照 2：把旧表直译进 4×4（裁定担心的那个做法：DOCK_ROWS 2->4 但分配照抄）
ALLOC_NAIVE_4x4 = {
    "name": "对照：4×4 朴素直译（无防错，裁定担心的那个）",
    "pins": [
        (1, "A", "DOCK_5V",  "DOCK_5V"),  (2, "A", "DOCK_GND", "DOCK_GND"),
        (3, "A", "KEY_UP",   "SW_UP"),    (4, "A", "KEY_DOWN", "SW_DOWN"),
        (1, "B", "DOCK_5V",  "DOCK_5V"),  (2, "B", "DOCK_GND", "DOCK_GND"),
        (3, "B", "KEY_LEFT", "SW_LEFT"),  (4, "B", "KEY_RIGHT","SW_RIGHT"),
        (1, "C", "KEY_L",    "SW_L"),     (2, "C", "KEY_R",    "SW_R"),
        (3, "C", "KEY_A",    "SW_A"),     (4, "C", "KEY_B",    "SW_B"),
        (1, "D", "KEY_X",    "SW_X"),     (2, "D", "KEY_Y",    "SW_Y"),
        (3, "D", "DOCK_SDA", "DPIN_SDA"), (4, "D", "DOCK_SCL", "DPIN_SCL"),
    ],
    "key_gpio": ALLOC_OLD_2x8["key_gpio"],
}

# 对照 3：P2 的 10 键退化版（位 16 由 DUMMY_4 改回 KEY_R），用来量「那 1 个按键买到什么」
ALLOC_P2_10KEY = {
    "name": "对照：P2 的 10 键退化版（位 16 = KEY_R，不防 D4）",
    "pins": [p if not (p[0] == 4 and p[1] == "D") else (4, "D", "KEY_R", "SW_R")
             for p in ALLOC_P2["pins"]],
    "key_gpio": dict(ALLOC_P2["key_gpio"], KEY_R=(11, 15)),
}

# 对照 4：P3 —— 本脚本跑出 F3「链式桥接」后构造的候选修补。
# 规则不再是「5V 的 8 邻域全哑」，而是「5V 所在的**整行与整列**，模块侧焊盘与底座侧弹簧针
# **两边都**必须是哑位」。代价：哑位由 4 个涨到 6 个，按键由 9 个掉到 7 个。
ALLOC_P3 = {
    "name": "P3：整行整列哑位（7 键）—— 针对 F3 链式桥接构造的候选",
    "pins": [
        (1, "A", "DUMMY_1",   "DPIN_1M_1"),
        (2, "A", "DUMMY_2",   "DPIN_1M_2"),
        (3, "A", "DUMMY_3",   "DPIN_1M_3"),
        (4, "A", "DOCK_5V",   "DOCK_5V"),
        (1, "B", "KEY_UP",    "SW_UP"),
        (2, "B", "KEY_DOWN",  "SW_DOWN"),
        (3, "B", "DOCK_GND",  "DOCK_GND"),
        (4, "B", "DUMMY_4",   "DPIN_1M_4"),
        (1, "C", "KEY_LEFT",  "SW_LEFT"),
        (2, "C", "KEY_RIGHT", "SW_RIGHT"),
        (3, "C", "KEY_L",     "SW_L"),
        (4, "C", "DUMMY_5",   "DPIN_1M_5"),
        (1, "D", "DOCK_GND",  "DOCK_GND"),
        (2, "D", "KEY_A",     "SW_A"),
        (3, "D", "KEY_B",     "SW_B"),
        (4, "D", "DUMMY_6",   "DPIN_1M_6"),
    ],
    "key_gpio": {k: v for k, v in ALLOC_P2["key_gpio"].items()
                 if k in ("KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT", "KEY_L", "KEY_A", "KEY_B")},
}

ACTIVE_ALLOCATION = ALLOC_P2

# 每个 D4 元素在**实物**上能不能发生，与在 **EDA 里**能不能发生，是两回事。
# [推导] 触点板中心 X = −30.595；J3 落脚线中面 X = −26.935（[ECHO-1] 两排 −26.135/−27.735）。
#        偏心 |−26.935 − (−30.595)| = 3.660 mm。把实物触点板转 90°/180°/镜像后焊到槽板上，
#        J3 焊盘会离槽板 2 × 3.660 = 7.320 mm，焊不上 → 实物层面这几类不可能发生。
#        但**在 EDA 里把 J2 封装转 180° 或镜像放置，几何完全不挡**：焊盘阵列原地变，板形不变。
#        本项目已有 D-009／D-009-R 的镜像前科（PINMAP.md:93）。
PHYSICAL_NOTE = {
    "e":        "（正确装配）",
    "rot90":    "实物不可能（J3 偏心 3.660 mm）；**EDA 封装错放可能**",
    "rot180":   "实物不可能（J3 偏心 3.660 mm）；**EDA 封装错放可能**",
    "rot270":   "实物不可能（J3 偏心 3.660 mm）；**EDA 封装错放可能**",
    "mirrorX":  "实物不可能；**EDA 镜像放置可能**",
    "mirrorZ":  "实物不可能；**EDA 镜像放置可能**",
    "mirrorD1": "实物不可能；**EDA 镜像＋旋转可能**",
    "mirrorD2": "实物不可能；**EDA 镜像＋旋转可能**",
}

# =============================================================================
# 3. 电气模型
# =============================================================================
R_SERIES_KEY = 1_000.0     # R_S_KEY_* 提案值 [FILE-5]
R_DUMMY_BLEED = 1_000_000.0  # 哑位泄放电阻（P2 提案）
R_CONTACT_OHM = 0.1        # 一次弹簧针接触，量级；unknown，仅用于「低阻/高阻」分类
R_COPPER = 0.0             # 纯铜
R_LINK_DNP = 0.0           # R_LINK 若装配为 0 Ω（DNP 时该通路根本不存在）

# 低阻阈值：小于它就认为「电气上连上了，够危险」
R_LOW_THRESHOLD = 100_000.0


def module_pad_class(net):
    if net in ("DOCK_5V", "SLOT_5V_IN"):
        return "HOST_5V_IN"
    if net in ("DOCK_GND", "SLOT_GND"):
        return "HOST_GND"
    if net.startswith("KEY_"):
        return "HOST_GPIO"
    if net in ("DOCK_SDA", "DOCK_SCL"):
        return "HOST_GPIO_NOSERIES"   # 无串阻，直击 GPIO0/1
    if net.startswith("DUMMY"):
        return "ISOLATED"
    if net.startswith("NC"):
        return "NOPAD"
    raise ValueError("未知模块侧网名：%s" % net)


def dock_pin_class(net):
    if net == "DOCK_5V":
        return "DOCK_5V_SRC"
    if net == "DOCK_GND":
        return "DOCK_GND_PIN"
    if net.startswith("SW_"):
        return "DOCK_SWITCH"
    if net.startswith("DPIN_1M"):
        return "DOCK_DUMMY_1M"
    if net.startswith("DPIN_"):
        return "DOCK_FLOAT"          # 旧表的 SDA/SCL 针：接底座 I²C 器件
    if net.startswith("NOPIN"):
        return "NOPIN"
    raise ValueError("未知底座侧网名：%s" % net)


# =============================================================================
# 4. 并查集
# =============================================================================
class DSU:
    __slots__ = ("p",)

    def __init__(self):
        self.p = {}

    def find(self, a):
        p = self.p
        if a not in p:
            p[a] = a
            return a
        r = a
        while p[r] != r:
            r = p[r]
        while p[a] != r:
            p[a], a = r, p[a]
        return r

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb

    def same(self, a, b):
        return self.find(a) == self.find(b)


# =============================================================================
# 5. 场的构造与 D4 变换
# =============================================================================
def build_field(alloc):
    """返回 (pads, pins)。每项 = dict(idx, col, row, x, z, net, cls)。"""
    geom = alloc.get("geometry", "4x4")
    if geom == "2x8":
        cols_x = [COLS_X[0] + (c - 1) * PITCH for c in range(1, 9)]
        rows_z = [ROWS_Z[0], ROWS_Z[0] - PITCH]
        rows = ["A", "B"]
    else:
        cols_x, rows_z, rows = COLS_X, ROWS_Z, ROW_NAME
    pads, pins = [], []
    for i, (col, row, mnet, dnet) in enumerate(alloc["pins"]):
        x = cols_x[col - 1]
        z = rows_z[rows.index(row)]
        pads.append(dict(idx=i, col=col, row=row, x=x, z=z, net=mnet, cls=module_pad_class(mnet)))
        pins.append(dict(idx=i, col=col, row=row, x=x, z=z, net=dnet, cls=dock_pin_class(dnet)))
    return pads, pins


def field_center(pads):
    xs = [p["x"] for p in pads]
    zs = [p["z"] for p in pads]
    return (min(xs) + max(xs)) / 2.0, (min(zs) + max(zs)) / 2.0


# D4：正方形对称群的 8 个元素，作用在以场心为原点的局部坐标 (u, w) 上。
# 4×4 方阵在 D4 下映回自身；2 行×8 列只在 {e, r180, mx, mz} 下自映（长方形群 D2）。
D4 = [
    ("e",        lambda u, w: (u, w)),
    ("rot90",    lambda u, w: (-w, u)),
    ("rot180",   lambda u, w: (-u, -w)),
    ("rot270",   lambda u, w: (w, -u)),
    ("mirrorX",  lambda u, w: (u, -w)),    # 沿 X 轴镜像（Z 取反）
    ("mirrorZ",  lambda u, w: (-u, w)),    # 沿 Z 轴镜像（X 取反）
    ("mirrorD1", lambda u, w: (w, u)),     # 主对角镜像（转置）
    ("mirrorD2", lambda u, w: (-w, -u)),   # 副对角镜像
]


def transform_pads(pads, tname, tfun, cx, cz, dx=0.0, dz=0.0, yaw_deg=0.0):
    """对焊盘场施加 D4 变换（绕场心）＋ 偏航 ＋ 平移，返回新的坐标列表。"""
    out = []
    ca = math.cos(math.radians(yaw_deg))
    sa = math.sin(math.radians(yaw_deg))
    for p in pads:
        u, w = p["x"] - cx, p["z"] - cz
        u, w = tfun(u, w)
        u, w = u * ca - w * sa, u * sa + w * ca
        out.append((cx + u + dx, cz + w + dz))
    return out


# =============================================================================
# 6. 接触与连通性
# =============================================================================
def contacts(pins, pad_xy):
    """返回接触对集合 frozenset{(pin_idx, pad_idx)}。铜对铜搭接判据。"""
    res = []
    r2 = R_CONTACT * R_CONTACT
    for pin in pins:
        if pin["cls"] == "NOPIN":
            continue
        px, pz = pin["x"], pin["z"]
        for j, (qx, qz) in enumerate(pad_xy):
            if pad_xy_cls[j] == "NOPAD":
                continue
            ddx = px - qx
            ddz = pz - qz
            if ddx * ddx + ddz * ddz < r2:
                res.append((pin["idx"], j))
    return frozenset(res)


pad_xy_cls = []   # 由 analyze_allocation 填，避免在内层循环里查 dict


def build_graph(pads, pins, contact_set, switches_closed):
    """建图并返回 (低阻并查集, 全阻并查集, 边表)。"""
    low = DSU()
    allg = DSU()
    edges = []
    adj_low = defaultdict(list)

    def add(a, b, r, why):
        edges.append((a, b, r, why))
        allg.union(a, b)
        if r < R_LOW_THRESHOLD:
            low.union(a, b)
            adj_low[a].append((b, r, why))
            adj_low[b].append((a, r, why))

    # —— 主机侧固定节点（哪怕没有边也要存在，便于断言度数 0）——
    for n in ("HOST_5V_IN", "HOST_GND", "HOST_5V_OUT", "HOST_3V3"):
        low.find(n)
        allg.find(n)

    # —— 模块板内部：焊盘 → 主机网络 ——
    for p in pads:
        node = "MPAD_%d" % p["idx"]
        c = p["cls"]
        if c == "HOST_5V_IN":
            add(node, "HOST_5V_IN", R_COPPER, "J1 pin17 纯铜，硬约束 1 禁串联器件")
        elif c == "HOST_GND":
            add(node, "HOST_GND", R_COPPER, "J1 pin20")
        elif c == "HOST_GPIO":
            add(node, "HOST_GPIO_%s" % p["net"], R_SERIES_KEY, "R_S_KEY 1kΩ")
        elif c == "HOST_GPIO_NOSERIES":
            add(node, "HOST_GPIO_%s" % p["net"], R_LINK_DNP, "R_LINK 0Ω（装配时）")
        elif c == "ISOLATED":
            low.find(node)
            allg.find(node)   # 孤立焊盘：存在但不连任何铜
        # NOPAD：不建节点

    # —— 底座内部：弹簧针 → 底座网络 ——
    for q in pins:
        node = "DPIN_%d" % q["idx"]
        c = q["cls"]
        if c == "DOCK_5V_SRC":
            add(node, "DOCK_5V_RAIL", R_COPPER, "底座 5V 输出")
        elif c == "DOCK_GND_PIN":
            add(node, "DOCK_GND_RAIL", R_COPPER, "底座地")
        elif c == "DOCK_SWITCH":
            if switches_closed:
                add(node, "DOCK_GND_RAIL", R_COPPER, "轻触开关按下")
            else:
                low.find(node)
                allg.find(node)
        elif c == "DOCK_DUMMY_1M":
            add(node, "DOCK_GND_RAIL", R_DUMMY_BLEED, "哑针 1MΩ 泄放")
        elif c == "DOCK_FLOAT":
            add(node, "DOCK_I2C_DEV", R_COPPER, "底座 I²C 器件脚")
        # NOPIN：不建节点

    # —— 错位产生的接触边 ——
    for (i, j) in contact_set:
        add("DPIN_%d" % i, "MPAD_%d" % j, R_CONTACT_OHM, "弹簧针接触")

    return low, allg, edges, adj_low


def trace_path(adj_low, src, dst, pads, pins):
    """在低阻子图里找一条 src→dst 的路径，用于把「哪两个网碰上了、怎么碰上的」写清楚。"""
    if src == dst:
        return [src]
    prev = {src: None}
    stack = [src]
    while stack:
        u = stack.pop()
        if u == dst:
            break
        for (v, r, why) in adj_low.get(u, ()):
            if v not in prev:
                prev[v] = (u, r, why)
                stack.append(v)
    if dst not in prev:
        return None
    seq = []
    cur = dst
    while cur is not None and prev[cur] is not None:
        u, r, why = prev[cur]
        seq.append((u, cur, r, why))
        cur = u
    seq.reverse()

    def label(n):
        if n.startswith("MPAD_"):
            p = pads[int(n[5:])]
            return "模块焊盘(列%d,行%s)=%s" % (p["col"], p["row"], p["net"])
        if n.startswith("DPIN_") and n[5:].isdigit():
            q = pins[int(n[5:])]
            return "底座针(列%d,行%s)=%s" % (q["col"], q["row"], q["net"])
        return n
    parts = [label(seq[0][0])]
    for (u, v, r, why) in seq:
        parts.append("--[%s %s]-->" % (why, ("%.0fΩ" % r) if r >= 1 else "≈0Ω"))
        parts.append(label(v))
    return " ".join(parts)


# =============================================================================
# 7. 判据 —— 每一条显式断言
# =============================================================================
def evaluate(pads, pins, contact_set, switches_closed):
    """返回事件列表。每条 = dict(sev, code, msg)。sev: FATAL / SEVERE / LATENT / WARN / INFO"""
    low, allg, edges, adj = build_graph(pads, pins, contact_set, switches_closed)
    ev = []

    gpio_nodes = sorted({"HOST_GPIO_%s" % p["net"] for p in pads if p["cls"].startswith("HOST_GPIO")})

    # 判据 1：任何情形下 5V_IN 不得接触到任何 GPIO 网
    #   1a：底座 5V 输出轨 → 主机 GPIO
    hit = [g for g in gpio_nodes if low.same("DOCK_5V_RAIL", g)]
    if hit:
        ev.append(dict(sev="FATAL", code="F1",
                       msg="底座 5V 输出轨 低阻连通 主机 GPIO：%s（共 %d 根）"
                           % (", ".join(g.replace("HOST_GPIO_", "") for g in hit), len(hit)),
                       path=trace_path(adj, "DOCK_5V_RAIL", hit[0], pads, pins)))
    #   1b：主机 5V_IN 自身 → 主机 GPIO（旧分析完全没有这一类）
    hit = [g for g in gpio_nodes if low.same("HOST_5V_IN", g)]
    if hit:
        ev.append(dict(sev="FATAL", code="F2",
                       msg="主机 5V_IN 低阻连通 主机 GPIO：%s（共 %d 根；自灌）"
                           % (", ".join(g.replace("HOST_GPIO_", "") for g in hit), len(hit)),
                       path=trace_path(adj, "HOST_5V_IN", hit[0], pads, pins)))

    # 判据 2：5V_OUT（H2 pin 18）绝不可被连接到任何东西
    comp = [n for n in allg.p if allg.same(n, "HOST_5V_OUT")]
    if len(comp) > 1:
        ev.append(dict(sev="FATAL", code="O1",
                       msg="H2 pin18 5V_OUT 被连到：%s（违反硬约束 2 / EL-D-02）"
                           % ", ".join(sorted(x for x in comp if x != "HOST_5V_OUT"))))

    # 判据 3：GND → 5V_IN 方向（G04）
    if low.same("HOST_5V_IN", "DOCK_GND_RAIL"):
        ev.append(dict(sev="SEVERE", code="S1",
                       msg="主机 5V_IN 低阻连通 底座地（G04：主机若经原生 USB 已上电，"
                           "就是短了用户的充电器；底座的限流/短路关断管不了主机自己的电源）",
                       path=trace_path(adj, "HOST_5V_IN", "DOCK_GND_RAIL", pads, pins)))
    if low.same("HOST_5V_IN", "HOST_GND"):
        ev.append(dict(sev="SEVERE", code="S2",
                       msg="主机 5V_IN 低阻连通 主机 GND（同一颗器件内部对地短路）",
                       path=trace_path(adj, "HOST_5V_IN", "HOST_GND", pads, pins)))

    # 判据 4：两根 GPIO 互相短接（不致命但要报）
    shorted = [(a, b) for a, b in itertools.combinations(gpio_nodes, 2) if low.same(a, b)]
    if shorted:
        ev.append(dict(sev="WARN", code="G1",
                       msg="主机 GPIO 互相短接 %d 对，例如 %s ↔ %s（两根都配成上拉输入时无损；"
                           "任一根被固件配成输出就是对推）"
                           % (len(shorted), shorted[0][0].replace("HOST_GPIO_", ""),
                              shorted[0][1].replace("HOST_GPIO_", "")),
                       path=trace_path(adj, shorted[0][0], shorted[0][1], pads, pins)))

    # 补充判据（旧文档没有，但同样是「两个网碰上了」）
    # 5：3V3 不得被底座接触（EL-D-03）
    comp3 = [n for n in allg.p if allg.same(n, "HOST_3V3")]
    if len(comp3) > 1:
        ev.append(dict(sev="FATAL", code="O2", msg="主机 3V3 被连到底座（违反 EL-D-03）"))

    # 6：潜伏型 —— 开关按下才成立的 5V_IN 对地短路
    if switches_closed and low.same("HOST_5V_IN", "DOCK_GND_RAIL"):
        for e in ev:
            if e["code"] == "S1":
                e["code"] = "s1"
                e["sev"] = "LATENT"
                e["msg"] += "【仅在按住某键时成立】"

    # 7：底座自身输出短路（可接受、可见）
    if low.same("DOCK_5V_RAIL", "DOCK_GND_RAIL"):
        ev.append(dict(sev="INFO", code="P1", msg="底座 5V 输出对底座地短路 → 保护动作，可接受"))

    # 8：幽灵按键（底座地落到按键焊盘）
    ghosts = [g.replace("HOST_GPIO_", "") for g in gpio_nodes
              if low.same(g, "DOCK_GND_RAIL") and not low.same(g, "DOCK_5V_RAIL")]
    if ghosts:
        ev.append(dict(sev="INFO", code="K1",
                       msg="被拉到底座地、读作按下的 GPIO：%s（功能错误，无损）" % ", ".join(ghosts)))

    # 9：高阻泄漏（1MΩ 哑针落到 5V_IN 上）—— 低阻并查集看不到，用全阻并查集
    if not low.same("HOST_5V_IN", "DOCK_GND_RAIL") and allg.same("HOST_5V_IN", "DOCK_GND_RAIL"):
        ev.append(dict(sev="INFO", code="L1",
                       msg="主机 5V_IN 经高阻（≥1MΩ）到底座地，约 5 µA，无损"))

    # 10：供电通不通（功能，不是安全）
    powered = low.same("DOCK_5V_RAIL", "HOST_5V_IN")
    return ev, powered


# =============================================================================
# 8. 解析最小触发位移（连续平移，穷举）
# =============================================================================
def min_translation_single(pins, pads, pin_pred, pad_pred, cx, cz, tname, tfun):
    """某根满足 pin_pred 的针接触到某个满足 pad_pred 的焊盘，所需的最小平移范数。
       = min over pairs |P_i - T(Q_j)| - R，下限截 0。None = 该类不存在。"""
    tq = transform_pads(pads, tname, tfun, cx, cz)
    best = None
    arg = None
    for q in pins:
        if not pin_pred(q):
            continue
        for j, p in enumerate(pads):
            if not pad_pred(p):
                continue
            d = math.hypot(q["x"] - tq[j][0], q["z"] - tq[j][1])
            if best is None or d < best:
                best = d
                arg = (q, p, d)
    if best is None:
        return None, None
    return max(0.0, best - R_CONTACT), arg


def min_norm_in_lens(c1, c2, R):
    """两个半径 R、圆心 c1/c2 的圆盘交集中范数最小的点的范数；无交集返回 None。
       用于桥接：δ 需同时使某针落在两个焊盘的 R 邻域内。"""
    d = math.hypot(c1[0] - c2[0], c1[1] - c2[1])
    if d >= 2 * R:
        return None
    cands = []
    if math.hypot(*c1) <= R and math.hypot(*c2) <= R:
        return 0.0
    for c in (c1, c2):
        n = math.hypot(*c)
        if n > R:
            pt = (c[0] * (1 - R / n), c[1] * (1 - R / n))
            if math.hypot(pt[0] - c1[0], pt[1] - c1[1]) <= R + 1e-9 and \
               math.hypot(pt[0] - c2[0], pt[1] - c2[1]) <= R + 1e-9:
                cands.append(math.hypot(*pt))
    # 两圆交点
    if d > 1e-12:
        a = d / 2.0
        h2 = R * R - a * a
        if h2 >= 0:
            h = math.sqrt(h2)
            mx = (c1[0] + c2[0]) / 2.0
            my = (c1[1] + c2[1]) / 2.0
            ux, uy = (c2[0] - c1[0]) / d, (c2[1] - c1[1]) / d
            for s in (+1, -1):
                pt = (mx + s * h * (-uy), my + s * h * ux)
                cands.append(math.hypot(*pt))
    return min(cands) if cands else None


def min_translation_bridge(pins, pads, pad_pred_a, pad_pred_b, cx, cz, tname, tfun):
    """一根针同时搭上「满足 a」和「满足 b」的两个焊盘，所需的最小平移范数。"""
    tq = transform_pads(pads, tname, tfun, cx, cz)
    best = None
    arg = None
    for q in pins:
        if q["cls"] == "NOPIN":
            continue
        for ja, pa in enumerate(pads):
            if not pad_pred_a(pa):
                continue
            for jb, pb in enumerate(pads):
                if ja == jb or not pad_pred_b(pb):
                    continue
                c1 = (q["x"] - tq[ja][0], q["z"] - tq[ja][1])
                c2 = (q["x"] - tq[jb][0], q["z"] - tq[jb][1])
                m = min_norm_in_lens(c1, c2, R_CONTACT)
                if m is not None and (best is None or m < best):
                    best = m
                    arg = (q, pa, pb, m)
    return best, arg


# =============================================================================
# 9. 可达性搜索（腔体内最坏位姿）
# =============================================================================
def board_corners(cx, cz, dx, dz, yaw_deg):
    ca, sa = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    out = []
    for x in PAD_BOARD_X:
        for z in PAD_BOARD_Z:
            u, w = x - cx, z - cz
            out.append((cx + u * ca - w * sa + dx, cz + u * sa + w * ca + dz))
    return out


def pose_feasible(cx, cz, dx, dz, yaw_deg):
    for (x, z) in board_corners(cx, cz, dx, dz, yaw_deg):
        if not (CAVITY_X[0] - 1e-9 <= x <= CAVITY_X[1] + 1e-9):
            return False
        if not (CAVITY_Z[0] - 1e-9 <= z <= CAVITY_Z[1] + 1e-9):
            return False
    return True


def reachable_min_distance(pins, pads, pin_pred, pad_pred, cx, cz, tname, tfun,
                           n=121, yaw_steps=41, yaw_max=20.0):
    """在腔体允许的位姿里，搜 pin_pred 针到 pad_pred 焊盘的可达最小中心距。"""
    best = float("inf")
    bestpose = None
    xs = [REACH_DX[0] + (REACH_DX[1] - REACH_DX[0]) * i / (n - 1) for i in range(n)]
    zs = [REACH_DZ[0] + (REACH_DZ[1] - REACH_DZ[0]) * i / (n - 1) for i in range(n)]
    yaws = [-yaw_max + 2 * yaw_max * i / (yaw_steps - 1) for i in range(yaw_steps)]
    tgt_pins = [q for q in pins if pin_pred(q)]
    tgt_pads = [j for j, p in enumerate(pads) if pad_pred(p)]
    if not tgt_pins or not tgt_pads:
        return None, None
    for yaw in yaws:
        for dx in xs:
            for dz in zs:
                if not pose_feasible(cx, cz, dx, dz, yaw):
                    continue
                tq = transform_pads(pads, tname, tfun, cx, cz, dx, dz, yaw)
                for q in tgt_pins:
                    for j in tgt_pads:
                        d = math.hypot(q["x"] - tq[j][0], q["z"] - tq[j][1])
                        if d < best:
                            best = d
                            bestpose = (yaw, dx, dz)
    return (None, None) if best == float("inf") else (best, bestpose)


# =============================================================================
# 10. 主流程
# =============================================================================
def analyze_allocation(alloc, verbose=False):
    global pad_xy_cls
    pads, pins = build_field(alloc)
    pad_xy_cls = [p["cls"] for p in pads]
    cx, cz = field_center(pads)
    n = len(pads)
    geom = alloc.get("geometry", "4x4")

    out = []
    w = out.append
    w("=" * 78)
    w("方案：%s" % alloc["name"])
    w("场：%d 位；场心 (X, Z) = (%.3f, %.3f)；间距 %.2f mm" % (n, cx, cz, PITCH))
    w("接触判据 R = (Ø%.1f + Ø%.1f)/2 = %.3f mm；桥接上限 2R = %.3f mm" %
      (PAD_D, TIP_D, R_CONTACT, R_BRIDGE_MAX))
    w("纯平移可达包络：ΔX ∈ [%+.3f, %+.3f]，ΔZ ∈ [%+.3f, %+.3f]（腔体减板外形）" %
      (REACH_DX[0], REACH_DX[1], REACH_DZ[0], REACH_DZ[1]))
    w("")

    fatal_events = []
    all_events = []

    # ---------- 第 0 遍：结构性断言（与错位无关）----------
    w("---- 第 0 遍：结构性断言 ----")
    struct_fail = 0
    nets = [p[2] for p in alloc["pins"]]
    if "SLOT_5V_OUT_NC" in nets or "5V_OUT" in nets:
        w("  [断言 2] 失败：触点场里出现了 5V_OUT")
        struct_fail += 1
    else:
        w("  [断言 2] 通过：触点场 %d 位里没有任何一位是 5V_OUT（H2 pin18）。" % n)
        w("            该焊盘在模块板上不连铜、不到 J3/J2 [FILE-1][FILE-4]，"
          "因此**任何错位都不可能碰到它**——它根本不在这个平面上。")
    if any(x in nets for x in ("SLOT_3V3", "VCC_3V3", "DOCK_3V3")):
        w("  [断言 5] 失败：触点场里出现了 3V3")
        struct_fail += 1
    else:
        w("  [断言 5] 通过：触点场里没有 3V3（EL-D-03）。")
    # 护城河完整性：5V_IN 焊盘的 8 邻域（含对角）是否全非 GPIO
    fv = [p for p in pads if p["cls"] == "HOST_5V_IN"]
    for p in fv:
        nb = [q for q in pads if q["idx"] != p["idx"]
              and abs(q["x"] - p["x"]) < 1.5 * PITCH and abs(q["z"] - p["z"]) < 1.5 * PITCH]
        bad = [q["net"] for q in nb if q["cls"].startswith("HOST_GPIO")]
        w("  [护城河] 5V_IN 焊盘 (列%d,行%s) 的 8 邻域共 %d 格：%s"
          % (p["col"], p["row"], len(nb), "全部非 GPIO ✓" if not bad else "含 GPIO ✗ → " + ",".join(bad)))
    # 桥接可能性（结构性）：哪些焊盘对中心距 < 2R
    bridgeable = []
    for a, b in itertools.combinations(pads, 2):
        d = math.hypot(a["x"] - b["x"], a["z"] - b["z"])
        if d < R_BRIDGE_MAX:
            bridgeable.append((a, b, d))
    n5v_gpio = [(a, b) for a, b, d in bridgeable
                if {a["cls"], b["cls"]} & {"HOST_5V_IN"} and
                (a["cls"].startswith("HOST_GPIO") or b["cls"].startswith("HOST_GPIO"))]
    n5v_gnd = [(a, b) for a, b, d in bridgeable
               if {a["cls"], b["cls"]} == {"HOST_5V_IN", "HOST_GND"}]
    w("  [桥接] 中心距 < 2R = %.2f mm 的焊盘对共 %d 组（只有正交相邻的 %.2f mm 达得到；"
      "对角 %.3f mm 达不到）" % (R_BRIDGE_MAX, len(bridgeable), PITCH, PITCH * math.sqrt(2)))
    w("  [断言 F2] 5V_IN 与 GPIO 可被同一根针桥接的焊盘对：%d 组 %s"
      % (len(n5v_gpio), "→ 结构上不可能 ✓" if not n5v_gpio else "✗ " +
         str([(a["net"], b["net"]) for a, b in n5v_gpio])))
    w("  [断言 S2] 5V_IN 与 GND  可被同一根针桥接的焊盘对：%d 组 %s"
      % (len(n5v_gnd), "→ 结构上不可能 ✓" if not n5v_gnd else "✗ " +
         str([(a["net"], b["net"]) for a, b in n5v_gnd])))
    w("")

    # ---------- 第 0c 遍：可行性不等式（与分配表无关，纯几何）----------
    w("---- 第 0c 遍：触点场可行性不等式（与分配表完全无关，是几何本身的性质）----")
    need_pad = TIP_D + 2 * max(TOL_X, TOL_Z)          # 可靠接触：针尖在最坏公差下仍完全落在焊盘内
    max_pad = PITCH - TIP_D                            # 不可链式桥接：一根针不得同时够到两个焊盘
    w("  [推导] 两个要求各自给焊盘直径一个边界：")
    w("    ① 可靠接触：(Ø焊盘 − Ø针尖)/2 ≥ 最坏公差  →  Ø焊盘 ≥ Ø针尖 + 2×公差 = %.2f + 2×%.2f = **%.2f mm**"
      % (TIP_D, max(TOL_X, TOL_Z), need_pad))
    w("    ② 不可链式桥接：(Ø焊盘 + Ø针尖)/2 ≤ 间距/2  →  Ø焊盘 ≤ 间距 − Ø针尖 = %.2f − %.2f = **%.2f mm**"
      % (PITCH, TIP_D, max_pad))
    if need_pad > max_pad:
        w("  → %.2f > %.2f，**两个要求互相矛盾，Ø焊盘无解**。" % (need_pad, max_pad))
        w("    现取 Ø%.1f：满足 ①（余量 %.2f mm），违反 ②（超出 %.2f mm）。"
          % (PAD_D, (PAD_D - need_pad), (PAD_D - max_pad)))
        w("    **结论：在 间距 %.2f ／ 针尖 Ø%.2f ／ 公差 ±%.2f 这三个数下，"
          "任何逐针分配方案都不可能同时做到『接触可靠』与『不会链式桥接』。**"
          % (PITCH, TIP_D, max(TOL_X, TOL_Z)))
        w("    这不是 P2 的毛病，是触点场三个几何参数本身的毛病；旧 2 行×8 列同样中招。")
        w("  三条出路（各自的数值门槛，我自己解的不等式）：")
        w("    a) 收紧定位公差到 ≤ (间距 − 2×Ø针尖)/2 = (%.2f − 2×%.2f)/2 = **%.3f mm**"
          " —— 比现有 ±%.2f 严 %.0f%%；须由 mech 任务重新给公差链。"
          % (PITCH, TIP_D, (PITCH - 2 * TIP_D) / 2, max(TOL_X, TOL_Z),
             100 * (1 - ((PITCH - 2 * TIP_D) / 2) / max(TOL_X, TOL_Z))))
        w("    b) 换更细针尖：Ø针尖 ≤ (间距 − 2×公差)/2 = (%.2f − 2×%.2f)/2 = **%.3f mm**"
          "（配 Ø焊盘 ∈ [%.2f, %.2f]）—— 选型约束，AS-26 一起关。"
          % (PITCH, max(TOL_X, TOL_Z), (PITCH - 2 * max(TOL_X, TOL_Z)) / 2,
             (PITCH - 2 * max(TOL_X, TOL_Z)) / 2 + 2 * max(TOL_X, TOL_Z), PITCH - (PITCH - 2 * max(TOL_X, TOL_Z)) / 2))
        w("    c) 放大间距：间距 ≥ 2×Ø针尖 + 2×公差 = 2×%.2f + 2×%.2f = **%.2f mm**"
          " —— 但触点板只有 %.2f × %.2f mm，4 列 × %.2f ＋ 焊盘 ＋ 边距放不下（见提案 allocation 第 4 节，我复核成立）。"
          % (TIP_D, max(TOL_X, TOL_Z), 2 * TIP_D + 2 * max(TOL_X, TOL_Z),
             PAD_BOARD_X[1] - PAD_BOARD_X[0], PAD_BOARD_Z[1] - PAD_BOARD_Z[0],
             2 * TIP_D + 2 * max(TOL_X, TOL_Z)))
        w("    d) 或者接受它，把闸门放到「上电前导通检验 ＋ 壳体防呆 AS-08」上，并**不再宣称"
          "『不依赖 AS-08』**。")
    else:
        w("  → %.2f ≤ %.2f，两个要求相容，Ø焊盘 ∈ [%.2f, %.2f]。" % (need_pad, max_pad, need_pad, max_pad))
    w("")

    # ---------- 第 0b 遍：链式桥接 F3（本脚本跑出来的新危险类，旧文档与提案都没有）----------
    w("---- 第 0b 遍：F3 链式桥接（解析）----")
    w("  旧分析（含提案 P2 的 F2/S2）只问「**一根**针会不会同时压住两个相邻焊盘」，")
    w("  答案是「5V 的邻居全是哑位，所以不可能」。但这只对了一半：")
    w("  **孤立哑焊盘本身是一块铜。** 它不连主机，可它把压在它身上的两根针连在一起。")
    w("  当整场沿 X（或 Z）平移 δ 且 %.2f − R < δ < R 时，**每一根针都同时压住相邻两个焊盘**，"
      % PITCH)
    w("  于是「焊盘—针—焊盘—针—…」交替成链，**整行（或整列）熔成一个网**。")
    chain_lo, chain_hi = PITCH - R_CONTACT, R_CONTACT
    if chain_lo >= chain_hi:
        w("  本场不成立：间距 %.2f ≥ 2R = %.2f，一根针压不到两个焊盘。" % (PITCH, R_BRIDGE_MAX))
    else:
        w("  成链窗口：δ ∈ (%.3f, %.3f) mm，宽 %.3f mm。阈值 %.3f mm = %.1f× 最坏公差 %.2f mm。"
          % (chain_lo, chain_hi, chain_hi - chain_lo, chain_lo, chain_lo / max(TOL_X, TOL_Z),
             max(TOL_X, TOL_Z)))
        w("  纯平移可达上限：−X %.2f / +X %.2f / ±Z %.2f mm —— 成链窗口**完全落在可达范围内**，"
          % (abs(REACH_DX[0]), REACH_DX[1], REACH_DZ[1]))
        w("  四个方向都够得到。")
        for axis, dd in (("X", (chain_lo + chain_hi) / 2), ("Z", (chain_lo + chain_hi) / 2)):
            dx, dz = (dd, 0.0) if axis == "X" else (0.0, dd)
            tq = transform_pads(pads, "e", D4[0][1], cx, cz, dx, dz)
            cs = contacts(pins, tq)
            low, allg, edges, adj = build_graph(pads, pins, cs, False)
            groups = defaultdict(set)
            for p in pads:
                groups[low.find("MPAD_%d" % p["idx"])].add(p["net"])
            for q in pins:
                if q["cls"] != "NOPIN":
                    groups[low.find("DPIN_%d" % q["idx"])].add("[针]" + q["net"])
            w("  沿 %s 平移 %+.3f mm 后，熔成的低阻分量：" % (axis, dd))
            for g, s in sorted(groups.items(), key=lambda kv: -len(kv[1])):
                if len(s) > 1:
                    w("      { %s }" % ", ".join(sorted(s)))
    w("")

    # ---------- 第 1 遍：离散命名错位穷举 ----------
    # 自由度：D4 八元素（4×4 方阵的完整对称群）× 格位偏移 ΔX/ΔZ ∈ {-3,-2.5,...,+3} 格
    # （含半格 → 覆盖「错位到一半时针尖同时搭到两个焊盘的瞬态」）× 开关开/合
    w("---- 第 1 遍：离散错位穷举（D4 八元素 × ΔX/ΔZ 各 −3…+3 格步长 0.5 格 × 开关开/合）----")
    steps = [i * 0.5 for i in range(-6, 7)]          # -3.0 … +3.0 格，步长 0.5 格
    transforms = D4 if geom == "4x4" else [t for t in D4 if t[0] in ("e", "rot180", "mirrorX", "mirrorZ")]
    if geom != "4x4":
        w("  （2 行×8 列不是方阵，其格点集只在 D2 = {e, rot180, mirrorX, mirrorZ} 下自映，"
          "故只枚举这 4 个；其余 4 个变换会让格点整体错位，退化为一般平移，由第 3 遍覆盖。）")
    memo = {}
    case_count = 0
    seen = {}      # (变换, 严重度, 代号) -> 最小位移的那条记录

    def run_pose(tname, tfun, dx, dz, tag):
        nonlocal case_count
        tq = transform_pads(pads, tname, tfun, cx, cz, dx, dz)
        cs = contacts(pins, tq)
        for sw in (False, True):
            case_count += 1
            key = (cs, sw)
            if key not in memo:
                memo[key] = evaluate(pads, pins, cs, sw)
            ev, powered = memo[key]
            for e in ev:
                rec = dict(e)
                rec["transform"] = tname
                rec["case"] = "%s %s ΔX=%+.3fmm ΔZ=%+.3fmm 开关%s" % (
                    tname, tag, dx, dz, "按下" if sw else "松开")
                rec["disp"] = math.hypot(dx, dz)
                all_events.append(rec)
                if e["sev"] in ("FATAL", "SEVERE", "LATENT", "WARN"):
                    k = (tname, e["sev"], e["code"])
                    if k not in seen or rec["disp"] < seen[k]["disp"]:
                        seen[k] = rec

    for tname, tfun in transforms:
        for sx in steps:
            for sz in steps:
                run_pose(tname, tfun, sx * PITCH, sz * PITCH, "(%+.1f格,%+.1f格)" % (sx, sz))
    w("  枚举位姿 %d 个（去重后不同接触态 %d 个）。" % (case_count, len(memo)))

    # ---------- 第 1b 遍：连续平移的连通性细扫（补 1 遍的格点采样）----------
    # 1 遍只走 0.5 格的格点；多跳通路可能在非格点位移上出现。这里在腔体可达范围
    # 外扩 1.5 倍后以 0.1 mm 步长全扫，仍带连通性判定。
    fine_lo_x, fine_hi_x = REACH_DX[0] * 1.5 - 1.0, REACH_DX[1] * 1.5 + 1.0
    fine_lo_z, fine_hi_z = REACH_DZ[0] * 1.5 - 1.0, REACH_DZ[1] * 1.5 + 1.0
    step = 0.1
    nfine = 0
    for tname, tfun in transforms:
        dx = fine_lo_x
        while dx <= fine_hi_x + 1e-9:
            dz = fine_lo_z
            while dz <= fine_hi_z + 1e-9:
                run_pose(tname, tfun, dx, dz, "[细扫]")
                nfine += 1
                dz += step
            dx += step
    w("  第 1b 遍细扫：步长 %.2f mm，ΔX ∈ [%+.2f, %+.2f]，ΔZ ∈ [%+.2f, %+.2f]，"
      "每变换 %d 个位姿。" % (step, fine_lo_x, fine_hi_x, fine_lo_z, fine_hi_z,
                              nfine // max(1, len(transforms))))
    w("  （细扫覆盖腔体可达范围的 1.5 倍 ＋1 mm，故「可达/不可达」的判断不受采样步长影响。）")
    w("")

    # ---------- 汇报 ----------
    w("  按变换分列的最严重事件（同一变换同一代号只留最小位移那条）：")
    for tname, _ in transforms:
        rows = [seen[k] for k in seen if k[0] == tname]
        if not rows:
            w("    [%-9s] 无 FATAL/SEVERE/LATENT/WARN 事件 ✓" % tname)
            continue
        rows.sort(key=lambda r: (["FATAL", "SEVERE", "LATENT", "WARN"].index(r["sev"]), r["disp"]))
        w("    [%-9s] %s" % (tname, PHYSICAL_NOTE.get(tname, "")))
        for r in rows:
            w("        [%-6s %-3s] %s" % (r["sev"], r["code"], r["msg"]))
            w("                最早于位移 %.3f mm：%s" % (r["disp"], r["case"]))
            if r.get("path"):
                w("                通路：%s" % r["path"])
            if r["sev"] in ("FATAL", "SEVERE"):
                fatal_events.append(r)
    w("")

    # ---------- 第 2 遍：整机错放 ----------
    w("---- 第 2 遍：整机级错放（绕 Y 180°、绕 Z 180°）----")
    # 绕 Y 轴 180°：(x,y,z) -> (-x, y, -z)，绕整机原点，不是绕场心
    my = [(-p["x"], -p["z"]) for p in pads]
    w("  绕 Y 轴 180°（前后翻转放入）：触点场映射到 X ∈ [%+.3f, %+.3f]，Z ∈ [%+.3f, %+.3f]"
      % (min(a for a, b in my), max(a for a, b in my), min(b for a, b in my), max(b for a, b in my)))
    cs = contacts(pins, my)
    w("    落在 +X 握把侧，底座该处无针。与底座针场的接触对数 = %d → %s"
      % (len(cs), "无任何电气接触 ✓" if not cs else "✗ 有接触！"))
    if cs:
        ev, _ = evaluate(pads, pins, cs, False)
        for e in ev:
            if e["sev"] in ("FATAL", "SEVERE"):
                r = dict(e, case="绕 Y 180°", disp=float("nan"))
                fatal_events.append(r)
                w("      [%s %s] %s" % (e["sev"], e["code"], e["msg"]))
    dmin = min(math.hypot(q["x"] - a, q["z"] - b) for q in pins for (a, b) in my)
    w("    最近的针-焊盘中心距 = %.3f mm（阈值 %.3f）→ 还差 %.3f mm" % (dmin, R_CONTACT, dmin - R_CONTACT))
    # 绕 Z 轴 180°：(x,y,z) -> (-x,-y,z)，触点面法向由 −Y 变 +Y
    w("  绕 Z 轴 180°（上下颠倒）：触点面法向由 −Y 变 +Y，朝向天花板，"
      "弹簧针在 −Y 侧顶不到它 → **无法配合**（机械上不成立）。")
    w("    保守起见，假设它仍能配合（即只取 XZ 投影 x→−x）时的接触对数：")
    mz = [(-p["x"], p["z"]) for p in pads]
    cs2 = contacts(pins, mz)
    w("      = %d → %s" % (len(cs2), "仍无接触 ✓" if not cs2 else "✗"))
    w("")

    # ---------- 第 3 遍：解析最小触发位移（连续平移，对角/多格/非整数全覆盖）----------
    w("---- 第 3 遍：解析最小触发位移（连续平移，穷举；正面关闭 G05）----")
    w("  方法：接触条件 |(q+δ) − T(p)| < R 是解析条件，故某类危险的最小触发位移")
    w("        = 该类网对的最小中心距 − R（单接触），或两圆盘交集的最小范数（桥接）。")
    w("        对角、多列、多行、非整数格位移、半格桥接**自动全覆盖**，不需要列个案。")
    is_5v_pin = lambda q: q["cls"] == "DOCK_5V_SRC"
    is_gnd_pin = lambda q: q["cls"] == "DOCK_GND_PIN"
    is_sw_pin = lambda q: q["cls"] == "DOCK_SWITCH"
    is_gpio_pad = lambda p: p["cls"].startswith("HOST_GPIO")
    is_5v_pad = lambda p: p["cls"] == "HOST_5V_IN"
    is_gnd_pad = lambda p: p["cls"] == "HOST_GND"

    hazard_rows = []
    for tname, tfun in transforms:
        f, fa = min_translation_single(pins, pads, is_5v_pin, is_gpio_pad, cx, cz, tname, tfun)
        s, sa = min_translation_single(pins, pads, is_gnd_pin, is_5v_pad, cx, cz, tname, tfun)
        sl, sla = min_translation_single(pins, pads, is_sw_pin, is_5v_pad, cx, cz, tname, tfun)
        f2, _ = min_translation_bridge(pins, pads, is_5v_pad, is_gpio_pad, cx, cz, tname, tfun)
        s2, _ = min_translation_bridge(pins, pads, is_5v_pad, is_gnd_pad, cx, cz, tname, tfun)
        gg, _ = min_translation_bridge(pins, pads, is_gpio_pad, is_gpio_pad, cx, cz, tname, tfun)
        hazard_rows.append((tname, f, s, sl, f2, s2, gg, fa, sa))

    def fmt(v):
        if v is None:
            return "不可能"
        return "%.3f (%.1f×)" % (v, v / max(TOL_X, TOL_Z))

    w("")
    w("  %-10s %-16s %-16s %-16s %-12s %-12s %-12s" %
      ("变换", "F: 5V针→GPIO焊盘", "S: GND针→5V焊盘", "s: 键针→5V焊盘",
       "F2桥接", "S2桥接", "GPIO-GPIO桥"))
    w("  " + "-" * 104)
    for (tname, f, s, sl, f2, s2, gg, fa, sa) in hazard_rows:
        w("  %-10s %-16s %-16s %-16s %-12s %-12s %-12s" %
          (tname, fmt(f), fmt(s), fmt(sl), fmt(f2), fmt(s2), fmt(gg)))
    w("  （括号内为相对最坏定位公差 %.2f mm 的倍数；「不可能」= 该类网对在几何上不存在）" % max(TOL_X, TOL_Z))
    w("")

    # ---------- 第 4 遍：可达性（腔体最坏位姿搜索）----------
    w("---- 第 4 遍：可达性 —— 腔体到底给不给得了这么大位移 ----")
    w("  假设模块壳体完全不存在（AS-08 一级防呆彻底失效），裸触点板在落入槽模块条带空腔里")
    w("  任意平移并绕 Y 偏航 ±20°，只要四个板角还在腔内就算合法。")
    w("  注意：D4 那七个变换是 **EDA 封装错放**，不是实物错放。实物触点板转不过去（J3 偏心 3.660 mm）。")
    for (tname, tfun) in transforms:
        d5g, pose5g = reachable_min_distance(pins, pads, is_5v_pin, is_gpio_pad, cx, cz, tname, tfun)
        dgn, posegn = reachable_min_distance(pins, pads, is_gnd_pin, is_5v_pad, cx, cz, tname, tfun)
        def verdict(d):
            if d is None:
                return "该类不存在"
            return ("**可达 → 会接触**" if d < R_CONTACT
                    else "不可达（还差 %.3f mm）" % (d - R_CONTACT))
        w("  [%s] F：5V 针到最近 GPIO 焊盘的腔内可达最小中心距 = %s  → %s"
          % (tname, "n/a" if d5g is None else "%.3f mm" % d5g, verdict(d5g)))
        if pose5g:
            w("        最坏位姿 yaw=%.1f°, ΔX=%+.3f, ΔZ=%+.3f" % pose5g)
        w("  [%s] S：GND 针到 5V_IN 焊盘的腔内可达最小中心距 = %s  → %s"
          % (tname, "n/a" if dgn is None else "%.3f mm" % dgn, verdict(dgn)))
        if d5g is not None and d5g < R_CONTACT:
            fatal_events.append(dict(sev="FATAL", code="R-F", transform=tname,
                                     case="%s（腔内可达，%s）" % (tname, PHYSICAL_NOTE.get(tname, "")),
                                     disp=0.0,
                                     msg="底座 5V 针在腔体允许的位姿内就能碰到主机 GPIO 焊盘"
                                         "（可达最小中心距 %.3f < 阈值 %.3f）" % (d5g, R_CONTACT)))
        if dgn is not None and dgn < R_CONTACT:
            fatal_events.append(dict(sev="SEVERE", code="R-S", transform=tname,
                                     case="%s（腔内可达，%s）" % (tname, PHYSICAL_NOTE.get(tname, "")),
                                     disp=0.0,
                                     msg="底座 GND 针在腔体内就能碰到主机 5V_IN 焊盘（G04 成立）"))
    w("")

    # ---------- 第 5 遍：GPIO-GPIO 桥接的可达性（判据 4）----------
    w("---- 第 5 遍：判据 4 —— 两根 GPIO 互相短接的可达性 ----")
    dgg, _ = min_translation_bridge(pins, pads, is_gpio_pad, is_gpio_pad, cx, cz, "e", D4[0][1])
    if dgg is None:
        w("  结构上不可能（没有任何两个 GPIO 焊盘中心距 < 2R）。")
    else:
        maxreach = math.hypot(max(abs(REACH_DX[0]), abs(REACH_DX[1])),
                              max(abs(REACH_DZ[0]), abs(REACH_DZ[1])))
        w("  正确封装（e）下最小触发位移 = %.3f mm（%.1f× 最坏公差 %.2f）；"
          "腔体纯平移最大位移 = %.3f mm" % (dgg, dgg / max(TOL_X, TOL_Z), max(TOL_X, TOL_Z), maxreach))
        w("  → %s" % ("**可达**：AS-08 壳体防呆失效时，一根针能同时压住两个相邻按键焊盘，"
                      "把两根主机 GPIO 短在一起。" if dgg < maxreach else "不可达。"))
        w("  后果：两根都配成带上拉的输入时只是「两键连动」，无损；**但只要固件把其中任一根"
          "配成输出（或 strapping 期间被驱动），就是推挽对推**。AS-15「11 根均可配为带上拉输入"
          "且无 strapping 副作用」至今未关闭 → 这条不能判为无损，只能判为「待 AS-15 关闭」。")
    w("")

    return out, fatal_events, struct_fail, all_events


def main():
    verbose = "--verbose" in sys.argv
    run_all = "--all" in sys.argv
    allocs = [ACTIVE_ALLOCATION]
    if run_all:
        allocs = [ALLOC_P2, ALLOC_P3, ALLOC_NAIVE_4x4, ALLOC_OLD_2x8]

    print(__doc__.split("用法：")[0].strip())
    print(PROVENANCE)

    rc = 0
    summary = []
    for alloc in allocs:
        out, fatals, struct_fail, allev = analyze_allocation(alloc, verbose)
        print("\n".join(out))
        # 汇总：按「正确封装（e）」与「EDA 封装错放（其余 D4）」分类判定
        uniq = {}
        for f in fatals:
            uniq.setdefault((f.get("transform", "?"), f["sev"], f["code"], f["msg"]), f)
        ident = {k: v for k, v in uniq.items() if k[0] in ("e", "mirrorD1", "?")}
        ident = {k: v for k, v in uniq.items() if k[0] == "e"}
        d4 = {k: v for k, v in uniq.items() if k[0] != "e"}

        print("---- 判定 ----")
        if struct_fail:
            print("  结构性断言失败 %d 条 → 退出码 2" % struct_fail)
            rc = max(rc, 2)

        print("  【类别 A：封装正确，只错位】—— 平移任意方向任意大小 ＋ 偏航 ±20°，含对角、多格、半格桥接")
        if not ident:
            print("    没有任何会打坏主机的事件。✓")
        else:
            for k in sorted(ident, key=lambda k: k[1] != "FATAL"):
                f = ident[k]
                print("    [%s %s] %s" % (f["sev"], f["code"], f["msg"]))
                print("        情形：%s" % f["case"])
                if f.get("path"):
                    print("        通路：%s" % f["path"])
            rc = max(rc, 1)

        print("  【类别 B：EDA 里 J2 封装被转/被镜像（实物转不过去，但 EDA 挡不住）】")
        if not d4:
            print("    没有任何会打坏主机的事件。✓")
        else:
            nf = sum(1 for k in d4 if k[1] == "FATAL")
            ns = sum(1 for k in d4 if k[1] == "SEVERE")
            print("    会打坏主机的事件：FATAL %d 起，SEVERE(G04 类) %d 起" % (nf, ns))
            for k in sorted(d4, key=lambda k: (k[1] != "FATAL", k[0])):
                f = d4[k]
                print("    [%-6s %-3s] %-9s %s" % (f["sev"], f["code"], k[0], f["msg"]))
                print("        情形：%s" % f["case"])
                if f.get("path"):
                    print("        通路：%s" % f["path"])
            rc = max(rc, 1)
        summary.append((alloc["name"], len(ident), len(d4)))
        print("")

    print("=" * 78)
    print("总结")
    print("  %-46s %10s %10s" % ("分配方案", "类别A(错位)", "类别B(封装错放)"))
    for name, na, nb in summary:
        print("  %-46s %10d %10d" % (name[:46], na, nb))
    print("")
    print("  类别 A = 封装正确、只发生错位（平移任意方向任意大小、偏航、对角、多格、半格桥接）。")
    print("  类别 B = EDA 里 J2 封装被旋转或镜像放置（实物做不到，EDA 挡不住；闸门只能是上电前导通检验）。")
    print("退出码 %d" % rc)
    return rc


if __name__ == "__main__":
    sys.exit(main())
