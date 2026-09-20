提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造

# 手持底座模块板 EEPROM 身份镜像取值（EEPROM V1，134 字节）

## 0. 范围与依据

对象：方案 D＋G 模块板上的 AT24C02（左槽，A0 = GPIO14 = 0 → 7 位地址 0x50）内的 134 字节 EEPROM V1 描述符。底座主板不含 EEPROM。

依据（全部为已核实源码，不是官方文档）：

| 来源 | 内容 | 位置 |
| --- | --- | --- |
| `esp-mosaico-bsp` commit `392860b1d1a123c3377947074b2af1f600e86c5d`，快照 `review/chrome/D1-module-interface/evidence/bsp/` | `mosaico_module_mgr.h` L23-25 magic/尺寸；L42-58 `mosaico_board_type_t`；L81-105 逻辑结构体 | 主机侧格式定义 |
| 同上 | `mosaico_module_mgr.c` L22-26 段偏移；L209-218 `crc16()`；L221-260 `parse_descriptor()`；L277-312 `type_to_name()`；L994-1004 `claim_matches_locked()`；L418-423 `read_eeprom()` | 主机侧校验、claim 与读取方式 |
| `review/chrome/D1-module-interface/BSP_AND_EEPROM.md` 第 3、4、7 节 | Chrome 对上述文件的核查结论 | 交叉核对 |
| `review/chrome/D1-module-interface/LEFT_SLOT.md` | 左槽 H2 引脚合同，GPIO14 专用 A0 | 参数区 GPIO 约束 |
| `/tmp/mosaico-v12/mosaico_eeprom_v1.py`（前次起点脚本） | 布局与本文件核对后重写为 `hardware/eeprom/mosaico_eeprom_v1.py` | 起点，不是依据 |

主机行为边界（决定本文件所有「理由」的前提）：`parse_descriptor()` 只校验 magic、三段 CRC、`param_length ≤ 64`；`claim_matches_locked()` 只比较 `board_type`；源码中**不存在** vendor_id / board_id 注册表，也没有按 vendor_id/board_id 选驱动的逻辑。因此除 `board_type` 外，所有字段的取值都是本项目自定义约定，只对本项目的主机驱动有意义。

## 1. 逐字段取值总表（样例镜像 `sample_handle.bin`）

小端字节列为镜像中的实际字节顺序。「状态」列：**决定** = 本提案的取值与理由；**ASSUMPTION** = 依赖未验证前提，见第 11 节。

| 偏移 | 长度 | 字段 | 取值 | 小端字节 | 理由摘要 | 状态 |
| --- | ---: | --- | --- | --- | --- | --- |
| 0x00 | 3 | magic | `"ESP"` | `45 53 50` | `MOSAICO_MODULE_MGR_EEPROM_MAGIC`，主机 memcmp 校验 | 源码事实 |
| 0x03 | 1 | board_type | `0x04` HANDLE | `04` | 第 2 节 | 决定 |
| 0x04 | 2 | board_id | `0x0101` | `01 01` | 第 3 节：高字节产品线 0x01（手持底座 方案 D＋G），低字节板卡 0x01（模块板） | 决定 |
| 0x06 | 2 | hw_version | `0x0100` | `00 01` | 第 4 节：模块板设计版 v1.0（首轮打板的原理图/PCB 版本） | 决定 |
| 0x08 | 2 | sw_version | `0x0100` | `00 01` | 第 4 节：主机侧合同 v1.0（KEY_* 语义 ＋ param v1） | 决定 |
| 0x0A | 2 | vendor_id | `0x4354` | `54 43` | 第 3 节：ASCII "CT"（ChromeTokyo），非 0x0000/0xFFFF | 决定，ASSUMPTION A-ID-02 |
| 0x0C | 4 | board_flags | `0x00000000` | `00 00 00 00` | 第 4 节：BSP 未定义位含义，保持 0 | 决定 |
| 0x10 | 4 | serial_number | `0x26090001` | `01 00 09 26` | 第 5 节：BCD YYMM `2609` ＋ 序号 `0001`；**样例专用** | 决定（样例值） |
| 0x14 | 32 | board_name | `"MK-HANDHELD-DOCK-MODULE"` ＋ 9 个 NUL | `4D 4B 2D 48 ...` | 第 6 节 | 决定 |
| 0x34 | 2 | desc_crc16 | `0xDBAE` | `AE DB` | CRC-16/MODBUS(0x00–0x33) | 计算值 |
| 0x36 | 4 | manufacture_date | `0x20260920` | `20 09 26 20` | 第 7 节：BCD YYYYMMDD，烧写日 | 决定（样例值） |
| 0x3A | 2 | batch_number | `0x0001` | `01 00` | 第 7 节：第 1 轮打板 | 决定 |
| 0x3C | 2 | factory_id | `0x0000` | `00 00` | 第 7 节：0 = 自行烧写 | 决定 |
| 0x3E | 2 | mfg_crc16 | `0x2E5C` | `5C 2E` | CRC-16/MODBUS(0x36–0x3D) | 计算值 |
| 0x40 | 2 | param_version | `0x0001` | `01 00` | 第 8 节 param v1 | 决定 |
| 0x42 | 2 | param_length | `24` | `18 00` | param v1 固定 24 字节 | 决定 |
| 0x44 | 64 | param_data | 见第 8 节 | `0A 01 14 02 FF×10 FF 00 DC 05 0B 00 00 00 00 00` ＋ 40 个 `00` | 第 8 节 | 决定 ＋ ASSUMPTION |
| 0x84 | 2 | param_crc16 | `0x3564` | `64 35` | CRC-16/MODBUS(0x40–0x83) | 计算值 |

