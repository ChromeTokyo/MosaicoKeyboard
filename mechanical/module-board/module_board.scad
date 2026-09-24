// ⚠ 2026-09-24 作废：本文件属 −Y 落入／两板／J3 时代，架构已转向直排针穿透＋撞针横顶＋−Z 压入（D-028）。仅存档供追溯，不得据以设计或复核。现行描述见 review/claude/option-j-seated.md，分工见 docs/WORK-SPLIT-20260924.md。
// 提案 · 未冻结 · 由 Claude 主控（claude-opus-5）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
//
// module_board.scad —— 方案 J（落座式）模块板参数化机械模型
// 分支 claude/design-d/mech-module ／ 目录 mechanical/module-board/
//
// 对象：左槽转接模块板（纯无源：J1 2×10P 公头 ＋ AT24C02 ＋ 底部弹簧针触点焊盘）。
//
// ====================================================================
// 2026-09-22 修订 c —— 公头形式由「右角」改为「直插」，J3 由「单排 16 位半孔」
//   改为「双排 8+8 @1.27 mm 焊盘对接焊」，弹簧针场由 2 行 × 8 列改为 4 行 × 4 列。
//
//   为什么改（三条，全部可复算）：
//   ① 右角路线下槽板躺在 XY 面、沿 −X 伸出 FIN_L = 26.0，模块总成 −X 端 = −53.595，
//      而底座落入槽 −X 壁 = −27.945，**干涉 25.650 mm**（check_cross_branch.py 实跑）。
//      要补这 25.65 只能把落入槽开到 X ≈ −57.9，而 D-pad 键帽沿 X 占 [−66, −42]、
//      D-pad 右开关体占 [−47.5, −41.5] —— 落入槽会把 D-pad 整个吞掉。右角路线死。
//   ② 改直插后槽板立在 YZ 面，X 向只占「胶芯 2.54 ＋ 板 1.6 ＋ 焊点 0.8」，
//      模块总成 −X 端收到 −37.295，落入槽只需开到 −37.445，槽壁外表面 −39.445，
//      对 D-pad 开关体 −41.5 仍留 2.055 mm。
//   ③ 直插使槽板底边沿 **Z** 走（原来沿 X），Z 向可用跨距只有落入槽的 12.18 mm，
//      放不下单排 16 位 @1.5 的 22.5 mm。改双排 8+8 @1.27（跨距 8.89）后放得下。
//      同时 2 行 × 8 列的触点场沿 X 占 17.78 mm，[检查 4]（触点场须整体落在
//      Mosaico 的 X 投影之外）会把触点板逼到 X ≈ −42.9，落入槽又撞 D-pad；
//      改 4 行 × 4 列（仍 16 针）后沿 X 只占 7.62 mm，触点板 X ∈ [−34.095, −23.095]。
//      改行列数由 ICD 第 3 节 AS-07 明文授权：「放不下则改 1.27 mm 或改行数，两板同改」。
//      **两板同改**：底座侧 dock_shell.scad 的 DOCK_COLS/DOCK_ROWS 同步改，
//      由 hardware/check_cross_branch.py 的 EQ 关系强制。
// ====================================================================
//
// 权威输入（本文必须与之一致，冲突时以它们为准）：
//   hardware/ICD-0.2-DRAFT.md                第 1 节坐标系、第 3 节弹簧针接口、第 5 节机械约束
//   review/claude/option-j-seated.md         方案 J 三条不可违反的不变量
//   origin/claude/design-d/module-board:hardware/module-board/PINMAP.md
//   hardware/ASSUMPTIONS.md                  AS-01～AS-30
//
// 「L 形 PCB」的实现说明（修订 c 后）：
//   槽板 fin 立在 **YZ 面**（板面法向 ±X，因为直插公头的针轴垂直于板面而针指向 +X），
//   触点板 pad_board 躺在 **XZ 面**（板面法向 −Y，因为弹簧针轴向 +Y）。
//   两面互相垂直、交线沿 **Z**，J3 就排在这条交线上：槽板两面各一排 8 个 SMD 焊盘，
//   触点板顶面在槽板落脚线两侧各一排 8 个焊盘，90° 填角焊。
//
// 单位 mm。坐标系严格用 ICD 第 1 节整机坐标：
//   基准姿态「屏朝用户、USB-C 朝下、左槽在左」
//   +X = 用户视角向右（左槽在 −X 面）   +Y = 向上（弹簧针轴向 +Y，整机沿 −Y 落入底座）
//   +Z = 从屏面指向用户                 原点 O = Mosaico 外形包络几何中心


// ====================================================================
// ASSUMPTION 块 —— 本文件全部未经实物核对的输入集中在此。
// 每条给出编号与到货验证方法。本分支新引入者临时编号 AS-31-mm-n / AS-32-mm-n。
// 禁止在本块以外出现任何硬编码尺寸。
// ====================================================================

// ---- 一、Mosaico 整机（AS-01）----
// ASSUMPTION: AS-01 Mosaico 外形 45.19 × 45.19 × 11.48 mm、33 g（官方视频简介标称，非图纸）。
//   验证：docs/MEASUREMENT_PROTOCOL.md 第 3 节，卡尺三向各 3 次取均值与极差；电子秤称重。
MOSAICO_W = 45.19;      // X 向宽
MOSAICO_H = 45.19;      // Y 向高
MOSAICO_T = 11.48;      // Z 向厚
MOSAICO_M = 33;         // g，只用于承力计算的 echo，不参与几何

// ASSUMPTION: AS-31-mm-1 Mosaico 外形按直角长方体包络建模，圆角/倒角/凸起未知。
MOSAICO_CORNER_R = 0;

// ---- 二、左槽 H2（AS-02～AS-05、AS-17）----
// ASSUMPTION: AS-03 母座在 −X 面、开口朝 −X、与外壳面近平齐（凹/凸量 unknown，按 0 建模）。
SLOT_FACE_X     = -MOSAICO_W / 2;
SLOT_FACE_RECESS = 0;

