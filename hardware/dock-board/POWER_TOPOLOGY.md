**历史记录（2026-09-24 C7）：方案 D＋G 分立电源链已被 D-029 的现成模块方向取代；本文件与旧 J2 几何不可用于现行方案 J 或制造。见 [ARCHIVED.md](ARCHIVED.md)。以下原文保留供追溯。**

提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造

# 底座主板电源拓扑（POWER_TOPOLOGY）

日期：2026-09-21。分支：`claude/design-d/dock-board`。输入提交：`origin/main` `3aa7146`（含 `hardware/ICD-0.2-DRAFT.md`、`hardware/ASSUMPTIONS.md`、`hardware/G6-TEST-PLAN.md`）。配套文件：`POWER_BUDGET.md`（电流预算）、`netlist.yaml`（逐针网表）、`schematic.svg`、`BOM.csv`、`DESIGN_NOTES.md`（取舍与验证清单）、`README.md`（本子系统假设登记 AS-31-dock-n）。

本文件回答一个问题：底座 USB-C 与单节锂电如何变成 `DOCK_5V`，并证明该路径满足 ICD 第 4 节 EL-D-01（纯硬件）、EL-D-08（双供电防反灌）、EL-D-11（不向主机注入）与硬约束 1、8。**所有阈值数值仍是提案**，`hardware/G6-TEST-PLAN.md` 第 2 节 TH-01～TH-12 的正式取值由 Chrome 定义；本文件在 `DESIGN_NOTES.md` 第 5 节给出「建议值」供其参考。

## 0. 读法与标签

- 数值来源分四类：**数据手册**（本次实际打开的 PDF，给出文档号、URL 与 typ/min/max）、**derived**（由数据手册数值计算）、**ASSUMPTION: AS-xx / AS-31-dock-n**（无依据的工作假设，验证方法见 `README.md` 第 2 节与 `hardware/ASSUMPTIONS.md`）、**待原厂数据手册核对**（未打开数据手册的器件）。
- 本次实际打开的数据手册（文本已抽取核对）：
  - TI TPS2553，SLVS841F（2016-08），https://www.ti.com/lit/ds/symlink/tps2553.pdf
  - TI LM66100，SLVSEZ8A（2019-06），https://www.ti.com/lit/ds/symlink/lm66100.pdf
  - TI BQ24074，SLUS810N（2021-10），https://www.ti.com/lit/ds/symlink/bq24074.pdf
  - TI TPS61023，SLVSF14B（2020-08），https://www.ti.com/lit/ds/symlink/tps61023.pdf
- 以上四颗为**主候选**。它们是否在嘉立创常备料（基础/扩展库）以及 LCSC 编码，本稿未能核实，全部标「LCSC 编码待核」（AS-27）。每类各给 2 个备选，见 `BOM.csv`。
- 网络名遵守 ICD 第 9 节：`VBUS_IN`（USB-C 输入）、`VBAT`（电池正）、`VSYS`（系统母线 = 充电 IC OUT）、`BOOST_5V`（升压输出）、`LIM_5V`（限流后、防反灌前，本板内部节点）、`DOCK_5V` / `DOCK_GND`（弹簧针接口）。

## 1. 拓扑总览

```
 USB-C J1 ──F1──┬──► VBUS_IN ──► U_CHG.IN                       ┌─────────────────────────────┐
 (CC1/CC2 各    │    (TVS D1)      BQ24074 线性充电 + 电源路径     │ 纯硬件链，无任何主机信号进入 │
  5.1 kΩ→GND)   └──LED_PG/LED_CHG   ├─ BAT ◄──► VBAT ◄── J3 电池 (B+, NTC, B−) ── U_PROT+Q_PROT ── DOCK_GND
                                    │            └─ TS ◄── NTC / R_TS_FIX
                                    └─ OUT ──► VSYS ──► U_UV(3.0 V 检测) ──► BOOST_EN ──► U_BOOST.EN
                                                 │                                   (SW_DOCK 到位联锁，DNP)
                                                 └──► U_BOOST TPS61023 (L1 1 µH) ──► BOOST_5V (5.10 V 名义)
                                                                                         │
                                                      U_LIM TPS2553 (RILIM 19.6 kΩ → IOS ≈1.3 A, 反向 135 mV 关断) ◄┘
                                                                                         │ LIM_5V
                                                      U_RB LM66100 理想二极管 (CE=VOUT, 反向即刻关断) ◄──────┘
                                                                                         │
                                                      DOCK_5V ──► J2 列 1 (A1,B1) ──► 模块板 SLOT_5V_IN ──► 主机 H2 pin17
                                                      DOCK_GND ──► J2 列 2 (A2,B2)
```

