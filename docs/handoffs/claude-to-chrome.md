# 交接包：Chrome（硬件总设计）T02–T05

> **主控裁决（2026-09-20，D-006）：本文件原名 `docs/handoffs/chrome.md`，已重命名为 `docs/handoffs/claude-to-chrome.md`。**
> 起因是同一路径出现两个互不相同的版本（本派发包与 Chrome 在 PR #4 中自写的 T02 交接），违反“同一源文件同时只允许一位编辑者”。
> 裁决方式为**分离职责而非合并内容**：`docs/handoffs/chrome.md` 长期且唯一归属 Chrome，用于登记自己的领取、进展日志与完成交接，主控不再写入；主控派发给 Chrome 的工作包一律写在本文件。
> 因此本文各处提到的“交接文件路径 `docs/handoffs/chrome.md`”“可编辑文件范围含 `docs/handoffs/chrome.md`”**仍然成立且不需改动**——那些指的是 Chrome 自己的交接文件。原第 0.5 节的合并方案已作废，见该节。
> 未解决项 U-34 据此关闭。


- 任务 ID：T02、T03、T04、T05（本文件一次性派发四项，允许按优先级串行领取）
- 负责人／角色：Chrome／GPT-6，硬件总设计（电路、电源、I²C、器件与封装、PCB、参数化外壳、机械 CAD、原厂与供应证据核验）
- 平台、实际模型 ID、推理档位：本交接包由 Claude 主控编写，主控本轮实际模型 `claude-opus-5`，高推理档位。Chrome 侧的平台、实际模型 ID 与推理档位由 Chrome 在领取时自行登记，本文件不代填。
- 日期：2026-09-20（本次修订：2026-09-20，按复核意见重写第 0 节全部核对项与第 6、7 节）
- 状态：`docs/TASK_BOARD.md` 的任务表把 T02–T05 记为 `READY`。**但远端已存在 Chrome 的 T02 分支 `origin/chrome/t02-a0-eda-validation`（tip `a6db65a`）与其自有的 `docs/handoffs/chrome.md`，任务板的 `READY` 与「尚未推送任何领取登记」两处记载均已过期。** 领取前必须按第 0.2 节先核对远端，再决定 T02 是「继续」还是「改为复核既有证据」。本文件写入仓库不表示已有会话启动、已开始工作、已联系任何人或已发生采购。
- 输入提交号及接口版本：本包以 `3d5a112` 为输入提交。各 ref 的实际指向与核对凭据见第 0.1 节，**三者并不相同**。接口版本：无。`docs/INTERFACE_CONTROL.md` 在工作区、基线与全部远端分支中**均不存在**（核对方式见第 0.4 节），共同接口未冻结，`docs/TEAM_PLAN.md` 第 5 节已就此明确说明。
- 输出分支、提交号、PR：待 Chrome 领取后填写。分支命名沿用 Chrome 已在用的 `chrome/<任务-简述>`，见第 0.2 节与各任务节。
- 改动文件及源文件／生成文件关系：本轮主控的实际改动与新增见第 0.3 节（逐条列出 Git 状态），**本文件此前「只新增本文件、未执行 git add」的陈述是错的，已删除**。`design/` 内源文件与生成文件的当前关系见第 0.6 节。

## 0. 本交接包的性质与边界

本文件是主控派发给 Chrome 的工作包，不是替 Chrome 做出的技术判断。主控角色按 `docs/TEAM_PLAN.md` 第 2 节不拥有硬件权威尺寸，因此本文件：

- 不给出、不推荐、不冻结任何机械或电气数值（板框、孔位、间距、直径、公差、电流、电压、阈值、行程、高度等）。需要数值的位置一律写“由 Chrome 提交、Hiro 复核后填入”。
- 不对 A0 草案的电路正确性、封装正确性或可生产性下结论。文件存在、脚本可运行、库已下载、计划已写入，都不等于电气正确、可生产或已验证。
- 不代表已启动 Chrome 会话，也不代表已与供应商、工厂或任何个人产生联系。

### 0.1 三个 Git 引用的实际指向（附核对凭据）

本节各行是**某一时刻的核对结果，不是无时效事实**。

| 引用 | 指向 | 核对时间 | 核对命令 |
| --- | --- | --- | --- |
| `HEAD`（分支 `docs/t01-lead-handover`） | `3d5a112` | 2026-09-20 12:43 JST | `git rev-parse main origin/main HEAD` |
| `main`（本地） | `3d5a112`，`git branch -vv` 显示 `[origin/main: behind 2]` | 2026-09-20 12:43 JST | `git rev-parse main`、`git branch -vv` |
| `origin/main`（远端跟踪 ref） | `4261fcb`，**领先基线 2 个提交** | 2026-09-20 12:43 JST | `git rev-parse origin/main` |

`origin/main` 领先的两个提交内容：`92cf2fb`（Record Hiro handoff，分支 `docs/hiro-session-handoff`）及其 PR #3 合并提交。其带来的唯一新文件是 `docs/handoffs/hiro.md`（`git ls-tree -r --name-only origin/main` 可见，基线 `3d5a112` 中无此文件）。

**重要：本次核对未执行 `git fetch`。** 上表与第 0.2 节的 `origin/*` 数据全部读自本机的远端跟踪 ref（`refs/remotes/origin/*`），它们反映的是上一次 fetch 时的远端状态，可能已经陈旧——`origin/chrome/t02-a0-eda-validation` 此前之所以被漏看，正是同一类问题。

**Chrome 领取前必须自行 `git fetch --all`，再重新执行 `git rev-parse main origin/main` 与 `git for-each-ref refs/remotes/`，复核本节与第 0.2 节的结论是否仍成立。** 据本节取基线而不复核，会取到错误的基线，或重复已推送的工作。

本包仍以 `3d5a112` 为输入提交的原因：`3d5a112` 是 T02–T05 四项任务的共同审查对象（`design/` 的 A0 草案与 `references/` 缓存），而 `origin/main` 领先的两个提交只新增 `docs/handoffs/hiro.md`，未改动 `design/`、`references/` 或任何本包引用的规则文档。若 Chrome 复核后发现远端已有触及 `design/`、`references/` 的提交，本包的输入提交号即失效，须由主控重新派发。

### 0.2 远端已存在的 Chrome 分支（领取前必读）

核对时间 2026-09-20 12:43 JST，命令 `git for-each-ref refs/remotes/`、`git log --oneline origin/chrome/t02-a0-eda-validation`、`git ls-tree -r --name-only origin/chrome/t02-a0-eda-validation`。

远端存在 `origin/chrome/t02-a0-eda-validation`，tip `a6db65a`，以 `3d5a112` 为分叉点（`git merge-base` 结果为 `3d5a112`）。其三个提交依次为：

| 提交 | 标题 |
| --- | --- |
| `75e07b9` | docs: claim T02 A0 EDA validation for Chrome |
| `3d8ad4c` | T02: record A0 EDA import and connectivity validation |
| `a6db65a` | docs: link T02 evidence handoff to PR 4 |

该分支共 69 个受版本管理文件，相对基线新增的是：`review/chrome/T02/REPORT.md`、`review/chrome/T02/evidence/` 下 20 个证据文件（含 `SHA256SUMS.json`、`a0-eda-altium.net`、7 个 PNG 与多份 JSON 诊断记录）、`tools/check_a0_static.py`，以及**该分支自己的 `docs/handoffs/chrome.md`**。除新增外，该分支还修改了 `docs/DESIGN_STATUS.md` 与 `docs/TASK_BOARD.md`（实测 `git diff --stat 3d5a112 origin/chrome/t02-a0-eda-validation`，共 23 个文件、5189 增 6 删）。基线的 `design/`、`references/` 在该分支上未被改动（`git diff --stat 3d5a112 origin/chrome/t02-a0-eda-validation -- design/ references/` 无输出）。

**合并冲突预警：** `docs/TASK_BOARD.md` 同时被该远端分支和主控本轮未提交改动修改（见第 0.3 节），`docs/DESIGN_STATUS.md` 被该分支修改而主控未动。合并时以哪一份为基础由主控裁决（`docs/OWNERSHIP.md` 第 5 节第 4 条：并发领取同一文件范围由 Claude 主控决定），Chrome 不要单方面覆盖。

由此产生三项必须在领取前处理的事：

1. **T02 的实际状态不是 `READY`。** 任务板的 `READY` 与「领取记录」中 Chrome 行的「尚未推送任何领取登记或进展记录」均已过期。`docs/STATUS.md` 第 2 节的「会话已启动，尚无进展记录」同样过期。这三处由主控更正，不属 Chrome 的文件范围；Chrome 只需据实登记自己的状态。
2. **`docs/handoffs/chrome.md` 存在两份内容。** 一份是本文件（主控派发包，在工作区、未提交），一份在 `origin/chrome/t02-a0-eda-validation` 上（Chrome 的 T02 完成交接，已提交）。两者字段结构不同，直接合并必然冲突。归属与合并方式见第 0.5 节。
3. **分支命名不再用 `hw/<任务-简述>`。** 本文件此前建议的 `hw/t02-eda-import-check` 等四个名字，建立在「Chrome 尚未推送任何东西」这一未核实假设上，已作废。改为沿用 Chrome 已在用的 `chrome/<任务-简述>`，证据目录沿用 `review/chrome/<任务 ID>/`。

