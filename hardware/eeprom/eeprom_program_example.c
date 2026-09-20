/* 提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造 */
/*
 * Mosaico 主机（BaseBoard V1.2）经左槽 I2C1 向模块板 AT24C02（7 位地址 0x50）烧写
 * EEPROM V1 身份镜像的示例固件。仅供台架/首次装配使用，不是产品固件。
 *
 * 所有 API 名称与签名的核对来源（不得引用未核对函数）：
 *   esp-mosaico-bsp @ 392860b1，仓库快照 review/chrome/D1-module-interface/evidence/bsp/
 *     bsp_subboard_init()                 include/bsp/subboard.h L58；实现 onboard/subboard.c L123-152：
 *                                          先 bsp_power_set_vcc_3v3(true)（pin19 VCC_3V3 上电）→ init_i2c_bus()
 *                                          （V1.2：I2C_NUM_1，SDA GPIO0 / SCL GPIO1，enable_internal_pullup）
 *                                          → 左 GPIO14 输出 0、右 GPIO39 输出 1
 *     bsp_subboard_get_i2c_bus()          subboard.h L61；subboard.c L154-157
 *     BSP_SUBBOARD_EEPROM_ADDR_LEFT 0x50  subboard.h L34
 *     MOSAICO_MODULE_MGR_EEPROM_IMAGE_SIZE 0x86，mosaico_module_mgr.h L25
 *     mosaico_module_mgr_init/_get_info/_request_rescan/_type_to_name/_slot_to_name  mosaico_module_mgr.h
 *     mosaico_module_mgr_info_t 字段 presence/descriptor_state/eeprom  mosaico_module_mgr.h L108-117
 *   ESP-IDF driver/i2c_master.h（https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/peripherals/i2c.html，2026-09-20 访问；
 *   BSP 自身已使用其中 i2c_master_probe / i2c_master_bus_add_device / i2c_master_bus_rm_device / i2c_master_transmit_receive）
 *     esp_err_t i2c_master_transmit(i2c_master_dev_handle_t, const uint8_t *write_buffer, size_t write_size, int xfer_timeout_ms)
 *     esp_err_t i2c_master_transmit_receive(i2c_master_dev_handle_t, const uint8_t *wbuf, size_t wsize, uint8_t *rbuf, size_t rsize, int xfer_timeout_ms)
 *     esp_err_t i2c_master_probe(i2c_master_bus_handle_t, uint16_t address, int xfer_timeout_ms)
 *     esp_err_t i2c_master_bus_add_device(i2c_master_bus_handle_t, const i2c_device_config_t *, i2c_master_dev_handle_t *)
 *     esp_err_t i2c_master_bus_rm_device(i2c_master_dev_handle_t)
 *   ASSUMPTION: ESP32-S31 目标上的 IDF 版本提供同名同签名 API（BSP 依赖它们编译，但本文件未在 S31 工具链上实际编译）。
 *   验证：在实物到货、BSP 可编译的 IDF 环境中把本文件加入示例工程编译一次。
 *
 * AT24C02 写入时序依据：Atmel/Microchip AT24C01A/02/04/08A/16A 数据手册 0180Z1–SEEPR–5/07
 * （https://ww1.microchip.com/downloads/en/DeviceDoc/doc0180.pdf，2026-09-20 打开）：
 *   2K 器件 32 页 × 8 字节，8 位字地址；页写最多 8 字节，允许部分页写；页内地址低 3 位自增并在页边界回卷；
 *   写周期 tWR 最大 5 ms，期间器件不应答，可用 Acknowledge Polling 探测完成。
 *   该手册把原 AT24C02 标为「不推荐新设计」，所购具体型号（AT24C02C/D 或兼容件）的页大小与 tWR 待原厂数据手册核对。
 *
 * 前置条件（详见 PROGRAMMING.md 第 3 节）：
 *   - 模块板已插入左槽；A1/A2 接 GND；A0 接 H2 pin10（GPIO14）；WP 为低（可写）；EEPROM VCC 来自 pin19。
 *   - 本固件里不启动 mosaico_module_mgr（或已 mosaico_module_mgr_deinit()），避免扫描任务在 tWR 期间探测。
 *   - 串口日志应先出现 BSP 的 "Hardware version: v1.2 (variant=v1.2)"（esp_mosaico.c detect_board_variant）。
 */

