提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造

# dock_handle —— 方案 D＋G 底座手柄的主机侧驱动（ESP-IDF 组件）

分支：`claude/design-d/firmware`。输入提交：`origin/main`（含 `hardware/ICD-0.2-DRAFT.md`、`hardware/ASSUMPTIONS.md`、`hardware/G6-TEST-PLAN.md`）、`origin/claude/design-d/module-board:hardware/module-board/PINMAP.md`（KEY_* → GPIO 唯一权威）、`origin/claude/design-d/eeprom:hardware/eeprom/IDENTITY.md`（EEPROM 身份与 param_data v1）。BSP 基线：`esp-mosaico/esp-mosaico-bsp` commit `392860b1d1a123c3377947074b2af1f600e86c5d`（本机克隆 `/tmp/mosaico-v12/esp-mosaico-bsp/`，与 `review/chrome/D1-module-interface/evidence/bsp/` 快照逐字节相同）。

## 1. 范围与前提

- 产品前提（已定）：完整、不拆解的 ESP-Mosaico（BaseBoard V1.2）横置于长条手柄中，左模块槽 H2 常驻插模块板（纯转接件），底座主板上的 10 个轻触开关经弹簧针进入模块板，再经 H2 直连主机 GPIO。模块板只有 AT24C02 与触点，**无 MCU、无 I²C 扩展器**，所以主机固件直接读 GPIO。
- 本组件只覆盖 ICD 第 8 节「固件接口要求」：十键驱动固定左槽、GPIO 来自 PINMAP.md、输入＋内部上拉、20–40 ms 轮询＋去抖、响应拔出并释放；最小测试固件 `keytest` 提供槽扫描/身份字段打印、十键自检、只读 I²C 地址扫描。**不写 EEPROM；除管理器自身对 GPIO14 的配置外不把任何槽位 GPIO 配成输出**（ICD 第 8 节最后一条）。
- 本组件不触碰 pin17/pin18 供电、不控制 GPIO60（硬约束 1、2 属底座与模块板任务）。
- 这是 D-017 主循环第 ① 步的产出：按现有信息把固件写完，不确定处标 `ASSUMPTION:` 并给到货后验证方法（§11）。**未在 ESP-IDF 中编译**（§7.5），只做了宿主机 clang 语法检查。

## 2. 目录

```text
firmware/dock_handle/
├── CMakeLists.txt                 组件构建：REQUIRES mosaico_module_mgr esp-mosaico-bsp esp_driver_gpio
├── idf_component.yml              依赖固定到 BSP commit 392860b1（git 源 + 子路径）
├── Kconfig                        轮询周期、去抖次数、队列深度、身份核对、EEPROM keymap 开关
├── include/dock_handle.h          公共 API
├── include/dock_handle_pinmap.h   KEY_* -> GPIO 宏表（PINMAP.md 镜像）
├── dock_handle.c                  实现
├── examples/keytest/              最小测试工程：扫描 + 认领 + 打印按键事件
│   ├── CMakeLists.txt  sdkconfig.defaults
│   └── main/  main.c  CMakeLists.txt  idf_component.yml  Kconfig.projbuild
├── README.md                      本文件
└── PC_LINK.md                     与电脑连接的软件通路建议（不做实现）
```

## 3. 设计要点

