提案 · 未冻结 · 由 Claude 主控（claude-opus-5）起草 · 不得据以制造

# R0 资料索引

本文件是 `docs/handoffs/claude-to-grok.md`（R0 审查包）的配套资料索引。用途只有一个：告诉你每份资料在仓库的哪里、它**能证明什么**。

规则：

1. 本索引**不含任何结论性提示**。「能证明什么」一栏写的是该文件的证据地位（它是谁写的、属于哪一类），不是它的结论对不对。
2. 所有路径相对仓库根目录。除特别标注外，均在领取时的 `origin/main` 上。
3. 列在「审查对象」组的文件是**被审对象**，其中的数值、结论与自述一律是待检验主张，**不得充当你结论的依据**（`docs/handoffs/claude-to-grok.md` 第 3 节的引用规则）。
4. 本索引不完备也不排他：仓库里还有很多文件，你需要时可自行查阅；但审查结论只针对审查包第 2 节划定的三项范围。

---

## 1. 固定基线 BSP 源码

**基线：** `esp-mosaico/esp-mosaico-bsp`，官方固定提交 **`392860b1d1a123c3377947074b2af1f600e86c5d`**。

**归档位置：** `review/chrome/D1-module-interface/evidence/bsp/`（以下「归档根」即指此目录，各文件路径接在其后）。这份归档由 Chrome 在 D1 任务中取得，Hiro 在 H0 中核过其与官方提交树的一致性；**你仍应自行重算哈希后再用**，不要默认它没被改过。

| 归档根下的相对路径 | 能证明什么 |
| --- | --- |
| `SOURCE_INDEX.json` | 登记本归档 12 个文件各自的来源 URL、字节数、SHA-256 与 git blob SHA-1，以及是否与该提交的树一致；用它核验你手上的源码就是基线本身 |
| `LICENSE` | 归档所依据的上游许可文本 |
| `components/esp-mosaico-bsp/include/bsp/esp_mosaico.h` | BSP 对外公开的板级定义：板卡变体枚举、板载外设与总线的引脚宏、版本相关声明 |
| `components/esp-mosaico-bsp/include/bsp/subboard.h` | 模块槽（子板）对外 API 的声明：槽位枚举、引脚映射与初始化接口的签名 |
| `components/esp-mosaico-bsp/onboard/subboard.c` | 模块槽的实现：左右槽引脚映射表、槽位上电与总线初始化顺序、对槽内特定引脚的配置动作 |
| `components/mosaico_module_mgr/include/mosaico_module_mgr.h` | 模块管理器的公开 API 与数据结构：板卡类型枚举、描述符字段、事件与订阅、认领／释放与扫描参数的声明 |
| `components/mosaico_module_mgr/mosaico_module_mgr.c` | 模块管理器的实现：EEPROM 读取时序与长度、描述符解析与校验、扫描与去抖、认领／释放、事件派发与拔出处理 |
| `components/mosaico_module_mgr/README.md` | 上游对模块管理器的自述文档，可与实现对照，但**上游文档也不等于实现** |
| `components/mosaico_module_mgr/CMakeLists.txt`、`components/mosaico_module_mgr/idf_component.yml` | 模块管理器组件的依赖与构建声明，可用于核对被审组件的依赖写法是否合理 |
| `components/esp-mosaico-bsp/CMakeLists.txt`、`components/esp-mosaico-bsp/idf_component.yml` | BSP 组件的依赖与构建声明 |
| `components/mosaico_module_interact/mosaico_module_interact.c` | 上游一个使用模块管理器的实例实现，可用作「管理器 API 应当如何被调用」的旁证 |

**归档缺什么（重要）：** 板级初始化实现 `components/esp-mosaico-bsp/onboard/esp_mosaico.c` **不在** `SOURCE_INDEX.json` 所列 12 个文件内，因此不在归档中。审查包第 3 节 Q5 需要它。请自行从同一固定提交取得：

```
https://raw.githubusercontent.com/esp-mosaico/esp-mosaico-bsp/392860b1d1a123c3377947074b2af1f600e86c5d/components/esp-mosaico-bsp/onboard/esp_mosaico.c
```

取得后在报告中登记字节数与 SHA-256，说明来源 URL，并把临时文件放在仓库外（不要提交进仓库，那会超出你的写入范围）。若其他题目也需要归档外的上游文件，按同样方式处理并登记。

---

## 2. 官方资料

