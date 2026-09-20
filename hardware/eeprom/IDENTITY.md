提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造

# 手持底座模块板 EEPROM 身份镜像取值（EEPROM V1，134 字节）

## 0. 范围与依据

对象：方案 D＋G 模块板上的 AT24C02 兼容 EEPROM（左槽，A0 = GPIO14 = 0 → 7 位地址 0x50）内的 134 字节 EEPROM V1 描述符。底座主板不含 EEPROM。电气接法（VCC 来自 pin19、WP、A1/A2、上拉 DNP）不在本文件，见 `hardware/ICD-0.2-DRAFT.md` 第 7.1 节与 `PROGRAMMING.md` 第 2 节。

依据（全部为已核实源码或已合入 main 的权威输入，不是 Espressif 官方文档）：

| 来源 | 内容 | 用途 |
| --- | --- | --- |
| `esp-mosaico-bsp` commit `392860b1d1a123c3377947074b2af1f600e86c5d`，快照 `review/chrome/D1-module-interface/evidence/bsp/` | `mosaico_module_mgr.h` L23-25 magic/尺寸；L42-58 `mosaico_board_type_t`；L81-105 逻辑结构体 | 主机侧格式定义 |
| 同上 | `mosaico_module_mgr.c` L22-26 段偏移；L199-207 `read_le16/32`；L209-218 `crc16()`；L221-260 `parse_descriptor()`；L277-312 `type_to_name()`；L373-390 `attach_eeprom_devices()`；L418-423 `read_eeprom()`；L439-442 识别日志；L481-483 probe 返回值解释；L994-1004 `claim_matches_locked()` | 主机侧校验、claim、读取与日志 |
| 同 commit 的本地完整克隆 `/tmp/mosaico-v12/esp-mosaico-bsp`（`git log -1` = `392860b`；**未收进证据包**，Chrome 复核时可按同 commit 重取） | `components/mosaico_module_joystick/mosaico_joystick.c` L189-206 `get_hardware_config()`、L441-497 `configure_hardware()`、L533-584 `mosaico_joystick_new()`、L209-222 `check_present_locked()`；`components/mosaico_module_interact/mosaico_module_interact.c` L137-153 静态硬件表、L803、L820-825 claim INTERACT；`components/esp-mosaico-bsp/onboard/esp_mosaico.c` L17 `BSP_HW_VERSION()`、L33-59 `detect_board_variant()` | 官方 HANDLE 驱动行为（第 2 节）、版本编码习惯（第 4 节） |
| `review/chrome/D1-module-interface/BSP_AND_EEPROM.md` 第 3、4、7 节 | Chrome 对上述文件的核查结论 | 交叉核对 |
| `review/chrome/D1-module-interface/LEFT_SLOT.md` | 左槽 H2 引脚合同，GPIO14 专用 A0 | 参数区 GPIO 约束 |
| `hardware/ICD-0.2-DRAFT.md` 第 7 节、第 9 节 | EEPROM 身份要求：board_name 建议、param_data 写 KEY 映射版本号、网络命名 | 本文件必须与之一致（第 13 节逐条对应） |
| `hardware/ASSUMPTIONS.md` AS-01～AS-30 | 已登记假设；本文件新增假设从 `AS-31-eeprom-n` 起（汇总阶段由主控统一编号） | 假设编号 |
| `hardware/module-board/PINMAP.md`（分支 `claude/design-d/module-board` WIP，**未合入 main**） | KEY_* → H2 针号 → GPIO 的唯一权威分配表；本文件只引用其**版本号**，不抄其 GPIO 值 | 第 8 节 `keymap_version` |

主机行为边界（决定本文件所有「理由」的前提）：`parse_descriptor()` 只校验 magic、三段 CRC、`param_length ≤ 64`；`claim_matches_locked()` 只比较 `board_type`；源码中**不存在** vendor_id / board_id 注册表，也没有按 vendor_id/board_id 选驱动的逻辑。因此除 `board_type` 外，所有字段的取值都是本项目自定义约定，只对本项目的主机驱动有意义。

## 1. 逐字段取值总表（样例镜像 `sample_handle.bin`）

小端字节列为镜像中的实际字节顺序。「状态」列：**决定** = 本提案的取值与理由；**ASSUMPTION** = 依赖未验证前提，见第 11 节。

