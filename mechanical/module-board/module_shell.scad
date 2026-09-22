// 提案 · 未冻结 · 由 Claude 主控（claude-opus-5）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
//
// module_shell.scad —— 模块板保护壳体（可 3D 打印）
// 分支 claude/design-d/mech-module ／ 目录 mechanical/module-board/
//
// 作用（四项，缺一不可）：
//   ① 保护 J1 直插公头与槽板走线；② 提供落入底座的导向面与定位基准；
//   ③ 提供承力闭环所需的硬限位足（见 MATING.md 第 4 节）；
//   ④ 领口夹持 Mosaico −X 区，使 H2 成为非定位、非承力的纯电气界面。
//
// ====================================================================
// 2026-09-22 修订 c —— 随 module_board.scad 的「右角 → 直插」一起重做。三处架构变化：
//
//   (a) **分型面由 Z 改为 X。** 槽板现在立在 YZ 面（板面法向 ±X），穿过槽板定位孔的
//       螺钉必须沿 X 走；沿 Z 的螺钉会走在槽板板面内，根本穿不过去。
//       SPLIT_X = FIN_MID_X，前半（+X，含领口）与后半（−X，含防呆键块）对合。
//       触点板横跨分型面，装配时像抽屉一样从前半的 −X 开口滑入。
//
//   (b) **取消两个 Ø3.20 定位销孔。** 触点板 Z 向宽 10.80，足部 Z 向净空 13.60（由落入槽
//       给定），两侧各只剩 1.20 mm 料；一个 Ø3.2 盲孔配 SHELL_MIN_W = 1.2 的壁需要
//       3.2 + 2 × 1.2 = 5.6 mm，**两侧都放不下**；X 两端同样放不下（足部比触点板长 1.2）。
//       改为：足部整体滑配进落入槽的模块条带（单边 CLR_MOD = 0.15，由底座侧给出）
//       ＋ 底缘 45° 引入倒角 ＋ 防呆键块。定位公差链见 module_board.scad AS-31-mm-6。
//       **这是本次修订最弱的一环，如实标注**：最坏 0.15 + 2 × PRINT_TOL = 0.45，
//       正好等于 DOCK_X_TOL 目标值，没有余量；RSS 0.26 有余量。MATING 第 6 节 c/f 两环须重算。
//
//   (c) **取消领口前/后唇，取消承力卡扣槽。**
//       前唇：模块壳 +Z 外表面若要包住 Mosaico 前面，需到 Z = 5.74 + 0.5 + 1.2 = 7.44，
//       而底座落入槽 +Z 只有 6.09、机身前外表面才 7.74 —— 前唇物理上无处容身。
//       故壳体 +Z 外表面取与 Mosaico 前面齐平（Z = MOSAICO_T/2），只保留上/下唇夹持 ±Y。
//       Mosaico 的 ±Z 由底座自己的屏窗压边与落入槽背壁约束，不需要模块壳再管。
//       承力卡扣：方案 J 第 5 节已把 15 N 预压由卡扣改为上压框 M2 螺钉，卡扣取消。
// ====================================================================
//
// 与 module_board.scad 的关系：本文件**不重复定义**板级尺寸，全部 include 进来。

include <module_board.scad>;

// include 会执行被包含文件的顶层语句。把 MODE 置为 "none"，使 module_board.scad
// 的输出分支不产生任何几何。**不要删除这一行**。
MODE = "none";


// ====================================================================
// ASSUMPTION 块 —— 壳体自身的尺寸假设（板级尺寸见 module_board.scad 顶部）
// ====================================================================

// ASSUMPTION: AS-31-mm-20 领口贴合面内衬 0.5 mm 闭孔泡棉／TPU（邵氏 A40–60）。
LINER = 0.5;

// ASSUMPTION: AS-31-mm-21 壁厚 2.0 mm、最小特征壁 1.2 mm，适配 0.4 mm 喷嘴 × 0.2 mm 层高。
SHELL_WALL   = 2.0;
SHELL_MIN_W  = 1.2;

// ASSUMPTION: AS-31-mm-18 3D 打印件孔位与高度公差 ±0.15 mm。
PRINT_TOL = 0.15;

