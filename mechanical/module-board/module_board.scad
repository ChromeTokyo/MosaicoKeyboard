// 提案 · 未冻结 · 由 Claude 主控（claude-opus-5）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
//
// module_board.scad —— 方案 D＋G 模块板参数化机械模型
// 分支 claude/design-d/mech-module ／ 目录 mechanical/module-board/
//
// 对象：左槽转接模块板（纯无源：J1 2×10P 公头 ＋ AT24C02 ＋ 底部 2×8 触点焊盘）。
//
// 权威输入（本文必须与之一致，冲突时以它们为准）：
//   hardware/ICD-0.2-DRAFT.md                第 1 节坐标系、第 3 节弹簧针接口、第 5 节机械约束
//   origin/claude/design-d/module-board:hardware/module-board/PINMAP.md   第 4 节 J2、第 5 节板形与 J3
//   origin/claude/design-d/module-board:hardware/module-board/netlist.yaml
//       boards.fin.outline_params      = [FIN_L, FIN_H, FIN_Z]                  ← 本文给值
//       boards.pad_board.outline_params = [PAD_BOARD_L, PAD_BOARD_W, MODULE_PAD_FACE_Y] ← 本文给值
//   hardware/ASSUMPTIONS.md                  AS-01～AS-30
//
// 「L 形 PCB」的实现说明：
//   任务描述中的「L 形 PCB（上段竖直、公头朝 +X、下段延伸到 Mosaico 底面以下、底面 2×8 触点区）」
//   在几何上不能由一块平面刚性板实现（PINMAP 第 5.1 节已证明：板面法向只能是 ±X 或 ±Z，
//   不存在 −Y 法向的面）。本文按 PINMAP 第 5.2 节 AS-31-mb-1 建模为
//       槽板 fin（XY 面，竖直段） ＋ 触点板 pad_board（XZ 面，水平段），J3 半孔焊接
//   —— 其 YZ 剖面正是一个 L（竖直腹板 ＋ 水平底板），沿 X 看是 T（底板在腹板两侧各伸出）。
//   若改用刚挠结合板（PINMAP 第 5.2 节备选 ②），则确实是「一块 L 形板」，本文全部尺寸不变，
//   只是 J3 由半孔焊接改为挠性段；ASSUMPTION: AS-31-mm-13。
//
// 单位 mm。坐标系严格用 ICD 第 1 节整机坐标，不用板级局部坐标：
//   基准姿态「屏朝用户、USB-C 朝下、左槽在左」
//   +X = 用户视角向右（左槽在 −X 面）   +Y = 向上（弹簧针轴向 +Y，整机沿 −Y 落入底座）
//   +Z = 从屏面指向用户                 原点 O = Mosaico 外形包络几何中心
//   行 A 靠 +Z（屏侧），行 B 靠 −Z（背侧）；J2 列 1 在 −X 最外侧。
//
// 渲染方向提示（与 PINMAP 第 4.1 节一致）：自 +Y 向 −Y 俯视且 +X 向右时，屏幕向上方向是 −Z。


// ====================================================================
// ASSUMPTION 块 —— 本文件全部未经实物核对的输入集中在此。
// 每条给出编号与到货验证方法。本分支新引入者临时编号 AS-31-mm-n，
// 汇总阶段由主控并入 hardware/ASSUMPTIONS.md 统一编号。
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
//   验证：到货拍六面照片与轮廓拓印，量圆角半径；若圆角 > 1 mm，壳体领口贴合面须改。
MOSAICO_CORNER_R = 0;   // 建模用圆角半径；到货后回填

// ---- 二、左槽 H2（AS-02～AS-05、AS-17）----
// ASSUMPTION: AS-03 母座在 −X 面、开口朝 −X、与外壳面近平齐（凹/凸量 unknown，按 0 建模）。
//   验证：基准姿态拍 −X 面正视照；深度尺量母座开口平面相对外壳面的凹/凸深度，回填 SLOT_FACE_RECESS。
SLOT_FACE_X     = -MOSAICO_W / 2;   // 左槽所在面 X 坐标（ICD 第 1 节 SLOT_FACE_X）
SLOT_FACE_RECESS = 0;               // >0 表示母座口面内凹（沿 +X 缩进）

