#!/usr/bin/env python3
"""Fail-closed J2 cross-source check; document/netlist agreement is not hardware approval.

Usage: python3 check_j2_contract.py --left-slot LEFT_SLOT.md --pinmap PINMAP.md --netlist netlist.yaml
Requires PyYAML, as does the module-board proposal's existing check_netlist.py.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys

import yaml


PAD_PACKAGE = re.compile(r"^PAD-ARRAY-(\d+)x(\d+)-P([0-9.]+)-D([0-9.]+)$")
J3_PACKAGE = re.compile(r"^[A-Z0-9-]+-2x8-P1\.27-D0\.70$")
PAD_NAME = re.compile(r"^J2\.([1-9][0-9]*[A-Z])$")
J3_NAME = re.compile(r"^r[01]\.[1-8]$")
KEY_NAME = re.compile(r"^KEY_[A-Z_]+$")


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject YAML duplicate mapping keys instead of silently taking the last one."""


def unique_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode) -> dict:
    seen: set[object] = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=True)
        try:
            duplicate = key in seen
            seen.add(key)
        except TypeError as exc:
            raise ValueError(f"netlist 使用不可哈希的映射键：{key}") from exc
        if duplicate:
            raise ValueError(f"netlist YAML 映射键重复：{key}")
    return yaml.SafeLoader.construct_mapping(loader, node, deep=True)


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def section(text: str, start: str, stop: str) -> str:
    first = re.search(start, text, re.MULTILINE)
    if first is None:
        raise ValueError(f"缺少必需章节 {start}")
    last = re.search(stop, text[first.end():], re.MULTILINE)
    if last is None:
        raise ValueError(f"缺少必需章节终点 {stop}")
    return text[first.end():first.end() + last.start()]


def cells(line: str) -> list[str]:
    return [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]


def parse_left_slot(text: str) -> dict[int, tuple[str, int | None, bool]]:
    table = section(text, r"^## 完整20脚与12根通用GPIO", r"^## V1\.2的I²C与电源状态")
    pins: dict[int, tuple[str, int | None, bool]] = {}
    for line in table.splitlines():
        fields = cells(line) if line.startswith("|") else []
        if len(fields) != 3 or not fields[0].isdigit():
            continue
        pin = int(fields[0])
        if pin in pins:
            raise ValueError(f"LEFT_SLOT H2.{pin} 重复")
        gpio = re.match(r"GPIO(\d+)\b", fields[1])
        signal = f"GPIO{gpio.group(1)}" if gpio else fields[1]
        pins[pin] = (signal, int(gpio.group(1)) if gpio else None, fields[2].startswith("可作直接按键输入"))
    if set(pins) != set(range(1, 21)):
        raise ValueError(f"LEFT_SLOT 20 针表不完整：缺 {sorted(set(range(1,21))-set(pins))}")
    return pins


