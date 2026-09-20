提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造

# 模块板 AT24C02 身份镜像烧写方法

## 0. 范围

对象：方案 D＋G 模块板上的 AT24C02（左槽 A0 = GPIO14 = 0 → 0x50）。写入内容为 `IDENTITY.md` 定义、`mosaico_eeprom_v1.py` 生成的 134 字节 EEPROM V1 镜像。三条路径：(a) 用 Mosaico 主机经左槽 I²C1 在系统内烧写；(b) 外部 USB-I²C 编程器；(c) 出厂预烧。第 6 节给出 AT24C02 页写与写周期细节，第 7 节为烧写后验收清单，第 8 节为假设表。

本文件不改变模块板电路；对模块板的接线要求（第 2 节）是提给 `hardware/module-board/` 任务的接口要求。

## 1. 器件事实：AT24C02

已实际打开的数据手册：Atmel（现 Microchip）**AT24C01A/02/04/08A/16A Two-wire Serial EEPROM**，文档号 `0180Z1–SEEPR–5/07`，<https://ww1.microchip.com/downloads/en/DeviceDoc/doc0180.pdf>（2026-09-20 打开，`pdftotext` 提取核对）。

| 参数 | 值 | 手册位置 |
| --- | --- | --- |
| 容量与组织 | 2K 位 = 256 × 8；32 页 × 8 字节；8 位字地址 | Memory Organization |
| 页写 | 最多 8 字节；允许部分页写；页内字地址低 3 位自增，到页边界回卷到同页起点，多于 8 字节会覆盖前面数据 | Write Operations – PAGE WRITE |
| 写周期 tWR | **最大 5 ms**（1.8 V 与 2.7/5 V 两档相同）；期间所有输入被禁止、器件不应答 | Table 5；Write Operations – BYTE WRITE |
| 完成检测 | Acknowledge Polling：发 START ＋ 器件地址字，内部写周期结束后器件才回 ACK | ACKNOWLEDGE POLLING |
| SCL 最高频率 | 100 kHz（1.8 V 档）／400 kHz（2.7 V、5 V 档） | Table 5 fSCL |
| 电源 | 2.7–5.5 V 或 1.8–5.5 V（按订货后缀） | Features |
| 器件地址字 | `1 0 1 0 A2 A1 A0 R/W`；A2/A1/A0 **必须与硬接线引脚电平一致** | Device Addressing、Figure 7 |
| WP | 接 GND：正常读写；接 VCC：整个阵列写保护 | Pin Description、Table 2 |
| 电流 | 写 100 kHz @5 V：典型 2.0 mA、最大 3.0 mA；读 0.4/1.0 mA；待机 @2.7 V 典型 1.6 µA、最大 4.0 µA | Table 4（5 V 条件；3.3 V 下的写电流待原厂数据手册核对） |
| 输入电平 | VIL ≤ 0.3·VCC，VIH ≥ 0.7·VCC | Table 4 |
| 绝对最大 | 任一引脚 −1.0 至 +7.0 V；DC 输出电流 5.0 mA | Absolute Maximum Ratings |
| 耐久 | 1M 次写（字节模式）；数据保持 100 年 | Features、Table 5 |

**注意**：该手册把原 AT24C02 标为 "Not Recommended for new design; refer to AT24C02B"。模块板 BOM 实际选用的型号（Microchip AT24C02C/AT24C02D，或嘉立创常备的国产兼容件）尚未确定；其页大小、tWR、地址引脚内部上下拉、WP 内部处理等**待原厂数据手册核对**，本文件所有时序余量按 doc0180 的 8 字节／5 ms 设计，若所购型号页更大或 tWR 更短，本流程仍然正确（按 8 字节页写、按 5 ms 等待是保守侧）。嘉立创 LCSC 编码由模块板 BOM 给出，本文件不指定。

## 2. 模块板上的接线前提（提给模块板任务的接口要求）