| 偏移 | 长度 | 字段 | 取值 | 小端字节 | 理由摘要 | 状态 |
| --- | ---: | --- | --- | --- | --- | --- |
| 0x00 | 3 | magic | `"ESP"` | `45 53 50` | `MOSAICO_MODULE_MGR_EEPROM_MAGIC`，主机 memcmp 校验 | 源码事实 |
| 0x03 | 1 | board_type | `0x04` HANDLE | `04` | 第 2 节 | 决定（ASSUMPTION AS-20） |
| 0x04 | 2 | board_id | `0x0101` | `01 01` | 第 3 节：高字节产品线 0x01（手持底座 方案 D＋G），低字节板卡 0x01（模块板） | 决定（AS-20、AS-31-eeprom-2） |
| 0x06 | 2 | hw_version | `0x0100` | `00 01` | 第 4 节：模块板设计版 v1.0（首轮打板的原理图/PCB 版本） | 决定 |
| 0x08 | 2 | sw_version | `0x0100` | `00 01` | 第 4 节：主机侧合同 v1.0（KEY_* 语义 ＋ param v1） | 决定 |
| 0x0A | 2 | vendor_id | `0x4354` | `54 43` | 第 3 节：ASCII "CT"（ChromeTokyo），非 0x0000/0xFFFF | 决定（AS-20、AS-31-eeprom-2） |
| 0x0C | 4 | board_flags | `0x00000000` | `00 00 00 00` | 第 4 节：BSP 未定义位含义，保持 0 | 决定 |
| 0x10 | 4 | serial_number | `0x26090001` | `01 00 09 26` | 第 5 节：BCD YYMM `2609` ＋ 序号 `0001`；**样例专用** | 决定（样例值） |
| 0x14 | 32 | board_name | `"MOSAICO-DOCK-MODULE-V1.0"` ＋ 8 个 NUL | `4D 4F 53 41 49 43 4F 2D 44 4F 43 4B 2D 4D 4F 44 55 4C 45 2D 56 31 2E 30 00…` | 第 6 节：ICD 7.2 建议的前缀 ＋ hw_version 派生的版本后缀 | 决定 |
| 0x34 | 2 | desc_crc16 | `0xF889` | `89 F8` | CRC-16/MODBUS(0x00–0x33) | 计算值 |
| 0x36 | 4 | manufacture_date | `0x20260920` | `20 09 26 20` | 第 7 节：BCD YYYYMMDD，烧写日 | 决定（样例值） |
| 0x3A | 2 | batch_number | `0x0001` | `01 00` | 第 7 节：第 1 轮打板 | 决定 |
| 0x3C | 2 | factory_id | `0x0000` | `00 00` | 第 7 节：0 = 自行烧写 | 决定 |
| 0x3E | 2 | mfg_crc16 | `0x2E5C` | `5C 2E` | CRC-16/MODBUS(0x36–0x3D) | 计算值 |
| 0x40 | 2 | param_version | `0x0001` | `01 00` | 第 8 节 param v1 | 决定 |
| 0x42 | 2 | param_length | `24` | `18 00` | param v1 固定 24 字节 | 决定 |
| 0x44 | 64 | param_data | 见第 8 节 | `0A 01 14 02 FF×10 FF 01 DC 05 0B 00 00 00 00 00` ＋ 40 个 `00` | 第 8 节（区内 0x0F = keymap_version = 1） | 决定 ＋ ASSUMPTION |
| 0x84 | 2 | param_crc16 | `0xD848` | `48 D8` | CRC-16/MODBUS(0x40–0x83) | 计算值 |

样例镜像完整转储（`xxd sample_handle.bin`；字段级转储见 `README.md` 贴出的 `dump` 输出）：

```text
00000000: 4553 5004 0101 0001 0001 5443 0000 0000  ESP.......TC....
00000010: 0100 0926 4d4f 5341 4943 4f2d 444f 434b  ...&MOSAICO-DOCK
00000020: 2d4d 4f44 554c 452d 5631 2e30 0000 0000  -MODULE-V1.0....
00000030: 0000 0000 89f8 2009 2620 0100 0000 5c2e  ...... .& ....\.
00000040: 0100 1800 0a01 1402 ffff ffff ffff ffff  ................
00000050: ffff ff01 dc05 0b00 0000 0000 0000 0000  ................
00000060: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000070: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000080: 0000 0000 48d8                           ....H.
SHA-256: 119e991a6a87b5b1afa18feefdbcb1fdb86cadc564c7ce7375133da0a9810832
```

## 2. board_type = 0x04 HANDLE

### 2.1 取 0x04 的理由