五级串联，每级只做一件事：① 输入保护与 USB 合规下拉；② 充电与电源路径（系统优先、电池补充）；③ 低压关断使能；④ 升压到 5.10 V；⑤ 限流 → 防反灌 → 接口。**链上没有 MCU、没有 I²C、没有来自 J2 任何信号线的反馈**；`KEY_*`、`DOCK_SDA/SCL` 与电源链在铜上完全不相交（见 `netlist.yaml`）。

## 2. 各级说明

### 2.1 USB-C 输入（J1、F1、D1、R_CC1/R_CC2）

- J1：USB Type-C 16P 母座，仅用 VBUS、GND、CC1、CC2；D+/D−、SBU 不连。CC1、CC2 各经 5.1 kΩ 到 `DOCK_GND`（USB Type-C 规范 UFP/Sink 的 Rd，声明为受电设备；不做 PD，不取 9 V/12 V）。`ASSUMPTION: AS-31-dock-12` 底座只按 5 V 单一输入设计。
- F1：2 A 一次性保险丝或 PPTC，1206。选型「待原厂数据手册核对」。作用是电池或 IN 侧硬故障时切断适配器，不参与正常限流（正常限流由 U_CHG 的 ILIM 完成）。
- D1：5 V 工作电压 TVS 到 `DOCK_GND`（VBUS 浪涌/ESD）。U_CHG 自身输入 OVP 10.5 V（数据手册 Table「Device Comparison」BQ24074 VOVP = 10.5 V；IN 引脚可承受 26 V 不损坏但停止工作，Pin Functions 表）。因此不另加输入 OVP 器件。
- LED_PG（绿，PGOOD）与 LED_CHG（红，CHG）各经 1 kΩ 接 `VBUS_IN`：两者是 U_CHG 的开漏状态输出（Pin Functions：PGOOD 在有效输入时拉低；CHG 在充电中拉低、充满或禁用时高阻），LED 电流来自适配器而非电池。

### 2.2 充电与电源路径（U_CHG = BQ24074，VQFN-16 3×3 mm）

选择理由：**独立式（standalone），无 I²C、无 MCU 配置**；自带动态电源路径管理（DPPM）与电池补充模式，边用边充时充电电流独立于系统负载可正常终止；输入电流限可编程到 1.5 A；OUT 在无电池或电池损坏时仍能供系统（数据手册第 1 页描述："enables the system to run with a defective or absent battery pack"）。这一条直接支持 G6-A2「只 USB、不接电池」的分步上电顺序。

引脚配置（数据手册 Table 7-1 / 7-2）：

| 引脚 | 接法 | 依据 |
| --- | --- | --- |
| IN (13) | `VBUS_IN`，C_IN 10 µF | 输入范围 4.35–10.5 V（BQ24074） |
| OUT (10,11) | `VSYS`，C_OUT 10 µF | 有输入时 OUT 调节至 4.4 V typ（4.3–4.5 V，`VO(REG)` BQ24073/74）；无输入时 OUT 经内部 FET 接 BAT，`VDO(BAT-OUT)` 50 mV typ / 100 mV max @1 A |
| BAT (2,3) | `VBAT`，C_BAT 10 µF | 充电电压 4.20 V（4.16–4.24） |
| TS (1) | 电池 NTC 或 R_TS_FIX 10 kΩ | 「TS monitors a 10 kΩ NTC thermistor」；不用时接 10 kΩ 固定电阻。阈值对应 Vishay 2 型曲线 R25 = 10 kΩ 的 0 °C / 50 °C，3 °C 迟滞（EC 表注 1）。`ASSUMPTION: AS-31-dock-7` |
| ISET (16) | R_ISET 1.78 kΩ → 500 mA | `ICHG = KISET / RISET`，KISET = 890 AΩ typ（797–973）→ 500 mA typ（448–547 mA）。`ASSUMPTION: AS-31-dock-4` |
| ILIM (12) | R_ILIM_CHG 1.1 kΩ → ≈1.46 A | `IINmax = KILIM / RILIM`，KILIM = 1610 AΩ typ（1500–1720，ILIM 500 mA–1.5 A 段）→ 1.46 A typ（1.36–1.56 A）；允许阻值 1.1–8 kΩ。`ASSUMPTION: AS-31-dock-5` |
| EN2 (5) / EN1 (6) | EN2 → `VSYS`（高），EN1 → `DOCK_GND`（低） | Table 7-2：(EN2, EN1) = (1, 0) 为「由 ILIM 电阻设定」。EN 引脚内部 285 kΩ 下拉，不得悬空。EN2 接 `VSYS` 而非 `VBUS_IN`，因为 VSYS ≤ 4.5 V 不会超过逻辑引脚绝对最大值，而 IN 可达 26 V |
| CE (4) | `DOCK_GND`（低 = 允许充电） | 内部 285 kΩ 下拉，不得悬空 |
| ITERM (15) | 开路 → 默认 10 % ICHG = 50 mA | Pin Functions：悬空为默认 10 % 终止 |
| TMR (14) | 开路 → 默认定时（预充 1800 s，快充 18000 s = 5 h）；预留 R_TMR 焊位（DNP） | 数据手册「Dynamic Charge Timers」：DPPM 降流时定时器同步放慢。1500 mAh / 0.5 A 名义 3 h，在 5 h 内；若实测常触发，装 R_TMR 72 kΩ → 10 × 72 × 48 s = 9.6 h |
| PGOOD (7) / CHG (9) | LED，见 2.1 | 开漏，最大灌电流 15 mA |
| VSS (8) / PAD | `DOCK_GND` | PAD 必须与 VSS 同电位，不作主地引入 |

