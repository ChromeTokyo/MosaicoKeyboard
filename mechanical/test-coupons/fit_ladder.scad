// 提案 · 未冻结 · 由 Claude 主控（claude-opus-5）起草 · 待 Chrome 采纳、Hiro／Grok 复核
//
// fit_ladder.scad —— 公差阶梯标定件（一次打印，代替十几轮试错）
//
// 为什么有这个文件：
//   外壳的滑配、卡扣、孔柱、限位高度这几处，靠「打一版→试→改一个数→再打一版」收敛，
//   每轮都是小时级，比 token 额度慢得多，是整个项目真正的节奏瓶颈。
//   本文件把「改一个数再打一次」换成「一次把这个数的一整排值都打出来」：
//   用户打一盘、用卡尺和手感把每一档试一遍，一次就得到全部配合的实测值，
//   之后所有壳体文件只需把量到的数填进参数表，不必再为找配合而反复打印。
//
// 打印设置（必须照做，否则量出来的是切片参数不是打印机能力）：
//   喷嘴 0.4 mm ／ 层高 0.2 mm ／ 壁 3 圈 ／ 填充 ≥ 20 %
//   **水平膨胀（Elephant foot / XY compensation）保持默认，不要为了这盘去调**
//   材料：与最终壳体同一卷（PETG 或 ABS；PLA 只能用来看，不能作数）
//   不加 brim（brim 会改第一层轮廓，影响 A 组高度与 B 组直径）
//
// 量完之后：把结果填进 mechanical/test-coupons/MEASURE.md 的表，回给主控。
// 那张表的数直接决定 module_board.scad 的 DOCK_Y_TOL——而 MATING.md 第 5.3 节已经算出，
// DOCK_Y_TOL 是弹簧针选型能否成立的绑定约束（±0.50 时全行程必须 2.0 mm；
// 压到 ±0.25 则 1.2 mm 行程的常备料就够用）。所以 A 组是这盘里最值钱的一组。

$fn = 64;
LABEL_H   = 0.6;    // 字高（凸起）
LABEL_SZ  = 3.2;    // 字号
GAP       = 6;      // 试件间距

// 在试件顶面刻字
module label(txt, sz = LABEL_SZ) {
    linear_extrude(LABEL_H) text(txt, size = sz, halign = "center", valign = "center");
}

// ====================================================================
// A 组 —— 高度重复性与位置一致性（决定 DOCK_Y_TOL，最要紧的一组）
// ====================================================================
// 五个同样标称 10.00 mm 高的方柱，摆在盘面四角与中心。
// 量五个的实际高度：
//   · 五个的极差 → 打印机在整个盘面上的高度一致性（热床平整度＋首层压扁）
//   · 五个的均值 − 10.00 → 系统性偏差，可以在模型里一次性补偿掉
//   · 极差的一半 = 壳体足底面高度公差，即 MATING.md 第 5.2 节表里那条 ±0.15 的实测替代值
// 顶面刻 A1…A5，**不要**打磨顶面，量的就是打印出来的样子。
A_SIZE = 10;
A_H    = 10.00;
module coupon_A(n) {
    difference() {
        cube([A_SIZE, A_SIZE, A_H], center = true);
        // 底面刻编号会影响首层，改刻在侧面
        translate([0, -A_SIZE/2 + LABEL_H/2, A_H/4])
            rotate([90, 0, 0]) rotate([0, 0, 180]) mirror([1,0,0])
                linear_extrude(LABEL_H + 0.01, center = true)
                    text(str("A", n), size = LABEL_SZ, halign = "center", valign = "center");
    }
}

// ====================================================================
// B 组 —— 小圆柱直径偏差（决定壳体定位柱的标称值）
// ====================================================================
// 模块板定位孔是 PCB 工艺的 Ø2.2 mm（精度高、可信）；壳体侧的柱子是打印件。
// 打六根标称 1.95 / 2.00 / 2.05 / 2.10 / 2.15 / 2.20 的柱，逐根量实际直径，
// 得到本台打印机在 Ø2 附近的偏差曲线，再倒推「要得到实际 Ø2.10 应该画多少」。
// 不做「插进打印孔里试」——打印孔本身不准，那样是拿两个误差互相量。
B_D    = [1.95, 2.00, 2.05, 2.10, 2.15, 2.20];
B_H    = 8;
B_BASE = 4;        // 底座厚，便于拿取和刻字
module coupon_B() {
    n = len(B_D);
    difference() {
        union() {
            cube([n * GAP + 6, 14, B_BASE], center = true);
            for (i = [0 : n - 1])
                translate([(i - (n - 1) / 2) * GAP, 2, B_BASE / 2])
                    cylinder(h = B_H, d = B_D[i]);
        }
        // 序号刻在底座上表面（1..6，对应上面的直径表）
        for (i = [0 : n - 1])
            translate([(i - (n - 1) / 2) * GAP, -4, B_BASE / 2 - LABEL_H])
                linear_extrude(LABEL_H + 0.01)
                    text(str(i + 1), size = 3, halign = "center", valign = "center");
    }
}