1. **枚举内唯一贴合的类别。** `mosaico_board_type_t`（`mosaico_module_mgr.h` L42-58）中，与「按键输入设备」相关的只有 `HANDLE = 0x04`（`type_to_name` → `"Handle"`）与 `INTERACT = 0x16`（`"Interaction"`）。INTERACT 已被官方交互模块占用，其驱动 `mosaico_interact_open()`（`mosaico_module_interact.c` L803 init 管理器，L820-825 以 INTERACT claim）claim 后按静态硬件表（L137-153：GPIO53 LDR、GPIO48 IR、GPIO13/12 按键、GPIO4 PIR、GPIO15 WS2812）初始化 PIR、按钮、ADC、WS2812；若本板取 0x16，运行该驱动的应用会把本板当交互模块，并把 GPIO15 配成 **RMT 输出**驱动 WS2812——对无源按键板无害，但已属把主机脚配成输出，违背第 8 节规则 1 的精神。官方 `mosaico_module_joystick` 驱动（`mosaico_joystick.c` L558-563）以 `MOSAICO_BOARD_TYPE_HANDLE` claim，其 README 第一句即 "discovers an EEPROM programmed as `MOSAICO_BOARD_TYPE_HANDLE`"，说明官方对 HANDLE 的语义就是「手柄类输入模块」，与本板功能一致。
2. **claim 只比 board_type。** `claim_matches_locked()` L994-1004 的匹配条件是 FREE ＋ PRESENT ＋ VALID ＋ `board_type == expected_type`。本项目自有驱动（分支 `claude/design-d/firmware` 的 `firmware/dock_handle/dock_handle.c`，前身 `/tmp/mosaico-v12/handheld_dock_skeleton.c`）以 `MOSAICO_BOARD_TYPE_HANDLE` claim，EEPROM 必须写同一值，否则 claim 永远 `ESP_ERR_NOT_FOUND`/`ESP_ERR_TIMEOUT`。
3. **日志可读。** 管理器识别日志（`mosaico_module_mgr.c` L439-442）会打印 `type=Handle(0x04)`，便于到货验证时肉眼确认。

### 2.2 不取 0x03 DOCK 的理由

`DOCK = 0x03`（`"Dock"`）字面上也像「底座」，但源码中没有任何 DOCK 客户端驱动，Espressif 对该类别的语义（充电座？扩展座？）无法从源码核实；本板对主机呈现的**功能**是 10 个按键输入，供电／充电经 pin17 属纯硬件路径（硬约束 1），主机固件不需要为此识别任何类别。选 HANDLE 描述功能，不选 DOCK 猜语义。

### 2.3 严禁 0x14

- `0x14` **不是** `mosaico_board_type_t` 成员：枚举在 `0x13 RELAY` 之后直接跳到 `0x16 INTERACT`，0x14／0x15 未定义。`mosaico_module_mgr_type_to_name(0x14)` 返回 `"Unknown"`，日志会显示 `type=Unknown(0x14)`。
- 没有任何驱动会以 0x14 claim；自有驱动若要用它，必须把非枚举值强转为 `mosaico_board_type_t`，一旦 Espressif 未来把 0x14 分配给别的模块类型，官方驱动就会 claim 本板并按别的硬件表配置 GPIO。
- `0x14 = 20` 恰是镜像中 `board_name` 字段的偏移（`parse_descriptor` L246 `raw + 0x14U`），也是工具中的 `OFF_BOARD_NAME` 常量；把偏移当类型值是最可能的混淆来源。工具 `mosaico_eeprom_v1.py` 的 `expect_handle()` 会拒绝任何非 0x04 的 board_type。

### 2.4 与官方 HANDLE 驱动共存：源码核实的行为与对策

官方 joystick 驱动被调用（`mosaico_joystick_new()`，L533-584；默认配置 `slot` 可为 `SLOT_AUTO`）时的行为，已在同 commit 源码中逐行核实：

| 步骤 | 源码 | 对本板的后果 |
| --- | --- | --- |
| 以 HANDLE claim，任一槽 | L558-563 | 若本板在槽内且 FREE，会被它抢先 claim |
| `get_hardware_config()` 静态表：X = GPIO48、Y = GPIO53（经 `bsp_subboard_map_gpio` 映射，左槽原样）；按键 GPIO16（`active_high = true`）、GPIO4、GPIO15、GPIO12、GPIO13（`active_high = false`） | L189-206 | 不读 EEPROM 决定引脚；vendor_id/board_id 完全不参与（`check_present_locked()` L209-222 也只看 board_type） |
| `configure_hardware()`：GPIO48/53 经 `adc_oneshot_io_to_channel()` 配成 **ADC 输入**；5 个按键脚 `gpio_config()` 为 **`GPIO_MODE_INPUT`**，GPIO16 开**下拉**、其余开上拉；`intr_type` 禁用 | L441-497 | **没有任何脚被配成输出**；对无源接地开关板无电气损坏风险。功能上：ADC 读到的是开关电平；GPIO16 被下拉后开关无论按否都读 0 |
| 之后周期性 `mosaico_joystick_read()` 采样、校准 | README 示例 | 本板的键被当作摇杆数据，功能错误但无害 |

