提案 · 未冻结 · 由 Claude 主控（claude-opus-5）组织的双路独立清点 · 待 Chrome 裁定、Hiro／Grok 复核 · 阻断项

# 跨分支一致性全量清点（2026-09-21）

## 这份清单怎么来的

主控手工发现触点场 X 差 19.5 mm 之后，起了一次**双路独立清点**——两个互不通气的独立
检查，一路从 ICD 的「留空／proposed」条目出发反查谁填了什么，一路不看 ICD 直接对四个
设计分支做穷举比对。两路都被要求「按物理含义匹配，不要只按变量名匹配」。

**结果：40 条不一致，其中 22 条阻断。** 手工只找到 3 条。

这不是说四个分支做得差——它们各自的自检都通过。**问题是此前不存在任何跨分支校验，
每个分支只查自己内部自洽。** 本清单同时也是那个缺失机制的第一次执行。


## 第 1 路清点小结

【结论】ICD-0.2-DRAFT 里标 proposed／待填／由某任务给值／unknown 的条目共 22 处，其中被两个及以上文件各自填了值的有 13 处，**其中 8 处不一致，3 处是主控此前未发现的阻断项**。「还有没有别的」的答案是：有，而且比已知的那一处更多。已验证一致、不必再查的有 9 处（H2 逐针合同、KEY_*→GPIO 表、J2 逐针分配与行列方向、DOCK_PITCH/COLS/ROWS、Mosaico 外形 AS-01、SLOT_FACE_X、SLOT_ROW_AXIS=Y、网络命名、EEPROM 镜像格式）。

【三个新的阻断项，按修复顺序】
1. **触点场 Z 向也完全不重叠（差 4.61 mm）**。CONFLICT-pogo-field.md 只比了 X 和 Y，漏了 Z0。这意味着即使采纳该文档推荐的选项 3 把 X 对齐，弹簧针仍然一根碰不到焊盘。根因是 module 侧的行 A Z 跟随右角公头反推出的槽板中面 −4.61，dock 侧直接假设场心在 Z=0。
2. **模块壳体整体塞不进落入槽**：X 向缺 25.65 mm、Z 向缺 4.52 mm。已知冲突只比了裸板 FIN_L（差 22 mm），实际要装进去的是 module_shell 的 35.0×48.5×18.1 包络。
3. **保持力方案两边互斥**：模块侧按「底座卡扣抓住、释放键松开」建立承力闭环（≥30 N），底座侧做的是用户手动扣的上压框，壳体上没有任何卡爪。加上 MD-05（Mosaico 本体柔性支承）在 dock 侧完全未实现 —— MATING.md 自己写明这一条不满足则「方案 D＋G 的承力假设不成立」。

另外查出 dock_shell.scad 内部两处几何写错（四角硬限位柱的 Y 起点／尺寸方向使柱顶比声明的配合面高 2.6 mm；−Z 侧两柱少减一个 2.4 mm 未贴槽壁），以及 CONFLICT-pogo-field.md 第 4 节推荐方案里 USB-C 余量算式把焊盘半径写成了直径 —— 真正卡死的不是焊盘而是触点板地板缺口，它已经侵入原生 USB-C 直通道 0.89 mm，而 dock_shell.scad 的 assert 表没有这项检查。

【关于公差】按您说的卡尺还没到，公差类的三条（DOCK_X_TOL 0.45/0.35、焊盘 Ø1.8/Ø2.0、名义压缩 1.20/1.30）本来就要等 AS-01/AS-04/AS-22 实测才能定，我按非阻断排在后面了。好消息是上面三个阻断项**一件仪器都不需要**——它们是我们自己四份文件之间的互相矛盾，今天就能裁定。

【流程】CONFLICT-pogo-field.md 第 6 节的判断是对的：ICD 每个「由某任务给值」的空位必须指定唯一给值方、其余文件 include 引用。本次全量扫描的结果是这条机制的量化依据——一处留空平均引出 1.6 个互不相干的真值。建议把「两个机械分支的 echo 输出逐行比对」做成合并前必过项，并给 dock_shell.scad 补上「触点板缺口 ∩ USB-C 通道 = ∅」「限位柱顶面 = 配合面」两条 assert。

【一处需要主控确认的口径差异】本次任务书写「可用 GPIO 12 个 {55,53,19,48,18,13,17,12,16,**14**,15,4}」，但 ICD §2 与 PINMAP §1 都是 **11 根 {55,53,19,48,18,13,17,12,16,15,4}**，GPIO14 是 H2 pin 10 的 EEPROM A0，ICD 明文禁止任何 KEY_* 落在其上。仓库文件内部一致，差异只在任务书那一句，请勿据任务书的 12 根做下游分配。

【已读文件，均只读未改】
/Users/chrome/mosaico/hardware/ICD-0.2-DRAFT.md、/Users/chrome/mosaico/hardware/ASSUMPTIONS.md
/private/tmp/wt-mech-module/mechanical/module-board/{module_board.scad, module_shell.scad, MATING.md, check_scad.py}、/private/tmp/wt-mech-module/mechanical/test-coupons/fit_ladder.scad
/private/tmp/wt-mech-dock/mechanical/dock-shell/{dock_shell.scad, keycaps.scad, CONFLICT-pogo-field.md, check_board_outline.py}
/private/tmp/wt-module-board/hardware/module-board/{PINMAP.md, netlist.yaml, DESIGN_NOTES.md, BOM.csv, gen_schematic.py}
/private/tmp/wt-dock-board/hardware/dock-board/{netlist.yaml, DESIGN_NOTES.md, POWER_BUDGET.md, POWER_TOPOLOGY.md, BOM.csv}
两个 SCAD 均实际编译取 ECHO（module_board、module_shell、dock_shell 全部 manifold 无错），dock 的 board_dxf 导出后跑 check_board_outline.py 全部通过——**每个分支的自检都是过的，这正是问题所在：没有一处做跨分支校验。**


## 第 2 路清点小结

在主控已手工发现的三条（触点场 X 差 19.5 mm、单针压力 0.6 vs 0.9 N、名义压缩 1.20 vs 1.30 mm）之外，我按「同一物理量」穷举比对四个分支，又找出 25 条，其中 13 条阻断。

最重的一条是**触点场 Z 起点 DOCK_PIN_FIELD_Z0 差 4.61 mm**（module_board.scad:238 的 −3.34/−5.88 对 dock_shell.scad:50 的 +1.27/−1.27），CONFLICT-pogo-field.md 第 1 节的表里没有它。含 Ø2.0 焊盘后两组仍差 1.07 mm 不重叠——也就是说**即使按选项 3 把 X 对齐，Z 上照样一根针碰不到焊盘**。根因同类：模块侧把行中心挂在槽板中面 −4.61（由 J1 右角公头近排针高反推），底座侧取对 Mosaico 厚度中面对称。

