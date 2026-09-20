/*
 * 提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
 *
 * keytest：读 eFuse 板版本 -> 初始化 BSP 电源 ->（可选）点亮屏幕 -> 启动模块管理器
 *          ->（可选）只读 I2C1 地址扫描 -> 打印两槽扫描结果与 EEPROM 描述字段
 *          -> 认领底座手柄 -> 打印每个按键事件与位图。
 *
 * 对应 hardware/ICD-0.2-DRAFT.md 第 8 节「最小测试固件须提供」：
 *   ① 槽扫描/身份读出：本例打印 presence、descriptor 状态、解码后的全部描述字段与 param_data 前 24 字节。
 *      管理器 API 不暴露 134 字节原始镜像与三段 CRC 值（只给 VALID/INVALID），原始镜像转储
 *      由 eeprom 分支 hardware/eeprom/eeprom_program_example.c 覆盖，本例不重复实现（见 README 已知限制）。
 *   ② 十键自检：逐键打印按下/释放与时间戳，位图支持多键同时。
 *   ③ 只读 I2C 地址扫描：i2c_master_probe() 只发地址字节看 ACK，不写任何地址。
 *
 * 引用的 BSP API 均在 esp-mosaico-bsp commit 392860b1 中核对（README「API 核实表」）：
 *   bsp_board_variant_get（bsp/esp_mosaico.h:43，实现 esp_mosaico.c:62）
 *   bsp_power_init（bsp/power.h:16，实现 esp_mosaico.c:143）
 *   bsp_subboard_get_i2c_bus（bsp/subboard.h:65，实现 subboard.c:154）
 *   bsp_display_start / bsp_display_lock / bsp_display_unlock（bsp/display.h:84,157,158）
 *   mosaico_module_mgr_init / subscribe / get_info / slot_to_name / type_to_name（mosaico_module_mgr.h）
 *   i2c_master_probe（ESP-IDF driver/i2c_master.h；管理器自身也用它探测 EEPROM，mosaico_module_mgr.c:481）
 * LVGL 调用只使用官方示例 examples/module_slot_scan 已使用的函数集：lv_screen_active、lv_label_create、
 *   lv_label_set_text、lv_obj_center、lv_obj_set_style_bg_color、lv_obj_set_style_bg_opa、
 *   lv_obj_set_style_text_color、lv_obj_set_style_text_font、lv_color_hex、lv_font_montserrat_20、LV_OPA_COVER。
 */

#include <inttypes.h>
#include <stdio.h>
#include <string.h>

#include "bsp/esp_mosaico.h"
#include "dock_handle.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "mosaico_module_mgr.h"
#include "sdkconfig.h"

#if CONFIG_KEYTEST_I2C_SCAN
#include "driver/i2c_master.h"
#endif
#if CONFIG_KEYTEST_USE_DISPLAY
#include "lvgl.h"
#endif

static const char *TAG = "keytest";

/* ------------------------------------------------------------------------- */
/* 可选屏幕显示：一个居中标签，两行文本（连接状态 / 当前按下的键）                */
/* ------------------------------------------------------------------------- */

#if CONFIG_KEYTEST_USE_DISPLAY
static lv_obj_t *s_label;

static void ui_init(void)
{
    lv_display_t *display = bsp_display_start();
    if (!display) {
        ESP_LOGW(TAG, "bsp_display_start failed; console only");
        return;
    }
    if (!bsp_display_lock(-1)) {
        return;
    }
    lv_obj_t *screen = lv_screen_active();
    lv_obj_set_style_bg_color(screen, lv_color_hex(0x101418), 0);
    lv_obj_set_style_bg_opa(screen, LV_OPA_COVER, 0);

    s_label = lv_label_create(screen);
    lv_obj_set_style_text_color(s_label, lv_color_hex(0xE6E6E6), 0);
    lv_obj_set_style_text_font(s_label, &lv_font_montserrat_20, 0);
    lv_label_set_text(s_label, "dock_handle: waiting\n-");
    lv_obj_center(s_label);
    bsp_display_unlock();
}