#include <inttypes.h>
#include <string.h>

#include "bsp/subboard.h"
#include "driver/i2c_master.h"
#include "esp_check.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "mosaico_module_mgr.h"

#include "sample_handle_image.h"   /* 由 mosaico_eeprom_v1.py c-array 生成：k_sample_handle_image[134] */

static const char *TAG = "eeprom_prog";

#define EEPROM_PAGE_SIZE          8U        /* AT24C02 页大小（doc0180）；所购型号待核对 */
#define EEPROM_I2C_FREQ_HZ        100000U   /* 与 mosaico_module_mgr.c L27 EEPROM_I2C_FREQ_HZ 一致 */
#define EEPROM_I2C_TIMEOUT_MS     100       /* 与 mosaico_module_mgr.c L28 EEPROM_I2C_TIMEOUT_MS 一致 */
#define EEPROM_TWR_POLL_LIMIT_MS  20        /* tWR max 5 ms（doc0180 Table 5）× 4 余量 */
#define EEPROM_IMAGE_SIZE         MOSAICO_MODULE_MGR_EEPROM_IMAGE_SIZE

/* 与 mosaico_module_mgr.c L209-218 crc16() 逐位等价，用于烧写前确认嵌入镜像自身有效。 */
static uint16_t crc16_modbus(const uint8_t *data, size_t len)
{
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < len; ++i) {
        crc ^= data[i];
        for (int bit = 0; bit < 8; ++bit) {
            crc = (crc & 1U) ? (uint16_t)((crc >> 1) ^ 0xA001U) : (uint16_t)(crc >> 1);
        }
    }
    return crc;
}

static uint16_t rd_le16(const uint8_t *p)
{
    return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}

/* 复现 parse_descriptor（mosaico_module_mgr.c L221-241）的四项校验；不解码字段。 */
static esp_err_t image_check(const uint8_t img[EEPROM_IMAGE_SIZE])
{
    if (memcmp(img, MOSAICO_MODULE_MGR_EEPROM_MAGIC, MOSAICO_MODULE_MGR_EEPROM_MAGIC_LEN) != 0) {
        return ESP_ERR_INVALID_RESPONSE;
    }
    if (rd_le16(img + 0x34) != crc16_modbus(img, 0x34) ||
        rd_le16(img + 0x3E) != crc16_modbus(img + 0x36, 0x3E - 0x36) ||
        rd_le16(img + 0x84) != crc16_modbus(img + 0x40, 0x84 - 0x40)) {
        return ESP_ERR_INVALID_CRC;
    }
    if (rd_le16(img + 0x42) > 64U) {
        return ESP_ERR_INVALID_SIZE;
    }
    return ESP_OK;
}

/* Acknowledge Polling：写周期内器件对地址字节不应答（i2c_master_probe 返回 ESP_ERR_NOT_FOUND）。 */
static esp_err_t eeprom_wait_ready(i2c_master_bus_handle_t bus, uint8_t addr)
{
    const TickType_t deadline = xTaskGetTickCount() + pdMS_TO_TICKS(EEPROM_TWR_POLL_LIMIT_MS) + 1;
    do {
        const esp_err_t ret = i2c_master_probe(bus, addr, EEPROM_I2C_TIMEOUT_MS);
        if (ret == ESP_OK) {
            return ESP_OK;
        }
        if (ret != ESP_ERR_NOT_FOUND) {
            return ret;   /* 总线级错误（超时/仲裁），不是正常的写周期 NACK */
        }
        vTaskDelay(1);
    } while ((int32_t)(deadline - xTaskGetTickCount()) > 0);
    return ESP_ERR_TIMEOUT;
}

