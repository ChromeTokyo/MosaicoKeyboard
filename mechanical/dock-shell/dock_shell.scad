// 提案 · 未冻结 · 由 Claude 主控（claude-opus-5）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
//
// dock_shell.scad —— 方案 D＋G 底座外壳（长条手持终端）参数化模型
// 分支 claude/design-d/mech-dock，目录 mechanical/dock-shell/
//
// 坐标系严格照 hardware/ICD-0.2-DRAFT.md 第 1 节：
//   原点 O = Mosaico 外形包络几何中心；+X 用户视角向右；+Y 向上（弹簧针轴向，落入方向 −Y）；
//   +Z 由屏面指向用户。基准姿态固定文字：「屏朝用户、USB-C 朝下、左槽在左」。
// 本文件不使用任何俯视/背视照片的「左右」。
//
// 标识符一律 ASCII（OpenSCAD 不接受非 ASCII 标识符），说明用中文注释。
// 所有尺寸集中在下面的 [ASSUMPTION 参数块]；派生量在其后统一计算，模块体内不再出现裸数字。
//
// 用法：
//   openscad -D 'PART="upper"'  -o upper.stl  dock_shell.scad
//   PART 取值：assembly / upper / lower / frame / mockup_upper / mockup_lower / section

/* =====================================================================
   [ASSUMPTION 参数块] 每一项都未经实物核对，到货验证步骤见 ERGONOMICS.md 第 6 节
   与 hardware/ASSUMPTIONS.md。本文件新增假设临时编号 AS-31-mechdock-n。
   ===================================================================== */

// --- [1] Mosaico 本体 ---------------------------------------------------
// ASSUMPTION: AS-01 外形 45.19 x 45.19 x 11.48 mm、33 g（官方视频简介标称，非图纸）
MOSAICO_W = 45.19;   // X
MOSAICO_H = 45.19;   // Y
MOSAICO_T = 11.48;   // Z

// --- [2] 模块板占用的空间（与 mech-module 共用，须双方一致）-------------
// ASSUMPTION: AS-31-mechdock-1 槽板＋H2 配对公头在 −X 方向占用 5.00 mm
//   （公头胶芯 ~2.54 ＋ PCB 1.6 ＋ 余量）。依赖 AS-02/AS-05/AS-06。
MODULE_STACK_X  = 5.00;
// ASSUMPTION: AS-31-mechdock-2 触点板配合面低于 Mosaico −Y 面 3.20 mm
//   （触点板厚 1.0～1.6 ＋ 装配间隙）。须满足 ICD ME-D-07：配合面 Y < −MOSAICO_H/2。
MODULE_UNDER_Y  = 3.20;
// ASSUMPTION: AS-31-mechdock-3 触点板外形 22.0 (X) x 9.0 (Z)
CONTACT_PCB_W   = 22.00;
CONTACT_PCB_D   =  9.00;

// --- [3] 弹簧针场（ICD 第 1 节列为「由机械任务给值」的参数）-------------
// ASSUMPTION: AS-07 2.54 mm、2 行 x 8 列
DOCK_PITCH = 2.54;
DOCK_COLS  = 8;
DOCK_ROWS  = 2;
// 本任务给出的数值（ICD 第 1 节 DOCK_PIN_FIELD_*）：
// ASSUMPTION: AS-31-mechdock-4 列 1（−X 最外）针尖中心 X = −26.00
DOCK_PIN_FIELD_X0 = -26.00;
// ASSUMPTION: AS-31-mechdock-5 行 A（+Z，屏侧）中心 Z = +1.27，行 B = −1.27
//   取对 Mosaico 厚度中面对称，使 ICD 第 3.3 节「Z 错一行」分析左右等价。
DOCK_PIN_FIELD_Z0 =  1.27;
// ASSUMPTION: AS-31-mechdock-6 托架定位公差（ICD 3.3 一级防呆要求 < 半个列距 1.27）
DOCK_X_TOL = 0.35;
DOCK_Z_TOL = 0.35;
// ASSUMPTION: AS-31-mechdock-7 弹簧针自由伸出 4.50、工作压缩后伸出 3.20（选型后回填，AS-26）
POGO_FREE_H = 4.50;
POGO_WORK_H = 3.20;
POGO_PCB_T  = 1.00;   // 弹簧针小板厚（90 度半孔焊在主板正面，同模块板 J3 做法）

// --- [4] 配合与工艺间隙 -------------------------------------------------
// ASSUMPTION: AS-31-mechdock-8 落入槽单边配合间隙 0.35（FDM，首版）
CLR_FIT   = 0.35;
CLR_PRINT = 0.20;   // 印刷件之间的一般活动间隙
WALL      = 2.00;   // 外壳壁厚
BAY_WALL  = 2.00;   // 落入槽壁厚

// --- [5] 整机外形 -------------------------------------------------------
// ASSUMPTION: AS-31-mechdock-9 屏面前沉 2.00（Mosaico 前面低于外壳前面 2 mm）
FRONT_PROUD = 2.00;
// ASSUMPTION: AS-31-mechdock-10 机身核心板厚 23.0（不含握把凸出）
CORE_T      = 23.00;
// ASSUMPTION: AS-31-mechdock-11 整机长度 167.0（由握把可达性反推，见 ERGONOMICS.md 第 2 节）
W_TOTAL     = 167.00;
R_CORNER    = 6.00;
// ASSUMPTION: AS-31-mechdock-12 顶端外表面 Y = +33.0（上压框 ＋ L/R 区）
Y_TOP_OUT   = 33.00;
// ASSUMPTION: AS-31-mechdock-13 屏窗四周压边 2.00（Mosaico 屏幕有效区未知，AS-25）
BEZEL_OVERLAP = 2.00;

// --- [6] 握把（深度、倾角可调）-----------------------------------------
GRIP_X_IN      = 30.00;   // 握把内侧 |X|
GRIP_Y_TOP     =  8.00;   // 握把上缘 Y
GRIP_Y_BOT     = -60.00;  // 握把下缘 Y
GRIP_R         =  8.00;   // 握把圆角半径
// 「深度倾角可调」：上下两端各自的后凸深度，两者之差即倾角
// ASSUMPTION: AS-31-mechdock-14 上端后凸 1.5、下端后凸 5.0（握把最厚处 28.0）
GRIP_DEPTH_TOP =  1.50;
GRIP_DEPTH_BOT =  5.00;
// ASSUMPTION: AS-31-mechdock-15 握把下端向内收 5.0（掌心收拢）
GRIP_RAKE_X    =  5.00;

