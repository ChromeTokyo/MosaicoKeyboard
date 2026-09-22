# G2 EVIDENCE-NOTES

Freeze: `3eb5cf8a28d1e2bfafbf2cbda118cb986500e541` · 2026-09-23 JST · Grok EspBot  
所有引用为**本机观察**；未经观察的数值不写入。

---

## A) Architecture & decisions

### A1. `review/claude/option-j-seated.md`

- L1–6：自称「唯一权威描述」、旧名作废 — 与 D-027 一致。
- L31–43：三条不变量（完整 / 反力不经 H2 / 供电不经软件）— 内部自洽。
- L56–63：相对 D+G 唯一实质变化 = 承力改螺钉；并正确指出必须新增压模块壳体足的压脚，否则违反不变量 ②。
- **跳跃 / 过期阻断（G2-01）**：L65–72 仍写「触点场差 19.5 mm、两段完全不重叠」并指向 `CONFLICT-pogo-field.md`。  
  **本机对照（2026-09-23 JST）**：
  - OpenSCAD ECHO `module_board.scad`：`DOCK_PIN_FIELD_X0 = -34.405`，`Z0 = 2.75`，`Y = -24.095`；列 X `[-34.405, -31.865, -29.325, -26.785]`。
  - `dock_shell.scad:91,97`：`DOCK_PIN_FIELD_X0 = -34.405`，`Z0 = 2.75`。
  - `check_cross_branch.py` 对两 worktree：**EXIT 0**，含 `DOCK_PIN_FIELD_*` 等值。  
  → Option J 文内阻断项与当前 mech 分支**不同步**；CONFLICT 文档仍保留旧 2×8 / −45.485 vs −26.00 表（`_wt-mech-dock/.../CONFLICT-pogo-field.md:15`）。
- **缺失 ASSUMPTION 显式清单**：全文几乎不挂 `AS-*` ID（仅叙事指向 MATING / CONFLICT）。螺钉绝对坐标「待触点场心」与 D-026「待回填」一致，但 Option J 未声明 AS-11 / AS-31-mm-3（J1 本体深）/ RETENTION 实测等开放假设。

### A2. D-025 / D-026（含 `0d18b5c`）vs TDS

- `0d18b5c` **是** freeze 祖先（`git merge-base --is-ancestor` = yes）。
- TDS 抽取（`pdftotext`）：Elongation at Break **4.27 %**；Flexural Modulus **5003 MPa**；HDT **53 ℃（0.45 MPa）**；Continuous Service Temperature **N/A**。与 `docs/DECISIONS.md:384–385`、`mechanical/MATERIALS.md` 表一致。
- PDF SHA-256 `2e1393c7…ba22c3` 与 MATERIALS.md 登记一致。
- D-025「模量约纯 PLA 的 1.5～2 倍」：相对常见纯 PLA 弯曲模量 ~2.9–3.6 GPa，5003/3200≈1.56，**数量级可支持**；非 TDS 原句。
- D-026 修订（四条→三条，废弃「单一材料」理由）在决策正文与 MATERIALS 修订说明中**一致**，诚实。
- **G2-02（HIGH）**：D-026 明文「底座侧用 M2 **黄铜热熔螺母**，**不得自攻入 PLA-CF**」（`docs/DECISIONS.md:385,462`）。  
  当前 `_wt-mech-dock/.../dock_shell.scad:223–226,249,796–797` 实现为 **M2 自攻**进 PLA-CF 打印柱（`BOSS_ID = 1.70`），并自承抗拔力未知、`RETENTION_N=30` 为设计目标。→ **决策与实现冲突**。
- **G2-03**：`MATING.md` 第 4 节仍以卡扣闭环 / `F_catch≥30 N` / MD-02 卡扣坐标为主（例 L150–168, L361–364, L412）；D-026 要求「第 4 节整个力闭环须重做」——**未在本 SHA / mech-module tip 完成**。

---

## B) Contact field ruling

### B1. `hardware/RULING-j2-4x4-pinout.md`

