# T18：可复现基线与输入冻结（修复提案）

- 日期：2026-09-20；执行：Claude 主控（临时接手 Chrome 的生成器维护，决策 D-014 文件移交）。
- 分支：`claude/t18-reproducible-baseline`；基线提交 `a9d383c`；领取提交 `94b30d5`。
- 输入：Chrome 的 T02 报告 F03 一节（`origin/chrome/t02-a0-eda-validation` 的 `review/chrome/T02/REPORT.md`）。未复用该分支的 `tools/check_a0_static.py`，结论全部自行验证。
- 运行环境：macOS / Python 3.9.6。

**本报告全部内容为提案，待 Chrome 采纳、Hiro 复核。未修复、未通过、未采纳。**

> **主控补记（2026-09-20）：** 本提案对 `design/build_design.py` 的改动，以及新增的
> `design/library-policy.json`、`design/references-lock.json`，曾因主控的一次 `git add -A`
> 误随 PR #10 合入 `main`，已由后续提交撤回。这三个文件**只存在于提案分支
> `claude/t18-reproducible-baseline`**，须经 Chrome 采纳后才可进入 `main`。
> `main` 上只保留本报告与 `regenerated/` 对照产物，供审阅使用。
> 误合入期间 `design/` 下的 5 份基线产物与 `references/` 未被改动。
本任务只改机制，不含任何硬件技术判断。器件选型、封装取舍、几何是否可接受，一律列入待裁决清单交 Chrome。
未执行 ERC、DRC、电气或机械验证；未执行 `git add` / `commit` / `push`；未修改 `design/` 下的 5 份基线产物与 `references/` 下任何文件。

---

## 一、改了什么

| 文件 | 类型 | 说明 |
| --- | --- | --- |
| `design/build_design.py` | 修改 | 三态库解析、硬失败、占位声明清单、锁文件校验、行尾统一、输出目录参数 |
| `design/library-policy.json` | 新增（清单） | 84 个位号的占位声明骨架。**内容待 Chrome 填写与裁决** |
| `design/references-lock.json` | 新增（清单） | 26 个被引用编码的路径、SHA-256 与器件标识；生成器启动时逐条校验 |
| `review/claude/T18/regenerated/` | 新增（对照） | 用当前 `references/` 重生成的 5 份产物，仅作对照，**不覆盖 `design/`** |
| `review/claude/T18/REPORT.md` | 新增 | 本文件 |

生成器 SHA-256：`d87580a7…f52727`（改前）→ `418d7fe1ba99e744fa2bc73d63dbe141d03ef4bca8d75748dec4efa2fd4a3ea6`（改后）。

### 1.1 机制改动逐条

| 原行为 | 位置（改前） | 新行为 |
| --- | --- | --- |
| `library()` 文件不存在返回 `None` | L19 | 返回三态 `MISSING`，记录位号、编码、期望路径 |
| `library()` 失败记录／`result` 为空同样返回 `None`，与上一条无法区分 | L21 | 返回三态 `INVALID`，细节含 `success` / `code` / `message` |
| 库解析成功但缺 `packageDetail` 时静默落入本地占位 | L211 | 判为 `INVALID`，与「缓存缺失」分开报出 |
| `raise ValueError('Missing verified library: '+code)` 只在未显式传 `pins` 时可达，且只报第一条、只报编码 | L28 | 判定移到按位号解析处，`add()` 与 `passive()` 两条路径同时生效；全程收集，一次性列出全部问题 |
| 空编码 `''` 同时表示「刻意占位」与「编码写错」 | L26、L39-40 | 取消语义重载：编码只表示编码，是否允许占位只由清单的 `policy` 列表示 |
| 无源器件缺库时静默取 `'C0603'` / `'R0603'` | L41-42 | 缺库即硬失败，除非清单显式标 `allow_placeholder` |
| `package` 兜底为字符串 `'TBD'` | L35 | 既无库又未显式给 `package` 时记为 `NO_PACKAGE` 硬失败 |
| 两处 `assert` 是脚本内唯一结构检查，`python3 -O` 可整体移除 | L33、L219 | 改为显式检查；脚本内 `assert` 数量为 0 |
| `group` 值不在四组内的器件静默不出现在原理图 | L183-195 | 渲染后核对「已渲染符号数 == 器件数」，失配即硬失败 |
| PCB LIB 头用反引号拼接且未经 `esc()` | L239 | 与原理图侧一致，经 `esc()` 处理（当前无值含反引号，输出逐字不变） |
| `csv.writer` 默认 `lineterminator='\r\n'` | L270、L273 | 显式 `lineterminator='\n'`，与 `.gitattributes` 的 `*.csv text eol=lf` 一致 |
| 输出目录写死 `design/`，任何试运行都覆盖已审查基线 | L267-269 | 新增 `--out-dir`；写入仓库内 `design/` 必须显式给出 `--allow-overwrite-baseline`，否则退出码 2 |
| 结束只打印器件数与网络数 | L277-278 | 追加：引用与可用缓存数、走占位的位号、被放行的位号、未被引用的缓存文件、清单与锁文件路径 |