// ====================================================================
// C 组 —— 滑配间隙（模块组件落入底座槽）
// ====================================================================
// 六对「轨 + 槽」，槽宽 = 轨宽 + 间隙，间隙 0.10 … 0.35 步进 0.05。
// 试法：手持轨插入槽，来回滑十次。判据依次是
//   ① 能不能徒手插进去（不能 → 太紧）
//   ② 滑动时有没有卡滞（有 → 太紧）
//   ③ 插到底后横向晃动量（晃得出来 → 太松）
// 取「能顺滑滑动且晃动最小」的一档。落入式结构宁可稍松，因为还有卡扣提供保持力。
C_CLR  = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35];
C_RAIL_W = 4;      // 轨宽
C_RAIL_H = 3;      // 轨高
C_LEN    = 18;     // 滑动长度
C_WALL   = 2;
module coupon_C_groove(clr, idx) {
    w = C_RAIL_W + clr;
    h = C_RAIL_H + clr;
    difference() {
        cube([w + 2 * C_WALL, C_LEN, h + C_WALL], center = true);
        translate([0, 0, C_WALL / 2 + 0.01])
            cube([w, C_LEN + 1, h + 0.02], center = true);
        translate([0, -C_LEN / 2 + 3, (h + C_WALL) / 2 - LABEL_H])
            linear_extrude(LABEL_H + 0.01)
                text(str(idx), size = 3, halign = "center", valign = "center");
    }
}
module coupon_C_rail() {
    // 所有档共用同一根轨（轨是基准，只有槽在变），故只打一根、多试几次
    union() {
        cube([C_RAIL_W, C_LEN + 8, C_RAIL_H], center = true);
        translate([0, C_LEN / 2 + 6, 0])
            cube([12, 6, C_RAIL_H], center = true);   // 拿手
    }
}

// ====================================================================
// D 组 —— 卡扣过盈量（Mosaico 落入后的保持力）
// ====================================================================
// 四根悬臂卡爪，过盈 0.20 / 0.30 / 0.40 / 0.50 mm，共用一块被扣板。
// 试法：把被扣板压进每根卡爪，记录
//   ① 有没有「咔」的到位感（没有 → 过盈太小）
//   ② 单手能不能压进去（不能 → 太大）
//   ③ 反复十次后爪根有没有发白／裂（有 → 应力过高，须加厚爪根或改料）
// PETG 与 ABS 的结果会明显不同，务必用最终材料打。
D_INT   = [0.20, 0.30, 0.40, 0.50];
D_ARM_L = 12;      // 悬臂长
D_ARM_T = 1.6;     // 悬臂厚
D_ARM_W = 6;       // 悬臂宽
D_BASE  = 4;
module coupon_D(intf, idx) {
    difference() {
        union() {
            cube([D_ARM_W + 6, 10, D_BASE], center = true);       // 底座
            translate([0, 0, D_BASE / 2])
                cube([D_ARM_W, D_ARM_T, D_ARM_L], center = false, $fn = 8);
        }
        translate([0, -3, D_BASE / 2 - LABEL_H])
            linear_extrude(LABEL_H + 0.01)
                text(str(idx), size = 3, halign = "center", valign = "center");
    }
    // 爪头：过盈量即爪头伸出悬臂内侧面的距离
    translate([0, D_ARM_T, D_BASE / 2 + D_ARM_L - 2])
        rotate([0, 90, 0])
            linear_extrude(D_ARM_W)
                polygon([[0, 0], [-2, 0], [0, -intf - 0.001]]);
}
module coupon_D_catch() {
    // 被扣板：厚 2.0，宽 8，供四根卡爪共用
    union() {
        cube([8, 2.0, 16], center = true);
        translate([0, 0, 10]) cube([16, 2.0, 4], center = true);   // 拿手
    }
}

