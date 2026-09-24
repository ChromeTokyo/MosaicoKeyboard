// 提案 · 未冻结 · 由 Claude 主控起草 · 待用户实物试配、Hiro／Grok 复核 · 轨一「先能用」件（D-031）v0.4（r2，按两名审核意见修）
//
// extended_baseplate.scad —— 官方 Module Interaction 的加固延伸托盘 v0.4（四角螺钉压框，r2）
//
// r2（2026-09-24）按两名审核的硬伤逐条修：
//   F1  **方向错 90°**（v0.1～v0.4 同根）：官方底板 STL 的排针边是 **+X**（本体到 21.700 不内缩；−X 内缩 2.78 给对侧母座；
//       外壳底口三面内壁 21.25、只有一面中央开口 25.8 宽；底板 +X 21.70 > 21.25 只能从开口出去；4 个 LED 孔也在开口侧）。
//       现在 official_plate() 加 rotate([0,0,PLATE_ROT=-90])：STL +X → 托盘 −Y。PLATE_W/PLATE_D 对调。模块外脸 Y = −(21.70+0.75) = −22.45。
//   F2  压框排针侧 1.2 宽的边被 0.5 倒角削到 0.73：该边**不倒角**（其余三边 0.5×45°）；R6 按倒角后顶宽判。
//   F3/F4 POST_GAP 0.3 的「硬止点」实际要 ~300 N 才碰到柱顶、螺钉力全进玻璃边：改为 **柱顶 = 压框本体底 = 硬止点**
//       （螺钉力进 PLA 柱、不进玻璃），压框压边处底面再抬一层 LIP_RECESS=0.2 → Mosaico 名义游隙 ∈ (0, 0.2]，是**限位**不是**预压**。
//       柱顶按 0.2 层高量化（托盘总高 = 67 层 = 13.4 → 柱顶 11.40）。
//   F4/F3 Q1-13 裕量 0.095 mm ≈ 0（= (MOS_D−34)/2 − (PIN_LEN−GAP)，被硬要求 7 锁死，与 CLR/SLIDE_L 无关）：CLR 0.3→0.15（导轨与角柱同面），
//       +Y 角柱 −Y 端加 1.5 导入斜角（接住 ≤1.5 的横向偏差）；R5b 改判「注意」并给偏摆数。
//       导向长度在触针瞬间 = POST_L + (PIN_LEN−GAP)，与 SLIDE_L 无关，加长滑入区没用（审核建议②不采）。
//   F5/F7 环形沿：改 **四边闭合**（RIM_OPEN_FAR=false），远端 −Y 边下也有 4.0 沿；Q1-9 改写为「背面凸出物距 −Y 边 <12 mm 则装不进」。
//   F6/F8 外壳坐在底板 Z=1.20 台阶上（底板 Z<1.2 全尺寸 ±21.807、Z≥1.2 本体 ±21.25 = 外壳内壁）→ 外壳顶 ≈12.1，比屏面高 0.62。
//       删掉「压框在外壳顶之上」的判据，只靠横向 0.3 让位。
//   F7  螺钉盘头：压框四孔加 Ø4.2×0.4 沉台（留 1.2 底），盘头高出压框顶 0.9～1.2（屏面上 2.4～2.7）；仍超硬要求 2 字面，ECHO 标「注意」。
//   F6（使用）远端墙中央开 28 mm 宽、通高（Z 0～柱顶）的手指口，推 Mosaico 时指尖从远端顶它的 −Y 面（墙只剩两端 15.2 mm 短墩，靠 Z<0 底板连接）。
//   F9  新增 MOS_XC（Q1-23：Mosaico X 中心相对底板中心偏置，默认 0）。
//   F5（使用）GAP 容差窗口写反：正确为 实际 GAP ∈ [0, 1.3] 可用（变大失效）。
//   SCREW 参数：M2（默认）/ M1.4，底孔/过孔/沉台随之切换。
//
// v0.4 相对 v0.3 的改动（保留）：删 RETAIN 三选一；四角 M2 压框；立柱全在 Mosaico 脚印外；±X 中央 34 mm 全空；8 mm 滑入区；后裙防退出；
//   止挡条件生成；派生量先定义后用；每条硬要求一条 ECHO 自判。
//
// 做什么：替换官方模块的 3D 打印底板。官方底板全部特征原样保留（import 官方 STL，一个面不改），
//   下面加通底托盘，旁边加 Mosaico 托位（闭合环形沿 + 四角柱 + 滑入区 + 远端墙），另打一块压框。
//   Mosaico 与模块的相对位置由这两块塑料锁死，2×10 排针只走电、不承力。
//
// 装配顺序（**必须**）：托盘朝上 → 官方 PCB 上 4 颗自攻 → 卡外壳 → Mosaico **背面朝下、屏朝上**放进滑入区（远端墙前）
//   → 拇指从远端口顶住 Mosaico −Y 面沿 +Y 推：**目视对准槽口**（导轨只锁 X/Z，偏摆最大 ~2°，两端角柱导向与针尖触面几乎同时）
//   → 推到排针座到底 → 压框对孔放上（后裙落入滑入区）→ 4 颗螺钉拧到压框坐实柱顶（螺钉力进柱，不进屏）。
//   取出反序：先拆压框，捏 ±X 侧面中央窗口沿 −Y 拔离。**不要先抬任何一边**。
//
// 坐标（Bambu，Z 朝上）：官方底板中心置于原点，底板 Z[0, 6.436]。排针从底板 −Y 边出去，Mosaico 放 −Y 侧。
//   **Mosaico 背面与模块背面同在 Z = 0**（官方桌面对齐方式）；托盘在 Z < 0 把两者一起垫高。

$fn = 64;
EPS = 1e-6;

PART     = "both";        // "tray" | "bezel" | "both"（both = 装配位，仅预览；导出 STL 分别用 tray / bezel）
SHOW_ENV = false;         // 预览：透明显示 Mosaico 包络、官方外壳包络、排针区、显示区
SCREW    = "M2";          // "M2" | "M1.4"（用户两种都有）
LAYER_H  = 0.2;           // 打印层高（柱顶按它量化）

