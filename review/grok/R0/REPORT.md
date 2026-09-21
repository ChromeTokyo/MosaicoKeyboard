提案 · 未冻结 · 由 Grok 独立复核（实际模型 ID 未由可核验接口暴露 / 推理档位未暴露）起草 · 待主控处理修改项 · 不得据以制造

# R0 设计提案首次独立复核报告

- 任务 ID：R0 设计提案首次独立复核
- 负责人／角色：Grok（EspBot），独立复核者，只读
- 平台、实际模型 ID、推理档位：
  - 平台：Grok Bot（本机 hostname `grok-bot-vm-*`；agent profile `name=EspBot`）
  - 实际模型 ID：**未由可核验接口暴露**（不填猜测值）
  - 推理档位：**未由可核验接口暴露**
  - **核验方式（2026-09-21 09:01 JST）**：检查本会话环境变量（无 `MODEL`／`XAI_*`／`GROK_MODEL` 等字段）、`/home/box/agent-data/agents/<id>/profile.json`（仅有 name/title/harness，无模型字段）、请求元数据中无模型 ID／档位字段。派发包写「Grok 4.6」与 D-020 同文，**不作为本会话核验结果**。
- 日期：2026-09-21
- 状态：IN_REVIEW（报告完成，待 push／PR）
- 输入提交号及接口版本：领取时 `git fetch origin --prune && git rev-parse origin/main` → **`a691e25fc1fc5f94840fe0fea6a339571942098a`**；接口 `hardware/ICD-0.2-DRAFT.md` 0.2 草案（未冻结）
- 输出分支、提交号、PR：分支 `grok/r0-design-review`；提交号／PR 在 push 后回填
- 改动文件：仅 `review/grok/R0/REPORT.md`、`docs/handoffs/grok.md`（新建）

## 0. 确认知悉（分工条款）

已读并确认知悉审查包 §1.4 与 MATERIALS 指向的 D-013／D-015／D-018／D-020：本次为用户批准的例外独立复核；不改变 TEAM_PLAN「Cursor／Grok 可选辅助、非关键路径」；结论不替代 Hiro H1–H4、不构成 G1–G3 放行、不批准制造；不以模型多数决定技术正确性。

## 0.1 独立性披露（按包头坦白条款）

**复算前已见相关痕迹（如实披露，不隐瞒）：**

1. 本会话更早一轮（审查包尚未合入 main 时）已从固定基线 BSP **自行**读过 `mosaico_module_mgr.c`／`subboard.*`／`esp_mosaico.h` 并手算／脚本算过与 Q1–Q5 同类的结果；当时也浏览过 `docs/STATUS.md`、`docs/DECISIONS.md` 中 **D-020／D-021** 行（派发与校准机制说明，非完整五题答案表）。
2. 本轮领取后**未读**：`review/hiro/H0/REPORT.md`、`review/hiro/H0/MATERIALS.md`、`docs/handoffs/claude-to-hiro.md`、`review/grok/R0/RUBRIC*`、`origin/docs/grok-r0-rubric`；MATERIALS 限制外的其余 DECISIONS 条目未再展开。
3. 下列五题答案均以本轮对固定基线源码的复算为准；与被审文件自述一致处单独标注「自述一致」，**不以自述为计算依据**。

## 1. 基线源码核验

| 项 | 结果 | 证据 |
| --- | --- | --- |
| `SOURCE_INDEX.json` 12 文件 sha256+bytes | **全部 OK** | 本机重算 vs INDEX；基线 commit `392860b1d1a123c3377947074b2af1f600e86c5d` |
| Q5 所需 `esp_mosaico.c`（归档外） | 已取得 | URL：`https://raw.githubusercontent.com/esp-mosaico/esp-mosaico-bsp/392860b1d1a123c3377947074b2af1f600e86c5d/components/esp-mosaico-bsp/onboard/esp_mosaico.c`；**17035 bytes**；SHA-256 **`4933c3bc76d3606c58353dc2ffd48a5f588f0d18a0cdf772658844fca8efa73e`**（存于仓库外 `/tmp/r0-evidence/esp_mosaico.c`，未入库） |

