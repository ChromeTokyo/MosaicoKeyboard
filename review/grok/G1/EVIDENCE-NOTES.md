提案 · 未冻结 · 由 Grok 独立复核（实际模型 ID 未由可核验接口暴露）起草 · 待主控定稿 · 不得据以制造

# G1 EVIDENCE-NOTES

冻结 SHA：`96fd823e93f264280207eb34b7a97e139ace7378`（2026-09-21 JST）。本文件为父代理定稿 `REPORT.md` 的证据底稿。

---

## A) G01–G08 在当前 main 的整改状态

对照真本 `origin/grok/r0-design-review:review/grok/R0/REPORT.md` §4。**本轮结论：G01–G08 在冻结 SHA 上均未关闭**（G08 仍为已标 ASSUMPTION 的可接受开放项）。V0 派发包旁注「G04／G05 尚未整改」与本轮源码／ICD 阅读一致。

### A.1 逐条

| ID | R0 要点 | 冻结 SHA 状态 | 证据（file:line） | 判定 |
| --- | --- | --- | --- | --- |
| **G01** | `dock_handle_pinmap.h` J2 焊盘注释与 PINMAP 不一致；GPIO 宏正确 | **仍开** | 头文件：`firmware/dock_handle/include/dock_handle_pinmap.h:45-81` 仍写 KEY_DOWN=**A4**、LEFT=**A5**、RIGHT=**A6**、L=**A7**、R=**B2**、A=**B3**、B=**B4**、X=**B5**、Y=**B6**；导言验收句 L28 仍写「A3=KEY_UP … B6=KEY_Y」。权威 PINMAP 修订 b：`git show origin/claude/design-d/module-board:hardware/module-board/PINMAP.md` §2 表为 DOWN=**B3**、LEFT=**A4**、RIGHT=**B4**、L=**A5**、R=**B5**、A=**A6**、B=**B6**、X=**A7**、Y=**B7**；同文件修订说明第 1 行已点名「`dock_handle_pinmap.h` 注释…需改为本文第 4 节」。GPIO 宏（DOWN=19 等）与 PINMAP §2 **一致**。`firmware/dock_handle/README.md:50-58` 转抄表同样带错误焊盘列（DOWN→A4、A→B3）。 | 未整改 |
| **G02** | 自称读取「PINMAP 2026-09-20 版」过期 | **仍开** | `dock_handle_pinmap.h:7`「2026-09-20 版」；`README.md:48`「2026-09-20」。PINMAP 修订 b 日期为 **2026-09-21**。 | 未整改 |
| **G03** | AS-16／AS-28 高估 eFuse 对 1.2 vs 1.2.1 分辨力 | **仍开** | `hardware/ASSUMPTIONS.md` AS-16（约 L32）验证列仍写「读 eFuse/版本信息…对照 BaseBoard 标签」；AS-28（约 L44）命题仍为「eFuse 中的板卡变体与…标签**严格对应**」。未见改为「仅区分 V1_0／V1_2 族」。 | 未整改 |
| **G04** | ICD §3.3「X−1 无损」对 GND→5V_IN 论证偏弱 | **仍开（紧急）** | `hardware/ICD-0.2-DRAFT.md:144` 仍写：X−1 时「GND 针 → 5V_IN 焊盘」…「主机 5V_IN 只接到底座地，无回路」→ 结论列 **「无损」**。未补「主机须断电／输入保护证据」前提，亦未降级措辞。若主机经原生 USB 已上电，5V_IN 网络对底座地存在把主机供电输入拉向地的路径——原 R0 推导仍成立。 | 未整改 |
| **G05** | 错位枚举缺对角／多列（或须显式依赖公差） | **仍开（紧急）** | `ICD-0.2-DRAFT.md:141-146` 表仅列：X±1 列、Z 错一行、绕 Y 180°。无对角（同时 X+Z）、无 ≥2 列组合行。L137 有「`DOCK_X_TOL` 必须…不可能达到 2 列」的一级要求，但二级表未写「因此对角／多列不在枚举内」的显式声明；AS-08（`ASSUMPTIONS.md` 约 L24）仍 OPEN。 | 未整改 |
| **G06** | AS-31-* 仅「待吸收」 | **仍开** | `ASSUMPTIONS.md` §3（约 L62–71）仍「待吸收」；总表无 AS-31 指针行。子系统仍自用 `AS-31-eeprom-*`／`AS-31-firmware-*`／`AS-31-mb-*`。 | 未整改 |
| **G07** | 未 ESP-IDF／真机编译 | **仍开** | `firmware/dock_handle/README.md:12`、`:195`、`:270`（§7.5／§12）仍自述未 `idf.py build`；BUILD-LOG §5 亦复述 IDF 6.2／esp32s31 缺口。 | 未整改 |
| **G08** | WP 默认 ICD vs 模块板冲突 | **仍开（已知可接受）** | `PROGRAMMING.md` §2.1 仍描述冲突并挂 `AS-31-eeprom-4`；需 Chrome 决策。不把 (a) 从 PASS 打落，但未闭合。 | 已知开放 |