其余阻断项按性质分四类：
一、几何包络类（与 X 冲突相互独立，选项 3 解决不了）：模块壳体 Z 包络 18.05 vs 落入槽内腔 12.18（−Z 干涉 4.52、+Z 干涉 1.35，且要穿过前后壳分型面）；模块领口上缘 +24.295 vs 上压框压面 +22.595 干涉 1.70；模块前唇与底座前壳压边抢同一条 2.0 mm 屏面带、Z 向叠 1.70；硬限位面 −24.195 vs −23.195 差 1.00。我用 OpenSCAD 把模块壳体包络与 dock_shell 求交，实测同时撞上外壳、槽壁、上压框、螺柱、D-pad 导向套、限位柱六处。
二、接口要求无人承接：MATING.md 交给底座的 MD-01/02/04/05 与 DB-01 在 dock_shell.scad 与 dock-board/netlist.yaml 里基本没有对应物——30 N 卡扣保持力对 0（底座改用可拆上压框，且未给任何保持力数值）；两根 Ø3.0 定位销与底座主板 Ø3.05 定位孔对 0，且按给定坐标实测撞 D-pad 键帽导向套与前后壳螺柱；「销与弹簧针同一张 Gerber ±0.10」这个换来 1.35 倍安全裕度的前提，在底座「弹簧针在独立小板上 90° 半孔焊」的实现下不成立。
三、电气要求与机械窗口打架：dock-board 的 AS-31-dock-8 要求 J2 列 2 用高 0.5 mm 的先接地针型，而 MATING.md 第 5.3 节的行程窗口是按 16 针等高算的——列 2 名义压缩 1.70（窗口上限，余量 0）、最坏 2.20 超过全行程 2.00，列 2 打底，整机落不到位。
四、硬件三份文件未跟上机械的改动：J2 焊盘 PINMAP.md:119 / netlist.yaml:68,190 / BOM.csv:15 全是 Ø1.8，而 module_board.scad:117 与 MATING.md 已改 Ø2.0——Gerber 从前者出，照打余量归零；轻触开关 dock_shell 按 6.0×6.0×4.3 建模，BOM 选的是 TS-1088 类 3.9×3.0（高度未给，未知），整条键帽行程链与 Ø4.5 顶推柱都落空。

关于任务点名的 CK-06：它查的**不是**同一组针的物理位置。dock-board/check_netlist.py:48-52 的 PINMAP_KEYS 是 PINMAP.md 第 2 节的硬编码副本，脚本从不读 PINMAP.md 也不读模块板网表，全文不含任何坐标，结构上不可能发现触点场冲突。我另写脚本把 PINMAP.md 表、module-board/netlist.yaml、dock-board/netlist.yaml 三处（含 nets、key_map、j2_contract）逐针比过：10 个键的 KEY↔H2 针↔GPIO↔J2 焊盘↔J3 位零差异，16 个 J2 焊盘网名也完全一致。逻辑分配是干净的，坏的只是「同名焊盘落在哪」。

关于公差：您说卡尺没到、公差晚点定——我把涉及公差取值的三条（DOCK_X_TOL 0.45 vs 0.35 vs 实现 RSS 0.434/最坏 0.939；公差链缺「小板↔主板焊接对位」一环；标定件阶梯最小 0.10 覆盖不到设计用的 0.05）都只登记差异与缺口，没有给建议值，等实物到手实测再定。另有 3 条标「未知」不编数：底座 USB-C 连接器本体高度、TS-1088 开关高度、电池插座坐标。

我只读未写，四个 worktree 与 main 的文件一个字没改。


---

# 阻断项（22 条）

## 1. 触点场 X 起点 DOCK_PIN_FIELD_X0（ICD §1「proposed 参数，由机械任务给值」）

**各方取值**：mech-module：−45.485（module_board.scad:237 派生，echo「ICD 第 1 节待填参数」）；mech-dock：−26.00（dock_shell.scad:47，AS-31-mechdock-4）

**差异**：19.485 mm；8 列场分别占 X[−45.485,−27.705] 与 X[−26.00,−8.22]，两段完全不重叠

**成因**：ICD §1 把这三个参数留空标「由机械任务给值」，两个机械分支各自填。mech-module 为规避 AS-22（原生 USB-C 位置未知）把触点板整体移出 Mosaico 投影；mech-dock 为不吃掉左握把把它放在 Mosaico 正下方。主控已发现，记录在 CONFLICT-pogo-field.md。

## 2. 触点场行 A 的 Z 坐标 DOCK_PIN_FIELD_Z0（同一 ICD §1 留空条目，CONFLICT-pogo-field.md 未记录）

**各方取值**：mech-module：−3.34（module_board.scad:238 = FIN_MID_Z + 1.27，跟随槽板中面 −4.61）；mech-dock：+1.27（dock_shell.scad:50，直接假设关于 Z=0 对称）

**差异**：4.61 mm；行 A/B 的 Z 区间 module=[−5.88,−3.34]，dock=[−1.27,+1.27]，最近的针（dock 行 B −1.27）与最近的焊盘（module 行 A −3.34）相距 2.07 mm，而 Ø2.0 焊盘半径 1.0 ＋ Ø0.9 针尖半径 0.45 = 1.45 mm

**成因**：Z 向同样完全不重叠，与 X 向是独立的第二个不重叠。根因不同：module 的行 A Z 由右角公头两排针高（AS-31-mb-2，J1_ROW_NEAR_H = 2.54）反推出的槽板中面 −4.61 决定，dock 直接假设场心在 Z=0。**即使 X 向按 CONFLICT 文档的选项 3 对齐，Z 向仍然一根针都碰不到焊盘。**这一条是新查出的，现有冲突记录里没有。

## 3. 配合面高度 DOCK_PIN_FIELD_Y ／ 弹簧针自由针尖 Y（同一 ICD §1 留空条目）

**各方取值**：mech-module：配合面 −24.095（module_board.scad:156 PAD_FACE_DROP=1.5 → :220/:239），要求自由针尖在 −22.895（MATING.md:411 DB-03）；mech-dock：配合面 −25.795（dock_shell.scad:35 MODULE_UNDER_Y=3.20 → :188/:193），自由针尖 = POGO_PCB_Y_TOP(−28.995) + POGO_FREE_H(4.50) = −24.495

**差异**：配合面差 1.70 mm；自由针尖差 1.60 mm。按 module 的配合面 −24.095 配 dock 的自由针尖 −24.495，针尖比焊盘面低 0.40 mm → 压缩量为负，完全不接触

**成因**：CONFLICT-pogo-field.md 记了 1.70 mm 这个差，但没换算成「净 0.40 mm 不接触」。两侧各自把「模块底面比 Mosaico 底面低多少」当自由量填了（1.50 vs 3.20），ICD 只写参数名不写值。

## 4. 模块组件在 −X 与 Z 方向占用的体积（ICD ME-D-08／MD-06 接口要求，ICD 未给数）

