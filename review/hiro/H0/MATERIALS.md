提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造

# H0 资料索引

- 日期：2026-09-20；编制：Claude 主控，实际模型 `claude-fable-5-1`。
- 配套派发包：`docs/handoffs/claude-to-hiro.md`。本文件只索引资料，不下结论；每条的「证明什么」是主控对该资料证据力的描述，供 Hiro 核对与反驳。
- 撰写时 `origin/main` 为 `1af3c36`。未注明分支的路径均在该提交的工作树上核实存在；Hiro 领取时以 `git rev-parse origin/main` 的结果为准。
- 置信度用法：`confirmed`＝来源文件明确写出或画出，仓库内可复核；`derived`＝由来源推断、计数或跨版次推广；`unknown`＝仓库内无法闭环；`陈述`＝某端的说法，仓库内无留证。

## 1. 官方资料

| 资料 | 位置 | 证明什么 | 置信度 | 局限 |
| --- | --- | --- | --- | --- |
| 《ESP-MOSAICO 扩展指南》中文版 | `references/official-v12/expansion_v121_zh.pdf`（共 4 页；SHA-256 见 `review/chrome/D1-module-interface/evidence/DOCUMENT_SOURCES.json`） | PDF 第 2 页（印刷 01）声明「该指南仅适用于 1.2.1 版本及以上」；第 3 页（印刷 02）步骤 1 为底板外侧线图：四角螺丝、散布过孔、边缘两组 2×10P、一排圆角矩形焊盘（主控计数 7 个）、中央无四焊盘组，步骤 2 显示拆四颗螺丝后整块底板取下；第 4 页（印刷 03）步骤 5 为底板内侧图，双绞线从顶边缺口穿入 | 页面内容 confirmed；「V1.2 无背部四焊盘」据此为 derived | 无标注的等轴线图；无电气网络、无额定、无尺寸；「1.2.1」与实拍丝印 `V1.2` 是否同一版次未证明 |
| 同上，英文版 | `references/official-v12/expansion_v121_en.pdf` | 同上 | 同上 | 同上 |
| 底板内侧图（已渲染） | `references/official-v12/exp_backplane.png` | 内侧焊盘丝印 `5V-I` `3V3`（BTB 连接器上方）、`GND` `VBAT5V-O`（BTB 下方）；顶边两个缺口。说明官方扩展取电路径是「拆底板、焊内侧、缺口穿线」 | 丝印 confirmed；「外侧因此无供电焊盘」为 derived | 线图，非实物 |
| 官方装配指南 | `references/official-v12/assembly_zh.pdf`、`references/official-v12/assembly_en.pdf` | 官方装配步骤 | unknown（主控为本包未逐页阅读；Chrome D1 亦未引用） | 内容未审 |
| 官方 V1.2 资料归档说明 | `references/official-v12/README.md` | 归档来源与日期；MakerWorld 模型页地址；内侧丝印读数；官方标称整机尺寸 45.19 × 11.48 mm、33 g（来源为视频简介） | 归档事实 confirmed；标称尺寸 derived | 3mf／STL 需登录下载，未取得 |
| MakerWorld 官方模型页 | https://makerworld.com/zh/models/3323223-esp-mosaico （发布账号 ESP-Mosaico） | 上述 V1.2 资料的发布渠道；`review/claude/REVERSAL-option-d.md` 第 2.2 节称页面实拍图中框模块槽上方印有逐脚引脚标签、与 V1.0 H2 表一致 | 页面存在 confirmed（2026-09-20 主控访问）；引脚标签一致性为陈述 | 主控未在仓库留该页截图；页面 2026-09-20 当天有更新 |
| 官方 V1.0 用户指南 | https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s31/esp-mosaico/user_guide.html ；HTML 快照 `review/chrome/T04/evidence/user-guide-2026-09-20.html`；rst 源快照 `review/chrome/D1-module-interface/evidence/user_guide_v10.rst`（固定提交 `3c0f6321`，URL 与 SHA-256 见 `evidence/DOCUMENT_SOURCES.json`） | rst 590 行：两组 2×10P、2.54 mm 间距扩展排针（H2 左、H1 右）；620–685 行左槽 H2 表：pin17 `5V_IN`「External 5 V input (can power and charge the device)」（651–653）、pin19 `VCC_3V3` 与 pin18 `5V_OUT` 均「controlled by GPIO60」（654–662）、pin10 `GPIO14`「TOUCH; EEPROM address select」、pin13／15 为 USB Serial/JTAG D−／D+（GPIO33／34） | V1.0 confirmed | 对 V1.2 的适用是推广（derived，派发包 A-H0-1） |
| CoreBoard V1.0 原理图 | https://dl.espressif.com/AE/SCH_SCH_ESP-Mosaico_CoreBoard_V1_0_2026-08-18.pdf ；本地 `review/chrome/T04/evidence/coreboard-v1.0-2026-08-18.pdf`；逐图证据 `review/chrome/T04/COREBOARD_INTERFACE_EVIDENCE.md`；哈希 `review/chrome/T04/EVIDENCE_MANIFEST.json` | V1.0：主板 I2C0 `R1`／`R2` 4.7 kΩ 上拉至 `MCU_3V3`，Codec 支路另有 2.2 kΩ；`5V_IN` 经 D10 至 VCHG（充电）与 D15 至 VSYS；D14 为 USB VBUS 到 `5V_OUT` 旁路；GPIO60 经 Q5 控制 `VCC_3V3` | V1.0 confirmed | 不是 V1.2；不是 BaseBoard 原理图 |
| 官方产品指南 | https://mosaico.espressif.com/guide/ ；快照 `review/chrome/T04/evidence/mosaico-product-guide-2026-09-20.html` | 模块 5 V 与 3.3 V 输出各最大 100 mA | confirmed | 是输出额定，不是 pin17 输入额定 |
| 官方 V1.0 背面图 Fig.7 | `review/claude/official-evidence/fig7-baseboard-back-native.png`、`review/claude/official-evidence/pads-silkscreen-zoom.png`；说明 `review/claude/official-evidence/README.md` | V1.0（`Baseboard-A 260710 V1.0`）背面中央有 `SDA / + / − / SCL` 四焊盘与 6 个圆形调试点；是与 V1.2 实拍对照的基线 | V1.0 confirmed | 不涉及 V1.2 |

