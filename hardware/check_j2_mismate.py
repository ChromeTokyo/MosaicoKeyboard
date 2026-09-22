#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 提案 · 未冻结 · 由 Claude 主控（claude-opus-5）裁定起草 · 待 Chrome 采纳、Hiro／Grok 复核
#
# check_j2_mismate.py —— J2 触点场错位的穷举安全判定（4 行 × 4 列，16 针）
#
# 为什么存在
# ----------
#   2026-09-22 把触点场由 2 行 × 8 列改成 4 行 × 4 列。几何上 4×4 是唯一解，但它把
#   ICD 第 3.2 节的逐针表和第 3.3 节「二级电气分配」的全部结论一次性作废：原分析建立在
#   「只有两行、行 A 屏侧行 B 背侧」上，谁挨着谁全变了。裁定把这条记为
#   「本次改动里唯一可能打坏主机的一条」。
#
#   在此之前仓库里判「错位安不安全」的只有两样，两样在结构上都看不见真正的机理：
#     · module_board.scad [检查 6][检查 7]：拿定位公差 0.45 比半间距 1.27，一句 OK。
#       它判的是**单根针的落点**，而且用的是「针尖整体落进焊盘」的 0.55 mm 判据。
#     · ICD 第 3.3 节那张四行表：只列了 X±1 列、错一行、绕 Y 180° 三种情形。
#       那是**举例**，不是枚举 —— Grok G05 指的正是这一条。
#
#   本脚本抓的是那两样都抓不到的一类错误：
#
#     焊盘 Ø2.0、针尖 Ø0.9、间距 2.54  ⇒  搭接阈值 R = (2.0+0.9)/2 = 1.45 mm > 半间距 1.27 mm
#
#   所以在半格错位时**一根针同时压住相邻两块铜**（各重叠 0.18 mm）。一块铜不是绝缘体，
#   它是一段没有端点的导线，不终止链条只延长链条：
#
#       焊盘 → 针 → 焊盘 → 针 → 焊盘 → …
#
#   X 半格错位时，**一整行 4 块焊盘会被 3 根针串成一个电节点**；Z 半格时整列如此。
#   「逐针对照表」（一针配一焊盘）在结构上看不见这类通路。本脚本把 16 根针、16 块焊盘、
#   主机 H2 侧、底座两条轨全部建成图节点，用并查集求连通分量，多跳通路自动浮现。
#
#   这条机理直接推翻了「用孤立哑焊盘做护城河」这一类提案：孤立铜恰恰是最坏的填充物，
#   它把 5 V 原样传给下一站；而 GND 焊盘是低阻节点，会把 5 V 钳到地。**对链式通路而言，
#   GND 焊盘严格优于孤立铜，与单跳直觉相反。**
#
# 判据（只判「通不通」，不判「多少毫安才烧」）
# --------------------------------------------
#   F  致命：某个 5 V 源与某根主机 GPIO 连通，且该分量内**没有地** → 未钳位的 5 V 进 GPIO
#   S  电源短路：5 V 与地连通（含 Grok G04：主机 5V_IN 对地）→ 电位塌陷，GPIO 被拉低而不是被抬高
#   G  GPIO 互短：键位错置／多键并联，功能错误，不致命，但必须报
#
#   本脚本**不判**器件会不会烧：这颗 SoC（BSP 里叫 esp32s31）的绝对最大额定与最大注入电流
#   在仓库内没有数据手册，unknown。所以全文不出现「无损」二字，只给「最小触发位移」
#   与「该位移是否落在可达包络内」。
#
# 用法
# ----
#   python3 hardware/check_j2_mismate.py              判冻结方案；退出码 0 = 通过
#   python3 hardware/check_j2_mismate.py --all        连同被否决的三版一起跑（复核裁定用）
#   python3 hardware/check_j2_mismate.py --tip-d 0.6  针头形状敏感性（AS-31-mm-5 未定形状）
#   python3 hardware/check_j2_mismate.py --verbose    打印全部事件与通路
#
#   **任何人改动 J2 逐针分配表，必须跑这个脚本，且必须 0 起 F。**
import argparse, math, sys

# ---------------------------------------------------------------------------
# §0 几何常量
#
#   全部取自本人实跑 openscad 的 ECHO，不引任何转述：
#     openscad -o /tmp/x.stl <origin/claude/design-d/mech-module:mechanical/module-board/module_board.scad>
#     openscad -o /tmp/y.stl <origin/claude/design-d/mech-dock:mechanical/dock-shell/dock_shell.scad>
#   两份的列 X／行 Z／配合面 Y 逐值相同。
#
#   ⚠ module_board.scad 行尾注释里的 −32.405（DOCK_PIN_FIELD_X0）、+2.95（Z0）、
#     −28.595（PAD_CENTER_X）、−23.095（PAD_X_MAX）**全是修订 d 之前的过期值**，
#     与 ECHO 差 2.0／0.2 mm。dock_shell.scad 的 DOCK_FIELD_XC 旁注同样过期。
#     **只信 ECHO，不要照注释算。** 本节的值我逐条与 ECHO 对过。
# ---------------------------------------------------------------------------
PITCH = 2.54
COL_X = [-34.405, -31.865, -29.325, -26.785]   # 列 1..4；列 4 最靠 Mosaico 中央
ROW_Z = [  2.750,   0.210,  -2.330,  -4.870]   # 行 A..D；行 A 在 +Z 屏侧
PAD_D_DEFAULT = 2.0     # DOCK_PAD_D        module_board.scad:123
TIP_D_DEFAULT = 0.9     # DOCK_PIN_TIP_D    module_board.scad:129
TOL_AXIS      = 0.45    # DOCK_X_TOL = DOCK_Z_TOL  module_board.scad:144-145