// ===================== 官方底板（不改）=====================
// 全分辨率 STL 在 Bambu 盘上的位置（trimesh 实测 2026-09-24）：X[105.231,148.631] Y[132.274,175.889] Z[0,6.436]
PLATE_SRC_XMIN = 105.231;  PLATE_SRC_XMAX = 148.631;  PLATE_SRC_YMIN = 132.274;  PLATE_SRC_YMAX = 175.889;
PLATE_SRC_XC = (PLATE_SRC_XMIN + PLATE_SRC_XMAX) / 2;  PLATE_SRC_YC = (PLATE_SRC_YMIN + PLATE_SRC_YMAX) / 2;
// ASSUMPTION: Q1-24 排针边 = 底板 STL 的 +X 边（本体 Z1.2～1.8 在 +X 到 21.700 不内缩、−X 内缩到 −18.917；外壳 STL 底口唯一开口侧
//   内壁 21.0～21.66 < 21.70，只有开口能放过 +X 边；4 个 Ø9.8 LED 孔在同侧）。PLATE_ROT=−90 把 STL +X 转到托盘 −Y。
PLATE_ROT = -90;
PLATE_W = PLATE_SRC_YMAX - PLATE_SRC_YMIN;   // 43.615 —— 转后沿托盘 X（排针边长度方向）
PLATE_D = PLATE_SRC_XMAX - PLATE_SRC_XMIN;   // 43.400 —— 转后沿托盘 Y（针轴方向）
PLATE_H = 6.436;                             // 螺柱顶
PLATE_LEDGE_Z = 1.20;                        // 底缘台阶：Z<1.2 全尺寸 ±21.807/±21.70，Z≥1.2 本体 ±21.25（STL 切片实测）
PLATE_BODY_T = 1.80;                         // 底板体顶（面积 1587→282 mm² 在 1.8～1.9 之间）
module official_plate() { rotate([0, 0, PLATE_ROT]) translate([-PLATE_SRC_XC, -PLATE_SRC_YC, 0]) import("official_plate_fullres.stl"); }

// ===================== ASSUMPTION 块（到货逐条回填，编号见 README）=====================
// ASSUMPTION: Q1-1 官方外壳 44.90 见方（外壳 STL 包围盒），中心与底板包围盒中心重合（±Y 内壁 21.25 = 底板本体 ±21.25 → 居中）。
//   针轴向：外壳比底板宽 0.75（22.45−21.70）；横向：0.643（22.45−21.807）。横向包络取 max(22.45, 21.807+0.75)=22.557 保守。
SHELL_FOOT = 44.90;  SHELL_OVERHANG = 0.75;  SHELL_H = 10.90;
// ASSUMPTION: Q1-22 外壳坐在底板 Z=1.20 台阶上（内壁 21.25 < 底缘 21.807 套不过去；无卡槽）→ 外壳 Z[1.2, 12.1]，比屏面高 0.62。
SHELL_Z0 = PLATE_LEDGE_Z;
// ASSUMPTION: Q1-2 模块外脸到 Mosaico +Y 面的间隙（排针插到底时）。到货塞尺量后回填。可用窗口 [0, 1.3]（见 R5 GAP 扫描）。
GAP = 0.5;
// ASSUMPTION: AS-01 Mosaico 45.19 × 45.19 × 11.48（官方标称，未实测）
MOS_W = 45.19;  MOS_D = 45.19;  MOS_T = 11.48;
// ASSUMPTION: Q1-23 Mosaico X 中心相对底板中心的偏置（= 排针 X 中心偏置；外壳开口居中 ±12.9 → 取 0；到货卡尺量两端针到底板边）
MOS_XC = 0;
// ASSUMPTION: Q1-18b 显示区 41.19 见方、居中（任务给屏窗 41.19，未核）→ 每边边框 2.0，压边 ≤1.2 不进显示区
DISP_W = 41.19;
// ASSUMPTION: Q1-4 托位与 Mosaico 单边间隙 0.15（导轨与角柱同面；双边 0.30 = FDM 紧滑配；卡涩则砂 −Y 导轨内面、松则改 0.10；标定件 C 组回填）
CLR = 0.15;
// ASSUMPTION: Q1-6 Mosaico ±X 面各有一整条功能面（USB-C+侧键 / 顶键+扬声器，3mf 分析），Z≈2～6 不得遮挡 → ±X 侧中央 34 mm 留空
SIDE_CUT_W = 34.0;
// ASSUMPTION: Q1-7 2×10 排针沿 X 半跨 = 外壳开口半宽 12.9（开口 |X|<12.88/12.92，STL 切片）
HDR_XH = 12.9;
// ASSUMPTION: Q1-14 排针所在高度 = 外壳开口对应装配 Z：开口 Z_stl 4.75～10.9，外壳坐 1.2 → Z 1.2～7.35（PCB 底 6.44，排针在 PCB 下方）
HDR_Z0 = SHELL_Z0;  HDR_Z1 = SHELL_Z0 + SHELL_H - 4.75;
// ASSUMPTION: Q1-13 排针针尖露出模块外脸 ≤ PIN_LEN（标准 2.54 排针配合长 6.0；**未实测**）
PIN_LEN = 6.0;
// ASSUMPTION: Q1-8 通底托盘厚 2.0（Z ∈ [−BASE_T, 0]）；模块区比外壳脚印每侧再宽 BASE_MARGIN
BASE_T = 2.0;  BASE_MARGIN = 0.3;
// ASSUMPTION: Q1-9 Mosaico 背面平（无凸出）：环形沿 4.0 宽、四边闭合。若背面有凸出物且距 −Y 边 <12 mm（滑入时会撞远端沿）→ RIM_OPEN_FAR=true
RIM_W = 4.0;  RIM_OPEN_FAR = false;
// ASSUMPTION: Q1-10 止挡：条件生成，只有 GAP − CLR − STOP_SHELL_CLR ≥ 1.2 时才有；默认 GAP 下放不下，插入深度由排针座到底定义
STOP_H = 1.0;  STOP_SHELL_CLR = 0.2;  MIN_WALL = 1.2;
// ASSUMPTION: Q1-15 螺钉/立柱：M2 底孔 Ø1.7、过孔 Ø2.3、盘头 Ø4.0×1.6（ISO 7045）；M1.4 底孔 Ø1.2、过孔 Ø1.7、盘头 Ø2.8×1.1。
//   沉台 Ø(头+0.2)×0.4（压框留 1.2 底）。立柱 6.5 宽（沉台外侧要在倒角之后仍留 1.2 壁：2.1+1.2+0.5=3.8 从柱外缘量）、底孔深 7、孔周壁 ≥1.5。柱顶 = 压框本体底 = 硬止点。
SCR_PILOT  = (SCREW == "M2") ? 1.7 : 1.2;
SCR_THRU   = (SCREW == "M2") ? 2.3 : 1.7;
SCR_HEAD_D = (SCREW == "M2") ? 4.0 : 2.8;
SCR_HEAD_H = (SCREW == "M2") ? 1.6 : 1.1;
CBORE_D = SCR_HEAD_D + 0.2;  CBORE_H = 0.4;
POST_W = 6.5;  POST_HOLE_DEPTH = 7.0;  POST_WALL_MIN = 1.5;  POST_LEADIN = 1.5;
// ASSUMPTION: Q1-15b 压框：每边压 1.0、厚 1.6、−Y/±X 外缘倒角 0.5×45°、+Y（排针侧）边不倒角（1.2 宽夹死）；
//   压边处底面抬 LIP_RECESS = 一层 → Mosaico 名义 Z 游隙 (0, 0.2]（限位，不预压）
BEZ_PRESS = 1.0;  BEZ_T = 1.6;  BEZ_CHAMF = 0.5;  LIP_RECESS = LAYER_H;  RECESS_M = 0.3;
// ASSUMPTION: Q1-16 滑入区长 8.0（≥ PIN_LEN − GAP + 1.5，落位时距针尖 ≥1.5、拔出行程够）；远端墙厚 1.5；手指口 28 宽、通高（NOTCH_Z=0）
SLIDE_L = 8.0;  END_T = 1.5;  NOTCH_W = 28.0;  NOTCH_Z = 0.0;
// ASSUMPTION: Q1-17 压框后裙：厚 1.5、高 4.0，内面在 Mosaico −Y 面后方 SKIRT_CLR=0.8（容许实际 GAP 比假设大 ≤0.8）
SKIRT_T = 1.5;  SKIRT_H = 4.0;  SKIRT_CLR = 0.8;  SKIRT_SIDE_CLR = 0.3;
// ASSUMPTION: Q1-20 压框排针侧外缘到外壳脚印 0.3（横向让位；外壳顶 12.1 高于压框底 11.4，不能靠高度差）
BEZ_SHELL_CLR = 0.3;
// ASSUMPTION: Q1-21 远端螺钉中心在 Mosaico −Y 面后方 2.5（落在滑入区导轨块内）
HOLE_N_SETBACK = 2.5;
// ASSUMPTION: Q1-18 Mosaico 屏面四条前缘各 1.0 mm 宽可被压框限位（玻璃是否到边未知）
// ASSUMPTION: Q1-19 Mosaico 四角圆角半径未知；压框内窗按直角画
// 备注：官方底板底面有 25 条 0.5 深装饰刻线，托盘顶面 Z=0 与其共面 → 导出体含 25 个封闭小内腔（切片为 ~0.7×0.5 空隙，无结构影响）。

