# G4 资料边界

本文件只列本会话实际打开过的对象。未打开的不算已复核。

## 已读

| 对象 | SHA / 位置 | 用途 |
| --- | --- | --- |
| PR #55 元数据 | `gh pr view 55`；头 `82df4c6534c3aa534e5ec67381e4a7767708c749`；基线 `96fd823e93f264280207eb34b7a97e139ace7378`；`mergeCommit` = null；draft；作者 login `Jarvis110469` | 头、基线、作者、文件清单 |
| PR #55 五次提交 | `30ec0d8`、`361b6ef`、`29c4239`、`ab886d7`、`82df4c6` | 作者邮箱均为 `chrome@chromedeMac-mini.local` |
| `14186ea98e686e061f13291c85443e4ce64d0373` | GitHub commit API | 预览合并的父母、树、提交者、所在分支 |
| `docs/MEASUREMENT_PROTOCOL.md` | `82df4c6` 全文 | 规程安全性与版次分界 |
| `review/chrome/T14/MEASUREMENT_RECORD.md` | `82df4c6` 全文 | 空白栏、清单、是否写入实测值 |
| 上述两文件加 `docs/TASK_BOARD.md`、`docs/handoffs/chrome.md` 的 diff | `96fd823...82df4c6` | 与 PR 说明对照；`git diff --stat` +140/−27，4 文件 |
| `hardware/ASSUMPTIONS.md` | `main` `96fd823` 第 18–21、33 行 | AS-02／03／04／05／17 的到货句子 |
| `hardware/ICD-0.2-DRAFT.md` | `main` `96fd823` 第 1 节 | 屏幕朝用户、USB-C 朝下、左槽在左 |
| `references/official-v12/README.md` | `main` `96fd823` | 扩展指南拆底板取电的已有记录 |
| `review/grok/G2/REPORT.md` | `origin/grok/g2-consistency-review` 头 `3b3ad3050fbe192e9242ce4efd6ed4620ba1db5d` | 方案 J／G2 HOLD 范围，不重做 |
| `review/grok/G3/REPORT.md` | `origin/grok/g3-d2d3-gates-review` 头 `cef80b8e114f372cca21ddfd344f0ab017e26cfc` | J1 配合仍未知；报告格式对照 |
| `cursor-cloud` `run-info` | 本会话 `bc-2e7662a6-22dd-521a-be6f-2d381b65f36b` | `originalModelName` |

## 未读 / 未跑

- 实物、卡尺、相机或任何到货照片的像素测量
- OpenSCAD、`check_fit_geometry.py`、方案 J 触点场几何的重跑
- `14186ea` 作为审查冻结点（树与头相同，且不在任何分支上）
- Hiro H1–H4 的新审查；本会话没有把 PR 作者显示名当作 Hiro 签字
