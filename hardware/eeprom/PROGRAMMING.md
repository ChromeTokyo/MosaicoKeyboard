提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造

# 模块板 EEPROM（AT24C02D）身份镜像烧写方法

## 0. 范围

对象：方案 D＋G 模块板上的 EEPROM U1（左槽 A0 = GPIO14 = 0 → 7 位地址 0x50）。写入内容为 `IDENTITY.md` 定义、`mosaico_eeprom_v1.py` 生成的 134 字节 EEPROM V1 镜像。三条路径：(a) 用 Mosaico 主机经左槽 I²C1 在系统内烧写；(b) 外部 USB-I²C 编程器；(c) 出厂预烧。第 6 节给出页写与写周期细节，第 7 节为烧写后验收清单，第 8 节为假设表。

本文件不改变模块板电路；对模块板的接线要求（第 2 节）是按 `hardware/ICD-0.2-DRAFT.md` 第 7.1 节提给 `hardware/module-board/` 任务的接口要求，并对照该任务分支（`claude/design-d/module-board`，WIP，未合入 main）的 `netlist.yaml`/`PINMAP.md` 逐项核对。

## 1. 器件事实：AT24C02D

模块板分支 `netlist.yaml` 选定 U1 = **AT24C02D-SSHM-T**（Microchip，SOIC-8，LCSC C34807）。本文件按该型号写；若 BOM 换件，本节须重核（**ASSUMPTION AS-31-eeprom-8**）。

已实际打开的数据手册：Atmel/Microchip **AT24C01D and AT24C02D**，文档号 `Atmel-8871F-SEEPROM-AT24C01D-02D-Datasheet_012017`，<https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-8871F-SEEPROM-AT24C01D-02D-Datasheet.pdf>（2026-09-21 打开，`pdftotext -layout` 提取后逐项核对；`netlist.yaml` 给的 LCSC 镜像链接 <https://www.lcsc.com/datasheet/C34807.pdf> 指向同一文档的 8871B 版，本文件以 Microchip 站 8871F 版为准）。

