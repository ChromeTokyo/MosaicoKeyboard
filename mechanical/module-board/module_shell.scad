// 提案 · 未冻结 · 由 Claude 主控（claude-opus-5）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
//
// module_shell.scad —— 模块板保护壳体（可 3D 打印，用户本周可打）
// 分支 claude/design-d/mech-module ／ 目录 mechanical/module-board/
//
// 作用（四项，缺一不可）：
//   ① 保护 J1 右角公头与槽板走线；② 提供落入底座的导向面与定位孔；
//   ③ 提供承力闭环所需的硬限位足与卡扣槽（见 MATING.md 第 4 节）；
//   ④ 领口夹持 Mosaico −X 区，使 H2 成为非定位、非承力的纯电气界面（MATING.md 第 4.3 节）。
//
// 与 module_board.scad 的关系：本文件**不重复定义**板级尺寸，全部 include 进来。
// 若 module_board.scad 的 ASSUMPTION 改值，本文件自动跟随。
//
// 坐标系与 module_board.scad 完全相同（ICD 第 1 节整机坐标）。
// 分型面：Z = SPLIT_Z = FIN_MID_Z（槽板中面），前半（+Z）与后半（−Z）对合。

include <module_board.scad>;

// include 会执行被包含文件的顶层语句。OpenSCAD 的变量是「文件作用域内最后一次赋值生效」，
// 因此这里把 MODE 置为 "none"，使 module_board.scad 的输出分支不产生任何几何，
// 只留下参数、函数与模块供本文件使用。**不要删除这一行**，否则导出 STL 时
// 两块 PCB 与 Mosaico 幽灵体会混进壳体实体里。
MODE = "none";


// ====================================================================
// ASSUMPTION 块 —— 壳体自身的尺寸假设（板级尺寸见 module_board.scad 顶部）
// ====================================================================

// ASSUMPTION: AS-31-mm-20 领口贴合面内衬 0.5 mm 闭孔泡棉／TPU（邵氏 A40–60），
//   吸收 Mosaico 相对模块组件的 ±0.3 mm 浮动（MATING.md 第 4.3 节措施 3）。
//   验证：首版件量夹持力与残余浮动量；G6-G1 五十次插拔后复量。
LINER = 0.5;

// ASSUMPTION: AS-31-mm-21 壁厚 2.0 mm、最小特征壁 1.2 mm，适配 0.4 mm 喷嘴 ×
//   0.2 mm 层高的 FDM；材料 PETG 或 ABS（PLA 不可，握把内温升与蠕变）。
//   验证：打印后按 MODULE_SHELL.md 第 6 节 P2 做壁厚与刚度检查。
SHELL_WALL   = 2.0;
SHELL_MIN_W  = 1.2;

// ASSUMPTION: AS-31-mm-18 3D 打印件孔位与高度公差 ±0.15 mm。**是 MATING.md 第 6 节公差链
//   最大的不确定项。** 验证：打标定件（含 Ø3.2 孔 ×4、20 mm 间距）量 20 处。
PRINT_TOL = 0.15;

// 装配间隙（打印件对 PCB）
CLR_FIN_Z  = 0.15;   // 鳍板槽对槽板厚度方向单边间隙
CLR_FIN_XY = 0.20;   // 鳍板槽对槽板轮廓单边间隙
CLR_PAD    = 0.05;   // 触点板槽单边间隙（MATING.md 第 6 节 e 环，刻意做紧）
CLR_J1     = 0.50;   // J1 本体让位