// --- [7] 电池仓（AS-12：1500 mAh 为参数化默认，型号未定）---------------
// ASSUMPTION: AS-12 ＋ AS-31-mechdock-16 采用 803450 级软包（8.0 x 34 x 50 mm，标称 1500 mAh）
BATT_T   =  8.00;   // Z
BATT_H   = 34.00;   // Y
BATT_W   = 50.00;   // X
BATT_CLR =  1.00;
// ASSUMPTION: AS-31-mechdock-17 电池偏置 −X，给 +X 侧让出原生 USB-C 直通道
BATT_X_CTR = -35.00;
BATT_Y_TOP = -27.00;

// --- [8] 底座主板（XY 面环形板，中央开窗让 Mosaico 穿过）---------------
// ASSUMPTION: AS-31-mechdock-18 主板厚 1.6，正面（元件面）Z = −2.60
BOARD_T       = 1.60;
BOARD_Z_FRONT = -2.60;
BOARD_EDGE_CLR = 0.40;
BOARD_TOP_Y    = 30.50;   // 主板上缘（L/R 开关所在带）

// --- [9] 按键（6x6 轻触开关）------------------------------------------
// ASSUMPTION: AS-31-mechdock-19 6.0 x 6.0 x 4.3 mm 轻触开关，柱头 Ø3.5、行程 0.25
SW_SIZE   = 6.00;
SW_H      = 4.30;
SW_ACT_D  = 3.50;
SW_TRAVEL = 0.25;
// D-pad（左握把）
DPAD_X = -54.00;
DPAD_Y =  -4.00;
DPAD_SW_R  = 9.50;    // 四个开关中心到十字中心
DPAD_ARM_L = 12.00;   // 十字臂长（中心到端）
DPAD_ARM_W = 10.50;   // 十字臂宽
// ABXY（右握把）
ABXY_X = 54.00;
ABXY_Y = -4.00;
ABXY_R  = 13.00;      // 四键中心到菱形中心
ABXY_D  = 10.50;      // 键帽直径
// 键帽配合（keycaps.scad 用同名参数，二者由 include 共享，不得各写一份）
// ASSUMPTION: AS-31-mechdock-21 键帽法兰兜深 1.5、法兰厚 1.0 → 限位行程 0.5 mm > 开关行程 0.25
CAP_FLANGE_MARGIN = 1.50;   // 法兰相对帽体的单边外扩
CAP_POCKET_T      = 1.50;   // 前壁内侧法兰兜深度
CAP_FLANGE_T      = 1.00;   // 法兰厚
CAP_PROUD         = 1.50;   // 帽面高出前面外表面
CAP_GUIDE_WALL    = 2.00;
// L/R（每侧握把顶部前倾面，按压方向 −Z）
LR_X   = 58.00;
LR_Y   = 27.50;       // L/R 键条（外露件）中心，人机位置，由 ERGONOMICS 定
LR_BAR_W = 20.00;     // X
LR_BAR_H =  8.00;     // Y
// ASSUMPTION: AS-31-mechdock-24 L/R **开关**中心与键条中心在 Y 上错开 1.0 mm。
//   2026-09-21 增加：开关若与键条同在 Y = 27.50，其 7 见方禁布区上沿到 Y = 31.00，
//   而主板上缘只到 BOARD_TOP_Y = 30.50，开关有 0.5 mm 悬在板外——
//   由 check_board_outline.py 查出（此前无人发现，因为板外形此前根本不存在）。
//   键条不动（人机位置不改），只把开关下移到 26.50，禁布上沿 30.00，留 0.5 mm 余量；
//   键条底面出一道 1.0 mm 的触动凸台压到开关柱头，是常规肩键做法。
//   验证：首版板与壳到手后，量键条行程终点是否仍能可靠触动开关。
LR_SW_Y = 26.50;
LR_SW_OFFSET_Y = LR_Y - LR_SW_Y;   // 键条触动凸台需要覆盖的 Y 偏移

// --- [10] 上压框 --------------------------------------------------------
// ASSUMPTION: AS-31-mechdock-20 弹簧针单针工作压力。
//   2026-09-21 由注释提升为变量：原值只写在注释里不参与任何校验，
//   这正是它与模块侧 MATING.md 要求的 ≤0.6 N 分歧长期没被发现的原因。
//   **注意：0.9 与模块侧的 0.6 仍然冲突，未裁定**，此处如实保留底座侧原值，
//   由 check_cross_branch.py 报出来，不私自改成一致。
POGO_FORCE_N = 0.9;   // 总预压力 = 16 × 0.9 = 14.4 N
// 底座当前实现的保持力：可拆上压框，**未给出任何保持力数值**，卡扣数量为 0。
// 模块侧 MATING.md 第 4.1 节要求 ≥30 N。如实吐 0 让脚本报出缺口。
RETENTION_PROVIDED_N = 0;
// 四角硬限位柱的 Y 向尺寸（原为 cube 里的字面量 2.6，提成变量以便参与契约）
STOP_POST_H = 2.6;
FRAME_H       = 9.00;
FRAME_TONGUE_L = 3.00;
FRAME_TONGUE_H = 4.00;
FRAME_PAD_T    = 1.20;   // 压面软垫厚（TPU 或泡棉胶带）

// --- [11] 开孔 ----------------------------------------------------------
// ASSUMPTION: AS-22 原生 USB-C 位于 −Y 面、X/Z 位置未知；默认取 X 居中、Z 居中
NATIVE_USB_X   =  0.00;
NATIVE_USB_W   = 12.00;
NATIVE_USB_D   =  9.00;
// 底座自身 USB-C（主板下缘）
DOCK_USB_X     = 30.00;
DOCK_USB_W     =  9.60;
DOCK_USB_H     =  4.00;
// ASSUMPTION: AS-25 扬声器/麦克风位置未知 → 落入槽背面与后壳做对位栅格孔（兼散热）
GRILLE_D       =  2.00;
GRILLE_PITCH   =  4.50;
// 螺柱
BOSS_OD = 5.60;
BOSS_ID = 1.70;   // M2 自攻底孔
SCREW_CLR_D = 2.40;

