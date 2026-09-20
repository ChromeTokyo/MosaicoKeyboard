/*
 * 提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
 *
 * dock_handle 驱动实现。起点为 handheld_dock_skeleton.c，按方案 D＋G 扩展为：
 * 单例上下文、轮询任务、去抖、事件队列、身份核对、EEPROM keymap、热插拔释放与自动重认领。
 *
 * 所有 BSP / 管理器 API 均在 esp-mosaico-bsp commit 392860b1 源码中核对（README.md「API 核实表」）：
 *   mosaico_module_mgr.h : _init:199  _subscribe:232  _unsubscribe:248  _get_info:261  _claim:281
 *                          _release:297  _slot_to_name:317  _type_to_name:325
 *   bsp/subboard.h       : bsp_subboard_map_gpio:98  BSP_SUBBOARD_ADDR_GPIO_LEFT:36
 *   bsp/esp_mosaico.h    : BSP_SUBBOARD_I2C_SDA/SCL:74-75  BSP_AUDIO_I2S_*:109-113
 *
 * 管理器行为依据（review/chrome/D1-module-interface/BSP_AND_EEPROM.md §5，源码 mosaico_module_mgr.c）：
 *   - 拔出时管理器只把 presence 改 ABSENT、descriptor 改 UNKNOWN（L513-531），不自动销毁客户端或释放
 *     lease；客户端须自行停止外设并 release —— 本驱动在 detach_now() 完成。
 *   - 正常 claim 只检查 FREE + PRESENT + VALID + board_type 匹配（L994-1004），不比较 vendor_id /
 *     board_id；官方 joystick 模块同为 HANDLE 类型。hardware/eeprom/IDENTITY.md §2.4 要求本项目驱动
 *     claim 后立即 get_info 核对身份，不符则 release —— 本驱动在 try_attach() 完成。
 *   - 回调在管理器事件任务中、不持锁运行（dispatch_event L623-660）；unsubscribe 会等待正在执行的
 *     回调结束（L1100 附近）。因此 deinit 顺序为：unsubscribe → 停轮询任务 → 回收，回调不会向已删除任务发通知。
 *
 * EEPROM param_data v1（IDENTITY.md §8，分支 claude/design-d/eeprom）主机侧使用规则：
 *   1. param_data 是提示不是安全边界：只允许把 EEPROM 给出的 GPIO 配成输入＋内部上拉；
 *   2. KEYMAP_VALID=0 用静态表；=1 时校验 10 个值都在左槽 11 根可用 GPIO 内且互异，再采用；失败回退静态表；
 *   3. sw_version 主版本不等于期望值时不解释 param_data。
 */

#include "dock_handle.h"

#include <inttypes.h>
#include <string.h>

#include "bsp/esp_mosaico.h"
#include "bsp/subboard.h"
#include "dock_handle_pinmap.h"
#include "driver/gpio.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "mosaico_module_mgr.h"

static const char *TAG = "dock_handle";

/* ---------------------------------------------------------------------------
 * 编译期约束：KEY_* GPIO 互不重复，且不落在禁用引脚上。
 * ------------------------------------------------------------------------- */

#define DOCK_GPIO_BIT(g) (1ULL << (unsigned)(g))

#define DOCK_HANDLE_ALL_KEY_MASK (                 \
    DOCK_GPIO_BIT(DOCK_HANDLE_GPIO_KEY_UP)    |    \
    DOCK_GPIO_BIT(DOCK_HANDLE_GPIO_KEY_DOWN)  |    \
    DOCK_GPIO_BIT(DOCK_HANDLE_GPIO_KEY_LEFT)  |    \
    DOCK_GPIO_BIT(DOCK_HANDLE_GPIO_KEY_RIGHT) |    \
    DOCK_GPIO_BIT(DOCK_HANDLE_GPIO_KEY_A)     |    \
    DOCK_GPIO_BIT(DOCK_HANDLE_GPIO_KEY_B)     |    \
    DOCK_GPIO_BIT(DOCK_HANDLE_GPIO_KEY_X)     |    \
    DOCK_GPIO_BIT(DOCK_HANDLE_GPIO_KEY_Y)     |    \
    DOCK_GPIO_BIT(DOCK_HANDLE_GPIO_KEY_L)     |    \
    DOCK_GPIO_BIT(DOCK_HANDLE_GPIO_KEY_R))

/* USB Serial/JTAG 在左槽 H2 pin13/15（LEFT_SLOT.md），BSP 无对应宏，此处按 D1 合同写死。 */
#define DOCK_HANDLE_USJ_DN_GPIO GPIO_NUM_33
#define DOCK_HANDLE_USJ_DP_GPIO GPIO_NUM_34