| 项 | 做法 | 依据 |
| --- | --- | --- |
| 认领 | `mosaico_module_mgr_claim()`，`expected_type = MOSAICO_BOARD_TYPE_HANDLE(0x04)`，`slot = LEFT`，`flags = 0`，`timeout_ms = 0` 单次尝试；等待由订阅回调的任务通知驱动；`dock_handle_init()` 阻塞至多 `claim_timeout_ms`（默认 3000 ms） | `mosaico_module_mgr.h:137-142, 281`；`handheld_dock_skeleton.c`（HANDLE、flags 0、3000 ms） |
| 身份核对 | 认领前用快照拒绝身份不符的 HANDLE 板（不抢官方 joystick 驱动的槽位、不碰其 GPIO）；**认领后立即 `get_info` 再核对** `vendor_id == 0x4354 && board_id == 0x0101 && (sw_version >> 8) == 0x01`，不符则 `release` | `IDENTITY.md` §2.4；`BSP_AND_EEPROM.md` §4（管理器只比较 board_type） |
| GPIO 表 | 默认 `dock_handle_pinmap.h`（PINMAP.md 镜像）。若 EEPROM `param_data` v1 `KEYMAP_VALID=1`：校验 10 个值都在左槽 11 根可用 GPIO 内且互异，通过才采用并打印与静态表的差异；任何失败回退静态表 | `IDENTITY.md` §8「主机侧使用规则」1–3 |
| GPIO 配置 | `bsp_subboard_map_gpio(LEFT, 左槽规范 GPIO)`；`gpio_reset_pin` 后 `GPIO_MODE_INPUT + GPIO_PULLUP_ENABLE + GPIO_INTR_DISABLE`，按下读 0。这是本驱动对 KEY_* 唯一允许的配置 | 硬约束 5；ICD EL-D-05 |
| 轮询与去抖 | 独立任务 `xTaskDelayUntil` 定周期采样（默认 20 ms，允许 20–40 ms）；每键计数器，连续 N 次（默认 3）与稳定态相反才切换 | 硬约束 7；ICD EL-D-07；`LEFT_SLOT.md`（无中断通路） |
| 事件与状态 | FreeRTOS 队列投递 `dock_handle_event_t {type, key, pressed, timestamp_us}`；`dock_handle_get_state()` 返回位图（bit n = `dock_handle_key_t` n）；`dock_handle_get_keymap_source()` 告知表来源 | 任务要求 |
| 热插拔 | 订阅管理器事件；本槽 `PRESENCE` 变 `ABSENT` 时：补发所有按下键的释放事件 → `gpio_reset_pin` → `mosaico_module_mgr_release()` → 投递 `DETACHED`；`auto_reattach` 时继续等待并自动重认领 | `mosaico_module_mgr.c:513-531`（拔出不改 owner，不自动 release）、`:1135-1200`（release 路径） |
| deinit 顺序 | `unsubscribe`（管理器会等待正在执行的回调返回）→ 停轮询任务 → 删任务 → 回收 | `mosaico_module_mgr.c` `dispatch_event`（:623-660，回调不持锁）与 `mosaico_module_mgr_unsubscribe()` 实现 |
| 只支持左槽 | `slot = RIGHT` 返回 `ESP_ERR_NOT_SUPPORTED`；`AUTO` 视为 `LEFT` | 右槽镜像把 16/15/17/18/19/55 映射到 40/38/37/54/52/49，与板载 I²S {54,37,49,52,40} 冲突（`subboard.c:52-67`，`esp_mosaico.h:109-113`） |
| 编译期检查 | `_Static_assert`：10 个 KEY_* GPIO 互不重复；不含 GPIO14（EEPROM A0）、GPIO0/1（I²C1）、GPIO33/34（USJ）、I²S 五脚；备用脚不作按键 | 硬约束 6；`LEFT_SLOT.md` |

## 4. KEY_* → GPIO（PINMAP.md 镜像）

权威来源：`hardware/module-board/PINMAP.md` 第 2 节（分支 `claude/design-d/module-board`，2026-09-20）。**上一轮 WIP 按 H2 针序顺排了十键，与 PINMAP.md 不一致，本版已改正**（改动：DOWN 53→19、LEFT 19→18、RIGHT 48→17、A 18→53、B 13→48、X 17→13、Y 12→12 不变、L 16 不变、R 15 不变、UP 55 不变）。

| KEY_* | H2 针 | GPIO | J2 焊盘（PINMAP §4.2） | 宏 |
| --- | --- | --- | --- | --- |
| KEY_UP | 1 | 55 | A3 | `DOCK_HANDLE_GPIO_KEY_UP` |
| KEY_DOWN | 3 | 19 | A4 | `DOCK_HANDLE_GPIO_KEY_DOWN` |
| KEY_LEFT | 5 | 18 | A5 | `DOCK_HANDLE_GPIO_KEY_LEFT` |
| KEY_RIGHT | 7 | 17 | A6 | `DOCK_HANDLE_GPIO_KEY_RIGHT` |
| KEY_L | 9 | 16 | A7 | `DOCK_HANDLE_GPIO_KEY_L` |
| KEY_R | 11 | 15 | B2 | `DOCK_HANDLE_GPIO_KEY_R` |
| KEY_A | 2 | 53 | B3 | `DOCK_HANDLE_GPIO_KEY_A` |
| KEY_B | 4 | 48 | B4 | `DOCK_HANDLE_GPIO_KEY_B` |
| KEY_X | 6 | 13 | B5 | `DOCK_HANDLE_GPIO_KEY_X` |
| KEY_Y | 8 | 12 | B6 | `DOCK_HANDLE_GPIO_KEY_Y` |
| （备用） | 12 | 4 | 不引出（TP7） | `DOCK_HANDLE_GPIO_SPARE`，不配置 |

