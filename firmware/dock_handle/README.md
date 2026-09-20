提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造

# dock_handle —— 方案 D＋G 底座手柄的主机侧驱动（ESP-IDF 组件）

## 1. 范围与前提

- 产品前提（已定）：完整、不拆解的 ESP-Mosaico（BaseBoard V1.2）横置于长条手柄中，左模块槽 H2 插模块板（纯转接件），底座主板上的 10 个轻触开关经弹簧针进入模块板，再经 H2 直连主机 GPIO。模块板只有 AT24C02 与触点，**无 MCU、无 I²C 扩展器**，所以主机固件直接读 GPIO。
- 固件基线：`esp-mosaico/esp-mosaico-bsp` commit `392860b1d1a123c3377947074b2af1f600e86c5d`，与 D1 接口合同同源；ESP-IDF ≥ 6.2，`idf.py --preview set-target esp32s31`。
- 本组件只覆盖主机侧按键输入与热插拔。底座电源路径、EEPROM 内容、模块板与外壳分属其他子系统任务；本组件不触碰 pin17/pin18 供电、不控制 GPIO60。
- 本目录是项目主循环第 ① 步的产出：按现有信息把固件写完，所有不确定处标 `ASSUMPTION:` 并给出到货后验证方法（§9）。**未在 ESP-IDF 环境中构建**（本机无 IDF），只做了宿主机 clang 语法检查（用桩头模拟 IDF / BSP 接口，见 §5.5）。

## 2. 目录

```text
firmware/dock_handle/
├── CMakeLists.txt                 组件构建：REQUIRES mosaico_module_mgr esp-mosaico-bsp esp_driver_gpio
├── idf_component.yml              依赖固定到 BSP commit 392860b1（git 源 + 子路径）
├── Kconfig                        轮询周期、去抖次数、队列深度、身份核对等
├── include/dock_handle.h          公共 API
├── include/dock_handle_pinmap.h   KEY_* -> GPIO 宏表（默认值，PINMAP.md 为准）
├── dock_handle.c                  实现
├── examples/keytest/              认领 + 打印按键事件的最小工程
│   ├── CMakeLists.txt  sdkconfig.defaults
│   └── main/  main.c  CMakeLists.txt  idf_component.yml  Kconfig.projbuild
├── README.md                      本文件
└── PC_LINK.md                     与电脑连接的软件通路建议（不做实现）
```

## 3. 设计要点

| 项 | 做法 | 依据 |
| --- | --- | --- |
| 认领 | `mosaico_module_mgr_claim()`，`expected_type = MOSAICO_BOARD_TYPE_HANDLE(0x04)`，`slot = LEFT`，`flags = 0`。等待由订阅回调的任务通知驱动，claim 本身用 `timeout_ms = 0` 单次尝试；`dock_handle_init()` 阻塞至多 `claim_timeout_ms`（默认 3000 ms） | `mosaico_module_mgr.h`（claim / subscribe 语义）；`handheld_dock_skeleton.c`（HANDLE、flags 0、3000 ms） |
| 身份核对（可选） | 认领前用 `mosaico_module_mgr_get_info()` 核对 `eeprom.vendor_id / board_id`；不符则不认领，并按快照代只告警一次 | `BSP_AND_EEPROM.md` §4：管理器 claim 只比较 board_type；官方 joystick 模块同为 HANDLE |
| GPIO | `bsp_subboard_map_gpio(slot, 左槽规范 GPIO)`；`gpio_reset_pin` 后配置 `GPIO_MODE_INPUT + GPIO_PULLUP_ENABLE`，按下读 0 | 硬约束 5：无源开关接地，拉高由主机内部上拉提供，3.3 V 域 |
| 轮询与去抖 | 独立任务 `xTaskDelayUntil` 定周期采样（默认 20 ms，允许 20–40 ms）；每键计数器，连续 N 次（默认 3）与稳定态相反才切换 | 硬约束 7：BSP 无中断通路，20–40 ms 轮询＋去抖（`LEFT_SLOT.md`） |
| 事件与状态 | FreeRTOS 队列投递 `dock_handle_event_t {type, key, pressed, timestamp_us}`；`dock_handle_get_state()` 返回位图（bit n = `dock_handle_key_t` n） | 任务要求 |
| 热插拔 | 订阅管理器事件；本槽 `PRESENCE` 变 `ABSENT` 时：补发所有按下键的释放事件 → `gpio_reset_pin` → `mosaico_module_mgr_release()` → 投递 `DETACHED`；`auto_reattach` 时继续等待并自动重认领 | `BSP_AND_EEPROM.md` §5：拔出时管理器不自动释放 lease，客户端须自行停止外设并 release |
| 只支持左槽 | `slot = RIGHT` 返回 `ESP_ERR_NOT_SUPPORTED`；`AUTO` 视为 `LEFT` | 右槽镜像把 16/15/17/18/19/55 映射到 40/38/37/54/52/49，与板载 I²S {54,37,49,52,40} 冲突（`subboard.c:52-67`，`esp_mosaico.h:108-114`） |
| 编译期检查 | `_Static_assert`：10 个 KEY_* GPIO 互不重复；不含 GPIO14（EEPROM A0）、GPIO0/1（I²C1）、GPIO33/34（USJ）、I²S 五脚；备用脚不作按键 | 硬约束 6、`LEFT_SLOT.md` |

