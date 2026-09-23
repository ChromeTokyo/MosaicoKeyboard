# V1.2 左槽 5 V IN 证据边界（未冻结）

核查日：2026-09-23 JST。目标是用户开箱视频所见的 BaseBoard-A V1.2／CoreBoard V1.2；具体到货硬件尚未核版、未拆解、未上电测 H2。此报告仅评估公开资料能支持哪些设计前提，不给 pin17 载流额定。

## 可用结论

乐鑫[现行 ESP-Mosaico 产品指南](https://mosaico.espressif.com/zh/guide/)的“扩展 I/O”表把 `IN` 定义为**外部 5 V 输入，可给设备供电**；同表的 `5V`、`3V` 是**向外输出**，各最多 100 mA。该页未标硬件版次、H2 针号、输入电流或内部电路。因此它支持方案 D 以外部 5 V 输入为方向，**不能把 100 mA 输出限额套到输入**，也不能单凭该页断言目标 V1.2 的 H2.17 能给机内电池充电。

[esp-dev-kits 用户指南](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s31/esp-mosaico/user_guide.html)的标题和开头明确限定 **CoreBoard V1.0**。它将左槽 H2.17 列为 `5V_IN`，并写 `VIN` 可给板载电池充电；[固定提交源码](https://github.com/espressif/esp-dev-kits/blob/3c0f6321d2be0398766dcf5c019990772e0f8e54/docs/en/esp-mosaico/user_guide.rst)便于复核。对应[CoreBoard V1.0 原厂原理图](https://dl.espressif.com/AE/SCH_SCH_ESP-Mosaico_CoreBoard_V1_0_2026-08-18.pdf)可追到 `5V_IN → D10 → VCHG/VBUS_IN → TP4057` 和经 D15 到系统电源的旧版路径（p3、p5；本仓库既有逐页摘录见 `review/chrome/T04/COREBOARD_INTERFACE_EVIDENCE.md`）。**这些只证明 V1.0**；V1.2 BaseBoard 接线、CoreBoard 器件与两路 USB/输入的合并方式均不得由它们继承。

本仓库的[官方归档说明](../../../references/official-v12/README.md)及 `references/official-v12/expansion_v121_zh.pdf`（SHA-256 `262b52d2b6939020dcb80e549f3d45b1cea8ddd2fc1bd250c85cb1475212aedc`）又有另一版次边界：PDF p2 写**仅适用于 1.2.1 及以上**。p3–4 说明背板/电池拆装和内侧扩展焊盘，但没有 H2.17→BaseBoard→CoreBoard 的逐网图、导体规格或输入限流/反灌保护。视频丝印 V1.2 与文档 1.2.1+ 的对应关系仍 unknown，不能仅凭相似外观宣告适用。

## 当前不能关闭的项目

| 问题 | 当前状态 | 取得关闭证据的方法 |
| --- | --- | --- |
| 目标 V1.2 的左槽 H2.17 是否接到产品页 `IN`、经何器件到系统与充电器 | `unknown`；V1.0 是旧版参照，不是 V1.2 电路证据 | 取得 BaseBoard-A V1.2 与 CoreBoard V1.2 原理图/BOM/布局或原厂逐网确认；再按到货板号复测通断 |
| 从 H2.17 输入时能否给内置 65 mAh 电池充电 | `unknown`；“可充电”明确出现在限定 V1.0 的旧指南，现行产品页只说供电 | 原厂 V1.2 说明或受限流、可观测的实物状态测试；不能用 V1.0 D10/D15 当证明 |
| H2.17 允许电压公差、连续/峰值电流、浪涌、接点及回流额定 | `unknown`；产品页未给输入值，100 mA 仅限输出 | 原厂额定及所用母座/公头图纸；若没有，只能定义保守**测试上限**，实测可工作不等于厂商额定 |
| 原生 USB 与 H2.17 同时接电时的反向电流/合路/故障行为 | `unknown`；V1.0 原理图不能外推 | V1.2 电气图或隔离测量，分别覆盖 USB 先接、模块先接、掉电、热插拔；记录限流、温升与反灌 |
| BaseBoard-A V1.2／CoreBoard V1.2 与扩展指南“1.2.1+”的修订对应 | `unknown` | 原厂版次对照、到货实拍丝印及包装批次 |

公开检索边界：2026-09-23 检查乐鑫[产品页及硬件链接](https://mosaico.espressif.com/zh/guide/hardware-docs/)、[esp-dev-kits 固定提交树](https://github.com/espressif/esp-dev-kits/tree/3c0f6321d2be0398766dcf5c019990772e0f8e54/docs/en/esp-mosaico)与[BSP 固定提交树](https://github.com/esp-mosaico/esp-mosaico-bsp/tree/6edd088e569967cb785426b6dfcd4604c7d744bd)；未在这些**指定版本/路径**找到 V1.2 BaseBoard/CoreBoard 原理图。此检索不能证明其他渠道从未公开。MakerWorld 模型页本次直读为 403，归档 PDF 的来历与哈希依仓库 `references/official-v12/README.md`；不据此断言附件清单从未变化。

设计交接：保留“底座升压后受保护 5 V → 左槽输入”作为**待验证拓扑**，pin18 `5V_OUT` 仍不可接底座供电。`review/chrome/D1-module-interface/LEFT_SLOT.md` 的 H2.17 用途栏目前直接写“供电并充电”，对目标 V1.2 的“充电”证据等级应降为 `unknown`；该合同正被另一待审分支固定哈希引用，本次仅提出修订，不在此并行分支改写以免制造隐形基线漂移。没有版本匹配的电气/实物证据前，不冻结输入额定或宣称 G3 电源通过。
