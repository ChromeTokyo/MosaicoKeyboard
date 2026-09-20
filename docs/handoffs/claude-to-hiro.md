提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造

# 交接包：Hiro H0 设计前提变更专项复核

> 本文件是主控派给 Hiro 的审查包，Hiro 只读。Hiro 的领取登记、进展日志与完成交接写在 `docs/handoffs/hiro.md`（该文件唯一归属 Hiro，主控不写入；归属规则与 `docs/DECISIONS.md` D-006 对 `docs/handoffs/chrome.md` 的裁决相同）。审查报告写 `review/hiro/H0/REPORT.md`。配套资料索引见 `review/hiro/H0/MATERIALS.md`。

- 任务 ID：**H0 设计前提变更专项复核**。这是一次专项复核，不占用 `docs/TEAM_PLAN.md` 第 4 节的 H1–H4 编号，也不替代其中任何一项。
- 负责人／角色：Hiro／GPT-6，独立审查。派发人：Claude 主控，实际模型 `claude-fable-5-1`。
- 平台、实际模型 ID、推理档位：派发方为 Claude Code，`claude-fable-5-1`，推理档位未由可核验接口暴露，不猜填。**Hiro 侧的平台、实际模型 ID 与推理档位由 Hiro 领取时在 `review/hiro/H0/REPORT.md` 抬头与 `docs/handoffs/hiro.md` 登记**，本文件不代填。
- 日期：2026-09-20。
- 状态：READY（待 Hiro 领取）。本文件写入仓库只表示审查包可领取，不表示 Hiro 已上线或已开始工作（`docs/DECISIONS.md` D-003）。
- 输入提交号及接口版本：**冻结提交号在领取时执行 `git fetch origin --prune && git rev-parse origin/main`，把结果登记进报告与进展日志。** 撰写本包时 `origin/main` 为 `1af3c36`（PR #25 合入后），该值仅供对照，不是冻结值。接口版本：`docs/INTERFACE_CONTROL.md` 为 ICD-0.2-DRAFT，未冻结；其正文四触点章节是 V1.0 历史草案，与本包审查的 V1.2 前提不对应，Chrome 只在文首加了适用范围警示。
- 输出分支、提交号、PR：由 Hiro 领取后填写。建议分支名 `hiro/h0-premise-review`；关机前必须 push 并开 PR，报告中注明复核过的 `main` 提交号（`docs/TEAM_PLAN.md` 第 4 节）。
- 改动文件及源文件／生成文件关系：Hiro 可写 `review/hiro/H0/REPORT.md`（新建）与 `docs/handoffs/hiro.md`。不得改 `design/`、`references/`、`docs/` 其他文件、`review/claude/`、`review/chrome/`；对这些文件的修改意见写进报告。本任务无生成文件。`docs/TASK_BOARD.md` 的 H0 登记行属主控的队列维护职责，本包未改任务板，由主控另行补登，Hiro 不需要改任务板。

## 0. 本包的性质与读法

1. **审查对象是主控自己的判断与文档，以及 Chrome 的 D1 交付。** 本包由被审对象的作者撰写，因此下文每处「主控当前判断」都是待检验的主张，不是审查输入。Hiro 应先独立查证、计算，再对照主控结论（`docs/TEAM_PLAN.md` 第 4 节）。
2. 结论只允许 `PASS`／`CHANGES_REQUIRED`／`BLOCKED`；**证据不全时不得 `PASS`**。三项范围可分别给结论，再给一个总结论。`PASS` 的含义是「主控的判断经独立查证成立，可作为方向前提继续投入」，不是硬件放行，也不是 G1／G2 通过。
3. 每条结论标「实际检查／推导／未检查」，引用到具体文件与行号。
4. 本包不含任何机械或电气数值的冻结请求。凡本包出现的数值（针号、GPIO 号、字节偏移、行号）都是引用来源的原文，供核对，不是设计值。
5. 与 D-017 的关系：用户已定项目主循环为迭代式打板（先按现有信息把设计做完并全部标 `ASSUMPTION` → 实物到货核尺寸、读 eFuse 版本 → 改设计 → 国内打板发日本 → 日本验证再改）。**H0 不阻塞第 ① 步的设计起草**，但范围 (a)(b) 的结论决定第 ① 步的前提是否要推翻，范围 (c) 的结论是第 ③ 步前 ICD 改版与第 ④ 步前非作者复核的输入。
6. 本包涉及的假设集中列在第 6 节，每条带到货后的验证步骤。Hiro 若发现本包把假设写成了事实，直接作为 CHANGES_REQUIRED 项写进报告。

## 1. 审查范围（三项）

### 1.1 范围 (a)：结论 1「V1.2 取消背部四扩展焊盘」由 confirmed 降 derived 是否恰当

**要回答什么**

1. 该结论现在标 `derived`（`docs/DECISIONS.md` D-016）。这个档位对不对？应更低（必须等实物才能作为前提使用），还是可以维持更高？
2. 官方《ESP-MOSAICO 扩展指南》（页面声明「仅适用于 1.2.1 版本及以上」）PDF 第 3 页（印刷页码 02）步骤 1 的底板外侧图，能否作为「V1.2 无背部四焊盘」的主要依据？它是无标注的等轴线图，不是照片，也不是带焊盘标注的图纸。
3. 实拍丝印 `V1.2`／日期码 `260821` 与指南所称「1.2.1」是否同一版次？若不能证明同一，指南对实拍板的适用边界应如何写？