// ASSUMPTION: AS-31-mm-22 领口唇伸出量：前（屏侧）2.0、后 4.0、上 3.0、下 3.0 mm；唇厚 1.2 mm。
//   前唇 2.0 mm 会压在屏幕面的左边缘上：**Mosaico 屏幕有效区到 −X 边的距离 unknown**。
//   验证：到货量屏幕有效区边界到机身 −X 边的距离；若 < 2.5 mm，前唇改 1.2 mm 或改为只在 ±Y 端点触。
COLLAR_LIP_FRONT  = 2.0;
COLLAR_LIP_BACK   = 4.0;
COLLAR_LIP_TOP    = 3.0;
COLLAR_LIP_BOTTOM = 3.0;
COLLAR_LIP_T      = 1.2;
// 领口沿 X 的导向长度：必须 > J1_MATE_LEN，保证一次性插入时先导向后接触（MATING.md 第 2.2 节 B3）
COLLAR_GUIDE_L    = 8.0;

// ASSUMPTION: AS-31-mm-23 定位孔：A 为 Ø3.20 圆孔（主基准），B 为 3.20 × 4.20 长圆孔
//   （长轴沿 A→B 即 X 向，避免过定位）；配 Ø3.00 定位销，engage 8.0 mm。
//   验证：MATING.md 第 11 节 M4，落入 20 次量针尖落点偏移。
GUIDE_HOLE_D    = 3.20;
GUIDE_SLOT_EXTRA = 1.00;   // 长圆孔沿 X 的额外长度
GUIDE_DEPTH     = 8.50;    // 壳体孔深（销露出 8.0，留 0.5 余量）
GUIDE_PIN_ENGAGE = 8.00;   // 接口参数：底座销露出长度，由 mech-dock 实现（MATING.md 第 3.1 节）
GUIDE_A_X = -48.50;  GUIDE_B_X = -31.00;   // 间距 17.5 mm（受足部长度与螺钉、卡扣让位限制，见文末 [壳-9]）
GUIDE_Z   = 2.30;                           // 两孔同 Z，位于触点板 +Z 侧之外

// ASSUMPTION: AS-31-mm-24 卡扣槽：宽 8.0（X）、深 1.2（Z）、锁止面 1.5（Y）、0° 正锁，
//   上方 30° 导入斜面；两处各需 ≥ 15 N 保持力（MATING.md 第 7.1 节）。
//   验证：M7 推拉力计沿 +Y 拉，≥ 30 N 不脱出。
CATCH_W     = 8.0;
CATCH_D     = 1.2;
CATCH_H     = 1.5;
CATCH_RAMP  = 1.5;
CATCH_Y     = -19.0;        // 锁止面中心 Y

// ASSUMPTION: AS-31-mm-25 螺钉 M2 自攻 ×4，扭矩 0.15 N·m（AS-31-mm-14）；
//   前半柱预孔 Ø1.60、后半过孔 Ø2.30、沉头窝 Ø4.0 × 1.2。
SCREW_PILOT_D = 1.60;
SCREW_CLR_D   = 2.30;
SCREW_HEAD_D  = 4.00;
SCREW_HEAD_H  = 1.20;
BOSS_D        = 4.60;
// 两颗穿过槽板定位孔，两颗只穿壳体
// 两颗只穿壳体的螺钉必须落在槽板轮廓之外，而槽板外只有「鳍板顶边以上」这一块区域
// 有足够厚度做 M2 柱（−X 侧壁只有 1.8 mm，领口侧只有 0.5 mm），故两颗都在 Y > FIN_Y_MAX。
S3_X = -27.00;  S3_Y =  19.50;   // 靠领口，负责领口上半的夹持
S4_X = -46.00;  S4_Y =  19.50;

// ASSUMPTION: AS-31-mm-26 防呆凸缘：足部 −X 端伸出 2.0 mm 的键块，底座腔对应开豁口；
//   反向放入时凸缘撞腔壁，落入深度 ≤ 3 mm（远小于弹簧针首次接触的 1.7 mm 之前）。
//   验证：M5／G6-H2，不带电，用无源样件做。
KEY_TAB_L = 2.0;
KEY_TAB_W = 8.0;   // 沿 Z
KEY_TAB_H = 5.2;   // 沿 Y