据此，上一版本文件里「尚无源码证实其是否把任何脚设为输出」的保留已关闭：**不设输出**。剩余风险是功能层面的「被错误认领」，对策：

1. 自有驱动 claim 成功后立即 `mosaico_module_mgr_get_info(lease.slot, &info)`，核对 `info.eeprom.vendor_id == 0x4354 && info.eeprom.board_id == 0x0101 && (info.eeprom.sw_version >> 8) == 0x01`，不符则 `mosaico_module_mgr_release()` 并报错。BSP 不做这一步，必须由本项目驱动做。分支 `claude/design-d/firmware` 的 `dock_handle.c` L259-274 已实现可配置的 vendor_id/board_id 核对，与此一致。
2. 产品应用不链接官方 `mosaico_module_joystick` 组件；这是固件阶段的约束，记入 `firmware/` 任务。**ASSUMPTION AS-31-eeprom-1**：用户将运行的默认应用不会自动调用 `mosaico_joystick_new()`；验证见第 11 节。
3. 本板按键全部为无源接地开关（硬约束 5），任何驱动把这些脚配成输入（含 ADC、下拉）都不会损坏硬件；第 8 节规则 1 禁止自有驱动按 EEPROM 内容配任何输出，使「被别的驱动配成输出」成为唯一残余电气风险，而 2.1 已证官方 HANDLE 驱动不这么做。

## 3. board_id 与 vendor_id

### 3.1 vendor_id = 0x4354

- 源码没有厂商注册表，任何值都不会被主机拒绝或识别；vendor_id 只服务于第 2.4 节的自有驱动核对与生产追溯。
- 取 ASCII `"CT"`（`0x43 0x54` → 数值 `0x4354`，小端存 `54 43`，十六进制转储中可直接读出 `TC`）。`CT` 指仓库所属组织 ChromeTokyo（`ChromeTokyo/MosaicoKeyboard`），不指任何真实厂商注册号。
- 排除项：`0x0000`（最可能是 Espressif 自家模块或未初始化值）、`0xFFFF`（空片值）、`0x303A`（Espressif 的 USB VID，不得冒用）。
- **ASSUMPTION AS-31-eeprom-2**（细化 `ASSUMPTIONS.md` AS-20）：Espressif 自家模块实际使用的 vendor_id/board_id 未知，假设与 `0x4354/0x0101` 不同。验证：到货后用 Mosaico 主机（或 `PROGRAMMING.md` 第 4 节的外部编程器）转储用户手上的官方交互模块（`review/claude/hardware-revision/v12-module-interaction.jpg` 所示实物）EEPROM，`python3 mosaico_eeprom_v1.py dump` 读出其 vendor_id/board_id 登记到本节；若相同则改本项目值并重生成样例。

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
| hw_version | 高字节 major、低字节 minor（与 BSP eFuse 版本宏 `BSP_HW_VERSION(major, minor)`，`esp_mosaico.c` L17，同一习惯） | `0x0100` = v1.0：模块板首轮打板的原理图/PCB 版本 | 网表或封装变化 → major＋1；仅换料/丝印/DNP 装配变化 → minor＋1。每轮 D-017 打板前由模块板任务确定并写入 `hardware/module-board/PINMAP.md`；**改 hw_version 会同步改 board_name 后缀**（第 6 节） |
| sw_version | 同上 | `0x0100` = 合同 v1.0：KEY_* 十键语义 ＋ param v1 布局 ＋ 「按键无源接地、主机内部上拉」 | 不兼容变更（键数、param 布局重排）→ major＋1；向后兼容的 param 追加 → minor＋1。自有驱动只核对 major |
| board_flags | BSP 注释仅写 "Board capability flags"，未定义任何位 | `0x00000000` | 保持 0。本项目需要的标志放在 param_data（`dock_features`），避免与 Espressif 将来定义的位冲突 |

## 5. serial_number 策略

