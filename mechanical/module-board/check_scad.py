#!/usr/bin/env python3
# 提案 · 未冻结 · 由 Claude 主控（claude-opus-5）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
#
# check_scad.py —— OpenSCAD 源文件静态检查（本机无 openscad 时的替代手段）
# 用法：python3 check_scad.py module_board.scad
# 检查项：① 括号/花括号/方括号配对与注释、字符串闭合 ② 变量/模块/函数引用是否有定义
#         ③ 顶层变量是否被重复赋值（OpenSCAD 取最后一次，易成笔误）
# 注意：这不是编译。它不检查几何是否可渲染，也不检查数值是否正确；
#       一旦本机装上 openscad，应改用 `openscad -o /tmp/mb.stl module_board.scad` 编译。
import re, sys, collections

import os
path = sys.argv[1]
src = open(path, encoding='utf-8').read()

# include <x.scad> / use <x.scad>：把被包含文件一并读入做定义收集（不递归展开几何）
included_src = ''
for m in re.finditer(r'\b(?:include|use)\s*<([^>]+)>', src):
    ip = os.path.join(os.path.dirname(os.path.abspath(path)), m.group(1))
    if os.path.exists(ip):
        included_src += '\n' + open(ip, encoding='utf-8').read()
        print(f'[INFO] 已并入 include 文件：{m.group(1)}')
    else:
        print(f'[WARN] include 的文件不存在：{m.group(1)}')

# --- 去掉注释与字符串（保留换行，便于报行号）---
def strip_scad(text):
    out = []
    i = 0
    n = len(text)
    state = 'code'
    while i < n:
        c = text[i]
        if state == 'code':
            if text.startswith('//', i):
                state = 'line'; out.append(' '); i += 2; continue
            if text.startswith('/*', i):
                state = 'block'; out.append(' '); i += 2; continue
            if c == '"':
                state = 'str'; out.append(' '); i += 1; continue
            out.append(c); i += 1
        elif state == 'line':
            out.append('\n' if c == '\n' else ' ')
            if c == '\n':
                state = 'code'
            i += 1
        elif state == 'block':
            if text.startswith('*/', i):
                state = 'code'; out.append('  '); i += 2; continue
            out.append('\n' if c == '\n' else ' '); i += 1
        elif state == 'str':
            if c == '\\':
                out.append('  '); i += 2; continue
            if c == '"':
                state = 'code'
            out.append('\n' if c == '\n' else ' '); i += 1
    return ''.join(out)

out = []
i = 0
n = len(src)
state = 'code'
while i < n:
    c = src[i]
    if state == 'code':
        if src.startswith('//', i):
            state = 'line'; out.append(' '); i += 2; continue
        if src.startswith('/*', i):
            state = 'block'; out.append(' '); i += 2; continue
        if c == '"':
            state = 'str'; out.append(' '); i += 1; continue
        out.append(c); i += 1
    elif state == 'line':
        if c == '\n':
            state = 'code'; out.append('\n')
        else:
            out.append(' ')
        i += 1
    elif state == 'block':
        if src.startswith('*/', i):
            state = 'code'; out.append('  '); i += 2; continue
        out.append('\n' if c == '\n' else ' '); i += 1
    elif state == 'str':
        if c == '\\':
            out.append('  '); i += 2; continue
        if c == '"':
            state = 'code'
        out.append('\n' if c == '\n' else ' '); i += 1
clean = ''.join(out)
if state != 'code':
    print(f'[FAIL] 文件结束时仍处于 {state} 状态（注释或字符串未闭合）')

# --- 括号配对 ---
pairs = {')': '(', ']': '[', '}': '{'}
stack = []
line = 1
errs = 0
for ch in clean:
    if ch == '\n':
        line += 1
    elif ch in '([{':
        stack.append((ch, line))
    elif ch in ')]}':
        if not stack:
            print(f'[FAIL] 第 {line} 行：多余的 {ch}'); errs += 1
        else:
            op, ol = stack.pop()
            if op != pairs[ch]:
                print(f'[FAIL] 第 {line} 行：{ch} 与第 {ol} 行的 {op} 不匹配'); errs += 1
if stack:
    for op, ol in stack:
        print(f'[FAIL] 第 {ol} 行的 {op} 未闭合'); errs += 1
if errs == 0:
    print('[OK] 括号/花括号/方括号全部配对')

# --- 定义收集 ---
assign_re = re.compile(r'(?:^|;)\s*([A-Za-z_]\w*)\s*=(?!=)', re.M)
mod_re    = re.compile(r'\bmodule\s+([A-Za-z_]\w*)\s*\(')
fun_re    = re.compile(r'\bfunction\s+([A-Za-z_]\w*)\s*\(')

clean_all = clean + strip_scad(included_src)
defined_vars = set(assign_re.findall(clean_all))
defined_mods = set(mod_re.findall(clean_all))
defined_funs = set(fun_re.findall(clean_all))

# 形参与 for/let 局部变量
params = set()
for m in re.finditer(r'\b(?:module|function)\s+[A-Za-z_]\w*\s*\(([^)]*)\)', clean_all):
    for p in m.group(1).split(','):
        p = p.strip()
        if not p:
            continue
        name = p.split('=')[0].strip()
        if re.fullmatch(r'[A-Za-z_]\w*', name):
            params.add(name)
for m in re.finditer(r'\bfor\s*\(([^)]*)\)', clean_all):
    for p in m.group(1).split(','):
        p = p.strip()
        mm = re.match(r'([A-Za-z_]\w*)\s*=', p)
        if mm:
            params.add(mm.group(1))

builtins = set('''
cube sphere cylinder polyhedron square circle polygon text surface import
translate rotate scale resize mirror multmatrix color offset hull minkowski
linear_extrude rotate_extrude projection difference union intersection render
echo assert let for if else each function module include use children
min max abs sign sin cos tan asin acos atan atan2 pow sqrt exp ln log round
ceil floor len concat chr ord str search version version_num norm cross lookup
rands is_undef is_list is_num is_bool is_string undef true false PI
d h r r1 r2 d1 d2 height center cut convexity size file layer scale twist slices include use
$fn $fa $fs $t $vpr $vpt $vpd $children $preview
'''.split())

used = set(re.findall(r'\$?[A-Za-z_]\w*', re.sub(r'<[^>]*>', ' ', clean)))
known = defined_vars | defined_mods | defined_funs | params | builtins
unknown = sorted(u for u in used if u not in known)
if unknown:
    print('[WARN] 未找到定义的标识符：', ', '.join(unknown))
else:
    print('[OK] 所有标识符均有定义（变量/模块/函数/形参/内置）')

# --- 模块与函数调用是否有定义 ---
calls = set(re.findall(r'\b([A-Za-z_]\w*)\s*\(', clean))
bad = sorted(c for c in calls if c not in defined_mods | defined_funs | builtins | params)
if bad:
    print('[WARN] 调用了未定义的模块/函数：', ', '.join(bad))
else:
    print('[OK] 所有模块/函数调用均有定义')

# --- 重复定义 ---
dup = [k for k, v in collections.Counter(assign_re.findall(clean)).items() if v > 1]
if dup:
    print('[WARN] 变量被多次赋值（OpenSCAD 取最后一次，可能是笔误）：', ', '.join(sorted(dup)))
else:
    print('[OK] 无重复顶层赋值')

print(f'[INFO] 顶层赋值 {len(defined_vars)} 个，module {len(defined_mods)} 个，function {len(defined_funs)} 个')