### 0.3 本轮主控的实际改动清单

快照时间 **2026-09-20 12:52 JST**，命令 `git status --porcelain`。状态码含义：`M ` 已暂存的修改；`A ` 已暂存的新增；`AM` 已暂存新增且暂存后又有修改。**这些状态码说明 `git add` 已执行；本文件此前「未执行 git add／commit／push」的说法与事实不符，已删除。** 截至快照时刻未执行 `git commit` 与 `git push`。

| 路径 | Git 状态 | 性质 |
| --- | --- | --- |
| `AGENTS.md` | `M ` 已暂存的修改 | 新增「进展同步（强制）」一节 |
| `docs/TEAM_PLAN.md` | `M ` 已暂存的修改 | 第 5 节进展同步条目、第 6 节 G4–G6 与放行链变更、第 7 节 |
| `docs/TASK_BOARD.md` | `M ` 已暂存的修改 | 新增「领取记录」一节、T14／T15 两行、T06 范围变更 |
| `docs/DECISIONS.md` | `AM` 已暂存新增，暂存后又有修改 | 决策记录 D-001–D-009 与待用户决策表 UD-01–UD-08 |
| `docs/OWNERSHIP.md` | `AM` 已暂存新增，暂存后又有修改 | 逐文件归属、编辑锁与未知项 U-01–U-32 |
| `docs/T06-DOMESTIC-EXECUTION.md` | `AM` 已暂存新增，暂存后又有修改 | T06 产出 |
| `docs/REFERENCES-INVENTORY.md` | `A ` 已暂存新增 | `references/` 引用盘点 |
| `docs/STATUS.md` | `A ` 已暂存新增 | 主控看板 |
| `docs/product/T13-PRODUCT-DIRECTION.md` | `A ` 已暂存新增 | T13 产出 |
| `docs/handoffs/chrome.md` | `AM` 已暂存新增，暂存后又有修改 | 本文件 |
| `review/claude/official-evidence/README.md`、`fig7-baseboard-back-native.png`、`pads-silkscreen-zoom.png`、`tools/measure_pads.py` | `A ` 已暂存新增 | 主控在本文件写作期间新增的官方资料证据目录 |

**本表是快照，不是稳定状态。** 本文件写作期间（12:43→12:52 JST，约 9 分钟）该清单已变化一次：`docs/OWNERSHIP.md`、`docs/T06-DOMESTIC-EXECUTION.md`、`docs/product/` 由未跟踪转为已暂存，并新增了 `review/claude/official-evidence/` 四个文件。**Chrome 使用前必须自行重跑 `git status --short` 与 `git log --oneline -1`，不要以本表为准。**

范围限定：**本文件本身不改动 `design/`、`references/`**；本轮主控其他改动即上表所列，集中在 `AGENTS.md`、`docs/` 与 `review/claude/`。这些改动何时进入仓库尚未确定，见第 0.4 节末段。

### 0.4 路径存在状态的逐项核对

核对时间 2026-09-20 12:43–12:52 JST（`review/` 行为 12:52 JST 的复核结果）。核对命令：`git ls-tree -r --name-only 3d5a112`、`git ls-tree -r --name-only origin/main`、`git ls-tree -r --name-only origin/chrome/t02-a0-eda-validation`、`git log --all --oneline -- <path>`、`ls -la`。**本文件此前把其中多个已存在的文件写成「尚未创建」，属状态误报，已按四类重新登记。**

| 路径 | 分类 | 核对依据 |
| --- | --- | --- |
| `docs/DESIGN_STATUS.md`、`docs/PROJECT_PLAN.md`、`docs/TASK_BOARD.md`、`docs/TEAM_PLAN.md`、`docs/handoffs/TEMPLATE.md` | 已提交到基线 `3d5a112` | `git ls-tree -r --name-only 3d5a112` |
| `docs/OWNERSHIP.md`、`docs/DECISIONS.md`、`docs/T06-DOMESTIC-EXECUTION.md`、`docs/product/T13-PRODUCT-DIRECTION.md`、`docs/REFERENCES-INVENTORY.md`、`docs/STATUS.md` | 仅存在于工作区（未提交） | `ls -la docs/`、`git status --porcelain`；`docs/product/` **非空** |
| `docs/handoffs/hiro.md` | 存在于 `origin/main`（`4261fcb`，PR #3 合并）但不在基线 | `git ls-tree -r --name-only origin/main` |
| `review/chrome/T02/**`、`tools/check_a0_static.py`、Chrome 版 `docs/handoffs/chrome.md` | 存在于 `origin/chrome/t02-a0-eda-validation`（`a6db65a`）但不在基线 | `git ls-tree -r --name-only origin/chrome/t02-a0-eda-validation` |
| `docs/handoffs/claude.md`、`docs/INTERFACE_CONTROL.md`、`mechanical/`、`product/`（根目录） | 确实尚未创建：工作区无，全部 ref 的历史中也无 | `ls -la`、`git log --all --oneline -- <path>` 无输出 |
| `review/claude/official-evidence/`（4 个文件） | 仅存在于工作区（已暂存，未提交），2026-09-20 12:46–12:48 JST 由主控新增 | `ls -laR review/`、`git status --porcelain` |
| `review/hiro/` | 本机存在但为**空目录**，未被 Git 跟踪；从 `3d5a112` 克隆得不到 | `ls -laR review/` |

Chrome 侧涉及的是 `docs/INTERFACE_CONTROL.md`（尚未创建，持有关系见第 5 节）与 `mechanical/`（尚未创建，由 Chrome 在 T03 创建）。`review/chrome/` 已由 Chrome 自己在远端建立，本地工作区尚无该目录。

注：`review/` 下现已同时出现 `review/chrome/`（远端分支）、`review/claude/`（工作区）与 `review/hiro/`（空目录）三个子目录，`docs/OWNERSHIP.md` 把整个 `review/` 归给 Hiro 的写法已被实际使用状况推翻，需由主控改为按子目录归属。

**基线之上的未提交规则改动（影响本包可执行性）。** 下列条文在基线 `3d5a112` 中**不存在**，只存在于本轮未提交的工作区改动中。实测：`git show 3d5a112:docs/TASK_BOARD.md | grep 领取记录` 无输出；`git show 3d5a112:AGENTS.md | grep 进展同步` 无输出；`git show 3d5a112:docs/TASK_BOARD.md | grep 'T14\|T15'` 无输出；`git show 3d5a112:docs/TEAM_PLAN.md` 中 G 节点只到 G5 且内容与现工作区不同。

| 未提交的规则改动 | 所在文件 | 本包中依赖它的位置 |
| --- | --- | --- |
| 「领取记录」一节 | `docs/TASK_BOARD.md` | 第 7 节的领取登记要求 |
| T14、T15 两行与 T06 范围变更 | `docs/TASK_BOARD.md` | 各任务节的依赖说明 |
| 「进展同步（强制）」一节 | `AGENTS.md` | 第 7 节的进展日志要求 |
| 第 5 节进展同步条目 | `docs/TEAM_PLAN.md` | 第 7 节的进展日志要求 |
| 第 6 节 G4–G6 与放行链变更、第 7 节 | `docs/TEAM_PLAN.md` | 各任务节的 G 节点对照 |

**后果：Chrome 若按 `3d5a112` 检出，在仓库里找不到这些依据，无法执行第 7 节的登记要求。** 两条可行路径由主控在派发时二选一并告知 Chrome：（甲）主控先把上述改动提交并推送，再把本包的输入提交号改为改动落库后的提交，并同步各任务节的输入提交号；（乙）Chrome 以 `3d5a112` 为**审查对象**、以主控推送后的提交为**规则依据**，两者分别登记。主控当前倾向（甲），但提交时点尚未确定，属本包的未闭合项。

### 0.5 交接文件归属（原“两份 chrome.md 的合并”，已由裁决取代）

| 文件 | 唯一负责人 | 用途 |
| --- | --- | --- |
| `docs/handoffs/chrome.md` | **Chrome** | Chrome 自己的领取登记、进展日志、完成交接。按 `docs/handoffs/TEMPLATE.md` 组织。主控不写入、不改写 |
| `docs/handoffs/claude-to-chrome.md`（本文件） | **Claude 主控** | 主控派发给 Chrome 的工作包与规则依据。Chrome 只读，不改写 |

本节原先规定的“由 Chrome 把主控版并入自己的版本”**已作废**。Chrome 无需做任何合并：PR #4 中你自己写的 `docs/handoffs/chrome.md` 原样保留即可，不会与本文件冲突。