规律：奇数排 pin1/3/5/7/9/11 = UP/DOWN/LEFT/RIGHT/L/R，偶数排 pin2/4/6/8 = A/B/X/Y。H2 针 ↔ GPIO 取自 `LEFT_SLOT.md`。改表方式：改 `include/dock_handle_pinmap.h` 默认值，或工程里 `target_compile_definitions(... -DDOCK_HANDLE_GPIO_KEY_A=GPIO_NUM_xx)`；`_Static_assert` 拦重复与禁用引脚，但拦不住「与 PINMAP.md 不一致」——那只能靠 §10 步 5 的到货验证。

弹簧针 2×8 分配（ICD 第 3.2 节，列 3–7 成对同列）与本表无直接耦合：固件只认 KEY_* 名与 H2 针，弹簧针位由模块板/底座任务保证。

## 5. 与 eeprom 分支的对接

`hardware/eeprom/IDENTITY.md`（分支 `claude/design-d/eeprom`，同为提案）定义了本驱动核对与解释的字段：

| 字段 | IDENTITY.md 取值 | 本驱动用法 | Kconfig |
| --- | --- | --- | --- |
| board_type | 0x04 HANDLE | claim 的 `expected_type`；严禁 0x14 | 固定 |
| vendor_id | 0x4354（"CT"） | 认领前后核对 | `CONFIG_DOCK_HANDLE_VENDOR_ID` |
| board_id | 0x0101 | 认领前后核对 | `CONFIG_DOCK_HANDLE_BOARD_ID` |
| sw_version | 0x0100 | 高字节 0x01 作身份核对项；同时门控 param_data 解释（规则 3） | `CONFIG_DOCK_HANDLE_SW_VERSION_MAJOR` |
| param_version / param_length | 0x0001 / 24 | 不符则忽略 param_data | — |
| param_data[0x01] key_flags | bit0 ACTIVE_LOW=1、bit1 KEYMAP_VALID | ACTIVE_LOW=0 视为与硬约束 5 矛盾，忽略 keymap；KEYMAP_VALID=0 用静态表 | `CONFIG_DOCK_HANDLE_USE_EEPROM_KEYMAP` |
| param_data[0x04..0x0D] key_gpio[10] | 样例 0xFF×10（未填） | 顺序 UP DOWN LEFT RIGHT A B X Y L R；校验后采用 | 同上 |
| param_data[0x02/0x03] poll/debounce | 20 / 2 | 只打印提示，不覆盖运行参数（本驱动去抖取更保守的 3） | — |

**ASSUMPTION: AS-31-firmware-8** 上述身份值以 eeprom 分支为准；该分支改值时同步 Kconfig 默认值。到货初期若 EEPROM 未烧正式身份，可临时 `CONFIG_DOCK_HANDLE_CHECK_IDENTITY=n` 排障，验收前必须恢复。

## 6. API 核实表

所有引用的函数、宏、类型都在 BSP commit `392860b1` 源码中 grep 到真实名称与签名；行号以该提交为准。凡未列入本表的 BSP 符号，本组件未使用。

### 6.1 `components/mosaico_module_mgr/include/mosaico_module_mgr.h`

