# 文件归属、编辑锁与未知项登记

基线提交：`3d5a112`。基线日期：2026-09-20。维护人：Claude（主控）。本轮实际模型：`claude-opus-5`，高推理档位。

本文的验收条件：第 2 节归属表覆盖 `git ls-files` 与 `git status --short --untracked-files=all` 列出的全部路径；第 3 节的「尚未创建」判断写明覆盖范围；第 4 节每条未知项有责任人与可执行的解除证据；全文不出现机械或电气数值。
本文的复核人：按 `docs/TEAM_PLAN.md` 由非作者复核，具体人选待主控指定，尚未指定。
本文的交接路径：`docs/handoffs/claude.md`（尚未创建，由 Claude 主控创建）。

**本文记录归属与状态，不构成任何硬件技术结论。** 文中不给出、不推荐、不冻结任何机械或电气数值（板框、孔位、间距、电流、阈值、公差等）。凡需要数值处一律写明由 Chrome 提交、Hiro 复核后填入。文件存在、脚本可运行、库已下载、计划已写入，都不等于电气正确、可生产或已验证。

本文是 T01 的核心交付之一，属 `docs/` 范围，由 Claude 主控维护。

## 1. 本文与 `docs/TEAM_PLAN.md` 第 2 节的关系

两份文件内容相邻，必须避免出现两份可各自漂移的责任表。暂行约定如下，尚未写入 `docs/TEAM_PLAN.md`，登记为 U-24。

| 事项 | 权威来源 |
| --- | --- |
| 角色职责边界、不承担的职责、放行规则 | `docs/TEAM_PLAN.md` 第 2 节 |
| 逐个文件／目录的权威负责人、类型、生成关系 | 本文第 2 节 |
| 某个文件当前是否被占用、由谁占用 | 本文第 2 节「当前编辑锁」列 |
| 任务领取记录与分支 | `docs/TASK_BOARD.md`「领取记录」 |
| 未知项与解除条件 | 本文第 4 节；硬件待解决项原文见 `docs/DESIGN_STATUS.md` |

本文第 2 节出现与 `docs/TEAM_PLAN.md` 第 2 节冲突的归属时，以 `docs/TEAM_PLAN.md` 为准，并由主控修订本文。

## 2. 归属表

类型取值：**设计源**（手写、可编辑、唯一权威）、**生成产物**（由设计源生成，不手改）、**参考缓存**（外部抓取，只读）、**文档**。

「当前编辑锁」记录的是**快照时刻的观测结果**，不是持续保证。

快照时刻：**2026-09-20 12:52 JST**，即本文最后一次整体重核的时刻，在该时刻执行了 `git fetch --all`、`git branch -r`、`git status --short --untracked-files=all` 与 `git ls-files`。本文的文件写入在该时刻之后一分钟内完成，写入期间未再重新取证。使用本节前必须重新执行这四条命令；**只执行 `git status --short` 查不出远端漂移**。

该时刻的本地未提交改动（全部已暂存，暂存动作不是本文作者执行的）：`AGENTS.md`、`docs/TASK_BOARD.md`、`docs/TEAM_PLAN.md`（已修改），`docs/DECISIONS.md`、`docs/OWNERSHIP.md`、`docs/REFERENCES-INVENTORY.md`、`docs/STATUS.md`、`docs/T06-DOMESTIC-EXECUTION.md`、`docs/handoffs/chrome.md`、`docs/product/T13-PRODUCT-DIRECTION.md`、`review/claude/official-evidence/` 下 4 个文件（新增）。`docs/` 下这些新增文件的抬头自述维护人为 Claude 主控；它们是否出自同一个会话不可从仓库核验。

**工作区在本文写作期间两次变化，均已按上述规则重核：** 12:46 时 `review/claude/official-evidence/` 出现 3 个未跟踪文件；12:52 时该目录增至 4 个文件，且全部本轮改动被另一方执行 `git add` 转为已暂存。两次变化中远端状态均未变。这两次变化的执行者不可从仓库核验。

远端状态（12:46 与 12:52 两次实测一致）：本地 `main` 与当前分支 `docs/t01-lead-handover` 的 tip 同为 `3d5a112`，该分支没有自有提交；`origin/main` 为 `4261fcb`，比输入提交多 2 个提交（`92cf2fb`、`4261fcb`，`git rev-list --left-right --count HEAD...origin/main` 输出 `0 2`）。**本轮的输入提交 `3d5a112` 不再是远端最新提交。** 另有远端分支 `origin/chrome/t02-a0-eda-validation`（tip `a6db65a`）尚未合入，见第 5.3 节。

### 2.1 顶层路径

| 路径 | 权威负责人 | 类型 | 生成关系 | 当前编辑锁 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `.gitattributes` | Claude 主控 | 文档（仓库配置） | 手写 | 空闲 | 含 `*.csv text eol=lf`，是 `design/` 两个 CSV 行尾归一化的来源 |
| `.gitignore` | Claude 主控 | 文档（仓库配置） | 手写 | 空闲 | 首条排除 `tools/python-packages/`；工作区与 `3d5a112` 中无 `tools/` 目录，但 `tools/check_a0_static.py` 已由 Chrome 在 `origin/chrome/t02-a0-eda-validation` 创建，该条目的来源仍无记载，见 U-27 |
| `AGENTS.md` | Claude 主控 | 文档 | 手写 | Claude 主控（T01，工作区有未提交改动） | 协作规则总则 |
| `CLAUDE.md` | Claude 主控 | 文档 | 手写 | 空闲 | 主控入口 |
| `README.md` | Claude 主控 | 文档 | 手写 | 空闲 | 无基线日期或版本行，与 `docs/` 下带日期的文档不一致；仓库导航未列 `docs/handoffs/` |
| `design/` | Chrome | 目录 | — | Chrome 持有，见 5.3 | 电气与 A0 设计源及其产物；Chrome 已领取 T02，分支 `chrome/t02-a0-eda-validation`（PR #4 未合入）。实测该分支未改动 `design/` 下任何文件，但该目录是其审查输入 |
| `docs/` | Claude 主控 | 目录 | — | 部分文件被占用，且存在远端并发改动，见 2.2 | 计划、状态、决策与交接 |
| `references/` | Chrome | 目录 | — | Chrome 持有，见 5.3 | 器件库缓存与官方资料入口；`docs/TEAM_PLAN.md` 第 2 节未列出该目录，归属为本文推定，见 U-25。Chrome 已领取 T02，分支 `chrome/t02-a0-eda-validation`（PR #4 未合入）；实测该分支未改动本目录下任何文件，但本目录是其审查输入 |
| `review/` | 共享目录，按子目录分配；顶层归属未定义，见 U-33 | 目录 | — | 按子目录分别判定，见 5.3 | 本机含空子目录 `review/hiro/`（未被 Git 跟踪），以及在本文写作期间出现的 `review/claude/official-evidence/`（12:52 时为 4 个文件，已暂存未提交）。`review/chrome/T02/` 已由 Chrome 在 `origin/chrome/t02-a0-eda-validation` 创建。从 `3d5a112` 克隆得不到 `review/` 下任何内容 |