// ====================================================================
// E 组 —— 壁厚与最小特征（确认 SHELL_MIN_W = 1.2 打得出来）
// ====================================================================
// 五片立壁 0.8 / 1.0 / 1.2 / 1.6 / 2.0，高 12。
// 看：能不能成型、有没有缺层、用手侧向掰是不是一掰就断。
// module_shell.scad 里 SHELL_MIN_W = 1.2 是假设，本组给它一个实测依据。
E_W = [0.8, 1.0, 1.2, 1.6, 2.0];
E_H = 12;
E_L = 16;
module coupon_E() {
    n = len(E_W);
    union() {
        cube([n * GAP + 6, E_L + 6, 3], center = true);
        for (i = [0 : n - 1])
            translate([(i - (n - 1) / 2) * GAP, 0, 1.5])
                cube([E_W[i], E_L, E_H], center = false);
    }
}

// ====================================================================
// F 组 —— M2 热熔螺母柱（2026-09-21 增加，因承力改螺钉而上了关键路径）
// ====================================================================
// 承力方式定为 M2 螺钉之后，螺纹在 PLA-CF 里怎么做就成了新的关键配合。
// PLA-CF 脆，直接自攻很可能开裂，所以主路线是黄铜热熔螺母。
// 但热熔螺母的孔径窗口很窄：孔大了螺母转空、孔小了熔入时把柱子撑裂。
// 六根柱，孔径 2.90 … 3.40 步进 0.10（常见 M2 热熔螺母外径约 3.2，滚花外径略大）。
// 试法：用烙铁把螺母压入每根柱，记录
//   ① 能不能压到齐平（压不动 → 孔太小）
//   ② 柱身有没有胀裂或纵向裂纹（有 → 孔太小或壁太薄）
//   ③ 拧入 M2 螺钉后用手拧到底，螺母会不会跟着转（会转 → 孔太大）
//   ④ 反复拧 5 次后螺母有没有松动
F_HOLE_D = [2.90, 3.00, 3.10, 3.20, 3.30, 3.40];
F_WALL   = 1.60;    // 柱壁厚（ASSUMPTION：足够承受熔入时的径向胀力，本组就是验证它）
F_H      = 7.00;    // 柱高（M2 热熔螺母常见长 3～4，留余量）
F_BASE   = 4;
module coupon_F() {
    n = len(F_HOLE_D);
    difference() {
        union() {
            cube([n * (max(F_HOLE_D) + 2*F_WALL + 3) + 6, 16, F_BASE], center = true);
            for (i = [0 : n - 1])
                translate([(i - (n - 1) / 2) * (max(F_HOLE_D) + 2*F_WALL + 3), 3, F_BASE/2])
                    cylinder(h = F_H, d = F_HOLE_D[i] + 2 * F_WALL);
        }
        for (i = [0 : n - 1]) {
            translate([(i - (n - 1) / 2) * (max(F_HOLE_D) + 2*F_WALL + 3), 3, F_BASE/2 - 0.01])
                cylinder(h = F_H + 0.02, d = F_HOLE_D[i]);
            translate([(i - (n - 1) / 2) * (max(F_HOLE_D) + 2*F_WALL + 3), -4, F_BASE/2 - LABEL_H])
                linear_extrude(LABEL_H + 0.01)
                    text(str(i + 1), size = 3, halign = "center", valign = "center");
        }
    }
}

// ====================================================================
// G 组 —— M2 自攻柱（验证「能不能省掉热熔螺母」）
// ====================================================================
// 如果 PLA-CF 能直接自攻 M2 且反复拧不滑牙，就不用买热熔螺母、不用烙铁工序。
// 这一组就是去判这件事，值一次试。孔径 1.50 / 1.60 / 1.70（M2 自攻常规底孔 1.5～1.7）。
// 试法：直接拧入 M2 螺钉，记录
//   ① 拧入时柱身有没有纵向开裂（PLA-CF 最可能的失效）
//   ② 拧到底的手感（打滑 → 孔太大）
//   ③ **反复拧出拧入 5 次后还夹不夹得住**（这是自攻最容易输的一项）
// 只要有任何一根开裂，自攻路线就否掉，回到 F 组的热熔螺母。
// 2026-09-21 扩充：用户现有 M1.2 / M1.4 / M2 三种螺钉。承力处用 M2，模块壳这类小件
// 用 M1.4（M2 螺柱在壁厚 2.0、最小特征 1.2 的件上占地太大）。两种都要试自攻，
// 因为 M1.4 处载荷小，自攻若成立就完全不需要热熔螺母，只给 M2 承力处买即可。
// 前 3 根 M2（底孔 1.50/1.60/1.70），后 3 根 M1.4（底孔 1.05/1.15/1.25）。
G_HOLE_D  = [1.50, 1.60, 1.70, 1.05, 1.15, 1.25];
G_SCREW   = ["M2", "M2", "M2", "M1.4", "M1.4", "M1.4"];
module coupon_G() {
    n = len(G_HOLE_D);
    difference() {
        union() {
            cube([n * 12 + 6, 16, F_BASE], center = true);
            for (i = [0 : n - 1])
                translate([(i - (n - 1) / 2) * 12, 3, F_BASE/2])
                    cylinder(h = F_H, d = G_HOLE_D[i] + 2 * F_WALL);
        }
        for (i = [0 : n - 1]) {
            translate([(i - (n - 1) / 2) * 12, 3, F_BASE/2 - 0.01])
                cylinder(h = F_H + 0.02, d = G_HOLE_D[i]);
            translate([(i - (n - 1) / 2) * 12, -4, F_BASE/2 - LABEL_H])
                linear_extrude(LABEL_H + 0.01)
                    text(str(i + 1), size = 3, halign = "center", valign = "center");
        }
    }
}