// 壳体足底面比触点面低 0.10 mm：硬限位永远先于焊盘着落，焊盘不承受压紧力
FOOT_PROUD = 0.10;

// 底缘 45° 引入倒角：落入时先由它把整机推进销的捕获范围（MATING.md 第 3.3 节）
LEADIN_CHAMFER = 1.5;

PART = "assembly";   // assembly | front | back | print
SHOW_BOARDS = true;  // assembly 模式下是否显示两块 PCB


// ====================================================================
// 派生量
// ====================================================================
SPLIT_Z = FIN_MID_Z;

MOSAICO_X_LO = -MOSAICO_W / 2;
MOSAICO_Y_HI =  MOSAICO_H / 2;
MOSAICO_Z_LO = -MOSAICO_T / 2;
MOSAICO_Z_HI =  MOSAICO_T / 2;

SHELL_FOOT_Y = MODULE_PAD_FACE_Y - FOOT_PROUD;     // 壳体足底面（＝底座硬限位面）
SHELL_TOP_Y  = MOSAICO_Y_HI + LINER + COLLAR_LIP_T;
SHELL_BOT_Y  = SHELL_FOOT_Y;
SEAT_X       = MOSAICO_X_LO - LINER;               // 领口贴合面（隔 0.5 内衬）
SHELL_X_LO   = FIN_X_MIN - SHELL_WALL;

SHELL_Z_HI = MOSAICO_Z_HI + LINER + COLLAR_LIP_T;  // +7.44
SHELL_Z_LO = MOSAICO_Z_LO - LINER - COLLAR_LIP_T;  // −7.44
FOOT_Z_LO  = PAD_Z_MIN - SHELL_WALL;               // 足部为容纳触点板向 −Z 加宽
FOOT_Z_HI  = SHELL_Z_HI;
FOOT_Y_HI  = -15.0;

CATCH_X    = J3_CENTER_X;                           // 与触点场同 X（MATING.md 第 4.2 节）
CATCH_Z_F  = FOOT_Z_HI;
CATCH_Z_B  = FOOT_Z_LO;
CATCH_Z_MEAN = (CATCH_Z_F + CATCH_Z_B) / 2;

// 领口中央开口：让 J1 本体与配合针、槽板前端通过
OPEN_Y_LO = -16.0;  OPEN_Y_HI = 16.0;
OPEN_Z_LO = FIN_Z_LO - 1.0;
OPEN_Z_HI = J1_BODY_Z_HI + 1.0;

// 壳体总包络（含防呆键块与领口后唇），倒角与 mech-dock 的腔体尺寸都用它
ENV_X_LO = SHELL_X_LO - KEY_TAB_L;
ENV_X_HI = SEAT_X + LINER + COLLAR_LIP_BACK;
ENV_Z_LO = FOOT_Z_LO;
ENV_Z_HI = SHELL_Z_HI;


// ====================================================================
// 工具
// ====================================================================
module bx(x0, x1, y0, y1, z0, z1) {
    translate([x0, y0, z0]) cube([x1 - x0, y1 - y0, z1 - z0]);
}

module guide_hole(x) {
    // 沿 +Y 打入的盲孔；B 孔沿 X 加长成长圆孔
    ex = (x == GUIDE_B_X) ? GUIDE_SLOT_EXTRA : 0;
    hull() {
        translate([x - ex / 2, SHELL_FOOT_Y - 0.5, GUIDE_Z])
            rotate([-90, 0, 0]) cylinder(h = GUIDE_DEPTH + 0.5, d = GUIDE_HOLE_D);
        translate([x + ex / 2, SHELL_FOOT_Y - 0.5, GUIDE_Z])
            rotate([-90, 0, 0]) cylinder(h = GUIDE_DEPTH + 0.5, d = GUIDE_HOLE_D);
    }
    // 30° 导入锥（孔口扩大）
    translate([x, SHELL_FOOT_Y - 0.01, GUIDE_Z])
        rotate([-90, 0, 0])
            cylinder(h = 1.5, d1 = GUIDE_HOLE_D + 1.7, d2 = GUIDE_HOLE_D);
}