## 2. 五道复算题

### Q1 — EEPROM 分段边界与总长

**出处（解析器）：**
- 总长宏：`mosaico_module_mgr.h:25` `MOSAICO_MODULE_MGR_EEPROM_IMAGE_SIZE 0x86U`（134）
- 偏移：`mosaico_module_mgr.c:22-26`（`EEPROM_DESC_CRC_OFFSET=0x34`，`MFG_DATA=0x36`，`MFG_CRC=0x3E`，`PARAM_DATA=0x40`，`PARAM_CRC=0x84`）
- 校验调用：`mosaico_module_mgr.c:228-232` `parse_descriptor`
- 读取：`mosaico_module_mgr.c:418-422` 从内部地址 `0` 连续读 `IMAGE_SIZE` 字节

**独立推导的分段：**

| 段 | 载荷起止（含起不含止） | 载荷字节数 | CRC 存放 |
| --- | --- | --- | --- |
| Descriptor | `[0x00, 0x34)` | 0x34 = 52 | `0x34..0x35`（2 B） |
| Manufacturing | `[0x36, 0x3E)` | 8 | `0x3E..0x3F` |
| Parameter | `[0x40, 0x84)` | 0x44 = 68 | `0x84..0x85` |

总长：52+2+8+2+68+2 = **134 = 0x86**。段间无重叠；`0x35→0x36`、`0x3F→0x40` 紧邻。

**与被审自述：** `mosaico_eeprom_v1.py` 中 `IMAGE_SIZE`／`OFF_*` 与上表一致（自述一致，非本题依据）。

### Q2 — CRC 参数与 `123456789` 校验值

**出处：** `mosaico_module_mgr.c:209-218`（算法）；`199-201` `read_le16`（小端读取 ⇒ 镜像中 CRC **小端存放**）。

| 参数 | 从源码读出 |
| --- | --- |
| 初值 | `0xFFFF`（L211） |
| 多项式 | `0xA001`（L215，右移形式） |
| 移位方向 | 右移（LSB first／反射） |
| 是否反射 | 是（字节异或后按 bit0 判断） |
| 最终异或 | 无（直接 `return crc`） |

**计算：** 按上述循环对 ASCII `123456789` 运行得到 **`0x4B37`**（与常见 CRC-16/MODBUS check 一致）。计算方式：本机 Python 复现与 C 同源逻辑。

**存放字节序：** 小端（`read_le16`）。

### Q3 — 左槽 H2 pin 1–12 GPIO 集合与 I²S 交集

**路径 A — 官方引脚表原文（V1.0）：** `user_guide_v10.rst:627-686`

| Pin | GPIO |
| --- | --- |
| 1 | 55 |
| 2 | 53 |
| 3 | 19 |
| 4 | 48 |
| 5 | 18 |
| 6 | 13 |
| 7 | 17 |
| 8 | 12 |
| 9 | 16 |
| 10 | 14 |
| 11 | 15 |
| 12 | 4 |

集合 A（大小 **12**）：`{4,12,13,14,15,16,17,18,19,48,53,55}`

**路径 B — BSP 槽位映射：** `subboard.c:55-66` `s_gpio_pairs[].left` 给出左槽规范 GPIO：`53,48,13,12,14,4,16,15,17,18,19,55`（与官方 pin1–12 集合相同；`connector_gpio[6]` 于 L31-33 仅含偶数脚 H2–H12 子集，完整 12 脚集合以 `s_gpio_pairs` + 官方表交叉为准）。

**两路径集合：相等，大小 12。**

**板载 I²S GPIO：** `esp_mosaico.h:109-113` → `{54,37,49,52,40}`（MCLK/SCLK/LRCLK/SDOUT/DSIN）。