## 2. BSP 源码（commit `392860b1`）

- 仓库：https://github.com/esp-mosaico/esp-mosaico-bsp 。固定提交 `392860b1d1a123c3377947074b2af1f600e86c5d`；Chrome 抓取时（2026-09-20T08:53Z）master 亦指向该 SHA。
- 快照与哈希：`review/chrome/D1-module-interface/evidence/bsp/SOURCE_INDEX.json`（每个文件的 raw URL、SHA-256、Git blob SHA-1、`matches_commit_tree`）。以下路径均相对 `review/chrome/D1-module-interface/evidence/bsp/components/`，行号为主控本次在快照上读到的行号（与 Chrome 引用的行号有个位数出入时以文件为准）。

| 文件 | 证明什么 | 置信度 |
| --- | --- | --- |
| `esp-mosaico-bsp/include/bsp/esp_mosaico.h` | 37–43：`bsp_board_variant_t` 只有 `V1_0`／`V1_2` 两档，`bsp_board_variant_get()` 从 eFuse USER_DATA 读；62–75：V1.0 主板与模块共用 I2C0（GPIO0／1），V1.2 主板改 GPIO56／3、模块槽用 `I2C_NUM_1`（GPIO0／1）；109–113：板载 I2S 为 GPIO 54／37／49／52／40 | confirmed |
| `esp-mosaico-bsp/include/bsp/subboard.h` | 19–39：标准模块用 AT24C02，左 GPIO14 接 A0 电平 0 得 7-bit `0x50`，右 GPIO39 电平 1 得 `0x51`；摄像头 EEPROM 固定 `0x50`、GPIO14 改作 camera D4 | confirmed |
| `esp-mosaico-bsp/onboard/subboard.c` | 24–67：左槽 12 根 GPIO 表（6 个明示 H2/H4/H6/H8/H10/H12 ＋ 6 个 extended）；73–98：V1.2 分支新建 I2C1 并开内部上拉（`enable_internal_pullup = true`）；101–120：地址脚配置为推挽输出；123–141：初始化顺序为开模块 `VCC_3V3`（L132）、建 I²C（L134）、设地址电平（L137）；212–224：左槽 GPIO 原样返回、右槽镜像 | confirmed |
| `mosaico_module_mgr/include/mosaico_module_mgr.h` | 23–25：magic ASCII `ESP`、镜像长度 `0x86`＝134 字节；29–33：默认扫描 250 ms、重试 2000 ms、去抖 3 次；42–58：板类枚举（INTERACT＝`0x16` 等）；81–105：描述符逻辑结构 | confirmed |
| `mosaico_module_mgr/mosaico_module_mgr.c` | 22–28：五个偏移常量与 100 kHz、100 ms；209–219：CRC16（初值 `0xFFFF`、`0xA001`、无末尾异或）；221–260：字段解析，228–232 为三段校验；373–389：注册两槽 EEPROM 设备；418–422：单字节内部地址 0 连续读 134 字节；458–600：扫描状态机与去抖；813–836：初始化流程；994–1047：claim；1135–1200：release | confirmed |
| `mosaico_module_interact/mosaico_module_interact.c` | 137–153：交互模块 GPIO 静态表；785–866：驱动主动 claim 与初始化流程，不按 vendor_id／board_id 自动加载 | confirmed |
| `mosaico_module_mgr/README.md`、`LICENSE`、两份 `CMakeLists.txt`、两份 `idf_component.yml` | 组件依赖与许可；`esp-mosaico-bsp/CMakeLists.txt:21` 依赖 `efuse` 组件 | confirmed |