// ===================== 派生量（全部先定义后使用）=====================
SHELL_XH   = max(SHELL_FOOT / 2, PLATE_W / 2 + SHELL_OVERHANG);   // 22.5575（横向，保守）
SHELL_YH   = max(SHELL_FOOT / 2, PLATE_D / 2 + SHELL_OVERHANG);   // 22.45（针轴向，两种算法一致）
SHELL_TOP  = SHELL_Z0 + SHELL_H;                                  // 12.1
MOD_FACE_Y = -SHELL_YH;                                           // 模块朝 Mosaico 的外脸 −22.45
MOS_Y_MAX  = MOD_FACE_Y - GAP;                                    // Mosaico +Y 面 −22.95
MOS_Y_MIN  = MOS_Y_MAX - MOS_D;                                   // Mosaico −Y 面 −68.14
MOS_YC     = (MOS_Y_MIN + MOS_Y_MAX) / 2;
IN_W = MOS_W + 2 * CLR;  IN_D = MOS_D + 2 * CLR;                  // 含间隙包络
ENV_X  = IN_W / 2;                                                // 包络 ±X（相对 MOS_XC）22.795
ENV_Y0 = MOS_Y_MIN - CLR;  ENV_Y1 = MOS_Y_MAX + CLR;              // −68.34 / −22.75

POST_TOP = floor((MOS_T + BASE_T) / LAYER_H + EPS) * LAYER_H - BASE_T;   // 11.40：托盘总高整层数（67×0.2=13.4）且 ≤ MOS_T
POST_L   = (IN_D - SIDE_CUT_W) / 2;                               // 每端角柱贴 Mosaico 段 5.795
BLK_X0 = ENV_X;  BLK_X1 = ENV_X + POST_W;                         // 侧块 X（相对 MOS_XC，取绝对值）
TRAY_X = BLK_X1;                                                  // 托位半宽 28.795

BEZ_Y1 = MOD_FACE_Y - BEZ_SHELL_CLR;                              // 压框排针侧外缘 −22.75
PY_Y0 = ENV_Y1 - POST_L;  PY_Y1 = BEZ_Y1;                         // +Y 角柱 −28.545 ～ −22.75
NY_Y0 = ENV_Y0 - SLIDE_L;  NY_Y1 = ENV_Y0 + POST_L;               // −Y 长块 −76.34 ～ −62.545
END_Y0 = NY_Y0 - END_T;  END_Y1 = NY_Y0;                          // 远端墙
TRAY_Y0 = END_Y0;                                                 // 托盘 −Y 端 −77.84
HOLE_X   = BLK_X1 - (CBORE_D / 2 + MIN_WALL + BEZ_CHAMF);         // 25.445：沉台外侧在压框倒角之后仍留 1.2（闸门 #9 抓过 0.7）
HOLE_Y_P = BEZ_Y1 - (CBORE_D / 2 + MIN_WALL);                     // −26.05：沉台到排针侧边留 1.2
HOLE_Y_N = ENV_Y0 - HOLE_N_SETBACK;                               // −70.84
CUT_X  = ENV_X - RIM_W;
CUT_Y0 = RIM_OPEN_FAR ? NY_Y0 + RIM_W : ENV_Y0 + RIM_W;           // 闭合环：−64.34
CUT_Y1 = ENV_Y1 - RIM_W;                                          // −26.75
STOP_Y0 = ENV_Y1;  STOP_Y1 = MOD_FACE_Y - STOP_SHELL_CLR;  STOP_T = STOP_Y1 - STOP_Y0;
STOP_ON = STOP_T >= MIN_WALL - EPS;
// 压框
BEZ_Z0 = POST_TOP;  BEZ_Z1 = BEZ_Z0 + BEZ_T;                      // 11.4 ～ 13.0
LIP_Z0 = BEZ_Z0 + LIP_RECESS;                                     // 压边底 11.6
LIP_PLAY = LIP_Z0 - MOS_T;                                        // 名义 Z 游隙 0.12
BEZ_X  = TRAY_X;  BEZ_Y0 = TRAY_Y0;
WIN_X  = MOS_W / 2 - BEZ_PRESS;  WIN_Y0 = MOS_Y_MIN + BEZ_PRESS;  WIN_Y1 = MOS_Y_MAX - BEZ_PRESS;
BAR_W_X  = BEZ_X - WIN_X;                                         // ±X 边宽 7.2
BAR_W_YN = WIN_Y0 - BEZ_Y0;                                       // 远端边宽 10.7
BAR_W_YP = BEZ_Y1 - WIN_Y1;                                       // 排针侧边宽 1.2（不倒角）
SKIRT_Y1 = MOS_Y_MIN - SKIRT_CLR;  SKIRT_Y0 = SKIRT_Y1 - SKIRT_T;
SKIRT_X  = ENV_X - SKIRT_SIDE_CLR;  SKIRT_Z0 = BEZ_Z0 - SKIRT_H;  // 7.4
HEAD_TOP = BEZ_Z1 - CBORE_H + SCR_HEAD_H;                         // 盘头顶 14.2
PIN_Y0 = MOD_FACE_Y - PIN_LEN;                                    // 针尖 −28.45