关键行为（数据手册第 9.3 节 Power Path）：输入有效时**系统负载优先**，`VDPPM = VO(REG) − 100 mV`：当输入电流限使 OUT 跌到 4.3 V，先削减充电电流；若系统需求超过输入限，进入电池补充模式（`VBSUP1`：OUT ≤ VBAT − 40 mV 进入），电池向系统放电。VIN-DPM 4.5 V typ（4.35–4.63 V）：弱适配器压降到此值时自动降输入电流，不会拖垮 USB 源。

热预算（derived，见 `POWER_BUDGET.md` 第 4 节）：输入 1.46 A、OUT 4.4 V 时线性压差功耗 ≈ (5.0 − 4.4) × 1.46 ≈ 0.88 W，加充电 (4.4 − 3.7) × 0.5 ≈ 0.35 W，合计 ≈ 1.2 W。BQ2407x 有热调节环（TJ 达 125 °C 时降充电电流，Figure 8-1），不会损坏但会拖慢充电。`ASSUMPTION: AS-31-dock-15` θJA 与实际温升到货测（G6-F1）。

### 2.3 电池、保护与 NTC（J3、U_PROT、Q_PROT、R_TS_FIX）

- J3：3 针电池插座（B+、NTC、B−），2.0 mm 间距 PH 类（型号待机械与 AS-12 电池型号确定）。若电池包无 NTC 线，J3 pin 2 悬空、装 R_TS_FIX 10 kΩ。
- U_PROT + Q_PROT：单节锂电保护 IC（DW01A 类：过充 ≈4.25–4.30 V、过放 ≈2.40 V、过流/短路；全部参数「待原厂数据手册核对」）+ 双 N-MOS（FS8205A 类）串在 B− 与 `DOCK_GND` 之间。**默认装配**（`ASSUMPTION: AS-31-dock-6`：电池包是否自带保护板 unknown）。若 AS-12 确认包内有 PCM，可 DNP 并用 0 Ω R_PROT_BYP 桥接 B− 到 `DOCK_GND`。
- 分工：过充由 U_CHG 的 4.20 V 调节 + U_PROT 过充作后备；过放由 U_UV 3.0 V 关断升压（2.4 节）先于 U_PROT 的 2.4 V 动作；过流/短路由 U_PROT 完成（U_CHG 对 OUT 也有短路检测 `VO(SC1/SC2)`）；温度由 TS 完成。四种故障均为**硬件**动作，无任何软件参与——这是第 3 节 (d) 的依据。
- NTC 参考点：包内 NTC 通常参考 B−，而保护 MOS 串在 B− 与地之间，充放电流下 B− 相对地有 Q_PROT 导通压降（数十 mV 级），对 75 µA 偏置的 10 kΩ NTC 读数影响可忽略（derived）；到货时按 G6-A3 记录 TS 电压即可确认。

### 2.4 低压关断使能（U_UV → BOOST_EN）

问题：U_BOOST 输入 UVLO 只有 0.5 V（下降）（TPS61023 EC 表 `VIN_UVLO` falling 0.4–0.5 V），U_PROT 过放 2.4 V；若不另设关断点，底座会把电池一直放到保护动作，损害循环寿命。

