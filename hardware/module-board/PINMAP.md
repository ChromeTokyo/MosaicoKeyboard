提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造

# 模块板引脚分配（PINMAP）

修订 b，2026-09-21（修订 a 为 2026-09-20 的 WIP 半成品）。适用对象：方案 D＋G 的**模块板**（左槽转接件，纯无源：H2 配对公头 ＋ AT24C02 ＋ 底部触点焊盘）。输入依据：`hardware/ICD-0.2-DRAFT.md`（第 1、2、3、7、9 节；**弹簧针逐针分配以其第 3.2 节为准，本文不得与之不同**）、`review/chrome/D1-module-interface/LEFT_SLOT.md`（H2 针号→GPIO 合同，BSP commit `392860b1`）、`hardware/ASSUMPTIONS.md`（AS-01～AS-30）。按 ICD 第 0.2 节，本文件是 **KEY_* → H2 针号 → GPIO 的唯一权威分配表**；底座主板、固件、EEPROM 镜像只使用 KEY_* 名，不得自行重排。

状态说明：本文全部为设计提案。凡标 `ASSUMPTION:` 的数值或方向均未经实物核对，每条附到货后验证方法；未标的引脚定义来自 D1 合同（源码交叉核对，仍非实物验证）。本文新引入的假设临时编号 `AS-31-mb-n`，汇总阶段由主控并入 `hardware/ASSUMPTIONS.md` 统一编号。

## 0. 修订 b 相对修订 a 的变更（供 firmware／eeprom／dock-board 分支同步）

| # | 变更 | 原因 | 受影响文件 |
| --- | --- | --- | --- |
| 1 | J2 逐针改为 ICD 第 3.2 节分配：列 1 `DOCK_5V`×2、列 2 `DOCK_GND`×2、列 3–7 十键**成对同列**（UP/DOWN、LEFT/RIGHT、L/R、A/B、X/Y）、列 8 `DOCK_SDA/SCL`。修订 a 的中心对称布局作废 | 与 ICD 一致；ICD 第 3.3 节的二级防呆分析基于此布局 | `firmware/dock_handle/include/dock_handle_pinmap.h` 注释中的 J2 焊盘位（A3=KEY_UP…B6=KEY_Y）需改为本文第 4 节；**宏值（GPIO）不变** |
| 2 | **KEY_* → GPIO 不变**（第 2 节） | 固件与 EEPROM keymap 已按修订 a 的 GPIO 表实现 | 无 |
| 3 | 坐标改用 ICD 第 1 节整机坐标（列沿 X、行沿 Z、弹簧针轴向 +Y），不再用板级局部 X/Y | 消除镜像二义 | dock-board 弹簧针布局须用同一坐标 |
| 4 | 网名改为 ICD 第 9 节：`SLOT_SPARE_GPIO4`（原 SPARE_GPIO4）、`SLOT_USJ_DN/DP`（原 *_NC）、`SLOT_5V_OUT_NC`（原 HOST_5V_OUT_NC）；测试点改功能名 `TP_5V/TP_GND/TP_3V3/TP_SDA/TP_SCL/TP_A0/TP_SPARE/TP_WP`（原 TP1–TP8） | 统一命名 | `dock_handle_pinmap.h` 注释（TP7→TP_SPARE） |
| 5 | pin 18 焊盘**不连铜、无测试点**；修订 a 的 TP8 删除 | ICD EL-D-02 | 修订 a 验证项 P8 改为直接探 J1 焊针 |
| 6 | `DOCK_SDA/SCL` 与 `SLOT_SDA/SCL` 分为两个网，经 DNP 0 Ω `R_LINK_SDA/SCL` 相连 | ICD 第 2 节 pin 14/16、EL-D-06/EL-D-10 | dock-board：默认看不到主机 I²C1 |
| 7 | 新增按键串阻位 `R_S_KEY_*`（ICD 第 2 节允许预留），提案值 1 kΩ；H2 侧网名 `SLOT_KEY_*`，弹簧针侧保持 `KEY_*` | 见 `DESIGN_NOTES.md` 第 6 节 | 无（对固件透明） |
| 8 | 新增 90° 转向接头 **J3**（槽板↔触点板半孔 T 形焊接），见第 5 节 | 几何推导：单块平面板无法同时给出 +X 配合与 −Y 触点面 | mech-module 须按第 5 节参数建模并确认 |
| 9 | WP 默认经 JP1 桥 1–2 接 GND（可写），与 eeprom 分支 `PROGRAMMING.md` ASSUMPTION P-01 一致；ICD 第 7.1 节「proposed 默认写保护」需 Chrome 择一 | eeprom 分支为 WP 策略归属方；D-017 迭代需主机在系统内重烧 | `hardware/ICD-0.2-DRAFT.md` 第 7.1 节 |

