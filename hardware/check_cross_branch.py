#!/usr/bin/env python3
# 提案 · 未冻结 · 由 Claude 主控（claude-opus-5）起草 · 待 Chrome 采纳、Hiro／Grok 复核
#
# check_cross_branch.py —— 跨分支契约比对
#
# 为什么存在：
#   2026-09-21 的双路独立清点在四个设计分支之间查出 40 条不一致、22 条阻断，其中包括
#   「模块总成物理上放不进落入槽」「弹簧针压缩量是负的」这种打样就报废的错误。
#   而每个分支自己的自检**全部通过**——因为自检只查本文件内部自洽，
#   从来没有任何东西比对过两个分支。这个脚本就是补那个缺口。
#
#   40 条能长到 40 条，唯一原因是没人在合并前跑过这种比对。所以它必须是**自动的**，
#   必须在每次合并前跑，必须以非零退出码失败，不能是一份靠人读的文档。
#
# 用法：
#   python3 hardware/check_cross_branch.py \
#       --module /private/tmp/wt-mech-module/mechanical/module-board/module_shell.scad \
#       --dock   /private/tmp/wt-mech-dock/mechanical/dock-shell/dock_shell.scad
#
# 原理：两个 .scad 各自的 icd_contract() 吐出 `ICD-CONTRACT|<键>|<值>`，
#       本脚本编译两边、抓这些行、按下面的关系表判定。
#
# **加新的跨件量时，两边同时加键并在 RELATIONS 里加一行。** 只加一边会被报成「只有一侧给值」。
import subprocess, sys, re, argparse, tempfile, os

# ---- 关系表 ----
# EQ   两边必须相等（在 tol 内）
# FIT  模块侧的需求必须落在底座侧的供给之内：(模块键, 底座键, 方向)
#      方向 '>=' 表示模块值须 ≥ 底座值；'<=' 表示须 ≤
# GE   模块侧为需求下限，底座侧必须 ≥ 它
EQ = [
    ('MOSAICO_W',          0.001, 'Mosaico X 向宽'),
    ('MOSAICO_H',          0.001, 'Mosaico Y 向高'),
    ('MOSAICO_T',          0.001, 'Mosaico Z 向厚'),
    ('DOCK_PIN_FIELD_X0',  0.001, '弹簧针场第 1 列 X'),
    ('DOCK_PIN_FIELD_Z0',  0.001, '弹簧针场行 A 的 Z'),
    ('DOCK_PIN_FIELD_Y',   0.001, '配合面 Y'),
    ('DOCK_PITCH',         0.001, '弹簧针间距'),
    ('DOCK_COLS',          0.001, '弹簧针列数'),
    ('DOCK_ROWS',          0.001, '弹簧针行数'),
    ('DOCK_X_TOL',         0.001, '托架定位公差 X'),
    ('DOCK_Z_TOL',         0.001, '托架定位公差 Z'),
    ('DOCK_PIN_TRAVEL',    0.001, '名义工作压缩量'),
    ('DOCK_PIN_FORCE_N',   0.001, '单针工作压力'),
    ('CONTACT_PCB_X',      0.001, '触点板 X 向长'),
    ('CONTACT_PCB_Z',      0.001, '触点板 Z 向宽'),
    ('HARD_STOP_Y',        0.150, '硬限位面 Y（容差取 MD-01 的 ±0.15）'),
]
FIT = [
    ('MODULE_ENV_X_LO', 'BAY_X_LO', '>=', '模块总成 −X 端须落在落入槽内'),
    ('MODULE_ENV_X_HI', 'BAY_X_HI', '<=', '模块总成 +X 端须落在落入槽内'),
    ('MODULE_ENV_Y_LO', 'BAY_Y_LO', '>=', '模块总成底面须不低于槽地板'),
    ('MODULE_ENV_Y_HI', 'BAY_Y_HI', '<=', '模块总成顶面须不高于上压框压面'),
    ('MODULE_ENV_Z_LO', 'BAY_Z_LO', '>=', '模块总成 −Z 面须落在落入槽内'),
    ('MODULE_ENV_Z_HI', 'BAY_Z_HI', '<=', '模块总成 +Z 面须落在落入槽内'),
]
GE = [
    ('RETENTION_N', '保持力：底座提供值须 ≥ 模块侧要求值'),
]