| AT24C02 引脚 | 接到 | 统一网络名 | 说明 |
| --- | --- | --- | --- |
| VCC | H2 pin19 VCC_3V3 | `SLOT_3V3` | 主机 `bsp_power_set_vcc_3v3(true)` 上电后才有电（`subboard.c` L132）。**不得**从底座供电（硬约束 3） |
| GND | H2 pin20 | `SLOT_GND` | |
| SDA | H2 pin16（GPIO0） | `SLOT_SDA` | V1.2 模块 I²C1，主机开内部上拉（`subboard.c` L93）；模块板外部上拉留 DNP 位（硬约束 4） |
| SCL | H2 pin14（GPIO1） | `SLOT_SCL` | 同上 |
| A0 | H2 pin10（GPIO14） | `SLOT_EEPROM_A0` | 主机推挽输出 0（`subboard.c` L101-120）。不接按键、不加上拉；是否加弱下拉（便于脱机编程）由模块板任务评估，默认不加 |
| A1、A2 | GND | — | 手册要求硬接线；接地后地址为 0x50（A0=0）／0x51（A0=1） |
| WP | GND | — | 建议经焊接跳线接 GND，预留改接 VCC 的锁定选项；默认可写（D-017 迭代需要重烧）。**ASSUMPTION P-01** |
| — | 100 nF 去耦到 GND | — | 通用做法，非手册要求；**ASSUMPTION P-02** |

脱机编程的接入点：模块板自带的 2×10P 槽位公头就是接口（pin10 A0、pin14 SCL、pin16 SDA、pin19 3V3、pin20 GND），不需要额外测试点；用配对母座或 2.54 mm 测试夹接入。若模块板空间允许，另留 5 个测试焊盘（**ASSUMPTION P-03**，空间未知）。

## 3. 方法 (a)：Mosaico 主机经左槽 I²C1 烧写

适用：首次装配（日本，用户自行）、每轮 D-017 打板后的重烧、序列号补写。不需要任何额外工具，只需能给 Mosaico 刷固件的 USB-C 线与 ESP-IDF 环境。

### 3.1 前提

1. 主机为 BaseBoard V1.2：BSP 启动日志应有 `Hardware version: v1.2 (variant=v1.2)`（`esp_mosaico.c` L57-58，`detect_board_variant()` 从 eFuse `USER_DATA` 读出）。V1.0 主机的模块总线是与主板共享的 I2C0，本流程未针对它验证。
2. 模块板插入**左槽**；右槽可空。
3. 烧写固件里**不启动** `mosaico_module_mgr`（或先 `mosaico_module_mgr_deinit()`，前提是所有 lease 已 release）。原因：管理器扫描任务每 250 ms 探测 0x50 并可能读描述；若探测落在 tWR 内会得到 NACK，连续 3 次会被判 ABSENT，且读到半写镜像会记 INVALID 并进入 2 s 重试。总线层面 ESP-IDF 会串行化事务，不会损坏器件，但状态会混乱。
4. 不运行摄像头驱动（它把 GPIO14 改作 DVP D4，会改变 A0 电平）。

### 3.2 步骤（对应 `eeprom_program_example.c`）