样例镜像完整转储（`python3 mosaico_eeprom_v1.py dump sample_handle.bin`）：

```text
00000000: 4553 5004 0101 0001 0001 5443 0000 0000  ESP.......TC....
00000010: 0100 0926 4d4b 2d48 414e 4448 454c 442d  ...&MK-HANDHELD-
00000020: 444f 434b 2d4d 4f44 554c 4500 0000 0000  DOCK-MODULE.....
00000030: 0000 0000 aedb 2009 2620 0100 0000 5c2e  ...... .& ....\.
00000040: 0100 1800 0a01 1402 ffff ffff ffff ffff  ................
00000050: ffff ff00 dc05 0b00 0000 0000 0000 0000  ................
00000060: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000070: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000080: 0000 0000 6435                           ....d5
SHA-256: 1157e7e50b3378b3f4b27cbcc4d65d237d37c55dac00fb679457b6523683f57b
```

## 2. board_type = 0x04 HANDLE

### 2.1 取 0x04 的理由

1. **枚举内唯一贴合的类别。** `mosaico_board_type_t`（`mosaico_module_mgr.h` L42-58）中，与「按键输入设备」相关的只有 `HANDLE = 0x04`（`type_to_name` → `"Handle"`）与 `INTERACT = 0x16`（`"Interaction"`）。INTERACT 已被官方交互模块占用，且其驱动 `mosaico_interact_open()`（`mosaico_module_interact.c` L820-825）claim 到 INTERACT 后会按静态硬件表初始化 PIR、按钮、ADC、WS2812；若本板取 0x16，运行该驱动的应用会把本板当交互模块配置 ADC/RMT 引脚。Chrome 并行核对指出官方 `mosaico_module_joystick` 驱动 claim 的正是 HANDLE 并随后 `get_hardware_config/configure_hardware`（`BSP_AND_EEPROM.md` 第 7 节，来源未收进证据包，见 A-ID-03），说明官方对 HANDLE 的语义就是「手柄类 GPIO 输入模块」，与本板功能一致。
2. **claim 只比 board_type。** `claim_matches_locked()` L994-1004 的匹配条件是 FREE ＋ PRESENT ＋ VALID ＋ `board_type == expected_type`。本项目自有驱动（`/tmp/mosaico-v12/handheld_dock_skeleton.c` 与后续 `firmware/`）以 `MOSAICO_BOARD_TYPE_HANDLE` claim，EEPROM 必须写同一值，否则 claim 永远 `ESP_ERR_NOT_FOUND`/`TIMEOUT`。
3. **日志可读。** 管理器识别日志（`mosaico_module_mgr.c` L436-440）会打印 `type=Handle(0x04)`，便于到货验证时肉眼确认。

### 2.2 不取 0x03 DOCK 的理由

`DOCK = 0x03`（`"Dock"`）字面上也像「底座」，但源码中没有任何 DOCK 客户端驱动，Espressif 对该类别的语义（充电座？扩展座？）无法从源码核实；本板对主机呈现的**功能**是 10 个按键输入，供电／充电经 pin17 属纯硬件路径，主机固件不需要为此识别任何类别。选 HANDLE 描述功能，不选 DOCK 猜语义。

