#!/usr/bin/env python3
# 提案 · 未冻结 · 由 Claude 主控（claude-opus-5）起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造
#
# make_layout_svg.py —— 由 dock_shell.scad 顶部同一组参数生成正视/侧视布局图。
# 本机未安装 OpenSCAD，本图是 PNG 渲染的替代物，用于核对落点与尺寸。
# 参数必须与 dock_shell.scad 一致；改 SCAD 后重跑本脚本。
#   python3 mechanical/dock-shell/make_layout_svg.py > mechanical/dock-shell/LAYOUT-front.svg

MOSAICO_W = MOSAICO_H = 45.19; MOSAICO_T = 11.48
MODULE_STACK_X = 5.00; MODULE_UNDER_Y = 3.20
CONTACT_PCB_W = 22.00
DOCK_PITCH = 2.54; DOCK_COLS = 8
DOCK_PIN_FIELD_X0 = -26.00; DOCK_PIN_FIELD_Z0 = 1.27
CLR_FIT = 0.35; WALL = 2.00; BAY_WALL = 2.00
FRONT_PROUD = 2.00; CORE_T = 23.00; W_TOTAL = 167.00
Y_TOP_OUT = 33.00; BEZEL_OVERLAP = 2.00
GRIP_X_IN = 30.0; GRIP_Y_TOP = 8.0; GRIP_Y_BOT = -60.0; GRIP_R = 8.0
GRIP_DEPTH_TOP = 1.5; GRIP_DEPTH_BOT = 5.0; GRIP_RAKE_X = 5.0
BATT_T = 8.0; BATT_H = 34.0; BATT_W = 50.0; BATT_CLR = 1.0
BATT_X_CTR = -35.0; BATT_Y_TOP = -27.0
BOARD_T = 1.60; BOARD_Z_FRONT = -2.60
DPAD_X, DPAD_Y = -54.0, -4.0; DPAD_SW_R = 9.5; DPAD_ARM_L = 12.0; DPAD_ARM_W = 10.5
ABXY_X, ABXY_Y = 54.0, -4.0; ABXY_R = 13.0; ABXY_D = 10.5
LR_X, LR_Y = 58.0, 27.5; LR_BAR_W = 20.0; LR_BAR_H = 8.0
NATIVE_USB_X = 0.0; NATIVE_USB_W = 12.0; NATIVE_USB_D = 9.0
DOCK_USB_X = 30.0; DOCK_USB_W = 9.6; DOCK_USB_H = 4.0
USB_ZONE_H = 4.5

Z_FRONT_OUT = MOSAICO_T/2 + FRONT_PROUD
Z_BACK_CORE = Z_FRONT_OUT - CORE_T
BAY_X_MIN = -(MOSAICO_W/2 + MODULE_STACK_X + CLR_FIT)
BAY_X_MAX = MOSAICO_W/2 + CLR_FIT
BAY_Y_FLOOR = -(MOSAICO_H/2 + MODULE_UNDER_Y)
BAY_Z_MIN = -(MOSAICO_T/2 + CLR_FIT); BAY_Z_MAX = -BAY_Z_MIN
BATT_Y_BOT = BATT_Y_TOP - BATT_H
Y_BOT_OUT = BATT_Y_BOT - BATT_CLR - USB_ZONE_H - WALL
H_TOTAL = Y_TOP_OUT - Y_BOT_OUT
DOCK_FIELD_XC = DOCK_PIN_FIELD_X0 + (DOCK_COLS-1)*DOCK_PITCH/2

S = 3.0          # 像素/毫米
MX, MY = 280, 240  # 正视图原点在画布上的位置（模型 0,0）
def fx(x): return MX + x*S
def fy(y): return MY - y*S
SX, SY = 700, 240  # 侧视图原点（Z 向右为 +Z 取反：屏面朝右）
def sx(z): return SX - z*S
def sy(y): return SY - y*S

out = []
def add(s): out.append(s)
def rect(x0,y0,w,h,cls,rx=0,f=fx,g=fy):
    add(f'<rect x="{f(x0):.2f}" y="{g(y0+h):.2f}" width="{w*S:.2f}" height="{h*S:.2f}" rx="{rx*S:.2f}" class="{cls}"/>')
def circ(x,y,d,cls,f=fx,g=fy):
    add(f'<circle cx="{f(x):.2f}" cy="{g(y):.2f}" r="{d*S/2:.2f}" class="{cls}"/>')
def txt(x,y,s,cls="lbl",anchor="middle"):
    add(f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}">{s}</text>')
def dimh(x0,x1,y,label):
    add(f'<line x1="{fx(x0):.2f}" y1="{fy(y):.2f}" x2="{fx(x1):.2f}" y2="{fy(y):.2f}" class="dim"/>')
    txt((fx(x0)+fx(x1))/2, fy(y)-4, label, "dimtxt")
