# 提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
# -*- coding: utf-8 -*-
"""
Mosaico 模块 EEPROM V1 身份镜像工具（134 字节，AT24C02）。

布局、字节序与 CRC 逐条核对自 esp-mosaico/esp-mosaico-bsp
commit 392860b1d1a123c3377947074b2af1f600e86c5d（仓库快照：
review/chrome/D1-module-interface/evidence/bsp/，SHA256 见其 SOURCE_INDEX.json）：

  components/mosaico_module_mgr/include/mosaico_module_mgr.h
      L23-25   MOSAICO_MODULE_MGR_EEPROM_MAGIC "ESP"、IMAGE_SIZE 0x86
      L42-58   mosaico_board_type_t 枚举（HANDLE = 0x04）
      L81-105  mosaico_module_mgr_eeprom_v1_t 逻辑结构体（非打包镜像）
  components/mosaico_module_mgr/mosaico_module_mgr.c
      L22-26   EEPROM_DESC_CRC_OFFSET 0x34 / MFG_DATA 0x36 / MFG_CRC 0x3E / PARAM_DATA 0x40 / PARAM_CRC 0x84
      L199-207 read_le16 / read_le32（小端）
      L209-218 crc16：初值 0xFFFF，逐字节异或，右移，最低位为 1 时异或 0xA001，无末尾异或
      L221-260 parse_descriptor：magic → 三段 CRC → param_length ≤ 64 → 逐字段解码
      L277-312 mosaico_module_mgr_type_to_name 字符串表
      L439-442 log_scan_change 识别日志 "Module identified: slot=%s type=%s(0x%02X) id=0x%04X name=%.32s"
               （只打印 board_type / board_id / board_name，不打印 hw_version，因此 board_name 内含版本）

三段 CRC 覆盖范围（与 parse_descriptor 一致）：
  descriptor    0x00–0x33 → CRC 存 0x34–0x35
  manufacturing 0x36–0x3D → CRC 存 0x3E–0x3F
  parameter     0x40–0x83 → CRC 存 0x84–0x85（覆盖 param_version、param_length 和完整 64 字节 param_data，
                                             不只是 param_length 指示的有效字节）

用法（仅标准库，Python 3.9+）：
  python3 mosaico_eeprom_v1.py selftest
  python3 mosaico_eeprom_v1.py sample  -o sample_handle.bin
  python3 mosaico_eeprom_v1.py build   --serial 0x26090002 --date 20261001 --batch 1 --factory 0 -o unit2.bin
  python3 mosaico_eeprom_v1.py build   ... --keymap-version 1               # PINMAP.md 的 KEY_* 映射版本号（ICD 7.2）
  python3 mosaico_eeprom_v1.py build   ... --keymap KEY_UP=55,KEY_DOWN=53,...   # 可选镜像表；来源只能是 hardware/module-board/PINMAP.md
  python3 mosaico_eeprom_v1.py verify  sample_handle.bin --expect-handle
  python3 mosaico_eeprom_v1.py dump    sample_handle.bin
  python3 mosaico_eeprom_v1.py c-array sample_handle.bin -o sample_handle_image.h
  python3 mosaico_eeprom_v1.py program --bus 1 --addr 0x50 sample_handle.bin   # 需 smbus2；仅外部 USB-I2C/树莓派路径

本文件不是固件；主机侧烧写见 PROGRAMMING.md 与 eeprom_program_example.c。
"""
from __future__ import annotations

import argparse
import hashlib
import struct
import sys
import time
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 镜像布局常量（偏移单位：字节；来源见文件头）
# ---------------------------------------------------------------------------
IMAGE_SIZE = 0x86            # 134 字节；mosaico_module_mgr.h L25
MAGIC = b"ESP"               # mosaico_module_mgr.h L23

OFF_MAGIC = 0x00
OFF_BOARD_TYPE = 0x03
OFF_BOARD_ID = 0x04
OFF_HW_VERSION = 0x06
OFF_SW_VERSION = 0x08
OFF_VENDOR_ID = 0x0A
OFF_BOARD_FLAGS = 0x0C
OFF_SERIAL = 0x10
OFF_BOARD_NAME = 0x14
BOARD_NAME_LEN = 32
OFF_DESC_CRC = 0x34          # mosaico_module_mgr.c L22
OFF_MFG_DATE = 0x36          # L23
OFF_BATCH = 0x3A
OFF_FACTORY = 0x3C
OFF_MFG_CRC = 0x3E           # L24
OFF_PARAM_VERSION = 0x40     # L25
OFF_PARAM_LENGTH = 0x42
OFF_PARAM_DATA = 0x44
PARAM_DATA_LEN = 64
OFF_PARAM_CRC = 0x84         # L26

# (段名, 起始, 结束(不含), CRC 存放偏移)
SEGMENTS: Tuple[Tuple[str, int, int, int], ...] = (
    ("descriptor", 0x00, OFF_DESC_CRC, OFF_DESC_CRC),
    ("manufacturing", OFF_MFG_DATE, OFF_MFG_CRC, OFF_MFG_CRC),
    ("parameter", OFF_PARAM_VERSION, OFF_PARAM_CRC, OFF_PARAM_CRC),
)

# mosaico_board_type_t（mosaico_module_mgr.h L42-58）与 type_to_name 字符串（.c L277-312）
BOARD_TYPES: Dict[int, str] = {
    0x01: "Core", 0x02: "Power", 0x03: "Dock", 0x04: "Handle",
    0x05: "Balance Car", 0x06: "Display", 0x07: "Camera", 0x08: "Sensor",
    0x09: "I/O Expansion", 0x10: "ToF", 0x11: "Matrix LED",
    0x12: "Thermal Camera", 0x13: "Relay", 0x16: "Interaction",
}
BOARD_TYPE_HANDLE = 0x04

# parse_descriptor 的返回值名称（mosaico_module_mgr.c L225-241）
ESP_OK = "ESP_OK"
ESP_ERR_INVALID_RESPONSE = "ESP_ERR_INVALID_RESPONSE"   # magic 不符
ESP_ERR_INVALID_CRC = "ESP_ERR_INVALID_CRC"             # 任一段 CRC 不符
ESP_ERR_INVALID_SIZE = "ESP_ERR_INVALID_SIZE"           # param_length > 64
ESP_ERR_INVALID_ARG = "ESP_ERR_INVALID_ARG"             # 本工具扩展：镜像不足 134 字节（主机固定读 134 字节，不会出现）

