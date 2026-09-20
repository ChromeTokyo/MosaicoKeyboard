# A0 设计状态与交接

基线日期：2026-09-20。

**本项目尚未完成可制造 PCB。现有文件属于电路草案和布局研究，不能直接下单。**

## 已有工作

- 已收集部分官方 ESP-Mosaico 使用文档、原理图及背面图片。
- 已生成 `design/build_design.py` 及其 A0 原理图、布局研究、BOM／引脚网络审核表。
- 已研究按键扩展、电源路径与四触点连接的候选方案。
- 已建立需求、执行计划和后续协作规则。

## 尚未完成

- 没有 Mosaico 实物；模块与触点精确机械约束没有完成确认。
- 没有完成嘉立创 EDA 的成功导入与工程可编辑性验证。
- 没有完成 PCB 布线、ERC、DRC、完整电气审查或实物验证。
- 没有确定最终电池、Pogo 型号和实际工厂装配方案。
- 没有完成外壳模型，也没有制造订单。

## 当前文件含义

| 文件 | 用途 | 限制 |
| --- | --- | --- |
| `design/build_design.py` | 生成实验性 A0 文件 | 仍需电气与格式审核，不能把脚本成功运行视为设计正确 |
| `design/mosaico-dock-schematic.json` | 原理图草案 | EDA 导入与网络一致性尚未确认 |
| `design/mosaico-dock-placement.json` | PCB 布局研究 | 未完成铜线布线，机械尺寸含占位假设 |
| `design/design-netlist.json` | 设计网络与器件数据 | 需与审核后的 EDA 工程逐项对应 |
| `design/bom-review.csv` | 候选器件审核表 | 不是已确认可采购的生产 BOM |
| `design/pin-net-review.csv` | 引脚网络审查输入 | 不是 ERC 或独立审查通过报告 |
| `references/` | 参考文档与库缓存 | 包含研究过程资料，并非全部已采用；应按实际引用建立清单 |

现有生成文件可能未覆盖后续补充的全部库缓存；接手时核对生成脚本、输入与输出是否一致，再形成可复现版本。

## 关键待解决项

| 编号 | 问题 | 对下一步的影响 |
| --- | --- | --- |
| O01 | 触点坐标、直径、间距、模块包络和工作高度缺少完整机械证据 | 阻止 Pogo 与最终板框定位冻结 |
| O02 | 草案中的 2.54 mm Pogo 间距、154 × 64 mm 板框与 54 × 54 mm 模块区域是研究占位值 | 不得作为官方尺寸或生产依据 |
| O03 | 背面图片方向与底座顶视的镜像关系需要带坐标图确认 | 防止供电／地或 SDA／SCL 对位错误 |
| O04 | TCA9517 与 MAX17048 的低电平阈值及噪声裕量存在兼容性疑点，现有接法需要审核 | 未解决前不得冻结 I²C 电路 |
| O05 | 输入限流、充电电流、升压输出、瞬态及热预算还需系统计算 | 不能承诺续航、充电速度或边用边充净充电能力 |
| O06 | 原生 USB-C 与底座供电同时连接时，需要核对完整电源状态和防反灌 | 完成电路审核并在样机中验证 |
| O07 | Mosaico 自身电源开关与底座开关是两个控制点 | 需要明确开机、关机、待机和充电行为 |
| O08 | 电池保护、NTC、插座极性和线束未冻结 | 不能仅按相似插头认定电池兼容 |
| O09 | USB／Pogo 等接口保护、测试点和掉电行为需要完整审核 | 纳入 M2 原理图完成条件 |
| O10 | 器件库下载不等于国内工厂有料且可贴装，部分器件高度影响握把 | BOM 与机械、制造三方同步审核 |

## 候选器件与功能

现有草案研究了 TCA9535、BQ24074、TPS61023、TPS2553、LM66100、TLV75533、TCA9517 与 MAX17048。它们只是候选组合，不是冻结选型。替换器件时必须重新审核引脚、封装、电气条件与空间。

背部电源在官方 CoreBoard 原理图中标为 `5V_IN`；不能把单节电池直接接上并假定等效。原生小电池与底座电池也不能直接并联。底座是否采用独立电量计尚待设计决策，原生电量计不能直接代表底座电池状态。

## 官方参考入口

- [ESP-Mosaico 官方用户指南](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s31/esp-mosaico/user_guide.html)
- [CoreBoard V1.0 官方原理图](https://dl.espressif.com/AE/SCH_SCH_ESP-Mosaico_CoreBoard_V1_0_2026-08-18.pdf)
- [BaseBoard 背面图片](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s31/_images/esp-mosaico-baseboard-back.png)
- [EasyEDA 文档格式参考](https://docs.easyeda.com/en/DocumentFormat/EasyEDA-Document-Format/index.html)

后续审核应记录所用文档版本、页码、器件数据表与结论。图片可用于辨认接口，不能作为无比例尺的精密尺寸依据。