`utf-8-sig`（CSV 的 UTF-8 BOM）与三份 JSON 的换行未改动：已提交版本与生成输出本来一致。这是有意保留，不是遗漏。

### 1.2 命令行

| 开关 | 用途 |
| --- | --- |
| `--out-dir PATH` | 产物输出目录。不给则默认仓库内 `design/`，而写入该目录需要 `--allow-overwrite-baseline` |
| `--allow-overwrite-baseline` | 显式允许覆盖已审查基线 |
| `--write-policy` | 登记模式：按仓库现状机械生成占位声明骨架，不生成产物 |
| `--write-lock` | 登记模式：按 `references/` 现状重新生成锁文件，不生成产物 |
| `--allow-missing` | 把库缺失／无效／未裁决降级为警告继续生成。默认关闭 |

`--allow-missing` 只能放行库可用性问题。位号未登记（`POLICY_MISSING`）、清单 `policy` 值非法、锁文件哈希或状态不符，一律不可降级——已实测验证（见 2.3）。

### 1.3 占位声明清单的性质

`design/library-policy.json` 的 84 行由 `--write-policy` 按仓库现状机械推出，`derived_from` 列写明依据：

| policy | 条数 | 机械依据 |
| --- | --- | --- |
| `require_library` | 69 | 该位号引用了一个 LCSC 编码，且该缓存当前可用 |
| `allow_placeholder` | 14 | 该位号在 `build_design.py` 中 `code` 为空串，本来就不引用任何库（R28、J3、TP1–TP12） |
| `unresolved` | 1 | 该位号引用了编码但缓存不可用（R26 / C23239）。生成器默认对该值硬失败 |

**这三类只是对仓库现状的机械记录，不是技术裁决。** `reason`、`placeholder_geometry` 两列一律留空，`review_state` 一律为「未审查」，须由 Chrome 逐行填写、Hiro 复核。
自动推导无法把一份缺失的缓存变成「允许占位」：缺失只会落进 `unresolved`，仍然硬失败。这条性质是有意设计的。

---

## 二、验证方法与结果

全部验证在仓库外的隔离副本 `/private/tmp/claude-501/.../scratchpad/T18/{base,orig1,orig2,dev,tA,tB,tC2,tC3,tD,tE,newrev6}` 中执行。验证期间 `design/` 下 5 份产物的 SHA-256 与开工时逐字相同（见 2.5）。

### 2.1 等价性：新生成器没有改变任何取值

| 比对 | 结果 |
| --- | --- |
| 满缓存下，新生成器 vs 原生成器：三份 JSON | **逐字相同** |
| 满缓存下，两份 CSV（去 CRLF、去 `--allow-missing` 标记后） | **逐字相同** |
| 删除 6 份缓存（C1591、C4177、C22978、C25819、C45783、C55266）后，新生成器 vs 仓库已提交基线：三份 JSON | **逐字相同** |
| 同上，两份 CSV（去标记后） | **逐字相同** |

