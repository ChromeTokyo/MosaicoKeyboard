// 提案 · 未冻结 · 由 Claude 主控起草 · 待用户实物试配、Hiro／Grok 复核 · 轨一「先能用」件（D-031）v0.2
//
// extended_baseplate.scad —— 官方 Module Interaction 的加固延伸托盘 v0.3
//
// v0.3（2026-09-24）：用户三问——「靱这两个卡扣吗？Mosaico 上有给你卡住的位置吗？两侧边缘会不会高出 Mosaico 影响手感？」
//   答：v0.2 的钩子搭在屏面边缘上，而 Mosaico 边缘轮廓（圆角？玻璃到边？有无侧槽？）未知，等于拿钩子压玻璃边；
//   远端唇 13.7 高出屏面 2.2 mm 正压在拇指那条边上。两条都不行。
//   v0.3 改为 **RETAIN 三选一**，默认 "bar"：
//     "bar"    远端唇降到 11.0（低于屏面 0.48），两端立柱带 M2 底孔；另打一根 6 mm 宽压条，两颗 M2 螺钉压在远端，
//              压条内侧一道 0.8 mm 薄唇搭在 Mosaico 前缘上。不依赖 Mosaico 任何边缘特征；压条顶面只高出屏面 0.5 mm，
//              且只在远端 6 mm 一条。Mosaico 被压平在环形沿上，近端靠排针 + 止挡，整体不能绕远端翘起（会撬针）。
//     "tongue" 到货确认 Mosaico 的 H1 侧面有与官方模块榫舌配合的槽后启用：远端唇内侧长一条榫舌（默认按官方模块槽
//              29.6 × 1.5 @ Z≈7.3 反推）——这是乐鑫自己用的定位方式，零压屏。装法为远端先斜着挂进槽再放平再推排针。
//     "hook"   v0.2 的钩子，保留供对比，**不推荐**。
//   ±X 角柱保持 4.0，远低于屏面，手感无影响。
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

// ===== 远端保持方式 =====
RETAIN = "bar";           // "bar" | "tongue" | "hook"
PART   = "both";          // "tray" | "bar" | "both"（bar 模式下另打压条）

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
LIP_H_END = (RETAIN == "hook") ? MOS_T + 0.5 + 1.2 + 0.5 : MOS_T - 1.08;   // bar/tongue：10.4，低于屏面
POST_H = LIP_H_END;                                                             // 立柱与远端唇齐平，压条平放其上
BAR_Z  = POST_H;                                                                // 压条底面
// ASSUMPTION: Q1-6 Mosaico ±X 面各有一整条功能面（一面 USB-C+两侧键，另一面顶键+扬声器格栅，3mf 分析），
//   两面唇边中央各留 34 mm 宽缺口，只留两端各 ~5.6 mm 角柱定位。到货核对后可收窄。
SIDE_CUT_W = 34.0;
// ASSUMPTION: Q1-7 "hook" 模式（v0.2，不推荐）：卡舌宽 8、过盈 0.5、两侧开缝
HOOK_W = 8.0;  HOOK_OVER = 0.5;  HOOK_SLOT = 1.0;  HOOK_LIP_H = 1.2;
// ASSUMPTION: Q1-11 "bar" 模式：远端两根立柱 6 × 6 通高到 POST_H，M2 底孔 Ø1.7（PLA 自攻，载荷只有几牛）；
//   压条 6 宽 × 2 厚，跨整个远端，内侧薄唇 0.8 厚、向 Mosaico 方向搭 BAR_OVER；螺钉过孔 Ø2.3
POST_W = 6.0;  BAR_T = 1.6;  BAR_OVER = 0.8;  BAR_HOLE_D = 2.3;  POST_HOLE_D = 1.7;   // 立柱在唇**外侧**，不进 Mosaico 脚印
// ASSUMPTION: Q1-12 "tongue" 模式：官方模块榫舌 29.6 × 1.5，位于厚度方向 ≈7.3（GLB 与 3mf 一致）。
//   假设 Mosaico 侧面有对应的槽 → 远端唇内侧长同尺寸榫舌。**到货看见槽再启用，否则别用。**
TONGUE_W = 29.6;  TONGUE_T = 1.4;  TONGUE_D = 1.0;  TONGUE_Z = 7.3;
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
Y_LIP_OUT = MOS_Y_MIN - CLR - LIP_T;                 // 远端唇外表面 Y
Y_POST_OUT = Y_LIP_OUT - ((RETAIN == "bar") ? POST_W : 0);   // bar 模式：托盘再向外延 POST_W 放立柱