#define DOCK_HANDLE_FORBIDDEN_MASK (               \
    DOCK_GPIO_BIT(BSP_SUBBOARD_ADDR_GPIO_LEFT) |   \
    DOCK_GPIO_BIT(BSP_SUBBOARD_I2C_SDA)        |   \
    DOCK_GPIO_BIT(BSP_SUBBOARD_I2C_SCL)        |   \
    DOCK_GPIO_BIT(DOCK_HANDLE_USJ_DN_GPIO)     |   \
    DOCK_GPIO_BIT(DOCK_HANDLE_USJ_DP_GPIO)     |   \
    DOCK_GPIO_BIT(BSP_AUDIO_I2S_MCLK)          |   \
    DOCK_GPIO_BIT(BSP_AUDIO_I2S_SCLK)          |   \
    DOCK_GPIO_BIT(BSP_AUDIO_I2S_LRCLK)         |   \
    DOCK_GPIO_BIT(BSP_AUDIO_I2S_SDOUT)         |   \
    DOCK_GPIO_BIT(BSP_AUDIO_I2S_DSIN))

_Static_assert(__builtin_popcountll(DOCK_HANDLE_ALL_KEY_MASK) == DOCK_HANDLE_KEY_COUNT,
               "KEY_* GPIO assignment contains duplicates (check dock_handle_pinmap.h)");
_Static_assert((DOCK_HANDLE_ALL_KEY_MASK & DOCK_HANDLE_FORBIDDEN_MASK) == 0,
               "KEY_* GPIO collides with EEPROM A0 / I2C1 / USJ / onboard I2S (check dock_handle_pinmap.h)");
_Static_assert((DOCK_HANDLE_ALL_KEY_MASK & DOCK_GPIO_BIT(DOCK_HANDLE_GPIO_SPARE)) == 0,
               "spare GPIO must not be assigned to a key");
_Static_assert(DOCK_HANDLE_KEY_COUNT <= 32, "state bitmap is 32 bits wide");

/* ---------------------------------------------------------------------------
 * 键表：左槽规范 GPIO（PINMAP 宏表）与网络名。
 * ------------------------------------------------------------------------- */

typedef struct {
    gpio_num_t left_gpio;
    const char *name;
} key_def_t;

static const key_def_t k_keys[DOCK_HANDLE_KEY_COUNT] = {
    [DOCK_HANDLE_KEY_UP]    = {DOCK_HANDLE_GPIO_KEY_UP,    "KEY_UP"},
    [DOCK_HANDLE_KEY_DOWN]  = {DOCK_HANDLE_GPIO_KEY_DOWN,  "KEY_DOWN"},
    [DOCK_HANDLE_KEY_LEFT]  = {DOCK_HANDLE_GPIO_KEY_LEFT,  "KEY_LEFT"},
    [DOCK_HANDLE_KEY_RIGHT] = {DOCK_HANDLE_GPIO_KEY_RIGHT, "KEY_RIGHT"},
    [DOCK_HANDLE_KEY_A]     = {DOCK_HANDLE_GPIO_KEY_A,     "KEY_A"},
    [DOCK_HANDLE_KEY_B]     = {DOCK_HANDLE_GPIO_KEY_B,     "KEY_B"},
    [DOCK_HANDLE_KEY_X]     = {DOCK_HANDLE_GPIO_KEY_X,     "KEY_X"},
    [DOCK_HANDLE_KEY_Y]     = {DOCK_HANDLE_GPIO_KEY_Y,     "KEY_Y"},
    [DOCK_HANDLE_KEY_L]     = {DOCK_HANDLE_GPIO_KEY_L,     "KEY_L"},
    [DOCK_HANDLE_KEY_R]     = {DOCK_HANDLE_GPIO_KEY_R,     "KEY_R"},
};

/* EEPROM keymap 允许的 GPIO 全集（左槽 11 根可用 GPIO，不含 GPIO14）。 */
static const gpio_num_t k_allowed_key_gpio[] = { DOCK_HANDLE_ALLOWED_KEY_GPIO_LIST };

/* ---------------------------------------------------------------------------
 * EEPROM param_data v1 布局（IDENTITY.md §8；绝对偏移 = 0x44 + 区内偏移）。BSP 不解释这些字节。
 * ------------------------------------------------------------------------- */

#define PARAM_V1_VERSION            0x0001U
#define PARAM_V1_MIN_LENGTH         0x18U
#define PARAM_V1_OFF_KEY_COUNT      0x00U
#define PARAM_V1_OFF_KEY_FLAGS      0x01U
#define PARAM_V1_OFF_POLL_MS        0x02U
#define PARAM_V1_OFF_DEBOUNCE       0x03U
#define PARAM_V1_OFF_KEY_GPIO       0x04U   /* 10 字节，顺序 UP DOWN LEFT RIGHT A B X Y L R */
#define PARAM_V1_OFF_SPARE_GPIO     0x0EU
#define PARAM_V1_OFF_DOCK_FEATURES  0x12U   /* uint16 LE */
#define PARAM_V1_KEY_FLAG_ACTIVE_LOW    (1U << 0)
#define PARAM_V1_KEY_FLAG_KEYMAP_VALID  (1U << 1)
#define PARAM_V1_GPIO_UNASSIGNED    0xFFU

/* ---------------------------------------------------------------------------
 * 运行时上下文（单例）。
 * ------------------------------------------------------------------------- */

#define NOTIFY_SLOT_CHANGED   (1U << 0)
#define NOTIFY_DETACH         (1U << 1)
#define NOTIFY_STOP           (1U << 2)

