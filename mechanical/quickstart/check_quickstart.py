#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_quickstart.py —— 轨一（D-031）延伸托盘的机器闸门。

**独立于设计者**：不读 .scad 的几何，只读导出的 STL，按硬要求逐条断言。
任何一条失败 → 退出码 1，并打印「哪条、哪里、差多少」。

依赖：python3 标准库 + numpy + trimesh + shapely（**不需要 rtree**——
不用 contains / ray / polygons_full，截面用 mesh.section().discrete 自建奇偶多边形）。

用法：
    python3 check_quickstart.py --tray extended_baseplate.stl [--bezel end_bar.stl]
        [--plate official_plate_fullres.stl] [--gap 0.5 --clr 0.3 --mos-w 45.19 --mos-d 45.19 --mos-t 11.48]
        [--json out.json]

坐标约定（与硬要求一致，Bambu Z 朝上）：官方底板 XY 包围盒中心置于原点，Z[0, 6.44]；
排针从底板 −Y 边出去；Mosaico 放 −Y 侧；Mosaico 背面与模块背面同在 Z=0。

闸门自己的假设（G-*，不是设计假设；数值来源见旁注）：
  G-1  模块朝 Mosaico 的外脸 Y = 官方底板 Ymin − SHELL_OVERHANG（硬要求 4：外壳比底板每侧宽 0.75）；
       外壳包络 = max(44.90 见方, 底板包围盒每侧 +0.75)（两者在 Y 向差 0.1，取并集保守）。
  G-2  Mosaico X 中心与模块 X 中心重合（scad 约定，AS 无数据；--mos-xc 可改）。
  G-3  压框「压住前缘」的判据：Z ∈ [MOS_T, MOS_T+2] 的压框截面落进 1.0 mm 前缘带；
       且每边压框材料最低点 ≤ MOS_T + 0.10（否则悬空不接触——v0.2 卡舌悬空 2.5 mm 就是这个错）。
       0.10 = 两个 0.2 层高的一半（FDM 首层公差量级），保守取。
  G-4  压框允许在前缘带内向下预压 ≤ 0.30（PLA 压框弹性变形量级；超出即视为「进 Mosaico 脚印」）。
  G-5  螺钉底孔有效深度 ≥ 3.0（M2×6 穿 1.6 压框剩 4.4；3.0 为下限，低于此 PLA 自攻没有意义）。
  G-6  可打印：壁 ≥ 1.2、悬空 ≤ 2.0（硬要求 6）；官方底板区（一个面不许改）不参与可打印性判定。
  G-7  截面比对容差 0.05 mm；面积阈值 0.01～0.05 mm²（OpenSCAD 导出 ASCII STL 的 tessellation 噪声量级）。