### 2.3 严禁 0x14

- `0x14` **不是** `mosaico_board_type_t` 成员：枚举在 `0x13 RELAY` 之后直接跳到 `0x16 INTERACT`，0x14／0x15 未定义。`mosaico_module_mgr_type_to_name(0x14)` 返回 `"Unknown"`，日志会显示 `type=Unknown(0x14)`。
- 没有任何驱动会以 0x14 claim；自有驱动若要用它，必须把非枚举值强转为 `mosaico_board_type_t`，一旦 Espressif 未来把 0x14 分配给别的模块类型，官方驱动就会 claim 本板并按别的硬件表配置 GPIO。
- `0x14 = 20` 恰是镜像中 `board_name` 字段的偏移（`parse_descriptor` L246 `raw + 0x14U`），也是 `OFF_BOARD_NAME` 常量；把偏移当类型值是最可能的混淆来源。工具 `mosaico_eeprom_v1.py` 的 `expect_handle()` 会拒绝任何非 0x04 的 board_type。

### 2.4 与官方 HANDLE 驱动共存的风险与对策

风险：若用户应用同时链接并调用官方 joystick 驱动（`SLOT_AUTO`），它可能先于自有驱动 claim 本板并按摇杆硬件表配置 GPIO（可能含 ADC 输入，尚无源码证实其是否把任何脚设为输出）。对策：

1. 自有驱动 claim 成功后立即 `mosaico_module_mgr_get_info(lease.slot, &info)`，核对 `info.eeprom.vendor_id == 0x4354 && info.eeprom.board_id == 0x0101 && (info.eeprom.sw_version >> 8) == 0x01`，不符则 `mosaico_module_mgr_release()` 并报错。BSP 不做这一步，必须由本项目驱动做。
2. 产品应用不链接官方 joystick 驱动；这是固件阶段的约束，记入 `firmware/` 任务。
3. 本板按键全部为无源接地开关（硬约束 5），任何驱动把这些脚配成输入都不会损坏硬件；被配成输出高并按下按键时会经开关短路到地——ESP32 GPIO 驱动电流有限，但仍应避免，属对策 1 的动机之一。

## 3. board_id 与 vendor_id

### 3.1 vendor_id = 0x4354

- 源码没有厂商注册表，任何值都不会被主机拒绝或识别；vendor_id 只服务于第 2.4 节的自有驱动核对与生产追溯。
- 取 ASCII `"CT"`（`0x43 0x54` → 数值 `0x4354`，小端存 `54 43`，十六进制转储中可直接读出 `TC`）。`CT` 指仓库所属组织 ChromeTokyo（`ChromeTokyo/MosaicoKeyboard`），不指任何真实厂商注册号。
- 排除项：`0x0000`（最可能是 Espressif 自家模块或未初始化值）、`0xFFFF`（空片值）、`0x303A`（Espressif 的 USB VID，不得冒用）。
- **ASSUMPTION A-ID-02**：Espressif 自家模块实际使用的 vendor_id/board_id 未知，假设与 `0x4354/0x0101` 不同。验证：到货后用 Mosaico 主机（或第 PROGRAMMING.md 第 4 节的外部编程器）转储用户手上的官方交互模块（`review/claude/hardware-revision/v12-module-interaction.jpg` 所示实物）EEPROM，`python3 mosaico_eeprom_v1.py dump` 读出其 vendor_id/board_id，登记到本节；若相同则改本项目值并重生成样例。

### 3.2 board_id = 0x0101

编码：高字节 = 产品线，低字节 = 板卡。

| board_id | 含义 | 状态 |
| --- | --- | --- |
| `0x0101` | 手持底座（方案 D＋G）· 模块板（转接板：2×10P 插槽位 ＋ AT24C02 ＋ 底部触点） | 本提案 |
| `0x0102` | 手持底座 · 底座主板（当前无 EEPROM，仅保留编号） | 保留 |
| `0x01FF` | 手持底座 · 实验/夹具板 | 保留 |
| `0x02xx` | 未来其他产品线 | 保留 |

同一 board_id 下，硬件改版靠 `hw_version` 区分，不另开 board_id。

## 4. hw_version、sw_version、board_flags