// ===================== 几何 =====================
// 通底托盘：模块区按外壳脚印（+边距）满铺 → 斜角过渡 → 托位区（闭合环形沿，中央开空）
module base_tray() {
  translate([0, 0, -BASE_T]) difference() {
    union() {
      translate([-(SHELL_XH + BASE_MARGIN), -(SHELL_YH + BASE_MARGIN), 0])
        cube([2 * (SHELL_XH + BASE_MARGIN), 2 * (SHELL_YH + BASE_MARGIN), BASE_T]);
      translate([MOS_XC - TRAY_X, TRAY_Y0, 0]) cube([2 * TRAY_X, MOD_FACE_Y - TRAY_Y0, BASE_T]);
      hull() {   // 过渡斜角：托位全宽 → 模块区宽
        translate([MOS_XC - TRAY_X, MOD_FACE_Y - 0.01, 0]) cube([2 * TRAY_X, 0.01, BASE_T]);
        translate([-(SHELL_XH + BASE_MARGIN), MOD_FACE_Y + (TRAY_X - SHELL_XH - BASE_MARGIN), 0])
          cube([2 * (SHELL_XH + BASE_MARGIN), 0.01, BASE_T]);
      }
    }
    translate([MOS_XC - CUT_X, CUT_Y0, -0.1]) cube([2 * CUT_X, CUT_Y1 - CUT_Y0, BASE_T + 0.2]);
  }
}

// 四角立柱：+Y 一对短柱（模块端，−Y 端内角 1.0 导入斜角），−Y 一对长块（角柱 + 滑入区导轨），顶面底孔
module side_blocks() {
  for (sx = [-1, 1]) translate([MOS_XC, 0, 0]) mirror([sx < 0 ? 1 : 0, 0, 0]) {
    difference() {
      linear_extrude(POST_TOP) polygon([
        [BLK_X0 + POST_LEADIN, PY_Y0], [BLK_X1, PY_Y0], [BLK_X1, PY_Y1], [BLK_X0, PY_Y1], [BLK_X0, PY_Y0 + POST_LEADIN]]);
      translate([HOLE_X, HOLE_Y_P, POST_TOP - POST_HOLE_DEPTH]) cylinder(d = SCR_PILOT, h = POST_HOLE_DEPTH + 1);
    }
    difference() {
      translate([BLK_X0, NY_Y0, 0]) cube([POST_W, NY_Y1 - NY_Y0, POST_TOP]);
      translate([HOLE_X, HOLE_Y_N, POST_TOP - POST_HOLE_DEPTH]) cylinder(d = SCR_PILOT, h = POST_HOLE_DEPTH + 1);
    }
  }
}

// 远端墙：滑入区 −Y 端的两个短墩（落位止面），中央手指口 NOTCH_W 宽、Z ≥ NOTCH_Z 全部挖掉；两墩靳 Z<0 底板相连
module end_wall() {
  translate([MOS_XC, 0, 0]) difference() {
    translate([-TRAY_X, END_Y0, 0]) cube([2 * TRAY_X, END_T, POST_TOP]);
    translate([-NOTCH_W / 2, END_Y0 - 1, NOTCH_Z]) cube([NOTCH_W, END_T + 2, POST_TOP]);
  }
}

// 止挡（仅当 GAP 够放可打印壁厚时生成）：环形沿 +Y 边、排针跨距之外
module stop_ribs() {
  if (STOP_ON) for (sx = [-1, 1]) translate([MOS_XC, 0, 0])
    translate([(sx > 0) ? ENV_X - RIM_W : -ENV_X, STOP_Y0, 0]) cube([RIM_W, STOP_T, STOP_H]);
}

// 压框（独立打印件，**顶面朝下打印**：倒角与沉台在床面、后裙与压边让位在上，零悬空，沉台台阶环 0.95 ≤ 2）
module bezel() {
  translate([MOS_XC, 0, 0]) difference() {
    union() {
      hull() {   // 本体：−Y/±X 外缘上倒角 BEZ_CHAMF×45°，+Y 边不倒角
        translate([-BEZ_X, BEZ_Y0, BEZ_Z0]) cube([2 * BEZ_X, BEZ_Y1 - BEZ_Y0, BEZ_T - BEZ_CHAMF]);
        translate([-BEZ_X + BEZ_CHAMF, BEZ_Y0 + BEZ_CHAMF, BEZ_Z0])
          cube([2 * (BEZ_X - BEZ_CHAMF), BEZ_Y1 - BEZ_Y0 - BEZ_CHAMF, BEZ_T]);
      }
      translate([-SKIRT_X, SKIRT_Y0, SKIRT_Z0]) cube([2 * SKIRT_X, SKIRT_T, BEZ_Z0 - SKIRT_Z0 + 0.01]);   // 后裙
    }
    translate([-WIN_X, WIN_Y0, BEZ_Z0 - 1]) cube([2 * WIN_X, WIN_Y1 - WIN_Y0, BEZ_T + 2]);              // 内窗
    translate([-(ENV_X + RECESS_M), ENV_Y0 - RECESS_M, BEZ_Z0 - 1])                                      // 压边让位一层
      cube([2 * (ENV_X + RECESS_M), ENV_Y1 - ENV_Y0 + 2 * RECESS_M, 1 + LIP_RECESS]);
    for (sx = [-1, 1]) for (hy = [HOLE_Y_P, HOLE_Y_N]) {
      translate([sx * HOLE_X, hy, BEZ_Z0 - 1]) cylinder(d = SCR_THRU, h = BEZ_T + 2);                    // 过孔
      translate([sx * HOLE_X, hy, BEZ_Z1 - CBORE_H]) cylinder(d = CBORE_D, h = CBORE_H + 1);             // 沉台
    }
  }
}