def dimv(y0,y1,x,label):
    add(f'<line x1="{fx(x):.2f}" y1="{fy(y0):.2f}" x2="{fx(x):.2f}" y2="{fy(y1):.2f}" class="dim"/>')
    txt(fx(x)-5, (fy(y0)+fy(y1))/2, label, "dimtxt", "end")

W = 900; H = 520
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
add('''<style>
 text{font-family:"Helvetica Neue",Arial,sans-serif}
 .lbl{font-size:9px;fill:#333}.ttl{font-size:13px;fill:#111;font-weight:600}
 .dimtxt{font-size:8px;fill:#0b6}
 .out{fill:#f7f7f7;stroke:#222;stroke-width:1.2}
 .grip{fill:#ececec;stroke:#888;stroke-width:0.8}
 .bay{fill:#fff;stroke:#c33;stroke-width:1.1}
 .win{fill:#dfeaf5;stroke:#36c;stroke-width:0.9}
 .key{fill:#fff;stroke:#222;stroke-width:0.9}
 .hid{fill:none;stroke:#999;stroke-width:0.7;stroke-dasharray:4 3}
 .pogo{fill:#c33;stroke:none}
 .dim{stroke:#0b6;stroke-width:0.6}
 .ctr{stroke:#c9c;stroke-width:0.5;stroke-dasharray:6 2 1 2}
 .brd{fill:none;stroke:#960;stroke-width:0.9;stroke-dasharray:5 2}
</style>''')
add('<rect width="100%" height="100%" fill="#ffffff"/>')

# ---- 正视图 ----
txt(MX+W_TOTAL*S/2, 22, "正视（+Z 朝用户）：屏朝用户、USB-C 朝下、左槽在左", "ttl")
rect(-W_TOTAL/2, Y_BOT_OUT, W_TOTAL, H_TOTAL, "out", 6)
for s in (-1,1):
    rect(min(s*GRIP_X_IN, s*W_TOTAL/2), GRIP_Y_BOT, abs(W_TOTAL/2-GRIP_X_IN), GRIP_Y_TOP-GRIP_Y_BOT, "grip", 8)
rect(BAY_X_MIN, BAY_Y_FLOOR, BAY_X_MAX-BAY_X_MIN, Y_TOP_OUT-BAY_Y_FLOOR, "bay", 1)
rect(-MOSAICO_W/2+BEZEL_OVERLAP, -MOSAICO_H/2+BEZEL_OVERLAP,
     MOSAICO_W-2*BEZEL_OVERLAP, MOSAICO_H-2*BEZEL_OVERLAP, "win", 1)
txt(fx(0), fy(0)+3, "屏窗 41.19²")
# 弹簧针场
for c in range(DOCK_COLS):
    for r in (1,-1):
        circ(DOCK_PIN_FIELD_X0+c*DOCK_PITCH, BAY_Y_FLOOR+ (1.0 if r>0 else -1.0), 1.4, "pogo")
txt(fx(DOCK_FIELD_XC), fy(BAY_Y_FLOOR)+11, "弹簧针 2×8 列1..8")
# D-pad
add(f'<path class="key" d="M {fx(DPAD_X-DPAD_ARM_L):.1f} {fy(DPAD_Y+DPAD_ARM_W/2):.1f} '
    f'h {(DPAD_ARM_L-DPAD_ARM_W/2)*S:.1f} v {-(DPAD_ARM_L-DPAD_ARM_W/2)*S:.1f} '
    f'h {DPAD_ARM_W*S:.1f} v {(DPAD_ARM_L-DPAD_ARM_W/2)*S:.1f} h {(DPAD_ARM_L-DPAD_ARM_W/2)*S:.1f} '
    f'v {DPAD_ARM_W*S:.1f} h {-(DPAD_ARM_L-DPAD_ARM_W/2)*S:.1f} v {(DPAD_ARM_L-DPAD_ARM_W/2)*S:.1f} '
    f'h {-DPAD_ARM_W*S:.1f} v {-(DPAD_ARM_L-DPAD_ARM_W/2)*S:.1f} h {-(DPAD_ARM_L-DPAD_ARM_W/2)*S:.1f} Z"/>')
for nm,(dx,dy) in {"UP":(0,DPAD_SW_R),"DOWN":(0,-DPAD_SW_R),"LEFT":(-DPAD_SW_R,0),"RIGHT":(DPAD_SW_R,0)}.items():
    circ(DPAD_X+dx, DPAD_Y+dy, 2.0, "pogo"); txt(fx(DPAD_X+dx), fy(DPAD_Y+dy)-4, nm)
# ABXY
for nm,(dx,dy) in {"A":(ABXY_R,0),"X":(0,ABXY_R),"Y":(-ABXY_R,0),"B":(0,-ABXY_R)}.items():
    circ(ABXY_X+dx, ABXY_Y+dy, ABXY_D, "key"); txt(fx(ABXY_X+dx), fy(ABXY_Y+dy)+3, nm)