// --- [12] 渲染 ----------------------------------------------------------
PART = "assembly";
FN_R = 28;
$fa = 4;
$fs = 0.5;

/* =====================================================================
   派生量（不要在此之下再写裸数字）
   ===================================================================== */
Z_FRONT_OUT  = MOSAICO_T/2 + FRONT_PROUD;          // +7.74
Z_BACK_CORE  = Z_FRONT_OUT - CORE_T;               // −15.26
Z_SPLIT      = -(MOSAICO_T/2 + CLR_FIT);           // −6.09，前后壳分型面 = 落入槽背面
GRIP_X_OUT   = W_TOTAL/2;
BOARD_Z_BACK = BOARD_Z_FRONT - BOARD_T;            // −4.20

BAY_X_MIN   = -(MOSAICO_W/2 + MODULE_STACK_X + CLR_FIT);   // −27.945
BAY_X_MAX   =  (MOSAICO_W/2 + CLR_FIT);                    // +22.945
BAY_Y_FLOOR = -(MOSAICO_H/2 + MODULE_UNDER_Y);             // −25.795
BAY_Z_MIN   = -(MOSAICO_T/2 + CLR_FIT);                    // −6.09
BAY_Z_MAX   =  (MOSAICO_T/2 + CLR_FIT);                    // +6.09

// 弹簧针配合面 = 模块板触点面（ICD 第 1 节 DOCK_PIN_FIELD_Y）
DOCK_PIN_FIELD_Y = BAY_Y_FLOOR;
POGO_PCB_Y_TOP   = DOCK_PIN_FIELD_Y - POGO_WORK_H;         // 弹簧针小板上表面
DOCK_FIELD_W     = (DOCK_COLS - 1) * DOCK_PITCH;           // 17.78
DOCK_FIELD_XC    = DOCK_PIN_FIELD_X0 + DOCK_FIELD_W/2;     // −17.11

BATT_X_MIN = BATT_X_CTR - BATT_W/2;
BATT_X_MAX = BATT_X_CTR + BATT_W/2;
BATT_Y_BOT = BATT_Y_TOP - BATT_H;
BATT_Z_MAX = BOARD_Z_BACK - 0.30;
BATT_Z_MIN = BATT_Z_MAX - BATT_T;

USB_ZONE_H = 4.50;
Y_BOT_OUT  = BATT_Y_BOT - BATT_CLR - USB_ZONE_H - WALL;    // −68.5
H_TOTAL    = Y_TOP_OUT - Y_BOT_OUT;
T_GRIP_MAX = Z_FRONT_OUT - (Z_BACK_CORE - GRIP_DEPTH_BOT);

WIN_X_MIN = -MOSAICO_W/2 + BEZEL_OVERLAP;
WIN_X_MAX =  MOSAICO_W/2 - BEZEL_OVERLAP;
WIN_Y_MIN = -MOSAICO_H/2 + BEZEL_OVERLAP;
WIN_Y_MAX =  MOSAICO_H/2 - BEZEL_OVERLAP;

SW_ACT_Z   = BOARD_Z_FRONT + SW_H;      // 开关柱头顶面 Z = +1.70
FRAME_Y0   = MOSAICO_H/2;               // 压面
FRAME_Y1   = FRAME_Y0 + FRAME_H;

BIG = 400;   // 用于布尔运算的大盒子

/* ---------- 一次编译即可暴露的硬性几何检查 ---------- */
assert(DOCK_X_TOL < DOCK_PITCH/2,
       "ICD 3.3 一级防呆：DOCK_X_TOL 必须小于半个列距，否则 X 错位可达 2 列");
assert(DOCK_Z_TOL < DOCK_PITCH/2,
       "ICD 3.3 一级防呆：DOCK_Z_TOL 必须小于半个行距");
assert(DOCK_PIN_FIELD_Y < -MOSAICO_H/2,
       "ICD ME-D-07：配合面必须低于 Mosaico −Y 面");
assert(DOCK_PIN_FIELD_X0 + DOCK_FIELD_W < 0,
       "ICD 3.3：弹簧针场必须整体偏置在 −X 侧");
assert(BAY_X_MIN + BAY_X_MAX < -MODULE_STACK_X/2,
       "落入槽必须在 X 上非对称，绕 Y 轴 180 度错放时模块板撞 +X 壁而进不去");
assert(BATT_X_MAX + BATT_CLR < NATIVE_USB_X - NATIVE_USB_W/2 - WALL,
       "电池仓必须给原生 USB-C 直通道让位");
assert(GRIP_Y_BOT > Y_BOT_OUT, "握把下缘必须在机身底面之上");
assert(BOARD_Z_BACK > Z_BACK_CORE + WALL, "主板必须落在机身内腔内");

echo(str("整机外形 W x H x T = ", W_TOTAL, " x ", H_TOTAL, " x ", T_GRIP_MAX, " mm"));
echo(str("落入槽内腔 X = [", BAY_X_MIN, ", ", BAY_X_MAX, "]  Y_floor = ", BAY_Y_FLOOR));
echo(str("弹簧针场：列 1 X = ", DOCK_PIN_FIELD_X0, "  列 8 X = ", DOCK_PIN_FIELD_X0 + DOCK_FIELD_W,
         "  行 A/B Z = ", DOCK_PIN_FIELD_Z0, " / ", -DOCK_PIN_FIELD_Z0,
         "  配合面 Y = ", DOCK_PIN_FIELD_Y));
echo(str("弹簧针小板上表面 Y = ", POGO_PCB_Y_TOP, "  主板正面 Z = ", BOARD_Z_FRONT));
echo(str("电池仓 X = [", BATT_X_MIN, ", ", BATT_X_MAX, "]  Y = [", BATT_Y_BOT, ", ", BATT_Y_TOP,
         "]  Z = [", BATT_Z_MIN, ", ", BATT_Z_MAX, "]"));

/* =====================================================================
   基本体：机身外形
   核心板与握把都用「球的 hull」构成，因此「把每个球的半径减 inset」
   就等于整体向内偏移 inset —— 用同一个模块生成外形与内腔，壁厚处处一致。
   ===================================================================== */