// ASSUMPTION: AS-02 H2 为 2×10P、间距 2.54 mm。
SLOT_PITCH      = 2.54;   // 同排相邻针中心距（沿 Y）
SLOT_ROW_PITCH  = 2.54;   // 两排中心距（沿 Z）
SLOT_PINS_PER_ROW = 10;

// ASSUMPTION: AS-04 槽中心 Z ≈ 厚度中点；Y 位置 unknown。
//   修订 d：把 ICD 第 1 节点名的 `SLOT_PIN1_Y` 提成**显式输入**，不再把「Y 向居中」
//   藏在 SLOT_CENTER_Y = 0 里。到货用卡尺量 H2 pin 1 中心到 Mosaico −Y 面的距离 d，
//   填 SLOT_PIN1_Y = d - MOSAICO_H/2 即可，全部下游尺寸自动跟随。
//   当前值 +11.43 = (10-1)*2.54/2，等价于「H2 在 Y 上居中」——这是假设，不是实测。
SLOT_PIN1_Y     = 11.43;
SLOT_CENTER_Z   = 0;

// ASSUMPTION: AS-17 奇数排在 −Z 还是 +Z、pin 1 在哪端，均 unknown。几何对 ±1 对称。
SLOT_ODD_ROW_SIDE = -1;
SLOT_PIN1_AT_PLUS_Y = true;

// ---- 三、J1 2×10P **直插**公头（AS-05、AS-06、AS-32-mm-1/2）----
// ASSUMPTION: AS-05 槽连接器为轴向插接排针/排母（E-01 未证实）。
// ASSUMPTION: AS-06 主机侧母座 V1.0 原理图标注 B-2200R20P-B120（Ckmtw，LCSC C124406）。
//   修订 c：配对公头基线由右角件改为**直插件**（2.54 mm 2×10P 直排针，如 BOOMELE
//   2.54-2*10P 直插系列）。ICD ME-D-06 原文授权「2.54 mm 2×10 直/弯排针；模块板一侧
//   公头是否用弯针……由模块板与机械任务定」——本文行使该授权，选**直**。
//   **配对公头的全部尺寸「待原厂数据手册核对」**。
// ASSUMPTION: AS-31-mm-2 配合针自胶芯前端面伸出 6.0 mm；到位时插入母座深度 5.0 mm。
J1_MATE_LEN     = 6.0;
J1_INSERT_DEPTH = 5.0;
// ASSUMPTION: AS-32-mm-1 直插 2×10P 排针胶芯沿 X（= 针轴向）厚 2.54 mm，
//   沿 Y 长 10 × 2.54 = 25.40 mm（端针外各半个间距），沿 Z 宽 2 × 2.54 = 5.08 mm。
//   这是 2.54 mm 系列排针的通行胶芯尺寸。待原厂图纸核对。
J1_INSUL_X      = 2.54;
J1_BODY_EXT_Y   = 1.27;   // 胶芯沿 Y 超出端针中心的量（半个间距）
J1_BODY_EXT_Z   = 1.27;   // 胶芯沿 Z 超出外排针中心的量（半个间距）
// ASSUMPTION: AS-32-mm-2 直插针尾穿过槽板后剪脚，焊点连同余高沿 −X 占 0.80 mm。
//   验证：首版板装配后用深度尺量焊点最高点相对板背面的高度。
J1_TAIL_X       = 0.80;
// 直插件两排针的 Z 间距天然等于排针自身行距，必须与母座一致
J1_ROW_PITCH_Z  = 2.54;

// ---- 四、板材 ----
// ASSUMPTION: AS-31-mm-4 两块板均 FR-4 2 层 1.6 mm。
PCB_T_FIN = 1.6;
PCB_T_PAD = 1.6;

// ---- 五、弹簧针接口 J2（AS-07、AS-08、AS-31-mb-3）----
// ASSUMPTION: AS-07 2.54 mm 间距、**4 行 × 4 列 = 16 针**（修订 c 由 2 行 × 8 列改）。
//   改行列数的授权见文件头 ③ 与 ICD 第 3 节 AS-07 原文。
//   **后果（必须由 module-board 任务关闭）**：PINMAP 第 3/4 节的逐针分配表要按
//   4 × 4 重排；ICD 3.3「Z 错一行」的电气后果分析要重做。本文只保证几何。
DOCK_PITCH = 2.54;
DOCK_COLS  = 4;
DOCK_ROWS  = 4;
// ASSUMPTION: AS-31-mb-3 J2 焊盘圆形 Ø2.0 mm（配 Ø0.9 针尖时允许偏移 0.55 mm）。
DOCK_PAD_D = 2.0;
// ASSUMPTION: AS-31-mm-5 弹簧针针头 Ø0.9、名义工作压缩 1.2、全行程 2.0、工作压力 0.6 N。
//   全行程 2.0 的推导见原文件注释（解 stroke/3 + 0.5 ≤ travel ≤ stroke − 0.8）。
//   **修订 c：这四个数现在是跨分支契约（check_cross_branch.py 的 EQ 项），
//   底座侧 dock_shell.scad 已同步取同值**（原底座取 travel 1.3 / force 0.9，
//   1.3 会使 [检查 9c] 判据 ② 失败，0.9 无任何推导，故两项均以模块侧为准）。
DOCK_PIN_TIP_D     = 0.9;
DOCK_PIN_TRAVEL    = 1.2;
DOCK_PIN_STROKE    = 2.0;
DOCK_PIN_NO_BOTTOM = 0.3;
DOCK_PIN_MIN_FRAC  = 1/3;
DOCK_PIN_FORCE_N   = 0.6;
// Y 向公差链最坏偏差（MATING 第 5 节）
DOCK_Y_TOL = 0.5;
// ASSUMPTION: AS-31-mm-6 托架对配合的定位公差目标 ±0.45 mm（X、Z 同值）。
//   修订 c：定位手段由「两个 Ø3.2 定位销孔」改为「模块壳足部整体滑配进落入槽的
//   模块条带（单边 CLR_MOD = 0.15）＋ 45° 引入倒角 ＋ 防呆键块」。
//   原因见 module_shell.scad [壳-1] 注释：折算后足部 ±Z 两侧各只剩 1.2 mm 料，
//   Ø3.2 盲孔配 1.2 壁需要 5.6 mm，两侧都放不下，销方案在本几何下无解。
//   新链：滑配 0.15 ＋ 两件各 ±PRINT_TOL 0.15 → 最坏 0.45（正好等于目标）、RSS 0.26。
//   **最坏值正好等于目标，是本设计最紧的一环**，验证见 MATING M4 / G6-H2。
DOCK_X_TOL = 0.45;
DOCK_Z_TOL = 0.45;
// ASSUMPTION: AS-31-mm-6b 焊盘边缘到板边最小余量 0.5 mm。
PAD_EDGE_MIN = 0.5;

