提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造

# hardware/eeprom —— 模块板 EEPROM 身份镜像

方案 D＋G 模块板上唯一的 IC 是一颗 AT24C02（左槽 A0 = GPIO14 = 0 → 0x50）。本目录定义写进它的 134 字节 EEPROM V1 身份镜像、生成/校验工具与烧写方法。格式与校验规则全部核对自 `esp-mosaico-bsp` commit `392860b1`（快照 `review/chrome/D1-module-interface/evidence/bsp/`）。

| 文件 | 内容 |
| --- | --- |
| `mosaico_eeprom_v1.py` | 生成 / 校验 / 转储 / C 数组 / Linux i2c-dev 烧写；`selftest` 自测。仅标准库，Python 3.9+ |
| `IDENTITY.md` | 逐字段取值与理由：board_type 0x04 HANDLE（严禁 0x14）、board_id 0x0101、vendor_id 0x4354、版本、序列号策略、param_data v1 布局、假设清单 |
| `PROGRAMMING.md` | 三条烧写路径（主机 I²C1 / 外部 USB-I²C / 出厂预烧）、AT24C02 页写与 tWR、验收清单 |
| `eeprom_program_example.c` | 主机侧烧写示例固件（ESP-IDF，API 逐一核对） |
| `sample_handle.bin` | 样例镜像，134 字节（二进制文件无法携带提案抬头，以本文件与 `SHA256SUMS` 代替） |
| `sample_handle_image.h` | 由工具从样例生成的 C 数组，供示例固件包含 |
| `SHA256SUMS` | 样例镜像与生成头文件的 SHA-256 |
| `SERIALS.csv` | 序列号登记表（样例序列号已占用） |

快速使用：

```sh
cd hardware/eeprom
python3 mosaico_eeprom_v1.py selftest
python3 mosaico_eeprom_v1.py dump sample_handle.bin
python3 mosaico_eeprom_v1.py verify sample_handle.bin --expect-handle
python3 mosaico_eeprom_v1.py build --serial 0x26090002 --date 20260921 -o unit-26090002.bin
grep -v '^#' SHA256SUMS | shasum -a 256 -c
```

边界：

- KEY_* → GPIO 分配由 `hardware/module-board/PINMAP.md` 决定；样例镜像的 key_gpio 表全部为 0xFF（未分配），PINMAP 定稿后用 `build --keymap` 填入。
- BSP 只校验 magic、三段 CRC 与 param_length；vendor_id/board_id 的核对由本项目驱动补做（`IDENTITY.md` 第 2.4 节）。
- 所有 `ASSUMPTION` 及到货后验证步骤见 `IDENTITY.md` 第 11 节、`PROGRAMMING.md` 第 8 节。
