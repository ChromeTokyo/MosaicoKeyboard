# T20 模块板 J2/J3 跨源合同核查（待独立复核）

日期：2026-09-23 JST。输入为 main `96fd823` 的 D1 左槽合同，及模块板待审提交 [`94e393c`](https://github.com/ChromeTokyo/MosaicoKeyboard/commit/94e393c55328cedca387affc7dd21aa316603b9c) 的 `PINMAP.md`/`netlist.yaml`。本报告是 **CHANGES_REQUIRED 提案**，只断言上述三个文本输入在固定版本下不一致；不批准或否决真实 PCB。Claude 拥有模块板设计源，Chrome 未改动其网表、引脚表、CAD 或 PCB。

## 固定输入与复现

| 输入 | SHA-256 | 取用方式 |
| --- | --- | --- |
| `review/chrome/D1-module-interface/LEFT_SLOT.md` | `d7922f2106e388dd4a6648465b07724f59301751923405d55eba38aa5a2e55ca` | 当前 main 的 D1 合同；只用于 H2 20 针功能、GPIO 与保留针锚定 |
| `hardware/module-board/PINMAP.md` | `fc986a2c00b0f0f264136f228376064c790a2cc309e869f69441728322e03727` | 模块板提交 `94e393c`，修订 c |
| `hardware/module-board/netlist.yaml` | `70668e5391ebd599037322850c1e63e755cb35b44fdf27a7905d0472327179bf` | 同一提交，仍是修订 b |

在仓库根目录复现；提取时固定提交，避免分支继续移动后混用版次：

```sh
git fetch origin claude/design-d/module-board
git show 94e393c55328cedca387affc7dd21aa316603b9c:hardware/module-board/PINMAP.md > /tmp/mosaico-j2-PINMAP.md
git show 94e393c55328cedca387affc7dd21aa316603b9c:hardware/module-board/netlist.yaml > /tmp/mosaico-j2-netlist.yaml
python3 review/chrome/T20-takeover/tools/check_j2_contract.py --left-slot review/chrome/D1-module-interface/LEFT_SLOT.md --pinmap /tmp/mosaico-j2-PINMAP.md --netlist /tmp/mosaico-j2-netlist.yaml
python3 review/chrome/T20-takeover/tools/test_check_j2_contract.py --left-slot review/chrome/D1-module-interface/LEFT_SLOT.md --pinmap /tmp/mosaico-j2-PINMAP.md --netlist /tmp/mosaico-j2-netlist.yaml
```

依赖 PyYAML，与模块板已有 `check_netlist.py` 相同。第一条 Python 命令预期 **退出 1，报告 7 类差异**；第二条预期 **退出 0，12 项测试通过**。测试把固定旧网表在内存中仅对齐 J2/J3，得到一份**合成的正控制**；它不是可以制造的设计源。随后注入 J2/J3 电源接按键、GPIO 错配、H2.10 被按键占用、重复引脚、pin18 反送、旧焊盘直径/封装等，必须失败。哈希不对时测试拒绝运行。

## 结果及影响

PINMAP §4.2 的 J2 已改为 4 行×4 列、`J2.1A…J2.4D`、节距 2.54 mm、焊盘 Ø2.0 mm，5V×2/GND×4/10 键；同提交网表 `J2` 仍是 `PAD-ARRAY-2x8-P2.54-D1.8` 和 `A1…B8`。PINMAP §5.3 的 J3 已改为双排 8+8、1.27 mm、`r0.1…r1.8`，12 个跨板网；网表 `J3` 仍是单排 `CASTELLATION-1x16-P1.50-D0.70`、数字脚、14 个跨板网，且没有新位名声明。脚本的 7 行诊断细分了这两组根因，**不是 7 个互不相关的硬件缺陷**。

网表自己的 `check_netlist.py` 在同一分支硬编码旧的 J2 2×8/Ø1.8 与 J3 数字脚；它验证旧网表的内部形式，不能作为修订 c 引脚表已同步的证据。即使把 J2 改对，J3 电源与按键位若互换，电气路径仍会错；只给 `J3.pins: 16` 而不声明 `pin_names`，会让新命名的网表与器件脚定义脱节。本检查器因此要求 J3 具名引脚、逐位网络及 `crossing_nets=12` 同时一致。

D1 左槽合同是第三独立输入。它禁止把 H2.10 EEPROM A0、H2.13/15 USB Serial/JTAG 或供电脚用作按键；本检查器再要求 J1.10/U1.A0 同在 `SLOT_EEPROM_A0`、pin18 保持单针 NC、H2.13/15 保持单针 NC、按键 H2/GPIO 对应 D1。这样可以阻止 PINMAP 与网表两份文件一起错接保留脚仍报绿。D1 文中关于 V1.2 pin17 给电池充电的叙述**没有被本检查器验证**；该内部路径与输入额定仍另待 V1.2 原理图或实物证据。

## 闸门边界与交接

脚本只读文本，核对 J2/J3 **名义**行列、节距、直径、具名引脚、网表连接和 H2/GPIO 合同。它**不读取 §4.2 的 X/Z 坐标与图形朝向**，不看 EDA 封装焊盘坐标、真实走线、绝缘间隙、接触顺序、J1 配对或误插公差。因此即使将来显示 PASS，也仅是文本合同一致；G1/G2/G3、制造放行与实物验证仍须各自的独立闸门。PINMAP §4.3 自述的 G04 5V/GND 错位短路是另一个已知阻断，不能被本脚本的 PASS 冲销。

给模块板源作者的下一步：在**同一提交**同步 PINMAP、netlist、旧 `check_netlist.py`、模块板 CAD/EDA、底座对接表及受影响固件注释；用此脚本复跑为 0，再跑原有网表自检与跨分支/几何/错位电气检查。最后由 Hiro 或 Grok 对更新后的同一提交独立复核。当前的 `94e393c` 不可据以打板。