// 装配间隙（打印件对 PCB）
CLR_FIN_X  = 0.15;   // 鳍板槽对槽板**厚度**方向单边间隙（现在是 X）
CLR_FIN_YZ = 0.20;   // 鳍板槽对槽板**轮廓**方向单边间隙（现在是 Y、Z）
CLR_PAD    = 0.05;   // 触点板槽单边间隙（MATING.md 第 6 节 e 环，刻意做紧）
CLR_J1     = 0.50;   // J1 胶芯让位
CLR_TAIL   = 0.30;   // J1 针尾焊点让位腔的单边余量

// ASSUMPTION: AS-31-mm-22 领口唇伸出量：上 3.0、下 3.0 mm；唇厚 1.2 mm。
//   修订 c：前唇、后唇取消（理由见文件头 (c)）。
COLLAR_LIP_TOP    = 3.0;
COLLAR_LIP_BOTTOM = 3.0;
COLLAR_LIP_T      = 1.2;
// 修订 d：上唇顶面比壳体顶面（承力压面）低这么多，使上压框的承力压面**只**落在
//   鳍板段顶面（X ≤ SEAT_X），绝不压到骑在 Mosaico 上方的领口上唇。
//   原值 0（两者齐平）时，求交实测压框在 X ∈ [−23.095, −19.595] 这 3.5 mm 上
//   压的是上唇，而上唇下方隔 LINER 0.5 就是 Mosaico +Y 面 —— 9.6 N 会灌进 Mosaico，
//   违反方案 J 不变量 ②。
COLLAR_TOP_DROP   = 0.30;
// 修订 d：领口沿 X 的真实导向长度是派生量，不是拍的 8.0。
//   原文件写 COLLAR_GUIDE_L = 8.0 且**不驱动任何几何**（grep 只出现在赋值与 echo 里），
//   [壳-5] 因此是一条空检查。真值 = LINER ＋ 两唇伸出量的较小者 = 3.50 mm < J1_MATE_LEN 6.0。
COLLAR_GUIDE_L    = LINER + min(COLLAR_LIP_TOP, COLLAR_LIP_BOTTOM);
// 结论：领口给不出「先导向后接触」，一次性对插必须用台面治具（MATING 第 2.1 节新增 A3）。
MATE_JIG_REQUIRED = true;

// ASSUMPTION: AS-31-mm-25 螺钉 M2 自攻 ×4（沿 X 贯穿），扭矩 0.15 N·m；
//   后半过孔 Ø2.30、沉头窝 Ø4.0 × 1.2，前半预孔 Ø1.60。
SCREW_PILOT_D = 1.60;
SCREW_CLR_D   = 2.30;
SCREW_HEAD_D  = 4.00;
SCREW_HEAD_H  = 1.20;
// 两颗穿过槽板定位孔（MOUNT_A/B），两颗只穿壳体，落在槽板顶边以上
S3_Z =  2.00;  S3_Y = 21.00;
S4_Z = -5.00;  S4_Y = 21.00;

// ASSUMPTION: AS-31-mm-26 防呆凸缘。
//   修订 d：**取消**。理由两条：① 底座 bay_keying_and_stops() 里从来没有对应豁口
//   （全仓 grep 无），键块不防任何呆，一级 A 防呆实际靠的是落入槽在 X 上的非对称；
//   ② 这 2.0 mm 正好等于领口承载背壁要的量，拿它去换 —— 模块总成 −X 端净增 0.40 mm。
KEY_TAB_L = 0;
KEY_TAB_W = 8.0;   // 沿 Z
KEY_TAB_H = 5.2;   // 沿 Y

// 壳体足底面比触点面低 0.10 mm：硬限位永远先于焊盘着落
FOOT_PROUD = 0.10;

// 底缘 45° 引入倒角
// 修订 d：1.5 → 0.40。1.5 的倒角把足底面两端各削掉 1.5 mm，实测落地面只剩
//   Z ∈ [−6.41, 4.29]，四根硬限位柱里有两根（Z = −7.86…−6.96 与 4.84…5.74）
//   **完全落空**（名义间隙 0.596 / 0.149 mm）。0.40 已覆盖落入槽滑配 0.15 ＋ 打印公差。
LEADIN_CHAMFER = 0.40;

PART = "assembly";   // assembly | front | back | print
SHOW_BOARDS = true;


// ====================================================================
// 派生量
// ====================================================================
SPLIT_X = FIN_MID_X;          // 分型面（沿 X），−26.935

MOSAICO_X_LO = -MOSAICO_W / 2;
MOSAICO_Y_HI =  MOSAICO_H / 2;
MOSAICO_Z_LO = -MOSAICO_T / 2;
MOSAICO_Z_HI =  MOSAICO_T / 2;

