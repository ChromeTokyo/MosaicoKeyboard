// 提案 · 未冻结 · 由 Claude 主控起草 · 待用户实物试配、Hiro／Grok 复核 · 轨一「先能用」件（D-031）v0.2
//
// extended_baseplate.scad —— 官方 Module Interaction 的加固延伸托盘（带卡扣）
//
// v0.2（2026-09-24）：① 改用官方 3mf 全分辨率底板（用户下载），不再用压缩 GLB；② 坐标改 Z 朝上
//   （Bambu 约定，导入即平躺）；③ 加 Mosaico 卡扣（用户：「缺了固定的装置比如卡扣」）；
//   ④ 加滑入止挡与装配顺序约束，保证排针进 H2 之前 Mosaico 已被三向定位（用户：「小心伤到排针」）。
//
// 做什么：替换官方模块的 3D 打印底板。官方底板全部特征原样保留（import 官方 STL，一个面不改，
//   与官方外壳的卡合面零改动），再加通底托盘 + Mosaico 唇框 + 卡扣。
//   Mosaico 与模块的相对位置由这一块塑料锁死，2×10 排针只走电、不承力。
//
// 装配顺序（**必须**）：托盘朝上 → 官方 PCB 上 4 颗自攻 → 卡外壳 → Mosaico **背面朝下、屏朝上**
//   放进唇框远端（远离模块），落到环形沿上 → 沿 +Y 推向模块直到止挡（此时排针才进 H2，
//   此前 Mosaico 已被 ±X 唇边与环形沿定住 X 与 Z，只剩 Y 向一个自由度，与针轴同向，针不受横向力）
//   → 按下远端边，卡扣扣住屏面边缘。取出反序：先掰开远端卡扣，抬起远端，再沿 −Y 拔离模块。
//
// 坐标（Bambu，Z 朝上）：官方底板中心置于原点，底板 Z[0, 6.44]。排针从底板 −Y 边出去（全分辨率壳的
//   −Y 壁底边有 ~24 mm 出口），Mosaico 放 −Y 侧。**Mosaico 背面与模块背面同在 Z = 0**——官方在桌面
//   上的对齐方式，排针与 H2 高度关系靠它保证；托盘在 Z < 0 把两者一起垫高，不改相对高度。

$fn = 48;

// ===================== 官方底板（不改）=====================
// 全分辨率 STL 在 Bambu 盘上的位置：X[105.23,148.63] Y[132.27,175.89] Z[0,6.44] → 平移到原点
PLATE_SRC_XC = (105.23 + 148.63) / 2;  PLATE_SRC_YC = (132.27 + 175.89) / 2;
PLATE_W = 43.40;  PLATE_D = 43.61;  PLATE_T = 1.9;   // 板厚（Z=1.5→1.9 截面面积骤降）
module official_plate() { translate([-PLATE_SRC_XC, -PLATE_SRC_YC, 0]) import("official_plate_fullres.stl"); }