# 触点板与落入槽模块条带（ECHO）
BOARD_X = (-36.095, -25.095)     # 长 11.00
BOARD_Z = ( -6.460,   4.340)     # 宽 10.80
BAY_X   = (-37.845, -22.945)     # ICD-CONTRACT|BAY_X_LO / BAY_X_HI
BAY_Z   = ( -8.010,   5.890)

COLN = ["列1", "列2", "列3", "列4"]
ROWN = ["行A", "行B", "行C", "行D"]

# ---------------------------------------------------------------------------
# §1 可达包络 —— 「错位最多能有多大」，四级，全部由上面的数推出，不外部引用
# ---------------------------------------------------------------------------
def envelopes():
    # δ = 针场相对焊盘场的平移。触点板在腔体内移动 s，则针相对焊盘移动 −s。
    dx_lo = -(BAY_X[1] - BOARD_X[1]); dx_hi = -(BAY_X[0] - BOARD_X[0])
    dz_lo = -(BAY_Z[1] - BOARD_Z[1]); dz_hi = -(BAY_Z[0] - BOARD_Z[0])
    return {
        # 名称: (每轴上限, 最坏方向 ‖δ‖, 说明)
        "E1 设计公差 DOCK_*_TOL": (TOL_AXIS, TOL_AXIS * math.sqrt(2),
            "module_board.scad:144-145。**这是半程链**：只覆盖底座壳↔模块壳足↔触点板槽。"),
        "E2 弹簧针小板全程链 a..h": (1.192, 1.192,
            "pogo 小板任务的 8 环链（同 Gerber 0.10 ＋ 铣边 0.15 ＋ 滑配 0.15 ×3 ＋ 板槽 0.20 ＋ 转角 0.142）。"),
        "E3 全程链含前后壳分型 j": (1.392, 1.392,
            "再加 CLR_PRINT 0.20：落入槽 X/Z 定位壁分属前后两个打印件（布尔实测）。"),
        "E4 裸触点板在腔体内": (max(abs(dx_lo), dx_hi), math.hypot(max(abs(dx_lo), dx_hi), max(abs(dz_lo), dz_hi)),
            "假设模块壳导向完全失效（AS-08 一级防呆失效）：δx∈[%+.3f,%+.3f] δz∈[%+.3f,%+.3f]"
            % (dx_lo, dx_hi, dz_lo, dz_hi)),
    }, (dx_lo, dx_hi, dz_lo, dz_hi)

# ---------------------------------------------------------------------------
# §2 网名 → 主机侧归宿
#     KEY_* → H2 针 → GPIO，逐条抄自 PINMAP.md 第 2 节（修订 b），本次重排**一个字没动**。
# ---------------------------------------------------------------------------
KEY_GPIO = {
    "KEY_UP":(1,"GPIO55"), "KEY_DOWN":(3,"GPIO19"), "KEY_LEFT":(5,"GPIO18"),
    "KEY_RIGHT":(7,"GPIO17"), "KEY_L":(9,"GPIO16"), "KEY_R":(11,"GPIO15"),
    "KEY_A":(2,"GPIO53"), "KEY_B":(4,"GPIO48"), "KEY_X":(6,"GPIO13"), "KEY_Y":(8,"GPIO12"),
}
# 旧 2×8 表里进过触点场的两根，**无串阻直通 GPIO**，本裁定已把它们移出触点场
NOSER_GPIO = {"DOCK_SDA":(16,"GPIO0"), "DOCK_SCL":(14,"GPIO1")}