SHELL_FOOT_Y = MODULE_PAD_FACE_Y - FOOT_PROUD;     // 硬限位面 = 落地面，−24.195
SHELL_TOP_Y  = MOSAICO_Y_HI + LINER + COLLAR_LIP_T;// 24.295
SHELL_BOT_Y  = SHELL_FOOT_Y;
SEAT_X       = MOSAICO_X_LO - LINER;               // 领口贴合面 −23.095
// 修订 d：足部 −X 壁由 SHELL_MIN_W 1.20 加到 1.60，使足底面在弹簧针过板窗口
//   之外留出 ≥0.4 mm 宽的落地实料（硬限位柱要站在这里）。
FOOT_BACK_W  = 1.60;
// 壳体 −X 外表面：足部由触点板决定，鳍板段由针尾焊点决定
SHELL_X_LO   = PAD_X_MIN - FOOT_BACK_W;
FIN_BOX_X_LO = FIN_SOLDER_X - CLR_TAIL - SHELL_MIN_W;   // −30.035（鳍板段后壁外表面）

// Z 包络：+Z 与 Mosaico 前面齐平（见文件头 (c)）；−Z 由鳍板腔后壁决定
SHELL_Z_HI = MOSAICO_Z_HI;                                     // +5.74
SHELL_Z_LO = min(FIN_Z_LO - CLR_FIN_YZ, PAD_Z_MIN - CLR_PAD) - SHELL_MIN_W;   // −7.86
FOOT_Z_LO  = SHELL_Z_LO;
FOOT_Z_HI  = SHELL_Z_HI;
FOOT_Y_HI  = -15.0;
// 领口唇的 Z 范围：只包住 Mosaico 本体厚度，绝不外凸（落入槽 ±6.09 容不下更多）
COLLAR_Z_LO = MOSAICO_Z_LO;
COLLAR_Z_HI = MOSAICO_Z_HI;

// 壳体总包络（含防呆键块与领口上/下唇）
ENV_X_LO = SHELL_X_LO - KEY_TAB_L;                             // −37.295
ENV_X_HI = SEAT_X + LINER + max(COLLAR_LIP_TOP, COLLAR_LIP_BOTTOM);   // −19.595
ENV_Z_LO = FOOT_Z_LO;
ENV_Z_HI = SHELL_Z_HI;

// 自检用余量
W_FIN_BACK   = (FIN_Z_LO - CLR_FIN_YZ) - SHELL_Z_LO;           // 鳍板腔 −Z 壁
W_FIN_FRONT  = SHELL_Z_HI - (FIN_Z_HI + CLR_FIN_YZ);           // 鳍板腔 +Z 壁
W_PAD_BACK   = (PAD_Z_MIN - CLR_PAD) - FOOT_Z_LO;
W_PAD_FRONT  = FOOT_Z_HI - (PAD_Z_MAX + CLR_PAD);
W_J1_FRONT   = SHELL_Z_HI - (J1_BODY_Z_HI + CLR_J1);
W_FIN_TAIL   = (FIN_SOLDER_X - CLR_TAIL) - FIN_BOX_X_LO;       // 针尾让位腔到后壁外表面
W_SEAT       = SEAT_X - (FIN_X_MAX + CLR_FIN_X);               // 鳍板腔到领口贴合面
FOOT_Z_BAND_LO = (PAD_Z_MIN - CLR_PAD) - FOOT_Z_LO;            // 足部 −Z 侧剩余带宽
FOOT_Z_BAND_HI = FOOT_Z_HI - (PAD_Z_MAX + CLR_PAD);            // 足部 +Z 侧剩余带宽
GUIDE_HOLE_NEED = 3.20 + 2 * SHELL_MIN_W;                      // Ø3.2 销孔配 1.2 壁所需带宽
GUIDE_PIN_OMITTED_ON_PURPOSE = true;   // 定位改由落入槽模块条带滑配承担（AS-32-dock-1）
COLLAR_BACK_W_EFF = SEAT_X - (PAD_X_MAX + CLR_PAD);            // 领口承载背壁实际厚度
BAY_FLOOR_REF = MODULE_PAD_FACE_Y - FOOT_PROUD - 1.20;         // 底座槽地板（仅供 [壳-13] 文字引用）