所引 BSP / 管理器函数均已在 392860b1 源码中找到真实名称与签名：`mosaico_module_mgr_init / claim / release / get_info / subscribe / unsubscribe / slot_to_name / type_to_name`、`bsp_subboard_map_gpio`、`bsp_board_variant_get`、`bsp_power_init`、`bsp_display_start / lock / unlock`。未使用任何未核实的函数。

## 4. KEY_* → GPIO（默认宏表）

权威来源是 `hardware/module-board/PINMAP.md`（模块板任务产出）。**ASSUMPTION: 撰写时 PINMAP.md 尚未入库，下表为按 H2 针序拟定的默认值。** 到货后验证：模块板单板逐一把某触点短接到 GND，`keytest` 打印的键名必须与 PINMAP.md 及底座丝印一致。

| KEY_* | H2 针 | GPIO（默认） | 宏 |
| --- | --- | --- | --- |
| KEY_UP | 1 | 55 | `DOCK_HANDLE_GPIO_KEY_UP` |
| KEY_DOWN | 2 | 53 | `DOCK_HANDLE_GPIO_KEY_DOWN` |
| KEY_LEFT | 3 | 19 | `DOCK_HANDLE_GPIO_KEY_LEFT` |
| KEY_RIGHT | 4 | 48 | `DOCK_HANDLE_GPIO_KEY_RIGHT` |
| KEY_A | 5 | 18 | `DOCK_HANDLE_GPIO_KEY_A` |
| KEY_B | 6 | 13 | `DOCK_HANDLE_GPIO_KEY_B` |
| KEY_X | 7 | 17 | `DOCK_HANDLE_GPIO_KEY_X` |
| KEY_Y | 8 | 12 | `DOCK_HANDLE_GPIO_KEY_Y` |
| KEY_L | 9 | 16 | `DOCK_HANDLE_GPIO_KEY_L` |
| KEY_R | 11 | 15 | `DOCK_HANDLE_GPIO_KEY_R` |
| （备用） | 12 | 4 | `DOCK_HANDLE_GPIO_SPARE`，本版不配置 |

H2 针号 ↔ GPIO 取自 `review/chrome/D1-module-interface/LEFT_SLOT.md`。改表方式：改 `include/dock_handle_pinmap.h` 默认值，或在工程里 `target_compile_definitions(... -DDOCK_HANDLE_GPIO_KEY_A=GPIO_NUM_xx)`；`_Static_assert` 会拦住重复与禁用引脚。

## 5. 构建

### 5.1 取得 BSP