# ---------------------------------------------------------------------------
# §3 候选分配表。每张表 4 行（A..D）× 4 列（1..4）。
#     DUMMY  = 模块侧孤立焊盘（有铜、不连任何网、不打过孔）；底座侧照装针，经 1 MΩ 接地
#     NOCU   = 模块侧**整片无铜**（裸阻焊）；底座侧照装针（保住 16×0.6 N 压力与对称分布）
# ---------------------------------------------------------------------------
SCHEMES = {
"frozen": ("【本裁定冻结】GND 环抱 5V：5V×2 ＋ GND×4 ＋ 10 键，SDA/SCL 移出触点场", [
    ["DOCK_5V",  "DOCK_GND", "KEY_UP",    "KEY_A"],
    ["DOCK_5V",  "DOCK_GND", "KEY_DOWN",  "KEY_B"],
    ["DOCK_GND", "DOCK_GND", "KEY_LEFT",  "KEY_X"],
    ["KEY_L",    "KEY_R",    "KEY_RIGHT", "KEY_Y"],
]),
"P2": ("【否决】角位 5V ＋ 孤立哑焊盘护城河：5V×1 ＋ GND×2 ＋ 9 键 ＋ 哑位×4", [
    ["DOCK_GND", "KEY_UP",    "DUMMY",  "DOCK_5V"],
    ["KEY_L",    "KEY_DOWN",  "DUMMY",  "DUMMY"],
    ["KEY_A",    "KEY_LEFT",  "KEY_B",  "KEY_X"],
    ["DOCK_GND", "KEY_RIGHT", "KEY_Y",  "DUMMY"],
]),
"P2_nocu": ("【对照】同 P2，但哑位改为模块侧整片无铜（裸阻焊），底座照装针", [
    ["DOCK_GND", "KEY_UP",    "NOCU",   "DOCK_5V"],
    ["KEY_L",    "KEY_DOWN",  "NOCU",   "NOCU"],
    ["KEY_A",    "KEY_LEFT",  "KEY_B",  "KEY_X"],
    ["DOCK_GND", "KEY_RIGHT", "KEY_Y",  "NOCU"],
]),
"S2": ("【未采纳】可制造优先：5V×2 ＋ GND×4 ＋ 10 键，5V 在 −X/−Z 双外角", [
    ["KEY_L",    "KEY_R",     "KEY_B",    "KEY_A"],
    ["KEY_LEFT", "KEY_RIGHT", "KEY_Y",    "KEY_X"],
    ["DOCK_GND", "DOCK_GND",  "DOCK_GND", "KEY_DOWN"],
    ["DOCK_5V",  "DOCK_5V",   "DOCK_GND", "KEY_UP"],
]),
"fallback8": ("【预置回退表】5V×2 ＋ GND×2 ＋ 无铜隔离×4 ＋ 8 键（砍 KEY_L/KEY_R）：连 G04 一并消掉", [
    ["DOCK_5V", "NOCU",     "KEY_UP",    "KEY_A"],
    ["DOCK_5V", "NOCU",     "KEY_DOWN",  "KEY_B"],
    ["NOCU",    "NOCU",     "KEY_LEFT",  "KEY_X"],
    ["DOCK_GND","DOCK_GND", "KEY_RIGHT", "KEY_Y"],
]),
"baseline": ("【对照基线】ICD 3.2 现行 2×8 表朴素折成 4×4（列 1..4 给行 A/B，列 5..8 给行 C/D）", [
    ["DOCK_5V", "DOCK_GND", "KEY_UP",   "KEY_LEFT"],
    ["DOCK_5V", "DOCK_GND", "KEY_DOWN", "KEY_RIGHT"],
    ["KEY_L",   "KEY_A",    "KEY_X",    "DOCK_SDA"],
    ["KEY_R",   "KEY_B",    "KEY_Y",    "DOCK_SCL"],
]),
}

# ---------------------------------------------------------------------------
# §4 D4：正方形格点场的对称群。4×4 方阵在 D4 下映回自身 —— 2 行×8 列不会，
#     **这是改成 4×4 新增的一整类风险**。实物旋转/镜像做不到（触点面会朝上；
#     且 J3 落脚线偏心 3.660 mm，转过去焊不上），但 **EDA 里 J2 封装被转/被镜像是真实可发生的**，
#     而 EDA 挡不住。本项目有 D-009/D-009-R 的镜像前科。
# ---------------------------------------------------------------------------
D4 = {
    "e":    lambda c, r: (c, r),
    "R90":  lambda c, r: (r, 3 - c),
    "R180": lambda c, r: (3 - c, 3 - r),
    "R270": lambda c, r: (3 - r, c),
    "MX":   lambda c, r: (3 - c, r),
    "MZ":   lambda c, r: (c, 3 - r),
    "MD1":  lambda c, r: (r, c),
    "MD2":  lambda c, r: (3 - r, 3 - c),
}

class DSU:
    def __init__(self): self.p = {}
    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]; x = self.p[x]
        return x
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb: self.p[ra] = rb

