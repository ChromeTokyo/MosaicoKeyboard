# Chrome 09-24 方案 J 电气研究交接（未冻结）

输入 `sweep/consistency-20260921` `ead27bb`，按 [新分工](../../../docs/WORK-SPLIT-20260924.md)与[主控现行架构](../../claude/option-j-seated.md)研究。**这些是候选、边界与阻断记录，不是硬件通过或可制造 PCB。** 现行连接为裸直排针进 Mosaico 左 H2，针尾在 Mosaico −X 侧，底座触头沿 +X 顶它，整机沿 −Z 入仓。前一轮 `chrome/no-board-pin-contact` 的右角排针、+Z 撞针和 J2 坐标不继承。

| 包 | 已交 | 未通过／下一输入 |
| --- | --- | --- |
| [C1](C1_STRAIGHT_HEADER.md) | ZHOURI `C5116480` 作为试插候选；原厂图给头 6.0±0.2、本体 2.54、尾 3.0±0.2 mm；无罩，LCSC/JLC 料页可核 | U3 外壳凹深和 H2 实际插深、针尾端面镀层/擦触寿命、导向受力 |
| [C2](C2_SIDE_WIPE_CONTACT.md) | Mill-Max/Harwin 原厂资料及尺寸/行程/力对照 | **无合格料号**。目标 0.7–1.7 mm X 行程尚未由 M5 证实；Omniball 行程太短、邻位装配及大球桥接疑点；需真正侧擦兼容件或改几何 |
| [C3](C3_CONTACT_FIELD.md) | H2 20 位逻辑对照；默认 **12 触点**（十键、p17 5V、p20 GND） | **上电/打样阻断**：−Z 落座时若 X 已接合，两种排朝向分别可能 p17 5V→p18 5V_OUT 或 p20 GND→p19 3V3。需要 U3 朝向、M1/M5 X 接合时序、M6 全扫掠闸门及断电实物验证。旧 4×4 静态脚本不能绿灯代替 |
| [C4](C4_EEPROM_FORM.md) | BSP 证明专用固件可无 EEPROM 静态读十键；小板串阻不能串入不断开的直排针 | 当前 `dock_handle` 强制身份/claim，需显式静态固件分支；(a)/(b) 形态由用户决定；EEPROM 常驻无法表示每天坐入/离座 |
| [C5](C5_POWER_MODULE.md) | 七项筛选；Adafruit 6106 是最接近台架样件；TPS2553/LM66100 是条件性限流/反灌候选；给 M2 的**板框占位 29.21×19.05 mm** | **无七项全过原装模块**：6106 的 NTC 被 10k 固定电阻代替；纹波、启动 >200mA、无电池 USB 运行、主机/触点电流额定及最终电池资料待核；不出生产网表 |
| C6 | 生产原理图/PCB/Gerber/BOM **未开画** | 依赖 C2、C3 动态安全、C5、Claude M2/M3、U3 实测与独立复核；任何旧设计文件不得作为布局基线 |
| C7 | 旧 `claude/design-d/dock-board` 源头已另建 [归档 PR #60](https://github.com/ChromeTokyo/MosaicoKeyboard/pull/60) | 只保留历史计算；PR 基线是旧分支，不应把分立网表合进现行设计 |

需 Hiro/Grok 独立复核 C1 原厂图、C2 尺寸/配对、C3 新安全问题及电源边界；主控记录裁决和冻结。`docs/DESIGN_STATUS.md` 的 J-IF-01～06 是同步阻断登记。

验证范围：原厂 PDF/开源原理图及 BSP 固定快照已对照；相对链接和 `git diff --check` 已检查；未上电、未编译/烧录静态十键固件、未做实物插配、未执行现行 PCB/ERC/DRC。旧 dock-board 分支的脚本通过只说明**历史网表内部一致性**。
