提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造

# ICD-0.2-DRAFT（方案 D＋G 分册）：Mosaico 左槽 ↔ 模块板 ↔ 底座主板 接口控制文档

版本：ICD-0.2-DRAFT，方案 D＋G 分册，主控代拟稿 a。日期：2026-09-20。输入提交：`origin/main` `1af3c36`。分支：`claude/design-d/icd`。

## 0. 归属、适用范围与状态标签

**接口控制文档的正式归属是 Chrome**（`docs/TEAM_PLAN.md`：ICD 由 Chrome 维护、Hiro 专项复核、Claude 记录冻结；现行文件为 `docs/INTERFACE_CONTROL.md`，其版本号同为 ICD-0.2-DRAFT）。Chrome 于 2026-09-20 额度耗尽下线，本稿是主控按 D-012（稀缺 GPT 额度只花在非作者复核与技术决策上）与 D-017（先按现有信息把设计做完、全部标 ASSUMPTION）代拟的**方案 D＋G 分册**。Chrome 回归后择一处理：并入 `docs/INTERFACE_CONTROL.md` 并删除本文件，或以本文件替代其方案 D 部分。两者并存期间，**冲突以 Chrome 文件为准**。

按 D-013 红线，本稿由 Claude 起草，因此本稿中任何接口结论都必须由 Hiro 或 Chrome 作非作者复核后才能进入冻结登记（第 10 节）。

适用范围：ESP-Mosaico BaseBoard **V1.2**、CoreBoard **V1.2**（用户开箱视频所示，到货未确认），完整整机不拆解、不改主板、不焊线，经左模块槽 H2 接方案 D＋G 的模块板与底座主板。`docs/INTERFACE_CONTROL.md` 中的四背部触点、共享 I²C0、Pogo 布局为 V1.0 历史草案，与本稿无关。

状态标签沿用 `docs/INTERFACE_CONTROL.md` 并增加一项：

| 标签 | 含义 |
| --- | --- |
| confirmed | 指定官方文件或固定提交源码明确写出；不代表实物通过 |
| derived | 由 confirmed 事实计算或推断 |
| proposed | 本稿提出的设计要求，等待非作者复核 |
| ASSUMPTION | 无官方依据的工作假设；编号与到货验证步骤见 `hardware/ASSUMPTIONS.md` |
| unknown | 仍需证据，未填数值 |

**本稿没有任何 measured 或 frozen 数值。**