# ---------------------------------------------------------------------------
# §5 电气判定：给定接触集合，建图求连通分量
#     pad_at(c,r)  = 模块侧焊盘的网（受 D4 置换影响：EDA 误放的是模块板封装）
#     pin_net(c,r) = 底座侧弹簧针的网（底座主板按名义表装配，不受该置换影响）
# ---------------------------------------------------------------------------
def evaluate(grid, contacts, transform="e", switches_closed=False):
    T = D4[transform]
    def pad_net(c, r):
        tc, tr = T(c, r); return grid[tr][tc]
    def pin_net(c, r):
        return grid[r][c]

    d = DSU(); NOTE = {}
    H5, HG, D5, DG = "主机 5V_IN", "主机 GND", "底座 5V 轨", "底座 GND 轨"
    for n in (H5, HG, D5, DG): d.find(n)

    pad_exists = {}
    for c in range(4):
        for r in range(4):
            n = pad_net(c, r)
            if n == "NOCU":            # 无铜：模块侧根本没有这个节点
                pad_exists[(c, r)] = False; continue
            pad_exists[(c, r)] = True
            node = ("pad", c, r)
            if   n == "DOCK_5V":  d.union(node, H5);  NOTE[node] = "J1 pin17 纯铜（硬约束 1 禁串联器件）"
            elif n == "DOCK_GND": d.union(node, HG);  NOTE[node] = "J1 pin20 纯铜"
            elif n in KEY_GPIO:   d.union(node, "主机 " + KEY_GPIO[n][1]); NOTE[node] = "经 R_S 1kΩ 到 H2 pin%d" % KEY_GPIO[n][0]
            elif n in NOSER_GPIO: d.union(node, "主机 " + NOSER_GPIO[n][1]); NOTE[node] = "R_LINK 0Ω，**无串阻**直通"
            # DUMMY：孤立铜，节点存在但不并任何网 —— 它正是链条的延长段
    for c in range(4):
        for r in range(4):
            n = pin_net(c, r); node = ("pin", c, r)
            d.find(node)
            if   n == "DOCK_5V":  d.union(node, D5)
            elif n == "DOCK_GND": d.union(node, DG)
            elif n in KEY_GPIO:
                if switches_closed: d.union(node, DG)      # 轻触开关另一端接 DOCK_GND
            # DUMMY/NOCU 的针经 1 MΩ 泄放接地：不是低阻通路，**不并**（5 µA 级，见 §8 说明）
            # DOCK_SDA/SCL 的底座侧唯一消费者 U_FG 是 dnp:true，悬空，不并
    for (pc, pr, dc, dr) in contacts:
        if pad_exists.get((dc, dr)): d.union(("pin", pc, pr), ("pad", dc, dr))

    comp = {}
    for x in list(d.p): comp.setdefault(d.find(x), []).append(x)

    F, S, G = [], [], []
    for members in comp.values():
        ms = set(members)
        gnd = (HG in ms) or (DG in ms)
        srcs = [s for s in (H5, D5) if s in ms]
        gpios = sorted(m for m in ms if isinstance(m, str) and m.startswith("主机 GPIO"))
        if srcs and gpios:
            (F if not gnd else S).append((srcs, gpios, ms))
        elif srcs and gnd:
            S.append((srcs, [], ms))
        if len(gpios) >= 2: G.append(gpios)
    return F, S, G

# ---------------------------------------------------------------------------
# §6 平移维的**完备**约化
#     针场与焊盘场是同一个间距 2.54 的 4×4 正交格，所以「哪根针压哪块盘」只取决于
#     格差 (u,v) 与连续位移 δ 的关系：  接触 ⟺ |δ − L(u,v)| < R，  L(u,v) = (u·P, −v·P)
#     即 δ 平面上以 7×7 = 49 个格点为心、半径 R 的等半径圆盘族。接触集合 S(δ) 只在这些
#     圆的边界上变化，因此**同一个 S 对应同一个电气结论**，枚举 S 的全部取值就等于把
#     整个 R² 平面枚举完 —— 没有「步长」这个概念，对角、错多列、非整数格位移全部自动覆盖。
# ---------------------------------------------------------------------------
def offsets(): return [(u, v) for u in range(-3, 4) for v in range(-3, 4)]
def Lpt(u, v): return (u * PITCH, -v * PITCH)

def prove_cases(R, out):
    offs = offsets()
    # 引理 1：任意两格点若能同时落在半径 R 内，中心距须 ≤ 2R
    adj = []
    for i, a in enumerate(offs):
        for b in offs[i + 1:]:
            if math.dist(Lpt(*a), Lpt(*b)) <= 2 * R + 1e-9: adj.append((a, b))
    # 引理 2：不存在三个格点两两 ≤ 2R  ⇒ |S| ≤ 2
    bad = 0
    for i, a in enumerate(offs):
        for j in range(i + 1, len(offs)):
            b = offs[j]
            if math.dist(Lpt(*a), Lpt(*b)) > 2 * R + 1e-9: continue
            for k in range(j + 1, len(offs)):
                c = offs[k]
                if (math.dist(Lpt(*a), Lpt(*c)) <= 2 * R + 1e-9 and
                    math.dist(Lpt(*b), Lpt(*c)) <= 2 * R + 1e-9): bad += 1
    diag = math.hypot(PITCH, PITCH)
    out("  引理 1：相邻格点距 %.3f ≤ 2R = %.3f（圆相交）；对角格点距 %.4f %s 2R（%s）"
        % (PITCH, 2 * R, diag, "≤" if diag <= 2 * R else ">", "相交" if diag <= 2 * R else "不相交"))
    out("  引理 2：穷举 C(49,3) = 18424 个三元组，两两距离全 ≤ 2R 的共 %d 个 ⇒ |S| ≤ %d"
        % (bad, 2 if bad == 0 else 3))
    if bad: out("  ⚠ |S| 可能 > 2，本脚本的情形表在此 R 下**不完备**，结论不得采信。")
    cases = [frozenset([g]) for g in offs] + [frozenset([a, b]) for a, b in adj]
    out("  情形表：单点 %d ＋ 桥接对 %d = **%d 个完备情形**（外加「全脱开」）"
        % (len(offs), len(adj), len(cases)))
    return cases, adj