第三、四行同时独立复核了分析阶段的结论：**已提交基线等价于「这 6 份缓存当时不可用」**，不是某个未知历史状态。

### 2.2 确定性：同输入两次运行逐字相同

```
$ python3 design/build_design.py --out-dir <A> --allow-missing
$ python3 design/build_design.py --out-dir <B> --allow-missing
$ for f in ...; do cmp -s <A>/$f <B>/$f && echo SAME $f; done
SAME  mosaico-dock-schematic.json
SAME  mosaico-dock-placement.json
SAME  design-netlist.json
SAME  bom-review.csv
SAME  pin-net-review.csv
```

`cmp` 逐字节比对，5 份全部相同，diff 为空。`python3 -O` 运行结果与正常运行同样逐字相同，且此时不再存在被优化开关移除的检查（脚本内 `assert` 数量为 0，删缓存在 `-O` 下退出码仍为 1）。

### 2.3 故障注入：原本静默的路径现在硬失败

| 实验 | 操作 | 改前（分析阶段实测） | 改后 |
| --- | --- | --- | --- |
| 删一份被引用缓存 | 删 `references/C45783.json` | 静默通过，退出码 0 | **退出码 1**，报出 C5 / C7 / C8 三个位号 + 编码 + 路径 + 「文件不存在」，另报锁文件状态变化；未写出任何产物 |
| 删三份被引用缓存 | 删 C130204 + C45783 + C55266 | 退出码 1，只报第一个编码 C130204，不报位号，另两份从未被提及 | **退出码 1**，11 项一次性列出：U1（含无法推导引脚表）、C5、C7、C8、U8 全部点名 |
| 失败记录（404） | 把 C1591 换成 `C16043.json` 的 404 内容 | 静默通过，退出码 0，6 个位号悄悄退回占位 | **退出码 1**，C1、C9、C14、C15、C16 全部报出，类别 `LIB_INVALID`，细节含 `success=False code=404` |
| 篡改锁文件哈希 | 把 C55266 的登记哈希改为 `000…0` | 不适用（无此机制） | **退出码 1**，报出 `references/C55266.json` 的登记哈希与实际哈希 |
| 本地改动缓存内容 | 向 `references/C25804.json` 追加一个换行 | 静默通过 | **退出码 1**，报出 C25804 的哈希不符 |
| 位号从清单中删除 | 删掉 U3 的清单条目 | 不适用（无此机制） | **退出码 1**，`POLICY_MISSING`；加 `--allow-missing` 仍为退出码 1 |

删缓存一例的实际输出：

```
阻断：下列问题必须解决后才能生成产物
位号       LCSC       文件                       类别                  细节
C5       C45783     references/C45783.json     LIB_MISSING         文件不存在
R26      C23239     references/C23239.json     POLICY_UNRESOLVED   清单标记为 unresolved（待 Chrome 裁决）；当前缓存状态：MISSING
C7       C45783     references/C45783.json     LIB_MISSING         文件不存在
C8       C45783     references/C45783.json     LIB_MISSING         文件不存在
-        C45783     references/C45783.json     LOCK_STATE_CHANGED  锁文件登记 state=OK，实际 state=MISSING（文件不存在）

共 5 项阻断，未写出任何产物。
```

### 2.4 当前仓库状态下的实际行为

不加 `--allow-missing` 直接运行，生成器**硬失败**：

```
$ python3 design/build_design.py --out-dir review/claude/T18/regenerated
阻断：下列问题必须解决后才能生成产物
R26      C23239     references/C23239.json     POLICY_UNRESOLVED   ...
共 1 项阻断，未写出任何产物。   (exit=1)
```

这是正确结果，不是缺陷：R26 引用的 C23239 在 `references/` 下没有文件，该位号该不该允许占位属 Chrome 裁决，生成器不替它决定。
因此本报告的对照产物是用 `--allow-missing` 生成的，被放行的位号只有 R26 一个，并在 stderr、stdout 摘要与 BOM 中都留了显式标记。