// ====================================================================
// 工具
// ====================================================================
module bx(x0, x1, y0, y1, z0, z1) {
    translate([x0, y0, z0]) cube([x1 - x0, y1 - y0, z1 - z0]);
}

// 沿 +X 的螺钉：后半过孔 ＋ 沉头窝，前半预孔
module screw_at(z, y, x_back) {
    translate([x_back - 0.01, y, z]) rotate([0, 90, 0])
        cylinder(h = SPLIT_X - x_back + 0.01, d = SCREW_CLR_D);
    translate([x_back - 0.01, y, z]) rotate([0, 90, 0])
        cylinder(h = SCREW_HEAD_H, d = SCREW_HEAD_D);
    translate([SPLIT_X, y, z]) rotate([0, 90, 0])
        cylinder(h = ENV_X_HI - SPLIT_X + 1, d = SCREW_PILOT_D);
}

// 底缘 45° 引入倒角
module bottom_leadin() {
    c = LEADIN_CHAMFER;
    difference() {
        bx(ENV_X_LO - 5, ENV_X_HI + 5, SHELL_BOT_Y - 1, SHELL_BOT_Y + c,
           ENV_Z_LO - 5, ENV_Z_HI + 5);
        hull() {
            bx(ENV_X_LO + c, ENV_X_HI - c, SHELL_BOT_Y, SHELL_BOT_Y + 0.01,
               ENV_Z_LO + c, ENV_Z_HI - c);
            bx(ENV_X_LO, ENV_X_HI, SHELL_BOT_Y + c - 0.01, SHELL_BOT_Y + c,
               ENV_Z_LO, ENV_Z_HI);
        }
    }
}


// ====================================================================
// 壳体实体
// ====================================================================
module shell_solid() {
    union() {
        // 鳍板段（包住槽板与 J1 针尾）
        bx(FIN_BOX_X_LO, SEAT_X, SHELL_BOT_Y, SHELL_TOP_Y, SHELL_Z_LO, SHELL_Z_HI);
        // 足部（包住触点板，承载硬限位面）
        bx(SHELL_X_LO, SEAT_X, SHELL_FOOT_Y, FOOT_Y_HI, FOOT_Z_LO, FOOT_Z_HI);
        // 防呆键块：修订 d 取消（KEY_TAB_L = 0）
        // 领口上唇（压住 Mosaico +Y 面外缘）；顶面比承力压面低 COLLAR_TOP_DROP
        bx(SEAT_X, SEAT_X + LINER + COLLAR_LIP_TOP, MOSAICO_Y_HI + LINER,
           SHELL_TOP_Y - COLLAR_TOP_DROP, COLLAR_Z_LO, COLLAR_Z_HI);
        // 领口下唇（承托台肩）
        bx(SEAT_X, SEAT_X + LINER + COLLAR_LIP_BOTTOM, SHELL_BOT_Y, MOSAICO_Y_LO - LINER,
           COLLAR_Z_LO, COLLAR_Z_HI);
    }
}

