提案 · 未冻结 · 由 Grok 独立复核起草 · 不得据以制造

# G6 资料索引

本索引只说明本轮读过什么。被审文件里的尺寸、料号和电源链仍是待检主张，不是放行。

冻结点：PR #61 头 `665f38472ace3eecb3edc5ec619b3a30a91cb1c3`，基线 `ead27bba0f9e8f8635a6dfe5280e234bab8dd2db`。PR #60 头 `2d0c045627cd3d217af37b14dd998df0ceca4feb`，基线 `8068ce2ddde42f81a64fd022a1529dc824a6ec4c`。本报告分支基线是 `origin/main` `96fd823e93f264280207eb34b7a97e139ace7378`。

| 路径 | 在哪一版 | 本轮用它做什么 |
| --- | --- | --- |
| `review/chrome/straight-header-side-contact/` C1–C5 与 README | #61 头 | 对照声称的料号、扫掠、固件门控和电源筛选 |
| `docs/DESIGN_STATUS.md`、`docs/TASK_BOARD.md`、`docs/handoffs/chrome.md` | #61 头相对 sweep 的 diff | 核对 J-IF-01～06 与 C6/C7 登记没有写成硬件通过 |
| `review/claude/option-j-seated.md` | sweep `ead27bb` | 坐标系、−Z 入仓、+X 撞针、不变量②、0.77/1.77 mm 原文 |
| `docs/WORK-SPLIT-20260924.md` | sweep `ead27bb` | M5 的 0.7–1.7 mm、七项判据、以及“改 4×4 脚本两个数即可复用” |
| `docs/DECISIONS.md` D-028、D-029 | sweep `ead27bb` | 现行架构与分立链作废的决定原文 |
| `review/chrome/D1-module-interface/LEFT_SLOT.md` | sweep `ead27bb` | 20 针网络，核对 p17/p18/p19/p20 |
| `firmware/dock_handle/include/dock_handle_pinmap.h` | sweep `ead27bb` | 十键针号与 GPIO |
| `firmware/dock_handle/dock_handle.c` | sweep `ead27bb` | PRESENT / VALID / HANDLE 与认领等待 |
| BSP `subboard.c`、`subboard.h`、`mosaico_module_mgr.c`、`SOURCE_INDEX.json` | sweep `ead27bb` 内的 392860b1 快照 | 左槽原样映射、GPIO14=0x50、探测与 claim |
| `hardware/check_j2_mismate.py` | sweep `ead27bb` | 确认仍是 4×4、焊盘 Ø2.0、旧坐标 |
| `references/official-v12/assembly_en.pdf` | 仓库，与 sweep 相同哈希 | 只核对 SHA。不从照片量孔 |
| C5116480 原厂 PDF、LCSC 商品页 | 本会话下载 | 三向尺寸、0.63 SQ、20 位身份、当日库存 |
| Mill-Max Omniball PDF、Harwin S1961 PDF | 本会话下载 | 行程、球径、焊盘/筒体直径、挠曲 |
| Adafruit 6106 `.sch` `.brd`、学习页 pinouts | 本会话下载 | R16 10 kΩ、板框、200 mA 停滞句 |
| TI bq25185、TPS2553 PDF | 本会话下载 | TS 固定电阻条款、ILIM 表、反向关断时间、EN 极性 |
| `hardware/dock-board/` 于 #60 头 | `2d0c045` | 历史标记、脚本实跑、G3-01 句子是否还在 |
| `review/grok/G2/REPORT.md`、`review/grok/G3/REPORT.md` | 分支 `grok/g2-consistency-review`、`grok/g3-d2d3-gates-review` | 确认先前 HOLD 条目，本轮不重跑其几何与 EEPROM 实验 |

未读作本轮证据：LM66100 原文、DFRobot DFR1026 页面、Harwin S7131 页面、实物插深、Hiro 的审查意见、PR #55 / #56 全文。C5 对 DFR1026 的否决不依赖本会话重新打开那个页面。