第 7 节要求的进展日志表写进你自己的 `docs/handoffs/chrome.md`。

### 0.6 `design/` 内源文件与生成文件的关系

这是文件层面的事实，不含任何电气结论。

| 文件 | 类别 | 说明 |
| --- | --- | --- |
| `design/build_design.py` | 手写设计源 | `design/` 下唯一手写文件，278 行，仅用 Python 标准库 |
| `design/mosaico-dock-schematic.json` | 生成产物 | 类别为生成产物；**生成时点与所用输入快照未确认**，与基线 `references/` 的对应关系见 6.1 C-02，未闭合项见 6.5 U-11 |
| `design/mosaico-dock-placement.json` | 生成产物 | 同上；内容上只有摆放与板框丝印，无铜线布线 |
| `design/design-netlist.json` | 生成产物 | 同上（生成时点与输入快照未确认） |
| `design/bom-review.csv` | 生成产物 | 同上（生成时点与输入快照未确认）；不是可下单清单 |
| `design/pin-net-review.csv` | 生成产物 | 同上（生成时点与输入快照未确认）；该文件在忽略行尾后与基线重跑结果一致，但这不足以推断其余四个文件的生成时点 |

**不要把「由脚本一次运行写出」当作已确认事实。** 6.1 的 C-02 给出相反证据：用基线 `3d5a112` 自带的 `references/` 重跑脚本，四个文件与仓库已提交版本不一致。既然仓库版产物无法由仓库版输入重现，「一次运行写出」就是未闭合的推测。

`AGENTS.md` 要求“若转为 EDA 原生工程主导，先明确唯一设计源及脚本的保留用途”。该决定目前**未落到仓库任何文件**（`docs/OWNERSHIP.md` U-12 已登记），属 Chrome 在 T02 之后需要给出的结论。

---

## 1. T02：嘉立创 EDA 导入与工程可编辑性验证

**目标**　确认 `design/` 中的 A0 JSON 能否被嘉立创 EDA 实际导入，导入后能否打开、编辑、保存、导出，以及导入结果的网络连接是否与 `design/design-netlist.json`、`design/pin-net-review.csv` 对应。失败时给出可复现的失败原因与修复方案，而不是绕开。

**领取前必办**　远端已存在 `origin/chrome/t02-a0-eda-validation`（`a6db65a`）与对应 PR（其分支上的 `docs/handoffs/chrome.md` 自述为 PR #4，主控未核实该 PR 的当前状态）。Chrome 领取前必须先执行 `git fetch --all`，核对该分支是否由自己推送，并据实判断本任务是**继续该分支的未完成部分**，还是**改为复核既有证据**。两种情况的登记写法不同，不得在未核对前直接按新任务开工。

| 项目 | 内容 |
| --- | --- |
| 输入提交号 | `3d5a112`（规则依据的提交号见第 0.4 节末段） |
| 可编辑文件范围 | `design/`（含新建的 EDA 原生工程文件与导出物）；`review/chrome/T02/`（证据目录，含 `review/chrome/T02/evidence/`）；`tools/`（检查脚本）；`docs/handoffs/chrome.md` 的完成登记与进展日志部分；`docs/TASK_BOARD.md` 的状态与领取记录行 |
| 只读文件 | `README.md`、`AGENTS.md`、`CLAUDE.md`、`docs/PROJECT_PLAN.md`、`docs/TEAM_PLAN.md`、`docs/DESIGN_STATUS.md`、`docs/DECISIONS.md`、`docs/OWNERSHIP.md`、`docs/REFERENCES-INVENTORY.md`、`docs/STATUS.md`、`references/` |
| 已生效的使用限制 | **`docs/DECISIONS.md` D-006a（状态「生效」）规定：在 `design/` 生成产物与 `references/` 的不一致被查明并复核前，`design/` 下五个生成文件不得作为任何下游工作的输入基准。** T02 的导入对象正是这五个文件，因此导入验证只能作为**工具链与格式验证**，其结果不得被引用为「设计输入已确认」。D-006a 的解除条件是查明不一致成因（6.5 U-11）并完成复核，解除由 Chrome 决定受控版本、Hiro 复核、主控记录 |
| 编辑锁 | `docs/OWNERSHIP.md` 第 5 节：同一源文件同时只允许一位编辑者；领取先于修改；`design/` 下五个生成产物只能由 `design/build_design.py` 重新生成，不得同时手改生成文件与生成脚本 |
| 明确不要做的事 | 不在导入未成功时宣称工程可用；不同时手改生成文件与生成脚本（`AGENTS.md`「设计文件与生成文件」一节）；不借本任务顺手修订电路、更换器件或调整任何尺寸；不把“导入没有报错”写成“网络正确”；不输出任何制造文件 |

**验收条件（对应 `docs/TEAM_PLAN.md` 第 6 节 G0「工具与资料可用」）**　G0 要求“真正 EDA／CAD 能打开、编辑、保存和导出”。因此 T02 通过的条件是：导入、编辑、保存、导出四个动作各有实际执行记录，且网络对应关系经逐项核对并给出核对范围。任一动作未实际执行的，写“未验证”，不得以其余三项通过推断。主控负责核对证据完整性，不判断电气结论。

**本任务需要关闭的盘点条目**　C-01（确定性已成立，仅作背景）、C-02、C-03、C-05、C-06、C-07；对应未知项 U-11、U-12、U-13、U-19。其中 U-11 的说明责任在 Hiro（A0 生成者），Chrome 负责复现确认。

**需要提交的证据形式**

- 工具名称与版本号（嘉立创 EDA 的版本字符串），操作系统与操作日期。
- 导入操作的实际结果记录：成功或失败、报错原文、可复现的操作步骤。
- 导入后工程的可编辑性证据：保存与再次打开后的文件、导出物（导出格式由 Chrome 按实际可用项选择并说明）。
- 网络对应核对记录：核对了哪些网络、用什么方法核对、哪些未核对。逐项区分实际检查、推导与未检查。
- 若失败：失败点、原因判断、修复方案，以及修复后是否重跑。

**证据落盘路径**　`review/chrome/T02/evidence/`，审查报告 `review/chrome/T02/REPORT.md`。该路径与 Chrome 在远端分支上已采用的位置一致，也与 `README.md` 对 `review/` 的定义（“后续电气、机械、生产与实物验收记录”）一致。注：`docs/OWNERSHIP.md` 目前把整个 `review/` 归给 Hiro，该写法需由主控改为按子目录归属（`review/hiro/` 归 Hiro，`review/chrome/` 归 Chrome，`review/claude/` 归主控）；修订前 Chrome 按本节路径执行即可，不受影响。

**输出分支命名**　`chrome/t02-a0-eda-validation`（沿用 Chrome 已在用的分支；若改为复核既有证据，可在同一分支上续提交）。

**交接文件路径**　`docs/handoffs/chrome.md`，按 `docs/handoffs/TEMPLATE.md` 的字段结构补写 T02 的完成内容、验证与证据、未解决问题、接下来做什么。合并方式见第 0.5 节。

**依赖与后继任务**　依赖：A0（`3d5a112`），无其他前置。后继：T07（电路修订，`docs/TASK_BOARD.md` 已列 T02 为其依赖）；同时是“唯一设计源”决定（U-12）的前提。

---

## 2. T03：参数化 CAD 工作流与模块包络

**目标**　验证参数化 CAD 工作流本身可用（可编辑源文件、可重建导出），核实官方 ESP-Mosaico 模块尺寸资料的可获得性，建立模块包络与机械未知项清单，为 Hiro 的 H3 机械审查与后续 G1 接口冻结备料。

| 项目 | 内容 |
| --- | --- |
| 输入提交号 | `3d5a112` |
| 可编辑文件范围 | `mechanical/`（**确实尚未创建**，见第 0.4 节，由 Chrome 创建）；`review/chrome/T03/evidence/`（证据目录）；`docs/handoffs/chrome.md`；`docs/TASK_BOARD.md` 的状态行。**不含 `docs/INTERFACE_CONTROL.md`**，见第 5 节的持有关系 |
| 只读文件 | `design/`、`references/`、`docs/` 下其余文档，其中 `docs/DECISIONS.md`、`docs/OWNERSHIP.md`、`docs/REFERENCES-INVENTORY.md`、`docs/STATUS.md` 为本轮新增的只读依据 |
| 已生效的约束 | `docs/OWNERSHIP.md` U-01、U-02、U-16 已登记机械未知项及其解除条件与责任人；本任务的未知项表应与之对齐，不另起编号 |
| 明确不要做的事 | 不把未确认的坐标、间距、厚度、行程填成已知值；不从无比例尺照片推算精密制造坐标（`AGENTS.md`「工程事实与证据」一节）；不用常见间距冒充未知 Pogo 尺寸；不宣布机械接口冻结；不因为 CAD 能建模就认为包络已确认；不直接编辑 `docs/INTERFACE_CONTROL.md` |