方案：电压检测器 U_UV（检测点 3.0 V，释放 ≈3.1–3.15 V，CMOS 推挽输出，SOT-23-3；候选见 `BOM.csv`，参数「待原厂数据手册核对」）监测 `VSYS`，输出经 R_EN 100 kΩ 驱动 U_BOOST.EN（EN 高阈值 ≤ 1.2 V，低阈值 0.35–0.45 V，TPS61023 EC 表）。`ASSUMPTION: AS-31-dock-10`。

- USB 接入时 `VSYS` = 4.4 V > 3.0 V，输出恒开，与电池是否耗尽无关 → EL-D-01 满足。
- `SW_DOCK`（**DNP，默认不装**）：常闭型微动开关焊位，接在 BOOST_EN 与 `DOCK_GND` 之间；装配后未放入 Mosaico 时把 EN 拉低（经 R_EN 与 U_UV 输出隔离），放入到位后开关断开、输出开启。这是 ICD 3.3 节「机械到位联锁」的可选实现，**仍是纯硬件**，不依赖主机信号。默认 DNP 是为了满足 G6-A2「不接 Mosaico 时 `DOCK_5V` 即有输出」的分步测试顺序；是否装配由 Chrome 在 G6-G 插拔试验后决定。

### 2.5 升压（U_BOOST = TPS61023，SOT-563；L1 1 µH；R_FB1/R_FB2）

- 输入 0.5–5.5 V，输出可设 2.2–5.5 V，谷值电流限 3.7 A typ（2.7 A min），同步整流，1 MHz（VIN > 1.5 V）；数据手册第 8.1 节："can output 5 V and 1.5 A from a single-cell Li-ion battery"；效率 94 % @ VIN 3.6 V、VOUT 5 V、IOUT 1.5 A（特性页）。**关断时输入输出真断开**（True disconnection），输出 OVP 5.7 V typ（5.5–6.0 V）。
- 输出设定：`VOUT = VREF × (1 + R1/R2)`，VREF = 595 mV typ（580–610 mV，PWM 模式）。取 R_FB1 = 909 kΩ、R_FB2 = 120 kΩ（均 1 %）→ 5.10 V 名义；含 VREF ±2.5 % 与电阻 ±1 %，空载约 4.93–5.27 V（derived）。`ASSUMPTION: AS-31-dock-1`（pin17 输入窗口 unknown，AS-10；若 G6-A7 表明主机需更高/更低，只改 R_FB1：768 kΩ → 5.16 V，750 kΩ → 5.06 V）。R2 < 300 kΩ 满足数据手册 8.2.2.1 的建议。
- L1：1 µH（数据手册允许 0.37–2.9 µH），饱和电流 ≥ 4.5 A（谷值限 3.7 A + 半个纹波），DCR ≤ 30 mΩ，4×4 mm 屏蔽功率电感；型号「待原厂数据手册核对」。电感电流计算见 `POWER_BUDGET.md` 第 3 节。
- C_BST_IN 10 µF（与 U_CHG 的 C_OUT 并联在 `VSYS`）；C_BST_OUT 2 × 22 µF X5R 10 V（有效电容随直流偏压下降，按 ≥ 20 µF 有效值选）。
- 工作点：`VSYS` 3.0–4.5 V 恒小于 5.10 V，**永不进入直通（pass-through）模式**，因此不依赖该功能。

### 2.6 限流（U_LIM = TPS2553，SOT-23-6，EN 高有效，恒流型）

- 工作范围 2.5–6.5 V；连续输出 1.5 A（TJ ≤ 105 °C）；rDS(on) 85 mΩ typ（DBV）；软启动内置（输出上升 0.7–1.5 ms）；短路响应 2 µs；过热 155 °C 关断后自恢复（恒流型「limits the current to IOS until the overload condition is removed or the device begins to thermal cycle」）。
- 限流设定：`IOS_nom(mA) = 23950 / RILIM(kΩ)^0.977`。取 R_ILIM_OUT = 19.6 kΩ（1 %）→ Table 2：IOS min/nom/max = 1215 / 1308 / 1415 mA。`ASSUMPTION: AS-31-dock-2`：名义 1.3 A 覆盖 AS-09 峰值 1 A 并留约 20 % 裕量，同时上限 1415 mA < U_RB 与 U_LIM 自身 1.5 A 连续额定。**TH-03 正式值由 Chrome 定义**；换 26.1 kΩ 即 1.0 A 档（908/989/1081 mA）。
- 反向电压保护（第 9.3.2 节）：当 VOUT 高于 VIN 135 mV typ（95–190 mV）持续 4 ms typ（3–7 ms）时关断 MOSFET，FAULT 拉低；恒流型在反向条件消失后自动恢复。未上电时反向漏电 `IREV` ≤ 1 µA（VOUT 6.5 V、VIN 0 V）。
- EN (3) 经 R_EN_LIM 100 kΩ 接 `BOOST_5V`（升压有电即开启）；FAULT (4) 开漏经 R_FLT 4.7 kΩ + LED_FLT（红）接 `BOOST_5V`，FAULT 去抖 7.5 ms（过流）/ 4 ms（反向）；C_LIM_IN 0.1 µF 靠近 IN。
- 变体：TPS2553-1（锁死型）过流后需断电或翻转 EN 才恢复；无 MCU 的底座只能靠拔 USB/等电池、或 SW_DOCK 翻转 EN 恢复，**默认不选**，见 `DESIGN_NOTES.md` 第 3 节。