# L/R
for s,nm in ((-1,"L"),(1,"R")):
    rect(s*LR_X-LR_BAR_W/2, LR_Y-LR_BAR_H/2, LR_BAR_W, LR_BAR_H, "key", 2)
    txt(fx(s*LR_X), fy(LR_Y)+3, nm)
# 隐藏件
rect(BATT_X_CTR-BATT_W/2, BATT_Y_BOT, BATT_W, BATT_H, "hid")
txt(fx(BATT_X_CTR), fy(BATT_Y_TOP-BATT_H/2)+3, "电池仓 50×34×8")
rect(NATIVE_USB_X-NATIVE_USB_W/2, Y_BOT_OUT, NATIVE_USB_W, BAY_Y_FLOOR-Y_BOT_OUT, "hid")
txt(fx(NATIVE_USB_X), fy(BAY_Y_FLOOR-14), "原生")
txt(fx(NATIVE_USB_X), fy(BAY_Y_FLOOR-18), "USB-C")
txt(fx(NATIVE_USB_X), fy(BAY_Y_FLOOR-22), "直通道")
rect(DOCK_USB_X-DOCK_USB_W/2, Y_BOT_OUT, DOCK_USB_W, 3.0, "key", 1)
txt(fx(DOCK_USB_X), fy(Y_BOT_OUT)+11, "底座 USB-C")
add(f'<line x1="{fx(0):.1f}" y1="{fy(Y_TOP_OUT+6):.1f}" x2="{fx(0):.1f}" y2="{fy(Y_BOT_OUT-6):.1f}" class="ctr"/>')
dimh(-W_TOTAL/2, W_TOTAL/2, Y_TOP_OUT+7, f"总长 {W_TOTAL:.1f}")
dimv(Y_BOT_OUT, Y_TOP_OUT, -W_TOTAL/2-7, f"总高 {H_TOTAL:.1f}")
dimh(BAY_X_MIN, BAY_X_MAX, BAY_Y_FLOOR-7, f"落入槽 {BAY_X_MAX-BAY_X_MIN:.2f}")

# ---- 侧视图 ----
txt(SX-40, 22, "侧视（自 +X 看，屏面朝右）", "ttl")
add(f'<rect x="{sx(Z_FRONT_OUT):.2f}" y="{sy(Y_TOP_OUT):.2f}" width="{CORE_T*S:.2f}" '
    f'height="{H_TOTAL*S:.2f}" rx="{6*S:.2f}" class="out"/>')
add(f'<rect x="{sx(Z_BACK_CORE):.2f}" y="{sy(GRIP_Y_TOP):.2f}" width="{GRIP_DEPTH_BOT*S:.2f}" '
    f'height="{(GRIP_Y_TOP-GRIP_Y_BOT)*S:.2f}" rx="{4*S:.2f}" class="grip"/>')
add(f'<rect x="{sx(BAY_Z_MAX):.2f}" y="{sy(Y_TOP_OUT):.2f}" width="{(BAY_Z_MAX-BAY_Z_MIN)*S:.2f}" '
    f'height="{(Y_TOP_OUT-BAY_Y_FLOOR)*S:.2f}" class="bay"/>')
txt(sx(0), sy(0)+3, "Mosaico 11.48")
add(f'<rect x="{sx(BOARD_Z_FRONT):.2f}" y="{sy(30.5):.2f}" width="{BOARD_T*S:.2f}" '
    f'height="{(30.5-(BATT_Y_BOT-1))*S:.2f}" class="brd"/>')
txt(sx(BOARD_Z_FRONT)-30, sy(-40), "主板 XY 面", "lbl", "end")
add(f'<rect x="{sx(-4.5):.2f}" y="{sy(BATT_Y_TOP):.2f}" width="{BATT_T*S:.2f}" '
    f'height="{BATT_H*S:.2f}" class="hid"/>')
txt(sx(-8.5)-6, sy(BATT_Y_TOP-BATT_H/2), "电池", "lbl", "end")
txt(SX-40, sy(Y_BOT_OUT)+16, f"核心板厚 {CORE_T:.1f}　握把最厚 {CORE_T+GRIP_DEPTH_BOT:.1f}", "dimtxt")
txt(SX-40, sy(Y_BOT_OUT)+28, "分型面 Z = −6.09（落入槽背面）", "dimtxt")
txt(20, H-14, "提案 · 未冻结 · claude-opus-5 起草 · 待 Chrome 采纳、Hiro 复核 · 不得据以制造 "
              "· 全部尺寸为 ASSUMPTION（AS-01/AS-07/AS-12/AS-22/AS-31-mechdock-*）", "lbl", "start")
add('</svg>')
print("\n".join(out))
