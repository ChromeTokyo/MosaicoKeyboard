# 提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
#
# dock_handle：方案 D＋G 底座手柄（10 键）主机侧 ESP-IDF 组件。
# 依赖组件名取自 esp-mosaico-bsp commit 392860b1 的目录名：
#   components/mosaico_module_mgr  -> mosaico_module_mgr
#   components/esp-mosaico-bsp     -> esp-mosaico-bsp
# 公共头 include/dock_handle.h 包含 mosaico_module_mgr.h 与 driver/gpio.h，故两者为 REQUIRES（public）。

idf_component_register(
    SRCS "dock_handle.c"
    INCLUDE_DIRS "include"
    REQUIRES
        mosaico_module_mgr
        esp-mosaico-bsp
        esp_driver_gpio
    PRIV_REQUIRES
        esp_timer
)
