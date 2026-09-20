/*
 * 提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
 *
 * KEY_* -> 左槽 GPIO 宏表（方案 D＋G，底座手柄模块板）。
 *
 * 权威来源：hardware/module-board/PINMAP.md 第 2 节「KEY_* → H2 针号 → GPIO（最终分配）」
 *   读取方式：git show origin/claude/design-d/module-board:hardware/module-board/PINMAP.md（2026-09-20 版）。
 *   本文件只是该表的 C 语言镜像；两者不一致时以 PINMAP.md 为准并修改本文件。
 *
 * 修订记录：上一轮 WIP 把 10 个键按 H2 针序 1..11 顺排（DOWN=GPIO53、LEFT=GPIO19 ……），
 *   与 PINMAP.md 不一致。PINMAP.md 的分配规律是：奇数排 pin1/3/5/7/9/11 = UP/DOWN/LEFT/RIGHT/L/R，
 *   偶数排 pin2/4/6/8 = A/B/X/Y，pin12 备用。本版已按 PINMAP.md 改正。
 *
 * H2 针号 <-> GPIO 的对应取自 review/chrome/D1-module-interface/LEFT_SLOT.md
 * （BSP commit 392860b1 subboard.c:24-67 与官方 V1.0 指南 user_guide_v10.rst:627-685 交叉核对）。
 *
 * 禁用引脚（编译期在 dock_handle.c 以 _Static_assert 拦截）：
 *   GPIO14    H2 pin10   EEPROM A0 专用（bsp/subboard.h:36 BSP_SUBBOARD_ADDR_GPIO_LEFT）
 *   GPIO0/1   H2 pin16/14 V1.2 模块 I2C1（bsp/esp_mosaico.h:74-75 BSP_SUBBOARD_I2C_SDA / _SCL）
 *   GPIO33/34 H2 pin13/15 USB Serial/JTAG，保留（LEFT_SLOT.md）
 *   GPIO54/37/49/52/40 板载 I2S（bsp/esp_mosaico.h:109-113；左槽原生 GPIO 与其无交集；
 *             右槽镜像会撞上，故本驱动不支持右槽）
 *
 * 电气：全部按键为无源开关接 SLOT_GND / DOCK_GND，拉高只由主机 GPIO 内部上拉提供（3.3 V 域），按下读 0。
 *
 * 到货后验证（对应 PINMAP.md 第 6 节 P4、README 第 8 节步 4）：
 *   模块板单板（不接底座）用镊子把 J2 上某个 KEY_* 焊盘对 DOCK_GND 短接，运行 examples/keytest，
 *   串口打印的键名必须与 PINMAP.md 第 4.2 节焊盘位（A3=KEY_UP … B6=KEY_Y）及底座丝印一致；
 *   不一致即修正 PINMAP.md 并同步本文件。
 *
 * 覆盖方式：工程 CMake 中 target_compile_definitions(... -DDOCK_HANDLE_GPIO_KEY_xx=GPIO_NUM_nn)；
 *   _Static_assert 会拦住重复值与禁用引脚，但不会拦住「与 PINMAP.md 不一致」——那只能靠到货验证。
 */

#pragma once

#include "driver/gpio.h"

/* ---- 奇数排：方向键 + 肩键 ---- */

/* H2 pin 1  — J2 焊盘 A3 */
#ifndef DOCK_HANDLE_GPIO_KEY_UP
#define DOCK_HANDLE_GPIO_KEY_UP     GPIO_NUM_55
#endif
/* H2 pin 3  — J2 焊盘 A4 */
#ifndef DOCK_HANDLE_GPIO_KEY_DOWN
#define DOCK_HANDLE_GPIO_KEY_DOWN   GPIO_NUM_19
#endif
/* H2 pin 5  — J2 焊盘 A5 */
#ifndef DOCK_HANDLE_GPIO_KEY_LEFT
#define DOCK_HANDLE_GPIO_KEY_LEFT   GPIO_NUM_18
#endif
/* H2 pin 7  — J2 焊盘 A6 */
#ifndef DOCK_HANDLE_GPIO_KEY_RIGHT
#define DOCK_HANDLE_GPIO_KEY_RIGHT  GPIO_NUM_17
#endif
/* H2 pin 9  — J2 焊盘 A7 */
#ifndef DOCK_HANDLE_GPIO_KEY_L
#define DOCK_HANDLE_GPIO_KEY_L      GPIO_NUM_16
#endif
/* H2 pin 11 — J2 焊盘 B2 */
#ifndef DOCK_HANDLE_GPIO_KEY_R
#define DOCK_HANDLE_GPIO_KEY_R      GPIO_NUM_15
#endif

/* ---- 偶数排：ABXY ---- */

/* H2 pin 2  — J2 焊盘 B3 */
#ifndef DOCK_HANDLE_GPIO_KEY_A
#define DOCK_HANDLE_GPIO_KEY_A      GPIO_NUM_53
#endif
/* H2 pin 4  — J2 焊盘 B4 */
#ifndef DOCK_HANDLE_GPIO_KEY_B
#define DOCK_HANDLE_GPIO_KEY_B      GPIO_NUM_48
#endif
/* H2 pin 6  — J2 焊盘 B5 */
#ifndef DOCK_HANDLE_GPIO_KEY_X
#define DOCK_HANDLE_GPIO_KEY_X      GPIO_NUM_13
#endif
/* H2 pin 8  — J2 焊盘 B6 */
#ifndef DOCK_HANDLE_GPIO_KEY_Y
#define DOCK_HANDLE_GPIO_KEY_Y      GPIO_NUM_12
#endif

/* ---- 备用 ---- */

/* H2 pin 12，第 11 根可用 GPIO。PINMAP.md 网名 SPARE_GPIO4（ICD 名 SLOT_SPARE_GPIO4），只到测试点 TP7，
 * 不上弹簧针。本驱动不配置、不上拉；留作下一轮迭代换针（例如某键被证实为 strapping 时替换）。 */
#ifndef DOCK_HANDLE_GPIO_SPARE
#define DOCK_HANDLE_GPIO_SPARE      GPIO_NUM_4
#endif

/*
 * EEPROM param_data v1 keymap（hardware/eeprom/IDENTITY.md 第 8 节，分支 claude/design-d/eeprom）
 * 的合法 GPIO 全集：左槽 11 根可用 GPIO（LEFT_SLOT.md），不含 GPIO14。
 * dock_handle.c 在 KEYMAP_VALID=1 时用它校验 EEPROM 给出的 10 个值，校验失败回退到上表。
 */
#define DOCK_HANDLE_ALLOWED_KEY_GPIO_LIST \
    GPIO_NUM_55, GPIO_NUM_53, GPIO_NUM_19, GPIO_NUM_48, GPIO_NUM_18, GPIO_NUM_13, \
    GPIO_NUM_17, GPIO_NUM_12, GPIO_NUM_16, GPIO_NUM_15, GPIO_NUM_4