#define WAITING_RETRY_MS      1000U   /* 等待态兜底轮询周期：即使错过事件也会重查槽位 */
#define DEINIT_TIMEOUT_MS     2000U
#define POLL_PERIOD_MIN_MS    20U
#define POLL_PERIOD_MAX_MS    40U
#define DEBOUNCE_MIN          2U
#define QUEUE_LEN_MIN         4U

typedef struct {
    bool initialized;
    dock_handle_config_t cfg;
    mosaico_module_lease_t lease;
    mosaico_module_subscription_t subscription;
    bool subscribed;
    QueueHandle_t queue;
    SemaphoreHandle_t done_sem;      /* 轮询任务退出时 give */
    SemaphoreHandle_t attached_sem;  /* 首次进入 ATTACHED 时 give，供 init 等待 */
    TaskHandle_t task;
    gpio_num_t io[DOCK_HANDLE_KEY_COUNT];
    uint8_t integrator[DOCK_HANDLE_KEY_COUNT];
    bool stable[DOCK_HANDLE_KEY_COUNT];
    volatile uint32_t state_bits;
    volatile dock_handle_link_t link;
    volatile dock_handle_keymap_source_t keymap_source;
    volatile bool stop;
    volatile bool detach_pending;
    volatile uint32_t dropped_events;
    uint32_t last_reject_generation;
    bool has_reject_generation;
} dock_ctx_t;

static dock_ctx_t s_dock;
static portMUX_TYPE s_dock_mux = portMUX_INITIALIZER_UNLOCKED;

/* ---------------------------------------------------------------------------
 * 小工具
 * ------------------------------------------------------------------------- */

const char *dock_handle_key_name(dock_handle_key_t key)
{
    if ((unsigned)key >= DOCK_HANDLE_KEY_COUNT) {
        return "KEY_?";
    }
    return k_keys[key].name;
}

gpio_num_t dock_handle_key_gpio(dock_handle_key_t key)
{
    if ((unsigned)key >= DOCK_HANDLE_KEY_COUNT || s_dock.link != DOCK_HANDLE_LINK_ATTACHED) {
        return GPIO_NUM_NC;
    }
    return s_dock.io[key];
}

uint32_t dock_handle_get_state(void)
{
    return s_dock.link == DOCK_HANDLE_LINK_ATTACHED ? s_dock.state_bits : 0U;
}

dock_handle_link_t dock_handle_get_link(void)
{
    return s_dock.initialized ? s_dock.link : DOCK_HANDLE_LINK_STOPPED;
}

bool dock_handle_is_attached(void)
{
    return s_dock.initialized && s_dock.link == DOCK_HANDLE_LINK_ATTACHED;
}

dock_handle_keymap_source_t dock_handle_get_keymap_source(void)
{
    return s_dock.link == DOCK_HANDLE_LINK_ATTACHED ? s_dock.keymap_source : DOCK_HANDLE_KEYMAP_NONE;
}

uint32_t dock_handle_get_dropped_events(void)
{
    return s_dock.dropped_events;
}

static void push_event(dock_handle_event_type_t type, dock_handle_key_t key, bool pressed, int64_t ts)
{
    if (!s_dock.queue) {
        return;
    }
    const dock_handle_event_t ev = {
        .type = type,
        .key = key,
        .pressed = pressed,
        .timestamp_us = ts,
    };
    if (xQueueSend(s_dock.queue, &ev, 0) != pdTRUE) {
        const uint32_t dropped = ++s_dock.dropped_events;
        if ((dropped & (dropped - 1U)) == 0U) { /* 1,2,4,8... 次时告警，避免刷屏 */
            ESP_LOGW(TAG, "event queue full, dropped=%" PRIu32 " (consumer too slow?)", dropped);
        }
    }
}

esp_err_t dock_handle_wait_event(dock_handle_event_t *out_event, uint32_t timeout_ms)
{
    ESP_RETURN_ON_FALSE(out_event, ESP_ERR_INVALID_ARG, TAG, "event output is null");
    ESP_RETURN_ON_FALSE(s_dock.initialized && s_dock.queue, ESP_ERR_INVALID_STATE, TAG,
                        "dock_handle is not initialized");
    const TickType_t ticks = timeout_ms == UINT32_MAX ? portMAX_DELAY : pdMS_TO_TICKS(timeout_ms);
    if (xQueueReceive(s_dock.queue, out_event, ticks) != pdTRUE) {
        return ESP_ERR_TIMEOUT;
    }
    return ESP_OK;
}

/* ---------------------------------------------------------------------------
 * 身份核对与 EEPROM keymap
 * ------------------------------------------------------------------------- */

static bool identity_ok(const mosaico_module_mgr_eeprom_v1_t *e)
{
    if (!s_dock.cfg.check_identity) {
        return true;
    }
    return e->vendor_id == s_dock.cfg.vendor_id &&
           e->board_id == s_dock.cfg.board_id &&
           (uint8_t)(e->sw_version >> 8) == s_dock.cfg.sw_version_major;
}

