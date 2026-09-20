# D1：左模块槽 BSP 实现核查（只读）

访问日期：2026-09-20。唯一源码基线：`esp-mosaico/esp-mosaico-bsp` commit `392860b1d1a123c3377947074b2af1f600e86c5d`；抓取时 master 仍为此 SHA。原始文件及 URL/SHA256 见 `SOURCE_INDEX.json`。以下是该版本公开实现，不等于用户实物/出厂固件已验证。未改工作仓库、未研究 H/UART。

## 1. 左槽 GPIO 与方向边界

`components/esp-mosaico-bsp/onboard/subboard.c:24–67` 的左槽 canonical GPIO 共 12 个：`53,48,13,12,14,4,16,15,17,18,19,55`。前六项明确注释为 H2/H4/H6/H8/H10/H12；后六项代码只给与右槽的镜像配对（40/38/37/54/52/49），没有在该表中写物理奇数针号，需合并官方连接器表/原理图。不要从此表猜俯视/背视方向。

| 源码明示触点名 | 左 GPIO | 右镜像 GPIO |
|---|---:|---:|
| H2 | 53 | 46 |
| H4 | 48 | 47 |
| H6 | 13 | 11 |
| H8 | 12 | 10 |
| H10 / EEPROM A0 | 14 | 39 |
| H12 | 4 | 5 |
| extended pair | 16 | 40 |
| extended pair | 15 | 38 |
| extended pair | 17 | 37 |
| extended pair | 18 | 54 |
| extended pair | 19 | 52 |
| extended pair | 55 | 49 |

左槽 `rotated_180=false`（L34），右槽为 true（L45）；`bsp_subboard_map_gpio()` L212–224 对左槽原样返回，对右槽按上述表转换。这是软件左右映射，不足以定义 PCB 看图方向。除 GPIO14 的发现态配置外，subboard 初始化没有给上述其余 11 根 GPIO 统一设输入/输出；功能方向由具体驱动决定。普通模块若保留标准 EEPROM A0 地址识别，不能同时把 GPIO14 当无条件空闲输入；“12 根 GPIO”不等于发现机制下 12 根都空闲。

## 2. 地址线和总线

`include/bsp/subboard.h:19–39` 明示标准模块使用 AT24C02，GPIO14/39 接 A0：左 GPIO14=0 → 7-bit 0x50；右 GPIO39=1 → 0x51。没有给出 EEPROM 厂家、封装/完整订货号、A1/A2/WP 的电气原理图，不自行补全。摄像头是例外：EEPROM 固定 0x50、无地址线；GPIO14 改作 camera D4，camera仅左槽（README L14）。

`subboard.c:101–120` 实际先 reset GPIO，再预设目标电平，配置推挽 GPIO_MODE_OUTPUT、禁内部上/下拉和中断。L123–151 初始化顺序是：使能共享子板 VCC rail → 初始化 I2C → 应用两槽地址电平。并非先读 EEPROM 才上电。

`include/bsp/esp_mosaico.h:62–75` 与 `subboard.c:73–98`：V1.0 主板与槽共享 I2C0（SDA0/SCL1）；V1.2 主板改 SDA56/SCL3，而左右槽仍 SDA0/SCL1，使用独立 I2C1、开启内部上拉。不能把 V1.0 的“与所有板载传感器同总线”套用到 V1.2。

## 3. EEPROM 读取与原始数据布局

`mosaico_module_mgr.h:23–25` magic = ASCII ESP，镜像总长 0x86=134 bytes。`mosaico_module_mgr.c:22–28,373–389,418–422` 使用 7-bit I2C、100kHz；发送单字节内部地址 0，再连续读 134 bytes，I2C timeout 100ms。管理器不提供烧写 EEPROM API。

下表均由 `mosaico_module_mgr.c:199–260` 解析器明确给出；多字节整数为 little-endian；C 结构体仅逻辑表示，不能直接 memcpy 当 EEPROM 镜像（头文件 L81–105）。