**验收条件（对应 G0，并为 G1 备料）**　G0 部分：CAD 工具能打开、编辑、保存、导出，且导出可从源文件重建。G1 备料部分：模块包络与机械未知项分别成表，已知项标注官方资料名称、版本、日期与位置，未知项标注解除所需的证据形式与提供方。`docs/TASK_BOARD.md` 对 T03 的要求是“未知坐标不得填成已知”，这是本任务的硬性不通过条件。本任务本身不放行 G1，G1 需 Hiro 专项复核并由 Claude 记录冻结版本。

**本任务需要关闭的盘点条目**　C-13；对应未知项 U-01、U-02、U-16（全部为机械几何，数值由 Chrome 提交、Hiro 复核后填入）。

**需要提交的证据形式**

- CAD 工具名称与版本、工作流说明（参数如何驱动模型、导出如何重建）。
- 可编辑源文件与由其重建的导出文件，二者版本对应关系写明。
- 模块包络表：每一项标注来源（官方图纸／官方文档／实测／假设），假设单独标记。
- 机械未知项表：未知内容、当前影响的任务、解除条件（需要哪份资料或哪次实测）、由谁提供。
- 明确记录“用户目前没有 Mosaico 实物”对哪些项造成不可解除的缺口。注：`docs/TEAM_PLAN.md` 第 7 节记载实物预计 2026-09 下旬送达日本用户本人，`docs/TASK_BOARD.md` 新增的 T14 是对应的测量规程任务（该行为未提交改动，见第 0.4 节）。

**证据落盘路径**　`review/chrome/T03/evidence/`。

**输出分支命名**　`chrome/t03-cad-envelope`。

**交接文件路径**　`docs/handoffs/chrome.md`。

**依赖与后继任务**　依赖：当前需求（`README.md`、`docs/PROJECT_PLAN.md` 第 3 节），无任务前置，可与 T02 并行或串行。后继：T08（冻结共同接口）、T11（外壳与尺寸链）；产出以**待填条目**形式交给 `docs/INTERFACE_CONTROL.md` 的机械部分，由该文件的持有分支统一录入。

---

## 3. T04：精确尺寸资料、器件原厂资料与嘉立创供应／工艺证据

**目标**　整理并核验三类证据：ESP-Mosaico 精确机械与接口资料、候选器件的原厂资料（数据表版本、页码、引脚表、推荐 land pattern）、嘉立创的供应与工艺证据（是否有料、能否贴装、工艺例外）。确认项与未确认项必须分开列出。

| 项目 | 内容 |
| --- | --- |
| 输入提交号 | `3d5a112`，候选 BOM 见 `design/bom-review.csv` |
| 可编辑文件范围 | `references/`（含 `references/README.md`）；`review/chrome/T04/evidence/`（证据目录）；`docs/handoffs/chrome.md`；`docs/TASK_BOARD.md` 的状态行。**不含 `docs/INTERFACE_CONTROL.md`**，资料索引以待填条目形式产出，见第 5 节 |
| 只读文件 | `design/` 的生成产物（本任务不改设计，只核验证据）；`docs/` 下其余文档，其中 `docs/DECISIONS.md`、`docs/OWNERSHIP.md`、`docs/REFERENCES-INVENTORY.md`、`docs/STATUS.md` 为本轮新增的只读依据 |
| 与既有盘点的关系 | 工作区已有主控本轮写的 `docs/REFERENCES-INVENTORY.md`（**尚未提交到 `3d5a112`，仅存在于工作区**），其第 2–4 节已按实际引用做过盘点：已引用 25 项／未引用 6 项／引用但缓存缺失 1 项。**本任务不重做该盘点**，改为核对其口径并补判定，见下方 C-11 |
| 明确不要做的事 | 不把“器件库能下载”写成“国内有料且可贴装”（`docs/DESIGN_STATUS.md` O10）；不把缓存 JSON 里的库存、价格、SMT 字段当作嘉立创供应承诺；不联系供应商、不询价、不下单——`docs/TEAM_PLAN.md` 第 2 节要求这类动作须有对应用户授权，本交接包不构成授权；不静默替换关键器件；不把链接可达当作链接内容支持结论 |

**验收条件（对应 G0 的资料可用性，并为 G2、G3 备料）**　G0 要求“关键模块尺寸有官方图纸或实测，假设明确”。T04 通过的条件是：每条被采用的证据都记录来源链接、文档版本或发布日期、访问日期、页码或字段位置、以及由此得出的结论；确认与未确认分列；未确认项写明解除条件。`docs/TASK_BOARD.md` 已写明“辅助搜索可选，Chrome 对采用的证据负责”。器件的原厂推荐 land pattern 与缓存封装是否一致，属本任务核对范围，结论由 Chrome 提交、Hiro 复核。

**本任务需要关闭的盘点条目**　C-09、C-10、C-11、C-12、C-14、C-15、C-16；对应未知项 U-10、U-13、U-14、U-15、U-17、U-18、U-20、U-21、U-29、U-30。

**需要提交的证据形式**

- 资料索引表：器件或对象、资料类型、来源 URL、文档版本或发布日期、访问日期、使用到的页码或章节、结论、确认或未确认。
- 供应与工艺证据：取自何处、抓取或查询日期、该证据能支持与不能支持的结论各是什么。
- 与 `design/bom-review.csv` 的交叉核对结果：哪些位号的证据已闭合，哪些仍缺。
- 无法获取的资料：明确写“未知”，并写出解除它需要什么证据、由谁提供。

**证据落盘路径**　`review/chrome/T04/evidence/`。

**输出分支命名**　`chrome/t04-source-evidence`。

**交接文件路径**　`docs/handoffs/chrome.md`。

**依赖与后继任务**　依赖：当前候选 BOM。可与 T02、T03 并行。后继：T05（审查需要原厂资料）、T07（修订版 BOM 须基于可采购器件）、T08（接口冻结需精确尺寸证据）、T10 与 T12（制造检查）。

---

## 4. T05：对 Hiro 原 A0 的首次独立电气审查

**目标**　按 `AGENTS.md`「已指定的负责人」一节与 `docs/TEAM_PLAN.md` 第 4 节，原 A0 由 Hiro 会话产生，对其**首次独立技术审查由 Chrome 执行**。重点为电源状态与 I²C 电平，对应 `docs/DESIGN_STATUS.md` 的 O04、O05、O06、O09。本任务要求**先出逐项审查记录，再动手修订**；修订属 T07，不在 T05 范围内。

| 项目 | 内容 |
| --- | --- |
| 输入提交号 | `3d5a112`；审查对象为该提交的 `design/` A0 草案与 T04 提供的原厂资料 |
| 可编辑文件范围 | `review/chrome/T05/`（审查记录与 `review/chrome/T05/evidence/`）；`docs/DESIGN_STATUS.md` 的待解决项状态更新；`docs/handoffs/chrome.md`；`docs/TASK_BOARD.md` 的状态行 |
| 只读文件 | 本任务阶段 `design/build_design.py` 与全部生成产物为只读，审查未出结论前不得修改被审查对象；`references/`；`docs/DECISIONS.md`、`docs/OWNERSHIP.md`、`docs/REFERENCES-INVENTORY.md`、`docs/STATUS.md`、`docs/TEAM_PLAN.md`、`AGENTS.md` |
| 已生效的使用限制 | **`docs/DECISIONS.md` D-006a（状态「生效」）**：在 `design/` 生成产物与 `references/` 的不一致被查明并复核前，五个生成文件不得作为任何下游工作的输入基准。T05 的审查对象正是这五个文件，因此审查结论必须绑定「所审的是哪一版产物」，并声明该版是否为受控版本（当前无受控版本，见 U-12）。解除条件同第 1 节 |
| 明确不要做的事 | 不在审查记录完成前修改电路（`docs/TASK_BOARD.md` 对 T05 的验收条件即为“先完成审查记录再修订”）；不在证据不全时给出 `PASS`；不用自己的另一会话冒充独立审查（`docs/TEAM_PLAN.md` 第 2 节）；不自批硬件通过；不把 ERC 结果当作电源设计验证（`docs/TEAM_PLAN.md` 第 6 节明确禁止） |

**验收条件（对应 G2「电气冻结」的准备环节）**　G2 的放行证据是“电源全部状态、关键参数计算、引脚／封装、总线电平、ERC、问题关闭记录”，由 Chrome 准备、Hiro 批次复核、Claude 补充跨模型审查。T05 是这条链的第一步，本任务本身**不放行 G2**。T05 通过的条件是：

1. 逐项审查记录先于任何修订产生，且覆盖 O04、O05、O06、O09 四项及审查中新发现的问题。
2. 每一项给出独立计算或独立核对过程，不以原作者结论为前提。
3. 输出结论为 `PASS`、`CHANGES_REQUIRED` 或 `BLOCKED` 三者之一。**证据不全时不得使用 `PASS`**（`docs/TEAM_PLAN.md` 第 4 节对审查输出的统一要求，此处同样适用）。
4. 结论绑定具体提交号，并声明所审产物版本与 D-006a 的关系；`docs/TEAM_PLAN.md` 第 5 节规定修改关键网络、器件、板框、孔位或尺寸后旧报告对受影响范围失效。