| 字段 | 编码 | 当前值 | 递增规则 |
| --- | --- | --- | --- |
| hw_version | 高字节 major、低字节 minor（与 BSP eFuse 版本宏 `BSP_HW_VERSION(major, minor)`，`esp_mosaico.c` L17 同一习惯） | `0x0100` = v1.0：模块板首轮打板的原理图/PCB 版本 | 网表或封装变化 → major＋1；仅换料/丝印/DNP 装配变化 → minor＋1。每轮 D-017 打板前由模块板任务确定并写入 `hardware/module-board/PINMAP.md` |
| sw_version | 同上 | `0x0100` = 合同 v1.0：KEY_* 十键语义 ＋ param v1 布局 ＋ 「按键无源接地、主机内部上拉」 | 不兼容变更（键数、param 布局重排）→ major＋1；向后兼容的 param 追加 → minor＋1。自有驱动只核对 major |
| board_flags | BSP 注释仅写 "Board capability flags"，未定义任何位 | `0x00000000` | 保持 0。本项目需要的标志放在 param_data（`dock_features`），避免与 Espressif 将来定义的位冲突 |

## 5. serial_number 策略

- 32 位，编码 `0xYYMMSSSS`：高 16 位为 BCD 年月（`26 09` = 2026-09，指**烧写**年月），低 16 位为该年月内的序号 `0x0001..0xFFFE`。
- 保留值：`0x00000000` = 未分配/开发件（`expect_handle()` 拒绝）；`0xFFFFFFFF` = 空片。
- 唯一性范围：同一 `board_id` 内唯一。登记表 `hardware/eeprom/SERIALS.csv`，每烧写一台追加一行（序列号、board_id、hw_version、日期、批次、烧写方式、镜像 SHA-256）。样例 `0x26090001` 已占用并标注「样例，不得复用」。
- 生成命令：`python3 mosaico_eeprom_v1.py build --serial 0x26090002 --date 20260921 --batch 1 --factory 0 -o unit-26090002.bin`。
- 序列号策略直接约束 PROGRAMMING.md 第 5 节：固定内容的工厂预烧会让所有单元序列号相同，因此预烧只能写序列号 0 的「半成品镜像」，再由主机在首次接入时补写；或按单元提供不同文件。

## 6. board_name

- 字段 32 字节，主机 `memcpy` 32 字节且**不保证 NUL 结尾**，日志用 `%.32s` 打印（`mosaico_module_mgr.c` L438-440）。本项目规定：ASCII 可打印字符 ≤ 31 字节，其余用 `0x00` 填充，保证任何 C 字符串函数安全。
- 取 `"MK-HANDHELD-DOCK-MODULE"`（23 字节）：`MK` = MosaicoKeyboard 仓库名，`HANDHELD-DOCK` = 产品，`MODULE` = 模块板（区别于底座主板）。不写版本号（版本在 hw_version），不写中文（避免多字节截断）。

## 7. 制造段（0x36–0x3D）

| 字段 | 编码 | 样例值 | 说明 |
| --- | --- | --- | --- |
| manufacture_date | BCD `0xYYYYMMDD`（BSP 注释 "Vendor-defined"） | `0x20260920` | 指 EEPROM **烧写**日期（本项目里等于模块板装配/验收日），不是 PCB 出厂日。十六进制转储中直接可读 |
| batch_number | 打板轮次（D-017 迭代序号） | `0x0001` | 与 hw_version 的区别：batch 是生产批次，hw_version 是设计版本；同一设计可能打两批 |
| factory_id | 烧写方 | `0x0000` | `0x0000` 自行烧写（方法 a/b）；`0x0001` 保留给国内 SMT 厂预烧；`0x0002` 保留给分销商编程服务；未核实任何一方能提供服务前不使用 |

## 8. param_data v1（本项目自定义，BSP 不解释）

`param_version = 0x0001`，`param_length = 24`。64 字节区剩余 40 字节填 0，**仍被参数段 CRC 覆盖**（CRC 覆盖 0x40–0x83 全部，`parse_descriptor` L232-235）。