static void ui_update(void)
{
    if (!s_label) {
        return;
    }
    char text[32 + DOCK_HANDLE_KEY_COUNT * 8] = {0};
    const char *link;
    switch (dock_handle_get_link()) {
    case DOCK_HANDLE_LINK_ATTACHED: link = "attached"; break;
    case DOCK_HANDLE_LINK_WAITING:  link = "waiting";  break;
    default:                        link = "stopped";  break;
    }
    int n = snprintf(text, sizeof(text), "dock_handle: %s\n", link);
    const uint32_t state = dock_handle_get_state();
    bool any = false;
    for (int i = 0; i < DOCK_HANDLE_KEY_COUNT && n > 0 && (size_t)n < sizeof(text); ++i) {
        if (state & (1U << i)) {
            /* 去掉 "KEY_" 前缀，屏幕上只显示 UP / A / L 等。 */
            n += snprintf(text + n, sizeof(text) - (size_t)n, "%s ", dock_handle_key_name((dock_handle_key_t)i) + 4);
            any = true;
        }
    }
    if (!any && n > 0 && (size_t)n < sizeof(text)) {
        snprintf(text + n, sizeof(text) - (size_t)n, "-");
    }
    if (!bsp_display_lock(50)) {
        return;
    }
    lv_label_set_text(s_label, text);
    bsp_display_unlock();
}
#else
static void ui_init(void) {}
static void ui_update(void) {}
#endif

/* ------------------------------------------------------------------------- */
/* ③ 只读 I2C1 地址扫描（G6-C；硬约束 6 / ICD EL-D-06）                          */
/* ------------------------------------------------------------------------- */

#if CONFIG_KEYTEST_I2C_SCAN
#define I2C_SCAN_FIRST_ADDR   0x08U   /* 0x00-0x07 为 I2C 规范保留 */
#define I2C_SCAN_LAST_ADDR    0x77U   /* 0x78-0x7F 为 I2C 规范保留 */
#define I2C_SCAN_TIMEOUT_MS   20

static void scan_i2c_bus(void)
{
    i2c_master_bus_handle_t bus = bsp_subboard_get_i2c_bus();
    if (!bus) {
        ESP_LOGW(TAG, "I2C scan skipped: subboard bus not initialized");
        return;
    }
    ESP_LOGI(TAG, "I2C1 read-only scan 0x%02X..0x%02X (module bus SDA=GPIO%d SCL=GPIO%d)",
             I2C_SCAN_FIRST_ADDR, I2C_SCAN_LAST_ADDR, (int)BSP_SUBBOARD_I2C_SDA, (int)BSP_SUBBOARD_I2C_SCL);
    unsigned found = 0;
    unsigned unexpected = 0;
    for (unsigned addr = I2C_SCAN_FIRST_ADDR; addr <= I2C_SCAN_LAST_ADDR; ++addr) {
        const esp_err_t ret = i2c_master_probe(bus, (uint16_t)addr, I2C_SCAN_TIMEOUT_MS);
        if (ret == ESP_OK) {
            ++found;
            if (addr == BSP_SUBBOARD_EEPROM_ADDR_LEFT) {
                ESP_LOGI(TAG, "  ACK 0x%02X  left slot EEPROM (AT24C02, A0=GPIO14=0)", addr);
            } else if (addr == BSP_SUBBOARD_EEPROM_ADDR_RIGHT) {
                ESP_LOGI(TAG, "  ACK 0x%02X  right slot EEPROM (A0=GPIO39=1); design D expects the right slot empty (AS-21)", addr);
            } else {
                ++unexpected;
                ESP_LOGW(TAG, "  ACK 0x%02X  UNEXPECTED device on module I2C1 (hard constraint 6 / EL-D-06)", addr);
            }
        } else if (ret != ESP_ERR_NOT_FOUND) {
            ESP_LOGW(TAG, "  probe 0x%02X error: %s", addr, esp_err_to_name(ret));
        }
    }
    ESP_LOGI(TAG, "I2C1 scan done: %u device(s), %u unexpected", found, unexpected);
}
#else
static void scan_i2c_bus(void) {}
#endif