// ===================== 几何 =====================
// 通底托盘：模块区按外壳脚印满铺 ＋ 间隙区 ＋ Mosaico 区环形沿
module base_tray() {
  translate([0, 0, -BASE_T]) {
    hull() {
      translate([0, 0, BASE_T / 2]) cube([SHELL_FOOT, SHELL_FOOT, BASE_T], center = true);
      translate([0, MOS_Y_MAX + CLR + LIP_T / 2, BASE_T / 2]) cube([OUT_W, LIP_T, BASE_T], center = true);
    }
    difference() {
      translate([0, (MOS_Y_MAX + CLR + LIP_T + Y_POST_OUT) / 2, BASE_T / 2]) cube([OUT_W, (MOS_Y_MAX + CLR + LIP_T) - Y_POST_OUT, BASE_T], center = true);
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

// −Y 远端：按 RETAIN 三选一
module end_lip_with_hooks() {
  y = MOS_Y_MIN - CLR - LIP_T / 2;  y0 = MOS_Y_MIN - CLR;
  difference() {
    translate([0, y, LIP_H_END / 2]) cube([OUT_W, LIP_T, LIP_H_END], center = true);
    if (RETAIN == "hook")
      for (sx = [-1, 1]) for (side = [-1, 1])
        translate([sx * OUT_W / 4 + side * (HOOK_W / 2 + HOOK_SLOT / 2), y, (LIP_H_END + 2.0) / 2 + 0.1])
          cube([HOOK_SLOT, LIP_T + 0.2, LIP_H_END - 2.0 + 0.2], center = true);
  }
  if (RETAIN == "hook")
    for (sx = [-1, 1])
      hull() {
        translate([sx * OUT_W / 4 - HOOK_W / 2, y0 - 0.01, HOOK_Z]) cube([HOOK_W, HOOK_OVER + 0.01, 0.01]);
        translate([sx * OUT_W / 4 - HOOK_W / 2, y0 - 0.01, HOOK_Z + HOOK_OVER + HOOK_LIP_H]) cube([HOOK_W, 0.01, 0.01]);
        translate([sx * OUT_W / 4 - HOOK_W / 2, y0 - LIP_T, HOOK_Z]) cube([HOOK_W, LIP_T, HOOK_OVER + HOOK_LIP_H]);
      }
  if (RETAIN == "bar")
    // 两根立柱在远端唇**外侧**两角（不进 Mosaico 脚印），从托盘底通高到 POST_H，顶面 M2 底孔
    for (sx = [-1, 1])
      difference() {
        translate([sx * (OUT_W / 2 - POST_W / 2), (Y_POST_OUT + Y_LIP_OUT) / 2, (POST_H - BASE_T) / 2]) cube([POST_W, POST_W, POST_H + BASE_T], center = true);
        translate([sx * (OUT_W / 2 - POST_W / 2), (Y_POST_OUT + Y_LIP_OUT) / 2, POST_H - 6.0]) cylinder(d = POST_HOLE_D, h = 6.1);
      }
  if (RETAIN == "tongue")
    // 榫舌：从远端唇内侧面向 +Y 伸 TONGUE_D，上面 45° 导入
    hull() {
      translate([-TONGUE_W / 2, y0 - 0.01, TONGUE_Z - TONGUE_T / 2]) cube([TONGUE_W, TONGUE_D + 0.01, TONGUE_T]);
      translate([-TONGUE_W / 2, y0 - 0.01, TONGUE_Z + TONGUE_T / 2]) cube([TONGUE_W, 0.01, TONGUE_D]);
    }
}

// 压条（独立打印件，RETAIN=="bar"）：本体压在两立柱与远端唇顶上（Y 从立柱外侧到唇内侧面，**不盖到 Mosaico 上方**）；
// 薄唇从唇内侧面向 Mosaico 方向探出 BAR_OVER，只存在于屏面 MOS_T 以上——搭在前缘上把 Mosaico 压平。
module end_bar() {
  y_in = MOS_Y_MIN - CLR;                                        // 唇内侧面 = Mosaico 面 − CLR
  difference() {
    union() {
      translate([0, (Y_POST_OUT + y_in) / 2, BAR_Z + BAR_T / 2]) cube([OUT_W, y_in - Y_POST_OUT, BAR_T], center = true);
      translate([0, y_in + BAR_OVER / 2 - 0.01, (MOS_T + BAR_Z + BAR_T) / 2]) cube([IN_W - 2.0, BAR_OVER + 0.02, BAR_Z + BAR_T - MOS_T], center = true);
    }
    for (sx = [-1, 1])
      translate([sx * (OUT_W / 2 - POST_W / 2), (Y_POST_OUT + Y_LIP_OUT) / 2, BAR_Z - 0.1]) cylinder(d = BAR_HOLE_D, h = BAR_T + 0.2);
  }
}

// 滑入止挡：Mosaico +Y 边处的挡条（在环形沿上，排针跨距之外才有，中间让开针）
module stop_ribs() {
  for (sx = [-1, 1])
    translate([sx * (IN_W / 2 - RIM_W / 2), MOS_Y_MAX + CLR + STOP_T / 2, STOP_H / 2])
      cube([RIM_W, STOP_T, STOP_H], center = true);
}

if (PART == "tray" || PART == "both") union() { official_plate(); base_tray(); side_lips(); end_lip_with_hooks(); stop_ribs(); }
if (RETAIN == "bar" && (PART == "bar" || PART == "both"))
  // 压条：both 模式下平放在托盘旁边一起打；bar 模式单独导出
  translate([0, (PART == "both") ? -30 : 0, (PART == "both") ? -BAR_Z : 0]) end_bar();

// ===================== 自检 =====================
echo(str("v0.3 托盘（Z 朝上）：Mosaico 位 Y[", MOS_Y_MIN, ",", MOS_Y_MAX, "]  X 中心 0  背面 Z=0  屏面 Z=", MOS_T));
echo(str("模块外脸 Y = ", MOD_FACE_Y, "  GAP = ", GAP, "（到货塞尺回填）；止挡在 Y = ", MOS_Y_MAX + CLR, "，高 ", STOP_H));
echo(str("保持方式 RETAIN = ", RETAIN, "；远端唇高 ", LIP_H_END, "（屏面 ", MOS_T, "，", (LIP_H_END <= MOS_T) ? "低于屏面 -> OK" : "高于屏面 -> 手感注意", "）"));
if (RETAIN == "bar") echo(str("压条：顶面 Z = ", BAR_Z + BAR_T, "（高出屏面 ", BAR_Z + BAR_T - MOS_T, "）；薄唇厚 ", BAR_Z + BAR_T - MOS_T, " 探出 ", BAR_OVER, "；立柱在唇外侧 Y[", Y_POST_OUT, ",", Y_LIP_OUT, "]，不进 Mosaico 脚印 -> OK；M2 ×2 底孔 Ø", POST_HOLE_D));
if (RETAIN == "tongue") echo(str("榫舌：", TONGUE_W, " × ", TONGUE_T, "，伸出 ", TONGUE_D, "，Z = ", TONGUE_Z, "——**到货确认 Mosaico 有槽再用**"));
echo(str("±X 唇高 ", LIP_H_SIDE, "，中央缺口 ", SIDE_CUT_W, "，两端角柱各 ", (OUT_D - SIDE_CUT_W) / 2));
echo(str("整件包围盒 X ±", OUT_W / 2, "  Y[", Y_POST_OUT, ",", SHELL_FOOT / 2, "] = ", SHELL_FOOT / 2 - Y_POST_OUT, " 长  Z[", -BASE_T, ",", (RETAIN == "hook") ? HOOK_Z + HOOK_OVER + HOOK_LIP_H : LIP_H_END, "]（压条另计 +", BAR_T, "）"));
echo("装配顺序：Mosaico 先放进远端落到环形沿 → 沿 +Y 推到止挡（此时才进排针）→ 压条对孔拧 2 颗 M2。取出反序：先拆压条。");