**各方取值**：mech-module：壳体包络 X[−53.595,−18.595]、Y[−24.195,+24.295]、Z[−10.610,+7.440]（module_shell.scad echo，MATING.md:416 MD-06），即超出 Mosaico −X 面 31.0 mm、Z 向 18.05 mm 厚；mech-dock：MODULE_STACK_X = 5.00（dock_shell.scad:32），落入槽内腔 X[−27.945,+22.945]、Z[−6.09,+6.09]（dock_shell.scad:186-190）

**差异**：X 向缺 25.65 mm（−53.595 vs 槽左壁 −27.945）；Z 向缺 4.52 mm（−Z 侧）与 1.35 mm（+Z 侧）；Y 向壳体领口高出 Mosaico 顶面 1.70 mm

**成因**：CONFLICT-pogo-field.md 只比了槽板 FIN_L 27.0 vs MODULE_STACK_X 5.0（差 22.0 mm），漏了模块**壳体**（module_shell.scad）比裸板还大，以及 **Z 向也放不进去**。按现在的文件，装了模块壳的 Mosaico 根本塞不进落入槽，且 dock 的上压框压脚（dock_shell.scad:556-560，落在 Y=+22.595、X[−27.945,−15.945]）会先撞上壳体领口而不是压在 Mosaico 顶面。

## 5. 触点板外形（ICD 第 0.2 节要求由 mech 给值，netlist 的 pad_board.outline_params）

**各方取值**：mech-module：PAD_BOARD_L = 26.0 (X) × PAD_BOARD_W = 8.0 (Z)（module_board.scad:170/172）；mech-dock：CONTACT_PCB_W = 22.00 (X) × CONTACT_PCB_D = 9.00 (Z)（dock_shell.scad:37-38）

**差异**：X 差 4.0 mm，Z 差 1.0 mm

**成因**：dock_shell.scad:326-329 按 22×9 在落入槽地板上开缺口（实际开到 24×11），module 的板是 26 宽 —— 26 > 24，触点板过不去地板缺口。两边都把「触点板多大」当自己的自由量填了，ICD 只列参数名。

## 6. 配合面 Y 的物理落实：底座四角硬限位柱高度（ICD §3.3 一级防呆 C／MD-01）

**各方取值**：mech-module 要求：硬限位面 Y = −24.195 ± 0.15（MATING.md:411 MD-01）；mech-dock 实现：dock_shell.scad:345-352，柱起点 Y = BAY_Y_FLOOR = −25.795、Y 向尺寸 2.6 → **柱顶 Y = −23.195**，与它自己注释「高度 = 配合面（−25.795）」不符；且 −Z 侧两柱放在 Z∈[−3.69,−1.29]（应为 [−6.09,−3.69]），未贴槽壁

**差异**：dock 柱顶 −23.195 比 module 要求的 −24.195 高 1.00 mm，比 dock 自己声明的配合面 −25.795 高 2.60 mm；−Z 侧两柱位置偏 2.4 mm

**成因**：这是 dock_shell.scad 内部的两处写错（Y 起点＋尺寸方向、−Z 侧少减一个 2.4），编译不报错所以自检没抓到。后果是「配合面高度由谁决定」在底座侧根本没落实：柱顶 −23.195 比 Mosaico 底面 −22.595 还低 0.6 mm，什么也挡不住，弹簧针压缩量无定义。与上一条 1.70 mm 的参数分歧是两回事，必须分别修。

## 7. 整机对模块的保持力实现方式（ICD 未指定，两边各自设计）

**各方取值**：mech-module：两处 0° 正锁卡扣，X=−36.595、Z=+7.440/−10.610，各 ≥15 N，合计 ≥30 N，配左握把外侧释放键行程 2.5 mm（MATING.md:412 MD-02、:417 MD-07）；mech-dock：可拆上压框，两侧舌片插槽壁竖槽＋正面弹性卡扣＋指扣＋系绳孔（dock_shell.scad:536-573），底座壳体上无任何卡扣、无释放键、无卡爪让位槽

**差异**：两套互斥方案；模块壳上的卡扣槽（module_shell.scad:75-79，宽 8.0×深 1.2×锁止面 1.5，Y=−19.0）在底座上没有对应卡爪

**成因**：弹簧针总压力 9.6～14.4 N 远大于 Mosaico 自重 0.32 N（module_board.scad 检查 9），必须有主动保持力。现在模块侧按「卡扣被底座抓住」设计承力闭环，底座侧按「用户手动扣上压框」设计 —— 两边都没有实现对方的件，照现在打样，模块壳上的卡扣槽是空的，上压框又压不到 Mosaico 顶面（见上文第 4 条）。另外 MATING.md:209 的硬要求 MD-05（Mosaico 本体柔性支承）在 dock_shell.scad 中也完全没有实现，MATING.md:20 明说「不满足时方案 D＋G 的承力假设不成立」。

## 8. J2 列 2（DOCK_GND）「地先接触」长行程针与弹簧针行程窗口（ICD §3.3 留「proposed 两条路线由底座任务择一」）

**各方取值**：dock-board 择路线一：列 2 工作高度比其余列多约 0.5 mm（DESIGN_NOTES.md:96、netlist.yaml:79-80 AS-31-dock-8）；mech-module 的行程窗口按全部 16 针等高算：名义压缩 T=1.20、Y 向最坏公差 t=±0.50、全行程 S=2.0、不打底余量 m=0.3（MATING.md:266-279，module_board.scad:126-139）；mech-dock 只有一个 POGO_WORK_H=3.20 给全部 16 针（dock_shell.scad:55-56）

**差异**：列 2 名义压缩变 1.70 mm，最坏 2.20 mm > 全行程 2.0 mm，超出 0.20 mm；判据②上限是 S−m = 1.70，名义值已顶到上限

**成因**：ICD 把「先接触次序」留成二选一，dock-board 选了路线一但没有回头核对 mech-module 刚刚收紧到 [1.95, 2.10] 的行程窗口，mech-dock 也没给列 2 留高度差。后果：最坏公差下两根 GND 针打底变成刚性支点，把整机顶起 0.2 mm，其余 14 针压缩量全部下降 → 十键接触不可靠。修法二选一：列 2 改为高 0.2 mm 以内，或按 MATING.md:293 第 5.4 节收紧 Y 向公差链。

## 9. DOCK_PIN_FIELD_Z0（触点场行 A 的 Z 坐标）

**各方取值**：module_board.scad:238 → DOCK_PIN_FIELD_Z0 = FIN_MID_Z + 2.54/2 = −3.34，行 B = −5.88（编译 ECHO「J2 行 A Z = -3.34  行 B Z = -5.88」）；dock_shell.scad:50 → DOCK_PIN_FIELD_Z0 = +1.27，行 B = −1.27（编译 ECHO「行 A/B Z = 1.27 / -1.27」）