**交集：** **空集** ∅。

### Q4 — 不可作普通按键输入的脚与 I²C 地址

**结论：** **GPIO14**（H2 pin 10）不可用作普通按键输入。

**理由与出处：**
- `subboard.h:26-27,36-39`：左槽地址选择 GPIO14，电平 0 → EEPROM `@0x50`
- `subboard.c:101-120`：发现阶段将该脚配置为 **推挽输出** 并驱动到 `address_select_level`
- 官方表 `user_guide_v10.rst:672-674`：pin 10 = GPIO14「TOUCH; EEPROM address select」

**主机驱动电平：** 左槽 **0（低）**。

**7 位 I²C 地址：** AT24C02 基址在 A2=A1=A0=0 时为 `0b1010000` = **`0x50`**；A0 接 GPIO14=0 ⇒ **`0x50`**（与 `BSP_SUBBOARD_EEPROM_ADDR_LEFT` 宏一致，`subboard.h:34`）。

### Q5 — eFuse → board variant

**出处：** `/tmp/r0-evidence/esp_mosaico.c`（已登记哈希）`detect_board_variant` **L33-60**：

| eFuse `USER_DATA` 版本值（`BSP_HW_VERSION(major,minor)`） | variant |
| --- | --- |
| `(1,0)` → `0x0100` | `BSP_BOARD_VARIANT_V1_0` |
| `(1,1)` → `0x0101` | `BSP_BOARD_VARIANT_V1_2` |
| `(1,2)` → `0x0102` | `BSP_BOARD_VARIANT_V1_2` |
| 其他 | `ESP_ERR_NOT_SUPPORTED` |

**能否分辨丝印 `V1.2` 与指南 `1.2.1`：** **不能。** 源码无 `1.2.1` 分支；二者若都编码为 major=1/minor=2，落入同一 `V1_2`。

**对 `ASSUMPTIONS.md`：** AS-16／AS-28 若暗示「读 eFuse 即可严格对应 BaseBoard 标签／区分 1.2 vs 1.2.1」，则**超出源码能力**（见发现 G03）。eFuse 只能区分 V1_0 vs V1_2 族。

## 3. 范围结论

| 范围 | 结论 | 性质 |
| --- | --- | --- |
| (a) `hardware/eeprom/` | **PASS**（格式／CRC／样例／枚举相容；已知 WP 冲突已标 ASSUMPTION） | 实际检查为主 |
| (b) `firmware/dock_handle/` | **CHANGES_REQUIRED** | 实际检查 |
| (c) ICD＋ASSUMPTIONS＋G6 | **CHANGES_REQUIRED** | 实际检查＋推导 |
| **总结论** | **CHANGES_REQUIRED** | |

`PASS` 仅表示文档／源码层面可作为下一步投入基础，**不是**硬件放行。

## 4. 发现清单

### G01 — `dock_handle_pinmap.h` 注释中的 J2 焊盘位与 PINMAP.md 不一致（宏值正确）

- **文件：** `firmware/dock_handle/include/dock_handle_pinmap.h`（如 L46「KEY_DOWN … A4」、L50「KEY_LEFT … A5」等）vs `origin/claude/design-d/module-board:hardware/module-board/PINMAP.md` 第 2 节（KEY_DOWN=**B3**，KEY_LEFT=**A4**，…）
- **为何是问题：** 到货焊盘对地短接验收会按注释／丝印对齐；注释错会导致误判键位。GPIO 宏与 PINMAP 一致，属文档漂移。PINMAP 修订 b 已点名需改注释。
- **影响：** 验收／装配指引；非运行时逻辑
- **建议：** 按 PINMAP 第 4 节改注释；README §4 转抄表同步

### G02 — `dock_handle_pinmap.h` 自称读取的 PINMAP「2026-09-20 版」已过期

- **文件：** 同头文件导言
- **建议：** 改为指向修订 b（2026-09-21）并注明「宏值未变、焊盘注释已更新」

