# 首批工作队列

状态基线：2026-09-20，按 GPT 统一负责硬件的第二次分工修订。负责人表示计划归属；除已在“领取记录”中登记的任务外，下表任务均未由对应平台实际领取，不代表 Agent 已经启动。Claude 是队列维护人；Chrome 的多个 READY 任务允许按优先级串行执行。

当前已领取：T01、T06、T13 由 Claude 会话领取，输入提交 `3d5a112`，分支 `docs/t01-lead-handover`；Chrome 已交 T02 待审，本轮优先 T14、接口草案与 T04 的 CoreBoard 子范围。详见文末“领取记录”。

| ID | 负责人 | 任务／交付 | 依赖 | 验收与复核 | 状态 |
| --- | --- | --- | --- | --- | --- |
| T01 | Claude | 接管主控，核实运行环境、各角色能力与分支，维护队列与决策记录，安排 Chrome 编写技术接口 | 阅读当前 main | 有版本化队列、文件归属与未知项；不把占位尺寸冻结 | IN_PROGRESS |
| T02 | Chrome | 验证 A0 在嘉立创 EDA 中导入、编辑、保存、导出与网络对应 | 当前 A0 | 报告实际结果，失败则记录可复现原因和修复方案；Claude 核对证据完整性 | IN_REVIEW（CHANGES_REQUIRED，PR #4；D-011证据完整性已核对，技术复核待Hiro） |
| T03 | Chrome | 验证参数化 CAD 工作流，核实官方模块尺寸，建立模块包络和机械未知项 | 当前需求 | 有可编辑源文件及可重建的导出；未知坐标不得填成已知；为 Hiro 接口审查备料 | READY |
| T04 | Chrome | 整理并核验 Mosaico 精确尺寸资料、器件原厂资料和嘉立创供应／工艺证据 | 当前候选 BOM | 来源链接、版本／日期、确认与未确认分开；辅助搜索可选，Chrome 对采用的证据负责 | IN_PROGRESS（CoreBoard 电源／I²C 子范围已交付；其余BOM／供应核验未完成） |
| T05 | Chrome | 对 Hiro 原 A0 独立电气审查，重点电源状态和 I²C 电平问题 | 当前 A0 与原厂资料 | 独立计算及逐项问题报告；先完成审查记录再修订；Claude 可补充跨模型质疑 | READY |
| T06 | Claude | **已改范围（2026-09-20）**：国内不设实物验收执行人，本任务改为“实物测量与日本端验收执行方案”，列出所需器材、能力与用户决策 | 用户供应与执行条件 | 明确需要的样品、器材、执行人及缺口；未采购或未到货不得标成落实 | IN_PROGRESS |
| T07 | Chrome | 根据审查形成电路修订版及计算／BOM，提出电气接口约束 | T02、T05，及相关 T04 证据 | 整理 Hiro H1 审查包；Claude 可补充跨模型质疑 | BLOCKED |
| T08 | Chrome 提交，Hiro 复核，Claude 记录 | 冻结共同接口，解决触点、板框、按键、电池与高度约束 | T03、T04、T07 相关参数及精确尺寸证据 | Hiro 独立接口审查；G1 证据齐全；Claude 记录版本 | BLOCKED |
| T09 | Hiro | H1：对 Chrome 修订版本独立复核电源与接口 | T07 冻结审查包 | 提交版本明确，逐项计算，输出 PASS／CHANGES_REQUIRED／BLOCKED | BLOCKED |
| T10 | Chrome | PCB 完整布局布线和制造审核输出 | T08、G2 通过 | Hiro H2 独立复核；未通过不输出生产放行 | BLOCKED |
| T11 | Chrome | 完成外壳、按键、尺寸链与装配，准备实际工艺样件 | T08；最终版本依赖 T10 | 源 CAD、STEP、装配图、检查与试装记录；Hiro H3 独立复核 | BLOCKED |
| T12 | Claude 协调，Chrome／Hiro 核验 | 集成制造包、出厂检查、发运与日本验收放行 | G3 后依次执行 G4、G5、G6 | 全部证据绑定版本；Hiro H4 审查；用户下单与寄送指示 | BLOCKED |
| T13 | Claude | 产品视觉方向和影响实体硬件的交互需求：按键语义、握持时屏幕方向、开孔需求 | 既定产品需求 | 提案与工程尺寸明确分开，Chrome 判断结构可实现性；不提前开发完整应用 UI | IN_PROGRESS |
| T14 | Chrome 出规程，用户执行，Claude 入库，Hiro 复核 | ESP-Mosaico 实物测量规程与执行：四触点位置与方向、模块包络与高度、开孔与接口可达性；含所需器材清单与照片留证要求 | 实物到货（预计 2026-09 下旬，日本） | 规程可由非工程背景者独立执行；测量结果含原始照片与数据；由测量导出的接口约束经 Hiro 复核后方可进入 G1 | IN_REVIEW（规程与记录表已交付待审；实物执行待到货，不能标DONE） |
| T15 | Claude | 日本端验收、备件与发运方案：用户可独立执行的测试步骤框架、备板与备件策略、可维修性要求、电池运输合规待确认项 | T06、放行链变更 | 与 TEAM_PLAN G4–G6 一致；阈值与仪器要求留给 Chrome 填入，不自行设定 | READY |
| T16 | 用户执行，Chrome 判定，Claude 记录 | **已改写（2026-09-20）**：`MOSAICO.3mf` 来源未核实且很可能是裸板外壳而非整机壳，原「相减得装配间隙」前提不成立（见 `review/claude/3mf-analysis.md`）。改为：打印该件并与实物比对，判定它对应裸板还是整机，据此决定其参考价值；整机尺寸以卡尺直接实测为准 | 用户 3D 打印机（已具备）；实物到货 | 比对结论有照片与实测数据支撑；不得由该件推出任何整机配合尺寸 | READY（打印可先做，比对待实物） |
| T17 | Claude 提案，用户打印试握 | 产品体量模型：按 T13 的形态方向出可打印的握持体量件，验证长条形、握把深度、按键落点与拇指可达范围 | T13 视觉与交互方向 | 只验证人机与手感，不含任何硬件配合尺寸；结论回写 T13 | READY |

