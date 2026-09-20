# references/ 目录盘点

基线日期：2026-09-20。输入提交：`3d5a112`，分支 `docs/t01-lead-handover`。负责人：Claude（主控）。

本文按实际引用关系盘点 `references/` 目录，用于落实 `AGENTS.md` 的「库缓存中未使用或误选的器件不能自动进入生产 BOM」，以及 `docs/DESIGN_STATUS.md` 中对 `references/` 的说明「应按实际引用建立清单」。

本文只记录仓库文件中已经存在的内容。**它不判定电气正确性、封装正确性或供应可行性，也不给出、推荐或冻结任何机械与电气数值。** 表中的料号与封装名是缓存 JSON 的自述字符串，未经原厂资料核对。阻容值、引脚号、电流、尺寸等参数由 Chrome 提交、Hiro 复核后填入相应设计文件，不在本文产生。

## 1. 口径与方法

- 器件身份取自每个 `C*.json` 的 `result.dataStr.head.c_para` 字段（`Manufacturer Part`、`package`、`Manufacturer`）与 `result.tags`，不从文件名推断。
- 「已引用」指该编号在 `design/build_design.py`、`design/design-netlist.json`、`design/bom-review.csv` 中至少出现一次。三个文件的编号集合一致（`bom-review.csv` 的差异项 `C0603` 是封装名，不是器件编号）。
- `design/mosaico-dock-schematic.json` 与 `design/mosaico-dock-placement.json` 是 `build_design.py` 的生成输出，编号集合与上述一致，不单独计数。
- `design/pin-net-review.csv` 中不含任何 LCSC 编号。
- 文本匹配会命中 `C0603`（封装名）、`C0000`（颜色值 `#CC0000` 的片段）、`C201610`（料号 `FTC201610S1R0MBCA` 的片段），均已排除。

| 类别 | 数量 | 说明 |
| --- | --- | --- |
| `references/` 中的 `C*.json` | 31 | 30 个成功记录，1 个失败记录 |
| 已引用 | 25 | 缓存存在且被 design 文件引用 |
| 未引用 | 6 | 缓存存在但 design 文件未引用（含 1 个失败记录） |
| 引用但缺失 | 1 | design 文件引用，但 `references/` 无对应文件 |

另有 `references/README.md`，为资料入口索引，不是器件缓存。

## 2. 已引用（25 项）

位号列引自 `design/bom-review.csv`。类别列译自缓存的 `tags` 字段，是缓存的分类标签，不是经核对的器件功能结论。

| LCSC 编号 | 缓存中的制造商料号 | 缓存中的封装名 | 制造商 | 缓存类别 | design 位号 |
| --- | --- | --- | --- | --- | --- |
| `C130204` | TCA9535PWR | TSSOP-24_L7.8-W4.4-P0.65-LS6.4-BL | TI（德州仪器） | I/O 扩展器 | U1 |
| `C54313` | BQ24074RGTR | QFN-16_L3.0-W3.0-P0.50-TL-EP1.7 | TI（德州仪器） | 电池管理 IC | U2 |
| `C919459` | TPS61023DRLR | SOT-563_L1.6-W1.2-P0.50-LS1.6-BR | TI（德州仪器） | DC-DC 变换器 | U3 |
| `C2869734` | LM66100DCKR | SC-70-6_L2.0-W1.3-P0.65-LS2.1-BL | TI（德州仪器） | 预购类（缓存分类） | U4 |
| `C404027` | TLV75533PDBVR | SOT-23-5_L3.0-W1.7-P0.95-LS2.8-BR | TI（德州仪器） | LDO 线性稳压器 | U5 |
| `C544515` | TCA9517DGKR | VSSOP-8_L3.0-W3.0-P0.65-LS5.0-BL | TI（德州仪器） | 电平转换／缓冲器 | U6 |
| `C2682616` | MAX17048G+T10 | TDFN-8_L2.0-W2.0-P0.50-BL-EP1.2 | ADI／MAXIM | 电池管理 IC | U7 |
| `C55266` | TPS2553DBVR | SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BR | TI（德州仪器） | 电源分配开关 | U8 |
| `C165948` | TYPE-C-31-M-12 | USB-C_SMD-TYPE-C-31-M-12_1 | 韩国韩荣 | USB 连接器 | J1 |
| `C160353` | B3B-PH-SM4-TB(LF)(SN) | CONN-SMD_B3B-PH-SM4-TB-LF-SN | JST | 线对板连接器 | J2 |
| `C5832342` | FTC201610S1R0MBCA | IND-SMD_L2.0-W1.6-B | cjiang（长江微电） | 功率电感 | L1 |
| `C2296` | KT-0805黄灯 | LED0805-R-RD | KENTO | LED | D1、D2 |
| `C720477` | TS-1088-AR02016 | SW-SMD_L3.9-W3.0-P4.45 | XUNPU（讯普） | 轻触开关 | SW1–SW11 |
| `C431540` | MSK12C02 | SW-TH_MSK12C02 | SHOU HAN（首韩） | 拨动开关 | SW12 |
| `C25804` | 0603WAF1002T5E | R0603 | UNI-ROYAL（厚声） | 贴片电阻 | R1–R17 |
| `C23186` | 0603WAF5101T5E | R0603 | UNI-ROYAL（厚声） | 贴片电阻 | R18、R19 |
| `C4177` | 0603WAF1801T5E | R0603 | UNI-ROYAL（厚声） | 贴片电阻 | R20 |
| `C22978` | 0603WAF3301T5E | R0603 | UNI-ROYAL（厚声） | 贴片电阻 | R21 |
| `C25819` | 0603WAF4702T5E | R0603 | UNI-ROYAL（厚声） | 贴片电阻 | R22 |
| `C23162` | 0603WAF4701T5E | R0603 | UNI-ROYAL（厚声） | 贴片电阻 | R23、R24、R29、R30 |
| `C25803` | 0603WAF1003T5E | R0603 | UNI-ROYAL（厚声） | 贴片电阻 | R25、R27 |
| `C1591` | CL10B104KB8NNNC | C0603 | SAMSUNG（三星） | 贴片电容 | C1、C9、C14、C15、C16 |
| `C15849` | CL10A105KB8NNNC | C0603 | SAMSUNG（三星） | 贴片电容 | C2、C3、C10、C11、C12、C13 |
| `C96446` | CL10A106MA8NRNC | C0603 | SAMSUNG（三星） | 贴片电容 | C4、C6 |
| `C45783` | CL21A226MAQNNNE | C0805 | SAMSUNG（三星） | 贴片电容 | C5、C7、C8 |