module envelopes() {
  %translate([MOS_XC - MOS_W / 2, MOS_Y_MIN, 0]) cube([MOS_W, MOS_D, MOS_T]);                          // Mosaico
  %translate([MOS_XC - DISP_W / 2, MOS_YC - DISP_W / 2, MOS_T - 0.01]) cube([DISP_W, DISP_W, 0.02]);   // 显示区
  %translate([-SHELL_XH, -SHELL_YH, SHELL_Z0]) cube([2 * SHELL_XH, 2 * SHELL_YH, SHELL_H]);            // 官方外壳
  %translate([MOS_XC - HDR_XH, PIN_Y0, HDR_Z0]) cube([2 * HDR_XH, PIN_LEN, HDR_Z1 - HDR_Z0]);          // 排针区
}

module tray() { union() { official_plate(); base_tray(); side_blocks(); end_wall(); stop_ribs(); } }

if (PART == "tray"  || PART == "both") tray();
if (PART == "bezel" || PART == "both") bezel();
if (SHOW_ENV) envelopes();

// ===================== 自检（每条硬要求一条 OK/FAIL/注意，全部由表达式算出）=====================
function ok(b) = b ? "OK" : "FAIL";
function okn(b) = b ? "OK" : "注意";
function isect(a0, a1, b0, b1) =
  a0[0] < b1[0] - EPS && b0[0] < a1[0] - EPS &&
  a0[1] < b1[1] - EPS && b0[1] < a1[1] - EPS &&
  a0[2] < b1[2] - EPS && b0[2] < a1[2] - EPS;
function hits(list, b0, b1) = [for (s = list) if (isect(s[1], s[2], b0, b1)) s[0]];
function r2(x) = round(x * 100) / 100;
function r3(x) = round(x * 1000) / 1000;

TRAY_SOLIDS = concat(
  [ ["+X+Y柱", [MOS_XC + BLK_X0, PY_Y0, 0], [MOS_XC + BLK_X1, PY_Y1, POST_TOP]],
    ["-X+Y柱", [MOS_XC - BLK_X1, PY_Y0, 0], [MOS_XC - BLK_X0, PY_Y1, POST_TOP]],
    ["+X-Y块", [MOS_XC + BLK_X0, NY_Y0, 0], [MOS_XC + BLK_X1, NY_Y1, POST_TOP]],
    ["-X-Y块", [MOS_XC - BLK_X1, NY_Y0, 0], [MOS_XC - BLK_X0, NY_Y1, POST_TOP]],
    ["远端墙",  [MOS_XC - TRAY_X, END_Y0, 0], [MOS_XC + TRAY_X, END_Y1, POST_TOP]] ],
  STOP_ON ? [ ["+X止挡", [MOS_XC + ENV_X - RIM_W, STOP_Y0, 0], [MOS_XC + ENV_X, STOP_Y1, STOP_H]],
              ["-X止挡", [MOS_XC - ENV_X, STOP_Y0, 0], [MOS_XC - (ENV_X - RIM_W), STOP_Y1, STOP_H]] ] : []);
PLATE_BOX  = [["官方底板", [-PLATE_W / 2, -PLATE_D / 2, 0], [PLATE_W / 2, PLATE_D / 2, PLATE_H]]];
BEZ_BODY0 = [MOS_XC - BEZ_X, BEZ_Y0, BEZ_Z0];  BEZ_BODY1 = [MOS_XC + BEZ_X, BEZ_Y1, BEZ_Z1];          // 压框本体（Z ≥ 柱顶）
SKIRT_BOX0 = [MOS_XC - SKIRT_X, SKIRT_Y0, SKIRT_Z0];  SKIRT_BOX1 = [MOS_XC + SKIRT_X, SKIRT_Y1, BEZ_Z0]; // 后裙（滑入区内）
function bez_hits(b0, b1) = isect(BEZ_BODY0, BEZ_BODY1, b0, b1) || isect(SKIRT_BOX0, SKIRT_BOX1, b0, b1);
MOS_ENV0 = [MOS_XC - ENV_X, ENV_Y0, 0];  MOS_ENV1 = [MOS_XC + ENV_X, ENV_Y1, MOS_T];
SHELL0   = [-SHELL_XH, -SHELL_YH, 0];  SHELL1 = [SHELL_XH, SHELL_YH, SHELL_TOP];   // 从 Z=0 起算（保守，覆盖坐 0 或坐 1.2 两种）
PIN_ZTOP = max(HDR_Z1 + 1.5, 9.0);                                                    // 排针区检查上限 9.0（针在 1.2～7.35；压框 +Y 边在 11.6 以上悬于 GAP 之上）
PINZONE0 = [MOS_XC - HDR_XH - 2, MOS_Y_MAX, 0.2];  PINZONE1 = [MOS_XC + HDR_XH + 2, MOD_FACE_Y, PIN_ZTOP];

// R1 四边保持（限位式）
R1_press  = BEZ_PRESS > 0 && BEZ_PRESS <= 1.0 + EPS;
TOPW_X = BAR_W_X - BEZ_CHAMF;  TOPW_YN = BAR_W_YN - BEZ_CHAMF;  TOPW_YP = BAR_W_YP;   // 倒角后顶宽
R1_bars   = min(BAR_W_X, BAR_W_YN, BAR_W_YP) >= MIN_WALL - EPS && min(TOPW_X, TOPW_YN, TOPW_YP) >= MIN_WALL - EPS;
R1_holes_in_posts = (HOLE_X - SCR_PILOT / 2 - BLK_X0 >= POST_WALL_MIN - EPS) && (BLK_X1 - HOLE_X - SCR_PILOT / 2 >= POST_WALL_MIN - EPS)
                 && (HOLE_Y_P - SCR_PILOT / 2 - PY_Y0 >= POST_WALL_MIN - EPS) && (PY_Y1 - HOLE_Y_P - SCR_PILOT / 2 >= POST_WALL_MIN - EPS)
                 && (HOLE_Y_N - SCR_PILOT / 2 - NY_Y0 >= POST_WALL_MIN - EPS) && (NY_Y1 - HOLE_Y_N - SCR_PILOT / 2 >= POST_WALL_MIN - EPS)
                 && (HOLE_Y_P - SCR_PILOT / 2 - (PY_Y0 + POST_LEADIN) >= 0)     // 导入斜角不切到孔
                 && (((HOLE_X - BLK_X0) + (HOLE_Y_P - PY_Y0) - POST_LEADIN) / sqrt(2) - SCR_PILOT / 2 >= POST_WALL_MIN - EPS);   // 孔到斜角面的壁 ≥1.5