| H0 | Hiro | 设计前提变更专项复核：(a) 结论 1 降 derived 是否恰当 (b) REVERSAL 是否成立 (c) Chrome D1 左槽合同独立复核 | 审查包 `docs/handoffs/claude-to-hiro.md`、资料索引 `review/hiro/H0/MATERIALS.md`（PR #26） | 输出 PASS／CHANGES_REQUIRED／BLOCKED，证据不全不得 PASS；报告 `review/hiro/H0/REPORT.md` | READY（待用户唤醒 Hiro 领取） |
| T20 | Claude（提案），Hiro 复核 | 方案 D＋G 全套设计提案：ICD-0.2 分册、ASSUMPTIONS 总表、G6 测试计划（已合入 PR #27）；模块板／底座主板电气、EEPROM 镜像、手柄驱动固件、参数化机械（进行中，各在 `claude/design-d/*` 分支） | D-017 主循环第①步 | 全部标 ASSUMPTION；不生成嘉立创 EDA JSON；每文件头有提案声明；四路对抗复核后合入 | IN_PROGRESS |

`READY`：可领取；`IN_PROGRESS`：有明确会话／分支正在执行；`BLOCKED`：前置条件未满足；`IN_REVIEW`：有交付待审；`DONE`：验收通过。领取时增加分支、输入提交号与交接路径，完成时补充 PR／证据链接。

T03 的工具验证和空间研究可先开展；精确机械数据缺失时只能保留草案。Chrome 可以在独立任务中交替研究 T10 与 T11，但同一源文件只允许一个编辑会话，最终装配和制造输出仍受冻结版本约束。应用 UI／固件完整设计与实现待硬件稳定后另建任务。

Cursor／Grok 默认没有领取任务，不是 T04 或其他核心工作的必需前置。不得为节省等待时间把 T03、T07、T08、T10、T11 或强制审查移交给它们。

## 领取记录

领取时登记输入提交号、分支、文件范围与交接路径；完成时补充 PR 与证据链接。未登记的任务视为未领取。

| ID | 领取人／平台 | 实际模型与档位 | 输入提交 | 分支 | 文件范围 | 交接路径 | 登记日期 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T01 | Claude 会话（Claude Code） | `claude-opus-5`，高推理档位 | `3d5a112` | `docs/t01-lead-handover` | `docs/OWNERSHIP.md`、`docs/DECISIONS.md`、`docs/handoffs/chrome.md`、`docs/handoffs/claude.md`、本文件 | `docs/handoffs/claude.md` | 2026-09-20 |
| T06 | 同上 | 同上 | `3d5a112` | 同上 | `docs/T06-DOMESTIC-EXECUTION.md` | `docs/handoffs/claude.md` | 2026-09-20 |
| T13 | 同上 | 同上 | `3d5a112` | 同上 | `docs/product/T13-PRODUCT-DIRECTION.md` | `docs/handoffs/claude.md` | 2026-09-20 |
| T02 | Chrome（Codex，系统标识 GPT-6） | 精确模型 ID 与档位未由可核验接口提供，Chrome 声明不猜填 | `3d5a112` | `chrome/t02-a0-eda-validation` | `review/chrome/T02/`、`tools/check_a0_static.py`、`docs/DESIGN_STATUS.md`、`docs/TASK_BOARD.md`、`docs/handoffs/chrome.md` | `docs/handoffs/chrome.md` | 2026-09-20，已交付，PR #4 |

