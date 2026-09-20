#!/usr/bin/env python3
# 提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
"""
模块板网表一致性检查（hardware/module-board）。

检查内容：
  1. 每个器件声明的每个引脚在 nets 中恰好出现一次（NC 引脚以单针网表示）。
  2. J1 20 针全部有归属；pin 13/15/18 为单针 no-connect 网。
  3. ICD-0.2 §3.2 弹簧针逐针分配：J2 16 个焊盘的网名与 ICD 表完全相同。
  4. KEY_* → H2 针 → GPIO 与 PINMAP.md 第 2 节一致；任何 KEY 不落在 pin 10/13/15/18。
  5. 硬约束 2/3：pin 18 网只有 J1.18；SLOT_3V3、SLOT_EEPROM_A0、SLOT_SPARE_GPIO4 不到 J2/J3。
  6. SLOT_SDA/SCL 与 DOCK_SDA/SCL 为不同网，且只经 dnp 的 R_LINK_* 相连。
  7. 跨 J3 的网集合 == 含 J2 焊盘的网集合，且 J3 位序与 PINMAP.md 第 5.3 节一致。
  8. 若存在 BOM.csv：refdes 集合与 components 一致。
  9. 若存在 schematic.svg：其中 data-net 标签 ⊆ nets，且每个 net 至少出现一次。
用法：python3 hardware/module-board/check_netlist.py   （退出码 0 = 全部通过）
"""
import csv
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
NETLIST = os.path.join(HERE, "netlist.yaml")
BOM = os.path.join(HERE, "BOM.csv")
SVG = os.path.join(HERE, "schematic.svg")

# ICD-0.2-DRAFT §3.2（列 1 在 −X；行 A 在 +Z）
ICD_J2 = {
    "A1": "DOCK_5V", "B1": "DOCK_5V",
    "A2": "DOCK_GND", "B2": "DOCK_GND",
    "A3": "KEY_UP", "B3": "KEY_DOWN",
    "A4": "KEY_LEFT", "B4": "KEY_RIGHT",
    "A5": "KEY_L", "B5": "KEY_R",
    "A6": "KEY_A", "B6": "KEY_B",
    "A7": "KEY_X", "B7": "KEY_Y",
    "A8": "DOCK_SDA", "B8": "DOCK_SCL",
}

# PINMAP.md §2：KEY → (H2 针, GPIO)
PINMAP_KEYS = {
    "KEY_UP": (1, 55), "KEY_DOWN": (3, 19), "KEY_LEFT": (5, 18), "KEY_RIGHT": (7, 17),
    "KEY_L": (9, 16), "KEY_R": (11, 15), "KEY_A": (2, 53), "KEY_B": (4, 48),
    "KEY_X": (6, 13), "KEY_Y": (8, 12),
}

# PINMAP.md §5.3：J3 位 → 网
PINMAP_J3 = {
    1: "DOCK_5V", 2: "DOCK_5V", 3: "DOCK_GND", 4: "DOCK_GND",
    5: "KEY_UP", 6: "KEY_DOWN", 7: "KEY_LEFT", 8: "KEY_RIGHT", 9: "KEY_L", 10: "KEY_R",
    11: "KEY_A", 12: "KEY_B", 13: "KEY_X", 14: "KEY_Y", 15: "DOCK_SDA", 16: "DOCK_SCL",
}

FORBIDDEN_KEY_H2 = {10, 13, 15, 18}