仓库内**没有**留证、只能算「陈述」的两项：`review/claude/REVERSAL-option-d.md` 第 2.3 节「对 BSP 全部 32 个 commit `git grep` 背部焊盘关键词零命中」；`docs/handoffs/claude.md` 第 1 节「BSP 从 eFuse 读版本号并打印 `Hardware version: vX.Y (variant=v1.N)`」。后者的函数声明在快照 `esp_mosaico.h:42–43` 可见，但打印字样所在的实现文件不在 D1 快照中。Hiro 若需采用须对公开仓库复核。

## 3. 第三方实拍及其局限

| 资料 | 位置 | 证明什么 | 置信度 | 局限 |
| --- | --- | --- | --- | --- |
| 裸板背面实拍 | `review/claude/hardware-revision/v12-baseboard-back.png`（字节数、SHA-256、来源链见同目录 `EVIDENCE_MANIFEST.json`） | 丝印 `ESP-Mosaico Baseboard-A`、`V1.2`、`260821`；两组 2×10P 通孔带逐脚丝印，标签集合与官方 H2／H1 表内容一致；右下一排 7 个焊盘 `GND BOOT RST RX TX 5V GND`；板中央为两个 logo 与散布过孔，无焊盘；通孔外观为焊锡填满的连接器引脚焊点；四角银色金属块位于白色外壳凹槽内、PCB 边界外 | 丝印可读为 confirmed；「中央无四焊盘」为该图的直接观察；「通孔已填满」「金属块在外壳上」「标签顺序与 H2 表逐脚一致」为 derived | 第三方开箱内容（小红书「数字之心」），用户转交，主控未接触原始发布页；板周被外壳唇边紧贴、上边缘截断；透视未校正 |
| 整机背面实拍 | `review/claude/hardware-revision/v12-assembled-back.png` | 外侧黑色面：`ESP-MOSAICO` 标识、二维码、四颗螺丝、一排 7 个焊盘及标签 | **主控重新判读：此为贴在底板外侧的标签面，不是 PCB 面**（画面无任何通孔） | 不能作为「四焊盘不存在」的独立证据；`review/claude/hardware-revision/README.md` 第 2 节据此撤回「两张独立实拍互证」（D-016） |
| 卡尺画面 | `review/claude/hardware-revision/v12-caliper-4527.jpg` | 有人用数显卡尺量整机，读数 45.27 mm | derived | 被测部位、朝向、归零均未知；不得作工程尺寸 |
| 交互模块实拍 | `review/claude/hardware-revision/v12-module-interaction.jpg` | 模块丝印 `ESP-Mosaico Module-Interaction V0.2`，两片电容触摸电极、WS2812 等 | confirmed（丝印） | 只与方案 G「改造现成模块」相关，不在本次范围 |
| 153 秒开箱拆机录屏（主控所引） | **不在仓库，无 URL。** `EVIDENCE_MANIFEST.json` 登记来源为小红书「数字之心」《esp mosaico 新鲜到货》 | 主控据其得出 V1.2 背面布局、卡尺读数、交互模块外观 | 陈述 | Hiro 无法复核；上两张 JPG 为其抽帧（JFIF 注释 `Lavc62.28.100`） |
| Chrome 对一段录屏的摘帧与判读 | `review/chrome/T14/video-20260920/README.md`、`SOURCE.json`、`032-size.jpg`、`058-back-sheet.jpg`、`066-baseboard.jpg`、`068-debug-fixture.jpg`、`078-coreboard.jpg`、`080-disassembly.jpg`（PR #12，已随 PR #23 合入） | `SOURCE.json`：文件 `ScreenRecording_09-20-2026 13-56-45_1.MP4`，时长 153.840318 s，1320×2868，SHA-256 `444e01c4…7847`，用户提供、称官方开箱、无发布 URL。README：00:58 揭开背面薄片后露出 BaseBoard；01:06 背板 `Baseboard-A / V1.2`，中央未见四枚圆焊盘；01:06–01:08 七枚矩形调试焊盘；01:18 CoreBoard `V1.2 / 260821`；拆下 BaseBoard 是在分离带电池与扬声器的功能板 | 摘帧内容 confirmed（有 SHA）；与主控所引录屏是否同一文件 unknown（时长相符，未核对） | 录屏原文件未入库；Chrome 说明为「按画面作证」，未转录音频 |