// ASSUMPTION: AS-02 H2 为 2×10P、间距 2.54 mm。
//   验证：卡尺量相邻针中心距 3 处；量 pin1–pin19 中心跨距（应 ≈ 9 × 2.54 = 22.86 mm）。
SLOT_PITCH      = 2.54;   // 同排相邻针中心距（沿 Y）
SLOT_ROW_PITCH  = 2.54;   // 两排中心距（沿 Z）
SLOT_PINS_PER_ROW = 10;

// ASSUMPTION: AS-04 槽中心 Z ≈ 厚度中点；Y 位置 unknown，此处按 Y 向居中建模。
//   验证：卡尺量 pin 1 中心到 −Y 面、到 +Z 面距离，pin 20 同样两值，回填下面两个量。
SLOT_CENTER_Y   = 0;      // 10 针跨距的中心 Y
SLOT_CENTER_Z   = 0;      // 两排的中心 Z

// ASSUMPTION: AS-17 奇数排（pin 1/3/…/19）在 −Z 侧还是 +Z 侧、pin 1 在 +Y 端还是 −Y 端，均 unknown。
//   影响：决定 J1 封装 1 脚方向与槽板正反面；若相反，槽板布局镜像重做（PINMAP 第 7 节 P1）。
//   验证：到货后 Mosaico 关机、不接任何外设，万用表通断档（严禁带电测电阻，测电阻必须完全断电）：
//         pin 20 对已知 GND（USB-C 外壳）通；微距拍左槽与中框丝印；与 PINMAP 第 3 节对照。
//   本文全部几何对 ±1 取值对称，只影响丝印与 1 脚标记，不影响外形尺寸。
SLOT_ODD_ROW_SIDE = -1;   // −1 = 奇数排在 −Z；+1 = 奇数排在 +Z
SLOT_PIN1_AT_PLUS_Y = true;

// ---- 三、J1 2×10P 右角公头（AS-05、AS-06、AS-31-mb-2）----
// ASSUMPTION: AS-05 槽连接器为轴向插接排针/排母（E-01 未证实）；四角银色块为整机组合用磁铁，非模块电气连接。
//   验证：目视母座孔形；回形针试四角吸附；不带电用绝缘塑料探针轻试插入深度；不拆机。
// ASSUMPTION: AS-06 主机侧母座 V1.0 原理图标注 B-2200R20P-B120（Ckmtw，LCSC C124406：右角排母、
//   3 A、绝缘体高 5 mm；V1.2 是否沿用 unknown）。配对公头基线 BOOMELE 2.54-2*10P（LCSC C9144，右角、公）。
//   **配对公头的全部尺寸「待原厂数据手册核对」**（2026-09-21 未能在线打开 C124406 图纸）。
//   验证：取得原厂规格书核针径、配合针长范围、插拔力；用候选公头只试插一次记录手感与到位量。
// ASSUMPTION: AS-31-mb-2 右角公头两排配合针相对槽板元件面的高度 ≈ 2.54 / 5.08 mm。
//   本文把它作为最关键的几何输入：见下面 Z_MARGIN_BACK 检查。
J1_ROW_NEAR_H  = 2.54;   // 近排配合针中心相对槽板元件面的高度
J1_ROW_FAR_H   = 5.08;   // 远排配合针中心相对槽板元件面的高度（应 = 近排 + SLOT_ROW_PITCH）
J1_BODY_SIDE   = +1;     // +1 = 本体装在槽板 +Z 面（针向 +Z 偏置）；−1 = 装在 −Z 面
// ASSUMPTION: AS-31-mm-2 配合针自本体前端面伸出长度 6.0 mm（候选 C124359 标「配合段 6 mm」，
//   右角件同系列沿用为假设）；到位时插入母座深度 5.0 mm（母座绝缘体高 5 mm）。待原厂图纸核对。
J1_MATE_LEN     = 6.0;
J1_INSERT_DEPTH = 5.0;
// ASSUMPTION: AS-31-mm-3 右角本体沿 X 深 8.5 mm、沿 Y 超出端针 1.5 mm、沿 Z 高出元件面 7.0 mm。待原厂图纸核对。
J1_BODY_LEN_X   = 8.5;
J1_BODY_EXT_Y   = 1.5;
J1_BODY_H_Z     = 7.0;
J1_BODY_FRONT_OVERHANG = 0;   // 本体前端面超出槽板 +X 边的量；0 = 齐平