/* ------------------------------------------------------------------------- */
/* ① 两槽扫描日志与 EEPROM 描述字段（与 module_slot_scan 同源的判定逻辑）        */
/* ------------------------------------------------------------------------- */

static void log_slot_info(const mosaico_module_mgr_info_t *info)
{
    const char *presence = info->presence == MOSAICO_MODULE_PRESENCE_PRESENT ? "PRESENT"
                           : info->presence == MOSAICO_MODULE_PRESENCE_ABSENT ? "ABSENT" : "UNKNOWN";
    const char *descriptor = info->descriptor_state == MOSAICO_MODULE_DESCRIPTOR_VALID ? "VALID"
                             : info->descriptor_state == MOSAICO_MODULE_DESCRIPTOR_INVALID ? "INVALID" : "UNKNOWN";
    const char *owner = info->owner_state == MOSAICO_MODULE_OWNER_FREE ? "FREE"
                        : info->owner_state == MOSAICO_MODULE_OWNER_CLAIMED ? "CLAIMED" : "RESTORING";

    ESP_LOGI(TAG, "slot %-5s addr=0x%02X %s descriptor=%s owner=%s gen=%" PRIu32 " last_error=%s",
             mosaico_module_mgr_slot_to_name(info->slot), info->eeprom_addr, presence, descriptor, owner,
             info->generation, esp_err_to_name(info->last_error));
    if (info->descriptor_state != MOSAICO_MODULE_DESCRIPTOR_VALID) {
        return;
    }
    const mosaico_module_mgr_eeprom_v1_t *e = &info->eeprom;
    ESP_LOGI(TAG, "  type=%s(0x%02X) board_id=0x%04X vendor_id=0x%04X hw=0x%04X sw=0x%04X flags=0x%08" PRIX32
             " serial=0x%08" PRIX32 " name=\"%.32s\"",
             mosaico_module_mgr_type_to_name((mosaico_board_type_t)e->board_type), e->board_type,
             e->board_id, e->vendor_id, e->hw_version, e->sw_version, e->board_flags, e->serial_number,
             e->board_name);
    ESP_LOGI(TAG, "  mfg: date=0x%08" PRIX32 " batch=0x%04X factory=0x%04X; param: version=0x%04X length=%u",
             e->manufacture_date, e->batch_number, e->factory_id, e->param_version, (unsigned)e->param_length);
    /* param_data v1 前 24 字节（IDENTITY.md 第 8 节布局）；十六进制原样打印，解释交给 dock_handle。 */
    char hex[24 * 3 + 1] = {0};
    for (unsigned i = 0; i < 24U; ++i) {
        snprintf(hex + i * 3U, sizeof(hex) - i * 3U, "%02X ", e->param_data[i]);
    }
    ESP_LOGI(TAG, "  param_data[0..23]: %s", hex);
}

static void on_module_event(const mosaico_module_mgr_event_t *event, void *user_data)
{
    (void)user_data;
    if (event && (event->changes & (MOSAICO_MODULE_CHANGE_PRESENCE | MOSAICO_MODULE_CHANGE_DESCRIPTOR |
                                    MOSAICO_MODULE_CHANGE_ERROR))) {
        log_slot_info(&event->info);
    }
}

/* ------------------------------------------------------------------------- */
/* ② 按键事件                                                                  */
/* ------------------------------------------------------------------------- */