| 区内偏移 | 绝对偏移 | 长度 | 字段 | 样例值 | 含义 | 状态 |
| --- | --- | ---: | --- | --- | --- | --- |
| 0x00 | 0x44 | 1 | key_count | `10` | 按键数 | 决定 |
| 0x01 | 0x45 | 1 | key_flags | `0x01` | bit0 `ACTIVE_LOW` = 1：按键接地，按下读 0（硬约束 5）；bit1 `KEYMAP_VALID` = 0：下方 key_gpio 表**未填**，主机用 PINMAP.md 编译进去的静态表；其余位保留 0 | 决定 |
| 0x02 | 0x46 | 1 | poll_period_ms | `20` | 建议轮询周期（硬约束 7：BSP 无中断通路，20–40 ms 轮询） | ASSUMPTION A-ID-04 |
| 0x03 | 0x47 | 1 | debounce_samples | `2` | 建议连续一致采样次数（20 ms × 2 = 40 ms 去抖） | ASSUMPTION A-ID-04 |
| 0x04–0x0D | 0x48–0x51 | 10 | key_gpio[10] | `FF ×10` | 按 `KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_A, KEY_B, KEY_X, KEY_Y, KEY_L, KEY_R` 顺序的左槽 canonical GPIO 号；`0xFF` = 未分配。**KEY_* → GPIO 的分配权属模块板任务（`hardware/module-board/PINMAP.md`），本文件不决定**；PINMAP 定稿后用 `build --keymap` 填表并置 `KEYMAP_VALID`。工具拒绝 GPIO14、重复值、非左槽 11 根之内的值 | 决定（占位） |
| 0x0E | 0x52 | 1 | spare_gpio | `0xFF` | 第 11 根备用 GPIO（预期为 PINMAP 未用的那一根） | 决定（占位） |
| 0x0F | 0x53 | 1 | reserved | `0x00` | | |
| 0x10 | 0x54 | 2 | battery_mah | `1500`（`DC 05`） | 标称电芯容量，仅供 UI 显示 | ASSUMPTION：任务书给定的参数化默认值 |
| 0x12 | 0x56 | 2 | dock_features | `0x000B` | bit0 `BATTERY` = 1；bit1 `USBC_CHARGE` = 1；bit2 `FUEL_GAUGE_ON_BUS` = 0（弹簧针接口 `DOCK_SDA/SCL` 预留但当前不装电量计）；bit3 `SUPPLIES_5V_IN` = 1（底座经 pin17 供电，方案前提） | 决定 |
| 0x14 | 0x58 | 1 | fuel_gauge_addr | `0x00` | 若日后加装电量计，其 7 位地址；工具拒绝 `0x50/0x51`（硬约束 6） | 决定 |
| 0x15–0x17 | 0x59–0x5B | 3 | reserved | `0` | | |
| 0x18–0x3F | 0x5C–0x83 | 40 | 未用 | `0` | 受 CRC 覆盖 | |

主机侧使用规则（写入 `firmware/` 任务）：

1. param_data 是**提示**，不是安全边界。主机只允许把 EEPROM 给出的 GPIO 配成**输入＋内部上拉**，绝不能按 EEPROM 内容把任何脚配成输出或复用为其他外设。
2. `KEYMAP_VALID = 0` 时使用编译进固件的 PINMAP 静态表；`= 1` 时先在主机侧再次校验 10 个值都在 `{55,53,19,48,18,13,17,12,16,15,4}` 且互异，再采用。任何失败退回静态表并记日志。
3. `sw_version` major 不等于驱动期望值时，不解释 param_data。

## 9. CRC 三段（与主机一致）

算法：CRC-16/MODBUS —— 初值 `0xFFFF`，逐字节异或，每位右移，最低位为 1 时异或 `0xA001`，无末尾异或，结果小端存放（`mosaico_module_mgr.c` L209-218；标准检查值 `crc16("123456789") = 0x4B37`，工具自测覆盖）。

| 段 | 覆盖范围 | 存放 | 样例值 |
| --- | --- | --- | --- |
| descriptor | `0x00–0x33`（52 字节） | `0x34–0x35` | `0xDBAE` |
| manufacturing | `0x36–0x3D`（8 字节） | `0x3E–0x3F` | `0x2E5C` |
| parameter | `0x40–0x83`（68 字节：param_version ＋ param_length ＋ 完整 64 字节 param_data） | `0x84–0x85` | `0x3564` |

134 字节中每个字节要么被某段 CRC 覆盖，要么就是 CRC 本身；工具自测逐字节翻转 134 次，全部被检出且只影响所属段。

