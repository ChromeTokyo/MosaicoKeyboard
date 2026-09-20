/*
 * 提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
 *
 * KEY_* -> 左槽 GPIO 宏表（方案 D＋G，底座手柄模块）。
 *
 * 权威来源：hardware/module-board/PINMAP.md（模块板任务产出）。
 * ASSUMPTION: 撰写本文件时 PINMAP.md 尚未入库，下表是按左槽 H2 针序拟定的分配，
 *             仅作为默认值。PINMAP.md 入库后以其为准；不一致时改本文件默认值，
 *             或在工程 CMake 中以 target_compile_definitions(-DDOCK_HANDLE_GPIO_KEY_xx=GPIO_NUM_nn) 覆盖。
 *   到货后验证：模块板单板（不接底座）逐一将某 KEY_* 触点短接到 GND，运行 examples/keytest，
 *              串口打印的键名必须与 PINMAP.md 及底座丝印一致；不一致即修正此表。
 *
 * H2 针号与 GPIO 的对应取自 review/chrome/D1-module-interface/LEFT_SLOT.md
 * （BSP commit 392860b1 subboard.c:24-67 与官方 V1.0 指南引脚表交叉核对）。
 *
 * 禁用引脚（编译期在 dock_handle.c 以 _Static_assert 拦截）：
 *   GPIO14  H2 pin10  EEPROM A0 专用（bsp/subboard.h BSP_SUBBOARD_ADDR_GPIO_LEFT）
 *   GPIO0/1 H2 pin16/14 V1.2 模块 I2C1（BSP_SUBBOARD_I2C_SDA / _SCL）
 *   GPIO33/34 H2 pin13/15 USB Serial/JTAG，保留
 *   GPIO54/37/49/52/40 板载 I2S（左槽原生 GPIO 与其无交集；右槽镜像会撞上，故本驱动不支持右槽）
 *
 * 全部按键为无源开关接 SLOT_GND，拉高由主机 GPIO 内部上拉提供（3.3 V 域），按下读 0。
 */

#pragma once

#include "driver/gpio.h"

/* H2 pin 1 */
#ifndef DOCK_HANDLE_GPIO_KEY_UP
#define DOCK_HANDLE_GPIO_KEY_UP     GPIO_NUM_55
#endif
/* H2 pin 2 */
#ifndef DOCK_HANDLE_GPIO_KEY_DOWN
#define DOCK_HANDLE_GPIO_KEY_DOWN   GPIO_NUM_53
#endif
/* H2 pin 3 */
#ifndef DOCK_HANDLE_GPIO_KEY_LEFT
#define DOCK_HANDLE_GPIO_KEY_LEFT   GPIO_NUM_19
#endif
/* H2 pin 4 */
#ifndef DOCK_HANDLE_GPIO_KEY_RIGHT
#define DOCK_HANDLE_GPIO_KEY_RIGHT  GPIO_NUM_48
#endif
/* H2 pin 5 */
#ifndef DOCK_HANDLE_GPIO_KEY_A
#define DOCK_HANDLE_GPIO_KEY_A      GPIO_NUM_18
#endif
/* H2 pin 6 */
#ifndef DOCK_HANDLE_GPIO_KEY_B
#define DOCK_HANDLE_GPIO_KEY_B      GPIO_NUM_13
#endif
/* H2 pin 7 */
#ifndef DOCK_HANDLE_GPIO_KEY_X
#define DOCK_HANDLE_GPIO_KEY_X      GPIO_NUM_17
#endif
/* H2 pin 8 */
#ifndef DOCK_HANDLE_GPIO_KEY_Y
#define DOCK_HANDLE_GPIO_KEY_Y      GPIO_NUM_12
#endif
/* H2 pin 9 */
#ifndef DOCK_HANDLE_GPIO_KEY_L
#define DOCK_HANDLE_GPIO_KEY_L      GPIO_NUM_16
#endif
/* H2 pin 11 */
#ifndef DOCK_HANDLE_GPIO_KEY_R
#define DOCK_HANDLE_GPIO_KEY_R      GPIO_NUM_15
#endif

/* H2 pin 12，第 11 根可用 GPIO，本版不配置、不上拉，留作备用（例如未来的 MENU 键）。 */
#ifndef DOCK_HANDLE_GPIO_SPARE
#define DOCK_HANDLE_GPIO_SPARE      GPIO_NUM_4
#endif
