#!/usr/bin/env python3
# 提案 · 未冻结 · 待 Chrome 采纳、Hiro／Grok 复核
#
# check_fit_geometry.py —— 跨分支**几何**比对（check_cross_branch.py 的搭档）
#
# 为什么存在：
#   check_cross_branch.py 只比对两个 .scad 各自 echo 出来的**变量**。它抓不到形状。
#   2026-09-22 的复核实测到三条它全部放行的致命项：
#     · 落入槽 +X 壁上一道限位筋对 Mosaico 过盈 0.850 × 33.190 × 3.000 mm，
#       Mosaico 整条落入行程被挡死 —— 而 BAY_X_HI 这个变量是对的；
#     · 上压框保持力螺柱与 D-pad 右开关体重叠 2.545 × 6.000 × 4.300 mm；
#     · 四根硬限位柱里两根站在引入倒角削掉的边带上，名义间隙 0.596 / 0.149 mm，
#       从不接触 —— 而 HARD_STOP_Y 这个变量也是对的。
#   这三条的共同点：**变量正确，形状错误**。所以必须有一个做布尔运算的检查。
#
# 用法：
#   python3 check_fit_geometry.py --module <module_shell.scad> --dock <dock_shell.scad>
#
# 判据：下表每一项都断言「求交为空」或「求交非空」，与设计意图一致才通过。
import argparse, os, re, subprocess, sys, tempfile

MOS = "MW=45.19; MH=45.19; MT=11.48; module mos(){ translate([-MW/2,-MH/2,-MT/2]) cube([MW,MH,MT]); }"

# (名称, 期望, scad 片段)  期望 'empty' 或 'solid'
CASES = [
    ("底座 ∩ Mosaico 包络（落座终位）", "empty",
     "intersection(){ handheld_all(); mos(); }"),
    ("底座 ∩ Mosaico 落入通道（沿 +Y 扫掠 0..60）", "empty",
     "intersection(){ union(){ for(k=[0:1:60]) translate([0,k,0]) mos(); } handheld_all(); }"),
    ("底座 ∩ 模块总成落入通道", "empty",
     "intersection(){ union(){ for(k=[0:1:50]) translate([0,k,0]) modsolid(); } handheld_all(); }"),
    ("模块壳 ∩ Mosaico 包络（不变量 ①②）", "empty",
     "intersection(){ modsolid(); mos(); }"),
    ("上压框 ∩ Mosaico 本体（软限位只压软垫）", "empty",
     "intersection(){ top_frame(); mos(); }"),
    ("上压框 ∩ 模块（名义间隙）", "empty",
     "intersection(){ top_frame(); modsolid(); }"),
    ("上压框沿 −X 偏 0.30（两件各 ±PRINT_TOL）∩ 模块", "empty",
     "intersection(){ translate([-0.30,0,0]) top_frame(); modsolid(); }"),
    ("保持力螺柱 ∩ 按键导向/开关体", "empty",
     "intersection(){ frame_screw_bosses(); union(){ buttons_guides(); buttons_openings(); "
     "for(i=[0:3]) translate([dpad_sw(i)[0]-3, dpad_sw(i)[1]-3, -2.60]) cube([6,6,4.30]); "
     "for(i=[0:3]) translate([abxy_sw(i)[0]-3, abxy_sw(i)[1]-3, -2.60]) cube([6,6,4.30]); } }"),
    ("保持力螺柱 ∩ 主板外形（主板必须让开）", "empty",
     "linear_extrude(height=1) intersection(){ projection(cut=false) frame_screw_bosses(); board_2d(); }"),
    ("键帽导向套 ∩ 落入槽内腔", "empty",
     "intersection(){ buttons_guides(); bay_cavity(0); }"),
    ("电池包络 ∩ 落入槽壁", "empty",
     "intersection(){ battery_envelope(); bay_walls(); }"),
    ("电池仓壁/仓盖 ∩ 弹簧针小板过板通道", "empty",
     "intersection(){ battery_bay_walls(); pogo_pass_channel(); }"),
    ("主板支撑筋 ∩ 弹簧针小板过板通道", "empty",
     "intersection(){ board_rails(); pogo_pass_channel(); }"),
    ("模块下沉 0.20 ∩ 底座 → 必须落在硬限位柱上（非空）", "solid",
     "intersection(){ translate([0,-0.20,0]) modsolid(); handheld_all(); }"),
    ("上压框下移 0.10 ∩ 模块 → 必须压到模块顶面（非空）", "solid",
     "intersection(){ translate([0,-0.10,0]) top_frame(); modsolid(); }"),
]