- 32 位，编码 `0xYYMMSSSS`：高 16 位为 BCD 年月（`26 09` = 2026-09，指**烧写**年月），低 16 位为该年月内的序号 `0x0001..0xFFFE`。
- 保留值：`0x00000000` = 未分配/开发件（`expect_handle()` 拒绝）；`0xFFFFFFFF` = 空片。
- 唯一性范围：同一 `board_id` 内唯一。登记表 `hardware/eeprom/SERIALS.csv`，每烧写一台追加一行（序列号、board_id、hw_version、日期、批次、烧写方式、镜像 SHA-256）。样例 `0x26090001` 已占用并标注「样例，不得复用」；**样例的 serial/date 只是样例**，实物烧写一律用 `build` 生成新序列号并登记（规则，不是假设）。
- 生成命令：`python3 mosaico_eeprom_v1.py build --serial 0x26090002 --date 20260921 --batch 1 --factory 0 -o unit-26090002.bin`（`build` 会打印镜像 SHA-256，直接抄入 `SERIALS.csv`）。
- 序列号策略直接约束 `PROGRAMMING.md` 第 5 节：固定内容的工厂预烧会让所有单元序列号相同，因此预烧只能写序列号 0 的「半成品镜像」，再由主机在首次接入时补写；或按单元提供不同文件。

## 6. board_name

- 字段 32 字节，主机 `memcpy` 32 字节且**不保证 NUL 结尾**，日志用 `%.32s` 打印（`mosaico_module_mgr.c` L439-442；`%.32s` 遇 NUL 或 32 字节即止，因此 ≤ 31 字节 ＋ NUL 填充与之兼容，这是 C 标准行为，不是假设）。本项目规定：ASCII 可打印字符 ≤ 31 字节，其余用 `0x00` 填充，保证任何 C 字符串函数安全。
- 取值 `MOSAICO-DOCK-MODULE-V<major>.<minor>`，由 hw_version 派生（工具 `handle_board_name()`）；样例 `"MOSAICO-DOCK-MODULE-V1.0"`（24 字节）。最长情形 `-V255.255` 共 28 字节，仍留 NUL。
- 理由：
  1. `hardware/ICD-0.2-DRAFT.md` 第 7.2 节建议「含 `MOSAICO-DOCK-MODULE` 与版本」，本文件遵从。上一版 WIP 用的 `MK-HANDHELD-DOCK-MODULE` 不含版本，与 ICD 不一致，已弃用。
  2. 管理器识别日志（L439-442）**只打印 board_type、board_id、board_name，不打印 hw_version**；把版本缀在名字里，串口上一眼就能分辨是哪一轮打板的模块板，到货验证与 D-017 迭代都用得上。
  3. 不写中文（避免多字节截断）；用 `-` 不用空格（便于 grep 日志）。
- 一致性由工具保证：`expect_handle()` 检查 board_name 以 `MOSAICO-DOCK-MODULE` 开头且等于 hw_version 派生名；`build --name` 可覆盖，但覆盖后 `expect_handle` 会报不一致（用于夹具/实验板）。

## 7. 制造段（0x36–0x3D）

| 字段 | 编码 | 样例值 | 说明 |
| --- | --- | --- | --- |
| manufacture_date | BCD `0xYYYYMMDD`（BSP 注释 "Vendor-defined"） | `0x20260920` | 指 EEPROM **烧写**日期（本项目里等于模块板装配/验收日），不是 PCB 出厂日。十六进制转储中直接可读。样例保持首版日期不变，避免 `SERIALS.csv` 登记漂移 |
| batch_number | 打板轮次（D-017 迭代序号） | `0x0001` | 与 hw_version 的区别：batch 是生产批次，hw_version 是设计版本；同一设计可能打两批 |
| factory_id | 烧写方 | `0x0000` | `0x0000` 自行烧写（方法 a/b）；`0x0001` 保留给国内 SMT 厂预烧；`0x0002` 保留给分销商编程服务；未核实任何一方能提供服务前不使用 |

## 8. param_data v1（本项目自定义，BSP 不解释）

`param_version = 0x0001`，`param_length = 24`。64 字节区剩余 40 字节填 0，**仍被参数段 CRC 覆盖**（CRC 覆盖 0x40–0x83 全部，`parse_descriptor` L232-235）。

