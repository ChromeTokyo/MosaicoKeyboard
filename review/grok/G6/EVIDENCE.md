提案 · 未冻结 · 由 Grok 独立复核起草 · 不得据以制造

# G6 证据：提交、哈希与重算

审查对象是 PR 头，不是派发消息里的试合并短 SHA。式子在本会话用 Python 重算。

## 提交

| 名称 | SHA |
| --- | --- |
| `origin/main` | `96fd823e93f264280207eb34b7a97e139ace7378` |
| PR #61 头 `chrome/straight-header-side-contact` | `665f38472ace3eecb3edc5ec619b3a30a91cb1c3` |
| PR #61 基线 `sweep/consistency-20260921` | `ead27bba0f9e8f8635a6dfe5280e234bab8dd2db` |
| GitHub 试合并对象 | `5d1ec685dbfb2a2a1cbdefbff4b7ce7d721915da` |
| 试合并父母 | `ead27bba0f9e8f8635a6dfe5280e234bab8dd2db` `665f38472ace3eecb3edc5ec619b3a30a91cb1c3` |
| PR #60 头 `chrome/dock-board-retire` | `2d0c045627cd3d217af37b14dd998df0ceca4feb` |
| PR #60 基线 `claude/design-d/dock-board` | `8068ce2ddde42f81a64fd022a1529dc824a6ec4c` |

`git diff --stat 5d1ec685 665f384` 为空。PR JSON 的 `mergeCommit` 为 null。#61 相对基线 9 个文件，`+203/−0`。

## 原件哈希（本会话下载或仓库内文件）

| 文件 | SHA-256 | 与 PR 声称 |
| --- | --- | --- |
| `references/official-v12/assembly_en.pdf` | `0798e39de4583f2b01d78bd0cd2318fb715ab5c2dd5180c4ff917c3b199957bf` | 相同 |
| LCSC 上的 C5116480 原厂 PDF | `0ed111eb1634ce9a37b7db95ed41f1f127768e4b85a80e28b310701210440a5b` | 相同 |
| Mill-Max Omniball PDF | `cee20c59c7c77a86aa7928119cc068d5c6e84c7825ebf5991251ad979d6db955` | 相同 |
| Harwin S1961 图 | `c2684394fdf160756dacf8c4c359bad524dbb0dd95530e0762dd3cc55786a0b3` | 相同 |
| Adafruit 6106 `.sch` | `d1f47f395296bb3e6450014745ead0d2665607e3f17d18c433826c5c35a9e039` | 相同 |
| Adafruit 6106 `.brd` | `653b8636b76a9f31950635950c72c748811e7b3d7258f7a7b1a99ce2cabc7708` | 相同 |
| TI bq25185 PDF | `c73ed7d63e6532bb05e26df30edd37c6ac2de310c1222a84a77625e15e133684` | 相同 |
| TI TPS2553 PDF | `88e453700cea2b263cdb5b44fce1e883e0f6d3b975457f879ac1423eeea42071` | 相同 |
| 归档 BSP `subboard.c` | `f1d80ae6e4a1a7091a778c1044a7cabd2a8bcea12cfedf32b1d9b524d39af5d7` | 与 `SOURCE_INDEX.json` 相同；commit `392860b1d1a123c3377947074b2af1f600e86c5d` |

LM66100 PDF 本会话未下载，不核对其声称哈希。

## 直排针图与商品页

原厂 PDF 文字层（一页，图题 `2.54-2*N`，日期 20250626）：`6.0±0.2`、`3.0±0.2`（两处）、`2.54`、`0.63 SQ`、`5.08`、`φ1.02`、2.5 A、黄铜、Au over Ni。`φ1.02` 在 PCB 布局侧，不当成针边长。

LCSC `C5116480` 同日重抓：名称 `ZHOURI 2.54-2*10`，20P，方针，节距 2.54 mm，配合端长度 6 mm，尾端 3 mm，绝缘高度 2.54 mm，额定 2.5 A，`inventoryLevel` 1680。C1 文中的 2815 与这次抓取不同。

## 落座几何

节距 `p = 2.54 mm`，半间距 `1.27 mm`。

Ø0.9 mm 圆头、边长 `a` 的方针，只碰端面：