// ---- 四、板材 ----
// ASSUMPTION: AS-31-mm-4 两块板均 FR-4 2 层 1.6 mm（与 netlist.yaml boards.*.thickness_mm 一致）。
//   见文末 echo 的 Z 余量检查：若 AS-31-mb-2 的近排高度 > 2.87 mm，槽板须改 1.0 mm 或接受背面外凸。
PCB_T_FIN = 1.6;
PCB_T_PAD = 1.6;

// ---- 五、弹簧针接口 J2（AS-07、AS-08、AS-31-mb-3）----
// ASSUMPTION: AS-07 2.54 mm 间距、2 行 × 8 列 = 16 针；逐针分配见 ICD 第 3.2 节 / PINMAP 第 4.2 节。
DOCK_PITCH = 2.54;
DOCK_COLS  = 8;
DOCK_ROWS  = 2;
// ASSUMPTION: AS-31-mb-3 J2 焊盘圆形 Ø1.8 mm（由 module-board 分支提出）。
//   本文第 8 节 echo 给出与定位公差的复算，并建议改 Ø2.0（见 MATING.md 第 6 节）。
DOCK_PAD_D = 1.8;
// ASSUMPTION: AS-31-mm-5 弹簧针针头直径 Ø0.9 mm、工作行程 0.8 mm、全行程 1.5 mm、
//   工作行程下单针压力 0.6 N。**全部「待原厂数据手册核对」**，选型归 dock-board 任务。
//   验证：dock-board 选定型号后打开原厂数据手册记录 URL 与额定；G6-G2 每 10 次插拔复测压降。
DOCK_PIN_TIP_D     = 0.9;
DOCK_PIN_TRAVEL    = 0.8;
DOCK_PIN_STROKE    = 1.5;
DOCK_PIN_FORCE_N   = 0.6;
// ASSUMPTION: AS-31-mm-6 托架对配合的定位公差目标 ±0.45 mm（X、Z 同值），由壳体滑配与导向筋实现。
//   远小于 1 列间距之半 1.27 mm，满足 AS-08「沿 X 错位不可能达到 2 列」。
//   验证：首版壳体与托架打印后，用带焊盘的无源模块板样件反复放入 20 次，每次量针尖落点偏移（G6-H2 同时做）。
DOCK_X_TOL = 0.45;
DOCK_Z_TOL = 0.45;

// ---- 六、触点面相对 Mosaico 底面的落差（ME-D-07、AS-22）----
// ASSUMPTION: AS-31-mm-7 触点面比 Mosaico −Y 面再低 1.5 mm，使模块板底面成为整机最低面。
//   验证：G6-H1／PINMAP P11，装配后深度尺量 MODULE_PAD_FACE_Y 相对 Mosaico 底面；
//         同时确认原生 USB-C 能插入（AS-22）。
PAD_FACE_DROP = 1.5;

// ---- 七、J3 90° 转向接头（AS-31-mb-5）----
// ASSUMPTION: AS-31-mb-5 16 位半孔，间距 1.5 mm、钻孔 Ø0.7 mm（嘉立创半孔规则：钻孔与孔边距
//   均 ≥ 0.6 mm，板尺寸 ≥ 10 × 10 mm；2026-09-21 检索 jlcpcb.com 半孔说明）。
//   单点载流 ≥ 0.5 A 为假设；DOCK_5V / DOCK_GND 各 2 位并联覆盖 AS-09 峰值 ≤ 1 A。
//   验证：PINMAP P10，首版样板 0.5 A／1.0 A 下测 J3 两端压降与温升。
J3_N     = 16;
J3_PITCH = 1.5;
J3_HOLE_D = 0.7;