| 步 | 调用 | 依据 |
| --- | --- | --- |
| 1 | 在 PC 上生成镜像并自检：`python3 mosaico_eeprom_v1.py build --serial 0x2609000N --date 2026MMDD -o unit.bin && python3 mosaico_eeprom_v1.py verify unit.bin --expect-handle && python3 mosaico_eeprom_v1.py c-array unit.bin -o sample_handle_image.h` | 工具 |
| 2 | `bsp_subboard_init()`：开 VCC_3V3（pin19）→ 建 I2C1（SDA0/SCL1，内部上拉）→ GPIO14 输出 0 | `subboard.h` L58；`subboard.c` L123-152 |
| 3 | `i2c_master_probe(bsp_subboard_get_i2c_bus(), 0x50, 100)` 应答才继续 | `subboard.h` L61；ESP-IDF `driver/i2c_master.h` |
| 4 | `i2c_master_bus_add_device()`：7 位、0x50、100 kHz | 与管理器 `attach_eeprom_devices()` L373-390 相同参数 |
| 5 | 17 次 `i2c_master_transmit(dev, [字地址, ≤8 字节], n+1, 100)`：0x00、0x08、…、0x78 各 8 字节，0x80 写 6 字节（部分页写） | doc0180 PAGE WRITE |
| 6 | 每页后 Acknowledge Polling：`i2c_master_probe()` 直到 `ESP_OK`，上限 20 ms（tWR 5 ms × 4）；返回 `ESP_ERR_NOT_FOUND` 表示仍在写周期，其他错误立即失败 | doc0180 ACKNOWLEDGE POLLING；管理器对 probe 返回值的同一解释 L481-483 |
| 7 | 回读：`i2c_master_transmit_receive(dev, &zero, 1, buf, 134, 100)`，与管理器 `read_eeprom()` 完全相同的读法；逐字节比对并再跑一次 magic/CRC/param_length 校验 | L418-423 |
| 8 | `i2c_master_bus_rm_device(dev)`，然后 `mosaico_module_mgr_init(NULL)` ＋ `mosaico_module_mgr_request_rescan(LEFT)`，轮询 `mosaico_module_mgr_get_info()` 直到 `presence == PRESENT && descriptor_state == VALID`，核对 `eeprom.board_type == 0x04` | `mosaico_module_mgr.h` |

预期串口日志（管理器，`mosaico_module_mgr.c` L438-440 格式）：

```text
I mosaico_module_mgr: Module present: slot=left eeprom=0x50
I mosaico_module_mgr: Module identified: slot=left type=Handle(0x04) id=0x0101 name=MK-HANDHELD-DOCK-MODULE
```

核心片段（完整可编译文件见 `eeprom_program_example.c`；API 签名核对来源列在该文件头部）：

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

**ASSUMPTION P-04**：`i2c_master_transmit` 等 `driver/i2c_master.h` API 在 ESP32-S31 目标的 IDF 版本中签名与 ESP-IDF 文档（esp32s3 页，2026-09-20 访问）一致。BSP 自身已调用同头文件的 `i2c_master_probe/bus_add_device/bus_rm_device/transmit_receive`，只有 `i2c_master_transmit` 未在 BSP 中出现。验证：实物到货后在能编译 BSP 的 IDF 环境编译 `eeprom_program_example.c`。

### 3.3 故障定位

| 现象 | 最可能原因 | 检查 |
| --- | --- | --- |
| 步 3 probe 失败（`ESP_ERR_NOT_FOUND`） | 模块未插到底；A1/A2 未接地；A0 未接 pin10 或主机 GPIO14 未输出 0；pin19 无 3.3 V | 万用表量 pin19 电压、pin10 电平；`i2c_master_probe(bus, 0x51, 100)` 若应答说明 A0 被拉高 |
| probe 超时（非 NOT_FOUND） | SDA/SCL 被拉死或未接；上拉不足 | 量 SDA/SCL 静态电平应为高；示波器看边沿（见 6.3） |
| 步 5 写入 NACK | WP 接了 VCC；地址错 | 量 WP 电平 |
| 步 6 超过 20 ms 仍无 ACK | 器件损坏或 tWR 更长的兼容件 | 换器件；查所购型号手册 |
| 回读不一致 | 页边界错误（帧起始地址非 8 的倍数）；总线噪声 | 检查工具生成的帧；缩短线缆 |
| 管理器 INVALID | 镜像本身 CRC 错（PC 端 `verify` 会先拦住）；回读与写入一致但 CRC 错说明 PC 端与主机版本格式不同 | A-ID-01 |

## 4. 方法 (b)：外部 USB-I²C 编程器

适用：模块板单板测试（未插主机）、批量烧写、主机不可用时。

### 4.1 夹具要求