function grip_pt(s, i) =
  let(
    xin  = s*(GRIP_X_IN  + GRIP_R),
    xout = s*(GRIP_X_OUT - GRIP_R),
    ytop = GRIP_Y_TOP - GRIP_R,
    ybot = GRIP_Y_BOT + GRIP_R,
    rake = s*GRIP_RAKE_X,
    ztop = Z_BACK_CORE - GRIP_DEPTH_TOP + GRIP_R,
    zbot = Z_BACK_CORE - GRIP_DEPTH_BOT + GRIP_R
  )
  i == 0 ? [xin,         ytop, ztop] :
  i == 1 ? [xout,        ytop, ztop] :
  i == 2 ? [xout - rake, ybot, zbot] :
           [xin  - rake, ybot, zbot];

// 机身核心板：8 个角球的 hull
module core_solid(inset = 0) {
  hull()
    for (sx = [-1, 1])
      for (py = [Y_TOP_OUT - R_CORNER, Y_BOT_OUT + R_CORNER])
        for (pz = [Z_FRONT_OUT - R_CORNER, Z_BACK_CORE + R_CORNER])
          translate([sx*(W_TOTAL/2 - R_CORNER), py, pz])
            sphere(r = R_CORNER - inset, $fn = FN_R);
}

// 单侧握把凸出：4 个平面点 x（前层、后层）
module grip_solid(s, inset = 0) {
  hull()
    for (i = [0 : 3])
      let(p = grip_pt(s, i)) {
        translate([p[0], p[1], Z_FRONT_OUT - GRIP_R])
          sphere(r = GRIP_R - inset, $fn = FN_R);
        translate([p[0], p[1], p[2]])
          sphere(r = GRIP_R - inset, $fn = FN_R);
      }
}

module body_solid(inset = 0) {
  union() {
    core_solid(inset);
    grip_solid(-1, inset);
    grip_solid( 1, inset);
  }
}

// 纯壳（外形减内腔）
module shell_only() {
  difference() {
    body_solid(0);
    body_solid(WALL);
  }
}

/* =====================================================================
   中央落入槽（Mosaico ＋ 常驻模块板）
   ===================================================================== */

// 槽内腔：顶部开口（向上穿出机身），前面开屏窗，其余由槽壁包住
module bay_cavity(extra = 0) {
  translate([BAY_X_MIN - extra, BAY_Y_FLOOR - extra, BAY_Z_MIN - extra])
    cube([BAY_X_MAX - BAY_X_MIN + 2*extra,
          (Y_TOP_OUT + BIG/4) - BAY_Y_FLOOR + 2*extra,
          BAY_Z_MAX - BAY_Z_MIN + 2*extra]);
}

// 槽壁实体（再由 cutouts 减去内腔）；与机身内腔求交，不外溢
module bay_walls() {
  intersection() {
    body_solid(0);
    difference() {
      translate([BAY_X_MIN - BAY_WALL, BAY_Y_FLOOR - BAY_WALL, BAY_Z_MIN - BAY_WALL])
        cube([BAY_X_MAX - BAY_X_MIN + 2*BAY_WALL,
              (Y_TOP_OUT + 1) - BAY_Y_FLOOR + BAY_WALL,
              BAY_Z_MAX - BAY_Z_MIN + 2*BAY_WALL]);
      // 内腔在 cutouts() 里统一减，这里只挖出让弹簧针小板与触点板通过的地板缺口
      translate([DOCK_FIELD_XC - CONTACT_PCB_W/2 - 1,
                 BAY_Y_FLOOR - BAY_WALL - 1,
                 -CONTACT_PCB_D/2 - 1])
        cube([CONTACT_PCB_W + 2, BAY_WALL + 2, CONTACT_PCB_D + 2]);
    }
  }
}

// 落入槽的机械防呆与硬限位：
//  一级 A —— 槽在 X 上非对称（−X 侧多出 MODULE_STACK_X），绕 Y 轴 180 度时模块板撞 +X 壁；
//  一级 B —— +X 壁上一道限位筋，使「无模块板的裸机」也只能按唯一朝向坐到底；
//  一级 C —— 四角硬限位柱决定配合面高度，弹簧针只被压到工作行程，不被压到底。
module bay_keying_and_stops() {
  intersection() {
    body_solid(0);
    union() {
      // 一级 B：+X 壁限位筋（Mosaico 侧面无特征，仅作二次保险与减晃）
      translate([BAY_X_MAX - 1.2, BAY_Y_FLOOR + 6, -1.5])
        cube([1.2, MOSAICO_H - 12, 3.0]);
      // 一级 C：四角硬限位柱（高度 = 配合面）
      for (sx = [-1, 1])
        for (sz = [-1, 1])
          translate([sx > 0 ? BAY_X_MAX - 4.5 : BAY_X_MIN + 1.0,
                     BAY_Y_FLOOR,
                     sz * (BAY_Z_MAX - 2.4)])
            cube([3.5, STOP_POST_H, 2.4], center = false);
    }
  }
}

/* =====================================================================
   内部结构：主板、电池仓、螺柱
   ===================================================================== */

// 主板支撑台（正面贴合 BOARD_Z_FRONT，背面留空给电池与走线）
module board_rails() {
  intersection() {
    body_solid(WALL);
    union() {
      for (s = [-1, 1])
        for (p = [[s*70, 20], [s*70, -45], [s*36, -52]])
          translate([p[0], p[1], BOARD_Z_BACK - 3.0])
            cylinder(d = BOSS_OD, h = 3.0, $fn = 24);
      // 下缘长支撑筋（USB-C 受力）
      translate([-60, BATT_Y_BOT - 1.5, BOARD_Z_BACK - 2.5])
        cube([120, 2.0, 2.5]);
    }
  }
}

module battery_bay_walls() {
  intersection() {
    body_solid(WALL);
    difference() {
      translate([BATT_X_MIN - BATT_CLR - 1.5, BATT_Y_BOT - BATT_CLR - 1.5, BATT_Z_MIN - 1.5])
        cube([BATT_W + 2*BATT_CLR + 3.0, BATT_H + 2*BATT_CLR + 3.0, BATT_T + 3.0]);
      translate([BATT_X_MIN - BATT_CLR, BATT_Y_BOT - BATT_CLR, BATT_Z_MIN - BIG/8])
        cube([BATT_W + 2*BATT_CLR, BATT_H + 2*BATT_CLR, BATT_T + BIG/8]);
    }
  }
}

