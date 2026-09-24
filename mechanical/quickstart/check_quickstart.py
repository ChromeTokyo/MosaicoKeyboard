#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_quickstart.py —— 轨一（D-031）延伸托盘的机器闸门（v2，按两名审核列出的闸门漏洞补齐）。

**独立于设计者**：不读 .scad 的几何，只读导出的 STL，按硬要求逐条断言。
任何一条失败 → 退出码 1，并打印「哪条、哪里、差多少」。

依赖：python3 标准库 + numpy + trimesh + shapely（**不需要 rtree**——
不用 contains / ray / polygons_full，截面用 mesh.section().discrete 自建奇偶多边形）。

用法：
    python3 check_quickstart.py --tray extended_baseplate.stl --bezel bezel.stl
        [--plate official_plate_fullres.stl] [--shell full_square4_Document_1.stl]
        [--gap 0.5 --clr 0.15 --pin-len 6.0 --mos-w/--mos-d/--mos-t ... --disp-w 41.19 --head-d 4.0 --head-h 1.6]
        [--readme README.md --scad extended_baseplate.scad] [--json out.json] [--quick 跳过第 9 条]

坐标约定（Bambu Z 朝上）：官方底板 XY 包围盒中心置于原点，Z[0, 6.44]；Mosaico 放 −Y 侧，背面与模块背面同在 Z=0。
**底板在托盘里可以被旋转/镜像**：闸门用 8 种对称变换把官方底板 STL 套到托盘截面上，找唯一零残差解（#0），
再从底板本体几何判断「排针边」是哪条，断言它朝 −Y（Mosaico 侧）——v0.1～v0.4 r1 都错了 90°，就是这一条没人查。

闸门自己的假设（G-*，不是设计假设；数值来源见旁注）：
  G-1  模块朝 Mosaico 的外脸 Y = 官方底板（变换后）Ymin − SHELL_OVERHANG（硬要求 4：外壳比底板每侧宽 0.75）；
       外壳包络 = max(44.90 见方, 底板包围盒每侧 +0.75)（两者在横向差 0.1，取并集保守）。
  G-2  Mosaico X 中心与模块 X 中心重合（--mos-xc 可改；设计侧对应 Q1-23，#13 核它有没有登记）。
  G-3  四边保持 = **限位式**：每条前缘 1.0 带内压框材料最低点 − MOS_T = 游隙，须 ∈ [−0.05, +0.30]。
       负 = 压框先压到玻璃、坐不到柱顶（螺钉力进玻璃，审核 F3）；>0.30 = 悬空压不到（v0.2 卡舌悬空 2.5 就是这个错）。
       另要求压框本体在四根柱顶正上方的底面 ≤ 柱顶 + 0.10（硬止点在柱，不在玻璃）。
  G-4  压框允许在前缘带内向下越过屏面 ≤ 0.05（只是截面容差，不再有「预压」概念）。
  G-5  螺钉底孔有效深度 ≥ 3.0（M2×6 穿 1.6 压框剩 4.4；3.0 为下限）。
  G-6  可打印：壁 ≥ 1.2、悬空 ≤ 2.0（硬要求 6）；官方底板区不参与可打印性判定。Z 向切片强制含顶面下 0.1 与底面上 0.1。
  G-7  截面比对容差 0.05 mm；面积阈值 0.01～0.05 mm²（tessellation 噪声量级）。
  G-8  排针边判据：底板本体（台阶以上）四边相对底缘的内缩量，唯一一条内缩 < 0.2 的边 = 排针边（PCB 排针从这边悬出、
       外壳这一面开口）；其对边内缩 ≥ 2（给对侧 2×10 母座）。若给了外壳 STL，再核：外壳只有一面开口，其余三面内壁
       ≤ 底板三条内缩边 + 0.1，且排针边底缘 > 内壁（只能从开口出去）。
  G-9  外壳坐高 = 底板横向两边内缩到 ≤ 外壳内壁 的最低 Z（台阶顶），外壳顶 = 坐高 + 10.9；#2 查到外壳顶。
  G-10 装配运动学：落位 = Mosaico −Y 面靠到远端墙止面；针尖 Y = 模块外脸 − PIN_LEN；「角柱先于针尖」裕量 ≥ 0.5 才算成立，
       否则 WARN（该裕量 = (MOS_D − 34)/2 − (PIN_LEN − GAP)，被硬要求 7 锁死，设计只能标注意）；
       偏摆 = atan(2·CLR_实测 / 触针瞬间导轨重叠长)，+Y 面横向偏移 > 1.27（半针距）则 WARN「须目视对准」。
  G-11 压框—托盘装配间隙 ≥ 0.15（两 STL 叠在装配位逐层求最近距离）；后裙到 Mosaico −Y 面 ∈ (0.3, PIN_LEN−GAP−1.0]。
