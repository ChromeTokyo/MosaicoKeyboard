# C4：EEPROM 与常驻转接件形态（2026-09-24）

**技术结论：专用应用固件可在没有 EEPROM 的左槽读取十键；现有 `dock_handle` 实现不可直接用于无 EEPROM 转接件。** 因此 (a) 裸直排针是一个可进一步验证的 v1 方向，(b) 穿透小板不是“为了 GPIO 读键”所必需。此结论仅是 BSP 软件路径核查，不解决 [C2](C2_SIDE_WIPE_CONTACT.md) 的擦触件、落座过程错接或 H2 插深，不能放行打样。用户保留 (a)/(b) 的形态决定。

## 固定源码核查

来源为项目已归档的 ESP-Mosaico BSP commit `392860b1`：[`subboard.c`](../D1-module-interface/evidence/bsp/components/esp-mosaico-bsp/onboard/subboard.c) L24–67 把左槽列为 12 根 GPIO；L101–120 仅把 GPIO14 设为标准模块 EEPROM A0 输出；L212–224 左槽映射原样返回。故**应用可直接**将其余十根 GPIO 设输入＋内部上拉，按键只短接地，不以 EEPROM 描述符为硬件前提。[现有静态键表](../../../firmware/dock_handle/include/dock_handle_pinmap.h)已分配 H2 pin1/3/5/7/9/11 给 UP/DOWN/LEFT/RIGHT/L/R，pin2/4/6/8 给 A/B/X/Y；H2 pin12 GPIO4 作备用。[现有输入配置](../../../firmware/dock_handle/dock_handle.c) L382–403 可作为轮询输入与去抖代码的起点。这里不声称原厂固件会自动识别手柄；须有专用应用安装或集成。

现有管理器 [`mosaico_module_mgr.c`](../D1-module-interface/evidence/bsp/components/mosaico_module_mgr/mosaico_module_mgr.c) L481–483 以 EEPROM 0x50 探测应答认定 `PRESENT`，L994–1004 的 claim 又要求 `PRESENT`。当前 `dock_handle.c` L407–467 只接受 `PRESENT`、`VALID`、`HANDLE` 身份并 claim，L706–748 在 init 时启动管理器、订阅事件、等待附着。因此仅关掉 identity 或 EEPROM keymap 开关仍会一直等待；不能把现有驱动标成“无 EEPROM 已支持”。

若选 (a)，固件须新增明确的**固定左槽静态模式**：初始化左槽供电所需 BSP，直接配置十根 GPIO，复用轮询/去抖和事件队列，同时绕开 manager 的 EEPROM 探测、claim、lease 和身份解析；`keytest` 与连接状态语义也要改。GPIO14 继续保持 BSP 标准地址输出，不占为第十一键。十键全松与 Mosaico 脱离手柄都可能读高，因此只靠这些十根线无法判在位；可由用户设定“手柄模式”或增加专用检测电路，不能把键松当作离座。

## (a) 与 (b) 的实际差别

| 路径 | 电气/软件事实 | 不能直接宣称的保护 |
| --- | --- | --- |
| (a) 裸直排针 | 20 根直通，底座选择 10 键＋电源/地触点；需要上述专用静态固件 | H2 针尾未加串阻、针尾端面无遮护；动态错位仍要另解。 |
| (b) 约 30×8 mm 穿透小板 | EEPROM 可以从 SDA/SCL/GPIO14/3V3/GND 等直通针**并联引出**，使现有 manager 有可能在装上转接件时认到模块；确切器件、焊盘、外形仍需重画 | 一根金属排针从头到尾不断开，焊在小板上的电阻不可能**串入这根针**。只有切断/改走分段导体与新触点路径才能给主机 GPIO 串阻，那已改变现行“直针尾端即触点”架构。即使 EEPROM 存在，管理器认的是**插在 H2 的常驻转接件**，不是 Mosaico 每天坐入/离开手柄。 |

若仅在手柄按键支路串电阻，它可限制某些该支路故障电流，但不能保护“5V 撞针误碰主机 GPIO 尾端”的主机侧最前端。若要求这个保护，需在 C3 的完整扫掠失配模型下另立隔离/上电时序方案。之前 `claude/design-d/module-board` 的 EEPROM/串阻网表基于旧板形，按[新分工](../../../docs/WORK-SPLIT-20260924.md)§6 作废，不移植为 (b) 网表。

**待验证：** 实机固件能否稳定读十键、按住键上电对启动的影响、内部上拉的抗噪/响应、离座过程 GPIO 瞬态；所有这些都未编译或上机测试。固件改造尚未领取，本报告不伪称已实现。