# ---------------------------------------------------------------------------
# 左槽 GPIO 合同（review/chrome/D1-module-interface/LEFT_SLOT.md）
# ---------------------------------------------------------------------------
LEFT_SLOT_KEY_GPIOS = frozenset({55, 53, 19, 48, 18, 13, 17, 12, 16, 15, 4})   # 11 根可作按键
LEFT_SLOT_EEPROM_A0_GPIO = 14                                                   # H2 pin10，专用，不得接按键
RESERVED_I2C_ADDRS = frozenset({0x50, 0x51})                                    # V1.2 模块 I2C1 上仅有的两个地址

KEY_ORDER: Tuple[str, ...] = (
    "KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT",
    "KEY_A", "KEY_B", "KEY_X", "KEY_Y", "KEY_L", "KEY_R",
)
KEY_GPIO_UNASSIGNED = 0xFF


def crc16_modbus(data: bytes) -> int:
    """与 mosaico_module_mgr.c L209-218 crc16() 逐位等价（CRC-16/MODBUS，check("123456789") = 0x4B37）。"""
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


# ---------------------------------------------------------------------------
# param_data v1（本项目自定义；BSP 不解释 param_data 内容）
# ---------------------------------------------------------------------------
PARAM_V1_VERSION = 0x0001
PARAM_V1_LEN = 24
PARAM_V1_FMT = "<BBBB10BBBHHB3x"   # 见 IDENTITY.md 第 8 节：key_count, key_flags, poll, debounce, key_gpio[10],
                                   # spare_gpio, keymap_version, battery_mah, dock_features, fuel_gauge_addr, 3 保留

PARAM_KEYFLAG_ACTIVE_LOW = 0x01     # 按键接地，按下读 0
PARAM_KEYFLAG_KEYMAP_VALID = 0x02   # key_gpio[] 已填写；清零表示主机应使用 PINMAP.md 的静态表

# KEY_* → GPIO 映射版本号（ICD-0.2-DRAFT 第 7.2 节：param_data 写入映射版本号供固件核对）。
# 分配本身只在 hardware/module-board/PINMAP.md 定义；本工具只登记版本号。
# ASSUMPTION（AS-31-eeprom-3）：PINMAP.md 尚无显式版本字段，约定其 2026-09-20 首版 = 1；
#   验证：PINMAP.md 合入 main 时在其头部登记 KEYMAP_VERSION=1，固件编译进的静态表声明同一值。
KEYMAP_VERSION_UNDECLARED = 0       # 主机不核对
PINMAP_KEYMAP_VERSION = 1

DOCK_FEAT_BATTERY = 0x0001
DOCK_FEAT_USBC_CHARGE = 0x0002
DOCK_FEAT_FUEL_GAUGE_ON_BUS = 0x0004
DOCK_FEAT_SUPPLIES_5V_IN = 0x0008   # 底座经 H2 pin17 向主机供电并充电（方案 D 前提）


@dataclass(frozen=True)
class ParamV1:
    key_count: int = 10
    key_flags: int = PARAM_KEYFLAG_ACTIVE_LOW
    poll_period_ms: int = 20          # ASSUMPTION: 20–40 ms 轮询区间的下限；到货后按实际抖动调整
    debounce_samples: int = 2         # ASSUMPTION: 连续 2 次采样一致（20 ms × 2 = 40 ms）
    key_gpio: Tuple[int, ...] = (KEY_GPIO_UNASSIGNED,) * 10   # KEY_ORDER 顺序；0xFF = 未分配
    spare_gpio: int = KEY_GPIO_UNASSIGNED
    keymap_version: int = PINMAP_KEYMAP_VERSION   # PINMAP.md 映射版本；0 = 未声明
    battery_mah: int = 1500           # ASSUMPTION（AS-12）: 参数化默认电芯 1500 mAh，仅供 UI 显示
    dock_features: int = DOCK_FEAT_BATTERY | DOCK_FEAT_USBC_CHARGE | DOCK_FEAT_SUPPLIES_5V_IN
    fuel_gauge_addr: int = 0x00       # 0 = 总线上无电量计；若加装，不得为 0x50/0x51

    def validate(self) -> None:
        if not 0 <= self.key_count <= 10:
            raise ValueError("key_count 必须在 0..10")
        if len(self.key_gpio) != 10:
            raise ValueError("key_gpio 必须恰为 10 项（KEY_ORDER 顺序）")
        assigned = [g for g in self.key_gpio if g != KEY_GPIO_UNASSIGNED]
        if assigned:
            if len(assigned) != 10:
                raise ValueError("key_gpio 要么全部为 0xFF，要么 10 键全部分配")
            if len(set(assigned)) != 10:
                raise ValueError("key_gpio 含重复 GPIO")
            for g in assigned:
                if g == LEFT_SLOT_EEPROM_A0_GPIO:
                    raise ValueError("GPIO14 为 EEPROM A0 专用，不得分配给按键")
                if g not in LEFT_SLOT_KEY_GPIOS:
                    raise ValueError("GPIO%d 不在左槽 11 根可用按键 GPIO 内" % g)
            if not self.key_flags & PARAM_KEYFLAG_KEYMAP_VALID:
                raise ValueError("已填写 key_gpio 但未置 KEYMAP_VALID 标志")
        elif self.key_flags & PARAM_KEYFLAG_KEYMAP_VALID:
            raise ValueError("置了 KEYMAP_VALID 标志但 key_gpio 全为 0xFF")
        if (self.key_flags & PARAM_KEYFLAG_KEYMAP_VALID) and self.keymap_version == KEYMAP_VERSION_UNDECLARED:
            raise ValueError("已填写 key_gpio 镜像表但 keymap_version 为 0（须写明其来源 PINMAP.md 版本）")
        if self.spare_gpio != KEY_GPIO_UNASSIGNED and (
                self.spare_gpio not in LEFT_SLOT_KEY_GPIOS or self.spare_gpio in assigned):
            raise ValueError("spare_gpio 必须是未被按键占用的左槽可用 GPIO 或 0xFF")
        if self.fuel_gauge_addr in RESERVED_I2C_ADDRS:
            raise ValueError("电量计地址不得为 0x50/0x51（V1.2 模块 I2C1 EEPROM 地址）")
        if self.fuel_gauge_addr and not (0x08 <= self.fuel_gauge_addr <= 0x77):
            raise ValueError("电量计 7 位地址应在 0x08..0x77")
        for name in ("poll_period_ms", "debounce_samples", "key_flags", "fuel_gauge_addr", "keymap_version"):
            v = getattr(self, name)
            if not 0 <= v <= 0xFF:
                raise ValueError("%s 超出 8 位" % name)
        for name in ("battery_mah", "dock_features"):
            v = getattr(self, name)
            if not 0 <= v <= 0xFFFF:
                raise ValueError("%s 超出 16 位" % name)

    def pack(self) -> bytes:
        self.validate()
        data = struct.pack(
            PARAM_V1_FMT,
            self.key_count, self.key_flags, self.poll_period_ms, self.debounce_samples,
            *self.key_gpio,
            self.spare_gpio, self.keymap_version,
            self.battery_mah, self.dock_features,
            self.fuel_gauge_addr,
        )
        assert len(data) == PARAM_V1_LEN
        return data

    @classmethod
    def unpack(cls, data: bytes) -> "ParamV1":
        if len(data) < PARAM_V1_LEN:
            raise ValueError("param_data 不足 %d 字节" % PARAM_V1_LEN)
        f = struct.unpack(PARAM_V1_FMT, data[:PARAM_V1_LEN])
        return cls(
            key_count=f[0], key_flags=f[1], poll_period_ms=f[2], debounce_samples=f[3],
            key_gpio=tuple(f[4:14]), spare_gpio=f[14], keymap_version=f[15],
            battery_mah=f[16], dock_features=f[17], fuel_gauge_addr=f[18],
        )

    def describe(self) -> List[str]:
        lines = [
            "  key_count=%d  key_flags=0x%02X (%s%s)" % (
                self.key_count, self.key_flags,
                "ACTIVE_LOW " if self.key_flags & PARAM_KEYFLAG_ACTIVE_LOW else "",
                "KEYMAP_VALID" if self.key_flags & PARAM_KEYFLAG_KEYMAP_VALID else "KEYMAP_UNSET->use PINMAP.md"),
            "  poll_period_ms=%d  debounce_samples=%d" % (self.poll_period_ms, self.debounce_samples),
        ]
        for name, g in zip(KEY_ORDER, self.key_gpio):
            lines.append("  %-9s -> %s" % (name, "GPIO%d" % g if g != KEY_GPIO_UNASSIGNED else "unassigned"))
        lines.append("  spare_gpio=%s" % ("GPIO%d" % self.spare_gpio if self.spare_gpio != KEY_GPIO_UNASSIGNED else "unassigned"))
        lines.append("  keymap_version=%d (%s)" % (
            self.keymap_version,
            "undeclared" if self.keymap_version == KEYMAP_VERSION_UNDECLARED else "hardware/module-board/PINMAP.md KEYMAP_VERSION"))
        lines.append("  battery_mah=%d  dock_features=0x%04X  fuel_gauge_addr=0x%02X" % (
            self.battery_mah, self.dock_features, self.fuel_gauge_addr))
        return lines