"""
import argparse
import json
import math
import os
import re
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


def covered_len(geom, axis):
    """连通片在 axis 方向投影区间并集长度。"""
    ivs = sorted((p.bounds[axis], p.bounds[axis + 2]) for p in parts(geom))
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
    return covered


def interiors_of(geom):
    out = []
    for p in parts(geom):
        for r in p.interiors:
            out.append(Polygon(r))
    return out


# ----------------------------------------------------------------------------
# 报告
# ----------------------------------------------------------------------------
class Report:
    def __init__(self):
        self.items = OrderedDict()
        self._cur = None

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

    def manual(self, msg):
        self.items[self._cur]["lines"].append(("manual", msg))

    def status(self, key):
        return self.items[key]["status"]

    def dump(self):
        nfail = nwarn = 0
        for key, it in self.items.items():
            st = it["status"]
            if st == "FAIL":
                nfail += 1
            if st == "WARN":
                nwarn += 1
            print("[%s] %s %s" % (st, key, it["title"]))
            for lvl, msg in it["lines"]:
                print("        %s %s" % ({"FAIL": "✗", "WARN": "!", "info": "·", "manual": "👁"}[lvl], msg))
        print("-" * 78)
        print("结果：%d 条失败 / %d 条；%d 条 WARN（WARN 不拦，但要在 README 里回应）" % (nfail, len(self.items), nwarn))
        return nfail


# ----------------------------------------------------------------------------
# 主体
# ----------------------------------------------------------------------------
def load_mesh(path):
    m = trimesh.load(path, force="mesh")
    if not isinstance(m, trimesh.Trimesh):
        raise SystemExit("不是三角网格：%s" % path)
    return m


def sym_transforms():
    """8 种平面对称变换：绕 Z 转 0/90/180/270 × 是否镜像 X。"""
    out = []
    for k in range(4):
        for mir in (False, True):
            ang = k * 90
            c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
            Mx = np.diag([-1.0, 1.0, 1.0]) if mir else np.eye(3)
            M = np.eye(4)
            M[:3, :3] = Rz @ Mx
            out.append(("rot%d%s" % (ang, "+mirX" if mir else ""), M))
    return out


def main():
    ap = argparse.ArgumentParser(description="轨一延伸托盘机器闸门（v0.4 硬要求，v2）")
    ap.add_argument("--tray", required=True, help="托盘 STL")
    ap.add_argument("--bezel", default=None, help="压框 STL（可选；缺省视为无压框）")
    ap.add_argument("--plate", default=None, help="官方底板全分辨率 STL（缺省找脚本同目录 official_plate_fullres.stl）")
    ap.add_argument("--shell", default=None, help="官方外壳 STL（缺省找 ../../references/official-module-interaction/full_square4_Document_1.stl）")
    ap.add_argument("--readme", default=None, help="README.md（缺省脚本同目录；#13 假设登记核对）")
    ap.add_argument("--scad", default=None, help="设计 .scad（缺省脚本同目录；只读其 ASSUMPTION 标签，不读几何）")
    ap.add_argument("--mos-w", type=float, default=45.19, help="Mosaico X 向宽（AS-01）")
    ap.add_argument("--mos-d", type=float, default=45.19, help="Mosaico Y 向深（AS-01）")
    ap.add_argument("--mos-t", type=float, default=11.48, help="Mosaico 厚（AS-01）")
    ap.add_argument("--mos-xc", type=float, default=0.0, help="Mosaico X 中心（G-2 / Q1-23）")
    ap.add_argument("--clr", type=float, default=0.15, help="包络单边间隙（Q1-4；须与设计一致）")
    ap.add_argument("--gap", type=float, default=0.50, help="模块外脸到 Mosaico 面间隙（Q1-2）")
    ap.add_argument("--pin-len", type=float, default=6.0, help="排针针尖露出模块外脸长度（Q1-13）")
    ap.add_argument("--disp-w", type=float, default=41.19, help="显示区见方（居中）")
    ap.add_argument("--head-d", type=float, default=4.0, help="螺钉盘头直径")
    ap.add_argument("--head-h", type=float, default=1.6, help="螺钉盘头高")
    ap.add_argument("--shell-foot", type=float, default=44.90, help="官方外壳外形见方")
    ap.add_argument("--shell-h", type=float, default=10.90, help="官方外壳高")
    ap.add_argument("--shell-overhang", type=float, default=0.75, help="外壳比底板每侧宽（Q1-1）")
    ap.add_argument("--side-cut", type=float, default=34.0, help="±X 功能区沿 Y 中央留空长度（Q1-6）")
    ap.add_argument("--func-z", type=float, nargs=2, default=(2.0, 6.0), help="±X 功能区 Z 区间")
    ap.add_argument("--pin-z", type=float, nargs=2, default=(2.0, 9.0), help="排针让位 Z 区间")
    ap.add_argument("--hole-d", type=float, default=1.7, help="自攻底孔直径")
    ap.add_argument("--hole-tol", type=float, default=0.2)
    ap.add_argument("--post-wall", type=float, default=1.5, help="立柱孔周最小壁")
    ap.add_argument("--hole-depth", type=float, default=3.0, help="底孔最小有效深度（G-5）")
    ap.add_argument("--n-holes", type=int, default=4)
    ap.add_argument("--bezel-max-t", type=float, default=1.6, help="压框最大厚（高出屏面上限）")
    ap.add_argument("--press-max", type=float, default=1.0, help="压框压前缘最大宽度（名义）")
    ap.add_argument("--press-frac", type=float, default=0.60, help="每边前缘带最低覆盖比例")
    ap.add_argument("--play-max", type=float, default=0.30, help="限位游隙上限（G-3）")
    ap.add_argument("--min-wall", type=float, default=1.2)
    ap.add_argument("--max-overhang", type=float, default=2.0)
    ap.add_argument("--max-bodies", type=int, default=None, help="托盘体数上限（含内腔；超出 WARN）")
    ap.add_argument("--json", default=None, help="把结果另存 JSON")
    ap.add_argument("--quick", action="store_true", help="跳过第 9 条可打印性（慢）")
    a = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    plate_path = a.plate or os.path.join(here, "official_plate_fullres.stl")
    shell_path = a.shell or os.path.join(here, "..", "..", "references", "official-module-interaction", "full_square4_Document_1.stl")
    readme_path = a.readme or os.path.join(here, "README.md")
    scad_path = a.scad or os.path.join(here, "extended_baseplate.scad")

    tray = load_mesh(a.tray)
    bezel = load_mesh(a.bezel) if a.bezel else None
    plate = load_mesh(plate_path)
    shell = load_mesh(shell_path) if os.path.exists(shell_path) else None

    # 官方底板置中（XY 包围盒中心 → 原点；Zmin → 0）
    pb = plate.bounds
    plate_c = plate.copy()
    plate_c.apply_translation([-(pb[0][0] + pb[1][0]) / 2, -(pb[0][1] + pb[1][1]) / 2, -pb[0][2]])

    ST = Slicer(tray, "tray")
    SB = Slicer(bezel, "bezel") if bezel is not None else None
    R = Report()
    A_TOL = 0.01
    E_TOL = 0.02
    MOS_T = a.mos_t

    print("=" * 78)
    print("check_quickstart v2 —— 轨一延伸托盘机器闸门")
    print("托盘  : %s  面 %d  包围盒 X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]" % (
        a.tray, len(tray.faces), *[tray.bounds[i][j] for j in range(3) for i in range(2)]))
    if bezel is not None:
        print("压框  : %s  面 %d  包围盒 X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]" % (
            a.bezel, len(bezel.faces), *[bezel.bounds[i][j] for j in range(3) for i in range(2)]))
    else:
        print("压框  : （未提供）")
    print("底板  : %s  置中后 X±%.3f Y±%.3f Z[0,%.2f]" % (plate_path, plate_c.bounds[1][0], plate_c.bounds[1][1], plate_c.bounds[1][2]))
    print("外壳  : %s" % (shell_path if shell is not None else "（未找到，跳过外壳一致性）"))

    # ======================================================================
    # 0. 底板定向（审核最大的洞：闸门与 scad 共用同一错误假设）
    # ======================================================================
    R.start("#0", "底板定向：8 种对称变换里唯一零残差解；排针边（本体不内缩的那条）必须朝 −Y（Mosaico 侧）；外壳开口一致")
    pbb = plate_c.bounds
    probe_box = box(pbb[0][0] - 0.4, pbb[0][1] - 0.4, pbb[1][0] + 0.4, pbb[1][1] + 0.4)   # 只比底板区（角柱在其外）
    tray_z3 = polys_only(ST.z(3.0).intersection(probe_box))
    tray_z15 = polys_only(ST.z(1.5).intersection(probe_box))
    fits = []
    for name, M in sym_transforms():
        pk = plate_c.copy()
        pk.apply_transform(M)
        SPk = Slicer(pk, "plate")
        d = 0.0
        for z, tz in ((3.0, tray_z3), (1.5, tray_z15)):
            pz = SPk.z(z)
            d += polys_only(tz.symmetric_difference(pz)).area if not (tz.is_empty and pz.is_empty) else 0.0
        fits.append((d, name, pk, SPk))
    fits.sort(key=lambda f: f[0])
    best_d, best_name, plate_k, SP = fits[0]
    second = fits[1][0]
    ref_area = SP.z(3.0).area + SP.z(1.5).area
    R.info("变换残差（Z=3 与 Z=1.5 截面对称差 mm²，底板两层截面共 %.0f）：" % ref_area + "  ".join("%s %.2f" % (n, d) for d, n, _, _ in fits))
    if best_d > 0.02 * ref_area:
        R.fail("没有一种变换能把官方底板 STL 套到托盘上（最好 %s 残差 %.2f mm² > 2%%）——托盘里的底板被改过或位置不对" % (best_name, best_d))
    elif second < 3 * best_d + 5:
        R.fail("底板定向不唯一：%s %.2f 与次解 %.2f 分不开" % (best_name, best_d, second))
    else:
        R.info("底板在托盘里的变换 = %s（残差 %.2f mm² = %.2f%%，Manifold 重三角化噪声；次解 %.2f）" % (best_name, best_d, 100 * best_d / ref_area, second))

    pcb = plate_k.bounds
    PL_XMIN, PL_YMIN, PL_ZMIN = pcb[0]
    PL_XMAX, PL_YMAX, PL_ZMAX = pcb[1]
    plate_rect = box(PL_XMIN, PL_YMIN, PL_XMAX, PL_YMAX)

    # 底板本体层与台阶（G-8 / G-9）
    zscan = []
    for z in z_levels(0.3, PL_ZMAX - 0.1, 0.1):
        s = SP.z(z)
        zscan.append((z, s.area, s.bounds if not s.is_empty else None))
    full_area = max(ar for _, ar, _ in zscan)
    body_levels = [(z, ar, b) for z, ar, b in zscan if ar > 0.5 * full_area and b is not None]
    body_top_z = max(z for z, _, _ in body_levels)
    body_z, _, body_b = body_levels[-1]
    inset = OrderedDict([
        ("-X", body_b[0] - PL_XMIN), ("+X", PL_XMAX - body_b[2]),
        ("-Y", body_b[1] - PL_YMIN), ("+Y", PL_YMAX - body_b[3]),
    ])
    R.info("底板本体（Z≈%.1f，顶 %.1f）四边相对底缘内缩：%s" % (body_z, body_top_z + 0.05, "  ".join("%s %.3f" % (k, v) for k, v in inset.items())))
    flush = [k for k, v in inset.items() if v < 0.2]
    header_edge = flush[0] if len(flush) == 1 else None
    opp = {"-X": "+X", "+X": "-X", "-Y": "+Y", "+Y": "-Y"}
    if header_edge is None:
        R.fail("本体不内缩的边有 %d 条（%s），判不出排针边（G-8）" % (len(flush), flush))
    else:
        if inset[opp[header_edge]] < 2.0:
            R.warn("排针边对边内缩只有 %.2f（<2，对侧 2×10 母座让位应 ≥2）" % inset[opp[header_edge]])
        if header_edge != "-Y":
            R.fail("**底板方向错**：排针边（本体不内缩、外壳开口侧）在 %s，应朝 −Y（Mosaico 侧）。托盘把 Mosaico 顶在模块的整墙面上，排针从 %s 边凌空伸出" % (header_edge, header_edge))
        else:
            R.info("排针边 = −Y（本体到底缘 %.3f，不内缩；对边 +Y 内缩 %.3f 给对侧母座）→ 朝 Mosaico，正确" % (PL_YMIN + inset["-Y"] * 0 - PL_YMIN + abs(body_b[1]), inset["+Y"]))
    # 台阶：横向（±X）内缩到本体的最低 Z
    ledge_z = None
    for z, ar, b in body_levels:
        if b is not None and (b[0] - PL_XMIN) > 0.3 and (PL_XMAX - b[2]) > 0.3:
            ledge_z = z
            break
    shell_inner_half = None
    if shell is not None:
        sb = shell.bounds
        shell_c = shell.copy()
        shell_c.apply_translation([-(sb[0][0] + sb[1][0]) / 2, -(sb[0][1] + sb[1][1]) / 2, -sb[0][2]])
        SS = Slicer(shell_c, "shell")
        H = (sb[1][0] - sb[0][0]) / 2
        Hs = sb[1][2] - sb[0][2]
        # 每面墙在中央 ±10 带内的材料（Z_stl 从 40 % 到 95 % 高）
        open_count = {"+X": 0, "-X": 0, "+Y": 0, "-Y": 0}
        nlev = 0
        for z in z_levels(0.4 * Hs, 0.95 * Hs, 0.5):
            s = SS.z(z)
            nlev += 1
            for side, g in (("+X", box(H - 1.6, -10, H + 1, 10)), ("-X", box(-H - 1, -10, -H + 1.6, 10)),
                            ("+Y", box(-10, H - 1.6, 10, H + 1)), ("-Y", box(-10, -H - 1, 10, -H + 1.6))):
                if polys_only(s.intersection(g)).area < 0.05:
                    open_count[side] += 1
        open_sides = [k for k, v in open_count.items() if v >= 0.6 * nlev]
        s9 = SS.z(0.8 * Hs)
        inner_face = {}
        for side, g in (("+X", box(H - 3.0, -10, H + 1, 10)), ("-X", box(-H - 1, -10, -H + 3.0, 10)),
                        ("+Y", box(-10, H - 3.0, 10, H + 1)), ("-Y", box(-10, -H - 1, 10, -H + 3.0))):
            if side in open_sides:
                continue
            m = polys_only(s9.intersection(g))
            if m.is_empty:
                continue
            b = m.bounds
            inner_face[side] = {"+X": b[0], "-X": -b[2], "+Y": b[1], "-Y": -b[3]}[side]
        s8 = SS.z(0.75 * Hs)
        open_w = None
        if len(open_sides) == 1:
            side = open_sides[0]
            ts = []
            for t in np.arange(-H + 0.5, H - 0.5, 0.25):
                if side in ("+X", "-X"):
                    g = box(H - 1.6, t - 0.12, H + 0.5, t + 0.12) if side == "+X" else box(-H - 0.5, t - 0.12, -H + 1.6, t + 0.12)
                else:
                    g = box(t - 0.12, H - 1.6, t + 0.12, H + 0.5) if side == "+Y" else box(t - 0.12, -H - 0.5, t + 0.12, -H + 1.6)
                if polys_only(s8.intersection(g)).area < 0.01:
                    ts.append(t)
            if ts:
                open_w = (min(ts), max(ts))
        if len(open_sides) != 1:
            R.warn("外壳 STL 开口面数 = %d（%s），无法用外壳核排针边" % (len(open_sides), open_sides))
        else:
            side = open_sides[0]
            lateral = ["+Y", "-Y"] if side in ("+X", "-X") else ["+X", "-X"]
            oppo = opp[side]
            R.info("外壳 STL：外形 %.2f 见方×%.2f 高，唯一开口面 %s（外壳自身坐标，打印时前脸朝下、装配时翻面），开口 t∈[%.2f,%.2f] 宽 %.1f；内壁：%s" % (
                2 * H, Hs, side, open_w[0] if open_w else float("nan"), open_w[1] if open_w else float("nan"),
                (open_w[1] - open_w[0]) if open_w else float("nan"), "  ".join("%s %.3f" % (k, v) for k, v in inner_face.items())))
            if header_edge is not None and all(k in inner_face for k in lateral + [oppo]):
                idx = {"-X": 0, "-Y": 1, "+X": 2, "+Y": 3}
                hdr_ext = abs(body_b[idx[header_edge]])
                lat_plate = [abs(body_b[idx[k]]) for k in inset if k not in (header_edge, opp[header_edge])]
                opp_plate = abs(body_b[idx[opp[header_edge]]])
                lat_shell = min(inner_face[k] for k in lateral)
                opp_shell = inner_face[oppo]
                ok = hdr_ext > lat_shell + 0.05 and all(v <= lat_shell + 0.1 for v in lat_plate) and opp_plate <= opp_shell + 0.1
                if ok:
                    R.info("一致性：排针边底板本体 %.3f > 外壳侧壁内面 %.3f（只能从开口出去）；底板两侧 %.3f/%.3f ≤ 侧壁 %.3f、对边 %.3f ≤ 对壁 %.3f → 外壳开口 = 排针边" % (
                        hdr_ext, lat_shell, lat_plate[0], lat_plate[1], lat_shell, opp_plate, opp_shell))
                else:
                    R.fail("外壳与底板套不上：排针边本体 %.3f vs 侧壁 %.3f；底板两侧 %s vs 侧壁 %.3f；对边 %.3f vs 对壁 %.3f" % (
                        hdr_ext, lat_shell, ["%.3f" % v for v in lat_plate], lat_shell, opp_plate, opp_shell))
    if ledge_z is None:
        SHELL_Z0 = 0.0
        R.warn("底板横向未见台阶，按外壳落 Z=0 处理（G-9）")
    else:
        SHELL_Z0 = ledge_z - 0.05
        R.info("底板横向台阶顶 Z≈%.2f（Z<%.2f 底缘 X±%.3f；以上本体 X±%.3f）→ 外壳坐 Z≈%.2f、顶 ≈%.2f（比屏面 %.2f 高 %.2f）（G-9）" % (
            SHELL_Z0, SHELL_Z0, PL_XMAX, body_b[2], SHELL_Z0, SHELL_Z0 + a.shell_h, MOS_T, SHELL_Z0 + a.shell_h - MOS_T))
    SHELL_TOP = SHELL_Z0 + a.shell_h

    # ---- 派生几何（G-1 / G-2）----
    OV = a.shell_overhang
    ENV_XMIN = min(-a.shell_foot / 2, PL_XMIN - OV)
    ENV_XMAX = max(a.shell_foot / 2, PL_XMAX + OV)
    ENV_YMIN = min(-a.shell_foot / 2, PL_YMIN - OV)
    ENV_YMAX = max(a.shell_foot / 2, PL_YMAX + OV)
    MOD_FACE_Y = ENV_YMIN
    MOS_YMAX = MOD_FACE_Y - a.gap
    MOS_YMIN = MOS_YMAX - a.mos_d
    MOS_YC = (MOS_YMIN + MOS_YMAX) / 2
    MOS_XMIN = a.mos_xc - a.mos_w / 2
    MOS_XMAX = a.mos_xc + a.mos_w / 2
    mos_rect = box(MOS_XMIN, MOS_YMIN, MOS_XMAX, MOS_YMAX)
    mos_env = box(MOS_XMIN - a.clr, MOS_YMIN - a.clr, MOS_XMAX + a.clr, MOS_YMAX + a.clr)
    env_rect = box(ENV_XMIN, ENV_YMIN, ENV_XMAX, ENV_YMAX)
    disp_rect = box(a.mos_xc - a.disp_w / 2, MOS_YC - a.disp_w / 2, a.mos_xc + a.disp_w / 2, MOS_YC + a.disp_w / 2)
    PIN_TIP_Y = MOD_FACE_Y - a.pin_len

    print("派生  : 底板变换 %s → X[%.3f,%.3f] Y[%.3f,%.3f]；外壳包络 X[%.3f,%.3f] Y[%.3f,%.3f] Z(0,%.2f]（坐 %.2f）；模块外脸 Y=%.3f；GAP=%.2f；针尖 Y=%.3f" % (
        best_name, PL_XMIN, PL_XMAX, PL_YMIN, PL_YMAX, ENV_XMIN, ENV_XMAX, ENV_YMIN, ENV_YMAX, SHELL_TOP, SHELL_Z0, MOD_FACE_Y, a.gap, PIN_TIP_Y))
    print("        Mosaico X[%.3f,%.3f] Y[%.3f,%.3f] Z[0,%.2f]；包络 +CLR %.2f → X[%.3f,%.3f] Y[%.3f,%.3f]；显示区 %.2f 见方" % (
        MOS_XMIN, MOS_XMAX, MOS_YMIN, MOS_YMAX, MOS_T, a.clr,
        MOS_XMIN - a.clr, MOS_XMAX + a.clr, MOS_YMIN - a.clr, MOS_YMAX + a.clr, a.disp_w))
    print("=" * 78)
    print()

    # ---- 预分析：托盘底孔、压框过孔/沉台（#3/#4/#8/#12 共用）----
    post_top = tray.bounds[1][2]

    def analyze_tray_holes():
        holes = []
        for z in z_levels(0.15, post_top - 0.05, 0.25):
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
                        continue
                    others = [rings[j] for j in range(len(rings)) if j != ri]
                    shell_only = Polygon(p.exterior, others)
                    if not shell_only.is_valid:
                        shell_only = shell_only.buffer(0)
                    wall = LinearRing(ring).distance(shell_only.boundary)
                    for h in holes:
                        if abs(h["cx"] - cx) < 0.3 and abs(h["cy"] - cy) < 0.3:
                            h["zs"].append(z); h["ds"].append(d); h["walls"].append(wall)
                            break
                    else:
                        holes.append({"cx": cx, "cy": cy, "zs": [z], "ds": [d], "walls": [wall]})
        return holes

    def analyze_bezel_holes():
        """压框上的竖孔：按 XY 归组，记录每层直径 → 过孔径、沉台径、沉台底 Z。"""
        if SB is None:
            return []
        groups = []
        zlo, zhi = bezel.bounds[0][2], bezel.bounds[1][2]
        for z in z_levels(zlo + 0.05, zhi - 0.03, 0.05):
            s = SB.z(z)
            for hp in interiors_of(s):
                d = 2 * math.sqrt(max(hp.area, 0) / math.pi)
                if not (1.2 <= d <= 8.0):
                    continue
                cx, cy = hp.centroid.x, hp.centroid.y
                for g in groups:
                    if abs(g["cx"] - cx) < 0.4 and abs(g["cy"] - cy) < 0.4:
                        g["zd"].append((z, d))
                        break
                else:
                    groups.append({"cx": cx, "cy": cy, "zd": [(z, d)]})
        out = []
        for g in groups:
            zd = sorted(g["zd"])
            ds = [d for _, d in zd]
            d_thru = min(ds)
            d_max = max(ds)
            cb_floor = None
            cb_d = None
            if d_max > d_thru + 0.5:
                big = [(z, d) for z, d in zd if d > d_thru + 0.5]
                cb_floor = min(z for z, _ in big) - 0.025
                cb_d = float(np.median([d for _, d in big]))
            out.append({"cx": g["cx"], "cy": g["cy"], "d_thru": d_thru, "cb_d": cb_d, "cb_floor": cb_floor,
                        "z0": zd[0][0], "z1": zd[-1][0]})
        return out

    tray_holes = analyze_tray_holes()
    bez_holes = analyze_bezel_holes()

    # ======================================================================
    # 1. 脚印干涉
    # ======================================================================
    R.start("#1", "脚印干涉：Z∈[0,%.2f] 内托盘实体 ∩ Mosaico 包络（+CLR %.2f）为空" % (MOS_T, a.clr))
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
        # 压框：Z ≤ MOS_T − 0.05 全区不许进包络（不再有预压概念，G-4）
        bad = []
        for z in z_levels(0.1, MOS_T - 0.06, 0.2):
            s = SB.z(z)
            if s.is_empty:
                continue
            inter = polys_only(s.intersection(probe))
            if inter.area > A_TOL:
                bad.append((z, inter.area, inter.bounds))
        if bad:
            R.fail("压框在屏面以下钻进 Mosaico 包络：%d 个截面，例 Z=%.2f %.2f mm² %s" % (len(bad), bad[0][0], bad[0][1], fmt_bounds(bad[0][2])))
    if R.status("#1") == "PASS":
        R.info("检查 %d 个 Z 截面 + 全部顶点，均在包络外" % len(zs))

    # ======================================================================
    # 2. 官方外壳脚印
    # ======================================================================
    R.start("#2", "官方外壳脚印：Z∈(0,%.2f] 内、外壳包络里，托盘截面 ≡ 官方底板截面（不加不减）；压框不进包络" % SHELL_TOP)
    zs = z_levels(0.1, SHELL_TOP - 0.05, 0.25, extra=(0.2, 0.5, 1.0, 1.15, 1.25, 1.5, 1.7, 1.95, 2.5, 3.5, 4.5, 5.5, 6.2, 6.4, 6.6, 7.5, 8.5, 9.5, 10.5, 10.85, 11.5, 12.0))
    extra_hits, miss_hits, bez_hits = [], [], []
    for z in zs:
        t = ST.z(z)
        tin = polys_only(t.intersection(env_rect)) if not t.is_empty else EMPTY
        p = SP.z(z) if z <= PL_ZMAX else EMPTY
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
    if R.status("#2") == "PASS":
        R.info("%d 个 Z 截面上，包络内托盘 ≡ 官方底板（容差 0.05 mm）；外壳顶 %.2f 高于压框底 %s → 靠横向让位，不靠高度差" % (
            len(zs), SHELL_TOP, ("%.2f" % bezel.bounds[0][2]) if bezel is not None else "—"))
        if bezel is not None:
            # 压框到外壳包络的横向最近距离（在外壳 Z 范围内）
            dmin = None
            for z in z_levels(max(SHELL_Z0 + 0.1, bezel.bounds[0][2] + 0.05), min(SHELL_TOP, bezel.bounds[1][2]) - 0.05, 0.4):
                b = SB.z(z)
                if not b.is_empty:
                    d = b.distance(env_rect)
                    dmin = d if dmin is None else min(dmin, d)
            if dmin is not None:
                R.info("压框到外壳包络横向最近 %.2f mm（外壳 Z 范围内）" % dmin)

    # ======================================================================
    # 3. 不高出屏面
    # ======================================================================
    R.start("#3", "不高出屏面：托盘 Zmax ≤ %.2f；压框 Zmax ≤ %.2f（厚 ≤ %.1f）；螺钉盘头高度另报" % (MOS_T, MOS_T + a.bezel_max_t, a.bezel_max_t))
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
        # 外缘倒角：顶面截面 vs 底部截面外轮廓的内缩量
        s_top = SB.z(bz - 0.05)
        s_mid = SB.z(bz - a.bezel_max_t + 0.3) if bz - a.bezel_max_t + 0.3 < bz - 0.05 else s_top
        if not s_top.is_empty and not s_mid.is_empty:
            bt, bm = s_top.bounds, s_mid.bounds
            ch = {"-X": bt[0] - bm[0], "+X": bm[2] - bt[2], "-Y": bt[1] - bm[1], "+Y": bm[3] - bt[3]}
            R.info("压框外缘倒角（顶面比本体内缩）：%s（+Y 排针侧 %s）" % (
                "  ".join("%s %.2f" % (k, v) for k, v in ch.items()), "有" if ch["+Y"] > 0.2 else "无——1.2 宽夹死，设计声明"))
            if max(ch["-X"], ch["+X"], ch["-Y"]) < 0.2:
                R.fail("压框外缘无倒角（硬要求 2 要求外缘倒角）")
        # 螺钉盘头
        if bez_holes:
            heads = []
            for h in bez_holes:
                floor_z = h["cb_floor"] if h["cb_floor"] is not None else bz
                heads.append((h, floor_z, floor_z + a.head_h))
            hmax = max(t for _, _, t in heads)
            desc = "；".join("@(%.1f,%.1f) 过孔 Ø%.2f%s 盘头顶 %.2f" % (
                h["cx"], h["cy"], h["d_thru"], (" 沉台 Ø%.2f 底 %.2f" % (h["cb_d"], fz)) if h["cb_d"] else " 无沉台", t) for h, fz, t in heads)
            R.info("螺钉盘头（Ø%.1f×%.1f 假设）：%s" % (a.head_d, a.head_h, desc))
            if hmax > MOS_T + a.bezel_max_t + 1e-3:
                R.warn("盘头顶最高 Z=%.2f，高出屏面 %.2f > %.1f：硬要求 2 字面只放行压框本身；四角、Mosaico 脚印外——**需用户认可或改沉头螺钉**" % (hmax, hmax - MOS_T, a.bezel_max_t))
            for h, fz, t in heads:
                if h["cb_d"] is not None and h["cb_d"] < a.head_d + 0.1:
                    R.fail("沉台 Ø%.2f < 盘头 Ø%.1f+0.1，盘头坐不进去" % (h["cb_d"], a.head_d))
                # 盘头是否完全落在压框顶面平台内（不悬出倒角/外缘）
                plat = SB.z(fz + 0.03) if h["cb_d"] is None else SB.z(fz - 0.03)
                disc = Point(h["cx"], h["cy"]).buffer(a.head_d / 2)
                if not plat.is_empty:
                    outside = polys_only(disc.difference(polys_only(plat).buffer(0.02)))
                    ring_out = polys_only(outside.difference(Point(h["cx"], h["cy"]).buffer(h["d_thru"] / 2 + 0.05)))
                    if ring_out.area > 0.05:
                        R.fail("盘头 @(%.1f,%.1f) 有 %.2f mm² 悬出压框承面（倒角/外缘）" % (h["cx"], h["cy"], ring_out.area))
                if disc.intersects(env_rect.buffer(-E_TOL)):
                    R.fail("盘头 @(%.1f,%.1f) 伸进外壳脚印" % (h["cx"], h["cy"]))

    # ======================================================================
    # 4. 四边保持（限位式，G-3）
    # ======================================================================
    R.start("#4", "四边保持（限位式）：压框在四条前缘各覆盖 ≥%d%%、压宽 ≤%.1f；每边游隙 ∈[−0.05,%.2f]；压框本体坐柱顶（硬止点）；不进显示区" % (
        int(a.press_frac * 100), a.press_max, a.play_max))
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
        zs_cov = z_levels(MOS_T + 0.03, MOS_T + 2.0, 0.1)
        slices_cov = [(z, SB.z(z)) for z in zs_cov]
        union_all = polys_only(unary_union([s for _, s in slices_cov if not s.is_empty])) if any(not s.is_empty for _, s in slices_cov) else EMPTY
        zs_fine = z_levels(MOS_T - 0.34, MOS_T + 0.6, 0.02)
        plays = {}
        for name, (band, ax, L) in bands.items():
            cov = polys_only(union_all.intersection(band)) if not union_all.is_empty else EMPTY
            covered = covered_len(cov, ax)
            frac = covered / L
            zlow = None
            for z in zs_fine:
                s = SB.z(z)
                if not s.is_empty and polys_only(s.intersection(band)).area > A_TOL:
                    zlow = z
                    break
            if frac < a.press_frac:
                R.fail("%s 前缘只被压住 %.1f mm / %.1f（%.0f%% < %d%%）" % (name, covered, L, frac * 100, int(a.press_frac * 100)))
                continue
            if zlow is None:
                R.fail("%s 前缘带上方 0.6 mm 内没有压框材料（悬空 > 0.6）" % name)
                continue
            play = zlow - MOS_T
            plays[name] = play
            if play < -0.05:
                R.fail("%s 前缘：压框最低材料 Z=%.2f 低于屏面 %.2f → 压框先压玻璃、坐不到柱顶，螺钉全部拉力进玻璃边（审核 F3）" % (name, zlow, -play))
            elif play > a.play_max + 0.01:
                R.fail("%s 前缘被覆盖 %.0f%%，但压框最低点 Z=%.2f 悬空 %.2f > %.2f，压不到" % (name, frac * 100, zlow, play, a.play_max))
            else:
                R.info("%s 前缘覆盖 %.1f mm / %.1f（%.0f%%），压框最低材料 Z=%.2f → 名义游隙 %.2f" % (name, covered, L, frac * 100, zlow, play))
        if plays:
            pn = min(plays.values())
            R.info("MOS_T 灵敏度（AS-01 未实测）：实测 %.2f/%.2f/%.2f → 最小游隙 %.2f/%.2f/%.2f（负 = 压框坐不到柱顶；> %.2f = 松）" % (
                MOS_T - 0.3, MOS_T, MOS_T + 0.3, pn + 0.3, pn, pn - 0.3, a.play_max))
            lo_ok = MOS_T + pn - a.play_max
            hi_ok = MOS_T + pn + 0.05
            R.info("→ 本压框可用的 Mosaico 实测厚度窗口 [%.2f, %.2f]；出窗则改 LIP_RECESS 重打压框（8 层）" % (lo_ok, hi_ok))
        # 硬止点：压框本体在每根柱顶正上方的底面 ≤ 柱顶 + 0.10
        if tray_holes:
            worst_dz = None
            for h in tray_holes:
                pts = [Point(h["cx"] + dx, h["cy"] + dy) for dx, dy in ((1.6, 0), (-1.6, 0), (0, 1.6), (0, -1.6))]
                zb = None
                for z in z_levels(bezel.bounds[0][2] + 0.03, bezel.bounds[1][2] - 0.03, 0.05):
                    s = SB.z(z)
                    if not s.is_empty and all(s.buffer(0.02).contains(p) for p in pts):
                        zb = z
                        break
                if zb is None:
                    R.fail("压框在柱 @(%.1f,%.1f) 正上方没有承面" % (h["cx"], h["cy"]))
                    continue
                dz = zb - post_top
                worst_dz = dz if worst_dz is None else max(worst_dz, dz)
            if worst_dz is not None:
                if worst_dz > 0.10 + 0.03:
                    R.fail("压框本体底比柱顶高 %.2f > 0.10：拧紧时没有硬止点，从压到屏面到坐到柱顶之间螺钉力全进玻璃边（审核 F3/F4）" % worst_dz)
                else:
                    R.info("硬止点：压框本体底 Z=%.2f 坐在柱顶 Z=%.2f（差 %.2f ≤ 0.10）→ 螺钉力进 PLA 柱，不进玻璃；柱顶低于屏面 %.2f" % (
                        post_top + worst_dz, post_top, worst_dz, MOS_T - post_top))
        # 4b 压宽 ≤ press_max（名义）+ X 游隙下的实际范围 + 显示区
        inner = mos_rect.buffer(-pm - E_TOL)
        over = polys_only(union_all.intersection(inner)) if not union_all.is_empty else EMPTY
        if over.area > A_TOL:
            R.fail("压框盖到屏面内侧 > %.1f mm：%.2f mm² 于 %s，最深 %.2f mm" % (
                pm, over.area, fmt_bounds(over.bounds), max_penetration(over, mos_rect.buffer(-pm))))
        wins = interiors_of(union_all)
        if wins:
            win = max(wins, key=lambda p: p.area)
            wb = win.bounds
            press = {"-X": wb[0] - MOS_XMIN, "+X": MOS_XMAX - wb[2], "-Y": wb[1] - MOS_YMIN, "+Y": MOS_YMAX - wb[3]}
            R.info("内窗 %s → 名义压边 %s；Mosaico X 游隙 ±%.2f → ±X 实际 %.2f～%.2f（>%.1f 的部分在 %.2f 边框内）" % (
                fmt_bounds(wb), "  ".join("%s %.2f" % (k, v) for k, v in press.items()), a.clr,
                min(press["-X"], press["+X"]) - a.clr, max(press["-X"], press["+X"]) + a.clr, pm, (a.mos_w - a.disp_w) / 2))
            if not win.buffer(-a.clr).contains(disp_rect):
                R.fail("压框内窗（收 X 游隙 %.2f 后）盖到显示区 %.2f 见方" % (a.clr, a.disp_w))
            else:
                R.info("显示区 %.2f 见方居中：内窗收 CLR 后仍完全露出（Y 向余量 %.2f/%.2f）" % (
                    a.disp_w, disp_rect.bounds[1] - wb[1], wb[3] - disp_rect.bounds[3]))
            # GAP 容差扫描：Mosaico 沿 Y 偏 δ 时的 +Y/−Y 压边
            border = (a.mos_d - a.disp_w) / 2
            lines = []
            for gap_try in (0.0, 0.5, 1.0, 1.3, 1.5):
                dlt = gap_try - a.gap
                pY = press["+Y"] - dlt
                nY = press["-Y"] + dlt
                st = "OK" if (pY > 0.05 and nY > 0.05 and pY <= border and nY <= border) else ("+Y 压不到" if pY <= 0.05 else "盖到显示区")
                lines.append("GAP %.1f→+Y %.2f/−Y %.2f %s" % (gap_try, pY, nY, st))
            R.info("GAP 容差（压边）：" + "；".join(lines) + "（后裙间隙见 #12）")

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
    R.start("#6", "±X 功能区让位：Mosaico ±X 面外 0～2 mm、Y 中央 %.0f mm、Z∈[%.0f,%.0f] 内托盘/压框为空" % (a.side_cut, *a.func_z))
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
    # 窗口深度（人工可达性）
    s5 = ST.z(5.0)
    if not s5.is_empty:
        outer = s5.bounds
        R.manual("±X 功能窗：长 %.0f × 高 ≈ %.1f（Z 0～柱顶），托盘外缘到 Mosaico 面深 %.2f mm——USB-C 插头可进，侧键要伸指按" % (
            a.side_cut, post_top, outer[2] - MOS_XMAX))

    # ======================================================================
    # 7. manifold
    # ======================================================================
    R.start("#7", "manifold：托盘与压框都 watertight；体数/内腔另报")
    for nm, m in (("托盘", tray), ("压框", bezel)):
        if m is None:
            continue
        if m.is_watertight:
            nb = m.body_count
            R.info("%s watertight，%d 面，%d 体%s" % (nm, len(m.faces), nb, "" if nb == 1 else "（1 实体 + %d 个封闭内腔：官方底板底面刻线被托盘顶面封住；切片器会当空腔处理，无结构影响）" % (nb - 1)))
            if a.max_bodies is not None and nb > a.max_bodies:
                R.warn("%s 体数 %d > --max-bodies %d" % (nm, nb, a.max_bodies))
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
    R.start("#8", "螺钉立柱：≥%d 个 Ø%.1f±%.1f 竖孔，孔周壁 ≥%.1f，深 ≥%.1f，顶部敞开，两端/两侧都有；压框过孔对位" % (
        a.n_holes, a.hole_d, a.hole_tol, a.post_wall, a.hole_depth))
    good = []
    for h in tray_holes:
        zlo, zhi = min(h["zs"]), max(h["zs"])
        depth = zhi - zlo + 0.25
        dmin, dmax = min(h["ds"]), max(h["ds"])
        wmin = min(h["walls"])
        covered = False
        for z in z_levels(zhi + 0.25, post_top - 0.05, 0.25):
            s = ST.z(z)
            if not s.is_empty and s.buffer(-0.05).contains(Point(h["cx"], h["cy"])):
                covered = True
                break
        floor_left = (zlo - 0.125) - tray.bounds[0][2]
        desc = "孔 @(%.2f, %.2f) Ø%.2f～%.2f Z[%.2f,%.2f] 深≈%.1f 壁≥%.2f 孔底到托盘底 %.1f" % (h["cx"], h["cy"], dmin, dmax, zlo, zhi, depth, wmin, floor_left)
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
        near_edge = [MOS_YMAX - h["cy"] for h in near]
        if near_edge:
            R.info("模块端螺钉中心到 Mosaico +Y 面 %.2f mm——+Y 边实际由 ±X 两条的角部压住，1.2 宽排针侧条只是连接筋" % min(near_edge))
    if SB is not None and good:
        for h in good:
            near_b = [b for b in bez_holes if abs(b["cx"] - h["cx"]) < 0.3 and abs(b["cy"] - h["cy"]) < 0.3 and 2.0 <= b["d_thru"] <= 3.2]
            if not near_b:
                R.fail("托盘底孔 @(%.2f, %.2f) 在压框上没有对应 Ø2.0～3.2 过孔" % (h["cx"], h["cy"]))
        R.info("压框过孔 %d 组，同心对位" % len(bez_holes))

    # ======================================================================
    # 9. 可打印性（G-6；官方底板区除外）
    # ======================================================================
    if not a.quick:
        R.start("#9", "可打印性：壁 ≥%.1f（三向截面腐蚀法，Z 向含顶/底面下 0.1）、悬空 ≤%.1f（相邻层）——官方底板区不判" % (a.min_wall, a.max_overhang))
        er = a.min_wall / 2 - 0.02

        def excl(axis, c):
            if axis == 2:
                return plate_rect if 0 < c <= PL_ZMAX else None
            if axis == 0:
                return box(PL_YMIN, 0, PL_YMAX, PL_ZMAX) if PL_XMIN <= c <= PL_XMAX else None
            return box(PL_XMIN, 0, PL_XMAX, PL_ZMAX) if PL_YMIN <= c <= PL_YMAX else None

        def thin_check(S, m, nm, use_excl):
            found = []
            for axis, lab in ((2, "Z"), (0, "X"), (1, "Y")):
                lo, hi = m.bounds[0][axis], m.bounds[1][axis]
                levels = z_levels(lo + 0.15, hi - 0.15, 0.5 if axis == 2 else 1.0)
                if axis == 2:
                    levels = sorted(set(levels + [round(lo + 0.1, 4), round(hi - 0.1, 4)]))
                for c in levels:
                    s = S.solid(axis, c)
                    if s.is_empty:
                        continue
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
            # 压框顶面朝下打印：首层 = 顶面；顶面上最窄条 ≥ 0.8（两道 0.4）
            s_top = SB.z(bezel.bounds[1][2] - 0.1)
            if not s_top.is_empty:
                thin08 = polys_only(s_top.difference(s_top.buffer(-0.39).buffer(0.41)))
                narrow = [p for p in parts(thin08) if p.area > 0.5 and max(p.bounds[2] - p.bounds[0], p.bounds[3] - p.bounds[1]) > 2]
                if narrow:
                    R.fail("压框顶面（反打首层）有 < 0.8 mm 的条：%s" % fmt_bounds(narrow[0].bounds))
                else:
                    R.info("压框顶面朝下打印：首层无 < 0.8 mm 条")
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
        if SB is not None:
            # 压框反打：从顶面往下逐层（即打印方向），悬空 ≤ 2
            ohb = []
            bl, bh = bezel.bounds[0][2], bezel.bounds[1][2]
            prev = None
            for z in sorted(z_levels(bl + 0.1, bh - 0.1, 0.2), reverse=True):
                if prev is not None:
                    s_new, s_old = SB.z(z), SB.z(prev)
                    if not s_new.is_empty:
                        un = polys_only(s_new.difference(s_old.buffer(a.max_overhang + 0.05)))
                        if un.area > 0.1:
                            ohb.append((z, un.area, un.bounds))
                prev = z
            if ohb:
                R.fail("压框（顶面朝下打印）有 %d 层 > %.1f mm 悬空：例 Z=%.2f %.2f mm² %s" % (len(ohb), a.max_overhang, ohb[0][0], ohb[0][1], fmt_bounds(ohb[0][2])))
            else:
                R.info("压框顶面朝下打印：逐层无 > %.1f mm 悬空（倒角 45°、沉台台阶环、后裙皆可）" % a.max_overhang)

    # ======================================================================
    # 10. 定位存在性
    # ======================================================================
    R.start("#10", "定位存在性：环形沿顶面在 Z=0 托住四边（≥60%）；四个 ±X 角柱贴着 Mosaico 包络（松动 ≤0.3）；止挡")
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
        covered = covered_len(cov, ax)
        if covered / L < 0.6:
            R.fail("Mosaico %s 边下方（Z=0 面）支撑只有 %.1f / %.1f mm（%.0f%%）——落不到环形沿上" % (name, covered, L, covered / L * 100))
        else:
            R.info("%s 边下方支撑 %.1f / %.1f mm（%.0f%%）" % (name, covered, L, covered / L * 100))
    # 沿的净宽（Mosaico 下）
    if not rim.is_empty:
        under = polys_only(rim.intersection(mos_rect))
        cb = under.bounds if not under.is_empty else None
        if cb is not None:
            wins = interiors_of(under)
            if wins:
                w = max(wins, key=lambda p: p.area).bounds
                R.info("环形沿在 Mosaico 下的净宽：−X %.2f / +X %.2f / −Y %.2f / +Y %.2f（中央开空 %s）" % (
                    w[0] - MOS_XMIN, MOS_XMAX - w[2], w[1] - MOS_YMIN, MOS_YMAX - w[3], fmt_bounds(w)))
    far_y = (MOS_YMIN - a.clr, MOS_YC - a.side_cut / 2)
    near_y = (MOS_YC + a.side_cut / 2, MOS_YMAX + a.clr)
    PLAY = 0.30
    for sx, sname in ((-1, "-X"), (1, "+X")):
        for (y0, y1), yname in ((far_y, "远端"), (near_y, "模块端")):
            xf = MOS_XMAX + a.clr if sx > 0 else MOS_XMIN - a.clr
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
                gap = (found.bounds[0] - xf) if sx > 0 else (xf - found.bounds[2])
                if gap > PLAY:
                    R.fail("%s %s 角柱离 Mosaico 包络 %.2f > %.2f，±X 定位松" % (sname, yname, gap, PLAY))
                else:
                    R.info("%s %s 角柱在 Y[%.1f,%.1f]，贴包络（额外松动 %.2f）" % (sname, yname, found.bounds[1], found.bounds[3], max(gap, 0)))
    stop_zone = box(MOS_XMIN - a.clr, MOS_YMAX + a.clr - 0.05, MOS_XMAX + a.clr, min(MOD_FACE_Y + 1.5, PL_YMIN - 0.05))
    stop_found = EMPTY
    for z in (0.3, 0.7, 1.1, 1.4):
        s = ST.z(z)
        if not s.is_empty:
            stop_found = polys_only(unary_union([stop_found, polys_only(s.intersection(stop_zone))]))
    if stop_found.is_empty or stop_found.area < A_TOL:
        R.warn("没有 +Y 止挡：Mosaico 推到底的位置由排针座到底（或官方外壳前脸）决定，同官方裸用。"
               "GAP=%.2f、CLR=%.2f、外壳让位 0.2 时止挡可用厚度 %.2f mm < 1.2 可打印壁——几何上放不下，不是漏画；GAP 实测 ≥ %.2f 才有" % (
                   a.gap, a.clr, a.gap - a.clr - 0.2, a.clr + 0.2 + 1.2))
    else:
        b = stop_found.bounds
        R.info("止挡实体在 X[%.1f,%.1f] Y[%.2f,%.2f]（是否顶到外壳看 #2）" % (b[0], b[2], b[1], b[3]))

    # ======================================================================
    # 11. 装配运动学（G-10）：落位余量、导向先于触针、偏摆、拔出行程、导入斜角、手指口
    # ======================================================================
    R.start("#11", "装配运动学：落位距针尖 ≥1.5；角柱导向先于针尖触面 ≥0.5（否则 WARN）；+Y 面横向偏摆 ≤1.27；拔出行程 ≥ 针配合长+1.5")
    s5 = ST.z(5.0)
    s1 = ST.z(1.0)
    # 远端墙止面：X 与 Mosaico 重叠、Y < MOS_YMIN−1 的实体的最大 Y
    end_in = None
    xclip = box(MOS_XMIN + 0.5, tray.bounds[0][1] - 1, MOS_XMAX - 0.5, MOS_YMIN - 0.5)
    for s in (s1, s5):
        for p in parts(polys_only(s.intersection(xclip))):
            b = p.bounds
            if b[3] - b[1] > 0.5:
                end_in = b[3] if end_in is None else max(end_in, b[3])
    if end_in is None:
        end_in = tray.bounds[0][1]
        R.warn("远端没有墙/止面，落位位置不定（按托盘 −Y 端 %.2f 算）" % end_in)
    slide_len = MOS_YMIN - end_in
    drop_py = end_in + a.mos_d       # 落位时 Mosaico +Y 面
    # ±X 角柱 / 导轨（Z=5 截面，Mosaico 面外 0～3 mm 带）
    post_start = {}
    guide_start = {}
    block_ymax = {}
    clr_meas = {}
    for sx, sname in ((1, "+X"), (-1, "-X")):
        face = MOS_XMAX if sx > 0 else MOS_XMIN
        band = box(face, MOS_YMIN - 12, face + 3.5, MOS_YMAX + 1) if sx > 0 else box(face - 3.5, MOS_YMIN - 12, face, MOS_YMAX + 1)
        pieces = parts(polys_only(s5.intersection(band)))
        near = [p for p in pieces if p.bounds[3] > MOS_YC]
        far = [p for p in pieces if p.bounds[1] < MOS_YC]
        if near:
            p = max(near, key=lambda q: q.area)
            post_start[sname] = p.bounds[1]
            # 全导向起点：内面到包络 ≤ 0.1 的最小 Y
            gs = None
            for y in np.arange(p.bounds[1], p.bounds[3], 0.05):
                seg = p.intersection(box(face - 4, y - 0.02, face + 4, y + 0.02))
                if seg.is_empty:
                    continue
                inner = seg.bounds[0] if sx > 0 else seg.bounds[2]
                if abs(inner - face) <= a.clr + 0.1:
                    gs = y
                    break
            guide_start[sname] = gs if gs is not None else p.bounds[3]
        if far:
            p = max(far, key=lambda q: q.area)
            block_ymax[sname] = p.bounds[3]
            seg = p.intersection(box(face - 4, MOS_YMIN - 6, face + 4, MOS_YMIN))
            if not seg.is_empty:
                inner = seg.bounds[0] if sx > 0 else seg.bounds[2]
                clr_meas[sname] = abs(inner - face)
    R.info("落位：远端止面 Y=%.2f → 滑入区长 %.2f；落位时 Mosaico +Y 面 %.2f，针尖 %.2f，距针尖 %.2f" % (
        end_in, slide_len, drop_py, PIN_TIP_Y, PIN_TIP_Y - drop_py))
    if PIN_TIP_Y - drop_py < 1.5 - 1e-3:
        R.fail("落位时距针尖只有 %.2f < 1.5：放进去就可能碰针" % (PIN_TIP_Y - drop_py))
    travel_eng = a.pin_len - a.gap
    if slide_len < travel_eng + 1.5 - 1e-3:
        R.fail("拔出行程 %.2f < 针配合长 %.2f + 1.5：Mosaico 退到墙时排针还没脱开" % (slide_len, travel_eng))
    else:
        R.info("拔出：沿 −Y 退 %.2f 针脱开，再 %.2f 到墙，然后才能上提（余量 %.2f ≥1.5）" % (travel_eng, slide_len - travel_eng, slide_len - travel_eng))
    if post_start:
        ps = max(post_start.values())
        lead = {k: guide_start[k] - post_start[k] for k in post_start}
        margin = PIN_TIP_Y - ps
        R.info("模块端角柱起点 Y=%.3f（导入斜角长 %s），针尖 Y=%.3f → 角柱先于针尖 %.3f mm；推进 %.2f 后角柱开始接、%.2f 后针触面、%.2f 到位" % (
            ps, "/".join("%.2f" % v for v in lead.values()), PIN_TIP_Y, margin, ps - drop_py, PIN_TIP_Y - drop_py, MOS_YMAX - drop_py))
        if margin < -1.0:
            R.fail("针尖比角柱导向早 %.2f mm 触面：Mosaico 歪着到针" % -margin)
        elif margin < 0.5:
            R.warn("「两端先导向再进针」在几何上不成立（裕量 %.3f < 0.5）：该裕量 = (MOS_D − %.0f)/2 − (PIN_LEN − GAP) = %.3f，被硬要求 7 的 34 mm 留空锁死，"
                   "与 CLR/滑入区长无关。PIN_LEN=%.1f 未实测（Q1-13），实际 >%.2f 则针先触面。**装配时必须目视对准槽口、轻推到有阻力再加力**" % (
                       margin, a.side_cut, (a.mos_d - a.side_cut) / 2 - travel_eng, a.pin_len, a.pin_len + margin))
        else:
            R.info("角柱导向先于针尖 %.2f ≥ 0.5" % margin)
        if min(lead.values()) < 0.5:
            R.warn("模块端角柱端面无导入斜角（%.2f），偏摆到位的 Mosaico 角会顶在端面上卡死" % min(lead.values()))
    else:
        R.fail("Z=5 截面找不到模块端角柱")
    if block_ymax and clr_meas:
        ovl = min(block_ymax.values()) - (MOS_YMIN - travel_eng)
        c = max(clr_meas.values())
        yaw = math.degrees(math.atan2(2 * c, ovl)) if ovl > 0 else 90.0
        lat = math.tan(math.radians(yaw)) * (a.mos_d - ovl / 2) + c if ovl > 0 else float("inf")
        R.info("针尖触面瞬间：−Y 导轨与 Mosaico 侧面重叠 %.2f mm，单边隙实测 %.2f（双边 %.2f）→ 偏摆 ≤%.2f°，+Y 面横向偏 ≤%.2f mm（半针距 1.27）" % (
            ovl, c, 2 * c, yaw, lat))
        if lat > 1.27:
            R.warn("横向偏摆 %.2f > 半针距 1.27：不目视对准会把针顶在槽口塑料上" % lat)
        # 落位（靳墙）时的支撑：Mosaico 整体沿 −Y 偏 slide_len
        rim = ST.z(-0.05)
        drop_rect = box(MOS_XMIN, MOS_YMIN - slide_len, MOS_XMAX, MOS_YMAX - slide_len)
        under = polys_only(rim.intersection(drop_rect)) if not rim.is_empty else EMPTY
        R.info("落位（靳墙）时背面下方支撑面积 %.0f mm²（到位时 %.0f mm²）——两位置都坐在环形沿/滑入区底面上" % (
            under.area, polys_only(rim.intersection(mos_rect)).area if not rim.is_empty else 0))
    # 手指口：远端墙 Y 带内中央的空缺（Z=1 与 Z=5 与 Z=9）
    if end_in is not None and end_in > tray.bounds[0][1] + 0.5:
        wall_band = box(MOS_XMIN, end_in - 3.0, MOS_XMAX, end_in + 0.01)
        gapx = None
        zopen = []
        for z in (0.5, 1.0, 3.0, 5.0, 7.0, 9.0, post_top - 0.3):
            s = ST.z(z)
            m = polys_only(s.intersection(wall_band)) if not s.is_empty else EMPTY
            xs = sorted((p.bounds[0], p.bounds[2]) for p in parts(m))
            # 找中央最大空隙
            best = None
            prev = MOS_XMIN
            for x0, x1 in xs + [(MOS_XMAX, MOS_XMAX)]:
                if x0 - prev > 4 and (best is None or x0 - prev > best[1] - best[0]):
                    best = (prev, x0)
                prev = max(prev, x1)
            if best:
                zopen.append(z)
                gapx = best if gapx is None else (max(gapx[0], best[0]), min(gapx[1], best[1]))
        wall_t = end_in - max(tray.bounds[0][1], end_in - 3.0)
        if gapx:
            R.manual("远端手指口：宽 %.1f（X[%.1f,%.1f]）、Z %.1f～%.1f 开；指尖要伸进 %.1f（墙厚）+ %.1f（滑入区）= %.1f mm 才顶到 Mosaico −Y 面" % (
                gapx[1] - gapx[0], gapx[0], gapx[1], min(zopen), max(zopen), wall_t, slide_len, wall_t + slide_len))
        else:
            R.manual("远端墙封死：Mosaico −Y 面只能从上方 %.1f mm 宽的缝够到，推拔别扭（审核 F6）" % slide_len)

    # ======================================================================
    # 12. 压框—托盘装配间隙（G-11）
    # ======================================================================
    if SB is not None:
        R.start("#12", "压框—托盘装配间隙：两 STL 叠在装配位，逐层最近距离 ≥0.15；后裙到 Mosaico −Y 面 ∈(0.3, 针配合长−1.0]")
        dmin, where = None, None
        for z in sorted(set(z_levels(max(bezel.bounds[0][2], 0.3), post_top - 0.05, 0.5) + [round(post_top - 0.05, 3), round(bezel.bounds[0][2] + 0.1, 3)])):
            b = SB.z(z)
            t = ST.z(z)
            if b.is_empty or t.is_empty:
                continue
            d = b.distance(t)
            if dmin is None or d < dmin:
                dmin, where = d, (z, b.bounds)
        if dmin is None:
            R.info("压框与托盘在 Z<柱顶 无共存层")
        elif dmin < 0.15 - 1e-3:
            R.fail("压框与托盘在 Z=%.2f 最近只有 %.3f（<0.15）：干涉或过紧，压框放不下（压框在该层 %s）" % (where[0], dmin, fmt_bounds(where[1])))
        else:
            R.info("压框（后裙）与托盘（长块/远端墩）逐层最近 %.2f mm（Z=%.2f）" % (dmin, where[0]))
        # 后裙到 Mosaico −Y 面
        sk = None
        for z in z_levels(bezel.bounds[0][2] + 0.1, MOS_T - 0.1, 0.5):
            b = SB.z(z)
            if b.is_empty:
                continue
            for p in parts(b):
                if p.bounds[3] < MOS_YMIN and p.bounds[2] > MOS_XMIN and p.bounds[0] < MOS_XMAX:
                    g = MOS_YMIN - p.bounds[3]
                    sk = g if sk is None else min(sk, g)
        if sk is None:
            R.warn("压框没有后裙/防退出特征：拆压框前 Mosaico 可沿 −Y 退出拔针")
        else:
            R.info("后裙内面到 Mosaico −Y 面 %.2f：Mosaico 最多退 %.2f，此时排针仍插入 %.2f" % (sk, sk, travel_eng - sk))
            if sk <= 0.3:
                R.fail("后裙间隙 %.2f ≤ 0.3：实际 GAP 稍大压框就放不下" % sk)
            if travel_eng - sk < 1.0:
                R.warn("后裙允许退 %.2f 后排针只剩 %.2f 插入（<1.0）" % (sk, travel_eng - sk))
            lines = []
            for gap_try in (0.0, 0.5, 1.0, 1.3, 1.5):
                dlt = gap_try - a.gap
                lines.append("GAP %.1f→后裙隙 %.2f%s" % (gap_try, sk - dlt, "" if sk - dlt > 0 else " 放不下"))
            R.info("GAP 容差（后裙）：" + "；".join(lines))

    # ======================================================================
    # 13. README 假设登记（硬要求 8）
    # ======================================================================
    R.start("#13", "假设登记：scad 的每个 ASSUMPTION 编号与闸门依赖的编号都在 README 表里")
    need = set(["Q1-2", "Q1-4", "Q1-13", "Q1-23", "AS-01"])
    if os.path.exists(scad_path):
        try:
            txt = open(scad_path, encoding="utf-8").read()
            for line in txt.splitlines():
                if "ASSUMPTION" in line:
                    need.update(re.findall(r"(Q1-\d+[a-z]?|AS-\d+)", line))
        except Exception as e:
            R.warn("读 scad 失败：%s" % e)
    else:
        R.warn("未找到 scad（%s），只核最小集合" % scad_path)
    if os.path.exists(readme_path):
        rd = open(readme_path, encoding="utf-8").read()
        missing = sorted(t for t in need if t not in rd)
        if missing:
            R.fail("README 缺登记：%s" % ", ".join(missing))
        else:
            R.info("README 已登记全部 %d 个编号：%s" % (len(need), ", ".join(sorted(need, key=lambda t: (t[:2], int(re.sub(r'\D', '', t) or 0), t)))))
    else:
        R.warn("未找到 README（%s）" % readme_path)

    # ======================================================================
    # 14. 刚度/其它 info（不拦）
    # ======================================================================
    R.start("#14", "整体刚度与其它（只报不拦）")
    sy = ST.solid(1, MOS_YC)
    if not sy.is_empty:
        ps = sorted(parts(sy), key=lambda p: p.bounds[0])
        desc = "；".join("X[%.1f,%.1f] Z[%.1f,%.1f] %.1f mm²" % (p.bounds[0], p.bounds[2], p.bounds[1], p.bounds[3], p.area) for p in ps)
        R.info("Mosaico 中央 Y=%.1f 处托盘截面（34 mm 留空段）：%s——扭转刚度靳这几条，桌面用可接受，手持不行" % (MOS_YC, desc))
    R.manual("外壳 STL 内壁与底板台阶：外壳坐 Z≈%.2f、顶 ≈%.2f，比 Mosaico 屏面高 %.2f；ANALYSIS「模块比 Mosaico 薄 0.58」不成立，到货实测（Q1-22）" % (
        SHELL_Z0, SHELL_TOP, SHELL_TOP - MOS_T))

    # ======================================================================
    nfail = R.dump()
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({k: {"title": v["title"], "status": v["status"], "lines": v["lines"]} for k, v in R.items.items()}, f, ensure_ascii=False, indent=1)
    sys.exit(1 if nfail else 0)


if __name__ == "__main__":
    main()