```bash
git clone https://github.com/esp-mosaico/esp-mosaico-bsp.git
git -C esp-mosaico-bsp checkout 392860b1d1a123c3377947074b2af1f600e86c5d
```

### 5.2 方式 A：组件管理器 git 依赖（`idf_component.yml` 已写死 commit）

直接在 `examples/keytest` 下构建，组件管理器按 `idf_component.yml` 拉取 `mosaico_module_mgr` 与 `esp-mosaico-bsp` 两个子目录组件。
**ASSUMPTION: 组件管理器对「git 源 + `path` 子目录」的解析，以及 `mosaico_module_mgr/idf_component.yml` 内 `override_path: ../esp-mosaico-bsp` 在该模式下能否解析，均未验证。** 验证方法：首次 `idf.py reconfigure` 是否成功；失败改用方式 B。

### 5.3 方式 B：本地 BSP 副本

```bash
export MOSAICO_BSP_COMPONENTS=/path/to/esp-mosaico-bsp/components
```

`examples/keytest/CMakeLists.txt` 检测到该变量后把 `esp-mosaico-bsp` 与 `mosaico_module_mgr` 加入 `EXTRA_COMPONENT_DIRS`。此时需注释掉 `firmware/dock_handle/idf_component.yml` 中的两个 git 依赖，避免同名组件二义（组件管理器对本地与托管同名组件的处理未验证）。

### 5.4 命令

```bash
cd firmware/dock_handle/examples/keytest
idf.py --preview set-target esp32s31
idf.py menuconfig        # 可调 Dock Handle / Dock Handle keytest 菜单
idf.py build
idf.py -p PORT flash monitor
```

控制台走 UART0（`sdkconfig.defaults`）。左槽 H2 pin13/15 是 USB Serial/JTAG（GPIO33/34），插上手柄模块板后被连接器占用（模块板不接这两针），USJ 控制台不可达。UART0 在官方 V1.0 指南中位于右槽 H1（TX0 GPIO58 / RX0 GPIO59；**ASSUMPTION: V1.2 相同，待核**），需要 USB-UART 转接板。原生 USB-C 的 CDC 控制台见 `PC_LINK.md`，需要 BSP 之外的组件，本示例不启用。

### 5.5 本机已做的检查

- `clang -fsyntax-only -Wall -Wextra -Wformat` 对 `dock_handle.c` 与 `examples/keytest/main/main.c`（显示开 / 关两种配置），使用桩头模拟 ESP-IDF 与 BSP 接口、并用 392860b1 的真实 `mosaico_module_mgr.h`、`bsp/subboard.h`、`bsp/esp_mosaico.h` 检查类型与签名。这只证明源码与所引接口一致，不证明能在 ESP-IDF 6.2 / esp32s31 上编译通过或运行正确。

## 6. 在应用中使用

```c
#include "dock_handle.h"

ESP_ERROR_CHECK(bsp_power_init());
esp_err_t ret = dock_handle_init(MOSAICO_MODULE_MGR_SLOT_LEFT);   // 内部会 mosaico_module_mgr_init(NULL)
if (ret == ESP_ERR_TIMEOUT) { /* 未插底座；auto_reattach 时后台继续等 */ }

dock_handle_event_t ev;
while (dock_handle_wait_event(&ev, UINT32_MAX) == ESP_OK) {
    if (ev.type == DOCK_HANDLE_EVENT_KEY) {
        printf("%s %s\n", dock_handle_key_name(ev.key), ev.pressed ? "down" : "up");
    }
}
uint32_t held = dock_handle_get_state();     // bit DOCK_HANDLE_KEY_A 等
```

事件语义：`DOCK_HANDLE_EVENT_ATTACHED` 表示已认领并配置好 GPIO；`DETACHED` 表示 lease 已释放，且之前按下的键已先收到释放事件；应用层不需要自己清按键状态。长按、重复、组合键语义不在本组件内，交给应用层（T13 交互设计）。