`docs/TEAM_PLAN.md`、`CLAUDE.md`、`README.md` 指定主控使用 Claude Fable 5.1；本轮实际执行模型为 `claude-opus-5`，按 `docs/TEAM_PLAN.md` 第 1 节如实登记，记录见 `docs/DECISIONS.md` D-001，待用户确认是否同步修订文档表述。

T02–T05 的交接包在 `docs/handoffs/claude-to-chrome.md`。交接包存在只表示 Chrome 可以直接领取，不表示已开始工作。T03、T05 仍为 READY；T04 本轮仅领取 CoreBoard 接口证据子范围，其余供应与封装核验待继续。

**主控裁决 D-006（2026-09-20）：** `docs/handoffs/chrome.md` 曾出现两个互不相同的版本（主控派发包与 Chrome 自写的 T02 交接），属同一源文件双编辑者。裁决为分离职责：`docs/handoffs/chrome.md` 唯一归属 Chrome，登记自己的领取、进展日志与交接，主控不写入；主控派发包改名为 `docs/handoffs/claude-to-chrome.md`，Chrome 只读。Chrome 无需做任何合并。`docs/OWNERSHIP.md` 的 U-34 据此关闭。

### Chrome 本轮增量领取（2026-09-20）

| ID | 领取人／平台 | 实际模型与档位 | 输入提交 | 分支 | 文件范围 | 交接路径 | 登记日期 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T14＋接口草案（非 T08 冻结） | Chrome／Codex | `gpt-6-astra`（界面 GPT-6 Astra），`ultra`；用户于本会话确认，非运行时反查 | `25c4902` | `chrome/interface-control-draft` | `docs/MEASUREMENT_PROTOCOL.md`、`docs/INTERFACE_CONTROL.md`、`review/chrome/T14/`、本文件 Chrome 行、Chrome 交接 | `docs/handoffs/chrome.md` | 2026-09-20 |
| T04 子范围 | Chrome／Codex | 同上 | `25c4902` | 同上（串行统一录入接口文件） | `review/chrome/T04/`，限 CoreBoard 官方电气资料核验；不领取全 BOM 审核完成状态 | `docs/handoffs/chrome.md` | 2026-09-20 |

