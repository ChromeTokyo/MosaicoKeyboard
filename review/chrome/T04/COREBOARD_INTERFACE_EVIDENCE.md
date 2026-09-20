# T04 前置核查：CoreBoard V1.0 电源与 I²C 接口证据

- 核查日期：2026-09-20（日本）。Chrome 内部资料核查；不是 Hiro 独立复核，不构成 T04、G1 或硬件放行。
- 适用版本：`SCH_ESP-Mosaico_CoreBoard_V1_0`，图框更新日期 `2026-08-18`，共 5 页；实物版本仍须核对。
- 方法：由官方用户指南的 Related Documents 链接确认 PDF 地址；下载原文件、文本定位、逐页渲染并目视核对网络与器件。未上电、未实测、未做电路仿真。
- 证据标签：**官方图示**＝文件直接画出；**推导**＝根据图示关系计算或推断；**未知**＝这些材料不能闭环。

## 1. 来源与可复核材料

| ID | 官方来源 | 本地证据与定位 |
| --- | --- | --- |
| S1 | [ESP-Mosaico V1.0 用户指南](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s31/esp-mosaico/user_guide.html) | [2026-09-20 HTML 快照](evidence/user-guide-2026-09-20.html)；Hardware Notes / DCDC 3.3 V Circuit / I²C Device Addresses / Module Interface / Related Documents |
| S2 | [CoreBoard V1.0 官方原理图 PDF](https://dl.espressif.com/AE/SCH_SCH_ESP-Mosaico_CoreBoard_V1_0_2026-08-18.pdf) | [原始 PDF](evidence/coreboard-v1.0-2026-08-18.pdf)；以下页码均为 PDF 页码，图框页码一致 |
| S3 | 本仓库已收录的官方 BaseBoard 图与第 3 章证据 | [Claude 证据索引](../../claude/official-evidence/README.md)；背面外视丝印 `SDA / + / − / SCL`，与底座贴合面的镜像处理见接口约束 |
| S4 | [ESP-Mosaico 产品指南](https://mosaico.espressif.com/guide/) | [2026-09-20 HTML 快照](evidence/mosaico-product-guide-2026-09-20.html)；Expansion I/O 给出模块 5 V 与 3.3 V 输出各最大 100 mA |

[EVIDENCE_MANIFEST.json](EVIDENCE_MANIFEST.json) 登记下载来源、文件 SHA-256、字节数与截图生成方法。全页图为从原 PDF 渲染的预览；局部图只作定位，原 PDF 为权威输入。文本提取仅作查找辅助。

## 2. 背部 `+` 与 `5V_IN`：架构对应已找到，物理导通仍未闭环

**官方图示：** S2 **p1 Overview，右下 `4P POGOPIN` 框**，电源箭头明确标为 `5V_IN`，另一组信号标为 `I2C`；同页左侧的两组 2×10P 接口也标 `5V_IN`。这比仅凭丝印 `+` 更强，支持“背部四触点电源的设计意图是 5 V 输入”。见 [p1 全图](evidence/coreboard-page-1.png)。

**官方图示：** S2 **p3 Interface，CN3** 把 `5V_IN` 引到 **45/47/49/51**，`GPIO_0` 到 **30**，`GPIO_1` 到 **28**；`VCC_3V3` 为 **53/55/57/59**，`5V_OUT` 为 **54/56/58/60**。见 [CN3 局部](evidence/p03-btb-pins.png)。S1 的 H1/H2 引脚表均把 Pin17 定为外部 5 V 输入，可供电并给板载电池充电。

**仍未知：** 本 PDF 没有 BaseBoard 详细原理图、背部四焊盘的位号/逐脚网络、走线宽铜厚或触点电流额定值。因此它不能单独证明“实物 `+` 到 CN3 对应脚无额外器件且直通”，也不能给出安全持续电流。应取得 BaseBoard 原理图，或在完全断电且已隔离电池的条件下按单独工程复核规程测量导通；普通用户的首轮尺寸测量不要求执行此项。

**接口约束建议：** 可把电源类别写成“官方架构 `5V_IN`，BaseBoard 实物网络待核”；不可把某二极管、USB 或升压芯片的额定电流套到背部焊盘。`docs/DESIGN_STATUS.md` 中“背部电源在 CoreBoard 原理图标为5V_IN”应保留这种证据层级，不能扩大为全部接口已确认。

## 3. CoreBoard 输入链与保护边界

S2 **p5 Power** 的 [输入路径局部图](evidence/p05-input-paths.png) 可直接追踪：

```text
5V_IN -> D10 (DSK24) -> VCHG / VBUS_IN
                       |-> U23 TP4057 的 VCC，给板载电池充电
                       +-> D15 (DSK24) -> VSYS -> Q2.1 (WST2011) -> VDD

5V_IN -> D9 (B5819WS) -> 5V_IN_flag
Type-C VBUS -> Q2.2 (WST2011) -> D13 (DSK24) -> VCHG / VBUS_IN
```

其中 D9 为供电状态/电池路径控制分支，不是主负载串联通路。p5 同时画出 VBAT 经 D11 与 Q6 到 VSYS 的电池供电分支。

**可确认的边界：** CoreBoard 的 `5V_IN` 主通路有二极管隔离及整机电源开关；本页未在 `5V_IN -> D10 -> VCHG` 上画出独立可调限流器、保险丝或过压关断器。不能据此宣称 BaseBoard 上也一定没有保护，也不能把二极管隔离等同完整输入保护。持续电流、压降、温升和异常供电边界仍需器件逐项核算及实测。

**U18 不在上述输入通路。** p5 **U18 TPS2041BDBVR** 的 IN/Pin5 接 `VOUT_BOOST / 5V_OUT`，OUT/Pin1 接 Type-C `VBUS`；见 [USB 输出局部图](evidence/p05-usb-output-path.png)。因此指南的 **5 V / 500 mA、超过 1 A 后关断并延时恢复**是 Type-C 作 source 时的描述，**不是 `5V_IN`、背部焊盘或模块 `5V_OUT` 的可用电流规格**。底座自己的输入/输出限流和故障观测仍必须设计。

S4 的 **Expansion I/O** 另给出模块 **5 V 输出最大 100 mA、3.3 V 输出最大 100 mA**；这两项不能套到 `5V_IN` 或背部输入触点。其原文没有明确左右槽能否各自取 100 mA 后叠加；两槽电源又连接同名共享网络，因此在获得更完整规格前，设计预算按每条共享输出轨总计不超过 100 mA 处理，而不是按槽数翻倍。这是保守设计约束，不是对厂家未给信息的补写。

板载电池 S1 标称 **3.7 V / 65 mAh**；S2 p1 的 4.2 V 电池标注是另一电压条件，不应误读为不同标称化学体系。p5 U23=TP4057、R47=15 kΩ，原图公式约 66 mA，与指南额定 65 mA 一致到标称精度；此电路不应拿来直接充底座大电池，两电池不可直接并联。

## 4. I²C 电平域、已有上拉与条件等效

| 项目 | 已确认的原图关系 | 对底座的约束 |
| --- | --- | --- |
| 共享总线 | p2 GPIO0/SDA 连 `BAT_SDA / AUDIO_SDA / BMI_SDA / TP_SDA`；GPIO1/SCL 连对应时钟网络 | 不是专用空闲 I²C，总线异常会影响主机多个功能 |
| 主侧上拉 | p2 **R2=4.7 kΩ，GPIO0/SDA -> MCU_3V3**；**R1=4.7 kΩ，GPIO1/SCL -> MCU_3V3** | 主侧已有 3.3 V 域上拉；不能默认“无上拉”再固定并接一组 |
| Codec 支路 | p4 **R21/R24 各 2.2 kΩ -> CODEC_3V3**，经 **Q1.1/Q1.2 LBSS138DW1T1G** 与 AUDIO_SDA/SCL 相接；ES_SDA/SCL 再经 **R25/R26 各33 Ω**进入 ES8311 | Codec 供电状态会改变低电平吸收电流与动态行为；不能把两侧当作一根永远等效固定电阻的总线 |
| 其他支路 | p3 BMI270、两颗 BMM150 均连主侧；显示/触摸通过 LCD 连接器连接 | 此 CoreBoard 图不能排除显示组件、BaseBoard 或已插模块的额外上拉/电容 |

见 [p2 上拉及共享网络](evidence/p02-i2c-pullups.png)、[p4 Codec 隔离/上拉](evidence/p04-codec-i2c.png) 与 [p4 全页串阻位置](evidence/coreboard-page-4.png)。

**有条件的推导：** 当 MCU_3V3 和 CODEC_3V3 均为 3.3 V、Q1 在低电平传递时导通，忽略 MOS 管导通压降，已知两组上拉对应约 `4.7 kΩ || 2.2 kΩ = 1.50 kΩ`，低电平接近 0 V 时约 **2.20 mA/线**。这仅是已知支路的低电平电流估算，**不是全总线在高电平、上升沿或 Codec 断电时的实测等效电阻**。R25/R26 位于 Codec 管脚侧，拉低器件位置也影响其压降。新增底座上拉须合并核算 VOL、吸收电流与上升时间，底座与主机任一断电时必须避免 I²C 反向供电。

S1 预留/占用的 7 位地址集合为 `0x11, 0x12, 0x19, 0x50, 0x51, 0x55, 0x5A, 0x69`。其中 `0x50/0x51` 是所插模块的 EEPROM，**不是保证任何裸机扫描都出现的器件**；底座仍须避开，除非未来明确获得对应槽位功能所有权并通过 BSP 方案审查。

## 5. GPIO60 与 5V_OUT：发现需要实物验证的文图差异

**官方图示：** p2 `VCC_PW = GPIO60`；p5 **Q5 AO3401A** 把 `MCU_3V3` 切换为 `VCC_3V3`，其 gate 接 VCC_PW，R51=100 kΩ 接回 MCU_3V3。p5 **U16 SY7088DGC** 的 EN/Pin9 接 `VCC_3V3`，因此 GPIO60 拉低可开启 VCC_3V3 并使能升压。见 [p5 电源控制](evidence/p05-power-control.png)、[p5 全页](evidence/coreboard-page-5.png)。

**但存在额外供电路径：** p5 **D14 DSK24** 从 Type-C **VBUS 正向连接到 `5V_OUT / VOUT_BOOST`**。它绕过 Q5 和 SY7088 的 EN 控制。S1 的 Hardware Notes 把模块 3.3 V/5 V 输出概括为 GPIO60 低时才输出；**原图不能支持把这句话用作“USB 已连接时 GPIO60 高能保证5V_OUT无电”的隔离保证**。

这是根据原图的电气推导，尚未经过实物验证。接口约束应保留此冲突：在 USB 输入存在时，5V_OUT 可能仍由 D14 获得电压。不得把 GPIO60 当作底座防反灌/紧急断电元件，也不得向 `5V_OUT` 外加底座供电。

必须由后续工程测试覆盖：USB 无/有 × 主机开/关 × GPIO60 高/低时的 `5V_OUT`、`VCC_3V3`、`MCU_3V3` 电压；同时记录底座是否连接。测试状态不得强迫一个已断电 GPIO 输出电平。限流、反向电流及两电源同时连接的验证另列 T04/G6，不交给首次尺寸测量直接操作。

## 6. GPIO57 / POWER_SWITCH 与 O07

S2 **p2 R19=0 Ω** 将 `GPIO57` 接至 `POWER_SWITCH`；p5 它连接 **U22 SAM8108 ONOFF/Pin4** 及按键 **S3** 的对地触发端。U22 OUT/Pin6 输出 `PWR_EN`，后者控制 Q2.1，见 p5 电源控制图。S1 DCDC 章节明确 BSP 正常运行保持 GPIO57 高阻，需要关机时以开漏拉低请求关闭。

可以记录这一请求语义，不能把 GPIO57 描述为切断底座电池的开关。方案 A 的四触点没有 GPIO57；方案 B 的官方 H1/H2 表与六调试焊盘也没有把 GPIO57 列为直接可用接点。CN3/Pin11 虽画出 GPIO57，CN3 本身不是本轮获准新增的接触资源。BOOT、EN/CHIP_PU 也不能等同 SAM8108 的 POWER_SWITCH。

## 7. 尚未解除的阻塞与后续输入

1. BaseBoard 原理图或合格断电导通证据：`+/-/SDA/SCL` 到对应内部网络、是否额外保护、实物板版本。
2. 背部触点和模块输入通孔、走线及连接器的额定输入电流与持续温升；不能由 USB source 500 mA 或模块输出 100 mA 倒推。模块输出已找到 S4 的 100 mA 限制，双槽合计边界仍待确认。
3. 上拉/寄生电容实测与电源状态相关 I²C 波形；器件绝对额定值、低电平/热插拔/断电容限须在选型审核中逐项完成。
4. D14 对 5V_OUT 的 USB 旁路行为，以及 USB/底座同时存在时的供电优先级与反灌量。
5. Hiro 对 Chrome 最终接口/电源修订独立复核；本资料包只补充输入，**不关闭上述问题，不冻结 PCB**。

此外，CoreBoard 原理图只定义电气连接，没有说明背面所见部件是独立外盖还是带电池/连接器的 BaseBoard，也没有给出四螺丝的安全拆解步骤。不能根据 Fig.7 的照片就把“拆背板”写成普通用户已获证实可反复执行的动作。