// ---- 六、触点面相对 Mosaico 底面的落差（ME-D-07、AS-22）----
// ASSUMPTION: AS-31-mm-7 触点面比 Mosaico −Y 面再低 1.5 mm。
//   **修订 c：底座侧 AS-31-mechdock-2 的 MODULE_UNDER_Y 由 3.20 改为与本值一致的 1.50。**
//   原底座 3.20 = 「触点板厚 1.6 ＋ 装配间隙」，即假定触点板顶面与 Mosaico 底面齐平；
//   但触点板整体在 X < −23.095（[检查 4]），与 Mosaico 在 X 上不重叠，无需让开，
//   1.50 够用且把整机 Y 链抬高 1.70 mm（直接减小电池下移量）。
PAD_FACE_DROP = 1.5;

// ---- 七、J3 90° 转向接头（AS-32-mm-3，取代 AS-31-mb-5 的单排半孔）----
// ASSUMPTION: AS-32-mm-3 J3 = **双排各 8 位、间距 1.27 mm 的 SMD 焊盘对接焊**。
//   槽板两面（元件面 X = FIN_X_MAX、焊接面 X = FIN_X_MIN）各一排 8 个焊盘，紧贴底边；
//   触点板顶面在槽板落脚线两侧各一排 8 个焊盘；90° 填角焊，用壳体当焊接夹具
//   （MATING 第 2.1 节 A2 保留）。
//   为什么不是单排半孔：单排 16 位即便取半孔最小节距 1.3 也要 19.5 mm，
//   而本几何沿 Z 只有 10.80 mm 板宽。双排 8 位 @1.27 跨距 7 × 1.27 = 8.89 mm，放得下。
//   为什么不是 1.5 mm：双排 8 位 @1.5 跨距 10.5 mm，加两端 0.35 焊盘半宽与 0.5 边距
//   要 12.2 mm > 10.80，放不下。
//   为什么不用半孔：半孔本质只有一排（在板边上），做不出双排；改双排即离开半孔工艺，
//   嘉立创常规 SMD 焊盘即可，同时**不再受「板尺寸 ≥ 10 × 10 mm」的半孔规则约束**
//   （本板 11.0 × 10.8 也满足）。
//   单点载流：5V/GND 各 2 位并联覆盖 AS-09 峰值 ≤ 1 A 的假设不变（AS-31-mb-5 的载流部分保留）。
//   验证：PINMAP P10，首版样板 0.5 A／1.0 A 下测 J3 两端压降与温升。
J3_PER_ROW = 8;
J3_ROWS    = 2;
J3_PITCH   = 1.27;
J3_PAD_W   = 0.70;   // 焊盘沿 Z 宽
J3_PAD_L   = 1.60;   // 焊盘沿 Y（槽板上）／沿 X（触点板上）长

// ---- 八、外形与定位孔（本文给值，回填 netlist.yaml 的 outline_params）----
// ASSUMPTION: AS-32-mm-4 触点板 +X 边到 Mosaico −X 面留 2.50 mm
//   = 领口内衬 LINER 0.50 ＋ **领口承载背壁 COLLAR_BACK_W 2.00**（修订 d 新增）。
//   为什么必须留 2.00：原值 0.50 使触点板槽一直挖到领口贴合面 SEAT_X，领口下唇
//   （承托整台 Mosaico 的唯一件）在 X = SEAT_X 平面上只剩 +Z 侧一条三角筋与壳体相连，
//   实测截面 0.455 mm²（求交实测：0.02276 mm³ / 0.05 mm 切片）。按 PLA-CF 拉伸 39 MPa
//   反解，该筋在 1.6 N 下就到极限，而 Mosaico 自重就有 0.3234 N。
//   留 2.00 mm 后下唇根部变成 1.10 (Y) × 约 12.6 (Z) ≈ 13.9 mm² 的整截面。
//   代价由取消防呆键块（KEY_TAB_L 2.0 → 0）抵掉，模块总成 −X 端只多 0.40 mm。
PAD_X_GAP    = 2.50;
// ASSUMPTION: AS-32-mm-5 触点板 X 向长 11.00、Z 向宽 10.80；槽板 Z 向宽与触点板等宽且齐平。
//   取值依据见文末 [检查 1]/[检查 5]/[检查 12] 的余量核算。
PAD_BOARD_L  = 11.00;   // 触点板 X 向长
PAD_BOARD_W  = 10.80;   // 触点板 Z 向宽（＝槽板 Z 向宽）
// ASSUMPTION: AS-32-mm-6 触点板／槽板 +Z 边到模块壳 +Z 外表面留 1.40 mm
//   （＝鳍板腔单边间隙 CLR_FIN_YZ 0.20 ＋ 壳体最小特征壁 SHELL_MIN_W 1.20）。
//   壳体 +Z 外表面取与 Mosaico 前表面齐平（Z = +MOSAICO_T/2），使模块在落入槽里
//   前面不外凸、只向 −Z 加深 —— 落入槽 +Z 侧前壁只有 1.65 mm，不能再吃。
PAD_Z_TOP_INSET = 1.40;
// ASSUMPTION: AS-32-mm-7 槽板顶边 Y = +18.50（原 +15.0）。抬高 3.5 mm 是为了把主定位孔 A
//   放到 J1 胶芯（Y ∈ [−12.70, +12.70]）之上：槽板沿 Z 只有 10.80 mm，胶芯占 5.08，
//   两侧各剩 2.86 mm，放不下 Ø2.2 孔配 Ø5.0 禁布圆，孔只能排在胶芯的 ±Y 两端。
FIN_Y_MAX    = 18.50;
// ASSUMPTION: AS-31-mm-9 定位孔 Ø2.2 mm 两个。用于壳体空心柱定位＋M2 自攻螺钉贯穿。
//   修订 c：孔位由 (X, Y) 改为 (Z, Y)——槽板现在立在 YZ 面。
MOUNT_HOLE_D = 2.2;
MOUNT_A_Z = -3.00;  MOUNT_A_Y =  15.50;    // 主定位（圆柱），在 J1 胶芯之上
MOUNT_B_Z = -3.00;  MOUNT_B_Y = -17.50;    // 副定位（长圆孔，长轴沿 Y），在 J1 胶芯之下
MOUNT_KEEPOUT_D = 5.0;   // 焊盘/走线禁布圆直径

