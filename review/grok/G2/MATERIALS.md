# G2 MATERIALS — 读了什么 / 没读什么

**Reviewer:** Grok EspBot（Cursor executor subagent）  
**Model ID:** 未由可核验接口暴露（D-024）  
**Role:** D-023 第二道独立复核（READ-ONLY on design；仅写本目录与 `docs/handoffs/grok.md`）  
**Freeze SHA:** `3eb5cf8a28d1e2bfafbf2cbda118cb986500e541`（分支 `grok/g2-consistency-review`，与 `sweep/consistency-20260921` tip 同 SHA）  
**Review date:** 2026-09-23 JST  
**Status of package:** IN_REVIEW

## 工作树 / 对照树（只读引用）

| 路径 | SHA / 说明 |
| --- | --- |
| 仓库根（本分支） | `3eb5cf8a28d1e2bfafbf2cbda118cb986500e541` |
| `_wt-mech-module` ← `origin/claude/design-d/mech-module` | `42172f77f04b371c5652f3e982deb07b551c9d83` |
| `_wt-mech-dock` ← `origin/claude/design-d/mech-dock` | `999ee0d20b54ff3d6dcf67297de0088a742a99a5` |
| R0 报告 | `origin/grok/r0-design-review:review/grok/R0/REPORT.md`（blob `cad5c089…`；提交 `d6cbca3` 2026-09-21） |
| PINMAP 对照 | `origin/claude/design-d/module-board:hardware/module-board/PINMAP.md`（fetch 时 tip 前进到含修订 c；用于对照，不改本 freeze） |

未 chase 移动的 remote tip 之外，本轮只为闸门拉取了上述 mech 分支 worktree，以及 R0 / module-board 只读对照。

## 已读（实际打开或等价抽取）

### 交接 / 决策
- `docs/handoffs/next-session.md`（全文）
- `docs/DECISIONS.md` D-022…D-027 与 D-026 详述／0d18b5c 修订段（`0d18b5c` 是本 freeze 祖先）
- `review/claude/option-j-seated.md`（全文）

### 触点场 / ICD / 更正
- `hardware/ICD-0.2-DRAFT.md`（重点 §3.1–3.3、§7.1 WP、版本历史）
- `hardware/RULING-j2-4x4-pinout.md`（全文；含 §4 G04/G05）
- `hardware/CORRECTION-20260922-gpio-count.md`（全文）
- `hardware/CONSISTENCY-SWEEP-20260921.md`（全文结构 + 阻断项抽样）
- `hardware/mismate-evidence/README.md`
- `review/chrome/D1-module-interface/LEFT_SLOT.md`
- BSP 证据：`…/bsp/…/subboard.h`、`subboard.c`（GPIO14=A0）、`mosaico_module_mgr/README.md`

### 机械 / 材料
- `_wt-mech-module/.../module_board.scad`、`module_shell.scad`、`MATING.md`（抽样）
- `_wt-mech-dock/.../dock_shell.scad`、`CONFLICT-pogo-field.md`（抽样）
- `_wt-mech-module/mechanical/MATERIALS.md`（TDS 表与修订说明）
- `references/materials/eSUN_ePLA-CF_TDS_V4.0_2023-07.pdf` → `pdftotext` 抽取；SHA-256 `2e1393c7ac594c194ded636b99a2c889e6815a30e6e48060f1762dd160ba22c3`（与 MATERIALS.md 登记一致）

### 固件 / 假设 / EEPROM
- `firmware/dock_handle/include/dock_handle_pinmap.h`
- `firmware/dock_handle/README.md`（未编译声明）
- `hardware/ASSUMPTIONS.md`（AS-16/28、§3 待吸收 AS-31）
- `hardware/eeprom/PROGRAMMING.md` §2.1 WP

### R0
- `origin/grok/r0-design-review:review/grok/R0/REPORT.md`（G01–G08 与摘要）

### 闸门脚本（本机实跑）
- `hardware/check_cross_branch.py`
- `hardware/check_fit_geometry.py`（官方整脚本曾挂在重扫掠；改为逐案 + 超时复跑，见 EVIDENCE-NOTES）
- `hardware/check_j2_mismate.py`（完整跑通，exit 0）

## 未读 / 未跑（明确边界）

- **未**领取或审阅 V0 auditor package
- **未**编辑 ICD / 设计文件 / 其他 review 目录
- **未** push、**未**开 PR、**未** merge
- 未完整审计四个 `claude/design-d/*` 的全部 PCB netlist／BOM 差异（仅 spot-check pad Ø 与 PINMAP 头）
- 未跑 `hardware/mismate-evidence/*.py` 竞争脚本（只读 README；常驻闸门是 `check_j2_mismate.py`）
- 未做 ESP-IDF / 真机编译（G07 仍开放）
- 未做任何实物测量（卡尺／推拉力／AS-11）
- `docs/handoffs/grok.md` 本轮前不存在；由本包新建
- Hiro H1–H4 包：未读、不替代

## 环境备注

- 本 Linux box 初始无 `openscad`；审查中安装了 Debian `openscad 2021.01-8` 后方可跑几何闸门。
- Mac 路径 `/private/tmp/wt-mech-*` 不存在；用仓库内 `_wt-mech-module` / `_wt-mech-dock` 代替。