**差异**：4.61 mm（Z 向）；含 Ø2.0 焊盘后模块行 A 覆盖 Z[−4.34,−2.34]，底座最近的行 B 针在 Z=−1.27，两者仍差 1.07 mm，不重叠

**成因**：与已发现的 X 向 19.5 mm 是同一类漏洞、但主控的 CONFLICT-pogo-field.md 第 1 节表里没有这一条。根因：模块侧把行中心挂在槽板中面 FIN_MID_Z = −4.61（由 J1 右角公头近排针高 2.54 反推，module_board.scad:204-207），底座侧则直接取对 Mosaico 厚度中面对称（Z=0）。即使把 X 冲突按选项 3 解决，Z 上仍然一根针碰不到焊盘。

## 10. J2 焊盘直径 DOCK_PAD_D / AS-31-mb-3

**各方取值**：Ø2.0：module_board.scad:117（2026-09-21 由 1.8 改 2.0）、MATING.md:335、:341、:421（MB-01）、:442；Ø1.8：PINMAP.md:119、module-board/netlist.yaml:68（假设清单）与 :190（J2 package = PAD-ARRAY-2x8-P2.54-D1.8）、module-board/BOM.csv:15（D1.8）

**差异**：0.20 mm（直径）；允许偏移 0.55 vs 0.45 mm；相邻焊盘净间距 0.54 vs 0.74 mm

**成因**：Ø2.0 只在机械分支执行了，硬件分支的三份文件（PINMAP、netlist、BOM）全部还是 Ø1.8——而 Gerber 是从 netlist/PINMAP 出的。按 Ø1.8 打板时 module_board.scad 的[检查 6]余量 = 0（MATING.md:335 写作 0.016 mm），等于不通过。顺带 MATING.md:389 给的触点场外缘 X[−46.385,−26.805] 也还是按 ±0.9 半径算的，与自己第 6.3 节的 Ø2.0 不一致（各差 0.10 mm）。

## 11. 触点板外形（PAD_BOARD_L × PAD_BOARD_W / CONTACT_PCB_W × CONTACT_PCB_D）

**各方取值**：module_board.scad:170（FIN_L=26.0→:224 PAD_BOARD_L）与 :172（PAD_BOARD_W=8.0）→ 26.0 (X) × 8.0 (Z)，ECHO「PAD_BOARD_L = 26  PAD_BOARD_W = 8」；dock_shell.scad:37-38 → CONTACT_PCB_W = 22.00 (X)、CONTACT_PCB_D = 9.00 (Z)

**差异**：X 差 4.0 mm、Z 差 1.0 mm

**成因**：底座落入槽地板给触点板留的缺口按 CONTACT_PCB_W+2 = 24 mm 开（dock_shell.scad:326-329），实际板 26 mm 过不去。两边各自填了 ICD 里同一个「触点板外形」参数，谁也没引用对方。另外 Z 向中心也不同：模块板 Z ∈[−8.61,−0.61]（中心 −4.61），底座缺口 Z ∈[−4.5,+4.5]（中心 0）。

## 12. 模块壳体 Z 向包络 vs 落入槽 Z 内腔

**各方取值**：module_shell.scad:127（SHELL_Z_HI = +7.44）、:129（FOOT_Z_LO = PAD_Z_MIN−2.0 = −10.61），ECHO「壳体包络 … Z [-10.61 , 7.44]」；dock_shell.scad:189-190（BAY_Z_MIN = −6.09、BAY_Z_MAX = +6.09）

**差异**：包络 18.05 mm vs 内腔 12.18 mm；−Z 侧干涉 4.52 mm、+Z 侧干涉 1.35 mm

**成因**：模块壳体足部为了包住 8 mm 宽的触点板向 −Z 加宽到 −10.61，领口唇又向 +Z 凸到 +7.44；底座落入槽只按「Mosaico 厚度 11.48 ＋ 单边 0.35 间隙」开 12.18 mm。而 −6.09 同时是前后壳分型面 Z_SPLIT（dock_shell.scad:182），模块足要穿过分型面进后壳。这条与 X 向 22 mm 的占用差是**独立**的两笔账，选项 3 只解决 X。用 OpenSCAD 把模块壳体包络与 dock_shell 求交，实测同时撞上 shell_only、bay_walls、top_frame、screw_bosses、buttons_guides、bay_keying_and_stops 六处。

## 13. 模块领口上缘 Y vs 上压框压面 Y

**各方取值**：module_shell.scad:122 → SHELL_TOP_Y = MOSAICO_Y_HI + LINER(0.5) + COLLAR_LIP_T(1.2) = +24.295，ECHO「壳体包络 … Y [-24.195 , 24.295]」；dock_shell.scad:215 → FRAME_Y0 = MOSAICO_H/2 = +22.595（压框压脚落面，:556-559）

**差异**：1.70 mm（Y 向干涉）

**成因**：模块壳体的领口唇翻过 Mosaico 顶面；底座上压框的压脚按「压在 Mosaico +Y 面」设计，X 范围 −27.745…−15.745 与模块壳体 X ≤ −18.595 有 9.15 mm 重叠。结果压框先压到模块领口而不是 Mosaico，压紧力路径和 MATING.md 第 4 节的承力闭环全都落空。

## 14. 屏面压边带（COLLAR_LIP_FRONT vs BEZEL_OVERLAP）

**各方取值**：module_shell.scad:54 → COLLAR_LIP_FRONT = 2.0，前唇覆盖屏面 X ∈[−22.595, −20.595]，唇顶面 Z = SHELL_Z_HI = +7.44（:127）；dock_shell.scad:77 → BEZEL_OVERLAP = 2.00 → :209 WIN_X_MIN = −20.595，前壳内表面 Z = Z_FRONT_OUT − WALL = +5.74

**差异**：两件抢同一条 2.0 mm 宽的屏面压边；Z 向干涉 1.70 mm

**成因**：两个数值相同（都是 2.0），但覆盖的是同一条屏幕边带——X 区间算出来完全重合（−22.595…−20.595）。模块领口唇 1.2 mm 厚坐在这条带上，底座前壳的压边又要坐在同一条带上，Z 上必然叠 1.70 mm。这是「数值相同却仍然冲突」的一条，逐个数比对发现不了，必须按覆盖区间比。

## 15. 硬限位面 Y（落入到位后整机坐在哪个高度）

**各方取值**：module_shell.scad:121 → SHELL_FOOT_Y = MODULE_PAD_FACE_Y − 0.10 = −24.195，ECHO「硬限位面 SHELL_FOOT_Y = -24.195」；MATING.md:411（MD-01）要求底座给 Y = −24.195 ± 0.15；dock_shell.scad:345-351 四角硬限位柱顶面 = BAY_Y_FLOOR + 2.6 = −23.195

**差异**：1.00 mm