def main() -> int:
    errors = []
    warnings = []

    with open(NETLIST, encoding="utf-8") as f:
        nl = yaml.safe_load(f)

    comps = nl["components"]
    nets = nl["nets"]

    # 引脚全集
    declared = {}
    for ref, c in comps.items():
        if "pin_names" in c:
            names = [str(p) for p in c["pin_names"]]
            if len(names) != int(c["pins"]):
                errors.append(f"{ref}: pin_names 数 {len(names)} != pins {c['pins']}")
        else:
            names = [str(i) for i in range(1, int(c["pins"]) + 1)]
        declared[ref] = set(names)

    # 使用统计
    used = {}
    pin_net = {}
    for net, n in nets.items():
        for ref, pin in n["pins"]:
            key = (str(ref), str(pin))
            if str(ref) not in declared:
                errors.append(f"net {net}: 未声明的器件 {ref}")
                continue
            if str(pin) not in declared[str(ref)]:
                errors.append(f"net {net}: {ref} 无引脚 {pin}")
                continue
            used[key] = used.get(key, 0) + 1
            pin_net[key] = net

    for ref, pins in declared.items():
        for p in sorted(pins, key=lambda s: (len(s), s)):
            cnt = used.get((ref, p), 0)
            if cnt == 0:
                errors.append(f"{ref}.{p} 未出现在任何网")
            elif cnt > 1:
                errors.append(f"{ref}.{p} 出现 {cnt} 次")

    def net_of(ref, pin):
        return pin_net.get((str(ref), str(pin)))

    def pins_of(net):
        return [(str(r), str(p)) for r, p in nets[net]["pins"]]

    # J1 20 针 / NC
    for p in (13, 15, 18):
        n = net_of("J1", p)
        if n is None:
            continue
        if len(pins_of(n)) != 1 or nets[n].get("class") != "no-connect":
            errors.append(f"J1.{p} 网 {n} 应为单针 no-connect")
    if net_of("J1", 18) != "SLOT_5V_OUT_NC":
        errors.append("J1.18 网名应为 SLOT_5V_OUT_NC")

    # J2 == ICD
    for pad, want in ICD_J2.items():
        got = net_of("J2", pad)
        if got != want:
            errors.append(f"J2.{pad}: 网 {got}，ICD §3.2 要求 {want}")

    # KEY → H2 → GPIO
    for key, (h2, gpio) in PINMAP_KEYS.items():
        slot = "SLOT_" + key
        if slot not in nets:
            errors.append(f"缺少网 {slot}")
            continue
        if net_of("J1", h2) != slot:
            errors.append(f"J1.{h2} 应为 {slot}，实际 {net_of('J1', h2)}")
        for n in (slot, key):
            if nets[n].get("gpio") != gpio:
                errors.append(f"{n}: gpio {nets[n].get('gpio')} != PINMAP {gpio}")
        rs = "R_S_" + key
        if net_of(rs, 1) != slot or net_of(rs, 2) != key:
            errors.append(f"{rs} 两端应为 {slot}/{key}")
    for p in FORBIDDEN_KEY_H2:
        n = net_of("J1", p)
        if n and "KEY" in n:
            errors.append(f"J1.{p} 上出现按键网 {n}")

    # 硬约束 2/3：不到 J2/J3 的网
    for n in ("SLOT_3V3", "SLOT_EEPROM_A0", "SLOT_SPARE_GPIO4", "SLOT_SDA", "SLOT_SCL", "EEPROM_WP"):
        for ref, _ in pins_of(n):
            if ref in ("J2", "J3"):
                errors.append(f"{n} 不得到 {ref}")
    if len(pins_of("SLOT_5V_OUT_NC")) != 1:
        errors.append("SLOT_5V_OUT_NC 只能有 J1.18 一针")
    if net_of("U1", 8) != "SLOT_3V3":
        errors.append("U1.VCC 必须接 SLOT_3V3（硬约束 3）")
    if net_of("U1", 1) != "SLOT_EEPROM_A0" or net_of("J1", 10) != "SLOT_EEPROM_A0":
        errors.append("U1.A0 与 J1.10 必须同为 SLOT_EEPROM_A0")
    for p in (2, 3):
        if net_of("U1", p) != "DOCK_GND":
            errors.append(f"U1.{p}（A1/A2）必须接地")

    # R_LINK 分网
    for sig in ("SDA", "SCL"):
        rl = f"R_LINK_{sig}"
        if not comps[rl].get("dnp"):
            errors.append(f"{rl} 必须默认 DNP")
        a, b = net_of(rl, 1), net_of(rl, 2)
        if {a, b} != {f"SLOT_{sig}", f"DOCK_{sig}"}:
            errors.append(f"{rl} 两端应为 SLOT_{sig}/DOCK_{sig}，实际 {a}/{b}")
        shared = set(pins_of(f"SLOT_{sig}")) & set(pins_of(f"DOCK_{sig}"))
        if shared:
            errors.append(f"SLOT_{sig} 与 DOCK_{sig} 共享引脚 {shared}")

    # J3 跨越
    j3_nets = {net_of("J3", i) for i in range(1, 17)}
    j2_nets = {net_of("J2", p) for p in ICD_J2}
    if j3_nets != j2_nets:
        errors.append(f"跨 J3 的网 {sorted(j3_nets)} != 含 J2 的网 {sorted(j2_nets)}")
    for pos, want in PINMAP_J3.items():
        if net_of("J3", pos) != want:
            errors.append(f"J3.{pos}: {net_of('J3', pos)} != PINMAP §5.3 {want}")
    if comps["J3"].get("crossing_nets") != len(j3_nets):
        errors.append(f"J3.crossing_nets={comps['J3'].get('crossing_nets')} 但实际 {len(j3_nets)}")

    # 电源两针并联
    for net, pads in (("DOCK_5V", {"A1", "B1"}), ("DOCK_GND", {"A2", "B2"})):
        got = {p for r, p in pins_of(net) if r == "J2"}
        if got != pads:
            errors.append(f"{net} 的 J2 焊盘 {got} != {pads}")

    # BOM
    if os.path.exists(BOM):
        with open(BOM, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        bom_refs = set()
        for r in rows:
            for ref in re.split(r"[,\s]+", r["refdes"].strip()):
                if ref:
                    bom_refs.add(ref)
        missing = set(comps) - bom_refs
        extra = bom_refs - set(comps)
        if missing:
            errors.append(f"BOM 缺少 refdes：{sorted(missing)}")
        if extra:
            errors.append(f"BOM 多出 refdes：{sorted(extra)}")
        for r in rows:
            refs = [x for x in re.split(r"[,\s]+", r["refdes"].strip()) if x]
            dnp_flags = {bool(comps.get(x, {}).get("dnp")) for x in refs if x in comps}
            if len(dnp_flags) > 1:
                errors.append(f"BOM 行 {r['refdes']} 混合了 DNP 与装配器件")
            if dnp_flags == {True} and "DNP" not in (r.get("备注", "") + r.get("value", "")):
                errors.append(f"BOM 行 {r['refdes']} 为 DNP 器件但未标 DNP")
    else:
        warnings.append("BOM.csv 不存在，跳过")

    # SVG 网标签
    if os.path.exists(SVG):
        with open(SVG, encoding="utf-8") as f:
            svg = f.read()
        labels = set(re.findall(r'data-net="([^"]+)"', svg))
        unknown = labels - set(nets)
        if unknown:
            errors.append(f"schematic.svg 含网表中不存在的网名：{sorted(unknown)}")
        absent = set(nets) - labels
        if absent:
            errors.append(f"schematic.svg 缺少网：{sorted(absent)}")
        refs_in_svg = set(re.findall(r'data-ref="([^"]+)"', svg))
        if refs_in_svg and refs_in_svg != set(comps):
            errors.append(f"schematic.svg 器件集合与网表不一致：缺 {sorted(set(comps) - refs_in_svg)}，多 {sorted(refs_in_svg - set(comps))}")
    else:
        warnings.append("schematic.svg 不存在，跳过")

    # 汇总
    n_comp = len(comps)
    n_dnp = sum(1 for c in comps.values() if c.get("dnp"))
    print(f"器件 {n_comp}（DNP {n_dnp}）；网 {len(nets)}；引脚 {sum(len(v) for v in declared.values())}")
    for w in warnings:
        print("WARN", w)
    for e in errors:
        print("FAIL", e)
    print("PASS" if not errors else f"{len(errors)} 项不通过")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
