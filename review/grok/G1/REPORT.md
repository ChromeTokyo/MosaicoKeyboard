提案 · 未冻结 · 由 Grok 独立复核（实际模型 ID 未由可核验接口暴露 / 推理档位未暴露）起草 · 待主控处理修改项 · 不得据以制造

# G1 独立复核报告（积压二线）

- 任务 ID：G1
- 负责人／角色：Grok（EspBot），**常设第二道独立复核**（D-023），只读；**不替代** Hiro H1–H4，不批准制造
- 平台、实际模型 ID、推理档位：
  - 平台：Grok Bot（agent profile `EspBot`）
  - 实际模型 ID：**未由可核验接口暴露**（D-024；不填猜测值）
  - 推理档位：**未由可核验接口暴露**
  - 核验方式（2026-09-21 JST）：环境变量与 agent `profile.json` 均无模型／档位字段
- 日期：2026-09-21（Asia/Tokyo）
- 状态：IN_REVIEW（报告完成，待 push／PR）
- 输入冻结提交：领取时 `git rev-parse HEAD` → **`96fd823e93f264280207eb34b7a97e139ace7378`**（其后不追随移动的 main）
- 对照真本 R0：`origin/grok/r0-design-review`（[PR #43](https://github.com/ChromeTokyo/MosaicoKeyboard/pull/43) 仍开）
- 改动文件：`review/grok/G1/MATERIALS.md`、`EVIDENCE-NOTES.md`、`REPORT.md`、`docs/handoffs/grok.md`
- BSP 抽查基线：`392860b1d1a123c3377947074b2af1f600e86c5d`（SOURCE_INDEX **12/12** SHA-256+bytes OK）

## 0. 确认知悉

已按 D-023／D-024 与只读边界执行：不设计、不改 `hardware/`／`firmware/`／`mechanical/`（除本目录与 grok 交接）；不以模型多数裁决；D1 结论标为 **G1-D1-*** 二线，**不替代 Hiro H1**；**未领取** V0 auditor 包（该包审审查者本身，应按其要求换模型家族）。

## 1. 范围与方法

| 块 | 内容 | 方法 |
| --- | --- | --- |
| A | G01–G08 在冻结 SHA 是否仍开；V0 附录 vs R0 真本 | 源码／ICD／ASSUMPTIONS 对照；`diff` 真本与附录 |
| B | BUILD-LOG MB-CHK-10 | 读日志；检索 `.scad`；尝试 OpenSCAD（本机缺失则声明） |
| C | Chrome D1 高后果主张 | 对 `evidence/bsp` + `user_guide_v10.rst` 独立核对 |

细节与行号见 `review/grok/G1/EVIDENCE-NOTES.md`。

## 2. 总结论

**CHANGES_REQUIRED**

证据不全（机械源缺失）与 G04／G05 仍开 → **不得 PASS**。未判 BLOCKED：设计文档与固件仍可继续整改；但机械「可制造」叙事在 `.scad` 入库并复算前应视为阻塞。

## 3. 关键结果

- **G04／G05：仍开（紧急）** — ICD `L144` 仍称 X−1「无损」；§3.3 错位表仍无对角／多列或显式公差排除声明。V0 旁注「尚未整改」与本轮核对一致。
- **G01–G03、G06–G07：仍开**；**G08** 仍为已知 ASSUMPTION（WP 默认待 Chrome）。
- **MB-CHK-10：未能确认** — `module_board.scad`（及 BUILD-LOG 所引另两份 `.scad`）**不在**冻结 SHA；PR #46 提交 `a6d87f2` 只新增 BUILD-LOG。本机无 OpenSCAD，未编译。仅确认日志内 2.405 vs ≥2.5 → 差 0.095 算术自洽。
- **D1 二线：** 左槽 GPIO 集合／GPIO14→0x50／I²S∅／init 上电顺序与 BSP+V1.0 指南一致；pin17 额定与「不得等 EEPROM」属边界／推导，**不得**当 V1.2 电气已闭合。

## 4. 发现表

| ID | 严重度 | 一句话 |
| --- | --- | --- |
| G1-A-G01 | must-fix | `dock_handle_pinmap.h`／README 焊盘注释 ≠ PINMAP 修订 b（GPIO 宏正确） |
| G1-A-G02 | nit | PINMAP 版本戳仍写 2026-09-20 |
| G1-A-G03 | must-fix | AS-16／AS-28 仍高估 eFuse 对 1.2 vs 1.2.1 分辨力 |
| G1-A-G04 | **blocker** | ICD X−1「无损」对 GND→5V_IN 论证未补强 |
| G1-A-G05 | **blocker** | 错位枚举缺对角／多列或显式公差排除 |
| G1-A-G06 | nit | AS-31-* 待吸收 |
| G1-A-G07 | must-fix | `dock_handle` 仍未 `idf.py build` |
| G1-A-G08 | nit | WP 默认待 Chrome（已知开放） |
| G1-B-01 | **blocker** | BUILD-LOG 引用的 `.scad` 未入库；MB-CHK-10 不可复算 |
| G1-B-02 | nit | ASSUMPTIONS 机械路径名与 BUILD-LOG 目录名不一致 |
| G1-B-03 | 信息 | 本机无 OpenSCAD；未编译 |
| G1-C-D1-01 | must-fix | pin17／V1.2 额定保持 unknown |
| G1-C-D1-02 | nit | LEFT_SLOT「按键上拉」措辞易误导（应以 ICD EL-D-05 为准） |
| G1-T-01 | 信息 | V0 附录为压缩转录；优先 R0 真本（附录删去 G04 完整推导） |

发现计数：**14**。

## 5. 附录比对（A 附）

`review/audit/V0/APPENDIX-grok-r0-transcript.md` = 主控据转贴的压缩件 + provenance 声明；Q／G 结论与真本一致，但删除大量 file:line 与 G04 完整推导。审计与闭环应以 `origin/grok/r0-design-review:review/grok/R0/REPORT.md` 为准。

## 6. 未做／边界

- 未跑 OpenSCAD；未 `idf.py build`；未读 Hiro H0 全文（避免锚定）；未改设计文件；未领取 V0。
- 本报告**不构成** G1–G3 放行，**不批准**制造。

## 7. 建议主控下一步

1. **优先**改 ICD §3.3（G04／G05），再请二线复扫。
2. 将 `mechanical/**/*.scad` 与 BUILD-LOG **同 SHA** 入库，便于复算 MB-CHK-10。
3. 合入／处理 [PR #43](https://github.com/ChromeTokyo/MosaicoKeyboard/pull/43)（R0 真本）；附录可保留作历史但标「非权威」。
4. 修 G01 焊盘注释与 G03 eFuse 措辞；G07 待本机 IDF ≥6.2 + esp32s31。