### 2.5 `design/` 未被触碰

| 文件 | SHA-256（开工时与完工时相同） |
| --- | --- |
| `design/design-netlist.json` | `9c608b08f3a22c1a978832f74b43d19be4a66b64d4d94657a888bfe9df9a57a5` |
| `design/mosaico-dock-placement.json` | `babe206c63c06c9a6448d3276f611697649145be219de4cc840c6636d33c3c34` |
| `design/mosaico-dock-schematic.json` | `4fb504f9a64ed3395eab75b35bfa626af4c694a5b0ea3208f118cb760f662fa9` |
| `design/bom-review.csv` | `edc39f64108ed5210b5fb91b2dade5c0f6d77b1eb1dd047993ffbe01da68a79f` |
| `design/pin-net-review.csv` | `bd5befdb62bff4d3d0f18951f2cd53e181838896cb4a42c444eef89a90370155` |

`git status` 只显示：`M design/build_design.py`、`?? design/library-policy.json`、`?? design/references-lock.json`，加 `review/claude/T18/` 下的新增文件。

### 2.6 行尾：一处与分析阶段描述不符的事实

分析阶段记为「每次运行后两份 CSV 在工作区必然显示为已修改」。实测更精确的情况是：

- 仓库中存储的 blob 与检出到工作区的文件**都是 LF**（`.gitattributes` 的 `*.csv text eol=lf` 生效）。
- 原生成器写出 CRLF 后，`git status` 报 ` M`，但 `git diff` 内容为空，并持续输出 `CRLF will be replaced by LF` 警告。已在独立临时仓库复现。

改用 `lineterminator='\n'` 后，`pin-net-review.csv` 与已提交版本**逐字节相同**（243 行，含 UTF-8 BOM），`bom-review.csv` 的差异收敛到 13 行——即真正的变更，不再被 243 行噪声掩盖。

---

## 三、重生成会带来的差异（逐位号）

对照：`design/`（已提交基线） vs `review/claude/T18/regenerated/`（当前 `references/` 重生成）。

总量：`design-netlist.json` 84 个器件中 12 个有差异；原理图 84 个 LIB 符号中 12 个有差异；PCB 84 个 LIB 封装中 12 个有差异；`bom-review.csv` 13 行有差异；`pin-net-review.csv` 逐字节相同。
**网络连接关系完全未变**：`nets`、`pins`、`xy`、`schxy` 四类字段逐条相同；原理图 `#@$` 之后的子图元（引脚、导线、网络标签）逐条相同。

### 3.1 封装名变化（3 个位号）

| 位号 | 值 | 来源编码 | 仓库版封装 | 重生成版封装 | 焊盘 | 焊盘中心距 | 裁决 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C5 | 22uF 25V X5R | C45783 | C0603 | **C0805** | 0.850×0.950 mm → 1.410×1.350 mm | 1.600 mm → 2.000 mm | **待 Chrome 裁决，本提案不判断孰对孰错** |
| C7 | 22uF 25V X5R | C45783 | C0603 | **C0805** | 同上 | 同上 | **待 Chrome 裁决，本提案不判断孰对孰错** |
| C8 | 22uF 25V X5R | C45783 | C0603 | **C0805** | 同上 | 同上 | **待 Chrome 裁决，本提案不判断孰对孰错** |

C0603 是缺库时脚本写死的字符串（与实际容值、耐压无关）；C0805 来自 C45783 缓存的 `c_para.package`，该缓存的 `packageDetail.title` 同样是 `C0805`，`result.title` 为 `CL21A226MAQNNNE`。哪一个正确不在本任务权限内。

### 3.2 仅几何与元数据变化（9 个位号，封装名不变）