def min_norm_for(case, R, cand):
    """该情形区域内到原点的最小 ‖δ‖（区域 = 落在 case 里的圆内、其余圆外）。"""
    best = None
    for p in cand:
        S = frozenset(g for g in offsets() if math.dist(p, Lpt(*g)) < R - 1e-7)
        if S == case:
            n = math.hypot(*p)
            if best is None or n < best: best = n
    return best

def candidates(R):
    """解析候选点：原点、各圆到原点的最近点、全部圆–圆交点，每个再向 8 方向推 ε。"""
    pts, offs = [(0.0, 0.0)], offsets()
    for g in offs:
        L = Lpt(*g); n = math.hypot(*L)
        pts.append((0.0, 0.0) if n <= R else (L[0] * (1 - R / n), L[1] * (1 - R / n)))
    for i, a in enumerate(offs):
        for b in offs[i + 1:]:
            A, B = Lpt(*a), Lpt(*b); dsq = math.dist(A, B)
            if dsq > 2 * R or dsq < 1e-9: continue
            mx, my = (A[0] + B[0]) / 2, (A[1] + B[1]) / 2
            h = math.sqrt(max(R * R - (dsq / 2) ** 2, 0.0))
            ux, uy = -(B[1] - A[1]) / dsq, (B[0] - A[0]) / dsq
            pts += [(mx + h * ux, my + h * uy), (mx - h * ux, my - h * uy)]
            pts.append((mx, my))
    eps = 1e-4; out = []
    for p in pts:
        out.append(p)
        for dx in (-eps, 0, eps):
            for dy in (-eps, 0, eps): out.append((p[0] + dx, p[1] + dy))
    return out

def contacts_for(S):
    """把格差集合 S 展开成实际的 (针列,针行,盘列,盘行) 接触对。"""
    out = []
    for (u, v) in S:
        for c in range(4):
            for r in range(4):
                if 0 <= c + u < 4 and 0 <= r + v < 4: out.append((c, r, c + u, r + v))
    return out

def reachable(nrm, dxlo, dxhi, dzlo, dzhi):
    """该 ‖δ‖ 是否落在腔体包络内（取最坏方向，保守）。"""
    return nrm <= math.hypot(max(abs(dxlo), dxhi), max(abs(dzlo), dzhi)) + 1e-9

# ---------------------------------------------------------------------------
# §7 结构不变量 —— 安全的**原因**，不是数值巧合。改表时这几条最先炸。
# ---------------------------------------------------------------------------
def invariants(grid, out):
    ok = True
    p5 = [(c, r) for c in range(4) for r in range(4) if grid[r][c] == "DOCK_5V"]
    # NOCU 与场外等价：模块侧没有这块铜，链条到此为止（P2 的 DUMMY 有铜，不等价）
    pw = {"DOCK_5V", "DOCK_GND", "NOCU"}
    # I1 链式安全：5V 焊盘的**轴向**邻居必须全是 GND 或场外。
    #    桥接只发生在轴向（对角圆盘不交，见 §6 引理 1），所以链条是格图上的车步。
    #    轴向邻居全是 GND ⇒ 任何离开 5V 的链条**第一跳就撞上地**，5V 被钳住。
    for (c, r) in p5:
        for (dc, dr) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nc, nr = c + dc, r + dr
            if not (0 <= nc < 4 and 0 <= nr < 4): continue
            if grid[nr][nc] not in pw:
                out("  [I1] **失败** 5V(%s,%s) 的轴向邻居 (%s,%s) 是 %s，既不是电源网也不是无铜位 —— 链式通路会把 5V 直送 GPIO"
                    % (COLN[c], ROWN[r], COLN[nc], ROWN[nr], grid[nr][nc])); ok = False
    # I2 单步安全：5V 焊盘的 8 邻域（含对角）必须全是电源网或场外。
    #    整格错位时针直接落到邻格，对角也算。
    for (c, r) in p5:
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if dc == dr == 0: continue
                nc, nr = c + dc, r + dr
                if not (0 <= nc < 4 and 0 <= nr < 4): continue
                if grid[nr][nc] not in pw:
                    out("  [I2] **失败** 5V(%s,%s) 的 8 邻域 (%s,%s) 是 %s" %
                        (COLN[c], ROWN[r], COLN[nc], ROWN[nr], grid[nr][nc])); ok = False
    # I3 场内不得出现 H2 pin18（5V_OUT）。结构性判据，与 δ 无关。
    flat = [grid[r][c] for c in range(4) for r in range(4)]
    if any("5V_OUT" in str(n) for n in flat):
        out("  [I3] **失败** 触点场内出现 5V_OUT（H2 pin18），违反硬约束 2"); ok = False
    # I4 无串阻的 GPIO 通路（SDA/SCL）不得进入触点场。
    bad = [n for n in flat if n in NOSER_GPIO]
    if bad:
        out("  [I4] **失败** 无串阻直通 GPIO 的网进入触点场：%s" % sorted(set(bad))); ok = False
    # I5 哑位若保留铜，则它是链条延长段，等于没有护城河。
    if "DUMMY" in flat:
        out("  [I5] **失败** 表中存在 DUMMY（孤立焊盘，有铜）。孤立铜不终止链条只延长链条，"
            "必须改成 NOCU（整片无铜）或 DOCK_GND。"); ok = False
    # I6 GND 图样在 D4 下不得自映 —— 这样「封装被转过/镜像过」肉眼与 DRC 都看得出来。
    gpat = frozenset((c, r) for c in range(4) for r in range(4) if grid[r][c] == "DOCK_GND")
    self_map = [k for k, T in D4.items() if k != "e" and
                frozenset(T(c, r) for (c, r) in gpat) == gpat]
    if self_map:
        out("  [I6] 注意 GND 图样在 %s 下自映 —— 目视判不出封装被转/被镜像。" % ",".join(self_map))
    else:
        out("  [I6] GND 图样在全部 7 个非恒等 D4 元素下都落到别处 ⇒ 「哪几个焊盘接地」一眼可判封装朝向 -> OK")
    if ok: out("  [I1][I2][I3][I4][I5] 全部通过")
    return ok

