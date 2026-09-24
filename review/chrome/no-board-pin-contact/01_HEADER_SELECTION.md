# C24-01：无板方案右角排针首选样件

**结论：** 先用 CJT `A2541WR-2x10P` 打样，采购入口 [LCSC `C5454488`](https://www.lcsc.com/product-detail/C5454488.html)。这是**唯一首选试插样件**，不是已放行的 H2 配对件，也不冻结底座槽口。2026-09-24 查询，`C5454488` 页面同一厂家型号、2×10、2.54 mm、0.64 方针、Gold，显示 1,335 件现货；库存会变化。旧 [JLC `C239341`](https://jlcpcb.com/partdetail/238445-A2541WR2x10P/C239341) 仍列 Extended／Wave Soldering，但 [LCSC 同码页](https://www.lcsc.com/product-detail/C239341.html) 显示缺货；两个料号不能直接当作相同供货承诺，`C5454488` 能否用于嘉立创 PCBA 未证实。无板方案原本也不依赖排针焊在底座 PCB 上，现阶段可单买实物核对。

| 候选 | 原厂尺寸／来源 | 不作为首选的理由或保留问题 |
| --- | --- | --- |
| **CJT A2541WR-2x10P**（LCSC `C5454488`／旧 JLC `C239341`） | [CJT A2541 原厂图 p15](https://www.cjt.com/upload/A2541.pdf)：塑胶长 25.40±0.25 mm、约宽 5.08 mm；插入端 `C=6.00±0.20 mm`；外露弯尾 `E=3.00±0.20 mm`；0.64 mm 方针。两排尾尖图示名义齐平。 | 首选，因为本体小且图纸给外露尾长；**未给两排独立共面度、弯尾尖端镀层保证、针对尾尖重复弹簧压接的寿命**。商品页的 `Gold` 不等于所有切口镀金。 |
| BOOMELE `2.54-2xNAW`／LCSC `C9144` | [原厂图](https://atta.szlcsc.com/upload/public/pdf/source/20250103/91F410755EE890F5F322646B3C21BFAE.pdf)：带罩 33.02±0.30 × 9.0±0.1 mm，外露尾 3.2±0.2 mm，罩体沿插合轴 8.8±0.1 mm。 | 罩有机械可卡优势，但厚／长，罩内有效公针长度未标；不优先按其大外形开槽。 |
| XFCN `PZ254R-12-20P`／JLC `C492438` | [JLC 料页与原厂图入口](https://jlcpcb.com/partdetail/XFCN-PZ254R_1220P/C492438)：塑胶长 25.40±0.40 mm，外露尾 3.0±0.2 mm，0.64 mm 方针。 | 原厂系列允许哑锡或镀金，确切 SKU 的弯尾表面处理未闭环；作为替代样件，不进冻结 BOM。 |

原厂图纸 SHA-256（已在 PR #54 `review/chrome/T20-takeover/sources/` 归档，独立复算）：CJT `1f6725d4883ba5df63ab61d479aa932a29cb50bbc609fed3edf420d36f9abe7e`；BOOMELE `5728a7614f65e6ca177a98dd9088790032c19e72b128eb0aea3910ee0f93e7f5`；XFCN `2b95c41a6dd3ed7571b2ba7eb6c3ebb6e21c844d8ef700eaf9ffe3c056e9e27d`。本分支不重复存 PDF。LCSC 新码 `C5454488` 的单独 PDF 当前未取得，不冒充其哈希。

**配对边界：** `C124406` 仍仅是旧项目对 V1.0 母座的候选，**V1.2 实物 H2 型号 unknown**。[C124406 原厂图](https://atta.szlcsc.com/upload/public/pdf/source/20170821/C124406_1503303322844901560.pdf) SHA-256 `9aaf464aa81271f10be0ff7ae8dce64d20964e03e05e67b2758d779f11cd3dba`；图中 `0.64×0.4` 是母座 PCB 焊脚，不是插孔允收规格。CJT 图纸指定的是自家 housing，未明示跨厂配合。3 A 页面额定也不证明主机 H2 pin17 或 V1.2 `5V_IN` 能承受 1 A。

**样件闸门：** 先用独立母座断电试插，不拿 Mosaico 作首次试错；确认 pin 1、插入深度、是否刮擦／过紧、20 针绝缘与导通。量两排尾尖相对 Z 高差和横向位置；向厂家索取弯尾切口镀层与端面长期压接资料；再以候选弹簧针测接触电阻、压降、反复压接磨损。任何一项不明，不能据此定底座 J2 坐标、针台或可生产 BOM。
