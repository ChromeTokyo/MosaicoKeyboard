提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造

# PC_LINK —— 手持终端与电脑的软件通路（第一版建议，不做实现）

本文件是 `firmware/dock_handle` 的配套建议书，不含代码；引用的 BSP / esp-mosaico-claw 符号已按 §3 的方式 grep 核实，未核实的配置项名一律标「待核」。

## 1. 结论

第一版通道：**Mosaico 原生 USB-C（ESP32-S31 USB 2.0 High-Speed OTG）上的 USB CDC-ACM 虚拟串口**，在 TinyUSB 上开两个 CDC 接口，接口 0 保留日志 / 下载，接口 1 承载手柄协议（§5）。理由：

1. 插上手柄模块板后，USB Serial/JTAG（GPIO33/34）所在的左槽 H2 pin13/15 被连接器占用且模块板不接这两针，USJ 通路物理上不可达。
2. 原生 USB-C 是官方文档明确的「供电、调试、通信」端口，出厂固件已集成 CDC 虚拟串口，用户对这个口已有使用预期。
3. 右槽 UART0 需要 USB-UART 转接板，不适合作为产品通路。

底座自带的 USB-C 在方案 D 中只做充电（`VBUS_IN`），不承载数据；见 §2 的选项说明。

## 2. 物理通路事实

| 通路 | 位置 | 插上手柄后 | 依据 |
| --- | --- | --- | --- |
| 原生 USB-C | 主机机身，ESP32-S31 USB 2.0 HS OTG，供电＋调试／下载＋应用通信；芯片原生只支持下载模式，无自带日志；出厂固件集成 CDC 虚拟串口并支持自动下载 | 可用 | 官方 V1.0 用户指南 `user_guide_v10.rst:249`、`:332` |
| USB Serial/JTAG | GPIO33（D−）/ GPIO34（D+）= 左槽 H2 pin13 / pin15 | **不可用**（被模块板连接器占用，模块板留空） | `LEFT_SLOT.md` pin13/15；用户指南 `:249`「left slot provides USB Serial/JTAG」 |
| UART0 | TX0 GPIO58 / RX0 GPIO59 = 右槽 H1 | 可用但需转接板；右槽若被其他模块占用则不可用。**ASSUMPTION: AS-31-firmware-11** V1.2 与 V1.0 指南一致，待核 | 用户指南右槽表 |
| Wi-Fi / BLE | 片上 | 可用 | 后续阶段，不在第一版 |
| 底座 USB-C | 底座主板，`VBUS_IN` → 电池管理 → `BOOST_5V` → pin17 | 无数据路径 | 方案 D＋G 前提；pin17 只有电源 |

关于底座 USB-C 承载数据的选项：把 H2 pin13/15（USJ）经模块板与弹簧针引到底座 USB-C 的 D+/D−，可让「一根线充电＋调试」。这与 D1 合同「pin13/15 保留」相抵触，且弹簧针接口要多 2 针并处理 USB 阻抗；**本版不采用**，仅记录为后续讨论项，需硬件任务评估。

## 3. `CONFIG_BSP_USB_CONSOLE` 的核实结果

任务文本与官方 V1.0 用户指南（`user_guide_v10.rst:284`）提到 `CONFIG_BSP_USB_CONSOLE`、`CONFIG_BSP_USB_CONSOLE_AUTO_INIT`、`CONFIG_BSP_USB_AUTO_DOWNLOAD`。核实结果：

| 位置 | 结果 |
| --- | --- |
| `esp-mosaico-bsp` @ 392860b1 全部源码 grep | **无**上述任何符号。BSP `Kconfig` 只有 `BSP_DISPLAY_ENABLE`、`BSP_CO5300_ENABLE_TE`、`BSP_LCD_QSPI_DRIVE_CAP`、`BSP_MOTOR_ENABLE_PWM`、`BSP_VCC_3V3_RAMP_MS` 五项；`bsp_README.md` 提到 USB OTG 能力但无 console 组件 |
| `esp-mosaico-claw` @ 903fe11e `boards/esp_mosaico/components/usb_hs_console/` | 有实现：`esp_err_t bsp_usb_console_init(void)`、`bool bsp_usb_console_is_initialized(void)`；Kconfig 符号为 `USB_HS_CONSOLE_USB_CDC_AUTO_DOWNLOAD`、`USB_HS_CONSOLE_USB_CDC_AUTO_INIT`；依赖 `espressif/esp_tinyusb`；用 `-Wl,--wrap=app_main` 在 `app_main` 前初始化；模拟 USB Serial/JTAG 的 VID/PID（`TINYUSB_ESPRESSIF_VID` / PID `0x1001`）与 DTR/RTS 复位序列，让 `idf.py` 能自动进入下载模式 |

