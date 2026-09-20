提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造

# 底座主板电流与热预算（POWER_BUDGET）

日期：2026-09-21。分支：`claude/design-d/dock-board`。输入提交：`origin/main` `3aa7146`。配套：`POWER_TOPOLOGY.md`（拓扑与器件）、`README.md`（假设 AS-31-dock-n 登记）、`hardware/ASSUMPTIONS.md`（AS-09、AS-10、AS-12、AS-18、AS-26）。

**本文件没有任何 measured 值。** 每个数字都在「来源」列标出：`数据手册`（`POWER_TOPOLOGY.md` 第 0 节列出的四份 TI 文档）、`derived`（由上游数字计算，公式写出）、`ASSUMPTION: AS-xx`（无依据的工作假设）。pin17 输入额定 **unknown**（ICD EL-D-12、D1 DOCUMENT_BOUNDARIES），本文件的全部负载侧数字都建立在 `ASSUMPTION: AS-09` 上，不得被引用为主机额定值。

## 1. 输入假设与常数

| 符号 | 含义 | 值 | 来源 |
| --- | --- | --- | --- |
| I_HOST_PK | 主机经 pin17 取用峰值电流 | 1.0 A | `ASSUMPTION: AS-09`（无官方依据） |
| I_HOST_SUS | 主机持续电流 | 0.6 A | `ASSUMPTION: AS-09` |
| I_HOST_TYP | 主机「典型」电流，仅用于给出续航感觉 | 0.3 A | `ASSUMPTION: AS-31-dock-16`（本文件新增，纯示意；G6-B9 回填） |
| V_BOOST | 升压设定 | 5.10 V 名义，空载 4.93–5.27 V | `ASSUMPTION: AS-31-dock-1`；范围 derived（VREF 580–610 mV，电阻 ±1 %） |
| η_BOOST | 升压效率（VSYS 3.0–4.4 V → 5.10 V，0.3–1.0 A） | 0.88 | `ASSUMPTION: AS-31-dock-3`；数据手册典型 94 % @ 3.6 V/1.5 A，取保守值 |
| V_BAT_NOM / MIN | 电池电压 名义 / 关断点 | 3.7 V / 3.0 V | `ASSUMPTION: AS-12`（电池型号 unknown）/ `ASSUMPTION: AS-31-dock-10` |
| C_BAT | 电池容量 | 1500 mAh | `ASSUMPTION: AS-12` |
| k_USE | 到 3.0 V 关断的可用容量比例 | 0.90 | `ASSUMPTION: AS-31-dock-17`（本文件新增；随电池规格书回填） |
| V_DO_BAT | U_CHG BAT→OUT 压降 @ 1 A | 50 mV typ / 100 mV max | 数据手册 BQ24074 `VDO(BAT-OUT)` |
| V_SYS_USB | 有 USB 输入时 VSYS | 4.4 V typ（4.3–4.5） | 数据手册 BQ24074 `VO(REG)` |
| I_IN_MAX | 输入电流限（R_ILIM_CHG 1.1 kΩ） | 1.46 A typ（1.36–1.56） | 数据手册 KILIM 1610 AΩ（1500–1720）/ 1.1 kΩ；`ASSUMPTION: AS-31-dock-5` |
| I_CHG | 快充电流（R_ISET 1.78 kΩ） | 500 mA typ（448–547） | 数据手册 KISET 890 AΩ（797–973）/ 1.78 kΩ；`ASSUMPTION: AS-31-dock-4` |
| I_OS | 输出限流（R_ILIM_OUT 19.6 kΩ） | 1308 mA nom（1215–1415） | 数据手册 TPS2553 Table 2；`ASSUMPTION: AS-31-dock-2` |
| R_LIM | U_LIM 导通电阻 | 85 mΩ typ / 135 mΩ max（125 °C） | 数据手册 TPS2553 rDS(on) DBV |
| R_RB | U_RB 导通电阻 @ 5 V | 79 mΩ typ / 110 mΩ max | 数据手册 LM66100 RON |
| R_POGO | 单根弹簧针接触电阻 | 50 mΩ | `ASSUMPTION: AS-31-dock-14`（待原厂数据手册核对，AS-26） |
| R_H2 | H2 pin17 / pin20 单针接触电阻 | 30 mΩ 各 | `ASSUMPTION: AS-18` 派生（载流与接触电阻 unknown） |
| R_CU | 底座 + 模块板铜走线合计（5 V 与回流） | 20 mΩ | `ASSUMPTION: AS-31-dock-14`（布线后按 IPC-2221 复算） |