## 1. 分配原则

1. GPIO14（H2 pin 10）为标准模块 EEPROM A0 地址线，**专用，不接按键、不引到弹簧针**（`subboard.h:19–39`，`subboard.c:101–120` 发现阶段驱动为 0；ICD 第 2 节）。
2. 11 根可用 GPIO {55, 53, 19, 48, 18, 13, 17, 12, 16, 15, 4}（D1 derived）中取 10 根作 KEY_*，余 1 根（GPIO4）作 `SLOT_SPARE_GPIO4`，只到测试点 `TP_SPARE`，**不引到弹簧针**（接口 2×8 无余针，ICD 第 2 节 pin 12）。
3. 按键为无源开关接 `DOCK_GND`，拉高只由主机内部上拉提供；全部 3.3 V 逻辑域；模块板上不出现任何 5 V 上拉或电平转换（硬约束 5，ICD EL-D-05）。
4. 任何 KEY_* 不得落在 GPIO14 或 pin 13/15（ICD 第 2 节约束）。
5. 与板载 I²S {54, 37, 49, 52, 40} 无交集（confirmed，`esp_mosaico.h:108–114`）；这只证明与板载 I²S 无冲突。
6. `ASSUMPTION: AS-15` 11 根候选均可配置为带内部上拉的输入且无 strapping 副作用。当前唯一依据是 `review/chrome/H01/evidence/idf-components__soc__esp32s31__register__soc__io_mux_reg.h` 中注释为 Strapping 的引脚（GPIO36、37、38、39、40、60、61）与候选无交集；这是 IDF 头文件注释，**不是数据手册**。验证：到货后查 ESP32-S31 数据手册 strapping 表并记录 URL；G6-D5 逐键按住开机。
7. 备用针选 H2 pin 12／GPIO4：官方 V1.0 引脚表中它是唯一标 DAC 的针（`user_guide_v10.rst` H2 表 pin 12 "GPIO4 DAC"），保留它不占用模拟输出能力；它位于偶数排末端、紧邻 pin 10 A0 线，留空后 A0 走线一侧无按键线相邻。11 根中任一根在电气上都能做按键，此选择是平局裁决，非电气必要。
8. KEY_* 的 GPIO 分配在修订 a 与 b 之间**保持不变**，避免 firmware／eeprom 分支重做。

## 2. KEY_* → H2 针号 → GPIO → 弹簧针位（最终分配）