// ---- 九、显示/导出控制（非尺寸）----
MODE = "assembly";   // assembly | fin_2d | pad_2d | fin_dxf | pad_dxf | exploded
$fn  = 48;
SHOW_MOSAICO = true;
EXPLODE      = 0;


// ====================================================================
// 派生量 —— 全部由上面的 ASSUMPTION 算出，此处不得出现新的数字常量
// ====================================================================

// 左槽两排配合针的 Z 坐标
SLOT_ROW_ODD_Z  = SLOT_CENTER_Z + SLOT_ODD_ROW_SIDE * SLOT_ROW_PITCH / 2;
SLOT_ROW_EVEN_Z = SLOT_CENTER_Z - SLOT_ODD_ROW_SIDE * SLOT_ROW_PITCH / 2;

// 10 针沿 Y 的跨距与端点
SLOT_ROW_SPAN_Y = (SLOT_PINS_PER_ROW - 1) * SLOT_PITCH;   // 22.86
// 槽中心 Y 由 pin 1 的 Y 反解（修订 d：AS-04 成为显式输入）
SLOT_CENTER_Y   = SLOT_PIN1_Y - (SLOT_PIN1_AT_PLUS_Y ? 1 : -1) * SLOT_ROW_SPAN_Y / 2;
SLOT_Y_LO = SLOT_CENTER_Y - SLOT_ROW_SPAN_Y / 2;
SLOT_Y_HI = SLOT_CENTER_Y + SLOT_ROW_SPAN_Y / 2;

// ---- 直插 X 链（这是修订 c 的核心，逐环可复算）----
J1_TIP_X        = SLOT_FACE_X + SLOT_FACE_RECESS + J1_INSERT_DEPTH;  // 到位时针尖 X = −17.595
J1_BODY_FRONT_X = J1_TIP_X - J1_MATE_LEN;                            // 胶芯前端面 = −23.595
FIN_X_MAX       = J1_BODY_FRONT_X - J1_INSUL_X;                      // 槽板元件面 = −26.135
FIN_X_MIN       = FIN_X_MAX - PCB_T_FIN;                             // 槽板焊接面 = −27.735
FIN_MID_X       = (FIN_X_MIN + FIN_X_MAX) / 2;                       // 槽板中面 = −26.935
FIN_SOLDER_X    = FIN_X_MIN - J1_TAIL_X;                             // 针尾焊点最 −X 点 = −28.535

// 触点面与触点板
MOSAICO_Y_LO = -MOSAICO_H / 2;
MODULE_PAD_FACE_Y = MOSAICO_Y_LO - PAD_FACE_DROP;    // 触点板底面 Y（ICD DOCK_PIN_FIELD_Y）
PAD_TOP_Y  = MODULE_PAD_FACE_Y + PCB_T_PAD;          // 触点板顶面 = 槽板底边
PAD_X_MAX  = SLOT_FACE_X - PAD_X_GAP;                // −23.095
PAD_X_MIN  = PAD_X_MAX - PAD_BOARD_L;                // −34.095
MOSAICO_Z_HI_LOCAL = MOSAICO_T / 2;
PAD_Z_MAX  = MOSAICO_Z_HI_LOCAL - PAD_Z_TOP_INSET;   // +4.54
PAD_Z_MIN  = PAD_Z_MAX - PAD_BOARD_W;                // −6.26

// 槽板外形：立在 YZ 面，Z 向与触点板等宽齐平
FIN_Z_LO  = PAD_Z_MIN;
FIN_Z_HI  = PAD_Z_MAX;
FIN_W_Z   = PAD_BOARD_W;                             // 槽板 Z 向宽（原 FIN_L 的角色）
FIN_MID_Z = (FIN_Z_LO + FIN_Z_HI) / 2;               // −0.86
FIN_Y_MIN = PAD_TOP_Y;                               // 槽板坐在触点板顶面上（J3 处）
FIN_H     = FIN_Y_MAX - FIN_Y_MIN;                   // 回填 netlist 的 FIN_H
FIN_Z     = FIN_MID_Z;
// netlist.yaml outline_params 里 fin 的「长」现在是 Z 向宽
FIN_L     = FIN_W_Z;