module catch_pocket(zface, outward) {
    // outward = +1 表示槽开向 +Z，−1 开向 −Z
    z0 = (outward > 0) ? zface - CATCH_D : zface;
    z1 = (outward > 0) ? zface + 0.01    : zface + CATCH_D;
    union() {
        bx(CATCH_X - CATCH_W / 2, CATCH_X + CATCH_W / 2,
           CATCH_Y - CATCH_H / 2, CATCH_Y + CATCH_H / 2, z0, z1);
        // 上方 30° 导入斜面：落入时卡爪爬上去
        hull() {
            bx(CATCH_X - CATCH_W / 2, CATCH_X + CATCH_W / 2,
               CATCH_Y + CATCH_H / 2 - 0.01, CATCH_Y + CATCH_H / 2, z0, z1);
            bx(CATCH_X - CATCH_W / 2, CATCH_X + CATCH_W / 2,
               CATCH_Y + CATCH_H / 2 + CATCH_RAMP * 1.73,
               CATCH_Y + CATCH_H / 2 + CATCH_RAMP * 1.73 + 0.01,
               (outward > 0) ? zface - 0.01 : zface,
               (outward > 0) ? zface        : zface + 0.01);
        }
    }
}

// 底缘 45° 引入倒角：构造「锥形包络之外、底部 LEADIN_CHAMFER 高度带以内」的实体，
// 从壳体中减去它，即把底面四周的棱全部倒成 45°。
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

module screw_at(x, y, through_pcb) {
    // 过孔 + 沉头窝（后半），预孔（前半）；through_pcb 时前半加一段 Ø2.0 定位柱
    translate([x, y, SHELL_Z_LO - 1]) cylinder(h = 200, d = SCREW_CLR_D);
    translate([x, y, SHELL_Z_LO - 0.01]) cylinder(h = SCREW_HEAD_H, d = SCREW_HEAD_D);
}


// ====================================================================
// 壳体实体
// ====================================================================
module shell_solid() {
    union() {
        // 主体（鳍板腔 + 领口根部）
        bx(SHELL_X_LO, SEAT_X, SHELL_BOT_Y, SHELL_TOP_Y, SHELL_Z_LO, SHELL_Z_HI);
        // 足部（向 −Z 加宽以容纳触点板，并承载定位孔、卡扣、硬限位面）
        bx(SHELL_X_LO, FIN_X_MAX, SHELL_FOOT_Y, FOOT_Y_HI, FOOT_Z_LO, FOOT_Z_HI);
        // 防呆键块
        bx(SHELL_X_LO - KEY_TAB_L, SHELL_X_LO, SHELL_FOOT_Y, SHELL_FOOT_Y + KEY_TAB_H,
           FIN_MID_Z - KEY_TAB_W / 2, FIN_MID_Z + KEY_TAB_W / 2);
        // 领口四唇（伸出 +X 抱住 Mosaico）
        bx(SEAT_X, SEAT_X + LINER + COLLAR_LIP_FRONT, SHELL_BOT_Y, SHELL_TOP_Y,
           MOSAICO_Z_HI + LINER, SHELL_Z_HI);                                   // 前（屏侧）
        bx(SEAT_X, SEAT_X + LINER + COLLAR_LIP_BACK, SHELL_BOT_Y, SHELL_TOP_Y,
           SHELL_Z_LO, MOSAICO_Z_LO - LINER);                                   // 后（背侧）
        bx(SEAT_X, SEAT_X + LINER + COLLAR_LIP_TOP, MOSAICO_Y_HI + LINER, SHELL_TOP_Y,
           SHELL_Z_LO, SHELL_Z_HI);                                             // 上
        bx(SEAT_X, SEAT_X + LINER + COLLAR_LIP_BOTTOM, SHELL_BOT_Y, MOSAICO_Y_LO - LINER,
           SHELL_Z_LO, SHELL_Z_HI);                                             // 下（承托台肩）
    }
}

