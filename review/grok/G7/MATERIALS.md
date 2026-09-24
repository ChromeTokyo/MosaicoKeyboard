# G7 已读范围

审查头：`f0536592ab4422532f9190851576ec82e261bf60`（PR #59，`chrome/single-board-press-in`）。基线：`96fd823e93f264280207eb34b7a97e139ace7378`。

| 材料 | 用途 |
| --- | --- |
| PR #59 API：头、基线、`merge_commit_sha`、正文、11 个提交、12 个文件 | 冻结对象 |
| 试合并 `2ed3a5234285ad917f46959b4777598da0a46a65` | 确认与头同树 |
| `review/chrome/single-board-press-in/README.md` | 声明与边界 |
| `corrected-orthographic-views.svg` 与同名 PNG | 方向坐标与像素核对 |
| `e0ad051` 的 `stepped-contact-section.svg` | 已撤图的左右关系 |
| `single_board_press_in_concept.scad`；`single-board-12-back.png` 色块 | 阶梯前草图 |
| `centered-controls-proportional.svg` 与 PNG；`centered-controls-prompt.txt` | 比例与效果图边界 |
| `999ee0d` 的 `dock_shell.scad` 外形／按键／电池段，以及 `LAYOUT-front.svg` 两处文本 | 105 mm 与 101.5 mm |
| `94e393c` 的 `hardware/module-board/PINMAP.md` §4–§5.1 | 旧 16 针构成、1.45 mm 阈值、E2 |
| PR #61 README 索引行（头 `665f384`） | 只取落座扫掠关系 |

未读作本判依据：#61 的 C1–C5 正文、错位脚本重跑、实物、EDA、DRC。本环境无 OpenSCAD，未导出 STL。