// 前后壳螺柱：前壳出柱（带底孔），后壳出沉孔
// 八个螺柱位：四角 ＋ 槽壁外侧上下各两个。
// 约束：不得落进电池仓（X [BATT_X_MIN, BATT_X_MAX]、Y [BATT_Y_BOT, BATT_Y_TOP]）
// 也不得落进原生 USB-C 直通道（X 附近 NATIVE_USB_X）。
function boss_pts() = [
  [-W_TOTAL/2 + 10,  Y_TOP_OUT  -  9],
  [ W_TOTAL/2 - 10,  Y_TOP_OUT  -  9],
  [-W_TOTAL/2 + 10,  Y_BOT_OUT  + 11],
  [ W_TOTAL/2 - 10,  Y_BOT_OUT  + 11],
  [-GRIP_X_IN - 2,   Y_TOP_OUT  -  9],
  [ GRIP_X_IN + 2,   Y_TOP_OUT  -  9],
  [-GRIP_X_IN - 2,   BATT_Y_TOP +  4],
  [ GRIP_X_IN + 2,   BATT_Y_TOP +  4]
];

module screw_bosses() {
  intersection() {
    body_solid(WALL);
    for (p = boss_pts())
      translate([p[0], p[1], Z_SPLIT])
        cylinder(d = BOSS_OD, h = Z_FRONT_OUT - Z_SPLIT, $fn = 28);
  }
}

module screw_holes() {
  for (p = boss_pts()) {
    // 前壳侧自攻底孔
    translate([p[0], p[1], Z_SPLIT - 0.01])
      cylinder(d = BOSS_ID, h = Z_FRONT_OUT - Z_SPLIT, $fn = 20);
    // 后壳侧过孔 ＋ 沉头
    translate([p[0], p[1], Z_BACK_CORE - GRIP_DEPTH_BOT - 1])
      cylinder(d = SCREW_CLR_D, h = (Z_SPLIT + 0.01) - (Z_BACK_CORE - GRIP_DEPTH_BOT - 1), $fn = 20);
    translate([p[0], p[1], Z_BACK_CORE - GRIP_DEPTH_BOT - 1])
      cylinder(d1 = SCREW_CLR_D + 2.6, d2 = SCREW_CLR_D, h = 1.6, $fn = 20);
  }
}

/* =====================================================================
   键帽导向与开孔
   ===================================================================== */

module cross_2d(len, w, r = 2.0) {
  offset(r = r) offset(delta = -r)
    union() {
      square([2*len, w], center = true);
      square([w, 2*len], center = true);
    }
}

module bar_2d(w, h, r = 2.0) {
  offset(r = r) offset(delta = -r) square([w, h], center = true);
}

// 通用：前面板开孔（帽体穿出）＋ 法兰兜（帽子不会掉出）
module cap_opening(margin_open, margin_flange, hgt_flange) {
  // 穿出孔：贯穿前壁
  translate([0, 0, Z_FRONT_OUT - WALL - 0.01])
    linear_extrude(height = WALL + 1.0) offset(r = margin_open) children(0);
  // 法兰兜：在前壁内侧
  translate([0, 0, Z_FRONT_OUT - WALL - hgt_flange])
    linear_extrude(height = hgt_flange + 0.02) offset(r = margin_flange) children(0);
}

// 导向套：法兰兜外围的一圈料，兼作行程限位与防转
module cap_guide(margin_flange, hgt_flange, wall_g, z_lo) {
  difference() {
    translate([0, 0, z_lo])
      linear_extrude(height = Z_FRONT_OUT - WALL - z_lo)
        offset(r = margin_flange + wall_g) children(0);
    translate([0, 0, z_lo - 0.5])
      linear_extrude(height = Z_FRONT_OUT - WALL - z_lo - hgt_flange + 0.5)
        offset(r = margin_flange - 1.0) children(0);
    translate([0, 0, Z_FRONT_OUT - WALL - hgt_flange])
      linear_extrude(height = hgt_flange + 1.0)
        offset(r = margin_flange) children(0);
  }
}

module buttons_guides() {
  intersection() {
    body_solid(WALL);
    union() {
      translate([DPAD_X, DPAD_Y, 0])
        cap_guide(CLR_PRINT + CAP_FLANGE_MARGIN, CAP_POCKET_T, CAP_GUIDE_WALL, BOARD_Z_FRONT + 1.0)
          cross_2d(DPAD_ARM_L, DPAD_ARM_W);
      for (a = [0 : 3])
        translate([ABXY_X + ABXY_R*cos(90*a), ABXY_Y + ABXY_R*sin(90*a), 0])
          cap_guide(CLR_PRINT + CAP_FLANGE_MARGIN, CAP_POCKET_T, CAP_GUIDE_WALL, BOARD_Z_FRONT + 1.0)
            circle(d = ABXY_D, $fn = 40);
      for (s = [-1, 1])
        translate([s*LR_X, LR_Y, 0])
          cap_guide(CLR_PRINT + CAP_FLANGE_MARGIN, CAP_POCKET_T, CAP_GUIDE_WALL, BOARD_Z_FRONT + 1.0)
            bar_2d(LR_BAR_W, LR_BAR_H);
    }
  }
}

module buttons_openings() {
  translate([DPAD_X, DPAD_Y, 0])
    cap_opening(CLR_PRINT, CLR_PRINT + CAP_FLANGE_MARGIN, CAP_POCKET_T) cross_2d(DPAD_ARM_L, DPAD_ARM_W);
  for (a = [0 : 3])
    translate([ABXY_X + ABXY_R*cos(90*a), ABXY_Y + ABXY_R*sin(90*a), 0])
      cap_opening(CLR_PRINT, CLR_PRINT + CAP_FLANGE_MARGIN, CAP_POCKET_T) circle(d = ABXY_D, $fn = 40);
  for (s = [-1, 1])
    translate([s*LR_X, LR_Y, 0])
      cap_opening(CLR_PRINT, CLR_PRINT + CAP_FLANGE_MARGIN, CAP_POCKET_T) bar_2d(LR_BAR_W, LR_BAR_H);
}

/* =====================================================================
   原生 USB-C 直通道（朝下）与底座 USB-C、声学栅格
   ===================================================================== */

module native_usb_duct() {
  intersection() {
    body_solid(0);
    difference() {
      translate([NATIVE_USB_X - NATIVE_USB_W/2 - 1.6, Y_BOT_OUT - 1, -NATIVE_USB_D/2 - 1.6])
        cube([NATIVE_USB_W + 3.2, BAY_Y_FLOOR - Y_BOT_OUT + 1, NATIVE_USB_D + 3.2]);
      native_usb_bore();
    }
  }
}

