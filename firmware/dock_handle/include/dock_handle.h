/*
 * 提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
 *
 * dock_handle —— 方案 D＋G 底座手柄（10 键：D-pad、ABXY、L/R）的主机侧驱动。
 *
 * 硬件模型：底座主板上的 10 个轻触开关经弹簧针进入模块板，再经左槽 H2 直连主机 GPIO；
 * 模块板只有 AT24C02 与触点，无 MCU、无 I2C 扩展器。因此本驱动只做：
 *   1. 通过 mosaico_module_mgr 以 MOSAICO_BOARD_TYPE_HANDLE 认领左槽（flags = 0）；
 *   2. 认领后按 hardware/eeprom/IDENTITY.md 第 2.4 节核对 vendor_id / board_id / sw_version 主版本，
 *      不符则立即 release（可用 Kconfig 关闭）；
 *   3. 用 bsp_subboard_map_gpio() 取 KEY_* 对应 GPIO，配置为输入＋内部上拉；GPIO 表默认来自
 *      dock_handle_pinmap.h（PINMAP.md 镜像），若 EEPROM param_data v1 的 KEYMAP_VALID=1 且校验通过
 *      则改用 EEPROM 表（IDENTITY.md 第 8 节「主机侧使用规则」）；
 *   4. 20–40 ms 周期轮询＋N 次一致去抖（BSP 无中断通路，见 LEFT_SLOT.md）；
 *   5. 以 FreeRTOS 队列投递 dock_handle_event_t；提供按键位图；
 *   6. 监听管理器事件，模块拔出时释放 GPIO 与 lease；可选自动重新认领。
 *
 * 所引 BSP API 均已在 esp-mosaico-bsp commit 392860b1 源码中核对到真实函数名与签名
 * （逐条见 README.md「API 核实表」）：
 *   mosaico_module_mgr_init / _claim / _release / _get_info / _subscribe / _unsubscribe /
 *   _slot_to_name / _type_to_name（components/mosaico_module_mgr/include/mosaico_module_mgr.h）；
 *   bsp_subboard_map_gpio（components/esp-mosaico-bsp/include/bsp/subboard.h:98）。
 */

#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "driver/gpio.h"
#include "esp_err.h"
#include "mosaico_module_mgr.h"
#include "sdkconfig.h"