### A.2 附录转录 vs 真本 REPORT — 实质差异

| 维度 | 真本 (`origin/grok/r0-design-review:…/R0/REPORT.md`) | V0 附录 (`review/audit/V0/APPENDIX-grok-r0-transcript.md`) |
| --- | --- | --- |
| 体量 | 251 行完整报告 | 68 行压缩转录 |
| 署名／来源 | Grok 起草原文 | **主控新增**性质声明：据用户转贴、非 Grok 自推；并声明「若有原件以原件为准」 |
| Q1–Q5 | 完整出处表、分段表、GPIO 表、eFuse 映射表 | 压缩为要点句；数值与结论与真本一致（未见改答案） |
| G01–G08 | 每条含文件／推导／建议 | 单表一行摘要；**删去** G04 完整「原生 USB 已上电→5V_IN 对地」推导链 |
| §5–7 分项检查表 | 有 | 压缩为三条 bullet |
| 独立性披露 §0.1 | 全文 | 「要点」缩写 |
| 总结论 | CHANGES_REQUIRED | 同 |

**实质判断：** 附录**不是**逐字副本；属忠实压缩 + 主控 provenance 框。**未见**把失败改成通过、或捏造额外发现。但审计若只读附录会**丢失** G04 论证细节与分项「未检查」边界。真本现已在 `origin/grok/r0-design-review`（tip 含 `d6cbca3`／`f64f1e4`），应优先真本。

---

## B) Mechanical BUILD-LOG 独立核对（MB-CHK-10）

### B.1 文件与工具

- 已读：`mechanical/verification/BUILD-LOG-20260921.md`（merge `96fd823` ← `a6d87f2`，PR #46）。
- **OpenSCAD：本 Linux 盒 PATH 中不存在**（`which openscad` 失败）。**未编译、未声称编译。**
- **源文件缺失：** 在冻结 SHA 上 `mechanical/module-board/module_board.scad`（以及 BUILD-LOG 所引 `dock_shell.scad`／`keycaps.scad`）**不存在**。`git show a6d87f2 --stat` 显示该提交**只新增** BUILD-LOG 一文件（+48 行），未入库任何 `.scad`。全仓库 `find`／`git log --all -- '*.scad'` 无 `module_board.scad` 历史。

### B.2 MB-CHK-10 声称

BUILD-LOG L38–42：

- 孔 B 到最近板边 = **2.405 mm**；判据 **≥ 2.5 mm**；差 **0.095 mm**（算术：2.5 − 2.405 = 0.095，自洽）。
- 出处自称：`module_board.scad` `[检查 10]` ECHO；孔 A = 3.495 mm（通过）。

**独立复算：** **不能**。缺少 scad 参数与 ECHO 公式，无法从仓库源重算边距。因此：

- **不能确认** 2.405 是否由模型几何真实算出；
- **仅能确认** BUILD-LOG 内部「2.405 vs 2.5 → 差 0.095」叙述自洽，且作者自判失败、禁止制造用途——该**流程态度**合理；
- **MB-CHK-10「确认」= 否（源缺失 + 无 OpenSCAD）**。