// J3：双排沿 Z 排布，居中于槽板 Z 中面；两排分别在槽板的两个板面上
J3_SPAN_Z   = (J3_PER_ROW - 1) * J3_PITCH;           // 8.89
J3_CENTER_Z = FIN_MID_Z;
J3_CENTER_X = (PAD_X_MIN + PAD_X_MAX) / 2;           // 触点板 X 中心（壳体卡口/触点场引用）
function j3_z(i) = J3_CENTER_Z - J3_SPAN_Z / 2 + (i - 1) * J3_PITCH;   // i = 1..8
function j3_row_x(r) = (r == 0) ? FIN_X_MAX : FIN_X_MIN;               // r = 0 元件面，1 焊接面

// J2：4 行 × 4 列，居中于触点板；列 1 在 −X 最外侧；行 A 在 +Z（屏侧）
J2_SPAN_X = (DOCK_COLS - 1) * DOCK_PITCH;            // 7.62
J2_SPAN_Z = (DOCK_ROWS - 1) * DOCK_PITCH;            // 7.62
PAD_CENTER_X = (PAD_X_MIN + PAD_X_MAX) / 2;          // −28.595
PAD_CENTER_Z = (PAD_Z_MIN + PAD_Z_MAX) / 2;          // −0.86
DOCK_PIN_FIELD_X0 = PAD_CENTER_X - J2_SPAN_X / 2;    // 列 1 中心 X = −32.405
DOCK_PIN_FIELD_Z0 = PAD_CENTER_Z + J2_SPAN_Z / 2;    // 行 A 中心 Z = +2.95
DOCK_PIN_FIELD_Y  = MODULE_PAD_FACE_Y;               // 配合面 Y = −24.095
function j2_x(c) = DOCK_PIN_FIELD_X0 + (c - 1) * DOCK_PITCH;   // c = 1..DOCK_COLS
function j2_z(r) = DOCK_PIN_FIELD_Z0 - r * DOCK_PITCH;         // r = 0..DOCK_ROWS-1，0 = 行 A

// J1 胶芯包络（直插：贴在槽板元件面上，沿 +X 伸出）
J1_BODY_X_MIN = FIN_X_MAX;
J1_BODY_X_MAX = J1_BODY_FRONT_X;
J1_BODY_Y_LO  = SLOT_Y_LO - J1_BODY_EXT_Y;           // −12.70
J1_BODY_Y_HI  = SLOT_Y_HI + J1_BODY_EXT_Y;           // +12.70
J1_BODY_Z_LO  = SLOT_CENTER_Z - SLOT_ROW_PITCH / 2 - J1_BODY_EXT_Z;   // −2.54
J1_BODY_Z_HI  = SLOT_CENTER_Z + SLOT_ROW_PITCH / 2 + J1_BODY_EXT_Z;   // +2.54

// 余量核算（供文末 echo）
J1_ROW_Z_MARGIN_HI = FIN_Z_HI - (SLOT_CENTER_Z + SLOT_ROW_PITCH / 2);
J1_ROW_Z_MARGIN_LO = (SLOT_CENTER_Z - SLOT_ROW_PITCH / 2) - FIN_Z_LO;
J3_Z_MARGIN_HI = FIN_Z_HI - (J3_CENTER_Z + J3_SPAN_Z / 2) - J3_PAD_W / 2;
J3_Z_MARGIN_LO = (J3_CENTER_Z - J3_SPAN_Z / 2) - J3_PAD_W / 2 - FIN_Z_LO;
J2_X_EDGE_MARGIN = (PAD_BOARD_L - J2_SPAN_X) / 2 - DOCK_PAD_D / 2;
J2_Z_EDGE_MARGIN = (PAD_BOARD_W - J2_SPAN_Z) / 2 - DOCK_PAD_D / 2;
PAD_ALLOW_OFFSET = (DOCK_PAD_D - DOCK_PIN_TIP_D) / 2;
F_PIN_TOTAL = DOCK_PIN_FORCE_N * DOCK_COLS * DOCK_ROWS;
W_MOSAICO_N = MOSAICO_M / 1000 * 9.8;
// 模块板本体（不含壳体）自 Mosaico −X 面向 −X 的占深
MODULE_STACK_NEED_X = -(min(FIN_SOLDER_X, PAD_X_MIN) - SLOT_FACE_X);

// AT24C02 SOIC-8 占位（修订 c：坐标改为 (Z, Y)，放在 J1 胶芯之下、避开定位孔 B 禁布圆）
// ASSUMPTION: AS-31-mm-10 U1（SOIC-8，约 5.0(Y) × 4.0(Z) × 1.75 mm）在槽板元件面下部。
U1_Z = 2.00;  U1_Y = -16.00;


// ====================================================================
// 几何
// ====================================================================

// ---- 2D 外形 ----
// 槽板外形。2D 的第一轴是整机坐标的 Z，第二轴是 Y（板立在 YZ 面）。
module fin_outline_2d() {
    difference() {
        translate([FIN_Z_LO, FIN_Y_MIN]) square([FIN_W_Z, FIN_H]);
        translate([MOUNT_A_Z, MOUNT_A_Y]) circle(d = MOUNT_HOLE_D);
        translate([MOUNT_B_Z, MOUNT_B_Y]) circle(d = MOUNT_HOLE_D);
    }
}

// 触点板外形。2D 的第一轴是 X，第二轴是整机坐标的 Z。
module pad_outline_2d() {
    difference() {
        translate([PAD_X_MIN, PAD_Z_MIN]) square([PAD_BOARD_L, PAD_BOARD_W]);
        translate([PAD_X_MIN - 10, PAD_Z_MIN - 10]) square([0.001, 0.001]);
    }
}