**成因**：底座的限位柱是从落入槽地板（−25.795）长 2.6 mm 起来的，柱顶 −23.195；模块要求的落地面是 −24.195。差 1.00 mm 会直接改变弹簧针实际压缩量，把 MATING.md 第 5 节 ±0.50 mm 的 Y 向链整条推翻。另外底座这四根柱顶 −23.195 比 Mosaico 底面 −22.595 还低 0.6 mm，所以它们其实谁也顶不到，dock_shell 自己也没自洽。

## 16. 保持力机构与保持力数值

**各方取值**：MATING.md:361-363 与 :412（MD-02）：底座侧悬臂卡爪两处，X = −36.595、Z = +7.440 / −10.610，各 ≥ 15 N，合计 ≥ 30 N，0° 正锁；配合槽见 module_shell.scad:75-79（CATCH_W 8.0 / CATCH_D 1.2 / CATCH_H 1.5 / CATCH_Y −19.0）。dock_shell.scad 全文没有任何卡扣，保持靠可拆上压框（:147-152 FRAME_*、:539-573），且**未给出任何保持力数值**

**差异**：30 N 的需求对 0（底座未给值）；机构形式完全不同（卡爪正锁 vs 上压框舌片）

**成因**：两个分支对「谁把整机压在弹簧针上」给了互斥的答案。模块侧把 30 N 当成对底座的硬接口要求并据此算了力偶（MATING.md 第 4.4 节），底座侧则把这件事交给了一个要用手插拔的上压框，卡扣槽 Z = +7.440 / −10.610 这两个面在底座落入槽里根本不存在（见 Z 包络那条）。

## 17. 落入导向定位销 / 底座主板 Ø3.05 定位孔

**各方取值**：MATING.md:119-129 与 :418（DB-01）：Ø3.0 销 ×2，(X,Z) = (−48.50, +2.30)、(−31.00, +2.30)，露出塑件 8.0 mm，底座主板开 Ø3.05 孔且与 J2 焊盘同一 Gerber；module_shell.scad:65-70 对应导向孔 Ø3.20 / 3.20×4.20。dock-board/netlist.yaml:107-117 的 board 段只有 layers/thickness/finish/outline_params，无任何机械孔；dock_shell.scad:697-702 的 BOARD_MH 只有 4 个 Ø2.2 固定孔

**差异**：需求 2 个 Ø3.05 定位孔 ＋ 2 根 Ø3.0 销 → 底座两份文件里都是 0 个；按给定坐标还与底座实体干涉

**成因**：整个落入导向的基准在底座侧没有承接方。我把两根销按 MATING 给的坐标建模后与 dock_shell 求交实测：销 A(−48.50,+2.30) 撞 buttons_guides()（D-pad 键帽导向套，销外缘进到 D-pad 十字臂边 0.25 mm 内）；销 B(−31.00,+2.30) 同时撞 bay_walls()（落入槽壁）与 X=−32 的前后壳螺柱（dock_shell.scad:397-400 的 boss_pts，Ø5.6）。

## 18. 弹簧针焊盘所在的 Gerber（公差链第 6.1 节 a 项的前提）

**各方取值**：MATING.md:120、:135、第 6.1 节 a 项（:318）：弹簧针焊盘与定位销孔「同一张 Gerber」，相对位置公差 ±0.10 mm；dock_shell.scad:736-737 ECHO「弹簧针小板：X 中心 = -17.11 宽 17.78 以 90 度半孔焊在板**元件面**，小板上表面 Y = -28.995」，主板本身是 XY 面板、中面 Z = −3.4（:665）

**差异**：公差链缺一环：小板↔主板的焊接对位（量级 ±0.2 mm 以上，未定值）

**成因**：底座实现里弹簧针根本不在主板 Gerber 上，而在一块 90° 半孔焊的独立小板上。而且主板法向是 Z，一根轴向 +Y 的定位销在几何上无法由这块板上的孔来定位。MATING.md 第 6.1 节正是拿「同一 Gerber ±0.10」换来了 1.35 倍安全裕度，这个前提在底座的实现下不成立，最坏累积 0.939 mm 要重算。**这一条的新数值要等实物与首版打印件实测才能定（卡尺未到）**，现在只能记为链条缺项。

## 19. J2 列 2（DOCK_GND）先接地针型的 +0.5 mm 工作高度

**各方取值**：dock-board/netlist.yaml:79（A2/B2 note「本列用行程更长针型」）与 :430、DESIGN_NOTES.md:96-98（AS-31-dock-8：列 2 工作高度比其余列多约 0.5 mm）、BOM.csv:82（备选 2 两条 1×8 就是为满足它）；MATING.md:266-279 的窗口只有一组值：名义压缩 T = 1.20、全行程 S = 2.00、判据②「最大工作压缩 ≤ S − 0.3 = 1.70」；dock_shell.scad:55-56 也只给一组 POGO_FREE_H 4.50 / POGO_WORK_H 3.20

**差异**：列 2 名义压缩 1.70 mm（窗口上限，余量 0），最坏 2.20 mm > 全行程 2.00 mm，超 0.20 mm

**成因**：地先接触是电气侧的硬要求，但机械侧的 Y 向行程窗口是按 16 根针等高算的，从来没有为列 2 留 0.5 mm。代入 MATING.md 第 5.3 节判据：列 2 的 T₂ = 1.70，±0.50 公差下实际 1.20…2.20，最坏值已经超过全行程本身 → 列 2 打底，整机落不到硬限位，其余 14 根针的压缩量随之失控。dock_shell 自己也没体现这 0.5 mm，等于三份文件三个说法。

## 20. 轻触开关封装与高度

**各方取值**：dock_shell.scad:109-113 → SW_SIZE 6.00 × 6.00、SW_H 4.30、SW_ACT_D 3.50、SW_TRAVEL 0.25（AS-31-mechdock-19「6.0 x 6.0 x 4.3 mm 轻触开关」），派生 :214 SW_ACT_Z = BOARD_Z_FRONT + SW_H = +1.70；dock-board/netlist.yaml:433-442 → package「SW-SMD 3.9×3.0 mm」；BOM.csv:84-93 → TS-1088-AR02016（C720477），备注「行程、操作力、寿命未核」，**高度未给**

**差异**：本体 6.0×6.0 vs 3.9×3.0 → 2.1 × 3.0 mm；柱头顶面 Z 依赖的 SW_H = 4.30 在硬件侧无对应值（未知）

**成因**：整条键帽行程链都挂在 SW_H = 4.30 上：keycaps.scad:42-47 把法兰位、限位行程 0.50、帽面顶 Z = +9.24 全部由 SW_ACT_Z = +1.70 推出，keycaps.scad:49 的 assert 也只校验 STOP_TRAVEL(0.5) > SW_TRAVEL(0.25)。TS-1088 类 2 端 SMD 开关比 6×6 插件式矮得多（具体高度两份文件都没写，**未知，不编**），柱头顶面一旦低于 +1.70，键帽就按不到开关。另外 keycaps.scad:22 的顶推柱 POST_D = 4.50 比 3.9×3.0 开关的短边还宽 1.5 mm，会压在开关外壳而不是柱头上。

