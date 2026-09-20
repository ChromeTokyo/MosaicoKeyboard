# 提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
#
# esp_driver_i2c：只读 I2C 地址扫描用 i2c_master_probe()（ICD 第 8 节要求 ③）。
# LVGL 头经 esp-mosaico-bsp -> espressif/esp_lvgl_adapter（public）传递到达。
# ASSUMPTION: 该传递在组件管理器下成立（官方 module_slot_scan/main 同样未直接列出 lvgl）；
#   若 idf.py build 报找不到 lvgl.h，在 PRIV_REQUIRES 追加 lvgl__lvgl。

idf_component_register(
    SRCS "main.c"
    INCLUDE_DIRS "."
    PRIV_REQUIRES
        dock_handle
        esp-mosaico-bsp
        mosaico_module_mgr
        esp_driver_i2c
        esp_timer
)