**2026-09-23 Chrome 仅修订第 2/5 节的到货验证措辞，未采纳或冻结本稿接口。** 第一轮遵守 `docs/MEASUREMENT_PROTOCOL.md` 第 0～5 节：只做认版、照片和绝缘外壳外表面的安全测量；仍接内置电池的机器不插拔模块、不把量具/探针伸入槽口、不做通断测试。需要接触、试装或通电的项目须另有同版专项步骤、夹具及独立复核；对应假设继续 `OPEN`。**本稿引用的 V1.2 Q07/Q08 三视图和记录格依赖待审 [PR #55](https://github.com/ChromeTokyo/MosaicoKeyboard/pull/55)；#55 未纳入时不能把本稿当完整第一轮指引。**

### 0.1 方案 D＋G 一句话

```
Mosaico ──[左槽 H2 2×10P 2.54 mm，装配时插一次此后不拔]── 模块板（纯转接：H2 配对公头 + AT24C02 + 底部触点焊盘）
                                                                          │ 沿 −Y 垂直落入
底座主板 ──[弹簧针 2×8 朝 +Y，承担每天插拔]───────────────────────────────╯
        （电池管理 + 10 轻触开关 + 弹簧针 + USB-C；无 MCU、无 I²C 扩展器）
```

按键全部为底座主板上的无源开关接 `DOCK_GND`；经弹簧针进入模块板 `KEY_*` 焊盘，再经 H2 直连主机 GPIO；拉高由主机内部上拉提供。

### 0.2 子系统与文件归属

| 子系统 | 分支（均由 Claude 起草，待 Chrome 采纳） | 本稿对其的要求 |
| --- | --- | --- |
| 模块板 | `claude/design-d/module-board` → `hardware/module-board/` | 实现第 2、3、7 节；**`KEY_*` → GPIO 分配写入 `hardware/module-board/PINMAP.md`**，其他子系统只用 `KEY_*` 名 |
| 底座主板 | `claude/design-d/dock-board` → `hardware/dock-board/` | 实现第 3、4 节；只用 `DOCK_*`、`KEY_*`、`VBUS_IN`/`VBAT`/`VSYS`/`BOOST_5V` 名 |
| EEPROM 身份 | `claude/design-d/eeprom` | 实现第 7 节镜像；不改变第 7.1 节地址与供电规则 |
| 固件（最小测试程序） | `claude/design-d/firmware` | 实现第 8 节接口；提供 `hardware/G6-TEST-PLAN.md` 需要的扫描与十键自检命令 |
| 机械（模块板/底座） | `claude/design-d/mech-module`、`claude/design-d/mech-dock` | 实现第 5 节坐标系与参数名；尺寸集中在 OpenSCAD 顶部 `// ASSUMPTION` 块 |

## 1. 坐标系

**基准姿态**：用户手持整机，Mosaico 屏幕朝用户，Mosaico 原生 USB-C 朝下。

| 轴 | 方向 | 说明 |
| --- | --- | --- |
| +X | 用户视角向右 | 左模块槽位于 −X 面；D-pad 在 −X 侧握把，ABXY 在 +X 侧握把 |
| +Y | 向上 | Mosaico 原生 USB-C 在 −Y 面；弹簧针轴向为 +Y；模块板随 Mosaico 沿 −Y 落入底座 |
| +Z | 从屏面指向用户 | 弹簧针两行沿 Z 排布；行 A 靠 +Z（屏侧），行 B 靠 −Z（背侧） |
| 原点 O | Mosaico 外形包络（`ASSUMPTION: AS-01`，45.19 × 45.19 × 11.48 mm）的几何中心 | 到货后若实测外形不同，原点定义不变、数值改 |

派生位置全部为参数、无数值（`unknown`，由 `hardware/ASSUMPTIONS.md` 登记、到货实测填入）：

| 参数 | 含义 | 状态 |
| --- | --- | --- |
| `MOSAICO_W`、`MOSAICO_H`、`MOSAICO_T` | 外形宽（X）、高（Y）、厚（Z） | ASSUMPTION AS-01 |
| `SLOT_FACE_X` | 左槽所在面的 X 坐标（= −MOSAICO_W/2，若母座与外壳面平齐） | ASSUMPTION AS-03 |
| `SLOT_PIN1_Y`、`SLOT_PIN1_Z` | H2 pin 1 中心在左槽面上的 Y、Z 坐标 | unknown，AS-04、AS-17 |
| `SLOT_ROW_AXIS`、`SLOT_ODD_ROW_SIDE` | 2×10 的 10 针方向沿 Y 或 Z；奇数针行在 +Z 或 −Z | unknown，AS-17 |
| `SLOT_OPEN_DIR` | 母座开口方向（= −X） | ASSUMPTION AS-03、AS-05 |
| `USBC_X`、`USBC_Z` | 原生 USB-C 在 −Y 面上的位置 | unknown，AS-22 |
| `DOCK_PIN_FIELD_X0`、`DOCK_PIN_FIELD_Z0`、`DOCK_PIN_FIELD_Y` | 弹簧针场第 1 列行 A 针尖坐标与配合面高度 | proposed 参数，由机械任务给值 |

方向约定的固定文字，供所有 SVG、OpenSCAD 与照片编号引用：「屏朝用户、USB-C 朝下、左槽在左」。禁止用任何俯视/背视照片的「左右」替代本节坐标。

## 2. 左槽 H2 20 针合同（模块板 ↔ Mosaico）

来源：`review/chrome/D1-module-interface/LEFT_SLOT.md`（Chrome D1，BSP commit `392860b1`，与官方 V1.0 指南 `user_guide_v10.rst:627–685` 交叉一致）。H2 针号是主机左槽连接器针号，不是 GPIO 号，不是照片从左到右序号。**针号 → 物理位置的方向（AS-17）第一轮只拍同版接口标记；若标记不清则仍 unknown。通断/二极管核实须待内置电池可安全隔离、同版配对图与绝缘夹具到位并经 Hiro 复核的 V1.2 专项步骤；关机不等于断电，也不预设 USB-C 外壳为 GND。**

| H2 针 | 主机网络 | ICD 网络名 | 方向 | 模块板处理 | 电气域 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | GPIO55 | `KEY_*`（分配见 PINMAP.md） | 底座→主机 | 直通到弹簧针焊盘 | 3.3 V，主机内部上拉 | 网络 confirmed；键名 proposed |
| 2 | GPIO53 | `KEY_*` | 底座→主机 | 直通 | 3.3 V | 同上 |
| 3 | GPIO19 | `KEY_*` | 底座→主机 | 直通 | 3.3 V | 同上 |
| 4 | GPIO48 | `KEY_*` | 底座→主机 | 直通 | 3.3 V | 同上 |
| 5 | GPIO18 | `KEY_*` | 底座→主机 | 直通 | 3.3 V | 同上 |
| 6 | GPIO13 | `KEY_*` | 底座→主机 | 直通 | 3.3 V | 同上 |
| 7 | GPIO17 | `KEY_*` | 底座→主机 | 直通 | 3.3 V | 同上 |
| 8 | GPIO12 | `KEY_*` | 底座→主机 | 直通 | 3.3 V | 同上 |
| 9 | GPIO16 | `KEY_*` | 底座→主机 | 直通 | 3.3 V | 同上 |
| 10 | GPIO14 | `SLOT_EEPROM_A0` | 主机→模块 | **只接 AT24C02 A0，不得接按键、不得引到弹簧针** | 3.3 V，主机推挽输出 0 | confirmed（`subboard.c:101–120`） |
| 11 | GPIO15 | `KEY_*` | 底座→主机 | 直通 | 3.3 V | 网络 confirmed；键名 proposed |
| 12 | GPIO4 | `SLOT_SPARE_GPIO4` | — | 引至模块板测试焊盘 `TP_SPARE`，**不引到弹簧针**（接口无余针） | 3.3 V | proposed |
| 13 | GPIO33 / USJ_DN | `SLOT_USJ_DN` | — | **NC**，焊盘不连铜 | — | 保留，proposed NC |
| 14 | GPIO1 / SCL | `SLOT_SCL` | 双向开漏 | 接 AT24C02 SCL；经 DNP 0 Ω `R_LINK_SCL` 到弹簧针 `DOCK_SCL` 焊盘；DNP 上拉位 `R_PU_SCL` 到 `SLOT_3V3` | 3.3 V 开漏 | 网络 confirmed；DNP 位 proposed |
| 15 | GPIO34 / USJ_DP | `SLOT_USJ_DP` | — | **NC**，焊盘不连铜 | — | 保留，proposed NC |
| 16 | GPIO0 / SDA | `SLOT_SDA` | 双向开漏 | 接 AT24C02 SDA；经 DNP 0 Ω `R_LINK_SDA` 到 `DOCK_SDA` 焊盘；DNP 上拉位 `R_PU_SDA` | 3.3 V 开漏 | 同上 |
| 17 | 5V_IN | `SLOT_5V_IN` | 底座→主机 | 直通到弹簧针 `DOCK_5V` 焊盘（2 针并联）；模块板上不放任何有源器件 | 5 V 名义；额定 unknown | 功能 confirmed（V1.0 指南）；V1.2 额定 unknown |
| 18 | 5V_OUT | `SLOT_5V_OUT_NC` | — | **NC，绝不连接任何网络**；焊盘不连铜，丝印「NC」 | — | 硬约束 2 |
| 19 | VCC_3V3 | `SLOT_3V3` | 主机→模块 | 只供 AT24C02 VCC、其去耦电容与 DNP 上拉位；**不引到弹簧针** | 3.3 V | 硬约束 3 |
| 20 | GND | `SLOT_GND` | 回流 | 直通到弹簧针 `DOCK_GND` 焊盘（2 针并联）；AT24C02 GND、A1、A2、WP 策略见第 7 节 | — | confirmed；单针载流 unknown（AS-18） |

约束：

- 11 根可用 GPIO 集合 `{55,53,19,48,18,13,17,12,16,15,4}`（derived，D1）。10 个 `KEY_*` 各占其中一根，余 1 根（默认 GPIO4）作 `SLOT_SPARE_GPIO4`。PINMAP.md 可以改用别的 GPIO 作备用，但**任何 `KEY_*` 都不得落在 GPIO14 或 pin 13/15**。
- 与板载 I²S `{54,37,49,52,40}` 交集为空（confirmed，`esp_mosaico.h:108–114`）。这只证明与板载 I²S 无冲突，不证明与其他驱动无冲突。
- `ASSUMPTION: AS-15` 11 根 GPIO 均可配置为带内部上拉的输入，且无 strapping 副作用。验证：到货后查主机 SoC 数据手册 strapping 表；G6-D5 按住每一键开机观察启动是否正常。
- 模块板对 `KEY_*` 可预留串阻位（`R_S_KEY_*`，默认 0 Ω）与 ESD 位，数值由模块板任务提案、Hiro 复核；ICD 不定值。

## 3. 弹簧针接口（底座主板 ↔ 模块板）

### 3.1 定义

- 底座主板装弹簧针（pogo pin），针尖朝 +Y；模块板底面（−Y 法向）为触点焊盘。**每天插拔发生在这里**；H2 槽位在装配时插一次此后不拔（方案 G 的核心）。
- `ASSUMPTION: AS-07` 2.54 mm 间距，2 行 × 8 列 = 16 针。验证：到货核实模块板可用底部宽度（依赖 AS-01、AS-04），若 8 列 × 2.54 = 17.78 mm 加边距放不下，改 1.27 mm 或改行数并重发本节。
- 编号：列 1 在 −X 极端（靠左握把外侧），列 8 靠 Mosaico 中央；行 A 靠 +Z（屏侧），行 B 靠 −Z。针号写作 `A1…A8`、`B1…B8`。
- 参数：`DOCK_PITCH`（默认 2.54）、`DOCK_COLS`（8）、`DOCK_ROWS`（2）、`DOCK_PAD_D`（模块板焊盘直径，由模块板任务定）、`DOCK_PIN_TRAVEL`（弹簧针工作行程，由选型定）、`DOCK_X_TOL`、`DOCK_Z_TOL`（托架对配合的 X、Z 定位公差，由机械任务定，须满足 3.3 节要求）。

### 3.2 逐针分配（proposed）

| 列 | 行 A（+Z，屏侧） | 行 B（−Z，背侧） | 说明 |
| --- | --- | --- | --- |
| 1（−X 最外） | `DOCK_5V` | `DOCK_5V` | 两针并联；模块板侧接 `SLOT_5V_IN`（H2 pin 17） |
| 2 | `DOCK_GND` | `DOCK_GND` | 两针并联；模块板侧接 `SLOT_GND`（H2 pin 20） |
| 3 | `KEY_UP` | `KEY_DOWN` | D-pad |
| 4 | `KEY_LEFT` | `KEY_RIGHT` | D-pad |
| 5 | `KEY_L` | `KEY_R` | 肩键 |
| 6 | `KEY_A` | `KEY_B` | ABXY |
| 7 | `KEY_X` | `KEY_Y` | ABXY |
| 8（靠中央） | `DOCK_SDA` | `DOCK_SCL` | 预留可选电量计；模块板侧经 DNP `R_LINK_SDA/SCL` 接 `SLOT_SDA/SCL`，**默认不装** |

底座侧：每个 `KEY_*` 针接一颗轻触开关的一端，开关另一端接 `DOCK_GND`；**底座对 `KEY_*`、`DOCK_SDA`、`DOCK_SCL` 不放任何上拉、不接任何电源**（硬约束 5、6）。`DOCK_5V` 由底座 `BOOST_5V` 经限流、短路保护与防反灌器件供出（硬约束 1、8），路径为纯硬件。

### 3.3 防呆（三级）

一级，机械（proposed，由机械任务实现并在 `hardware/ASSUMPTIONS.md` 登记参数）：

- 弹簧针场只位于模块板正下方，偏置在 −X 侧（AS-08）。Mosaico 为近似正方形，但装上模块板后组件不对称：绕 Y 轴转 180° 放入时触点面落到 +X 侧握把上方，**触不到任何针**；绕 X 或 Z 轴转 180° 时触点面朝上，无法配合。
- 托架用非对称限位与硬限位，使错误朝向在压到任何电触点之前就被几何阻止。
- 托架对 X 方向定位公差 `DOCK_X_TOL` 必须小于焊盘允许偏移，使**沿 X 错位不可能达到 2 列**（列 1 的 5 V 错到列 3 的 `KEY_*` 就是主机 GPIO 损坏）。数值由机械与模块板任务联合给出，Hiro 复核。

二级，电气分配（proposed，即 3.2 节布局的理由）：

| 错位情形 | 底座针 → 模块板焊盘 | 结果 | 结论 |
| --- | --- | --- | --- |
| X 方向 +1 列（针场相对焊盘向中央偏） | 5V 针 → GND 焊盘；GND 针 → 列 3 键焊盘；键针 → 相邻键焊盘；列 7 键针 → SDA/SCL 焊盘；列 8 针悬空 | 5V–GND 短路由底座输出短路保护吸收；主机键线被拉低等同按键；键位置换 | 无损，功能错误可辨认 |
| X 方向 −1 列 | 5V 针悬空；GND 针 → 5V_IN 焊盘；键针 → GND 焊盘或相邻键；SDA/SCL 针 → 列 7 键焊盘 | 无 5 V 源接入任何信号；主机 5V_IN 只接到底座地，无回路 | 无损 |
| Z 方向错一行 | 行 A 针 → 行 B 焊盘：5V→5V、GND→GND、键→键、SDA→SCL；行 B 针悬空 | 同列同类，只有 SDA/SCL 互换与键位置换 | 无损 |
| 绕 Y 轴 180° | 由一级机械保证触不到针 | — | 若一级失效，5V 针会落到列 8 SDA/SCL 焊盘，**有损**；因此一级不可省 |

三级，电源保护（硬约束 1、8，由底座任务实现）：`DOCK_5V` 输出限流与短路关断、防反灌；阈值由 Chrome 定义。**限流不等于允许反向电压**，未证明错误接触安全前不放行带电插接。

先接触次序：等长弹簧针无法保证 GND 先于 5V 接触。proposed 两条路线由底座任务择一：`DOCK_GND` 用行程更长的针型；或不依赖先接地，靠输出软启动与主机 5V_IN 输入容忍（AS-19，unknown）。G6-G 插拔试验记录浪涌。

### 3.4 载流

`DOCK_5V` 与 `DOCK_GND` 各 2 针并联。单针额定「待原厂数据手册核对」（AS-26），并联后须覆盖 `ASSUMPTION: AS-09` 峰值 ≤ 1 A。接触电阻在 G6-G 每 10 次插拔后以 0.5 A 下压降复测。

## 4. 电气约束（硬约束 1–9 及派生）

| ID | 约束 | 依据 | 实现归属 | 验证 |
| --- | --- | --- | --- | --- |
| EL-D-01 | **`DOCK_5V` → pin 17 供电是纯硬件路径**，不等待 EEPROM 识别、不等待主机任何 GPIO 或 I²C 许可、不依赖 GPIO60 | `subboard.c:122–141`：主机先开模块 VCC_3V3 → 初始化 I²C → 扫描；主机电池耗尽时若底座等许可则死锁 | 底座 | G6-A2/A3：不接 Mosaico、不接模块板时 `DOCK_5V` 即有输出 |
| EL-D-02 | **pin 18 5V_OUT 绝不连接底座输出**；模块板焊盘 NC 且不连铜 | V1.0 原理图 D14 使 USB VBUS 可绕过 GPIO60 到 5V_OUT；V1.2 unknown | 模块板 | G6-A6：pin 18 焊盘对 `DOCK_5V`、`SLOT_5V_IN` 均开路 |
| EL-D-03 | **EEPROM 由 pin 19 `SLOT_3V3` 取电**；底座不得向 `SLOT_3V3` 或任何主机 3.3 V 网络送电；弹簧针接口无 3V3 针 | 避免主机掉电、底座有电时经上拉/EEPROM 向主机注入 | 模块板、底座 | G6-A6：模块板在底座上、Mosaico 未接时 `SLOT_3V3` 焊盘为 0 V |
| EL-D-04 | **不照搬 V1.0 的 4.7 kΩ 上拉结论**；模块板预留 `R_PU_SDA`、`R_PU_SCL` DNP 位到 `SLOT_3V3`；底座不放上拉 | V1.2 模块 I²C1 独立（GPIO0/1），源码只证明内部上拉开启 | 模块板 | G6-E：有示波器时测 SDA/SCL 上升时间与低电平；无则记录 EEPROM 读出成功率 |
| EL-D-05 | 按键为无源开关接 `DOCK_GND`；拉高由主机内部上拉提供；全部 3.3 V 域；**禁 5 V 上拉、禁任何底座侧拉高** | D1 合同 | 底座、模块板、固件（配置输入上拉） | G6-A6 通断；G6-D 十键 |
| EL-D-06 | V1.2 模块 I²C1 上只有 0x50（左 EEPROM）/0x51（右 EEPROM）；底座若加 I²C 器件**不得用这两个地址**；默认 `R_LINK_SDA/SCL` DNP | D1；第 6 节地址表 | 底座、模块板 | G6-C 地址扫描 |
| EL-D-07 | BSP 无按键中断通路；十键以 20–40 ms 轮询 + 去抖（`ASSUMPTION: AS-23`） | D1；固件任务 | 固件 | G6-D 手感与丢键记录 |
| EL-D-08 | 底座 USB-C 与 Mosaico 原生 USB-C **可能同时供电**；底座对 pin 17 的输出必须防反灌（主机侧有电时不得向底座 `BOOST_5V`/`VSYS`/`VBAT` 回灌）；`ASSUMPTION: AS-11` 主机内部合并拓扑 | `docs/INTERFACE_CONTROL.md` EL-01/EL-08（V1.0 D10/D14），V1.2 unknown | 底座 | G6-B 八态表；反向电流阈值待 Chrome 定义 |
| EL-D-09 | 器件优先嘉立创常备料（AS-27）；H2 配对公头给候选并标「待原厂规格核对」（AS-06）；LCSC 编码器件关键参数未打开数据手册者一律写「待原厂数据手册核对」 | 任务书 | 全部 | BOM 审核 |
| EL-D-10 | 派生：主机上电、底座无电（电池空、USB 未接）时，主机内部上拉经 `KEY_*` 看到的只是开路开关，经 `DOCK_SDA/SCL`（若装 `R_LINK`）看到的是**未上电底座 I²C 器件**，其 ESD 二极管可能把 3.3 V 拉进底座 → 因此 `R_LINK` 默认 DNP；装配前须审核该器件 Ioff/断电容限 | `docs/INTERFACE_CONTROL.md` EL-06 同类问题 | 底座、模块板 | G6-B 态 (D=0,B=0,N=1)：测 `DOCK_SDA/SCL` 针对 `DOCK_GND` 电压与流入底座电流 |
| EL-D-11 | 派生：底座有电、主机无电（态 D/B 任一为 1、N=0 且主机关机）时，除 `DOCK_5V` → pin 17 外，底座不得经任何针向主机注入电流；`KEY_*` 开关即使被按住也只连到 GND | 幽灵供电 | 底座 | G6-B 态 (1,0,0)：测 `KEY_*`、`DOCK_SDA/SCL` 针电压为 0 V |
| EL-D-12 | pin 17 输入额定 unknown；电源预算按 `ASSUMPTION: AS-09`（整机峰值 ≤ 1 A、持续 ≤ 0.6 A @ 5 V）做假设性计算并注明无官方依据；`DOCK_5V` 设定电压与容差 `ASSUMPTION: AS-10`（5.0 V 名义），限流阈值待 Chrome 定义 | D1 DOCUMENT_BOUNDARIES：不得用 100 mA 模块输出或 500 mA USB source 代替 | 底座 | G6-A4 假负载阶梯；G6-B 用原生 USB 串电流表测整机实际峰值/持续电流，回填 AS-09 |

## 5. 机械约束（全部 ASSUMPTION，数值集中在 `hardware/ASSUMPTIONS.md`）

| ID | 约束 | 假设编号 | 到货验证 |
| --- | --- | --- | --- |
| ME-D-01 | Mosaico 整机外形 45.19 × 45.19 × 11.48 mm、33 g（官方视频简介标称，非图纸） | AS-01 | 第一轮 W/H 各量 3 次；T 只在前后均为可安全触及的绝缘边框时量，否则侧视并记未测；质量另称，缺项不关闭 AS-01 |
| ME-D-02 | 左槽 2×10P 间距 2.54 mm | AS-02 | 第一轮 Q07/Q08 三视图、行列与标尺齐平证据；Chrome 回算可见孔距/跨距，未认针号不写 1→19；不能据照片定制造尺寸 |
| ME-D-03 | 母座在机身 −X 面、开口朝 −X；与外壳面的凹陷/凸出量 unknown | AS-03 | Q07 正视/斜视/定位照和外壳基准；凹深无绝缘检具保持未测 |
| ME-D-04 | 槽中心 Z ≈ 厚度中点；Y 位置 unknown，参数 `SLOT_PIN1_Y` | AS-04 | Q07 标可见孔位与外壳/USB-C 基准；Chrome 映射 ICD 轴；未认针号不写 pin 1 坐标 |
| ME-D-05 | 槽连接器为轴向插接排针/排母（E-01 未证实）；四角银色块为整机之间组合用磁铁，非模块连接 | AS-05 | P00d/Q06/Q07/Q08 外观照；不做回形针试吸或探针插入，磁性仍 unknown |
| ME-D-06 | 配对公头：`B-2200R20P-B120` 的配对件候选（2.54 mm 2×10 直/弯排针）「待原厂规格核对」；模块板一侧公头是否用弯针实现向 −Y 转向，由模块板与机械任务定 | AS-06 | 先核同版母座与原厂规格；试插仅按后续独立评审步骤，第一轮不插拔 |
| ME-D-07 | 模块板厚度、外形与 Mosaico 底面 −Y 的关系：触点面必须低于 Mosaico −Y 面（`MODULE_PAD_FACE_Y < −MOSAICO_H/2`），且不遮挡原生 USB-C | AS-22 | 第一轮 P14_USB-C 与旁置标尺、外壳基准；卡尺不进入小开孔，接口中心待后续回算和试配 |
| ME-D-08 | 模块板在槽内保持力 unknown（槽可能无锁扣）；机械任务需给模块板与 Mosaico 本体的辅助固定 | AS-24 | 第一轮 Q07 外观照；保持力与晃动待同版样件、独立试装步骤 |
| ME-D-09 | Mosaico −Y 面除 USB-C 外是否还有需暴露的孔（扬声器、麦克风、按键） unknown | AS-25 | 到货目视 |
| ME-D-10 | 弹簧针场位置、行程、托架定位公差（`DOCK_X_TOL`、`DOCK_Z_TOL`）由机械任务给出并满足 3.3 节 | AS-08 | 首版打板后用无源检具核 |
| ME-D-11 | 电池 1500 mAh 3.7 V 软包为参数化默认值；尺寸、保护板、插头 unknown | AS-12 | 用户所在地可购型号确认后回填 |

## 6. I²C 地址表（V1.2 模块 I²C1：SDA=GPIO0/H2 pin 16，SCL=GPIO1/H2 pin 14）

| 7 位地址 | 器件 | 出现条件 | 状态 |
| --- | --- | --- | --- |
| 0x50 | 左槽模块 EEPROM（AT24C02，A0=GPIO14=0，A1=A2=0） | 模块板插入且 pin 19 有电 | confirmed（`subboard.h:19–39`） |
| 0x51 | 右槽模块 EEPROM（A0=GPIO39=1） | 用户另插右模块时 | confirmed；本方案不使用右槽（AS-21） |
| 0x00–0x07、0x78–0x7F | I²C 规范保留 | — | 禁用 |
| 0x11、0x12、0x19、0x55、0x5A、0x69 | V1.0 主板器件；V1.2 已移到主板 I2C0（GPIO56/3） | 本总线上不应出现 | proposed：底座器件仍避开，保留跨版本兼容 |
| 待定 | 底座可选电量计（候选类别：单节电池电量计，LCSC 常备料；地址「待原厂数据手册核对」） | 仅当 `R_LINK_SDA/SCL` 装配且 EL-D-10 审核通过 | proposed，默认不装 |

100 kHz（confirmed，模块管理器 `mosaico_module_mgr.c:22–28`）。底座器件若装配须支持 100 kHz 且总线电容预算由 Chrome 定义。

## 7. EEPROM 身份

### 7.1 电气（本稿约束）

- 器件类别：AT24C02 兼容，3.3 V，256 × 8，硬件 A0，单字节内部地址，支持从地址 0 连续读 134 字节。具体订货号由 EEPROM/模块板任务从嘉立创常备料选，参数「待原厂数据手册核对」。
- VCC ← `SLOT_3V3`（pin 19），就地去耦；GND ← `SLOT_GND`；A0 ← `SLOT_EEPROM_A0`（pin 10）；A1、A2 ← `SLOT_GND`（使地址为 0x50/0x51 区分）。
- WP：proposed 默认拉到 `SLOT_3V3`（写保护），经 DNP 跳线/焊桥 `J_WP` 可拉低以便烧录夹具写入；主机固件模块管理器**无写 EEPROM API**（confirmed），量产/维修烧录由独立夹具完成，接口由 EEPROM 任务定义。
- 烧录夹具接触点：proposed 在模块板上留 4 个测试焊盘 `TP_SDA`、`TP_SCL`、`TP_3V3`、`TP_GND`（与 H2 断开时可独立供电烧录），位置由模块板任务定。

### 7.2 镜像格式（confirmed，来源 `review/chrome/D1-module-interface/BSP_AND_EEPROM.md` 第 3 节，解析器 `mosaico_module_mgr.c:199–260`）

总长 134 字节（0x86），多字节 little-endian；magic 为 ASCII `ESP`；三段 CRC16：初值 0xFFFF、逐字节异或、右移、最低位为 1 时异或 0xA001、无末尾异或。校验区间：0x00–0x33 → 0x34；0x36–0x3D → 0x3E；0x40–0x83 → 0x84。参数 CRC 覆盖完整 64 字节参数区。`param_length ≤ 64`。

| 偏移 | 长度 | 字段 | 本方案取值归属 |
| --- | --- | --- | --- |
| 0x00 | 3 | magic `ESP` | 固定 |
| 0x03 | 1 | board_type | EEPROM 任务提案；`ASSUMPTION: AS-20` 官方未分配我方类型 |
| 0x04 | 2 | board_id | EEPROM 任务提案 |
| 0x06 | 2 | hw_version | 与模块板 PCB 版本绑定 |
| 0x08 | 2 | sw_version | 与镜像格式版本绑定 |
| 0x0A | 2 | vendor_id | EEPROM 任务提案（AS-20） |
| 0x0C | 4 | board_flags | EEPROM 任务 |
| 0x10 | 4 | serial_number | 每块模块板唯一 |
| 0x14 | 32 | board_name | 建议含「MOSAICO-DOCK-MODULE」与版本，不保证 NUL 结尾 |
| 0x34 | 2 | descriptor CRC | 计算 |
| 0x36–0x3D | 8 | 制造日期、批次、工厂 | 打板批次 |
| 0x3E | 2 | manufacturing CRC | 计算 |
| 0x40 | 2 | param_version | EEPROM 任务 |
| 0x42 | 2 | param_length | ≤ 64 |
| 0x44 | 64 | param_data | proposed：写入 `KEY_*` → GPIO 映射版本号（与 PINMAP.md 一致），供固件核对 |
| 0x84 | 2 | parameter CRC | 计算 |

**空白 EEPROM 不合格**；烧入合法身份也不会自动产生十键驱动（confirmed，D1 结论 3）。十键功能依赖固件任务的主机侧驱动（第 8 节）。

## 8. 固件接口要求（供 `claude/design-d/firmware`）

- 十键驱动固定左槽；GPIO 来自 `hardware/module-board/PINMAP.md`，配置为输入 + 内部上拉；轮询周期与去抖参数按 EL-D-07；响应模块拔出事件并释放。
- 最小测试固件须提供：① 槽扫描/身份读出命令（`hardware/G6-TEST-PLAN.md` 中暂用任务书名称 `module_slot_scan`，实际名称以固件任务为准），输出 presence、134 字节原始镜像、三段 CRC 结果；② 十键自检 `keytest`，逐键显示按下/释放与时间戳，支持多键同时；③ 只读的 I²C 地址扫描（不写任何地址）。
- 不得写 EEPROM；不得驱动 GPIO14 以外的槽位 GPIO 为输出。

## 9. 跨子系统网络命名总表

| 位置 | 网络名 | 对应 |
| --- | --- | --- |
| H2 / 模块板槽侧 | `SLOT_5V_IN` `SLOT_GND` `SLOT_SDA` `SLOT_SCL` `SLOT_3V3` `SLOT_EEPROM_A0` `SLOT_SPARE_GPIO4` `SLOT_USJ_DN` `SLOT_USJ_DP` `SLOT_5V_OUT_NC` | 第 2 节 |
| 按键（模块板与底座共用） | `KEY_UP` `KEY_DOWN` `KEY_LEFT` `KEY_RIGHT` `KEY_A` `KEY_B` `KEY_X` `KEY_Y` `KEY_L` `KEY_R` | GPIO 分配只在 PINMAP.md |
| 弹簧针接口 | `DOCK_5V` `DOCK_GND` `DOCK_SDA` `DOCK_SCL` + 同名 `KEY_*` | 第 3 节 |
| 底座电源 | `VBUS_IN`（USB-C 输入）`VBAT`（电池）`VSYS`（系统母线）`BOOST_5V`（升压输出，经保护后成为 `DOCK_5V`） | 底座任务 |

模块板上 `SLOT_5V_IN` 与 `DOCK_5V`、`SLOT_GND` 与 `DOCK_GND` 是同一铜网络的两个名字（槽侧/针侧），网表中以 `DOCK_5V`/`DOCK_GND` 为网络名、`SLOT_*` 为 H2 焊盘标签。

## 10. 冻结登记（由主控记录，当前全部空缺）

| 版本 | 对应内容提交 | 非作者复核（Hiro/Chrome）提交与结论 | 日期 | 节点 | 主控记录 |
| --- | --- | --- | --- | --- | --- |
| ICD-0.2-DRAFT 方案 D＋G 分册 a | 本分支最终提交号 | 尚未复核 | 2026-09-20 | 非 G1/G2/G3 放行 | 未冻结 |

进入冻结至少需要：到货认版（BaseBoard/CoreBoard 标识与 eFuse）、`hardware/ASSUMPTIONS.md` 中 AS-01～AS-08、AS-17 关闭、pin 17 额定或经审核的限流值、EL-D-08 八态验证方案、Hiro 对第 3.3 节防呆与第 4 节的复核结论。按 D-017，首版打板不要求本表冻结，但打板前须完成非作者复核并满足 `docs/TEAM_PLAN.md` 第 6 节 G3 远程验收补偿约束。

## 11. 版本历史

| 版本 | 日期 | 变更 | 作者 |
| --- | --- | --- | --- |
| 方案 D＋G 分册 a | 2026-09-20 | 首稿：坐标系、H2 合同、弹簧针 2×8 分配与三级防呆、EL-D-01～12、ME-D-01～11、地址表、EEPROM 身份、固件接口、命名总表 | Claude 主控（claude-fable-5-1） |