## 21. 底座主板固定孔位 vs 外壳里实际造出的主板支撑柱

**各方取值**：dock_shell.scad:697-702 → BOARD_MH = (±75.1, 24.5)、(±75.1, −60.1) 共 4 个 Ø2.2（ECHO「固定孔 Ø2.2 x4，中心 = [[-75.1, 24.5], [75.1, 24.5], [-75.1, -60.1], [75.1, -60.1]]」）；dock_shell.scad:366 board_rails() 实际造出的支撑柱在 (±70, 20)、(±70, −45)、(±36, −52) 共 6 处；dock_shell.scad:393-394 前后壳螺柱在 (±73.5, 24.0)

**差异**：4 个孔与 6 根柱无一对应；固定孔 (±75.1, 24.5) 与 Ø5.6 前后壳螺柱 (±73.5, 24.0) 中心距仅 1.68 mm，需 ≥ 3.9 mm

**成因**：这是同一个文件内导出给 PCB 用的锚点表与实际几何脱节：board_anchors_echo() 是 PCB 那边唯一的消费源，但它 echo 的孔位是从包络角内缩 6 mm 硬算出来的（:698-701），不是从 board_rails() 的柱位来的。PCB 照这张表打孔，装配时既没有柱可拧，又会撞上前后壳的自攻螺柱。

## 22. 弹簧针自由针尖 Y（Y_TIP_FREE）

**各方取值**：MATING.md:239 与 :420（DB-03）→ Y = −22.895（= 触点面 −24.095 + 名义压缩 1.200）；dock_shell.scad:55-56 与派生 :194 → POGO_PCB_Y_TOP = −28.995，自由针尖 = −28.995 + POGO_FREE_H 4.50 = −24.495

**差异**：1.60 mm

**成因**：这是已知的两条（配合面 Y 差 1.70、名义压缩差 0.10）在同一个量上的合成结果，但它是**直接交给 dock-board 打板的那个数**（DB-03），值得单列：按 −22.895 选针和按 −24.495 装针，首次接触位置差 1.6 mm，超过全行程 2.0 mm 的三分之二。


---

# 非阻断项（18 条）

## 1. J2 焊盘直径 DOCK_PAD_D（ICD §3.1「由模块板任务定」）

**各方取值**：module-board（电气分支）：Ø1.8 —— netlist.yaml:190 封装名 PAD-ARRAY-2x8-P2.54-D1.8、PINMAP.md:119、BOM.csv:15、DESIGN_NOTES.md:278、gen_schematic.py:276；mech-module（机械分支）：Ø2.0 —— module_board.scad:117、MATING.md:341/442（2026-09-21 主动由 1.8 改 2.0，并对 module-board 发出要求 MB-01）

**差异**：0.2 mm

**成因**：ICD 把焊盘直径交给模块板任务，机械分支算完公差链后单方面改了值并写进自己的 SCAD，但电气分支的网表/BOM/封装名仍是 D1.8，没人回填。按现在的 netlist 出 Gerber 就是 Ø1.8：配 Ø0.9 针尖时允许偏移 (1.8−0.9)/2 = 0.45 mm，正好等于 mech-module 的 DOCK_X_TOL=0.45，余量 0（MATING.md:335 用 RSS 算是 0.016 mm，机械分支自己判为「等于不通过」）。装得上，但最坏公差下针尖压在焊盘边沿，接触不可靠。注：若采用 mech-dock 的 0.35 公差，Ø1.8 反而有 0.10 mm 余量 —— 这一条要和下一条一起定。

## 2. 托架定位公差 DOCK_X_TOL / DOCK_Z_TOL（ICD §3.1、ME-D-10「由机械任务定」）

**各方取值**：mech-module：±0.45（module_board.scad:146-147，AS-31-mm-6，声明由壳体滑配与导向筋实现）；mech-dock：±0.35（dock_shell.scad:52-53，AS-31-mechdock-6）

**差异**：0.10 mm

**成因**：同一个「由机械任务给值」的参数被两个机械分支各填一次，CONFLICT-pogo-field.md 未记录。两者都满足 ICD §3.3「必须 < 半个列距 1.27」的硬约束，所以不阻断；但它直接决定上一条焊盘直径够不够，两条必须一起裁定。**这一条依赖实测（AS-01/AS-04/AS-31-mm-18），卡尺未到货前无法关闭，建议排在几何类冲突之后处理。**

## 3. 弹簧针单针工作压力（ICD §3.1 DOCK_PIN_TRAVEL 相关，选型未定 AS-26）

**各方取值**：mech-module：0.6 N／针，总 9.6 N（module_board.scad:140，MATING.md:290 明写选型要求 ≤0.6 N）；mech-dock：0.9 N／针，总 14.4 N（dock_shell.scad:148，AS-31-mechdock-20）

**差异**：0.3 N／针，总 4.8 N

**成因**：CONFLICT-pogo-field.md 第 7 节已记录。按 0.9 N 选型会使 MATING.md 第 4 节的保持力核算（卡扣 ≥30 N、硬限位净压力 15.6 N）全部要重做。选型本身归 dock-board（P-DK-04），目前型号未定（AS-31-dock-25），两个数都是猜的。

## 4. 弹簧针名义工作压缩量 DOCK_PIN_TRAVEL（ICD §3.1「由选型定」）

**各方取值**：mech-module：1.20 mm（module_board.scad:126）；mech-dock：1.30 mm（dock_shell.scad:55-56，由 POGO_FREE_H 4.50 − POGO_WORK_H 3.20 推出）

**差异**：0.10 mm

**成因**：CONFLICT-pogo-field.md 第 7 节已记录，建议 dock 侧改 POGO_WORK_H = 3.30。MATING.md 第 5.3 节刚更正过的行程窗口 [1.95, 2.10] 是按 T=1.20 解出来的；T 若为 1.30，窗口变为 [2.10, 2.25]，与「常规 2.54 间距弹簧针全行程多在 1.0～2.0」的选型现实更冲突。

## 5. AT24C02 WP 默认电平（ICD §7.1「proposed 默认拉到 SLOT_3V3 写保护」）

**各方取值**：ICD-0.2-DRAFT.md:207：proposed 默认 WP → SLOT_3V3（写保护），经 DNP 跳线 J_WP 可拉低；module-board：netlist.yaml:175/328 默认锡桥 JP1 1–2 → WP 接 DOCK_GND（**可写**），改桥 2–3 才写保护

**差异**：默认状态相反

**成因**：ICD 把 WP 策略标 proposed，eeprom 分支（PROGRAMMING.md P-01）与 module-board 取了「默认可写」以便 D-017 迭代中在系统内重烧，ICD 未回填。PINMAP.md 第 0 节第 9 条自己已经标出需 Chrome 择一，属已知未决而非漏网。不阻断装配，但量产件默认可写是一个要明示的风险决定。