# ---------------------------------------------------------------------------
def run(name, R, verbose, out):
    title, grid = SCHEMES[name]
    env, (dxlo, dxhi, dzlo, dzhi) = envelopes()
    out("\n" + "=" * 78)
    out("方案 %s —— %s" % (name, title))
    out("=" * 78)
    out("  版图（自 +Y 俯视；+X 向右 = 朝 Mosaico 中央，行 A 在 +Z 屏侧）")
    out("        " + "".join("%-12s" % c for c in COLN))
    for r in range(4):
        out("  %s  " % ROWN[r] + "".join("%-12s" % grid[r][c] for c in range(4)))
    out("\n  § 结构不变量")
    inv_ok = invariants(grid, out)

    cases, _ = prove_cases(R, out) if verbose else (prove_cases(R, lambda s: None)[0], None)
    cand = candidates(R)
    norms = {c: min_norm_for(c, R, cand) for c in cases}

    worst = {"F": None, "S": None}
    events = {"F": [], "S": []}
    gcount = 0
    for tname in D4:
        for sw in (False, True):
            for case in cases:
                n = norms[case]
                if n is None: continue
                F, S, G = evaluate(grid, contacts_for(case), tname, sw)
                gcount += len(G)
                for kind, lst in (("F", F), ("S", S)):
                    if not lst: continue
                    rec = (n, tname, sw, case, lst)
                    events[kind].append(rec)
                    if tname == "e" and (worst[kind] is None or n < worst[kind]): worst[kind] = n

    def summarize(kind, label):
        ident = [e for e in events[kind] if e[1] == "e"]
        reach = [e for e in ident if reachable(e[0], dxlo, dxhi, dzlo, dzhi)]
        mn = min((e[0] for e in ident), default=None)
        out("\n  § 判据 %s —— %s" % (kind, label))
        if mn is None:
            out("    正确朝向：**0 起**（任何平移下都不出现）")
        else:
            out("    正确朝向：共 %d 个情形命中；**最小触发位移 ‖δ‖ = %.3f mm**" % (len(ident), mn))
            for nm, (ax, dg, _) in env.items():
                out("      对 %-24s（最坏 %.3f mm）：%s，余量 %.2f×"
                    % (nm, dg, "**够得到**" if mn <= dg else "够不到", mn / dg))
            out("    落在 E4 腔体包络内的情形：**%d 个**" % len(reach))
        d4 = [e for e in events[kind] if e[1] != "e"]
        if d4:
            out("    EDA 封装被转/被镜像（D4 非恒等）：%d 个情形，最小触发 ‖δ‖ = %.3f mm"
                % (len(d4), min(e[0] for e in d4)))
        if verbose and ident:
            for n, tn, sw, case, lst in sorted(ident)[:6]:
                out("      · ‖δ‖=%.3f  格差%s  开关%s" % (n, sorted(case), "全闭" if sw else "全断"))
                for srcs, gpios, _ in lst[:2]:
                    out("          %s ↔ %s" % ("／".join(srcs), "／".join(gpios) if gpios else "地"))
        return mn, len(reach)

    # —— 独立复验：不用情形表，直接在 δ 平面上稠密扫描，看能不能扫出更小的 F ——
    step, lim = 0.02, 4.6
    dense = None; k = 0
    while k * step <= lim:
        rr = k * step
        m = max(8, int(2 * math.pi * rr / step)) if rr > 0 else 1
        for i in range(m):
            th = 2 * math.pi * i / m
            dd = (rr * math.cos(th), rr * math.sin(th))
            S = frozenset(g for g in offsets() if math.dist(dd, Lpt(*g)) < R)
            if not S: continue
            F, _, _ = evaluate(grid, contacts_for(S), "e", False)
            if F: dense = rr; break
        if dense is not None: break
        k += 1
    out("\n  § 稠密扫描独立复验（极坐标，步长 %.2f mm，不使用情形表）" % step)
    out("    扫到的最小 F 半径 = %s" % ("未在 %.1f mm 内扫到" % lim if dense is None else "%.3f mm" % dense))

    fmin, freach = summarize("F", "未钳位的 5 V 进入主机 GPIO（会打坏主机的那一类）")
    smin, sreach = summarize("S", "5 V 与地连通；含 Grok G04「主机 5V_IN 对地」")
    out("\n  § 判据 G —— 两根主机 GPIO 互短（功能错误，不致命）")
    out("    全枚举中出现 %d 条次：键位错置／多键并联。可被固件用作「物理互斥键同时为低 ⇒ 未落座」的判据。" % gcount)
    return {"inv": inv_ok, "F_min": fmin, "F_reach": freach, "S_min": smin, "S_reach": sreach}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="连同被否决的方案一起跑")
    ap.add_argument("--tip-d", type=float, default=TIP_D_DEFAULT, help="针尖有效搭接直径（敏感性）")
    ap.add_argument("--pad-d", type=float, default=PAD_D_DEFAULT, help="焊盘直径（敏感性）")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--pinmap", metavar="PATH",
                    help="交叉核对 PINMAP.md 第 4.2 节的逐针表与本脚本 frozen 表是否逐格一致。"
                         "两份副本漂开正是 check_cross_branch.py 存在的那一类错误。")
    a = ap.parse_args()
    R = (a.pad_d + a.tip_d) / 2.0
    L = []; out = lambda s="": (L.append(s), print(s))[1]

    env, (dxlo, dxhi, dzlo, dzhi) = envelopes()
    out("check_j2_mismate.py —— J2 触点场错位穷举判定")
    out("提案 · 未冻结 · 不得据以制造")
    out("")
    out("§ 几何（全部取自本人实跑 OpenSCAD 的 ECHO）")
    out("  列 1..4 中心 X = %s" % COL_X)
    out("  行 A..D 中心 Z = %s" % ROW_Z)
    out("  焊盘 Ø%.1f ／ 针尖 Ø%.1f  ⇒  **搭接阈值 R = %.3f mm**；半间距 = %.3f mm"
        % (a.pad_d, a.tip_d, R, PITCH / 2))
    if R > PITCH / 2:
        out("  ⇒ **R > 半间距**：半格错位时一根针同时压住相邻两块铜（每侧重叠 %.3f mm），"
            % (R - PITCH / 2))
        out("     整行/整列被串成一个电节点。**这就是本脚本存在的理由。**")
    else:
        out("  ⇒ R ≤ 半间距：不会发生单针桥接（本几何下不成立，此路径仅供敏感性对照）")
    out("  注：module_board.scad [检查 6] 的 0.55 mm 是「针尖整体落进焊盘 = 接触可靠」，")
    out("      本脚本判「碰没碰上」用 R = %.2f。用 0.55 判危险会把全部桥接情形漏掉。" % R)
    out("")
    out("§ 可达包络（全部由 §0 的几何推出）")
    for nm, (ax, dg, note) in env.items():
        out("  %-26s 最坏 ‖δ‖ = %6.3f mm   %s" % (nm, dg, note))
    out("  ⚠ E1 常被当成「安全余量」的分母，但它是**半程链**。诚实的最坏值是 E2/E3。")

    if a.pinmap:
        import re as _re
        txt = open(a.pinmap, encoding="utf-8").read()
        grid = SCHEMES["frozen"][1]; bad = 0; seen = 0
        for ln in txt.split("\n"):
            m = _re.match(r"^\|\s*\d+\s*\|\s*`J2\.([1-4])([A-D])`\s*\|.*?\|\s*`(\w+)`\s*\|", ln)
            if not m: continue
            seen += 1
            c, r, net = int(m.group(1)) - 1, "ABCD".index(m.group(2)), m.group(3)
            if grid[r][c] != net:
                out("  [PINMAP] **不一致** J2.%s%s：PINMAP 写 %s，本脚本 frozen 表是 %s"
                    % (m.group(1), m.group(2), net, grid[r][c])); bad += 1
        out("\n§ 与 PINMAP 第 4.2 节交叉核对：读到 %d 格，不一致 %d 格 -> %s"
            % (seen, bad, "OK" if (bad == 0 and seen == 16) else "**FAIL**"))
        if bad or seen != 16: return 1

    names = list(SCHEMES) if a.all else ["frozen"]
    res = {}
    for n in names: res[n] = run(n, R, a.verbose, out)

    out("\n" + "=" * 78)
    out("总表（F = 未钳位 5V 进 GPIO；S = 5V 与地连通，含 G04）")
    out("=" * 78)
    out("  %-10s %-9s %-14s %-12s %s" % ("方案", "不变量", "F 最小 ‖δ‖", "F 腔体可达", "S 最小 ‖δ‖"))
    for n in names:
        r = res[n]
        out("  %-10s %-9s %-14s %-12s %s" % (
            n, "通过" if r["inv"] else "**失败**",
            "无" if r["F_min"] is None else "%.3f mm" % r["F_min"],
            "0 起" if not r["F_reach"] else "**%d 起**" % r["F_reach"],
            "无" if r["S_min"] is None else "%.3f mm" % r["S_min"]))

    fr = res["frozen"]
    out("\n§ 裁决（针对冻结方案）")
    bad = (not fr["inv"]) or fr["F_reach"] > 0
    if not bad:
        out("  **通过**：正确朝向下，腔体包络内 0 起 F。")
        out("  F 最小触发位移 %.3f mm，大于 E4 腔体包络的最坏 %.3f mm —— 即使模块壳导向完全失效"
            % (fr["F_min"], env["E4 裸触点板在腔体内"][1]))
        out("  （AS-08 一级防呆归零），裸触点板在腔体里也够不到。这条结论**不依赖任何未关闭假设**。")
        out("  S（含 G04）最小触发 %.3f mm，**落在 E2/E3 全程公差链之内，会真实发生**。" % fr["S_min"])
        out("  这不是本表的缺陷：见下面的不可能性定理。")
    else:
        out("  **不通过**")
    out("")
    out("§ 定理：在**铺满铜**的 16 位场上，G04 消不掉；要消掉它必须拿位置去换")
    out("  半格桥接时每块焊盘与其轴向邻居必然导通。5V 焊盘的轴向邻居只有四种可能：")
    out("    · 场外   → 安全，但一个角位最多 2 个方向朝外，另外 2 个必在场内；")
    out("    · KEY    → 未钳位的 5 V 经 1 kΩ 直接进 GPIO（F，会打坏主机，不可恢复）；")
    out("    · GND    → 主机 5V_IN 对地（S ＝ G04，后果悬在 AS-11 上）；")
    out("    · 无铜   → 链条终止，两样都不发生 —— **但这个位置就不能放键了**。")
    out("  ⇒ 若 16 位全部载铜（frozen／S2 都是），则至少 2 个轴向邻居必须在 KEY 与 GND 之间二选一，")
    out("    **G04 在几何上无法消除**；选 GND 是两害相权，因为 F 不可恢复而 S 可被限流/保护吸收。")
    out("  ⇒ 要连 G04 一起消掉，唯一办法是把位置改成**模块侧整片无铜**（不是孤立焊盘！）。")
    out("    代价是按键数。见 fallback8：5V×2 ＋ GND×2 ＋ 无铜×4 ＋ **8 键**，F 与 S 同时不可达。")
    out("  ⇒ Grok G04 **成立**（ICD 3.3「无损」的措辞必须撤回）。它的解法不是换个排法，")
    out("    而是：要么写成前提条件并进 G6 禁测项（本裁定选此），要么付两个按键。")
    out("")
    out("§ 本脚本**不**覆盖（不要当成已证明）")
    out("  1. 这颗 SoC（BSP 里叫 esp32s31）的绝对最大额定与最大注入电流：仓库内无数据手册，unknown。")
    out("     本脚本只判「通不通」，不判「多少毫安才烧」。")
    out("  2. 主机 5V_IN 与原生 USB VBUS 的内部拓扑（AS-11，unknown）—— G04 的后果悬在这上面。")
    out("  3. Y 向插入深度的先后接触次序：等长针无法保证先接地。本脚本是准静态的，只判终态；")
    out("     「5V 已接、地未接」的瞬态没建模，ICD 3.3 该项仍开放。")
    out("  4. J3/J1 单点错焊造成的任意网置换（D4 只覆盖刚体错位与整体旋转镜像）。")
    out("  5. 弹簧针针头形状（AS-31-mm-5 只定了 Ø0.9、行程、压力）。用 --tip-d 做敏感性：")
    out("     链式通路成立的充要条件是 R > 半间距，即 Ø针尖_有效 > 2×%.2f − %.1f = %.2f mm。"
        % (PITCH / 2, a.pad_d, PITCH - a.pad_d))
    out("  6. D4 类（EDA 封装被转/被镜像）**本脚本只报不挡**：它在 Δ=0 就生效，任何排法都挡不住。")
    out("     唯一闸门是 G6 的上电前导通检验，那是流程，不是几何。")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
