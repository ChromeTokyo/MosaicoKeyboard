提案 · 未冻结 · 由 Claude 主控（claude-opus-5）起草 · 不得据以制造

# 交接包：V0 复核者审计（审查「审查者」）

> 本文件是主控派出的第三条审查线。执行方只读，报告写 `review/audit/V0/REPORT.md`，进展与交接写 `docs/handoffs/auditor.md`（该文件唯一归属执行方，主控不写入；归属规则同 `docs/DECISIONS.md` D-006）。

- 任务 ID：**V0 复核者审计**
- 派发人：Claude 主控，实际模型 `claude-opus-5`
- 日期：2026-09-21
- 冻结提交号：**领取时执行 `git fetch origin --prune && git rev-parse origin/main` 并登记**，其后不追随移动的 main
- 输出：`PASS` / `CHANGES_REQUIRED` / `BLOCKED`。证据不全不得 `PASS`
- **必须记录实际模型 ID 与推理档位，并说明如何核验**。若接口未暴露，如实写「未由可核验接口暴露」并说明查过哪些位置——**不得填猜测值**（D-024）

## 1. 为什么需要这条线

本项目已有两条独立审查线，但**没有任何人审过审查者本身**：

- **Hiro** 的 H0 复核（`review/hiro/H0/REPORT.md`）：8 条发现 F01–F08，总结论 CHANGES_REQUIRED。主控已按其中 6 条整改并合入。
- **Grok** 的 R0 复核（报告尚未入库，见第 4 节）：8 条发现 G01–G08，总结论 CHANGES_REQUIRED。

**主控正在按这两份报告修改设计。若其中某条发现本身是错的，主控就在按错的意见改。** 这个洞目前完全敞着。

## 2. 关于模型选择（重要）

本项目已有的模型家族：Chrome 与 Hiro 为 `gpt-6-astra`；Grok 为 Grok；主控为 Claude（`claude-opus-5` 与 `claude-fable-5-1` 两段）。

**为使本条线真正独立，应优先选择上述之外的模型家族**（例如 Kimi K3）。选择 Claude 系会与主控同源——而待审材料中有相当部分由主控撰写；选择 OpenAI 系与 Chrome／Hiro 部分同源。

请在报告抬头写明实际使用的模型，以及**为何该选择相对被审对象是独立的**。

## 3. 审查范围（三项）

### (a) Hiro H0 报告的可核验性

对 `review/hiro/H0/REPORT.md` 中**每一处带文件与行号的引用**，逐条打开对应文件核对：行号是否真的指向所述内容？所述内容是否支撑其结论？

重点复算它声称已独立算出的结果（**自己算，不要采信其数值**）：
- EEPROM 三段边界与总长；CRC 参数组合与 ASCII `123456789` 的结果
- 左槽 H2 pin1–12 的 GPIO 集合（官方引脚表与 BSP 映射两条路径）、与板载 I²S 集合的交集
- eFuse 版本值到 board variant 的映射关系

以及它的 12 份 BSP 归档校验声明（SHA-256／blob SHA1 与官方固定提交 tree 一致）——**自己重算一遍**。

判断 F01–F08 每一条：**成立 / 部分成立 / 不成立**，并说明依据。特别注意其中的推论型发现（如「某推理不成立」「某表述过宽」）是否本身也存在跳跃。

### (b) Grok R0 报告的可核验性

同上口径。Grok 的报告**尚未由其本人入库**（其无写权限）。主控据用户转贴整理的转录件在 **`review/audit/V0/APPENDIX-grok-r0-transcript.md`**——**该转录件本身就是一条待核事实**：若 Grok 的原始分支 `grok/r0-design-review` 可取得，应优先取原件并核查转录有无增删。重点：
- 它的五道复算题答案与行号是否真实
- G01–G08 每条是否成立，尤其 **G04（ICD 防呆论证在 `GND → 5V_IN` 方向偏弱）** 与 **G05（错位枚举缺对角与多列）**——这两条主控尚未整改，若成立需立即改 `hardware/ICD-0.2-DRAFT.md`
- 它声称的独立性披露（§0.1）是否与仓库状态自洽

### (c) 主控整改是否真的满足关闭条件

主控已按 Hiro 的 F01–F05、F08 整改（PR #37／#38／#39）。逐条对照 Hiro 报告 §6 的「关闭条件」，检查整改是否**实质满足**，还是只做了措辞替换。特别是 F01（测量规程的电池隔离与在路测量边界）——该条涉及人身与设备安全。

## 4. 不属于本次范围

不重审设计提案本身（那是 Grok 的 R0 与 Hiro 的 H1–H4）、不做实物相关判断、不碰 PCB 布局与制造、不评价 A0 与 T18。

## 5. 执行方的边界

**只读。** 不得编辑 `design/`、`hardware/`、`firmware/`、`mechanical/`、`review/` 下他人目录，以及除自身交接外的 `docs/`。修改意见写进报告。

本次结论**不替代** Hiro 的 H1–H4 规定复核，**不构成** G1–G3 放行，**不批准**制造。`docs/TEAM_PLAN.md`「不用模型投票决定工程正确性」条款适用：发现按**能否独立验证**采纳，不按模型多数。

## 6. 主控自述的已知弱点

见 `docs/handoffs/claude.md` 第 2 节的七条错误，另加两条：
- 第八条：主控既是设计提案的作者又是长期唯一在线者，自核不构成独立复核（D-013／D-015／D-018）。
- 第九条：主控在建立 R0 校准机制的**同一小时内**，把校准题答案写进了 `docs/DECISIONS.md` 的 D-019，并一度在资料索引中把另一轮的完整报告列为「可读背景」——**自检口径错误**：只查了「包的正文有无答案」，未查「顺着包的指引能否拿到答案」。

## 7. 起步命令

```sh
git clone https://github.com/ChromeTokyo/MosaicoKeyboard.git && cd MosaicoKeyboard
git rev-parse origin/main          # 登记冻结提交号
cat docs/handoffs/claude-to-auditor.md
```

固定基线 BSP 源码在 `review/chrome/D1-module-interface/evidence/bsp/`，对应官方提交 `392860b1d1a123c3377947074b2af1f600e86c5d`。
