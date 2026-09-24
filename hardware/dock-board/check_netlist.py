#!/usr/bin/env python3
# 历史记录（2026-09-24 C7）：此脚本只检查已作废的旧网表内部一致性；退出 0 不代表现行方案 J 安全/可制造。见 ARCHIVED.md。
# 提案 · 未冻结 · 由 Claude 主控（claude-opus-5）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
"""
底座主板网表一致性检查（hardware/dock-board）。

CK-01 每个声明的引脚在 nets 中恰好出现一次（NC 引脚以单针网表示）。
CK-02 J2 的 16 个针与 j2_contract（= ICD-0.2 第 3.2 节 = 模块板 PINMAP 第 4.2 节）完全一致。
CK-03 **BOOST_EN、LIM_EN 两网的 pins 中不出现 J2、U_FG** —— 这是 POWER_TOPOLOGY.md 第 3 节 (a)
      声称「可由 netlist.yaml 的 BOOST_EN、LIM_EN 网络 pins 列表机械核对」的那次核对本身。
      本脚本把两网的完整 pins 列表原样打印出来，供人工复读。
CK-04 J2 的 12 根信号针所在网，refdes 只允许 {J2, SW_*, U_FG, TP_*}（EL-D-05、EL-D-11）。
      （POWER_TOPOLOGY 第 3 节 (a) 写「除 DOCK_5V/DOCK_GND 外的 14 针」，那是 16 − 2 的算法，
        把列 1、列 2 的各一根并联冗余针也算进去了；实际信号针是 12 根。见 DESIGN_NOTES.md 第 7 节。）
CK-05 不存在任何名字含 3V3 的网（EL-D-03）。
CK-06 KEY_* 的 GPIO / H2 针号与模块板 PINMAP 第 2 节一致，且不落在 H2 pin 10/13/15/18。
CK-07 DOCK_5V / DOCK_GND 各占 J2 两针，且 DOCK_5V 网上无主机侧器件。
CK-08 若存在 BOM.csv：基线行（角色=基线）的位号集合 == components 集合。
CK-09 若存在 schematic.svg：其中 data-net 标签 ⊆ nets。

用法：python3 hardware/dock-board/check_netlist.py    （退出码 0 = 全部通过）
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

# ICD-0.2-DRAFT 第 3.2 节（列 1 在 −X 最外；行 A 在 +Z 屏侧）。
# 与 origin/claude/design-d/module-board:hardware/module-board/check_netlist.py 的 ICD_J2 逐字相同。
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

# 模块板 PINMAP.md 第 2 节：KEY → (H2 针, GPIO)
PINMAP_KEYS = {
    "KEY_UP": (1, 55), "KEY_DOWN": (3, 19), "KEY_LEFT": (5, 18), "KEY_RIGHT": (7, 17),
    "KEY_L": (9, 16), "KEY_R": (11, 15), "KEY_A": (2, 53), "KEY_B": (4, 48),
    "KEY_X": (6, 13), "KEY_Y": (8, 12),
}

FORBIDDEN_KEY_H2 = {10, 13, 15, 18}

# CK-03：使能网中禁止出现的位号
ENABLE_NETS = ["BOOST_EN", "LIM_EN"]
ENABLE_FORBIDDEN_REFDES = ["J2", "U_FG"]


def declared_pins(comps):
    out = {}
    for ref, c in comps.items():
        n = int(c["pins"])
        if "pin_names" in c:
            names = [str(p) for p in c["pin_names"]]
            if len(names) != n:
                raise SystemExit(f"{ref}: pin_names 数 {len(names)} != pins {n}")
        else:
            names = [str(i) for i in range(1, n + 1)]
        if len(set(names)) != len(names):
            raise SystemExit(f"{ref}: pin_names 有重复")
        out[ref] = names
    return out


def main() -> int:
    errors, notes = [], []
    with open(NETLIST, encoding="utf-8") as f:
        nl = yaml.safe_load(f)

    comps = nl["components"]
    nets = nl["nets"]
    contract = nl["j2_contract"]
    decl = declared_pins(comps)

    # ---- CK-01 ----
    used = {}
    for net, d in nets.items():
        for entry in d["pins"]:
            ref, pin = str(entry[0]), str(entry[1])
            if ref not in decl:
                errors.append(f"CK-01 网 {net} 引用了未声明的位号 {ref}")
                continue
            if pin not in decl[ref]:
                errors.append(f"CK-01 网 {net} 引用了 {ref} 上不存在的引脚 {pin}（可用：{decl[ref]}）")
                continue
            used.setdefault((ref, pin), []).append(net)
    for (ref, pin), lst in sorted(used.items()):
        if len(lst) > 1:
            errors.append(f"CK-01 {ref}.{pin} 出现在多个网：{lst}")
    for ref, pins in sorted(decl.items()):
        for p in pins:
            if (ref, p) not in used:
                errors.append(f"CK-01 {ref}.{p} 没有出现在任何网中")
    print(f"CK-01 引脚归属：声明 {sum(len(v) for v in decl.values())} 个引脚，"
          f"{len(comps)} 个器件，网 {len(nets)} 个")

    # ---- CK-02 ----
    j2_net = {}
    for net, d in nets.items():
        for entry in d["pins"]:
            if str(entry[0]) == "J2":
                j2_net[str(entry[1])] = net
    if j2_net != ICD_J2:
        for pad in sorted(set(ICD_J2) | set(j2_net)):
            if ICD_J2.get(pad) != j2_net.get(pad):
                errors.append(f"CK-02 J2.{pad}：ICD 要求 {ICD_J2.get(pad)}，网表为 {j2_net.get(pad)}")
    for pad, c in contract.items():
        if c["net"] != ICD_J2.get(pad):
            errors.append(f"CK-02 j2_contract.{pad} 与 ICD 第 3.2 节不符")
        if c["module_pad"] != pad:
            errors.append(f"CK-02 j2_contract.{pad}：模块板焊盘应同名（两板同 (X,Z)、不镜像），实为 {c['module_pad']}")
    print(f"CK-02 J2 逐针：16/16 与 ICD 第 3.2 节及模块板 PINMAP 第 4.2 节一致"
          if not [e for e in errors if e.startswith("CK-02")] else "CK-02 失败")

    # ---- CK-03（任务书要求真的跑一次的那次核对）----
    print()
    print("CK-03 使能网机械核对（POWER_TOPOLOGY.md 第 3 节 (a)）")
    for net in ENABLE_NETS:
        if net not in nets:
            errors.append(f"CK-03 网 {net} 不存在")
            continue
        pins = [(str(a), str(b)) for a, b in nets[net]["pins"]]
        refs = sorted({r for r, _ in pins})
        print(f"  net {net}：pins = " + ", ".join(f"{r}.{p}" for r, p in pins))
        print(f"           位号集合 = {refs}")
        hit = [r for r in refs if r in ENABLE_FORBIDDEN_REFDES]
        if hit:
            errors.append(f"CK-03 网 {net} 中出现被禁止的位号 {hit} —— "
                          f"拓扑与 POWER_TOPOLOGY 第 3 节 (a) 的论证不符，必须改拓扑")
        else:
            print(f"           禁止位号 {ENABLE_FORBIDDEN_REFDES}：未出现 → 通过")
    print()

    # ---- CK-04 ----
    allowed_re = re.compile(r"^(J2|SW_[A-Z]+|U_FG|TP_.*)$")
    sig_pads = [p for p, n in ICD_J2.items() if n not in ("DOCK_5V", "DOCK_GND")]
    bad = []
    for pad in sig_pads:
        net = j2_net.get(pad)
        for entry in nets[net]["pins"]:
            r = str(entry[0])
            if not allowed_re.match(r):
                bad.append(f"CK-04 J2.{pad}（网 {net}）连到不允许的位号 {r}")
    errors.extend(bad)
    print(f"CK-04 J2 的 {len(sig_pads)} 根非电源针：所在网只连 {{J2, SW_*, U_FG(DNP), TP_*}}"
          + ("" if not bad else " —— 失败"))

    # ---- CK-05 ----
    bad3v3 = [n for n in nets if "3V3" in n.upper()]
    if bad3v3:
        errors.append(f"CK-05 出现 3.3 V 网：{bad3v3}（违反 EL-D-03）")
    print(f"CK-05 3.3 V 网：{len(bad3v3)} 个（要求 0）")

    # ---- CK-06 ----
    for key, (h2, gpio) in PINMAP_KEYS.items():
        d = nets.get(key)
        if d is None:
            errors.append(f"CK-06 缺少网 {key}")
            continue
        if d.get("gpio") != gpio or d.get("h2_pin") != h2:
            errors.append(f"CK-06 {key}：网表 gpio={d.get('gpio')} h2={d.get('h2_pin')}，"
                          f"PINMAP 为 gpio={gpio} h2={h2}")
        if h2 in FORBIDDEN_KEY_H2:
            errors.append(f"CK-06 {key} 落在禁止的 H2 针 {h2}")
        km = nl["key_map"].get(key, {})
        if km.get("gpio") != gpio or km.get("h2_pin") != h2:
            errors.append(f"CK-06 key_map.{key} 与 PINMAP 不一致")
    print(f"CK-06 十键 GPIO/H2 针号：10/10 与模块板 PINMAP 第 2 节一致"
          if not [e for e in errors if e.startswith("CK-06")] else "CK-06 失败")

    # ---- CK-07 ----
    p5 = [p for p, n in j2_net.items() if n == "DOCK_5V"]
    pg = [p for p, n in j2_net.items() if n == "DOCK_GND"]
    if sorted(p5) != ["A1", "B1"]:
        errors.append(f"CK-07 DOCK_5V 应占 J2 A1/B1，实为 {sorted(p5)}")
    if sorted(pg) != ["A2", "B2"]:
        errors.append(f"CK-07 DOCK_GND 应占 J2 A2/B2，实为 {sorted(pg)}")
    d5refs = sorted({str(e[0]) for e in nets["DOCK_5V"]["pins"]})
    print(f"CK-07 DOCK_5V 占针 {sorted(p5)}，DOCK_GND 占针 {sorted(pg)}；DOCK_5V 网位号 = {d5refs}")

    # ---- CK-08 ----
    if os.path.exists(BOM):
        with open(BOM, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        base = {r["位号"].strip() for r in rows if r.get("角色", "").strip() == "基线" and r["位号"].strip()}
        only_bom = base - set(comps)
        only_net = set(comps) - base
        if only_bom:
            errors.append(f"CK-08 BOM 有、网表无：{sorted(only_bom)}")
        if only_net:
            errors.append(f"CK-08 网表有、BOM 基线行无：{sorted(only_net)}")
        print(f"CK-08 BOM 基线位号 {len(base)} 个，网表器件 {len(comps)} 个")
    else:
        notes.append("CK-08 跳过：BOM.csv 不存在")

    # ---- CK-09 ----
    if os.path.exists(SVG):
        with open(SVG, encoding="utf-8") as f:
            svg = f.read()
        labels = set(re.findall(r'data-net="([^"]+)"', svg))
        unknown = sorted(l for l in labels if l not in nets)
        if unknown:
            errors.append(f"CK-09 SVG 中的 data-net 不在网表：{unknown}")
        print(f"CK-09 SVG 标注网 {len(labels)} 个，全部存在于网表" if not unknown else "CK-09 失败")
    else:
        notes.append("CK-09 跳过：schematic.svg 不存在")

    print()
    for n in notes:
        print("注意：" + n)
    if errors:
        print(f"\n失败 {len(errors)} 项：")
        for e in errors:
            print("  - " + e)
        return 1
    print("历史网表内部检查通过；现行方案 J 的电气、机械及制造安全未验证。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