#ifdef __cplusplus
extern "C" {
#endif

/** 按键编号。位图中的 bit n 对应枚举值 n。名称与跨子系统统一网络名 KEY_* 一一对应。
 *  顺序与 IDENTITY.md 第 8 节 param_data v1 的 key_gpio[10] 顺序相同（UP DOWN LEFT RIGHT A B X Y L R）。 */
typedef enum {
    DOCK_HANDLE_KEY_UP = 0,     /*!< KEY_UP    D-pad 上 */
    DOCK_HANDLE_KEY_DOWN,       /*!< KEY_DOWN  D-pad 下 */
    DOCK_HANDLE_KEY_LEFT,       /*!< KEY_LEFT  D-pad 左 */
    DOCK_HANDLE_KEY_RIGHT,      /*!< KEY_RIGHT D-pad 右 */
    DOCK_HANDLE_KEY_A,          /*!< KEY_A */
    DOCK_HANDLE_KEY_B,          /*!< KEY_B */
    DOCK_HANDLE_KEY_X,          /*!< KEY_X */
    DOCK_HANDLE_KEY_Y,          /*!< KEY_Y */
    DOCK_HANDLE_KEY_L,          /*!< KEY_L    左肩键 */
    DOCK_HANDLE_KEY_R,          /*!< KEY_R    右肩键 */
    DOCK_HANDLE_KEY_COUNT,
} dock_handle_key_t;

/** 事件类型。 */
typedef enum {
    DOCK_HANDLE_EVENT_KEY = 0,  /*!< 按键状态变化；key / pressed 有效 */
    DOCK_HANDLE_EVENT_ATTACHED, /*!< 已认领槽位、身份核对通过并配置好全部 KEY_* GPIO */
    DOCK_HANDLE_EVENT_DETACHED, /*!< 模块被拔出或驱动停止；lease 已释放，之前按下的键已补发释放事件 */
} dock_handle_event_type_t;

/** 按键事件。 */
typedef struct {
    dock_handle_event_type_t type; /*!< 事件类型 */
    dock_handle_key_t key;         /*!< 仅 type == DOCK_HANDLE_EVENT_KEY 时有效 */
    bool pressed;                  /*!< true = 按下（GPIO 读 0），false = 释放 */
    int64_t timestamp_us;          /*!< esp_timer_get_time() 采样时刻，微秒 */
} dock_handle_event_t;

/** 驱动与槽位的连接状态。 */
typedef enum {
    DOCK_HANDLE_LINK_STOPPED = 0, /*!< 未初始化或已 deinit */
    DOCK_HANDLE_LINK_WAITING,     /*!< 已初始化，槽位未认领，等待匹配模块 */
    DOCK_HANDLE_LINK_ATTACHED,    /*!< 已认领，正在轮询按键 */
} dock_handle_link_t;

/** 当前生效的 KEY_* -> GPIO 表来源。 */
typedef enum {
    DOCK_HANDLE_KEYMAP_NONE = 0,  /*!< 未 ATTACHED */
    DOCK_HANDLE_KEYMAP_STATIC,    /*!< dock_handle_pinmap.h（PINMAP.md 镜像） */
    DOCK_HANDLE_KEYMAP_EEPROM,    /*!< EEPROM param_data v1 key_gpio[]，已通过合法集合与互异校验 */
} dock_handle_keymap_source_t;

/** 运行参数。 */
typedef struct {
    mosaico_module_mgr_slot_t slot; /*!< 只接受 LEFT；AUTO 视为 LEFT；RIGHT 返回 ESP_ERR_NOT_SUPPORTED */
    uint32_t claim_timeout_ms;      /*!< init 阻塞等待首次认领的时间；0 = 不等待 */
    uint32_t poll_period_ms;        /*!< 轮询周期，允许 20–40 ms */
    uint8_t debounce_count;         /*!< 连续一致采样次数，>= 2 */
    uint8_t event_queue_len;        /*!< 事件队列深度，>= 4 */
    bool auto_reattach;             /*!< 拔出后是否在后台等待并自动重新认领 */
    bool check_identity;            /*!< 认领后核对 EEPROM vendor_id / board_id / sw_version 主版本 */
    uint16_t vendor_id;             /*!< check_identity 时要求的 vendor_id（IDENTITY.md：0x4354 "CT"） */
    uint16_t board_id;              /*!< check_identity 时要求的 board_id（IDENTITY.md：0x0101） */
    uint8_t sw_version_major;       /*!< check_identity 时要求的 sw_version 高字节（IDENTITY.md：0x01） */
    bool use_eeprom_keymap;         /*!< 允许采用 EEPROM param_data v1 的 key_gpio[]（校验通过才采用） */
} dock_handle_config_t;

#if CONFIG_DOCK_HANDLE_CHECK_IDENTITY
#define DOCK_HANDLE_DEFAULT_CHECK_IDENTITY  true
#define DOCK_HANDLE_DEFAULT_VENDOR_ID       CONFIG_DOCK_HANDLE_VENDOR_ID
#define DOCK_HANDLE_DEFAULT_BOARD_ID        CONFIG_DOCK_HANDLE_BOARD_ID
#else
#define DOCK_HANDLE_DEFAULT_CHECK_IDENTITY  false
#define DOCK_HANDLE_DEFAULT_VENDOR_ID       0
#define DOCK_HANDLE_DEFAULT_BOARD_ID        0
#endif
/* sw_version 主版本同时门控 param_data 解释（IDENTITY.md 第 8 节规则 3），不随 CHECK_IDENTITY 关闭。 */
#define DOCK_HANDLE_DEFAULT_SW_MAJOR        CONFIG_DOCK_HANDLE_SW_VERSION_MAJOR

#if CONFIG_DOCK_HANDLE_AUTO_REATTACH
#define DOCK_HANDLE_DEFAULT_AUTO_REATTACH   true
#else
#define DOCK_HANDLE_DEFAULT_AUTO_REATTACH   false
#endif

#if CONFIG_DOCK_HANDLE_USE_EEPROM_KEYMAP
#define DOCK_HANDLE_DEFAULT_USE_EEPROM_KEYMAP true
#else
#define DOCK_HANDLE_DEFAULT_USE_EEPROM_KEYMAP false
#endif

/** 默认参数，数值来自 Kconfig。 */
#define DOCK_HANDLE_DEFAULT_CONFIG() {                                  \
    .slot = MOSAICO_MODULE_MGR_SLOT_LEFT,                               \
    .claim_timeout_ms = CONFIG_DOCK_HANDLE_CLAIM_TIMEOUT_MS,            \
    .poll_period_ms = CONFIG_DOCK_HANDLE_POLL_PERIOD_MS,                \
    .debounce_count = CONFIG_DOCK_HANDLE_DEBOUNCE_COUNT,                \
    .event_queue_len = CONFIG_DOCK_HANDLE_EVENT_QUEUE_LEN,              \
    .auto_reattach = DOCK_HANDLE_DEFAULT_AUTO_REATTACH,                 \
    .check_identity = DOCK_HANDLE_DEFAULT_CHECK_IDENTITY,               \
    .vendor_id = DOCK_HANDLE_DEFAULT_VENDOR_ID,                         \
    .board_id = DOCK_HANDLE_DEFAULT_BOARD_ID,                           \
    .sw_version_major = DOCK_HANDLE_DEFAULT_SW_MAJOR,                   \
    .use_eeprom_keymap = DOCK_HANDLE_DEFAULT_USE_EEPROM_KEYMAP,         \
}