### 2.2 `docs/` 下的文件

| 路径 | 权威负责人 | 类型 | 生成关系 | 当前编辑锁 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `docs/DESIGN_STATUS.md` | Claude 主控记录，硬件结论由 Chrome 提交、Hiro 复核 | 文档 | 手写 | 存在远端并发改动：Chrome（PR #4，未合入）占用 | O01–O10 的原文出处；原文不含任务编号。PR #4 对本文件有 13 行改动（新增 O11–O14 并改写三处限制说明）；本文只登记该改动存在，其技术结论不在本文判定 |
| `docs/PROJECT_PLAN.md` | Claude 主控 | 文档 | 手写 | 空闲 | 里程碑 M0–M7 |
| `docs/TEAM_PLAN.md` | Claude 主控 | 文档 | 手写 | Claude 主控（T01，工作区有未提交改动） | 质量节点，未提交版本中已由 G0–G5 扩为 G0–G6；第 2 节固定责任表与本文的关系见第 1 节 |
| `docs/TASK_BOARD.md` | Claude 主控 | 文档 | 手写 | **并发占用**：Claude 主控（T01，本地未提交）与 Chrome（PR #4，未合入） | 任务队列与领取记录，本地未提交版本中已由 T01–T13 扩为 T01–T15；PR #4 对本文件有 15 行改动（把 T02 改为 `IN_REVIEW`，新增「Chrome 领取记录」节，并把 T01 改回 `READY`）。这是一次已经发生的并发编辑冲突，裁决见 5.3 |
| `docs/STATUS.md` | Claude 主控 | 文档 | 手写 | Claude 主控（T01，新增未提交） | 不在 `3d5a112` 中，本轮新增；跨端进度入口 |
| `docs/DECISIONS.md` | Claude 主控 | 文档 | 手写 | Claude 主控（T01，新增未提交） | 不在 `3d5a112` 中，本轮新增；含 D-001–D-009 与一张 `UD-` 前缀的「待用户决策」表（UD-01–UD-08）。与本文直接相关的三条：D-006 对应 U-11、U-12；D-007（放行链变更、G4–G6 重构）对应 U-23；D-009（新增 T14、T15）对应 U-22 的映射缺口。该文件第 4 节末尾声明了各前缀的归属（列出 `D`、`UD`、`U`、`Q`、`A` 五个前缀，同句写作「四套编号」，计数与所列前缀数不符），见 U-32 |
| `docs/REFERENCES-INVENTORY.md` | Claude 主控 | 文档 | 手写 | Claude 主控（T01，新增未提交） | 不在 `3d5a112` 中，本轮新增；`references/` 引用关系清单 |
| `docs/OWNERSHIP.md` | Claude 主控 | 文档 | 手写 | Claude 主控（T01，新增未提交） | 本文 |
| `docs/T06-DOMESTIC-EXECUTION.md` | Claude 主控 | 文档 | 手写 | Claude 主控（T01，新增未提交） | 不在 `3d5a112` 中，本轮新增；T06 交付 |
| `docs/product/T13-PRODUCT-DIRECTION.md` | Claude 主控 | 文档 | 手写 | Claude 主控（T01，新增未提交） | 不在 `3d5a112` 中，本轮新增；T13 交付；目录选择见 U-26 |
| `docs/handoffs/TEMPLATE.md` | Claude 主控 | 文档 | 手写 | 空闲 | 交接模板 |
| `docs/handoffs/chrome.md` | Chrome（本人登记进展与交接），Claude 主控只编写交接包 | 文档 | 手写 | **版本冲突，待主控裁决**：Claude 主控（本地未提交）与 Chrome（PR #4，未合入） | 不在 `3d5a112` 中。本地版本为 Claude 主控写的 T02–T05 交接包；`origin/chrome/t02-a0-eda-validation` 上另有 Chrome 自己写的 T02 交接（29 行）。同一源文件出现两个互不相同的版本，违反第 5.1 节第 1 条，属已发生的冲突，见 U-34 |
| `docs/handoffs/hiro.md` | Hiro | 文档 | 手写 | Hiro（已合入 `origin/main`，本地不可见） | **已存在**于 `origin/main` `4261fcb`（由 `92cf2fb` 新增，经 PR #3 合入），是 `3d5a112..origin/main` 新增的唯一文件；因本地 `main` 落后 2 个提交而未出现在当前工作区。内容为 Hiro 本轮交接，可用 `git show origin/main:docs/handoffs/hiro.md` 读出 |
| `docs/handoffs/` | Claude 主控 | 目录 | — | 部分文件被占用，见本节 | 统一交接入口；工作区当前含 `TEMPLATE.md`、`chrome.md`；`hiro.md` 在 `origin/main` 上 |
| `docs/product/` | Claude 主控 | 目录 | — | 部分文件被占用，见本节 | 本轮新建，尚未被 Git 跟踪；与根目录 `product/` 的路径冲突见 U-26 |

### 2.3 `design/` 下的文件

`design/build_design.py` 是 `design/` 下唯一的手写设计源，其余五个文件全部由它生成。本轮已在仓库外的临时副本中执行该脚本，记录如下：解释器仅 `/usr/bin/python3`（3.9.6）一个；退出码 0；同一解释器下连续运行两次，五个产物的 SHA-256 逐一相同。**未在其他 Python 版本上运行，跨版本一致性未知。** 这只说明代码能执行并写出文件，不说明电路正确、封装正确或可生产。运行未在仓库内进行，仓库文件未被改动。

下表「当前编辑锁」列的「空闲」只表示没有任何角色对该单个文件提出过改动；**整个 `design/` 目录处于 Chrome 已领取的 T02 范围内**（见 2.1 与 5.3），其他角色在 T02 结束前不得改动。