def parse_keymap(text: str) -> Tuple[int, ...]:
    """解析 'KEY_UP=55,KEY_DOWN=53,...' 为 KEY_ORDER 顺序的 10 元组。"""
    values = {k: KEY_GPIO_UNASSIGNED for k in KEY_ORDER}
    for item in text.split(","):
        item = item.strip()
        if not item:
            continue
        name, _, num = item.partition("=")
        name = name.strip().upper()
        if name not in values:
            raise ValueError("未知键名 %s（应为 %s）" % (name, "/".join(KEY_ORDER)))
        values[name] = int(num.strip(), 0)
    return tuple(values[k] for k in KEY_ORDER)


# ---------------------------------------------------------------------------
# 描述符
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Descriptor:
    board_type: int
    board_id: int = 0
    hw_version: int = 0
    sw_version: int = 0
    vendor_id: int = 0
    board_flags: int = 0
    serial_number: int = 0
    board_name: bytes = b""
    manufacture_date: int = 0
    batch_number: int = 0
    factory_id: int = 0
    param_version: int = 0
    param_data: bytes = b""          # 有效字节；param_length = len(param_data)

    def validate(self) -> None:
        for name, bits in (("board_type", 8), ("board_id", 16), ("hw_version", 16), ("sw_version", 16),
                           ("vendor_id", 16), ("board_flags", 32), ("serial_number", 32),
                           ("manufacture_date", 32), ("batch_number", 16), ("factory_id", 16),
                           ("param_version", 16)):
            v = getattr(self, name)
            if not 0 <= v < (1 << bits):
                raise ValueError("%s 超出 %d 位范围" % (name, bits))
        if len(self.board_name) > BOARD_NAME_LEN:
            raise ValueError("board_name 超过 32 字节")
        if len(self.param_data) > PARAM_DATA_LEN:
            raise ValueError("param_data 超过 64 字节")

    def to_image(self) -> bytes:
        """构造 134 字节镜像并写入三段 CRC。"""
        self.validate()
        img = bytearray(IMAGE_SIZE)
        img[OFF_MAGIC:OFF_MAGIC + 3] = MAGIC
        img[OFF_BOARD_TYPE] = self.board_type
        struct.pack_into("<HHHH", img, OFF_BOARD_ID, self.board_id, self.hw_version, self.sw_version, self.vendor_id)
        struct.pack_into("<II", img, OFF_BOARD_FLAGS, self.board_flags, self.serial_number)
        img[OFF_BOARD_NAME:OFF_BOARD_NAME + BOARD_NAME_LEN] = self.board_name.ljust(BOARD_NAME_LEN, b"\x00")
        struct.pack_into("<IHH", img, OFF_MFG_DATE, self.manufacture_date, self.batch_number, self.factory_id)
        struct.pack_into("<HH", img, OFF_PARAM_VERSION, self.param_version, len(self.param_data))
        img[OFF_PARAM_DATA:OFF_PARAM_DATA + PARAM_DATA_LEN] = self.param_data.ljust(PARAM_DATA_LEN, b"\x00")
        for _, start, end, crc_off in SEGMENTS:
            struct.pack_into("<H", img, crc_off, crc16_modbus(bytes(img[start:end])))
        return bytes(img)

    @classmethod
    def from_image(cls, img: bytes, check: bool = True) -> "Descriptor":
        """按 parse_descriptor 的字段偏移解码。check=True 时先执行与主机等价的校验。"""
        if check:
            res = verify(img)
            if not res.ok:
                raise ValueError("镜像无效：%s（%s）" % (res.esp_err, "; ".join(res.errors)))
        board_id, hw, sw, vendor = struct.unpack_from("<HHHH", img, OFF_BOARD_ID)
        flags, serial = struct.unpack_from("<II", img, OFF_BOARD_FLAGS)
        date, batch, factory = struct.unpack_from("<IHH", img, OFF_MFG_DATE)
        pver, plen = struct.unpack_from("<HH", img, OFF_PARAM_VERSION)
        plen = min(plen, PARAM_DATA_LEN)
        return cls(
            board_type=img[OFF_BOARD_TYPE], board_id=board_id, hw_version=hw, sw_version=sw,
            vendor_id=vendor, board_flags=flags, serial_number=serial,
            board_name=bytes(img[OFF_BOARD_NAME:OFF_BOARD_NAME + BOARD_NAME_LEN]).rstrip(b"\x00"),
            manufacture_date=date, batch_number=batch, factory_id=factory,
            param_version=pver, param_data=bytes(img[OFF_PARAM_DATA:OFF_PARAM_DATA + plen]),
        )