T14 本轮交付：[测量手册](MEASUREMENT_PROTOCOL.md)、[空白记录表](../review/chrome/T14/MEASUREMENT_RECORD.md)、[电气／机械统一接口草案](INTERFACE_CONTROL.md)、[修复顺序](../review/chrome/T14/REPAIR_ORDER.md)。初版技术内容提交 `423a357`；[PR #9](https://github.com/ChromeTokyo/MosaicoKeyboard/pull/9)，分支已同步 `1030776`，无接口冻结。T04 子范围证据见 [CoreBoard 核查](../review/chrome/T04/COREBOARD_INTERFACE_EVIDENCE.md)。

### Chrome 接续登记（Claude 限额后）

| ID | 领取人／模型 | 输入 | 分支／文件范围 | 状态与交接 |
| --- | --- | --- | --- | --- |
| T02/F03：Claude T18提案复核 | Chrome／`gpt-6-astra`、`ultra`（用户确认） | main `edb5301`；候选实现`56030b9`；未合入领取`94b30d5` | `chrome/t18-proposal-review`；`review/chrome/T18/`、Chrome交接、此登记 | IN_REVIEW；八项隔离观测完成，CHANGES_REQUIRED，见`review/chrome/T18/REPORT.md`；不代表T18/T19已采纳 |

| T14／T03：开箱视频接口版本核查 | Chrome／`gpt-6-astra`、`ultra`（用户确认） | 用户2026-09-20提供153.84秒视频＋main `edb5301` 官方证据 | `chrome/t18-proposal-review`，用户在接续期间追加；视频技术摘录、ICD／测量规程及记录表、设计状态风险提示、本人交接 | IN_REVIEW；六张摘图、对照报告及ICD／T14分流完成；到货版本待确认 |

上述Chrome接续复核与视频版本分流统一交付 [PR #12](https://github.com/ChromeTokyo/MosaicoKeyboard/pull/12)，待复核、未合并，不改变硬件放行状态。

用户于2026-09-20明确要求Claude恢复后验证本次发现；逐项入口见 [Chrome交接：待Claude复核](handoffs/chrome.md#待-claude-恢复后复核用户明确要求2026-09-20)。当前仍为待复核，未登记Claude通过。

### Chrome 第二批低额度领取（2026-09-20）

| 任务 | 平台／实际模型／推理档位 | 输入提交 | 分支 | 文件范围 | 状态／交接 |
| --- | --- | --- | --- | --- | --- |
| C1 → C2 → C3 → C4 → C5（严格串行） | Codex／`gpt-6-astra`／`ultra`（用户此前确认） | `37ccf53` | `chrome/h-low-quota-batch` | `review/chrome/H01/`、`H02/`、`H03-mcu/`、`H04-power/`；`docs/INTERFACE_CONTROL.md`；本人任务登记及`docs/handoffs/chrome.md` | C1 STOPPED（用户取消，部分证据保留）；C2 CANCELLED（未开始）；C3–C5 被 D1–D3 新派发替代；不修F01/F02、不改生成器、不做CAD/PCB |

### Chrome 改派：左槽方案 D（2026-09-20）

| 任务 | 平台／实际模型／推理档位 | 输入提交 | 分支 | 文件范围 | 状态／交接 |
| --- | --- | --- | --- | --- | --- |
| D1 → D2 → D3（顺序交付） | Codex／`gpt-6-astra`／`ultra`（用户确认） | `ff24626`（PR #21） | `chrome/h-low-quota-batch`（沿用分支，范围已改为D） | `review/chrome/D1-module-interface/`、`D2-eeprom/`、`D3-power/`；`docs/INTERFACE_CONTROL.md`适用范围；本人任务登记、Chrome交接及新问题状态 | D1 IN_REVIEW（[交付](../review/chrome/D1-module-interface/README.md)）；D2 IN_PROGRESS；D3 QUEUED。C1/C2已取消，H仅备份；不修F01/F02、不改生成器、不做CAD/PCB、不冻结接口 |

### 主控代为集成 Chrome 遗留工作（2026-09-20）

Chrome（Codex／`gpt-6-astra`）已于 2026-09-20 彻底耗尽额度下线。其 D1 已交付（[D1 接口合同](../review/chrome/D1-module-interface/README.md)，IN_REVIEW，待 Hiro 复核）；D2／D3 未完成，上表「D2 IN_PROGRESS；D3 QUEUED」是 Chrome 下线前的自述状态，现已停止推进。PR #12（T18 提案复核 CHANGES_REQUIRED、开箱视频版本核查）与 `chrome/h-low-quota-batch`（D1、H-01 中间资料、进展日志）由主控代为集成到 `integrate/chrome-leftovers`；集成只做合并与冲突解决，不改变 Chrome 的技术结论、T18 状态与任何硬件放行状态。

| ID | 领取人／平台 | 实际模型与档位 | 输入提交 | 分支 | 文件范围 | 交接路径 | 登记日期 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Chrome 遗留整合（PR #12 ＋ `chrome/h-low-quota-batch`） | Claude 主控（Claude Code） | `claude-fable-5-1`；推理档位未由可核验接口提供，不猜填 | main `6953715`；`chrome/h-low-quota-batch` `b44c728`；`chrome/t18-proposal-review` `009a488` | `integrate/chrome-leftovers` | 仅合并与冲突解决：`docs/MEASUREMENT_PROTOCOL.md`、`docs/INTERFACE_CONTROL.md`、`docs/TASK_BOARD.md`、`docs/DESIGN_STATUS.md`、`docs/handoffs/chrome.md`、`review/chrome/**`；`design/`、`references/` 相对 main 无改动 | 合并提交说明及本节 | 2026-09-20 |

### Chrome 2026-09-23 独立证据补充（与待审 PR #50/#51/#53 并行）

| 任务 | 平台／实际模型与档位 | 输入提交 | 分支 | 文件范围 | 状态／交接 |
| --- | --- | --- | --- | --- | --- |
| V1.2 左槽 pin17 输入边界与 J1 公母配合候选 | Codex／当前模型切换后的精确 ID 与档位未由可核验接口暴露 | main `96fd823`；官方 1.2.1+ 归档与厂家图纸 | `chrome/v12-input-j1-boundaries` | `review/chrome/T20-takeover/` 独立来源报告与必要证据；本人任务登记及 `docs/handoffs/chrome.md` | IN_REVIEW；[draft PR #54](https://github.com/ChromeTokyo/MosaicoKeyboard/pull/54)，只核官方/厂家可证事实与 unknown；不改电路/CAD/PCB，不自批 V1.2 供电额定或 J1 配对；待非作者复核。 |