## 4. 主控文档

| 文档 | 位置 | 在本次审查中的角色 | 其关键结论的置信度 |
| --- | --- | --- | --- |
| 前一主控会话交接（含接手补记） | `docs/handoffs/claude.md` | 第 0 节：当前方案 D＋G；第 1 节：三个事实（第一行已按 D-016 降为 derived，是范围 (a) 的对象）；第 2 节：七个错误；第 3 节：UD-A～UD-D；第 4 节：预告本 H0 包并要求把 REVERSAL 纳入范围 | 见派发包第 1、2 节 |
| 方向更正文件 | `review/claude/REVERSAL-option-d.md` | 范围 (b) 的审查对象 | 2.1 confirmed（源码）；2.2 主控本次认为应为 derived；2.3 陈述 |
| 硬件版本差异 | `review/claude/hardware-revision/README.md`；`review/claude/hardware-revision/EVIDENCE_MANIFEST.json` | 范围 (a) 的审查对象；第 2 节对比表、第 2.1 节更强证据（2026-09-20 晚补）、第 7 节局限 | 第 1 节结论 derived（D-016） |
| 方案 H | `review/claude/option-h-pogo-uart-mcu.md` | 被降级的方案；第 1、2 节是「背面无 I²C 因而需 MCU」推理链的出处；第 5 节记录 H-01～H-03 | 已降为备份 |
| 方案 G | `review/claude/option-g-resident-adapter.md` | D 的机械落地方式；第 1 节记录模块槽连接器耐久问题，第 3 节论证对 E-01 不敏感 | 提案，机械细节不在本次范围 |
| 方案 E | `review/claude/option-e-rotated-slot.md` | 已不再需要；第 5 节定义 E-01 | 已作废 |
| 官方 V1.0 证据与摄影测量更正 | `review/claude/official-evidence/README.md`；`review/claude/official-evidence/tools/measure_pads.py` | V1.0 四焊盘定义（O03）与 2.54 mm 间距更正（O02）；错误 3、4 的现场 | V1.0 confirmed；间距为 derived，实测前不得冻结 |
| 3mf 来源核实 | `review/claude/3mf-analysis.md` | 错误 1、2 的现场 | 来源已确认为官方；用途仍待实物比对 |
| D＋G 概念图 | `review/claude/concept/overview.svg`、`review/claude/concept/mechanical-action.svg` | 方向示意 | 不含工程尺寸 |
| T18 提案报告 | `review/claude/T18/REPORT.md`（另有 `review/claude/T18/regenerated/` 五份对照产物） | 错误 7 的现场：主控补记称实现「只存在于提案分支」，与 Chrome 复核时的远端不符 | 提案，CHANGES_REQUIRED（Chrome PR #12） |
| 主控看板 | `docs/STATUS.md` | 第 5.4 节为当前方案表；第 5.2 节为按 D＋G 重写的推进边界 | 汇总，不构成技术结论 |
| 需求表 | `docs/PROJECT_PLAN.md` 第 2 节 | R02、R05 已按方案 D 改写；R04 带「不再必要、待用户决定」补注 | 需求层 |
| 决策记录 | `docs/DECISIONS.md` | D-003（跨平台边界）；D-006（交接文件归属）；D-010（V1.0 4.7 kΩ 上拉，范围 (c) c4／c8 涉及其适用范围）；D-012～D-014（额度分工与非作者复核红线）；D-015（接手、同上下文复核不构成独立复核）；D-016（结论 1 降 derived）；D-017（迭代式打板）。第 1 节初版四条已重编号为 D-006a～D-009a | 记录 |
| 团队分工 | `docs/TEAM_PLAN.md` 第 4 节（Hiro 批次审查规则与 PASS 条件、A0 自审边界）、第 7 节（D-017 主循环） | 规则 | 规则 |
| 统一接口约束 | `docs/INTERFACE_CONTROL.md`（ICD-0.2-DRAFT） | 正文按 V1.0 四触点编写；文首有 Chrome 加的方案 D 适用范围警示 | 未冻结，待改版 |
| 到货测量手册 | `docs/MEASUREMENT_PROTOCOL.md` | 第 0 节先认版本；第 4A 节仅 V1.0；第 4B 节按方案 H 的背面焊盘写，4B.3 含四角与模块接口特写；待补模块槽与模块板测量项 | 规程，实物未执行 |
| 给 Chrome 的派发包 | `docs/handoffs/claude-to-chrome.md` | 记录 C1–C5（方案 H 任务，已作废）与 D1–D3 改派 | 记录 |
| 任务板 | `docs/TASK_BOARD.md` | 领取记录；「主控代为集成 Chrome 遗留工作」一节登记 Chrome 下线与 D1 待 Hiro 复核 | 记录；H0 行待主控补登 |
| 项目入口 | `README.md`、`AGENTS.md`、`CLAUDE.md` | 协作规则；`README.md` 仍含「当前已定方向为方案 H」等过期表述 | 阅读时以 `docs/handoffs/claude.md` 第 0 节与 `docs/STATUS.md` 第 5.4 节为准 |
| Hiro 自己的交接 | `docs/handoffs/hiro.md` | Hiro 上次关机前状态；本次进展日志写入处 | Hiro 所有 |