| 位号 | 来源编码 | 封装名 | 仓库版焊盘 | 重生成版焊盘 | 焊盘中心距 | 新增图元 | 裁决 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | C1591 | C0603 | 0.850×0.950 mm | 0.800×0.900 mm | 1.600 → 1.400 mm | +6 条丝印 TRACK | **待 Chrome 裁决，本提案不判断孰对孰错** |
| C9 | C1591 | C0603 | 同上 | 同上 | 同上 | +6 条 TRACK | **待 Chrome 裁决，本提案不判断孰对孰错** |
| C14 | C1591 | C0603 | 同上 | 同上 | 同上 | +6 条 TRACK | **待 Chrome 裁决，本提案不判断孰对孰错** |
| C15 | C1591 | C0603 | 同上 | 同上 | 同上 | +6 条 TRACK | **待 Chrome 裁决，本提案不判断孰对孰错** |
| C16 | C1591 | C0603 | 同上 | 同上 | 同上 | +6 条 TRACK | **待 Chrome 裁决，本提案不判断孰对孰错** |
| R20 | C4177 | R0603 | 0.850×0.950 mm | 0.806×0.864 mm | 1.600 → 1.507 mm | +2 条 TRACK | **待 Chrome 裁决，本提案不判断孰对孰错** |
| R21 | C22978 | R0603 | 同上 | 同上 | 同上 | +2 条 TRACK | **待 Chrome 裁决，本提案不判断孰对孰错** |
| R22 | C25819 | R0603 | 同上 | 同上 | 同上 | +2 条 TRACK | **待 Chrome 裁决，本提案不判断孰对孰错** |
| U8 | C55266 | SOT-23-6_L2.9-W1.6-P0.95-LS2.8 | 0.800×0.600 mm | 1.100×0.600 mm | 2.000 → 2.700 mm（外侧脚） | +2 个 CIRCLE、+2 条 TRACK | **待 Chrome 裁决，本提案不判断孰对孰错** |

U8 的封装名在两版中都是 `SOT-23-6_L2.9-W1.6-P0.95-LS2.8`（`build_design.py` 第 95 行写死），而 C55266 缓存的 `packageDetail.title` 是 `SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BR`。重生成后 BOM 的 Footprint 列写着不带 `-BR` 的名字、PCB 几何却来自带 `-BR` 的库。**以哪一个为准、是否代表不同的 land pattern，待 Chrome 与原厂资料核对，本提案不判断孰对孰错。**

### 3.3 原理图侧：12 个位号的 `c_para` 元数据

同一组 12 个位号，原理图 LIB 头新增 `Manufacturer`、`Manufacturer Part`、`JLCPCB Part Class` 三项（C5/C7/C8 另含 `package` 由 C0603 变 C0805）。例：

| 位号 | 新增 Manufacturer | 新增 Manufacturer Part | 新增 JLCPCB Part Class |
| --- | --- | --- | --- |
| C1 | SAMSUNG(三星) | CL10B104KB8NNNC | Extended Part |
| C5 | SAMSUNG(三星) | CL21A226MAQNNNE | Basic Part |
| R20 | UNI-ROYAL(厚声) | 0603WAF1801T5E | Basic Part |

这些值来自缓存文件，不是本提案填写的。是否应进入 BOM 元数据，**待 Chrome 裁决**。

### 3.4 机制带来的 1 行差异（与库数据无关）

| 位号 | 差异 | 原因 |
| --- | --- | --- |
| R26 | `bom-review.csv` 的 Geometry status 追加 ` [UNRESOLVED via --allow-missing]` | 该位号引用的 C23239 无缓存文件，对照产物是用 `--allow-missing` 放行生成的 |

该标记只写进 BOM，不进 `design-netlist.json`，也不影响任何几何或网络。不加 `--allow-missing` 的正常运行不会产生该标记。

### 3.5 差异归类小结

| 归类 | 位号数 | 是否属硬件裁决 |
| --- | --- | --- |
| 封装名变化（C0603 → C0805） | 3（C5、C7、C8） | **是，属 Chrome** |
| 仅几何／元数据变化 | 9（C1、C9、C14、C15、C16、R20、R21、R22、U8） | **是，属 Chrome** |
| 机制标记 | 1（R26） | 否，机制产物 |
| 行尾 | 全部 CSV | 否，纯机制修正 |