**依据在哪**

| 证据 | 位置（均在 `main`） | 它能证明什么 | 它不能证明什么 |
| --- | --- | --- | --- |
| 第三方实拍：裸板背面 | `review/claude/hardware-revision/v12-baseboard-back.png`；字节数与 SHA-256 见同目录 `EVIDENCE_MANIFEST.json` | 丝印 `ESP-Mosaico Baseboard-A`、`V1.2`、`260821`；两组 2×10P 通孔带逐脚丝印；右下一排 7 个焊盘 `GND BOOT RST RX TX 5V GND`；板中央（V1.0 四焊盘位置）为两个 logo 与散布过孔，无焊盘 | 板周最外一圈被外壳唇边紧贴、上边缘一小段被画面截断，不能确证整板无焊盘；来源为第三方开箱内容，拍摄条件未知 |
| 第三方实拍：整机背面 | `review/claude/hardware-revision/v12-assembled-back.png` | 外侧黑色面：`ESP-MOSAICO` 标识、二维码、四颗螺丝、一排 7 个焊盘及标签 | **这是贴在底板外侧的标签面，不是 PCB 面**（画面中无任何通孔，而 BaseBoard 背面必有两组 2×10P 共 40 个通孔）。不能作为「PCB 上无四焊盘」的独立证据；`review/claude/hardware-revision/README.md` 第 2 节原「两张独立实拍互证」据此撤回 |
| 官方扩展指南外侧全图 | `references/official-v12/expansion_v121_zh.pdf` PDF 第 3 页（印刷页码 02）步骤 1、步骤 2；英文版 `references/official-v12/expansion_v121_en.pdf` 同页 | 底板外侧线图：四角螺丝、散布过孔、边缘两组 2×10P 阵列、一排圆角矩形焊盘（主控本次重新渲染计数为 7 个，需 Hiro 复核），中央无四焊盘组；步骤 2 显示拆四颗螺丝后整块底板取下 | 版次是否等于实拍的 V1.2；线图是否与实物逐一对应；焊盘电气定义、额定、尺寸 |
| 官方扩展指南内侧取电路径 | 同 PDF 第 4 页（印刷页码 03）步骤 5；已渲染图 `references/official-v12/exp_backplane.png`；说明 `references/official-v12/README.md` | 官方认可的扩展取电方式是拆底板四颗螺丝、焊到**内侧**焊盘 `5V-I` `3V3`（BTB 上方）与 `GND` `VBAT5V-O`（BTB 下方）、线从顶边缺口穿出 | 这是推论的基础而非直接证据：若外侧仍有供电焊盘，官方不太可能把取电路径设计成需拆机的内侧焊接。**该推论属 derived** |
| 官方指南版次声明 | 同 PDF 第 2 页（印刷页码 01）「该指南仅适用于 1.2.1 版本及以上」 | 指南作者认为 1.2.1 以下版本不适用 | 「1.2.1」是硬件版次、套件版次还是文档版次；与 BaseBoard 丝印 `V1.2` 的对应 |
| 官方 V1.0 背面图（对照基线） | `review/claude/official-evidence/fig7-baseboard-back-native.png`、`pads-silkscreen-zoom.png`；说明 `review/claude/official-evidence/README.md` 第 1 节 | V1.0（`Baseboard-A 260710 V1.0`）背面中央确有 `SDA / + / − / SCL` 四焊盘，6 个圆形调试点 | 不涉及 V1.2 |
| Chrome 对开箱录屏的独立判读 | `review/chrome/T14/video-20260920/README.md`、`SOURCE.json` 与六张摘帧（PR #12，已随 PR #23 合入） | Chrome 独立记录：00:58 揭开背面薄片后才露出 BaseBoard 背面；01:06 背板近照 `Baseboard-A / V1.2`，中央未见四枚圆焊盘；01:18 CoreBoard 亦为 `V1.2 / 260821`；拆下 BaseBoard 是在分离带电池与扬声器的功能板 | 录屏原文件不在仓库；`SOURCE.json` 登记 SHA-256 与时长 153.840318 s；与主控所引 153 秒录屏是否同一文件未核对（时长相符） |
| BSP 板型枚举 | `review/chrome/D1-module-interface/evidence/bsp/components/esp-mosaico-bsp/include/bsp/esp_mosaico.h:37–43` | `bsp_board_variant_t` 只有 `V1_0`、`V1_2` 两个值，`bsp_board_variant_get()` 注释写明从 eFuse USER_DATA 读板级版本 | 打印 `Hardware version` 字样的实现文件不在快照中；eFuse 中的 variant 烧在 CoreBoard 芯片内，与 BaseBoard 丝印的对应关系源码无法证明 |
| BSP 对背部焊盘零命中 | `review/claude/REVERSAL-option-d.md` 第 2.3 节 | 主控陈述：对 BSP 全部 32 个 commit `git grep` 背部焊盘相关关键词零命中 | 仓库内没有该检索的输出留证；Hiro 若采用须自行对公开仓库复跑 |

**主控当前判断（供反驳）**