| KEY_* | H2 针 | GPIO | 官方 V1.0 表功能标注 | H2 侧网名 | 串阻 | 弹簧针侧网名 | J2 焊盘 | J3 位 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| KEY_UP | 1 | GPIO55 | ADC | `SLOT_KEY_UP` | R_S_KEY_UP | `KEY_UP` | A3 | 5 |
| KEY_DOWN | 3 | GPIO19 | ADC | `SLOT_KEY_DOWN` | R_S_KEY_DOWN | `KEY_DOWN` | B3 | 6 |
| KEY_LEFT | 5 | GPIO18 | TOUCH | `SLOT_KEY_LEFT` | R_S_KEY_LEFT | `KEY_LEFT` | A4 | 7 |
| KEY_RIGHT | 7 | GPIO17 | TOUCH | `SLOT_KEY_RIGHT` | R_S_KEY_RIGHT | `KEY_RIGHT` | B4 | 8 |
| KEY_L | 9 | GPIO16 | TOUCH | `SLOT_KEY_L` | R_S_KEY_L | `KEY_L` | A5 | 9 |
| KEY_R | 11 | GPIO15 | TOUCH | `SLOT_KEY_R` | R_S_KEY_R | `KEY_R` | B5 | 10 |
| KEY_A | 2 | GPIO53 | ADC | `SLOT_KEY_A` | R_S_KEY_A | `KEY_A` | A6 | 11 |
| KEY_B | 4 | GPIO48 | ADC | `SLOT_KEY_B` | R_S_KEY_B | `KEY_B` | B6 | 12 |
| KEY_X | 6 | GPIO13 | TOUCH | `SLOT_KEY_X` | R_S_KEY_X | `KEY_X` | A7 | 13 |
| KEY_Y | 8 | GPIO12 | TOUCH | `SLOT_KEY_Y` | R_S_KEY_Y | `KEY_Y` | B7 | 14 |
| （备用，不接键） | 12 | GPIO4 | DAC | `SLOT_SPARE_GPIO4` | — | — | 不引出，仅 `TP_SPARE` | — |

分配规律：奇数排 pin 1/3/5/7/9/11 依次为 UP、DOWN、LEFT、RIGHT、L、R；偶数排 pin 2/4/6/8 为 A、B、X、Y。弹簧针侧按 ICD 第 3.2 节成对同列：列 3 UP/DOWN、列 4 LEFT/RIGHT、列 5 L/R、列 6 A/B、列 7 X/Y（行 A 在前）。TOUCH／ADC 标注只说明该针的模拟复用能力，作数字输入不受影响；固件须显式配置为输入并启用内部上拉（BSP 未统一配置这 11 根的方向，`BSP_AND_EEPROM.md` §1）。

`R_S_KEY_*` 为 0603 串阻位，提案值 **1 kΩ**（`DESIGN_NOTES.md` 第 6 节；ICD 第 2 节把数值交给模块板任务提案、Hiro 复核）。装 0 Ω 时 `SLOT_KEY_*` 与 `KEY_*` 同铜，对固件无差别。

## 3. J1（2×10P 公头，配合主机左槽 H2）逐针网络

J1 针号**定义为与主机左槽 H2 同号**（配合后 J1.n 与 H2.n 导通）。双排标准编号：奇数排 1, 3, …, 19 一排，偶数排 2, 4, …, 20 一排，1 与 2 相对。`ASSUMPTION: AS-17` 奇数排在 +Z 还是 −Z、pin 1 在 +Y 端还是 −Y 端，到货前未知；这决定 J1 封装 1 脚方向与槽板正反面，见第 5.3 节与第 7 节 P1。