被引用不等于已审核。这 25 项在 `design/bom-review.csv` 中的 Geometry status 均为「Supplier library geometry; final manufacturer audit pending」，即仍未完成原厂资料核对。

## 3. 未引用（6 项）

以下编号在仓库中除自身缓存文件外，没有任何引用（已对 `*.md`、`*.py`、`*.csv`、`*.json` 全仓检索确认）。

| LCSC 编号 | 缓存中的制造商料号 | 缓存中的封装名 | 制造商 | 缓存类别 | 记录状态 |
| --- | --- | --- | --- | --- | --- |
| `C165960` | B1505XT-1WR2 | PWRM-SMD_BXXXXXT-1WR2 | MORNSUN（金升阳） | 电源模块 | 成功 |
| `C2290` | KT-0603W | LED0603-R-RD_WHITE | KENTO | LED | 成功 |
| `C22827` | 0603WAF1803T5E | R0603 | UNI-ROYAL（厚声） | 贴片电阻 | 成功 |
| `C23138` | 0603WAF3300T5E | R0603 | UNI-ROYAL（厚声） | 贴片电阻 | 成功 |
| `C28323` | CL21B105KBFNNNE | C0805 | SAMSUNG（三星） | 贴片电容 | 成功 |
| `C16043` | 未知 | 未知 | 未知 | 未知 | 失败：`{"success": false, "code": 404, "message": "Component not found"}` |

`C16043` 文件仅含一条 404 记录，无法从内容判断它对应什么器件，只能确认它未被 design 引用。抓取它的原因在仓库中没有记录。

这 6 项是研究过程残留，可以保留在 `references/` 作为过程记录，但在被正式选用并完成审核前，不得出现在任何 BOM 输出中。

## 4. 引用但缺失（1 项）

| LCSC 编号 | design 位号 | 引用位置 | `references/` 是否有文件 |
| --- | --- | --- | --- |
| `C23239` | R26 | `design/build_design.py:92`、`design/design-netlist.json:1424`、`design/bom-review.csv:52`，并已进入生成的原理图与布局文件 | 否 |

这是本次盘点最需要处理的一项，原因是生成脚本的静默回退行为：

`design/build_design.py` 的 `library()` 在缓存文件不存在时直接 `return None`（第 19 行 `if not p.exists(): return None`），`passive()` 随后回退到本地绘制的通用封装名（第 39–42 行）。因此 `C23239` 在没有任何库几何来源的情况下，仍然带着该编号进入了原理图、布局、网表和 BOM。

`design/bom-review.csv` 第 52 行把 R26 的 Geometry status 标为「Locally drawn placeholder; library/land-pattern verification required」，这与事实一致；但同一行的 LCSC 列仍然写着 `C23239`。若直接照抄该 CSV 采购，会把一个没有库封装依据的编号带进生产。