## 2. 输出侧：电压跌落链（`BOOST_5V` → 主机 pin17）

串联电阻（derived）：

| 段 | typ | max |
| --- | --- | --- |
| U_LIM | 0.085 Ω | 0.135 Ω |
| U_RB | 0.079 Ω | 0.110 Ω |
| J2 `DOCK_5V` 两针并联 | 0.025 Ω | 0.025 Ω |
| J2 `DOCK_GND` 两针并联 | 0.025 Ω | 0.025 Ω |
| H2 pin17 + pin20 | 0.060 Ω | 0.060 Ω |
| 铜 | 0.020 Ω | 0.020 Ω |
| **合计 R_PATH** | **0.294 Ω** | **0.375 Ω** |

主机 pin17 处电压（derived：`V_pin17 = V_BOOST − I × R_PATH`）：

| I_HOST | V_BOOST 名义 5.10 V、R typ | V_BOOST 下限 4.93 V、R max | 在 TP_DOCK5V（不含 J2/H2/铜）名义 |
| --- | --- | --- | --- |
| 0.3 A | 5.01 V | 4.82 V | 5.05 V |
| 0.6 A | 4.92 V | 4.71 V | 5.00 V |
| 1.0 A | 4.81 V | 4.55 V | 4.94 V |

判读：pin17 可接受窗口 unknown（`ASSUMPTION: AS-10`）。V1.0 原理图 pin17 后串有二极管 D10 再到充电 IC（`docs/INTERFACE_CONTROL.md` EL-01，V1.2 unknown），若 V1.2 沿用且 D10 为肖特基，峰值 1 A 时主机内部 VCHG 可能低至 ≈4.2–4.3 V，主机内置 65 mAh 电池的充电可能在峰值期间暂停，但系统供电不受影响（derived，仅提示）。**处置**：G6-A7 若观察到主机在底座上充电异常而在原生 USB 正常，优先把 R_FB1 改 768 kΩ（5.16 V）；不得超过 5.25 V 空载上限以留 USB VBUS 类容差（`ASSUMPTION: AS-31-dock-1` 的上界）。

## 3. 电池放电侧（态 B3：只电池）

### 3.1 升压输入功率与电池电流

公式：`P_BOOST_OUT = V_BOOST × I_HOST`；`P_BOOST_IN = P_BOOST_OUT / η_BOOST`；`I_BAT = P_BOOST_IN / (V_BAT − V_DO_BAT)`。

| I_HOST | P_BOOST_OUT | P_BOOST_IN | I_BAT @ 3.7 V（VSYS 3.65） | I_BAT @ 3.3 V（3.25） | I_BAT @ 3.0 V（2.95） | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| 0.3 A | 1.53 W | 1.74 W | 0.48 A | 0.54 A | 0.59 A | derived（AS-09/AS-31-dock-16、-3、-1） |
| 0.6 A | 3.06 W | 3.48 W | 0.95 A | 1.07 A | 1.18 A | derived |
| 1.0 A | 5.10 W | 5.80 W | 1.59 A | 1.78 A | 1.97 A | derived |

器件裕量核对（derived）：

- U_CHG BAT→OUT 通路：`IOUT` 绝对最大 4.5 A（数据手册 Absolute Maximum）；1.97 A 峰值 < 4.5 A。压降 100 mV max @ 1 A，按线性外推 2 A 约 0.2 V（derived，超出表列条件，到货测 TP_VBAT − TP_VSYS 核实）。
- U_PROT/Q_PROT 放电过流阈值须 > 2.0 A 且 < 短路值；DW01A 类典型过流检测电压 150 mV ÷ 双 MOS 导通电阻（待核）→ 阈值待核；若 < 2 A 会在峰值误切，选型时必须核对（`BOM.csv` 备注）。

### 3.2 升压电感电流（最恶劣：VSYS 2.95 V、I_HOST 1.0 A）

数据手册 TPS61023 式 (5)(6)：`IL_DC = V_OUT × I_OUT / (V_IN × η)`；`ΔIL = V_IN × D / (L × f_SW)`，`D = 1 − V_IN/V_OUT`。