module shell_cavity() {
    union() {
        // 鳍板槽（对 +Y 敞开，便于装配时把槽板落进后半）
        bx(FIN_X_MIN - CLR_FIN_X, FIN_X_MAX + CLR_FIN_X,
           FIN_Y_MIN - 0.01, FIN_Y_MAX + CLR_FIN_YZ,
           FIN_Z_LO - CLR_FIN_YZ, FIN_Z_HI + CLR_FIN_YZ);
        // J1 针尾（穿过槽板后剪脚）让位
        bx(FIN_SOLDER_X - CLR_TAIL, FIN_X_MIN,
           J1_BODY_Y_LO - 0.5, J1_BODY_Y_HI + 0.5,
           J1_BODY_Z_LO - 0.5, J1_BODY_Z_HI + 0.5);
        // J1 胶芯与配合针让位，同时就是领口中央开口（针由此伸向 H2）
        bx(J1_BODY_X_MIN - CLR_J1, SEAT_X + 30,
           J1_BODY_Y_LO - CLR_J1, J1_BODY_Y_HI + CLR_J1,
           J1_BODY_Z_LO - CLR_J1, J1_BODY_Z_HI + CLR_J1);
        // U1 与测试点区让位（在槽板元件面上，朝 +X）
        bx(FIN_X_MAX + CLR_FIN_X, FIN_X_MAX + CLR_FIN_X + 2.5,
           U1_Y - 4.0, U1_Y + 4.0, U1_Z - 2.5, U1_Z + 2.5);
        // 触点板槽（对 −Y 敞开，四面精密限位 —— 这是 X/Z 定位链的 e 环）
        // 修订 d：+X 边界由 SEAT_X 改为 PAD_X_MAX + CLR_PAD。原来挖到领口贴合面，
        //   等于把领口背壁整段掏空 —— [壳-13] 算出的 1.95 mm 背壁在几何里根本不存在，
        //   这正是「自检 echo 的数与模型实际挖出来的形状不是一回事」的又一例。
        bx(PAD_X_MIN - CLR_PAD, PAD_X_MAX + CLR_PAD,
           MODULE_PAD_FACE_Y - 10, PAD_TOP_Y + 0.01,
           PAD_Z_MIN - CLR_PAD, PAD_Z_MAX + CLR_PAD);
        // J3 双排焊点让位槽：壳体不得压在 90° 填角焊上
        bx(FIN_X_MIN - J3_PAD_L - 0.30, FIN_X_MAX + J3_PAD_L + 0.30,
           PAD_TOP_Y - 0.20, PAD_TOP_Y + J3_PAD_L + 0.40,
           FIN_Z_LO - CLR_FIN_YZ, FIN_Z_HI + CLR_FIN_YZ);
        // 螺钉（沿 X）
        screw_at(MOUNT_A_Z, MOUNT_A_Y, FIN_BOX_X_LO);
        screw_at(MOUNT_B_Z, MOUNT_B_Y, SHELL_X_LO);
        screw_at(S3_Z, S3_Y, FIN_BOX_X_LO);
        screw_at(S4_Z, S4_Y, FIN_BOX_X_LO);
        // 底缘 45° 引入倒角
        bottom_leadin();
        // Mosaico 本体及内衬的占位（保证壳体不侵入 Mosaico 空间）
        bx(SEAT_X, SEAT_X + 60, MOSAICO_Y_LO - LINER, MOSAICO_Y_HI + LINER,
           MOSAICO_Z_LO - LINER, MOSAICO_Z_HI + LINER);
    }
}

module shell() {
    difference() {
        shell_solid();
        shell_cavity();
    }
}

// 分型：前半 = X > SPLIT_X（含领口），后半 = X < SPLIT_X（含防呆键块）
module shell_front() {
    intersection() {
        shell();
        bx(SPLIT_X, ENV_X_HI + 5, SHELL_BOT_Y - 5, SHELL_TOP_Y + 5,
           ENV_Z_LO - 5, ENV_Z_HI + 5);
    }
}

module shell_back() {
    intersection() {
        shell();
        bx(ENV_X_LO - 5, SPLIT_X, SHELL_BOT_Y - 5, SHELL_TOP_Y + 5,
           ENV_Z_LO - 5, ENV_Z_HI + 5);
    }
}


// ====================================================================
// 输出
// ====================================================================
if (PART == "assembly") {
    if (SHOW_MOSAICO) mosaico_ghost();
    if (SHOW_BOARDS) { fin_board_3d(); j1_body_3d(); j1_pins_3d(); u1_3d();
                       j3_pads_3d(); pad_board_3d(); j2_pads_3d(); }
    color("LightSteelBlue", 0.55) shell_front();
    color("SteelBlue",     0.55) shell_back();
} else if (PART == "front") {
    shell_front();
} else if (PART == "back") {
    shell_back();
} else if (PART == "print") {
    // 分型面朝下摊平（绕 Y 轴转 90°，使分型面落到 XY 平面）
    rotate([0, 90, 0]) translate([-SPLIT_X, 0, 0]) shell_front();
    translate([0, 60, 0]) rotate([0, -90, 0]) translate([-SPLIT_X, 0, 0]) shell_back();
} else {
    echo("未知 PART：", PART);
}


// ====================================================================
// 自检 echo
// ====================================================================
function W(c) = c ? "  -> OK" : "  -> FAIL: 须改设计";
WEPS = 1e-6;
echo("==== module_shell.scad 派生尺寸（修订 c：X 分型 ＋ 无定位销 ＋ 无前后唇）====");
echo(str("壳体包络：X [", ENV_X_LO, " , ", ENV_X_HI,
         "]  Y [", SHELL_BOT_Y, " , ", SHELL_TOP_Y, "]  Z [", ENV_Z_LO, " , ", ENV_Z_HI, "]"));