| 路径 | 能证明什么 |
| --- | --- |
| `review/chrome/D1-module-interface/evidence/user_guide_v10.rst` | 官方 ESP-Mosaico 用户指南 **V1.0** 原文（Hiro 在 H0 中比对过它与官方固定提交 `3c0f6321d2be0398766dcf5c019990772e0f8e54` 的原始文件一致）。其中含官方给出的扩展排针引脚表、接口与外设描述。**这是 V1.0 文档；出货硬件为 V1.2，两者的差异本身是项目的已知问题，引用时请标明版本** |
| `review/chrome/D1-module-interface/evidence/DOCUMENT_SOURCES.json` | 登记上述官方文档的来源与哈希，用于核验你读的是归档原件 |
| `references/official-v12/expansion_v121_zh.pdf`、`expansion_v121_en.pdf` | 官方《ESP-MOSAICO 扩展指南》，文件名声明仅适用于 1.2.1 版本及以上；含底板内外侧图与官方扩展取电流程 |
| `references/official-v12/assembly_zh.pdf`、`assembly_en.pdf` | 官方装配指南 |
| `references/official-v12/exp_backplane.png` | 扩展指南中底板内侧图的渲染件 |
| `references/official-v12/README.md` | 上述四份 PDF 的归档来源（MakerWorld 官方模型页）、归档日期与归档人；用于判断这批资料的证据地位 |
| `references/README.md` | 官方用户指南、CoreBoard V1.0 原理图、底板背面图的官方链接入口；PDF 本身不入库，需要时从来源重取 |
| `references/C*.json` | A0 阶段生成脚本使用的器件库 JSON（立创编号命名）。与本次三项范围无直接关系，列出只为说明 `references/` 下这些文件是什么 |

---

## 3. 审查对象文件清单

**以下全部是被审对象。** 其中的数值、结论、自述的「已核实」与贴出的运行输出，都是待检验主张。

### 3.1 范围 (a)：`hardware/eeprom/`

| 路径 | 是什么 |
| --- | --- |
| `hardware/eeprom/README.md` | 目录导读与快速使用命令；自述各文件职责与边界 |
| `hardware/eeprom/mosaico_eeprom_v1.py` | 身份镜像的生成／校验／转储／C 数组导出／烧写工具，含 `selftest`；纯标准库。**它是镜像数值的唯一来源** |
| `hardware/eeprom/IDENTITY.md` | 逐字段取值与理由、param 布局、校验分段表、对「BSP 做什么／不做什么」的断言、假设清单。**它是理由的唯一来源** |
| `hardware/eeprom/PROGRAMMING.md` | 三条烧写路径、器件页写与写周期、接线前提、验收清单、假设清单 |
| `hardware/eeprom/eeprom_program_example.c` | 主机侧烧写示例固件（ESP-IDF），自称 API 已逐一核对 |
| `hardware/eeprom/sample_handle.bin` | 样例镜像二进制（二进制无法携带提案抬头，以 `README.md` 与 `SHA256SUMS` 代替） |
| `hardware/eeprom/sample_handle_image.h` | 由工具从样例镜像生成的 C 数组 |
| `hardware/eeprom/SHA256SUMS` | 样例镜像与生成头文件的 SHA-256 登记 |
| `hardware/eeprom/SERIALS.csv` | 序列号登记表 |

### 3.2 范围 (b)：`firmware/dock_handle/`

| 路径 | 是什么 |
| --- | --- |
| `firmware/dock_handle/README.md` | 组件说明、设计要点表、引脚表转抄、**第 6 节自称的「API 核实表」**、构建方式、到货验证顺序、假设清单、已知限制、依据索引 |
| `firmware/dock_handle/dock_handle.c` | 驱动实现：认领、身份核对、引脚配置、轮询与去抖、事件队列、热插拔与释放、反初始化 |
| `firmware/dock_handle/include/dock_handle.h` | 公共 API 声明 |
| `firmware/dock_handle/include/dock_handle_pinmap.h` | KEY_* → GPIO 宏表，自称是 `hardware/module-board/PINMAP.md` 的镜像 |
| `firmware/dock_handle/Kconfig` | 轮询周期、去抖次数、队列深度、身份核对开关等构建期选项 |
| `firmware/dock_handle/CMakeLists.txt`、`firmware/dock_handle/idf_component.yml` | 组件构建与依赖声明（依赖自称固定到基线提交） |
| `firmware/dock_handle/examples/keytest/`（`CMakeLists.txt`、`sdkconfig.defaults`、`main/main.c`、`main/CMakeLists.txt`、`main/Kconfig.projbuild`、`main/idf_component.yml`） | 最小测试工程：槽扫描、认领、身份字段打印、十键自检、只读 I²C 地址扫描 |
| `firmware/dock_handle/PC_LINK.md` | 与电脑连接的软件通路建议（自述不做实现），含对一组 Kconfig 符号是否存在的核实结果 |