static void log_identity_reject_once(const mosaico_module_mgr_info_t *info)
{
    /* 同为 HANDLE 类型但身份不符（例如官方 joystick）：每个快照代只告警一次。 */
    if (s_dock.has_reject_generation && s_dock.last_reject_generation == info->generation) {
        return;
    }
    s_dock.has_reject_generation = true;
    s_dock.last_reject_generation = info->generation;
    ESP_LOGW(TAG, "slot %s: HANDLE board vendor=0x%04X board=0x%04X sw=0x%04X, expected 0x%04X/0x%04X/0x%02Xxx; not using",
             mosaico_module_mgr_slot_to_name(info->slot), info->eeprom.vendor_id, info->eeprom.board_id,
             info->eeprom.sw_version, s_dock.cfg.vendor_id, s_dock.cfg.board_id, s_dock.cfg.sw_version_major);
}

static bool gpio_allowed_for_key(uint8_t gpio)
{
    for (size_t i = 0; i < sizeof(k_allowed_key_gpio) / sizeof(k_allowed_key_gpio[0]); ++i) {
        if ((uint8_t)k_allowed_key_gpio[i] == gpio) {
            return true;
        }
    }
    return false;
}

/*
 * 解析 param_data v1，决定本次 ATTACHED 使用的左槽规范 GPIO 表。
 * 输出 out_left[]，返回来源。任何校验失败都回退静态表并打印原因。
 */
static dock_handle_keymap_source_t resolve_keymap(const mosaico_module_mgr_eeprom_v1_t *e,
                                                  gpio_num_t out_left[DOCK_HANDLE_KEY_COUNT])
{
    for (size_t i = 0; i < DOCK_HANDLE_KEY_COUNT; ++i) {
        out_left[i] = k_keys[i].left_gpio;
    }
    if (!s_dock.cfg.use_eeprom_keymap) {
        return DOCK_HANDLE_KEYMAP_STATIC;
    }
    if ((uint8_t)(e->sw_version >> 8) != s_dock.cfg.sw_version_major) {
        ESP_LOGW(TAG, "param_data ignored: sw_version 0x%04X major != 0x%02X (IDENTITY.md rule 3)",
                 e->sw_version, s_dock.cfg.sw_version_major);
        return DOCK_HANDLE_KEYMAP_STATIC;
    }
    if (e->param_version != PARAM_V1_VERSION || e->param_length < PARAM_V1_MIN_LENGTH ||
        e->param_length > sizeof(e->param_data)) {
        ESP_LOGW(TAG, "param_data ignored: version=0x%04X length=%u (expect v1, >= %u)",
                 e->param_version, (unsigned)e->param_length, (unsigned)PARAM_V1_MIN_LENGTH);
        return DOCK_HANDLE_KEYMAP_STATIC;
    }

    const uint8_t *p = e->param_data;
    const uint8_t key_count = p[PARAM_V1_OFF_KEY_COUNT];
    const uint8_t key_flags = p[PARAM_V1_OFF_KEY_FLAGS];
    const uint16_t dock_features = (uint16_t)(p[PARAM_V1_OFF_DOCK_FEATURES] |
                                              ((uint16_t)p[PARAM_V1_OFF_DOCK_FEATURES + 1U] << 8));
    ESP_LOGI(TAG, "param_data v1: key_count=%u flags=0x%02X poll_hint=%u ms debounce_hint=%u spare_gpio=0x%02X features=0x%04X",
             key_count, key_flags, p[PARAM_V1_OFF_POLL_MS], p[PARAM_V1_OFF_DEBOUNCE],
             p[PARAM_V1_OFF_SPARE_GPIO], dock_features);
    /* poll / debounce 只是提示；运行参数由应用配置并经 validate_config 检查，不在此覆盖。 */

    if ((key_flags & PARAM_V1_KEY_FLAG_ACTIVE_LOW) == 0U) {
        /* 硬约束 5：按键无源接地。EEPROM 声称高有效则与硬件合同矛盾，不采用其 keymap。 */
        ESP_LOGE(TAG, "param_data claims ACTIVE_HIGH keys; contradicts hard constraint 5, keymap ignored");
        return DOCK_HANDLE_KEYMAP_STATIC;
    }
    if ((key_flags & PARAM_V1_KEY_FLAG_KEYMAP_VALID) == 0U) {
        return DOCK_HANDLE_KEYMAP_STATIC;   /* IDENTITY.md 规则 2：KEYMAP_VALID=0 用静态表 */
    }
    if (key_count != DOCK_HANDLE_KEY_COUNT) {
        ESP_LOGW(TAG, "param_data key_count=%u != %u, keymap ignored", key_count, (unsigned)DOCK_HANDLE_KEY_COUNT);
        return DOCK_HANDLE_KEYMAP_STATIC;
    }

    gpio_num_t from_eeprom[DOCK_HANDLE_KEY_COUNT];
    for (size_t i = 0; i < DOCK_HANDLE_KEY_COUNT; ++i) {
        const uint8_t g = p[PARAM_V1_OFF_KEY_GPIO + i];
        if (g == PARAM_V1_GPIO_UNASSIGNED || !gpio_allowed_for_key(g)) {
            ESP_LOGW(TAG, "param_data key_gpio[%u]=0x%02X not in left-slot key GPIO set, keymap ignored",
                     (unsigned)i, g);
            return DOCK_HANDLE_KEYMAP_STATIC;
        }
        for (size_t j = 0; j < i; ++j) {
            if ((uint8_t)from_eeprom[j] == g) {
                ESP_LOGW(TAG, "param_data key_gpio[%u] duplicates key_gpio[%u] (GPIO%u), keymap ignored",
                         (unsigned)i, (unsigned)j, g);
                return DOCK_HANDLE_KEYMAP_STATIC;
            }
        }
        from_eeprom[i] = (gpio_num_t)g;
    }

    /* 校验通过：采用，并把与静态表的差异打出来 —— 这是到货时发现 PINMAP 与 EEPROM 不一致的主要手段。 */
    unsigned diffs = 0;
    for (size_t i = 0; i < DOCK_HANDLE_KEY_COUNT; ++i) {
        if (from_eeprom[i] != k_keys[i].left_gpio) {
            ESP_LOGW(TAG, "  %-9s EEPROM GPIO%d != static GPIO%d", k_keys[i].name, (int)from_eeprom[i],
                     (int)k_keys[i].left_gpio);
            ++diffs;
        }
        out_left[i] = from_eeprom[i];
    }
    if (diffs) {
        ESP_LOGW(TAG, "EEPROM keymap differs from dock_handle_pinmap.h in %u keys; using EEPROM. Reconcile PINMAP.md.", diffs);
    }
    return DOCK_HANDLE_KEYMAP_EEPROM;
}

