# G3 资料边界

本文件只列本会话实际打开过的对象。未打开的不算已复核。

## 已读

| 对象 | SHA / 位置 | 用途 |
| --- | --- | --- |
| PR #51 元数据与 diff | 头 `caa29c2ddb0068cc6b8169cf73cfde9670e27677`，基线 `96fd823e93f264280207eb34b7a97e139ace7378` | 文件清单、作者、draft 状态 |
| PR #50 元数据与 diff | 头 `dea6c8fdace4cf74b35596cb0b4bf97947c6affb`，基线 `3eb5cf8a28d1e2bfafbf2cbda118cb986500e541` | 闸门补丁 |
| `review/chrome/D2-eeprom/TECHNICAL_REVIEW.md` | #51 头 | D2 结论 |
| `review/chrome/D2-eeprom/SUPPLY_CHECK.md` | #51 头 | 料号表述 |
| `review/chrome/D2-eeprom/evidence/SUPPLY_SOURCES.json` | #51 头 | 哈希声明 |
| `review/chrome/D2-eeprom/evidence/AT24C02D-Microchip.pdf` | #51 头，26 页 | 8871F 文本 |
| `review/chrome/D3-power/TOPOLOGY_REVIEW.md` | #51 头 | 八态与数值意见 |
| `review/chrome/T20-takeover/AS31_J1_SPEC.md` | #51 头 | J1 尺寸声明 |
| `review/chrome/T20-takeover/D4_PREPOWER_CONTINUITY.md` | #51 头 | 通断表 |
| `review/chrome/T20-takeover/PROJECT_STATE_20260923.md` | #51 头 | 项目快照 |
| `review/chrome/T20-takeover/sources/C9144_BOOMELE.pdf` | #51 头，1 页 | 渲染 + OCR |
| `review/chrome/T20-takeover/sources/C124406_Ckmtw.pdf` | #51 头，1 页 | 渲染 + OCR |
| #51 对 `docs/DESIGN_STATUS.md`、`docs/INTERFACE_CONTROL.md`、`docs/TASK_BOARD.md`、`docs/handoffs/chrome.md`、`review/chrome/D1-module-interface/LEFT_SLOT.md` 的 diff | 相对 `96fd823` | 确认只加问题行和未冻结段落 |
| `hardware/eeprom/PROGRAMMING.md` | `main` `96fd823` | WP 第 7.5 节、0x00–0x85 |
| `hardware/eeprom/` 工具与 `SHA256SUMS` | 同上，本机执行 | 17 页写 |
| `hardware/ICD-0.2-DRAFT.md` 第 143–145 行 | `main` `96fd823` | 「无损」仍在 |
| `hardware/dock-board/POWER_TOPOLOGY.md`、`POWER_BUDGET.md` | `8068ce2ddde42f81a64fd022a1529dc824a6ec4c` | 电阻、ILIM、5.25 V |
| `hardware/module-board/PINMAP.md`、`netlist.yaml` | `94e393c55328cedca387affc7dd21aa316603b9c` | 4×4 表与 2×8 网 |
| `hardware/check_fit_geometry.py`、`hardware/check_cross_branch.py` | `3eb5cf8` 与 `dea6c8f` | 假绿复现与补丁 |
| `hardware/test_check_gates_fail_closed.py` | `dea6c8f` | 8 项测试，本机跑过 |
| `docs/DECISIONS.md` D-026 | sweep `3eb5cf8` | 确认 #50/#51 未改决策 |
| `review/grok/G2/REPORT.md` 结论表 | PR #49 头 `3b3ad30` | HOLD 清单对照，不重做 G2 |
| `cursor-cloud` `run-info` | 本会话 | 模型 ID |

## 未读 / 未跑

- 用户给出的 `e8ecde65…` 与 `edf43c63…`：fetch 后不是合法对象
- 嘉立创商品页 HTML（仓库里没有快照字节）
- Microchip、TI、USB-IF 官网的重新下载
- AT24C02C 原厂手册
- 真实 OpenSCAD、真实 `.scad` 几何、`check_j2_mismate.py` 的再执行
- 实物通断、烧录、ESP32-S31 编译
- Hiro 本轮没有新的 H1–H4 报告可对照；不把 GitHub 显示名当作复核记录