module native_usb_bore() {
  translate([NATIVE_USB_X - NATIVE_USB_W/2, Y_BOT_OUT - 2, -NATIVE_USB_D/2])
    cube([NATIVE_USB_W, BAY_Y_FLOOR - Y_BOT_OUT + 4, NATIVE_USB_D]);
}

module dock_usb_opening() {
  translate([DOCK_USB_X - DOCK_USB_W/2,
             Y_BOT_OUT - 2,
             BOARD_Z_FRONT + 0.2 - DOCK_USB_H/2])
    cube([DOCK_USB_W, WALL + 4, DOCK_USB_H]);
}

// 声学/散热栅格：落入槽背壁与后壳对位打通（AS-25 位置未知 → 覆盖整个背面）
module acoustic_grille() {
  nx = floor((BAY_X_MAX - BAY_X_MIN - 8) / GRILLE_PITCH);
  ny = floor((MOSAICO_H - 8) / GRILLE_PITCH);
  for (i = [0 : nx - 1])
    for (j = [0 : ny - 1])
      translate([BAY_X_MIN + 4 + GRILLE_D/2 + i*GRILLE_PITCH,
                 -MOSAICO_H/2 + 4 + GRILLE_D/2 + j*GRILLE_PITCH,
                 Z_BACK_CORE - GRIP_DEPTH_BOT - 2])
        cylinder(d = GRILLE_D, h = (BAY_Z_MIN + 1) - (Z_BACK_CORE - GRIP_DEPTH_BOT - 2), $fn = 16);
}

/* =====================================================================
   上压框（第三件）：两侧舌片落入槽壁的竖槽，正面一个弹性卡扣 ＋ 指扣
   ===================================================================== */

module frame_slots() {
  for (s = [-1, 1])
    translate([s > 0 ? BAY_X_MAX : BAY_X_MIN - FRAME_TONGUE_L - CLR_PRINT,
               FRAME_Y0 - CLR_PRINT,
               -FRAME_TONGUE_H/2 - CLR_PRINT])
      cube([FRAME_TONGUE_L + CLR_PRINT, (Y_TOP_OUT + 2) - FRAME_Y0, FRAME_TONGUE_H + 2*CLR_PRINT]);
}

module top_frame() {
  difference() {
    union() {
      // 压框主体
      translate([BAY_X_MIN + CLR_PRINT, FRAME_Y0 + FRAME_PAD_T, BAY_Z_MIN + CLR_PRINT])
        cube([BAY_X_MAX - BAY_X_MIN - 2*CLR_PRINT,
              FRAME_H - FRAME_PAD_T,
              Z_FRONT_OUT - BAY_Z_MIN - 2*CLR_PRINT]);
      // 压脚（两条，落在 Mosaico +Y 面的两端，中间留空给顶部特征，AS-25）
      for (s = [-1, 1])
        translate([s > 0 ? BAY_X_MAX - 12 - CLR_PRINT : BAY_X_MIN + CLR_PRINT,
                   FRAME_Y0, -MOSAICO_T/2 + 1.0])
          cube([12, FRAME_PAD_T, MOSAICO_T - 2.0]);
      // 两侧舌片
      for (s = [-1, 1])
        translate([s > 0 ? BAY_X_MAX - CLR_PRINT : BAY_X_MIN - FRAME_TONGUE_L,
                   FRAME_Y0 + 1.0, -FRAME_TONGUE_H/2])
          cube([FRAME_TONGUE_L + CLR_PRINT, FRAME_H - 2.0, FRAME_TONGUE_H]);
    }
    // 指扣凹
    translate([-9, FRAME_Y1 - 3.5, Z_FRONT_OUT - 1.4])
      cube([18, 4.0, 2.0]);
    // 系绳孔（防丢）
    translate([BAY_X_MAX - 6, FRAME_Y1 - 4.5, Z_FRONT_OUT - 6])
      rotate([0, 0, 0]) cylinder(d = 2.4, h = 8, $fn = 20);
  }
}

/* =====================================================================
   整机（未分件）
   ===================================================================== */

module cutouts() {
  union() {
    bay_cavity(0);                                   // 中央落入槽内腔
    // 屏窗（前面板）
    translate([WIN_X_MIN, WIN_Y_MIN, BAY_Z_MAX - 0.01])
      cube([WIN_X_MAX - WIN_X_MIN, WIN_Y_MAX - WIN_Y_MIN, Z_FRONT_OUT - BAY_Z_MAX + 1.0]);
    // 电池仓
    translate([BATT_X_MIN - BATT_CLR, BATT_Y_BOT - BATT_CLR, BATT_Z_MIN])
      cube([BATT_W + 2*BATT_CLR, BATT_H + 2*BATT_CLR, BATT_T]);
    buttons_openings();
    native_usb_bore();
    dock_usb_opening();
    acoustic_grille();
    frame_slots();
    screw_holes();
  }
}

module handheld_all() {
  difference() {
    union() {
      shell_only();
      bay_walls();
      bay_keying_and_stops();
      board_rails();
      battery_bay_walls();
      screw_bosses();
      buttons_guides();
      native_usb_duct();
    }
    cutouts();
  }
}

/* ---------- 分型：前壳（上壳，+Z）／后壳（下壳，−Z）---------- */

module half_space_front() {
  translate([-BIG/2, -BIG/2, Z_SPLIT]) cube([BIG, BIG, BIG]);
}
module half_space_back() {
  translate([-BIG/2, -BIG/2, Z_SPLIT - BIG]) cube([BIG, BIG, BIG]);
}

// 搭接唇：前壳向后伸出一圈，落进后壳内侧
module lap_lip(inset_extra = 0, hgt = 1.8) {
  intersection() {
    difference() {
      body_solid(WALL + inset_extra);
      body_solid(WALL + 1.2 + inset_extra);
    }
    translate([-BIG/2, -BIG/2, Z_SPLIT - hgt]) cube([BIG, BIG, hgt]);
  }
}

module upper_shell() {
  union() {
    intersection() { handheld_all(); half_space_front(); }
    difference() { lap_lip(0, 1.8); cutouts(); }
  }
}