| 区内偏移 | 绝对偏移 | 长度 | 字段 | 样例值 | 含义 | 状态 |
| --- | --- | ---: | --- | --- | --- | --- |
| 0x00 | 0x44 | 1 | key_count | `10` | 按键数 | 决定 |
| 0x01 | 0x45 | 1 | key_flags | `0x01` | bit0 `ACTIVE_LOW` = 1：按键接地，按下读 0（硬约束 5）；bit1 `KEYMAP_VALID` = 0：下方 key_gpio 镜像表**未填**，主机用编译进去的 PINMAP.md 静态表；其余位保留 0 | 决定 |
| 0x02 | 0x46 | 1 | poll_period_ms | `20` | 建议轮询周期（硬约束 7：BSP 无中断通路，20–40 ms 轮询） | ASSUMPTION AS-23 |
| 0x03 | 0x47 | 1 | debounce_samples | `2` | 建议连续一致采样次数（20 ms × 2 = 40 ms 去抖） | ASSUMPTION AS-23 |
| 0x04–0x0D | 0x48–0x51 | 10 | key_gpio[10] | `FF ×10` | 按 `KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_A, KEY_B, KEY_X, KEY_Y, KEY_L, KEY_R` 顺序的左槽 canonical GPIO 号的**可选镜像**；`0xFF` = 未填。**KEY_* → GPIO 的分配权属 `hardware/module-board/PINMAP.md`，本文件与本镜像都不决定**；填表只能用 `build --keymap` 从 PINMAP.md 抄入并置 `KEYMAP_VALID`。工具拒绝 GPIO14、重复值、非左槽 11 根之内的值、填表却不声明 keymap_version | 决定（默认不填） |
| 0x0E | 0x52 | 1 | spare_gpio | `0xFF` | 第 11 根备用 GPIO（PINMAP.md 未用的那一根）的可选镜像 | 决定（默认不填） |
| 0x0F | 0x53 | 1 | **keymap_version** | `1` | **KEY_* → GPIO 映射版本号**（ICD 7.2 要求写入 param_data 供固件核对）= `hardware/module-board/PINMAP.md` 的 `KEYMAP_VERSION`。`0` = 未声明（主机不核对）。主机把它与编译进固件的静态表所声明的版本比较，不等则拒绝启用按键并记日志——这正是当前两个 WIP 分支之间存在的差异（`claude/design-d/firmware` 的 `dock_handle_pinmap.h` 默认表与 PINMAP.md 不同）要防的事故 | 决定；ASSUMPTION AS-31-eeprom-3 |
| 0x10 | 0x54 | 2 | battery_mah | `1500`（`DC 05`） | 标称电芯容量，仅供 UI 显示 | ASSUMPTION AS-12 |
| 0x12 | 0x56 | 2 | dock_features | `0x000B` | bit0 `BATTERY` = 1；bit1 `USBC_CHARGE` = 1；bit2 `FUEL_GAUGE_ON_BUS` = 0（弹簧针接口 `DOCK_SDA/SCL` 预留但默认不装电量计，`R_LINK` DNP，ICD EL-D-06/10）；bit3 `SUPPLIES_5V_IN` = 1（底座经 pin17 供电，方案前提） | 决定 |
| 0x14 | 0x58 | 1 | fuel_gauge_addr | `0x00` | 若日后加装电量计，其 7 位地址；工具拒绝 `0x50/0x51`（硬约束 6）与 I²C 保留地址 | 决定 |
| 0x15–0x17 | 0x59–0x5B | 3 | reserved | `0` | | |
| 0x18–0x3F | 0x5C–0x83 | 40 | 未用 | `0` | 受 CRC 覆盖 | |

主机侧使用规则（提给 `firmware/` 任务）：

1. param_data 是**提示**，不是安全边界。主机只允许把 EEPROM 给出的 GPIO 配成**输入＋内部上拉**，绝不能按 EEPROM 内容把任何脚配成输出或复用为其他外设。
2. `keymap_version` 与固件编译进的 PINMAP 版本常量比较：相等或 EEPROM 为 0 → 使用静态表；不等 → 不启用按键，记日志并上报（防止「模块板按 PINMAP v2 打板、固件仍是 v1」的键位错乱）。
3. `KEYMAP_VALID = 0` 时使用编译进固件的 PINMAP 静态表；`= 1` 时先在主机侧再次校验 10 个值都在 `{55,53,19,48,18,13,17,12,16,15,4}` 且互异，再采用，且仍受规则 2 约束。任何失败退回静态表并记日志。
4. `sw_version` major 不等于驱动期望值时，不解释 param_data。

## 9. CRC 三段（与主机一致）

算法：CRC-16/MODBUS —— 初值 `0xFFFF`，逐字节异或，每位右移，最低位为 1 时异或 `0xA001`，无末尾异或，结果小端存放（`mosaico_module_mgr.c` L209-218；标准检查值 `crc16("123456789") = 0x4B37`，工具自测覆盖）。

| 段 | 覆盖范围 | 存放 | 样例值 |
| --- | --- | --- | --- |
| descriptor | `0x00–0x33`（52 字节） | `0x34–0x35` | `0xF889` |
| manufacturing | `0x36–0x3D`（8 字节） | `0x3E–0x3F` | `0x2E5C` |
| parameter | `0x40–0x83`（68 字节：param_version ＋ param_length ＋ 完整 64 字节 param_data） | `0x84–0x85` | `0xD848` |

134 字节中每个字节要么被某段 CRC 覆盖，要么就是 CRC 本身；工具自测逐字节翻转 134 次，全部被检出且只影响所属段（`README.md` 贴有实际运行输出）。