// ---- 八、外形与定位孔（本文给值，回填 netlist.yaml 的 outline_params）----
// ASSUMPTION: AS-31-mm-8 槽板 X 向长 26.0 mm、顶边 Y = +15.0 mm；触点板与槽板 X 向等长齐平、
//   Z 向宽 8.0 mm。取值依据见文末 echo 的余量核算；到货关闭 AS-01/AS-02/AS-04 后复核。
FIN_L        = 26.0;    // 槽板 X 向长
FIN_Y_MAX    = 15.0;    // 槽板顶边 Y
PAD_BOARD_W  = 8.0;     // 触点板 Z 向宽
// ASSUMPTION: AS-31-mm-9 定位孔 Ø2.2 mm 两个，位置见下。用于壳体空心柱定位＋M2 自攻螺钉贯穿。
//   验证：首版壳体装配试配；若 3D 打印柱径偏差大，改 Ø2.4 并在壳体侧加削平。
MOUNT_HOLE_D = 2.2;
MOUNT_A_X = -46.10;  MOUNT_A_Y = 11.50;    // 主定位（圆柱）
MOUNT_B_X = -26.00;  MOUNT_B_Y = -18.00;   // 副定位（壳体侧用菱形/削边柱，避免过定位）
MOUNT_KEEPOUT_D = 5.0;   // 焊盘/走线禁布圆直径

// ---- 九、显示/导出控制（非尺寸）----
MODE = "assembly";   // assembly | fin_2d | pad_2d | fin_dxf | pad_dxf | exploded
$fn  = 48;
SHOW_MOSAICO = true;
EXPLODE      = 0;    // exploded 模式下触点板沿 −Y 拉开的距离


// ====================================================================
// 派生量 —— 全部由上面的 ASSUMPTION 算出，此处不得出现新的数字常量
// ====================================================================

// 左槽两排配合针的 Z 坐标
SLOT_ROW_ODD_Z  = SLOT_CENTER_Z + SLOT_ODD_ROW_SIDE * SLOT_ROW_PITCH / 2;
SLOT_ROW_EVEN_Z = SLOT_CENTER_Z - SLOT_ODD_ROW_SIDE * SLOT_ROW_PITCH / 2;

// 10 针沿 Y 的跨距与端点（PINMAP 第 5.1 节：−X 面 45.19(Y) × 11.48(Z)，22.86 mm 只放得下沿 Y）
SLOT_ROW_SPAN_Y = (SLOT_PINS_PER_ROW - 1) * SLOT_PITCH;   // 22.86
SLOT_Y_LO = SLOT_CENTER_Y - SLOT_ROW_SPAN_Y / 2;
SLOT_Y_HI = SLOT_CENTER_Y + SLOT_ROW_SPAN_Y / 2;

// 槽板元件面 Z：使近排配合针落在离本体侧较近的那一排槽针上
FIN_FACE_Z = (SLOT_CENTER_Z - J1_BODY_SIDE * SLOT_ROW_PITCH / 2)
             - J1_BODY_SIDE * J1_ROW_NEAR_H;
FIN_BACK_Z = FIN_FACE_Z - J1_BODY_SIDE * PCB_T_FIN;
FIN_MID_Z  = (FIN_FACE_Z + FIN_BACK_Z) / 2;          // 槽板中面 Z —— 回填 netlist 的 FIN_Z
FIN_Z      = FIN_MID_Z;                              // netlist.yaml outline_params 名
FIN_Z_LO   = min(FIN_FACE_Z, FIN_BACK_Z);
FIN_Z_HI   = max(FIN_FACE_Z, FIN_BACK_Z);