## 5. Chrome 产出

| 产出 | 位置 | 内容 | 状态 |
| --- | --- | --- | --- |
| D1 左槽接口核查 | `review/chrome/D1-module-interface/README.md`、`LEFT_SLOT.md`、`BSP_AND_EEPROM.md`、`DOCUMENT_BOUNDARIES.md`、`evidence/DOCUMENT_SOURCES.json`、`evidence/user_guide_v10.rst`、`evidence/bsp/`（见第 2 节）。Chrome 输入 `main` `ff24626`，原分支 `chrome/h-low-quota-batch`（tip `b44c728`），经 PR #23 合入 | 范围 (c) 的审查对象：20 脚合同、12 根 GPIO、GPIO14 专用、与 I2S 无交集、V1.2 独立 I2C1、EEPROM 134 字节与三段 CRC、三条硬约束、pin17 额定 unknown | IN_REVIEW；Chrome 自注「不构成 Hiro 独立复核」 |
| Chrome 进展日志 | `docs/handoffs/chrome.md`「改派：方案 D 左槽模块」一节 | 2026-09-20 17:53–17:58 JST：D1 领取、两步中间推送、D1 交付、D2 领取 | D2、D3 无交付物；Chrome 已下线 |
| C1／H-01 停止点 | `review/chrome/H01/REPORT.md`、`review/chrome/H01/evidence/SOURCE.json` 及原始资料 | ESP32-S31 默认 UART0 TX=GPIO58、RX=GPIO59 与控制台配置的原始资料；明示「不得据此写背面 UART 已证实可用」 | 已中止，方案 H 降级，不在本次范围 |
| T18 机制复核（PR #12） | `review/chrome/T18/REPORT.md`、`RECOVERY.json`、`candidate/`、`check_proposal.py`、`check-results.json`（原分支 `chrome/t18-proposal-review`，tip `009a488`，经 PR #23 合入） | 从 `56030b9` 恢复候选；R01、R02；结论 CHANGES_REQUIRED；指出提案分支当时无实现（错误 7） | 不在本次范围，但为派发包第 2 节弱点 7 的依据 |
| 开箱录屏摘帧与判读 | `review/chrome/T14/video-20260920/` | 见第 3 节 | 已合入 |
| CoreBoard V1.0 电源与 I²C 证据 | `review/chrome/T04/COREBOARD_INTERFACE_EVIDENCE.md`、`review/chrome/T04/EVIDENCE_MANIFEST.json`、`review/chrome/T04/evidence/` | V1.0 原理图逐图证据（见第 1 节）；第 5 节 D14 旁路与 GPIO60 文图差异 | 已合入，V1.0 |
| 摄影测量分方向复跑 | `review/chrome/T14/geometry/GEOMETRY_RECHECK.md` | 错误 4 的发现现场；接受 D-009-R | 已合入；不在本次范围 |
| T14 测量记录表与修复顺序 | `review/chrome/T14/MEASUREMENT_RECORD.md`、`review/chrome/T14/REPAIR_ORDER.md` | 实物测量模板；F03→F01→F02 顺序 | 已合入；不在本次范围 |
| T02 EDA 验证（PR #4，OPEN） | 分支 `chrome/t02-a0-eda-validation`（tip `a6db65a`，撰写时未合入） | A0 导入验证与网络误连证据 | 不在本次范围；`docs/DECISIONS.md` D-011 要求合入前先与 `main` 同步以免误删 `docs/handoffs/hiro.md` |

## 6. 阅读注意（不计入五组）

1. `README.md` 与 `docs/DESIGN_STATUS.md` 部分段落仍是方案 H 或 A0 时期的表述；当前有效方案以 `docs/handoffs/claude.md` 第 0 节与 `docs/STATUS.md` 第 5.4 节为准。
2. 远端分支 tip 会变。撰写时：`main` `1af3c36`、`chrome/h-low-quota-batch` `b44c728`、`chrome/t18-proposal-review` `009a488`、`chrome/t02-a0-eda-validation` `a6db65a`、`claude/t18-reproducible-baseline` `e33465e`（与 `docs/handoffs/claude.md` 所记 `94b30d5` 不同，有后续推送，本包未审）。领取时以 `git ls-remote --heads origin` 为准。
3. 本文件所列行号是主控在 `1af3c36` 快照上读到的；Chrome 文档引用的行号有个位数出入（例如 I2S 定义 Chrome 写 108–114、实际 109–113），以文件为准，不构成 CHANGES_REQUIRED 项。
4. 本文件不替代派发包第 6 节的 ASSUMPTION 清单；凡本文件写「derived」而设计文档要采用的，都必须转写为带验证步骤的 `ASSUMPTION:`。