echo(str("分型面 SPLIT_X = ", SPLIT_X, "（槽板中面）；前半厚 ", ENV_X_HI - SPLIT_X,
         " mm，后半厚 ", SPLIT_X - ENV_X_LO, " mm"));
echo(str("硬限位面 SHELL_FOOT_Y = ", SHELL_FOOT_Y, "（比触点面低 ", FOOT_PROUD, " mm）"));
echo(str("[壳-1] 取消 Ø3.20 定位销孔的定量理由：足部 ±Z 剩余带宽 = ",
         FOOT_Z_BAND_LO, " / ", FOOT_Z_BAND_HI, " mm，X 两端剩余 = ",
         (PAD_X_MIN - CLR_PAD) - SHELL_X_LO, " / ", 0,
         " mm；一个 Ø3.20 盲孔配 ", SHELL_MIN_W, " mm 壁需要 ", GUIDE_HOLE_NEED,
         " mm。修订 d：原判据写成「放不下才通过」，方向是反的，只能误报、",
         "保护不了任何东西；改为「要么放得下并装销，要么明确记为滑配定位」",
         W(GUIDE_PIN_OMITTED_ON_PURPOSE
           || max(FOOT_Z_BAND_LO, FOOT_Z_BAND_HI) >= GUIDE_HOLE_NEED)));
echo(str("[壳-2] 鳍板腔壁厚：−Z = ", W_FIN_BACK, "  +Z = ", W_FIN_FRONT,
         "  针尾腔到后壁 = ", W_FIN_TAIL, " mm；应 ≥ ", SHELL_MIN_W,
         W(W_FIN_BACK >= SHELL_MIN_W - WEPS && W_FIN_FRONT >= SHELL_MIN_W - WEPS
           && W_FIN_TAIL >= SHELL_MIN_W - WEPS)));
echo(str("[壳-3] 触点板槽壁厚：−Z = ", W_PAD_BACK, "  +Z = ", W_PAD_FRONT,
         " mm；应 ≥ ", SHELL_MIN_W,
         W(W_PAD_BACK >= SHELL_MIN_W - WEPS && W_PAD_FRONT >= SHELL_MIN_W - WEPS)));
echo(str("[壳-4] 鳍板腔到领口贴合面的料厚 = ", W_SEAT, " mm（J1 让位窗之外），应 ≥ ", SHELL_WALL,
         W(W_SEAT >= SHELL_WALL - WEPS)));
echo(str("[壳-5] 领口导向长度（派生真值）= ", COLLAR_GUIDE_L, " mm，J1_MATE_LEN = ", J1_MATE_LEN,
         " —— 领口给不出「先导向后接触」，差 ", J1_MATE_LEN - COLLAR_GUIDE_L,
         " mm；因此对插必须用台面治具（MATING 第 2.1 节 A3）",
         W(COLLAR_GUIDE_L > J1_MATE_LEN || MATE_JIG_REQUIRED)));
echo(str("[壳-6] J1 胶芯让位到壳体 +Z 外表面壁厚 = ", W_J1_FRONT, " mm；应 ≥ ", SHELL_MIN_W,
         W(W_J1_FRONT >= SHELL_MIN_W - WEPS)));
echo(str("[壳-7] 壳体 +Z 外表面 ", SHELL_Z_HI, " 与 Mosaico 前面 ", MOSAICO_Z_HI,
         " 齐平（差 ", SHELL_Z_HI - MOSAICO_Z_HI, "）；−Z 外表面 ", FOOT_Z_LO,
         " 相对 Mosaico 背面 ", MOSAICO_Z_LO, " 外凸 ", MOSAICO_Z_LO - FOOT_Z_LO,
         " mm —— 这一段必须由底座在模块条带把落入槽向 −Z 加深来承接",
         W(SHELL_Z_HI <= MOSAICO_Z_HI + WEPS)));
echo(str("[壳-8] 领口只保留上/下唇：上唇伸出 ", COLLAR_LIP_TOP, "、下唇 ", COLLAR_LIP_BOTTOM,
         " mm，Z 范围 [", COLLAR_Z_LO, " , ", COLLAR_Z_HI,
         "]（不超出 Mosaico 本体厚度，否则落入槽 ±",
         MOSAICO_T / 2, " 容不下）",
         W(COLLAR_Z_HI <= MOSAICO_T / 2 + WEPS && COLLAR_Z_LO >= -MOSAICO_T / 2 - WEPS)));