| 起始偏移 | 字节数 | 字段 |
|---|---:|---|
| 0x00 | 3 | magic ESP |
| 0x03 | 1 | board_type |
| 0x04 | 2 | board_id（vendor-defined） |
| 0x06 | 2 | hw_version |
| 0x08 | 2 | sw_version |
| 0x0A | 2 | vendor_id |
| 0x0C | 4 | board_flags |
| 0x10 | 4 | serial_number |
| 0x14 | 32 | board_name（不保证 NUL 结尾） |
| 0x34 | 2 | descriptor CRC |
| 0x36 | 4 | manufacture_date（vendor-defined） |
| 0x3A | 2 | batch_number |
| 0x3C | 2 | factory_id |
| 0x3E | 2 | manufacturing CRC |
| 0x40 | 2 | param_version |
| 0x42 | 2 | param_length ≤ 64 |
| 0x44 | 64 | param_data |
| 0x84 | 2 | parameter CRC |

CRC 算法 L209–218：初值 0xFFFF，逐字节异或，每位右移并在最低位为1时异或 0xA001，无末尾 XOR。三段各自验证：0x00–0x33 → 0x34；0x36–0x3D → 0x3E；0x40–0x83 → 0x84（L225–237）。参数 CRC 覆盖完整固定64字节参数区及头部，不仅 param_length 的有效字节。校验仅 magic、三个 CRC、param_length≤64；此解析器未限制 vendor_id/board_id/board_type 的有效编号。

## 4. 厂商/产品标识及“自动绑定”边界

头文件 L86–105 有 vendor_id 和 board_id 字段，但管理器没有厂商 ID 分配表、产品 ID 注册表或动态加载驱动 URL。`mosaico_module_mgr.c:994–1004` 正常 claim 只要求槽 FREE、PRESENT、描述 VALID 且 board_type 匹配，未比较 vendor_id/board_id；指定显式槽还可通过 ALLOW_INVALID_DESCRIPTOR 绕过无效描述限制（不等于可占空槽）。

头文件 L42–58 已枚举板类：CORE01、POWER02、DOCK03、HANDLE04、BALANCE_CAR05、DISPLAY06、CAMERA07、SENSOR08、IO_EXP09、TOF10、MATRIX_LED11、THERMAL12、RELAY13、INTERACT16（值均十六进制）。这些是源码预设类别，不能视为自动具备驱动的设备清单。新模块写入合法 EEPROM 能使管理器报告存在和描述有效；实现具体按键/游戏手柄功能仍需主机固件中有兼容驱动和应用接入，不能仅烧身份信息便自动工作。

## 5. 软件热插拔顺序与局限

- `mosaico_module_mgr.h:29–33` 默认 scan_period_ms=250、descriptor_retry_ms=2000、debounce_count=3。不是 300ms；应用可传自定义配置。
- `mosaico_module_mgr.c:813–836`：bsp_subboard_init → 注册两槽 EEPROM I2C 设备 → 启动事件和扫描任务。
- L458–600：probe 地址；ESP_OK 表示应答，ESP_ERR_NOT_FOUND表示未应答，其他总线错误记错误；连续3次相同 presence 才转换状态；确认 present 后读描述/校验；发出 presence/descriptor/error change 并唤醒 claim 等待方。VALID描述通常不反复读取，只有显式 rescan 或错误/无效时按重试周期读。
- L994–1047：具体驱动以 expected_type 主动 claim；管理器赋独占 lease，未自动创建功能驱动。复用控制脚且不声明 PROBE_WHILE_CLAIMED 时，presence/descriptor 改UNKNOWN并暂停扫描（L1024–1033、363–370）；固定地址 EEPROM 的特例可继续 probe。
- L513–531：拔出导致 ABSENT、descriptor UNKNOWN；保留之前 EEPROM 字段用于识别移除事件，但不再有效。管理器未在该分支自动销毁客户端驱动或释放 lease，客户端需要响应事件、停止外设并释放。
- L1135–1200：release → RESTORING → 必要时恢复 GPIO14/39 地址功能 → 成功FREE并立即请求重扫；恢复失败退回CLAIMED、原lease保留，可重试。客户端应先停止释放外设，再release（README claim示例）。

这证明软件轮询/去抖/状态通知机制，不能证明任意带电插拔的电气可靠性、触点先后接触顺序、浪涌/短路保护或 GPIO14 复用时任意新模块仍可被检测；这类实物/电路条件在此次软件源码中不确定。

## 6. 检索边界

已读 subboard.c、subboard.h、esp_mosaico.h、module_mgr .c/.h、README、组件依赖。mgr README 引用的 `docs/mosaico_module_mgr_workflow.md` 在固定commit树中不存在，直接raw URL于访问时404；未用该链接补猜 EEPROM 格式。驱动实际调用例证由并行子核查补充。