def parse_pinmap(text: str, h2_contract: dict[int, tuple[str, int | None, bool]]) -> tuple[dict[str, tuple[str, int]], dict[str, int], tuple[int, int, float, float], dict[str, str], dict[str, int]]:
    title = re.search(r"^## 4\. J2[^\n]*?(\d+)\s*行\s*×\s*(\d+)\s*列", text, re.MULTILINE)
    if title is None:
        raise ValueError("§4 J2 标题缺行列数")
    rows, cols = map(int, title.groups())
    if rows * cols != 16 or rows > 26 or cols < 1:
        raise ValueError(f"§4 行列 {rows}×{cols} 不等于 16 个接点")
    geometry = section(text, r"^### 4\.1\b", r"^### 4\.2\b")
    pitch_match = re.search(r"ASSUMPTION: AS-07[^\n]*?([0-9.]+)\s*mm\s*间距", geometry)
    if pitch_match is None:
        raise ValueError("§4.1 AS-07 缺接点节距")
    pitch = float(pitch_match.group(1))
    pad_match = re.search(r"ASSUMPTION: AS-31-mb-3[^\n]*?焊盘为圆形\s*\*\*Ø\s*([0-9.]+)\s*mm", text)
    if pad_match is None:
        raise ValueError("AS-31-mb-3 缺当前焊盘直径；历史值不可代入")
    diameter = float(pad_match.group(1))

    table = section(text, r"^### 4\.2\b", r"^### 4\.3\b")
    pads: dict[str, tuple[str, int]] = {}
    j3_nets: dict[str, str] = {}
    j3_pads: dict[str, str] = {}
    row_gpios: dict[str, int] = {}
    ordinals: set[int] = set()
    for line in table.splitlines():
        fields = cells(line) if line.startswith("|") else []
        if not fields or not fields[0].isdigit():
            continue
        if len(fields) != 9:
            raise ValueError(f"§4.2 表行缺列：{line}")
        ordinal, label, net = int(fields[0]), fields[1], fields[5]
        pad = PAD_NAME.fullmatch(label)
        if pad is None:
            raise ValueError(f"§4.2 第 {ordinal} 行焊盘名非法：{label}")
        if ordinal in ordinals or pad.group(1) in pads:
            raise ValueError(f"§4.2 重复序号或焊盘：{ordinal} / {label}")
        ordinals.add(ordinal)
        if net not in {"DOCK_5V", "DOCK_GND"} and not KEY_NAME.fullmatch(net):
            raise ValueError(f"§4.2 {label} 网名非法：{net}")
        try:
            h2 = int(fields[6])
        except ValueError as exc:
            raise ValueError(f"§4.2 {label} H2 针号非法：{fields[6]}") from exc
        pads[pad.group(1)] = (net, h2)
        j3 = fields[8]
        if not J3_NAME.fullmatch(j3) or j3 in j3_nets:
            raise ValueError(f"§4.2 {label} J3 位非法或重复：{j3}")
        j3_nets[j3] = net
        j3_pads[j3] = pad.group(1)
        if KEY_NAME.fullmatch(net):
            gpio = re.fullmatch(r"GPIO(\d+)", fields[7])
            if gpio is None:
                raise ValueError(f"§4.2 {label} GPIO 非法：{fields[7]}")
            row_gpios[net] = int(gpio.group(1))
        elif fields[7] != "—":
            raise ValueError(f"§4.2 {label} 电源网络不应填写 GPIO：{fields[7]}")
    expected = {f"{col}{chr(ord('A') + row)}" for col in range(1, cols + 1) for row in range(rows)}
    if set(pads) != expected or ordinals != set(range(1, rows * cols + 1)):
        raise ValueError(f"§4.2 接点不完整：缺 {sorted(expected - set(pads))}，多 {sorted(set(pads) - expected)}")
    if sum(net == "DOCK_5V" for net, _ in pads.values()) != 2 or sum(net == "DOCK_GND" for net, _ in pads.values()) != 4:
        raise ValueError("§4.2 供电接点数不满足当前 5V×2、GND×4 提案")
    key_pads = {net: h2 for net, h2 in pads.values() if KEY_NAME.fullmatch(net)}
    if len(key_pads) != 10:
        raise ValueError("§4.2 必须有 10 个互异 KEY 网络")
    expected_j3 = {f"r{side}.{position}" for side in range(2) for position in range(1, 9)}
    if set(j3_nets) != expected_j3:
        raise ValueError(f"§4.2 J3 位不完整：缺 {sorted(expected_j3 - set(j3_nets))}")

    j3_section = section(text, r"^### 5\.3\b", r"^## 6\.")
    title_pitch = re.search(r"双排\s*8＋8\s*@\s*([0-9.]+)", j3_section)
    joint_pad = re.search(r"焊盘\s*([0-9.]+)\s*×\s*([0-9.]+)\s*mm\s*@\s*([0-9.]+)", j3_section)
    if title_pitch is None or joint_pad is None or float(title_pitch.group(1)) != 1.27 or float(joint_pad.group(1)) != 0.70 or float(joint_pad.group(3)) != 1.27:
        raise ValueError("PINMAP §5.3 J3 必须明确双排 8＋8 @1.27，焊盘宽 0.70 mm")
    j3_table: dict[str, tuple[str, str]] = {}
    for line in j3_section.splitlines():
        fields = [cell.strip() for cell in line.strip().strip("|").split("|")] if line.startswith("|") else []
        if len(fields) != 3 or fields[0] not in {str(n) for n in range(1, 9)}:
            continue
        position = fields[0]
        for side, cell in (("r1", fields[1]), ("r0", fields[2])):
            match = re.search(r"`([^`]+)`\s*←\s*J2\.([1-9][0-9]*[A-Z])", cell)
            if match is None or f"{side}.{position}" in j3_table:
                raise ValueError(f"PINMAP §5.3 J3 {side}.{position} 位表非法或重复")
            j3_table[f"{side}.{position}"] = (match.group(1), match.group(2))
    if set(j3_table) != expected_j3 or any(j3_table[pin] != (j3_nets[pin], j3_pads[pin]) for pin in expected_j3):
        raise ValueError("PINMAP §5.3 J3 逐位网名/J2 位与 §4.2 不一致")

    key_table = section(text, r"^## 2\.\s", r"^## 3\.\s")
    key_h2: dict[str, int] = {}
    key_gpios: dict[str, int] = {}
    for line in key_table.splitlines():
        fields = cells(line) if line.startswith("|") else []
        if len(fields) >= 3 and KEY_NAME.fullmatch(fields[0]) and fields[1].isdigit():
            if fields[0] in key_h2:
                raise ValueError(f"§2 重复按键 {fields[0]}")
            key_h2[fields[0]] = int(fields[1])
            gpio = re.fullmatch(r"GPIO(\d+)", fields[2])
            if gpio is None:
                raise ValueError(f"§2 {fields[0]} GPIO 非法：{fields[2]}")
            key_gpios[fields[0]] = int(gpio.group(1))
    if key_h2 != key_pads:
        raise ValueError(f"PINMAP §2 与 §4.2 KEY→H2 不同：§2={key_h2}，§4.2={key_pads}")
    if key_gpios != row_gpios:
        raise ValueError(f"PINMAP §2 与 §4.2 KEY→GPIO 不同：§2={key_gpios}，§4.2={row_gpios}")
    if len(set(key_h2.values())) != 10:
        raise ValueError("PINMAP 十个按键必须占互异 H2 针")
    for key, h2 in key_h2.items():
        contract = h2_contract.get(h2)
        if contract is None or not contract[2] or contract[1] != key_gpios[key]:
            raise ValueError(f"PINMAP {key} 的 H2.{h2}/GPIO{key_gpios[key]} 违反 LEFT_SLOT 20 针合同")
    for pad, (net, h2) in pads.items():
        expected_h2 = 17 if net == "DOCK_5V" else 20 if net == "DOCK_GND" else key_h2[net]
        if h2 != expected_h2:
            raise ValueError(f"PINMAP {pad} 的 H2.{h2} 与 {net} 预期 H2.{expected_h2} 不同")
    return pads, key_h2, (rows, cols, pitch, diameter), j3_nets, key_gpios


