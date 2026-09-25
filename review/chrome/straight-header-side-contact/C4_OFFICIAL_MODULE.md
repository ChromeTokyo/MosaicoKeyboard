# C4 补充：官方 Module Interaction 能否作十键手柄转接件（2026-09-25）

**结论：不能把这块官方模块直接代入现行方案 J，称作已可用的十键转接件。** 官方装配图可见一侧公针插进 Mosaico、另一侧为母座；它不是现行方案 J 所需的「穿过直排针本体、留裸针尾供底座撞针侧擦」构造。若底座主板也放母座，得到的是母座对母座，无法直接配接。即使另加公针，配合动作、受力、外形和电路都变成另一套架构，须重新审查；官方 PCB 目前没有可核对的网表。此结论是对**直接替换**的否定，不是否定另行设计并验证的改造方案，也不是硬件放行。

## 证据边界

| 已核实的依据 | 能证明什么 | 不能证明什么 |
| --- | --- | --- |
| 已归档的官方 [英文装配指南 pp.2–4](https://github.com/ChromeTokyo/MosaicoKeyboard/blob/eb56b33fb42ca3191aa842e9f1d211d879d8beb2/references/official-module-interaction/guide-b.pdf)（SHA-256 `0c0cf889f44397cb9f14b0da9371631190fbbf3df34fcf9cad0623b1799f4c46`），[design-3](https://github.com/ChromeTokyo/MosaicoKeyboard/blob/eb56b33fb42ca3191aa842e9f1d211d879d8beb2/references/official-module-interaction/design-3.png)、[design-6](https://github.com/ChromeTokyo/MosaicoKeyboard/blob/eb56b33fb42ca3191aa842e9f1d211d879d8beb2/references/official-module-interaction/design-6.png) | PCB 有插向 Mosaico 的双排公针、两个轴座，另一侧可见 2×10 母座；图片里的模块装在 Mosaico 右侧 | 公针与母座逐脚直通、针号朝向、EEPROM/电源网络、额定电流、插拔寿命、改放左槽的外壳配合 |
| 固定 BSP `392860b1` 的 [交互模块驱动](../D1-module-interface/evidence/bsp/components/mosaico_module_interact/mosaico_module_interact.c) L137–153、L785–824，及[左槽 H2 表](../D1-module-interface/LEFT_SLOT.md) | 驱动为交互模块分配六根左槽 GPIO，并按 `INTERACT` 类型向管理器 claim；这不是专用十键手柄驱动 | 实物 V0.2 PCB 究竟焊接了哪些网络、对侧母座暴露哪些 GPIO |
| 官方 [esp-dev-kits 快照 `ab7aff2e`](https://github.com/espressif/esp-dev-kits/tree/ab7aff2e0c171e6918c88555b700798f36caeb67)与已归档两份 MakerWorld 3MF | 2026-09-25 检索的 esp-dev-kits 全树（4919 项，未截断）未见 Module Interaction V0.2 的原理图／网表／Gerber；3MF 解包只见打印对象、指南及图片 | 不代表官方或其他渠道绝无电路源。MakerWorld 当前下载清单本次无法复核（页面返回 403） |

[官方 MakerWorld 模型页](https://makerworld.com/zh/models/3349721-esp-mosaico-module-interaction)提供产品出处；归档资料及其派生尺寸在固定提交的[解析](https://github.com/ChromeTokyo/MosaicoKeyboard/blob/eb56b33fb42ca3191aa842e9f1d211d879d8beb2/references/official-module-interaction/ANALYSIS.md)。官方 esp-dev-kits 的 [Mosaico 用户指南](https://github.com/espressif/esp-dev-kits/blob/ab7aff2e0c171e6918c88555b700798f36caeb67/docs/en/esp-mosaico/user_guide.rst)标为 CoreBoard V1.0，不能用它给 V0.2 交互模块或 V1.2 主机定网表。上述图片只用于判断可见配接外形；`44.90 × 44.90 × 10.90 mm` 是压缩网格的 **derived** 外廓，不能用于制造冻结。

## 对现行十键线路的影响

现行 [C3 十键表](C3_CONTACT_FIELD.md)用 H2 p1/3/5/7/9/11 与 p2/4/6/8 作十键，p12 留作备用。按 [H2 GPIO 合同](../D1-module-interface/LEFT_SLOT.md)和 BSP `get_hw_config()`，其中以下五根已被**官方交互模块驱动分配**：

| 十键位 | H2 / GPIO | 官方交互模块驱动用途 |
| --- | --- | --- |
| A | p2 / GPIO53 | LDR |
| B | p4 / GPIO48 | IR |
| X | p6 / GPIO13 | 模块左键 |
| Y | p8 / GPIO12 | 模块右键 |
| R | p11 / GPIO15 | WS2812 |

p12 / GPIO4 还被该驱动分给 PIR。其余十键表中的 p1/3/5/7/9 未被该驱动显式分配，**不等于**已证明从官方 PCB 的外侧母座引出且无其他负载。若上述六根确实接到板上器件，原来左槽「11 根可供十键选择」的论证不能原封不动套在官方模块**后面**。特别是两个现成轴座只能代表两路输入；它们不能自动扩充成独立十路。`mosaico_interact_open()`要求 `INTERACT` 身份，现有 `dock_handle` 要求 `HANDLE` 身份及管理器 claim（见 [原 C4](C4_EEPROM_FORM.md)），同一模块身份不能被当成两种驱动已无冲突。官方板是否确实装有 EEPROM、写了什么内容，仍需读取实物或取得电路源；不能仅凭旧[解析](https://github.com/ChromeTokyo/MosaicoKeyboard/blob/eb56b33fb42ca3191aa842e9f1d211d879d8beb2/references/official-module-interaction/ANALYSIS.md)的推测定案。

## 三条路径，避免混作一条

| 路径 | 当前判断 | 还要做什么 |
| --- | --- | --- |
| 保留方案 J 的裸直排针／自制小板 | [原 C4](C4_EEPROM_FORM.md) 的软件判断继续成立：专用固件可跳过 EEPROM 直接读左槽十键；当前固件尚不支持。官方模块不改变 C2 擦触件、[C3 动态错针](C3_CONTACT_FIELD.md)和 C5 电源阻断 | C1/C2/C3/M1/M5/M6 各自闭环，独立复核后才考虑 C6 |
| 官方模块留作原用途／Q1 两键试用 | 官方外形和两键固件是可测的参考样件，不能据此给最终十键手柄放行 | 到货测公针、壳体与 H2；Q3 测识别、两键、电源，但结果只覆盖该用例 |
| 官方模块加转接公针、改 PCB，或让手柄沿 X 轴插其外侧母座 | **新架构研究项**。在图示右侧模块改放左侧、针 1 朝向、手柄配对性与十路电路未证实前，不纳入方案 J。新增连接器也需定义独立轴向止挡；不能沿用「−Z 落座、尾端侧擦、H2 不受剪」的论证 | 先取得原理图/网表，或样件断电逐脚通断与对地/电源测量；确认六路板载负载、外侧母座 pinout、EEPROM/5V_IN/5V_OUT 路径；再做左右槽实配、全行程碰撞/受力与供电故障验证，交 Hiro/Grok 独立审查，由主控记录架构变更 |

**上电边界：** 未证明外侧母座各孔与 H2 p17/p18/p19/p20 的对应关系及电源网络前，不从手柄向该母座送 5 V。官方模块也不消除现行 [J-IF-03](../../../docs/DESIGN_STATUS.md) 的 `5V_IN` 对 `5V_OUT`、GND 对 `VCC_3V3` 动态错位风险。先做无电通断，再以有限流、可观测的分步供电检查真实样件；不凭外观或 V1.0 手册推载流能力。

**交接给主控：** 官方交互模块不是 C4 的「免转接件」捷径。不要以它替换 (a)/(b) 后直接开 C6，也不要据此改 Claude 的机械设计；如考虑第三条路径，应由用户/主控作为新的架构选择，重新分配机械、电气和审查工作。本人未改官方板、未编译固件、未通电、未实配，结论等待 Hiro/Grok 对接口与风险独立复核。