/* ---------------------------------------------------------------------------
 * GPIO 配置与释放
 * ------------------------------------------------------------------------- */

static void release_key_gpios(void)
{
    for (size_t i = 0; i < DOCK_HANDLE_KEY_COUNT; ++i) {
        if (s_dock.io[i] != GPIO_NUM_NC) {
            (void)gpio_reset_pin(s_dock.io[i]);
            s_dock.io[i] = GPIO_NUM_NC;
        }
    }
}

static esp_err_t configure_key_gpios(const gpio_num_t left[DOCK_HANDLE_KEY_COUNT])
{
    uint64_t mask = 0;
    for (size_t i = 0; i < DOCK_HANDLE_KEY_COUNT; ++i) {
        /* 左槽原样返回（subboard.c:212-224）；右槽会镜像到与板载 I2S 冲突的 GPIO，已在 init 拒绝。 */
        s_dock.io[i] = bsp_subboard_map_gpio((bsp_subboard_slot_t)s_dock.cfg.slot, left[i]);
        (void)gpio_reset_pin(s_dock.io[i]);
        mask |= DOCK_GPIO_BIT(s_dock.io[i]);
    }
    /* 按键为无源开关接 DOCK_GND，拉高只来自主机内部上拉（3.3 V 域），按下读 0。
     * 这是本驱动对 KEY_* 引脚唯一允许的配置：输入＋上拉，禁中断（BSP 无中断通路），绝不配成输出。 */
    const gpio_config_t keys = {
        .pin_bit_mask = mask,
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    return gpio_config(&keys);
}

/* ---------------------------------------------------------------------------
 * 认领 / 去抖轮询 / 释放
 * ------------------------------------------------------------------------- */

static bool candidate_ok(const mosaico_module_mgr_info_t *info)
{
    if (info->presence != MOSAICO_MODULE_PRESENCE_PRESENT ||
        info->descriptor_state != MOSAICO_MODULE_DESCRIPTOR_VALID ||
        info->owner_state != MOSAICO_MODULE_OWNER_FREE) {
        return false;
    }
    if (info->eeprom.board_type != (uint8_t)MOSAICO_BOARD_TYPE_HANDLE) {
        return false;
    }
    if (!identity_ok(&info->eeprom)) {
        /* 认领前就拒绝：不抢官方 joystick 驱动的槽位，也不对它的 GPIO 做任何配置。 */
        log_identity_reject_once(info);
        return false;
    }
    return true;
}

static bool try_attach(void)
{
    mosaico_module_mgr_info_t info = {0};
    if (mosaico_module_mgr_get_info(s_dock.cfg.slot, &info) != ESP_OK) {
        return false;
    }
    if (!candidate_ok(&info)) {
        return false;
    }

    /* 普通模块不复用槽位控制 GPIO，flags = 0：管理器持续保持 EEPROM 选址电平，拔出探测照常。 */
    const mosaico_module_mgr_claim_config_t claim = {
        .expected_type = MOSAICO_BOARD_TYPE_HANDLE,
        .slot = s_dock.cfg.slot,
        .timeout_ms = 0,   /* 单次尝试；等待由本任务的事件通知完成 */
        .flags = 0,
    };
    mosaico_module_lease_t lease = {0};
    esp_err_t ret = mosaico_module_mgr_claim(&claim, &lease);
    if (ret != ESP_OK) {
        if (ret != ESP_ERR_NOT_FOUND) {
            ESP_LOGW(TAG, "claim %s failed: %s", mosaico_module_mgr_slot_to_name(s_dock.cfg.slot),
                     esp_err_to_name(ret));
        }
        return false;
    }

    /* IDENTITY.md §2.4：claim 成功后立即 get_info 重新核对（关闭 get_info 与 claim 之间的换板窗口）。 */
    if (mosaico_module_mgr_get_info(lease.slot, &info) != ESP_OK ||
        info.presence != MOSAICO_MODULE_PRESENCE_PRESENT ||
        info.descriptor_state != MOSAICO_MODULE_DESCRIPTOR_VALID ||
        info.eeprom.board_type != (uint8_t)MOSAICO_BOARD_TYPE_HANDLE ||
        !identity_ok(&info.eeprom)) {
        ESP_LOGW(TAG, "post-claim identity check failed on %s; releasing", mosaico_module_mgr_slot_to_name(lease.slot));
        (void)mosaico_module_mgr_release(&lease);
        return false;
    }

    gpio_num_t left[DOCK_HANDLE_KEY_COUNT];
    const dock_handle_keymap_source_t source = resolve_keymap(&info.eeprom, left);

    ret = configure_key_gpios(left);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "configure key GPIOs failed: %s", esp_err_to_name(ret));
        release_key_gpios();
        (void)mosaico_module_mgr_release(&lease);
        return false;
    }

    memset(s_dock.integrator, 0, sizeof(s_dock.integrator));
    memset(s_dock.stable, 0, sizeof(s_dock.stable));
    s_dock.state_bits = 0;
    s_dock.detach_pending = false;
    s_dock.lease = lease;
    s_dock.keymap_source = source;
    s_dock.link = DOCK_HANDLE_LINK_ATTACHED;

    ESP_LOGI(TAG, "attached: slot=%s eeprom=0x%02X type=%s vendor=0x%04X board=0x%04X hw=0x%04X sw=0x%04X name=\"%.32s\" keymap=%s",
             mosaico_module_mgr_slot_to_name(lease.slot), info.eeprom_addr,
             mosaico_module_mgr_type_to_name((mosaico_board_type_t)info.eeprom.board_type),
             info.eeprom.vendor_id, info.eeprom.board_id, info.eeprom.hw_version, info.eeprom.sw_version,
             info.eeprom.board_name, source == DOCK_HANDLE_KEYMAP_EEPROM ? "eeprom" : "static");
    for (size_t i = 0; i < DOCK_HANDLE_KEY_COUNT; ++i) {
        ESP_LOGI(TAG, "  %-9s -> GPIO%d", k_keys[i].name, (int)s_dock.io[i]);
    }

    push_event(DOCK_HANDLE_EVENT_ATTACHED, DOCK_HANDLE_KEY_COUNT, false, esp_timer_get_time());
    if (s_dock.attached_sem) {
        (void)xSemaphoreGive(s_dock.attached_sem);
    }
    return true;
}