| 量 | 值 | 来源 |
| --- | --- | --- |
| D | 1 − 2.95/5.10 = 0.42 | derived |
| IL_DC | 5.10 × 1.0 / (2.95 × 0.88) = 1.96 A | derived |
| ΔIL（L = 1.0 µH，f = 1 MHz） | 2.95 × 0.42 / (1e-6 × 1e6) = 1.24 A p-p | derived；f_SW 1 MHz 为数据手册 typ（VIN > 1.5 V） |
| I_PEAK | 1.96 + 0.62 = 2.58 A | derived |
| I_PEAK（L −30 % = 0.7 µH，数据手册建议按此裕量） | 1.96 + 0.89 = 2.85 A | derived |
| I_VALLEY | 1.96 − 0.62 = 1.34 A | derived；< 谷值限流 2.7 A min，裕量 2× |
| 进入限流时的电感峰值 | 3.7 A + 0.62 = 4.3 A（典型限流值） | derived；决定 L1 饱和电流 |

L1 选型要求：1.0 µH，Isat ≥ 4.5 A，DCR ≤ 30 mΩ（`ASSUMPTION: AS-31-dock-18`，具体型号「待原厂数据手册核对」）。

### 3.3 续航（示意，全部 derived 自 ASSUMPTION）

`t = C_BAT × k_USE / I_BAT(3.7 V)`：

| I_HOST | I_BAT | t |
| --- | --- | --- |
| 0.3 A | 0.48 A | 2.8 h |
| 0.6 A | 0.95 A | 1.4 h |
| 1.0 A（假设持续，实际为峰值） | 1.59 A | 0.85 h |

能量法交叉核对：1500 mAh × 3.7 V × 0.9 = 5.0 Wh；÷ 3.48 W = 1.43 h，与表一致。

**设计后果（提请 Chrome 决策）**：若 G6-B9 实测主机持续电流 ≥ 0.4 A @ 5 V，1500 mAh 的电池只给约 2 h，与「手持终端」用途不匹配；届时应把 AS-12 改为 2500–3000 mAh（体积、重量、充电时间同步变化，机械与充电电流均需改）。本稿不预先放大电池，因为 AS-09 本身没有依据。

## 4. USB 输入侧（态 B5、B7）

### 4.1 输入电流分配（DPPM，系统优先）

`I_SYS = P_BOOST_IN / V_SYS_USB`；`I_CHG_ACT = min(I_CHG, I_IN_MAX − I_SYS)`，若为负则进入电池补充模式。

| 态 | I_HOST | I_SYS @ 4.4 V | I_CHG_ACT | I_IN 合计 | 电池净电流 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| B7 | 0.3 A | 0.40 A | 0.50 A | 0.90 A | +0.50 A（充） | derived |
| B7 | 0.6 A | 0.79 A | 0.50 A | 1.29 A | +0.50 A | derived |
| B7 | 1.0 A | 1.32 A | 0.14 A | 1.46 A（到限） | +0.14 A | derived；DPPM 削充电 |
| B7 | ≥ 1.11 A | ≥ 1.46 A | 0 | 1.46 A | 负（补充模式放电） | derived：1.46 × 4.4 × 0.88 / 5.10 = 1.11 A |
| B5（无电池） | 1.0 A | 1.32 A | — | 1.32 A | — | derived；上限 1.11 A @ 5.10 V 恰好覆盖 AS-09 峰值 |

结论：在 AS-09 下，边用边充始终净充电；无电池态可输出到 1.11 A。若 AS-09 峰值上修到 1.2 A 以上，无电池态将不能覆盖峰值，需改 U_CHG 输入限或允许 `DOCK_5V` 短时跌落——由 Chrome 在 AS-09 回填后决定。

### 4.2 只充电（不接主机）

| 量 | 值 | 来源 |
| --- | --- | --- |
| 输入电流 | ≈ 0.50 A + 1.5 mA（`ICC` 1.1–1.5 mA） | derived + 数据手册 |
| 充电时间 | CC 段 ≈ 1500 × 0.8 / 500 = 2.4 h，CV 尾段 ≈ 1 h，合计 ≈ 3.5 h | `ASSUMPTION: AS-31-dock-4` 派生；默认快充定时 5 h（TMR 悬空 18000 s） |
| 预充电流（VBAT < 3.0 V） | KPRECHG 88 AΩ / 1.78 kΩ ≈ 49 mA | 数据手册 KPRECHG 70–105 AΩ；derived |
| 终止电流 | 0.1 × ICHG = 50 mA（45–55） | 数据手册 ITERM 默认 |