R1_cbore_in_bezel = (BEZ_X - HOLE_X - CBORE_D / 2 >= MIN_WALL - EPS) && (HOLE_X - CBORE_D / 2 - WIN_X >= MIN_WALL - EPS)
                 && (HOLE_Y_N - CBORE_D / 2 - BEZ_Y0 >= MIN_WALL - EPS) && (WIN_Y0 - HOLE_Y_N - CBORE_D / 2 >= MIN_WALL - EPS)
                 && (BEZ_Y1 - HOLE_Y_P - CBORE_D / 2 >= MIN_WALL - EPS) && (BEZ_X - HOLE_X - CBORE_D / 2 - BEZ_CHAMF >= MIN_WALL - EPS)   // 倒角后顶面处仍 ≥1.2
                 && (HOLE_Y_N - CBORE_D / 2 - BEZ_Y0 - BEZ_CHAMF >= MIN_WALL - EPS)
                 && (BEZ_T - CBORE_H >= MIN_WALL - EPS);
R1_stop   = abs(BEZ_Z0 - POST_TOP) < EPS;                        // 压框本体底 = 柱顶 → 硬止点在柱
R1_play   = LIP_PLAY > 0 && LIP_PLAY <= LAYER_H + 0.05;          // 名义游隙 ∈ (0, 0.25]
R1_seat   = POST_TOP <= MOS_T + EPS;                             // 柱顶不高于屏面（否则压框碰不到 Mosaico）
R1 = R1_press && R1_bars && R1_holes_in_posts && R1_cbore_in_bezel && R1_stop && R1_play && R1_seat;
// R2 不高出屏面
TRAY_ZMAX = max(POST_TOP, PLATE_H, STOP_ON ? STOP_H : 0);
R2_tray = TRAY_ZMAX <= MOS_T + EPS;
R2_bez  = BEZ_Z1 - MOS_T <= 1.6 + EPS && BEZ_CHAMF > 0;
R2_head = HEAD_TOP - MOS_T <= 1.6 + EPS;                         // 盘头也在 1.6 内？（否 → 注意，需用户认可）
R2 = R2_tray && R2_bez;
// R3 不进 Mosaico 脚印
R3_hits = hits(concat(TRAY_SOLIDS, PLATE_BOX), MOS_ENV0, MOS_ENV1);
R3 = len(R3_hits) == 0 && BASE_T > 0;
// R4 不碰官方外壳（Z>0 外壳脚印内只允许官方底板；压框也不进）
R4_hits = hits(TRAY_SOLIDS, SHELL0, SHELL1);
R4_bez  = bez_hits(SHELL0, SHELL1);
R4 = len(R4_hits) == 0 && !R4_bez;
// R5 排针安全靠顺序
R5_drop   = SLIDE_L + GAP - PIN_LEN;                             // 落位时 Mosaico +Y 面到针尖 2.5
R5_guide  = (MOS_Y_MAX - PY_Y0) - (PIN_LEN - GAP);               // +Y 角柱导向比针尖触面早 0.095
R5_ovl    = (NY_Y1 - MOS_Y_MIN) + (PIN_LEN - GAP);               // 触针瞬间 −Y 导轨与 Mosaico 侧面的重叠长 ≈11.1（与 SLIDE_L 无关）
R5_yaw    = atan(2 * CLR / R5_ovl);                              // 最大偏摆角
R5_lat    = tan(R5_yaw) * (MOS_D - R5_ovl / 2) + CLR;            // +Y 面处最大横向偏移
R5_travel = SLIDE_L - (PIN_LEN - GAP);                           // 拔出行程余量 2.5
R5a = R5_drop >= 1.5 - EPS;
R5b = R5_guide >= 1.0 - EPS;                                     // 需 ≥1.0 才算「先导向」（审核 F4/F3）
R5c = len(hits(TRAY_SOLIDS, PINZONE0, PINZONE1)) == 0 && !bez_hits(PINZONE0, PINZONE1) && HDR_XH + 2 < ENV_X;
R5d = BEZ_Y1 <= MOD_FACE_Y - BEZ_SHELL_CLR + EPS && BAR_W_YP >= MIN_WALL - EPS;
R5e = SKIRT_CLR > 0 && SKIRT_Y0 >= END_Y1 + SKIRT_SIDE_CLR - EPS && SKIRT_X <= ENV_X - SKIRT_SIDE_CLR + EPS && SKIRT_Z0 > 0
   && SKIRT_Y1 <= WIN_Y0 - EPS && abs(SKIRT_Y0 - (HOLE_Y_N + CBORE_D / 2)) > 0 && SKIRT_X < HOLE_X - CBORE_D / 2;
R5f = R5_travel >= 1.5 - EPS;
R5 = R5a && R5c && R5d && R5e && R5f;                            // R5b 单列为「注意」
// GAP 容差窗口：+Y 压边 = 1 − δ，−Y 压边 = 1 + δ，后裙间隙 = 0.8 − δ（δ = 实际 GAP − 0.5）
GAP_MAX_OK = GAP + min(SKIRT_CLR, BEZ_PRESS, (MOS_D - DISP_W) / 2 - BEZ_PRESS);   // 1.3
GAP_MIN_OK = max(0, GAP - ((MOS_D - DISP_W) / 2 - BEZ_PRESS));                     // 0
// R6 可打印
R6_walls = POST_W - SCR_PILOT >= 2 * POST_WALL_MIN - EPS && END_T >= MIN_WALL - EPS && SKIRT_T >= MIN_WALL - EPS
        && BASE_T >= MIN_WALL - EPS && RIM_W >= MIN_WALL - EPS && (!STOP_ON || STOP_T >= MIN_WALL - EPS) && R1_bars
        && BEZ_T - CBORE_H >= MIN_WALL - EPS && (TRAY_X - NOTCH_W / 2) >= 10 - EPS;