// ===================== ASSUMPTION 块（到货逐条回填）=====================
// ASSUMPTION: Q1-1 官方外壳 44.90 见方，比底板每侧宽 0.75；排针侧外脸 = 底板 −Y 边 − 0.75
SHELL_FOOT = 44.90;  SHELL_OVERHANG = 0.75;
// ASSUMPTION: Q1-2 模块外脸到 Mosaico +Y 面的间隙（排针插到底时）。照片近乎贴合。到货塞尺量后回填。
GAP = 0.5;
// ASSUMPTION: AS-01 Mosaico 45.19 × 45.19 × 11.48（官方标称，未实测）
MOS_W = 45.19;  MOS_D = 45.19;  MOS_T = 11.48;
// ASSUMPTION: Q1-4 唇边与 Mosaico 单边间隙 0.30（FDM 滑配；标定件 C 组回填）
CLR = 0.30;
// ASSUMPTION: Q1-5 唇边厚 1.5；±X 唇高 4.0（避开侧键/USB-C/顶键，只抓背侧下 4 mm）；−Y 远端唇覆盖全厚（带卡扣）
LIP_T = 1.5;  LIP_H_SIDE = 4.0;
// 远端唇必须高过 Mosaico 屏面（11.48）再加钩子的斜面，否则卡舌悬空（v0.2 首版就犯了这个错）
LIP_H_END = MOS_T + 0.5 + 1.2 + 0.5;   // ≈13.68
// ASSUMPTION: Q1-6 Mosaico ±X 面各有一整条功能面（一面 USB-C+两侧键，另一面顶键+扬声器格栅，3mf 分析），
//   两面唇边中央各留 34 mm 宽缺口，只留两端各 ~5.6 mm 角柱定位。到货核对后可收窄。
SIDE_CUT_W = 34.0;
// ASSUMPTION: Q1-7 卡扣：远端唇顶两个卡舌，宽 8、过盈 0.5、45° 导入；卡舌两侧开 1 mm 缝让它独立弹（PLA 应变 ≈1.1 %）
HOOK_W = 8.0;  HOOK_OVER = 0.5;  HOOK_SLOT = 1.0;  HOOK_LIP_H = 1.2;
// ASSUMPTION: Q1-8 通底托盘厚 2.0（Z ∈ [−BASE_T, 0]）
BASE_T = 2.0;
// ASSUMPTION: Q1-9 Mosaico 背面可能有凸出螺钉头，其下只铺 4 mm 环形沿
RIM_W = 4.0;
// ASSUMPTION: Q1-10 滑入止挡：托盘环形沿在 Mosaico +Y 边处竖一道 1.0 高的挡条，Mosaico 推到它为止 → 定义 GAP，
//   防止过推把排针本体顶死在母座上。
STOP_H = 1.0;  STOP_T = 1.2;

// ===================== 派生量 =====================
MOD_FACE_Y = -PLATE_D / 2 - SHELL_OVERHANG;          // 模块朝 Mosaico 的外脸 Y = −22.56
MOS_Y_MAX  = MOD_FACE_Y - GAP;                       // Mosaico +Y 面
MOS_Y_MIN  = MOS_Y_MAX - MOS_D;
MOS_YC     = (MOS_Y_MIN + MOS_Y_MAX) / 2;
IN_W  = MOS_W + 2 * CLR;   IN_D  = MOS_D + 2 * CLR;
OUT_W = IN_W + 2 * LIP_T;  OUT_D = IN_D + 2 * LIP_T;
HOOK_Z = MOS_T;                                      // 卡舌钩底面 = Mosaico 屏面高度（背面在 Z=0）

// ===================== 几何 =====================
// 通底托盘：模块区按外壳脚印满铺 ＋ 间隙区 ＋ Mosaico 区环形沿
module base_tray() {
  translate([0, 0, -BASE_T]) {
    hull() {
      translate([0, 0, BASE_T / 2]) cube([SHELL_FOOT, SHELL_FOOT, BASE_T], center = true);
      translate([0, MOS_Y_MAX + CLR + LIP_T / 2, BASE_T / 2]) cube([OUT_W, LIP_T, BASE_T], center = true);
    }
    difference() {
      translate([0, MOS_YC, BASE_T / 2]) cube([OUT_W, OUT_D, BASE_T], center = true);
      translate([0, MOS_YC, BASE_T / 2]) cube([IN_W - 2 * RIM_W, IN_D - 2 * RIM_W, BASE_T + 0.1], center = true);
    }
  }
}

// ±X 侧唇（低，带大缺口 → 实际只剩两端角柱）
module side_lips() {
  for (sx = [-1, 1])
    difference() {
      translate([sx * (IN_W / 2 + LIP_T / 2), MOS_YC, LIP_H_SIDE / 2]) cube([LIP_T, OUT_D, LIP_H_SIDE], center = true);
      translate([sx * (IN_W / 2 + LIP_T / 2), MOS_YC, LIP_H_SIDE / 2]) cube([LIP_T + 0.2, SIDE_CUT_W, LIP_H_SIDE + 0.2], center = true);
    }
}

