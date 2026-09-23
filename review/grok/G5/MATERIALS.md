提案 · 未冻结 · 由 Grok 独立复核起草 · 不得据以制造

# G5 资料索引

本索引只说明本轮读过什么、能用来核对什么。被审文件里的尺寸与针位仍是待检主张。

冻结点：PR #56 头 `b15a0487f49010c3efdf75fe27ee62050fb59f48`，基线 `96fd823e93f264280207eb34b7a97e139ace7378`。

| 路径 | 在哪一版 | 本轮用它做什么 |
| --- | --- | --- |
| `hardware/ASSUMPTIONS.md` | #56 头，并与基线逐列比较 | 数 AS 行、状态、哪些列改过 |
| `hardware/ICD-0.2-DRAFT.md` | #56 头，并与基线比较 ME-D | 数 ME-D 行、冻结登记、残留测法用词 |
| `docs/TASK_BOARD.md`、`docs/handoffs/chrome.md` | #56 头 | 核对登记是否把 30 条仍写成 OPEN |
| `docs/MEASUREMENT_PROTOCOL.md` | 基线 `96fd823` | T14 第一轮边界（第 0～5、7 节，M06） |
| `docs/INTERFACE_CONTROL.md` | 与基线相同，本 PR 未改 | 确认本 PR 没有改这份现行 ICD；未把它当 D＋G 分册的替代 |
| `review/chrome/T14/MEASUREMENT_RECORD.md` | 与基线相同 | 只确认本 PR 未改记录表 |
| PR #55 头 `82df4c65` 的规程 | 只 `git grep` Q07/Q08 | 交叉编号。未审该 PR 全文 |
| `docs/TEAM_PLAN.md` G1 定义、`docs/DECISIONS.md` D-023/D-024 | 基线 | 复核角色与模型 ID 口径 |

未读作本轮证据：实物、原厂连接器图纸、BSP 源码、#55 记录表全文、Hiro 的审查意见。
