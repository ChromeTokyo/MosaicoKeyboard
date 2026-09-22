# 2026-09-23 Chrome 接手时项目状态与交回主控的事项

本页是截至 2026-09-23 08:24 JST 的**分支状态快照**，输入 `origin/main=96fd823`。不改主控唯一维护的 `docs/STATUS.md`；其正文仍停留在 2026-09-20，不能用作今日的实时任务板。本文中的“已合入”只说明资料或提案在 main，并不等于审核/制造放行。

## 已有可复用资产

- main 已收进方案 D＋G 的 ICD/假设/G6 测试计划提案、D1 左槽引脚/BSP证据、EEPROM 身份镜像工具及手柄驱动固件提案；`hardware/eeprom/` 的本机 134 字节自检可运行。目标 ESP32-S31 固件、模块板与底座主板**没有**在当前 main 完成可制造的同版电气/机械源。待审 Claude 的四条 `claude/design-d/*` 分支与 `sweep/consistency-20260921` 也未并入 main。
- OpenSCAD 编译/流形记录已随 PR #46 入 main，但所用机械 `.scad` **并未随同一 SHA 入 main 或 sweep**，G2 的几何结果不能由普通新检出直接复跑。原记录还有一个壁厚自检未达到 2.5 mm 的项；不能把“编译成功”称为结构通过。
- 主线仍是 V1.2 左槽模块板＋底座弹簧针；A0 四背部触点架构只作历史。扩展指南明确适用 **1.2.1及以上**，不自动证明出货 V1.2 每条铜线。左槽 pin17 输入额定、pin20 回流、真实双 USB 合并和样机几何都未闭环。

## 本次 Chrome 已接走并推送

| 工作 | 交付 | 必须保留的限制 |
| --- | --- | --- |
| H0 F06/F07 | [D1 物理适用假设](../D1-module-interface/LEFT_SLOT.md)及[D3 双电源合同](../D3-power/TOPOLOGY_REVIEW.md) | 文字接口补齐不等于 Hiro H0 通过，V1.2 铜线/额定仍未实测 |
| D2 | [24C02 首选与供应证据](../D2-eeprom/SUPPLY_CHECK.md)、[烧录/写保护技术复核](../D2-eeprom/TECHNICAL_REVIEW.md) | 首选 C34807；原 WP“写同值”验收无判别力，默认桥冲突；当日分配库存与实物未核 |
| D3 | [纯硬件拓扑、八态、提案数值审查](../D3-power/TOPOLOGY_REVIEW.md) | 提案 Type-C 输入限流未随源能力设定；反馈备选电阻计算错；NTC/返修/额定待设计者修 |
| AS-31-mm-3 | [两份原厂图与 J1 尺寸证据](AS31_J1_SPEC.md) | C9144 是带罩公头，8.8±0.1 mm 是其轴向塑胶尺寸；8.5±0.15 mm 是母座。直接配合仍 unknown |
| D4 准备 | [断电逐点通断规程](D4_PREPOWER_CONTINUITY.md) | 4×4 表仅是待审 PINMAP，模块板网表仍 2×8；不能照此制板或上电 |
| G2 机器闸门 | [draft PR #50](https://github.com/ChromeTokyo/MosaicoKeyboard/pull/50)，从未合入 sweep 出独立分支 | 两脚本假绿已修并通过8项替身回归；真实 SCAD 尚不能同 SHA 复跑、G2 仍 HOLD |

## 当前放行阻断与下一位接手者动作

1. **G1/G2 仍未通过。** [Grok G1 PR #48](https://github.com/ChromeTokyo/MosaicoKeyboard/pull/48) 和 [G2 PR #49](https://github.com/ChromeTokyo/MosaicoKeyboard/pull/49) 都是 CHANGES_REQUIRED；G2 的 fit 有两处实体碰撞与一次超时，J2 错位检查的 EXIT0 只覆盖未钳位 5V→GPIO，约 1.090 mm 的 5V↔GND 仍可达。不能把 #50 的脚本修复等同机械或电气通过。
2. **统一 J2 真源。** 待审 `PINMAP.md` 已写 4×4/Ø2.0，模块板 `netlist.yaml` 仍 2×8/Ø1.8；main ICD 也是旧 2×8 文字。Claude 需在同一提交同步网表、PCB/触点号、ICD、几何、错位电路分析和 G6；Hiro/Grok 必须按最终版本复核。用户截图中“不要删任何一道闸门”的原则在此保持。
3. **机械源与紧固方案闭环。** 将模块和底座 `.scad` 与检查器放在可检出的同一提交；机械作者修实体碰撞、超时、主板与弹簧针小板净空。待审 [PR #47](https://github.com/ChromeTokyo/MosaicoKeyboard/pull/47) 的螺钉/材料裁定尚未并入 main，旧自攻/卡扣保持力计算不能作为当前冻结值。
4. **电源设计源修正。** Claude 的待审底座分支须改 Type-C 能力/输入限流、升压反馈备选数字、真实 NTC 路径、可返修方案；模块板须修 EEPROM WP 默认保护与可判别测试。Chrome 报告只给独立复核意见，未改 Claude 原设计源。
5. **实物与独立复核。** 到货记录 CoreBoard/BaseBoard 板号、槽位方向、J1 样品实际配合、pin17/20 电气边界与 4×4 的可制造接触位置；测量记录按既有 T14 规程。样板仍先做 D4 断电通断，再按 G6 无电池 USB 分步上电。Chrome 作者不能替 Hiro/Grok 签硬件通过。

另有历史 [T02 PR #4](https://github.com/ChromeTokyo/MosaicoKeyboard/pull/4) 仍开着；其证据已核但合入前需先与 main 同步，避免误删 `docs/handoffs/hiro.md`。draft [R0 PR #43](https://github.com/ChromeTokyo/MosaicoKeyboard/pull/43) 与 #47–#49 都是待审材料，不能凭分支文件把其中“裁定”“冻结”字眼当 main 的已生效结论。