def parse_netlist(data: object) -> tuple[dict[str, set[str]], dict[str, object]]:
    if not isinstance(data, dict) or not isinstance(data.get("components"), dict) or not isinstance(data.get("nets"), dict):
        raise ValueError("netlist 缺 components/nets 字典")
    pin_nets: dict[str, set[str]] = {}
    components = data["components"]
    for ref, spec in components.items():
        if not isinstance(spec, dict) or not isinstance(spec.get("pins"), int) or spec["pins"] < 1:
            raise ValueError(f"netlist {ref} 缺正整数 pins 声明")
        names = spec.get("pin_names")
        if names is not None and (not isinstance(names, list) or len(names) != spec["pins"] or len(set(str(name) for name in names)) != len(names)):
            raise ValueError(f"netlist {ref}.pin_names 与 pins 数量/唯一性不符")
    for net, spec in data["nets"].items():
        if not isinstance(spec, dict) or not isinstance(spec.get("pins"), list):
            raise ValueError(f"netlist 网 {net} 缺 pins 列表")
        for pair in spec["pins"]:
            if not isinstance(pair, list) or len(pair) != 2:
                raise ValueError(f"netlist 网 {net} 引脚条目非法：{pair}")
            ref, pin = pair
            component = components.get(ref)
            if not isinstance(component, dict):
                raise ValueError(f"netlist 网 {net} 引用了未声明器件 {ref}")
            names = component.get("pin_names")
            if names is not None:
                if str(pin) not in {str(name) for name in names}:
                    raise ValueError(f"netlist 网 {net} 引用了 {ref} 未声明引脚 {pin}")
            elif not isinstance(pin, int) or pin < 1 or pin > component["pins"]:
                raise ValueError(f"netlist 网 {net} 引用了 {ref} 越界引脚 {pin}")
            refpin = f"{ref}.{pin}"
            if refpin in pin_nets:
                raise ValueError(f"netlist 引脚重复列出（同网或跨网）：{refpin}")
            pin_nets[refpin] = {str(net)}
    return pin_nets, data