---

## 四、未解决项与待 Chrome 裁决清单

本提案一行都没有替 Chrome 决定下列任何一条。

| 编号 | 事项 | 本提案已确认的事实 | 归属 |
| --- | --- | --- | --- |
| D1 | C5／C7／C8 的 22uF 应用 C0603 还是 C0805 | 差异来源为 C45783 缓存；焊盘 0.850×0.950 → 1.410×1.350 mm，中心距 1.600 → 2.000 mm | Chrome |
| D2 | 其余 9 个位号采用库几何还是保留已审查的本地占位几何 | 各位号的焊盘尺寸、中心距、新增丝印图元数见 3.2 | Chrome |
| D3 | 6 份缓存（C1591、C4177、C22978、C25819、C45783、C55266）各自冻结在「基线状态（视为不可用）」还是「当前缓存状态」 | 已证明基线 ≡ 这 6 份不可用；锁文件当前登记为 `OK` + 当前哈希 | Chrome |
| D4 | `library-policy.json` 每行填 `require_library` 还是 `allow_placeholder`，及各自 `reason` / `placeholder_geometry` | 只提供表结构、校验规则与按现状推出的骨架；`reason` 全空、`review_state` 全为「未审查」 | Chrome 填写，Hiro 复核 |
| D5 | R26 引用的 C23239：编码写错、器件未选定，还是缓存漏下载 | `references/C23239.json` 不存在；当前唯一的 `unresolved` 条目；不裁决就无法生成产物 | Chrome |
| D6 | R28（26.1k 1%）的实际 LCSC 采购编码 | 脚本注为 pending，`code` 为空串，占位封装 R0603 | Chrome |
| D7 | `footprint()` 静默丢弃的图元是否必须补回 | 25 份可用缓存共 595 个封装图元，保留 260、丢弃 **335**：SOLIDREGION 267、SVGNODE 25、CIRCLE 25、ARC 18。丢弃最多：C130204/U1 53、C54313/U2 38、C165948/J1 35 | Chrome |
| D8 | U8 封装名 `-BR` 后缀 | 脚本写死不带 `-BR`，C55266 缓存的 `packageDetail.title` 带 `-BR` | Chrome 与原厂资料核对 |
| D9 | 6 份未被引用的缓存（C16043、C165960、C22827、C2290、C23138、C28323）应删、应留为候选，还是应被某位号引用 | 其中 C16043 内容为 `success=false / 404 / Component not found`（74 字节），当前未被任何位号引用 | Chrome |
| D10 | J3 的 2.54 mm Pogo 占位间距 | 硬编码在 `build_design.py` 第 230-231 行；Pogo 真实尺寸未冻结 | Chrome 与机械冻结流程 |
| D11 | 生成器自身与清单文件的 SHA-256 不符时，应记为提示还是硬失败 | 本提案记为提示（生成器是受审查的代码，不是输入缓存；硬失败会使每次改动都必须重写锁文件） | Chrome |
| D12 | BOM 是否应为「声明的占位」增加可区分的第三种 Geometry status 值 | 本提案**有意未做**，以免在已审查基线的 schema 上引入 85 行噪声；占位区分现放在清单、锁文件与 stdout 摘要中 | Chrome |
| D13 | 是否保留 `--allow-overwrite-baseline` 这道写入保护 | 不给该开关时 `python3 design/build_design.py` 退出码 2；这改变了原有的无参调用习惯 | Chrome |
| D14 | 本提案是否采纳、以何顺序落地、改动后的产物是否可进入基线 | — | Chrome 决定，Hiro 复核 |

### 不在 T18 范围内

- F01（POGO_5V 与 BOOST_SW 导线重叠合并）、F02（PCB 数据格式不被编辑器接受，含 layerid、重复 uid、holeCenter、DRCRULE 结构）均未处理。uid 种子复用导致的父子 ID 冲突在机制上与本任务同源，但归属 F02。
- ERC、DRC、引脚电气类型（242 个引脚当前全为 Undefined）、电源电流与热计算、原厂引脚表核对、工厂采购与贴装能力、实物验收，全部未做。