static void handle_event(const dock_handle_event_t *ev)
{
    switch (ev->type) {
    case DOCK_HANDLE_EVENT_KEY:
        ESP_LOGI(TAG, "%-9s %s  t=%" PRId64 " ms  state=0x%03" PRIX32,
                 dock_handle_key_name(ev->key), ev->pressed ? "DOWN" : "UP  ",
                 ev->timestamp_us / 1000, dock_handle_get_state());
        break;
    case DOCK_HANDLE_EVENT_ATTACHED:
        ESP_LOGI(TAG, "dock attached; keymap source=%s; KEY_* -> GPIO:",
                 dock_handle_get_keymap_source() == DOCK_HANDLE_KEYMAP_EEPROM ? "eeprom param_data v1"
                                                                              : "static dock_handle_pinmap.h");
        for (int i = 0; i < DOCK_HANDLE_KEY_COUNT; ++i) {
            ESP_LOGI(TAG, "  %-9s GPIO%d", dock_handle_key_name((dock_handle_key_t)i),
                     (int)dock_handle_key_gpio((dock_handle_key_t)i));
        }
        break;
    case DOCK_HANDLE_EVENT_DETACHED:
        ESP_LOGW(TAG, "dock detached");
        break;
    default:
        break;
    }
    ui_update();
}

void app_main(void)
{
    /* 项目主循环第 ② 步「读 eFuse」：BSP 从 eFuse USER_DATA 读硬件版本（esp_mosaico.c:40-60），
     * v1.0 -> V1_0，v1.1/v1.2 -> V1_2，其他值返回 ESP_ERR_NOT_SUPPORTED；未编程时 efuse 读回 0 亦属其他值。
     * 此时 bsp_subboard_init 也无法工作，直接停止并把原因打出来，供 AS-16 / AS-28 登记。 */
    bsp_board_variant_t variant = BSP_BOARD_VARIANT_V1_0;
    esp_err_t ret = bsp_board_variant_get(&variant);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "bsp_board_variant_get failed: %s (eFuse USER_DATA unprogrammed or unsupported); stop",
                 esp_err_to_name(ret));
        return;
    }
    ESP_LOGI(TAG, "board variant: %s", variant == BSP_BOARD_VARIANT_V1_2 ? "V1.2 (v1.1 uses the same mapping)" : "V1.0");
    if (variant != BSP_BOARD_VARIANT_V1_2) {
        ESP_LOGW(TAG, "design D targets BaseBoard V1.2 (dedicated module I2C1); V1.0 is not covered by the pin contract");
    }

    ESP_ERROR_CHECK(bsp_power_init());
    ui_init();

    /* 先起管理器（内部 bsp_subboard_init：开模块 3.3V -> I2C1 -> GPIO14=0），才有总线可扫、才能看到
     * 手柄模块被识别为 Handle(0x04) 的过程。 */
    ESP_ERROR_CHECK(mosaico_module_mgr_init(NULL));
    scan_i2c_bus();

    mosaico_module_subscription_t subscription = {0};
    ESP_ERROR_CHECK(mosaico_module_mgr_subscribe(on_module_event, NULL, &subscription));
    for (mosaico_module_mgr_slot_t slot = MOSAICO_MODULE_MGR_SLOT_LEFT; slot < MOSAICO_MODULE_MGR_SLOT_COUNT; ++slot) {
        mosaico_module_mgr_info_t info = {0};
        if (mosaico_module_mgr_get_info(slot, &info) == ESP_OK) {
            log_slot_info(&info);
        }
    }

    ret = dock_handle_init(MOSAICO_MODULE_MGR_SLOT_LEFT);
    if (ret == ESP_ERR_TIMEOUT) {
        ESP_LOGW(TAG, "no dock handle claimed yet; plug the module, the driver keeps waiting");
    } else {
        ESP_ERROR_CHECK(ret);
    }
    ui_update();

    int64_t last_heartbeat = esp_timer_get_time();
    const int64_t heartbeat_us = (int64_t)CONFIG_KEYTEST_HEARTBEAT_S * 1000000LL;
    for (;;) {
        dock_handle_event_t ev;
        if (dock_handle_wait_event(&ev, 200) == ESP_OK) {
            handle_event(&ev);
        }
        const int64_t now = esp_timer_get_time();
        if (now - last_heartbeat >= heartbeat_us) {
            last_heartbeat = now;
            ESP_LOGI(TAG, "heartbeat link=%d state=0x%03" PRIX32 " dropped=%" PRIu32,
                     (int)dock_handle_get_link(), dock_handle_get_state(), dock_handle_get_dropped_events());
        }
    }
}