| 参数 | 值（8871F） | 手册位置 | 对本流程的影响 |
| --- | --- | --- | --- |
| 容量与组织 | 2 Kbit；**8 字节页**；8 位字地址 | Features "8-byte Page Write Mode"；§5.2 | 134 字节 = 16 整页 ＋ 1 个 6 字节部分页 |
| 页写 | 一次最多 8 字节，须在同一行（A7–A3 相同）；**允许部分页写**；页内地址回卷，高位不递增 | §5.2 | 帧起始地址必须是 8 的倍数 |
| 写周期 tWR | **最大 5 ms**（三种速率档相同）；期间对读写不响应 | Features；Table 8-3 `tWR 5 ms`；§5.4 | 每页后 Acknowledge Polling，上限 20 ms |
| 完成检测 | Acknowledge Polling：发 Start ＋ 器件地址（R/W=0），写周期中器件不 ACK，结束后 ACK | §5.3 | `i2c_master_probe()` 循环即可 |
| 器件地址 | `1010 A2 A1 A0 R/W`；A2/A1/A0 必须与引脚电平一致 | §4、Table 4-1 | A1=A2=GND、A0 由主机 GPIO14 驱动 → 0x50 |
| **地址脚与 WP 内部下拉** | A0/A1/A2/WP **悬空时内部下拉到 GND**；下拉「有意做得较强」，引脚电位高于 ~0.5·VCC 后下拉退出；厂方建议尽量接到确定电平 | 引脚表 Note 1；§4 | ① 脱机编程时 A0 悬空也读 0 → 仍是 0x50；② **JP1 不桥接 = WP 悬空 = 可写**，不是写保护；③ 主机 GPIO14 推挽驱动不受该下拉影响 |
| WP 极性 | WP = GND：正常写；WP = VCC（或有效 VIH）：全阵列禁写 | 引脚表；§5.5 Table 5-1 | 写保护要**主动拉高** |
| WP 被置位时的行为 | 器件**仍对器件地址、字地址、数据字节 ACK**，只是 Stop 后不发生写周期 | §5.5 | **写保护状态下烧写不会报 NACK**，只有回读才能发现；示例固件与工具都强制回读比对 |
| WP 采样时刻 | 每次 Byte/Page Write 的 Stop 条件处采样；tSU.WP / tHD.WP 4000 ns（标准模式） | §5.5；Table 8-3 | 烧写期间 JP1 状态不得变动 |
| SCL 频率 | 100 kHz（标准）／400 kHz（快速）@ 1.7–3.6 V；1 MHz @ 2.5–3.6 V | Features；Table 8-3 | 主机管理器用 100 kHz，余量充足 |
| **工作电压** | **1.7–3.6 V**（整个封装家族） | §8.2 Table 8-1；Features | **不得用 5 V 编程器或 5 V 供电的夹具**（与老 AT24C02 的 5 V 能力不同） |
| 绝对最大额定 | VCC 对地 −0.5 至 **+4.10 V**；任一引脚对地 −0.6 至 **VCC + 0.5 V**；DC 输出电流 5.0 mA | §8.1 | 5 V 编程器即使只接 SDA/SCL 也超过「VCC + 0.5 V」；U1 不上电时任何引脚都不得被驱动到 0.5 V 以上——夹具必须先供 3.3 V 再接总线 |
| 电流 | 读 @3.6 V/1 MHz：典型 0.15、最大 0.5 mA；写 @3.6 V/1 MHz：典型 0.20、**最大 1.0 mA**；待机 @3.6 V：典型 0.10、最大 0.8 µA；输入漏电最大 3 µA | Table 8-2 | pin19 负载可忽略（ASSUMPTION AS-13） |
| SDA 外部上拉 | 引脚表明示「须用外部上拉，**阻值不超过 10 kΩ**」；AC 测试条件 RPUP：10 kΩ @100 kHz、4 kΩ @400 kHz、1.3 kΩ @1 MHz，CL = 100 pF | 引脚表 SDA；Table 8-3 Note 2 | 见 6.3：主机内部上拉是否满足 ≤ 10 kΩ 是 AS-14 要实测的核心问题 |
| 输入边沿 | tR 最大 1000 ns（标准模式）；tF 300 ns | Table 8-3 | 6.3 |
| 耐久与保持 | 1,000,000 次写（字节或页模式）；100 年 @55 °C | Features；§8.6 | 本用途无影响 |
| 订货码 | `-SSHM-T`：SOIC-8，`M` = 1.7–3.6 V 档 | §9 订货信息（"M: 1.7V min"） | 与 netlist 一致 |

历史参考：上一版本文件引用的 `doc0180`（AT24C01A/02/04/08A/16A，5 V 家族）中「8 字节页、tWR 5 ms、Acknowledge Polling」与 8871F 一致；差异在电压（老件 2.7/5 V，新件 1.7–3.6 V）与地址脚/WP 内部下拉（老件无）。本文件所有结论按 8871F。

## 2. 模块板上的接线前提（对照 ICD 7.1 与模块板分支 netlist）

| U1 引脚 | 接到 | 统一网络名 | ICD 7.1 | 模块板分支 `netlist.yaml` | 说明 |
| --- | --- | --- | --- | --- | --- |
| 8 VCC | H2 pin19 VCC_3V3 ＋ C1 100 nF | `SLOT_3V3` | VCC ← pin19，就地去耦 | U1.8、C1、TP3 | 主机 `bsp_power_set_vcc_3v3(true)` 上电后才有电（`subboard.c` L132）。**不得**从底座供电（硬约束 3）。C1 值 **ASSUMPTION AS-31-eeprom-5** |
| 4 GND | H2 pin20 | `SLOT_GND` | GND ← pin20 | U1.4、TP2 | |
| 5 SDA | H2 pin16（GPIO0） | `SLOT_SDA` | 接 SDA；DNP 上拉位 | U1.5、R1（DNP）、TP4、J2.B1 | V1.2 模块 I²C1，主机开内部上拉（`subboard.c` L93）；外部上拉 DNP（硬约束 4；6.3） |
| 6 SCL | H2 pin14（GPIO1） | `SLOT_SCL` | 接 SCL；DNP 上拉位 | U1.6、R2（DNP）、TP5、J2.A8 | 同上 |
| 1 A0 | H2 pin10（GPIO14） | `SLOT_EEPROM_A0` | A0 ← pin10 | U1.1、TP6 | 主机推挽输出 0（`subboard.c` L101-120）。不接按键、不到弹簧针。器件内部下拉使脱机时也为 0 |
| 2 A1、3 A2 | GND | — | ← `SLOT_GND` | U1.2、U1.3 → SLOT_GND | 接地后地址 0x50（A0=0）／0x51（A0=1） |
| 7 WP | JP1 中心焊盘 | `EEPROM_WP` | **proposed 默认拉到 `SLOT_3V3`（写保护）**，经跳线可拉低 | JP1 三焊盘锡桥：1 = GND、2 = WP、3 = 3V3；**默认桥 1–2（可写）** | **两处不一致**，见下 |