- 结论本身大概率正确：V1.2 背面没有 V1.0 的四扩展焊盘。但原 `confirmed` 的依据链「两张独立实拍互证」不成立，因为两张图中只有一张是 PCB 面。**降为 `derived` 恰当。** 不应更低：在「方向前提」层面已有官方外侧图、官方内侧取电流程、实拍中央无焊盘三者叠加，足以支撑「方案 A 在 V1.2 上不成立」继续作为前提使用。也不应更高：官方图无标注、版次对应未证明、实拍无来源链且板周被遮，实物未到货。
- 官方外侧图**可以**作为主要依据，但要加两条限定写进结论文档：（i）它是示意线图，只能证明「官方描绘的 1.2.1 及以上底板外侧无四焊盘组」，不能证明每块出货板；（ii）它与实拍的可对应点是 7 个焊盘的位置与两组 2×10P 阵列的位置一致，其余细节不逐一对应。
- 版次问题仓库内无法闭环。可用的旁证只有 BSP 枚举只认 `V1_0`／`V1_2` 两档：若「1.2.1」是硬件版次，BSP 也只会把它识别为 `V1_2`。主控判断应把「1.2.1」当作官方文档口径、「V1.2」当作 BaseBoard 丝印口径，两者关系写 `unknown`；到货后同时记录 BaseBoard 丝印、CoreBoard 丝印与串口打印的 variant 三个值再判定。
- 随之应补进 `review/claude/hardware-revision/README.md` 的三条观察已在其第 2.1 节补记（2×10P 通孔已被焊锡填满；四角银色块嵌在外壳里不在 PCB 上；BaseBoard 本身就是整机后盖板）。三条均为 derived，须实物确认。
- 主控**不**认为该结论需要等实物才能作为方向前提使用；但任何冻结动作必须等到货后按 `docs/MEASUREMENT_PROTOCOL.md` 第 0 节读版本、目视背面，并刷 BSP 示例从串口日志读 variant。

**Hiro 要交付什么**：对上述三个问题各给一个明确回答；对 `derived` 档位给出同意或改判及理由；指出主控的证据表里哪些行应删、哪些应加。

### 1.2 范围 (b)：`review/claude/REVERSAL-option-d.md` 这次方向更正是否成立

**要回答什么**

1. 把方案 H（背面撞针 ＋ 底座 MCU ＋ UART）降为备份、回到方案 D（插左模块槽的模块）＋ G（常驻转接件），这个方向更正在逻辑上是否成立？
2. 这是同一天内对同一问题的第二次更正，且推翻的是几小时前刚被用户确认的方案 H 与需求修订 R04。它属于「新证据驱动的必要更正」，还是「过度反应」？
3. 更正文件第 2 节把三项依据都标为 `confirmed`，是否每一项都够得上？

**依据在哪**

| 依据 | 位置（均在 `main`） | 性质 |
| --- | --- | --- |
| 更正文件本身 | `review/claude/REVERSAL-option-d.md` | 审查对象 |
| V1.2 模块槽独立 I²C 总线 | BSP 快照 `review/chrome/D1-module-interface/evidence/bsp/components/esp-mosaico-bsp/include/bsp/esp_mosaico.h:62–75`（`BSP_SUBBOARD_I2C_PORT_V1_2` 为 `I2C_NUM_1`，SDA `GPIO_NUM_0`、SCL `GPIO_NUM_1`；主板总线 V1.2 改 `GPIO_NUM_56`／`GPIO_NUM_3`）；`.../onboard/subboard.c:73–98`（V1.2 分支新建 I2C1，`enable_internal_pullup = true`） | 源码，对 commit `392860b1` 为 confirmed |
| 模块槽 pin17 为 `5V_IN`，可供电并充电 | 官方 V1.0 用户指南 H2 表快照 `review/chrome/D1-module-interface/evidence/user_guide_v10.rst:651–653`；实拍 `v12-baseboard-back.png` 左槽阵列丝印含 `IN`、`3V3`、`5V`、`GND` | 官方文字为 V1.0；「V1.2 引脚定义未改」由丝印一致推得，derived |
| 左槽 12 根 GPIO、与 I2S 无交集 | 见范围 (c) | Chrome D1 |
| 方案 H 的出发点 | `review/claude/option-h-pogo-uart-mcu.md` 第 1、2 节：背面没有 I²C，按键走 UART，因此需要 MCU | 主控文档 |
| 方案 G 对连接器耐久问题的处理 | `review/claude/option-g-resident-adapter.md` 第 1–3 节 | 主控文档，机械细节不在本次范围 |
| 被推翻的需求修订 | `docs/PROJECT_PLAN.md` 第 2 节 R04（已加「方案 H 降级后本修订不再必要，待用户决定」补注）；R02、R05 已按方案 D 改写 | 需求层，回退权在用户（UD-B） |
| 前一主控对该更正的定性 | `docs/handoffs/claude.md` 第 0 节、第 2 节第 6 行 | 主控文档 |
| 当前方案表 | `docs/STATUS.md` 第 5.4 节 | 汇总，不构成技术结论 |

**主控当前判断（供反驳）**