| 行 | 符号 | 签名 / 定义 | 用处 |
| --- | --- | --- | --- |
| 23-25 | `MOSAICO_MODULE_MGR_EEPROM_MAGIC` / `_IMAGE_SIZE` | `"ESP"` / `0x86U` | 文档引用 |
| 26 | `MOSAICO_MODULE_MGR_SLOT_AUTO` | `= MOSAICO_MODULE_MGR_SLOT_COUNT` | `validate_config` 将 AUTO 视为 LEFT |
| 36-40 | `mosaico_module_mgr_slot_t` | `LEFT = 0, RIGHT, COUNT` | 全部 |
| 47 | `MOSAICO_BOARD_TYPE_HANDLE` | `= 0x04` | claim、候选核对 |
| 61-65 | `mosaico_module_presence_t` | `UNKNOWN, ABSENT, PRESENT` | 候选核对、拔出检测 |
| 68-72 | `mosaico_module_descriptor_state_t` | `UNKNOWN, VALID, INVALID` | 候选核对 |
| 75-79 | `mosaico_module_owner_state_t` | `FREE, CLAIMED, RESTORING` | 候选核对、keytest 日志 |
| 86-105 | `mosaico_module_mgr_eeprom_v1_t` | 字段 `board_type board_id hw_version sw_version vendor_id board_flags serial_number board_name[32] … param_version param_length param_data[64]` | 身份核对、param_data 解析、日志 |
| 108-117 | `mosaico_module_mgr_info_t` | `slot presence descriptor_state owner_state generation last_error eeprom_addr eeprom` | 全部 |
| 120-123 | `mosaico_module_lease_t` | `{ slot; id; }`，`id == 0` 无效 | 认领/释放 |
| 137-142 | `mosaico_module_mgr_claim_config_t` | `{ expected_type; slot; timeout_ms; flags; }`，`timeout_ms = 0` 单次尝试 | `try_attach` |
| 145-150 | `mosaico_module_change_t` | `PRESENCE = 1<<0, DESCRIPTOR = 1<<1, OWNER = 1<<2, ERROR = 1<<3` | 回调过滤 |
| 153-156 | `mosaico_module_mgr_event_t` | `{ changes; info; }` | 回调 |
| 168 | `mosaico_module_mgr_event_callback_t` | `void (*)(const mosaico_module_mgr_event_t *event, void *user_data)` | `on_module_event` |
| 171-174 | `mosaico_module_subscription_t` | `{ index; generation; }` | 订阅句柄 |
| 199 | `mosaico_module_mgr_init` | `esp_err_t (const mosaico_module_mgr_config_t *config)`；NULL 时幂等 | init |
| 232-233 | `mosaico_module_mgr_subscribe` | `esp_err_t (mosaico_module_mgr_event_callback_t callback, void *user_data, mosaico_module_subscription_t *out_subscription)` | init |
| 248 | `mosaico_module_mgr_unsubscribe` | `esp_err_t (const mosaico_module_subscription_t *subscription)` | deinit |
| 261 | `mosaico_module_mgr_get_info` | `esp_err_t (mosaico_module_mgr_slot_t slot, mosaico_module_mgr_info_t *out_info)` | 候选核对、认领后核对、keytest |
| 281 | `mosaico_module_mgr_claim` | `esp_err_t (const mosaico_module_mgr_claim_config_t *config, mosaico_module_lease_t *out_lease)`；返回 `ESP_ERR_NOT_FOUND` 表示非阻塞无匹配 | `try_attach` |
| 297 | `mosaico_module_mgr_release` | `esp_err_t (const mosaico_module_lease_t *lease)` | `detach_now`、核对失败回滚 |
| 317 | `mosaico_module_mgr_slot_to_name` | `const char *(mosaico_module_mgr_slot_t slot)`，返回 `"left"/"right"/"auto"/"unknown"`（.c:263-275） | 日志 |
| 325 | `mosaico_module_mgr_type_to_name` | `const char *(mosaico_board_type_t type)`，HANDLE → `"Handle"`（.c:277-312） | 日志 |
| 213 / 309 | `mosaico_module_mgr_deinit` / `_request_rescan` | 存在，**本组件未使用** | — |

### 6.2 `components/esp-mosaico-bsp/include/bsp/subboard.h`

| 行 | 符号 | 签名 / 定义 | 用处 |
| --- | --- | --- | --- |
| 34-35 | `BSP_SUBBOARD_EEPROM_ADDR_LEFT` / `_RIGHT` | `0x50U` / `0x51U` | keytest I²C 扫描分类 |
| 36 | `BSP_SUBBOARD_ADDR_GPIO_LEFT` | `GPIO_NUM_14` | 禁用引脚 `_Static_assert` |
| 41-45 | `bsp_subboard_slot_t` | `LEFT = 0, RIGHT, COUNT`（与管理器槽枚举同值，代码作显式强转） | `bsp_subboard_map_gpio` 参数 |
| 65 | `bsp_subboard_get_i2c_bus` | `i2c_master_bus_handle_t (void)`（实现 `subboard.c:154`） | keytest I²C 扫描 |
| 98 | `bsp_subboard_map_gpio` | `gpio_num_t (bsp_subboard_slot_t slot, gpio_num_t left_gpio)`；左槽原样返回（`subboard.c:212-224`） | `configure_key_gpios` |

### 6.3 `components/esp-mosaico-bsp/include/bsp/esp_mosaico.h`、`power.h`、`display.h`

| 文件:行 | 符号 | 签名 / 定义 | 用处 |
| --- | --- | --- | --- |
| esp_mosaico.h:37-40 | `bsp_board_variant_t` | `BSP_BOARD_VARIANT_V1_0 = 0, BSP_BOARD_VARIANT_V1_2` | keytest |
| esp_mosaico.h:43 | `bsp_board_variant_get` | `esp_err_t (bsp_board_variant_t *variant)`；实现 `esp_mosaico.c:62`，读 eFuse USER_DATA（`:40-60`），v1.0→V1_0，v1.1/v1.2→V1_2，其他 `ESP_ERR_NOT_SUPPORTED` | keytest 第 ② 步读 eFuse |
| esp_mosaico.h:74-75 | `BSP_SUBBOARD_I2C_SDA` / `_SCL` | `GPIO_NUM_0` / `GPIO_NUM_1` | 禁用引脚、扫描日志 |
| esp_mosaico.h:109-113 | `BSP_AUDIO_I2S_MCLK/SCLK/LRCLK/SDOUT/DSIN` | `GPIO_NUM_54/37/49/52/40` | 禁用引脚 |
| power.h:16 | `bsp_power_init` | `esp_err_t (void)`；实现 `esp_mosaico.c:143` | keytest |
| display.h:84 | `bsp_display_start` | `lv_display_t *(void)` | keytest（可选） |
| display.h:157 | `bsp_display_lock` | `bool (int32_t timeout_ms)` | keytest（可选） |
| display.h:158 | `bsp_display_unlock` | `void (void)` | keytest（可选） |