echo(str("[壳-12] 足底落地面（含 ", LEADIN_CHAMFER, " mm 引入倒角）X ∈ [",
         SHELL_X_LO + LEADIN_CHAMFER, " , ", SEAT_X - LEADIN_CHAMFER,
         "]；触点板槽 X ∈ [", PAD_X_MIN - CLR_PAD, " , ", PAD_X_MAX + CLR_PAD,
         "]。硬限位柱只能站在两者之差上：−X 条 ", (PAD_X_MIN - CLR_PAD) - (SHELL_X_LO + LEADIN_CHAMFER),
         " mm，+X 条 ", (SEAT_X - LEADIN_CHAMFER) - (PAD_X_MAX + CLR_PAD),
         " mm；两条都须 ≥ 0.40（底座 stop_posts 据此定位）",
         W((PAD_X_MIN - CLR_PAD) - (SHELL_X_LO + LEADIN_CHAMFER) >= 0.40 - WEPS
           && (SEAT_X - LEADIN_CHAMFER) - (PAD_X_MAX + CLR_PAD) >= 0.40 - WEPS)));
echo(str("[壳-13] 领口下唇根部（X = SEAT_X 平面）整截面 = ", COLLAR_BACK_W_EFF,
         " mm 厚 × 唇 Y 带 ", MOSAICO_Y_LO - LINER - SHELL_BOT_Y,
         " mm；下唇是 Mosaico 在 Y 上唯一的承托件（底座在 Mosaico 正下方 ",
         MOSAICO_Y_LO - BAY_FLOOR_REF, " mm 内无料），根部必须是整截面而不是残筋",
         W(COLLAR_BACK_W_EFF >= SHELL_MIN_W - WEPS)));
echo(str("[壳-14] 上压框承力压面只落在鳍板段顶面：领口上唇顶面 = ",
         SHELL_TOP_Y - COLLAR_TOP_DROP, "，壳体顶面 = ", SHELL_TOP_Y,
         "，下沉 ", COLLAR_TOP_DROP, " mm（须 ≥ 2×PRINT_TOL = ", 2 * PRINT_TOL,
         "）—— 否则 9.6 N 经上唇灌进 Mosaico，违反方案 J 不变量 ②",
         W(COLLAR_TOP_DROP >= 2 * PRINT_TOL - WEPS)));
echo(str("[壳-9] 四颗 M2 沿 X 贯穿：MOUNT_A(Z ", MOUNT_A_Z, ", Y ", MOUNT_A_Y,
         ")、MOUNT_B(Z ", MOUNT_B_Z, ", Y ", MOUNT_B_Y, ") 穿槽板；S3(Z ", S3_Z, ", Y ", S3_Y,
         ")、S4(Z ", S4_Z, ", Y ", S4_Y, ") 只穿壳体，须在槽板顶边 ", FIN_Y_MAX, " 以上",
         W(S3_Y > FIN_Y_MAX + WEPS && S4_Y > FIN_Y_MAX + WEPS)));
// 修订 d：原 [壳-10] 按「整条包络」算力偶臂（X 8.05 / Z 5.8），是虚的 ——
//   足底真正能落地的只有触点板槽两侧的两条实料，柱站在别处等于悬空。
LAND_X_LO_A = SHELL_X_LO + LEADIN_CHAMFER;   LAND_X_HI_A = PAD_X_MIN - CLR_PAD;
LAND_X_LO_B = PAD_X_MAX + CLR_PAD;           LAND_X_HI_B = SEAT_X - LEADIN_CHAMFER;
LAND_ARM_X  = (LAND_X_LO_B + LAND_X_HI_B)/2 - (LAND_X_LO_A + LAND_X_HI_A)/2;
echo(str("[壳-10] 真实落地条：−X [", LAND_X_LO_A, " , ", LAND_X_HI_A,
         "]（宽 ", LAND_X_HI_A - LAND_X_LO_A, "），+X [", LAND_X_LO_B, " , ", LAND_X_HI_B,
         "]（宽 ", LAND_X_HI_B - LAND_X_LO_B, "）；两条中心距 = 真实 X 力偶臂 ",
         LAND_ARM_X, " mm；Z 向力偶臂由底座两排柱的 Z 间距给定；",
         DOCK_COLS * DOCK_ROWS, " 针总压 ", F_PIN_TOTAL,
         " N 由上压框经足顶面压入。合力点 X = ", (PAD_X_MIN + PAD_X_MAX)/2,
         " 必须落在两条之间", W((PAD_X_MIN + PAD_X_MAX)/2 > LAND_X_HI_A
                              && (PAD_X_MIN + PAD_X_MAX)/2 < LAND_X_LO_B)));