### 4.3 适配器要求

`ASSUMPTION: AS-31-dock-5`：适配器须能供 5 V ≥ 1.5 A。弱适配器（USB-A 500 mA 口、Type-C 默认功率）在 VBUS 跌到 VIN-DPM 4.5 V typ（4.35–4.63 V）时被 U_CHG 自动降流，不会掉电，只是充电与输出能力下降；此时 VSYS 仍 4.4 V 或更低，升压输出不变。**未做 CC 电流广告检测**（Rp 判读），这是有意的简化，见 `DESIGN_NOTES.md` 第 3 节。

## 5. 底座自身静态与辅助电流

### 5.1 只电池、无主机（`DOCK_5V` 空载）

| 项 | 在其所在节点 | 折算到 VBAT（× 5.10/3.65/η_light；轻载 η 取 0.7，`ASSUMPTION: AS-31-dock-9`） | 来源 |
| --- | --- | --- | --- |
| U_BOOST IQ | 20 µA @ VOUT + 0.9 µA @ VIN | ≈ 41 µA | 数据手册 typ |
| U_LIM IIN_on（RILIM ≈ 20 kΩ） | 120 µA typ / 140 max | ≈ 240 µA | 数据手册 |
| U_RB IQ | 0.15 µA | ≈ 0 | 数据手册 |
| R_FB 分压 | 5.10 / 1.029 MΩ = 5 µA | ≈ 10 µA | derived |
| LED_OUT（蓝，Vf ≈ 2.8 V，R 4.7 kΩ） | (5.10 − 2.8)/4.7k ≈ 0.49 mA | ≈ 0.98 mA | derived；Vf 为 `ASSUMPTION`，LED 型号待核 |
| U_CHG IBAT(PDWN) | 4.3 µA typ / 6.5 max | 4.3 µA | 数据手册 |
| U_UV | ≈ 1–2 µA | ≈ 2 µA | 待原厂数据手册核对 |
| U_PROT | ≈ 3 µA | ≈ 3 µA | 待原厂数据手册核对 |
| U_FG（若装） | ≈ 3–25 µA | — | 待原厂数据手册核对；默认 DNP |
| **合计（LED_OUT 装）** | | **≈ 1.28 mA** | derived |
| **合计（JP_LED 断开）** | | **≈ 0.30 mA** | derived |

待机天数（derived，1500 mAh × 0.9）：LED_OUT 装 ≈ 44 天；断开 ≈ 190 天。`ASSUMPTION: AS-31-dock-9` 登记为「装 LED ≤ 1.5 mA，断开 ≤ 0.35 mA」，G6-A3 断 USB、不接主机，串电流表测 VBAT 电流回填。

### 5.2 USB 侧指示灯

LED_PG、LED_CHG 各 (5.0 − 2.0)/1 kΩ ≈ 3 mA，来自 `VBUS_IN`，不计入电池预算；LED_FLT 仅故障时亮，≈ 0.5 mA 来自 `BOOST_5V`。

## 6. 热预算

θJA 均为数据手册 Thermal Information 表（JEDEC 标准板，实际 2 层小板可能更差；`ASSUMPTION: AS-31-dock-15` 实板温升到货测）。环境 25 °C。

