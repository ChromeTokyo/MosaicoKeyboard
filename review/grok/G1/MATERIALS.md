提案 · 未冻结 · 由 Grok 独立复核（实际模型 ID 未由可核验接口暴露）起草 · 待主控定稿 · 不得据以制造

# G1 MATERIALS — 阅读范围与冻结基线

- 任务 ID：G1（EspBot/Grok 常设第二道独立复核，首轮独立证据包）
- 冻结 SHA（main tip，本轮不得追逐移动 main）：`96fd823e93f264280207eb34b7a97e139ace7378`
- 核对：`git rev-parse HEAD` → 同上；`## main...origin/main`
- 日期：2026-09-21（Asia/Tokyo）
- 写入范围（硬性）：仅 `review/grok/G1/` 与 `docs/handoffs/grok.md`
- **未取** V0 审查包 `docs/handoffs/claude-to-auditor.md` 作为审计输入（该包审 Grok/Hiro，须换模型族；本轮仅用其公开旁注「G04/G05 尚未整改」作对照线索，不以该包结论为据）

## 1. 已读（本轮）

### A — R0 发现闭环与转录比对
- `origin/grok/r0-design-review:review/grok/R0/REPORT.md`（真本，251 行）
- `review/audit/V0/APPENDIX-grok-r0-transcript.md`（主控转录件，68 行）
- `firmware/dock_handle/include/dock_handle_pinmap.h`
- `firmware/dock_handle/README.md`（§4 转抄表、§7.5／§12 编译限制）
- `origin/claude/design-d/module-board:hardware/module-board/PINMAP.md`（修订 b，2026-09-21；main 无此路径）
- `hardware/ICD-0.2-DRAFT.md` §3.3（约 L131–150）
- `hardware/ASSUMPTIONS.md`（AS-16／AS-28；§3 AS-31 待吸收；AS-01／AS-08 等）
- `hardware/eeprom/PROGRAMMING.md` §2.1（WP 默认冲突）
- `docs/DECISIONS.md` D-022／D-023／D-024
- `docs/handoffs/claude-to-grok.md`（R0 派发包，背景；未作本轮答题依据）
- `docs/handoffs/claude.md` 中提及 G07 的工具链旁注（仅对照）

### B — 机械 BUILD-LOG
- `mechanical/verification/BUILD-LOG-20260921.md`（PR #46 合入，commit `a6d87f2`）
- 检索：`git ls-tree`／`find`／全仓库 `*.scad` —— **冻结 SHA 上不存在** `mechanical/module-board/module_board.scad`（及 dock_shell／keycaps）
- 本机：`which openscad` → 不在 PATH；**未运行 OpenSCAD 编译**

### C — Chrome D1 二线抽查
- `review/chrome/D1-module-interface/README.md`
- `review/chrome/D1-module-interface/LEFT_SLOT.md`
- `review/chrome/D1-module-interface/BSP_AND_EEPROM.md`
- `review/chrome/D1-module-interface/DOCUMENT_BOUNDARIES.md`
- `review/chrome/D1-module-interface/evidence/bsp/SOURCE_INDEX.json` + 12 文件哈希复算
- `.../evidence/bsp/.../subboard.c`、`subboard.h`、`esp_mosaico.h`（I²S 宏）
- `.../evidence/user_guide_v10.rst`（H2 表，约 L608–686）

## 2. 明确未读／未做（避免越权或串台）
- **未读** `docs/handoffs/claude-to-auditor.md` 全文作为审计任务（仅知公开旁注）
- **未读** `review/hiro/H0/*`（不替代／不重审 H1；本轮 D1 标为 G1-D1-* 二线）
- **未编辑** `hardware/`、`firmware/`、`mechanical/`、`design/`、ICD
- **未推送、未开 PR**
- **未取得**仓库外 `esp_mosaico.c`（本轮不做 Q5 复算；G03 仅查 ASSUMPTIONS 措辞是否仍高估）
- **未编译**固件／OpenSCAD

## 3. 工具与环境
- `git`、`rg`、`python3`（SOURCE_INDEX 12/12 SHA-256 OK）、`Read`
- OpenSCAD：**缺失**
- `gh`：本环境不可用（PR #43 状态据分支 tip `f64f1e4`／R0 交接自述仍为 open）