### B.3 其他矛盾／风险

1. **证据链断裂（新发现）：** 验证日志引用的几何源未合入同一 SHA → 第三方无法复现 ECHO。属必须修复的过程／入库问题。
2. **Genus：** BUILD-LOG 称 module_board genus 20、dock_shell 170、keycaps **−16**（并解释分件）。无源／无编译则**无法核验**；负 genus 解释表面上说得通，但不构成证实。
3. **尺寸 vs ASSUMPTIONS：** BUILD-LOG 整机外形 **167 × 101.5 × 28 mm** 指**底座外壳**包络；AS-01 的 **45.19 × 45.19 × 11.48 mm** 指 **Mosaico 主机**。二者对象不同，**不构成直接数值矛盾**。但 ASSUMPTIONS §3 仍写 mech 路径「`mechanical/module/`／`mechanical/dock/`（路径待确认）」而 BUILD-LOG 使用 `mechanical/module-board/`／`mechanical/dock-shell/`——**路径命名未在总表闭合**，属文档漂移（nit／must-fix 视主控口径）。
4. **电池仓** 50×34×8 等为日志自述实测，仓库内无对应 ASSUMPTION 闭合值可对拍（AS-12 电池尺寸仍 unknown）。

---

## C) Chrome D1 二线抽查（标签 G1-D1-*；不替代 Hiro H1）

基线：`review/chrome/D1-module-interface/evidence/bsp/` commit **`392860b1d1a123c3377947074b2af1f600e86c5d`**。本轮复算 SOURCE_INDEX **12/12 SHA-256+bytes OK**。

### C.1 左槽 pin 合同（高后果）

| 主张（D1） | 本轮核对 | 支持？ |
| --- | --- | --- |
| H2 pin1–12 → GPIO 表（LEFT_SLOT.md L9–20） | 与 `user_guide_v10.rst` H2 表（约 L627–686：1→55 … 10→14 … 12→4）一致；集合 `{4,12,13,14,15,16,17,18,19,48,53,55}` | **支持**（V1.0 指南原文） |
| BSP 左槽 12 GPIO 集合相同 | `subboard.c:54-67` `s_gpio_pairs[].left` 给出同集；`connector_gpio[6]`（L30–33）仅为偶数脚子集——D1／BSP_AND_EEPROM 已说明奇数脚靠指南交叉 | **支持**（且 D1 未隐瞒交叉依赖） |
| 与板载 I²S 交集 ∅ | `esp_mosaico.h:109-113` → `{54,37,49,52,40}`；与上集无交 | **支持** |
| 「能直连」≠ 出厂已支持十键 | README／LEFT_SLOT 均有限定 | **支持**（表述克制） |

**风险／跳跃：** 奇数脚映射**依赖 V1.0 用户指南**；`DOCUMENT_BOUNDARIES.md` 已声明 V1.2 内部实现 unknown。LEFT_SLOT L3 亦写 V1.2 实物方向／额定仍须实测。二线：**合同作为「软件+ V1.0 表交叉」成立；不得当成 V1.2 铜皮／额定已证实。**

### C.2 EEPROM 地址选择

| 主张 | 核对 | 支持？ |
| --- | --- | --- |
| 左：GPIO14 驱 0 → AT24C02 @ **0x50** | `subboard.h:26-39`（宏 ADDR_LEFT=0x50、GPIO_LEFT=14、LEVEL_LEFT=0）；`subboard.c:101-120` 推挽输出并 `gpio_set_level`；init L136–138 对两槽调用 | **支持** |
| 发现阶段该脚不作普通输入 | 同上 OUTPUT 配置 | **支持** |
| 摄像头例外复用 GPIO14 | `subboard.h:29-31`；`subboard.c:103` 注释 | **支持** |

### C.3 供电时序相关主张