| 路径 | 权威负责人 | 类型 | 生成关系 | 当前编辑锁 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `design/build_design.py` | Chrome | 设计源 | 输入为 `references/<LCSC编码>.json`，一次运行写出下列 5 个产物；不读 `docs/`、不联网 | 空闲 | 首行自述 "NOT manufacturing data"；仅用标准库。缺 IC 库时报错退出，缺无源器件库时静默回退占位封装，见 U-19 |
| `design/mosaico-dock-schematic.json` | Chrome | 生成产物 | 由 `build_design.py` 生成 | 空闲（不得手改） | 与用同提交 `references/` 重跑的结果有 24 行差异 |
| `design/mosaico-dock-placement.json` | Chrome | 生成产物 | 由 `build_design.py` 生成 | 空闲（不得手改） | 只有摆放与丝印，无铜线布线；与重跑结果有 24 行差异 |
| `design/design-netlist.json` | Chrome | 生成产物 | 由 `build_design.py` 生成 | 空闲（不得手改） | 84 个器件、43 个网络；与重跑结果有 30 行差异，器件数无增减 |
| `design/bom-review.csv` | Chrome | 生成产物 | 由 `build_design.py` 生成 | 空闲（不得手改） | 忽略行尾后有 12 个数据行与重跑结果不同；不是可下单清单 |
| `design/pin-net-review.csv` | Chrome | 生成产物 | 由 `build_design.py` 生成 | 空闲（不得手改） | 忽略行尾后与重跑结果 243 行全等 |

`design/` 与 `references/` 在同一提交 `099af5b` 入库，但用该提交自带的 `references/` 重跑得到不同结果。已复现的观测是：仓库中已提交的四个产物与同提交 `references/` 的重跑结果不一致，差异集中在 12 个位号（C1、C5、C7、C8、C9、C14、C15、C16、R20、R21、R22、U8）与 6 个 LCSC 编码（C1591、C4177、C22978、C25819、C45783、C55266）。

由此可提出的假说是：已提交产物对应一个当时这 6 个编码取不到库几何的输入快照。**该假说不等于已查明成因。** `design/build_design.py` 的 `library()` 在三种情况下同样返回 `None`——文件不存在、`success` 为假、`result` 为空；仓库内的 `references/C16043.json` 正是文件存在却返回 `None` 的实例。因此文件缺失、抓取失败记录或内容不同都能导致同一结果。当时 `references/` 的实际内容未经生成者确认，成因判定权留给 U-11 指定的责任人，取舍见 U-12，封装问题见 U-13。

### 2.4 `references/` 下的文件

全部为外部抓取的只读缓存，不是生成产物，也不是设计源。抓取日期与接口版本未在文件中登记，缓存不可精确复现（U-17）。「已引用／未引用」按 `design/build_design.py`、`design/design-netlist.json`、`design/bom-review.csv` 的实际引用交叉核对得出，详见 `docs/REFERENCES-INVENTORY.md`。缓存存在不等于器件已选定、封装已核对或国内有料可贴装。

与 2.3 节同理，下表「当前编辑锁」列的「空闲」只表示没有任何角色对该单个文件提出过改动；**整个 `references/` 目录处于 Chrome 已领取的 T02 范围内**（见 2.1 与 5.3）。

| 路径 | 权威负责人 | 类型 | 生成关系 | 当前编辑锁 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `references/README.md` | Chrome | 文档 | 手写 | 空闲 | 官方资料入口与缓存说明 |
| `references/C130204.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用（U1） |
| `references/C15849.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用 |
| `references/C1591.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用；属重跑差异涉及的 6 个编码 |
| `references/C160353.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用（J2） |
| `references/C16043.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 未引用；内容为 404 失败记录，对应器件未知 |
| `references/C165948.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用（J1） |
| `references/C165960.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 未引用 |
| `references/C22827.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 未引用 |
| `references/C2290.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 未引用 |
| `references/C2296.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用（D1、D2） |
| `references/C22978.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用；属重跑差异涉及的 6 个编码 |
| `references/C23138.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 未引用 |
| `references/C23162.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用 |
| `references/C23186.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用 |
| `references/C25803.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用 |
| `references/C25804.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用 |
| `references/C25819.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用；属重跑差异涉及的 6 个编码 |
| `references/C2682616.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用（U7） |
| `references/C28323.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 未引用 |
| `references/C2869734.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用（U4）；`result.tags` 为 `["Pre-ordered Chips"]`，`c_para` 标注 `JLCPCB Part Class: Extended Part`，供应状态见 U-18 |
| `references/C404027.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用（U5） |
| `references/C4177.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用；属重跑差异涉及的 6 个编码 |
| `references/C431540.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用（SW12） |
| `references/C45783.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用；属重跑差异涉及的 6 个编码，其差异表现即为 U-13 所述封装问题 |
| `references/C54313.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用（U2） |
| `references/C544515.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用（U6）；缓存 `lcsc.url` 路径含 presales，供应状态见 U-18 |
| `references/C55266.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用（U8）；属重跑差异涉及的 6 个编码 |
| `references/C5832342.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用（L1）；`result.lcsc` 只含 `id` 与 `number`，无 `url`、`stock`、`price`，`c_para` 标注 `JLCPCB Part Class: Extended Part`，供应状态见 U-18 |
| `references/C720477.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用（SW1–SW11） |
| `references/C919459.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用（U3） |
| `references/C96446.json` | Chrome | 参考缓存 | 外部抓取 | 空闲 | 已引用 |

`references/C23239.json` 被 `design/` 引用但在仓库中不存在，见第 3 节与 U-14。

## 3. 规划中但尚未创建的路径

下列路径在 `docs/TEAM_PLAN.md`、`docs/TASK_BOARD.md` 或 `README.md` 中被引用，但在工作区与提交 `3d5a112` 中都不存在（快照时刻同第 2 节）。

**本节的判断范围只覆盖工作区与 `3d5a112`，不覆盖 `origin/main` 与其他远端分支。** 第 2 节的「不存在」判断同样只覆盖这两者。已知的例外已从本表移出：`docs/handoffs/hiro.md` 存在于 `origin/main`，`tools/check_a0_static.py` 与 `review/chrome/T02/` 存在于 `origin/chrome/t02-a0-eda-validation`。本轮已用 `git ls-tree -r --name-only` 对 `origin/main` 与 `origin/chrome/t02-a0-eda-validation` 逐项核对，确认 `docs/handoffs/claude.md`、`docs/INTERFACE_CONTROL.md`、`mechanical/`、`product/`、`references/C23239.json` 在这两个远端分支上同样不存在。出现新的远端分支时须重新核对：先 `git fetch --all`，再用 `git branch -avv` 与 `git ls-tree` 逐项确认。

