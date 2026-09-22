# 下一次开工先读这份（2026-09-22 收工）

## 一句话状态

**方案 J（落座式）的几何与逐针分配都已冻结成提案，三道机器闸门全绿；
但没有一条经过实物验证，且四件事必须由用户或 Chrome 关闭才能打样。**

## 三道常驻闸门（改任何设计后必须全跑到退出码 0）

```bash
python3 hardware/check_cross_branch.py \
  --module /private/tmp/wt-mech-module/mechanical/module-board/module_shell.scad \
  --dock   /private/tmp/wt-mech-dock/mechanical/dock-shell/dock_shell.scad
```
```bash
python3 hardware/check_fit_geometry.py \
  --module /private/tmp/wt-mech-module/mechanical/module-board/module_shell.scad \
  --dock   /private/tmp/wt-mech-dock/mechanical/dock-shell/dock_shell.scad
```
```bash
python3 hardware/check_j2_mismate.py
```

| 闸门 | 抓什么 | 建立起因 |
| --- | --- | --- |
| `check_cross_branch.py` | **变量**不一致 | 双路清点查出 40 条跨分支不一致、22 条阻断，而各分支自检全绿 |
| `check_fit_geometry.py` | **形状**干涉（布尔求交） | 上条全绿的几何里，Mosaico 过盈 0.850 mm **根本放不进去** |
| `check_j2_mismate.py` | **错位后的电气通路** | 焊盘 Ø2.0 ＋ 针尖 Ø0.9 ⇒ 搭接阈值 1.45 > 半间距 1.27，一针压两铜 |

三道是逐层补出来的，每一道都是**上一道全绿之后仍然出事**才加的。**不要删任何一道。**

## 本周的四条大结论

1. **架构定名方案 J（落座式）**，唯一权威描述 `review/claude/option-j-seated.md`。
   不许再说「方案 D＋G」。
2. **J1 改 2.54 mm 2×10P 直插**（槽板立 YZ 面），J3 改双排 8+8 @1.27 SMD 对接焊，
   触点场 **4 行 × 4 列**。模块 −X 端由 −53.595 收到 −37.295。
3. **承力由 M2 螺钉承担，取消承力卡扣**（`docs/DECISIONS.md` D-026）。
   主材 eSUN ePLA-CF（TDS 已归档，断裂伸长率 4.27 %、HDT 仅 53 °C）。
4. **逐针分配冻结**：5V×2 ＋ GND×4 ＋ KEY×10，SDA/SCL 移出触点场。
   `hardware/RULING-j2-4x4-pinout.md`。按键映射与固件宏值零改动。

## 必须关掉才能打样的四件（按风险排序）

| # | 事 | 关闭方式 | 归谁 |
| --- | --- | --- | --- |
| 1 | **D4 类错位**（EDA 里封装被转 180°/镜像），Δ=0 即致命，**任何排法都挡不住** | 只能靠 G6 上电前导通检验，是流程不是几何。须写进放行清单 | Chrome |
| 2 | **`RETENTION_N = 30` 是设计目标值**，M2 自攻在 PLA-CF 打印柱里的抗拔力一个数据都没有 | 标定件 F/G 两组 ＋ 推拉力计实测 | 用户 |
| 3 | **定位公差链最坏值正好等于目标、零余量**；`MATING.md` 第 6 节六环链未按新拓扑重算 | 重算 ＋ 标定件 A 组实测填 `DOCK_Y_TOL` | Claude ／ 用户 |
| 4 | **AS-31-mm-3（J1 本体 X 深 8.5 mm）无原厂依据** | **一份原厂规格书就能关，不需要任何仪器**——这是性价比最高的一条 | Chrome |

## 用户手上的活

打 `mechanical/test-coupons/fit_ladder.scad`（七组）。
**C/D/E/G 四组不需要卡尺，现在就能做。** A/B 等卡尺，F 等 M2 热熔螺母。
判据与待填表在同目录 `MEASURE.md`。**必须用硬化喷嘴**，不加 brim，水平膨胀保持默认。

## 两条我传播过的错误，别再传

- **可直连按键的 GPIO 是 11 根不是 12 根**（GPIO14 = EEPROM A0，专用）。
  见 `hardware/CORRECTION-20260922-gpio-count.md`。
- **`dock_shell` 的 14238/29152 是改直插之前的数**，当前是 13920/28472。
  我拿旧数当现值，还用它立过「不要采信转述」的纪律。

## Grok 的 R0 报告不在 main 上

`review/grok/R0/` 在 main 上只有 `MATERIALS.md`。正文在 `origin/grok/r0-design-review`
（PR #43，仍 DRAFT）。**这就是 G01–G08 挂了好几天的原因**——在 main 上按图索骥找不到。
本轮已关闭 **G04（成立，ICD 3.3「无损」措辞必须撤回）** 与 **G05（枚举已做到穷举）**，
G01/G02 随按键映射未动而自然关闭。**G03、G06、G07、G08 仍未处理。**

## 未合并的分支

四个 `claude/design-d/*` 与 `sweep/consistency-20260921` 全部未合入 main。
按 D-013，设计者不得担任本轮独立复核人——**这些要 Hiro 或 Grok 过一遍再合**。