| 器件 | 工况 | 功耗（derived） | θJA | 温升 | TJ | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| U_CHG BQ24074 RGT | B7，I_HOST 0.6 A：(5.0 − 4.4) × 1.29 + (4.4 − 3.7) × 0.5 | 0.77 + 0.35 = 1.12 W | 44.5 °C/W | 50 °C | 75 °C | 最热点候选；热调节环 125 °C 不触发 |
| U_CHG | B7，I_HOST 1.0 A：0.6 × 1.46 + 0.7 × 0.14 | 0.98 W | 44.5 | 44 °C | 69 °C | |
| U_CHG | 只充电，VBAT 3.3 V：(5.0 − 3.3) × 0.5 | 0.85 W | 44.5 | 38 °C | 63 °C | |
| U_BOOST TPS61023 DRL | B3，I_HOST 1.0 A：总损耗 (1 − 0.88) × 5.10 = 0.61 W，IC 占 60 %（`ASSUMPTION: AS-31-dock-3` 派生） | 0.37 W | 142.7（标准）/ 91.4（EVM） | 53 / 34 °C | 78 / 59 °C | 需大面积地铜与过孔；数据手册按 EVM 铺铜可达 91.4 |
| U_BOOST | B3，I_HOST 0.6 A | 0.22 W | 142.7 | 31 °C | 56 °C | |
| L1 | I_RMS ≈ 2.0 A，DCR 30 mΩ | 0.12 W | — | — | — | 电感自身温升待选型后核 |
| U_LIM TPS2553 DBV | 1.0 A 连续：0.085 × 1² | 0.085 W | 182.6 | 16 °C | 41 °C | |
| U_LIM | `DOCK_5V` 短路：5.10 × 1.3 | 6.6 W | 182.6 | → 155 °C 关断 | 热循环 | 数据手册设计行为；G6-A5 ≤ 2 s |
| U_RB LM66100 DCK | 1.0 A：0.079 × 1² | 0.079 W | 192 | 15 °C | 40 °C | |
| J2 弹簧针 | 1.0 A，每针 0.5 A × 50 mΩ | 12.5 mW/针 | — | — | — | G6-F1 红外测针区 |

判读：无器件超出额定；U_CHG 与 U_BOOST 是两个需要铺铜散热的位置，布局阶段按各自数据手册 Layout 节处理。**TH-07 正式值待 Chrome 定义**；`DESIGN_NOTES.md` 第 5 节给出建议。

## 7. 到货后实测步骤（把本文件每个 ASSUMPTION 变成 MEASURED）

按 `hardware/G6-TEST-PLAN.md` 编号执行，本节只说明每一步回填哪个数字。

| 步骤 | 条件 | 测什么 | 回填 |
| --- | --- | --- | --- |
| G6-A2 | 只 USB、空载 | TP_DOCK5V 电压；USB 在线表电流 | AS-31-dock-1 空载电压；第 5 节静态电流的 USB 侧部分 |
| G6-A3 | 接电池、断 USB、空载 | 串电流表测 VBAT 电流（LED_OUT 装/断各一次） | AS-31-dock-9 |
| G6-A3 | 接电池、接 USB | USB 电流 = 充电电流 + 静态 | AS-31-dock-4、-5（TH-04） |
| G6-A4 | 假负载 0.2/0.5/1.0 A，三种供电 | TP_DOCK5V、TP_BOOST、TP_VSYS、TP_VBAT 电压；输入电流；红外各热点 | 第 2 节跌落链（R_LIM、R_RB 实值）；AS-31-dock-3（η = P_out/P_in）；AS-31-dock-15 温升 |
| G6-A4 | 1.0 A 级，只电池 | 有示波器时探 L1 两端或 SW 节点电流（可选） | 第 3.2 节电感峰值 |
| G6-A5 | 短路 ≤ 2 s | 短路电流读数 | AS-31-dock-2（TH-03） |
| G6-B2 | 只原生 USB | 流入底座电流、`DOCK_5V` 节点电压 | TH-06；AS-11 |
| G6-B7 | 边用边充、主机满载 | USB 电流、VBAT 电流方向与大小、U_CHG 温度 | 第 4.1 节 DPPM 分配；AS-31-dock-15 |
| G6-B9 | 主机单独经原生 USB 满载 | 峰值/持续电流 | **AS-09 回填**，本文件全部负载侧数字随之重算；AS-31-dock-16 |
| G6-G2 | 每 10 次插拔，0.5 A | 针–焊盘压降 | AS-31-dock-14（TH-08） |
| 台架 | 可调电源代替电池，3.4 → 2.8 V 缓降再回升 | `DOCK_5V` 关断/恢复时的 VBAT | AS-31-dock-10 |
| 台架 | 电池规格书 | 容量、保护板、NTC、尺寸 | AS-12、AS-31-dock-6、-7、-17 |

## 8. 版本历史

| 版本 | 日期 | 变更 | 作者 |
| --- | --- | --- | --- |
| A0-proposal | 2026-09-21 | 首稿：输入假设表、跌落链、电池侧、USB 侧 DPPM 分配、静态电流、热预算、实测回填映射 | Claude 主控（claude-fable-5-1） |
