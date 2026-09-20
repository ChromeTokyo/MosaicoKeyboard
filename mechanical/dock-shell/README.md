提案 · 未冻结 · 由 Claude 主控（claude-opus-5）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造

# mechanical/dock-shell —— 底座外壳与键帽

分支 `claude/design-d/mech-dock`。2026-09-21 首稿。本目录实现 `hardware/ICD-0.2-DRAFT.md`
第 1 节坐标系、第 3 节弹簧针接口的机械侧、第 5 节 ME-D-01～ME-D-11 与第 3.3 节一级防呆。

## 文件

| 文件 | 内容 |
| --- | --- |
| `dock_shell.scad` | 外壳参数化模型（前壳＋后壳＋上压框三件、螺柱）。全部尺寸集中在文件顶部 `[ASSUMPTION 参数块]` |
| `keycaps.scad` | 十字帽、ABXY 圆帽、L/R 条帽。`include <dock_shell.scad>` 借参数，尺寸不写第二份 |
| `ERGONOMICS.md` | 握持、拇指可达、按键落点与行程、总长/厚取舍、T17 体量模型打印说明、未决项 |
| `LAYOUT-front.svg` | 正视＋侧视布局图（PNG 渲染的替代物） |
| `make_layout_svg.py` | 上图的生成脚本；改 SCAD 后重跑 |

## 编译与渲染状态

**本机（darwin，2026-09-21）未安装 OpenSCAD，本轮未编译、未渲染 PNG。**
两个 `.scad` 只通过了一个自写的静态检查（括号配对、模块/函数定义与调用、标识符定义），
这**不等于** OpenSCAD 能编译通过。命令见 `ERGONOMICS.md` 第 9 节。

## 本任务给出的接口数值（ICD 第 1 节留给机械任务的参数）

下列数值供 `claude/design-d/dock-board`、`claude/design-d/module-board`、`claude/design-d/mech-module`
直接取用。坐标系 = ICD 第 1 节（原点 = Mosaico 外形包络几何中心）。全部 `ASSUMPTION`。

| 参数 | 值 | 说明 |
| --- | --- | --- |
| `DOCK_PIN_FIELD_X0` | −26.00 mm | 弹簧针列 1（`DOCK_5V`，−X 最外）中心 X；列 8 在 −8.22 |
| `DOCK_PIN_FIELD_Z0` | +1.27 mm | 行 A（+Z，屏侧）中心 Z；行 B = −1.27。对 Mosaico 厚度中面对称 |
| `DOCK_PIN_FIELD_Y` | −25.795 mm | 配合面（= 模块板触点面）Y，满足 ICD ME-D-07 的 `< −MOSAICO_H/2` |
| `DOCK_X_TOL` / `DOCK_Z_TOL` | 0.35 / 0.35 mm | 托架定位公差，远小于半个列距 1.27（ICD 3.3 一级防呆） |
| 弹簧针小板上表面 Y | −28.995 mm | = 配合面 − 工作伸出 3.20 |
| 主板元件面 Z / 背面 Z | −2.60 / −4.20 mm | 底座主板为 XY 面环形板，中央开窗让 Mosaico 穿过 |
| 轻触开关柱头顶面 Z | +1.70 mm | = 主板元件面 ＋ 开关高 4.30 |
| 主板可用外形 | X ∈ [−81.5, +81.5]、Y ∈ [−66.5, +30.5] | 机身内腔；中央窗须避开 X ∈ [−30.2, +25.2]、Y ∈ [−26.3, +31] |
| 十键开关中心 | 见 `ERGONOMICS.md` 第 4 节表 | 键名与 GPIO 的唯一权威仍是 `hardware/module-board/PINMAP.md` |
| 底座 USB-C 开孔 | 中心 X +30.0、Y 面 −68.5、Z 中心 −2.4，孔 9.6 × 4.0 | 连接器在主板下缘、朝 −Y |
| 电池仓 | X ∈ [−60, −10]、Y ∈ [−61, −27]、Z ∈ [−12.5, −4.5] | 803450 级 8.0 × 34 × 50（AS-12，1500 mAh 默认） |
| 整机 | 167.0 × 101.5 × 28.0 mm，≈ 227 g（估） | |

## 对其他分支的三条机械请求

1. **dock-board**：D-pad 中心 (−54.0, −4.0) 留 Ø8.0 净空、不布器件、不开窗——十字帽的中央支点
   直接支在这块铜面上（`keycaps.scad` 的 `PIVOT_CLEAR_D`）。
2. **dock-board**：主板在 X ∈ [−7.6, +7.6]、Y < −26 的范围内留贯穿缺口，给 Mosaico 原生 USB-C
   的直通道让位（AS-22 位置未知，默认居中；实测后只改 `NATIVE_USB_X` 一个数）。
3. **module-board / mech-module**：触点板外形须落在 X ∈ [−28.11, −6.11]、Z ∈ [−4.5, +4.5]，
   **不得越过 X = −6.5**（否则挡住上条直通道）；触点面 Y = −25.795。

另需 dock-board 回话一条（`ERGONOMICS.md` 第 10 节第 3 项）：底座侧承接弹簧针的做法，
本稿假设是「主板正面 90° 半孔焊接的水平弹簧针小板」（与模块板 J3 同一手法，可用普通直插弹簧针）；
若能找到常备的卧式 2×8 弹簧针排则可省掉小板。两条路都不改 ICD 第 3.2 节的逐针分配。

## 本目录新增的假设

`AS-31-mechdock-1` … `AS-31-mechdock-27`，逐条写在 `dock_shell.scad` 参数块与 `ERGONOMICS.md`
第 7 节验证表里，待主控汇总时并入 `hardware/ASSUMPTIONS.md`。

**没有任何 measured 值。** 到货验证全部是不通电的尺寸与配合测量；
测电阻必须完全断电，上电只测电压（`hardware/G6-TEST-PLAN.md` 第 0 节）。