- 更正**成立，不是过度反应**。理由：其逻辑不依赖范围 (a) 的精确置信度。即便背面仍有焊盘，模块槽也是官方专门为扩展准备的接口，V1.2 还为它配了独立 I²C 总线；走模块槽不需要 MCU，也不需要 I²C 扩展器。方案 H 引入 MCU 的唯一动机是绕开「背面无 I²C」，一旦不必绕开，MCU 就失去存在理由。
- 与第一次更正的区别：第一次（方案 A 到 H）依据的是第三方照片；第二次（H 到 D＋G）依据的是 BSP 源码这一可复核的一手证据。两次更正的证据等级不同。
- 主控承认更正文件第 2.2 节「引脚定义在 V1.2 上未改」是由外壳与 PCB 丝印一致推得，标 `confirmed` 偏高，应改为 `derived`；第 2.3 节「零命中」仓库内无留证，应标为陈述。第 2.1 节标 `confirmed` 成立。
- 需要 Hiro 一并判断、但主控没有把握的点：左槽与摄像头模块的冲突（`docs/handoffs/claude.md` 第 3 节 UD-A）是否应在方向层面就否决 D；`E-01` 连接器机械形态未知，是否让 D＋G 与 H 一样带有未闭环的实物依赖（主控认为 G 对 E-01 不敏感，见 `option-g-resident-adapter.md` 第 3 节，但这是主控自己的论证）；D＋G 把每日插拔转移到弹簧针接口后，模块板与 Mosaico 之间「插一次不再拔」在用户实际使用中能否成立。

**Hiro 要交付什么**：对更正的成立性给结论；若认为属过度反应，写出应保留 H 为主线的理由与触发条件；若认为成立，列出 D＋G 方向上必须在实物到货前关闭的前提清单。

### 1.3 范围 (c)：Chrome D1 左槽引脚合同的独立复核

这是 Chrome 下线前的最后一份产出。Chrome 在 `BSP_AND_EEPROM.md` 首段自注「不构成 Hiro 独立复核」，在 `README.md` 末段写「关键接口仍交 Hiro 独立复核」。主控只做了同上下文核对（D-015），不是规定的非作者复核。

**审查对象（已随 PR #23 合入 `main`；Chrome 登记的输入 `main` 为 `ff24626`，BSP 固定提交 `392860b1d1a123c3377947074b2af1f600e86c5d`）**

- `review/chrome/D1-module-interface/README.md`
- `review/chrome/D1-module-interface/LEFT_SLOT.md`
- `review/chrome/D1-module-interface/BSP_AND_EEPROM.md`
- `review/chrome/D1-module-interface/DOCUMENT_BOUNDARIES.md`
- `review/chrome/D1-module-interface/evidence/bsp/SOURCE_INDEX.json` 及其下源码快照；`review/chrome/D1-module-interface/evidence/user_guide_v10.rst`；`review/chrome/D1-module-interface/evidence/DOCUMENT_SOURCES.json`

以下行号均相对 `review/chrome/D1-module-interface/evidence/bsp/components/`。

**要逐项独立复核的结论**