def valid_nonempty_stl(path):
    """只有可解析且含面片的 STL 才是 solid，文件存在本身不是证据。"""
    if not os.path.isfile(path):
        return False
    size = os.path.getsize(path)
    with open(path, 'rb') as f:
        head = f.read(4096)
        if size >= 84:
            triangles = int.from_bytes(head[80:84], 'little')
            if triangles > 0 and size == 84 + 50 * triangles:
                return True
        f.seek(max(0, size - 256))
        tail = f.read()
    # OpenSCAD 也可生成 ASCII STL。空文件、诊断文本不能当几何输出。
    return (head.lstrip().startswith(b'solid') and
            b'facet normal' in head and b'endfacet' in head and
            b'endsolid' in tail)


def run(tmpdir, module, dock, frag, timeout_s):
    src = (f'use <{os.path.abspath(dock)}>\nuse <{os.path.abspath(module)}>\n{MOS}\n'
           'module modsolid(){ union(){ shell_front(); shell_back(); } }\n' + frag + '\n')
    p = os.path.join(tmpdir, 'p.scad'); o = os.path.join(tmpdir, 'p.stl')
    open(p, 'w', encoding='utf8').write(src)
    if os.path.exists(o): os.unlink(o)
    try:
        r = subprocess.run(['openscad', '-o', o, p], capture_output=True, text=True,
                           timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return 'error', f'OpenSCAD 超过 {timeout_s:g} 秒仍未完成'
    except OSError as exc:
        return 'error', f'无法启动 OpenSCAD：{exc}'
    out = r.stderr + r.stdout
    # 未定义的 module 会被 OpenSCAD 静默忽略 —— intersection 于是只剩一个子件，
    # 结果必然非空。这会把「检查没跑」伪装成「检查失败」，必须单独报出来。
    m0 = re.search(r'Ignoring unknown (?:module|function) \'([^\']+)\'', out)
    if m0:
        return 'n/a', f'被测文件里没有 {m0.group(1)}()，该项无法判定'
    if r.returncode != 0 or 'ERROR' in out or 'WARNING' in out:
        tail = out.strip().splitlines()[-1][:120] if out.strip() else '无诊断文本'
        return 'error', f'OpenSCAD 退出码 {r.returncode}：{tail}'
    empty = 'Current top level object is empty' in out
    solid = valid_nonempty_stl(o)
    if empty and solid:
        return 'error', '同时出现空结果标记与非空 STL，无法信任本次判定'
    if empty:
        return 'empty', ''
    if solid:
        m = re.search(r'Vertices:\s+(\d+)', out)
        return 'solid', f'{m.group(1)} 顶点' if m else '有效非空 STL'
    return 'error', '无空结果标记，也无有效非空 STL'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--module', required=True)
    ap.add_argument('--dock', required=True)
    ap.add_argument('--case-timeout', type=float, default=120.0,
                    help='每项 OpenSCAD 最长运行秒数（默认 120）')
    a = ap.parse_args()
    if a.case_timeout <= 0:
        ap.error('--case-timeout 必须大于 0')
    fails, na = [], []
    with tempfile.TemporaryDirectory() as td:
        for name, want, frag in CASES:
            got, info = run(td, a.module, a.dock, frag, a.case_timeout)
            ok = (got == want)
            mark = '✓' if ok else ('–' if got == 'n/a' else '✗')
            print(f'{mark} {name}：期望 {want}，实得 {got} {info}')
            if got == 'n/a': na.append(name)
            elif not ok: fails.append(name)
    if na:
        print(f'\n– 无法判定 {len(na)} 条（被测 .scad 缺少检查所需的 module，须先补上）：')
        for f in na: print('  - ' + f)
    if fails or na:
        print(f'\n✗ 不通过：{len(fails)} 条判定失败、{len(na)} 条未判定：')
        for f in fails: print('  - ' + f)
        print('\n所有检查须真实运行并得到可判定结果；碰撞、超时和模型缺失都阻止放行。')
        return 1
    print(f'\n✓ 全部通过：{len(CASES)} 项布尔求交判定')
    return 0

if __name__ == '__main__':
    sys.exit(main())