测试焊盘（ICD 7.1 要求 `TP_SDA/TP_SCL/TP_3V3/TP_GND` 四个）：模块板分支 netlist 已给 TP2 GND、TP3 3V3、TP4 SDA、TP5 SCL、TP6 A0，满足要求并多出 A0；本文件以这些编号为脱机编程接入点（第 4 节），不再要求另留焊盘。备用接入点是 J1 公头本身（pin10/14/16/19/20）。

### 2.1 WP 默认态：ICD 与模块板分支冲突，本文件的处理

| 方案 | 默认 JP1 | 优点 | 代价 |
| --- | --- | --- | --- |
| ICD 7.1（权威输入） | 桥 2–3，WP = 3V3，写保护 | 任何固件 bug 都写不坏身份区 | 每次重烧（D-017 每轮：hw_version、keymap_version、序列号都可能变）都要改锡桥；模块板插在槽内后 JP1 是否可触及 unknown；方法 (a) 在系统内烧写前必须先改桥 |
| 模块板分支 netlist（WIP） | 桥 1–2，WP = GND，可写 | 方法 (a) 随时可用，迭代成本最低 | 依赖「主机上没有任何代码会写 0x50」——管理器确无写 API（`IDENTITY.md` 第 10 节），风险只来自自有烧写固件误运行 |

本文件**以 ICD 为基线**（定稿/量产：桥 2–3 写保护），并提出**样机阶段例外**：D-017 首轮样机桥 1–2 可写，每台在第 7 节验收通过后改桥 2–3 并复测写保护（7.5）。这需要 Chrome 决策并同步模块板 netlist 的 `default_bridge`；登记为 **ASSUMPTION AS-31-eeprom-4**（含「装配后 JP1 可触及」）。无论哪种默认，数据手册的两个事实都成立：JP1 不桥接 = WP 悬空 = 内部下拉 = **可写**；WP 高时写入仍 ACK，只能靠回读发现。

## 3. 方法 (a)：Mosaico 主机经左槽 I²C1 烧写

适用：首次装配（日本，用户自行）、每轮 D-017 打板后的重烧、序列号补写。不需要任何额外工具，只需能给 Mosaico 刷固件的 USB-C 线与 ESP-IDF 环境。

### 3.1 前提

1. 主机为 BaseBoard V1.2：BSP 启动日志应有 `Hardware version: v1.2 (variant=v1.2)`（`esp_mosaico.c` L57-58，`detect_board_variant()` L33-59 从 eFuse `USER_DATA` 读出）。V1.0 主机的模块总线是与主板共享的 I2C0，本流程未针对它验证。
2. 模块板插入**左槽**；右槽可空。
3. **JP1 处于 1–2（WP → GND）**，或按 2.1 的量产默认先改桥。烧写过程中不得改动。
4. 烧写固件里**不启动** `mosaico_module_mgr`（或先 `mosaico_module_mgr_deinit()`，前提是所有 lease 已 release）。原因：管理器扫描任务每 250 ms 探测 0x50 并可能读描述；若探测落在 tWR 内会得到 NACK，连续 3 次会被判 ABSENT，且读到半写镜像会记 INVALID 并进入 2 s 重试。总线层面 ESP-IDF 会串行化事务，不会损坏器件，但状态会混乱。
5. 不运行摄像头驱动（它把 GPIO14 改作 DVP D4，会改变 A0 电平）。

### 3.2 步骤（对应 `eeprom_program_example.c`）