**跨分支输入（不在 `main`）：**

| 取法 | 是什么 |
| --- | --- |
| `git show origin/claude/design-d/module-board:hardware/module-board/PINMAP.md` | 模块板分支的引脚分配表，被固件与 EEPROM 两处引为 KEY_* → GPIO 的**唯一权威来源** |
| `git show origin/claude/design-d/module-board:hardware/module-board/netlist.yaml` | 模块板网表（含器件选型与连接）；本次不审模块板本身，仅在需要核对引用一致性时查阅 |
| `git show origin/claude/design-d/module-board:hardware/module-board/check_netlist.py` | 模块板网表检查脚本；同上，仅供查阅 |

### 3.3 范围 (c)：`hardware/` 三份文档

| 路径 | 是什么 |
| --- | --- |
| `hardware/ICD-0.2-DRAFT.md` | 方案 D＋G 的接口控制文档草案：坐标系、左槽 20 针合同、弹簧针接口与防呆论证、电气与机械约束、I²C 地址表、EEPROM 身份要求、固件接口要求、网络命名总表、冻结登记 |
| `hardware/ASSUMPTIONS.md` | 假设总登记表：每条假设的使用文件、若错影响、到货验证步骤、器材、负责人、状态；以及硬约束与假设的对应、其他分支假设的待吸收清单、关闭记录与使用规则 |
| `hardware/G6-TEST-PLAN.md` | 日本端整机验收测试计划：版本绑定与记录字段、器材清单、阈值登记表、A–H 各段测试项、故障树、判定与遗留、记录模板 |

### 3.4 背景（可读，但不是本次审查对象）

| 路径 | 是什么 |
| --- | --- |
| `review/chrome/D1-module-interface/`（`README.md`、`LEFT_SLOT.md`、`BSP_AND_EEPROM.md`、`DOCUMENT_BOUNDARIES.md`） | Chrome 的 D1 分析文档，是上述设计的输入之一。**它已在 H0 中被独立复核过，本次不重审；且按审查包第 3 节规则，它的数值不得充当你复算题答案的来源** |
| `review/hiro/H0/REPORT.md`、`review/hiro/H0/MATERIALS.md` | **本次不读。** 这是另一轮（H0）独立复核的报告，其中完整列出该轮提出的发现清单，并包含若干已由该轮算出的数值结果。读它会把你的判断锚定在别人的结论上，而本次要的正是**独立**的一遍。若你确实需要了解 H0 的范围边界，本包正文第 4 节已摘录相关两句，不必打开原文。 |
| `docs/handoffs/claude-to-hiro.md` | **本次不读。** 这是 H0 的派发包，其正文逐条写出了该轮的技术要点与源码行号。需要审查包写法的示范请看 `docs/handoffs/TEMPLATE.md`。 |
| `docs/handoffs/claude.md` | 主控交接：当前方案、本轮事实、**第 2 节自述错误**、待用户决定事项、各端状态、未解决问题 |
| `docs/STATUS.md`、`docs/TASK_BOARD.md`、`docs/DESIGN_STATUS.md` | 项目当前状态、任务队列与领取记录、设计成熟度登记 |
| `docs/INTERFACE_CONTROL.md` | V1.0 四触点时期的历史接口文档，文首有适用范围警示。**不是本次审查对象**，列出只为避免与 `hardware/ICD-0.2-DRAFT.md` 混淆 |
| `design/`、`review/claude/`、`review/chrome/` 其余目录 | A0 草案与更早阶段的分析。按审查包第 4 节，均不在本次范围 |

---

## 4. 项目决策与边界

### 4.1 `docs/TEAM_PLAN.md` 关键条款