- 供电 **3.3 V** 到 `SLOT_3V3`、GND 到 `SLOT_GND`。虽然 AT24C02 允许 5 V，但模块板是 3.3 V 域（硬约束 5），DNP 上拉与 ESD 件按 3.3 V 选，且不得在模块板插着主机时脱机上电——会经 pin19 向主机 3.3 V 网络倒灌。
- `SLOT_EEPROM_A0`（pin10）**接 GND** → 0x50；接 VCC 则为 0x51，也可用，但与工具默认 `--addr 0x50` 不同。
- SDA/SCL 上拉由编程器提供（多数 USB-I²C 适配器板载 4.7–10 kΩ，具体待适配器手册核对）。
- WP 接 GND。

### 4.2 工具

| 工具 | 用法 | 说明 |
| --- | --- | --- |
| 任意 Linux 板（树莓派等）＋ `i2c-tools` ＋ `smbus2` | `i2cdetect -y 1` 应在 `50` 处显示器件；`python3 mosaico_eeprom_v1.py program --bus 1 --addr 0x50 unit.bin` | 工具内实现 8 字节页写、1 字节读 ACK 轮询（上限 20 ms）、134 字节回读比对。`--dry-run` 只打印 17 帧 |
| CH341A 类 24 系列编程器 ＋ 开源 `ch341eeprom` 或厂商软件 | 需要 256 字节整片文件：`{ cat unit.bin; head -c 122 /dev/zero \| tr '\0' '\377'; } > unit_256.bin`，选型 24C02 写入，再读回 256 字节 | 主机只读前 134 字节，0x86–0xFF 填 0xFF 或 0x00 均可。部分 CH341A 板 VCC 为 5 V，须确认或改 3.3 V |
| MCP2221A／FT232H 等 | 用其厂商库按 6.1 节帧格式写页；或跑树莓派同一 `program` 命令 | 待适配器手册核对 |

### 4.3 校验

读回整片（134 或 256 字节）后 `python3 mosaico_eeprom_v1.py verify dump.bin --expect-handle`；工具接受 ≥134 字节文件并忽略多余字节。最后仍须插入主机做第 7 节的在线验收。

## 5. 方法 (c)：出厂预烧

| 途径 | 现状 | 限制 |
| --- | --- | --- |
| 嘉立创 SMT 下单时由厂方烧写 24C02 | **待核对**：是否提供 I²C EEPROM 编程服务、最低起订、文件格式与费用，均未查证，不假定存在 | 需要 256 字节文件；同一文件 → 所有单元序列号相同 |
| 分销商（Mouser/Digi-Key 等）器件编程服务 | **待核对**：Microchip 串行 EEPROM 是否在其编程服务目录内、起订量、交期 | 同上 |
| 主机首次接入时自烧（(a) 的变体） | 可行：模块板贴空片（出厂 0xFF，主机判 `ESP_ERR_INVALID_RESPONSE` → descriptor INVALID），用户运行 `eeprom_program_example.c` 一次即可 | 每台生成不同序列号文件，或固件内按序号递增生成（需实现） |

结论：按 D-017 的数量（每轮数块板）与序列号唯一性要求（IDENTITY.md 第 5 节），首轮不采用工厂预烧；基线是 (a)，台架用 (b)。若将来预烧，只烧「序列号 = 0、manufacture_date = 0」的半成品镜像（工具 `expect_handle` 会标记序列号保留值，提示补写），由主机在首次接入时补写序列号与日期。

## 6. AT24C02 页写与写周期细节

### 6.1 帧序列（134 字节 → 17 帧）

| 帧 | 字地址 | 数据字节数 | 镜像范围 |
| --- | --- | ---: | --- |
| 1–16 | 0x00, 0x08, …, 0x78 | 8 | 0x00–0x7F |
| 17 | 0x80 | 6 | 0x80–0x85（部分页写） |

