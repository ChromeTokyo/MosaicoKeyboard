提案 · 未冻结 · 由 Claude 主控（claude-fable-5-1）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造

# 方案 D＋G 假设总登记（ASSUMPTIONS）

日期：2026-09-20。输入提交：`origin/main` `1af3c36`。分支：`claude/design-d/icd`。维护：Claude 主控记录，Chrome 采纳后由 Chrome 维护技术内容，Hiro 复核关闭结论。

本表是 D-017 主循环第 ③ 步「改设计逐条关闭假设」的唯一登记入口。任何设计文件使用假设数值时必须写 `ASSUMPTION: AS-xx` 并指向本表；本表每条给出到货后可执行的验证步骤与器材。**本表没有任何 measured 值**；关闭一条假设的唯一方式是把实测记录（照片编号、读数、日期、执行人）填入「关闭记录」列并由 Hiro 复核。

**2026-09-23 Chrome 仅勘误验证步骤，未采纳或冻结本稿设计。** 到货第一轮以 `docs/MEASUREMENT_PROTOCOL.md` 第 0～5 节的认版、外观和安全外表面测量为界；补齐 V1.2 记录的 [draft PR #55](https://github.com/ChromeTokyo/MosaicoKeyboard/pull/55) 仍待审。下表后续夹具、试插、上电、通断和 G6 项目是待制定/复核的验证计划，**不是用户到货即可执行的动作**。关机和拔 USB 不等于内置电池已隔离；没有同版针位图、可靠夹具及 Hiro 复核时保持 `OPEN`，照片估算不冒充制造尺寸。

状态取值：`OPEN`（未验证）、`MEASURED`（用户已实测，待复核）、`CLOSED`（Hiro 复核通过）、`FALSIFIED`（证伪，设计须改）、`SUPERSEDED`（被其他假设替代）。

负责人缩写：Chrome（技术采纳与修订）、用户（日本端实测）、Hiro（复核）、Claude（记录）；子系统任务分支见 `hardware/ICD-0.2-DRAFT.md` 第 0.2 节。

## 1. 假设总表

| 编号 | 假设 | 使用文件 | 若错影响 | 到货验证步骤 | 器材 | 负责人 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AS-01 | Mosaico 整机外形 45.19 × 45.19 × 11.48 mm，33 g（官方视频简介标称，非图纸） | ICD 第 1、5 节；mech-module、mech-dock OpenSCAD 顶部块 | 托架内腔、模块板长度、握把总长全部错；可能夹不住或晃动 | 按 `docs/MEASUREMENT_PROTOCOL.md` 第 3 节：卡尺量 W/H/T 各 3 次取均值与极差，记录含/不含突出物两组；称重 | 卡尺（用户已有）、电子秤 | 用户测、Chrome 回填、Hiro 复核 | OPEN |
| AS-02 | 左槽 H2 为 2×10P、间距 2.54 mm | ICD 第 2、5 节；module-board 公头封装 | 模块板公头插不进或错位；整块模块板重打 | 第一轮拍 Q07/Q08 正视、斜视、定位照；数可见行列，副本标首尾及相邻三组孔中心，标尺在接口旁绝缘支架上并拍齐平侧视。Chrome 从可信原图估算孔距/跨距；无同平面证据或针号未认定时分别写“尺寸未测”／“pin 1→19 未认定”。不以卡尺接触孔位，不把排针插入作比例尺 | 手机、卡尺在远离设备处校过的标尺、绝缘支架；后续检具待设计 | 用户拍照、Chrome 回算 | OPEN |
| AS-03 | 母座位于机身 −X 面（屏朝用户、USB-C 朝下时的左侧），开口朝 −X，与外壳面近平齐 | ICD 第 1、5 节；mech-module | 模块板转向件几何全错 | 第一轮按屏朝人/USB-C 朝下姿态拍 Q07 正视、斜视、定位照，记录开口朝向与外壳基准；卡尺只量绝缘外壳外表面。开口凹/凸深度无同平面侧向参照或专门绝缘检具时记“未测”，待后续步骤 | 手机、标尺；后续绝缘检具待设计 | 用户拍照、Chrome 回算 | OPEN |
| AS-04 | 槽中心 Z 高度约为厚度中点；Y 位置 unknown，以参数 `SLOT_PIN1_Y`、`SLOT_PIN1_Z` 表示 | ICD 第 1 节参数；mech-module | 模块板公头位置错、触点面高度错 | 在 Q07 副本标可见首尾孔中心、两排中心及外壳上下边/USB-C 基准，记录较长一行的方向；Chrome 按照片与同平面参照估算相对位置，再映射 ICD 轴。不以卡尺/深度杆进入接口；针号未证实时不写 pin 1/20 坐标，仍记“未测” | 手机、已校标尺；后续绝缘检具待设计 | 用户拍照、Chrome 回算 | OPEN |
| AS-05 | 槽连接器为轴向插接排针/排母（E-01 未证实）；四角银色块为整机之间组合用磁铁，非模块电气连接 | ICD 第 5 节 ME-D-05；方案可行性前提 | 若为磁吸侧向触点，方案 D＋G 的公头方案不成立，需重定接口 | 第一轮拍 P00d/Q06 四角及 Q07/Q08 槽口，记录孔形、金属块或安装孔外观，由 Chrome 判读；磁性、插入深度未测。不要拿回形针/磁铁试吸，也不把任何探针插入接口 | 手机 | 用户拍照、Chrome 判读 | OPEN |
| AS-06 | `B-2200R20P-B120`（V1.0 原理图标注）的配对件是 2.54 mm 2×10 排针类公头；候选料「待原厂规格核对」 | ICD ME-D-06；module-board BOM | 插拔力、针长、保持力不匹配；可能损伤母座 | 先取得同版实物母座识别证据与原厂规格书，核针径、配合针长范围和插拔力；候选件试插仅在独立步骤、夹具与风险复核完成后进行，第一轮不插拔 | 同版母座/候选件规格书；后续无源样件 | Chrome | OPEN |
| AS-07 | 弹簧针接口 2.54 mm、2 行 × 8 列 = 16 针，分配见 ICD 第 3.2 节 | ICD 第 3 节；module-board 焊盘；dock-board 弹簧针 | 模块板底部宽度不够放 8 列（17.78 mm + 边距）则改 1.27 mm 或改行数，两板同改 | AS-01、AS-04 关闭后计算模块板可用底宽；首版打板后用无源检具核对位 | 卡尺、检具 | Chrome、mech 任务 | OPEN |
| AS-08 | 弹簧针场位于模块板正下方、偏置 −X 侧；配合轴 −Y；托架定位公差 `DOCK_X_TOL` < 1 列间距的一半 | ICD 第 3.3 节一级防呆；mech-dock | 错位可达 2 列时 5 V 落到 `KEY_*`，损坏主机 GPIO | 首版托架打印后，用带焊盘的无源模块板样件反复放入 20 次，每次量针尖落点偏移；确认 180° 错放触不到针 | 3D 打印件、卡尺、无源样板 | Chrome、用户 | OPEN |
| AS-09 | 电源预算：整机峰值 ≤ 1 A、持续 ≤ 0.6 A @ 5 V；**无官方依据**，pin 17 输入额定 unknown | ICD EL-D-12；dock-board 升压/限流选型；G6-A4 | 限流误触发或升压不足；或器件过设计 | G6-B：Mosaico 单独用原生 USB-C 经 USB 电流表跑最重负载（屏最亮、Wi-Fi、音频）记录峰值/持续；再经底座 `DOCK_5V` 复测 | USB-C 在线电压电流表（需购）、假负载 | 用户测、Chrome 回填 | OPEN |
| AS-10 | `DOCK_5V` 名义 5.0 V；主机 pin 17 可接受的输入电压窗口 unknown | dock-board 升压设定；G6-A2 | 过高损主机、过低充不进 | 查 V1.0 原理图 5V_IN 路径二极管压降作参考（不作 V1.2 结论）；G6-A7 接 Mosaico 后记录能否充电与开机的最低/正常电压 | 万用表 | Chrome、用户 | OPEN |
| AS-11 | **硬约束 8 双供电**：主机内部把 pin 17 5V_IN 与原生 USB VBUS 合并的拓扑参照 V1.0（D10、D14），V1.2 unknown；假设主机不会经 pin 17 向外送电，但底座仍必须防反灌 | ICD EL-D-08；dock-board 防反灌器件；G6-B | 若 V1.2 主机会从 pin 17 反向输出，底座无防护则电池/升压被灌 | G6-B 态 (0,0,1)：只接原生 USB、底座无电，测 pin 17 → 底座方向电流与 `DOCK_5V` 节点电压；态 (1,1,1) 测双向电流 | USB 电流表 ×2、万用表 | Chrome 定阈值、用户测 | OPEN |
| AS-12 | 电池 1500 mAh 3.7 V 软包为参数化默认；尺寸、保护板、NTC、插头 unknown；采购地优先日本 | dock-board 充电参数；mech-dock 电池腔 | 电池腔放不下或充电电流不匹配 | 用户确认本地可购型号与规格书；回填尺寸、保护板、插头；运输方案未定前不随包寄送（`docs/TEAM_PLAN.md` 第 6 节） | 规格书 | 用户、Chrome | OPEN |
| AS-13 | 主机 `VCC_3V3`（pin 19）向模块供电能力：V1.0 资料为共享 100 mA 上限；V1.2 unknown；EEPROM + DNP 上拉负载远小于此 | ICD EL-D-03；module-board | 若 V1.2 能力更小或有使能条件，EEPROM 不被识别 | G6-A7：Mosaico 开机后测模块板 `TP_3V3` 电压；G6-C 识别成功即侧面证明 | 万用表 | 用户 | OPEN |
| AS-14 | V1.2 模块 I²C1 外部上拉存在与阻值 unknown；源码只证明主机内部上拉开启；模块板预留 `R_PU_SDA/SCL` DNP | ICD EL-D-04；module-board | 上升时间过长导致 EEPROM 读错或 CRC 失败 | G6-E：有示波器时测 SDA/SCL 上升时间、VOL；无则记录 100 次 `module_slot_scan` 成功率；决定是否装 DNP 上拉 | 示波器/逻辑分析仪（可选） | Chrome、用户 | OPEN |
| AS-15 | 11 根可用 GPIO 均可配为带内部上拉的输入，且开机时被按住不改变启动模式（无 strapping 副作用） | ICD 第 2 节；firmware；PINMAP.md | 某键开机被按住则进下载模式或异常 | 查主机 SoC 数据手册 strapping 表并记录 URL；G6-D5 逐键按住开机 | 数据手册、Mosaico | firmware 任务、用户 | OPEN |
| AS-16 | 到货 CoreBoard/BaseBoard 为 V1.2 且出厂固件行为与 BSP `392860b1` 一致（模块管理器 250 ms 扫描、3 次去抖、134 字节读） | ICD 第 7、8 节；firmware | 版本不同则 GPIO 表、I²C 总线、EEPROM 期望全部需复核 | `docs/MEASUREMENT_PROTOCOL.md` 第 0 节认版；读 eFuse/版本信息（命令由 firmware 任务给出）；对照 BaseBoard 标签 | Mosaico、USB 线、电脑 | 用户、Claude 记录 | OPEN |
| AS-17 | H2 针号与物理位置：奇数针行位置、pin 1 朝向与 D1 表一致 | ICD 第 1、2 节；module-board 焊盘序 | 全部 20 针镜像错，pin 17 5 V 可能落到 GPIO | 第一轮仅拍 Q07/Q08 的可见 pin 1/缺口/键位标记和三视图，照抄实物；Chrome 建立同版待核针位图。通断/二极管测试须另制 V1.2 专项步骤，先证实内置电池安全隔离、同版测试点配对与绝缘夹具并经 Hiro 复核；不以关机视为断电，不预设 USB-C 外壳为 GND。照片不能单独关闭本项 | 手机；后续夹具/仪器待专项步骤 | 用户拍照、Chrome/Hiro 后续复核 | OPEN |
| AS-18 | pin 20 单针 GND 回流载流满足 AS-09 电流 | ICD 第 2 节；module-board | 触点发热、压降过大 | G6-F 温升：0.6 A 持续 30 min 后红外测 H2 区域；G6-G 插拔后复测压降 | 红外测温仪（需购）、USB 电流表 | 用户 | OPEN |
| AS-19 | 主机 pin 17 对热插拔浪涌与等长弹簧针同时接触可容忍 | ICD 第 3.3 节先接触次序 | 主机输入器件应力、复位 | G6-G 每次插拔观察主机是否复位/重启；有示波器时抓 `DOCK_5V` 瞬态 | 示波器（可选） | Chrome、用户 | OPEN |
| AS-20 | EEPROM 身份字段 board_type/vendor_id/board_id 官方未分配；自定值不与官方量产模块冲突，且管理器只校验 magic、CRC、param_length | ICD 第 7.2 节；eeprom 任务 | 与官方驱动误绑定；或未来固件拒识 | G6-C 读出并核对；对照 BSP 头文件枚举 `mosaico_module_mgr.h:42–58`；固件升级后复测 | Mosaico、测试固件 | eeprom 任务、Hiro | OPEN |
| AS-21 | 右槽保持为空，0x51 不出现；用户若插右模块，地址并存但不冲突 | ICD 第 6 节 | 若右模块带其他 I²C 器件占用地址则底座可选器件冲突 | G6-C 地址扫描（只读）记录全部应答地址 | 测试固件 | 用户 | OPEN |
| AS-22 | 原生 USB-C 位于 −Y 面、不被托架与模块板遮挡，双 USB 可同时插 | ICD ME-D-07；mech-dock | 无法双供电或无法用原生口调试 | 到货量 USB-C 中心 X/Z 与开口尺寸；首版托架试插 USB-C 线 | 卡尺 | 用户 | OPEN |
| AS-23 | 十键 20–40 ms 轮询 + 去抖满足手感，无需中断 | ICD EL-D-07；firmware | 丢键或迟滞 | G6-D 连击与长按记录；用户主观评分 | 测试固件 | firmware 任务、用户 | OPEN |
| AS-24 | 左槽无锁扣，模块板保持力不足以承受每天插拔底座的力；需机械辅助固定到 Mosaico 本体 | ICD ME-D-08；mech-module | 模块板在槽内松动，H2 接触不良 | 第一轮只看可见锁扣/挡肩并拍 Q07；保持力和晃动须待同版配对件、机械样件及独立试装步骤复核后再测，不为取证插拔原装模块 | 手机；后续无源样件 | mech 任务、用户 | OPEN |
| AS-25 | Mosaico −Y 面除 USB-C 外无需暴露的孔；±X 面除左槽外无需暴露的接口 | mech-dock 托架开孔 | 遮挡扬声器/麦克风/按键 | 到货目视六面并拍照 | 手机 | 用户 | OPEN |
| AS-26 | 所选弹簧针单针额定电流「待原厂数据手册核对」；`DOCK_5V`/`DOCK_GND` 各 2 针并联满足 AS-09 | ICD 第 3.4 节；dock-board BOM | 针发热、接触电阻上升 | 打开原厂数据手册记录 URL 与额定；G6-G 0.5 A 压降复测 | 数据手册、万用表 | Chrome | OPEN |
| AS-27 | 主要器件在嘉立创常备料（基础库/扩展库）可得且可贴装 | 全部 BOM | 缺料换型需重新审核 | 下单前在嘉立创逐项核库存与封装 | 嘉立创后台 | Chrome | OPEN |
| AS-28 | CoreBoard 芯片 eFuse 中的板卡变体与用户看到的 BaseBoard 日期码/版本标签严格对应 | AS-16；ICD 第 0 节 | 主板与核心板版本不一致，GPIO/I²C 表可能混用 | 读 eFuse（firmware 任务给命令）并与 BaseBoard 标签、`docs/MEASUREMENT_PROTOCOL.md` 第 0 节结果一起登记 | 电脑、USB 线 | 用户、Claude | OPEN |
| AS-29 | Mosaico 的 5V_IN 充电与供电在 pin 17 有电且主机关机时仍工作（即底座可给关机的主机充电） | dock 使用场景；G6-B | 若主机关机时不接受 pin 17 充电，则「放回底座即充电」不成立 | G6-B 态 (1,1,0)：主机关机放入底座，30 min 后开机看电量变化 | 万用表、计时器 | 用户 | OPEN |
| AS-30 | 模块板 pin 13/15（USB Serial/JTAG）留 NC 不影响主机原生 USB 与调试 | ICD 第 2 节 | 若主机要求这两针有终端则调试口异常 | G6-A7 接模块板后用原生 USB-C 连接电脑确认串口/JTAG 枚举正常 | 电脑 | 用户 | OPEN |

## 2. 硬约束与假设的对应

| 硬约束 | 相关假设 | 说明 |
| --- | --- | --- |
| 1 pin 17 纯硬件供电 | AS-09、AS-10、AS-29 | 约束本身不是假设；其数值（电压、限流）是 |
| 2 pin 18 NC | — | 无假设，纯规则 |
| 3 EEPROM 由 pin 19 取电 | AS-13 | 供电能力是假设 |
| 4 不照搬 4.7 kΩ | AS-14 | 上拉存在性是假设 |
| 5 无源按键 3.3 V | AS-15、AS-23 | strapping 与轮询是假设 |
| 6 地址避开 0x50/0x51 | AS-21 | 右槽状态是假设 |
| 7 轮询去抖 | AS-23 | — |
| 8 双供电防反灌 | **AS-11**、AS-19、AS-22 | 主机内部合并拓扑 V1.2 unknown |
| 9 嘉立创常备料、配对公头待核 | AS-06、AS-26、AS-27 | — |

## 3. 其他子系统分支的假设（待吸收）

2026-09-20 执行 `git fetch origin && git ls-remote origin 'refs/heads/claude/design-d/*'`，**远端尚无任何 `claude/design-d/*` 分支**（本分支为首个推送）。因此以下分支的假设尚未吸收，标「待补」。各分支推送后，由主控执行：

```
git fetch origin
git show origin/claude/design-d/<key>:hardware/<dir>/README.md   # 或该分支自述的假设文件
```

并把其 `ASSUMPTION:` 条目并入第 1 节（沿用 AS-31 起编号，不重排已有编号；若与已有条目重复则在该条目「使用文件」列追加文件名）。

| 分支 | 目录 | 预计假设类别 | 状态 |
| --- | --- | --- | --- |
| `claude/design-d/module-board` | `hardware/module-board/` | 公头选型、焊盘直径、串阻/ESD、`KEY_*` → GPIO 分配 | 待补 |
| `claude/design-d/dock-board` | `hardware/dock-board/` | 充电/升压/限流/防反灌器件与阈值、弹簧针型号、USB-C、开关型号 | 待补 |
| `claude/design-d/eeprom` | `hardware/eeprom/`（路径待该分支确认） | board_type/vendor_id/board_id 取值、WP 策略、烧录夹具 | 待补 |
| `claude/design-d/firmware` | `firmware/` | 轮询参数、扫描命令名、eFuse 读取方法 | 待补 |
| `claude/design-d/mech-module` | `mechanical/module/`（路径待确认） | 转向件几何、保持力、模块板外形 | 待补 |
| `claude/design-d/mech-dock` | `mechanical/dock/`（路径待确认） | 托架、握把、电池腔、定位公差 `DOCK_X_TOL`/`DOCK_Z_TOL` | 待补 |

## 4. 关闭记录

| 编号 | 日期 | 执行人 | 实测值/照片编号 | 复核人 | 结论 |
| --- | --- | --- | --- | --- | --- |
| （空） | | | | | |

## 5. 使用规则

1. 设计文件引用格式：`ASSUMPTION: AS-xx <一句话>`；OpenSCAD 在顶部 `// ASSUMPTION` 块集中列出；YAML 网表在 `assumptions:` 键下列出编号。
2. 新增假设时在本表追加行、编号递增、不复用已作废编号；作废写 `SUPERSEDED` 并注明替代编号。
3. 假设关闭后，使用该假设的每个文件必须在下一次提交中把 `ASSUMPTION` 标签改为 `MEASURED（AS-xx，日期）` 并更新数值；未更新的文件不得进入打板包。
4. 用户在日本端的实测记录按 `docs/MEASUREMENT_PROTOCOL.md` 的照片编号与建档规则留证，由 Claude 入库，Hiro 复核后本表改状态。