**下表中标注「尚未创建」的项均为「不得视为已有交付」。** 引用它们的文档不得使用「已写入」「已完成」等完成式表述。

| 路径 | 引用出处 | 由谁创建 | 状态 |
| --- | --- | --- | --- |
| `docs/handoffs/claude.md` | `docs/TASK_BOARD.md` T01、T06、T13 的交接路径 | Claude 主控 | 尚未创建，不得视为已有交付 |
| `docs/INTERFACE_CONTROL.md` | `docs/TEAM_PLAN.md` 第 2 节与第 5 节 | Chrome | 尚未创建，不得视为已有交付；第 5 节已正确标注，第 2 节未标注 |
| `mechanical/` | `docs/TEAM_PLAN.md` 第 2 节 Chrome 产物 | Chrome | 尚未创建，不得视为已有交付 |
| `product/` | `docs/TEAM_PLAN.md` 第 2 节 Claude 产物 | Claude 主控 | 尚未创建，不得视为已有交付；本轮交付实际写入 `docs/product/`，路径冲突见 U-26 |
| `review/hiro/` | `README.md` 仓库导航；`docs/TEAM_PLAN.md` 第 2 节 | Hiro | 本机为空目录且未被 Git 跟踪，从 `3d5a112` 克隆得不到，不得视为已有交付 |
| `review/`（顶层） | `README.md` 仓库导航 | 归属未定义，见 U-33 | 在 `3d5a112` 中不存在；本机含未跟踪的 `review/hiro/`（空）与已暂存未提交的 `review/claude/official-evidence/`；`review/chrome/T02/` 已存在于 `origin/chrome/t02-a0-eda-validation` |
| `references/C23239.json` | `design/build_design.py`、`design/design-netlist.json`、`design/bom-review.csv` 引用 R26 的 LCSC 编码 C23239 | Chrome | 尚未创建，不得视为已有交付；缺失导致静默占位，见 U-14、U-19 |
| `tools/`、`tools/python-packages/` | `.gitignore` | `tools/` 已由 Chrome 创建；`tools/python-packages/` 未定 | 在工作区与 `3d5a112` 中不存在。`tools/check_a0_static.py` 已由 Chrome 在 `origin/chrome/t02-a0-eda-validation` 创建（PR #4，未合入），其 `docs/handoffs/chrome.md` 说明其用途为可重复的文件核对工具；`.gitignore` 中该条目的来源仍无记载，见 U-27 |

以下五个路径在本轮开始时不存在、在本轮 T01 进行中出现于工作区（抬头自述维护人为 Claude 主控，是否出自同一会话不可从仓库核验），已移出上表并登记在第 2.2 节：`docs/DECISIONS.md`、`docs/handoffs/chrome.md`、`docs/T06-DOMESTIC-EXECUTION.md`、`docs/product/`、`docs/product/T13-PRODUCT-DIRECTION.md`。截至 12:52 它们已暂存但仍未提交，**在提交并推送前，其他角色 clone 仓库仍然得不到这些文件**。

`docs/TASK_BOARD.md` 的本地未提交版本把 T01、T06、T13 标为 `IN_PROGRESS`，但本地 `main` 与分支 `docs/t01-lead-handover` 的 tip 同为 `3d5a112`，该分支没有自有提交。按 `AGENTS.md`「领取任务与执行结果必须落到仓库」与 `docs/TEAM_PLAN.md` 第 3 节「任务状态以仓库记录为准」，这些状态需要在提交并推送后才成立。本文自身同样处于未提交状态，适用同一条约束。

同一时刻 `origin/main` 为 `4261fcb`，比输入提交多 2 个提交（`92cf2fb`、`4261fcb`），本地 `main` 落后 2 个提交。**复核本节时不能只执行 `git status --short`；必须同时执行 `git fetch` 与 `git rev-parse origin/main`，否则查不出远端漂移。** 本轮的输入提交 `3d5a112` 已不是远端最新提交，据此产出的全部快照结论都需在提交前重新核对一次。

## 4. 未知项登记

编号 U-01 起。U-01 至 U-10 逐条对应 `docs/DESIGN_STATUS.md` 的 O01–O10；U-11 起为本轮盘点新发现、O 编号未覆盖的项。

`docs/DESIGN_STATUS.md` 原文不含任务编号，「影响哪些任务或质量节点」一列是由 O 条目文字与 `docs/TASK_BOARD.md`、`docs/TEAM_PLAN.md` 推导得出，标记为推导，须由 Chrome 在编写 `docs/INTERFACE_CONTROL.md`（尚未创建）时确认，见 U-22。

