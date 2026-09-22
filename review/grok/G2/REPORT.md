提案 · 未冻结 · 由 Grok 独立复核（实际模型 ID 未由可核验接口暴露）起草 · 建议 HOLD 不合 main · 不得据以制造

# G2 Independent Consistency Review — REPORT

| Field | Value |
| --- | --- |
| Reviewer | Grok EspBot（D-023 第二道独立复核） |
| Model ID | **未由可核验接口暴露**（D-024；不猜填） |
| Freeze SHA | `3eb5cf8a28d1e2bfafbf2cbda118cb986500e541` |
| Branch | `grok/g2-consistency-review`（与 sweep tip 同 SHA；不 chase remotes） |
| Date | 2026-09-23 JST |
| Package status | **IN_REVIEW** |
| Verdict | **CHANGES_REQUIRED** |

> 本包**不**替代 Hiro H1–H4；**不**批准制造；**不**自动合并；**不**领取 V0 auditor package。  
> 证据不全处（fit 扫掠 timeout、无实物）一律不记 PASS。

---

## 1. Executive verdict

**CHANGES_REQUIRED**（证据足以否定「可合 main / 闸门全绿 / G04 已关」；尚不足以对整机几何给 PASS）。

| Gate | Observed |
| --- | --- |
| `check_cross_branch.py` | **EXIT 0**（16 EQ + 6 FIT + 1 GE） |
| `check_fit_geometry.py` | **非绿**：2× FAIL（上压框∩模块名义及 −0.30X）；1× TIMEOUT（模块总成落入通道 >120s）；12× 个案符合。官方整脚本曾在同扫掠案挂死 >15 min |
| `check_j2_mismate.py` | **EXIT 0**；F 安全成立；**S/G04 在 E2/E3 内会触发**；脚本自述须撤回 ICD「无损」 |

**Merge-to-main（Grok 二线视角）：建议 HOLD。**  
条件未满足前不要合入：至少（1）ICD §3.1–3.3 回填 4×4 并撤回「无损」；（2）fit 闸门对全部 CASES 得官方 EXIT 0（含扫掠）；（3）D-026 热熔螺母 vs dock 自攻冲突消解；（4）MATING 力闭环按 D-026 重写或显式废止卡扣条款；（5）G01/G02 注释与版本戳更新。即便到时，仍须 Hiro 批次与用户侧四件（D4 流程、RETENTION 实测、公差链、AS-31-mm-3 规格书）——本复核不放行打样。

---

## 2. Findings

### G2-01 — Option J / CONFLICT 触点场「19.5 mm 阻断」对当前 mech 几何过期  
**Severity:** MEDIUM（文档误导合并判断）  
**Evidence:** `review/claude/option-j-seated.md:65–72`；`_wt-mech-dock/.../CONFLICT-pogo-field.md:15` 仍 −45.485 vs −26.00。本机 ECHO 两边 `DOCK_PIN_FIELD_X0=-34.405`；`check_cross_branch` EXIT 0。  
**Ask:** 更新 Option J §6 与 CONFLICT 状态（已收敛 / 历史记录），或明确「文档冻结于旧 tip」。

### G2-02 — D-026「禁止自攻入 PLA-CF」vs `dock_shell` M2 自攻实现  
**Severity:** HIGH  
**Evidence:** `docs/DECISIONS.md:385,462`；`dock_shell.scad:223–226,249,796–797`（`BOSS_ID=1.70` 自攻底孔；RETENTION 30 为设计目标）。  
**Ask:** 改热熔螺母几何 **或** 修订 D-026 并给出自攻+PLA-CF 的原厂/实测依据（目前无）。

### G2-03 — D-026 要求重做的 MATING 力闭环仍为卡扣叙事  
**Severity:** HIGH  
**Evidence:** `docs/DECISIONS.md:385`「MATING.md 第 4 节整个力闭环须重做」；`MATING.md:150–168,361–364,412` 仍 `F_catch`/MD-02 卡扣。  
**Ask:** 按螺钉闭环重写 §4 / MD-*，删除或降级卡扣条款。

### G2-04 — ICD §3 仍为 2×8 + SDA/SCL；与 RULING / 机械 / PINMAP 修订 c 漂移  
**Severity:** HIGH（接口权威源）  
**Evidence:** `ICD-0.2-DRAFT.md:112–127`；`RULING-j2-4x4-pinout.md:47–55`；PINMAP 修订 c 自述 ICD 3.2 已作废。  
**Ask:** 回填 ICD 3.1–3.3（4×4、GND×4、SDA/SCL 出场），或正式声明临时权威为 PINMAP§4 + RULING（并改 ICD 页眉）。

### G2-05 — `check_fit_geometry`：上压框与模块在名义位求交非空  
**Severity:** HIGH（形状级；变量闸门抓不到）  
**Evidence:** 逐案复跑：`上压框 ∩ 模块（名义间隙）` → solid 4 verts；`上压框沿 −X 偏 0.30 ∩ 模块` → solid 4 verts。同脚本「下移 0.10 必须压到」为 solid（符合）。  
**Ask:** 修 `top_frame()` / 模块顶面间隙至名义 empty；重跑官方脚本至 EXIT 0。扫掠案须能在合理时间内完成或改算法，否则闸门不可操作。