// ====================================================================
// 排布 —— 全部摆在一盘上（约 150 × 120 mm，常见 220 床绰绰有余）
// ====================================================================
// A 组故意摆到四角与中心，就是要测盘面不同位置的差异，不要把它们挪到一起。
PLATE_X = 150;
PLATE_Y = 120;

// A1..A5：四角 + 中心
for (p = [[-PLATE_X/2 + 10, -PLATE_Y/2 + 10, 1],
          [ PLATE_X/2 - 10, -PLATE_Y/2 + 10, 2],
          [ PLATE_X/2 - 10,  PLATE_Y/2 - 10, 3],
          [-PLATE_X/2 + 10,  PLATE_Y/2 - 10, 4],
          [ 0,               0,              5]])
    translate([p[0], p[1], A_H / 2]) coupon_A(p[2]);

// B 组
translate([-35, 40, B_BASE / 2]) coupon_B();

// C 组：六个槽一排，外加一根共用轨
for (i = [0 : len(C_CLR) - 1])
    translate([-45 + i * 16, 18, (C_RAIL_H + C_CLR[i] + C_WALL) / 2])
        coupon_C_groove(C_CLR[i], i + 1);
translate([45, 18, C_RAIL_H / 2]) rotate([0, 0, 90]) coupon_C_rail();

// D 组：四根卡爪一排，外加共用被扣板
for (i = [0 : len(D_INT) - 1])
    translate([-40 + i * 18, -22, D_BASE / 2]) coupon_D(D_INT[i], i + 1);
translate([45, -22, 8]) rotate([90, 0, 0]) coupon_D_catch();

// E 组
translate([-30, -45, 1.5]) coupon_E();

// F 组 热熔螺母柱
translate([-25, 58, F_BASE / 2]) coupon_F();

// G 组 自攻柱
translate([44, 58, F_BASE / 2]) coupon_G();

// ====================================================================
// 自检 echo
// ====================================================================
echo("==== fit_ladder.scad 标定件 ====");
echo(str("A 组 高度重复性：5 件，标称高 ", A_H, " mm，摆位四角＋中心"));
echo(str("B 组 小圆柱直径：", B_D, "（序号 1..", len(B_D), "）"));
echo(str("C 组 滑配间隙：", C_CLR, "（序号 1..", len(C_CLR), "），轨 ",
         C_RAIL_W, " × ", C_RAIL_H, " mm，共用一根"));
echo(str("D 组 卡扣过盈：", D_INT, "（序号 1..", len(D_INT), "），悬臂 ",
         D_ARM_L, " × ", D_ARM_T, " mm，共用一块被扣板"));
echo(str("E 组 壁厚：", E_W, " mm，高 ", E_H));
echo(str("F 组 M2 热熔螺母柱孔径：", F_HOLE_D, "（序号 1..", len(F_HOLE_D),
         "），柱壁 ", F_WALL, " 柱高 ", F_H));
echo(str("G 组 自攻柱：序号 1..", len(G_HOLE_D), "  孔径 ", G_HOLE_D,
         "  对应螺钉 ", G_SCREW));
echo(str("盘面占用约 ", PLATE_X, " × ", PLATE_Y, " mm"));
echo("量完填 MEASURE.md；A 组结果直接决定 DOCK_Y_TOL，进而决定弹簧针全行程要求");