| 步 | 调用 | 依据 |
| --- | --- | --- |
| 1 | 在 PC 上生成镜像并自检：`python3 mosaico_eeprom_v1.py build --serial 0x2609000N --date 2026MMDD -o unit.bin && python3 mosaico_eeprom_v1.py verify unit.bin --expect-handle && python3 mosaico_eeprom_v1.py c-array unit.bin -o sample_handle_image.h`；把 `build` 打印的 SHA-256 记入 `SERIALS.csv` | 工具 |
| 2 | `bsp_subboard_init()`：开 VCC_3V3（pin19）→ 建 I2C1（SDA0/SCL1，内部上拉）→ GPIO14 输出 0 | `subboard.h` L62；`subboard.c` L123-152 |
| 3 | `i2c_master_probe(bsp_subboard_get_i2c_bus(), 0x50, 100)` 应答才继续 | `subboard.h` L65；`mosaico_module_mgr.c` L481 同一调用 |
| 4 | `i2c_master_bus_add_device()`：7 位、0x50、100 kHz | 与管理器 `attach_eeprom_devices()` L373-390 相同参数 |
| 5 | 17 次 `i2c_master_transmit(dev, [字地址, ≤8 字节], n+1, 100)`：0x00、0x08、…、0x78 各 8 字节，0x80 写 6 字节（部分页写） | 8871F §5.2；`i2c_master_transmit()` 在同 commit BSP 的 `onboard/sensors.c` L51、L197 已被调用 |
| 6 | 每页后 Acknowledge Polling：`i2c_master_probe()` 直到 `ESP_OK`，上限 20 ms（tWR 5 ms × 4）；返回 `ESP_ERR_NOT_FOUND` 表示仍在写周期，其他错误立即失败 | 8871F §5.3；管理器对 probe 返回值的同一解释 L481-483 |
| 7 | 回读：`i2c_master_transmit_receive(dev, &zero, 1, buf, 134, 100)`，与管理器 `read_eeprom()` 完全相同的读法；逐字节比对并再跑一次 magic/CRC/param_length 校验。**回读是发现 WP 被置位的唯一手段**（第 1 节） | L418-423；8871F §5.5 |
| 8 | `i2c_master_bus_rm_device(dev)`，然后 `mosaico_module_mgr_init(NULL)` ＋ `mosaico_module_mgr_request_rescan(LEFT)`，轮询 `mosaico_module_mgr_get_info()` 直到 `presence == PRESENT && descriptor_state == VALID`，核对 `eeprom.board_type == 0x04` | `mosaico_module_mgr.h` |
| 9 | （量产默认）改桥 JP1 2–3，按 7.5 复测写保护 | 2.1 |

预期串口日志（管理器，`mosaico_module_mgr.c` L429-442 格式）：

```text
I mosaico_module_mgr: Module present: slot=left eeprom=0x50
I mosaico_module_mgr: Module identified: slot=left type=Handle(0x04) id=0x0101 name=MOSAICO-DOCK-MODULE-V1.0
```

核心片段（完整文件见 `eeprom_program_example.c`；API 签名核对来源列在该文件头部；宿主机 clang 语法检查见 `README.md`）：

```c
/* 页写 + ACK 轮询；off 为 8 的倍数，不跨页；最后一页 6 字节 */
static esp_err_t eeprom_write_image(i2c_master_bus_handle_t bus, i2c_master_dev_handle_t dev, uint8_t addr,
                                    const uint8_t *img, size_t len)
{
    uint8_t frame[1 + 8];
    for (size_t off = 0; off < len; off += 8) {
        const size_t n = (len - off < 8) ? (len - off) : 8;
        frame[0] = (uint8_t)off;
        memcpy(&frame[1], img + off, n);
        ESP_RETURN_ON_ERROR(i2c_master_transmit(dev, frame, 1 + n, 100), TAG, "page 0x%02X", (unsigned)off);
        ESP_RETURN_ON_ERROR(eeprom_wait_ready(bus, addr), TAG, "tWR poll 0x%02X", (unsigned)off);   /* i2c_master_probe 直到 ESP_OK */
    }
    return ESP_OK;
}
```