### 2.7 防反灌（U_RB = LM66100，SC-70-6）

- 1.5–5.5 V，1.5 A 连续，RON 79 mΩ typ @ 5 V（110 mΩ max，−40～85 °C），IQ 150 nA。CE (3) 接 VOUT：数据手册 Pin Functions 明示「Can be connected to VOUT for reverse current protection」；比较器：VCE − VIN > 35 mV typ（0–80 mV）关断，< −150 mV typ（−250～−80 mV）开启。
- 反向阻断后 OUT→IN 漏电 ≤ 5.1 µA max（−40～105 °C），≤ 2.1 µA 另一条件（EC 表两行，条件差异见原文第 5 页）。反向激活电流 `IRCB` 0.5 A typ / 1 A max（VCE = VOUT）：即反向电流需先在 RON 上建立 ≥ VOFF 才触发关断——这是比较器型理想二极管的固有特性，稳态反向电流由本板 `BOOST_5V` 节点自身的静态电流（约 0.15 mA，见 `POWER_BUDGET.md` 第 5 节）而不是 IRCB 决定，因为同步升压在 VOUT 高于设定值时停止开关、其 PMOS 体二极管方向阻断 VOUT→SW。
- ST (5) 接 TP_ST（状态测试点，仅测量）；N/C (4) 接地。
- R_BYP（0 Ω，**DNP**）跨 VIN–VOUT：若 Chrome 复核后判定 U_LIM 单级反向保护足够，可去掉 U_RB 改桥接；默认两级独立（AS-11 主机内部拓扑 unknown，两级成本极低）。

### 2.8 输出节点（DOCK_5V、DOCK_GND、J2 列 1/2）

- C_DOCK 仅 1 µF：热插拔时向主机输入电容倾泻的电荷来自此电容与 U_LIM 恒流输出，故意把大电容留在 `BOOST_5V` 侧，减小 AS-19 涉及的接触瞬态（`DESIGN_NOTES.md` 第 4 节）。
- D2：5 V 双向 TVS（`DOCK_5V` 到 `DOCK_GND`），保护暴露的弹簧针。
- LED_OUT（蓝/白）经 R_LED_OUT 4.7 kΩ 与焊桥 JP_LED（默认闭合）接 `DOCK_5V`：G6-A2「指示灯真值」用；量产可断开 JP_LED 省 ≈0.6 mA（`ASSUMPTION: AS-31-dock-9`）。
- J2 列 1（A1、B1）= `DOCK_5V` 两针并联；列 2（A2、B2）= `DOCK_GND` 两针并联（ICD 3.2 节）。列 2 用工作高度多 0.5 mm 的针型实现「地先接触」（`ASSUMPTION: AS-31-dock-8`，ICD 3.3 节两条路线取前者）。
- 测试点：TP_VBUS、TP_VSYS、TP_VBAT、TP_BOOST、TP_LIM、TP_DOCK5V、TP_GND ×2、TP_EN、TP_FAULT、TP_ST；位置与丝印由布局阶段定，名称已在 `netlist.yaml`。

## 3. 四项显式论证

### (a) 路径不经软件判断（硬约束 1、EL-D-01、任务书 R04）

逐级列出决定 `DOCK_5V` 是否有输出的全部条件，并说明每个条件的来源：