// 槽板 X 范围：本体前端面与槽板 +X 边齐平，配合针伸入母座 J1_INSERT_DEPTH
J1_TIP_X       = SLOT_FACE_X + SLOT_FACE_RECESS + J1_INSERT_DEPTH;   // 到位时针尖 X
J1_BODY_FRONT_X = J1_TIP_X - J1_MATE_LEN;
FIN_X_MAX = J1_BODY_FRONT_X - J1_BODY_FRONT_OVERHANG;
FIN_X_MIN = FIN_X_MAX - FIN_L;

// 触点面与触点板
MOSAICO_Y_LO = -MOSAICO_H / 2;
MODULE_PAD_FACE_Y = MOSAICO_Y_LO - PAD_FACE_DROP;    // 触点板底面 Y（ICD DOCK_PIN_FIELD_Y）
PAD_TOP_Y  = MODULE_PAD_FACE_Y + PCB_T_PAD;          // 触点板顶面 = 槽板底边
FIN_Y_MIN  = PAD_TOP_Y;
FIN_H      = FIN_Y_MAX - FIN_Y_MIN;                  // 回填 netlist 的 FIN_H
PAD_BOARD_L = FIN_L;                                 // 回填 netlist 的 PAD_BOARD_L
PAD_X_MIN = FIN_X_MIN;
PAD_X_MAX = FIN_X_MAX;
PAD_Z_MIN = FIN_MID_Z - PAD_BOARD_W / 2;
PAD_Z_MAX = FIN_MID_Z + PAD_BOARD_W / 2;

// J3：沿槽板底边排布，居中
J3_SPAN     = (J3_N - 1) * J3_PITCH;                 // 22.5
J3_CENTER_X = (FIN_X_MIN + FIN_X_MAX) / 2;
function j3_x(i) = J3_CENTER_X - J3_SPAN / 2 + (i - 1) * J3_PITCH;   // i = 1..16，位 1 在 −X 端

// J2：与 J3 同心，列 1 在 −X 最外侧；行 A 在 +Z、行 B 在 −Z，跨骑槽板中面
J2_SPAN_X = (DOCK_COLS - 1) * DOCK_PITCH;            // 17.78
DOCK_PIN_FIELD_X0 = J3_CENTER_X - J2_SPAN_X / 2;     // 列 1 中心 X（ICD 第 1 节参数）
DOCK_PIN_FIELD_Z0 = FIN_MID_Z + DOCK_PITCH / 2;      // 行 A 中心 Z（ICD 第 1 节参数）
DOCK_PIN_FIELD_Y  = MODULE_PAD_FACE_Y;               // 配合面高度（ICD 第 1 节参数）
function j2_x(c) = DOCK_PIN_FIELD_X0 + (c - 1) * DOCK_PITCH;         // c = 1..8
function j2_z(r) = DOCK_PIN_FIELD_Z0 - (r == 0 ? 0 : DOCK_PITCH);    // r = 0 → 行 A，1 → 行 B

// J1 本体包络
J1_BODY_X_MIN = J1_BODY_FRONT_X - J1_BODY_LEN_X;
J1_BODY_Y_LO  = SLOT_Y_LO - J1_BODY_EXT_Y;
J1_BODY_Y_HI  = SLOT_Y_HI + J1_BODY_EXT_Y;
J1_BODY_Z_LO  = (J1_BODY_SIDE > 0) ? FIN_FACE_Z : FIN_FACE_Z - J1_BODY_H_Z;
J1_BODY_Z_HI  = (J1_BODY_SIDE > 0) ? FIN_FACE_Z + J1_BODY_H_Z : FIN_FACE_Z;

