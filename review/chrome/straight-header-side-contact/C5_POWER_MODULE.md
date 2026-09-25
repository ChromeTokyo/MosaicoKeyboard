# C5：现成电源模块筛选与非 MCU 供电链草案（2026-09-24）

**暂无满足七项判据的原装成品模块，C5 不定案，不输出生产网表。** 最接近的是 Adafruit `6106`；可以先买样件做台架试验，但其电池温度输入在原装板上由固定 10 kΩ 电阻代替电芯 NTC，且成板 5V 纹波/精度、Mosaico 启动电流匹配未验证。最紧急的集成阻断仍是 [C3 落座过程可能电源错针](C3_CONTACT_FIELD.md)；电源模块合格也不能绕过它。

## 七项判据对照

[新分工](../../../docs/WORK-SPLIT-20260924.md)§3.6 的七项是：无轻载自动关断、边充边用、电芯 NTC、5V 精度/纹波、1S 保护、可换修、有现货。以下 `?` 表示资料或实测不足，不能当作通过。

| 候选 | 轻载持续 / 边充边用 | 电芯 NTC | 5V 精度/纹波 | 1S 保护 | 维修/供货 | 判定 |
| --- | --- | --- | --- | --- | --- | --- |
| [Adafruit `6106`](https://www.adafruit.com/product/6106) | 升压 EN 默认可输出、无资料说低负载定时关断；[产品页](https://www.adafruit.com/product/6106)明确 bq25185 power path 与 USB 接入时边供负载边充；轻载实测仍需做 | **不通过**：原厂[开源 `.sch`](https://github.com/adafruit/Adafruit-bq25185-with-5V-Boost-PCB/blob/main/Adafruit%20bq25185%20with%205V%20Boost%20Breakout.sch)显示 `TS/MR`→`THERM`→R16 10 kΩ→GND，2 针电池口；[TI bq25185 §6.3.9](https://www.ti.com/lit/ds/symlink/bq25185.pdf)明言固定 10 kΩ 用于**不需要** TS 温感时 | 标 5V/1A；成板纹波、启动跌落/精度未给；厂商警告**启动瞬间 >200 mA 可使升压停滞**，必须量 Mosaico 启动波形 | 芯片有电池欠压/过流/短路等功能，[指南](https://learn.adafruit.com/adafruit-bq25185-usb-dc-solar-charger-with-5v-boost-board/pinouts)列出；原装 NTC 缺失，不能称完整 | 原板可整板更换；USB-C/螺钉端子/JST 电池口；查询时在售，实时库存会变 | **仅台架样件** |
| [DFRobot `DFR1026`](https://www.dfrobot.com/product-2632.html) | 厂商称 5V 常开、边充边放；但放电时须短按 KEY 开输出，断电/低载后状态须实测 | 官方引脚图只有 VIN/BAT/VOUT/KEY/GND，无贴电芯 NTC 输入证据 | 标 5V/2A；纹波、容差和主机启动情况无成板数据 | 厂商称过流/过压/短路/过温；过温测量位置及电芯低压切断阈值未核 | 25×16 mm、可整板换、在售；需外置 USB-C/接线 | **未通过 NTC/纹波，不能定案** |

Adafruit 6106 的[原厂 `.brd`](https://github.com/adafruit/Adafruit-bq25185-with-5V-Boost-PCB/blob/main/Adafruit%20bq25185%20with%205V%20Boost%20Breakout.brd) `Dimension` 层边框 X=0…29.21、Y=0…19.05 mm，故交主控 M2 的**PCB 板框占位**为 **29.21×19.05 mm**；实际最高器件、USB 插头、线束弯曲、可换修余量另计。`.brd` SHA-256 `653b8636b76a9f31950635950c72c748811e7b3d7258f7a7b1a99ce2cabc7708`；`.sch` SHA-256 `d1f47f395296bb3e6450014745ead0d2665607e3f17d18c433826c5c35a9e039`。TI [`bq25185`](https://www.ti.com/lit/ds/symlink/bq25185.pdf) PDF SHA-256 `c73ed7d63e6532bb05e26df30edd37c6ac2de310c1222a84a77625e15e133684`。这三项是样件版本证据，不是本项目已确认元件的生产 BOM。

若要改装 6106，把 0402 R16 去除、按 TI 指定 25°C/10 kΩ、β(25/85)=3435 K 的电芯贴附 NTC 接入 TS/MR，只能作为**另一个待验证样机方案**：须核断线/短路检测、冷热阈值、线束可靠性、充电电流（原板默认 1A、剪跳线后 500mA）与所购电芯规格。不能把“芯片支持 NTC”写成“原装模块已接电池 NTC”；手焊 0402 的返修门槛也需量产方确认。供货/电池外形未定前，不能把 1500 mAh 占位假设当实际电池型号。

## 两颗外加保护器件与**条件性**电源链

| 功能 | 候选 | 已查证事实／待定 |
| --- | --- | --- |
| 输出限流/故障可读 | TI [`TPS2553DBVR`](https://www.ti.com/lit/ds/symlink/tps2553.pdf)，[LCSC `C55266`](https://www.lcsc.com/product-detail/C55266.html) | `TPS2553` 为**高有效 EN**。R_ILIM 决定限流；TI 表中 20 kΩ 为 1.200–1.375 A，49.9 kΩ 为 0.475–0.565 A，均不能在 H2 p17/p20 额定、Mosaico 启动峰值和温升未知时选定。其反向比较器约 3–7 ms 才关，**不单独承担即时反灌**。原厂 PDF SHA-256 `88e453700cea2b263cdb5b44fce1e883e0f6d3b975457f879ac1423eeea42071`。 |
| 持续反灌阻断 | TI [`LM66100DCKR`](https://www.ti.com/lit/ds/symlink/lm66100.pdf)，[LCSC `C2869734`](https://www.lcsc.com/product-detail/C2869734.html) | TI §8.3.2/Fig.13 的 **Always-ON RCB** 接法是 CE 接 VOUT；输入接限流输出，输出才到 H2 p17。不是把 CE 悬空或误接主机 GPIO。原厂 PDF SHA-256 `83c17370a97b85ecebe20605da0b955d4ff6f9a474e9692b611a6685d7ad0f00`。 |

仅作电源**连接意图**，不是已选模块的可制造 netlist：

```text
底座 USB-C/5V ──→ 候选模块充电＋Power Path ──→ 候选模块持续 5V 升压
                      ↕ 独立 1S 电芯（保护、贴芯 NTC 待选）       │
                                                           TPS2553 限流/FAULT
                                                                  │
                                                           LM66100 反灌阻断
                                                                  │
                                                          H2 pin17 5V_IN
公共 GND ─────────────────────────────────────────────────── H2 pin20 GND
```

全路径**不经过 MCU 软件许可**；5V_IN 不能取自 H2 pin18 `5V_OUT`，也不从 pin19 反送 3.3V。TPS2553 的 `FAULT` 可接可读测试点/灯，不能假定该灯能诊断所有故障。G3 需要主板提供模块输出、限流前后、H2 输入、GND、FAULT 的可触测试点，以及**默认断开主机的分步上电跳接/接插件**；先仅 USB 无电池、接假负载测各级，再接电芯与主机。候选模块能否**无电池仅 USB**稳定升压、其内部 SYS 是否可从外部安全测试，尚未验证；若做不到，则该模块不满足既定 G3 分步验证链。双 USB（底座和 Mosaico 原生）、内置 65mAh 电池、插拔/错接四态、充电热与线束极性都需实物测试。

**下一判定输入：** Mosaico p17/p20 允许电流、主机 USB/电池各态启动电流、所购电池包资料与 NTC/保护/插头极性、模块实物的无电池 USB 起机和 5V 纹波、装入全过程隔离方式。C3/J-IF-03 未关闭前，不做“给 H2 供电”的台架步骤，也不冻结 C6。