static void poll_keys(void)
{
    const int64_t now = esp_timer_get_time();
    uint32_t bits = s_dock.state_bits;
    for (size_t i = 0; i < DOCK_HANDLE_KEY_COUNT; ++i) {
        const bool raw_pressed = gpio_get_level(s_dock.io[i]) == 0;
        if (raw_pressed == s_dock.stable[i]) {
            s_dock.integrator[i] = 0;
            continue;
        }
        if (++s_dock.integrator[i] < s_dock.cfg.debounce_count) {
            continue;
        }
        s_dock.integrator[i] = 0;
        s_dock.stable[i] = raw_pressed;
        if (raw_pressed) {
            bits |= (1U << i);
        } else {
            bits &= ~(1U << i);
        }
        push_event(DOCK_HANDLE_EVENT_KEY, (dock_handle_key_t)i, raw_pressed, now);
    }
    s_dock.state_bits = bits;
}

static void detach_now(const char *reason)
{
    const int64_t now = esp_timer_get_time();
    /* 先补发释放事件，消费者不会看到“永远按着”的键。 */
    for (size_t i = 0; i < DOCK_HANDLE_KEY_COUNT; ++i) {
        if (s_dock.stable[i]) {
            s_dock.stable[i] = false;
            push_event(DOCK_HANDLE_EVENT_KEY, (dock_handle_key_t)i, false, now);
        }
        s_dock.integrator[i] = 0;
    }
    s_dock.state_bits = 0;
    release_key_gpios();

    if (s_dock.lease.id != 0) {
        /* 拔出后 owner_state 仍为 CLAIMED、lease_id 不变（mosaico_module_mgr.c L513-531 不改 owner），
         * 因此 release 正常返回 ESP_OK 并触发重扫（L1135-1200）。 */
        const esp_err_t ret = mosaico_module_mgr_release(&s_dock.lease);
        if (ret != ESP_OK) {
            /* flags=0 时 release 不涉及 GPIO 恢复，失败只可能是管理器停止或 lease 已失效。 */
            ESP_LOGE(TAG, "release slot %s failed: %s", mosaico_module_mgr_slot_to_name(s_dock.lease.slot),
                     esp_err_to_name(ret));
        }
    }
    s_dock.lease = (mosaico_module_lease_t) {0};
    s_dock.detach_pending = false;
    s_dock.keymap_source = DOCK_HANDLE_KEYMAP_NONE;
    s_dock.link = DOCK_HANDLE_LINK_WAITING;
    ESP_LOGI(TAG, "detached (%s)", reason);
    push_event(DOCK_HANDLE_EVENT_DETACHED, DOCK_HANDLE_KEY_COUNT, false, now);
}