def build(board_type: int, **fields) -> bytes:
    """便捷入口：build(0x04, board_id=..., ...) -> 134 字节。"""
    return Descriptor(board_type=board_type, **fields).to_image()


# ---------------------------------------------------------------------------
# 校验（与 mosaico_module_mgr.c parse_descriptor L221-241 顺序一致）
# ---------------------------------------------------------------------------
@dataclass
class VerifyResult:
    ok: bool
    esp_err: str
    size_ok: bool
    magic_ok: bool
    crc_ok: Dict[str, bool]
    crc_stored: Dict[str, int]
    crc_calc: Dict[str, int]
    param_length: int
    param_length_ok: bool
    errors: List[str] = field(default_factory=list)
    extra_bytes: int = 0             # 镜像超出 134 字节的部分（例如 256 字节整片转储），主机不读取


def verify(img: bytes) -> VerifyResult:
    errors: List[str] = []
    size_ok = len(img) >= IMAGE_SIZE
    extra = max(0, len(img) - IMAGE_SIZE)
    if not size_ok:
        return VerifyResult(False, ESP_ERR_INVALID_ARG, False, False, {}, {}, {}, 0, False,
                            ["镜像仅 %d 字节，主机固定读取 %d 字节" % (len(img), IMAGE_SIZE)], extra)
    img = bytes(img[:IMAGE_SIZE])
    magic_ok = img[OFF_MAGIC:OFF_MAGIC + 3] == MAGIC
    crc_ok: Dict[str, bool] = {}
    stored: Dict[str, int] = {}
    calc: Dict[str, int] = {}
    for name, start, end, crc_off in SEGMENTS:
        stored[name] = struct.unpack_from("<H", img, crc_off)[0]
        calc[name] = crc16_modbus(img[start:end])
        crc_ok[name] = stored[name] == calc[name]
    plen = struct.unpack_from("<H", img, OFF_PARAM_LENGTH)[0]
    plen_ok = plen <= PARAM_DATA_LEN

    if not magic_ok:
        err = ESP_ERR_INVALID_RESPONSE
        errors.append("magic %r != b'ESP'" % img[OFF_MAGIC:OFF_MAGIC + 3])
    elif not all(crc_ok.values()):
        err = ESP_ERR_INVALID_CRC
        for name in crc_ok:
            if not crc_ok[name]:
                errors.append("%s CRC 存 0x%04X 算 0x%04X" % (name, stored[name], calc[name]))
    elif not plen_ok:
        err = ESP_ERR_INVALID_SIZE
        errors.append("param_length %d > 64" % plen)
    else:
        err = ESP_OK
    return VerifyResult(err == ESP_OK, err, size_ok, magic_ok, crc_ok, stored, calc, plen, plen_ok, errors, extra)


# ---------------------------------------------------------------------------
# 本项目手持底座模块板的身份取值（详见 IDENTITY.md；每项理由与假设在该文档）
# ---------------------------------------------------------------------------
HANDLE_BOARD_TYPE = BOARD_TYPE_HANDLE          # 0x04 HANDLE；严禁 0x14（非枚举值，且恰为 board_name 偏移，易混淆）
HANDLE_BOARD_ID = 0x0101                       # 高字节 0x01 产品线「手持底座 方案 D＋G」，低字节 0x01「模块板」
HANDLE_VENDOR_ID = 0x4354                      # ASCII "CT"（ChromeTokyo）；非 0x0000 / 0xFFFF；无官方注册表
HANDLE_HW_VERSION = 0x0100                     # 高字节打板轮次 1，低字节同轮修订 0
HANDLE_SW_VERSION = 0x0100                     # 主机侧合同版本 1.0（KEY_* 语义 + param v1）
HANDLE_BOARD_FLAGS = 0x00000000                # BSP 未定义位含义，保持 0；本项目标志放在 param_data
# board_name：ICD-0.2-DRAFT 第 7.2 节建议「含 MOSAICO-DOCK-MODULE 与版本」。主机识别日志（mosaico_module_mgr.c L439-442）
# 只打印 type/id/name，不打印 hw_version，所以把 hw_version 以 -Vmajor.minor 缀在名字里，串口一眼可辨。
HANDLE_BOARD_NAME_PREFIX = b"MOSAICO-DOCK-MODULE"   # 19 字节；加 "-V255.255" 最长 28 字节 < 32


def handle_board_name(hw_version: int) -> bytes:
    """按 hw_version 派生 board_name，例如 0x0100 -> b'MOSAICO-DOCK-MODULE-V1.0'（24 字节，ASCII，NUL 填充）。"""
    return HANDLE_BOARD_NAME_PREFIX + b"-V%d.%d" % (hw_version >> 8, hw_version & 0xFF)


HANDLE_BOARD_NAME = handle_board_name(HANDLE_HW_VERSION)   # 默认 hw_version 对应的名字（样例用）

SAMPLE_SERIAL = 0x26090001                     # BCD YYMM(2609) << 16 | 序号 0x0001；样例，不是实物编号
SAMPLE_DATE = 0x20260920                       # BCD YYYYMMDD；首版样例日期，重生成时保持不变（SERIALS.csv 已登记）
SAMPLE_BATCH = 0x0001                          # 第 1 轮打板
SAMPLE_FACTORY = 0x0000                        # 0x0000 = 自行烧写（非工厂预烧）

# 样例镜像 SHA-256（selftest 用于检测非预期改动；改动任何默认值后须同步更新并在 SHA256SUMS 登记）
SAMPLE_SHA256 = "119e991a6a87b5b1afa18feefdbcb1fdb86cadc564c7ce7375133da0a9810832"


def handle_descriptor(serial_number: int = SAMPLE_SERIAL,
                      manufacture_date: int = SAMPLE_DATE,
                      batch_number: int = SAMPLE_BATCH,
                      factory_id: int = SAMPLE_FACTORY,
                      hw_version: int = HANDLE_HW_VERSION,
                      sw_version: int = HANDLE_SW_VERSION,
                      param: Optional[ParamV1] = None,
                      board_name: Optional[bytes] = None) -> Descriptor:
    param = param if param is not None else ParamV1()
    name = board_name if board_name is not None else handle_board_name(hw_version)
    return Descriptor(
        board_type=HANDLE_BOARD_TYPE, board_id=HANDLE_BOARD_ID,
        hw_version=hw_version, sw_version=sw_version,
        vendor_id=HANDLE_VENDOR_ID, board_flags=HANDLE_BOARD_FLAGS,
        serial_number=serial_number, board_name=name,
        manufacture_date=manufacture_date, batch_number=batch_number, factory_id=factory_id,
        param_version=PARAM_V1_VERSION, param_data=param.pack(),
    )