## 7. 与 `module_slot_scan` 配合

- `module_slot_scan` 是 BSP 官方双槽热插拔示例（`examples/module_slot_scan`）：相机、交互板有专用面板，其他已识别的板只显示类型名。手柄模块板 EEPROM 的 `board_type = 0x04` 会显示为 `Handle`（`mosaico_module_mgr.c:300-301`）。
- 建议顺序：先烧 `module_slot_scan`，只验证 EEPROM 链路（左槽 `PRESENT` + 描述 `VALID` + `Handle`，地址 0x50）；通过后再烧 `keytest` 验证按键。两者是独立固件，不同时运行。
- `keytest` 内置了与 `module_slot_scan` 同源的两槽扫描日志（`log_slot_info()`），没有面板；只看串口也能确认识别结果。
- 两个示例都把控制台放在 UART（`module_slot_scan` 因相机 D2 与 GPIO33 冲突，本例因模块板占用 H2 pin13/15）。

## 8. 到货后验证顺序

| 步 | 操作 | 预期 | 关闭的假设 |
| --- | --- | --- | --- |
| 1 | 烧 `keytest`，看启动日志 | `board variant: V1.2`。若 `bsp_board_variant_get failed`，eFuse USER_DATA 未编程或不支持，停止并记录 | A-01 |
| 2 | 两槽都空 | 两槽 `ABSENT`，`last_error = ESP_OK`；否则 I²C1 或上拉有问题 | — |
| 3 | 模块板单板（不接底座，EEPROM 已按 V1 格式烧 `board_type 0x04`）插左槽 | `slot left addr=0x50 PRESENT descriptor=VALID type=Handle`；`dock_handle` 打 `attached` 与 10 行 `KEY_* -> GPIOnn` | A-02（EEPROM A0 接 GPIO14、由 pin19 取电）、A-07 |
| 4 | 单板上逐个把 KEY_* 触点短接到 GND | 打印键名与 PINMAP.md、底座丝印一致；`state` 位图只置对应位 | A-03 |
| 5 | 示波器看一只轻触开关的抖动时长 | 抖动 < (去抖次数−1)×轮询周期 = 40 ms；否则加大 `CONFIG_DOCK_HANDLE_DEBOUNCE_COUNT` | A-04 |
| 6 | 接上底座（先不装电池、不接底座 USB），全部 10 键各按一次，再做组合（D-pad 双键、A+B、L+R、四键同按） | 每键独立 GPIO，无鬼键、无漏键；组合时位图正确 | — |
| 7 | 运行中拔模块板；按住某键拔 | 约 1 s 内 `detached`（管理器 250 ms 扫描 × 3 次去抖）；按住的键先收到 `UP` 再收到 `DETACHED`；插回后 `attached` | A-05 |
| 8 | 主机 GPIO 高电平电压、上升沿（单板与整机各测一次） | 内部上拉能把整条按键网络（弹簧针 + 走线 + 开关）拉到可靠高电平；否则提请硬件任务加外部上拉 | A-06 |
| 9 | 按住任一键上电 / 复位 | 正常启动，无进入下载模式或启动失败 | A-08 |
| 10 | 24 h 心跳日志 | `dropped=0`，无 `last_error`，无自发 `detached` | — |
| 11 | 若有官方 joystick 模块：开 `CONFIG_DOCK_HANDLE_CHECK_IDENTITY`，插 joystick | 打一次 `not claiming` 告警，不认领 | A-07 |

底座供电（pin17）相关验证属于底座主板任务；本固件不参与供电时序，只需在步骤 6–10 观察无 I²C 错误与无异常复位。

## 9. 假设清单