| J1/H2 针 | 主机网络 / GPIO | 模块板网络 | 处理 |
| --- | --- | --- | --- |
| 1 | GPIO55 | `SLOT_KEY_UP` | → R_S_KEY_UP → `KEY_UP` → J3.5 → J2.A3 |
| 2 | GPIO53 | `SLOT_KEY_A` | → R_S_KEY_A → `KEY_A` → J3.11 → J2.A6 |
| 3 | GPIO19 | `SLOT_KEY_DOWN` | → R_S_KEY_DOWN → `KEY_DOWN` → J3.6 → J2.B3 |
| 4 | GPIO48 | `SLOT_KEY_B` | → R_S_KEY_B → `KEY_B` → J3.12 → J2.B6 |
| 5 | GPIO18 | `SLOT_KEY_LEFT` | → R_S_KEY_LEFT → `KEY_LEFT` → J3.7 → J2.A4 |
| 6 | GPIO13 | `SLOT_KEY_X` | → R_S_KEY_X → `KEY_X` → J3.13 → J2.A7 |
| 7 | GPIO17 | `SLOT_KEY_RIGHT` | → R_S_KEY_RIGHT → `KEY_RIGHT` → J3.8 → J2.B4 |
| 8 | GPIO12 | `SLOT_KEY_Y` | → R_S_KEY_Y → `KEY_Y` → J3.14 → J2.B7 |
| 9 | GPIO16 | `SLOT_KEY_L` | → R_S_KEY_L → `KEY_L` → J3.9 → J2.A5 |
| 10 | GPIO14（EEPROM A0） | `SLOT_EEPROM_A0` | 只接 U1.A0 与 `TP_A0`；**不接按键、不到 J3/J2** |
| 11 | GPIO15 | `SLOT_KEY_R` | → R_S_KEY_R → `KEY_R` → J3.10 → J2.B5 |
| 12 | GPIO4 | `SLOT_SPARE_GPIO4` | 只到 `TP_SPARE`；不到 J3/J2 |
| 13 | GPIO33 / USJ_DN | `SLOT_USJ_DN` | **NC**：焊盘存在、不连铜、无测试点（不给 USB 差分线加桩；AS-30） |
| 14 | GPIO1 / SCL（V1.2 模块 I²C1） | `SLOT_SCL` | U1.SCL、`R_PU_SCL`（DNP）、`TP_SCL`；经 `R_LINK_SCL`（DNP 0 Ω）→ `DOCK_SCL` → J3.16 → J2.B8 |
| 15 | GPIO34 / USJ_DP | `SLOT_USJ_DP` | **NC**，同 13 |
| 16 | GPIO0 / SDA（V1.2 模块 I²C1） | `SLOT_SDA` | U1.SDA、`R_PU_SDA`（DNP）、`TP_SDA`；经 `R_LINK_SDA`（DNP 0 Ω）→ `DOCK_SDA` → J3.15 → J2.A8 |
| 17 | 5V_IN（底座向主机供电并充电） | `DOCK_5V`（H2 焊盘标签 `SLOT_5V_IN`） | 纯铜 → J3.1/J3.2 → J2.A1/J2.B1；`TP_5V`；模块板上**无任何串联器件**（硬约束 1） |
| 18 | 5V_OUT（主机向外输出） | `SLOT_5V_OUT_NC` | **NC，绝不连接任何网络**：焊盘不连铜，丝印「NC」（硬约束 2，ICD EL-D-02） |
| 19 | VCC_3V3（主机向模块供电） | `SLOT_3V3` | U1.VCC、C1、`R_PU_SDA/SCL` 上端、JP1.3、`TP_3V3`；**不到 J3/J2**（硬约束 3，ICD EL-D-03） |
| 20 | GND | `DOCK_GND`（H2 焊盘标签 `SLOT_GND`） | → J3.3/J3.4 → J2.A2/J2.B2；U1 GND/A1/A2、C1、JP1.1、`TP_GND`、ESD 器件地 |

网名约定（ICD 第 9 节）：模块板上 `SLOT_5V_IN` 与 `DOCK_5V`、`SLOT_GND` 与 `DOCK_GND` 是同一铜网络的两个名字；网表以 `DOCK_5V`／`DOCK_GND` 为网名，`SLOT_*` 为 H2 焊盘标签。

## 4. J2（底部弹簧针接触焊盘，2×8＝16）逐针定义

### 4.1 坐标框架（ICD 第 1 节整机坐标，不用板级局部坐标）

基准姿态：屏朝用户、USB-C 朝下、左槽在左。+X 用户视角向右；+Y 向上（弹簧针轴向）；+Z 从屏面指向用户。