module lower_shell() {
  difference() {
    intersection() { handheld_all(); half_space_back(); }
    lap_lip(-CLR_PRINT, 1.9);
  }
}

/* ---------- T17 体量模型：只留体块，不打精细特征 ---------- */
module mockup_solid() {
  difference() {
    body_solid(0);
    bay_cavity(0);
  }
}

/* =====================================================================
   底座主板外形与元件锚点 —— 由外壳几何**导出**，不是另写一份
   ---------------------------------------------------------------------
   2026-09-21 增加。此前主板只有网表没有外形，外壳这边只定义了板厚与板面 Z，
   两边谁也不知道板的 XY 长什么样；那样先做外壳，板一画出来必然要回头改外壳。
   这里把因果理顺：**板外形 = 外壳内腔在板中面的截面 − 装配间隙 − 落入槽投影**，
   元件锚点直接取外壳里已有的按键／接口坐标。外壳改一次，板框和锚点自动跟着变，
   不存在「两份数各自漂移」的可能。PCB 那边只消费 DXF 与本文件 echo 出的锚点表。
   ===================================================================== */

BOARD_Z_MID = BOARD_Z_FRONT - BOARD_T / 2;      // 主板中面 Z

// ASSUMPTION: AS-31-mechdock-22 板四周留 BOARD_EDGE_CLR = 0.40 mm 装配间隙；
//   落入槽外壁与板之间另留 0.60 mm，避免槽壁根部圆角压到板边。
//   验证：首版壳与板到手后实测板能否无干涉落位。
BAY_BOARD_CLR = 0.60;

// ASSUMPTION: AS-31-mechdock-23 主板固定用 4 个 Ø2.2 螺钉孔，位于四角内侧 6 mm，
//   对应下壳的空心柱。禁布圆 Ø5.0。
BOARD_MOUNT_D       = 2.20;
BOARD_MOUNT_KEEPOUT = 5.00;
BOARD_MOUNT_INSET   = 6.00;

// 板外形（2D，XY 平面）
module board_outline_2d() {
  difference() {
    // 内腔在板中面的截面，再内缩装配间隙
    offset(r = -BOARD_EDGE_CLR)
      projection(cut = true)
        translate([0, 0, -BOARD_Z_MID]) body_solid(WALL);

    // 落入槽在同一平面的投影（含槽壁），外扩后挖掉——Mosaico 与模块板从这里穿过
    offset(r = BAY_BOARD_CLR)
      projection(cut = true)
        translate([0, 0, -BOARD_Z_MID]) bay_cavity(BAY_WALL);

    // 上缘截平到 BOARD_TOP_Y（再往上是上压框与落入口，没有放板的空间）
    translate([0, BOARD_TOP_Y + BIG / 2, 0]) square([BIG, BIG], center = true);
  }
}

// 四个固定孔的中心（从板外形的包络角内缩取，写死为参数便于 PCB 直接用）
BOARD_MH = [
  [-(W_TOTAL / 2 - WALL - BOARD_EDGE_CLR - BOARD_MOUNT_INSET),  BOARD_TOP_Y - BOARD_MOUNT_INSET],
  [ (W_TOTAL / 2 - WALL - BOARD_EDGE_CLR - BOARD_MOUNT_INSET),  BOARD_TOP_Y - BOARD_MOUNT_INSET],
  [-(W_TOTAL / 2 - WALL - BOARD_EDGE_CLR - BOARD_MOUNT_INSET),  Y_BOT_OUT + WALL + BOARD_EDGE_CLR + BOARD_MOUNT_INSET],
  [ (W_TOTAL / 2 - WALL - BOARD_EDGE_CLR - BOARD_MOUNT_INSET),  Y_BOT_OUT + WALL + BOARD_EDGE_CLR + BOARD_MOUNT_INSET],
];

module board_2d() {
  difference() {
    board_outline_2d();
    for (m = BOARD_MH) translate(m) circle(d = BOARD_MOUNT_D, $fn = 32);
  }
}

// D-pad 四个开关中心（上右下左）
function dpad_sw(i) = [DPAD_X + DPAD_SW_R * cos(i * 90 + 90),
                       DPAD_Y + DPAD_SW_R * sin(i * 90 + 90)];
// ABXY 四个开关中心（上右下左 = X A B Y 的菱形，命名由 mech-dock 定）
function abxy_sw(i) = [ABXY_X + ABXY_R * cos(i * 90 + 90),
                       ABXY_Y + ABXY_R * sin(i * 90 + 90)];

module board_anchors_echo() {
  echo("==== 底座主板锚点（由 dock_shell.scad 导出，PCB 直接用）====");
  echo(str("板中面 Z = ", BOARD_Z_MID, "  板厚 = ", BOARD_T,
           "  元件面 Z = ", BOARD_Z_FRONT, "  焊接面 Z = ", BOARD_Z_BACK));
  echo(str("板上缘 Y = ", BOARD_TOP_Y, "  板下缘 Y ≈ ", Y_BOT_OUT + WALL + BOARD_EDGE_CLR,
           "  板最大宽 X ≈ ±", W_TOTAL / 2 - WALL - BOARD_EDGE_CLR));
  echo(str("落入槽开窗（板上必须让开）X [", BAY_X_MIN - BAY_WALL - BAY_BOARD_CLR,
           " , ", BAY_X_MAX + BAY_WALL + BAY_BOARD_CLR,
           "]  上至板上缘，下至 Y = ", BAY_Y_FLOOR - BAY_WALL - BAY_BOARD_CLR));
  echo(str("固定孔 Ø", BOARD_MOUNT_D, " x4，中心 = ", BOARD_MH,
           "，禁布圆 Ø", BOARD_MOUNT_KEEPOUT));
  echo(str("D-pad 开关中心（上/右/下/左）= ",
           [for (i = [0 : 3]) dpad_sw(i)], "  开关体 ", SW_SIZE, " 见方"));
  echo(str("ABXY 开关中心（上/右/下/左）= ",
           [for (i = [0 : 3]) abxy_sw(i)]));
  echo(str("L/R 开关中心 = ", [[-LR_X, LR_SW_Y], [LR_X, LR_SW_Y]],
           "  （键条中心 Y = ", LR_Y, "，开关下移 ", LR_SW_OFFSET_Y,
           " mm 以避开板上缘）按压方向 −Z"));
  echo(str("弹簧针小板：X 中心 = ", DOCK_FIELD_XC, "  宽 ", DOCK_FIELD_W,
           "  以 90 度半孔焊在板**元件面**，小板上表面 Y = ", POGO_PCB_Y_TOP));
  echo(str("底座 USB-C：X = ", DOCK_USB_X, "  位于板下缘，朝 −Y"));
  echo(str("电池仓（板背面，不穿板）X [", BATT_X_MIN, " , ", BATT_X_MAX,
           "]  Y [", BATT_Y_BOT, " , ", BATT_Y_TOP, "]  Z [", BATT_Z_MIN, " , ", BATT_Z_MAX, "]"));
  echo("元件面朝 +Z（朝屏幕一侧）；开关、弹簧针小板在元件面，电池在背面。");
}