同一文件中还有若干无采购编号的行，一并列出以免被当成可下单清单：

| 位号 | LCSC 列 | Geometry status |
| --- | --- | --- |
| R28 | 空 | Locally drawn placeholder；备注「Exact LCSC procurement code pending」 |
| J3 | 空 | Locally drawn placeholder；封装名为 `POGO_GEOMETRY_UNVERIFIED` |
| TP1–TP12 | 空 | Locally drawn placeholder；封装名为 `TESTPAD_1.0mm` |

J3 与 TP 系列的具体数值不在本文讨论范围，由 Chrome 提交、Hiro 复核后填入。

## 5. 缓存元数据的限制

- 缓存 JSON 中没有抓取时间，也没有记录实际使用的接口版本。`references/README.md` 的示例 URL 带 `version=6.4.19.5`，但文件内容无法证明每个缓存都来自该版本。缓存因此不可精确复现。
- `result.updated_at` 是库记录在服务端的更新时间，取值分布在 2024-05-17 至 2026-09-19，不是抓取时间，不能当作证据日期。
- 缓存含 `SMT`、`jlcOnSale`、库存与价格字段。这些是抓取当时的快照，不构成嘉立创有料、可贴装或价格的证据，对应 `docs/DESIGN_STATUS.md` 的 O10。本文不转录这些数值，以免被当成采购结论。
- `C5832342` 的 `SMT` 字段为空，其余 29 条成功记录该字段为 true。含义未知。
- `C2869734` 的缓存类别为「Pre-ordered Chips」（预购），`C544515` 的 `lcsc.url` 路径含 `presales`。这两条是缓存抓取当时的供应分类标记，当前供应状态未知。

## 6. 规则落地建议

本节是主控提出的流程建议，不构成对 `design/` 文件的修改授权；涉及 `design/` 的改动由 Chrome 执行。

| 编号 | 规则 | 当前状态 | 建议动作 | 责任人 |
| --- | --- | --- | --- | --- |
| P-1 | 生产 BOM 只能取自第 2 节「已引用」清单，且每行必须同时具备 LCSC 编号与经核对的封装 | 未落实；当前 BOM 中存在有编号无库封装、以及无编号的行 | 在 BOM 生成或导出环节加入该校验 | Chrome 实施，Hiro 复核 |
| P-2 | 第 3 节「未引用」的 6 个编号不得自动进入任何 BOM | 目前它们确实未进入 BOM，但没有任何机制阻止后续误用 | 在 `references/README.md` 标注未采用状态（本轮未改该文件） | Chrome 或 Claude 另起提交 |
| P-3 | 「引用但缺失」必须清零 | 存在 1 项（`C23239`） | 补齐库文件或改用已核验器件；在此之前 R26 行不得随 BOM 下单 | Chrome 提交，Hiro 复核 |
| P-4 | 生成脚本遇到缺失库时应显式失败或显式标记，而非静默回退到通用封装 | 未落实 | 由 Chrome 判断修改方式；本文只提出问题，不改 `design/` | Chrome |
| P-5 | 缓存应记录抓取日期与接口版本 | 未落实 | 重新抓取或补充索引时一并登记 | Chrome |

## 7. 未解决项

| 编号 | 问题 | 解除所需证据 | 由谁提供 |
| --- | --- | --- | --- |
| RI-01 | `C23239` 被 design 引用但无库文件，R26 的焊盘是本地绘制的占位图形 | 补齐并核对该编号的库封装，或替换为已核验器件，并说明 land pattern 依据 | Chrome 提交，Hiro 复核 |
| RI-02 | 6 个未引用编号的抓取原因与预期用途在仓库中无记录 | 说明当初的候选用途，或明确标注放弃 | Chrome |
| RI-03 | `C16043` 内容仅为 404，对应什么器件未知 | 重新抓取确认，或删除并在索引中说明 | Chrome |
| RI-04 | 缓存无抓取日期与接口版本，不可精确复现 | 重新抓取并登记日期与版本 | Chrome |
| RI-05 | `C5832342` 的 `SMT` 字段为空，含义未知 | 核实该编号的实际贴装可行性 | Chrome 核实，Hiro 复核 |
| RI-06 | R28、J3、TP1–TP12 无采购编号 | 完成选型后补齐编号与封装依据 | Chrome 提交，Hiro 复核 |
| RI-07 | 25 个已引用编号的封装均未完成原厂核对 | 逐项核对原厂资料的引脚表与推荐 land pattern，记录数据表版本与页码 | Chrome 提交，Hiro 复核 |

本文不改变任何设计结论，也不解除上述任何一项。`references/` 中存在库文件，只说明抓取成功，不说明器件已选用、封装已核对或国内工厂可采购可贴装。