/* 管理器事件任务回调：只置标志并通知轮询任务，不在此做 I/O（mosaico_module_mgr.h:159-161 要求回调短）。 */
static void on_module_event(const mosaico_module_mgr_event_t *event, void *user_data)
{
    (void)user_data;
    if (!event || event->info.slot != s_dock.cfg.slot) {
        return;
    }
    uint32_t bits = NOTIFY_SLOT_CHANGED;
    if (s_dock.link == DOCK_HANDLE_LINK_ATTACHED &&
        (event->changes & MOSAICO_MODULE_CHANGE_PRESENCE) &&
        event->info.presence == MOSAICO_MODULE_PRESENCE_ABSENT) {
        s_dock.detach_pending = true;
        bits |= NOTIFY_DETACH;
    }
    TaskHandle_t task = s_dock.task;
    if (task) {
        (void)xTaskNotify(task, bits, eSetBits);
    }
}

static void dock_task(void *arg)
{
    (void)arg;
    TickType_t last_wake = xTaskGetTickCount();
    const TickType_t period = pdMS_TO_TICKS(s_dock.cfg.poll_period_ms);

    while (!s_dock.stop) {
        if (s_dock.link != DOCK_HANDLE_LINK_ATTACHED) {
            if (!try_attach()) {
                uint32_t bits = 0;
                (void)xTaskNotifyWait(0, UINT32_MAX, &bits, pdMS_TO_TICKS(WAITING_RETRY_MS));
            }
            last_wake = xTaskGetTickCount();
            continue;
        }

        (void)xTaskDelayUntil(&last_wake, period);
        if (s_dock.stop) {
            break;
        }
        if (s_dock.detach_pending) {
            detach_now("module unplugged");
            if (!s_dock.cfg.auto_reattach) {
                ESP_LOGW(TAG, "auto_reattach disabled; driver stopped, call dock_handle_deinit()/init() to restart");
                break;
            }
            continue;
        }
        poll_keys();
    }

    if (s_dock.link == DOCK_HANDLE_LINK_ATTACHED) {
        detach_now("driver stopped");
    }
    s_dock.link = DOCK_HANDLE_LINK_STOPPED;
    (void)xSemaphoreGive(s_dock.done_sem);
    /* 不自删：句柄保持有效直到 dock_handle_deinit() 删除本任务。 */
    for (;;) {
        vTaskSuspend(NULL);
    }
}

/* ---------------------------------------------------------------------------
 * 生命周期
 * ------------------------------------------------------------------------- */

static void unsubscribe_if_needed(void)
{
    if (s_dock.subscribed) {
        /* 会等待正在执行的回调返回（mosaico_module_mgr.c unsubscribe 实现），之后回调不再触发。 */
        (void)mosaico_module_mgr_unsubscribe(&s_dock.subscription);
        s_dock.subscribed = false;
    }
}

static void teardown(void)
{
    unsubscribe_if_needed();
    if (s_dock.queue) {
        vQueueDelete(s_dock.queue);
    }
    if (s_dock.done_sem) {
        vSemaphoreDelete(s_dock.done_sem);
    }
    if (s_dock.attached_sem) {
        vSemaphoreDelete(s_dock.attached_sem);
    }
    memset(&s_dock, 0, sizeof(s_dock));
    for (size_t i = 0; i < DOCK_HANDLE_KEY_COUNT; ++i) {
        s_dock.io[i] = GPIO_NUM_NC;
    }
}