| 编号 | 未知内容 | 影响哪些任务或质量节点 | 解除所需证据 | 责任人 | 对应 O 编号 |
| --- | --- | --- | --- | --- | --- |
| U-01 | 触点坐标、直径、间距、模块包络与工作高度缺完整机械证据 | T08 直接受阻；T03、T04 为产出任务；经 T08 间接影响 T10、T11、T12；G1（推导） | 官方带坐标机械图纸或实测记录，注明文档版本、页码与日期 | Chrome 提交、Hiro 复核后填入 | O01 |
| U-02 | 草案中的板框、模块区域与 Pogo 间距是研究占位值 | T08；经 T08 间接影响 T10、T11、T12；G1（推导） | 以 U-01 的官方证据替换全部占位值，并重新生成受影响文件 | Chrome 提交、Hiro 复核后填入 | O02 |
| U-03 | 背面图片方向与底座顶视的镜像关系未确认 | T08；T05、T07 的必要输入；产出侧为 T04（推导） | 带坐标系的官方图纸或实测对位记录 | Chrome 提交、Hiro 复核后填入 | O03 |
| U-04 | TCA9517 与 MAX17048 的低电平阈值及噪声裕量兼容性存疑 | T05、T07；T09 的审查对象；G2，经 G2 影响 T10（推导） | 原厂数据表逐项参数比对与独立计算 | Chrome 提交、Hiro 复核后填入 | O04 |
| U-05 | 输入限流、充电电流、升压输出、瞬态与热预算未完成系统计算 | T05、T07、T09；约束 T13 不得展示续航或充电数值；G2（推导） | 完整系统计算与依据，含所有电源状态 | Chrome 提交、Hiro 复核后填入 | O05 |
| U-06 | 原生 USB-C 与底座供电同时连接时的电源状态与防反灌未核对 | T05、T07、T09、T12；G2、G4（推导） | 电路审核结论加样机实测记录，仅审核不足以关闭 | Chrome 提交、Hiro 复核，实测后填入 | O06 |
| U-07 | Mosaico 自身电源开关与底座开关是两个控制点，行为未定义 | T07、T11、T13（推导） | 开机、关机、待机、充电四种行为的明确定义与电路实现 | Chrome 提交、Hiro 复核；交互语义由 Claude 提案 | O07 |
| U-08 | 电池保护、NTC、插座极性与线束未冻结 | T07、T08；产出侧 T04；经 T08 影响 T11；G1（推导） | 电芯或电池包的原厂与供应资料，含保护板与接口定义 | Chrome 提交、Hiro 复核后填入 | O08 |
| U-09 | 接口保护、测试点与掉电行为需完整审核 | T05、T07、T09；经 G2 影响 T10；M2 完成条件（推导） | 逐项审核记录与问题关闭证据 | Chrome 提交、Hiro 复核 | O09 |
| U-10 | 器件库下载不等于国内有料可贴装；部分器件高度影响握把 | T04、T07、T10、T11、T12；G0、G3（推导） | 嘉立创实际库存、封装与贴装能力确认，以及器件高度数据 | Chrome 提交、Hiro 复核后填入 | O10 |
| U-11 | 仓库已提交的 `design/` 产物与同提交 `references/` 不一致的成因未知：生成时间点、当时 `references/` 的实际内容、是先生成后补库还是中途替换过库文件。`library()` 在文件不存在、`success` 为假、`result` 为空三种情况下都返回 `None`，三者产生相同的占位回退结果，仅凭现有产物无法区分 | T02、T05、T07；G2（推导） | 由 A0 生成者（按 `docs/TEAM_PLAN.md` 为 Hiro）说明生成时的输入快照 | Hiro 说明，Chrome 复现确认 | 无对应 O 编号；`docs/DESIGN_STATUS.md`「现有生成文件可能未覆盖后续补充的全部库缓存」一句的具体化 |
| U-12 | `design/` 的受控版本取舍未知：是否把重跑结果提交入库，还是等 EDA 原生工程成为唯一设计源后废弃脚本产物；脚本与未来 EDA 工程的从属关系也未写入仓库任何文件 | 影响 `design/` 全部文件的编辑锁与 T02、T07；`AGENTS.md` 第 34 行要求 | 一份写明唯一设计源、脚本保留用途与从属关系的决定 | Chrome 决定，Hiro 复核，Claude 主控记录 | 无对应 O 编号 |
| U-13 | C45783 的原厂推荐 land pattern 未知。仓库已提交的 `design/bom-review.csv` 第 47、59、60 行（C5、C7、C8）写的 C0603 是脚本在库查不到时的硬编码占位值（`'C0603' if kind=='cap' else 'R0603'`，见 U-19），同一行的 Geometry status 已写明 `Locally drawn placeholder; library/land-pattern verification required`，不是对该料号的封装记载；带库重跑得到 `C0805`。两者都不是原厂依据 | T02、T07、T10；G2（推导） | 原厂数据表与推荐 land pattern，注明版本与页码 | Chrome 提交、Hiro 复核后填入 | O10 |
| U-14 | C23239 是否为 R26 的正确采购编码未知，仓库内无该库缓存可核对 | T04、T07；G0、G2（推导） | 补齐库缓存并核对 land pattern，或更换器件 | Chrome 补充来源与版本，Hiro 复核 | O10 |
| U-15 | R28 的 LCSC 采购编码未知，脚本内自述 pending | T04、T07（推导） | 选定器件并登记编码、数据表版本与供应状态 | Chrome 提交、Hiro 复核后填入 | O10 |
| U-16 | J3 Pogo 接口的全部几何参数未知；脚本内为明确标注的占位值，焊盘由脚本内置逻辑绘制，无库或原厂图纸支撑 | T08、T11；G1（推导） | 官方机械图纸或实测数据 | Chrome 提交、Hiro 复核后填入 | O01、O02 |
| U-17 | `references/` 缓存的抓取日期与实际接口版本未知，缓存不可精确复现；JSON 内的 `updated_at` 是服务端库记录更新时间，不是抓取时间 | T04；G0；`AGENTS.md` 对输入资料索引与复现说明的要求 | 重新抓取并登记日期、接口版本与来源 | Chrome | 无对应 O 编号 |
| U-18 | 三个编码的当前供应与贴装状态未知。实测可核验的缓存异常为：C5832342 的 `result.lcsc` 只含 `id` 与 `number`，无 `url`、`stock`、`price`，`c_para` 标注 `JLCPCB Part Class: Extended Part`；C2869734 的 `result.tags` 为 `["Pre-ordered Chips"]`，`c_para` 同样标注 Extended Part；C544515 的 `lcsc.url` 路径含 `presales` 且 `stock` 为 0。缓存字段不等于当前供应状态 | T04；G0、G3（推导） | 向嘉立创核实这三个料号的库存、贴装可行性、交期，以及是否属扩展料及其对应的加工费与备料要求 | Chrome 核实、Hiro 复核 | O10 |
| U-19 | `design/build_design.py` 缺无源器件库时不报错、静默回退占位封装，是否改为显式失败或显式标记未定；该路径正是 U-11 与 U-14 能静默产生的机制 | T02、T07（推导） | 一份修改后的脚本与其复现说明 | Chrome 实施，Hiro 复核 | 无对应 O 编号；与 `AGENTS.md`「库缓存中未使用或误选的器件不能自动进入生产 BOM」直接相关 |
| U-20 | 6 个未引用缓存（C165960、C2290、C22827、C23138、C28323、C16043）当初的候选用途未知；C16043 对应什么器件未知，其内容仅为 404 记录 | T04；G0（推导） | 重新抓取确认，或删除并在索引中写明原因 | Chrome | O10 |
| U-21 | 25 个已引用编号的封装是否与原厂推荐 land pattern 一致未知；全部条目当前状态为待原厂核对 | T04、T07、T10；G2、G3（推导） | 逐项核对数据表版本与页码 | Chrome 提交、Hiro 复核后填入 | O10 |
| U-22 | O01–O10 到任务编号的阻塞映射为文字推导结果，`docs/DESIGN_STATUS.md` 原文不含任务编号；推导基于 T01–T13，本轮新增的 T14、T15 尚未纳入映射 | 影响本表全部推导行的可信度 | 由 Chrome 在编写 `docs/INTERFACE_CONTROL.md`（尚未创建）时确认每条的归属任务与关闭条件 | Chrome 确认，Hiro 在对应审查包复核 | O01–O10 全部 |
| U-23 | 三套编号之间无映射表：`README.md` 与 `docs/PROJECT_PLAN.md` 的里程碑 M0–M7、`docs/TEAM_PLAN.md` 的质量节点（本轮已由 G0–G5 扩为 G0–G6）、`docs/TASK_BOARD.md` 的任务（本轮已由 T01–T13 扩为 T01–T15）。G0 在任务队列中无承接任务，G2 无明确产出任务；M0–M7 尚未随 G6 与放行链变更同步修订 | 影响全部放行判断与 T10 的前置条件追溯 | 由主控与 Chrome 共同确定后写入一份文档，其余文档统一引用 | Claude 主控与 Chrome | 无对应 O 编号 |
| U-24 | 本文与 `docs/TEAM_PLAN.md` 第 2 节固定责任表的主从关系尚未写入 `docs/TEAM_PLAN.md`，本文第 1 节的约定为单方面登记 | T01 | 在 `docs/TEAM_PLAN.md` 第 2 节补一句指向本文的说明 | Claude 主控 | 无对应 O 编号 |
| U-25 | `references/` 目录的权威负责人未在 `docs/TEAM_PLAN.md` 第 2 节列出；本文按「原厂与供应证据核验」归给 Chrome 属推定 | T04 | 在 `docs/TEAM_PLAN.md` 第 2 节明确该目录归属 | Claude 主控确认 | 无对应 O 编号 |
| U-26 | `product/` 与 `docs/product/` 哪一个是正确的产品文档目录未定：`docs/TEAM_PLAN.md` 第 2 节指向根目录 `product/`，`docs/TASK_BOARD.md` 领取记录指向 `docs/product/`；本轮 T13 交付已写入 `docs/product/`，冲突已实际发生 | T13 | 主控确定后同步修订 `docs/TEAM_PLAN.md` 第 2 节、`docs/TASK_BOARD.md` 领取记录与 `README.md` 仓库导航；`docs/DECISIONS.md` 已把该项列为待用户决策 | Claude 主控，或按用户指示 | 无对应 O 编号 |
| U-27 | `.gitignore` 中 `tools/python-packages/` 一条的来源未知：该条目先于 `tools/` 出现，七份文档无任何记载。`tools/` 本身已由 Chrome 在 `origin/chrome/t02-a0-eda-validation` 实际创建（`tools/check_a0_static.py`，PR #4 未合入），因此未知的只剩该 `.gitignore` 条目的来源与 `tools/python-packages/` 的预期用途 | 无直接任务影响；影响接手者对本地工具链的理解 | 确认该配置的来源并保留或删除；`tools/` 的目录约定由 Chrome 在合入 PR #4 时写明 | Claude 主控，`tools/` 用途由 Chrome 说明 | 无对应 O 编号 |
| U-28 | 主控文档中「Claude Fable 5.1」与本轮实际执行模型 `claude-opus-5` 的差异如何处理未知：修订五份文档表述，还是保留原表述并在决策记录中说明 | T01 及全部文档表述 | 用户明确指示；本会话不自行改写角色表述 | 用户决定，Claude 主控执行 | 无对应 O 编号 |
| U-29 | 外链可达性未知。上一轮记录过一次针对 `references/README.md` 中 analog.com MAX17048 页面的自动化请求未成功，但未留下所用命令、工具、超时设置与执行时间，本轮也未重做，因此该结果不可复核，**降级为「一次自动化请求未成功，方式未留证」，是否真正不可达未知**。其余链接上一轮只核验过 HTTP 状态码，未读取任何页面或 PDF 内容，可达不等于内容支持文档论述 | T04；G0；与 U-04 同一器件（推导） | 人工在浏览器中确认，或改用其他官方入口获取；无论哪种方式都须登记命令或操作步骤、执行日期、原始输出摘要、文档版本与页码 | Chrome，Hiro 复核 | O04 |
| U-30 | 候选器件 TLV 型号在仓库中有三种写法（`docs/DESIGN_STATUS.md` 写 TLV75533、`references/README.md` 写 TLV755P、`design/bom-review.csv` 写 TLV75533PDBVR），哪一种是正确器件标识未知 | T04、T07（推导） | 原厂数据表确认完整型号 | Chrome 提交、Hiro 复核后填入 | O10 |
| U-31 | `docs/TASK_BOARD.md` 未提交版本中的两处完成式表述（「已写入 `docs/handoffs/chrome.md`」「记录见 `docs/DECISIONS.md` D-001」）在本轮进行中因对应文件被补齐而由虚转实，但两个文件都还未提交；一并提交前，任何从远端 clone 的角色仍读不到它们。是否在提交说明中注明这一先后关系未定 | T01 | 把全部本轮改动一次提交并推送，或在表述中标明文件为同批新增 | Claude 主控 | 无对应 O 编号 |
| U-32 | 已解决，保留备查：本文上一版曾断言本文与 `docs/DECISIONS.md` 存在 U 编号空间冲突。复核 `docs/DECISIONS.md` 现文后确认该冲突不存在——该文件第 4 节使用 `UD-01`–`UD-08`，并在节末声明各前缀归属，其中 `U-NN` 明确属 `docs/OWNERSHIP.md` 的未知项登记。本文沿用 `U-` 前缀，不派发编号修订任务。仍需注意该声明句把 `D`、`UD`、`U`、`Q`、`A` 五个前缀写作「四套编号」，计数与所列前缀数不符 | T01 | 无需解除；如要消除计数不符，由主控在 `docs/DECISIONS.md` 中更正该句 | Claude 主控 | 无对应 O 编号 |
| U-33 | `review/` 顶层目录与 `review/<角色>/` 的归属规则未定义：`docs/TEAM_PLAN.md` 第 2 节只把 `review/hiro/` 列为 Hiro 的产物目录，未指定顶层，也未规定其他角色能否建立自己的子目录。实际已出现 `review/chrome/T02/`（`origin/chrome/t02-a0-eda-validation`）与本机未跟踪的 `review/claude/official-evidence/`。本文按子目录分配属推定，与 U-25 同类 | T01；影响各角色证据目录的落点与第 5.3 节的锁判定 | 在 `docs/TEAM_PLAN.md` 第 2 节明确 `review/` 顶层归属与 `review/<角色>/` 的建立规则 | Claude 主控确认 | 无对应 O 编号 |
| U-34 | `docs/handoffs/chrome.md` 出现两个互不相同的版本：本地未提交版本为 Claude 主控编写的 T02–T05 交接包，`origin/chrome/t02-a0-eda-validation` 上为 Chrome 自己写的 T02 交接。以哪一版为基准、如何合并未定。这是第 5.1 节第 1 条禁止的同一源文件双编辑者，属已发生的冲突 | T01、T02；影响 Chrome 的交接与进展日志入口 | 按第 5.1 节第 4 条由主控裁决：确定合并方式与谁继续持有该文件，裁决结果写回 `docs/TASK_BOARD.md`。裁决不涉及 PR #4 的任何技术结论 | Claude 主控裁决，Chrome 执行 | 无对应 O 编号 |