**ASSUMPTION AS-31-eeprom-6**：ESP32-S31 目标的 IDF 版本中 `driver/i2c_master.h` 五个函数（`i2c_master_probe / bus_add_device / bus_rm_device / transmit / transmit_receive`）签名与 ESP-IDF 文档（esp32s3 页，2026-09-20 访问）一致。同 commit 的 BSP 已调用全部五个（管理器四个 ＋ `sensors.c` 的 `i2c_master_transmit`），BSP 能为 S31 编译即隐含此假设成立；本文件仅在宿主机以桩头做了 clang 语法/类型检查。验证：实物到货后在能编译 BSP 的 IDF 环境编译 `eeprom_program_example.c`。

### 3.3 故障定位

| 现象 | 最可能原因 | 检查 |
| --- | --- | --- |
| 步 3 probe 失败（`ESP_ERR_NOT_FOUND`） | 模块未插到底；pin19 无 3.3 V；A1/A2 未接地；A0 被拉高 | 万用表量 TP3 电压、TP6 电平；`i2c_master_probe(bus, 0x51, 100)` 若应答说明 A0 为高 |
| probe 超时（非 NOT_FOUND） | SDA/SCL 被拉死或未接；上拉不足 | 量 TP4/TP5 静态电平应为高；示波器看边沿（6.3） |
| 步 5 写入 NACK | 地址错、器件未上电、总线故障。**不是 WP**——WP 高时器件照常 ACK | 复查步 3 |
| 步 6 超过 20 ms 仍无 ACK | 器件损坏，或换了 tWR 更长的兼容件 | 换器件；查所购型号手册（AS-31-eeprom-8） |
| 回读全 0xFF 或与写入不符但器件一直 ACK | **WP 为高**（JP1 桥在 2–3 或误接）| 量 JP1 中心焊盘电平；示例固件在回读全 0xFF 时会打印此提示 |
| 回读部分不符 | 页边界错误（帧起始地址非 8 的倍数）；总线噪声 | 检查工具 `--dry-run` 生成的帧；缩短线缆 |
| 管理器 INVALID | 镜像本身 CRC 错（PC 端 `verify` 会先拦住）；回读与写入一致但主机仍判 CRC 错，说明主机固件与 392860b1 格式不同 | AS-16 |

## 4. 方法 (b)：外部 USB-I²C 编程器

适用：模块板单板测试（未插主机）、批量烧写、主机不可用时。

### 4.1 夹具要求

- 供电 **3.3 V** 到 TP3（`SLOT_3V3`）、GND 到 TP2。**AT24C02D 工作电压上限 3.6 V**（第 1 节），任何 5 V 编程器或 5 V 供电夹具都不得直接使用；且不得在模块板插着主机时脱机上电——会经 pin19 向主机 3.3 V 网络倒灌（硬约束 3）。
- SDA → TP4、SCL → TP5；上拉由编程器提供，**≤ 10 kΩ**（8871F 引脚表），多数 USB-I²C 适配器板载 4.7–10 kΩ，具体待适配器手册核对。
- A0（TP6）：接 GND → 0x50；悬空时器件内部下拉也是 0（第 1 节），但按厂方建议仍接 GND。接 3.3 V 则为 0x51，也可用，但与工具默认 `--addr 0x50` 不同。
- JP1 桥 1–2（WP = GND）。

### 4.2 工具

| 工具 | 用法 | 说明 |
| --- | --- | --- |
| 任意 Linux 板（树莓派等，I/O 为 3.3 V）＋ `i2c-tools` ＋ `smbus2` | `i2cdetect -y 1` 应在 `50` 处显示器件；`python3 mosaico_eeprom_v1.py program --bus 1 --addr 0x50 unit.bin` | 工具内实现 8 字节页写、1 字节读 ACK 轮询（上限 20 ms）、134 字节回读比对。`--dry-run` 只打印 17 帧 |
| CH341A 类 24 系列编程器 ＋ 开源 `ch341eeprom` 或厂商软件 | 需要 256 字节整片文件：`{ cat unit.bin; head -c 122 /dev/zero \| tr '\0' '\377'; } > unit_256.bin`，选型 24C02 写入，再读回 256 字节 | 主机只读前 134 字节，0x86–0xFF 填 0xFF 或 0x00 均可。**多数 CH341A 板 VCC 与 I/O 为 5 V，必须确认已改 3.3 V 才能接 AT24C02D** |
| MCP2221A／FT232H 等 3.3 V 适配器 | 用其厂商库按 6.1 节帧格式写页；或跑树莓派同一 `program` 命令 | 待适配器手册核对 |