def read_contract(path):
    # 注意：不能用 -o /dev/null —— openscad 靠扩展名判断导出格式，无后缀会直接报
    # 「Invalid suffix」而根本不执行脚本，于是一行 ECHO 也拿不到。必须给个真后缀。
    with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tf:
        tmp = tf.name
    try:
        r = subprocess.run(['openscad', '-o', tmp, path],
                           capture_output=True, text=True)
    finally:
        try: os.unlink(tmp)
        except OSError: pass
    out = {}
    for line in (r.stderr + r.stdout).splitlines():
        m = re.search(r'ICD-CONTRACT\|([A-Za-z0-9_]+)\|([-0-9.eE]+)', line)
        if m:
            out[m.group(1)] = float(m.group(2))
    if not out:
        print(f'FAIL: {path} 没有吐出任何 ICD-CONTRACT 行。'
              f'该文件是否缺 icd_contract() 段？\nopenscad stderr 尾部:\n'
              + '\n'.join((r.stderr or '').splitlines()[-5:]))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--module', required=True)
    ap.add_argument('--dock',   required=True)
    a = ap.parse_args()

    M, D = read_contract(a.module), read_contract(a.dock)
    if not M or not D:
        return 2
    print(f'模块侧给出 {len(M)} 个键，底座侧给出 {len(D)} 个键\n')

    fails, warns = [], []

    for key, tol, desc in EQ:
        if key not in M or key not in D:
            warns.append(f'{key}（{desc}）：只有 '
                         f'{"模块" if key in M else "底座" if key in D else "没有一"}侧给了值 '
                         f'—— 另一侧必须补上，否则这个量没有任何东西在管')
            continue
        if abs(M[key] - D[key]) > tol:
            fails.append(f'{key}（{desc}）：模块 {M[key]} ≠ 底座 {D[key]}，'
                         f'差 {abs(M[key]-D[key]):.3f}（容差 {tol}）')

    for mk, dk, op, desc in FIT:
        if mk not in M or dk not in D:
            warns.append(f'{mk} / {dk}（{desc}）：缺一侧的值')
            continue
        ok = (M[mk] >= D[dk] - 1e-9) if op == '>=' else (M[mk] <= D[dk] + 1e-9)
        if not ok:
            gap = abs(M[mk] - D[dk])
            fails.append(f'{mk} = {M[mk]} 不满足 {op} {dk} = {D[dk]}'
                         f'（{desc}）：**干涉 {gap:.3f} mm**')

    for key, desc in GE:
        if key not in M or key not in D:
            warns.append(f'{key}（{desc}）：缺一侧的值')
            continue
        if D[key] < M[key] - 1e-9:
            fails.append(f'{key}（{desc}）：模块侧要求 {M[key]}，底座侧只提供 {D[key]}，'
                         f'缺 {M[key]-D[key]:.3f}')

    only_m = sorted(set(M) - set(D) - {k for k, *_ in
                    [(x[0],) for x in FIT] } - {x[0] for x in FIT})
    only_d = sorted(set(D) - set(M) - {x[1] for x in FIT})
    for k in only_m:
        if k not in {x[0] for x in FIT}:
            warns.append(f'{k}：只有模块侧给了值（{M[k]}），底座侧无对应键')
    for k in only_d:
        if k not in {x[1] for x in FIT}:
            warns.append(f'{k}：只有底座侧给了值（{D[k]}），模块侧无对应键')

    if warns:
        print(f'⚠ 警告 {len(warns)} 条（不阻断，但说明契约有洞）：')
        for w in warns:
            print(f'  - {w}')
        print()
    if fails:
        print(f'✗ 不通过，{len(fails)} 条阻断：')
        for f in fails:
            print(f'  - {f}')
        print('\n以上每一条都会在打样后变成废板或装不上。合并前必须清零。')
        return 1
    print(f'✓ 全部通过：{len(EQ)} 条等值、{len(FIT)} 条包含、{len(GE)} 条供需关系')
    return 0

if __name__ == '__main__':
    sys.exit(main())