以上全部机械与电气数值（板框、孔位、间距、电流、阈值、公差、Pogo 尺寸、电池规格、封装等）在本文中均未给出、未推荐、未核对。主控不拥有硬件权威尺寸。

## 5. 编辑锁规则

### 5.1 规则

1. **同一源文件同一时间只允许一位编辑者。** 适用于 `design/build_design.py`、未来的 EDA 与 CAD 原生工程、三维模型，以及本文第 2 节列出的每一个文件。Chrome 可使用分开的电气与机械会话，但同一源文件仍只能有一位编辑者。
2. **领取先于修改。** 开始编辑前把领取记录写入 `docs/TASK_BOARD.md`「领取记录」表，登记任务 ID、领取人与平台、实际模型与档位、输入提交号、分支、文件范围、交接路径与日期。未登记的任务视为未领取，未登记的编辑视为越权。
3. **释放锁。** 改动合入主分支、或领取人明确放弃并在任务板注明后，锁释放。会话结束但改动未提交时，锁仍视为持有，并须在对应 `docs/handoffs/<角色>.md` 写明未完成范围。其中 `claude.md` 尚未创建；`hiro.md` 已存在于 `origin/main` `4261fcb`；`chrome.md` 当前存在两个互不相同的版本，见 U-34。
4. **冲突由主控裁决。** 并发领取同一文件范围时，由 Claude 主控决定谁继续、谁改期，裁决结果写入任务板。不能靠文字约定声称已实施自动锁。
5. **生成产物不手改。** `design/` 下的五个生成产物只能由 `design/build_design.py` 重新生成。不得同时手改生成文件与生成脚本。修改脚本后须重新生成全部产物并一并提交。
6. **接口变更先更新统一约束。** 涉及触点、板框、孔位、按键或电池空间时，先更新 `docs/INTERFACE_CONTROL.md`（尚未创建），再同步电路、PCB、机械与验收文档。
7. **跨角色改动通过 PR，但有明确例外。** 非本文第 2 节所列权威负责人不得直接修改该文件，只能提交问题单或 PR 建议。关键电源与接口由非作者复核。

   本条的**排他写入只适用于计划、决策与放行记录类文档**：`docs/TEAM_PLAN.md`、`docs/PROJECT_PLAN.md`、`docs/DECISIONS.md`、`docs/OWNERSHIP.md`、`docs/STATUS.md`、`AGENTS.md`、`CLAUDE.md`、`README.md`。以下例外逐条列出，不作扩大或缩小解释：

   1. `docs/TASK_BOARD.md`「领取记录」节中属于本角色的行，由该角色自行追加与更新，依据 `docs/TEAM_PLAN.md` 第 5 节与本节第 2 条。
   2. `docs/TASK_BOARD.md` 主表中本角色已领取任务的状态字段，由该角色自行更新。
   3. `docs/DESIGN_STATUS.md`「关键待解决项」表的新增行，由发现问题的角色自行追加，依据 `AGENTS.md`「新发现的问题及时更新 `docs/DESIGN_STATUS.md`」。
   4. `docs/handoffs/<角色>.md` 中属于本角色的交接与「进展日志」内容，由该角色自行写入，依据 `AGENTS.md`「进展同步（强制）」节。

   在上述四种例外中，主控只负责合并、统一编号与消除冲突，不得以归属表为由阻挡其他角色登记硬件问题或领取记录。除此之外的内容仍按本条正文走 PR。