每帧：`START, 0xA0(0x50<<1|W), ACK, 字地址, ACK, D0, ACK, …, Dn, ACK, STOP`。STOP 后进入 tWR。帧起始地址必须是 8 的倍数：若从 0x04 写 8 字节，第 5 字节会回卷到 0x00 覆盖 magic。

### 6.2 时间预算（100 kHz）

单帧最长 10 字节 × 9 位 / 100 kHz ≈ 0.9 ms，加 tWR ≤ 5 ms → 每页 < 6 ms，17 页 < 0.1 s；加 ACK 轮询开销总计约 0.1–0.2 s。工具与示例固件对每页等待上限 20 ms。

### 6.3 上拉与边沿（ASSUMPTION P-05）

V1.2 主机对 I2C1 开的是 ESP32 **内部**上拉（`subboard.c` L93），阻值以 ESP32-S31 数据手册为准（未查，待核对）。doc0180 Table 5 对 2.7 V 档要求输入上升时间 tR ≤ 0.3 µs（1.8 V 档 1.0 µs）——这是器件输入端参数，实际总线边沿由上拉与总线电容决定；模块板走线很短，但底座结构使 SDA/SCL 不经弹簧针（EEPROM 在模块板上），电容应很小。验证：到货后示波器量 SDA/SCL 上升时间与低电平，决定 DNP 外部上拉是否装配（硬约束 4：不得照搬 V1.0 的 4.7 kΩ 结论）。

### 6.4 其他

- 主机在系统内烧写时 EEPROM 电流 ≤ 3 mA（5 V 条件），远小于官方 3.3 V 扩展输出 up to 100 mA 的能力（`docs/INTERFACE_CONTROL.md` E4）；3.3 V 下具体值待核对。
- 写耐久 1M 次，本用途（每台一生烧写几次）无影响。
- 全片仅使用 0x00–0x85；不要把任何运行时数据（按键统计、电量学习值等）写入 0x86–0xFF：主机管理器不读它们，但会增加误写身份区的风险；运行时数据放主机 NVS。

## 7. 烧写后验收清单

1. PC 端：`verify --expect-handle` 通过；`SERIALS.csv` 已登记该序列号与镜像 SHA-256。
2. 器件端：回读 134 字节与镜像逐字节一致（方法 a 步 7 或方法 b 4.3）。
3. 主机端：识别日志出现 `type=Handle(0x04) id=0x0101 name=MK-HANDHELD-DOCK-MODULE`；`mosaico_module_mgr_get_info(LEFT)` 的 `descriptor_state == VALID`、`eeprom.vendor_id == 0x4354`、`eeprom.serial_number` 等于登记值。
4. 拔插一次：`presence` 应 ABSENT → PRESENT，描述重新 VALID（验证 A0/3V3 经槽位供电正常）。
5. 若 WP 采用锁定选项：锁定后再执行一次方法 a 步 5，应 NACK，回读不变。

## 8. 假设清单

| 编号 | ASSUMPTION | 验证 |
| --- | --- | --- |
| P-01 | WP 经焊接跳线接 GND，默认可写 | 模块板原理图评审；到货后按第 7 节第 5 项测锁定 |
| P-02 | 100 nF 去耦足够 | 通用做法；示波器看写周期内 VCC 纹波 |
| P-03 | 模块板有空间放 5 个测试焊盘 | 模块板布局阶段决定；没有也可用槽位公头 |
| P-04 | ESP32-S31 目标 IDF 提供 `i2c_master_transmit` 等同签名 API | 在可编译 BSP 的环境编译示例 |
| P-05 | 主机内部上拉在 100 kHz 下边沿达标 | 示波器量 tR、VIL；决定 DNP 上拉装配 |
| P-06 | 所购 EEPROM 型号页 ≥ 8 字节、tWR ≤ 5 ms、A0-A2 无内部上下拉冲突、WP 低有效 | 打开所购型号原厂手册逐项核对 |
| P-07 | 嘉立创/分销商预烧服务存在与否 | 下单前询问，记录到第 5 节 |