/* 逐页写入：帧 = [8 位字地址][最多 8 字节]。off 恒为 8 的倍数，不会跨页；最后一页 6 字节为部分页写。 */
static esp_err_t eeprom_write_image(i2c_master_bus_handle_t bus, i2c_master_dev_handle_t dev, uint8_t addr,
                                    const uint8_t *img, size_t len)
{
    uint8_t frame[1 + EEPROM_PAGE_SIZE];
    for (size_t off = 0; off < len; off += EEPROM_PAGE_SIZE) {
        const size_t n = (len - off < EEPROM_PAGE_SIZE) ? (len - off) : EEPROM_PAGE_SIZE;
        frame[0] = (uint8_t)off;
        memcpy(&frame[1], img + off, n);
        ESP_RETURN_ON_ERROR(i2c_master_transmit(dev, frame, 1 + n, EEPROM_I2C_TIMEOUT_MS), TAG,
                            "page 0x%02X write failed", (unsigned)off);
        ESP_RETURN_ON_ERROR(eeprom_wait_ready(bus, addr), TAG, "tWR poll timeout after page 0x%02X", (unsigned)off);
    }
    return ESP_OK;
}

/* 与 mosaico_module_mgr.c L418-423 read_eeprom() 相同的读法：写 1 字节地址 0，再连续读 134 字节。 */
static esp_err_t eeprom_read_image(i2c_master_dev_handle_t dev, uint8_t *out, size_t len)
{
    const uint8_t word_addr = 0;
    return i2c_master_transmit_receive(dev, &word_addr, sizeof(word_addr), out, len, EEPROM_I2C_TIMEOUT_MS);
}

/**
 * 向左槽 EEPROM 烧写并回读校验。
 * 成功返回 ESP_OK；镜像自身无效返回 parse_descriptor 同名错误；回读不一致返回 ESP_ERR_INVALID_STATE。
 */
esp_err_t eeprom_program_left_slot(const uint8_t *img, size_t len)
{
    ESP_RETURN_ON_FALSE(img && len == EEPROM_IMAGE_SIZE, ESP_ERR_INVALID_SIZE, TAG, "image must be %u bytes",
                        (unsigned)EEPROM_IMAGE_SIZE);
    ESP_RETURN_ON_ERROR(image_check(img), TAG, "refusing to program an image the host would reject");

    /* 上电顺序由 BSP 决定：VCC_3V3(pin19) → I2C1 → GPIO14=0（A0 低 → 0x50）。不要在此前访问总线。 */
    ESP_RETURN_ON_ERROR(bsp_subboard_init(), TAG, "bsp_subboard_init failed");
    i2c_master_bus_handle_t bus = bsp_subboard_get_i2c_bus();
    ESP_RETURN_ON_FALSE(bus, ESP_ERR_INVALID_STATE, TAG, "subboard I2C bus is null");

    const uint8_t addr = BSP_SUBBOARD_EEPROM_ADDR_LEFT;
    ESP_RETURN_ON_ERROR(i2c_master_probe(bus, addr, EEPROM_I2C_TIMEOUT_MS), TAG,
                        "EEPROM 0x%02X not responding: check module seated, A0/A1/A2, pin19 3V3", addr);

    const i2c_device_config_t cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = addr,
        .scl_speed_hz = EEPROM_I2C_FREQ_HZ,
    };
    i2c_master_dev_handle_t dev = NULL;
    ESP_RETURN_ON_ERROR(i2c_master_bus_add_device(bus, &cfg, &dev), TAG, "add EEPROM device failed");

    esp_err_t ret = eeprom_write_image(bus, dev, addr, img, len);
    uint8_t readback[EEPROM_IMAGE_SIZE] = {0};
    if (ret == ESP_OK) {
        ret = eeprom_read_image(dev, readback, sizeof(readback));
    }
    if (ret == ESP_OK && memcmp(readback, img, len) != 0) {
        for (size_t i = 0; i < len; ++i) {
            if (readback[i] != img[i]) {
                ESP_LOGE(TAG, "readback mismatch at 0x%02X: wrote 0x%02X read 0x%02X", (unsigned)i, img[i], readback[i]);
                break;
            }
        }
        ret = ESP_ERR_INVALID_STATE;
    }
    if (ret == ESP_OK) {
        ret = image_check(readback);   /* 回读镜像必须能被主机接受 */
    }
    (void)i2c_master_bus_rm_device(dev);
    return ret;
}