| 量 | a = 0.64 mm | a = 0.63 mm |
| --- | --- | --- |
| 轴向触及 `a/2 + 0.45` | 0.7700 mm | 0.7650 mm |
| 对角触及 `a/√2 + 0.45` | 0.9025 mm | 0.8955 mm |
| 小于半间距，终点不双搭 | 是 | 是 |
| 邻针开始被对角碰到的位移 `p − 触及` | 1.6375 mm | 1.6445 mm |
| 轴向开路带 | 0.77–1.77 mm | 0.765–1.775 mm |

扫掠：主机沿 −Z 运动时，触头在主机坐标中沿 +Z 移动。奇数排 Z 较大时，p17 的触头先对齐 p18；偶数排 Z 较大时，p20 的触头先对齐 p19。领先针的电气接触比两排中心距再提前大约一个触及半径。

## Omniball

`0.091 × 25.4 = 2.3114 mm`，半径 `R = 1.1557 mm`。

满行程 `0.030 × 25.4 = 0.7620 mm`；`0.025 × 25.4 = 0.6350 mm`；`0.035 × 25.4 = 0.8890 mm`。

交线圆半径 `ρ = √(2 R s − s²)`：

| 压缩 s | ρ |
| --- | --- |
| 0.635 mm | 1.0318 mm |
| 0.762 mm | 1.0866 mm |
| 0.889 mm | 1.1245 mm |

0.64 mm 方尾、节距 2.54 mm：间隙半宽 `(2.54 − 0.64) / 2 = 0.95 mm`。间隙中点同时碰到两尾的压缩根为 **0.4976 mm** 与 1.8138 mm。名义满行程落在这两根之间。针心对准时，到邻针近边 2.22 mm，ρ 1.087 mm 碰不到。

0.63 mm 方尾：间隙半宽 0.955 mm，桥接压缩根 **0.5048 mm**。对准时到邻边 2.225 mm，仍碰不到。

`.102 × 25.4 = 2.5908 mm`，比 2.54 mm 大 0.0508 mm。`.128 × 25.4 = 3.2512 mm`（连接器建议焊盘）。`.118 × 25.4 = 2.9972 mm`（0945 图上另一处直径标注，本轮不指定它是筒体还是焊盘）。

Ø0.9 mm 球的最大交线圆半径是 0.45 mm，小于 0.95 mm。

## 6106 与 TPS2553

`.sch`：`R16` 器件 `_0402NO`，值 `10K`。网 `THERM` 连接 `IC2` 引脚 `TS/MR` 与 `R16` pin 2。`R16` pin 1 与 GND 符号相连。

`.brd`：layer 20 导线包围盒 X 0–29.21 mm，Y 0–19.05 mm。尺寸线 `x1=0,x2=29.21` 与 `y1=0,y2=19.05`。

bq25185 第 18 页 §6.3.9：「If the TS function is not required, connect a 10kΩ resistor from the TS/MR pin to GND.」

TPS2553 第 5 页：`EN = Active High for the TPS2553`。第 7 页电气表：20 kΩ 在 −40 °C 至 125 °C 为 1200 / 1295 / 1375 mA；49.9 kΩ 为 475 / 520 / 565 mA。反向电压到 MOSFET 关断：3 / 5 / 7 ms。

Adafruit pinouts 页原文要点：TPS61023（页面写作 TP61023）在超过 200 mA 的瞬时负载下会 stall。该页没有给出纹波毫伏数。

## 固件与旧网表

`dock_handle.c` 于 `ead27bb`：`candidate_ok` 在 L407–422；GPIO 配置在 L382–401；`init` 在 L706–748。`mosaico_module_mgr.c`：探测 `present = probe_ret == ESP_OK` 在 L481–483；`claim_matches_locked` 要求 `PRESENT` 在 L994–998。左槽地址宏在 `subboard.h` L34–38。

#60 头上 `check_netlist.py` 退出码 0。首行报告 214 个引脚、75 个器件、60 个网。末行：“历史网表内部检查通过；现行方案 J 的电气、机械及制造安全未验证。”

归档后的 `POWER_TOPOLOGY.md` 仍有：`R_FB1 = 909 kΩ` 得到 5.10 V，以及 `768 kΩ → 5.16 V`、`750 kΩ → 5.06 V`。
