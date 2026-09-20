# 提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
#
# keytest：认领底座手柄并在控制台（可选屏幕）打印按键事件。
# 可选：设置环境变量 MOSAICO_BSP_COMPONENTS 指向本地 esp-mosaico-bsp/components 目录，
# 用本地副本代替 idf_component.yml 里的 git 依赖（见 ../../README.md「构建」）。

cmake_minimum_required(VERSION 3.16)

if(DEFINED ENV{MOSAICO_BSP_COMPONENTS})
    list(APPEND EXTRA_COMPONENT_DIRS
        "$ENV{MOSAICO_BSP_COMPONENTS}/esp-mosaico-bsp"
        "$ENV{MOSAICO_BSP_COMPONENTS}/mosaico_module_mgr")
endif()
list(APPEND EXTRA_COMPONENT_DIRS "${CMAKE_CURRENT_LIST_DIR}/../..")

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(dock_handle_keytest)