## 10. 主机侧行为核对（BSP 做什么、不做什么）

| 行为 | 源码 | 对本项目的含义 |
| --- | --- | --- |
| 读取：先写 1 字节内部地址 0，再连续读 134 字节；7 位地址、100 kHz、超时 100 ms | `mosaico_module_mgr.c` L27-28、L373-390、L418-423 | EEPROM 的 0x86–0xFF 永不被读；镜像文件就是 134 字节 |
| 校验：magic → 三段 CRC → param_length ≤ 64 | L221-241 | 不校验 board_type 是否在枚举内、不校验 vendor_id/board_id/版本 |
| 扫描：默认 250 ms 探测、连续 3 次一致才改 presence；VALID 后不重复读，除非显式 rescan 或出错 | `mosaico_module_mgr.h` L29-33；`.c` L458-600 | 重烧 EEPROM 后主机不会自动刷新描述，须 `mosaico_module_mgr_request_rescan()` 或重新插拔/复位 |
| probe 返回值：`ESP_OK` 应答、`ESP_ERR_NOT_FOUND` 未应答、其他为总线错误 | L481-483 | 烧写时的 Acknowledge Polling 沿用同一解释（`PROGRAMMING.md` 3.2 步 6） |
| claim：FREE ＋ PRESENT ＋ VALID ＋ board_type 相等 | L994-1004 | 见第 2.4 节，vendor_id/board_id 核对由自有驱动补做 |
| 识别日志格式 `"Module identified: slot=%s type=%s(0x%02X) id=0x%04X name=%.32s"` | L439-442 | 本镜像预期日志：`Module identified: slot=left type=Handle(0x04) id=0x0101 name=MOSAICO-DOCK-MODULE-V1.0` |
| 拔出后保留最后一次有效 eeprom 字段、descriptor 置 UNKNOWN；不自动释放 lease | L513-531 | 自有驱动须订阅事件或轮询 presence，主动 release |
| 上电顺序：VCC_3V3 → I2C1 → GPIO14=0 | `subboard.c` L123-152 | 与 pin17 供电无关；EEPROM 从 pin19 取电即可被读到（硬约束 1、3） |
| 管理器**没有**写 EEPROM 的 API | 全文件无 `i2c_master_transmit(` | 烧写由本目录的示例固件或外部编程器完成（`PROGRAMMING.md`） |

## 11. 假设清单与到货验证步骤

已在 `hardware/ASSUMPTIONS.md` 登记、本文件直接引用的假设：**AS-12**（电池 1500 mAh，param `battery_mah`）、**AS-16**（实物固件与 BSP 392860b1 的 EEPROM V1 格式相同；验证：刷 `eeprom_program_example.c` 或任一 BSP 示例，插入烧好的模块板，串口应出现第 10 节识别日志；另转储官方交互模块 EEPROM，`verify` 应返回 `ESP_OK`）、**AS-20**（身份字段官方未分配、管理器只校验 magic/CRC/param_length）、**AS-23**（20 ms 轮询 ＋ 2 次采样去抖；验证：实物按键抖动用示波器或固件统计测量，调整后 `build --poll-ms/--debounce` 并更新样例）。

本目录新增（临时编号，汇总阶段由主控并入 ASSUMPTIONS.md 并统一为 AS-31 起的正式编号；`PROGRAMMING.md` 第 8 节的 AS-31-eeprom-4～8 与此表连续）：

| 编号 | ASSUMPTION | 到货后验证 | 关闭后动作 |
| --- | --- | --- | --- |
| AS-31-eeprom-1 | 用户将运行的默认应用不会自动调用官方 `mosaico_joystick_new()`（源码已证：该驱动以 HANDLE claim 且只把脚配成输入，见 2.4；未证的是「谁会调用它」） | 检查用户实际刷入的应用工程是否链接 `mosaico_module_joystick` 组件（`idf_component.yml`/CMake）；开机后串口若出现 `Joystick opened: slot=left`（`mosaico_joystick.c` L585-588 格式）即证伪 | 证伪则在应用层排除该组件，或评估改用其他 board_type |
| AS-31-eeprom-2 | Espressif 自家模块的 vendor_id/board_id 与 `0x4354/0x0101` 不同（细化 AS-20） | 转储官方交互模块，`dump` 读值登记到第 3.1 节 | 相同则改值、重生成样例、更新 `SHA256SUMS` |
| AS-31-eeprom-3 | `keymap_version = 1` 对应 `hardware/module-board/PINMAP.md` 2026-09-20 首版（该文件尚无显式版本字段） | PINMAP.md 合入 main 时在其头部登记 `KEYMAP_VERSION=1`；固件 `dock_handle_pinmap.h` 声明同一常量并与 PINMAP.md 表一致（当前 WIP 不一致，见第 8 节）；G6-D 十键自检逐键对照底座丝印 | PINMAP 每次改表 → `KEYMAP_VERSION`＋1 → 本目录 `PINMAP_KEYMAP_VERSION` 同步、重生成样例；固件常量同步 |