def sample_image() -> bytes:
    return handle_descriptor().to_image()


def expect_handle(img: bytes) -> List[str]:
    """本项目专用的语义检查（BSP 不做这些检查；供自家驱动/生产测试使用）。返回问题列表，空表示通过。"""
    problems: List[str] = []
    res = verify(img)
    if not res.ok:
        return ["镜像无效：%s" % res.esp_err] + res.errors
    d = Descriptor.from_image(img, check=False)
    if d.board_type != HANDLE_BOARD_TYPE:
        problems.append("board_type 0x%02X != 0x04 HANDLE" % d.board_type)
    if d.vendor_id != HANDLE_VENDOR_ID:
        problems.append("vendor_id 0x%04X != 0x%04X" % (d.vendor_id, HANDLE_VENDOR_ID))
    if d.board_id != HANDLE_BOARD_ID:
        problems.append("board_id 0x%04X != 0x%04X" % (d.board_id, HANDLE_BOARD_ID))
    if d.param_version != PARAM_V1_VERSION or len(d.param_data) != PARAM_V1_LEN:
        problems.append("param_version/param_length 不是 v1 (0x0001 / %d)" % PARAM_V1_LEN)
    else:
        try:
            ParamV1.unpack(d.param_data).validate()
        except ValueError as exc:
            problems.append("param_data v1 非法：%s" % exc)
    if d.serial_number in (0x00000000, 0xFFFFFFFF):
        problems.append("serial_number 为保留值 0x%08X" % d.serial_number)
    if not d.board_name.startswith(HANDLE_BOARD_NAME_PREFIX):
        problems.append("board_name %r 不以 %r 开头（ICD-0.2-DRAFT 7.2 建议）" % (d.board_name, HANDLE_BOARD_NAME_PREFIX))
    if d.board_name != handle_board_name(d.hw_version):
        problems.append("board_name %r 与 hw_version 0x%04X 派生名 %r 不一致" % (
            d.board_name, d.hw_version, handle_board_name(d.hw_version)))
    return problems


# ---------------------------------------------------------------------------
# 转储
# ---------------------------------------------------------------------------
def _hex(b: bytes) -> str:
    return " ".join("%02X" % x for x in b)


def dump(img: bytes) -> str:
    res = verify(img)
    out: List[str] = []
    out.append("镜像长度 %d 字节%s" % (len(img), "（主机只读前 134 字节，其余 %d 字节忽略）" % res.extra_bytes if res.extra_bytes else ""))
    out.append("SHA-256(前 134 字节): %s" % hashlib.sha256(bytes(img[:IMAGE_SIZE])).hexdigest())
    out.append("parse_descriptor 等价结果: %s%s" % (res.esp_err, "" if res.ok else "  <- " + "; ".join(res.errors)))
    if not res.size_ok:
        return "\n".join(out)
    img = bytes(img[:IMAGE_SIZE])
    d = Descriptor.from_image(img, check=False)
    rows = [
        (OFF_MAGIC, 3, "magic", repr(img[0:3])),
        (OFF_BOARD_TYPE, 1, "board_type", "0x%02X %s" % (d.board_type, BOARD_TYPES.get(d.board_type, "Unknown"))),
        (OFF_BOARD_ID, 2, "board_id", "0x%04X" % d.board_id),
        (OFF_HW_VERSION, 2, "hw_version", "0x%04X (v%d.%d)" % (d.hw_version, d.hw_version >> 8, d.hw_version & 0xFF)),
        (OFF_SW_VERSION, 2, "sw_version", "0x%04X (v%d.%d)" % (d.sw_version, d.sw_version >> 8, d.sw_version & 0xFF)),
        (OFF_VENDOR_ID, 2, "vendor_id", "0x%04X" % d.vendor_id),
        (OFF_BOARD_FLAGS, 4, "board_flags", "0x%08X" % d.board_flags),
        (OFF_SERIAL, 4, "serial_number", "0x%08X" % d.serial_number),
        (OFF_BOARD_NAME, 32, "board_name", repr(d.board_name.decode("ascii", "replace"))),
        (OFF_DESC_CRC, 2, "desc_crc16", "存 0x%04X 算 0x%04X %s" % (res.crc_stored["descriptor"], res.crc_calc["descriptor"], "OK" if res.crc_ok["descriptor"] else "BAD")),
        (OFF_MFG_DATE, 4, "manufacture_date", "0x%08X" % d.manufacture_date),
        (OFF_BATCH, 2, "batch_number", "0x%04X" % d.batch_number),
        (OFF_FACTORY, 2, "factory_id", "0x%04X" % d.factory_id),
        (OFF_MFG_CRC, 2, "mfg_crc16", "存 0x%04X 算 0x%04X %s" % (res.crc_stored["manufacturing"], res.crc_calc["manufacturing"], "OK" if res.crc_ok["manufacturing"] else "BAD")),
        (OFF_PARAM_VERSION, 2, "param_version", "0x%04X" % d.param_version),
        (OFF_PARAM_LENGTH, 2, "param_length", "%d%s" % (res.param_length, "" if res.param_length_ok else " (>64 非法)")),
        (OFF_PARAM_DATA, 64, "param_data", "(下方解码)"),
        (OFF_PARAM_CRC, 2, "param_crc16", "存 0x%04X 算 0x%04X %s" % (res.crc_stored["parameter"], res.crc_calc["parameter"], "OK" if res.crc_ok["parameter"] else "BAD")),
    ]
    out.append("%-6s %-4s %-17s %-48s %s" % ("偏移", "长度", "字段", "原始字节(小端)", "解码"))
    for off, n, name, val in rows:
        raw = img[off:off + n]
        raw_s = _hex(raw if n <= 16 else raw[:16]) + (" ..." if n > 16 else "")
        out.append("0x%02X   %-4d %-17s %-48s %s" % (off, n, name, raw_s, val))
    out.append("param_data 原始 64 字节:")
    for i in range(0, PARAM_DATA_LEN, 16):
        out.append("  0x%02X: %s" % (OFF_PARAM_DATA + i, _hex(img[OFF_PARAM_DATA + i:OFF_PARAM_DATA + i + 16])))
    if d.param_version == PARAM_V1_VERSION and len(d.param_data) >= PARAM_V1_LEN:
        out.append("param_data v1 解码:")
        p = ParamV1.unpack(d.param_data)
        out.extend(p.describe())
        try:
            p.validate()
        except ValueError as exc:
            out.append("  param v1 校验失败: %s" % exc)
    return "\n".join(out)