---

## 五、复现

从仓库根目录执行。`<对照目录>` 应位于 `design/` 之外。

```sh
# 1. 校验当前输入是否与锁文件一致，并生成对照产物
#    当前仓库状态下这一步会硬失败（R26 / C23239 未裁决），这是预期结果
python3 design/build_design.py --out-dir <对照目录>

# 2. 明确放行 R26 后生成对照产物（stderr、stdout 与 BOM 均留标记）
python3 design/build_design.py --out-dir <对照目录> --allow-missing

# 3. 确定性：换一个目录再跑一次，逐字节比对
python3 design/build_design.py --out-dir <对照目录2> --allow-missing
for f in mosaico-dock-schematic.json mosaico-dock-placement.json design-netlist.json \
         bom-review.csv pin-net-review.csv; do
  cmp -s <对照目录>/$f <对照目录2>/$f && echo "SAME  $f" || echo "DIFF  $f"
done

# 4. 与已提交基线比较
diff <(tr -d '\r' < design/bom-review.csv) <对照目录>/bom-review.csv
cmp design/pin-net-review.csv <对照目录>/pin-net-review.csv   # 逐字节相同

# 5. 重新登记（改动清单或 references/ 后）
python3 design/build_design.py --write-policy   # 只重建骨架；已填内容会被覆盖，先备份
python3 design/build_design.py --write-lock
```

故障注入请在仓库外的副本中做，例如：

```sh
cp -R design references <仓库外副本>/ && cd <仓库外副本>
rm references/C45783.json
python3 design/build_design.py --out-dir ./out     # 预期退出码 1，报出 C5/C7/C8
```

`--write-policy` 会覆盖 `design/library-policy.json` 的全部内容，包括 Chrome 已填写的 `reason` 与 `review_state`。这是当前实现的局限，**在 Chrome 开始填写清单之前应先解决**（例如改为只补新增位号、保留已有列）。本提案未实现该保护。

---

## 六、边界与性质声明

- 本提案**未做 ERC、DRC、电气或机械验证**，不构成任何硬件结论。
- 本提案**不判断**哪个封装正确、哪套几何应被采用、哪些位号允许占位、哪些被丢弃的图元必须补回。全部列入第四节交 Chrome。
- 生成器改动经实测在相同输入下产出逐字节相同的结果，因此「没有改变任何器件、封装、网络或坐标取值」是可验证的事实，而不是声明。
- `design/library-policy.json` 的内容是按仓库现状机械推出的骨架，**不是审查结论**，每行 `review_state` 均为「未审查」。
- `design/references-lock.json` 登记的是「当前 `references/` 的状态」，**不代表冻结点已确定**（见 D3）。
- 本报告一切结论为**提案，待 Chrome 采纳、Hiro 复核**，不构成「已修复」「已通过」「已采纳」。
- 未执行 `git add` / `git commit` / `git push`；未修改 `design/` 下 5 份产物与 `references/` 下任何文件。

## 七、交接说明

下一步需要 Chrome 的输入：

1. 裁决 D5（R26 / C23239）。在此之前生成器无法在不加 `--allow-missing` 的情况下产出任何产物。
2. 逐行填写 `design/library-policy.json` 的 `policy`、`reason`、`placeholder_geometry`，并把 `review_state` 改为实际状态；填写前先处理第五节末尾提到的 `--write-policy` 覆盖问题。
3. 裁决 D3（6 份缓存的冻结点），据此决定 `design/references-lock.json` 首版应登记为哪个状态。
4. 裁决 D1、D2、D8：若采纳库几何，`design/` 下的 5 份产物需要作为明确的设计变更重新审查，而不是静默覆盖。
5. 裁决 D11、D12、D13 三项机制取舍。

本任务未向 `docs/` 写入任何进展记录或交接文件；按 `AGENTS.md` 的进展同步要求，该记录应由主控在 `docs/handoffs/` 下补齐。