**本任务需要关闭的盘点条目**　C-02（审查所依据的产物版本须明确）、C-04；对应未知项 U-04、U-05、U-06、U-09、U-11、U-13。

**需要提交的证据形式**

- 逐项审查记录：问题编号、审查对象（位号、网络、页）、依据的原厂资料与版本页码、独立计算过程与中间量、结论、结论等级。
- 全供电状态枚举：需覆盖底座 USB-C、电池、原生 USB-C 的组合状态（O06）。状态定义与各状态的判据由 Chrome 给出。
- I²C 电平与噪声裕量的核对过程（O04），含所依据的数据表条目位置。
- 电流、热、瞬态预算的计算过程（O05）。所有数值由 Chrome 提交、Hiro 复核后填入，主控不预设任何数值。
- 接口保护、测试点、掉电行为的核对范围与结论（O09）。
- 明确列出“已查范围”与“未查范围”，未查项不得留空。

**证据落盘路径**　审查记录 `review/chrome/T05/REPORT.md`，证据 `review/chrome/T05/evidence/`。此前建议的“放在 `design/` 或 `docs/` 下”与 `README.md` 对 `review/` 的定义冲突，已作废。`review/hiro/` 是 Hiro 的产物目录，与 `review/chrome/` 互不混用。

**输出分支命名**　`chrome/t05-a0-electrical-review`。

**交接文件路径**　`docs/handoffs/chrome.md`，并在其中给出审查记录文件的实际路径。

**依赖与后继任务**　依赖：当前 A0 与原厂资料（与 T04 部分互为输入，允许交替推进）。后继：T07（电路修订版与 H1 审查包整理）→ T09（Hiro H1 独立复核）→ G2 → T10。主控可按 `CLAUDE.md` 中“首次独立技术审查由 Chrome 执行，你可以补充跨模型质疑”一句补充质疑，但补充质疑不替代 Hiro 的独立复核。

---

## 5. 主控请求 Chrome 创建 `docs/INTERFACE_CONTROL.md`

该文件**确实尚未创建**（核对依据见第 0.4 节：工作区无，全部 ref 历史中也无）。`docs/TEAM_PLAN.md` 第 5 节已写明“该文件尚待创建，不能视为接口已经冻结”，同一文档第 2 节的固定责任表把它列为 Chrome 负责维护的产物但未加状态标注，读表时容易误认为已存在。

| 项目 | 约定 |
| --- | --- |
| 维护人 | Chrome（`docs/TEAM_PLAN.md` 第 2 节） |
| **写权持有** | **由分支 `chrome/interface-control-draft` 单独持有。T03、T04 只产出待填条目（机械包络条目、资料索引条目），不直接编辑该文件**，以符合 `docs/TEAM_PLAN.md` 第 2 节“同一源文件同时仅一位编辑者”与第 5 节“各角色使用自己的分支” |
| 合并方式 | T03、T04 的待填条目随各自分支交付，由持有分支的会话统一录入后合并。若 Chrome 以串行方式执行，可在完成 T03、T04 后再开持有分支，一次录入 |
| 覆盖范围 | 必须**同时覆盖电气与机械约束**，不得拆成两份各自漂移的文件 |
| 复核 | Hiro 复核关键接口（H1 电源与接口、H3 机械与装配） |
| 冻结版本记录 | 由 Claude 主控记录冻结版本与任务依赖，Claude 不填写其中的技术数值 |
| 当前状态与依赖 | 未创建，接口未冻结。**该文件未创建前 T08 无法开始**（T08 的任务即“冻结共同接口”，其依赖为 T03、T04、T07）；**T08 的产出即 G1 的放行证据，G1 未通过前 T10、T11 的前置不成立**。此前把“通过 G1”写成 T08 的前置条件，是把 T08 的验收结果倒挂为其开工条件，已更正 |

主控需要在该文件中看到的条目**类别**（只列类别，不填任何数值——全部数值由 Chrome 提交、Hiro 复核后填入）：

1. 坐标系与方向定义：底座顶视、模块前视与后视的方向约定，以及三者之间的镜像关系（对应 O03）。
2. 四触点接口：每个触点的网络归属、位置、几何特征与公差类别，以及来源资料的版本与页码。
3. Pogo 接口：型号类别、工作行程与压缩量、累计公差链的组成项、硬限位方式。
4. 板框与安装：主板轮廓、安装孔、禁布区、高度限制区。
5. 模块仓：模块包络、落入路径、导向与定位特征、上压框约束。
6. 电池空间：电池包外形空间、线束路径、插座极性与保护件位置的约束类别。
7. 按键与结构：按键中心与间距、十字帽与键帽的结构约束、肩键路径、握把厚度约束。
8. 电气接口约束：I²C 总线的电平域与上拉归属、供电路径的输入输出约束、掉电与上电顺序约束、保护与测试点位置约束。
9. 每条约束的证据栏：来源、版本或日期、页码或字段位置、状态（已确认／未确认／假设）。
10. 变更影响栏：该条约束变更后需要重新审核的电气、PCB、机械与制造范围（对应 `docs/TEAM_PLAN.md` 第 5 节“旧报告对受影响范围失效”）。
11. 冻结记录栏：冻结提交号、冻结日期、复核人、对应质量节点。此栏由 Claude 填写记录部分，技术内容仍由 Chrome 提供。

该文件建立后即成为电气与机械的共用约束源，`docs/PROJECT_PLAN.md` 第 3 节要求“机械与 PCB 共用一份接口约束”。

---

## 6. 本轮盘点交给 Chrome 的已知问题

以下是主控本轮在仓库层面的**文档级核对结果**，作为输入线索交给 Chrome。**这些是文件与证据链层面的观察，技术结论仍由 Chrome 判定、Hiro 复核。** 其中涉及机械或电气数值的条目一律记为未知，本文件不给出倾向性意见。

说明：`docs/REFERENCES-INVENTORY.md`、`docs/STATUS.md`、`docs/OWNERSHIP.md`、`docs/DECISIONS.md` 均已存在于工作区，但在基线提交 `3d5a112` 中**尚未提交**（见第 0.4 节），引用时以实际工作区状态为准。

四张表统一为六列：编号／观察／性质／归属任务／关闭条件／判定人。「未知项编号」列引用 `docs/OWNERSHIP.md` 第 4 节已有的 U-01–U-32 编号空间。**本节未按复核建议另起 U-01…U-09 一套新编号**，理由：`docs/OWNERSHIP.md` 已用 U-01 起登记 32 条未知项，其 U-32 条目本身就是在提示未知项编号空间冲突；再建一套会出现第三个含义不同的 U 空间。编号空间的最终统一由主控处理（U-32）。注：U-32 的原文说 `docs/DECISIONS.md` 第 4 节「同时用 U-01 起」，但该文件实际使用的是 `UD-01` 起的前缀（实测 `grep -c UD-0 docs/DECISIONS.md` 为 11，`grep -c '| U-0' docs/DECISIONS.md` 为 0）；U-32 的这一句已过期，需由主控更正，不影响本节的编号沿用。

### 6.1 `design/` 生成可复现性