- 冻结构成：5V×2 + GND×4 + KEY×10；SDA/SCL 移出（L47–55）。与 `check_j2_mismate.py` 输出版图一致。
- I1/I2 不变量与桥接机理 R=1.45 > 半间距 1.27：本机 mismate 复现相同数字。

### B2. vs ICD-0.2-DRAFT.md **on THIS SHA**

- ICD §3.1 仍写 **2 行 × 8 列**（L112–114）；§3.2 仍列 SDA/SCL 在列 8（L120–127）。
- PINMAP 修订 c（module-board 分支）自述：「ICD 第 3.2 节 2×8 表已作废；回填前 PINMAP §4 为唯一权威」。  
  → **ICD 与裁定/机械/PINMAP 三方漂移（G2-04）**。

### B3. GPIO14 = A0 → 11 not 12

- `CORRECTION-20260922-gpio-count.md` 主张成立。
- 证据：`LEFT_SLOT.md:18`「GPIO14 … 专用；不得接按键」；`:30`「保留 GPIO14 后余 **11** 根」。
- BSP：`subboard.h:24–26` left GPIO14=0 → 0x50；`subboard.c:59` `{GPIO_NUM_14, GPIO_NUM_39}` comment EEPROM A0。  
  → 更正文件与 D1/BSP **一致**（G2 不另开 finding；记为 verified）。

---

## C) Three machine gates（本机）

Worktree 路径：
- `--module _wt-mech-module/mechanical/module-board/module_shell.scad`
- `--dock   _wt-mech-dock/mechanical/dock-shell/dock_shell.scad`

### C1. `check_cross_branch.py` → **EXIT 0**

```
模块侧给出 26 个键，底座侧给出 26 个键
✓ 全部通过：16 条等值、6 条包含、1 条供需关系
```

### C2. `check_fit_geometry.py` → **未得官方干净 EXIT 0**

- 官方整脚本在「底座 ∩ 模块总成落入通道」OpenSCAD 求交上 **>15 min 无输出**（CPU ~100%，无 STL）；已中止。
- 按脚本同源 `CASES` **逐案**复跑（官方 empty/solid 判据；扫掠案 timeout=120s，其余 90s），结果：

| 结果 | 项 |
| --- | --- |
| ✓ empty/solid 符合 | 12 项（含终位 Mosaico 空、Mosaico 扫掠空、模块∩Mosaico 空、上压框∩Mosaico 空、螺柱∩键/板空、电池相关空、下沉硬限位非空、压框下移压到模块非空） |
| ✗ FAIL | **上压框 ∩ 模块（名义间隙）** → solid（4 verts）；**上压框沿 −X 偏 0.30 ∩ 模块** → solid（4 verts） |
| TIMEOUT | **底座 ∩ 模块总成落入通道**（>120s） |

→ 几何闸门 **不能记绿**。名义上压框已与模块求交非空，与「名义间隙 empty」意图矛盾（**G2-05**）。Timeout 案证据不全，不伪称通过。

### C3. `check_j2_mismate.py` → **EXIT 0**

关键观察（脚本 stdout）：
- R=1.450；半间距=1.270；桥接成立。
- F（未钳位 5V→GPIO）最小 ‖δ‖=**3.874 mm**；E4 腔体内 **0** 起 → 冻结表 F 通过。
- S（5V↔GND，含 G04）最小 ‖δ‖=**1.090 mm**；对 E2/E3 **够得到**；脚本明确：  
  **「Grok G04 成立（ICD 3.3『无损』的措辞必须撤回）」**。
- D4（封装旋转/镜像）Δ=0 即触发，脚本「只报不挡」。

---

## D) G04 / G05 关闭核验（批判 Claude 声称）

### D1. G04 — **ICD 上未关闭**

- Claude / next-session 称「本轮已关闭 G04（…『无损』必须撤回）」。
- **本 SHA ICD** `hardware/ICD-0.2-DRAFT.md:143–145` 二级表仍写：
  - X+1：**无损**
  - **X−1：无损**
  - Z 错一行：**无损**