结论：指南里的配置名与目前公开代码不一致，很可能对应尚未公开或更新的 BSP 版本。第一版规划按 `esp-mosaico-claw` 组件的真实名字与结构做，可直接复制该组件（Apache-2.0）到本仓库固件工程，或等 Espressif BSP 内置后切换。不得在文档或代码里假定 `CONFIG_BSP_USB_CONSOLE` 已存在。

## 4. 通道方案对比

| 方案 | 优点 | 缺点 | 建议 |
| --- | --- | --- | --- |
| A. 复用 CDC 控制台接口 0，日志与协议混流 | 零额外配置；`idf.py monitor` 直接看 | 日志会污染协议流，宿主端要过滤；下载复位会打断会话 | 仅调试期 |
| B. **第二个 CDC-ACM 接口（接口 1）专用协议** | 日志／下载与协议隔离；宿主端只是一个串口；跨平台免驱 | 需 TinyUSB 配置 2 个 CDC（`esp_tinyusb` 的 CDC 数量配置项名待核）；描述符稍大 | **第一版** |
| C. USB HID Gamepad | 电脑零驱动识别为游戏手柄，任何支持手柄的软件直接可用 | 单向、无文本通道；Vibe Coding 终端需要双向文本 | 第二阶段与 B 组成复合设备 |
| D. Vendor bulk / WebUSB | 浏览器直连 | 需 WinUSB 描述符、权限流程复杂 | 后续 |
| E. Wi-Fi WebSocket | 无线；可远离电脑 | 配网、功耗、与电池预算耦合 | 后续 |

## 5. 协议建议（v0，文本行协议）

目标：人可读、能用普通串口终端观察、宿主端用 Python 几十行即可实现；后续如需低开销再升级二进制帧。

编码：ASCII；一行一条消息，`\n` 结尾；字段以单个空格分隔；首字段是消息类型；数值为十进制，位图为 `0x` 前缀十六进制；时间戳是 `esp_timer_get_time()/1000`（毫秒，自启动起），与 `dock_handle_event_t.timestamp_us` 同源。

设备 → 电脑：

| 消息 | 何时 | 示例 |
| --- | --- | --- |
| `HELLO <fw> <ver> proto <n> board <variant>` | 端口打开后、以及收到 `PING` 前的首次输出 | `HELLO dock_handle 0.1 proto 0 board V1.2` |
| `LINK <attached|waiting|stopped> <t_ms>` | `DOCK_HANDLE_EVENT_ATTACHED` / `DETACHED`、启动时 | `LINK attached 1234` |
| `KEY <KEY_name> <D|U> <t_ms>` | 每个 `DOCK_HANDLE_EVENT_KEY` | `KEY KEY_A D 123456` |
| `STATE <0xbitmap> <t_ms>` | 每个 KEY 事件之后，或响应 `GET STATE` | `STATE 0x011 123456`（bit0 UP、bit4 A） |
| `INFO <field> <value>` | 响应 `GET INFO`，逐行输出 EEPROM 描述字段 | `INFO board_type 0x04`、`INFO vendor_id 0xFFFF` |
| `PONG <nonce>` | 响应 `PING` | `PONG 42` |
| `ERR <code> <text>` | 无法解析或状态不允许 | `ERR 1 unknown command` |

电脑 → 设备：

| 消息 | 作用 |
| --- | --- |
| `PING <nonce>` | 探活；设备回 `PONG` |
| `GET STATE` | 立即回一条 `STATE` |
| `GET INFO` | 回 EEPROM 描述（来自 `mosaico_module_mgr_get_info()`） |
| `SET REPORT <keys|state|both|off>` | 选择是否推送 `KEY` / `STATE`；默认 `both` |

位图位序 = `dock_handle_key_t`（UP=0 … R=9）。键名与统一网络名一致（`KEY_UP` … `KEY_R`），电脑端不必知道 GPIO。