| 级 | 输出条件 | 条件来源 | 是否含主机/软件 |
| --- | --- | --- | --- |
| U_CHG OUT | VIN 有效，或 VBAT > 内部 FET 导通条件 | 器件内部比较器 | 否 |
| U_UV | `VSYS` > 3.0 V | 电压检测器 | 否 |
| SW_DOCK（若装） | Mosaico 机械到位 | 微动开关 | 否（机械） |
| U_BOOST | EN > 1.2 V 且 VIN > 1.8 V（启动） | 器件内部 | 否 |
| U_LIM | EN（= `BOOST_5V` 经 100 kΩ）> 1.1 V，VIN > UVLO 2.45 V，无过流/过热/反向 | 器件内部 | 否 |
| U_RB | VOUT − VIN < 35 mV（即正向） | 器件内部比较器 | 否 |

结论：从 `VBUS_IN`/`VBAT` 到 `DOCK_5V` 之间的六个使能条件全部由底座自身电压或机械状态决定。**J2 上除 `DOCK_5V`/`DOCK_GND` 外的 14 针（10 × `KEY_*`、`DOCK_SDA/SCL`、其余 GND/5V 并联针）没有任何一根连到上表任何一个使能节点**（可由 `netlist.yaml` 的 `BOOST_EN`、`LIM_EN` 网络 pins 列表机械核对：其中不出现 J2、U_FG）。主机 `subboard.c:122–141` 的「先开模块 3.3 V → 初始化 I²C → 扫描」顺序因此不构成任何依赖：主机电池耗尽、GPIO 全部无效时，底座仍以同样条件输出。

### (b) 主机原生 USB 同时供电时底座不被反向充电（硬约束 8、EL-D-08、AS-11）

反向路径必须经过 J2 列 1 → U_RB → U_LIM → `BOOST_5V` → U_BOOST → `VSYS` → U_CHG → `VBAT`/`VBUS_IN`。逐级阻断能力（全部为数据手册数值）：

| 级 | 底座有电（`BOOST_5V` ≈ 5.1 V） | 底座无电（`BOOST_5V` = 0） |
| --- | --- | --- |
| U_RB | VOUT − VIN > 35 mV typ 即关断（比较器，µs 级）；关断后漏电 ≤ 5.1 µA | 同左；VIN = 0 时反向耐压至 VOUT − VIN ≤ 5.5 V，漏电 ≤ 5.1 µA |
| U_LIM | VOUT − VIN > 135 mV 持续 4 ms 关断；恢复自动 | `IREV` ≤ 1 µA（VOUT 6.5 V、VIN 0 V） |
| U_BOOST | VOUT 高于设定即停止开关；同步 PMOS 体二极管方向为 SW→VOUT，阻断 VOUT→SW；OVP 5.7 V | 关断态「True disconnection」，`IVOUT_LKG` ≤ 3 µA |
| U_CHG | OUT→BAT 为受控 FET；OUT→IN 无路径（线性调节 FET 单向） | 同左 |

因此在八态表的 N = 1 各态中，从主机流入底座的稳态电流上限由 U_RB 漏电（≤ 5.1 µA）决定；`DESIGN_NOTES.md` 第 5 节据此向 Chrome **建议** TH-06 ≤ 10 µA（含仪表裕量），正式值待 Chrome 定义。瞬态：U_LIM 有最长 7 ms 的窗口，但 U_RB 在其前面以 µs 级先关断，窗口内反向电流只能给 `LIM_5V` 节点的 0.1 µF 充电。**AS-11 若被证伪（V1.2 主机会经 pin17 向外送电）**，本设计依然不被灌入，只是 `DOCK_5V` 节点会被主机抬到其电压，U_RB/U_LIM 进入关断——G6-B2 必须同时记录 `DOCK_5V` 节点电压与流入电流。

### (c) 底座充电时对外输出行为（态 D = 1）

- U_CHG 有效输入时 `VSYS` 被调节到 4.4 V typ（与电池电压无关），U_BOOST 由 4.4 V 升到 5.10 V，`DOCK_5V` 与不充电时完全相同。
- 电流分配（DPPM）：输入电流限 ≈1.46 A 内，**系统负载优先**，剩余给电池充电（≤ 0.5 A）；系统需求超过输入限时充电电流先被削到 0，再进入电池补充模式（电池向系统放电）。在 AS-09 假设下：持续 0.6 A @ 5 V → 系统从 `VSYS` 取 ≈0.8 A → 剩余 ≈0.66 A → 电池仍以 0.5 A 满速充；峰值 1 A @ 5 V → 系统取 ≈1.32 A → 电池充电降至 ≈0.14 A，仍为净充电（数值推导见 `POWER_BUDGET.md` 第 4 节）。
- 无电池（G6-A2、态 (1,0,0)）：OUT 仍 4.4 V，输出正常；峰值 1 A 时 `VSYS` 可用功率 ≈4.4 V × 1.46 A ≈ 6.4 W，经升压后 ≈1.1 A @ 5.1 V（η 88 %，`ASSUMPTION: AS-31-dock-3`），刚好覆盖；若 AS-09 峰值被上修则无电池态不保证峰值。
- 拔出底座 USB（态 D 1 → 0）：`VSYS` 从 4.4 V 切到 VBAT（内部 FET，`VDO(BAT-OUT)` 100 mV max），U_BOOST 输入连续、输出不中断（derived；G6-B6/B8 记录主机是否复位）。