static esp_err_t stop_task(void)
{
    if (!s_dock.task) {
        return ESP_OK;
    }
    /* 先取消订阅，保证之后没有回调会再向本任务发通知；再让任务退出。 */
    unsubscribe_if_needed();
    s_dock.stop = true;
    (void)xTaskNotify(s_dock.task, NOTIFY_STOP, eSetBits);
    if (xSemaphoreTake(s_dock.done_sem, pdMS_TO_TICKS(DEINIT_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "poll task did not stop within %u ms", (unsigned)DEINIT_TIMEOUT_MS);
        return ESP_ERR_TIMEOUT;
    }
    /* 任务已 give done_sem 并进入 vTaskSuspend，此时删除是安全的。 */
    vTaskDelete(s_dock.task);
    s_dock.task = NULL;
    return ESP_OK;
}

static esp_err_t validate_config(dock_handle_config_t *cfg)
{
    if (cfg->slot == MOSAICO_MODULE_MGR_SLOT_AUTO) {
        ESP_LOGI(TAG, "slot AUTO requested; design D uses the left slot only, using LEFT");
        cfg->slot = MOSAICO_MODULE_MGR_SLOT_LEFT;
    }
    ESP_RETURN_ON_FALSE(cfg->slot != MOSAICO_MODULE_MGR_SLOT_RIGHT, ESP_ERR_NOT_SUPPORTED, TAG,
                        "right slot mirrors KEY_* onto onboard I2S GPIOs (40/37/54/52/49); not supported");
    ESP_RETURN_ON_FALSE(cfg->slot == MOSAICO_MODULE_MGR_SLOT_LEFT, ESP_ERR_INVALID_ARG, TAG, "invalid slot");
    ESP_RETURN_ON_FALSE(cfg->poll_period_ms >= POLL_PERIOD_MIN_MS && cfg->poll_period_ms <= POLL_PERIOD_MAX_MS,
                        ESP_ERR_INVALID_ARG, TAG, "poll_period_ms must be within %u..%u",
                        (unsigned)POLL_PERIOD_MIN_MS, (unsigned)POLL_PERIOD_MAX_MS);
    ESP_RETURN_ON_FALSE(cfg->debounce_count >= DEBOUNCE_MIN, ESP_ERR_INVALID_ARG, TAG,
                        "debounce_count must be >= %u", (unsigned)DEBOUNCE_MIN);
    ESP_RETURN_ON_FALSE(cfg->event_queue_len >= QUEUE_LEN_MIN, ESP_ERR_INVALID_ARG, TAG,
                        "event_queue_len must be >= %u", (unsigned)QUEUE_LEN_MIN);
    return ESP_OK;
}

esp_err_t dock_handle_init_with_config(const dock_handle_config_t *config)
{
    dock_handle_config_t cfg = config ? *config : (dock_handle_config_t)DOCK_HANDLE_DEFAULT_CONFIG();
    ESP_RETURN_ON_ERROR(validate_config(&cfg), TAG, "invalid dock_handle configuration");

    portENTER_CRITICAL(&s_dock_mux);
    const bool already = s_dock.initialized;
    if (!already) {
        s_dock.initialized = true;
    }
    portEXIT_CRITICAL(&s_dock_mux);
    ESP_RETURN_ON_FALSE(!already, ESP_ERR_INVALID_STATE, TAG, "dock_handle already initialized");

    s_dock.cfg = cfg;
    s_dock.link = DOCK_HANDLE_LINK_WAITING;
    s_dock.keymap_source = DOCK_HANDLE_KEYMAP_NONE;
    for (size_t i = 0; i < DOCK_HANDLE_KEY_COUNT; ++i) {
        s_dock.io[i] = GPIO_NUM_NC;
    }

    /* 与官方模块驱动一致：由驱动自行启动管理器；已运行时幂等（mosaico_module_mgr.h:184-186）。
     * 管理器内部 bsp_subboard_init() 会先打开模块 VCC_3V3，再初始化 I2C1，再设 GPIO14=0（subboard.c:122-141）。
     * 本驱动不触碰 GPIO60 / pin17 / pin18 供电（硬约束 1、2）。 */
    esp_err_t ret = mosaico_module_mgr_init(NULL);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "mosaico_module_mgr_init failed: %s", esp_err_to_name(ret));
        teardown();
        return ret;
    }

    s_dock.queue = xQueueCreate(cfg.event_queue_len, sizeof(dock_handle_event_t));
    s_dock.done_sem = xSemaphoreCreateBinary();
    s_dock.attached_sem = xSemaphoreCreateBinary();
    if (!s_dock.queue || !s_dock.done_sem || !s_dock.attached_sem) {
        teardown();
        return ESP_ERR_NO_MEM;
    }

    if (xTaskCreate(dock_task, "dock_handle", CONFIG_DOCK_HANDLE_TASK_STACK_SIZE, NULL,
                    CONFIG_DOCK_HANDLE_TASK_PRIORITY, &s_dock.task) != pdPASS) {
        teardown();
        return ESP_ERR_NO_MEM;
    }

    ret = mosaico_module_mgr_subscribe(on_module_event, NULL, &s_dock.subscription);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "mosaico_module_mgr_subscribe failed: %s", esp_err_to_name(ret));
        (void)stop_task();
        teardown();
        return ret;
    }
    s_dock.subscribed = true;

    if (s_dock.link != DOCK_HANDLE_LINK_ATTACHED) {
        (void)xSemaphoreTake(s_dock.attached_sem, pdMS_TO_TICKS(cfg.claim_timeout_ms));
    }
    if (s_dock.link == DOCK_HANDLE_LINK_ATTACHED) {
        return ESP_OK;
    }
    if (cfg.auto_reattach) {
        ESP_LOGW(TAG, "no HANDLE module claimed within %" PRIu32 " ms; waiting in background",
                 cfg.claim_timeout_ms);
        return ESP_ERR_TIMEOUT;
    }
    ESP_LOGE(TAG, "no HANDLE module claimed within %" PRIu32 " ms", cfg.claim_timeout_ms);
    (void)stop_task();
    teardown();
    return ESP_ERR_TIMEOUT;
}

esp_err_t dock_handle_init(mosaico_module_mgr_slot_t slot)
{
    dock_handle_config_t cfg = DOCK_HANDLE_DEFAULT_CONFIG();
    cfg.slot = slot;
    return dock_handle_init_with_config(&cfg);
}

esp_err_t dock_handle_deinit(void)
{
    ESP_RETURN_ON_FALSE(s_dock.initialized, ESP_ERR_INVALID_STATE, TAG, "dock_handle is not initialized");
    const esp_err_t ret = stop_task();   /* 内部先 unsubscribe，再停任务 */
    if (ret != ESP_OK) {
        return ret;
    }
    teardown();
    ESP_LOGI(TAG, "deinitialized");
    return ESP_OK;
}