| 主张 | 核对 | 支持？ |
| --- | --- | --- |
| `bsp_subboard_init`：先开模块 VCC_3V3 → I²C → 地址脚 | `subboard.c:132-138`：`bsp_power_set_vcc_3v3(true)` → `init_i2c_bus` → `configure_address_select` | **支持** |
| 因此 **pin17 底座供电不能等待 EEPROM／GPIO 许可**（否则耗尽电池时死锁） | BSP **无** pin17 控制代码；此为系统推理，ICD EL-D-01 亦采纳 | **推理成立，但不是 BSP 直接事实**——须标「derived」 |
| pin19 供 EEPROM；底座不得反送 3.3V | 与指南 pin19=VCC_3V3（GPIO60 控）及 D1 边界一致；BSP 示使能 VCC rail，未示底座可供电 | **方向支持**；额定／保护仍 unknown（DOCUMENT_BOUNDARIES） |
| LEFT_SLOT L27「拟供 EEPROM **与按键上拉**」 | 后续 ICD／固件定案为按键靠**主机内部上拉**、模块板无 5V／键上拉 | **轻微过述**（「按键上拉」易被读成模块侧上拉）；应用层应以 ICD EL-D-05 为准 |

### C.4 顶层风险摘要（给父代理）

1. **G1-D1-01** pin17／双电源／V1.2 保护链仍 unknown（DOCUMENT_BOUNDARIES）——设计可继续草案，**不可**当额定闭合。
2. **G1-D1-02** 奇数 GPIO 合同锚定 V1.0 指南——V1.2 丝印／实物未测前保留 AS-17 类风险。
3. **G1-D1-03** 「pin17 不得等待 EEPROM」为正确系统约束，但证据链是推导不是 BSP 引脚驱动表。
4. 本轮**未**重做 Hiro H1；以上为二线抽查。

---

## 提议发现清单（供 REPORT 采纳）

| ID | 严重度 | 摘要 |
| --- | --- | --- |
| G1-A-G01 | must-fix | J2 焊盘注释／README 转抄表与 PINMAP 修订 b 不一致（GPIO 宏正确） |
| G1-A-G02 | nit（建议 must-fix 一并改） | PINMAP 版本戳仍写 2026-09-20 |
| G1-A-G03 | must-fix | AS-16／AS-28 仍暗示 eFuse↔标签严格对应 |
| G1-A-G04 | **blocker**（或 must-fix+禁带电错位测） | ICD L144「X−1 无损」未补强／未降级 |
| G1-A-G05 | **blocker**／must-fix | 错位枚举仍缺对角／多列或显式公差排除声明 |
| G1-A-G06 | nit | AS-31-* 未入总表 |
| G1-A-G07 | must-fix | dock_handle 仍未 IDF 编译 |
| G1-A-G08 | nit（已知） | WP 默认待 Chrome |
| G1-B-01 | **blocker**（相对「可制造机械源」叙事） | BUILD-LOG 所引 `.scad` 未在冻结 SHA；MB-CHK-10 无法独立复算 |
| G1-B-02 | nit | ASSUMPTIONS mech 路径名与 BUILD-LOG 目录名不一致 |
| G1-B-03 | 信息 | 本机无 OpenSCAD；未编译 |
| G1-C-D1-01 | must-fix（文档） | 保持 pin17／V1.2 额定 unknown；禁止用 D1 PASS 语气关闭 |
| G1-C-D1-02 | nit | LEFT_SLOT「按键上拉」措辞易误导 |
| G1-T-01 | 信息 | V0 附录相对真本为压缩转录；无改结论但缺 G04 推导细节 |

**计数：** 提议发现 **14** 条（含信息／nit）；其中与 R0 未关闭项直接对应 **8** 条；新机械／过程 **3**；D1 二线 **2**；转录 **1**。

**G04／G05 仍开？** **是。**  
**MB-CHK-10 已确认？** **否**（源缺失 + 无 OpenSCAD；仅确认日志内差 0.095 mm 算术自洽）。  
**提议总结论：** **CHANGES_REQUIRED**（证据缺口亦排除 PASS）。