- `ASSUMPTION: AS-07` 2.54 mm 间距、2 行 × 8 列。验证：AS-01、AS-04 关闭后计算模块板可用底宽；首版打板后用无源检具核对位。
- 列 c = 1…8 沿 X：**列 1 在 −X 极端（靠左握把外侧），列 8 靠 Mosaico 中央**。行 A 靠 +Z（屏侧），行 B 靠 −Z（背侧）。
- 焊盘中心（触点板底面，法向 −Y）：`X(c) = DOCK_PIN_FIELD_X0 + (c − 1) × 2.54`；`Z(A) = DOCK_PIN_FIELD_Z0`，`Z(B) = DOCK_PIN_FIELD_Z0 − 2.54`；触点面高度 `Y = MODULE_PAD_FACE_Y`（须 < −MOSAICO_H/2，ICD ME-D-07）。三个参数由 mech-dock／mech-module 给值，本文不填数。
- 底座主板顶层弹簧针（针尖朝 +Y）按**相同 (X, Z)** 布置。两板各自的 EDA 顶视图都是自 +Y 向 −Y 看，同一 (X, Z) 落在屏幕同一位置，**两板之间不做镜像**。
- **EDA 顶视图方向提示**：自 +Y 向 −Y 看且 +X 向右时，屏幕向上是 **−Z**。因此在触点板与底座主板的 EDA 顶视图中，**列 1 在左、行 B（−Z）在上、行 A（+Z）在下**。任何一方若改用底视图给坐标，必须注明并镜像。项目历史上已出现镜像错误（D-009／D-009-R），此处不留二义。

### 4.2 逐针表（等于 ICD 第 3.2 节）

| 列 | 行 A（+Z，屏侧） | 行 B（−Z，背侧） | X 坐标 | 模块板侧来源 | 说明 |
| --- | --- | --- | --- | --- | --- |
| 1（−X 最外） | `DOCK_5V` | `DOCK_5V` | X0 | J3.1/J3.2 ← J1.17 | 两针并联；纯铜 |
| 2 | `DOCK_GND` | `DOCK_GND` | X0 + 2.54 | J3.3/J3.4 ← J1.20 | 两针并联；建议底座在此列用先接触（行程更长）针型（ICD 第 3.3 节，由底座任务择一） |
| 3 | `KEY_UP` | `KEY_DOWN` | X0 + 5.08 | J3.5 / J3.6 | D-pad |
| 4 | `KEY_LEFT` | `KEY_RIGHT` | X0 + 7.62 | J3.7 / J3.8 | D-pad |
| 5 | `KEY_L` | `KEY_R` | X0 + 10.16 | J3.9 / J3.10 | 肩键 |
| 6 | `KEY_A` | `KEY_B` | X0 + 12.70 | J3.11 / J3.12 | ABXY |
| 7 | `KEY_X` | `KEY_Y` | X0 + 15.24 | J3.13 / J3.14 | ABXY |
| 8（靠中央） | `DOCK_SDA` | `DOCK_SCL` | X0 + 17.78 | J3.15 / J3.16 ← R_LINK（DNP） | 预留可选电量计；默认与主机 I²C1 断开 |

焊盘名即 `J2.A1 … J2.B8`；`netlist.yaml` 中 J2 的 16 个引脚用这些名字。

### 4.3 错位分析（电气层面）

ICD 第 3.3 节已给出 X 方向 ±1 列、Z 方向错一行、绕 Y 轴 180° 的四种情形结论（前三种无损，第四种由一级机械防呆保证触不到针）。本板补充两点：

