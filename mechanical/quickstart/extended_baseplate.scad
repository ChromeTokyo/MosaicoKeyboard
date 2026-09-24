// 提案 · 未冻结 · 由 Claude 主控起草 · 待用户实物试配、Hiro／Grok 复核 · 轨一「先能用」件（D-031）
//
// extended_baseplate.scad —— 官方 Module Interaction 的加固延伸托盘
//
// 做什么：替换官方模块的 3D 打印底板。官方底板全部特征原样保留（直接 import 官方 GLB 导出的 STL，
//   与官方外壳的卡合面一个面都不改），再加一块通底托盘把 Mosaico 也定位住：
//   Mosaico 与模块的相对位置由这一块塑料锁死，2×10 排针只走电、不承力。
//   官方原设计里模块是悬空挂在排针上的——这正是要改掉的。
//
// 不做什么：不改 Mosaico、不改官方 PCB、不改官方外壳。
//
// 坐标：沿用官方 GLB 打印盘坐标。Y = 厚度方向（向上）。官方底板背面在 Y = 0，
//   占 X[-22.77, 20.63]  Y[0, 6.44]  Z[-47.89, -4.27]。排针从底板 +X 边出去（与外壳敞开侧一致），
//   Mosaico 放 +X 侧。**Mosaico 背面与模块背面同在 Y = 0**——官方在桌面上摆放时的对齐方式，
//   排针与 H2 的高度关系靠它保证；托盘在 Y < 0，把两者一起垫高，不改相对高度。

$fn = 48;

// ===================== 官方底板（不改）=====================
PLATE_X_MIN = -22.77;  PLATE_X_MAX = 20.63;
PLATE_Z_MIN = -47.89;  PLATE_Z_MAX = -4.27;
PLATE_XC = (PLATE_X_MIN + PLATE_X_MAX) / 2;
PLATE_ZC = (PLATE_Z_MIN + PLATE_Z_MAX) / 2;         // −26.08

// ===================== ASSUMPTION 块（到货逐条回填）=====================
// ASSUMPTION: Q1-1 官方外壳 44.90 见方，比底板 43.40 每侧宽 0.75；敞开侧外脸 = 底板 X_MAX + 0.75
SHELL_FOOT = 44.90;  SHELL_OVERHANG = 0.75;
// ASSUMPTION: Q1-2 模块外脸到 Mosaico −X 面的间隙。照片近乎贴合。到货塞尺量后回填。
GAP = 0.5;
// ASSUMPTION: AS-01 Mosaico 45.19 × 45.19 × 11.48（官方标称，未实测）
MOS_W = 45.19;  MOS_H = 45.19;  MOS_T = 11.48;
// ASSUMPTION: Q1-3 Mosaico 与模块 Z 向同心（排针居中于模块边、H2 居中于 Mosaico 边，3mf 分析 y≈0）
MOS_ZC = PLATE_ZC;
// ASSUMPTION: Q1-4 唇边与 Mosaico 单边间隙 0.30（FDM 滑配；标定件 C 组回填）
CLR = 0.30;
// ASSUMPTION: Q1-5 唇边高 4.0、厚 1.5——只抓 Mosaico 背侧下 4 mm，避开屏幕与侧键
LIP_H = 4.0;  LIP_T = 1.5;
// ASSUMPTION: Q1-6 USB-C 在 Mosaico 某一 ±Z 面居中，开口宽 9.14（3mf）。两个 ±Z 面都留 14 mm 缺口，
//   到货确认是哪一面后关掉另一面的缺口。
USB_CUT_W = 14.0;
// ASSUMPTION: Q1-7 2×10 排针沿 Z 半跨 11.43 + 半针宽 0.32 = 11.75；−X 面回折只在 |dz| > HDR_HALF_SPAN 之外
HDR_HALF_SPAN = 13.0;
// ASSUMPTION: Q1-8 通底托盘厚 2.0，位于 Y ∈ [−BASE_T, 0]，是整件刚性的来源
BASE_T = 2.0;
// ASSUMPTION: Q1-9 Mosaico 背面可能有凸出螺钉头（3mf 未给），故其下只铺 4 mm 宽环形沿，中央开空
RIM_W = 4.0;