| # | Chrome 的结论 | Chrome 给的依据 | Hiro 应做的独立动作 |
| --- | --- | --- | --- |
| c1 | 左槽 H2 的 12 根通用 GPIO 为 `{55,53,19,48,18,13,17,12,16,14,15,4}`，按 H2 针号 1–12 排列；pin13／pin15 的 `USJ_DN`（GPIO33）／`USJ_DP`（GPIO34）不计入 | `esp-mosaico-bsp/onboard/subboard.c:24–67`（6 个明示 H2/H4/H6/H8/H10/H12 ＋ 6 个 extended）；奇数针号对照 `user_guide_v10.rst:620–685` | 从 rst 表与源码表分别独立列出集合并比对；确认 12 根中没有 GPIO33／34；确认「12 根」不包含 I²C 的 GPIO0／1 |
| c2 | `GPIO14`（H2 pin10）为 EEPROM A0 地址选择，专用，不得接按键 | `esp-mosaico-bsp/include/bsp/subboard.h:19–39`；`subboard.c:101–120` 将其配置为推挽输出 | 核对左槽电平 0 对应 7-bit `0x50`、右槽 `GPIO39` 电平 1 对应 `0x51`；判断「按键接到 GPIO14 会发生什么」是否已被合同排除 |
| c3 | 12 根 GPIO 与板载 I2S `{54,37,49,52,40}` 交集为空 | `esp-mosaico-bsp/include/bsp/esp_mosaico.h:108–114` | 重算交集；确认这只证明与 I2S 无冲突，不证明与其他外设无复用 |
| c4 | V1.2 模块槽为独立 `I2C_NUM_1`（GPIO0／1），主板改 GPIO56／3；主板地址 `0x11 0x12 0x19 0x55 0x5A 0x69` 不再占用模块总线，模块总线上只有 `0x50`／`0x51` | `esp_mosaico.h:62–75`、`subboard.c:73–98` | 读源码确认；注意 V1.2 分支开启的是**内部上拉**，外部上拉是否存在、是否足够为 `unknown`；判断 `docs/DECISIONS.md` D-010（V1.0 CoreBoard R1／R2 4.7 kΩ）的适用范围是否应显式限定为 V1.0 共享 I2C0 |
| c5 | EEPROM 镜像 134 字节（`0x86`）、magic ASCII `ESP`、三段 CRC16（`0x00–0x33` 校验到 `0x34`、`0x36–0x3D` 到 `0x3E`、`0x40–0x83` 到 `0x84`）、算法初值 `0xFFFF`、逐位右移并按 `0xA001` 异或、无末尾异或；`param_length` 不超过 64；100 kHz、单字节内部地址 0、连续读 134 字节 | `mosaico_module_mgr/include/mosaico_module_mgr.h:23–25, 81–105`；`mosaico_module_mgr/mosaico_module_mgr.c:22–28`（偏移常量）、`209–219`（CRC）、`221–260`（解析，其中 228–232 为三段校验）、`373–389`、`418–422` | 对照解析器逐字段核对偏移与长度之和是否为 134；独立识别 CRC 变体；确认参数 CRC 覆盖完整 64 字节参数区而非仅有效长度；确认 `param_version` 位于 `0x40` 且被参数段 CRC 覆盖 |
| c6 | 硬约束一：**pin17 供电不得等待 EEPROM 识别或主机 GPIO 许可**，否则主机电池耗尽时形成启动循环依赖 | `subboard.c:123–141`：`bsp_subboard_init()` 顺序为开模块 `VCC_3V3`（L132）→ 建 I²C（L134）→ 设地址电平（L137） | 读源码确认顺序；判断该约束表述是否完备（例如是否还应写明「不依赖 GPIO60」与「双电源同时存在时对 pin17 的防反灌」） |
| c7 | 硬约束二：EEPROM 从 pin19 `VCC_3V3` 取电，**不得从底座反送 3.3 V**；pin18 `5V_OUT` 留空不接 | `user_guide_v10.rst:654–662`（pin19 `VCC_3V3` 与 pin18 `5V_OUT` 均「controlled by GPIO60」）；`DOCUMENT_BOUNDARIES.md`（V1.0 原理图有 D14 旁路，GPIO60 不是无电保证） | 判断反灌风险表述是否成立；确认 D14 旁路结论仅对 V1.0；判断「EEPROM 在主机未调用 `bsp_subboard_init()` 时无电、模块不会被识别」这一固件与电源时序的耦合是否应写进合同 |
| c8 | 硬约束三：**不得照搬 V1.0 的 4.7 kΩ／2.2 kΩ 上拉结论**到 V1.2 模块总线；模块板预留外部上拉 DNP 位 | `LEFT_SLOT.md`「V1.2 的 I²C 与电源状态」一节；`docs/DECISIONS.md` D-010；`review/chrome/T04/COREBOARD_INTERFACE_EVIDENCE.md` 第 4 节 | 判断 D-010 是否需要加版本限定；判断「预留 DNP 位、实测后决定装配」是否足以覆盖内部上拉不足的情形 |
| c9 | pin17 输入的额定电流、电压容差、热插拔浪涌、双电源反灌边界：**unknown**；不得借用 100 mA 模块输出或 500 mA USB source 数值 | `DOCUMENT_BOUNDARIES.md`；`review/chrome/T04/COREBOARD_INTERFACE_EVIDENCE.md` 第 2、3 节 | 确认 Chrome 没有推算数字填空；确认这些 `unknown` 已完整列出；判断在 D-017 迭代打板下「按 `ASSUMPTION` 做电源预算」的可接受边界 |
| c10 | 软件面：模块管理器为 250 ms 轮询 ＋ 3 次去抖，无中断通路；空白 EEPROM 不合格；烧入合法身份不会自动产生十键驱动 | `mosaico_module_mgr.h:29–33`；`mosaico_module_mgr.c:458–600, 994–1047`；`mosaico_module_interact/mosaico_module_interact.c:785–866` | 抽查行号与结论是否对应；这一项影响固件工作量，不影响电气合同 |

**主控当前判断（供反驳）**

- 主控本次在 `main` 快照上重做了 c1–c6 的核对（**同上下文复核，D-015，不构成独立复核**），结果与 Chrome 一致：源码表 `{53,48,13,12,14,4}` ∪ `{16,15,17,18,19,55}` 与 rst 表奇数针 `{55,19,18,17,16,15}` ∪ 偶数针 `{53,48,13,12,14,4}` 相等；与 `{54,37,49,52,40}` 交集为空；`0x84 + 2 = 0x86 = 134`；CRC 循环与三段区间在 `mosaico_module_mgr.c:209–232` 可直接读到；初始化顺序在 `subboard.c:132–137` 可直接读到。主控核对得到的行号与 Chrome 引用的略有出入（I2S 定义实际在 `esp_mosaico.h:109–113`，`bsp_subboard_init()` 起于 `subboard.c:123`），属引用精度问题，不影响结论；Hiro 请以自己读到的行号为准。
- c6–c8 三条硬约束主控认为成立，且必须写进后续 ICD 改版。主控另建议补两条供 Hiro 判断是否列入合同：（i）底座 USB-C 与 Mosaico 原生 USB-C 可能同时供电，底座对 pin17 的输出必须防反灌，且防反灌不得依赖任何软件判断；（ii）pin19 `VCC_3V3` 受 GPIO60 控制、由 `bsp_subboard_init()` 主动开启，若主机固件未调用该初始化则 EEPROM 无电，模块不会被识别。
- Chrome 已在 `LEFT_SLOT.md` 写明：H2 针号是官方表的逻辑编号，**V1.2 实物的 pin1 朝向、键位与接触次序须实测**。主控同意，且认为这是模块板 PCB 起草时最需要显式标 `ASSUMPTION` 的一条。
- 未闭环且本次不要求 Hiro 闭环：pin17 额定；V1.2 外部上拉；pin20 单接点回流载流；连接器机械形态（`E-01`）；V1.2 BaseBoard 内部 5 V 路径与保护（Chrome 只追到 V1.0 的 D10／VCHG／D15／VSYS）。