### G03 — AS-28／认版路径高估 eFuse 对 1.2 vs 1.2.1 的分辨力

- **文件：** `hardware/ASSUMPTIONS.md` AS-16／AS-28；对照 Q5 源码
- **建议：** 改写为「eFuse 仅区分 V1_0／V1_2 族；1.2 vs 1.2.1 须依赖丝印／扩展指南适用范围／行为测试」

### G04 — ICD §3.3「X−1 列无损」论证偏弱

- **文件：** `hardware/ICD-0.2-DRAFT.md:144`
- **推导：** X−1 时底座 GND 针落到模块 `DOCK_5V`／`SLOT_5V_IN` 焊盘 ⇒ 主机 5V_IN 网络对底座地。主机若经原生 USB 已上电，存在把主机供电输入拉向地的路径；「无损」依赖未写明的主机输入保护／未上电前提。
- **建议：** 补前提（主机必须断电／或引用输入保护证据），或降级「无损」措辞并列入 G6 错位带电禁测项

### G05 — 错位枚举未覆盖对角／多列组合

- **文件：** ICD §3.3 仅列 ±1 列、错一行、绕 Y 180°
- **建议：** 显式声明「托架公差保证不可能 ≥2 列／不可能同时 X+Z」（依赖 AS-08／`DOCK_X_TOL`），或补组合情形表

### G06 — 子系统 `AS-31-*` 仅「待吸收」，总表无逐条条目

- **文件：** `hardware/ASSUMPTIONS.md` 待吸收说明 vs `IDENTITY.md`／`PROGRAMMING.md`／`firmware/dock_handle/README.md` 中大量 `AS-31-eeprom-*`／`AS-31-firmware-*`
- **建议：** 可接受为过渡，但应给吸收期限或在总表增加「指针行」列出全部 AS-31 编号，避免关闭假设时漏项

### G07 — 固件未在 ESP-IDF／真机编译（作者已自述）

- **文件：** `firmware/dock_handle/README.md` 已知限制
- **性质：** 高风险残留，不单独把符号表判失败；本轮对管理器 API 名称做了抽查（`claim`／`release`／`subscribe`／`get_info`／`HANDLE=0x04` 等与头文件相符），**未做完整签名逐参数审计与编译**
- **建议：** 主控安排一次针对固定 BSP commit 的 IDF 编译门禁后再提高采信

### G08 —（范围 a 观察）WP 默认态 ICD vs 模块板冲突

- **文件：** `PROGRAMMING.md` §2.1
- **判定：** 已标 ASSUMPTION 并给样机／量产分流，**可接受为已知开放项**，不阻挡 (a) PASS；须 Chrome 决策闭合

## 5. 范围 (a) 摘要 — PASS

| 问题 | 判定 | 检查类型 |
| --- | --- | --- |
| 镜像布局 vs 解析器 | 一致（见 Q1；工具 OFF_* 与 mgr 一致） | 实际检查 |
| CRC 算法／分段／字节序 | 一致（见 Q2） | 实际检查 |
| `sample_handle.bin` | magic `ESP`；三段 CRC OK；`param_length=24≤64`；长度 134；SHA256 与 `SHA256SUMS`／header 一致 | 实际检查 |
| board_type `0x04` | 落在 `mosaico_board_type_t`（`mosaico_module_mgr.h:47`）；claim 比 type（作者断言与枚举相容——官方 HANDLE 语义冲突属 AS-20，未独立证伪） | 实际检查＋推导 |
| 烧写 API | 示例使用的 `i2c_master_transmit_receive` 读路径与 mgr `read_eeprom` 同形；完整 IDF 符号表未在本环境交叉编译验证 → 记入 G07 风险，不升级为 (a) 失败 | 部分检查 |

## 6. 范围 (b) 摘要 — CHANGES_REQUIRED

