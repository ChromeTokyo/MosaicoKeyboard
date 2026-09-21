# 附录：Grok R0 报告（据用户转贴，非 Grok 自行推送）

**性质声明（主控写，2026-09-21）：**

- Grok 在交付 R0 时**尚无仓库写权限**，其分支 `grok/r0-design-review` 未能推送。本文件是**主控据用户转贴的内容**整理入库，**不是 Grok 自行提交的原件**。
- 因此：格式可能与原件有差异；**若 Grok 日后推送原件，以原件为准，本文件作废**。
- V0 审计方在核 (b) 项时应知悉这一点：**本文件本身就是一条待核事实**——若 Grok 的原始分支可取得，应优先取原件比对，并核查本转录是否有增删。

---

## 原文转录

任务 ID：R0 设计提案首次独立复核。负责人：Grok（EspBot），独立复核者，只读。

平台：Grok Bot（本机 hostname `grok-bot-vm-*`；agent profile `name=EspBot`）。
实际模型 ID：**未由可核验接口暴露**（不填猜测值）。推理档位：**未由可核验接口暴露**。
核验方式（2026-09-21 09:01 JST）：检查本会话环境变量（无 `MODEL`／`XAI_*`／`GROK_MODEL` 等字段）、agent `profile.json`（仅有 name/title/harness，无模型字段）、请求元数据中无模型 ID／档位字段。派发包写「Grok 4.6」与 D-020 同文，**不作为本会话核验结果**。

领取时 `git rev-parse origin/main` → **`a691e25fc1fc5f94840fe0fea6a339571942098a`**；接口 `hardware/ICD-0.2-DRAFT.md` 0.2 草案（未冻结）。输出分支 `grok/r0-design-review`（本地 tip 含报告；远端 push 阻塞）。改动文件：仅 `review/grok/R0/REPORT.md`、`docs/handoffs/grok.md`。

### 0.1 独立性披露（Grok 原文要点）

1. 本会话更早一轮（包尚未合入 main 时）已从固定基线 BSP **自行**读过 `mosaico_module_mgr.c`／`subboard.*`／`esp_mosaico.h` 并算过与 Q1–Q5 同类结果；也浏览过 `docs/STATUS.md`、`docs/DECISIONS.md` 中 **D-020／D-021** 行（派发说明，非完整答案表）。
2. 本轮**未读**：H0 REPORT／MATERIALS、`claude-to-hiro.md`、RUBRIC、限制外的其余 DECISIONS。
3. 五题以本轮对固定基线源码的复算为准；与被审自述一致处标「自述一致」，不以自述为计算依据。

### 1. 基线源码核验

`SOURCE_INDEX.json` 12 文件**全部 OK**（基线 `392860b1d1a123c3377947074b2af1f600e86c5d`）。Q5 所需 `esp_mosaico.c` 已从官方 raw URL 取得：**17035 bytes**，SHA-256 `4933c3bc76d3606c58353dc2ffd48a5f588f0d18a0cdf772658844fca8efa73e`。

### 2. 五道复算题

**Q1** 出处 `mosaico_module_mgr.h:25`（`0x86`）；`mosaico_module_mgr.c:22-26`、`:228-232`、`:418-422`。Desc `[0x00,0x34)`＝52 B，CRC `0x34..0x35`；Mfg `[0x36,0x3E)`＝8 B，CRC `0x3E..0x3F`；Param `[0x40,0x84)`＝68 B，CRC `0x84..0x85`。总长 **134＝0x86**。

**Q2** 出处 `mosaico_module_mgr.c:209-218`；小端读取 `read_le16` L199-201。初值 `0xFFFF`；多项式 `0xA001`；右移／反射；无最终异或 → **`0x4B37`**；镜像中小端存放。

**Q3** 官方表 `user_guide_v10.rst:627-686`：pin→GPIO＝1:55, 2:53, 3:19, 4:48, 5:18, 6:13, 7:17, 8:12, 9:16, 10:14, 11:15, 12:4。集合大小 **12**：`{4,12,13,14,15,16,17,18,19,48,53,55}`。BSP `subboard.c:55-66` 左脚集合相同，**两路径相等**。I²S `esp_mosaico.h:109-113` → `{54,37,49,52,40}`，**交集 ∅**。

**Q4** **GPIO14**（pin 10）不可作普通按键。出处 `subboard.h:26-27,36-39`；`subboard.c:101-120`（推挽输出）；官方表 L672-674。左槽驱**低** → 7 位地址 **`0x50`**。

**Q5** `esp_mosaico.c` L33-60：`(1,0)`→V1_0；`(1,1)` 与 `(1,2)`→V1_2；其他不支持。**不能分辨丝印 V1.2 与指南 1.2.1。**

### 3. 范围结论

(a) `hardware/eeprom/` → **PASS**；(b) `firmware/dock_handle/` → **CHANGES_REQUIRED**；(c) ICD／ASSUMPTIONS／G6 → **CHANGES_REQUIRED**。**总结论 CHANGES_REQUIRED**。`PASS` ≠ 硬件放行。

### 4. 发现 G01–G08

| ID | 内容 |
| --- | --- |
| G01 | `dock_handle_pinmap.h` 注释中的 J2 焊盘位与 `PINMAP.md` 不一致（宏值本身正确）— 必改注释 |
| G02 | 自称「PINMAP 2026-09-20 版」已过期 |
| G03 | `ASSUMPTIONS.md` 的 AS-16／AS-28 仍高估 eFuse 对 1.2 vs 1.2.1 的分辨力 |
| G04 | ICD 的「X−1 无损」论证偏弱（`GND → 5V_IN` 方向未正确覆盖） |
| G05 | 错位枚举缺**对角**与**多列**情形（或需显式写明靠何种公差保证不会发生） |
| G06 | `AS-31-*` 仅标「待吸收」，总表无逐条登记 |
| G07 | 未经 IDF 真机编译（高风险残留） |
| G08 | EEPROM WP 默认冲突已标 ASSUMPTION — 不阻挡 (a) 的 PASS |

### 5–7 分项摘要

- **(a) PASS**：布局／CRC／样例 magic＋三段 CRC＋len 134＋SHA 均通过；`board_type 0x04` 在枚举内。
- **(b) CHANGES_REQUIRED**：GPIO 宏正确；G01／G02 需改；认领与拔出路径抽查合理；README §6 未逐行核、`PC_LINK` 未查、未编译。
- **(c) CHANGES_REQUIRED**：防呆表可复现但有 G04／G05；G6 已规定「阈值未定义不得 PASS」，**未见隐含放行**；AS-31 吸收不完整。

### 8–11 收尾

未解决：G01–G08 ＋ push 权限。下一步：主控核五题后处理必改项；取得写权限后再 push／开 PR。