1. `R_S_KEY_*` 装 1 kΩ 时，任何把 5 V 误压到 `KEY_*` 焊盘的情形（X 错 2 列、一级防呆失效的 180° 错放）对主机 GPIO 的注入电流被限到约 1.5 mA 量级（`DESIGN_NOTES.md` 第 6 节）。**这是降低损坏概率的措施，不是免除机械防呆的理由**；`DOCK_SDA/SCL`（列 8）没有串阻，180° 错放时 5 V 落到列 8 焊盘，但默认 `R_LINK` DNP，该焊盘在模块板上不连到主机。
2. 装 `R_LINK`（可选电量计方案）后，180° 错放变为**有损**（5 V 经 0 Ω 到 GPIO0/1）；因此装 `R_LINK` 的前提是 AS-08 一级防呆已关闭。

### 4.4 焊盘与表面处理

- `ASSUMPTION: AS-31-mb-3` 焊盘为圆形 Ø1.8 mm，中心距 2.54 mm，相邻净间距 0.74 mm。验证：底座任务选定弹簧针后按「焊盘直径 ≥ 针头直径 ＋ 2 × (`DOCK_X_TOL`, `DOCK_Z_TOL` 中较大者)」复算；针头直径与定位公差目前均为 unknown。
- 表面处理：嘉立创标准工艺为 HASL／无铅 HASL／ENIG／OSP，电镀硬金只作为板边「金手指」选项提供（2026-09-21 检索 jlcpcb.com 表面处理说明；面内硬金焊盘能否做「待嘉立创工艺确认」）。**默认 ENIG**，接受首版磨损寿命有限；G6-G 每 10 次插拔拍照记录焊盘磨损，作为是否换硬金或改厚金工艺的依据。
- 焊盘位于触点板**底层**（−Y 面）；触点板顶层（+Y 面）对应位置只放 J3 的 SMD 焊盘与过孔，不放器件（`DESIGN_NOTES.md` 第 3 节）。

## 5. 板形与 90° 转向接头 J3

### 5.1 为什么需要转向（derived，依赖 AS-01、AS-02）

- 左槽 2×10 母座在 −X 面，配合方向 +X。母座 10 针方向的跨距为 9 × 2.54 = 22.86 mm；−X 面尺寸为 45.19（Y）× 11.48（Z）（AS-01），因此 **10 针方向只能沿 Y**，两排沿 Z（`SLOT_ROW_AXIS = Y`，ICD 第 1 节参数由此取值；到货按 AS-04 核实）。
- 触点面法向 −Y（弹簧针轴向 +Y，ICD 第 3.1 节）。
- 一块平面刚性板要么与 −X 面平行（YZ 面，配直插公头），要么与屏面平行（XY 面，配右角公头）；两者的板面法向都是 ±X 或 ±Z，**都不存在 −Y 法向的面**。板在 XZ 面（水平）时公头 10 针方向只能沿 Z，与母座矛盾。因此纯单板不可实现，必须有一次 90° 转向。

### 5.2 提案板形（ASSUMPTION: AS-31-mb-1）

两块刚性 FR-4 板，一次焊接成 T 形组件；网表仍是一份（`netlist.yaml`），J3 是两板之间的焊接接头。

| 板 | 板面 | 内容 | 外形参数（mech-module 给值） |
| --- | --- | --- | --- |
| 槽板（fin） | XY 面（与屏面平行），位于 Mosaico −X 侧，向 −X 与 −Y 延伸 | J1（右角公头，配合针指向 +X，两排沿 Z 叠置）、U1、C1、JP1、R_PU、R_LINK、R_S_KEY_*、ESD 位、全部测试点；底边（−Y 边）16 位半孔 = J3 | `FIN_L`（X 向）、`FIN_H`（Y 向）、`FIN_Z`（板面 Z 坐标） |
| 触点板（pad board） | XZ 面（水平），位于槽板底边之下 | 底面 J2 2×8 焊盘；顶面 16 个 J3 SMD 焊盘；两面之间过孔 | `PAD_BOARD_L`（X）、`PAD_BOARD_W`（Z）、`MODULE_PAD_FACE_Y` |

