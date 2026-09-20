#!/usr/bin/env python3
# 提案 · 未冻结 · 由 Claude 主控（claude-opus-5）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
"""
由 netlist.yaml 生成 schematic.svg（网标签式原理图）。

为什么是生成的而不是手画的：schematic.svg 必须与 netlist.yaml 逐网对应，
check_netlist.py 第 10 项会比对两者的网集合。手工维护一张 33 网、41 器件的图
必然与网表漂移；这里从同一份 YAML 生成，漂移不可能发生。

画法采用 EDA 的「网标签（net label）」惯例：不拉长导线，每个器件引脚出短脚，
脚上挂网名标签；同名标签即同网。这样 J1 的 20 针、J2 的 16 焊盘、J3 的 16 位
都能逐针标注而不产生跨图连线。

用法：python3 hardware/module-board/gen_schematic.py
"""
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
NETLIST = os.path.join(HERE, "netlist.yaml")
OUT = os.path.join(HERE, "schematic.svg")

W, H = 1780, 2330

# ---------- 画图基元 ----------
E = []


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def text(x, y, s, cls="t", anchor="start", extra=""):
    E.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}"{extra}>{esc(s)}</text>')


def rect(x, y, w, h, cls="box", extra=""):
    E.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" class="{cls}"{extra}/>')


def line(x1, y1, x2, y2, cls="w"):
    E.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}"/>')


def netlabel(x, y, net, anchor="start", cls="net"):
    """网标签：带 data-net，check_netlist.py 据此比对网集合。"""
    dx = 6 if anchor == "start" else -6
    E.append(f'<text x="{x + dx}" y="{y + 4}" class="{cls}" text-anchor="{anchor}" '
             f'data-net="{esc(net)}">{esc(net)}</text>')


def refdes(x, y, ref, cls="ref", anchor="start"):
    """器件位号：带 data-ref。"""
    E.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}" '
             f'data-ref="{esc(ref)}">{esc(ref)}</text>')


def section(x, y, w, h, title, sub=""):
    rect(x, y, w, h, "sect")
    text(x + 14, y + 26, title, "h2")
    if sub:
        text(x + 14, y + 46, sub, "sub")


