// 提案 · 未冻结 · 由 Claude 主控（claude-opus-5）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
//
// keycaps.scad —— 十字帽、ABXY 圆帽、L/R 条帽（可直接打印）
// 分支 claude/design-d/mech-dock，目录 mechanical/dock-shell/
//
// 坐标系同 hardware/ICD-0.2-DRAFT.md 第 1 节。本文件用 include 借用
// dock_shell.scad 的参数块，**不另抄一份尺寸**：改一处即两处同步。
//
// 用法：
//   openscad -D 'CAP="dpad"'  -o cap_dpad.stl  keycaps.scad
//   CAP 取值：all / dpad / abxy / lr / plate（plate = 全部摆平供一次打印）

include <dock_shell.scad>
PART = "none";   // 覆盖 dock_shell.scad 的顶层分发：只借参数，不渲染外壳

/* =====================================================================
   [ASSUMPTION 参数块]（键帽专有；共用尺寸见 dock_shell.scad）
   ===================================================================== */
// ASSUMPTION: AS-31-mechdock-19 6x6x4.3 轻触开关，柱头 Ø3.5、行程 0.25 mm、
//   操作力 160～260 gf。到货验证：dock-board 选型定型后按数据手册回填（AS-27）。
// ASSUMPTION: AS-31-mechdock-22 顶推柱端面直径 4.5（> 柱头 3.5，压柱头不压壳体）
POST_D        = 4.50;
POST_REST_GAP = 0.00;   // 静止时顶推柱端面贴柱头顶面
// ASSUMPTION: AS-31-mechdock-23 十字帽中央支点球径 5.0，支在主板 D-pad 区中心无器件铜面
//   → 要求 dock-board 在 D-pad 中心留 Ø8 净空、不布器件、不开窗（本文对 dock-board 的唯一机械请求之一）
PIVOT_D       = 5.00;
PIVOT_CLEAR_D = 8.00;
DPAD_HUB_D    = 7.00;
// ASSUMPTION: AS-31-mechdock-24 键帽材料 PETG／ABS，FDM 层高 0.15、喷嘴 0.4
CAP_FN        = 48;
CAP_DOME_R    = 26.00;  // ABXY 帽面球冠半径（手感用，非功能）
ANTIROT_W     = 1.60;   // 防转筋宽
ANTIROT_L     = 1.20;   // 防转筋伸出长

CAP = "all";
$fa = 3;
$fs = 0.35;

/* =====================================================================
   派生量（与外壳同源，不重复定义数值）
   ===================================================================== */
CAP_TOP_Z    = Z_FRONT_OUT + CAP_PROUD;          // 帽面顶 Z = +9.24
FRONT_IN_Z   = Z_FRONT_OUT - WALL;               // 前壁内表面 Z = +5.74
FLANGE_TOP_Z = FRONT_IN_Z;                       // 静止位：法兰顶贴前壁内表面
FLANGE_BOT_Z = FRONT_IN_Z - CAP_FLANGE_T;        // = +4.74
POCKET_BOT_Z = FRONT_IN_Z - CAP_POCKET_T;        // = +4.24
STOP_TRAVEL  = CAP_POCKET_T - CAP_FLANGE_T;      // 限位行程 0.50

assert(STOP_TRAVEL > SW_TRAVEL,
       "限位行程必须大于轻触开关行程，否则限位先到、键按不动");
assert(POST_D > SW_ACT_D,
       "顶推柱端面必须大于开关柱头，才不会顶到开关壳体");
echo(str("键帽：帽面顶 Z = ", CAP_TOP_Z, "  法兰 ", FLANGE_BOT_Z, "~", FLANGE_TOP_Z,
         "  限位行程 ", STOP_TRAVEL, "  开关柱头顶面 Z = ", SW_ACT_Z));

/* =====================================================================
   通用件
   ===================================================================== */

// 顶推柱：从法兰底面伸到开关柱头顶面
module push_post(d = POST_D) {
  translate([0, 0, SW_ACT_Z + POST_REST_GAP])
    cylinder(d = d, h = FLANGE_BOT_Z - SW_ACT_Z - POST_REST_GAP, $fn = 32);
  // 端面倒角（打印时是顶面，不需支撑）
  translate([0, 0, SW_ACT_Z + POST_REST_GAP])
    cylinder(d1 = d - 0.8, d2 = d, h = 0.4, $fn = 32);
}

// 法兰：帽体外扩 CAP_FLANGE_MARGIN，厚 CAP_FLANGE_T，位于前壁内侧
module flange_from(profile_margin = 0) {
  translate([0, 0, FLANGE_BOT_Z])
    linear_extrude(height = CAP_FLANGE_T)
      offset(r = CAP_FLANGE_MARGIN - CLR_PRINT + profile_margin) children(0);
}

// 帽体：从法兰顶穿过前壁、露出 CAP_PROUD
module cap_body() {
  translate([0, 0, FLANGE_TOP_Z - 0.01])
    linear_extrude(height = CAP_TOP_Z - FLANGE_TOP_Z + 0.01)
      offset(r = -CLR_PRINT) children(0);
}

// 防转筋：法兰外缘两条小凸，落进导向套的对应槽
module antirot(profile) {
  for (s = [-1, 1])
    translate([0, 0, FLANGE_BOT_Z])
      linear_extrude(height = CAP_FLANGE_T)
        translate([s * (profile + CAP_FLANGE_MARGIN + ANTIROT_L/2 - 0.2), 0])
          square([ANTIROT_L, ANTIROT_W], center = true);
}