def c_array(img: bytes, symbol: str = "k_sample_handle_image") -> str:
    lines = [
        "/* 提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造 */",
        "/* 由 mosaico_eeprom_v1.py c-array 生成，勿手改。SHA-256: %s */" % hashlib.sha256(img).hexdigest(),
        "#pragma once",
        "#include <stdint.h>",
        "#define %s_SIZE %dU" % (symbol.upper(), len(img)),
        "static const uint8_t %s[%d] = {" % (symbol, len(img)),
    ]
    for i in range(0, len(img), 12):
        chunk = img[i:i + 12]
        lines.append("    " + " ".join("0x%02X," % b for b in chunk) + "  /* 0x%02X */" % i)
    lines.append("};")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# 外部 USB-I2C / Linux i2c-dev 烧写（可选依赖 smbus2；主机侧烧写见 eeprom_program_example.c）
# ---------------------------------------------------------------------------
EEPROM_PAGE_SIZE = 8            # AT24C02 页 8 字节（datasheet doc0180 Memory Organization；所购型号待原厂数据手册核对）
EEPROM_TWR_LIMIT_S = 0.020      # tWR 最大 5 ms（doc0180 Table 5）× 4 余量


def program_smbus(bus_num: int, addr: int, img: bytes, dry_run: bool = False) -> bytes:
    """经 Linux i2c-dev 以 8 字节页写入并回读校验。返回回读的 134 字节。"""
    if len(img) != IMAGE_SIZE:
        raise ValueError("镜像必须为 134 字节")
    if not verify(img).ok:
        raise ValueError("拒绝烧写无效镜像")
    if dry_run:
        pages = [(off, img[off:off + EEPROM_PAGE_SIZE]) for off in range(0, IMAGE_SIZE, EEPROM_PAGE_SIZE)]
        for off, chunk in pages:
            print("page 0x%02X (%d B): %s" % (off, len(chunk), _hex(chunk)))
        print("共 %d 次页写（最后一页 %d 字节，部分页写）" % (len(pages), len(pages[-1][1])))
        return img
    try:
        from smbus2 import SMBus, i2c_msg   # type: ignore
    except ImportError as exc:
        raise SystemExit("需要 smbus2（pip install smbus2）；此路径仅用于树莓派/USB-I2C 适配器上的 Linux i2c-dev") from exc
    with SMBus(bus_num) as bus:
        for off in range(0, IMAGE_SIZE, EEPROM_PAGE_SIZE):
            chunk = img[off:off + EEPROM_PAGE_SIZE]
            bus.i2c_rdwr(i2c_msg.write(addr, bytes([off]) + chunk))
            deadline = time.monotonic() + EEPROM_TWR_LIMIT_S
            while True:                     # ACK polling：写周期内器件不应答（doc0180 "Acknowledge Polling"）
                try:
                    bus.i2c_rdwr(i2c_msg.read(addr, 1))
                    break
                except OSError:
                    if time.monotonic() > deadline:
                        raise TimeoutError("page 0x%02X 写周期超过 %.0f ms 仍无应答" % (off, EEPROM_TWR_LIMIT_S * 1e3))
                    time.sleep(0.0005)
        w = i2c_msg.write(addr, b"\x00")
        r = i2c_msg.read(addr, IMAGE_SIZE)
        bus.i2c_rdwr(w, r)
        back = bytes(r)
    if back != img:
        diff = [i for i in range(IMAGE_SIZE) if back[i] != img[i]]
        raise RuntimeError("回读不一致，偏移: %s" % ", ".join("0x%02X" % i for i in diff[:16]))
    return back