def main():
    with open(NETLIST, encoding="utf-8") as f:
        nl = yaml.safe_load(f)
    comps, nets = nl["components"], nl["nets"]
    h2 = nl["h2_contract"]

    # 引脚 → 网 反查
    pin_net = {}
    for net, n in nets.items():
        for r, p in n["pins"]:
            pin_net[(str(r), str(p))] = net

    def N(ref, pin):
        return pin_net[(str(ref), str(pin))]

    # ---------- 标题 ----------
    rect(0, 0, W, H, "bg")
    text(40, 52, "ESP-Mosaico 左槽模块板 · 原理图（网标签式）", "h1")
    text(40, 80, "提案 · 未冻结 · 由 Claude 主控（claude-opus-5）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造", "warn")
    text(40, 104, f"修订 {nl['meta']['revision']}　{nl['meta']['date']}　"
                  f"器件 {len(comps)}（DNP {sum(1 for c in comps.values() if c.get('dnp'))}）　网 {len(nets)}　"
                  "由 netlist.yaml 生成：python3 gen_schematic.py", "sub")
    text(40, 126, "同名网标签即同网，不拉跨图连线。虚线框 = DNP（默认不装）。坐标与列序见 PINMAP.md 第 4.1 节；"
                  "逐针分配等同 ICD-0.2-DRAFT 第 2、3.2 节。", "sub")

    # ================= 第 1 段：J1 / EEPROM / 上拉与链接 =================
    Y0 = 150
    section(40, Y0, 470, 880, "J1 — 2×10P 2.54 mm 右角公头（配合主机左槽 H2）",
            "针号与 H2 同号；配合方向 +X。ASSUMPTION AS-06 / AS-17")
    bx, by, pitch = 112, Y0 + 78, 40
    rect(bx, by - 14, 166, 20 * pitch + 8, "comp")
    refdes(bx + 83, by - 24, "J1", "ref", "middle")
    for i in range(1, 21):
        y = by + (i - 1) * pitch
        nm = N("J1", i)
        nc = nets[nm].get("class") == "no-connect"
        # 引脚方块：针号 + H2 合同上的主机网络/GPIO
        rect(bx + 8, y - 9, 150, 18, "pin_nc" if nc else "pin")
        text(bx + 15, y + 5, f"{i:>2}", "pinno")
        text(bx + 42, y + 5, str(h2[i]), "gpio_s")
        # 出脚 + 网标签
        line(bx + 166, y, bx + 200, y, "w_nc" if nc else "w")
        netlabel(bx + 200, y, nm, "start", "net_nc" if nc else "net")
        if nc:
            line(bx + 177, y - 7, bx + 189, y + 7, "x")
            line(bx + 189, y - 7, bx + 177, y + 7, "x")
    text(52, Y0 + 866, "pin 13 / 15 / 18：焊盘存在、不连铜、无测试点（硬约束 2、AS-30）", "note")

    # --- EEPROM ---
    section(540, Y0, 500, 520, "U1 — AT24C02D 身份 EEPROM（0x50）",
            "VCC 取自 pin 19 SLOT_3V3（硬约束 3）；引脚以名称索引，序同 Table 1-1")
    ux, uy, up = 700, Y0 + 96, 42
    rect(ux, uy - 16, 150, 8 * up - 10, "comp")
    refdes(ux + 75, uy - 26, "U1", "ref", "middle")
    left_pins = ["A0", "A1", "A2", "GND"]
    right_pins = ["VCC", "WP", "SCL", "SDA"]
    for k, pn in enumerate(left_pins):
        y = uy + k * up
        text(ux + 10, y + 5, pn, "pinname")
        line(ux, y, ux - 40, y)
        netlabel(ux - 40, y, N("U1", pn), "end")
    for k, pn in enumerate(right_pins):
        y = uy + k * up
        text(ux + 140, y + 5, pn, "pinname", "end")
        line(ux + 150, y, ux + 190, y)
        netlabel(ux + 190, y, N("U1", pn), "start")
    # C1
    cy = uy + 4 * up + 26
    refdes(ux - 40, cy - 14, "C1", "ref")
    text(ux + 6, cy - 14, "100 nF 0603 X7R 50 V（C1591）", "note")
    line(ux - 30, cy, ux - 30, cy + 34)
    line(ux - 46, cy + 12, ux - 14, cy + 12, "cap")
    line(ux - 46, cy + 20, ux - 14, cy + 20, "cap")
    netlabel(ux - 46, cy - 2, N("C1", 1), "end")
    netlabel(ux - 46, cy + 36, N("C1", 2), "end")
    # JP1
    jy = cy + 74
    refdes(ux - 46, jy - 14, "JP1", "ref")
    text(ux - 10, jy - 14, "三焊盘锡桥：默认桥 1–2（WP→GND，可写）", "note")
    for k in range(3):
        y = jy + 10 + k * 26
        rect(ux - 46, y - 8, 22, 16, "pad")
        text(ux - 35, y + 4, str(k + 1), "pinno", "middle")
        line(ux - 24, y, ux + 6, y)
        netlabel(ux + 6, y, N("JP1", k + 1), "start", "net_s")
    # 默认桥 1–2：竖向连接焊盘 1 与 2
    line(ux - 52, jy + 10, ux - 52, jy + 36, "bridge")
    text(ux - 60, jy + 26, "桥", "note", "end")
    text(ux - 46, jy + 108, "两侧不得同时桥接（会把 SLOT_3V3 短到 DOCK_GND）", "note")

    # --- 上拉 / 链接电阻 ---
    section(1070, Y0, 670, 440, "I²C：DNP 上拉与 DNP 0 Ω 链接位",
            "SLOT_SDA/SCL 与 DOCK_SDA/SCL 是两个网，默认断开（EL-D-04 / EL-D-10）")
    rows = [("R_PU_SDA", 1, 2, "上拉 → SLOT_3V3"), ("R_PU_SCL", 1, 2, "上拉 → SLOT_3V3"),
            ("R_LINK_SDA", 1, 2, "0 Ω 链接位"), ("R_LINK_SCL", 1, 2, "0 Ω 链接位")]
    for k, (ref, pa, pb, desc) in enumerate(rows):
        y = Y0 + 110 + k * 78
        netlabel(1240, y, N(ref, pa), "end")
        line(1245, y, 1290, y)
        rect(1290, y - 13, 84, 26, "comp_dnp")
        line(1374, y, 1420, y)
        netlabel(1420, y, N(ref, pb), "start")
        refdes(1332, y - 22, ref, "ref", "middle")
        text(1332, y + 5, "DNP", "dnp", "middle")
        text(1620, y + 5, desc, "note")
    text(1084, Y0 + 424, "R_PU 阻值待 P6/G6-E 决定，≤10 kΩ（AT24C02D 手册）；不得照搬 V1.0 的 4.7 kΩ（硬约束 4）", "note")

    # --- 说明块 ---
    section(1070, Y0 + 470, 670, 410, "供电与隔离规则（硬约束 1/2/3）",
            "本板无 MCU、无 I²C 扩展器、无电源 IC")
    bullets = [
        "pin 17 SLOT_5V_IN → DOCK_5V：全程纯铜，中间无任何串联器件，",
        "　　不等 EEPROM 识别、不等主机 GPIO 许可（硬约束 1 / EL-D-01）。",
        "pin 18 SLOT_5V_OUT_NC：单针网，焊盘不连铜、无测试点、丝印 NC。",
        "　　绝不连到底座任何输出（硬约束 2 / EL-D-02）。",
        "pin 19 SLOT_3V3：只供 U1.VCC、C1、DNP 上拉上端、JP1.3。",
        "　　不跨 J3、不到 J2；弹簧针接口无 3V3 针（硬约束 3 / EL-D-03）。",
        "按键为底座侧无源开关接 DOCK_GND，拉高只由主机内部上拉提供；",
        "　　模块板上无 5 V 上拉、无电平转换（硬约束 5 / EL-D-05）。",
        "SLOT_EEPROM_A0（pin 10）只到 U1.A0 与 TP_A0，不接按键、不到 J2/J3。",
        "SLOT_SPARE_GPIO4（pin 12）只到 TP_SPARE，接口 2×8 无余针。",
    ]
    for k, b in enumerate(bullets):
        text(1084, Y0 + 546 + k * 30, b, "note")
    text(1084, Y0 + 546 + len(bullets) * 30 + 18,
         "载流：DOCK_5V / DOCK_GND 各占 J2 两针、J3 两位并联（AS-09 峰值 ≤1 A）", "note")

    # ================= 第 2 段：串阻 / 测试点 / ESD =================
    Y1 = 1060
    section(40, Y1, 700, 540, "R_S_KEY_* — 按键串阻位（10 只，0603）",
            "H2 侧 SLOT_KEY_*（pin 1） → 弹簧针侧 KEY_*（pin 2）；提案 1 kΩ，装 0 Ω 时两侧同铜")
    keys = ["UP", "DOWN", "LEFT", "RIGHT", "L", "R", "A", "B", "X", "Y"]
    for k, kk in enumerate(keys):
        ref = "R_S_KEY_" + kk
        y = Y1 + 92 + k * 43
        netlabel(300, y, N(ref, 1), "end")
        line(305, y, 350, y)
        rect(350, y - 12, 76, 24, "comp")
        text(388, y + 5, "1 kΩ", "val", "middle")
        refdes(388, y - 18, ref, "ref_s", "middle")
        line(426, y, 470, y)
        netlabel(470, y, N(ref, 2), "start")
        text(700, y + 5, f"GPIO{nets[N(ref, 1)]['gpio']}", "gpio", "end")
    text(52, Y1 + 524, "ASSUMPTION AS-31-mb-4 / AS-31-mb-6：1 kΩ 下按下电平仍 < V_IL，且对 5 V 误接触限流有效（待 P4 / Hiro 复核）", "note")

    # --- 测试点 ---
    section(770, Y1, 420, 540, "测试点（槽板顶面 SMD 圆焊盘）",
            "TP_3V3 / TP_GND / TP_SDA / TP_SCL 为 ICD 第 7.1 节烧录夹具四点")
    tps = ["TP_5V", "TP_GND", "TP_3V3", "TP_SDA", "TP_SCL", "TP_A0", "TP_SPARE", "TP_WP"]
    for k, tp in enumerate(tps):
        y = Y1 + 96 + k * 52
        E.append(f'<circle cx="850" cy="{y}" r="11" class="tp"/>')
        refdes(820, y + 5, tp, "ref", "end")
        line(861, y, 900, y)
        netlabel(900, y, N(tp, 1), "start")
    text(782, Y1 + 524, "pin 18 无测试点：P8 直接探 J1 焊针（ICD EL-D-02）", "note")

    # --- ESD ---
    section(1220, Y1, 520, 540, "ESD 位（13 只 SOD-523 双向 TVS，全部 DNP）",
            "pin 1 = 信号，pin 2 = DOCK_GND；取舍见 DESIGN_NOTES 第 7 节")
    esd = ["D_ESD_KEY_" + k for k in keys] + ["D_ESD_SDA", "D_ESD_SCL", "D_ESD_5V"]
    for k, d in enumerate(esd):
        col, row = k // 7, k % 7
        x = 1244 + col * 250
        y = Y1 + 96 + row * 58
        rect(x, y - 12, 26, 24, "comp_dnp")
        text(x + 13, y + 5, "▽", "dnp", "middle")
        refdes(x + 34, y - 4, d, "ref_s")
        netlabel(x + 30, y + 14, N(d, 1), "start", "net_s")
    text(1232, Y1 + 524, "默认 DNP：模块板不在信号链常带 ESD；装配前须核结电容对 I²C 与按键沿的影响", "note")

    # ================= 第 3 段：J3 / J2 =================
    Y2 = 1630
    section(40, Y2, 520, 660, "J3 — 槽板↔触点板 90° 半孔焊接接头（16 位）",
            "位 1 在 −X 端，沿 +X 递增；ASSUMPTION AS-31-mb-5")
    refdes(300, Y2 + 74, "J3", "ref", "middle")
    for i in range(1, 17):
        y = Y2 + 96 + (i - 1) * 34
        rect(150, y - 11, 34, 22, "pad")
        text(167, y + 5, str(i), "pinno", "middle")
        line(184, y, 224, y)
        netlabel(224, y, N("J3", i), "start")
    text(52, Y2 + 644, "跨 J3 共 14 网；SLOT_3V3 / SLOT_EEPROM_A0 / SLOT_SPARE_GPIO4 / SLOT_SDA / SLOT_SCL / EEPROM_WP 不跨越", "note")

    # --- J2 物理阵列 ---
    section(590, Y2, 1150, 660, "J2 — 底部弹簧针接触焊盘 2×8 @2.54 mm（触点板底层，−Y 面）",
            "视图 = EDA 顶视图（自 +Y 看向 −Y，+X 向右）：列 1 在左，行 B（−Z，背侧）在上，行 A（+Z，屏侧）在下")
    refdes(640, Y2 + 96, "J2", "ref")
    px0, pyB, pyA, ppitch = 700, Y2 + 180, Y2 + 300, 122
    for c in range(1, 9):
        x = px0 + (c - 1) * ppitch
        text(x, Y2 + 130, f"列 {c}", "collab", "middle")
        for row, py in (("B", pyB), ("A", pyA)):
            pad = f"{row}{c}"
            nm = N("J2", pad)
            E.append(f'<circle cx="{x}" cy="{py}" r="26" class="j2pad"/>')
            text(x, py + 5, pad, "padlab", "middle")
            ly = py - 40 if row == "B" else py + 52
            netlabel(x, ly, nm, "middle", "net_s")
    text(636, pyB + 6, "行 B", "collab", "end")
    text(636, pyA + 6, "行 A", "collab", "end")
    # 尺寸线
    line(px0, Y2 + 392, px0 + 7 * ppitch, Y2 + 392, "dim")
    line(px0, Y2 + 386, px0, Y2 + 398, "dim")
    line(px0 + 7 * ppitch, Y2 + 386, px0 + 7 * ppitch, Y2 + 398, "dim")
    text(px0 + 3.5 * ppitch, Y2 + 414, "7 × 2.54 = 17.78 mm（ASSUMPTION AS-07）", "note", "middle")
    text(px0 - 60, Y2 + 452, "列 1 在 −X 极端（靠左握把外侧）；列 8 靠 Mosaico 中央。", "note")
    text(px0 - 60, Y2 + 478, "列 1 = DOCK_5V ×2，列 2 = DOCK_GND ×2，列 3–7 = 十键成对同列，列 8 = DOCK_SDA/SCL。", "note")
    text(px0 - 60, Y2 + 504, "焊盘 Ø1.8 mm（ASSUMPTION AS-31-mb-3），表面处理 ENIG（AS-31-mb-8）。", "note")
    text(px0 - 60, Y2 + 530, "底座主板顶层弹簧针按相同 (X, Z) 布置，两板之间不做镜像。", "note")
    text(px0 - 60, Y2 + 560, "错位分析见 ICD 第 3.3 节：X ±1 列、Z 错一行均无损；绕 Y 轴 180° 由一级机械防呆保证触不到针。", "note")
    text(px0 - 60, Y2 + 586, "装 R_LINK 后 180° 错放变为有损，因此装 R_LINK 的前提是 AS-08 一级防呆已关闭。", "warnnote")

    # ---------- 输出 ----------
    style = """
  :root { --bg:#ffffff; --fg:#111827; --mut:#6b7280; --ln:#374151; --acc:#1d4ed8;
          --box:#f9fafb; --brd:#d1d5db; --pad:#fde68a; --nc:#9ca3af; --warn:#b91c1c; --dnp:#7c3aed; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#0b0f19; --fg:#e5e7eb; --mut:#9ca3af; --ln:#9ca3af; --acc:#93c5fd;
            --box:#111827; --brd:#374151; --pad:#78350f; --nc:#6b7280; --warn:#fca5a5; --dnp:#c4b5fd; }
  }
  .bg { fill: var(--bg); }
  text { font-family: "Noto Sans CJK SC","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif; fill: var(--fg); }
  .h1 { font-size: 26px; font-weight: 700; }
  .h2 { font-size: 16px; font-weight: 700; }
  .sub, .note { font-size: 12.5px; fill: var(--mut); }
  .warnnote { font-size: 12.5px; fill: var(--warn); }
  .warn { font-size: 12.5px; fill: var(--warn); font-weight: 600; }
  .t { font-size: 13px; }
  .net { font-size: 13px; font-weight: 600; fill: var(--acc); font-family: ui-monospace,"SF Mono",Menlo,Consolas,monospace; }
  .net_s { font-size: 11px; font-weight: 600; fill: var(--acc); font-family: ui-monospace,Menlo,Consolas,monospace; }
  .net_nc { font-size: 13px; font-weight: 600; fill: var(--nc); font-family: ui-monospace,Menlo,Consolas,monospace; }
  .ref { font-size: 13px; font-weight: 700; }
  .ref_s { font-size: 11px; font-weight: 700; }
  .pinno { font-size: 12px; fill: var(--fg); font-family: ui-monospace,Menlo,Consolas,monospace; }
  .pinname { font-size: 12px; font-weight: 600; font-family: ui-monospace,Menlo,Consolas,monospace; }
  .gpio { font-size: 11.5px; fill: var(--mut); font-family: ui-monospace,Menlo,Consolas,monospace; }
  .gpio_s { font-size: 10.5px; fill: var(--mut); font-family: ui-monospace,Menlo,Consolas,monospace; }
  .val { font-size: 12px; }
  .dnp { font-size: 11px; font-weight: 700; fill: var(--dnp); }
  .collab { font-size: 12px; fill: var(--mut); font-weight: 600; }
  .padlab { font-size: 12px; font-weight: 700; fill: var(--fg); font-family: ui-monospace,Menlo,Consolas,monospace; }
  .sect { fill: none; stroke: var(--brd); stroke-width: 1.2; rx: 8; }
  .box, .comp { fill: var(--box); stroke: var(--ln); stroke-width: 1.4; }
  .comp_dnp { fill: none; stroke: var(--dnp); stroke-width: 1.4; stroke-dasharray: 5 3; }
  .pin { fill: var(--box); stroke: var(--ln); stroke-width: 1; }
  .pin_nc { fill: none; stroke: var(--nc); stroke-width: 1; stroke-dasharray: 4 3; }
  .pad { fill: var(--box); stroke: var(--ln); stroke-width: 1.2; }
  .tp { fill: var(--box); stroke: var(--ln); stroke-width: 2; }
  .j2pad { fill: var(--pad); stroke: var(--ln); stroke-width: 1.6; }
  .w { stroke: var(--ln); stroke-width: 1.4; }
  .w_nc { stroke: var(--nc); stroke-width: 1.2; stroke-dasharray: 4 3; }
  .x { stroke: var(--nc); stroke-width: 1.6; }
  .cap { stroke: var(--ln); stroke-width: 2.4; }
  .bridge { stroke: var(--ln); stroke-width: 4; stroke-linecap: round; }
  .dim { stroke: var(--mut); stroke-width: 1; }
"""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
           f'role="img" aria-label="ESP-Mosaico 左槽模块板原理图">\n'
           f'<title>ESP-Mosaico 左槽模块板 原理图（提案 · 未冻结 · 不得据以制造）</title>\n'
           f'<style>{style}</style>\n' + "\n".join(E) + "\n</svg>\n")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)

    # 生成后自证：网集合与器件集合必须与网表完全一致
    import re
    labels = set(re.findall(r'data-net="([^"]+)"', svg))
    refs = set(re.findall(r'data-ref="([^"]+)"', svg))
    bad = []
    if labels != set(nets):
        bad.append(f"网不一致：缺 {sorted(set(nets) - labels)}，多 {sorted(labels - set(nets))}")
    if refs != set(comps):
        bad.append(f"器件不一致：缺 {sorted(set(comps) - refs)}，多 {sorted(refs - set(comps))}")
    for b in bad:
        print("FAIL", b)
    print(f"已写出 {OUT}：网标签 {len(labels)}/{len(nets)}，器件 {len(refs)}/{len(comps)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