// ---- 3D ----
// 槽板实体。fin_outline_2d() 的两轴是 (Z, Y)，挤出方向要变成 +X。
// 需要的映射是 (u, v, w) → (w, v, u)，行列式 = −1，因此必须 mirror 一次：
//   mirror([1,0,0]) 把 (u,v,w) 变成 (−u,v,w)，再 rotate([0,90,0])（(x,y,z)→(z,y,−x)）
//   得到 (w, v, u) —— 挤出方向落到 +X，2D 第一轴落到 +Z，第二轴落到 +Y。
// **不要写 rotate([90,0,90])**：那是 (u,v,w) → (w, u, v)，会把 2D 的 Z 轴甩到 Y 上，
// 定位孔与 J3 全部错位。2026-09-22 由「模块总成 ∩ 底座」求交实测抓出（交集 24 顶点）。
module fin_board_3d() {
    color("DarkGreen")
    translate([FIN_X_MIN, 0, 0])
        rotate([0, 90, 0])
            mirror([1, 0, 0])
                linear_extrude(height = PCB_T_FIN)
                    fin_outline_2d();
}

module pad_board_3d() {
    color("DarkGreen")
    translate([PAD_X_MIN, MODULE_PAD_FACE_Y, PAD_Z_MIN])
        cube([PAD_BOARD_L, PCB_T_PAD, PAD_BOARD_W]);
}

module j2_pads_3d() {
    color("Gold")
    for (c = [1 : DOCK_COLS], r = [0 : DOCK_ROWS - 1])
        translate([j2_x(c), MODULE_PAD_FACE_Y - 0.01, j2_z(r)])
            rotate([-90, 0, 0])
                cylinder(h = 0.06, d = DOCK_PAD_D);
}

// J3 焊盘：槽板两面各一排 8 个（贴底边），触点板顶面两侧各一排 8 个
module j3_pads_3d() {
    color("Silver") {
        for (r = [0 : J3_ROWS - 1], i = [1 : J3_PER_ROW])
            translate([j3_row_x(r) + (r == 0 ? 0 : -0.06), FIN_Y_MIN, j3_z(i) - J3_PAD_W / 2])
                cube([0.06, J3_PAD_L, J3_PAD_W]);
        for (r = [0 : J3_ROWS - 1], i = [1 : J3_PER_ROW])
            translate([(r == 0 ? FIN_X_MAX : FIN_X_MIN - J3_PAD_L), PAD_TOP_Y - 0.06,
                       j3_z(i) - J3_PAD_W / 2])
                cube([J3_PAD_L, 0.06, J3_PAD_W]);
    }
}

module j1_body_3d() {
    color("DimGray")
    translate([J1_BODY_X_MIN, J1_BODY_Y_LO, J1_BODY_Z_LO])
        cube([J1_BODY_X_MAX - J1_BODY_X_MIN,
              J1_BODY_Y_HI - J1_BODY_Y_LO,
              J1_BODY_Z_HI - J1_BODY_Z_LO]);
}

module j1_pins_3d() {
    color("Goldenrod")
    for (k = [0 : SLOT_PINS_PER_ROW - 1]) {
        y = SLOT_Y_LO + k * SLOT_PITCH;
        for (zr = [SLOT_ROW_ODD_Z, SLOT_ROW_EVEN_Z]) {
            // 配合段（伸出胶芯前端面）
            translate([J1_BODY_FRONT_X, y - 0.32, zr - 0.32])
                cube([J1_MATE_LEN, 0.64, 0.64]);
            // 针尾（穿过槽板并剪脚）
            translate([FIN_SOLDER_X, y - 0.32, zr - 0.32])
                cube([J1_BODY_FRONT_X - FIN_SOLDER_X, 0.64, 0.64]);
        }
    }
}

module u1_3d() {
    color("Black")
    translate([FIN_X_MAX, U1_Y - 2.5, U1_Z - 2.0])
        cube([1.75, 5.0, 4.0]);
}

module mosaico_ghost() {
    color([0.6, 0.7, 0.9, 0.18])
    translate([-MOSAICO_W / 2, -MOSAICO_H / 2, -MOSAICO_T / 2])
        cube([MOSAICO_W, MOSAICO_H, MOSAICO_T]);
}

module module_board_assembly(explode = 0) {
    fin_board_3d();
    j1_body_3d();
    j1_pins_3d();
    u1_3d();
    j3_pads_3d();
    translate([0, -explode, 0]) { pad_board_3d(); j2_pads_3d(); }
}


// ====================================================================
// DXF 导出
// ====================================================================
//   openscad -o fin.dxf -D 'MODE="fin_2d"' module_board.scad   两轴 = (Z, Y)
//   openscad -o pad.dxf -D 'MODE="pad_2d"' module_board.scad   两轴 = (X, Z)

if (MODE == "assembly") {
    if (SHOW_MOSAICO) mosaico_ghost();
    module_board_assembly(0);
} else if (MODE == "exploded") {
    if (SHOW_MOSAICO) mosaico_ghost();
    module_board_assembly(EXPLODE > 0 ? EXPLODE : 12);
} else if (MODE == "fin_2d") {
    fin_outline_2d();
} else if (MODE == "pad_2d") {
    pad_outline_2d();
} else if (MODE == "fin_dxf") {
    projection(cut = false) rotate([0, 90, 0]) fin_board_3d();
} else if (MODE == "pad_dxf") {
    projection(cut = false) rotate([-90, 0, 0]) pad_board_3d();
} else if (MODE == "none") {
    // 被 module_shell.scad include 时使用
} else {
    echo("未知 MODE：", MODE);
}


// ====================================================================
// 自检 echo —— 每次编译打印，供复核比对。全部为派生值，不是实测值。
// ====================================================================
echo("==== module_board.scad 派生尺寸（修订 c：直插 ＋ 双排 J3 ＋ 4×4 触点场）====");
echo(str("槽板 fin（YZ 面）：X [", FIN_X_MIN, " , ", FIN_X_MAX, "]  Y [", FIN_Y_MIN, " , ", FIN_Y_MAX,
         "]  Z [", FIN_Z_LO, " , ", FIN_Z_HI, "]"));