**Hiro 要交付什么**：对 c1–c10 逐项给「实际检查／推导／未检查」与「同意／不同意／需修改」；给出 D1 整体结论；列出必须由 Chrome 后继者补的项。

## 2. 主控自述的已知弱点（请优先怀疑这些）

前一主控会话（实际模型 `claude-opus-5`）与本会话（`claude-fable-5-1`）在同一天内合计有七个已记录的错误，见 `docs/handoffs/claude.md` 第 2 节。本节如实转录，不淡化。

| # | 错误 | 谁发现的 | 现状 | 与本次审查的关系 |
| --- | --- | --- | --- | --- |
| 1 | 把 `MOSAICO.3mf` 当成官方整机中框，未查来源即采信，并据其内腔推整机尺寸 | 主控自己的对抗质疑轮 | 已更正，见 `review/claude/3mf-analysis.md` | 说明主控有「先采信后核源」的倾向，范围 (a) 的照片判读同源 |
| 2 | 反向纠错过头：把该文件判为「未核实为官方」，理由只是官方文档站没有 | 用户提供的官方评论截图 | 已二次更正 | 说明主控存在「更正再更正」的模式，范围 (b) 要专门评估这一点 |
| 3 | 摄影测量用垂直标定量水平间距，得出「2.54 mm 被证伪」的错误结论，并经用户转达给了 Chrome | 主控自己的并行核查 | 已撤回，见 `docs/DECISIONS.md` D-009-R | 一次错误结论已外溢到另一端 |
| 4 | 焊盘直径用 `(h+w)/2` 除以水平标定，混轴，偏小约 3% | **Chrome**（`review/chrome/T14/geometry/GEOMETRY_RECHECK.md`） | 已更正，见 `review/claude/official-evidence/README.md` 第 2.4 节 | Chrome 曾是主控的有效纠错者，现已下线 |
| 5 | `git add -A` 把仍在进行的 T18 提案扫进 `main`，违反自定的 D-013 | 主控自己 | 已撤回，PR #11 | 流程纪律问题 |
| 6 | **方案方向错误**：把「背面」当成唯一通路，为绕开它引入 MCU 并据此让用户修订需求 R04，而官方模块槽本来一应俱全 | 主控自己的并行工作流 | 已更正，见 `review/claude/REVERSAL-option-d.md` | 范围 (b) 的直接对象 |
| 7 | **撤回 T18 误合入时，未把实现补进提案分支**：`claude/t18-reproducible-baseline` 在 Chrome 复核时（`94b30d5`）只有领取声明与 D-012～D-014，没有实现；实现只存在于已撤回的 `main` 历史提交 `56030b9`。`review/claude/T18/REPORT.md` 的主控补记「这三个文件只存在于提案分支」与当时远端事实不符 | **Chrome**，PR #12（`review/chrome/T18/REPORT.md`） | Chrome 从 `56030b9` 恢复候选并审出 R01（`--write-policy` 重新登记会清空已填的人工审核字段）、R02（缺少必需焊盘的缓存经 `--write-lock` 重新登记后仍可作为可用输出），T18 状态 CHANGES_REQUIRED；补实现与修两问题待主控执行。撰写本包时该分支远端 tip 已变为 `e33465e`，与 `docs/handoffs/claude.md` 所记不同，说明有后续推送，其内容本包未审 | 不在本次范围，但说明主控对「仓库里实际有什么」的自述不可默认可信；Hiro 对本包每条路径都应 `ls` 或 `git show` 核实 |

此外三条结构性弱点：

- **交叉校验缺位。** Chrome（Codex／`gpt-6-astra`）已彻底耗尽额度下线（`docs/DECISIONS.md` D-015）。上表第 4、7 两项都是 Chrome 发现的；Chrome 下线后，主控的判断在 Hiro 之前没有第二个技术视角。D1 是 Chrome 的最后产出；其进展日志中已领取的 D2（AT24C02 选型与供货）、D3（电源拓扑接 pin17）没有交付物。
- **本轮主控复核为同上下文复核，不构成独立复核（D-015）。** 本会话对前一会话结论的审计（D-016 降级、`review/claude/hardware-revision/README.md` 第 2.1 节补记、`REVERSAL` 置信度的再评估、范围 (c) 的行号核对）都是同一角色、同一仓库上下文内的再审，不满足 `docs/TEAM_PLAN.md` 第 1、4 节与 D-013 对非作者复核的要求。本包里出现的每条「主控当前判断」都可能延续上表的同类偏差。
- **本包由被审对象撰写。** 范围 (a) 的置信度降级、范围 (b) 的「成立」判断，都是主控对自己前一会话工作的再审。范围 (a) 中「两张独立实拍互证」这一证据链错误已作为审查对象呈现，不另编号，以免预设 Hiro 的结论。

## 3. 不属于本次范围（避免消耗 Hiro 额度）