# ---------------------------------------------------------------------------
# 自测
# ---------------------------------------------------------------------------
def selftest(verbose: bool = True) -> int:
    def log(msg: str) -> None:
        if verbose:
            print("  ok  " + msg)

    # 1. CRC 算法：CRC-16/MODBUS 标准检查值
    assert crc16_modbus(b"123456789") == 0x4B37
    assert crc16_modbus(b"") == 0xFFFF
    log("crc16 check(\"123456789\") == 0x4B37")

    # 2. 样例镜像基本属性
    img = sample_image()
    assert len(img) == IMAGE_SIZE == 134
    res = verify(img)
    assert res.ok and res.esp_err == ESP_OK, res
    assert expect_handle(img) == [], expect_handle(img)
    assert img[0:3] == b"ESP" and img[3] == 0x04
    assert struct.unpack_from("<H", img, 0x04)[0] == 0x0101
    assert struct.unpack_from("<H", img, 0x0A)[0] == 0x4354
    assert HANDLE_BOARD_NAME == b"MOSAICO-DOCK-MODULE-V1.0" and len(HANDLE_BOARD_NAME) == 24
    assert img[0x14:0x14 + len(HANDLE_BOARD_NAME)] == HANDLE_BOARD_NAME and img[0x14 + len(HANDLE_BOARD_NAME)] == 0
    assert len(handle_board_name(0xFFFF)) == 28 <= BOARD_NAME_LEN - 1     # 最长派生名仍留 NUL
    assert img[0x44 + 0x0F] == PINMAP_KEYMAP_VERSION == 1                # keymap_version 位于 param 区 0x0F
    log("sample: 134 B, ESP_OK, board_type 0x04, name %s, keymap_version %d, expect_handle 通过" % (
        HANDLE_BOARD_NAME.decode(), PINMAP_KEYMAP_VERSION))

    # 3. 段 CRC 存放位置与覆盖范围（与 C 常量一致）
    assert struct.unpack_from("<H", img, 0x34)[0] == crc16_modbus(img[0x00:0x34])
    assert struct.unpack_from("<H", img, 0x3E)[0] == crc16_modbus(img[0x36:0x3E])
    assert struct.unpack_from("<H", img, 0x84)[0] == crc16_modbus(img[0x40:0x84])
    log("三段 CRC 位置 0x34/0x3E/0x84，覆盖 0x00-0x33/0x36-0x3D/0x40-0x83")

    # 4. 每个字节都受保护：翻转任一字节都必须使校验失败（含 CRC 字节自身）
    for i in range(IMAGE_SIZE):
        bad = bytearray(img)
        bad[i] ^= 0x01
        r = verify(bytes(bad))
        assert not r.ok, "偏移 0x%02X 翻转未被检出" % i
        if i < 3:
            assert r.esp_err == ESP_ERR_INVALID_RESPONSE
        else:
            assert r.esp_err == ESP_ERR_INVALID_CRC
            seg = "descriptor" if i < 0x36 else "manufacturing" if i < 0x40 else "parameter"
            assert not r.crc_ok[seg] and all(r.crc_ok[s] for s in r.crc_ok if s != seg), (i, r.crc_ok)
    log("134 个字节逐个翻转均被检出，且只影响所属段")

    # 5. 翻转 param_data 未使用区（超出 param_length 的字节）也必须失败：参数 CRC 覆盖完整 64 字节
    bad = bytearray(img)
    bad[OFF_PARAM_DATA + PARAM_DATA_LEN - 1] ^= 0x80
    assert verify(bytes(bad)).esp_err == ESP_ERR_INVALID_CRC
    log("param_data 尾部未用字节受参数 CRC 覆盖")

    # 6. param_length > 64（重算 CRC 后）→ ESP_ERR_INVALID_SIZE；顺序在 CRC 之后
    bad = bytearray(img)
    struct.pack_into("<H", bad, OFF_PARAM_LENGTH, 65)
    struct.pack_into("<H", bad, OFF_PARAM_CRC, crc16_modbus(bytes(bad[0x40:0x84])))
    assert verify(bytes(bad)).esp_err == ESP_ERR_INVALID_SIZE
    log("param_length 65 → ESP_ERR_INVALID_SIZE")

    # 7. 空片/全零
    assert verify(b"\xFF" * 256).esp_err == ESP_ERR_INVALID_RESPONSE
    assert verify(b"\x00" * IMAGE_SIZE).esp_err == ESP_ERR_INVALID_RESPONSE
    assert verify(img[:100]).esp_err == ESP_ERR_INVALID_ARG
    log("出厂 0xFF 空片 / 全零 → ESP_ERR_INVALID_RESPONSE；短镜像被拒")

    # 8. 往返：镜像→结构→镜像
    d = Descriptor.from_image(img)
    assert d == handle_descriptor(), d
    assert d.to_image() == img
    log("Descriptor 往返一致")

    # 9. board_name 边界：32 字节无 NUL 合法；33 字节拒绝
    d32 = replace(handle_descriptor(), board_name=b"A" * 32)
    i32 = d32.to_image()
    assert verify(i32).ok and Descriptor.from_image(i32).board_name == b"A" * 32
    try:
        replace(handle_descriptor(), board_name=b"A" * 33).to_image()
        raise AssertionError("33 字节 board_name 未被拒绝")
    except ValueError:
        pass
    log("board_name 32 字节（无 NUL）合法，33 字节拒绝")

    # 9b. board_name 派生与 expect_handle 的名字核对
    assert handle_board_name(0x0203) == b"MOSAICO-DOCK-MODULE-V2.3"
    i_hw = replace(handle_descriptor(hw_version=0x0203), board_name=b"MOSAICO-DOCK-MODULE-V2.3").to_image()
    assert expect_handle(i_hw) == [], expect_handle(i_hw)
    assert any("不一致" in s for s in expect_handle(replace(handle_descriptor(), hw_version=0x0101).to_image()))
    assert any("不以" in s for s in expect_handle(replace(handle_descriptor(), board_name=b"MK-X").to_image()))
    log("board_name 由 hw_version 派生；名字/版本不一致、前缀错误均被 expect_handle 报出")

    # 10. ParamV1 往返与约束（下方 key_gpio 元组只是测试数据，不是 KEY_*→GPIO 分配；分配只在 PINMAP.md）
    p = ParamV1()
    assert ParamV1.unpack(p.pack()) == p and len(p.pack()) == PARAM_V1_LEN
    assert p.keymap_version == PINMAP_KEYMAP_VERSION
    full = ParamV1(key_flags=PARAM_KEYFLAG_ACTIVE_LOW | PARAM_KEYFLAG_KEYMAP_VALID,
                   key_gpio=(55, 53, 19, 48, 18, 13, 17, 12, 16, 15), spare_gpio=4)
    assert ParamV1.unpack(full.pack()) == full
    assert ParamV1.unpack(replace(p, keymap_version=0).pack()).keymap_version == 0
    assert ParamV1.unpack(replace(p, keymap_version=255).pack()).keymap_version == 255
    for bad_p in (
            replace(full, key_gpio=(14, 53, 19, 48, 18, 13, 17, 12, 16, 15)),          # GPIO14 A0 专用
            replace(full, key_gpio=(55, 55, 19, 48, 18, 13, 17, 12, 16, 15)),          # 重复
            replace(full, key_gpio=(54, 53, 19, 48, 18, 13, 17, 12, 16, 15)),          # 板载 I2S GPIO
            replace(full, key_flags=PARAM_KEYFLAG_ACTIVE_LOW),                          # 已填表未置标志
            replace(p, key_flags=PARAM_KEYFLAG_ACTIVE_LOW | PARAM_KEYFLAG_KEYMAP_VALID),  # 置标志未填表
            replace(p, fuel_gauge_addr=0x50), replace(p, fuel_gauge_addr=0x51),        # 保留地址
            replace(full, spare_gpio=55),                                               # spare 与按键冲突
            replace(full, keymap_version=0),                                            # 填了镜像表却不声明版本
            replace(p, keymap_version=256),                                             # 超 8 位
    ):
        try:
            bad_p.pack()
            raise AssertionError("非法 ParamV1 未被拒绝: %r" % (bad_p,))
        except ValueError:
            pass
    assert parse_keymap("KEY_UP=55,KEY_DOWN=53,KEY_LEFT=19,KEY_RIGHT=48,KEY_A=18,KEY_B=13,KEY_X=17,KEY_Y=12,KEY_L=16,KEY_R=15") == full.key_gpio
    log("ParamV1 往返一致；GPIO14/重复/I2S/标志不一致/0x50-0x51/keymap_version 非法 均被拒绝")

    # 11. 确定性与登记的 SHA-256
    assert sample_image() == img
    sha = hashlib.sha256(img).hexdigest()
    if SAMPLE_SHA256 != "__SAMPLE_SHA256__":
        assert sha == SAMPLE_SHA256, "样例 SHA-256 %s 与登记值 %s 不符：默认值被改动，须同步更新 SAMPLE_SHA256 与 SHA256SUMS" % (sha, SAMPLE_SHA256)
        log("样例 SHA-256 与登记值一致: %s" % sha)
    else:
        log("样例 SHA-256（尚未登记）: %s" % sha)

    # 12. c_array 输出可解析回同一镜像
    txt = c_array(img)
    nums = [int(tok.rstrip(","), 16) for line in txt.splitlines() if line.startswith("    0x")
            for tok in line.split("/*")[0].split()]
    assert bytes(nums) == img
    log("c-array 往返一致")

    if verbose:
        print("selftest: 全部通过")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _int(s: str) -> int:
    return int(s, 0)