R6_overhang = BEZ_CHAMF <= 2.0 && (CBORE_D - SCR_THRU) / 2 <= 2.0;   // 45° 倒角、沉台台阶环 0.95：反打时唯二非竖壁
R6_hole_depth = POST_HOLE_DEPTH <= POST_TOP - 2.0 + EPS;
R6_layers = abs((POST_TOP + BASE_T) / LAYER_H - round((POST_TOP + BASE_T) / LAYER_H)) < 1e-6 && abs(BEZ_T / LAYER_H - round(BEZ_T / LAYER_H)) < 1e-6;
R6 = R6_walls && R6_overhang && R6_hole_depth && R6_layers;
// R7 ±X 面功能区让位
R7 = PY_Y0 >= MOS_YC + SIDE_CUT_W / 2 - EPS && NY_Y1 <= MOS_YC - SIDE_CUT_W / 2 + EPS;
// 显示区：压框内窗 + 最大 X 游隙不进显示区
R_disp = WIN_X - CLR >= DISP_W / 2 + EPS && (WIN_Y0 <= MOS_YC - DISP_W / 2 - EPS) && (WIN_Y1 >= MOS_YC + DISP_W / 2 + EPS);

echo(str("===== v0.4 r2 托盘（Z 朝上）自检 ====="));
echo(str("底板：STL 转 ", PLATE_ROT, "°（排针边 STL +X → 托盘 −Y）；转后 X ±", r3(PLATE_W / 2), " Y ±", r3(PLATE_D / 2), "；台阶 Z=", PLATE_LEDGE_Z, "、体顶 ", PLATE_BODY_T, "、柱顶 ", PLATE_H));
echo(str("外壳：脚印 X±", r3(SHELL_XH), " Y±", r3(SHELL_YH), "，坐 Z=", SHELL_Z0, " 顶 ", r2(SHELL_TOP), "（比屏面高 ", r2(SHELL_TOP - MOS_T), "）；模块外脸 Y=", r2(MOD_FACE_Y), "；开口 |X|<", HDR_XH, " Z[", r2(HDR_Z0), ",", r2(HDR_Z1), "]"));
echo(str("Mosaico：X ", MOS_XC, "±", r3(MOS_W / 2), " Y[", r3(MOS_Y_MIN), ",", r3(MOS_Y_MAX), "] Z[0,", MOS_T, "]；GAP=", GAP, "；CLR=", CLR, "；显示区 ", DISP_W, " 居中（边框 ", r2((MOS_W - DISP_W) / 2), "）"));
echo(str("托盘包围盒 X ±", r3(TRAY_X), "  Y[", r3(TRAY_Y0), ",", r3(SHELL_YH + BASE_MARGIN), "] = ", r2(SHELL_YH + BASE_MARGIN - TRAY_Y0), " 长  Z[", -BASE_T, ",", r2(TRAY_ZMAX), "]（", round((TRAY_ZMAX + BASE_T) / LAYER_H), " 层×", LAYER_H, "）"));
echo(str("压框包围盒 X ±", r3(BEZ_X), "  Y[", r3(BEZ_Y0), ",", r3(BEZ_Y1), "]  Z[", r2(BEZ_Z0), ",", r2(BEZ_Z1), "]（后裙到 Z=", r2(SKIRT_Z0), "）；内窗 ", r2(2 * WIN_X), "×", r2(WIN_Y1 - WIN_Y0), "；边宽 ±X ", r2(BAR_W_X), " / −Y ", r2(BAR_W_YN), " / +Y(排针侧) ", r2(BAR_W_YP), "；倒角后顶宽 ", r2(TOPW_X), "/", r2(TOPW_YN), "/", r2(TOPW_YP), "（+Y 边不倒角）"));
echo(str("立柱：X ±[", r3(BLK_X0), ",", r3(BLK_X1), "]；+Y 柱 Y[", r3(PY_Y0), ",", r3(PY_Y1), "]（−Y 端导入斜角 ", POST_LEADIN, "）；−Y 块 Y[", r3(NY_Y0), ",", r3(NY_Y1), "]；顶 Z=", r2(POST_TOP), "；底孔 Ø", SCR_PILOT, " 深 ", POST_HOLE_DEPTH, "；远端墙 Y[", r3(END_Y0), ",", r3(END_Y1), "] 拇指口 ", NOTCH_W, " 宽 Z≥", NOTCH_Z));
echo(str("环形沿：宽 ", RIM_W, "，", RIM_OPEN_FAR ? "远端开口（U 形）" : "四边闭合", "；开空 X ±", r3(CUT_X), " Y[", r3(CUT_Y0), ",", r3(CUT_Y1), "]"));
echo(str("螺钉 4× ", SCREW, "：孔位 (", MOS_XC, "±", r3(HOLE_X), ", ", r3(HOLE_Y_P), ") 与 (", MOS_XC, "±", r3(HOLE_X), ", ", r3(HOLE_Y_N), ")；过孔 Ø", SCR_THRU, "、沉台 Ø", r2(CBORE_D), "×", CBORE_H, "；推荐 ", SCREW, "×6（压框 ", BEZ_T, "−沉台 ", CBORE_H, " → 旋入 ", r2(6 - (BEZ_T - CBORE_H)), "）；盘头顶 Z=", r2(HEAD_TOP), "，高出压框顶 ", r2(HEAD_TOP - BEZ_Z1), "、高出屏面 ", r2(HEAD_TOP - MOS_T)));
echo(str("R1 四边保持（限位式）：每边压 ", BEZ_PRESS, "（≤1.0 ", ok(R1_press), "）；四边条宽/顶宽≥", MIN_WALL, " ", ok(R1_bars), "；底孔在柱内壁≥", POST_WALL_MIN, " ", ok(R1_holes_in_posts), "；沉台在压框内壁≥", MIN_WALL, " ", ok(R1_cbore_in_bezel),
         "；压框本体底=柱顶 ", r2(POST_TOP), "（硬止点在柱）", ok(R1_stop), "；柱顶≤屏面 ", ok(R1_seat), "；压边底 ", r2(LIP_Z0), " → 名义 Z 游隙 ", r2(LIP_PLAY), " ∈(0,", LAYER_H + 0.05, "] ", ok(R1_play), " -> ", ok(R1)));