## 6. DOCK_5V 输出限流阈值（ICD EL-D-12／§3.3 三级「阈值由 Chrome 定义」）

**各方取值**：ICD-0.2-DRAFT.md:148/171：留空，「待 Chrome 定义」；dock-board 自填：R_ILIM_OUT 19.6 kΩ → IOS 1215/1308/1415 mA，验收判据 TH-03 动作 1.15–1.50 A（DESIGN_NOTES.md:114、:331 AS-31-dock-2）

**差异**：对照 AS-09 假设的整机峰值 ≤1 A，限流点高出约 30 %；pin 17 输入额定本身 unknown

**成因**：只有一个文件填了值，不是两文件互相矛盾，但属于「ICD 留空被单方填上且未回填」的同一类流程漏洞。dock-board 自己在 DESIGN_NOTES.md:236-244 诚实标注了「这一级限流保护的是底座自身与弹簧针，不保护主机」，并给了随 AS-09 实测回填的决策树（<0.4 A 持续则改 26.1 kΩ）。处理方式是 Chrome 追认或改值，不是修冲突。

## 7. 触点场右缘与原生 USB-C 通道的余量（AS-22，CONFLICT-pogo-field.md 推荐方案的唯一风险点）

**各方取值**：CONFLICT-pogo-field.md:79-82 写：8 列场右缘含 Ø2.0 焊盘到 X=−6.22，USB-C 左缘 −6.00，余量 0.22 mm；实算：列 8 中心 −8.22 ＋ 焊盘半径 1.0 = **−7.22**（原文加了直径而非半径）；真正卡死的是触点板本身与地板缺口 —— 触点板右缘 = DOCK_FIELD_XC(−17.11)+11 = **−6.11**（余量 0.11 mm），地板缺口右缘 = −5.11，**已经侵入 USB-C 通道 X[−6,+6] 达 0.89 mm**（dock_shell.scad:156-157 与 :326-329）

**差异**：文档 0.22 mm vs 焊盘实际 1.22 mm vs 触点板实际 0.11 mm vs 地板缺口 −0.89 mm（负余量）

**成因**：CONFLICT 文档结论（余量等于零、必须先关闭 AS-22）方向正确，但算式用错了半径且比错了对象，数字不能直接拿去施工。真正的干涉点是 dock_shell.scad 为触点板开的地板缺口已经和原生 USB-C 直通道打通了 0.89 mm，dock_shell.scad 的 assert 表里没有这一项检查。采纳选项 3 之前必须把这条补成硬性 assert。现阶段不阻断（选项 3 尚未采纳），但推荐处置的关键数要改。

## 8. 托架定位公差 DOCK_X_TOL / DOCK_Z_TOL

**各方取值**：module_board.scad:146-147 → 0.45 / 0.45（AS-31-mm-6，目标值）；dock_shell.scad:52-53 → 0.35 / 0.35（AS-31-mechdock-6）；MATING.md:40 与第 6.1 节（:325）给的**实现值**是 RSS 0.434、最坏 0.939

**差异**：0.10 mm（两个假设之间）；底座的 0.35 比模块自己算出的 RSS 0.434 还小 0.084 mm，比最坏值 0.939 小 0.589 mm

**成因**：这条不是打不进去，是「按谁的数做接触质量判据」。底座写 0.35 只是为了满足自己 assert(DOCK_X_TOL < 1.27)，没有任何链路核算支撑；模块侧的 0.45 是目标，实测链最坏 0.939。若 Ø1.8 焊盘被恢复（见焊盘直径那条），0.45 下余量直接归零 → 那时这条转为阻断。**最终取值必须等首版打印件到手、用卡尺量 20 次落点才能关闭（AS-31-mm-18 是链里最大不确定项），现在不宜定数。**

## 9. 模块板定位孔 MOUNT_B 的 X 坐标

**各方取值**：module_board.scad:180 → MOUNT_B_X = −26.30（:177-179 注明 2026-09-21 由 −26.00 沿 −X 移 0.30，否则[检查 10]不通过）；MATING.md:133 与 :423（MB-03）仍写 (−26.00, −18.00)

**差异**：0.30 mm；据此 MATING.md:133 给的「销 B 与 MOUNT_B 沿 X 净距 1.75 mm」也过时，module_shell.scad ECHO[壳-9]实际是 1.45 mm

**成因**：同一天的两处改动只落到了 scad，MATING.md 的接口要求表和让位论证没跟着改。MB-03 是要交给 module-board 任务打孔的数，照 −26.00 打会让[检查 10]的边距余量掉到 2.405 < 2.5。

## 10. Mosaico 本体的柔性支承（MD-05）

**各方取值**：MATING.md:209-211（MD-05）：底座托架必须在 Mosaico −Y 面下提供邵氏 A40–60 柔性支承，落入到位预压 ≤ 0.3 N，±Z 与 +X 方向软限位间隙 ≥ 0.5 mm，用于承担 50 g 冲击下 591 N·mm 的力矩（需要 39.4 N 限位力差，可用只有 15.6 N）；dock_shell.scad:345-351 只有四角刚性限位柱，柱顶 Y = −23.195，比 Mosaico 底面 −22.595 低 0.6 mm

**差异**：要求柔性支承＋预压 ≤0.3 N → 底座给的是刚性柱，且低 0.6 mm 根本不接触

**成因**：MATING.md 自己写明「这一条不满足时，方案 D＋G 的承力假设不成立」。底座侧压根没有这个概念，四角柱既不柔性也够不着 Mosaico。冲击工况是假设值（AS-31-mm-16 设计工况 50 g），无法在家验证，所以我不把它标阻断，但它是承力论证的单点。

## 11. 一级防呆手段（足部 −X 键块豁口）

**各方取值**：module_shell.scad:97-99 → KEY_TAB_L 2.0 (X) × KEY_TAB_W 8.0 (Z) × KEY_TAB_H 5.2 (Y)，MATING.md:395 称其为「一级防呆的主承担者」、:414（MD-04）要求底座腔开对应豁口；dock_shell.scad:338-354 的防呆只有 +X 壁一道 1.2 mm 限位筋与四角柱，靠 :229-230 的 assert（落入槽 X 非对称 5.0 mm）实现，无键块豁口

**差异**：需要 2.0 × 8.0 × 5.2 mm 的豁口 → 底座 0 个；两边各自实现了一套互不相认的一级防呆

**成因**：两种防呆都成立、但依赖的是对方不知道的形状。底座的非对称量是 MODULE_STACK_X = 5.0（已知冲突项），模块的是键块；把 X 冲突按任一方向解决后，另一方的防呆就失效，必须一起重定。

## 12. 整机厚度 28 mm