| 编号 | 观察 | 性质 | 归属任务 | 关闭条件 | 判定人 |
| --- | --- | --- | --- | --- | --- |
| C-01 | `design/build_design.py`（278 行）可在 `/usr/bin/python3`（3.9.6）与 `/opt/homebrew/bin/python3.14`（3.14.7）下运行，退出码均为 0，两版解释器产出的五个文件逐字节相同，输出不依赖 Python 小版本。复现时间 2026-09-20 12:44–12:47 JST，在仓库外临时副本中执行 | 脚本可执行且确定性成立。**这不代表电路正确、封装正确或可生产** | T02（背景事实） | 无需关闭 | — |
| C-02 | 用**基线 `3d5a112` 自带的 `references/`**（与 `099af5b` 的 `references/` 逐字节相同，实测 `git diff --stat 099af5b 3d5a112 -- references/` 无输出）重跑脚本，`bom-review.csv`、`design-netlist.json`、`mosaico-dock-schematic.json`、`mosaico-dock-placement.json` 四个文件与仓库已提交版本不一致；`pin-net-review.csv` 在忽略行尾后一致。复现环境：`/usr/bin/python3`，Python 3.9.6（Clang 21.0.0），在仓库外临时副本中执行，仓库文件未被改动 | 仓库中已提交的生成产物**与仓库中任何一版 `references/` 都不对应，成因未知**（此句为观察，不是推导）。此前写的「对应一个更早的输入快照」是推导而非事实，且与 6.5 U-11「成因未知」自相矛盾，已删除：仓库历史中不存在能产出已提交产物的更早 `references/` 版本，所谓更早快照只能是未入库的假设状态 | T02、T05；U-11、U-12 | 由 A0 生成者说明生成时的输入快照，Chrome 复现确认，并决定 `design/` 的受控版本 | Hiro 说明，Chrome 复现确认并决定受控版本，Hiro 复核 |
| C-03 | 差异集中在 12 个位号（C1、C5、C7、C8、C9、C14、C15、C16、R20、R21、R22、U8），对应 6 个 LCSC 编码（C1591、C4177、C22978、C25819、C45783、C55266）：仓库版这些行的 Geometry status 为「Locally drawn placeholder」，重跑版为「Supplier library geometry」，即仓库版走脚本内置占位封装分支，重跑版走 `references/` 库封装分支 | 生成输入差异，非人为改动 | T02；U-11 | 同 C-02 | Chrome |
| C-04 | 其中 C45783（用于 C5、C7、C8）的封装字段在两版之间不同：仓库版 `design/bom-review.csv` 记为 C0603，重跑版与 `references/C45783.json` 的 `package` 字段一致，记为 C0805 | **正确封装未知。本文件不给出结论** | T05、T07、T10；U-13 | 原厂数据表与推荐 land pattern，注明版本与页码 | 由 Chrome 依原厂与供应资料提交，Hiro 复核后填入 |
| C-05 | 脚本（提交 `3d5a112` 版本）第 19 行 `if not p.exists(): return None`，`passive()`（第 39–42 行）在库缺失时不报错，静默回退到本地绘制的通用封装；IC 缺库则在 `add()` 处抛 `ValueError` 退出 | 无源器件存在静默失败路径，缺失输入不会中断构建 | T02、T07；U-19 | 一份改为显式失败或显式标记的脚本及其复现说明 | Chrome 实施，Hiro 复核 |
| C-06 | 生成产物中 `design/mosaico-dock-placement.json` 无任何铜线布线；文档名与板面丝印自带草案与禁止制造标注 | 与 `docs/DESIGN_STATUS.md` 的描述一致 | T02（背景事实） | 无需关闭 | — |
| C-07 | 脚本与未来 EDA 原生工程的从属关系尚未落到仓库任何文件，`AGENTS.md`「设计文件与生成文件」一节要求写明 | 待决定 | T02；U-12 | 一份写明唯一设计源、脚本保留用途与从属关系的决定 | Chrome 决定，Hiro 复核，Claude 记录 |

### 6.2 `references/` 引用与缺口

| 编号 | 观察 | 性质 | 归属任务 | 关闭条件 | 判定人 |
| --- | --- | --- | --- | --- | --- |
| C-08 | `references/` 共 31 个 `C*.json`（30 条成功记录、1 条 404 失败记录）。按 `design/` 实际引用交叉核对：25 个已引用、6 个未引用、1 个被引用但缓存缺失。明细见 `docs/REFERENCES-INVENTORY.md` 第 2–4 节（尚未提交到 `3d5a112`，仅存在于工作区） | 文件层面统计 | T04（核对口径） | 核对该文件的盘点口径是否成立 | Chrome |
| C-09 | R26 引用 `C23239`，但 `references/C23239.json` 在工作区与 git 历史中均不存在。该位号仍带着 LCSC 编号进入原理图、布局、网表与 BOM（`design/bom-review.csv` 在 `3d5a112` 中的第 52 行），封装为本地绘制占位 | 证据链缺口。`AGENTS.md`「设计文件与生成文件」一节规定“库缓存中未使用或误选的器件不能自动进入生产 BOM”，此处是其反向情形 | T04、T07；U-14 | 补齐库缓存并核对 land pattern，或更换器件 | Chrome 补齐来源，Hiro 复核 |
| C-10 | R28 的 LCSC 列为空，脚本自述采购编码待定；J3 与 TP1–TP12 无 LCSC 编码 | `design/bom-review.csv` 不是可下单清单 | T04、T07；U-15 | 选定器件并登记编码、数据表版本与供应状态 | Chrome 提交，Hiro 复核 |
| C-11 | 6 个缓存未被引用：C16043（内容为 404 记录，对应器件未知）、C165960、C2290、C22827、C23138、C28323。仓库中无抓取原因记录 | `docs/DESIGN_STATUS.md` **第 32 行**的 `references/` 行写明“应按实际引用建立清单”；`references/README.md` 只写到“`C*.json` 中包含研究过程的候选、未采用及可能查询失败的记录”，其全文不含“清单”二字（实测 `grep -n 清单 references/README.md` 无输出）。此前把该引文错归给 `references/README.md`，已更正 | T04；U-20 | **核对 `docs/REFERENCES-INVENTORY.md`（尚未提交到 `3d5a112`，仅存在于工作区）的盘点口径，并补这 6 个未引用编码的去留判定**（保留、重抓确认，或删除并在索引中写明原因）。清单本身已由主控建立，不必重做 | Chrome |
| C-12 | 缓存 JSON 无抓取时间与接口版本记录，缓存不可精确复现；其中的库存、价格、SMT 等字段是抓取当时快照；JSON 内的 `updated_at` 是服务端库记录更新时间，不是抓取时间 | **不构成嘉立创有料或可贴装的证据**（对应 O10） | T04；U-17 | 重新抓取并登记日期、接口版本与来源 | Chrome |
| C-13 | J3（Pogo 接口）在脚本中无 LCSC 编码，封装名标注为未核实几何，note 明写当前间距是占位值而非已发布尺寸 | **全部几何参数未知。本文件不给出任何数值** | T03、T08、T11；U-16 | 官方机械图纸或实测数据 | 由 Chrome 提交，Hiro 复核后填入 |
| C-14 | 同一候选 LDO 在三处文件中的型号写法不同：`docs/DESIGN_STATUS.md` 第 53 行写 `TLV75533`，`references/README.md` 第 21 行写 `TLV755P`（链接指向 `https://www.ti.com/product/TLV755P`），`design/bom-review.csv` 第 57 行写 `TLV75533PDBVR`（位号 U5，LCSC 编码 `C404027`，缓存封装名 `SOT-23-5_L3.0-W1.7-P0.95-LS2.8-BR`） | 文档写法差异，易在检索与数据表核对时错配。列出三种写法属文档级事实，不构成选型或封装结论 | T04、T07；U-30 | 原厂数据表确认完整型号 | 哪一种是正确器件标识由 Chrome 提交、Hiro 复核后填入 |

### 6.3 外部资料可达性

本节两条是**某一时刻的网络快照**，不是无时效事实。核对日期 2026-09-20，时间 12:45 JST（C-16 的三次重试为 12:45–12:46 JST）。工具：`curl 8.7.1 (x86_64-apple-darwin25.0) libcurl/8.7.1 (SecureTransport)`。命令：`curl -sS -L -o /dev/null -w '%{http_code}' --max-time 15 --retry 2 --retry-delay 2 <URL>`（C-16 的三次为 `--max-time 15 --retry 0`，逐次手动重试）。

| 编号 | 观察 | 性质 | 归属任务 | 关闭条件 | 判定人 |
| --- | --- | --- | --- | --- | --- |
| C-15 | `docs/DESIGN_STATUS.md`「官方参考入口」一节的 4 条链接，与 `references/README.md` 中 7 个 TI 器件入口（BQ24074、TPS61023、TPS2553、LM66100、TLV755P、TCA9535、TCA9517）、1 个器件库接口示例（`https://easyeda.com/api/products/C130204/components?version=6.4.19.5`），共 12 个 URL 在上述时刻均返回 HTTP 200（`docs/DESIGN_STATUS.md` 与 `references/README.md` 共有的 EasyEDA 文档格式链接只计一次） | **只核验了状态码，未读取任何页面或 PDF 内容。链接可达不等于内容支持文档中的论述。状态码结论随时可能失效** | T04；U-29 | **Chrome 在 T04 引用前须自行重核，并按第 3 节验收条件登记来源 URL、文档版本或发布日期、访问日期、页码与结论** | Chrome，Hiro 复核 |
| C-16 | `references/README.md` 第 24 行的 MAX17048 厂商页面 `https://www.analog.com/en/products/max17048.html` 连续三次请求均失败，返回码 000，三次报错均为 `curl: (92) HTTP/2 stream 1 was not closed cleanly: INTERNAL_ERROR (err 2)` | 是否真正不可达未知。可能是站点对自动化请求的限制，也可能是网络路径问题。MAX17048 为 analog.com 条目，不在 C-15 的 12 个 200 之内 | T04；U-29、U-04（同一器件） | 人工在浏览器中确认，或改用其他官方入口获取数据表并登记版本、页码与结论 | Chrome，Hiro 复核 |

### 6.4 计划文档层面的缺口（影响交接引用的可信度）