// ===================== 派生量 =====================
MOD_FACE_X = PLATE_X_MAX + SHELL_OVERHANG;          // 模块朝 Mosaico 的外脸 X = 21.38
MOS_X_MIN  = MOD_FACE_X + GAP;
MOS_X_MAX  = MOS_X_MIN + MOS_W;
MOS_XC     = (MOS_X_MIN + MOS_X_MAX) / 2;
IN_W  = MOS_W + 2 * CLR;   IN_H  = MOS_H + 2 * CLR;
OUT_W = IN_W + 2 * LIP_T;  OUT_H = IN_H + 2 * LIP_T;

// ===================== 几何 =====================
module official_plate() { import("official_plate_bottom.stl"); }

// 通底托盘：模块区按外壳脚印满铺（外壳四壁落在托盘上）＋ 间隙区满铺 ＋ Mosaico 区环形沿
module base_tray() {
  translate([0, -BASE_T, 0]) {
    hull() {
      translate([PLATE_XC, BASE_T / 2, PLATE_ZC]) cube([SHELL_FOOT, BASE_T, SHELL_FOOT], center = true);
      translate([MOS_X_MIN - CLR - LIP_T / 2, BASE_T / 2, MOS_ZC]) cube([LIP_T, BASE_T, OUT_H], center = true);
    }
    difference() {
      translate([MOS_XC, BASE_T / 2, MOS_ZC]) cube([OUT_W, BASE_T, OUT_H], center = true);
      translate([MOS_XC, BASE_T / 2, MOS_ZC]) cube([IN_W - 2 * RIM_W, BASE_T + 0.1, IN_H - 2 * RIM_W], center = true);
    }
  }
}

// U 形唇边：+X 面全长；±Z 面全长各带 USB-C 缺口；朝模块的 −X 面在排针跨距内敞开、跨距外回折
module lips() {
  difference() {
    translate([MOS_XC, LIP_H / 2, MOS_ZC]) cube([OUT_W, LIP_H, OUT_H], center = true);
    translate([MOS_XC - LIP_T, LIP_H / 2 + 0.01, MOS_ZC]) cube([IN_W + 2 * LIP_T, LIP_H + 0.1, IN_H], center = true);
    for (sz = [-1, 1])
      translate([MOS_XC, LIP_H / 2 + 0.01, MOS_ZC + sz * (IN_H / 2 + LIP_T / 2)])
        cube([USB_CUT_W, LIP_H + 0.1, LIP_T + 0.2], center = true);
  }
  for (sz = [-1, 1]) {
    z_in  = MOS_ZC + sz * (HDR_HALF_SPAN + 1.0);
    z_out = MOS_ZC + sz * (IN_H / 2 + LIP_T);
    translate([MOS_X_MIN - CLR - LIP_T, 0, min(z_in, z_out)]) cube([LIP_T, LIP_H, abs(z_out - z_in)]);
  }
}

union() { official_plate(); base_tray(); lips(); }

// ===================== 自检 =====================
echo(str("轨一托盘：Mosaico 位 X[", MOS_X_MIN, ",", MOS_X_MAX, "]  Z 中心 ", MOS_ZC,
         "  唇框外形 ", OUT_W, " x ", OUT_H, "  唇高 ", LIP_H));
echo(str("模块外脸 X = ", MOD_FACE_X, "  间隙 GAP = ", GAP, "（到货塞尺回填）"));
echo(str("−X 面回折起点 |dz| = ", HDR_HALF_SPAN + 1.0, "，须 > 排针半跨 11.75",
         (HDR_HALF_SPAN + 1.0 > 11.75) ? "  -> OK" : "  -> FAIL"));
echo(str("托盘 Y[", -BASE_T, ",0]；模块区满铺 ", SHELL_FOOT, " 见方；Mosaico 区环形沿宽 ", RIM_W));
echo(str("整件包围盒 X[", PLATE_XC - SHELL_FOOT / 2, ",", MOS_X_MAX + CLR + LIP_T, "] = ",
         MOS_X_MAX + CLR + LIP_T - (PLATE_XC - SHELL_FOOT / 2), " mm 长，Z 宽 ", OUT_H, "，总高 ", BASE_T + 6.44));
echo("Mosaico 背面与模块背面同在 Y=0；Mosaico 下方不得铺满底，否则排针与 H2 高度错位。");