## 10. 主机侧行为核对（BSP 做什么、不做什么）

| 行为 | 源码 | 对本项目的含义 |
| --- | --- | --- |
| 读取：先写 1 字节内部地址 0，再连续读 134 字节；7 位地址、100 kHz、超时 100 ms | `mosaico_module_mgr.c` L27-28、L373-390、L418-423 | AT24C02 的 0x86–0xFF 永不被读；镜像文件就是 134 字节 |
| 校验：magic → 三段 CRC → param_length ≤ 64 | L221-241 | 不校验 board_type 是否在枚举内、不校验 vendor_id/board_id/版本 |
| 扫描：默认 250 ms 探测、连续 3 次一致才改 presence；VALID 后不重复读，除非显式 rescan 或出错 | `mosaico_module_mgr.h` L29-33；`.c` L458-600 | 重烧 EEPROM 后主机不会自动刷新描述，须 `mosaico_module_mgr_request_rescan()` 或重新插拔/复位 |
| claim：FREE ＋ PRESENT ＋ VALID ＋ board_type 相等 | L994-1004 | 见第 2.4 节，vendor_id/board_id 核对由自有驱动补做 |
| 识别日志格式 `"Module identified: slot=%s type=%s(0x%02X) id=0x%04X name=%.32s"` | L438-440 | 本镜像预期日志：`Module identified: slot=left type=Handle(0x04) id=0x0101 name=MK-HANDHELD-DOCK-MODULE` |
| 拔出后保留最后一次有效 eeprom 字段、descriptor 置 UNKNOWN；不自动释放 lease | L513-531 | 自有驱动须订阅事件或轮询 presence，主动 release |
| 上电顺序：VCC_3V3 → I2C1 → GPIO14=0 | `subboard.c` L123-152 | 与 pin17 供电无关；EEPROM 从 pin19 取电即可被读到（硬约束 1、3） |

## 11. 假设清单与到货验证步骤

| 编号 | ASSUMPTION | 到货后验证 | 关闭后动作 |
| --- | --- | --- | --- |
| A-ID-01 | 实物出厂固件／用户将刷入的 BSP 与 commit 392860b1 的 EEPROM V1 格式相同 | 刷 `eeprom_program_example.c` 或任一 BSP 示例，插入烧好的模块板，串口应出现第 10 节的识别日志；另用主机转储官方交互模块 EEPROM，`verify` 应返回 `ESP_OK` | 不同则按新源码更新工具与本文件 |
| A-ID-02 | Espressif 自家模块的 vendor_id/board_id 与 `0x4354/0x0101` 不同 | 转储官方交互模块，`dump` 读值登记到第 3.1 节 | 相同则改值、重生成样例、更新 SHA256SUMS |
| A-ID-03 | 官方 `mosaico_module_joystick` 驱动以 HANDLE claim，且默认应用不会自动运行它 | 在同一 commit 的 BSP 仓库读 `mosaico_module_joystick/mosaico_joystick.c` L534-584 与其 README；检查用户将运行的应用是否链接该组件 | 若默认应用会自动 claim HANDLE，评估改用其他类型或在应用层排除 |
| A-ID-04 | 轮询 20 ms、去抖 2 次采样足够 | 实物按键抖动用示波器或固件统计测量，调整后 `build --poll-ms/--debounce` | 更新样例与本表 |
| A-ID-05 | 样例 serial/date 仅为样例 | 实物烧写一律用 `build` 生成新序列号并登记 SERIALS.csv | 无 |
| A-ID-06 | 主机 `%.32s` 与 31 字节 ＋ NUL 的 board_name 兼容 | 观察识别日志名称完整 | 无 |

## 12. 变更规则

- 改任何默认值 → 运行 `python3 mosaico_eeprom_v1.py selftest`（会因登记的 SHA-256 不符而失败）→ 更新 `SAMPLE_SHA256` 常量 → 重生成 `sample_handle.bin`、`sample_handle_image.h`、`SHA256SUMS` → 更新本文件第 1、9 节样例值。
- 本文件与 `mosaico_eeprom_v1.py` 中 `HANDLE_*`／`SAMPLE_*`／`ParamV1` 默认值必须一致；工具是数值的唯一来源，本文件是理由的唯一来源。
- KEY_* → GPIO 表只从 `hardware/module-board/PINMAP.md` 抄入，不在此处决定。
