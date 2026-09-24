# G9 证据摘录

冻结时刻：2026-09-24。审查头 `3820c416bca6315a51c276a2d2aff52195d5ccc4`。试合并 `f181a3931b7cacaf6b35b63643056ead2af90b81` 与头 `git diff` 为空。

## 哈希

```
262b52d2b6939020dcb80e549f3d45b1cea8ddd2fc1bd250c85cb1475212aedc  references/official-v12/expansion_v121_zh.pdf  4264551
5728a7614f65e6ca177a98dd9088790032c19e72b128eb0aea3910ee0f93e7f5  C9144_BOOMELE.pdf  582684
9aaf464aa81271f10be0ff7ae8dce64d20964e03e05e67b2758d779f11cd3dba  C124406_Ckmtw.pdf  544021
1f6725d4883ba5df63ab61d479aa932a29cb50bbc609fed3edf420d36f9abe7e  CJT_A2541.pdf  2740660
2b95c41a6dd3ed7571b2ba7eb6c3ebb6e21c844d8ef700eaf9ffe3c056e9e27d  XFCN_C492438.pdf  146864
```

C9144 blob `4fa6ed37c31d990cc077d30cccdafe72dce7f95a` 与 C124406 blob `d336c654763f1415b478b209281549b3ba35804c` 在 PR #54 头和 PR #51 头上相同。

## 官方页（2026-09-24 打开）

中文产品指南扩展 I/O：

- `IN`：5 V 输入，可通过外部电源为 ESP-Mosaico 供电。
- `5V`：5 V 输出，最大 100 mA。
- `3V`：3.3 V 输出，最大 100 mA。

V1.0 用户指南：标题限定 CoreBoard V1.0；`VIN` 可给板载电池充电；H2 pin 17 `5V_IN` = External 5 V input (can power and charge the device)。归档 rst 第 651–653 行相同。

扩展指南第 2 页页眉：本指南仅适用于 1.2.1 版本及以上的 ESP-Mosaico。无文本层，此句来自渲染。

## 图纸读数

C9144，渲染第 1 页：A=33.02（A±0.3），A1=30.72（A1±0.1），B=22.86（B±0.1），罩内短边 6.5±0.1，插合轴塑胶 8.8±0.1。罩内公针伸出未标注。

C124406，渲染第 1 页：图题 `220R-2*XP H=8.5mm`，图号 `Ckmtw-220-00013`。塑胶插合轴 8.5±0.15，短边 5.0±0.15，焊脚 `0.64×0.4±0.03`。图面无 `C124406` 字样。

CJT，PDF 第 15 页文本层，直角段 `A2541WR-2xXP`：2×10 的 A=22.86、B=25.40，A±0.20、B±0.25，`C(6.00±0.20)`，PIN 0.64 SQ，配对为 CJT A2541 housing。

XFCN，第 1 页文本层加侧视渲染：`PZ254R-12-XX`，订购说明 `2x10=20P`，2×10 的 A=22.86、B=25.40（B±0.40），SQ 0.64，端面到针尖 6.0±0.2，端面到折尾中心 6.9±0.2，Current rating 3A，配对为 XFCN PM254。

纸面间隙（推导，中心对齐，罩内空腔对母座外壳）：短边 1.25 mm，长边 4.42 mm。不是配合证明。

## 料号检索

归档 CoreBoard V1.0 PDF 原始字节未找到 `C124406`、`B-2200`、`2200R20`、`B120`、`Ckmtw`。文本摘录第 65 行是「2 * （2 * 10P 2.54’连接座）」。