/**
 * 烧写后用官方模块管理器做最终确认：presence PRESENT、descriptor VALID、board_type HANDLE。
 * 管理器默认 250 ms 扫描、3 次去抖（MOSAICO_MODULE_MGR_DEFAULT_CONFIG），首次识别通常在 1 s 内。
 */
static esp_err_t confirm_with_module_mgr(void)
{
    ESP_RETURN_ON_ERROR(mosaico_module_mgr_init(NULL), TAG, "module manager init failed");
    ESP_RETURN_ON_ERROR(mosaico_module_mgr_request_rescan(MOSAICO_MODULE_MGR_SLOT_LEFT), TAG, "rescan request failed");

    mosaico_module_mgr_info_t info = {0};
    for (int i = 0; i < 40; ++i) {   /* 最多等 4 s */
        vTaskDelay(pdMS_TO_TICKS(100));
        ESP_RETURN_ON_ERROR(mosaico_module_mgr_get_info(MOSAICO_MODULE_MGR_SLOT_LEFT, &info), TAG, "get_info failed");
        if (info.presence == MOSAICO_MODULE_PRESENCE_PRESENT &&
            info.descriptor_state != MOSAICO_MODULE_DESCRIPTOR_UNKNOWN) {
            break;
        }
    }
    if (info.presence != MOSAICO_MODULE_PRESENCE_PRESENT) {
        ESP_LOGE(TAG, "manager: left slot not PRESENT (presence=%d err=%s)", info.presence, esp_err_to_name(info.last_error));
        return ESP_ERR_NOT_FOUND;
    }
    if (info.descriptor_state != MOSAICO_MODULE_DESCRIPTOR_VALID) {
        ESP_LOGE(TAG, "manager: descriptor state %d, last_error=%s", info.descriptor_state, esp_err_to_name(info.last_error));
        return ESP_ERR_INVALID_RESPONSE;
    }
    ESP_LOGI(TAG, "manager sees: slot=%s eeprom=0x%02X type=%s(0x%02X) vendor=0x%04X id=0x%04X hw=0x%04X sw=0x%04X serial=0x%08" PRIX32 " name=%.32s",
             mosaico_module_mgr_slot_to_name(info.slot), info.eeprom_addr,
             mosaico_module_mgr_type_to_name((mosaico_board_type_t)info.eeprom.board_type), info.eeprom.board_type,
             info.eeprom.vendor_id, info.eeprom.board_id, info.eeprom.hw_version, info.eeprom.sw_version,
             info.eeprom.serial_number, info.eeprom.board_name);
    return info.eeprom.board_type == MOSAICO_BOARD_TYPE_HANDLE ? ESP_OK : ESP_ERR_INVALID_RESPONSE;
}

void app_main(void)
{
    /* 样例镜像的 serial_number 固定为 0x26090001；批量烧写时应按 IDENTITY.md 第 5 节为每台生成不同镜像。 */
    ESP_LOGI(TAG, "programming %u-byte EEPROM V1 image into LEFT slot 0x%02X",
             (unsigned)K_SAMPLE_HANDLE_IMAGE_SIZE, BSP_SUBBOARD_EEPROM_ADDR_LEFT);
    esp_err_t ret = eeprom_program_left_slot(k_sample_handle_image, K_SAMPLE_HANDLE_IMAGE_SIZE);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "programming FAILED: %s", esp_err_to_name(ret));
        return;
    }
    ESP_LOGI(TAG, "programming and readback OK; confirming with module manager");
    ret = confirm_with_module_mgr();
    ESP_LOGI(TAG, "module manager confirmation: %s", ret == ESP_OK ? "PASS" : esp_err_to_name(ret));
}