| 不做 | 原因 |
| --- | --- |
| 实物尺寸、公差、连接器几何、上电验证、I²C 波形、EEPROM 实读 | 实物预计 2026-09 下旬到货；测量按 `docs/MEASUREMENT_PROTOCOL.md` 执行后另派 |
| PCB、封装、制造包 | 尚无按 D＋G 架构画出的电路；A0 架构已作废 |
| T18 的 R01／R02 修复 | 提案作者（主控）的工作；Hiro 不修代码 |
| 方案 E／G 的机械细节（旋转、转接件结构、弹簧针落点） | 属 Chrome 后继者；本次只审方向逻辑 |
| H-01（背面 UART0 占用）、H-02（背面 5 V 载流）、H-03（背面焊盘几何） | 方案 H 已降为备份；`review/chrome/H01/REPORT.md` 是 Chrome 中止的停止点记录 |
| 原 A0 的 F01／F02 与 T05 电气审查 | A0 按 V1.0 四触点 ＋ I²C 扩展器架构绘制，架构已作废 |
| `docs/INTERFACE_CONTROL.md` 改版、`docs/MEASUREMENT_PROTOCOL.md` 第 4B 节改写 | 主控与 Chrome 后继者的工作；Hiro 只在 (c) 中指出应写进 ICD 的约束 |
| UD-A 槽位取舍、UD-B R04 回退 | 用户决策 |
| `README.md` 仍写「当前已定方向为方案 H」等过期表述的修复 | 主控文档维护；阅读时以 `docs/handoffs/claude.md` 第 0 节与 `docs/STATUS.md` 第 5.4 节为准 |

## 4. 关于自审的说明

Hiro 参与过原 A0 草案的产生（`docs/TEAM_PLAN.md` 第 4 节、`docs/handoffs/hiro.md`）。**本次审查对象是主控的判断与文档，以及 Chrome 的 D1，不是 A0**；三项范围都不要求 Hiro 评价 A0 电路本身的质量。因此本次不构成自审，Hiro 无需回避。若 Hiro 在范围 (b) 中需要指出「A0 的 I²C 扩展器架构在 V1.2 前提下失去对象」，那是对前提的判断，不是对 A0 的技术审查；对原 A0 的非作者审查要求（由 Chrome 执行）不受本次影响。

## 5. 输出要求

1. 报告写 `review/hiro/H0/REPORT.md`，抬头按 `docs/handoffs/TEMPLATE.md` 字段登记任务 ID、平台、实际模型 ID 与推理档位、复核过的 `main` 提交号。
2. 三项范围各给 `PASS`／`CHANGES_REQUIRED`／`BLOCKED`，再给一个总结论。**证据不全不得 PASS。**
3. 每条结论标「实际检查／推导／未检查」，引用到具体文件与行号。
4. 领取时与关机前各在 `docs/handoffs/hiro.md` 的进展日志追加一行（`AGENTS.md`「进展同步（强制）」）。无法完成时写清已查范围与未查范围。
5. 不修改 `design/`、`references/`、主控与 Chrome 的任何文件；对它们的修改意见写在报告里。
6. 报告开头沿用本包首行的「提案 · 未冻结」声明格式，把起草者改为 Hiro；PASS 也不等于制造放行。

## 6. 本包使用的假设（ASSUMPTION 清单）

每条在设计文档中使用时必须原样带 `ASSUMPTION:` 标签与验证步骤。Hiro 不需要验证它们，但若发现本包或 D1 把其中任何一条写成了事实，列为 CHANGES_REQUIRED。

| 编号 | 假设 | 目前依据 | 到货后验证步骤 |
| --- | --- | --- | --- |
| A-H0-1 | `ASSUMPTION:` V1.2 左槽 20 针的电气定义与官方 V1.0 用户指南 H2 表逐脚一致 | 实拍 `v12-baseboard-back.png` 与官方线图上左槽阵列的丝印集合与 H2 表内容一致（主控本次目视：`55 ADC`、`33 DN`、`34 DP`、`IN`、`3V3`、`14`、`1 SCL`、`0 SDA`、`5V`、`GND` 等可辨，顺序与朝向未逐脚核对）；BSP 左槽映射函数对左槽原样返回 | 按 `docs/MEASUREMENT_PROTOCOL.md` 第 4B.3 节拍左槽特写并逐脚抄丝印；整机断电、隔离电池后，用万用表从模块板一侧对 pin17／pin19／pin20 与背面 `5V`／`GND` 焊盘做通断，对 pin14／pin16 与背面 2×10P 丝印 `1`／`0` 做通断 |
| A-H0-2 | `ASSUMPTION:` 左槽连接器为 2.54 mm 间距轴向插接排针排母，母座在机身左侧面、开口朝左 | 官方 V1.0 指南 `user_guide_v10.rst:590` 写明 2×10P、2.54 mm；V1.0 原理图标注 `B-2200R20P-B120`；`E-01` 未证实 | 第 4B.3 节拍左右接口特写；卡尺量相邻孔中心距与两排间距各三处取均值；记录母座开口方向与 pin1 位置 |
| A-H0-3 | `ASSUMPTION:` eFuse 中的 board variant 与 BaseBoard 丝印 `V1.2` 严格对应 | `esp_mosaico.h:42–43` 声明从 eFuse USER_DATA 读；variant 烧在 CoreBoard 芯片内，丝印在 BaseBoard 上 | 刷任意 BSP 示例，抄录串口日志中的板级版本打印；同时按第 0 节抄录 BaseBoard 与 CoreBoard 丝印；三值并列登记 |
| A-H0-4 | `ASSUMPTION:` V1.2 模块槽 I²C1 外部上拉存在与否及阻值未知；按「可能只有内部上拉」设计并预留 DNP 位 | `subboard.c:93` `enable_internal_pullup = true`；V1.0 的 4.7 kΩ 结论不适用 | 主机上电、槽内无模块时，测 pin14／pin16 对 pin19 的电阻；接示波器看 100 kHz 读 EEPROM 时的上升沿，再决定 DNP 位是否装配 |
| A-H0-5 | `ASSUMPTION:` pin17 输入额定未知；电源预算按「整机峰值 ≤ 1 A、持续 ≤ 0.6 A」假设计算，无官方依据 | 官方仅写「可供电并充电」，无数值（`DOCUMENT_BOUNDARIES.md`） | 用限流可调电源经模块板给 pin17 供电，从 0.3 A 逐级上调，记录整机开机、充电、屏幕满亮与音频满载时的电流与 pin17 压降；任何异常即停 |
| A-H0-6 | `ASSUMPTION:` 实拍 `V1.2 / 260821` 与官方指南「1.2.1 及以上」为同一版次 | 无直接证据；BSP 只有 `V1_0`／`V1_2` 两档 | 与 A-H0-3 同步登记；若三值一致且背面确无四焊盘，结论 1 可升 confirmed |