### (d) 电池保护由硬件完成

| 故障 | 第一道 | 第二道 | 软件参与 |
| --- | --- | --- | --- |
| 过充 | U_CHG 4.20 V 恒压 + 终止（50 mA） + 安全定时器 | U_PROT 过充阈值（待核，≈4.25–4.30 V）切断 B− | 无 |
| 过放 | U_UV 3.0 V 关闭升压（`ASSUMPTION: AS-31-dock-10`） | U_PROT 过放阈值（待核，≈2.4 V） | 无 |
| 过流/短路（放电） | U_LIM 恒流 1.3 A（限制 `DOCK_5V` 短路时的电池放电） | U_PROT 过流/短路切断 B−；U_BOOST 谷值限流 3.7 A | 无 |
| 过流/短路（`VSYS` 节点） | U_CHG `VO(SC1)` 0.9 V / `VO(SC2)` 250 mV 短路检测 | U_PROT | 无 |
| 温度 | U_CHG TS：0 °C / 50 °C 停充（10 kΩ NTC） | U_LIM/U_BOOST/U_CHG 各自过热关断 | 无 |
| 输入过压 | U_CHG OVP 10.5 V 停止工作（IN 耐 26 V） | D1 TVS、F1 | 无 |

若电池包自带 PCM（AS-12 待确认），则形成三道；U_PROT 与 PCM 的双重 MOS 串联电阻（约 2 × 50 mΩ 量级，待核）在 1.6 A 峰值放电时多损耗 ≈0.1 W，可接受；确认后可 DNP 其一。

## 4. 状态表（底座 USB D × 底座电池 B × 主机原生 USB N）

沿用 `docs/INTERFACE_CONTROL.md` 第 5 节与 `hardware/G6-TEST-PLAN.md` B 段编号。「预期」为本拓扑的设计行为（derived），**不是通过判据**；阈值由 Chrome 定义。

| 态 | D | B | N | `VSYS` | `DOCK_5V` | 底座对主机 | 主机对底座 | 重点验证 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | 0 | 0 | 0 | 0 | 0 | 无 | 主机若靠内置 65 mAh 电池运行：其内部上拉经 `KEY_*` 看到开路开关；`DOCK_SDA/SCL` 无器件（R_LINK DNP，U_FG DNP） | EL-D-10/11：测 `KEY_*`、`DOCK_SDA/SCL` 针对 `DOCK_GND` 电压，应等于主机上拉、无电流路径 |
| B2 | 0 | 0 | 1 | 0 | 被主机抬起？取决于 AS-11 | 无 | 反向：U_RB 阻断，≤ 5.1 µA + U_LIM ≤ 1 µA | **TH-06**；同时记录 `DOCK_5V` 节点电压（若 > 0 说明 V1.2 主机会向 pin17 送电，AS-11 证伪） |
| B3 | 0 | 1 | 0 | = VBAT − VDO | 5.10 V | 供电 + 给主机充电；U_UV 在 VBAT < 3.0 V 关断 | 无 | TH-01/TH-05；插接瞬态是否复位（AS-19）；AS-29 主机关机时是否受充 |
| B4 | 0 | 1 | 1 | = VBAT − VDO | 5.10 V | 供电；主机内部如何在 pin17 与原生 VBUS 间分配 unknown（AS-11） | 阻断 | 两路电流方向与大小；底座电池不应被充（`VBAT` 电流方向） |
| B5 | 1 | 0 | 0 | 4.4 V | 5.10 V | 供电，最大 ≈1.1 A @ 5.1 V（输入限 1.46 A、η 88 %） | 无 | TH-01；**分步上电第一态**（G6-A2） |
| B6 | 1 | 0 | 1 | 4.4 V | 5.10 V | 供电 | 阻断 | 拔任一 USB 的瞬态；主机是否复位 |
| B7 | 1 | 1 | 0 | 4.4 V | 5.10 V | 供电，系统优先、剩余充电（DPPM） | 无 | TH-04 净充电、TH-07 温升（U_CHG ≈1.2 W 是最热点候选） |
| B8 | 1 | 1 | 1 | 4.4 V | 5.10 V | 供电 | 阻断 | 全部切换与故障恢复 |