module shell_cavity() {
    union() {
        // 领口中央开口：J1 本体与配合针、槽板前端由此通过
        bx(SEAT_X - 6.0, SEAT_X + 30, OPEN_Y_LO, OPEN_Y_HI, OPEN_Z_LO, OPEN_Z_HI);
        // 鳍板槽（对 +X 敞开）
        bx(FIN_X_MIN - CLR_FIN_XY, SEAT_X + 1, FIN_Y_MIN - 0.01, FIN_Y_MAX + CLR_FIN_XY,
           FIN_Z_LO - CLR_FIN_Z, FIN_Z_HI + CLR_FIN_Z);
        // J1 本体让位
        bx(J1_BODY_X_MIN - CLR_J1, SEAT_X + 30, J1_BODY_Y_LO - CLR_J1, J1_BODY_Y_HI + CLR_J1,
           J1_BODY_Z_LO - CLR_J1, J1_BODY_Z_HI + CLR_J1);
        // U1 与测试点区让位
        bx(U1_X - 6, U1_X + 6, U1_Y - 8, U1_Y + 8, FIN_Z_HI, FIN_Z_HI + 3.0);
        // 触点板槽（对 −Y 敞开，四面精密限位 —— 这是 X/Z 定位链的 e 环）
        bx(PAD_X_MIN - CLR_PAD, PAD_X_MAX + CLR_PAD, MODULE_PAD_FACE_Y - 10, PAD_TOP_Y + 0.01,
           PAD_Z_MIN - CLR_PAD, PAD_Z_MAX + CLR_PAD);
        // J3 焊点让位槽：壳体不得压在半孔焊点上
        bx(FIN_X_MIN - 1, FIN_X_MAX + 1, PAD_TOP_Y - 0.8, PAD_TOP_Y + 1.2,
           FIN_Z_LO - 0.8, FIN_Z_HI + 0.8);
        // 定位孔
        guide_hole(GUIDE_A_X);
        guide_hole(GUIDE_B_X);
        // 卡扣槽
        catch_pocket(CATCH_Z_F, +1);
        catch_pocket(CATCH_Z_B, -1);
        // 螺钉
        screw_at(MOUNT_A_X, MOUNT_A_Y, true);
        screw_at(MOUNT_B_X, MOUNT_B_Y, true);
        screw_at(S3_X, S3_Y, false);
        screw_at(S4_X, S4_Y, false);
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

module shell_front() {
    intersection() {
        shell();
        bx(SHELL_X_LO - 10, SEAT_X + 40, SHELL_BOT_Y - 5, SHELL_TOP_Y + 5, SPLIT_Z, SHELL_Z_HI + 5);
    }
}

module shell_back() {
    intersection() {
        shell();
        bx(SHELL_X_LO - 10, SEAT_X + 40, SHELL_BOT_Y - 5, SHELL_TOP_Y + 5, FOOT_Z_LO - 5, SPLIT_Z);
    }
}


// ====================================================================
// 输出
// ====================================================================
if (PART == "assembly") {
    if (SHOW_MOSAICO) mosaico_ghost();
    if (SHOW_BOARDS) { fin_board_3d(); j1_body_3d(); j1_pins_3d(); pad_board_3d(); j2_pads_3d(); }
    color("LightSteelBlue", 0.55) shell_front();
    color("SteelBlue",     0.55) shell_back();
} else if (PART == "front") {
    shell_front();
} else if (PART == "back") {
    shell_back();
} else if (PART == "print") {
    // 分型面朝下摊平；后半用绕 Y 轴 180° 的真旋转翻面（不可用 mirror，会得到镜像件）
    translate([0, 0, -SPLIT_Z]) shell_front();
    translate([60, 0, 0]) rotate([0, 180, 0]) translate([0, 0, -SPLIT_Z]) shell_back();
} else {
    echo("未知 PART：", PART);
}


// ====================================================================
// 自检 echo
// ====================================================================
echo("==== module_shell.scad 派生尺寸（ASSUMPTION，未经实物核对）====");
echo(str("壳体包络：X [", SHELL_X_LO - KEY_TAB_L, " , ", SEAT_X + LINER + COLLAR_LIP_BACK,
         "]  Y [", SHELL_BOT_Y, " , ", SHELL_TOP_Y, "]  Z [", FOOT_Z_LO, " , ", SHELL_Z_HI, "]"));
echo(str("分型面 SPLIT_Z = ", SPLIT_Z, "；前半厚 ", SHELL_Z_HI - SPLIT_Z,
         " mm，后半厚（足部）", SPLIT_Z - FOOT_Z_LO, " mm"));
echo(str("硬限位面 SHELL_FOOT_Y = ", SHELL_FOOT_Y, "（比触点面低 ", FOOT_PROUD, " mm）"));
echo(str("定位孔：A (", GUIDE_A_X, " , ", GUIDE_Z, ") 圆 Ø", GUIDE_HOLE_D,
         "；B (", GUIDE_B_X, " , ", GUIDE_Z, ") 长圆 ", GUIDE_HOLE_D, " × ",
         GUIDE_HOLE_D + GUIDE_SLOT_EXTRA, "；间距 ", GUIDE_B_X - GUIDE_A_X, " mm"));
echo(str("[壳-1] 定位孔到触点板槽的壁厚 = ",
         GUIDE_Z - GUIDE_HOLE_D / 2 - (PAD_Z_MAX + CLR_PAD), " mm，应 ≥ ", SHELL_MIN_W));
echo(str("[壳-2] 定位孔到足部 +Z 外表面壁厚 = ",
         FOOT_Z_HI - (GUIDE_Z + GUIDE_HOLE_D / 2), " mm，应 ≥ ", SHELL_MIN_W));
echo(str("[壳-3] 卡扣 X = ", CATCH_X, " 与触点场心 X = ", J3_CENTER_X,
         " 相同 → 绕 Z 轴力矩名义为 0"));
echo(str("[壳-4] 卡扣 Z 合力点 = ", CATCH_Z_MEAN, "，触点场心 Z = ", FIN_MID_Z,
         "，偏差 ΔZ = ", CATCH_Z_MEAN - FIN_MID_Z,
         " mm → 残余力矩由足部硬限位的力偶吸收，核算见 MATING.md 第 4.4 节"));
echo(str("[壳-5] 领口导向长度 = ", COLLAR_GUIDE_L, " mm，应 > J1_MATE_LEN = ", J1_MATE_LEN,
         "（一次性插入先导向后接触，MATING.md 第 2.2 节 B3）"));
echo(str("[壳-6] 鳍板腔后壁厚 = ", (FIN_Z_LO - CLR_FIN_Z) - SHELL_Z_LO,
         " mm；前壁（到 J1 让位）= ", SHELL_Z_HI - (J1_BODY_Z_HI + CLR_J1), " mm；应 ≥ ", SHELL_MIN_W));
echo(str("[壳-7] 壳体 +Z 外表面 ", SHELL_Z_HI, " 相对 Mosaico 屏面 ", MOSAICO_Z_HI,
         " 外凸 ", SHELL_Z_HI - MOSAICO_Z_HI, " mm；足部 −Z 外表面 ", FOOT_Z_LO,
         " 相对 Mosaico 背面 ", MOSAICO_Z_LO, " 外凸 ", MOSAICO_Z_LO - FOOT_Z_LO,
         " mm（由 mech-dock 的握把厚度承接，MD-06）"));
echo(str("[壳-8] 前唇压在屏幕面上 ", COLLAR_LIP_FRONT,
         " mm —— 屏幕有效区边距 unknown，AS-31-mm-22 待到货量"));
echo(str("[壳-9] 让位距离：定位孔 B(", GUIDE_B_X, ") 与螺钉 MOUNT_B(", MOUNT_B_X,
         ") 沿 X 净距 = ", abs(MOUNT_B_X - GUIDE_B_X) - (GUIDE_HOLE_D + GUIDE_SLOT_EXTRA) / 2 - SCREW_CLR_D / 2,
         " mm；定位孔 B 与卡扣槽沿 Z 无交集（孔 Z 上缘 ", GUIDE_Z + GUIDE_HOLE_D / 2,
         "，前卡扣槽 Z 下缘 ", CATCH_Z_F - CATCH_D, "）"));
echo(str("[壳-10] 硬限位落地面：X [", SHELL_X_LO, " , ", SEAT_X + LINER + COLLAR_LIP_BOTTOM,
         "]（含下唇），力偶臂 ≈ ", ((SEAT_X + LINER + COLLAR_LIP_BOTTOM) - SHELL_X_LO) / 2 - 1,
         " mm；Z [", FOOT_Z_LO, " , ", FOOT_Z_HI, "]，力偶臂 ≈ ", (FOOT_Z_HI - FOOT_Z_LO) / 2 - 1, " mm"));
echo("==== 结束 ====");

// ====================================================================
// ICD 契约输出 —— 供 hardware/check_cross_branch.py 自动比对
// ====================================================================
// 2026-09-21 增加。起因：2026-09-21 的双路清点在四个设计分支之间查出 40 条不一致、
// 22 条阻断，而每个分支自己的自检**全部通过**——因为自检只查本文件内部自洽，
// 从来没有任何东西比对过两个分支。这一段就是补那个缺口。
//
// 规则：**凡是两个分支都要知道的物理量，必须在这里吐一行**，格式
//     ICD-CONTRACT|<键>|<值>
// 键名由 ICD 第 1 节定义，两边必须用同一个键名指同一个物理量（**按物理含义，不按变量名**）。
// 新增任何跨件量时，两边同时加键，否则 check_cross_branch.py 会报「只有一侧给了值」。
module icd_contract() {
  // —— Mosaico 本体包络（两边必须完全一致）——
  echo(str("ICD-CONTRACT|MOSAICO_W|", MOSAICO_W));
  echo(str("ICD-CONTRACT|MOSAICO_H|", MOSAICO_H));
  echo(str("ICD-CONTRACT|MOSAICO_T|", MOSAICO_T));
  // —— 弹簧针场（ICD 第 1 节留空，正是 40 条冲突的震中）——
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
  echo(str("ICD-CONTRACT|MODULE_ENV_X_LO|", SHELL_X_LO - KEY_TAB_L));
  echo(str("ICD-CONTRACT|MODULE_ENV_X_HI|", SEAT_X + LINER + COLLAR_LIP_BACK));
  echo(str("ICD-CONTRACT|MODULE_ENV_Y_LO|", SHELL_FOOT_Y));
  echo(str("ICD-CONTRACT|MODULE_ENV_Y_HI|", SHELL_TOP_Y));
  echo(str("ICD-CONTRACT|MODULE_ENV_Z_LO|", FOOT_Z_LO));
  echo(str("ICD-CONTRACT|MODULE_ENV_Z_HI|", SHELL_Z_HI));
  // —— 承力闭环 ——
  echo(str("ICD-CONTRACT|HARD_STOP_Y|", SHELL_FOOT_Y));
  // MATING.md 第 4.1 节：卡扣保持力要求 ≥30 N（两处各 ≥15）。D-026 后改由 M2 螺钉承担，
  // 数值待触点场心确定后回填；在此之前吐出需求值，供比对底座侧是否给出了实现。
  echo(str("ICD-CONTRACT|RETENTION_N|", 30));
}
icd_contract();