/**
 * @brief 以默认参数初始化并认领指定槽位。
 *
 * 等价于 dock_handle_init_with_config()，只把 slot 换成参数。
 *
 * @param slot MOSAICO_MODULE_MGR_SLOT_LEFT 或 MOSAICO_MODULE_MGR_SLOT_AUTO（视为 LEFT）
 * @return 见 dock_handle_init_with_config()
 */
esp_err_t dock_handle_init(mosaico_module_mgr_slot_t slot);

/**
 * @brief 初始化驱动：启动模块管理器、订阅事件、创建轮询任务，并等待首次认领。
 *
 * 驱动是单例。内部调用 mosaico_module_mgr_init(NULL)，与官方模块驱动一样可重复调用（幂等）。
 *
 * @param config 参数；NULL 使用 DOCK_HANDLE_DEFAULT_CONFIG()
 * @return
 *  - ESP_OK：在 claim_timeout_ms 内认领成功，已进入 ATTACHED
 *  - ESP_ERR_TIMEOUT：超时未认领。若 auto_reattach 为 true，驱动保持运行并在后台等待，
 *    认领成功时投递 DOCK_HANDLE_EVENT_ATTACHED；若为 false，驱动已回滚到 STOPPED
 *  - ESP_ERR_INVALID_ARG：参数越界
 *  - ESP_ERR_NOT_SUPPORTED：slot 为 RIGHT（右槽镜像 GPIO 与板载 I2S 冲突）
 *  - ESP_ERR_INVALID_STATE：已初始化
 *  - ESP_ERR_NO_MEM：队列或任务创建失败
 *  - 其他：mosaico_module_mgr_init / subscribe 的错误码
 */
esp_err_t dock_handle_init_with_config(const dock_handle_config_t *config);

/**
 * @brief 停止轮询、释放 GPIO 与 lease、取消订阅并回收资源。
 *
 * @return ESP_OK；ESP_ERR_INVALID_STATE 表示未初始化；ESP_ERR_TIMEOUT 表示轮询任务未在限时内退出
 */
esp_err_t dock_handle_deinit(void);

/**
 * @brief 当前去抖后的按键位图：bit n = 1 表示 dock_handle_key_t 值为 n 的键处于按下。
 *
 * 未 ATTACHED 时返回 0。
 */
uint32_t dock_handle_get_state(void);

/** @brief 当前连接状态。 */
dock_handle_link_t dock_handle_get_link(void);

/** @brief 是否已认领并在轮询。 */
bool dock_handle_is_attached(void);

/** @brief 当前生效的 KEY_* -> GPIO 表来源；未 ATTACHED 返回 DOCK_HANDLE_KEYMAP_NONE。 */
dock_handle_keymap_source_t dock_handle_get_keymap_source(void);

/**
 * @brief 从事件队列取一个事件。
 *
 * @param out_event 输出事件
 * @param timeout_ms 等待时间；0 立即返回，UINT32_MAX 永久等待
 * @return ESP_OK；ESP_ERR_TIMEOUT 无事件；ESP_ERR_INVALID_ARG；ESP_ERR_INVALID_STATE 未初始化
 */
esp_err_t dock_handle_wait_event(dock_handle_event_t *out_event, uint32_t timeout_ms);

/**
 * @brief 因队列满而丢弃的事件累计数（诊断用）。
 */
uint32_t dock_handle_get_dropped_events(void);

/**
 * @brief 某键在当前槽位上实际使用的 GPIO；未 ATTACHED 或键号非法返回 GPIO_NUM_NC。
 */
gpio_num_t dock_handle_key_gpio(dock_handle_key_t key);

/**
 * @brief 键名，与统一网络名一致（"KEY_UP" … "KEY_R"）；非法返回 "KEY_?"。
 */
const char *dock_handle_key_name(dock_handle_key_t key);

#ifdef __cplusplus
}
#endif