### 6.4 ESP-IDF / FreeRTOS（在本机 ESP-IDF v5.5.4 源码核实；目标 6.2 待核，AS-31-firmware-9）

| 符号 | 出处 | 用处 |
| --- | --- | --- |
| `i2c_master_probe(i2c_master_bus_handle_t, uint16_t address, int xfer_timeout_ms)` | `esp_driver_i2c/include/driver/i2c_master.h:253`；管理器自身以它探测 EEPROM（`mosaico_module_mgr.c:481`） | keytest 只读扫描 |
| `xTaskDelayUntil`、`xTaskNotify`、`xTaskNotifyWait`、`vTaskSuspend`、`vTaskDelete` | `freertos/FreeRTOS-Kernel/include/freertos/task.h` | 轮询任务 |
| `gpio_config`、`gpio_reset_pin`、`gpio_get_level`、`GPIO_NUM_NC` | `esp_driver_gpio/include/driver/gpio.h` | GPIO |
| `portENTER_CRITICAL(portMUX_TYPE *)` | IDF FreeRTOS 移植层 | init 单例保护 |

### 6.5 核实为「不存在」的符号

- `CONFIG_BSP_USB_CONSOLE*`、`CONFIG_BSP_USB_AUTO_DOWNLOAD`：BSP 392860b1 全部源码无此符号（详见 `PC_LINK.md` §3）。
- 任何「按键中断」「按键回调」API：BSP 对模块槽 GPIO 无中断通路（`LEFT_SLOT.md`）。
- 管理器写 EEPROM API：不存在（`BSP_AND_EEPROM.md` §3）。

## 7. 构建

### 7.1 工具链要求

BSP `idf_component.yml` 要求 `idf: ">=6.2"`、目标 `esp32s31`（`components/esp-mosaico-bsp/idf_component.yml`）；官方示例 `sdkconfig.defaults` 用 `CONFIG_IDF_TARGET="esp32s31"` ＋ `CONFIG_IDF_EXPERIMENTAL_FEATURES=y`，即 `idf.py --preview set-target esp32s31`。

### 7.2 取得 BSP

```bash
git clone https://github.com/esp-mosaico/esp-mosaico-bsp.git
git -C esp-mosaico-bsp checkout 392860b1d1a123c3377947074b2af1f600e86c5d
```

### 7.3 方式 A：组件管理器 git 依赖（`idf_component.yml` 已写死 commit）

直接在 `examples/keytest` 下构建，组件管理器按 `idf_component.yml` 拉取 `mosaico_module_mgr` 与 `esp-mosaico-bsp` 两个子目录组件。**ASSUMPTION: AS-31-firmware-4** 组件管理器对「git 源 + `path` 子目录」的解析，以及 `mosaico_module_mgr/idf_component.yml` 内 `override_path: ../esp-mosaico-bsp` 在该模式下能否解析，均未验证。验证：首次 `idf.py reconfigure`；失败改方式 B。

### 7.4 方式 B：本地 BSP 副本

```bash
export MOSAICO_BSP_COMPONENTS=/path/to/esp-mosaico-bsp/components
```

`examples/keytest/CMakeLists.txt` 检测到该变量后把 `esp-mosaico-bsp` 与 `mosaico_module_mgr` 加入 `EXTRA_COMPONENT_DIRS`。此时需注释掉 `firmware/dock_handle/idf_component.yml` 中的两个 git 依赖，避免同名组件二义。

命令：

```bash
cd firmware/dock_handle/examples/keytest
idf.py --preview set-target esp32s31
idf.py menuconfig        # Dock Handle / Dock Handle keytest 菜单
idf.py build
idf.py -p PORT flash monitor
```

控制台走 UART0（`sdkconfig.defaults`，与官方 `module_slot_scan` 相同关闭 USJ）。左槽 H2 pin13/15 是 USB Serial/JTAG（GPIO33/34），插上模块板后被连接器占用（模块板不接这两针，AS-30），USJ 控制台不可达。UART0 在官方 V1.0 指南中位于右槽 H1（TX0 GPIO58 / RX0 GPIO59；**ASSUMPTION: AS-31-firmware-5** V1.2 相同），需 USB-UART 转接板。原生 USB-C 的 CDC 控制台见 `PC_LINK.md`。