### 5.2 目前没有技术手段强制

**上述规则目前没有任何技术手段强制执行，完全依靠流程与 PR 约束。**

本轮实测（2026-09-20 已用 `gh api repos/ChromeTokyo/MosaicoKeyboard` 复核一次）：当前账号对 `ChromeTokyo/MosaicoKeyboard` 的权限为 `admin: false`、`maintain: false`、`push: true`、`triage: true`、`pull: true`，仓库 `visibility` 为 `public`。没有 admin 或 maintain 权限，因此无法配置分支保护规则、无法要求 PR 审查、无法设置 CODEOWNERS 强制审批、无法禁止直接推送 `main`。任何角色只要有 push 权限，都可以在不经过领取和复核的情况下直接改动任意文件。

这意味着：

| 想要的约束 | 当前能否强制 | 现状依靠什么 |
| --- | --- | --- |
| `main` 必须经 PR 合入 | 否 | 各角色自觉使用分支与 PR |
| PR 必须由非作者审查 | 否 | `AGENTS.md`、`docs/TEAM_PLAN.md` 的书面规定 |
| 按目录限定编辑者（CODEOWNERS） | 否 | 本文第 2 节的归属表 |
| 同一文件的并发编辑检测 | 否 | 领取记录加主控裁决 |

若用户希望把其中任何一条变成技术强制，需要由仓库拥有者授予 admin 或 maintain 权限，或由拥有者自行在 GitHub 仓库设置中配置。本会话不具备该权限，也未进行任何设置修改。

### 5.3 本文写入时刻的锁状态摘要

快照时刻：2026-09-20 12:52 JST，与第 2 节同一时刻。**使用前必须先 `git fetch --all`，再用 `git branch -avv`、`git status --short --untracked-files=all` 与 OPEN PR 清单重新核对；本地 `git status` 不足以判定锁状态。**

