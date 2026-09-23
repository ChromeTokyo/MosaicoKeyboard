# G3 证据笔记

数字是本会话算出的。行号指该 SHA 上的文件，不指本报告分支。

## 升压电阻

来源：`8068ce2:hardware/dock-board/POWER_TOPOLOGY.md` 约第 91–94 行；`POWER_BUDGET.md` 约第 16、54 行。

公式：`VOUT = 0.595 × (1 + R1/120)`，R 以 kΩ 计。

```
909 → 0.595 × (1 + 7.575)     = 0.595 × 8.575    = 5.102125
768 → 0.595 × (1 + 6.4)       = 0.595 × 7.4      = 4.403
750 → 0.595 × (1 + 6.25)      = 0.595 × 7.25     = 4.31375
5.16 V → R1 = 120 × (5.16/0.595 − 1) = 920.672 kΩ
5.06 V → R1 = 120 × (5.06/0.595 − 1) = 900.504 kΩ
```

只扫 R1 ±1%、R2 名义、VREF ∈ {0.580, 0.610}：

```
0.580 × (1 + 909×0.99/120) = 4.9296
0.610 × (1 + 909×1.01/120) = 5.2770
```

R1 与 R2 独立 ±1%、VREF ∈ {0.580, 0.595, 0.610} 的角点最小/最大约 **4.8865 / 5.3241 V**。

单调性：`∂VOUT/∂R1 = VREF/R2`。VREF > 0 且 R2 > 0 时，768 kΩ 的输出低于 909 kΩ，不能是 5.16 V 对 5.10 V。

## 输入限流

来源：同一 `POWER_TOPOLOGY.md` 约第 45、63 行。`R = 1.1 kΩ = 1100 Ω`。

```
1500/1100 = 1.3636 A
1610/1100 = 1.4636 A
1720/1100 = 1.5636 A
```

## EEPROM

- 数据手册 SHA-256 `397ff061aa7a4ae36864592813831e9386e9467f10049064d7f139f26be6475e`，1288069 字节。文本层标题 `Atmel-8871F-SEEPROM-AT24C01D-02D-Datasheet_012017`。SDA：「external pull-up resistor (not to exceed 10KΩ)」。
- `96fd823`：`selftest` EXIT 0；`verify --expect-handle` EXIT 0；在 `hardware/eeprom/` 下 `sha256sum -c SHA256SUMS` 两项 OK。
- `program --bus 0 --dry-run sample_handle.bin` 末行：`共 17 次页写（最后一页 6 字节，部分页写）`。地址 0x00…0x78 共 16 页 × 8 字节，加 0x80 的 6 字节。
- `PROGRAMMING.md` 约第 186、194 行：只用 0x00–0x85；第 7.5 节用同一镜像回读判断 WP。
- `94e393c:hardware/module-board/netlist.yaml` 约第 173–178、326–328 行：`default_bridge: [1, 2]`。

## J1

渲染第 1 页后的读数与 `AS31_J1_SPEC.md` 的表一致（轴向尺寸不在 PDF 文本层）。哈希：

```
C9144  582684  5728a7614f65e6ca177a98dd9088790032c19e72b128eb0aea3910ee0f93e7f5
C124406 544021 9aaf464aa81271f10be0ff7ae8dce64d20964e03e05e67b2758d779f11cd3dba
```

间隙（罩内最小 − 母座外廓最大）：

```
长边 (30.72 − 0.1) − (25.9 + 0.30) = 4.42
短边 (6.5 − 0.1) − (5.0 + 0.15)   = 1.25
20P 长边 2.54 × (20/2) + 0.5 = 25.9
```

## D4 与网表

`94e393c:hardware/module-board/PINMAP.md` 约第 125–140 行与 D4 表的 16 个焊盘名、网名、H2 针号一致。

同一文件 `netlist.yaml`：

```
DOCK_5V  → J2 A1, B1          （约 232–233 行）
DOCK_GND → J2 A2, B2          （约 245–246 行）
DOCK_SDA → J2 A8              （约 306 行）
DOCK_SCL → J2 B8              （约 315 行）
KEY_*    → J2 A3…A7 / B3…B7   （约 337–355 行）
封装     PAD-ARRAY-2x8-P2.54-D1.8
```

`main:hardware/ICD-0.2-DRAFT.md:143–145` 仍以「无损」结束三行错位表。

## 闸门

旧脚本 `3eb5cf8`，替身 OpenSCAD：

- fit：15 条 `n/a`，打印全部通过，EXIT 0
- cross：仅 `MOSAICO_W`，警告 22 条，打印「16 条等值、6 条包含、1 条供需」，EXIT 0

新脚本 `dea6c8f`，同一替身：fit EXIT 1；cross EXIT 1，`等值 1/16，包含 0/6，供需 0/1`。

`python3 -m unittest -v hardware/test_check_gates_fail_closed.py`（工作目录为 #50 头的 `hardware/` 检出）：`Ran 8 tests`，`OK`。

`CASES` 中期望 `solid` 的只有：

- `translate([0,-0.20,0]) modsolid()`
- `translate([0,-0.10,0]) top_frame()`

其余 13 项期望 `empty`。