/* ---------- 顶层分发 ---------- */
if (PART == "assembly") {
  color("Gainsboro") upper_shell();
  color("DimGray")   lower_shell();
  color("SteelBlue") top_frame();
} else if (PART == "upper") {
  upper_shell();
} else if (PART == "lower") {
  lower_shell();
} else if (PART == "frame") {
  top_frame();
} else if (PART == "mockup_upper") {
  intersection() { mockup_solid(); half_space_front(); }
} else if (PART == "mockup_lower") {
  intersection() { mockup_solid(); half_space_back(); }
} else if (PART == "section") {
  difference() {
    union() {
      color("Gainsboro") upper_shell();
      color("DimGray")   lower_shell();
      color("SteelBlue") top_frame();
    }
    translate([-BIG/2, -BIG/2, -BIG/2]) cube([BIG/2, BIG, BIG]);
  }
} else if (PART == "board_2d") {
  board_2d();
  board_anchors_echo();
} else if (PART == "board_dxf") {
  // openscad -o dock_board_outline.dxf -D 'PART="board_dxf"' dock_shell.scad
  board_2d();
  board_anchors_echo();
} else if (PART == "none") {
  // keycaps.scad 用 include <dock_shell.scad> 借参数时覆盖为 "none"，不渲染外壳
} else {
  assert(false, "PART 取值须为 assembly/upper/lower/frame/mockup_upper/mockup_lower/section/board_2d/board_dxf/none");
}

// ====================================================================
// ICD 契约输出 —— 供 hardware/check_cross_branch.py 自动比对
// ====================================================================
// 2026-09-21 增加，与 module_shell.scad 的同名段配对。
// 起因：双路清点在四个设计分支之间查出 40 条不一致、22 条阻断，而每个分支自己的
// 自检**全部通过**——自检只查本文件内部自洽，从来没有任何东西比对过两个分支。
//
// 键名必须与模块侧一致（按**物理含义**对齐，不按变量名）。
// 语义分两类：
//   · 同名等值类（MOSAICO_*、DOCK_PIN_FIELD_* 等）——两边必须相等；
//   · 需求/供给类——模块侧吐 MODULE_ENV_*（我需要多大空间），
//     底座侧吐 BAY_*（我提供多大空间），由脚本做包含判定。
module icd_contract() {
  echo(str("ICD-CONTRACT|MOSAICO_W|", MOSAICO_W));
  echo(str("ICD-CONTRACT|MOSAICO_H|", MOSAICO_H));
  echo(str("ICD-CONTRACT|MOSAICO_T|", MOSAICO_T));
  echo(str("ICD-CONTRACT|DOCK_PIN_FIELD_X0|", DOCK_PIN_FIELD_X0));
  echo(str("ICD-CONTRACT|DOCK_PIN_FIELD_Z0|", DOCK_PIN_FIELD_Z0));
  echo(str("ICD-CONTRACT|DOCK_PIN_FIELD_Y|",  DOCK_PIN_FIELD_Y));
  echo(str("ICD-CONTRACT|DOCK_PITCH|", DOCK_PITCH));
  echo(str("ICD-CONTRACT|DOCK_COLS|",  DOCK_COLS));
  echo(str("ICD-CONTRACT|DOCK_ROWS|",  DOCK_ROWS));
  echo(str("ICD-CONTRACT|DOCK_X_TOL|", DOCK_X_TOL));
  echo(str("ICD-CONTRACT|DOCK_Z_TOL|", DOCK_Z_TOL));
  // 名义工作压缩 = 自由高 − 工作高（底座侧不直接给 TRAVEL，这里派生，便于与模块侧比）
  echo(str("ICD-CONTRACT|DOCK_PIN_TRAVEL|", POGO_FREE_H - POGO_WORK_H));
  // 单针压力：原先只写在 AS-31-mechdock-20 的注释里（16 × 0.9 ≈ 14.4 N），
  // 注释不参与任何校验，正是它与模块侧 0.6 N 分歧半天没被发现的原因。提升为变量。
  echo(str("ICD-CONTRACT|DOCK_PIN_FORCE_N|", POGO_FORCE_N));
  echo(str("ICD-CONTRACT|CONTACT_PCB_X|", CONTACT_PCB_W));
  echo(str("ICD-CONTRACT|CONTACT_PCB_Z|", CONTACT_PCB_D));
  // 落入槽提供给模块总成的净空间（模块侧的 MODULE_ENV_* 必须落在其内）
  echo(str("ICD-CONTRACT|BAY_X_LO|", BAY_X_MIN));
  echo(str("ICD-CONTRACT|BAY_X_HI|", BAY_X_MAX));
  echo(str("ICD-CONTRACT|BAY_Y_LO|", BAY_Y_FLOOR));
  echo(str("ICD-CONTRACT|BAY_Y_HI|", FRAME_Y0));
  echo(str("ICD-CONTRACT|BAY_Z_LO|", BAY_Z_MIN));
  echo(str("ICD-CONTRACT|BAY_Z_HI|", BAY_Z_MAX));
  // 四角硬限位柱顶面（配合面的物理落实）
  echo(str("ICD-CONTRACT|HARD_STOP_Y|", BAY_Y_FLOOR + STOP_POST_H));
  // 底座当前**没有任何卡扣**，保持力靠可拆上压框且未给数值。如实吐 0，
  // 让脚本把「模块侧要求 30 N、底座侧供给 0」报出来，而不是靠人读文档发现。
  echo(str("ICD-CONTRACT|RETENTION_N|", RETENTION_PROVIDED_N));
}
icd_contract();