- 右角公头的两排配合针相对槽板板面的高度（标准右角排针约 2.54 与 5.08 mm，`ASSUMPTION: AS-31-mb-2`，待所选公头原厂图纸核对）决定 `FIN_Z` 与母座中心 Z 的偏置；槽板在母座中心的 +Z 侧还是 −Z 侧由 AS-17（奇数排位置）决定。
- 备选实现（`DESIGN_NOTES.md` 第 3 节）：① 1.27 mm 右角排针连接两板；② 刚挠结合板；③ 1.0 mm FFC 连接器＋标准 FFC 软排线（容忍 `SLOT_PIN1_Y` 未知带来的高度误差）。任何备选都不改变网表中除 J3 之外的内容。

### 5.3 J3 逐位（16 位半孔，沿 X 排列，位 1 在 −X 端）

| J3 位 | 网络 | J3 位 | 网络 |
| --- | --- | --- | --- |
| 1 | `DOCK_5V` | 9 | `KEY_L` |
| 2 | `DOCK_5V` | 10 | `KEY_R` |
| 3 | `DOCK_GND` | 11 | `KEY_A` |
| 4 | `DOCK_GND` | 12 | `KEY_B` |
| 5 | `KEY_UP` | 13 | `KEY_X` |
| 6 | `KEY_DOWN` | 14 | `KEY_Y` |
| 7 | `KEY_LEFT` | 15 | `DOCK_SDA` |
| 8 | `KEY_RIGHT` | 16 | `DOCK_SCL` |

- 位序与 J2 列序一致（列 1→列 8），触点板上无交叉。
- `ASSUMPTION: AS-31-mb-5` 半孔间距 1.5 mm、钻孔 Ø0.7 mm（嘉立创半孔规则：钻孔与孔边距均 ≥ 0.6 mm，板尺寸 ≥ 10 × 10 mm，2026-09-21 检索 jlcpcb.com 半孔说明）；16 × 1.5 = 22.5 mm，与 8 列 × 2.54 的触点场同量级。单个半孔焊点载流 ≥ 0.5 A 为假设，`DOCK_5V`／`DOCK_GND` 各 2 位并联覆盖 AS-09 峰值 ≤ 1 A。验证：首版样板 0.5 A 与 1.0 A 下测 J3 两端压降与温升（G6-F3 同时观察）。
- 跨越 J3 的网络共 14 个：`DOCK_5V`、`DOCK_GND`、10 个 `KEY_*`、`DOCK_SDA`、`DOCK_SCL`。**`SLOT_3V3`、`SLOT_EEPROM_A0`、`SLOT_SPARE_GPIO4`、`SLOT_SDA/SCL`、`EEPROM_WP` 不跨越 J3**，触点板上不存在任何 3.3 V 网络（硬约束 3 在板形层面成立）。

## 6. 主机侧供电顺序与本板的依赖关系（供固件与底座任务引用）

- 主机 `bsp_subboard_init()` 顺序：开模块 VCC_3V3（GPIO60）→ 初始化 I²C1（内部上拉开）→ GPIO14 输出 0（`subboard.c:122–141`）。因此 U1 在主机固件运行前**无电**，模块板不得依赖 3.3 V 先于主机存在。
- GPIO60 同时是 strapping 引脚（Boot Mode select 3，第 1 节第 6 条来源），VCC_3V3 使能脚在复位期间的状态受启动配置影响；底座任务不得把 pin 19 出现 3.3 V 当作「主机已启动」的判据。
- 底座对 pin 17 的 5 V 输出必须是纯硬件路径，不等待 EEPROM 识别、不等待任何 GPIO 许可（硬约束 1，ICD EL-D-01）。模块板上 pin 17 到 J2 之间只有铜（含 J3 两个半孔焊点），没有任何可以「等待」的器件；等待与否由底座任务保证。

## 7. 到货后验证清单（与本表直接相关）