### 7.5 本轮实际做了什么、没做什么

- **未执行 `idf.py build`。** 本机唯一的 ESP-IDF 是 `~/esp/esp-idf` **v5.5.4**（`git describe`），其 `components/soc/` 只有 esp32/c2/c3/c5/c6/c61/h2/h21/h4/p4/s2/s3，**没有 esp32s31 目标**；`idf.py` 也不在 PATH。BSP 要求 IDF ≥ 6.2 preview，本机无法满足，故未编译、未链接、未上机。
- **已执行宿主机语法检查**（Apple clang 21，`-fsyntax-only -std=gnu17 -Wall -Wextra -Wformat`）：
  - 对 `dock_handle.c`、`examples/keytest/main/main.c`（显示开/关 × I²C 扫描开/关四种配置）全部通过，无警告。
  - 检查使用 **392860b1 的真实头** `mosaico_module_mgr.h`、`bsp/subboard.h`（sha256 与 BSP 克隆一致），因此对管理器与 subboard 的类型、字段、签名的引用是经编译器核对的。
  - 其余接口用桩头模拟：`esp_err.h`、`esp_log.h`、`esp_check.h`、`esp_timer.h`、`driver/gpio.h`、`driver/i2c_master.h`、`freertos/*`、`lvgl.h`，以及 `bsp/esp_mosaico.h` 的桩（只含本工程用到的宏与原型，数值与签名逐行抄自真实头并注行号）。**桩头只证明本工程源码与所引接口自洽，不证明能在 ESP-IDF 6.2 / esp32s31 上编译通过或运行正确。**
- 到货前若有人手上有 IDF 6.2 preview 环境，请先跑 `idf.py build` 并把结果贴回本文件。

## 8. 在应用中使用

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

事件语义：`ATTACHED` 表示已认领、身份核对通过并配置好 GPIO；`DETACHED` 表示 lease 已释放，且之前按下的键已先收到释放事件；应用层不需要自己清按键状态。长按、重复、组合键语义交给应用层（T13 交互设计）。**产品应用不得链接官方 `mosaico_module_joystick` 驱动**（IDENTITY.md §2.4 对策 2）：它也以 HANDLE 认领，且用 `SLOT_AUTO`。

## 9. 与 `module_slot_scan` 配合

- `module_slot_scan` 是 BSP 官方双槽热插拔示例（`examples/module_slot_scan`）：相机、交互板有专用面板，其他已识别的板只显示类型名。手柄模块板 EEPROM `board_type = 0x04` 会显示为 `Handle`（`mosaico_module_mgr.c:300-301`）。
- 建议顺序：先烧 `module_slot_scan`，只验证 EEPROM 链路（左槽 `PRESENT` + `VALID` + `Handle`，地址 0x50）；通过后再烧 `keytest`。两者是独立固件，不同时运行。
- `keytest` 内置了同源的两槽扫描日志（`log_slot_info()`），并多打印 owner、generation、hw/sw、serial、mfg、param_version/length 与 `param_data` 前 24 字节；没有面板，只看串口。
- 两个示例都把控制台放在 UART（`module_slot_scan` 因相机 D2 与 GPIO33 冲突，本例因模块板占用 H2 pin13/15）。
- ICD 第 8 节 ①要求的「134 字节原始镜像 + 三段 CRC 结果」：管理器 API 只给 `VALID/INVALID`，不暴露原始字节与 CRC 值；原始镜像转储与 CRC 复算由 eeprom 分支 `hardware/eeprom/eeprom_program_example.c`（烧写夹具侧）与 `mosaico_eeprom_v1.py` 覆盖，`keytest` 不重复实现（§12）。

## 10. 到货后验证顺序