def compare(pads: dict[str, tuple[str, int]], keys: dict[str, int], geometry: tuple[int, int, float, float],
            j3_nets: dict[str, str], gpios: dict[str, int], h2_contract: dict[int, tuple[str, int | None, bool]],
            actual: dict[str, set[str]], data: dict[str, object]) -> list[str]:
    errors: list[str] = []
    components = data["components"]
    j1 = components.get("J1")
    if not isinstance(j1, dict) or j1.get("pins") != 20:
        errors.append("J1 必须声明 20 针")
    actual_j1 = {pin[3:] for pin in actual if pin.startswith("J1.")}
    expected_j1 = {str(pin) for pin in range(1, 21)}
    if actual_j1 != expected_j1:
        errors.append(f"J1 网表须恰好覆盖 1…20 针：缺 {sorted(expected_j1-actual_j1)}，多 {sorted(actual_j1-expected_j1)}")
    h2_mirror = data.get("h2_contract")
    if not isinstance(h2_mirror, dict):
        errors.append("netlist 缺 H2 20 针镜像合同")
    else:
        for pin, (signal, _, _) in h2_contract.items():
            mirrored = str(h2_mirror.get(pin, ""))
            if not re.fullmatch(re.escape(signal) + r"(?:_[A-Z0-9]+)*", mirrored):
                errors.append(f"netlist h2_contract.{pin}={mirrored} != LEFT_SLOT {signal}")
    j2 = components.get("J2")
    if not isinstance(j2, dict):
        return ["netlist 缺 J2 器件"]
    package = PAD_PACKAGE.fullmatch(str(j2.get("package", "")))
    if package is None:
        errors.append(f"J2 package 无法解析：{j2.get('package')}")
    else:
        nr, nc, pitch, diameter = int(package[1]), int(package[2]), float(package[3]), float(package[4])
        if (nr, nc) != geometry[:2]:
            errors.append(f"J2 封装行列 {nr}×{nc} != PINMAP {geometry[0]}×{geometry[1]}")
        if abs(pitch - geometry[2]) > 1e-6 or abs(diameter - geometry[3]) > 1e-6:
            errors.append(f"J2 封装节距/直径 {pitch}/{diameter} mm != PINMAP {geometry[2]}/{geometry[3]} mm")
    names = [str(name) for name in j2.get("pin_names", [])]
    if len(names) != len(set(names)) or len(names) != 16 or set(names) != set(pads):
        errors.append(f"J2 pin_names 与 PINMAP 不同：缺 {sorted(set(pads)-set(names))}，多 {sorted(set(names)-set(pads))}")
    if j2.get("pins") != 16:
        errors.append(f"J2 声明引脚数 {j2.get('pins')} != 16")
    j3 = components.get("J3")
    if not isinstance(j3, dict) or not J3_PACKAGE.fullmatch(str(j3.get("package", ""))) or j3.get("pins") != 16 or j3.get("crossing_nets") != 12:
        errors.append("J3 必须为 2×8 @1.27 mm/Ø0.70 mm、16 位、12 个跨板网络的提案")
    if isinstance(j3, dict):
        j3_names = j3.get("pin_names")
        if not isinstance(j3_names, list) or len(j3_names) != 16 or set(j3_names) != set(j3_nets):
            errors.append("J3.pin_names 必须完整声明 r0.1…r1.8，且与 PINMAP §4.2 相同")
    actual_j2 = {pin[3:]: nets for pin, nets in actual.items() if pin.startswith("J2.")}
    if set(actual_j2) != set(pads):
        errors.append(f"J2 网表接点集合不同：缺 {sorted(set(pads)-set(actual_j2))}，多 {sorted(set(actual_j2)-set(pads))}")
    for pad, (net, _) in pads.items():
        got = actual_j2.get(pad)
        if got is not None and got != {net}:
            errors.append(f"J2.{pad} 网 {sorted(got)} != PINMAP {net}")
    actual_j3 = {pin[3:]: nets for pin, nets in actual.items() if pin.startswith("J3.")}
    if set(actual_j3) != set(j3_nets):
        errors.append(f"J3 网表接点集合不同：缺 {sorted(set(j3_nets)-set(actual_j3))}，多 {sorted(set(actual_j3)-set(j3_nets))}")
    for pin, net in j3_nets.items():
        got = actual_j3.get(pin)
        if got is not None and got != {net}:
            errors.append(f"J3.{pin} 网 {sorted(got)} != PINMAP {net}")
    def only(refpin: str, want: str) -> None:
        got = actual.get(refpin)
        if got != {want}:
            errors.append(f"{refpin} 网 {sorted(got) if got else []} != {want}")
    only("J1.17", "DOCK_5V")
    only("J1.20", "DOCK_GND")
    only("J1.19", "SLOT_3V3")
    only("J1.18", "SLOT_5V_OUT_NC")
    only("J1.10", "SLOT_EEPROM_A0")
    only("U1.A0", "SLOT_EEPROM_A0")
    only("J1.12", "SLOT_SPARE_GPIO4")
    only("J1.13", "SLOT_USJ_DN")
    only("J1.15", "SLOT_USJ_DP")
    only("J1.14", "SLOT_SCL")
    only("J1.16", "SLOT_SDA")
    nc = data["nets"].get("SLOT_5V_OUT_NC")
    if not isinstance(nc, dict) or nc.get("class") != "no-connect" or nc.get("pins") != [["J1", 18]]:
        errors.append("pin18 必须是只有 J1.18 的 no-connect 网")
    for net, pin in (("SLOT_USJ_DN", 13), ("SLOT_USJ_DP", 15)):
        spec = data["nets"].get(net)
        if not isinstance(spec, dict) or spec.get("class") != "no-connect" or spec.get("pins") != [["J1", pin]]:
            errors.append(f"{net} 必须是只有 J1.{pin} 的 no-connect 网")
    for net in ("SLOT_3V3", "SLOT_5V_OUT_NC", "SLOT_SDA", "SLOT_SCL"):
        if any(pin.startswith("J2.") for pin, nets in actual.items() if net in nets):
            errors.append(f"{net} 不得进入 J2")
    for key, h2 in keys.items():
        only(f"J1.{h2}", f"SLOT_{key}")
        only(f"R_S_{key}.1", f"SLOT_{key}")
        only(f"R_S_{key}.2", key)
        for net in (key, f"SLOT_{key}"):
            spec = data["nets"].get(net)
            if not isinstance(spec, dict) or spec.get("gpio") != gpios[key]:
                errors.append(f"{net}.gpio 与 PINMAP §2 GPIO{gpios[key]} 不同")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--left-slot", required=True, type=Path)
    parser.add_argument("--pinmap", required=True, type=Path)
    parser.add_argument("--netlist", required=True, type=Path)
    args = parser.parse_args()
    try:
        left_slot_bytes = args.left_slot.read_bytes()
        pinmap_bytes = args.pinmap.read_bytes()
        netlist_bytes = args.netlist.read_bytes()
        h2_contract = parse_left_slot(left_slot_bytes.decode("utf-8-sig"))
        pads, keys, geometry, j3_nets, gpios = parse_pinmap(pinmap_bytes.decode("utf-8-sig"), h2_contract)
        actual, data = parse_netlist(yaml.load(netlist_bytes.decode("utf-8-sig"), Loader=UniqueKeyLoader))
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
        print(f"INPUT ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"LEFT_SLOT sha256={hashlib.sha256(left_slot_bytes).hexdigest()}")
    print(f"PINMAP sha256={hashlib.sha256(pinmap_bytes).hexdigest()}")
    print(f"netlist sha256={hashlib.sha256(netlist_bytes).hexdigest()}")
    errors = compare(pads, keys, geometry, j3_nets, gpios, h2_contract, actual, data)
    if errors:
        print(f"FAIL: {len(errors)} 处跨源不一致")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: LEFT_SLOT 20 针合同、{len(pads)} 个 J2/J3 接点、名义行列/节距/直径及 GPIO 镜像字段跨源一致；不代表 PCB/G2 通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