补充态（不在八态内）：

- 底座短路（G6-A5）：U_LIM 恒流 1.3 A，`DOCK_5V` 跌至 IOS × R_short；LED_FLT 亮；移除短路自动恢复。功耗 ≈5.1 V × 1.3 A ≈ 6.6 W 集中在 U_LIM，2 s 内靠热惯性，更长会进入 155 °C 热循环——G6-A5 的 ≤ 2 s 上限与此一致。
- 电池耗尽且无 USB：U_UV 关断升压（`DOCK_5V` = 0），U_PROT 尚未动作；接入 USB 后 `VSYS` = 4.4 V 立即恢复输出，同时预充电池。
- 错位插入（ICD 3.3 节二级表）：5V 针落到 GND 焊盘 → 等同短路态，由 U_LIM 吸收；GND 针落到 5V 焊盘 → 无源，无路径。**这不放行带电错插**，一级机械防呆仍不可省。

## 5. 与 ICD 第 4 节约束的对应

| ICD 约束 | 本拓扑实现 | 核对方式 |
| --- | --- | --- |
| EL-D-01 纯硬件 | 第 3 节 (a) 六级使能全部本地 | `netlist.yaml` 使能网络无 J2 引脚 |
| EL-D-03 不向主机送 3.3 V | 底座无 3.3 V 网络；J2 无 3V3 针 | 网表无 `*3V3*` 网络 |
| EL-D-05 按键无源 | `KEY_*` 只连 SW_* 与 J2；无上拉、无电源 | 网表 `KEY_*` pins 仅 [J2, SW] |
| EL-D-06 地址避让 | U_FG 候选地址 0x36/0x62/0x0B（待核），默认 DNP | `BOM.csv` |
| EL-D-08 防反灌 | 第 3 节 (b) 两级 | G6-B2/B4/B6/B8 |
| EL-D-10 幽灵供电 | U_FG DNP；R_LINK 在模块板 DNP；装配前 Ioff 审核 | G6-B1 |
| EL-D-11 不向主机注入 | 除 `DOCK_5V` 外，J2 各针只连开关/DNP 器件 | G6-B 态 (1,0,0) 测 `KEY_*` 针为 0 V |
| EL-D-12 预算按 AS-09 | `POWER_BUDGET.md` | G6-A4、G6-B9 |

## 6. 备选拓扑（未采用，供 Chrome 取舍）

| 备选 | 结构 | 不采用理由 |
| --- | --- | --- |
| 分立电源路径 | TP4056（线性 1 A，LCSC 常备）+ 肖特基（USB→VSYS）+ P-MOS（VBAT→VSYS，栅接 VBUS）负载共享 | 可行且料全常备；但充电终止在系统负载下仍受 VSYS 节点扰动，且无输入电流限（弱适配器直接压垮），无 OVP；作为 U_CHG 缺料时的降级方案保留在 `BOM.csv` 备选 |
| 无电源路径 | 充电 IC 直接挂 VBAT，升压从 VBAT 取电 | 边用边充时充电 IC 看到的是电池 + 负载，终止判据失效，可能永不终止（长期浮充） |
| 电源银行 SoC | IP5306 类（充电 + 升压 + 指示一体） | 轻载自动关机（无负载数十秒后关断输出）与 EL-D-01「不接主机也须有输出」冲突，且关机后需按键唤醒；不采用 |
| 单级防反灌 | 只用 U_LIM 的反向保护 | 4 ms 窗口 + 135 mV 阈值；AS-11 unknown 时不愿只靠一级；R_BYP 焊位保留供复核后简化 |
| 肖特基防反灌 | SS34 串在输出 | 0.3–0.5 V 压降随电流变化，`DOCK_5V` 负载调整率差，且 pin17 窗口 unknown；不采用 |
| I²C 可配置充电 IC | BQ2560x 等开关型 | 需 MCU/I²C 配置，违反「无 MCU」；默认寄存器虽可工作但引入 I²C 器件与地址管理 |

## 7. 版本历史

| 版本 | 日期 | 变更 | 作者 |
| --- | --- | --- | --- |
| A0-proposal | 2026-09-21 | 首稿：五级拓扑、四项论证、八态表、ICD 对应、备选 | Claude 主控（claude-fable-5-1） |