与本组件 API 的对应：`KEY` ← `DOCK_HANDLE_EVENT_KEY`；`LINK` ← `ATTACHED / DETACHED` 与 `dock_handle_get_link()`；`STATE` ← `dock_handle_get_state()`；`INFO` ← `mosaico_module_mgr_get_info()`；建议再加一行 `INFO keymap <static|eeprom>` ← `dock_handle_get_keymap_source()`。

二进制升级路径（v1，需要时再做）：COBS 分帧，帧内 1 字节类型 + 载荷 + CRC-16/MODBUS（初值 0xFFFF、多项式 0xA001 反射，与 EEPROM V1 描述符相同，可复用实现）。

## 6. 宿主端建议

- Python 3 + `pyserial`；macOS 设备名 `/dev/cu.usbmodem*`，Linux `/dev/ttyACM*`，Windows `COMx`。若采用方案 B，需按接口序号或 USB 接口描述字符串识别「协议口」而非「日志口」。
- 若沿用 `esp-mosaico-claw` 的 USJ VID/PID 模拟（`TINYUSB_ESPRESSIF_VID` / `0x1001`）与 DTR/RTS 复位，`idf.py` 的自动下载可用，但宿主应用打开端口时须避免产生 `RTS=1, DTR=0` 序列（该实现把它解释为复位）。**ASSUMPTION: AS-31-firmware-13** 常见串口库默认的 DTR/RTS 行为不会触发该序列，待实测；保险做法是协议口不挂复位回调，只在接口 0 上保留。
- 时间基准：设备时间戳自启动起；宿主端在 `HELLO` / 首个 `PONG` 时对齐一次即可。

## 7. 与供电共存的注意事项

- 电脑经原生 USB-C 连接时 VBUS 5 V 进入主机；底座同时经 pin17 供 5 V。两路 5 V 并存的防反灌是硬约束 8，由底座硬件负责，固件不参与也不能参与。
- 主机 Type-C 由 HUSB320 处理 CC 检测与供电方向（用户指南 `:113-114`）。**ASSUMPTION: AS-31-firmware-14** 主机口作 sink 接电脑、同时 pin17 有底座 5 V 时，HUSB320 与主机电源路径的行为未知，到货后先不装底座电池、只接电脑；再接底座供电观察 USB 枚举是否掉线。
- USB 数据链路与 pin17 无电气关系，供电路径不影响协议通道本身。

## 8. 第一版实现清单（后续任务输入，本目录不实现）

1. 引入 `espressif/esp_tinyusb`；配置 CDC 接口数为 2（配置项名以 `esp_tinyusb` 当前版本 Kconfig 为准，待核）。
2. 复制或依赖 `esp-mosaico-claw` 的 `usb_hs_console` 组件，接口 0 作日志 / 下载。
3. 新组件 `dock_link`：从 `dock_handle_wait_event()` 消费事件，编码为 §5 行协议写入接口 1；解析 `PING / GET / SET`。
4. 宿主端 `tools/dock_link.py`：打开端口、打印事件、`PING` 探活；作为日本端验收工具的一部分。
5. VID/PID：产品化前决定是继续模拟 USJ PID、使用 Espressif 分配的测试 PID，还是申请自有 PID；不得在文档中假定已获分配。

## 9. 假设清单（本分支临时编号，汇总阶段并入 `hardware/ASSUMPTIONS.md`；README §11 引用）

| 编号 | ASSUMPTION | 验证 |
| --- | --- | --- |
| AS-31-firmware-11 | 到货 V1.2 的 USJ 仍在左槽 pin13/15、UART0 仍在右槽 GPIO58/59 | 官方 V1.2 资料或实测 |
| AS-31-firmware-12 | `esp_tinyusb` 当前版本支持 2 个 CDC-ACM 接口且配置项存在 | 查该组件 Kconfig |
| AS-31-firmware-13 | 宿主串口库默认 DTR/RTS 行为不会触发 USJ 兼容复位序列 | 实测 macOS / Linux / Windows 三平台 |
| AS-31-firmware-14 | 电脑 USB 与底座 pin17 同时供电时 USB 枚举稳定 | 到货分步实测（§7） |
| AS-31-firmware-15 | Espressif 后续 BSP 会内置 USB console（指南已提前写出配置名） | 跟踪 BSP 仓库；出现后切换 |
