# C24-04：无转接板时能否不装 EEPROM（BSP 固定快照判定）

**判定：可以由专用应用固件直接读左 H2 的十根 GPIO，不需要 EEPROM 作为电气前提；但仓库现有 `dock_handle` 驱动不能原样工作。** 这是基于公开 BSP 固定提交 `392860b1d1a123c3377947074b2af1f600e86c5d` 的代码级结论，未在用户实物/出厂固件上运行。v1 无板方案应从硬件 BOM 删除 AT24C02 及 H2 pin10/14/16/19 的底座接触；`hardware/eeprom/` 保留为旧有板设计记录或未来 v2，不作为新方案已实现功能。

## 代码证据与边界

- [已归档 `subboard.c`](../D1-module-interface/evidence/bsp/components/esp-mosaico-bsp/onboard/subboard.c) L24–67 列出左槽 12 根 GPIO，L212–224 对左槽映射原样返回。十键现有分配为 H2 pin1/2/3/4/5/6/7/8/9/11，即 GPIO55/53/19/48/18/13/17/12/16/15，另留 pin12 GPIO4。GPIO14/pin10 在标准模块流程中被当 EEPROM 地址选择脚；即使不装 EEPROM，也先保留，不额外占用。十键无源开关可由应用对这些 GPIO 配输入+内部 3.3 V 上拉、轮询/消抖；无板时按键仍通过底座弹簧针与 pin20 GND 构成回路。输入电气/上拉强度/上电默认态须实测，不能从源码推出抗干扰通过。
- [已归档 `mosaico_module_mgr.c`](../D1-module-interface/evidence/bsp/components/mosaico_module_mgr/mosaico_module_mgr.c) L481–483、513–536：管理器用 I²C probe 地址 0x50 判存在；无 EEPROM 则稳定状态为 `ABSENT`，不会读有效描述。L994–1004 正常 `claim` 要求 `PRESENT`；`ALLOW_INVALID_DESCRIPTOR` 仅绕过**已存在但无效**的描述，不允许 claim 空槽。因此不能靠改 `board_type` 或改配置骗过无板硬件。
- 现有 [`dock_handle.c`](../../../firmware/dock_handle/dock_handle.c) L407–466 先 `get_info`、检查 `PRESENT+VALID+HANDLE` 身份，再 `claim`，之后才调用 `configure_key_gpios`；其 L382–400 的确已定义输入+内部上拉，但在无 EEPROM 情况下根本到不了这一步。直接把 EEPROM 器件从 BOM 删除，现有驱动只会保持未连接状态，十键不会上报。

## v1 固件要求（待实施和独立复核）

1. 增加明确的 **固定左槽无 EEPROM 模式**（独立驱动或对现有驱动的显式编译/运行选项），静态配置上述十 GPIO 为输入上拉并按现有键序消抖；绕开模块管理器的 presence/descriptor/claim 入口，不能让普通可插模块模式同时占用同一 GPIO。
2. 固定模式不得把“十键均未按下”解释为“底座已拔出”：两种状态在无身份触点时电气相同。分离/重连及同时插其他模块的策略要由产品固件明确（例如固定手柄模式只在用户启用时占用左槽，退出时复位 GPIO），不能继承旧 EEPROM 自动识别宣称。
3. 验证冷启动、GPIO 默认电平、主机掉电时底座仍有电、按住键拔出、部分接触、机械抖动、音频/USB 同时运行。无板键线仅无源，不向掉电主机主动送 3.3/5 V；pin17 供电仍须**纯硬件启动**，不等待 MCU 扫描或 GPIO60。
4. 若用户要求保留“任意官方模块热插识别并在插底座时自动切换”，无 EEPROM 加现有管理器不足以实现；需要另有可靠识别通路或恢复一块带 EEPROM 的板，此项由主控定产品行为。

本结论只证明**软件可改造**，不证明出厂系统支持、物理 pin1 朝向、GPIO strapping/上拉足够、触点安全或机械放行。
