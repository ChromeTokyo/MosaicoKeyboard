# 历史方案：09-21 分立电源链（2026-09-24 降级）

**本目录不是当前设计源，不可按此制造、报价、采购或给主机上电。** 这里的 BQ24074→TPS61023→TPS2553→LM66100 逐件设计、旧 **2×8 J2** 触点场、两针并联 5V/GND 与 −Y 入仓几何，已被 2026-09-24 [D-028/D-029 与现行方案 J](https://github.com/ChromeTokyo/MosaicoKeyboard/blob/sweep/consistency-20260921/review/claude/option-j-seated.md)取代。现行方向用**现成充电/保护/升压模块**，只保留必要的输出限流与反灌阻断；手柄侧 2×10 接触字段固定按 H2 针号，底座撞针沿 +X、整机沿 −Z 入仓。

保留 `POWER_TOPOLOGY.md`、`POWER_BUDGET.md`、`netlist.yaml`、`BOM.csv`、`schematic.svg` 和 `check_netlist.py` 作为**历史计算与曾用假设**记录。旧脚本即使退出 0，也只代表旧网表内部自洽，不证明现行电气、插配、失配或制造安全。旧 BQ24074/TPS61023 离散链本身的错误/未核项也不能因“归档”被追认为正确。当前 [Chrome C5 筛选](https://github.com/ChromeTokyo/MosaicoKeyboard/blob/chrome/straight-header-side-contact/review/chrome/straight-header-side-contact/C5_POWER_MODULE.md)尚未选出七项全过的成品模块，所以**不存在可以从本目录直接迁移的生产网表**。

若未来重新考虑分立链，需另立新任务、以当时现行 ICD 与 H2 实物额定为起点，对电池温感、启动/持续电流、热、无电池 USB 上电、全行程错针及双 USB 反灌重新独立审核；不得把本历史 `netlist.yaml` 复制成新 PCB 源。