### 4.3 校验

读回整片（134 或 256 字节）后 `python3 mosaico_eeprom_v1.py verify dump.bin --expect-handle`；工具接受 ≥134 字节文件并忽略多余字节。最后仍须插入主机做第 7 节的在线验收。

## 5. 方法 (c)：出厂预烧

| 途径 | 现状 | 限制 |
| --- | --- | --- |
| 嘉立创 SMT 下单时由厂方烧写 24C02 | **待核对**（ASSUMPTION AS-31-eeprom-7）：是否提供 I²C EEPROM 编程服务、最低起订、文件格式与费用，均未查证，不假定存在 | 需要 256 字节文件；同一文件 → 所有单元序列号相同 |
| 分销商（Mouser/Digi-Key 等）器件编程服务 | **待核对**（同上）：Microchip 串行 EEPROM 是否在其编程服务目录内、起订量、交期 | 同上 |
| 主机首次接入时自烧（(a) 的变体） | 可行：模块板贴空片（出厂 0xFF，主机判 `ESP_ERR_INVALID_RESPONSE` → descriptor INVALID），用户运行 `eeprom_program_example.c` 一次即可 | 每台生成不同序列号文件，或固件内按序号递增生成（需实现） |

结论：按 D-017 的数量（每轮数块板）、序列号唯一性（`IDENTITY.md` 第 5 节）以及每轮都可能变化的 hw_version / keymap_version（`IDENTITY.md` 第 4、8 节），首轮不采用工厂预烧；基线是 (a)，台架用 (b)。若将来预烧，只烧「序列号 = 0、manufacture_date = 0」的半成品镜像（工具 `expect_handle` 会标记序列号保留值，提示补写），由主机在首次接入时补写序列号与日期。

## 6. 页写与写周期细节

### 6.1 帧序列（134 字节 → 17 帧）

| 帧 | 字地址 | 数据字节数 | 镜像范围 |
| --- | --- | ---: | --- |
| 1–16 | 0x00, 0x08, …, 0x78 | 8 | 0x00–0x7F |
| 17 | 0x80 | 6 | 0x80–0x85（部分页写） |

每帧：`START, 0xA0(0x50<<1|W), ACK, 字地址, ACK, D0, ACK, …, Dn, ACK, STOP`。STOP 后进入 tWR。帧起始地址必须是 8 的倍数：若从 0x04 写 8 字节，第 5 字节会回卷到 0x00 覆盖 magic（8871F §5.2「高位地址不递增」）。工具 `program --dry-run` 会打印全部 17 帧。

### 6.2 时间预算（100 kHz）

单帧最长 10 字节 × 9 位 / 100 kHz ≈ 0.9 ms，加 tWR ≤ 5 ms → 每页 < 6 ms，17 页 < 0.1 s；加 ACK 轮询开销总计约 0.1–0.2 s。工具与示例固件对每页等待上限 20 ms。

### 6.3 上拉与边沿（ASSUMPTION AS-14）

- V1.2 主机对 I2C1 开的是 ESP32 **内部**上拉（`subboard.c` L93），阻值以 ESP32-S31 数据手册为准（未查，待核对）。
- 8871F 要求 SDA 外部上拉**不超过 10 kΩ**，标准模式 tR ≤ 1000 ns（100 pF、10 kΩ 测试条件）。若 S31 内部上拉阻值大于 10 kΩ（其他 ESP32 系列的内部上拉典型值在数十 kΩ 量级，S31 数值 unknown），则仅靠内部上拉不满足器件手册条件，即便管理器读取成功也属于余量不足。这使模块板的 DNP 上拉位 `R1/R2` 从「可选」变成「很可能要装」，但阻值仍须按实测决定，不得照搬 V1.0 的 4.7 kΩ（硬约束 4）。
- 模块板走线很短，SDA/SCL 不经弹簧针（默认 `R_LINK` DNP），电容应很小；验证：到货后示波器量 TP4/TP5 上升时间与低电平，决定 R1/R2 装配与阻值（`hardware/ASSUMPTIONS.md` AS-14；PINMAP.md 验证项 P6）。