echo(str("[壳-11] 承力卡扣已取消（方案 J 第 5 节：15 N 预压改由上压框两颗 M2 承担），",
         "模块侧不再吐卡扣保持力需求的实现，只吐需求值 RETENTION_N"));
echo("==== 结束 ====");

// ====================================================================
// ICD 契约输出 —— 供 hardware/check_cross_branch.py 自动比对
// ====================================================================
// 规则：**凡是两个分支都要知道的物理量，必须在这里吐一行**，格式
//     ICD-CONTRACT|<键>|<值>
// 键名由 ICD 第 1 节定义，两边必须用同一个键名指同一个物理量（按物理含义，不按变量名）。
module icd_contract() {
  // —— Mosaico 本体包络 ——
  echo(str("ICD-CONTRACT|MOSAICO_W|", MOSAICO_W));
  echo(str("ICD-CONTRACT|MOSAICO_H|", MOSAICO_H));
  echo(str("ICD-CONTRACT|MOSAICO_T|", MOSAICO_T));
  // —— 弹簧针场 ——
  echo(str("ICD-CONTRACT|DOCK_PIN_FIELD_X0|", DOCK_PIN_FIELD_X0));
  echo(str("ICD-CONTRACT|DOCK_PIN_FIELD_Z0|", DOCK_PIN_FIELD_Z0));
  echo(str("ICD-CONTRACT|DOCK_PIN_FIELD_Y|",  DOCK_PIN_FIELD_Y));
  echo(str("ICD-CONTRACT|DOCK_PITCH|", DOCK_PITCH));
  echo(str("ICD-CONTRACT|DOCK_COLS|",  DOCK_COLS));
  echo(str("ICD-CONTRACT|DOCK_ROWS|",  DOCK_ROWS));
  echo(str("ICD-CONTRACT|DOCK_PAD_D|", DOCK_PAD_D));
  // —— 弹簧针选型契约 ——
  echo(str("ICD-CONTRACT|DOCK_PIN_TIP_D|",  DOCK_PIN_TIP_D));
  echo(str("ICD-CONTRACT|DOCK_PIN_TRAVEL|", DOCK_PIN_TRAVEL));
  echo(str("ICD-CONTRACT|DOCK_PIN_STROKE|", DOCK_PIN_STROKE));
  echo(str("ICD-CONTRACT|DOCK_PIN_FORCE_N|",DOCK_PIN_FORCE_N));
  // —— 定位公差 ——
  echo(str("ICD-CONTRACT|DOCK_X_TOL|", DOCK_X_TOL));
  echo(str("ICD-CONTRACT|DOCK_Z_TOL|", DOCK_Z_TOL));
  // —— 触点板外形 ——
  echo(str("ICD-CONTRACT|CONTACT_PCB_X|", PAD_BOARD_L));
  echo(str("ICD-CONTRACT|CONTACT_PCB_Z|", PAD_BOARD_W));
  // —— 模块总成（含壳体）的实际包络：底座的落入槽必须容得下它 ——
  echo(str("ICD-CONTRACT|MODULE_ENV_X_LO|", ENV_X_LO));
  echo(str("ICD-CONTRACT|MODULE_ENV_X_HI|", ENV_X_HI));
  echo(str("ICD-CONTRACT|MODULE_ENV_Y_LO|", SHELL_FOOT_Y));
  echo(str("ICD-CONTRACT|MODULE_ENV_Y_HI|", SHELL_TOP_Y));
  echo(str("ICD-CONTRACT|MODULE_ENV_Z_LO|", ENV_Z_LO));
  echo(str("ICD-CONTRACT|MODULE_ENV_Z_HI|", ENV_Z_HI));
  // —— 承力闭环 ——
  echo(str("ICD-CONTRACT|HARD_STOP_Y|", SHELL_FOOT_Y));
  // MATING.md 第 4.1 节：保持力要求 ≥30 N。D-026 后改由上压框 M2 螺钉承担。
  echo(str("ICD-CONTRACT|RETENTION_N|", 30));
}
icd_contract();