| 编号 | 观察 | 性质 | 归属任务 | 关闭条件 | 判定人 |
| --- | --- | --- | --- | --- | --- |
| C-17 | 仓库同时存在三套编号：`README.md` 与 `docs/PROJECT_PLAN.md` 的 M0–M7、`docs/TEAM_PLAN.md` 的质量节点（本轮未提交改动中已由 G0–G5 扩为 G0–G6）、`docs/TASK_BOARD.md` 的任务（本轮未提交改动中已由 T01–T13 扩为 T01–T15），没有任何文档给出三者的对应表 | 编号体系缺口 | 主控主责；U-23 | 由主控与 Chrome 共同确定后写入一份文档，其余文档统一引用。本交接包已在各任务节直接标注对应的 G 节点，作为局部对照 | Claude 主控与 Chrome |
| C-18 | G0 在 `docs/TASK_BOARD.md` 中没有任何任务被标注为其产出方；T10 的依赖写“G2 通过”，但无任务声明产出 G2 | 放行链追溯缺口 | 主控主责；U-23 | 同 C-17 | Claude 主控 |
| C-19 | `H1`／`H2` 在仓库内指两种不同事物：`README.md` 与 `docs/PROJECT_PLAN.md` 中指模块自身左右两侧的板间盲插连接器（需求是不使用），`docs/TEAM_PLAN.md` 与 `docs/TASK_BOARD.md` 中指 Hiro 的审查批次编号 | 术语歧义 | 全部交接与审查 | 阅读时按上下文区分；本文件中的 H1／H3 一律指 Hiro 的审查批次 | — |
| C-20 | 路径存在状态已按「已提交到基线／仅存在于工作区／存在于远端分支但不在基线／确实尚未创建」四类重新逐项核对，结果见第 0.4 节。此前本条把 `docs/OWNERSHIP.md`、`docs/DECISIONS.md`、`docs/T06-DOMESTIC-EXECUTION.md`、`docs/product/T13-PRODUCT-DIRECTION.md` 写成“尚未创建”，把 `docs/product/` 写成空目录，均为误报，已更正；`docs/handoffs/hiro.md` 的正确状态是“存在于 `origin/main` 但不在基线” | 状态误报已更正。把已存在的文件写成“尚未创建”与把未创建写成已存在同属误报 | T03（`mechanical/`）、第 5 节（`docs/INTERFACE_CONTROL.md`） | 见第 0.4 节各行；Chrome 侧只需创建 `mechanical/` 与 `docs/INTERFACE_CONTROL.md` | Chrome 创建其中两项，其余属主控范围 |
| C-21 | `docs/DESIGN_STATUS.md` 的 O01–O10 原文不含任务编号。主控已按文字推导出各项对应的阻塞任务（登记在 `docs/OWNERSHIP.md` 第 4 节，标记为推导），**该映射为推导结果，未经确认** | 推导，未确认 | 全部任务；U-22 | 请 Chrome 在编写 `docs/INTERFACE_CONTROL.md` 时确认每条待解决项的归属任务与关闭条件 | Chrome 确认，Hiro 在对应审查包中复核 |
| C-22 | `docs/TEAM_PLAN.md`、`CLAUDE.md`、`README.md`、`docs/PROJECT_PLAN.md`、`AGENTS.md` 共五份文档写明主控为 Claude Fable 5.1，本轮实际执行模型为 `claude-opus-5` | 已如实登记（`docs/DECISIONS.md` D-001） | 不影响 Chrome 的任务范围；U-28 | 用户决定是否同步修订文档表述 | 用户决定，Claude 主控执行 |

### 6.5 本轮明确记为未知的事项

以下事项主控**不给出结论**，列出是为了让 Chrome 知道它们尚未闭合。编号沿用 `docs/OWNERSHIP.md` 第 4 节的 U 编号空间（理由见本节开头）。

| 未知项编号 | 未知内容 | 归属任务 | 关闭条件 | 判定人 |
| --- | --- | --- | --- | --- |
| U-11 | 仓库版生成产物与仓库版 `references/` 不一致的具体成因（生成时间点、当时库内容、是否中途替换过库文件），以及**仓库版产物究竟对应哪一份输入快照**。按 `docs/TEAM_PLAN.md`，A0 由 Hiro 产生，需由 A0 生成者说明。与 6.1 C-02 互相指向 | T02、T05、T07 | A0 生成者说明生成时的输入快照，Chrome 复现确认 | Hiro 说明，Chrome 确认 |
| U-12 | 两版输出中哪一版应作为 `design/` 的受控版本，以及是否在 EDA 工程成为唯一设计源后废弃脚本产物；脚本与未来 EDA 工程的从属关系也未写入仓库任何文件 | T02、T07 | 一份写明唯一设计源、脚本保留用途与从属关系的决定 | Chrome 决定，Hiro 复核，Claude 记录 |
| U-13 | C45783 的正确封装（`design/bom-review.csv` 记 C0603，`references/C45783.json` 的 `package` 字段为 C0805） | T05、T07、T10 | 原厂数据表与推荐 land pattern，注明版本与页码 | Chrome 提交，Hiro 复核后填入 |
| U-14 | C23239 是否为 R26 的正确采购编码（仓库内无该缓存可核对） | T04、T07 | 补齐库缓存并核对 land pattern，或更换器件 | Chrome 补充，Hiro 复核 |
| U-15 | R28 的 LCSC 采购编码 | T04、T07 | 选定器件并登记编码、数据表版本与供应状态 | Chrome 提交，Hiro 复核后填入 |
| U-16 | J3 Pogo 接口的全部几何参数（间距、直径、位置、公差、朝向） | T03、T08、T11 | 官方机械图纸或实测数据 | Chrome 提交，Hiro 复核后填入 |
| U-21 | 25 个已引用编码的封装是否与原厂推荐 land pattern 一致；`design/bom-review.csv` 中这些条目的 Geometry status 当前均为待原厂核对 | T04、T07、T10 | 逐项核对数据表版本与页码 | Chrome 提交，Hiro 复核后填入 |
| U-18 | `C5832342`（功率电感，缓存自述料号 FTC201610S1R0MBCA）的缓存 SMT 字段为空的含义；`C2869734`（缓存类别 Pre-ordered Chips）与 `C544515`（`lcsc.url` 路径含 presales）的当前供应状态 | T04 | 向嘉立创核实库存、贴装可行性与交期 | Chrome 核实，Hiro 复核 |
| U-04、U-05、U-06、U-09 | `design/*.json` 的电气正确性、ERC、DRC 全部未验证。本轮只做证据链与可复现性盘点，不构成任何电气或结构结论 | T05、T07、T09 | 见 `docs/OWNERSHIP.md` 第 4 节各行的解除条件 | Chrome 提交，Hiro 复核 |
| U-29 | 6.3 两条网络快照的时效性：状态码结论随时失效，且未读取任何页面或 PDF 内容 | T04 | 引用前重核并登记访问日期、版本与页码 | Chrome，Hiro 复核 |
| —（本包新增，尚未在 `docs/OWNERSHIP.md` 登记） | 第 0.4 节末段所列未提交规则改动的提交时点未定，本包选（甲）还是（乙）尚未确定 | T01（主控） | 主控提交并推送，或明确告知 Chrome 采用（乙） | Claude 主控 |

以上每一项涉及数值的解除方式相同：**由 Chrome 提交证据，Hiro 复核后填入**；主控只负责记录状态与版本。

---

## 7. 领取、进展同步与完成

### 7.1 领取时

在 `docs/TASK_BOARD.md` 的任务表中把对应任务状态由 `READY` 改为 `IN_PROGRESS`（T02 须先按第 0.2 节核对远端后据实填写），并在“领取记录”表中登记领取人／平台、实际模型 ID 与推理档位、输入提交号、分支、文件范围、交接路径 `docs/handoffs/chrome.md`、登记日期。未登记的任务视为未领取。

依据：`docs/TASK_BOARD.md`「领取记录」一节。**该节在基线 `3d5a112` 中尚未包含，属本轮主控新增的未提交改动**（实测 `git show 3d5a112:docs/TASK_BOARD.md | grep 领取记录` 无输出）。若 Chrome 按 `3d5a112` 检出后找不到该节，按第 0.4 节末段的（乙）路径处理：以主控推送后的提交为规则依据，另行登记。

### 7.2 进展同步（强制）

`AGENTS.md`「进展同步（强制）」一节与 `docs/TEAM_PLAN.md` 第 5 节要求：各端在**四个时点**必须向 `docs/handoffs/<角色>.md` 的「进展日志」表推送一次记录——

1. 领取任务时；
2. 每完成一个可独立检查的中间步骤时；
3. 遇到阻塞时；
4. 会话即将结束或额度耗尽时。

记录允许很短，但必须是事实陈述，不写“进展顺利”这类无信息内容。**进展记录不等于交接，也不等于验收**：交接仍按 `docs/handoffs/TEMPLATE.md` 提交，技术结论仍需对应的检查与非作者复核。主控据此更新 `docs/STATUS.md`；某端超过一个工作日没有进展记录，主控向用户提示需要催办。