| 编号 | ASSUMPTION | 到货后验证 |
| --- | --- | --- |
| A-01 | 到货 BaseBoard 为 V1.2 且 eFuse USER_DATA 已编程，BSP 能识别 | §8 步 1 |
| A-02 | 模块板 EEPROM A0 接 H2 pin10（GPIO14），从 pin19 VCC_3V3 取电，地址落在 0x50 | §8 步 3 |
| A-03 | §4 的 KEY_* → GPIO 默认表；PINMAP.md 入库后以其为准 | §8 步 4 |
| A-04 | 轻触开关抖动 ≤ 40 ms，20 ms × 3 次去抖足够 | §8 步 5 |
| A-05 | 管理器默认配置（250 ms 扫描、3 次去抖）下拔出检测约 0.75–1 s，可接受 | §8 步 7 |
| A-06 | ESP32-S31 GPIO 内部上拉足以拉高整条按键网络，无需外部上拉（S31 内部上拉阻值未查数据手册） | §8 步 8；不足则提请硬件任务在模块板/底座板加外部上拉位 |
| A-07 | EEPROM `vendor_id = 0xFFFF`、`board_id = 0x0001` 为占位值（沿用 skeleton 配套脚本），最终值由 EEPROM 任务定义 | EEPROM 任务入库后同步 Kconfig 默认值；§8 步 11 |
| A-08 | 所选 10 个 GPIO 在 ESP32-S31 上无 strapping / 启动电平要求（未打开 S31 数据手册） | §8 步 9；查 ESP32-S31 数据手册 strapping 表 |
| A-09 | 组件管理器能解析 `idf_component.yml` 的 git 子路径依赖 | 首次 `idf.py reconfigure` |
| A-10 | UART0 TX0/RX0 = GPIO58/59 在右槽 H1（来自 V1.0 指南），V1.2 相同 | 到货用官方 V1.2 资料或实测核对 |

## 10. 已知限制

- HANDLE 类型与官方 joystick 模块共用 `0x04`；默认不核对 vendor/board id，插入 joystick 也会被当作手柄认领（GPIO 48/53 是它的摇杆模拟轴，读到的只是无意义的电平）。EEPROM 身份定下后开启 `CONFIG_DOCK_HANDLE_CHECK_IDENTITY`。
- 无中断：按键识别最坏延迟 ≈ 去抖次数 × 轮询周期（默认 60 ms）。每 20 ms 读 10 个 GPIO，CPU 开销可忽略。
- 拔出检测依赖管理器对 EEPROM 的探测，不是按键线本身；拔出瞬间按键线被内部上拉拉高，表现为释放，不会误报按下。
- 只支持左槽；只支持一套手柄（单例）。
- 不提供长按、自动重复、组合键语义；不提供 LED / 马达反馈（本设计底座无 LED）。
- 插上模块板后 USB Serial/JTAG 控制台不可用，见 §5.4 与 `PC_LINK.md`。
- EEPROM 烧写不在 BSP 公开流程内（BSP README「Hardware Notes」）；需外部编程器或一次性烧写固件，不属于本组件。镜像格式见 `review/chrome/D1-module-interface/BSP_AND_EEPROM.md` §3。
- `dock_handle_deinit()` 最多等待轮询任务 2 s。
- 未在 ESP-IDF 中构建、未上机；`idf_component.yml` 的依赖解析方式未验证（A-09）。

## 11. 依据索引

- `review/chrome/D1-module-interface/LEFT_SLOT.md`：H2 针号 ↔ GPIO、可用 GPIO 集、I²S 无交集、无中断通路、pin17 供电不得等待主机。
- `review/chrome/D1-module-interface/BSP_AND_EEPROM.md`：管理器 claim / release / 拔出行为、EEPROM 镜像格式、驱动接入例证。
- `review/chrome/D1-module-interface/evidence/bsp/`（commit 392860b1 快照）：`mosaico_module_mgr.h/.c`、`bsp/subboard.h`、`subboard.c`、`bsp/esp_mosaico.h`、`mosaico_module_interact.c`。
- 官方 V1.0 用户指南（`review/chrome/D1-module-interface/evidence/user_guide_v10.rst`）：扩展排针表、USB / USJ / UART 描述。
- `docs/DECISIONS.md` D-017：迭代式打板主循环。