### 6.4 其他

- 主机在系统内烧写时 EEPROM 电流最大 1.0 mA（8871F Table 8-2，3.6 V/1 MHz 条件，100 kHz 下更低），远小于官方 3.3 V 扩展输出 up to 100 mA 的能力（`docs/INTERFACE_CONTROL.md` E4；V1.2 能力 unknown，AS-13）。
- 写耐久 1M 次，本用途（每台一生烧写几次）无影响。
- 全片仅使用 0x00–0x85；不要把任何运行时数据（按键统计、电量学习值等）写入 0x86–0xFF：主机管理器不读它们，但会增加误写身份区的风险；运行时数据放主机 NVS。

## 7. 烧写后验收清单

1. PC 端：`verify --expect-handle` 通过；`SERIALS.csv` 已登记该序列号与镜像 SHA-256。
2. 器件端：回读 134 字节与镜像逐字节一致（方法 a 步 7 或方法 b 4.3）。
3. 主机端：识别日志出现 `type=Handle(0x04) id=0x0101 name=MOSAICO-DOCK-MODULE-V1.0`；`mosaico_module_mgr_get_info(LEFT)` 的 `descriptor_state == VALID`、`eeprom.vendor_id == 0x4354`、`eeprom.hw_version` 与名字后缀一致、`eeprom.serial_number` 等于登记值。
4. 拔插一次：`presence` 应 ABSENT → PRESENT，描述重新 VALID（验证 A0/3V3 经槽位供电正常）。
5. 写保护（量产默认或样机验收后改桥）：JP1 改桥 2–3，量 JP1 中心焊盘为 3.3 V；再执行一次方法 a 步 5–7：**写入应正常 ACK、回读应与改桥前完全一致**（8871F §5.5：WP 高时 ACK 但不写）；若回读变了，说明 WP 未真正拉高。

## 8. 假设清单

编号与 `IDENTITY.md` 第 11 节连续（AS-31-eeprom-1～3 在该文件）；汇总阶段由主控并入 `hardware/ASSUMPTIONS.md` 并统一正式编号。

| 编号 | ASSUMPTION | 验证 | 关闭后动作 |
| --- | --- | --- | --- |
| AS-31-eeprom-4 | WP 默认态：以 ICD 7.1「默认写保护」为基线，样机阶段例外为可写；且模块板装入槽位、机械件装配后 JP1 仍可触及并可改桥 | Chrome 决策并同步模块板 `netlist.yaml` `default_bridge`；机械任务出装配图后核对 JP1 位置；到货后实际改桥一次并按 7.5 复测 | 决策写入 ICD 7.1 与 netlist；若不可触及，改为「首次烧写在最终装配前完成」的流程约束 |
| AS-31-eeprom-5 | U1 去耦 100 nF（netlist C1）足够 | 通用做法；示波器看写周期内 TP3 纹波 | 无 |
| AS-31-eeprom-6 | ESP32-S31 目标 IDF 提供五个同签名 `i2c_master_*` API（BSP 同 commit 已全部调用） | 在可编译 BSP 的 IDF 环境编译 `eeprom_program_example.c` | 无 |
| AS-31-eeprom-7 | 嘉立创/分销商预烧服务存在与否 unknown，首轮不依赖 | 下单前询问，记录到第 5 节 | 若存在且便宜，评估半成品镜像预烧 |
| AS-31-eeprom-8 | 模块板 BOM 最终器件为 AT24C02D-SSHM-T（或页 ≥ 8 字节、tWR ≤ 5 ms、1.7–3.6 V、地址脚/WP 行为不劣于第 1 节的兼容件） | BOM 定稿时核对；到货核对器件丝印/订货码 | 换件则重写第 1 节并复核第 2–7 节 |

已被替代的旧编号：P-01 → AS-31-eeprom-4；P-02 → 5；P-03（另留测试焊盘）→ 由模块板分支 TP2–TP6 满足，不再是假设；P-04 → 6；P-05 → 引用 AS-14；P-06 → 8（AT24C02D 手册已打开，剩余部分是 BOM 不换件）；P-07 → 7。