| 位置 | 能证明什么 |
| --- | --- |
| 第 1 节「谁主导」 | 分工的权威来源：Claude 主控、Chrome 硬件总设计、Hiro 独立复核；**Cursor／Grok 不承担核心设计、强制审查或任何交付的唯一责任**；选择模型时须记录实际模型 ID 与推理档位，额度耗尽时提交交接并暂停、不静默降级 |
| 第 2 节固定责任表 | Cursor／Grok 一行写明「可选辅助，默认无核心任务」，不编辑权威电路／PCB／CAD、不选定最终器件、不批准制造、**不作为关键路径依赖**；表后一段写明「辅助资料不能直接进入冻结设计，**不用模型投票决定工程正确性**」 |
| 第 3 节「主控如何工作」 | 任务状态以仓库记录为准，不能只保存在聊天记忆里 |
| 第 4 节批次审查 | 审查包的构成要求；先独立查证与计算、再对照作者结论；输出只取 `PASS`／`CHANGES_REQUIRED`／`BLOCKED`，**证据不全时不能用 `PASS`**；关机前提交并推送、注明复核过的提交号；**不得自动让 Cursor／Grok 代签**规定的 GPT 独立硬件审查 |
| 第 5 节工程交接约定 | 各角色用自己的 worktree 与分支；**进展同步是强制项**；PR 须记录所用模型、输入提交号、改动文件、工程依据、已做检查、未做检查与风险；报告必须对应一个具体提交版本 |
| 第 6 节质量节点 | G0–G6 的放行证据与责任；G3 的远程验收补偿约束；**测试规程、判据与故障树须在发运前写成用户可独立执行的步骤，不能假设日本端具备工程调试能力**（范围 (c) 第 3、4 问的判据出处） |
| 第 7 节排期原则 | D-017 主循环：先带假设做完设计 → 实物核尺寸 → 逐条关闭假设 → 打板 → 日本验证。解释了为什么现在的设计文件允许大量 `ASSUMPTION` |

### 4.2 `docs/DECISIONS.md` 关键条目

> **读取限制：** 本次只读 **D-013、D-015、D-018、D-020** 四条——它们是本次派发的法理依据（非作者复核红线、主控模型切换、Grok 加入与授权边界）。**其余条目本次不读**：该文件还登记了此前各轮复核的结论与数值，读了同样会把判断锚定在他人结论上。

| 编号 | 能证明什么 |
| --- | --- |
| D-001 | 主控实际执行模型与文档指定模型不一致时的登记方式；本项目「如实登记实际模型 ID」的先例 |
| D-003 | 本会话不启动也不核实其他平台的会话；任何「已安排」只表示交接包已写入仓库，各端状态以该端自己写回仓库的记录为准 |
| D-006（文末补记中的正式定义） | **交接文件归属裁决**：`docs/handoffs/<角色>.md` 唯一归属该角色，主控不写入；主控派发包另用 `claude-to-<角色>.md`。这是 `docs/handoffs/grok.md` 归你、且本次由你自己创建的依据 |
| D-009-R | 撤回一条错误结论的处理方式（保留错误成因与教训、不静默删除）；主控自述错误 3 的出处 |
| D-010 | I²C 上拉事实作为设计输入的采纳记录；注意其依据是 **CoreBoard V1.0** 原理图 |
| D-013 | **红线：谁设计谁不得担任该次的独立审查人。** 主控接手产出的任何设计或修复必须由非作者复核；额度紧张不构成免除理由 |
| D-014 | 文件编辑权临时移交的登记方式（同一源文件同时只允许一位编辑者） |
| D-015 | 主控模型第一次切换（`claude-opus-5` → `claude-fable-5-1`）；同一会话、共享上下文 |
| D-016 | 一条结论由 confirmed 降为 derived 的完整记录，含降级理由与升回条件；可作为「证据地位应如何登记」的范例 |
| D-017 | 迭代式打板主循环；设计产出进入 `hardware/`、`firmware/`、`mechanical/` 新目录，与 A0 的 `design/` 分离 |
| D-018 | 主控模型第二次切换（切回 `claude-opus-5`）；写明**与 D-015 同理，主控自核仍属同上下文核验，不构成独立复核**。这是本次 R0 存在的直接依据 |

### 4.3 其他边界文件

| 路径 | 能证明什么 |
| --- | --- |
| `AGENTS.md` | 各端通用工作规则：领取任务与执行结果必须落到仓库、进展同步强制、不要用自身生成结果代替独立审查 |
| `CLAUDE.md` | 主控侧的同类规则，含「没有跨平台调度能力时提供明确交接包，不能声称已启动其他平台」 |
| `docs/handoffs/TEMPLATE.md` | 交接与报告的字段模板：任务 ID、角色与模型、输入提交、输出提交／PR、完成内容、验证与证据、未解决问题、下一步。**你的报告与交接按它收尾** |
| `docs/OWNERSHIP.md` | 文件归属与编辑锁登记、未知项清单；用于确认某个文件该谁改 |
| `docs/MEASUREMENT_PROTOCOL.md` | 实物到货后的测量规程；范围 (c) 中若干假设的验证步骤引用到它 |