## 完成内容

本包（`docs/handoffs/claude-to-hiro.md`）与资料索引（`review/hiro/H0/MATERIALS.md`）已写入分支 `docs/hiro-h0-package`。所引用的仓库路径均在撰写时于 `origin/main`（`1af3c36`）工作树上核实存在。本包写入不表示任何审查已开始或任何结论已成立。

## 验证与证据

- 主控为写本包实际做过的检查：以 110 dpi 重新渲染 `references/official-v12/expansion_v121_zh.pdf` 第 2、3、4 页并目视（第 3 页步骤 1 外侧图焊盘排计数 7，中央无四焊盘组；第 4 页内侧丝印 `5V-I 3V3`／`GND VBAT5V-O` 与顶边两个缺口可辨；第 2 页版次声明可辨）；缩放目视 `v12-baseboard-back.png`（中央无焊盘、板周被外壳唇边遮挡、上边缘截断、2×10P 通孔呈实心焊点、四角银色块在外壳内）与 `v12-assembled-back.png`（标签面，无通孔）；在 `main` 的 BSP 快照中读 `esp_mosaico.h:37–43, 60–116`、`subboard.h:15–40`、`subboard.c:20–70, 70–155, 205–230`、`mosaico_module_mgr.h:20–35, 78–108`、`mosaico_module_mgr.c:22–28, 195–262, 370–425`、`user_guide_v10.rst:590, 620–700`，并重算 c1 集合、c3 交集、c5 长度；`git ls-remote` 核对远端分支 tip。
- 主控未做：未复跑 `REVERSAL-option-d.md` 第 2.3 节的 BSP 全提交 grep；未核对 PR #12 录屏 SHA 与主控所引录屏是否同一文件；未逐页阅读 `assembly_zh.pdf`；未编译或运行 BSP；未访问 MakerWorld 页面复核 REVERSAL 第 2.2 节所称的外壳引脚标签；未接触实物。
- 上述检查是主控的同上下文核对（D-015），**不是**规定的非作者复核，也不改变任何结论的置信度。

## 未解决问题

| 问题 | 影响 | 负责人 |
| --- | --- | --- |
| 结论 (a) 的置信度档位与官方图的证据地位 | 决定 D＋G 是否可作为方向前提继续投入 | Hiro 判定 |
| D1 的三条硬约束是否完备、是否应增补防反灌与 `bsp_subboard_init()` 耦合两条；pin17 额定 unknown 在 D-017 下是否可按 ASSUMPTION 推进 | 决定电源拓扑与 ICD 改版的边界 | Hiro 复核；Chrome 后继者补 |
| Chrome 下线后 D2、D3 与 ICD 改版无人执行 | 硬件技术判定权空缺，主控只整合不代行 | 用户决定 Chrome 是否有后继会话 |
| T18 R01／R02 未修 | F03 基线继续悬空 | 主控 |
| `README.md` 等文档仍含方案 H 时期表述 | 影响 Hiro 读文档时的定位 | 主控 |

## 接下来做什么

1. 用户在 Hiro 上线时告知：先 `git fetch origin --prune`，再读 `docs/handoffs/claude-to-hiro.md` 与 `review/hiro/H0/MATERIALS.md`。
2. Hiro 领取、登记、审查、推送报告与交接；关机前必须 push。
3. 主控收到 `review/hiro/H0/REPORT.md` 后：按结论更新 `docs/STATUS.md` 与 `docs/DECISIONS.md`；若 (a) 或 (b) 为 CHANGES_REQUIRED，先改前提再动第 ① 步已起草的设计；若 (c) 为 CHANGES_REQUIRED，把修改项写进 ICD 改版清单并转给 Chrome 后继者。
4. 可并行、不依赖 H0 结论的工作（D-017 第 ① 步）：模块板与底座主板按 `ASSUMPTION` 起草；主控修 T18 R01／R02 与文档过期表述；用户打印 T17 体量模型。
5. 本会话离线后其他角色能否继续：能。本包与索引已在仓库，Hiro 不需要本会话的对话记忆。