- RULING `hardware/RULING-j2-4x4-pinout.md:189,203`：判定 G04 **成立**；关闭动作是把「无损」改为依赖 AS-11、并进 G6 禁测 — **该动作未落到 ICD 文件**。
- mismate 实跑 S=1.090 mm 落在 E2/E3 内，与 RULING 一致。  
→ **G04 finding 仍有效；「已关闭」不成立。**（G2-06）

### D2. G05 — **闸门层关闭 / ICD 层未关闭**

- RULING L205–215：用完备约化穷举关闭 G05（对角/多列/半格桥接）。`check_j2_mismate.py` EXIT 0 支持该技术关闭。
- ICD §3.3 仍只列 ±1 列、错一行、180°（旧 2×8 语境），**无**穷举声明，也**无**更新后的 DOCK_X_TOL 排除表述。  
→ 对 **4×4 冻结表**，枚举闸门可视为 G05 技术关闭；对 **权威 ICD 文本**，G05 **未关闭**。（G2-07）

---

## E) G01–G03, G06–G08 on this SHA

对照 R0 `d6cbca3:review/grok/R0/REPORT.md`：

| ID | R0 要点 | 本 SHA 观察 | 状态 |
| --- | --- | --- | --- |
| G01 | pinmap.h 焊盘注释 vs PINMAP | freeze 上 `dock_handle_pinmap.h:41–80` 仍写 A3/A4/…；验收句 L28 仍「A3=KEY_UP … B6=KEY_Y」。PINMAP 修订 c 用 `J2.3A` 等新名，并说「只需改注释」。宏值与 KEY→GPIO 未变。 | **注释侧未关**；「映射未动故自然关闭」只覆盖宏值半边（G2-08） |
| G02 | 「2026-09-20 版」戳过期 | 同文件 L7 仍写 2026-09-20；PINMAP 已修订 c（2026-09-22） | **未关** |
| G03 | AS-28 eFuse 不能分 1.2 vs 1.2.1 | `ASSUMPTIONS.md` AS-16/AS-28 仍 OPEN，措辞未按 R0 建议收紧 | **仍开** |
| G06 | AS-31-* 待吸收 | `ASSUMPTIONS.md` §3 仍「待吸收」 | **仍开** |
| G07 | 未 IDF 编译 | `firmware/dock_handle/README.md:12,195,270` 仍明确未 `idf.py build` | **仍开** |
| G08 | WP 默认 ICD vs 模块板 | ICD:207 默认写保护；`PROGRAMMING.md:53–60` 仍标冲突 / AS-31-eeprom-4 | **仍开** |

---

## F) Consistency sweep spot-check

文档声称 40 不一致 / 22 阻断（写于旧并行态）。对 **当前 mech tips** 抽样：

1. **触点场 X0 差 19.5 mm**（sweep #1 / Option J）— **几何上已对齐**（两边 −34.405；cross-branch 绿）。**文档（Option J / CONFLICT）未改** → 文档过期，非现存几何阻断。
2. **DOCK_COLS/ROWS** — 两边均为 4（module_board:120–121；dock_shell:86–87）— 已同步。
3. **焊盘 Ø1.8 vs Ø2.0** — SCAD `DOCK_PAD_D=2.0`；`origin/claude/design-d/module-board` netlist 仍见 `PAD-ARRAY-…-D1.8` / AS-31-mb-3 Ø1.8 注释 — **跨分支硬件文件阻断仍可能真实**（G2-09）。
4. **保持力方案互斥** — dock 已改上压框+螺钉；MATING 仍卡扣叙事 — **半修复 / 文档欠同步**（连到 G2-02/G2-03）。
5. **RETENTION 30 N** — dock 自承设计目标、无实测 — 与 next-session「必须关的事 #2」一致，**仍开**。

---

## 闸门与声称对照（一句话）

| 声称 | 观察 |
| --- | --- |
| 「三道机器闸门全绿」 | cross ✓；mismate ✓（但自承 G04）；**fit 非绿**（2 fail + 1 timeout） |
| 「G04 已关闭」 | **否** — ICD 仍「无损」 |
| 「G05 已关闭」 | 闸门/穷举 **是**；ICD 文本 **否** |
| 「G01/G02 自然关闭」 | 宏值是；**注释/版本戳否** |