**各方取值**：dock_shell.scad:207 → T_GRIP_MAX = Z_FRONT_OUT − (Z_BACK_CORE − GRIP_DEPTH_BOT) = 28.00，ECHO「整机外形 W x H x T = 167 x 101.5 x 28 mm」（也是 ICD/任务书引用的数）；keycaps.scad:42 → CAP_TOP_Z = Z_FRONT_OUT + CAP_PROUD = +9.24，机身最后面 = −20.26

**差异**：1.50 mm（= CAP_PROUD）；实际最大厚度 29.5 mm

**成因**：28 mm 是不含键帽外凸的机身厚度，但对外一直当整机厚度用。键帽由 keycaps.scad include dock_shell.scad 共享参数，所以两边数值本身自洽，只是「整机厚度」这个词在两处指的不是同一个量。

## 13. CK-06 到底核对了什么（任务点名要重新确认的那条）

**各方取值**：dock-board/check_netlist.py:48-52 → PINMAP_KEYS 是 PINMAP.md 第 2 节的**硬编码副本**；:36-46 → ICD_J2 同样是硬编码副本；:167-181 的 CK-06 只比对 netlist.yaml 内部的 nets / key_map / j2_contract 与这份副本。脚本全文不读 PINMAP.md，不读 module-board/netlist.yaml，且**不含任何几何量**（无 X/Z/Y）

**差异**：逻辑分配 0 处差异（我独立验证）；几何 0 处覆盖

**成因**：我另写脚本把 PINMAP.md 第 2 节表格、module-board/netlist.yaml（SLOT_KEY_*/KEY_*/J2 焊盘/J3 位）、dock-board/netlist.yaml（nets、key_map、j2_contract 三处）四个来源逐针比过：10 个键的 KEY 名↔H2 针↔GPIO↔J2 焊盘↔J3 位**零差异**，16 个 J2 焊盘的网名也完全一致。所以 CK-06 的结论本身是对的，但它证明的只是「同名焊盘的网名一致」，证明不了「同名焊盘落在同一个物理位置」——后者需要 X0/Z0/Y，而脚本里一个坐标都没有。结构上它不可能发现触点场冲突，此前通过并不构成任何几何背书。

## 14. 两份网表的 outline_params 从未回填

**各方取值**：module-board/netlist.yaml:80 → outline_params: [FIN_L, FIN_H, FIN_Z]（仍是符号）、:86 → [PAD_BOARD_L, PAD_BOARD_W, MODULE_PAD_FACE_Y]；module_board.scad 已 echo 出 26 / 37.495 / −4.61 与 26 / 8 / −24.095。dock-board/netlist.yaml:116-117 → [DOCK_BOARD_L, DOCK_BOARD_W, DOCK_PIN_FIELD_X0, DOCK_PIN_FIELD_Z0, DOCK_PIN_FIELD_Y]，注明「本网表不填数」

**差异**：8 个应回填的几何参数，两份网表里 0 个有值

**成因**：这是冲突能长到今天没被发现的机制性原因之一：两份网表都不携带任何几何，两个 scad 各自 echo 一套，中间没有任何文件把它们摆在一起。主控在 CONFLICT-pogo-field.md 第 6 节提的「唯一给值方 ＋ 其余引用」正是补这个，但目前连回填动作本身都还没发生。

## 15. 触点板厚度

**各方取值**：module-board/netlist.yaml:85 → pad_board thickness_mm: 1.6（module_board.scad:104 PCB_T_PAD = 1.6 与之一致）；dock_shell.scad:33-34 注释 → MODULE_UNDER_Y 3.20 由「触点板厚 1.0～1.6 ＋ 装配间隙」推得，未固定取值；dock_shell.scad:57 POGO_PCB_T = 1.00 是底座自己的弹簧针小板厚

**差异**：底座按 1.0～1.6 的区间推，模块已定死 1.6；区间宽度 0.6 mm

**成因**：底座的 MODULE_UNDER_Y = 3.20（已知冲突项之一）建立在一个区间而不是一个值上，所以那 1.70 mm 的差里有 0.6 mm 是「取值方式不同」造成的，不全是设计意图差异。修 1.70 mm 时要一起把这个区间钉死。

## 16. 滑配间隙（标定件覆盖范围 vs 设计实际用值）

**各方取值**：test-coupons/fit_ladder.scad:91 → C_CLR = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35]；module_shell.scad:48 → CLR_PAD = 0.05（触点板槽单边间隙，MATING.md 第 6 节 e 环刻意做紧）；:46-47 → CLR_FIN_Z 0.15 / CLR_FIN_XY 0.20；dock_shell.scad:61 → CLR_FIT = 0.35

**差异**：设计里最紧的一环 0.05 mm 低于标定阶梯最小值 0.10 mm，阶梯覆盖不到；底座的 0.35 正好踩在阶梯上限

**成因**：公差阶梯件是用来代替试错的，但它没有覆盖公差链里最关键的那一环（0.05 mm 的触点板槽）。**这条要等打印件与卡尺到齐才能动**，现在只登记覆盖缺口，不改阶梯取值。

## 17. 底座自身 USB-C 开孔的 Z 位置与所选连接器

**各方取值**：dock_shell.scad:160-162 → DOCK_USB_W 9.60 × DOCK_USB_H 4.00；:516-520 → 开孔中心 Z = BOARD_Z_FRONT + 0.2 = −2.40（即基本压在板面上）；dock-board/netlist.yaml:125-135 与 BOM.csv:2 → TYPE-C-31-M-12（LCSC C165948）贴板式 16P，本体坐在元件面 Z = −2.6 之上，**本体高度两份文件都没写 → 未知**

**差异**：未知（缺连接器高度）；若按常见贴板式 Type-C 本体高约 3.26 mm 推算（**这是我推的，不是文件里的值**），本体 Z 到 +0.66 而开孔上沿只到 −0.40，干涉约 1.06 mm

**成因**：外壳按「开孔中心 ≈ 板面」开，像是给沉板式连接器留的；BOM 选的是贴板式。真值取决于 C165948 的本体高度，BOM.csv:2 自己写着「焊盘图未核 / 待原厂数据手册核对」。我不编这个数，标未知，列入待核清单。

## 18. 电池插座 J3 的让位

**各方取值**：dock-board/BOM.csv:30 → B3B-PH-SM4-TB（JST PH 2.0 mm 卧贴 3P，C160353），装在主板上；dock_shell.scad:376-386 battery_bay_walls() 只按电池本体 50×34×8 加 BATT_CLR 1.00 造仓壁，:198-202 电池仓 X[−60,−10]、Y[−61,−27]、Z[−12.5,−4.5]

**差异**：插座位置与引线走向：底座外壳未定义（未知）

**成因**：电池在主板背面（Z −12.5…−4.5），插座卧贴在主板上（元件面 −2.6 还是焊接面 −4.2，两份文件都没说），电池引线要从仓里绕到插座。两边没有任何一处给出插座坐标，属于「还没人填」而不是「填了两个不同的值」，先登记以免和触点场一样拖到打板才发现。