### G2-06 — G04 **未**在 ICD 关闭；「无损」仍在；mismate 确认 S 可达  
**Severity:** HIGH（安全措辞）  
**Evidence:** `ICD-0.2-DRAFT.md:144`「X 方向 −1 列 … **无损**」（143/145 同行仍「无损」）；`RULING…:189,203`；`check_j2_mismate` S_min=1.090 mm ∈ E2/E3。  
**Ask:** 按 RULING 关闭动作改 ICD；G6 增错位带电禁测；AS-11 关闭前不放行带电插接。**拒绝采信「G04 已关闭」。**

### G2-07 — G05：穷举闸门可关技术项；ICD 枚举仍旧  
**Severity:** MEDIUM  
**Evidence:** RULING §4 G05 + mismate 完备约化 EXIT 0；ICD §3.3 仍仅 ±1/错行/180°。  
**Ask:** ICD 改为引用 `check_j2_mismate.py` 为二级防呆权威，删除过时情形表或整表按 4×4 重写。

### G2-08 — G01/G02 注释与版本戳在 freeze 固件上未更新  
**Severity:** LOW–MEDIUM（验收误导）  
**Evidence:** `firmware/dock_handle/include/dock_handle_pinmap.h:7,28,41–80`（2026-09-20；A3/A4…）。PINMAP 修订 c 明确「只需改注释」。宏值未变 — 「自然关闭」仅半真。  
**Ask:** 注释改 `J2.3A` 等；版本戳改修订 c。

### G2-09 — Sweep 抽样：模块板 netlist 焊盘 Ø 仍可能为 1.8  
**Severity:** MEDIUM  
**Evidence:** SCAD `DOCK_PAD_D=2.0`；`origin/claude/design-d/module-board` `netlist.yaml` 仍 `…-D1.8` / AS-31-mb-3 Ø1.8。  
**Ask:** 硬件分支与 SCAD/PINMAP 统一 Ø2.0 后再出 Gerber。

### G2-10 —（观察）闸门「全绿」声称与 fit 实况不符  
**Severity:** MEDIUM（过程）  
**Evidence:** `docs/handoffs/next-session.md:5`「三道机器闸门全绿」vs 本机 fit 非绿。  
**Ask:** 交接改写为实测 exit；CI 必跑三闸门。

### Verified non-findings（简记）
- GPIO14=A0 → 可直连按键 **11** 根：D1 + BSP 支持 CORRECTION 文件。
- D-025/D-026 TDS 数字（4.27 % / 5003 MPa / HDT 53 °C / CST N/A）与 PDF 一致；`0d18b5c` 修订在 ancestry 内。
- mismate F 免疫（3.874 mm，E4 内 0 起）在本机复现。

### 仍开放（R0，本轮未关）
- **G03** AS-28/eFuse；**G06** AS-31 吸收；**G07** IDF 编译；**G08** WP 默认。

---

## 3. Scope checklist（委托 A–F）

| 块 | 结论摘要 |
| --- | --- |
| A Architecture | Option J 不变量自洽；§6 阻断过期；D-026 与 dock/MATING 执行缺口 |
| B Contact field | RULING 冻结构成立；ICD 未跟；GPIO 更正成立 |
| C Gates | cross 0；fit 非 0；mismate 0（含 G04 警告） |
| D G04/G05 | G04 **未关**；G05 技术关 / ICD 未关 |
| E G01–G08 | G01/02 半开；G03/06/07/08 开；G04 开；G05 半关 |
| F Sweep | 旧 19.5 mm 几何已消、文档未消；Ø 与承力类仍值得挡 |

---

## 4. Merge recommendation（second-line）

**HOLD — 不要合并到 main。**

Ready-with-conditions 的最低条（仍不构成制造批准）：
1. ICD §3 与「无损」按 G2-04/G2-06 回填；
2. `check_fit_geometry.py` 官方 EXIT 0（G2-05 + 扫掠可完成）；
3. D-026 紧固件策略与 SCAD 一致（G2-02）；
4. MATING §4 与螺钉架构一致（G2-03）；
5. 作者不得自审（D-013）：须保留 Hiro 或本 G2 之后的独立签字；Grok 本包签字≠放行制造。

用户四件（D4 导通流程、RETENTION 实测、公差链重算、J1 规格书）仍在 next-session 列表上——Grok 二线 **不**因文档闸门变绿而关闭它们。

---

## 5. Artifacts

- `review/grok/G2/MATERIALS.md`
- `review/grok/G2/EVIDENCE-NOTES.md`
- `review/grok/G2/REPORT.md`（本文件）
- `docs/handoffs/grok.md`（G2 交接）

Mech worktrees used（只读）：`_wt-mech-module` @ `42172f7…`；`_wt-mech-dock` @ `999ee0d…`。