echo(str("  netlist outline_params → FIN_W_Z = ", FIN_W_Z, "  FIN_H = ", FIN_H, "  FIN_X 中面 = ", FIN_MID_X));
echo(str("触点板 pad_board（XZ 面）：X [", PAD_X_MIN, " , ", PAD_X_MAX, "]  Z [", PAD_Z_MIN, " , ", PAD_Z_MAX,
         "]  底面 Y = ", MODULE_PAD_FACE_Y));
echo(str("  netlist outline_params → PAD_BOARD_L = ", PAD_BOARD_L, "  PAD_BOARD_W = ", PAD_BOARD_W,
         "  MODULE_PAD_FACE_Y = ", MODULE_PAD_FACE_Y));
echo(str("ICD 第 1 节待填参数 → DOCK_PIN_FIELD_X0 = ", DOCK_PIN_FIELD_X0,
         "  DOCK_PIN_FIELD_Z0 = ", DOCK_PIN_FIELD_Z0,
         "  DOCK_PIN_FIELD_Y = ", DOCK_PIN_FIELD_Y));
echo(str("J2 列 1..", DOCK_COLS, " 中心 X = ", [for (c = [1 : DOCK_COLS]) j2_x(c)]));
echo(str("J2 行 A..", DOCK_ROWS, " 中心 Z = ", [for (r = [0 : DOCK_ROWS - 1]) j2_z(r)],
         "（行 A 在 +Z 屏侧，符合 ICD 第 3.1 节）"));
echo(str("J3 双排：每排 ", J3_PER_ROW, " 位 @", J3_PITCH, "，位 1 Z = ", j3_z(1),
         "  位 ", J3_PER_ROW, " Z = ", j3_z(J3_PER_ROW), "  跨距 = ", J3_SPAN_Z,
         "；两排 X = ", j3_row_x(0), " / ", j3_row_x(1)));
echo(str("直插 X 链：针尖 ", J1_TIP_X, " → 胶芯前 ", J1_BODY_FRONT_X, " → 元件面 ", FIN_X_MAX,
         " → 焊接面 ", FIN_X_MIN, " → 针尾焊点 ", FIN_SOLDER_X,
         "；模块板本体需要的 −X 占深 = ", MODULE_STACK_NEED_X, " mm"));

function V(c) = c ? "  -> OK" : "  -> FAIL: 须改设计";
EPS = 1e-6;
echo("---- 几何检查（判定不通过则须改设计，不是实测结论）----");
echo("     每条末尾为模型自判。统计失败项用 grep -c '\-> F''AIL'，结果 0 即全通过。（说明行里故意把标记拆开写，否则它会匹配到自己——2026-09-22 连踩两次这个坑。）");
echo(str("[检查 1] 槽板 Z 向须同时容下 H2 两排配合针与 J3 双排：H2 两排到板边余量 = ",
         J1_ROW_Z_MARGIN_HI, " / ", J1_ROW_Z_MARGIN_LO,
         " mm；J3 外侧焊盘到板边余量 = ", J3_Z_MARGIN_HI, " / ", J3_Z_MARGIN_LO,
         " mm；四者均应 ≥ ", PAD_EDGE_MIN,
         V(J1_ROW_Z_MARGIN_HI >= PAD_EDGE_MIN - EPS && J1_ROW_Z_MARGIN_LO >= PAD_EDGE_MIN - EPS
           && J3_Z_MARGIN_HI >= PAD_EDGE_MIN - EPS && J3_Z_MARGIN_LO >= PAD_EDGE_MIN - EPS)));
echo(str("[检查 2] 直插公头两排针 Z 间距 = ", J1_ROW_PITCH_Z,
         " mm，应等于母座 SLOT_ROW_PITCH = ", SLOT_ROW_PITCH,
         V(abs(J1_ROW_PITCH_Z - SLOT_ROW_PITCH) < EPS)));
echo(str("[检查 3] 触点面 Y = ", MODULE_PAD_FACE_Y, " 应 < Mosaico 底面 ", MOSAICO_Y_LO,
         "（ICD ME-D-07），余量 = ", MOSAICO_Y_LO - MODULE_PAD_FACE_Y,
         V(MODULE_PAD_FACE_Y < MOSAICO_Y_LO)));
echo(str("[检查 4] 触点板在 X 上完全落在 Mosaico 投影之外：J2 列 ", DOCK_COLS, " 外缘 X = ",
         j2_x(DOCK_COLS) + DOCK_PAD_D / 2, " 应 < ", SLOT_FACE_X,
         "（成立则不遮挡原生 USB-C，AS-22 只需核对 Z 向）",
         V(j2_x(DOCK_COLS) + DOCK_PAD_D / 2 < SLOT_FACE_X)));
echo(str("[检查 5] J2 焊盘到触点板边缘余量：X 向 = ", J2_X_EDGE_MARGIN,
         " mm，Z 向 = ", J2_Z_EDGE_MARGIN, " mm；应 ≥ ", PAD_EDGE_MIN,
         V(J2_X_EDGE_MARGIN >= PAD_EDGE_MIN - EPS && J2_Z_EDGE_MARGIN >= PAD_EDGE_MIN - EPS)));
echo(str("[检查 6] 定位公差 ±", DOCK_X_TOL, " mm 对 Ø", DOCK_PAD_D, " 焊盘／Ø",
         DOCK_PIN_TIP_D, " 针尖：允许偏移 = ", PAD_ALLOW_OFFSET,
         " mm，余量 = ", PAD_ALLOW_OFFSET - DOCK_X_TOL,
         " mm（须 > 0）。相邻焊盘净间距 ", DOCK_PITCH - DOCK_PAD_D, " mm",
         V(PAD_ALLOW_OFFSET - DOCK_X_TOL > EPS)));
