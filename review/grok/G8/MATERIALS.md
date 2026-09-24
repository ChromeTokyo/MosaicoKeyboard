# G8 已读范围

日期：2026-09-24。只读。没有把下列设计源改写入本分支。

| 材料 | 版本 | 用途 |
| --- | --- | --- |
| PR #53 头上的 `check_j2_contract.py`、`test_check_j2_contract.py`、`J2_CONTRACT_REPORT.md` | `85c1fb896ca32e9c256827e18b5ae165391d4e88` | 被审检查器、回归与作者复现说明 |
| 同头的 `docs/TASK_BOARD.md`、`docs/handoffs/chrome.md` 增量 | 同上 | 确认没有改设计源，只登记 IN_REVIEW |
| `hardware/module-board/PINMAP.md` | `94e393c55328cedca387affc7dd21aa316603b9c` | §0b、§2、§4.1–§4.3、§5.2、§5.3 |
| `hardware/module-board/netlist.yaml` | 同上 | `h2_contract`、`J2`、`J3`、`DOCK_5V`／`DOCK_GND`／`DOCK_SDA`／`DOCK_SCL` |
| `hardware/module-board/check_netlist.py` | 同上 | 旧硬编码 `ICD_J2`、`PINMAP_J3`；实跑退出 0 |
| `review/chrome/D1-module-interface/LEFT_SLOT.md` | `96fd823e93f264280207eb34b7a97e139ace7378` | 20 针表与「可作直接按键输入」 |
| `review/grok/G3/REPORT.md` 中 G3-07 与 HOLD 段 | 审查分支 `grok/g3-d2d3-gates-review`（未合入 main） | 对照既有 4×4／2×8 记录 |
| `review/grok/G2/REPORT.md` 的结论段 | 审查分支 `grok/g2-consistency-review` | 确认本 PR 不关闭 G2 HOLD |
| `docs/DECISIONS.md` D-023、D-024 | `origin/main` | 角色与模型 ID 口径 |

未读作本结论依据：模块板 CAD／SCAD、底座 EDA、G2 几何闸门的重新运行、实物。§4.2 的 X／Z 只做了表内减法，用来确认脚本没有读取这两列。