// 余量核算（供文末 echo）
Z_MARGIN_BACK  = MOSAICO_T / 2 - max(abs(FIN_Z_LO), abs(FIN_Z_HI));  // 槽板板面到 Mosaico 同侧面的余量
J1_ROW_NEAR_H_MAX = MOSAICO_T / 2 - SLOT_ROW_PITCH / 2 - PCB_T_FIN;  // 不外凸时近排高度上限
J3_EDGE_MARGIN = (FIN_L - J3_SPAN) / 2;
J2_X_EDGE_MARGIN = (PAD_BOARD_L - J2_SPAN_X) / 2 - DOCK_PAD_D / 2;
J2_Z_EDGE_MARGIN = (PAD_BOARD_W - DOCK_PITCH) / 2 - DOCK_PAD_D / 2;
PAD_ALLOW_OFFSET = (DOCK_PAD_D - DOCK_PIN_TIP_D) / 2;   // 针尖完全落在焊盘内允许的最大偏移
F_PIN_TOTAL = DOCK_PIN_FORCE_N * DOCK_COLS * DOCK_ROWS; // 16 针总压力
W_MOSAICO_N = MOSAICO_M / 1000 * 9.8;


// ====================================================================
// 几何
// ====================================================================

// ---- 2D 外形（同时用于挤出与 DXF 导出）----
module fin_outline_2d() {
    difference() {
        translate([FIN_X_MIN, FIN_Y_MIN]) square([FIN_L, FIN_H]);
        // 定位孔
        translate([MOUNT_A_X, MOUNT_A_Y]) circle(d = MOUNT_HOLE_D);
        translate([MOUNT_B_X, MOUNT_B_Y]) circle(d = MOUNT_HOLE_D);
        // J3 半孔：钻孔中心落在底边上，成形后为半孔
        for (i = [1 : J3_N])
            translate([j3_x(i), FIN_Y_MIN]) circle(d = J3_HOLE_D);
    }
}

// 触点板外形。2D 的第一轴是 X，第二轴是整机坐标的 Z（不是 Y）。
// 触点板本身无孔；保留 difference 结构，便于后续加工艺边或定位孔。
module pad_outline_2d() {
    difference() {
        translate([PAD_X_MIN, PAD_Z_MIN]) square([PAD_BOARD_L, PAD_BOARD_W]);
        // （暂无减料）
        translate([PAD_X_MIN - 10, PAD_Z_MIN - 10]) square([0.001, 0.001]);
    }
}

// ---- 3D ----
module fin_board_3d() {
    color("DarkGreen")
    translate([0, 0, FIN_Z_LO])
        linear_extrude(height = PCB_T_FIN)
            fin_outline_2d();
}

// 触点板实体。直接按包络建模，避免「2D 外形在 XZ、挤出方向在 Y」的旋转二义。
// 外形若将来变为非矩形，改为：rotate([-90,0,0]) linear_extrude(PCB_T_PAD) pad_outline_2d();
// rotate([-90,0,0]) 把 (x,y,z) 映为 (x,z,−y)，故挤出方向 +Z 变为 +Y，2D 第二轴 y 变为 −Z——
// 使用时须把 pad_outline_2d() 的第二轴取反，否则 Z 向镜像。本文因此不用该写法。
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

module j1_body_3d() {
    color("DimGray")
    translate([J1_BODY_X_MIN, J1_BODY_Y_LO, J1_BODY_Z_LO])
        cube([J1_BODY_LEN_X, J1_BODY_Y_HI - J1_BODY_Y_LO, J1_BODY_Z_HI - J1_BODY_Z_LO]);
}

module j1_pins_3d() {
    color("Goldenrod")
    for (k = [0 : SLOT_PINS_PER_ROW - 1]) {
        y = SLOT_Y_LO + k * SLOT_PITCH;
        for (zr = [SLOT_ROW_ODD_Z, SLOT_ROW_EVEN_Z])
            translate([J1_BODY_FRONT_X, y - 0.32, zr - 0.32])
                cube([J1_MATE_LEN, 0.64, 0.64]);
    }
}