/* =====================================================================
   1) 十字帽（D-pad）
      中央支点：帽底中央 Ø5 半球，支在主板 D-pad 中心的无器件铜面 →
                帽绕中心摇动，四臂各压一颗开关。
      四向限位：法兰四臂端在法兰兜底面 POCKET_BOT_Z 触底，限位行程 0.50 mm；
                任一方向压到底时，对角臂被抬起，不会同时压下相邻两键。
   ===================================================================== */
module cap_dpad() {
  difference() {
    union() {
      // 帽面（露出部分，四臂端略抬起便于拇指找边）
      cap_body() cross_2d(DPAD_ARM_L, DPAD_ARM_W);
      // 法兰（四向限位面）
      flange_from() cross_2d(DPAD_ARM_L, DPAD_ARM_W);
      // 中央轮毂 ＋ 半球支点
      translate([0, 0, PIVOT_D/2 - 0.01])
        cylinder(d = DPAD_HUB_D, h = FLANGE_BOT_Z - PIVOT_D/2 + 0.01, $fn = CAP_FN);
      translate([0, 0, BOARD_Z_FRONT + PIVOT_D/2])
        sphere(d = PIVOT_D, $fn = CAP_FN);
      translate([0, 0, BOARD_Z_FRONT + PIVOT_D/2])
        cylinder(d = PIVOT_D, h = PIVOT_D/2, $fn = CAP_FN);
      // 四个顶推柱（对准四颗开关）
      for (a = [0 : 3])
        translate([DPAD_SW_R*cos(90*a), DPAD_SW_R*sin(90*a), 0]) push_post();
    }
    // 帽面十字压痕（方向指示，非功能）
    translate([0, 0, CAP_TOP_Z - 0.5])
      linear_extrude(height = 1.0) cross_2d(DPAD_ARM_L - 3.0, 1.6, 0.6);
    // 中央浅凹（拇指定位）
    translate([0, 0, CAP_TOP_Z + CAP_DOME_R - 0.6])
      sphere(r = CAP_DOME_R, $fn = 96);
  }
}

/* =====================================================================
   2) ABXY 圆帽
   ===================================================================== */
module cap_round(label_notch = false) {
  difference() {
    union() {
      cap_body() circle(d = ABXY_D, $fn = CAP_FN);
      flange_from() circle(d = ABXY_D, $fn = CAP_FN);
      antirot(ABXY_D/2);
      push_post();
      // 轮毂：法兰底到顶推柱，避免细长柱
      translate([0, 0, FLANGE_BOT_Z - 2.2])
        cylinder(d1 = POST_D + 1.2, d2 = ABXY_D - 2.0, h = 2.2, $fn = CAP_FN);
    }
    // 帽面球冠（手感）
    translate([0, 0, CAP_TOP_Z + CAP_DOME_R - 0.45])
      sphere(r = CAP_DOME_R, $fn = 96);
    if (label_notch)
      translate([0, -ABXY_D/2 + 0.8, CAP_TOP_Z - 0.4])
        cylinder(d = 1.2, h = 1.0, $fn = 16);
  }
}

/* =====================================================================
   3) L/R 条帽
      帽面做前低后高的楔形：食指从机身顶部弯下来时先碰到后缘。
   ===================================================================== */
module cap_lr() {
  difference() {
    union() {
      // 楔形帽面
      hull() {
        translate([0, -LR_BAR_H/2 + 1.2, FLANGE_TOP_Z])
          linear_extrude(height = CAP_TOP_Z - 0.7 - FLANGE_TOP_Z)
            offset(r = -CLR_PRINT) bar_2d(LR_BAR_W, 2.4);
        translate([0, LR_BAR_H/2 - 1.2, FLANGE_TOP_Z])
          linear_extrude(height = CAP_TOP_Z + 1.0 - FLANGE_TOP_Z)
            offset(r = -CLR_PRINT) bar_2d(LR_BAR_W, 2.4);
      }
      flange_from() bar_2d(LR_BAR_W, LR_BAR_H);
      antirot(LR_BAR_W/2);
      push_post();
      translate([0, 0, FLANGE_BOT_Z - 2.2])
        cylinder(d1 = POST_D + 1.2, d2 = LR_BAR_H - 1.6, h = 2.2, $fn = CAP_FN);
    }
    // 顶面防滑槽
    for (i = [-2 : 2])
      translate([i * 3.4, 0, CAP_TOP_Z - 0.2])
        rotate([0, 0, 90]) cube([LR_BAR_H + 2, 0.9, 1.6], center = true);
  }
}

/* =====================================================================
   摆平供打印（帽面朝下贴平台，法兰悬空 1.5 mm 可直接桥接，不需支撑）
   ===================================================================== */
module lay_flat(x, y) {
  translate([x, y, 0]) rotate([180, 0, 0]) translate([0, 0, -CAP_TOP_Z]) children();
}

module print_plate() {
  lay_flat(0, 0)    cap_dpad();
  for (i = [0 : 3])
    lay_flat(34 + (i % 2) * 16, (floor(i / 2)) * 16 - 8) cap_round(i == 0);
  lay_flat(-32,  10) cap_lr();
  lay_flat(-32, -10) cap_lr();
}

/* ---------- 顶层分发 ---------- */
if (CAP == "all") {
  cap_dpad();
  translate([ABXY_X - DPAD_X, 0, 0])
    for (a = [0 : 3])
      translate([ABXY_R*cos(90*a), ABXY_R*sin(90*a), 0]) cap_round(a == 3);
  for (s = [-1, 1]) translate([s * (LR_X - abs(DPAD_X)), LR_Y - DPAD_Y, 0]) cap_lr();
} else if (CAP == "dpad") {
  cap_dpad();
} else if (CAP == "abxy") {
  cap_round(false);
} else if (CAP == "lr") {
  cap_lr();
} else if (CAP == "plate") {
  print_plate();
} else {
  assert(false, "CAP 取值须为 all/dpad/abxy/lr/plate");
}
