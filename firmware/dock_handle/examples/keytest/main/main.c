/*
 * 提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
 *
 * keytest：读 eFuse 板版本 -> 初始化 BSP 电源 ->（可选）点亮屏幕 -> 启动模块管理器并打印两槽扫描结果
 *          -> 认领底座手柄 -> 打印每个按键事件与位图。
 *
 * 引用的 BSP API 均在 esp-mosaico-bsp commit 392860b1 中核对：
 *   bsp_board_variant_get（bsp/esp_mosaico.h）、bsp_power_init（bsp/power.h，esp_mosaico.c:143）、
 *   bsp_display_start / bsp_display_lock / bsp_display_unlock（bsp/display.h:84,157,158）、
 *   mosaico_module_mgr_init / subscribe / get_info / slot_to_name / type_to_name（mosaico_module_mgr.h）。
 * LVGL 调用与官方示例 examples/module_slot_scan 使用的函数集一致（lv_screen_active、lv_label_create、
 * lv_label_set_text、lv_obj_align、lv_obj_set_style_*、lv_color_hex）。
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

#if CONFIG_KEYTEST_USE_DISPLAY
#include "lvgl.h"
#endif

static const char *TAG = "keytest";

/* ------------------------------------------------------------------------- */
/* 可选屏幕显示                                                               */
/* ------------------------------------------------------------------------- */

#if CONFIG_KEYTEST_USE_DISPLAY
static lv_obj_t *s_label_link;
static lv_obj_t *s_label_keys;

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

    s_label_link = lv_label_create(screen);
    lv_obj_set_style_text_color(s_label_link, lv_color_hex(0xE6E6E6), 0);
    lv_obj_set_style_text_font(s_label_link, &lv_font_montserrat_20, 0);
    lv_label_set_text(s_label_link, "dock_handle: waiting");
    lv_obj_align(s_label_link, LV_ALIGN_TOP_MID, 0, 60);

    s_label_keys = lv_label_create(screen);
    lv_obj_set_style_text_color(s_label_keys, lv_color_hex(0x7FD4FF), 0);
    lv_obj_set_style_text_font(s_label_keys, &lv_font_montserrat_20, 0);
    lv_label_set_text(s_label_keys, "");
    lv_obj_center(s_label_keys);
    bsp_display_unlock();
}

static void ui_update(void)
{
    if (!s_label_link || !s_label_keys) {
        return;
    }
    char keys[DOCK_HANDLE_KEY_COUNT * 10 + 1] = {0};
    const uint32_t state = dock_handle_get_state();
    for (int i = 0; i < DOCK_HANDLE_KEY_COUNT; ++i) {
        if (state & (1U << i)) {
            /* 去掉 "KEY_" 前缀，屏幕上只显示 UP / A / L 等。 */
            strlcat(keys, dock_handle_key_name((dock_handle_key_t)i) + 4, sizeof(keys));
            strlcat(keys, " ", sizeof(keys));
        }
    }
    if (!bsp_display_lock(50)) {
        return;
    }
    switch (dock_handle_get_link()) {
    case DOCK_HANDLE_LINK_ATTACHED:
        lv_label_set_text(s_label_link, "dock_handle: attached");
        break;
    case DOCK_HANDLE_LINK_WAITING:
        lv_label_set_text(s_label_link, "dock_handle: waiting");
        break;
    default:
        lv_label_set_text(s_label_link, "dock_handle: stopped");
        break;
    }
    lv_label_set_text(s_label_keys, keys[0] ? keys : "-");
    bsp_display_unlock();
}
#else
static void ui_init(void) {}
static void ui_update(void) {}
#endif

/* ------------------------------------------------------------------------- */
/* 与 module_slot_scan 同源的两槽扫描日志：验证 EEPROM 是否被识别为 Handle    */
/* ------------------------------------------------------------------------- */

static void log_slot_info(const mosaico_module_mgr_info_t *info)
{
    const char *presence = info->presence == MOSAICO_MODULE_PRESENCE_PRESENT ? "PRESENT"
                           : info->presence == MOSAICO_MODULE_PRESENCE_ABSENT ? "ABSENT" : "UNKNOWN";
    const char *descriptor = info->descriptor_state == MOSAICO_MODULE_DESCRIPTOR_VALID ? "VALID"
                             : info->descriptor_state == MOSAICO_MODULE_DESCRIPTOR_INVALID ? "INVALID" : "UNKNOWN";
    if (info->descriptor_state == MOSAICO_MODULE_DESCRIPTOR_VALID) {
        ESP_LOGI(TAG, "slot %-5s addr=0x%02X %s descriptor=%s type=%s(0x%02X) vendor=0x%04X board=0x%04X name=\"%.32s\"",
                 mosaico_module_mgr_slot_to_name(info->slot), info->eeprom_addr, presence, descriptor,
                 mosaico_module_mgr_type_to_name((mosaico_board_type_t)info->eeprom.board_type),
                 info->eeprom.board_type, info->eeprom.vendor_id, info->eeprom.board_id, info->eeprom.board_name);
    } else {
        ESP_LOGI(TAG, "slot %-5s addr=0x%02X %s descriptor=%s last_error=%s",
                 mosaico_module_mgr_slot_to_name(info->slot), info->eeprom_addr, presence, descriptor,
                 esp_err_to_name(info->last_error));
    }
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

static void handle_event(const dock_handle_event_t *ev)
{
    switch (ev->type) {
    case DOCK_HANDLE_EVENT_KEY:
        ESP_LOGI(TAG, "%-9s %s  t=%" PRId64 " ms  state=0x%03" PRIX32,
                 dock_handle_key_name(ev->key), ev->pressed ? "DOWN" : "UP  ",
                 ev->timestamp_us / 1000, dock_handle_get_state());
        break;
    case DOCK_HANDLE_EVENT_ATTACHED:
        ESP_LOGI(TAG, "dock attached; KEY_* -> GPIO:");
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
    /* 项目主循环第 2 步：读 eFuse 版本。BSP 在 USER_DATA 未编程或版本不支持时返回 ESP_ERR_NOT_SUPPORTED，
     * 此时 bsp_subboard_init 也无法工作，直接停止并把原因打出来。 */
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

    /* 先起管理器并订阅，才能看到手柄模块被识别为 Handle(0x04) 的过程。 */
    ESP_ERROR_CHECK(mosaico_module_mgr_init(NULL));
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