| 问题 | 判定 | 检查类型 |
| --- | --- | --- |
| PINMAP GPIO 宏 | 10 键 GPIO 与 PINMAP 第 2 节一致 | 实际检查 |
| 焊盘注释／版本戳 | **G01／G02** | 实际检查 |
| 认领／释放／拔出 | `try_attach` 后身份复核失败则 release；`detach_now` 先补发释放事件再 `release_key_gpios` 再 `mgr_release`；订阅回调仅对 ABSENT 触发 — 与作者注释的管理器「不自动 release lease」语义相符（抽查） | 实际检查＋推导 |
| 右槽 | 显式 `ESP_ERR_NOT_SUPPORTED` | 实际检查 |
| API 核实表逐行 | **未完整逐行核对 README §6 全部行号**（额度内抽查通过）→ 标「部分未检查」 | 部分未检查 |
| PC_LINK.md Kconfig 存在性 | **未检查** | 未检查 |
| 真机编译 | 未做（G07） | 未检查 |

## 7. 范围 (c) 摘要 — CHANGES_REQUIRED

| 问题 | 判定 | 检查类型 |
| --- | --- | --- |
| 防呆二级表 | ±1 列／错行／180° 映射可复现；**G04／G05** | 实际检查＋推导 |
| 假设覆盖 | AS-01–30 被 ICD／eeprom／firmware 引用；AS-31-* 在总表仅待吸收（**G06**） | 实际检查 |
| 验证步骤可执行性 | 多数步骤指明测什么／仪器；依赖「待 Chrome 定义」阈值的项不能得 PASS — G6 正文已要求 `阈值未定义` 不得写 PASS（`G6-TEST-PLAN.md` 判定节）→ **未发现隐含放行漏洞** | 实际检查 |
| 阈值表自洽 | TH-01–12 均有测试项引用；阈值空缺时 VERDICT 只能是「阈值未定义」 | 实际检查 |
| 网络命名 | KEY_*／DOCK_*／SLOT_* 与 eeprom／firmware 用语大体一致；未做第 9 节逐符号全表 diff | 部分检查 |

## 8. 完成内容

- 领取冻结提交 `a691e25fc1fc5f94840fe0fea6a339571942098a`
- 基线 12 文件哈希核验；拉取并登记 `esp_mosaico.c`
- 完成 Q1–Q5 独立复算（含披露）
- 完成范围 (a)(b)(c) 审查并给出结论与 G01–G08
- 新建本报告与 `docs/handoffs/grok.md`

## 9. 验证与证据

- 工具：本机 `python3`、`rg`、`git`、`sha256sum`／hashlib；无 ESP-IDF 目标编译
- 禁止阅读项：已遵守 MATERIALS「本次不读」
- 证据路径：仓库内被审文件与 `review/chrome/D1-module-interface/evidence/bsp/`；仓库外 `/tmp/r0-evidence/esp_mosaico.c`

## 10. 未解决问题

| 问题 | 影响 | 负责人 |
| --- | --- | --- |
| G01／G02 注释漂移 | 到货键位验收误导 | 主控／firmware 作者 |
| G03 eFuse 认版能力 | 错误关闭 AS-16／28 | 主控 |
| G04／G05 防呆「无损」 | 错位带电风险被低估 | 主控／Chrome（回归后） |
| G06 AS-31 未入总表 | 假设关闭遗漏 | 主控 |
| G07 未 IDF 编译 | 符号／链接错误可能漏网 | 主控 |
| G08 WP 默认 | 样机／量产流程 | Chrome |
| 本环境无 GitHub 写权限 | 无法在无登录时完成 push／PR | 用户授权登录 |

## 11. 接下来做什么

1. 用户为 Grok Bot／`gh` 提供 GitHub 写权限后：push `grok/r0-design-review` 并开 PR。
2. 主控先核对 §2 五题，再按采信权重处理 G01–G08。
3. 可并行：Chrome 额度恢复后定 G6 阈值；模块板合入 PINMAP；IDF 编译门禁。