def _read(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def _write(path: Optional[str], data: bytes, label: str) -> None:
    if path:
        with open(path, "wb") as f:
            f.write(data)
        print("%s -> %s (%d B, sha256 %s)" % (label, path, len(data), hashlib.sha256(data).hexdigest()))
    else:
        sys.stdout.buffer.write(data)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Mosaico 模块 EEPROM V1 身份镜像工具（134 字节）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("selftest", help="运行自测")

    s = sub.add_parser("sample", help="生成本项目手持底座模块板的样例镜像（固定取值，见 IDENTITY.md）")
    s.add_argument("-o", "--out", help="输出文件；省略则写 stdout")

    b = sub.add_parser("build", help="按本项目身份取值生成单台镜像")
    b.add_argument("--serial", type=_int, required=True, help="serial_number，32 位，建议 0xYYMMSSSS，见 IDENTITY.md")
    b.add_argument("--date", type=_int, required=True, help="manufacture_date，BCD 0xYYYYMMDD，可写 20260920")
    b.add_argument("--batch", type=_int, default=SAMPLE_BATCH, help="batch_number（打板轮次），默认 %d" % SAMPLE_BATCH)
    b.add_argument("--factory", type=_int, default=SAMPLE_FACTORY, help="factory_id，0=自行烧写")
    b.add_argument("--hw", type=_int, default=HANDLE_HW_VERSION, help="hw_version，默认 0x%04X" % HANDLE_HW_VERSION)
    b.add_argument("--sw", type=_int, default=HANDLE_SW_VERSION, help="sw_version，默认 0x%04X" % HANDLE_SW_VERSION)
    b.add_argument("--keymap-version", type=_int, default=PINMAP_KEYMAP_VERSION,
                   help="KEY_*→GPIO 映射版本号 = hardware/module-board/PINMAP.md 的 KEYMAP_VERSION；0=未声明；默认 %d" % PINMAP_KEYMAP_VERSION)
    b.add_argument("--keymap", help="可选镜像表 KEY_UP=55,KEY_DOWN=53,...（全部 10 键）；来源必须是 hardware/module-board/PINMAP.md")
    b.add_argument("--name", help="覆盖 board_name（ASCII ≤ 31 字节）；默认按 hw_version 派生 MOSAICO-DOCK-MODULE-Vx.y")
    b.add_argument("--battery-mah", type=_int, default=ParamV1.battery_mah)
    b.add_argument("--poll-ms", type=_int, default=ParamV1.poll_period_ms)
    b.add_argument("--debounce", type=_int, default=ParamV1.debounce_samples)
    b.add_argument("--fuel-gauge-addr", type=_int, default=0)
    b.add_argument("-o", "--out")

    v = sub.add_parser("verify", help="按主机 parse_descriptor 等价规则校验")
    v.add_argument("image")
    v.add_argument("--expect-handle", action="store_true", help="附加本项目身份语义检查")

    d = sub.add_parser("dump", help="逐字段转储")
    d.add_argument("image")

    c = sub.add_parser("c-array", help="输出 C 数组头文件")
    c.add_argument("image")
    c.add_argument("-o", "--out")
    c.add_argument("--symbol", default="k_sample_handle_image")

    p = sub.add_parser("program", help="经 Linux i2c-dev（smbus2）烧写并回读校验；不适用于 Mosaico 主机本身")
    p.add_argument("image")
    p.add_argument("--bus", type=_int, required=True, help="/dev/i2c-N 的 N")
    p.add_argument("--addr", type=_int, default=0x50, help="7 位地址，A0 接地时为 0x50")
    p.add_argument("--dry-run", action="store_true", help="只打印页写序列，不访问总线")

    a = ap.parse_args(argv)

    if a.cmd == "selftest":
        return selftest()
    if a.cmd == "sample":
        _write(a.out, sample_image(), "sample")
        return 0
    if a.cmd == "build":
        flags = PARAM_KEYFLAG_ACTIVE_LOW
        key_gpio: Tuple[int, ...] = (KEY_GPIO_UNASSIGNED,) * 10
        if a.keymap:
            key_gpio = parse_keymap(a.keymap)
            flags |= PARAM_KEYFLAG_KEYMAP_VALID
        param = ParamV1(key_flags=flags, key_gpio=key_gpio, keymap_version=a.keymap_version,
                        battery_mah=a.battery_mah,
                        poll_period_ms=a.poll_ms, debounce_samples=a.debounce,
                        fuel_gauge_addr=a.fuel_gauge_addr,
                        dock_features=ParamV1.dock_features | (DOCK_FEAT_FUEL_GAUGE_ON_BUS if a.fuel_gauge_addr else 0))
        name = a.name.encode("ascii") if a.name else None
        img = handle_descriptor(serial_number=a.serial, manufacture_date=a.date, batch_number=a.batch,
                                factory_id=a.factory, hw_version=a.hw, sw_version=a.sw, param=param,
                                board_name=name).to_image()
        problems = expect_handle(img)
        if problems:
            print("生成的镜像未通过 expect_handle：\n  " + "\n  ".join(problems), file=sys.stderr)
            return 2
        _write(a.out, img, "build")
        return 0
    if a.cmd == "verify":
        img = _read(a.image)
        res = verify(img)
        print("%s: %s" % (a.image, res.esp_err))
        for name in ("descriptor", "manufacturing", "parameter"):
            if name in res.crc_ok:
                print("  %-13s CRC 存 0x%04X 算 0x%04X %s" % (name, res.crc_stored[name], res.crc_calc[name], "OK" if res.crc_ok[name] else "BAD"))
        for e in res.errors:
            print("  - " + e)
        rc = 0 if res.ok else 1
        if a.expect_handle and res.ok:
            problems = expect_handle(img)
            print("  expect_handle: %s" % ("通过" if not problems else "失败"))
            for e in problems:
                print("  - " + e)
            rc = rc or (0 if not problems else 3)
        return rc
    if a.cmd == "dump":
        print(dump(_read(a.image)))
        return 0
    if a.cmd == "c-array":
        txt = c_array(_read(a.image), a.symbol)
        if a.out:
            with open(a.out, "w", encoding="utf-8") as f:
                f.write(txt)
            print("c-array -> %s" % a.out)
        else:
            sys.stdout.write(txt)
        return 0
    if a.cmd == "program":
        img = _read(a.image)
        back = program_smbus(a.bus, a.addr, img, dry_run=a.dry_run)
        if not a.dry_run:
            print("烧写并回读一致，sha256 %s" % hashlib.sha256(back).hexdigest())
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