| 步 | 操作 | 预期 | 关闭的假设 / 对应 G6 |
| --- | --- | --- | --- |
| 1 | 烧 `keytest`，看启动日志 | BSP 打 `Hardware version: v1.x`，keytest 打 `board variant: V1.2`。若 `bsp_board_variant_get failed`，eFuse USER_DATA 未编程或不支持，停止并记录 | AS-16、AS-28 |
| 2 | 两槽都空 | I²C 扫描 `0 device(s)`；两槽 `ABSENT`，`last_error=ESP_OK`；否则 I²C1 或上拉有问题 | G6-C |
| 3 | 模块板单板（不接底座，EEPROM 已按 IDENTITY.md 烧好）插左槽 | 扫描 `ACK 0x50 left slot EEPROM`，无其他地址；`slot left … PRESENT descriptor=VALID`，`type=Handle(0x04) board_id=0x0101 vendor_id=0x4354 sw=0x0100`；`dock_handle` 打 `attached … keymap=static`（样例镜像 KEYMAP_VALID=0）与 10 行 `KEY_* -> GPIOnn` | AS-13、AS-14、AS-20；G6-C |
| 4 | 若 EEPROM 已用 `build --keymap` 填表 | `keymap=eeprom`，且**不出现** `EEPROM keymap differs` 告警；出现即 PINMAP.md 与 EEPROM 工具输入不一致，先对账再继续 | AS-31-firmware-8 |
| 5 | 单板上逐个把 J2 KEY_* 焊盘对 DOCK_GND 短接 | 打印键名与 PINMAP.md §4.2 焊盘位、底座丝印一致；`state` 位图只置对应位 | PINMAP P4 |
| 6 | 示波器看一只轻触开关的抖动时长 | 抖动 < (去抖次数−1)×轮询周期 = 40 ms；否则加大 `CONFIG_DOCK_HANDLE_DEBOUNCE_COUNT` | AS-31-firmware-1；G6-D4 |
| 7 | 接上底座（先不装电池、不接底座 USB），10 键各按一次，再做组合（D-pad 双键、A+B、L+R、四键同按） | 每键独立 GPIO，无鬼键、无漏键；组合时位图正确 | G6-D1/D2 |
| 8 | 每键长按 10 s、快速连击 20 次 | 长按持续为 DOWN 无抖动；连击无丢键 | AS-23；G6-D3 |
| 9 | 运行中拔模块板；按住某键拔 | 约 1 s 内 `detached`（管理器 250 ms × 3 次去抖）；按住的键先 `UP` 再 `DETACHED`；插回后 `attached` | AS-31-firmware-2 |
| 10 | 主机 GPIO 高电平电压、上升沿（单板与整机各测一次） | 内部上拉能把整条按键网络（弹簧针 + 走线 + 开关）拉到可靠高电平；否则提请硬件任务加外部上拉位 | AS-31-firmware-3 |
| 11 | 按住任一键上电 / 复位，11 根各一次 | 正常启动，无进入下载模式 | AS-15；PINMAP P3；G6-D5 |
| 12 | 24 h 心跳日志 | `dropped=0`，无 `last_error`，无自发 `detached` | — |
| 13 | 若有官方 joystick 模块：插 joystick | 打一次 `HANDLE board vendor=… not using`，不认领；`module_slot_scan` 同样只显示 Handle | IDENTITY.md §2.4 |

底座供电（pin17）相关验证属底座主板任务；本固件不参与供电时序，只需在步骤 7–12 观察无 I²C 错误与无异常复位。

## 11. 假设清单（本分支临时编号 AS-31-firmware-n，汇总阶段并入 `hardware/ASSUMPTIONS.md`）

已在 `hardware/ASSUMPTIONS.md` 登记、本组件直接引用的：AS-15（strapping）、AS-16/AS-28（版本与 eFuse）、AS-20（身份官方未分配）、AS-21（右槽空）、AS-23（轮询满足手感）、AS-30（pin13/15 NC）。以下为本分支新增：

| 编号 | ASSUMPTION | 到货后验证 |
| --- | --- | --- |
| AS-31-firmware-1 | 轻触开关抖动 ≤ 40 ms，20 ms × 3 次去抖足够 | §10 步 6 |
| AS-31-firmware-2 | 管理器默认配置（250 ms 扫描、3 次去抖）下拔出检测约 0.75–1 s，可接受 | §10 步 9 |
| AS-31-firmware-3 | ESP32-S31 GPIO 内部上拉足以拉高整条按键网络，无需外部上拉（S31 内部上拉阻值未查数据手册） | §10 步 10；不足则提请硬件任务在模块板加外部上拉位 |
| AS-31-firmware-4 | 组件管理器能解析 `idf_component.yml` 的 git 子路径依赖与其内部 `override_path` | 首次 `idf.py reconfigure` |
| AS-31-firmware-5 | UART0 TX0/RX0 = GPIO58/59 在右槽 H1（V1.0 指南），V1.2 相同 | 官方 V1.2 资料或实测 |
| AS-31-firmware-6 | LVGL 头经 `esp-mosaico-bsp` → `espressif/esp_lvgl_adapter`（public）传递到 `main`，无需显式 REQUIRES | `idf.py build`；失败加 `lvgl__lvgl` |
| AS-31-firmware-7 | `keytest` 启动时的 I²C 扫描与管理器扫描任务并发访问 I2C1 由 IDF `i2c_master` 总线锁串行化（v5.5.4 `i2c_master.c` 有 `bus_lock_mux`；6.2 待核） | 上机观察扫描期间无 I²C 错误日志；否则把扫描移到 `mosaico_module_mgr_init` 之前自行建总线（需改代码） |
| AS-31-firmware-8 | EEPROM 身份 vendor 0x4354 / board 0x0101 / sw 0x0100 与 param_data v1 布局以 eeprom 分支 IDENTITY.md 为准，该分支尚未被采纳 | eeprom 分支合入后对账 Kconfig 默认值；§10 步 3、4 |
| AS-31-firmware-9 | ESP-IDF 6.2 preview 的 FreeRTOS / gpio / i2c_master API 与 v5.5.4 一致（`xTaskDelayUntil`、`i2c_master_probe` 等） | `idf.py build` |
| AS-31-firmware-10 | 所选 10 个 GPIO 在 ESP32-S31 上无 strapping / 启动电平要求（PINMAP.md §1.5 依据的是 IDF 寄存器头注释，不是数据手册） | 与 AS-15 同：查 S31 数据手册 strapping 表；§10 步 11 |
| AS-31-firmware-11 ～ 15 | 见 `PC_LINK.md` §9（USJ/UART 位置、`esp_tinyusb` 双 CDC、宿主 DTR/RTS 行为、双供电时 USB 枚举、BSP 未来内置 USB console） | 同文件 |