echo(str("[检查 7] 错位不可达 1 列/1 行：定位公差 ", DOCK_X_TOL, " 应远小于半间距 ",
         DOCK_PITCH / 2, "（AS-08 一级防呆的数值依据）",
         V(DOCK_X_TOL < DOCK_PITCH / 2 && DOCK_Z_TOL < DOCK_PITCH / 2)));
echo(str("[检查 8] 绕 Y 轴 180° 错放时触点场映射到 X [",
         -(j2_x(DOCK_COLS)), " , ", -(j2_x(1)), "]，位于 +X 握把侧，底座该处无针（ICD 第 3.3 节）"));
echo(str("[检查 9] ", DOCK_COLS * DOCK_ROWS, " 针总压力 = ", F_PIN_TOTAL,
         " N；Mosaico 自重 = ", W_MOSAICO_N,
         " N。重力远不足以压紧，必须由上压框 M2 螺钉提供保持力，见 MATING.md 第 4 节"));
echo(str("[检查 9b] Y 向配合链：触点面 Y = ", MODULE_PAD_FACE_Y,
         "；弹簧针自由针尖应位于 Y = ", MODULE_PAD_FACE_Y + DOCK_PIN_TRAVEL,
         "；名义压缩 ", DOCK_PIN_TRAVEL, " mm，占全行程 ",
         DOCK_PIN_TRAVEL / DOCK_PIN_STROKE * 100, " %"));
echo(str("[检查 9c] 弹簧针行程窗口：最坏公差 ±", DOCK_Y_TOL, " → 工作行程 ",
         DOCK_PIN_TRAVEL - DOCK_Y_TOL, " ～ ", DOCK_PIN_TRAVEL + DOCK_Y_TOL,
         " mm；判据 ① 最小 ≥ 全行程×", DOCK_PIN_MIN_FRAC, " = ",
         DOCK_PIN_STROKE * DOCK_PIN_MIN_FRAC,
         "；判据 ② 最大 ≤ 全行程−", DOCK_PIN_NO_BOTTOM, " = ",
         DOCK_PIN_STROKE - DOCK_PIN_NO_BOTTOM,
         V(DOCK_PIN_TRAVEL - DOCK_Y_TOL >= DOCK_PIN_STROKE * DOCK_PIN_MIN_FRAC - EPS
           && DOCK_PIN_TRAVEL + DOCK_Y_TOL <= DOCK_PIN_STROKE - DOCK_PIN_NO_BOTTOM + EPS)));
echo(str("[检查 10] 定位孔 A 到最近板边距离 = ",
         min(MOUNT_A_Z - FIN_Z_LO, FIN_Z_HI - MOUNT_A_Z, MOUNT_A_Y - FIN_Y_MIN, FIN_Y_MAX - MOUNT_A_Y),
         " mm；孔 B = ",
         min(MOUNT_B_Z - FIN_Z_LO, FIN_Z_HI - MOUNT_B_Z, MOUNT_B_Y - FIN_Y_MIN, FIN_Y_MAX - MOUNT_B_Y),
         " mm；应 ≥ ", MOUNT_KEEPOUT_D / 2,
         V(min(MOUNT_A_Z - FIN_Z_LO, FIN_Z_HI - MOUNT_A_Z, MOUNT_A_Y - FIN_Y_MIN, FIN_Y_MAX - MOUNT_A_Y) >= MOUNT_KEEPOUT_D / 2 - EPS
           && min(MOUNT_B_Z - FIN_Z_LO, FIN_Z_HI - MOUNT_B_Z, MOUNT_B_Y - FIN_Y_MIN, FIN_Y_MAX - MOUNT_B_Y) >= MOUNT_KEEPOUT_D / 2 - EPS)));
echo(str("[检查 11] 定位孔 B 与 J1 胶芯包络：胶芯 X [", J1_BODY_X_MIN, " , ", J1_BODY_X_MAX,
         "] Y [", J1_BODY_Y_LO, " , ", J1_BODY_Y_HI, "] Z [", J1_BODY_Z_LO, " , ", J1_BODY_Z_HI,
         "]；孔 B Y = ", MOUNT_B_Y, "，禁布圆应低于胶芯下沿",
         V(MOUNT_B_Y + MOUNT_KEEPOUT_D / 2 < J1_BODY_Y_LO)));
echo(str("[检查 12] 定位孔 A 禁布圆应高于 J1 胶芯上沿（槽板沿 Z 只有 ", FIN_W_Z,
         " mm，胶芯占 ", J1_BODY_Z_HI - J1_BODY_Z_LO, " mm，两侧各剩 ",
         (FIN_W_Z - (J1_BODY_Z_HI - J1_BODY_Z_LO)) / 2, " mm，放不下 Ø", MOUNT_HOLE_D,
         " 孔配 Ø", MOUNT_KEEPOUT_D, " 禁布圆，故两孔只能排在胶芯的 ±Y 两端）",
         V(MOUNT_A_Y - MOUNT_KEEPOUT_D / 2 > J1_BODY_Y_HI)));
echo(str("[检查 13] J3 双排对接焊：两排分别落在槽板的两个板面（X = ", j3_row_x(0), " / ",
         j3_row_x(1), "），触点板上对应焊盘在落脚线两侧；单排跨距 ", J3_SPAN_Z,
         " mm，若改单排 ", J3_PER_ROW * J3_ROWS, " 位 @", J3_PITCH, " 需 ",
         (J3_PER_ROW * J3_ROWS - 1) * J3_PITCH, " mm > 板宽 ", FIN_W_Z, " mm，故必须双排",
         V(J3_SPAN_Z + J3_PAD_W + 2 * PAD_EDGE_MIN <= FIN_W_Z + EPS)));
echo("==== 结束 ====");