// AT24C02 SOIC-8 与 0603 器件只作占位包络，位置由 module-board 布局最终确定
// ASSUMPTION: AS-31-mm-10 U1（SOIC-8，约 5.0 × 4.0 × 1.75 mm）与测试点区放在槽板 −X 下部，
//   避开 J1 本体、定位孔禁布圆与 J3 边缘 2 mm 带。验证：module-board 出 Gerber 后对照本模型。
U1_X = -44.0;  U1_Y = -6.0;
module u1_3d() {
    color("Black")
    translate([U1_X - 2.5, U1_Y - 2.0, FIN_FACE_Z + (J1_BODY_SIDE > 0 ? 0 : -1.75)])
        cube([5.0, 4.0, 1.75]);
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
    translate([0, -explode, 0]) { pad_board_3d(); j2_pads_3d(); }
}


// ====================================================================
// DXF 导出
// ====================================================================
// 方式一（推荐，尺寸无损）：直接导出本文件的 2D 模块。
//   openscad -o fin.dxf -D 'MODE="fin_2d"' module_board.scad
//   openscad -o pad.dxf -D 'MODE="pad_2d"' module_board.scad
//   fin_2d 的两轴是 (X, Y)；pad_2d 的两轴是 (X, Z)，导入 EDA 时第二轴按 Z 解读。
//
// 方式二（对已建成的 3D 实体取投影，用于核对建模与外形是否一致）：
//   projection(cut = false) 把实体沿观察轴压扁到 XY 平面，因此导出前必须先把
//   目标板旋转到与 XY 平面平行：
//     槽板本就在 XY 面，直接 projection(cut=false) fin_board_3d();
//     触点板在 XZ 面，须先 rotate([90,0,0]) 再 projection。
//   命令：openscad -o fin_proj.dxf -D 'MODE="fin_dxf"' module_board.scad
//        openscad -o pad_proj.dxf -D 'MODE="pad_dxf"' module_board.scad
//   注意：projection() 会丢失 Z 信息且合并重叠轮廓，只可用于核对，不可作为制造底图。

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
    projection(cut = false) fin_board_3d();
} else if (MODE == "pad_dxf") {
    projection(cut = false) rotate([90, 0, 0]) pad_board_3d();
} else {
    echo("未知 MODE：", MODE);
}


// ====================================================================
// 自检 echo —— 每次编译打印，供复核比对。全部为派生值，不是实测值。
// ====================================================================
echo("==== module_board.scad 派生尺寸（ASSUMPTION，未经实物核对）====");
echo(str("槽板 fin：X [", FIN_X_MIN, " , ", FIN_X_MAX, "]  Y [", FIN_Y_MIN, " , ", FIN_Y_MAX,
         "]  Z [", FIN_Z_LO, " , ", FIN_Z_HI, "]"));
echo(str("  netlist outline_params → FIN_L = ", FIN_L, "  FIN_H = ", FIN_H, "  FIN_Z = ", FIN_Z));
echo(str("触点板 pad_board：X [", PAD_X_MIN, " , ", PAD_X_MAX, "]  Z [", PAD_Z_MIN, " , ", PAD_Z_MAX,
         "]  底面 Y = ", MODULE_PAD_FACE_Y));
echo(str("  netlist outline_params → PAD_BOARD_L = ", PAD_BOARD_L, "  PAD_BOARD_W = ", PAD_BOARD_W,
         "  MODULE_PAD_FACE_Y = ", MODULE_PAD_FACE_Y));
echo(str("ICD 第 1 节待填参数 → DOCK_PIN_FIELD_X0 = ", DOCK_PIN_FIELD_X0,
         "  DOCK_PIN_FIELD_Z0 = ", DOCK_PIN_FIELD_Z0,
         "  DOCK_PIN_FIELD_Y = ", DOCK_PIN_FIELD_Y));
echo(str("J2 列 1..8 中心 X = ", [for (c = [1 : DOCK_COLS]) j2_x(c)]));
echo(str("J2 行 A Z = ", j2_z(0), "  行 B Z = ", j2_z(1), "（行 A 在 +Z 屏侧，符合 ICD 第 3.1 节）"));
echo(str("J3 位 1 X = ", j3_x(1), "  位 16 X = ", j3_x(J3_N), "  跨距 = ", J3_SPAN,
         "  边距 = ", J3_EDGE_MARGIN));