| 文件范围 | 持有者 | 依据 |
| --- | --- | --- |
| `AGENTS.md`、`docs/TEAM_PLAN.md`、`docs/STATUS.md`、`docs/DECISIONS.md`、`docs/REFERENCES-INVENTORY.md`、`docs/OWNERSHIP.md`、`docs/T06-DOMESTIC-EXECUTION.md`、`docs/product/T13-PRODUCT-DIRECTION.md` | Claude 主控（T01，改动未提交） | 工作区 git 状态；各文件抬头自述维护人为 Claude 主控 |
| `docs/TASK_BOARD.md`、`docs/DESIGN_STATUS.md` | **并发占用待裁决**：Claude 主控（本地未提交）与 Chrome（分支 `chrome/t02-a0-eda-validation`，PR #4 未合入） | `git diff --stat 3d5a112 origin/chrome/t02-a0-eda-validation` 显示两文件分别有 15 行与 13 行改动；同时本地工作区对 `docs/TASK_BOARD.md` 有未提交改动 |
| `docs/handoffs/chrome.md` | **版本冲突待裁决**：Claude 主控（本地未提交）与 Chrome（PR #4，未合入，29 行） | 同上；同一源文件出现两个互不相同的版本，见 U-34 |
| `docs/handoffs/hiro.md` | Hiro（已合入 `origin/main` `4261fcb`） | `git show origin/main:docs/handoffs/hiro.md`；本地 `main` 落后 2 个提交，工作区不可见 |
| `design/`、`references/` 全部文件 | Chrome 持有（T02 已领取，PR #4 未合入）；属审查输入，不在其登记的改动范围内 | `origin/chrome/t02-a0-eda-validation` 的 `docs/TASK_BOARD.md` 已登记 T02 的领取人、分支、输入提交与文件范围，并写明「本任务保留 A0 设计源作为审查输入，不提前开展 T07 电气修订」。实测该分支未改动这两个目录下任何文件。其他角色在 T02 结束前不得改动这两个目录 |
| `tools/check_a0_static.py`、`review/chrome/T02/` | Chrome（PR #4，未合入） | 该分支新增；见第 3 节 |
| `review/hiro/` | 无人持有 | 本机为空目录且未被 Git 跟踪，见第 3 节 |
| `review/claude/official-evidence/` | 未知 | 在本文写作期间出现：12:46 为 3 个未跟踪文件，12:52 增至 4 个并已暂存；创建者与暂存执行者均不可从仓库核验 |

**待主控裁决的冲突：** 上表第 2、3 行是已经发生的并发编辑，不是潜在风险。按第 5.1 节第 4 条，由 Claude 主控决定 `docs/TASK_BOARD.md`、`docs/DESIGN_STATUS.md`、`docs/handoffs/chrome.md` 三个文件各以哪一版为基准、如何合并，裁决结果写回 `docs/TASK_BOARD.md`。裁决只处理文件版本与编辑权，**不涉及 PR #4 的任何技术内容**。

关于 Chrome 的领取状态，按仓库可核验事实登记如下：Chrome 已推送分支 `origin/chrome/t02-a0-eda-validation`（tip `a6db65a`，含 `75e07b9`、`3d8ad4c`、`a6db65a` 三个提交）并开启 PR #4（状态 OPEN），该分支改动 `docs/DESIGN_STATUS.md`、`docs/TASK_BOARD.md`、`docs/handoffs/chrome.md`，新增 `review/chrome/T02/` 与 `tools/check_a0_static.py`。本文只登记该分支与 PR 的存在及其文件范围。**Chrome 的报告存在不等于 T02 通过**：该分支自述技术结论为 `CHANGES_REQUIRED`，其全部技术结论待 Hiro 复核与主控核对证据完整性，不在本文判定。

`docs/TASK_BOARD.md` 本地未提交版本中关于「用户已于 2026-09-20 启动 Chrome 会话」的记载来自用户告知，本文只转述该记载的存在，不确认会话状态；但该行同时写的「尚未推送任何领取登记或进展记录」与上述远端事实不符，须随本轮改动一并更正。

## 6. 本文的证据边界

- 本文只记录文件归属、创建状态与未知项。不判定电气正确性、封装正确性、结构可行性或供应可行性。
- 第 2.3 节关于脚本可运行与产物差异的陈述，来自本轮在仓库外临时副本中的复现运行：把 `099af5b` 的完整树导出到临时目录，用该提交自带的 `references/` 运行 `design/build_design.py`，再与同提交的 `design/` 产物逐文件比对。解释器只用了 `/usr/bin/python3`（3.9.6）一个，连续运行两次，五个产物的 SHA-256 逐一相同；未在其他 Python 版本上运行。仓库文件未被改动，运行前后 `design/` 下五个产物的 SHA-256 未变，全程未执行 `git add`、`git commit` 或 `git push`。临时副本位于会话 scratchpad 目录下，不属于仓库，可能随会话结束被清理；需要复核时按 `design/build_design.py` 的输入说明重新复现即可。
- 第 2.4 节的引用关系来自 `docs/REFERENCES-INVENTORY.md`，器件身份从缓存 JSON 的自述字段读取，未从文件名推断，也未经原厂资料核对。
- 第 4 节标注「推导」的任务与质量节点映射，须按 U-22 确认后才可作为依据。
- **快照规则。** 第 2、3、5.3 节是快照，必须同时覆盖三组命令：`git status --short --untracked-files=all`、`git ls-files`，以及 `git fetch --all` 之后的 `git branch -avv`（含 `git rev-parse origin/main` 与 OPEN PR 清单）。三者任一在写作过程中发生变化时，第 2、3、5.3 节必须整体重核后才能定稿。上一版只覆盖了前两组，并把快照时刻写成早于实际写入时刻，远端事实因此在写入时即已过期。
- 本次按该规则重核两轮：12:46 与 12:52。工作区在两轮之间发生变化（`review/claude/official-evidence/` 由 3 个文件增至 4 个，全部本轮改动被另一方 `git add` 转为已暂存），第 2、3、5.3 节已按 12:52 的状态整体重写；远端状态两轮一致。本文作者未执行 `git add`。
- `docs/` 下本轮新增文件的抬头自述维护人为 Claude 主控；这些文件是否出自同一个会话不可从仓库核验。本文对自己一侧与对其他角色采用同一标准：只转述仓库中的记载与可核验的分支事实，不确认任何会话状态。
- 本节不覆盖外链可达性检查。U-29 所述的链接请求结果来自上一轮且未留命令与执行时间，本轮未重做，该结论不可复核。
- 本文未声称启动任何其他平台会话、未联系任何人、未采购或下单。`docs/TASK_BOARD.md` 中关于 Chrome 会话已启动的记载来自用户告知，本文只转述该记载的存在，不确认其状态；Chrome 已推送的分支与 PR 则是仓库可核验事实，按事实登记。
- 本文的作者未执行 `git add`、`git commit` 或 `git push`，也未修改本文以外的任何仓库文件。12:52 时本轮改动已处于已暂存状态，该暂存动作由本文作者以外的一方执行，执行者不可从仓库核验。
