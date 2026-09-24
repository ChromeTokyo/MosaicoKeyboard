# G9 已读范围

审查头：`3820c416bca6315a51c276a2d2aff52195d5ccc4`（PR #54，`chrome/v12-input-j1-boundaries`）。基线：`96fd823e93f264280207eb34b7a97e139ace7378`。

## 本 PR 的全部文本与图纸

| 路径 | 用途 |
| --- | --- |
| `review/chrome/T20-takeover/V12_INPUT_BOUNDARY.md` | 输入边界主张 |
| `review/chrome/T20-takeover/J1_MATING_OPTIONS.md` | J1 纸面比较与断电路径 |
| `review/chrome/T20-takeover/sources/README.md` | 四份 PDF 的 URL 与 SHA-256 |
| `review/chrome/T20-takeover/sources/*.pdf` | 四份归档图纸，本会话重算哈希并渲染所引页 |
| `docs/DESIGN_STATUS.md` | D-IF-01 补记、D-IF-04、D-IF-05 |
| `docs/TASK_BOARD.md` | 任务登记行 |
| `docs/handoffs/chrome.md` | 2026-09-23 进展日志 |

## 对照用的已在 main 或公开的材料

| 路径或 URL | 本轮用法 |
| --- | --- |
| `https://mosaico.espressif.com/zh/guide/` | 2026-09-24 读取扩展 I/O 表 |
| `https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s31/esp-mosaico/user_guide.html` | 2026-09-24 读取 V1.0 标题、`VIN` 与 H2.17 |
| `review/chrome/D1-module-interface/evidence/user_guide_v10.rst` | 第 590、651–653 行，与现行指南对照 |
| `review/chrome/T04/evidence/coreboard-v1.0-2026-08-18.pdf` | 字节搜索料号；文本摘录第 65 行 |
| `review/chrome/T04/COREBOARD_INTERFACE_EVIDENCE.md` | 只用来定位既有的 V1.0 D10/D15 摘录，不把它当成 V1.2 证据 |
| `references/official-v12/expansion_v121_zh.pdf` | 重算 SHA-256，渲染第 2–4 页 |
| `references/official-v12/README.md` | 归档说明；未把它的尺寸句当成工程尺寸 |
| `review/chrome/D1-module-interface/LEFT_SLOT.md` | 第 25 行仍写「供电并充电」 |
| `hardware/ASSUMPTIONS.md` AS-06、`hardware/ICD-0.2-DRAFT.md` ME-D-06 | main 上仍写「原理图标注」 |
| `94e393c:hardware/module-board/BOM.csv` | J1 = C9144 的待审基线 |

## 交叉引用，未重审全文

| 对象 | 本轮用法 |
| --- | --- |
| PR #51 头 `caa29c2` | D2 WP、D3 ILIM/升压、D4 断电表、`AS31_J1_SPEC.md`；确认 C9144/C124406 blob 相同 |
| `review/grok/G3/REPORT.md` 的 G3-06 | 对照 8.8±0.1 与 8.5±0.15；本轮自行渲染，不把 G3 的数字当唯一来源 |
| `review/grok/G6/REPORT.md` | 只查 pin17 额定与上电句，确认无冲突 |
| JLC C239341、C492438 | 2026-09-24 读取装配类别与配合针长度 |