echo("---- 几何检查（不通过则须改设计，不是实测结论）----");
echo(str("[检查 1] 槽板背面到 Mosaico 同侧外表面余量 = ", Z_MARGIN_BACK,
         " mm；> 0 表示槽板不外凸。近排针高上限 J1_ROW_NEAR_H ≤ ", J1_ROW_NEAR_H_MAX,
         " mm（当前 ", J1_ROW_NEAR_H, "）"));
echo(str("[检查 2] 两排配合针高差 = ", J1_ROW_FAR_H - J1_ROW_NEAR_H,
         " mm，应等于 SLOT_ROW_PITCH = ", SLOT_ROW_PITCH));
echo(str("[检查 3] 触点面 Y = ", MODULE_PAD_FACE_Y, " 应 < Mosaico 底面 ", MOSAICO_Y_LO,
         "（ICD ME-D-07），余量 = ", MOSAICO_Y_LO - MODULE_PAD_FACE_Y));
echo(str("[检查 4] 触点板在 X 上完全落在 Mosaico 投影之外：J2 列 8 外缘 X = ",
         j2_x(DOCK_COLS) + DOCK_PAD_D / 2, " 应 < ", SLOT_FACE_X,
         "（成立则不遮挡原生 USB-C，AS-22 只需核对 Z 向）"));
echo(str("[检查 5] J2 焊盘到触点板边缘余量：X 向 = ", J2_X_EDGE_MARGIN,
         " mm，Z 向 = ", J2_Z_EDGE_MARGIN, " mm"));
echo(str("[检查 6] 定位公差 ±", DOCK_X_TOL, " mm 对 Ø", DOCK_PAD_D, " 焊盘／Ø",
         DOCK_PIN_TIP_D, " 针尖：允许偏移 = ", PAD_ALLOW_OFFSET,
         " mm，余量 = ", PAD_ALLOW_OFFSET - DOCK_X_TOL,
         " mm（≤ 0 时建议 J2 焊盘改 Ø2.0，净间距仍有 ",
         DOCK_PITCH - 2.0, " mm）"));
echo(str("[检查 7] 错位不可达 2 列：定位公差 ", DOCK_X_TOL, " 应远小于半间距 ",
         DOCK_PITCH / 2, "（AS-08 一级防呆的数值依据）"));
echo(str("[检查 8] 绕 Y 轴 180° 错放时触点场映射到 X [",
         -(j2_x(DOCK_COLS)), " , ", -(j2_x(1)), "]，位于 +X 握把侧，底座该处无针（ICD 第 3.3 节）"));
echo(str("[检查 9] 16 针总压力 = ", F_PIN_TOTAL, " N；Mosaico 自重 = ", W_MOSAICO_N,
         " N。重力远不足以压紧，必须由卡扣提供保持力，见 MATING.md 第 4 节"));
echo(str("[检查 10] 定位孔 A 到最近板边距离 = ",
         min(MOUNT_A_X - FIN_X_MIN, FIN_X_MAX - MOUNT_A_X, MOUNT_A_Y - FIN_Y_MIN, FIN_Y_MAX - MOUNT_A_Y),
         " mm；孔 B = ",
         min(MOUNT_B_X - FIN_X_MIN, FIN_X_MAX - MOUNT_B_X, MOUNT_B_Y - FIN_Y_MIN, FIN_Y_MAX - MOUNT_B_Y),
         " mm；应 ≥ ", MOUNT_KEEPOUT_D / 2));
echo(str("[检查 11] 定位孔 B 与 J1 本体包络：本体 X [", J1_BODY_X_MIN, " , ", J1_BODY_FRONT_X,
         "] Y [", J1_BODY_Y_LO, " , ", J1_BODY_Y_HI, "]；孔 B Y = ", MOUNT_B_Y,
         "，应低于本体下沿"));
echo("==== 结束 ====");