"""
import argparse
import json
import math
import sys
import warnings
from collections import OrderedDict

import numpy as np

warnings.filterwarnings("ignore")

try:
    import trimesh
    from shapely.geometry import Polygon, box, Point, LinearRing
    from shapely.ops import unary_union
except ImportError as e:  # pragma: no cover
    print("缺依赖：", e, file=sys.stderr)
    sys.exit(2)

EMPTY = Polygon()


# ----------------------------------------------------------------------------
# 截面工具（无 rtree）
# ----------------------------------------------------------------------------
class Slicer:
    """对一个 mesh 做平面截面，返回 shapely 多边形（世界坐标）。缓存。"""

    def __init__(self, mesh, name):
        self.mesh = mesh
        self.name = name
        self._cache = {}
        self._vz = [np.unique(np.round(mesh.vertices[:, i], 4)) for i in range(3)]

    def safe_coord(self, axis, c):
        """把截面位置从顶点平面上挪开（截在共面处会得到退化环）。"""
        v = self._vz[axis]
        for _ in range(20):
            i = np.searchsorted(v, c)
            near = []
            if i < len(v):
                near.append(abs(v[i] - c))
            if i > 0:
                near.append(abs(v[i - 1] - c))
            if not near or min(near) > 2e-3:
                return c
            c += 0.0113
        return c

    def solid(self, axis, c):
        """axis: 0/1/2 = 截面法向 X/Y/Z。返回 2D 实体（其余两轴按 (a,b) 升序作为平面坐标）。"""
        c = self.safe_coord(axis, c)
        key = (axis, round(c, 5))
        if key in self._cache:
            return self._cache[key]
        origin = [0.0, 0.0, 0.0]
        normal = [0.0, 0.0, 0.0]
        origin[axis] = c
        normal[axis] = 1.0
        try:
            sec = self.mesh.section(plane_origin=origin, plane_normal=normal)
        except Exception:
            sec = None
        result = EMPTY
        if sec is not None:
            cols = [i for i in range(3) if i != axis]
            rings = []
            try:
                loops = sec.discrete
            except Exception:
                loops = []
            for lp in loops:
                pts = np.asarray(lp)[:, cols]
                if len(pts) < 3:
                    continue
                pg = Polygon(pts)
                if not pg.is_valid:
                    pg = pg.buffer(0)
                if pg.is_empty or pg.area < 1e-6:
                    continue
                rings.append(pg)
            solid = None
            for pg in sorted(rings, key=lambda p: -p.area):
                solid = pg if solid is None else solid.symmetric_difference(pg)
            if solid is not None and not solid.is_empty:
                if not solid.is_valid:
                    solid = solid.buffer(0)
                result = solid
        self._cache[key] = result
        return result

    def z(self, zc):
        return self.solid(2, zc)


def parts(geom):
    if geom is None or geom.is_empty:
        return []
    if hasattr(geom, "geoms"):
        out = []
        for g in geom.geoms:
            out.extend(parts(g))
        return out
    if isinstance(geom, Polygon):
        return [geom]
    return []


def polys_only(geom):
    ps = parts(geom)
    if not ps:
        return EMPTY
    return unary_union(ps)


def fmt_bounds(b):
    return "X[%.2f,%.2f] Y[%.2f,%.2f]" % (b[0], b[2], b[1], b[3])


def max_penetration(inter, region):
    """inter ⊂ region：inter 的点离 region 边界最远多少 = 最深钻进多少。"""
    if inter.is_empty:
        return 0.0
    bd = region.exterior
    best = 0.0
    for p in parts(inter):
        for x, y in p.exterior.coords:
            best = max(best, bd.distance(Point(x, y)))
    return best


def z_levels(z0, z1, step, extra=()):
    zs = list(np.arange(z0, z1 + 1e-9, step))
    zs += [z for z in extra if z0 - 1e-9 <= z <= z1 + 1e-9]
    return sorted(set(round(z, 4) for z in zs))


# ----------------------------------------------------------------------------
# 报告
# ----------------------------------------------------------------------------
class Report:
    def __init__(self):
        self.items = OrderedDict()

    def start(self, key, title):
        self.items[key] = {"title": title, "status": "PASS", "lines": []}
        self._cur = key

    def fail(self, msg):
        self.items[self._cur]["status"] = "FAIL"
        self.items[self._cur]["lines"].append(("FAIL", msg))

    def warn(self, msg):
        if self.items[self._cur]["status"] == "PASS":
            self.items[self._cur]["status"] = "WARN"
        self.items[self._cur]["lines"].append(("WARN", msg))

    def info(self, msg):
        self.items[self._cur]["lines"].append(("info", msg))

    def dump(self):
        nfail = 0
        for key, it in self.items.items():
            st = it["status"]
            if st == "FAIL":
                nfail += 1
            print("[%s] %s %s" % (st, key, it["title"]))
            for lvl, msg in it["lines"]:
                print("        %s %s" % ({"FAIL": "✗", "WARN": "!", "info": "·"}[lvl], msg))
        print("-" * 78)
        print("结果：%d 条失败 / %d 条" % (nfail, len(self.items)))
        return nfail


# ----------------------------------------------------------------------------
# 主体
# ----------------------------------------------------------------------------
def load_mesh(path):
    m = trimesh.load(path, force="mesh")
    if not isinstance(m, trimesh.Trimesh):
        raise SystemExit("不是三角网格：%s" % path)
    return m


def main():
    ap = argparse.ArgumentParser(description="轨一延伸托盘机器闸门（v0.4 硬要求）")
    ap.add_argument("--tray", required=True, help="托盘 STL")
    ap.add_argument("--bezel", default=None, help="压框 STL（可选；缺省视为无压框）")
    ap.add_argument("--plate", default=None, help="官方底板全分辨率 STL（缺省找脚本同目录 official_plate_fullres.stl）")
    ap.add_argument("--mos-w", type=float, default=45.19, help="Mosaico X 向宽（AS-01）")
    ap.add_argument("--mos-d", type=float, default=45.19, help="Mosaico Y 向深（AS-01）")
    ap.add_argument("--mos-t", type=float, default=11.48, help="Mosaico 厚（AS-01）")
    ap.add_argument("--mos-xc", type=float, default=0.0, help="Mosaico X 中心（G-2）")
    ap.add_argument("--clr", type=float, default=0.30, help="包络单边间隙（Q1-4）")
    ap.add_argument("--gap", type=float, default=0.50, help="模块外脸到 Mosaico 面间隙（Q1-2）")
    ap.add_argument("--shell-foot", type=float, default=44.90, help="官方外壳外形见方")
    ap.add_argument("--shell-h", type=float, default=10.90, help="官方外壳高")
    ap.add_argument("--shell-overhang", type=float, default=0.75, help="外壳比底板每侧宽（Q1-1）")
    ap.add_argument("--side-cut", type=float, default=34.0, help="±X 功能区沿 Y 中央留空长度（Q1-6）")
    ap.add_argument("--func-z", type=float, nargs=2, default=(2.0, 6.0), help="±X 功能区 Z 区间")
    ap.add_argument("--pin-z", type=float, nargs=2, default=(2.0, 9.0), help="排针让位 Z 区间")
    ap.add_argument("--hole-d", type=float, default=1.7, help="M2 自攻底孔直径")
    ap.add_argument("--hole-tol", type=float, default=0.2)
    ap.add_argument("--post-wall", type=float, default=1.5, help="立柱孔周最小壁")
    ap.add_argument("--hole-depth", type=float, default=3.0, help="底孔最小有效深度（G-5）")
    ap.add_argument("--n-holes", type=int, default=4)
    ap.add_argument("--bezel-max-t", type=float, default=1.6, help="压框最大厚（高出屏面上限）")
    ap.add_argument("--press-max", type=float, default=1.0, help="压框压前缘最大宽度")
    ap.add_argument("--press-frac", type=float, default=0.60, help="每边前缘带最低覆盖比例")
    ap.add_argument("--hover", type=float, default=0.10, help="压框离屏面最大悬空（G-3）")
    ap.add_argument("--preload", type=float, default=0.30, help="压框允许预压深度（G-4）")
    ap.add_argument("--min-wall", type=float, default=1.2)
    ap.add_argument("--max-overhang", type=float, default=2.0)
    ap.add_argument("--json", default=None, help="把结果另存 JSON")
    ap.add_argument("--quick", action="store_true", help="跳过第 9 条可打印性（慢）")
    a = ap.parse_args()

    import os
    here = os.path.dirname(os.path.abspath(__file__))
    plate_path = a.plate or os.path.join(here, "official_plate_fullres.stl")

    tray = load_mesh(a.tray)
    bezel = load_mesh(a.bezel) if a.bezel else None
    plate = load_mesh(plate_path)

    # 官方底板置中（XY 包围盒中心 → 原点；Z 不动）
    pb = plate.bounds
    plate_c = plate.copy()
    plate_c.apply_translation([-(pb[0][0] + pb[1][0]) / 2, -(pb[0][1] + pb[1][1]) / 2, 0.0])
    pcb = plate_c.bounds
    PL_XMIN, PL_YMIN, PL_ZMIN = pcb[0]
    PL_XMAX, PL_YMAX, PL_ZMAX = pcb[1]

    # ---- 派生几何（G-1 / G-2）----
    OV = a.shell_overhang
    ENV_XMIN = min(-a.shell_foot / 2, PL_XMIN - OV)
    ENV_XMAX = max(a.shell_foot / 2, PL_XMAX + OV)
    ENV_YMIN = min(-a.shell_foot / 2, PL_YMIN - OV)
    ENV_YMAX = max(a.shell_foot / 2, PL_YMAX + OV)
    MOD_FACE_Y = ENV_YMIN                       # 模块朝 Mosaico 的外脸
    MOS_YMAX = MOD_FACE_Y - a.gap
    MOS_YMIN = MOS_YMAX - a.mos_d
    MOS_YC = (MOS_YMIN + MOS_YMAX) / 2
    MOS_XMIN = a.mos_xc - a.mos_w / 2
    MOS_XMAX = a.mos_xc + a.mos_w / 2
    MOS_T = a.mos_t
    mos_rect = box(MOS_XMIN, MOS_YMIN, MOS_XMAX, MOS_YMAX)
    mos_env = box(MOS_XMIN - a.clr, MOS_YMIN - a.clr, MOS_XMAX + a.clr, MOS_YMAX + a.clr)
    env_rect = box(ENV_XMIN, ENV_YMIN, ENV_XMAX, ENV_YMAX)
    plate_rect = box(PL_XMIN, PL_YMIN, PL_XMAX, PL_YMAX)

    print("=" * 78)
    print("check_quickstart —— 轨一延伸托盘机器闸门")
    print("托盘  : %s  面 %d  包围盒 X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]" % (
        a.tray, len(tray.faces), *[tray.bounds[i][j] for j in range(3) for i in range(2)]))
    if bezel is not None:
        print("压框  : %s  面 %d  包围盒 X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]" % (
            a.bezel, len(bezel.faces), *[bezel.bounds[i][j] for j in range(3) for i in range(2)]))
    else:
        print("压框  : （未提供）")
    print("底板  : %s  置中后 X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]" % (
        plate_path, PL_XMIN, PL_XMAX, PL_YMIN, PL_YMAX, PL_ZMIN, PL_ZMAX))
    print("派生  : 外壳包络 X[%.3f,%.3f] Y[%.3f,%.3f] Z(0,%.2f]；模块外脸 Y=%.3f；GAP=%.2f" % (
        ENV_XMIN, ENV_XMAX, ENV_YMIN, ENV_YMAX, a.shell_h, MOD_FACE_Y, a.gap))
    print("        Mosaico X[%.3f,%.3f] Y[%.3f,%.3f] Z[0,%.2f]；包络 +CLR %.2f → X[%.3f,%.3f] Y[%.3f,%.3f]" % (
        MOS_XMIN, MOS_XMAX, MOS_YMIN, MOS_YMAX, MOS_T, a.clr,
        MOS_XMIN - a.clr, MOS_XMAX + a.clr, MOS_YMIN - a.clr, MOS_YMAX + a.clr))
    print("=" * 78)

    ST = Slicer(tray, "tray")
    SB = Slicer(bezel, "bezel") if bezel is not None else None
    SP = Slicer(plate_c, "plate")
    R = Report()
    A_TOL = 0.01    # mm²，面积阈值（G-7）
    E_TOL = 0.02    # mm，边界重合容差

    # ======================================================================
    # 1. 脚印干涉
    # ======================================================================
    R.start("#1", "脚印干涉：Z∈[0,%.2f] 内托盘实体 ∩ Mosaico 包络（+CLR）为空" % MOS_T)
    probe = mos_env.buffer(-E_TOL)
    zs = z_levels(0.1, MOS_T - 0.05, 0.25, extra=(0.5, 2, 4, 6, 8, 10, 11.3))
    worst = []
    for z in zs:
        s = ST.z(z)
        inter = polys_only(s.intersection(probe)) if not s.is_empty else EMPTY
        if inter.area > A_TOL:
            worst.append((z, inter.area, inter.bounds, max_penetration(inter, mos_env)))
    if worst:
        zlist = [w[0] for w in worst]
        R.fail("托盘钻进 Mosaico 包络：%d 个截面（Z %.2f～%.2f）" % (len(worst), min(zlist), max(zlist)))
        for z, ar, b, pen in sorted(worst, key=lambda w: -w[1])[:4]:
            R.fail("  Z=%.2f 相交 %.2f mm²，%s，最深钻入 %.2f mm" % (z, ar, fmt_bounds(b), pen))
    # 顶点法补漏（截面之间的小特征）
    v = tray.vertices
    inside = (v[:, 0] > MOS_XMIN - a.clr + E_TOL) & (v[:, 0] < MOS_XMAX + a.clr - E_TOL) & \
             (v[:, 1] > MOS_YMIN - a.clr + E_TOL) & (v[:, 1] < MOS_YMAX + a.clr - E_TOL) & \
             (v[:, 2] > E_TOL) & (v[:, 2] < MOS_T - E_TOL)
    if inside.any():
        vb = v[inside]
        lo, hi = vb.min(0), vb.max(0)
        R.fail("托盘有 %d 个顶点落在 Mosaico 包络内：X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]" % (
            inside.sum(), lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    if SB is not None:
        # 压框：Z ≤ MOS_T − preload 全区不许；(MOS_T − preload, MOS_T] 只允许在 1.0 前缘带内（G-4）
        inner = mos_rect.buffer(-a.press_max)
        bad = []
        for z in z_levels(0.1, MOS_T - 0.02, 0.2):
            s = SB.z(z)
            if s.is_empty:
                continue
            region = probe if z <= MOS_T - a.preload else inner.buffer(-E_TOL)
            inter = polys_only(s.intersection(region))
            if inter.area > A_TOL:
                bad.append((z, inter.area, inter.bounds))
        if bad:
            R.fail("压框在屏面以下钻进 Mosaico：%d 个截面，例 Z=%.2f %.2f mm² %s" % (len(bad), bad[0][0], bad[0][1], fmt_bounds(bad[0][2])))
    if R.items["#1"]["status"] == "PASS":
        R.info("检查 %d 个 Z 截面 + 全部顶点，均在包络外" % len(zs))

    # ======================================================================
    # 2. 官方外壳脚印
    # ======================================================================
    R.start("#2", "官方外壳脚印：Z∈(0,%.2f] 内、外壳包络里，托盘截面 ≡ 官方底板截面（不加不减）" % a.shell_h)
    zs = z_levels(0.1, a.shell_h - 0.05, 0.25, extra=(0.2, 0.5, 1.0, 1.5, 1.7, 1.95, 2.5, 3.5, 4.5, 5.5, 6.2, 6.4, 6.6, 7.5, 8.5, 9.5, 10.5, 10.85))
    extra_hits, miss_hits, bez_hits = [], [], []
    for z in zs:
        t = ST.z(z)
        tin = polys_only(t.intersection(env_rect)) if not t.is_empty else EMPTY
        p = SP.z(z)
        extra = polys_only(tin.difference(p.buffer(0.05))) if not tin.is_empty else EMPTY
        missing = polys_only(p.difference(tin.buffer(0.05))) if not p.is_empty else EMPTY
        if extra.area > 0.05:
            extra_hits.append((z, extra.area, extra.bounds, extra))
        if missing.area > 0.05:
            miss_hits.append((z, missing.area, missing.bounds))
        if SB is not None:
            b = SB.z(z)
            bin_ = polys_only(b.intersection(env_rect.buffer(-E_TOL))) if not b.is_empty else EMPTY
            if bin_.area > A_TOL:
                bez_hits.append((z, bin_.area, bin_.bounds))
    if extra_hits:
        zl = [h[0] for h in extra_hits]
        R.fail("托盘在外壳包络内多出了官方底板以外的实体（会顶到官方外壳壁/角柱）：Z %.2f～%.2f 共 %d 层" % (min(zl), max(zl), len(extra_hits)))
        z, ar, b, geom = sorted(extra_hits, key=lambda h: -h[1])[0]
        R.fail("  最大层 Z=%.2f 多出 %.2f mm²，分 %d 块：" % (z, ar, len(parts(geom))))
        for p in sorted(parts(geom), key=lambda p: -p.area)[:4]:
            R.fail("    %.2f mm² 于 %s（伸进包络 %.2f mm）" % (p.area, fmt_bounds(p.bounds), max_penetration(p, env_rect)))
    if miss_hits:
        zl = [h[0] for h in miss_hits]
        R.fail("官方底板有截面在托盘里缺失/被改（一个面不许改）：Z %.2f～%.2f 共 %d 层" % (min(zl), max(zl), len(miss_hits)))
        for z, ar, b in sorted(miss_hits, key=lambda h: -h[1])[:3]:
            R.fail("  Z=%.2f 缺 %.2f mm² 于 %s" % (z, ar, fmt_bounds(b)))
    if bez_hits:
        R.fail("压框进了外壳包络：例 Z=%.2f %.2f mm² %s" % (bez_hits[0][0], bez_hits[0][1], fmt_bounds(bez_hits[0][2])))
    if R.items["#2"]["status"] == "PASS":
        R.info("%d 个 Z 截面上，包络内托盘 ≡ 官方底板（容差 0.05 mm）" % len(zs))

    # ======================================================================
    # 3. 不高出屏面
    # ======================================================================
    R.start("#3", "不高出屏面：托盘 Zmax ≤ %.2f；压框 Zmax ≤ %.2f（厚 ≤ %.1f）" % (MOS_T, MOS_T + a.bezel_max_t, a.bezel_max_t))
    zmax = tray.bounds[1][2]
    if zmax > MOS_T + 1e-3:
        top = tray.vertices[tray.vertices[:, 2] > zmax - 1e-3]
        R.fail("托盘 Zmax=%.2f 高出屏面 %.2f mm，位置 X[%.2f,%.2f] Y[%.2f,%.2f]" % (
            zmax, zmax - MOS_T, top[:, 0].min(), top[:, 0].max(), top[:, 1].min(), top[:, 1].max()))
    else:
        R.info("托盘 Zmax=%.2f，低于屏面 %.2f mm" % (zmax, MOS_T - zmax))
    if bezel is not None:
        bz = bezel.bounds[1][2]
        if bz > MOS_T + a.bezel_max_t + 1e-3:
            R.fail("压框 Zmax=%.2f，高出屏面 %.2f > %.1f" % (bz, bz - MOS_T, a.bezel_max_t))
        else:
            R.info("压框 Zmax=%.2f，高出屏面 %.2f mm（≤ %.1f）" % (bz, bz - MOS_T, a.bezel_max_t))
        R.info("压框外缘倒角：闸门不判，人工看")

    # ======================================================================
    # 4. 四边保持
    # ======================================================================
    R.start("#4", "四边保持：压框在 Z∈[%.2f,%.2f] 压住 Mosaico 四条前缘各 ≥%d%%，压宽 ≤%.1f，不悬空（G-3）" % (
        MOS_T, MOS_T + 2, int(a.press_frac * 100), a.press_max))
    if SB is None:
        R.fail("没有压框，且托盘 Zmax ≤ 屏面 → 四条前缘没有任何东西压着，任一角都能抬起")
    else:
        pm = a.press_max
        bands = OrderedDict([
            ("-Y（远端）", (box(MOS_XMIN, MOS_YMIN, MOS_XMAX, MOS_YMIN + pm), 0, a.mos_w)),
            ("+Y（模块端）", (box(MOS_XMIN, MOS_YMAX - pm, MOS_XMAX, MOS_YMAX), 0, a.mos_w)),
            ("-X", (box(MOS_XMIN, MOS_YMIN, MOS_XMIN + pm, MOS_YMAX), 1, a.mos_d)),
            ("+X", (box(MOS_XMAX - pm, MOS_YMIN, MOS_XMAX, MOS_YMAX), 1, a.mos_d)),
        ])
        zs = z_levels(MOS_T + 0.03, MOS_T + 2.0, 0.1)
        slices = [(z, SB.z(z)) for z in zs]
        union_all = polys_only(unary_union([s for _, s in slices if not s.is_empty])) if any(not s.is_empty for _, s in slices) else EMPTY
        for name, (band, ax, L) in bands.items():
            cov = polys_only(union_all.intersection(band)) if not union_all.is_empty else EMPTY
            # 覆盖长度：各连通片在边方向上的投影区间并集
            ivs = []
            for p in parts(cov):
                b = p.bounds
                ivs.append((b[ax], b[ax + 2]))
            ivs.sort()
            covered = 0.0
            cur = None
            for lo, hi in ivs:
                if cur is None or lo > cur[1]:
                    if cur:
                        covered += cur[1] - cur[0]
                    cur = [lo, hi]
                else:
                    cur[1] = max(cur[1], hi)
            if cur:
                covered += cur[1] - cur[0]
            frac = covered / L
            # 悬空：该边带上最低有材料的 Z
            zlow = None
            for z, s in slices:
                if not s.is_empty and polys_only(s.intersection(band)).area > A_TOL:
                    zlow = z
                    break
            if frac < a.press_frac:
                R.fail("%s 前缘只被压住 %.1f mm / %.1f（%.0f%% < %d%%）" % (name, covered, L, frac * 100, int(a.press_frac * 100)))
            elif zlow is not None and zlow - MOS_T > a.hover + 0.05:
                R.fail("%s 前缘被覆盖 %.0f%%，但压框最低点 Z=%.2f 悬空 %.2f > %.2f，压不到" % (name, frac * 100, zlow, zlow - MOS_T, a.hover))
            else:
                R.info("%s 前缘覆盖 %.1f mm / %.1f（%.0f%%），最低材料 Z=%.2f" % (name, covered, L, frac * 100, zlow if zlow else float("nan")))
        # 4b 压宽 ≤ press_max：屏面上方压框不得进到内矩形
        inner = mos_rect.buffer(-pm - E_TOL)
        over = polys_only(union_all.intersection(inner)) if not union_all.is_empty else EMPTY
        if over.area > A_TOL:
            R.fail("压框盖到屏面内侧 > %.1f mm：%.2f mm² 于 %s，最深 %.2f mm" % (
                pm, over.area, fmt_bounds(over.bounds), max_penetration(over, mos_rect.buffer(-pm))))

    # ======================================================================
    # 5. 排针让位
    # ======================================================================
    R.start("#5", "排针让位：GAP 区（Y∈[%.3f,%.3f]，全 Mosaico 宽）Z∈[%.1f,%.1f] 内托盘/压框为空" % (
        MOS_YMAX, MOD_FACE_Y, a.pin_z[0], a.pin_z[1]))
    gap_rect = box(MOS_XMIN - a.clr, MOS_YMAX, MOS_XMAX + a.clr, MOD_FACE_Y).buffer(-E_TOL / 2)
    hits = []
    for z in z_levels(a.pin_z[0] + 0.02, a.pin_z[1] - 0.02, 0.25):
        for nm, S in (("托盘", ST), ("压框", SB)):
            if S is None:
                continue
            s = S.z(z)
            inter = polys_only(s.intersection(gap_rect)) if not s.is_empty else EMPTY
            if inter.area > A_TOL / 2:
                hits.append((nm, z, inter.area, inter.bounds))
    if hits:
        R.fail("GAP 区被挡：%d 处，例 %s Z=%.2f %.2f mm² %s" % (len(hits), hits[0][0], hits[0][1], hits[0][2], fmt_bounds(hits[0][3])))
    else:
        R.info("GAP 区 Z∈[%.1f,%.1f] 全空（GAP 宽仅 %.2f，顺序装配时排针沿 Y 进 H2）" % (a.pin_z[0], a.pin_z[1], a.gap))

    # ======================================================================
    # 6. ±X 功能区让位
    # ======================================================================
    R.start("#6", "±X 功能区让位：Mosaico ±X 面外 0～2 mm、Y 中央 %.0f mm、Z∈[%.0f,%.0f] 内托盘为空" % (a.side_cut, *a.func_z))
    zones = {
        "-X": box(MOS_XMIN - 2.0, MOS_YC - a.side_cut / 2, MOS_XMIN, MOS_YC + a.side_cut / 2).buffer(-E_TOL),
        "+X": box(MOS_XMAX, MOS_YC - a.side_cut / 2, MOS_XMAX + 2.0, MOS_YC + a.side_cut / 2).buffer(-E_TOL),
    }
    for side, zone in zones.items():
        hits = []
        for z in z_levels(a.func_z[0] + 0.02, a.func_z[1] - 0.02, 0.25):
            for nm, S in (("托盘", ST), ("压框", SB)):
                if S is None:
                    continue
                s = S.z(z)
                inter = polys_only(s.intersection(zone)) if not s.is_empty else EMPTY
                if inter.area > A_TOL:
                    hits.append((nm, z, inter.area, inter.bounds))
        if hits:
            zl = [h[1] for h in hits]
            R.fail("%s 侧功能区被遮：Z %.2f～%.2f，例 %s %.2f mm² %s" % (side, min(zl), max(zl), hits[0][0], hits[0][2], fmt_bounds(hits[0][3])))
        else:
            R.info("%s 侧功能区 Y[%.2f,%.2f] 让空" % (side, MOS_YC - a.side_cut / 2, MOS_YC + a.side_cut / 2))

    # ======================================================================
    # 7. manifold
    # ======================================================================
    R.start("#7", "manifold：托盘与压框都 watertight")
    for nm, m in (("托盘", tray), ("压框", bezel)):
        if m is None:
            continue
        if m.is_watertight:
            R.info("%s watertight，%d 面，%d 体" % (nm, len(m.faces), m.body_count))
        else:
            e = m.edges_sorted
            u, cnt = np.unique(e, axis=0, return_counts=True)
            bad = u[cnt != 2]
            pts = m.vertices[bad.reshape(-1)] if len(bad) else np.zeros((0, 3))
            hist = {int(k): int(v) for k, v in zip(*np.unique(cnt, return_counts=True)) if k != 2}
            loc = "X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]" % (pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max(), pts[:, 2].min(), pts[:, 2].max()) if len(pts) else "?"
            R.fail("%s 非 watertight：%d 条坏边（面数分布 %s），位置 %s；%d 体" % (nm, len(bad), hist, loc, m.body_count))

    # ======================================================================
    # 8. 螺钉立柱
    # ======================================================================
    R.start("#8", "螺钉立柱：≥%d 个 Ø%.1f±%.1f 竖孔，孔周壁 ≥%.1f，深 ≥%.1f，顶部敞开，两端都有；压框过孔对位" % (
        a.n_holes, a.hole_d, a.hole_tol, a.post_wall, a.hole_depth))
    holes = []   # dict(cx, cy, zs, ds, walls)
    zs = z_levels(0.15, tray.bounds[1][2] - 0.05, 0.25)
    for z in zs:
        s = ST.z(z)
        for p in parts(s):
            rings = list(p.interiors)
            for ri, ring in enumerate(rings):
                hp = Polygon(ring)
                if not hp.is_valid:
                    hp = hp.buffer(0)
                d = 2 * math.sqrt(max(hp.area, 0) / math.pi)
                if abs(d - a.hole_d) > a.hole_tol + 0.05:
                    continue
                cx, cy = hp.centroid.x, hp.centroid.y
                if 0 < z <= PL_ZMAX + 0.05 and plate_rect.contains(Point(cx, cy)):
                    continue  # 官方底板自己的孔不算
                # 孔周壁：孔环到「所在多边形去掉此孔后」边界（外轮廓 + 其他孔）的最近距离
                # 注意 shapely 2.x 迭代 interiors 每次给新对象，不能用 is 比较，按下标排除
                others = [rings[j] for j in range(len(rings)) if j != ri]
                shell_only = Polygon(p.exterior, others)
                if not shell_only.is_valid:
                    shell_only = shell_only.buffer(0)
                wall = LinearRing(ring).distance(shell_only.boundary)
                # 归组
                for h in holes:
                    if abs(h["cx"] - cx) < 0.3 and abs(h["cy"] - cy) < 0.3:
                        h["zs"].append(z); h["ds"].append(d); h["walls"].append(wall)
                        break
                else:
                    holes.append({"cx": cx, "cy": cy, "zs": [z], "ds": [d], "walls": [wall]})
    good = []
    for h in holes:
        zlo, zhi = min(h["zs"]), max(h["zs"])
        depth = zhi - zlo + 0.25
        dmin, dmax = min(h["ds"]), max(h["ds"])
        wmin = min(h["walls"])
        # 顶部敞开：孔顶以上所有截面在孔心处都无实体
        covered = False
        for z in z_levels(zhi + 0.25, tray.bounds[1][2] - 0.05, 0.25):
            s = ST.z(z)
            if not s.is_empty and s.buffer(-0.05).contains(Point(h["cx"], h["cy"])):
                covered = True
                break
        desc = "孔 @(%.2f, %.2f) Ø%.2f～%.2f Z[%.2f,%.2f] 深≈%.1f 壁≥%.2f" % (h["cx"], h["cy"], dmin, dmax, zlo, zhi, depth, wmin)
        ok = True
        if wmin < a.post_wall - 0.02:
            R.fail(desc + " —— 孔周壁 %.2f < %.1f" % (wmin, a.post_wall)); ok = False
        if depth < a.hole_depth - 0.05:
            R.fail(desc + " —— 深 %.1f < %.1f" % (depth, a.hole_depth)); ok = False
        if covered:
            R.fail(desc + " —— 孔顶被托盘实体盖住，螺钉进不去"); ok = False
        if ok:
            R.info(desc)
            good.append(h)
    if len(good) < a.n_holes:
        R.fail("合格底孔只有 %d 个，要求 %d 个" % (len(good), a.n_holes))
    if good:
        far = [h for h in good if h["cy"] < MOS_YC]
        near = [h for h in good if h["cy"] > MOS_YC]
        left = [h for h in good if h["cx"] < a.mos_xc]
        right = [h for h in good if h["cx"] > a.mos_xc]
        if not far or not near:
            R.fail("底孔只在 Mosaico 的一端（远端 %d / 模块端 %d）——压框另一端没有螺钉，那一端的前缘压不住" % (len(far), len(near)))
        if not left or not right:
            R.fail("底孔只在 X 一侧（−X %d / +X %d）" % (len(left), len(right)))
    # 8d 压框过孔对位
    if SB is not None and good:
        bh = []
        for z in z_levels(bezel.bounds[0][2] + 0.1, bezel.bounds[1][2] - 0.05, 0.2):
            s = SB.z(z)
            for p in parts(s):
                for ring in p.interiors:
                    hp = Polygon(ring)
                    d = 2 * math.sqrt(max(hp.area, 0) / math.pi)
                    if 2.0 <= d <= 3.2:
                        bh.append((hp.centroid.x, hp.centroid.y, d))
        for h in good:
            near_b = [b for b in bh if abs(b[0] - h["cx"]) < 0.3 and abs(b[1] - h["cy"]) < 0.3]
            if not near_b:
                R.fail("托盘底孔 @(%.2f, %.2f) 在压框上没有对应 Ø2.0～3.2 过孔" % (h["cx"], h["cy"]))
        R.info("压框过孔 %d 个截面命中" % len(bh))

    # ======================================================================
    # 9. 可打印性（G-6；官方底板区除外）
    # ======================================================================
    if not a.quick:
        R.start("#9", "可打印性：壁 ≥%.1f（三向截面腐蚀法）、悬空 ≤%.1f（相邻层）——官方底板区不判" % (a.min_wall, a.max_overhang))
        er = a.min_wall / 2 - 0.02

        def excl(axis, c):
            """官方底板在该截面上的矩形（要从判定里扣掉）。"""
            if axis == 2:
                return plate_rect if 0 < c <= PL_ZMAX else None
            if axis == 0:
                return box(PL_YMIN, 0, PL_YMAX, PL_ZMAX) if PL_XMIN <= c <= PL_XMAX else None
            return box(PL_XMIN, 0, PL_XMAX, PL_ZMAX) if PL_YMIN <= c <= PL_YMAX else None

        def thin_check(S, m, nm, use_excl):
            found = []
            for axis, lab in ((2, "Z"), (0, "X"), (1, "Y")):
                lo, hi = m.bounds[0][axis], m.bounds[1][axis]
                for c in z_levels(lo + 0.15, hi - 0.15, 0.5 if axis == 2 else 1.0):
                    s = S.solid(axis, c)
                    if s.is_empty:
                        continue
                    # 先在完整截面上腐蚀（否则与底板相连的 1.2 壁会被切窄误判），再把底板区从「薄」结果里扣掉
                    thick = s.buffer(-er).buffer(er + 0.02)
                    thin = polys_only(s.difference(thick))
                    ex = excl(axis, c) if use_excl else None
                    if ex is not None and not thin.is_empty:
                        thin = polys_only(thin.difference(ex.buffer(0.3)))
                    for p in parts(thin):
                        b = p.bounds
                        ext = max(b[2] - b[0], b[3] - b[1])
                        if p.area > 0.5 and ext > 2.0:
                            found.append((lab, c, p.area, b, ext))
            if found:
                found.sort(key=lambda f: -f[2])
                R.fail("%s 有 %d 处壁 < %.1f mm；最大三处：" % (nm, len(found), a.min_wall))
                for lab, c, ar, b, ext in found[:3]:
                    oth = {"Z": "X/Y", "X": "Y/Z", "Y": "X/Z"}[lab]
                    R.fail("  %s=%.2f 截面：%.1f mm² 长 %.1f，%s 范围 [%.2f,%.2f]/[%.2f,%.2f]" % (lab, c, ar, ext, oth, b[0], b[2], b[1], b[3]))
            else:
                R.info("%s 三向截面无 < %.1f mm 薄壁（官方底板区除外）" % (nm, a.min_wall))

        thin_check(ST, tray, "托盘", True)
        if SB is not None:
            thin_check(SB, bezel, "压框", False)
        # 悬空（只判托盘，Z 朝上打印）
        oh = []
        zlo, zhi = tray.bounds[0][2], tray.bounds[1][2]
        prev_z = None
        for z in z_levels(zlo + 0.25, zhi - 0.05, 0.5):
            if prev_z is not None:
                s_up, s_dn = ST.z(z), ST.z(prev_z)
                ex = excl(2, z)
                if not s_up.is_empty:
                    un = polys_only(s_up.difference(s_dn.buffer(a.max_overhang + 0.05)))
                    if ex is not None and not un.is_empty:
                        un = polys_only(un.difference(ex.buffer(0.05)))
                    if un.area > 0.1:
                        oh.append((z, un.area, un.bounds))
            prev_z = z
        if oh:
            R.fail("托盘有 %d 层出现 > %.1f mm 的无支撑悬空/桥：" % (len(oh), a.max_overhang))
            for z, ar, b in sorted(oh, key=lambda o: -o[1])[:3]:
                R.fail("  Z=%.2f 无支撑 %.2f mm² 于 %s" % (z, ar, fmt_bounds(b)))
        else:
            R.info("托盘逐层无 > %.1f mm 悬空" % a.max_overhang)

    # ======================================================================
    # 10. 定位存在性（推导自硬要求 5「先落到环形沿上（±X 两向已定位）→ 推到止挡」与硬要求 7「两端角柱」）
    # ======================================================================
    R.start("#10", "定位存在性：环形沿顶面在 Z=0 托住四边；四个 ±X 角柱贴着 Mosaico 包络（松动 ≤0.3）；止挡")
    # (a) 环形沿：Z=−0.05 处（Mosaico 背面正下方）四条边各自 4 mm 带内有支撑 ≥ 60 %
    rim = ST.z(-0.05)
    RW = 4.0
    rim_bands = OrderedDict([
        ("-Y", (box(MOS_XMIN, MOS_YMIN, MOS_XMAX, MOS_YMIN + RW), 0, a.mos_w)),
        ("+Y", (box(MOS_XMIN, MOS_YMAX - RW, MOS_XMAX, MOS_YMAX), 0, a.mos_w)),
        ("-X", (box(MOS_XMIN, MOS_YMIN, MOS_XMIN + RW, MOS_YMAX), 1, a.mos_d)),
        ("+X", (box(MOS_XMAX - RW, MOS_YMIN, MOS_XMAX, MOS_YMAX), 1, a.mos_d)),
    ])
    for name, (band, ax, L) in rim_bands.items():
        cov = polys_only(rim.intersection(band)) if not rim.is_empty else EMPTY
        ivs = sorted((p.bounds[ax], p.bounds[ax + 2]) for p in parts(cov))
        covered, cur = 0.0, None
        for lo, hi in ivs:
            if cur is None or lo > cur[1]:
                if cur:
                    covered += cur[1] - cur[0]
                cur = [lo, hi]
            else:
                cur[1] = max(cur[1], hi)
        if cur:
            covered += cur[1] - cur[0]
        if covered / L < 0.6:
            R.fail("Mosaico %s 边下方（Z=0 面）支撑只有 %.1f / %.1f mm（%.0f%%）——落不到环形沿上" % (name, covered, L, covered / L * 100))
        else:
            R.info("%s 边下方支撑 %.1f / %.1f mm（%.0f%%）" % (name, covered, L, covered / L * 100))
    # (b) ±X 角柱：四个角（±X × 远端/模块端）在 Z∈(0.2,2] 都有贴着包络的导向面
    far_y = (MOS_YMIN - a.clr, MOS_YC - a.side_cut / 2)
    near_y = (MOS_YC + a.side_cut / 2, MOS_YMAX + a.clr)
    PLAY = 0.30
    for sx, sname in ((-1, "-X"), (1, "+X")):
        for (y0, y1), yname in ((far_y, "远端"), (near_y, "模块端")):
            xf = MOS_XMAX + a.clr if sx > 0 else MOS_XMIN - a.clr          # 包络面
            xa, xb = (xf - 0.05, xf + PLAY + 1.0) if sx > 0 else (xf - PLAY - 1.0, xf + 0.05)
            zone = box(xa, y0, xb, y1)
            found = EMPTY
            for z in (0.3, 0.8, 1.3, 1.8):
                s = ST.z(z)
                if not s.is_empty:
                    found = polys_only(unary_union([found, polys_only(s.intersection(zone))]))
            if found.is_empty or (found.bounds[3] - found.bounds[1]) < 2.0:
                R.fail("%s %s 角柱缺失：Z∈(0.2,2] 内、包络面外 %.1f mm 带里没有导向面（Y[%.1f,%.1f]）" % (sname, yname, PLAY + 1.0, y0, y1))
            else:
                # 导向面离包络面多远（=CLR 之外的额外松动）
                gap = (found.bounds[0] - xf) if sx > 0 else (xf - found.bounds[2])
                if gap > PLAY:
                    R.fail("%s %s 角柱离 Mosaico 包络 %.2f > %.2f，±X 定位松" % (sname, yname, gap, PLAY))
                else:
                    R.info("%s %s 角柱在 Y[%.1f,%.1f]，贴包络（额外松动 %.2f）" % (sname, yname, found.bounds[1], found.bounds[3], max(gap, 0)))
    # (c) 止挡：Mosaico +Y 面之外、模块外脸之前的带里（宽 = GAP − CLR），Z∈(0.2,1.5] 有无实体
    stop_zone = box(MOS_XMIN - a.clr, MOS_YMAX + a.clr - 0.05, MOS_XMAX + a.clr, min(MOD_FACE_Y + 1.5, PL_YMIN - 0.05))
    stop_found = EMPTY
    for z in (0.3, 0.7, 1.1, 1.4):
        s = ST.z(z)
        if not s.is_empty:
            stop_found = polys_only(unary_union([stop_found, polys_only(s.intersection(stop_zone))]))
    if stop_found.is_empty:
        R.warn("没有 +Y 止挡：Mosaico 推到底的位置将由官方外壳前脸或排针本体决定（GAP 由实物定）。"
               "注意：GAP=%.2f、CLR=%.2f 时止挡可用厚度只有 %.2f mm，1.2 壁的止挡必然进外壳包络（与 #2 冲突）" % (a.gap, a.clr, a.gap - a.clr))
    else:
        b = stop_found.bounds
        R.info("止挡实体在 X[%.1f,%.1f] Y[%.2f,%.2f]（是否顶到外壳看 #2）" % (b[0], b[2], b[1], b[3]))

    # ======================================================================
    print()
    nfail = R.dump()
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({k: {"title": v["title"], "status": v["status"], "lines": v["lines"]} for k, v in R.items.items()}, f, ensure_ascii=False, indent=1)
    sys.exit(1 if nfail else 0)


if __name__ == "__main__":
    main()