// −Y 远端唇（高）＋ 两个卡舌
module end_lip_with_hooks() {
  y = MOS_Y_MIN - CLR - LIP_T / 2;
  difference() {
    translate([0, y, LIP_H_END / 2]) cube([OUT_W, LIP_T, LIP_H_END], center = true);
    // 卡舌两侧开缝，让卡舌独立弹
    for (sx = [-1, 1]) for (side = [-1, 1])
      translate([sx * OUT_W / 4 + side * (HOOK_W / 2 + HOOK_SLOT / 2), y, (LIP_H_END + 2.0) / 2 + 0.1])
        cube([HOOK_SLOT, LIP_T + 0.2, LIP_H_END - 2.0 + 0.2], center = true);
  }
  // 卡舌钩：搭在唇内侧面 y0 上，向 +Y 伸出 HOOK_OVER；底面平（Z = 屏面高），上面斜（导入）。
  // 用 hull 拼两块薄片成楔形，坐标全部绝对值，不用 rotate 猜方向。
  y0 = MOS_Y_MIN - CLR;
  for (sx = [-1, 1])
    hull() {
      translate([sx * OUT_W / 4 - HOOK_W / 2, y0 - 0.01, HOOK_Z]) cube([HOOK_W, HOOK_OVER + 0.01, 0.01]);                       // 底边：伸出最远
      translate([sx * OUT_W / 4 - HOOK_W / 2, y0 - 0.01, HOOK_Z + HOOK_OVER + HOOK_LIP_H]) cube([HOOK_W, 0.01, 0.01]);           // 顶边：缩回唇面
      translate([sx * OUT_W / 4 - HOOK_W / 2, y0 - LIP_T, HOOK_Z]) cube([HOOK_W, LIP_T, HOOK_OVER + HOOK_LIP_H]);              // 与唇体融合
    }
}

// 滑入止挡：Mosaico +Y 边处的挡条（在环形沿上，排针跨距之外才有，中间让开针）
module stop_ribs() {
  for (sx = [-1, 1])
    translate([sx * (IN_W / 2 - RIM_W / 2), MOS_Y_MAX + CLR + STOP_T / 2, STOP_H / 2])
      cube([RIM_W, STOP_T, STOP_H], center = true);
}

union() { official_plate(); base_tray(); side_lips(); end_lip_with_hooks(); stop_ribs(); }

// ===================== 自检 =====================
echo(str("v0.2 托盘（Z 朝上）：Mosaico 位 Y[", MOS_Y_MIN, ",", MOS_Y_MAX, "]  X 中心 0  背面 Z=0  屏面 Z=", MOS_T));
echo(str("模块外脸 Y = ", MOD_FACE_Y, "  GAP = ", GAP, "（到货塞尺回填）；止挡在 Y = ", MOS_Y_MAX + CLR, "，高 ", STOP_H));
echo(str("卡舌：2 个，宽 ", HOOK_W, "，过盈 ", HOOK_OVER, "，钩底 Z = ", HOOK_Z, "；卡舌应变 ≈ ",
         3 * LIP_T * HOOK_OVER / (2 * LIP_H_END * LIP_H_END) * 100, " %（PLA 反复许用 ≈1.65 %）",
         (3 * LIP_T * HOOK_OVER / (2 * LIP_H_END * LIP_H_END) * 100 < 1.65) ? "  -> OK" : "  -> FAIL"));
echo(str("±X 唇高 ", LIP_H_SIDE, "，中央缺口 ", SIDE_CUT_W, "，两端角柱各 ", (OUT_D - SIDE_CUT_W) / 2));
echo(str("整件包围盒 X ±", OUT_W / 2, "  Y[", MOS_Y_MIN - CLR - LIP_T, ",", SHELL_FOOT / 2, "] = ",
         SHELL_FOOT / 2 - (MOS_Y_MIN - CLR - LIP_T), " 长  Z[", -BASE_T, ",", max(LIP_H_END, HOOK_Z + HOOK_OVER + HOOK_LIP_H), "]"));
echo("装配顺序：Mosaico 先放进远端落到环形沿 → 沿 +Y 推到止挡（此时才进排针）→ 按下远端扣住。取出反序。");
