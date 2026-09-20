/* 提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造 */
/*
 * Mosaico 主机（BaseBoard V1.2）经左槽 I2C1 向模块板 AT24C02（7 位地址 0x50）烧写
 * EEPROM V1 身份镜像的示例固件。仅供台架/首次装配使用，不是产品固件。
 *
 * 所有 API 名称与签名的核对来源（不得引用未核对函数）：
 *   esp-mosaico-bsp @ 392860b1，仓库快照 review/chrome/D1-module-interface/evidence/bsp/
 *     bsp_subboard_init()                 include/bsp/subboard.h L62；实现 onboard/subboard.c L123-152：
 *                                          先 bsp_power_set_vcc_3v3(true)（pin19 VCC_3V3 上电）→ init_i2c_bus()
 *                                          （V1.2：I2C_NUM_1，SDA GPIO0 / SCL GPIO1，enable_internal_pullup）
 *                                          → 左 GPIO14 输出 0、右 GPIO39 输出 1
 *     bsp_subboard_get_i2c_bus()          subboard.h L65；subboard.c L154-157
 *     BSP_SUBBOARD_EEPROM_ADDR_LEFT 0x50  subboard.h L34
 *     MOSAICO_MODULE_MGR_EEPROM_MAGIC/_LEN/_IMAGE_SIZE 0x86  mosaico_module_mgr.h L23-25
 *     mosaico_module_mgr_init L199 / _get_info L261 / _request_rescan L309 / _slot_to_name L317 / _type_to_name L325  mosaico_module_mgr.h
 *     mosaico_module_mgr_info_t 字段 slot/presence/descriptor_state/last_error/eeprom_addr/eeprom  mosaico_module_mgr.h L108-117
 *     mosaico_module_mgr_eeprom_v1_t 字段 board_type/board_id/hw_version/sw_version/vendor_id/serial_number/board_name  L86-105
 *   ESP-IDF driver/i2c_master.h（https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/peripherals/i2c.html，2026-09-20 访问）。
 *   同 commit 的 BSP 已调用其中全部五个函数：mosaico_module_mgr.c L386 bus_add_device、L402 bus_rm_device、
 *   L421 transmit_receive、L481 probe；onboard/sensors.c L51、L197 i2c_master_transmit(device, buffer, length + 1, -1)
 *   （sensors.c 在本地完整克隆 /tmp/mosaico-v12/esp-mosaico-bsp，未收进证据包）。
 *     esp_err_t i2c_master_transmit(i2c_master_dev_handle_t, const uint8_t *write_buffer, size_t write_size, int xfer_timeout_ms)
 *     esp_err_t i2c_master_transmit_receive(i2c_master_dev_handle_t, const uint8_t *wbuf, size_t wsize, uint8_t *rbuf, size_t rsize, int xfer_timeout_ms)
 *     esp_err_t i2c_master_probe(i2c_master_bus_handle_t, uint16_t address, int xfer_timeout_ms)
 *     esp_err_t i2c_master_bus_add_device(i2c_master_bus_handle_t, const i2c_device_config_t *, i2c_master_dev_handle_t *)
 *     esp_err_t i2c_master_bus_rm_device(i2c_master_dev_handle_t)
 *   ASSUMPTION（AS-31-eeprom-6）: ESP32-S31 目标上的 IDF 版本提供同名同签名 API（BSP 依赖它们编译；本文件只在宿主机
 *   以桩头通过 clang -fsyntax-only 检查，见 README.md，未在 S31 工具链上实际编译）。
 *   验证：在实物到货、BSP 可编译的 IDF 环境中把本文件加入示例工程编译一次。
 *
 * EEPROM 写入时序依据：模块板分支 netlist 选定 U1 = AT24C02D-SSHM-T（LCSC C34807）。数据手册
 * Atmel-8871F-SEEPROM-AT24C01D-02D-Datasheet_012017
 * （https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-8871F-SEEPROM-AT24C01D-02D-Datasheet.pdf，2026-09-21 打开）：
 *   8 字节页写、允许部分页写、页内地址回卷（§5.2）；tWR 最大 5 ms（Table 8-3），期间器件不 ACK，可用 Acknowledge Polling（§5.3）；
 *   工作电压 1.7–3.6 V（Table 8-1）；A0/A1/A2/WP 悬空时内部下拉到 GND（引脚表 Note 1）；
 *   WP = VCC 时全阵列禁写，但器件对地址/数据字节仍正常 ACK，只是不发生写周期（§5.5）——因此本文件靠回读比对发现写保护。
 *   ASSUMPTION（AS-31-eeprom-8）: BOM 最终器件仍为 AT24C02D（换件须重核页大小与 tWR）。
 *
 * 前置条件（详见 PROGRAMMING.md 第 3 节）：
 *   - 模块板已插入左槽；A1/A2 接 GND；A0 接 H2 pin10（GPIO14）；JP1 桥 1–2 使 WP = GND（可写）；EEPROM VCC 来自 pin19。
 *   - 本固件里不启动 mosaico_module_mgr（或已 mosaico_module_mgr_deinit()），避免扫描任务在 tWR 期间探测。
 *   - 串口日志应先出现 BSP 的 "Hardware version: v1.2 (variant=v1.2)"（esp_mosaico.c L57-58，detect_board_variant）。
 */

#include <inttypes.h>
#include <stdbool.h>
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

#define EEPROM_PAGE_SIZE          8U        /* AT24C02D 页大小（8871F Features、§5.2） */
#define EEPROM_I2C_FREQ_HZ        100000U   /* 与 mosaico_module_mgr.c L27 EEPROM_I2C_FREQ_HZ 一致 */
#define EEPROM_I2C_TIMEOUT_MS     100       /* 与 mosaico_module_mgr.c L28 EEPROM_I2C_TIMEOUT_MS 一致 */
#define EEPROM_TWR_POLL_LIMIT_MS  20        /* tWR max 5 ms（8871F Table 8-3）× 4 余量 */
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
        bool blank = true;
        for (size_t i = 0; i < len; ++i) {
            blank = blank && readback[i] == 0xFF;
            if (readback[i] != img[i]) {
                ESP_LOGE(TAG, "readback mismatch at 0x%02X: wrote 0x%02X read 0x%02X", (unsigned)i, img[i], readback[i]);
                break;
            }
        }
        if (blank) {
            /* 8871F §5.5：WP = VCC 时器件仍 ACK 但不写；空片回读全 0xFF 是 WP 被置位（JP1 桥在 2–3）最常见的表现。 */
            ESP_LOGE(TAG, "readback is blank (0xFF): WP is probably high (JP1 bridged 2-3); AT24C02D ACKs but does not write");
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
    /* 样例镜像（MOSAICO-DOCK-MODULE-V1.0，keymap_version 1）的 serial_number 固定为 0x26090001；
     * 批量烧写时应按 IDENTITY.md 第 5 节为每台 build 不同镜像并重新生成 sample_handle_image.h。 */
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