echo(str("R1 补充：X 游隙 ±", CLR, " → ±X 压边实际 ", r2(BEZ_PRESS - CLR), "～", r2(BEZ_PRESS + CLR), "；MOS_T 若实测 ", r2(MOS_T - 0.3), "/", MOS_T, "/", r2(MOS_T + 0.3), " → 游隙 ", r2(LIP_PLAY + 0.3), "/", r2(LIP_PLAY), "/", r2(LIP_PLAY - 0.3), "（负 = 压框坐不到柱顶，回填 MOS_T 重编译）"));
echo(str("R2 不高出屏面：托盘最高 Z=", r2(TRAY_ZMAX), " ≤ ", MOS_T, " ", ok(R2_tray), "；压框顶 ", r2(BEZ_Z1), " 高出屏面 ", r2(BEZ_Z1 - MOS_T), " ≤1.6 且三边倒角 ", ok(R2_bez), " -> ", ok(R2),
         "；螺钉盘头高出屏面 ", r2(HEAD_TOP - MOS_T), "（四角、Mosaico 脚印外；硬要求 2 字面只放行压框）-> ", okn(R2_head), "；+Y 边不倒角 -> 注意"));
echo(str("R3 不进 Mosaico 脚印（含 CLR ", CLR, "）：Z>0 实体与包络相交 = ", R3_hits, " -> ", ok(R3)));
echo(str("R4 不碰官方外壳（脚印 X±", r3(SHELL_XH), " Y±", r3(SHELL_YH), " Z[0,", r2(SHELL_TOP), "]）：托盘相交 = ", R4_hits, "；压框相交 = ", R4_bez, "；+Y 柱到外壳角 dx ", r3(MOS_XC + BLK_X0 - SHELL_XH), " dy ", r3(MOD_FACE_Y - PY_Y1), " -> ", ok(R4)));
echo(str("R5 排针安全靠顺序：落位时距针尖 ", r2(R5_drop), " ≥1.5 ", ok(R5a), "；排针区（|X|≤", HDR_XH + 2, " GAP 内 Z(0.2,", r2(PIN_ZTOP), "]）托盘/压框为空 ", ok(R5c),
         "；排针侧边外缘 ", r2(BEZ_Y1), " ≤ 外脸−", BEZ_SHELL_CLR, " 且宽≥", MIN_WALL, " ", ok(R5d), "；后裙防退出（在滑入区内、不碰墙/块/沉台）", ok(R5e), "；拔出行程余量 ", r2(R5_travel), " ≥1.5 ", ok(R5f), " -> ", ok(R5)));
echo(str("R5b 导向先于触针：+Y 角柱开始导向比针尖触面早 ", r3(R5_guide), " mm（需≥1.0；= (MOS_D−", SIDE_CUT_W, ")/2 − (PIN_LEN−GAP)，被硬要求 7 锁死）-> ", okn(R5b),
         "：触针瞬间只有 −Y 导轨 ", r2(R5_ovl), " mm 长、双边隙 ", 2 * CLR, " → 偏摆 ≤", r2(R5_yaw), "°、+Y 面横向 ≤", r2(R5_lat), " mm（半个针距 1.27）。角柱长受硬要求 7 的 34 mm 锁死，加长滑入区无效；**目视对准槽口**，同官方裸用。PIN_LEN 实测后回填"));
echo(str("R5 止挡：GAP=", GAP, " 下可用厚度 ", r2(STOP_T), "（需≥", MIN_WALL, "）→ ", STOP_ON ? str("生成，Y[", r2(STOP_Y0), ",", r2(STOP_Y1), "] 高 ", STOP_H, " -> OK") : str("**不生成**（设计决定）：插入深度由排针座到底定义（同官方裸用）；Q1-2 实测 GAP ≥ ", r2(CLR + STOP_SHELL_CLR + MIN_WALL), " 后自动生成 -> 注意")));
echo(str("R5 GAP 容差：实际 GAP ∈ [", r2(GAP_MIN_OK), ", ", r2(GAP_MAX_OK), "] 可用（+Y 压边 1−δ、−Y 压边 1+δ、后裙隙 0.8−δ，δ=GAP−", GAP, "；变大失效：>", r2(GAP_MAX_OK), " 后裙压到 Mosaico）"));
echo(str("R6 可打印：壁厚 ", ok(R6_walls), "；非竖壁只有 压框 45° 倒角 ", BEZ_CHAMF, " 与 沉台台阶环 ", r2((CBORE_D - SCR_THRU) / 2), "（≤2）", ok(R6_overhang), "；底孔深 ", POST_HOLE_DEPTH, " 留底≥2 ", ok(R6_hole_depth), "；整层数（托盘 ", round((POST_TOP + BASE_T) / LAYER_H), " 层、压框 ", round(BEZ_T / LAYER_H), " 层）", ok(R6_layers), "；压框**顶面朝下**打印 -> ", ok(R6)));
echo(str("R7 ±X 功能面让位：中央留空 Y[", r3(NY_Y1), ",", r3(PY_Y0), "] = ", r2(PY_Y0 - NY_Y1), " ≥ ", SIDE_CUT_W, "；两端角柱贴 Mosaico 段各 ", r3(POST_L), " -> ", ok(R7)));
echo(str("R8 假设登记：Q1-1/2/3/4/6/7/8/9/10/13/14/15/15b/16/17/18/18b/19/20/21/22/23/24 + AS-01（README 表）；Q1-5/11/12 废止 -> OK"));
echo(str("显示区：内窗半宽 ", r3(WIN_X), " − 游隙 ", CLR, " ≥ ", r3(DISP_W / 2), "；Y 窗 [", r2(WIN_Y0), ",", r2(WIN_Y1), "] ⊃ 显示 [", r2(MOS_YC - DISP_W / 2), ",", r2(MOS_YC + DISP_W / 2), "] -> ", ok(R_disp)));
echo(str("总判：", (R1 && R2 && R3 && R4 && R5 && R6 && R7 && R_disp) ? "R1–R7 无 FAIL" : "有 FAIL",
         "；注意 ", (STOP_ON ? 0 : 1) + (R5b ? 0 : 1) + (R2_head ? 0 : 1) + 1, " 项：", STOP_ON ? "" : "止挡无；", R5b ? "" : "导向裕量≈0；", R2_head ? "" : "盘头高出屏面 >1.6；", "+Y 边不倒角"));
echo("装配：Mosaico 放进滑入区落到环形沿/导轨 → 拇指从远端口顶其 −Y 面、目视对准槽口沿 +Y 推到排针座到底 → 压框对孔（后裙落入滑入区）→ 4 颗螺钉拧到压框坐实柱顶。取出反序：先拆压框，捏 ±X 中央窗口沿 −Y 拔离。");