## 12. 已知限制

- **未在 ESP-IDF 中编译、未上机**（§7.5）。
- HANDLE 类型与官方 joystick 模块共用 `0x04`；默认开启身份核对，插入 joystick 不会被认领。关闭核对时 joystick 会被当作手柄认领（GPIO 48/53 是它的摇杆模拟轴，读到的只是无意义的电平）。
- 无中断：按键识别最坏延迟 ≈ 去抖次数 × 轮询周期（默认 60 ms）。每 20 ms 读 10 个 GPIO，CPU 开销可忽略。
- 拔出检测依赖管理器对 EEPROM 的探测，不是按键线本身；拔出瞬间按键线被内部上拉拉高，表现为释放，不会误报按下。
- 只支持左槽；只支持一套手柄（单例）。
- 不提供长按、自动重复、组合键语义；不提供 LED / 马达反馈（本设计底座无 LED）。
- 插上模块板后 USB Serial/JTAG 控制台不可用，见 §7.4 与 `PC_LINK.md`。
- `keytest` 不转储 134 字节原始 EEPROM 镜像、不复算三段 CRC（管理器 API 不暴露）；由 eeprom 分支工具覆盖（§9）。
- `keytest` 的 I²C 扫描只做一次（启动时），不监视后续插入的 I²C 器件。
- EEPROM 烧写不在 BSP 公开流程内；由 eeprom 分支 `PROGRAMMING.md` 定义。
- `dock_handle_deinit()` 最多等待轮询任务 2 s。
- `idf_component.yml` 的依赖解析方式未验证（AS-31-firmware-4）。

## 13. 依据索引

- `hardware/ICD-0.2-DRAFT.md`：坐标系、H2 合同、弹簧针 2×8 分配、EL-D-01～12、第 8 节固件接口要求、第 9 节网络命名。
- `hardware/ASSUMPTIONS.md`：AS-01～30；本分支新增见 §11。
- `hardware/G6-TEST-PLAN.md`：G6-C（I²C 扫描）、G6-D（十键）步骤；TH-10 待 Chrome 定义。
- `origin/claude/design-d/module-board:hardware/module-board/PINMAP.md`：KEY_* → H2 针 → GPIO → J2 焊盘；P3/P4 验证。
- `origin/claude/design-d/eeprom:hardware/eeprom/IDENTITY.md`：身份字段取值、§2.4 驱动核对、§8 param_data v1 与主机侧使用规则。
- `review/chrome/D1-module-interface/LEFT_SLOT.md`：H2 针号 ↔ GPIO、可用 GPIO 集、I²S 无交集、无中断通路、pin17 供电不得等待主机。
- `review/chrome/D1-module-interface/BSP_AND_EEPROM.md`：管理器 claim / release / 拔出行为、EEPROM 镜像格式、驱动接入例证。
- `review/chrome/D1-module-interface/evidence/bsp/`（392860b1 快照）与 `/tmp/mosaico-v12/esp-mosaico-bsp/`（同提交完整克隆）：§6 全部行号的出处。
- `/tmp/mosaico-v12/handheld_dock_skeleton.c`：本驱动起点。
- 官方 V1.0 用户指南（`review/chrome/D1-module-interface/evidence/user_guide_v10.rst`）：扩展排针表、USB / USJ / UART 描述。
- `docs/DECISIONS.md` D-017：迭代式打板主循环。