依据状态：该规则出自 `AGENTS.md`「进展同步（强制）」与 `docs/TEAM_PLAN.md` 第 5 节，**两处均为本轮主控新增的未提交改动，在基线 `3d5a112` 中尚未包含**（实测 `git show 3d5a112:AGENTS.md | grep 进展同步` 无输出）。决策记录见 `docs/DECISIONS.md` D-008a（该文件同样未提交）。

### 7.3 进展日志

下表为空表头，由 Chrome 按 7.2 的四个时点自行追加行。主控不代填。

| 日期 | 任务 ID | 当前在做什么 | 本次已确认的事实及依据 | 尚未确认 | 阻塞项 | 下一步 |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |

注：远端 `origin/chrome/t02-a0-eda-validation` 上的 `docs/handoffs/chrome.md` 也没有这张表（该规则晚于其提交产生）。按第 0.5 节合并时，把本表并入 Chrome 版即可。

### 7.4 完成时

按 `docs/handoffs/TEMPLATE.md` 的字段结构，在本文件 `docs/handoffs/chrome.md` 中补写该任务的完成内容、验证与证据、未解决问题、接下来做什么，并在任务板补充 PR 与证据链接。证据路径按各任务节的「证据落盘路径」填写。

### 7.5 其他

- 允许 T02–T05 串行执行，不必等待其他角色。`docs/TEAM_PLAN.md` 第 3 节规定普通工作不等待 Hiro 在线；但 T05 的结论进入 T07 后，H1 独立复核（T09）由 Hiro 执行，不得由 Chrome 自审代替。
- 无法完成时写清已查范围与未查范围，提交交接并暂停，不静默降级、不转移核心职责。

---

# 第二批派发：低额度模式（2026-09-20）

- 派发人：Claude 主控，实际模型 `claude-opus-5`。
- 背景：用户告知 Chrome 本周额度仅剩约 20%，指示「跑空额度再说」，并要求**频繁保存进展**，因为无法预知在哪一步耗尽。
- 输入提交：本文件所在提交（合入 main 后以 main 的提交号为准）。
- **本批次按「价值／额度」严格排序。做到哪一条算哪一条，不要求做完。**

## 0. 三条硬性执行纪律

1. **每完成一条任务就立刻 `commit` ＋ `push` ＋ 在 `docs/handoffs/chrome.md` 的进展日志追加一行。不要攒着最后一起提交。** 额度可能在任意一步耗尽，未推送的工作等于不存在。
2. **每条任务内部再拆小步，每小步结束也推一次。** 宁可提交历史碎，也不要丢工作。
3. **额度将尽时，优先把「已查到什么、还差什么、下一步该做什么」写进进展日志并推送**，而不是勉强完成当前任务。半成品加清晰交接，价值远高于没交接的完整工作。

## 1. 不要做的事（明确排除，避免浪费额度）

| 不要做 | 原因 |
| --- | --- |
| **不要修 F01（POGO_5V／BOOST_SW 网络误并）** | A0 原理图是按 V1.0 的四触点 ＋ I²C 扩展器架构画的，**该架构已作废**（V1.2 取消四触点，需求 R04 已修订为底座 MCU ＋ UART）。修好一个要重画的电路没有价值 |
| **不要修 F02（PCB 数据格式不被编辑器接受）** | 同上。PCB 需按新架构重做，修旧格式无意义 |
| **不要碰 `design/build_design.py`** | 按决策 D-014 该文件编辑权已临时移交 Claude 用于 T18，尚未交回 |
| 不要做 T03／T11 的机械 CAD | 实物未到货，关键几何全部未知 |
| 不要开始 T10 PCB 布局 | 架构刚变更，接口未冻结 |

**F03 可复现基线由 Claude 以 T18 提案形式完成**，产出在 `review/claude/T18/`，待你采纳。本批次不要求你审它；有余力时再看。

## 2. 任务清单（严格按此顺序）

### C1　H-01：背面 `RX`／`TX` 是否为 UART0、是否被日志占用

**为什么排第一**：成本低、直接决定方案 H 的通信通路是否可用。

要回答：ESP32-S31 上 UART0 的默认引脚；ESP-IDF 控制台输出的默认配置与默认值；ESP-Mosaico BSP 中控制台与日志的实际配置（给文件路径与行号）；官方文档「出厂固件经 USB CDC 输出日志」的原文出处；**在出厂固件下 UART0 是否空闲**。

结论表述为「可用／被占用／需改配置后可用／无法判定」，并写明依据与残留不确定性。**不得据此冻结任何设计。**

落盘：`review/chrome/H01/REPORT.md`。

### C2　H-02：背面 `5V` 焊盘的载流能力

**为什么排第二**：这是方案 H 最可能致命的技术点。底座需经该焊盘给整机供电**并充电**，而官方对该脚**无任何电流标注**。若载流不足，方案 H 的电源路径不成立。

依据：你在 T04 中已归档的官方 CoreBoard V1.0 原理图（`review/chrome/T04/evidence/`）。要查明：5V 网络的来源与去向、串在路径上的器件（限流开关、保护、二极管）、任何线宽或电流标注、V1.0 四触点的 `+` 脚与背面 `5V` 焊盘是否同网、以及 BTB 上 5V_IN 占用的并联脚数。

**注意 V1.0／V1.2 的适用边界**：原理图是 V1.0 的，背面焊盘是 V1.2 的，两者的对应关系本身就是一个待确认项，请显式处理，不要默认同网。

产出「可承载电流的判断范围 ＋ 未知项 ＋ 实物到货后如何验证」。**官方无数据时写 unknown，不要推一个数字出来当结论。**

落盘：`review/chrome/H02/REPORT.md`。

### C3　MCU 选型候选清单

依据需求 R04（已修订，见 `docs/PROJECT_PLAN.md`）：职责仅限扫键经 UART 上报、USB–UART 桥、驱动 `BOOT`／`RST` 做下载时序、读电池状态上报；禁止参与供电通断决策、禁止承担电池保护、禁止省电状态机、禁止持有持久化配置；**失效安全为硬要求**。

选型纪律：优先嘉立创常备料、优先带原生 USB 以省去独立 USB–UART 桥片、不选冷门封装。

产出 3–5 个候选，逐个给：型号、封装、原生 USB 支持、可用 IO 数、嘉立创供货与贴装状态（以实际查询结果为准，注明查询日期）、以及**不推荐的理由**。不要只列优点。

落盘：`review/chrome/H03-mcu/CANDIDATES.md`。

### C4　新架构的电源拓扑草案

底座 USB-C 输入 → 充电 → 电池 → 升压／稳压／限流／防反灌 → 背面 `5V` 焊盘。

**硬约束（R04 验收项）：供电路径不得经过 MCU 的软件判断。MCU 未烧录固件或人为停机时，Mosaico 仍须能正常工作。** 请在拓扑中显式标出这条路径，并说明负载开关的默认状态与上电时序如何保证该要求。

产出功能级拓扑与关键器件类别，**不要求选定型号**，不要求计算完成。

落盘：`review/chrome/H04-power/TOPOLOGY.md`。

### C5　`docs/INTERFACE_CONTROL.md` 改版为 V1.2 ／方案 H

现版 ICD-0.1-DRAFT 是按 V1.0 四触点写的，其中关于四触点的定义、镜像规则与坐标变换在 V1.2 上**没有对象**。

**若额度已紧张，不要重写全文**——只做一件事：在文首加一段适用范围声明，逐节标注哪些内容仅适用 V1.0、哪些仍然通用，并把待补的 V1.2 条目列成清单。**保留原内容不删**，改版留给额度恢复后。

## 3. 需要你知道的本轮变更

| 变更 | 出处 |
| --- | --- |
| 出货硬件为 BaseBoard V1.2，背面取消四扩展焊盘，调试焊盘由 6 个变 7 个 | `review/claude/hardware-revision/README.md` |
| 方案 A 不成立；方案 H（背面撞针 ＋ UART ＋ 底座 MCU）已定为方向 | `review/claude/option-h-pogo-uart-mcu.md` |
| 需求 R04 已由用户修订，允许一颗受限职责 MCU | `docs/PROJECT_PLAN.md` R04、`README.md` |
| README 已按 V1.2 与方案 H 全线对齐，架构图重画 | `README.md` |
| 主控已就本轮变更向 Hiro 派发 H0 专项复核 | `docs/handoffs/claude-to-hiro.md` |
| 主控本轮自述的四个错误 | 见 H0 审查包的「已知弱点」一节 |

## 4. 登记要求

领取时在 `docs/TASK_BOARD.md` 的领取记录表登记平台、实际模型 ID 与推理档位、输入提交号、分支、文件范围。进展日志写你自己的 `docs/handoffs/chrome.md`（该文件按 D-006 归你所有，主控不写入）。

**不自批硬件通过。** 本批次所有产出均为待复核材料，规定的独立复核由 Hiro 执行。
