#!/usr/bin/env python3
"""Regression controls for fixed WIP inputs at module-board commit 94e393c.

Usage: python3 test_check_j2_contract.py --pinmap /tmp/PINMAP.md --netlist /tmp/netlist.yaml
Extract inputs with the two `git show 94e393c:hardware/module-board/...` commands in README.md.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
from pathlib import Path
import unittest

import yaml

import check_j2_contract as checker


PINMAP_SHA = "fc986a2c00b0f0f264136f228376064c790a2cc309e869f69441728322e03727"
NETLIST_SHA = "70668e5391ebd599037322850c1e63e755cb35b44fdf27a7905d0472327179bf"


class ContractTests(unittest.TestCase):
    pinmap_path: Path
    netlist_path: Path

    @classmethod
    def setUpClass(cls) -> None:
        pinmap_bytes = cls.pinmap_path.read_bytes()
        netlist_bytes = cls.netlist_path.read_bytes()
        if hashlib.sha256(pinmap_bytes).hexdigest() != PINMAP_SHA or hashlib.sha256(netlist_bytes).hexdigest() != NETLIST_SHA:
            raise ValueError("测试输入哈希不等于固定的 94e393c 提案；不要用此测试给其他版次背书")
        cls.pads, cls.keys, cls.geometry, cls.j3_nets, cls.gpios = checker.parse_pinmap(pinmap_bytes.decode())
        cls.original = yaml.safe_load(netlist_bytes.decode())

    @classmethod
    def valid_control(cls) -> dict:
        """Keep all non-J2/J3 circuitry; align only the two connectors to PINMAP."""
        data = copy.deepcopy(cls.original)
        for spec in data["nets"].values():
            spec["pins"] = [pair for pair in spec["pins"] if pair[0] not in ("J2", "J3")]
        data["components"]["J2"].update(
            package="PAD-ARRAY-4x4-P2.54-D2.0", pin_names=list(cls.pads)
        )
        data["components"]["J3"].update(
            package="SMD-JOINT-2x8-P1.27-D0.70", crossing_nets=12,
            pin_names=list(cls.j3_nets)
        )
        for pad, (net, _) in cls.pads.items():
            data["nets"][net]["pins"].append(["J2", pad])
        for pin, net in cls.j3_nets.items():
            data["nets"][net]["pins"].append(["J3", pin])
        return data

    @classmethod
    def errors(cls, data: dict) -> list[str]:
        actual, parsed = checker.parse_netlist(data)
        return checker.compare(cls.pads, cls.keys, cls.geometry, cls.j3_nets, cls.gpios, actual, parsed)

    def test_wip_drift_fails(self) -> None:
        errors = self.errors(self.original)
        self.assertTrue(any("J2 封装行列" in e for e in errors))
        self.assertTrue(any("J3 必须" in e for e in errors))
        self.assertTrue(any("J3 网表接点集合" in e for e in errors))

    def test_consistent_control_passes(self) -> None:
        self.assertEqual([], self.errors(self.valid_control()))

    def test_j3_power_key_swap_fails(self) -> None:
        data = self.valid_control()
        data["nets"]["DOCK_5V"]["pins"].remove(["J3", "r1.7"])
        data["nets"]["KEY_UP"]["pins"].remove(["J3", "r0.7"])
        data["nets"]["DOCK_5V"]["pins"].append(["J3", "r0.7"])
        data["nets"]["KEY_UP"]["pins"].append(["J3", "r1.7"])
        self.assertTrue(any("J3.r1.7" in e for e in self.errors(data)))

    def test_gpio_mirror_fails(self) -> None:
        data = self.valid_control()
        data["nets"]["KEY_UP"]["gpio"] = 99
        self.assertTrue(any("KEY_UP.gpio" in e for e in self.errors(data)))

    def test_duplicate_j1_or_j2_pin_fails(self) -> None:
        for pin in (["J1", 17], ["J2", "1A"]):
            with self.subTest(pin=pin):
                data = self.valid_control()
                data["nets"]["DOCK_5V"]["pins"].append(pin)
                with self.assertRaisesRegex(ValueError, "重复列出"):
                    self.errors(data)

    def test_pin18_backfeed_fails_even_without_duplicate(self) -> None:
        data = self.valid_control()
        data["nets"]["SLOT_5V_OUT_NC"]["pins"].remove(["J1", 18])
        data["nets"]["DOCK_5V"]["pins"].append(["J1", 18])
        self.assertTrue(any("J1.18" in e for e in self.errors(data)))

    def test_j2_power_to_key_swap_fails(self) -> None:
        data = self.valid_control()
        data["nets"]["DOCK_5V"]["pins"].remove(["J2", "1A"])
        data["nets"]["KEY_UP"]["pins"].remove(["J2", "3A"])
        data["nets"]["DOCK_5V"]["pins"].append(["J2", "3A"])
        data["nets"]["KEY_UP"]["pins"].append(["J2", "1A"])
        self.assertTrue(any("J2.1A" in e for e in self.errors(data)))

    def test_pad_diameter_drift_fails(self) -> None:
        data = self.valid_control()
        data["components"]["J2"]["package"] = "PAD-ARRAY-4x4-P2.54-D1.8"
        self.assertTrue(any("节距/直径" in e for e in self.errors(data)))

    def test_j3_old_package_fails(self) -> None:
        data = self.valid_control()
        data["components"]["J3"]["package"] = "CASTELLATION-1x16-P1.50-D0.70"
        self.assertTrue(any("J3 必须" in e for e in self.errors(data)))

    def test_j3_pin_names_missing_fails(self) -> None:
        data = self.valid_control()
        del data["components"]["J3"]["pin_names"]
        self.assertTrue(any("J3.pin_names" in e for e in self.errors(data)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pinmap", required=True, type=Path)
    parser.add_argument("--netlist", required=True, type=Path)
    options = parser.parse_args()
    ContractTests.pinmap_path = options.pinmap
    ContractTests.netlist_path = options.netlist
    unittest.main(argv=[__file__], verbosity=2)