## 12. 变更规则

- 改任何默认值 → 运行 `python3 mosaico_eeprom_v1.py selftest`（会因登记的 SHA-256 不符而失败）→ 更新 `SAMPLE_SHA256` 常量 → 重生成 `sample_handle.bin`、`sample_handle_image.h`、`SHA256SUMS`（命令见 `SHA256SUMS` 头部注释）→ 更新本文件第 1、9 节样例值与 `README.md` 贴出的输出。
- 本文件与 `mosaico_eeprom_v1.py` 中 `HANDLE_*`／`SAMPLE_*`／`ParamV1`／`PINMAP_KEYMAP_VERSION` 默认值必须一致；工具是数值的唯一来源，本文件是理由的唯一来源。
- KEY_* → GPIO 表只从 `hardware/module-board/PINMAP.md` 抄入，不在此处决定；PINMAP.md 改表必须同时递增 `KEYMAP_VERSION`。
- hw_version 变更 → board_name 后缀自动跟随（工具派生），不得手改名字造成两者不一致。

## 13. 与 `hardware/ICD-0.2-DRAFT.md` 第 7 节的逐条对应

| ICD 条目 | ICD 内容 | 本目录落实 | 一致性 |
| --- | --- | --- | --- |
| 7.1 器件类别 | AT24C02 兼容、3.3 V、256×8、硬件 A0、单字节内部地址、从 0 连续读 134 字节；订货号由 EEPROM/模块板任务从嘉立创常备料选 | 模块板分支 `netlist.yaml` 选 `AT24C02D-SSHM-T`（LCSC C34807）；`PROGRAMMING.md` 第 1 节已打开其原厂数据手册核对页写/tWR/WP/地址脚行为 | 一致 |
| 7.1 VCC/GND/A0/A1/A2 | VCC ← pin19、GND ← pin20、A0 ← pin10、A1/A2 ← GND | `PROGRAMMING.md` 第 2 节 | 一致 |
| 7.1 WP | proposed 默认拉到 `SLOT_3V3`（写保护），经 DNP 跳线可拉低 | `PROGRAMMING.md` 第 2 节以 ICD 为基线，并记录模块板分支 `netlist.yaml` JP1 默认可写与之**相反**，列为待 Chrome 决策项（AS-31-eeprom-4） | 已对齐并暴露冲突 |
| 7.1 管理器无写 API；烧录由独立夹具，接口由 EEPROM 任务定义 | — | `PROGRAMMING.md` 三条路径；测试焊盘用模块板分支的 TP2–TP6 | 一致 |
| 7.2 格式（134 字节、小端、三段 CRC、param_length ≤ 64） | confirmed | 工具与本文件第 1、9 节；自测贴在 `README.md` | 一致 |
| 7.2 board_type | EEPROM 任务提案；AS-20 | `0x04 HANDLE`，第 2 节 | 一致 |
| 7.2 board_id / vendor_id | EEPROM 任务提案（AS-20） | `0x0101` / `0x4354`，第 3 节 | 一致 |
| 7.2 hw_version 与模块板 PCB 版本绑定 | — | 第 4 节；名字后缀跟随 | 一致 |
| 7.2 sw_version 与镜像格式版本绑定 | — | 第 4 节：合同 v1.0 = KEY 语义 ＋ param v1 | 一致 |
| 7.2 board_name 建议含 `MOSAICO-DOCK-MODULE` 与版本 | 建议 | `MOSAICO-DOCK-MODULE-V1.0`，第 6 节 | 一致（上一版 WIP 不一致，已改） |
| 7.2 param_data 写 KEY_* → GPIO 映射版本号（与 PINMAP.md 一致）供固件核对 | proposed | param v1 区内 0x0F `keymap_version`，第 8 节 | 一致（上一版 WIP 缺此字段，已补） |
| 7.2 空白 EEPROM 不合格；烧入身份不自动产生十键驱动 | confirmed | 第 10 节；驱动在 `firmware/` 任务 | 一致 |
| 第 9 节网络命名 | `SLOT_*`、`KEY_*`、`DOCK_*` | 本目录只用这些名字；GPIO 号只出现在「左槽 11 根可用集合」的校验常量里，不做 KEY 分配 | 一致 |