| # | 验证项 | 方法 | 影响 |
| --- | --- | --- | --- |
| P1 | H2 pin 1 的物理朝向与奇偶排位置（AS-17） | 不插拔模块；Mosaico 关机、不接外设，万用表通断档：pin 20 对已知 GND（USB-C 外壳）通；微距拍左槽及中框丝印（`docs/MEASUREMENT_PROTOCOL.md` 第 0 节 P00e）；与第 3 节对照 | 决定 J1 封装 1 脚方向与槽板正反面（第 5.2 节）；若相反，槽板布局镜像重做（D-017 接受迭代）。**此项在打板前完成**（主循环第 ② 步先于第 ④ 步） |
| P2 | 槽位连接器形态（E-01、AS-05）与 10 针方向（AS-04） | 同上；确认是否为 2.54 mm 右角排母、开口朝 −X、插入深度；量 pin 1 与 pin 19 中心到 −Y 面距离 | J1 选右角或直插公头、针长；第 5.1 节 `SLOT_ROW_AXIS = Y` 推导是否成立 |
| P3 | 11 根候选 GPIO 无一为 strapping（AS-15） | 查 ESP32-S31 数据手册 strapping 表并记录 URL；刷测试固件，逐键按住开机 11 次（G6-D5） | 若某针为 strapping，用 `SLOT_SPARE_GPIO4` 换针并修订第 2 节 |
| P4 | 各 KEY 针配置输入＋内部上拉后空闲为高、对地短接为低 | 模块板单板插槽、不接底座：`keytest` 打印 10 键电平；用绝缘柄镊子在 J2 焊盘对 `DOCK_GND` 逐个短接，键名须与第 4.2 节焊盘位一致 | 确认 KEY→GPIO 表、内部上拉可用性、`R_S_KEY_*` 1 kΩ 下按下电平 |
| P5 | pin 19 `SLOT_3V3` 出现时刻与电压（AS-13） | 万用表或示波器探 `TP_3V3` 对 `TP_GND`，从上电到 BSP 日志 "Subboard I2C initialized" | 确认 U1 供电顺序假设 |
| P6 | pin 14/16 I²C1 空闲电平、上升时间、主机侧外部上拉是否存在（AS-14） | 主机开机、`R_PU_SDA/SCL` 未装：示波器测 `TP_SDA/TP_SCL` 上升时间（G6-E1）；主机关机状态下万用表测 pin 14/16 对 pin 19 阻值 | 决定 `R_PU_*` 是否装配及阻值（AT24C02D 数据手册要求 SDA 外部上拉不超过 10 kΩ） |
| P7 | EEPROM 在 0x50 应答、134 字节读出与三段 CRC | 测试固件 `module_slot_scan`（G6-C1） | 确认 A0 接法与地址 |
| P8 | pin 18 各状态电压 | 万用表探 J1 pin 18 焊针（无测试点、焊盘不连铜）对 `TP_GND`：主机关机／开机／GPIO60 高低各状态 | 只记录，不接底座；用于 `docs/INTERFACE_CONTROL.md` EL-08 D14 旁路问题 |
| P9 | pin 17 输入路径（AS-09、AS-10） | 限流电源经 `TP_5V/TP_GND` 供 5 V，从 100 mA 起逐级升至假设峰值，记录主机是否充电、温升 | pin 17 输入额定 unknown，只做记录，不得据此宣称额定 |
| P10 | J3 接头载流与压降（AS-31-mb-5） | 触点板 `DOCK_5V` 焊盘对 `TP_5V`、`DOCK_GND` 焊盘对 `TP_GND`，0.5 A／1.0 A 假负载下测压降；红外看焊点温升 | 若压降或温升超阈值（待 Chrome 定义），增加半孔数或改备选接头 |
| P11 | 触点面高度与 Mosaico −Y 面关系（ME-D-07、AS-22） | 装配后深度尺量 `MODULE_PAD_FACE_Y` 相对 Mosaico 底面；原生 USB-C 能否插入 | 槽板高度 `FIN_H` 修订 |
