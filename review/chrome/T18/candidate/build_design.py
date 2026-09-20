"""Generate the editable electrical draft and placement study. NOT manufacturing data."""
from pathlib import Path
import json, re, uuid, math, csv, html, collections
import argparse, hashlib, os, platform, sys

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / 'references'
OUT = ROOT / 'design'
REV = 'A0-DRAFT'
components = []
libraries = {}

# --- T18 提案：输入冻结、占位声明与硬失败 ---------------------------------
# 本节为机制改动，不改变任何器件、封装、网络或坐标取值。
# 提案，待 Chrome 采纳、Hiro 复核。

POLICY_SCHEMA = 'mosaico-library-policy/1'
LOCK_SCHEMA = 'mosaico-references-lock/1'
POLICY_VALUES = ('require_library', 'allow_placeholder', 'unresolved')
ALLOW_MISSING_TAG = ' [UNRESOLVED via --allow-missing]'

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--out-dir', default=None,
                help='产物输出目录。默认为仓库内 design/；写入该目录必须同时给出 --allow-overwrite-baseline。')
ap.add_argument('--allow-overwrite-baseline', action='store_true',
                help='允许把产物写回仓库内 design/，即覆盖已审查基线。')
ap.add_argument('--policy', default=None, help='占位声明清单路径（默认 design/library-policy.json）。')
ap.add_argument('--lock', default=None, help='缓存锁文件路径（默认 design/references-lock.json）。')
ap.add_argument('--write-policy', action='store_true',
                help='登记模式：按仓库现状机械生成占位声明清单，不生成产物。清单内容仍待 Chrome 填写与裁决。')
ap.add_argument('--write-lock', action='store_true',
                help='登记模式：按 references/ 现状重新生成锁文件，不生成产物，且跳过锁校验。')
ap.add_argument('--allow-missing', action='store_true',
                help='把库缺失／无效／未裁决降级为警告继续生成。默认关闭；开启时 stdout、stderr 与 BOM 均留显式标记。')
ARGS = ap.parse_args()

POLICY_PATH = Path(ARGS.policy).resolve() if ARGS.policy else (OUT / 'library-policy.json')
LOCK_PATH = Path(ARGS.lock).resolve() if ARGS.lock else (OUT / 'references-lock.json')
REGISTRY_MODE = ARGS.write_policy or ARGS.write_lock

if ARGS.out_dir:
    OUT = Path(ARGS.out_dir).resolve()
if not REGISTRY_MODE and OUT == (ROOT / 'design') and not ARGS.allow_overwrite_baseline:
    sys.stderr.write(
        '拒绝写入 %s：该目录保存已审查基线。\n'
        '请用 --out-dir 指定对照目录，或在确实要覆盖基线时显式给出 --allow-overwrite-baseline。\n'
        % (ROOT / 'design'))
    raise SystemExit(2)


def rel(p):
    try:
        return Path(p).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(p)


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def write_text_lf(path, text):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


ERRORS = []      # 阻断项：生成前一次性列出并以非零码退出，退出前不写出任何产物
WARNINGS = []    # --allow-missing 降级后的同类项
UNRESOLVED_REFS = set()   # 被 --allow-missing 放行的位号，用于 BOM 标记
NOTICES = []


def record(ref, code, path, kind, detail, downgradable=True):
    row = {'refdes': ref, 'lcsc': code, 'path': path, 'kind': kind, 'detail': detail}
    if downgradable and ARGS.allow_missing:
        WARNINGS.append(row)
        if ref:
            UNRESOLVED_REFS.add(ref)
    else:
        ERRORS.append(row)


def fail(msg):
    sys.stderr.write(msg.rstrip('\n') + '\n')
    raise SystemExit(1)


def _table(rows, title):
    out = ['', title, '-' * len(title),
           '%-8s %-10s %-34s %-22s %s' % ('位号', 'LCSC', '文件', '类别', '细节')]
    for r in rows:
        out.append('%-8s %-10s %-34s %-22s %s'
                   % (r['refdes'] or '-', r['lcsc'] or '-', r['path'] or '-', r['kind'], r['detail']))
    return '\n'.join(out)


_reported = []


def check_errors():
    if WARNINGS and not _reported:
        sys.stderr.write(_table(WARNINGS, '警告：--allow-missing 已放行下列问题，产物不得作为基线候选') + '\n')
        _reported.append(True)
    if ERRORS:
        sys.stderr.write(_table(ERRORS, '阻断：下列问题必须解决后才能生成产物') + '\n')
        sys.stderr.write('\n共 %d 项阻断，未写出任何产物。\n' % len(ERRORS))
        raise SystemExit(1)


# --- 库解析：三态，取代原先「返回 None」的二态 ---------------------------
# OK / MISSING / INVALID。原实现把「文件不存在」与「失败记录」压成同一个 None，
# 调用方无法区分，也无法在日志中留下痕迹。

def resolve_code(code):
    """按 LCSC 编码解析缓存文件，返回三态结果（按编码缓存，不含位号信息）。"""
    if code in libraries:
        return libraries[code]
    p = REF / (code + '.json')
    r = {'code': code, 'path': rel(p), 'state': None, 'detail': '', 'data': None,
         'sha256': None, 'bytes': None}
    if not p.exists():
        r['state'] = 'MISSING'
        r['detail'] = '文件不存在'
        libraries[code] = r
        return r
    raw = p.read_bytes()
    r['sha256'] = hashlib.sha256(raw).hexdigest()
    r['bytes'] = len(raw)
    try:
        d = json.loads(raw.decode('utf-8-sig'))
    except Exception as e:
        r['state'] = 'INVALID'
        r['detail'] = 'JSON 解析失败：%s' % e
        libraries[code] = r
        return r
    if not d.get('success'):
        r['state'] = 'INVALID'
        r['detail'] = '失败记录：success=%r code=%r message=%r' % (
            d.get('success'), d.get('code'), d.get('message'))
    elif not d.get('result'):
        r['state'] = 'INVALID'
        r['detail'] = 'result 为空'
    elif not d['result'].get('packageDetail'):
        r['state'] = 'INVALID'
        r['detail'] = '缺少 packageDetail（原实现会在此静默落入本地占位）'
    else:
        r['state'] = 'OK'
        r['data'] = d['result']
    libraries[code] = r
    return r


# --- 占位声明清单 ---------------------------------------------------------

POLICY = {}
POLICY_ORDER = []
POLICY_LOADED = False
POLICY_SHA = None

if not ARGS.write_policy:
    if not POLICY_PATH.exists():
        fail('占位声明清单不存在：%s\n先执行 --write-policy 生成骨架，再由 Chrome 逐行填写与裁决。' % rel(POLICY_PATH))
    POLICY_SHA = sha256_file(POLICY_PATH)
    _pj = json.loads(POLICY_PATH.read_text(encoding='utf-8'))
    if _pj.get('schema') != POLICY_SCHEMA:
        fail('占位声明清单 schema 不符：%r，期望 %r（%s）' % (_pj.get('schema'), POLICY_SCHEMA, rel(POLICY_PATH)))
    for e in _pj.get('entries', []):
        ref = e.get('refdes')
        if not ref:
            fail('占位声明清单存在缺少 refdes 的条目：%s' % rel(POLICY_PATH))
        if ref in POLICY:
            fail('占位声明清单位号重复：%s（%s）' % (ref, rel(POLICY_PATH)))
        POLICY[ref] = e
        POLICY_ORDER.append(ref)
    POLICY_LOADED = True


_resolved_ref = {}
_policy_seen = set()


def resolve_for(ref, code):
    """按位号解析库，并按清单判定是否放行。同一位号只记录一次错误。"""
    if ref in _resolved_ref:
        return _resolved_ref[ref]
    _policy_seen.add(ref)
    res = resolve_code(code) if code else None

    if ARGS.write_policy:          # 登记模式：不判定，只解析
        out = res if (res and res['state'] == 'OK') else None
        _resolved_ref[ref] = out
        return out

    ent = POLICY.get(ref)
    if ent is None:
        record(ref, code, rel(POLICY_PATH), 'POLICY_MISSING',
               '位号未在占位声明清单中登记', downgradable=False)
        _resolved_ref[ref] = res if (res and res['state'] == 'OK') else None
        return _resolved_ref[ref]

    pol = ent.get('policy')
    if pol not in POLICY_VALUES:
        record(ref, code, rel(POLICY_PATH), 'POLICY_INVALID',
               'policy=%r，允许值为 %s' % (pol, '/'.join(POLICY_VALUES)), downgradable=False)
        _resolved_ref[ref] = res if (res and res['state'] == 'OK') else None
        return _resolved_ref[ref]

    declared = ent.get('lcsc', '')
    if declared != code:
        record(ref, code, rel(POLICY_PATH), 'POLICY_CODE_MISMATCH',
               '清单登记编码 %r 与生成器实际引用 %r 不一致' % (declared, code), downgradable=False)

    if pol == 'allow_placeholder':
        if res is not None and res['state'] != 'OK':
            record(ref, code, res['path'], 'LIB_' + res['state'],
                   '清单允许占位，但仍引用了不可用的编码：%s' % res['detail'], downgradable=False)
        out = res if (res and res['state'] == 'OK') else None
        _resolved_ref[ref] = out
        return out

    # require_library / unresolved
    if pol == 'unresolved':
        record(ref, code, res['path'] if res else '-', 'POLICY_UNRESOLVED',
               '清单标记为 unresolved（待 Chrome 裁决）；当前缓存状态：%s'
               % (res['state'] if res else 'NO_CODE'))
    if not code:
        record(ref, '', '-', 'NO_CODE', 'policy=%s 但该位号未指定 LCSC 编码' % pol,
               downgradable=(pol == 'unresolved'))
        _resolved_ref[ref] = None
        return None
    if res['state'] != 'OK' and pol == 'require_library':
        record(ref, code, res['path'], 'LIB_' + res['state'], res['detail'])
    out = res if res['state'] == 'OK' else None
    _resolved_ref[ref] = out
    return out


def lib_of(c):
    """返回该位号可用的库数据（result），不可用时返回 None。"""
    res = resolve_for(c['ref'], c['code'])
    return res['data'] if res else None


# --- 锁文件 ---------------------------------------------------------------

LOCK = None
LOCK_SHA = None
if not REGISTRY_MODE:
    if not LOCK_PATH.exists():
        fail('缓存锁文件不存在：%s\n先执行 --write-lock 登记当前 references/ 状态。' % rel(LOCK_PATH))
    LOCK_SHA = sha256_file(LOCK_PATH)
    LOCK = json.loads(LOCK_PATH.read_text(encoding='utf-8'))
    if LOCK.get('schema') != LOCK_SCHEMA:
        fail('缓存锁文件 schema 不符：%r，期望 %r（%s）' % (LOCK.get('schema'), LOCK_SCHEMA, rel(LOCK_PATH)))


def verify_lock_entries():
    """逐条比对锁文件登记与 references/ 实际状态。任何差异都是阻断项。"""
    if LOCK is None:
        return
    for e in LOCK.get('entries', []):
        code = e['lcsc']
        actual = resolve_code(code)
        if actual['state'] != e.get('state'):
            record('', code, e.get('path', ''), 'LOCK_STATE_CHANGED',
                   '锁文件登记 state=%s，实际 state=%s（%s）'
                   % (e.get('state'), actual['state'], actual['detail'] or '-'),
                   downgradable=False)
            continue
        if actual['state'] == 'MISSING':
            continue
        if actual['sha256'] != e.get('sha256'):
            record('', code, e.get('path', ''), 'LOCK_HASH_MISMATCH',
                   '锁文件登记 %s，实际 %s' % (e.get('sha256'), actual['sha256']),
                   downgradable=False)
        elif actual['bytes'] != e.get('bytes'):
            record('', code, e.get('path', ''), 'LOCK_SIZE_MISMATCH',
                   '锁文件登记 %s 字节，实际 %s 字节' % (e.get('bytes'), actual['bytes']),
                   downgradable=False)


def verify_lock_coverage(refs_by_code):
    if LOCK is None:
        return
    locked = set(e['lcsc'] for e in LOCK.get('entries', []))
    used = set(k for k in refs_by_code if k)
    for code in sorted(used - locked):
        record(', '.join(refs_by_code[code]), code, rel(REF / (code + '.json')), 'LOCK_UNREGISTERED',
               '生成器引用了该编码，但锁文件未登记', downgradable=False)
    for code in sorted(locked - used):
        record('', code, rel(REF / (code + '.json')), 'LOCK_STALE_ENTRY',
               '锁文件登记了该编码，但生成器已不再引用', downgradable=False)
    gen = (LOCK.get('generator') or {})
    actual_gen = sha256_file(Path(__file__).resolve())
    if gen.get('sha256') and gen['sha256'] != actual_gen:
        NOTICES.append('生成器自身 sha256 与锁文件登记不一致：锁 %s，实际 %s。'
                       '本提案把它记为提示而非阻断（生成器是受审查的代码，不是输入缓存）；'
                       '是否升级为阻断交 Chrome 裁决。' % (gen['sha256'], actual_gen))
    pol = (LOCK.get('policy') or {})
    if pol.get('sha256') and POLICY_SHA and pol['sha256'] != POLICY_SHA:
        NOTICES.append('占位声明清单 sha256 与锁文件登记不一致：锁 %s，实际 %s。同上，记为提示。'
                       % (pol['sha256'], POLICY_SHA))


def uid(s): return 'gge' + uuid.uuid5(uuid.NAMESPACE_URL, 'mosaico-handheld/'+s).hex
def fmt(v): return ('%.5f' % float(v)).rstrip('0').rstrip('.')
def esc(v): return str(v).replace('~','-').replace('`', "'")

def add(ref, code, value, nets, group, xy, kind='ic', note='', pins=None, package=None):
    res = resolve_for(ref, code)
    d = res['data'] if res else None
    if pins is None:
        if not d:
            record(ref, code, rel(REF / ((code or '?') + '.json')), 'NO_PINS',
                   '未显式给出 pins 且库不可用，无法推导引脚表', downgradable=False)
            pins = dict((k, k) for k in nets)      # 仅为继续收集错误；出错时不会写出任何产物
        else:
            pins = {}
            for s in d['dataStr']['shape']:
                if s.startswith('P~'):
                    a = s.split('^^'); pins[a[0].split('~')[3]] = a[3].split('~')[4]
    if set(nets) != set(pins):
        record(ref, code, '-', 'PIN_NET_MISMATCH',
               '引脚集合与网络集合不符：%s' % sorted(set(nets) ^ set(pins)), downgradable=False)
    if package is None and not d:
        record(ref, code, '-', 'NO_PACKAGE',
               '既无可用库、也未显式给出 package，封装名会退化为 TBD', downgradable=False)
    c = dict(ref=ref,code=code,value=value,nets=nets,pins=pins,group=group,xy=xy,
             kind=kind,note=note,package=package or (d['dataStr']['head']['c_para']['package'] if d else 'TBD'))
    components.append(c)
    return c

def passive(ref,value,code,a,b,group,xy,kind='res',note=''):
    res = resolve_for(ref, code)
    d = res['data'] if res else None
    return add(ref,code,value,{'1':a,'2':b},group,xy,kind,note,pins={'1':'1','2':'2'},
               package=None if d else ('C0603' if kind=='cap' else 'R0603'))

# Actual pin numbers are checked against manufacturer pin tables, not inferred from symbol positions.
keynets=['KEY_UP','KEY_DOWN','KEY_LEFT','KEY_RIGHT','KEY_A','KEY_B','KEY_X','KEY_Y',
         'KEY_L','KEY_R','KEY_MODE','GAUGE_ALERT_N','POWER_FAULT_N','SPARE_13','SPARE_14','SPARE_15']
keypins=[str(i) for i in list(range(4,12))+list(range(13,21))]
n=dict(zip(keypins,keynets));n.update({'1':'IO_INT_N','2':'GND','3':'GND','12':'GND','21':'GND',
                                  '22':'DOCK_SCL','23':'DOCK_SDA','24':'DOCK_3V3'})
add('U1','C130204','TCA9535PWR',n,'input',(42,33),note='7-bit address 0x20; 16 external pull-ups; interrupt test point only')
positions=[(25,23),(25,41),(16,32),(34,32),(138,32),(129,41),(120,32),(129,23),(25,6),(129,6),(40,48)]
for i,net in enumerate(keynets[:11]):
    add('SW'+str(i+1),'C720477',net[4:],{'1':net,'2':'GND'},'input',positions[i],kind='switch')
for i,net in enumerate(keynets):
    passive('R'+str(i+1),'10k 1%','C25804','DOCK_3V3',net,'input',(38+(i%4)*2.8,19+(i//4)*2.6))
passive('R17','10k 1%','C25804','DOCK_3V3','IO_INT_N','input',(46,35))
passive('C1','100nF 50V X7R','C1591','DOCK_3V3','GND','input',(45,30),'cap')
passive('C2','1uF 50V X5R','C15849','DOCK_3V3','GND','input',(45,33),'cap')

# Charging: USB-C 5 V only, 500 mA input ceiling; intended for a suitable power adapter.
# A battery may supplement the system while the source current limit is reached.
usb={'A1B12':'GND','B1A12':'GND','A4B9':'USB_5V','B4A9':'USB_5V','A5':'CC1','B5':'CC2',
     'A6':None,'B6':None,'A7':None,'B7':None,'A8':None,'B8':None,'1':'GND','2':'GND','3':'GND','4':'GND'}
add('J1','C165948','USB-C CHARGE 5V',usb,'charge',(18,59),note='Data pins intentionally NC; verify exact PCB-edge datum and shell solder process')
passive('R18','5.1k 1%','C23186','CC1','GND','charge',(25,55))
passive('R19','5.1k 1%','C23186','CC2','GND','charge',(28,55))
add('U2','C54313','BQ24074RGTR',{'1':'BAT_NTC','2':'PACK_P','3':'PACK_P','4':'GND','5':'GND',
    '6':'SYS_RAW','7':'CHG_PGOOD_N','8':'GND','9':'CHG_ACTIVE_N','10':'SYS_RAW','11':'SYS_RAW',
    '12':'CHG_ILIM','13':'USB_5V','14':'CHG_TMR','15':None,'16':'CHG_ISET','17':'GND'},
    'charge',(34,55),note='EN1=1 EN2=0: <=500mA input; ITERM NC: 10%; actual charge current load-dependent')
add('J2','C160353','PROTECTED 1S PACK + NTC',{'1':'PACK_P','2':'BAT_NTC','3':'GND','4':'GND','5':'GND'},
    'charge',(8,47),note='Pin order is OUR specification, not a universal battery standard; pack/cable must match')
passive('R20','1.8k 1%','C4177','CHG_ISET','GND','charge',(34,51),note='890/1800 = 0.494 A nominal; verify selected pack permits this current')
passive('R21','3.3k 1%','C22978','CHG_ILIM','GND','charge',(37,52),note='ILIM must be populated even in fixed USB input-current mode')
passive('R22','47k 1%','C25819','CHG_TMR','GND','charge',(37,55),note='Fast-charge safety timer approx. 6.27h before DPPM timer extensions')
passive('R23','4.7k 1%','C23162','USB_5V','LED_CHG_A','charge',(29,60))
passive('R24','4.7k 1%','C23162','USB_5V','LED_PG_A','charge',(34,60))
add('D1','C2296','CHARGE',{'1':'CHG_ACTIVE_N','2':'LED_CHG_A'},'charge',(30,62),kind='led')
add('D2','C2296','USB VALID',{'1':'CHG_PGOOD_N','2':'LED_PG_A'},'charge',(35,62),kind='led')
for ref,val,code,net,xy in [('C3','1uF 50V X5R','C15849','USB_5V',(31,55)),
                            ('C4','10uF 25V X5R','C96446','PACK_P',(10,54)),
                            ('C5','22uF 25V X5R','C45783','SYS_RAW',(39,58))]:
    passive(ref,val,code,net,'GND','charge',xy,'cap')

# Boost and output protection. Switch controls EN, not the battery's load current.
add('U3','C919459','TPS61023DRLR',{'1':'BOOST_FB','2':'DOCK_EN','3':'SYS_RAW','4':'GND','5':'BOOST_SW','6':'BOOST_5V'},
    'power',(112,48),note='Nominal 4.992V; tolerances, ripple and downstream voltage drop require bench validation')
add('L1','C5832342','1uH 4.6A Isat',{'1':'SYS_RAW','2':'BOOST_SW'},'power',(109,48),kind='inductor')
add('SW12','C431540','DOCK POWER',{'1':'SYS_RAW','2':'DOCK_EN','3':'GND','4':'GND'},
    'power',(143,58),kind='slide',note='Mechanical slide pin map must be checked against exact part drawing')
passive('R25','100k 1%','C25803','DOCK_EN','GND','power',(139,55))
passive('R26','732k 1%','C23239','BOOST_5V','BOOST_FB','power',(112,52))
passive('R27','100k 1%','C25803','BOOST_FB','GND','power',(115,52))
add('U8','C55266','TPS2553DBVR',{'1':'BOOST_5V','2':'GND','3':'BOOST_5V','4':'POWER_FAULT_N','5':'OUT_ILIM','6':'LIMITED_5V'},
    'power',(119,48),pins={'1':'IN','2':'GND','3':'EN','4':'FAULT_N','5':'ILIM','6':'OUT'},package='SOT-23-6_L2.9-W1.6-P0.95-LS2.8',
    note='26.1k gives approx. 0.91-1.08A current limit (TI table); constant-current version, not -1')
passive('R28','26.1k 1%','', 'OUT_ILIM','GND','power',(119,52),note='Exact LCSC procurement code pending')
add('U4','C2869734','LM66100DCKR',{'1':'LIMITED_5V','2':'GND','3':'POGO_5V','4':None,'5':'GND','6':'POGO_5V'},
    'power',(124,48),note='CE tied to VOUT is required for reverse-current blocking')
add('U5','C404027','TLV75533PDBVR',{'1':'BOOST_5V','2':'GND','3':'BOOST_5V','4':None,'5':'DOCK_3V3'},
    'power',(134,49),note='Dock logic supply; does not use Pogo positive as a 3.3V rail')
for ref,val,code,net,xy in [('C6','10uF 25V X5R','C96446','SYS_RAW',(108,51)),
    ('C7','22uF 25V X5R','C45783','BOOST_5V',(113,45)),('C8','22uF 25V X5R','C45783','BOOST_5V',(116,45)),
    ('C9','100nF 50V X7R','C1591','BOOST_5V',(118,45)),('C10','1uF 50V X5R','C15849','LIMITED_5V',(123,45)),
    ('C11','1uF 50V X5R','C15849','POGO_5V',(127,48)),('C12','1uF 50V X5R','C15849','BOOST_5V',(132,46)),
    ('C13','1uF 50V X5R','C15849','DOCK_3V3',(137,49))]:
    passive(ref,val,code,net,'GND','power',xy,'cap')

# Dock-side I2C pullups only. Host-side pullups already exist on MCU_3V3 in Mosaico (R1/R2).
add('U6','C544515','TCA9517DGKR',{'1':'DOCK_3V3','2':'HOST_SCL','3':'HOST_SDA','4':'GND',
    '5':'DOCK_3V3','6':'DOCK_SDA','7':'DOCK_SCL','8':'DOCK_3V3'},'bus',(110,35),
    note='A side to Mosaico; B side to dock. NO dock-powered pullups on HOST_SDA/HOST_SCL.')
passive('R29','4.7k 1%','C23162','DOCK_3V3','DOCK_SDA','bus',(113,31))
passive('R30','4.7k 1%','C23162','DOCK_3V3','DOCK_SCL','bus',(113,33))
for ref,xy in [('C14',(107,33)),('C15',(113,37))]:passive(ref,'100nF 50V X7R','C1591','DOCK_3V3','GND','bus',xy,'cap')
add('U7','C2682616','MAX17048G+T10',{'1':'GND','2':'PACK_P','3':'PACK_P','4':'GND','5':'GAUGE_ALERT_N',
    '6':'GND','7':'DOCK_SCL','8':'DOCK_SDA','9':'GND'},'bus',(9,38),note='7-bit address 0x36; measures dock battery, not Mosaico internal battery')
passive('C16','100nF 50V X7R','C1591','PACK_P','GND','bus',(9,35),'cap')
# Numbering below is from the TOP of the dock, mirrored from the official rear-view photograph.
add('J3','','POGO INTERFACE - GEOMETRY TBD',{'1':'HOST_SCL','2':'GND','3':'POGO_5V','4':'HOST_SDA'},
    'bus',(77,35),pins={'1':'SCL','2':'GND','3':'+5V','4':'SDA'},package='POGO_GEOMETRY_UNVERIFIED',
    note='2.54mm pitch is a placeholder, NOT a released dimension. Replace with verified drawing before routing.')
for i,net in enumerate(['GND','USB_5V','PACK_P','SYS_RAW','BOOST_5V','POGO_5V','DOCK_3V3','HOST_SDA','HOST_SCL','DOCK_SDA','DOCK_SCL','IO_INT_N']):
    add('TP'+str(i+1),'',net,{'1':net},'test',(10+i*3.4,13),kind='test',pins={'1':'TP'},package='TESTPAD_1.0mm')

# --- 全部器件登记完毕：先校验输入，再决定是否生成 -------------------------

REFS_BY_CODE = collections.OrderedDict()
for c in components:
    REFS_BY_CODE.setdefault(c['code'], []).append(c['ref'])

if POLICY_LOADED:
    for ref in POLICY_ORDER:
        if ref not in _policy_seen:
            record(ref, POLICY[ref].get('lcsc', ''), rel(POLICY_PATH), 'POLICY_STALE_ENTRY',
                   '清单登记了该位号，但生成器已不再定义它', downgradable=False)

verify_lock_entries()
verify_lock_coverage(REFS_BY_CODE)


def placeholder_rows():
    rows = []
    for c in components:
        if resolve_for(c['ref'], c['code']) is None:
            ent = POLICY.get(c['ref'], {})
            rows.append({'refdes': c['ref'], 'lcsc': c['code'],
                         'policy': ent.get('policy', '(未登记)'),
                         'reason': ent.get('reason', ''),
                         'allow_missing_release': c['ref'] in UNRESOLVED_REFS})
    return rows


def lock_document():
    entries = []
    for code in REFS_BY_CODE:
        if not code:
            continue
        r = resolve_code(code)
        d = r['data'] or {}
        pd = d.get('packageDetail') or {}
        entries.append(collections.OrderedDict([
            ('lcsc', code), ('path', r['path']), ('state', r['state']),
            ('sha256', r['sha256']), ('bytes', r['bytes']),
            ('detail', r['detail'] or None),
            ('result_uuid', d.get('uuid')), ('result_title', d.get('title')),
            ('result_update_time', d.get('updateTime')),
            ('package_uuid', pd.get('uuid')), ('package_title', pd.get('title')),
            ('package_update_time', pd.get('updateTime')),
            ('refdes', list(REFS_BY_CODE[code])),
        ]))
    entries.sort(key=lambda e: e['lcsc'])
    return collections.OrderedDict([
        ('schema', LOCK_SCHEMA),
        ('status', '提案，待 Chrome 采纳、Hiro 复核'),
        ('notice', [
            '本文件登记生成器实际引用的每一份库缓存的路径、SHA-256 与文件内读到的器件标识。',
            '生成器启动时逐条校验；state / sha256 / 字节数任一不符即硬失败并列出差异。',
            '重新登记：python3 design/build_design.py --write-lock。',
            'state=MISSING 表示该编码当前没有缓存文件；这本身不是裁决，冻结在哪个状态由 Chrome 决定。',
            '未被任何位号引用的缓存文件不在本文件登记范围内。',
        ]),
        ('generator', collections.OrderedDict([
            ('path', rel(Path(__file__).resolve())),
            ('sha256', sha256_file(Path(__file__).resolve())),
            ('python', platform.python_version()),
        ])),
        ('policy', collections.OrderedDict([
            ('path', rel(POLICY_PATH)),
            ('sha256', POLICY_SHA),
        ])),
        ('entries', entries),
        ('placeholders', [collections.OrderedDict([('refdes', r['refdes']), ('lcsc', r['lcsc']),
                                                   ('policy', r['policy'])])
                          for r in placeholder_rows()]),
    ])


def policy_document():
    """按仓库现状机械推出清单骨架。不含任何器件或封装取舍；每行均标为未审查。"""
    entries = []
    for c in components:
        code = c['code']
        if not code:
            pol = 'allow_placeholder'
            derived = "仓库现状：build_design.py 未给该位号指定 LCSC 编码（code=''），几何由脚本本地绘制。"
        else:
            r = resolve_code(code)
            if r['state'] == 'OK':
                pol = 'require_library'
                derived = '仓库现状：该位号引用 %s，且 %s 当前可用。' % (code, r['path'])
            else:
                pol = 'unresolved'
                derived = '仓库现状：该位号引用 %s，但 %s 当前不可用（%s）。' % (code, r['path'], r['detail'])
        entries.append(collections.OrderedDict([
            ('refdes', c['ref']), ('lcsc', code), ('policy', pol),
            ('derived_from', derived),
            ('reason', ''), ('placeholder_geometry', ''), ('review_state', '未审查'),
        ]))
    return collections.OrderedDict([
        ('schema', POLICY_SCHEMA),
        ('status', '名单内容待 Chrome 填写与裁决；提案，待 Chrome 采纳、Hiro 复核'),
        ('notice', [
            '本清单声明每个位号是否允许使用本地占位封装。位号在清单中缺席即为错误，生成器硬失败。',
            'policy 允许值：require_library（必须有可用库）、allow_placeholder（允许本地占位）、'
            'unresolved（未裁决，生成器默认硬失败）。',
            'entries 中的 policy 与 derived_from 由 --write-policy 按仓库现状机械推出，'
            '不含任何器件选型或封装取舍，必须由 Chrome 逐行复核后改写。',
            'reason、placeholder_geometry 两列一律留空，review_state 一律为「未审查」，由 Chrome 填写、Hiro 复核。',
            '本清单取消了原生成器中空编码的语义重载：编码只表示编码，是否允许占位只由 policy 表示。',
        ]),
        ('entries', entries),
    ])


if ARGS.write_policy:
    POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(POLICY_PATH, json.dumps(policy_document(), ensure_ascii=False, indent=2) + '\n')
    if ERRORS or WARNINGS:
        sys.stderr.write(_table(ERRORS + WARNINGS, '登记模式：下列问题已写入清单，仍待 Chrome 裁决') + '\n')
    sys.stdout.write(json.dumps({'wrote': rel(POLICY_PATH), 'entries': len(components),
                                 'status': '清单骨架已写出；内容待 Chrome 填写与裁决'},
                                ensure_ascii=False) + '\n')
    raise SystemExit(0)

if ARGS.write_lock:
    # 登记模式只负责如实记录 references/ 的当前状态，不替代占位裁决：
    # 未解决项照样列出，但不阻止锁文件写出，否则永远无法为「缓存缺失」这一状态建立登记。
    if ERRORS or WARNINGS:
        sys.stderr.write(_table(ERRORS + WARNINGS, '登记模式：下列问题已如实登记，仍待 Chrome 裁决') + '\n')
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(LOCK_PATH, json.dumps(lock_document(), ensure_ascii=False, indent=2) + '\n')
    sys.stdout.write(json.dumps({'wrote': rel(LOCK_PATH),
                                 'entries': len([k for k in REFS_BY_CODE if k]),
                                 'unresolved': len(ERRORS) + len(WARNINGS),
                                 'status': '锁文件已写出；冻结点待 Chrome 裁决'},
                                ensure_ascii=False) + '\n')
    raise SystemExit(0)

check_errors()

def text(x,y,s,size=10,mark='L',anchor='start',idseed=''):
    return f'T~{mark}~{fmt(x)}~{fmt(y)}~0~#17324D~Arial~{size}pt~~~~comment~{esc(s)}~1~{anchor}~{uid(idseed+str(x)+str(y)+s)}~0'

def pinshape(ref,num,name,x,y,right=False):
    direction=-20 if right else 20; anchor='end' if right else 'start'; angle=0 if right else 180
    return (f'P~show~0~{num}~{x}~{y}~{angle}~{uid(ref+"pin"+num)}~0^^{x}~{y}^^M {x} {y} h {direction}~#880000'
        f'^^1~{x+direction+( -4 if right else 4)}~{y+4}~0~{esc(name)}~{anchor}~~8pt~#0000FF'
        f'^^1~{x+direction/2}~{y-3}~0~{num}~middle~~7pt~#0000FF^^0~{x+direction}~{y}^^0~M {x+direction} {y}')

def sym(c,x,y):
    ref=c['ref'];pins=list(c['pins'].items());b=[];connections=[]
    simple=c['kind'] in ('res','cap','switch','led','inductor') and len(pins)==2
    half=math.ceil(len(pins)/2);w=200;h=max(60,half*20+20)
    if simple:
        w=40;h=30
        for idx,(num,name) in enumerate(pins):
            px=x-40 if idx==0 else x+40;py=y
            b.append(pinshape(ref,num,'',px,py,idx==1));connections.append((num,px,py,idx==1))
        if c['kind']=='cap':
            b += [f'PL~{x-4} {y-12} {x-4} {y+12}~#880000~1~0~none~{uid(ref+"a")}',
                  f'PL~{x+4} {y-12} {x+4} {y+12}~#880000~1~0~none~{uid(ref+"b")}',
                  f'PL~{x-20} {y} {x-4} {y}~#880000~1~0~none~{uid(ref+"c")}',
                  f'PL~{x+4} {y} {x+20} {y}~#880000~1~0~none~{uid(ref+"d")}']
        elif c['kind']=='switch':
            b += [f'PL~{x-20} {y} {x+14} {y-12}~#880000~1~0~none~{uid(ref+"lever")}',f'C~{x+20}~{y}~2~#880000~1~0~none~{uid(ref+"c")}']
        else:
            b.append(f'R~{x-20}~{y-8}~~~40~16~#880000~1~0~none~{uid(ref+"rect")}~0')
        b += [text(x,y-35,ref,10,'P','middle',ref),text(x,y-20,c['value'],8,'N','middle',ref)]
    else:
        b.append(f'R~{x-w/2}~{y-h/2}~~~{w}~{h}~#880000~1~0~none~{uid(ref+"rect")}~0')
        for idx,(num,name) in enumerate(pins):
            right=idx>=half;k=idx-half if right else idx
            px=x+(w/2+20)*(1 if right else -1);py=y-h/2+20+k*20
            b.append(pinshape(ref,num,name,px,py,right));connections.append((num,px,py,right))
        b += [text(x,y-h/2-32,ref,11,'P','middle',ref),text(x,y-h/2-14,c['value'],9,'N','middle',ref)]
    para={'package':c['package'],'name':c['value'],'pre':ref,'BOM_Manufacturer Part':c['value'],
          'Supplier':'LCSC','Supplier Part':c['code'],'spicePre':re.sub(r'\d','',ref),'spiceSymbolName':c['value']}
    d=lib_of(c)
    if d: para.update({k:v for k,v in d['dataStr']['head']['c_para'].items() if k in ['Manufacturer','Manufacturer Part','JLCPCB Part Class']})
    config='`'.join(esc(t) for kv in para.items() for t in kv)
    shapes=[f'LIB~{x}~{y}~{config}~0~0~{uid(ref)}~0~~{uid("sym"+ref)}~0~'+ '#@$' +'#@$'.join(b)]
    for num,px,py,right in connections:
        net=c['nets'][num]
        if net is None:
            shapes.append(f'O~{px}~{py}~{uid(ref+num+"nc")}~M{px-3},{py-3} L{px+3},{py+3} M{px+3},{py-3} L{px-3},{py+3}~#CC0000')
        else:
            ex=px+(35 if right else -35)
            shapes.append(f'W~{px} {py} {ex} {py}~#008800~1~0~none~{uid(ref+num+"wire")}~0')
            shapes.append(f'N~{ex}~{py}~0~#006060~{net}~{uid(ref+num+"label")}~'+('start' if right else 'end')+f'~{ex+(2 if right else -2)}~{py-2}~Arial~8pt~0')
    c['schxy']=[x,y]
    return shapes

# A single sheet keeps named-net connectivity explicit across all functional sections.
shapes=[text(40,40,'MOSAICO HANDHELD DOCK / A0 ELECTRICAL DRAFT',24),
        text(40,72,'NOT FOR FABRICATION: mechanical interface, battery selection, component sourcing and electrical validation remain open.',13)]
groups=[('input','01 / INPUTS',40,120,1600,1120),('charge','02 / USB-C AND CHARGER',1680,120,1500,1120),
        ('power','03 / BOOST AND PROTECTION',40,1280,1600,1000),('bus','04 / I2C AND BATTERY GAUGE',1680,1280,1500,1000)]
rendered=set()
for group,title,gx,gy,gw,gh in groups:
    shapes += [f'R~{gx}~{gy}~~~{gw}~{gh}~#A0ADBB~1~0~none~{uid(group)}~0',text(gx+20,gy+35,title,18)]
    big=[c for c in components if c['group']==group and c['kind'] in ('ic','slide')]
    small=[c for c in components if c['group']==group and c not in big]
    for i,c in enumerate(big):
        cols=3;x=gx+260+(i%cols)*490;y=gy+270+(i//cols)*320
        shapes+=sym(c,x,y);rendered.add(c['ref'])
    start=gy+(610 if len(big)>3 else 530)
    for i,c in enumerate(small):
        x=gx+210+(i%5)*300;y=start+(i//5)*90
        shapes+=sym(c,x,y);rendered.add(c['ref'])
for i,c in enumerate(c for c in components if c['group']=='test'):
    shapes+=sym(c,230+(i%6)*520,2380+(i//6)*150);rendered.add(c['ref'])
_unrendered=[c['ref'] for c in components if c['ref'] not in rendered]
if _unrendered:
    fail('下列位号未渲染出原理图符号（group 值不在已分派的分组内），但仍会进入 BOM 与 PCB：%s' % _unrendered)
sch={'head':{'docType':'1','editorVersion':'6.5.51','newgId':True,'c_para':{'Prefix Start':'1','name':'Mosaico Dock A0 DRAFT'},'x':0,'y':0},
     'canvas':'CA~3400~2800~#FFFFFF~yes~#CCCCCC~10~3400~2800~line~10~pixel~5~0~0','shape':shapes,'BBox':{'x':0,'y':0,'width':3400,'height':2800},'colors':[]}

def points_move(s,dx,dy):
    a=[float(x) for x in s.split()] if s.strip() else []
    return ' '.join(fmt(n+(dx if i%2==0 else dy)) for i,n in enumerate(a))

def pcbpad(x,y,w,h,num,net,seed,shape='RECT'):
    return f'PAD~{shape}~{fmt(x)}~{fmt(y)}~{fmt(w)}~{fmt(h)}~1~{net or ""}~{num}~0~~0~{uid(seed)}~0~~Y~0~0~0.1~1~0'

def pcbtext(x,y,s,seed,kind='P',layer=3,size=4):
    return f'TEXT~{kind}~{fmt(x)}~{fmt(y)}~0.5~0~none~{layer}~~{size}~{esc(s)}~~~{uid(seed)}~0'

def footprint(c):
    ref=c['ref'];x,y=[v/.254 for v in c['xy']];d=lib_of(c);b=[]
    if d is not None:
        if not d.get('packageDetail'):
            fail('%s：库可用但缺少 packageDetail，不再静默落入本地占位。' % ref)
        pd=d['packageDetail']['dataStr'];hx=float(pd['head']['x']);hy=float(pd['head']['y']);dx=x-hx;dy=y-hy
        for j,s in enumerate(pd['shape']):
            a=s.split('~');t=a[0]
            if t=='PAD':
                a[2]=fmt(float(a[2])+dx);a[3]=fmt(float(a[3])+dy)
                if a[10]:a[10]=points_move(a[10],dx,dy)
                if len(a)>14 and a[14]:a[14]=points_move(a[14],dx,dy)
                if a[8] not in c['nets']:
                    fail('%s：封装内 PAD 的脚号 %r 在设计网络表中不存在。' % (ref,a[8]))
                a[7]=c['nets'][a[8]] or '';a[12]=uid(ref+'pad'+str(j));b.append('~'.join(a))
            elif t=='TRACK' and a[2] in ['3','12']:
                a[4]=points_move(a[4],dx,dy);a[5]=uid(ref+'trk'+str(j));b.append('~'.join(a))
            elif t=='CIRCLE' and a[5] in ['3','12']:
                a[1]=fmt(float(a[1])+dx);a[2]=fmt(float(a[2])+dy);a[6]=uid(ref+'cir'+str(j));b.append('~'.join(a))
            elif t=='HOLE':
                a[1]=fmt(float(a[1])+dx);a[2]=fmt(float(a[2])+dy);a[4]=uid(ref+'hole'+str(j));b.append('~'.join(a))
        c['footprint_status']='Supplier library geometry; final manufacturer audit pending'
    else:
        c['footprint_status']='Locally drawn placeholder; library/land-pattern verification required'
        if ref=='J3':
            for i,n in enumerate(c['pins']):b.append(pcbpad(x+(i-1.5)*10,y,5.9,5.9,n,c['nets'][n],ref+n,'ELLIPSE'))
        elif c['kind']=='test':b.append(pcbpad(x,y,1/.254,1/.254,'1',c['nets']['1'],ref,'ELLIPSE'))
        elif ref=='U8':
            for n,px,py in [('1',-1,0.95),('2',-1,0),('3',-1,-.95),('4',1,-.95),('5',1,0),('6',1,.95)]:
                b.append(pcbpad(x+px/.254,y+py/.254,.8/.254,.6/.254,n,c['nets'][n],ref+n))
        else:
            for i,n in enumerate(c['pins']):b.append(pcbpad(x+(i-.5)*1.6/.254,y,.85/.254,.95/.254,n,c['nets'][n],ref+n))
    b.append(pcbtext(x-3,y-8,ref,ref+'ref'))
    pp='`'.join(esc(t) for t in ['package',c['package'],'Manufacturer Part',c['value'],'Supplier Part',c['code']])
    return f'LIB~{fmt(x)}~{fmt(y)}~{pp}~0~~{uid(ref)}~0~~{uid("fp"+ref)}~0~'+ '#@$' +'#@$'.join(b)

pcbsh=[footprint(c) for c in components]
# Rounded outline, a real closed path but only a provisional ergonomic envelope.
outline=[]
for cx,cy,start in [(148,6,-90),(148,58,0),(6,58,90),(6,6,180)]:
    for a in range(start,start+91,10):outline += [(cx+6*math.cos(math.radians(a)))/.254,(cy+6*math.sin(math.radians(a)))/.254]
outline+=outline[:2]
pcbsh.append('TRACK~0.5~10~~'+' '.join(fmt(v) for v in outline)+'~'+uid('outline')+'~0')
for i,(x,y) in enumerate([(6,6),(148,6),(6,58),(148,58),(48,58),(106,58)]):
    pcbsh.append(f'HOLE~{fmt(x/.254)}~{fmt(y/.254)}~{fmt(2.2/.254)}~{uid("mount"+str(i))}~0')
    pcbsh.append(f'CIRCLE~{fmt(x/.254)}~{fmt(y/.254)}~{fmt(2.5/.254)}~0.5~12~{uid("keepout"+str(i))}~0')
for x1,y1,x2,y2,label in [(50,5,104,59,'MODULE ENVELOPE TBD'),(45,0,109,64,'RF KEEP-OUT TBD')]:
    pts=[x1,y1,x2,y1,x2,y2,x1,y2,x1,y1]
    pcbsh.append('TRACK~0.5~12~~'+' '.join(fmt(v/.254) for v in pts)+'~'+uid(label)+'~0')
    pcbsh.append(pcbtext((x1+2)/.254,(y1+4)/.254,label,label+'text',kind='L',layer=12,size=5))
pcbsh.append(pcbtext(53/.254,48/.254,'A0 DRAFT - DO NOT FAB', 'draftmark',kind='L',size=5))
layers=['1~TopLayer~#FF0000~true~true~true','2~BottomLayer~#0000FF~true~false~true',
 '3~TopSilkLayer~#FFFF00~true~false~true','4~BottomSilkLayer~#808000~false~false~true',
 '5~TopPasterLayer~#808080~false~false~true','6~BottomPasterLayer~#800000~false~false~true',
 '7~TopSolderLayer~#800080~false~false~true','8~BottomSolderLayer~#AA00FF~false~false~true',
 '9~Ratlines~#6464FF~true~false~true','10~BoardOutline~#FF00FF~true~false~true',
 '11~Multi-Layer~#C0C0C0~true~false~true','12~Document~#FFFFFF~true~false~true']
pcb={'head':{'docType':'3','editorVersion':'6.5.51','newgId':True,'c_para':{'name':'Mosaico Dock A0 PLACEMENT ONLY'},'x':0,'y':0},
 'canvas':'CA~1200~800~#000000~yes~#FFFFFF~1~1200~800~line~1~mm~0.6~45~visible~0.5~0~0',
 'shape':pcbsh,'layers':layers,'objects':[],'BBox':{'x':0,'y':0,'width':154/.254,'height':64/.254},
 'DRCRULE':{'trackWidth':0.6,'track2Track':0.6,'pad2Pad':0.6,'track2Pad':0.6,'hole2Hole':1,'holeSize':1.2},'netColors':{}}
check_errors()
OUT.mkdir(parents=True, exist_ok=True)
for name,obj in [('mosaico-dock-schematic.json',sch),('mosaico-dock-placement.json',pcb),('design-netlist.json',components)]:
    write_text_lf(OUT/name, json.dumps(obj,ensure_ascii=False,indent=2))
with (OUT/'bom-review.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(['Designator','Value','LCSC','Footprint','Geometry status','Notes'])
    for c in components:
        status=c['footprint_status']+(ALLOW_MISSING_TAG if c['ref'] in UNRESOLVED_REFS else '')
        w.writerow([c['ref'],c['value'],c['code'],c['package'],status,c['note']])
with (OUT/'pin-net-review.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(['Reference','Pin','Pin name','Net','Notes'])
    for c in components:
        for n,v in c['pins'].items():w.writerow([c['ref'],n,v,c['nets'][n] or 'NC',c['note']])

_ph=placeholder_rows()
_unref=sorted(p.stem for p in REF.glob('*.json') if p.stem not in REFS_BY_CODE)
if ARGS.allow_missing and UNRESOLVED_REFS:
    sys.stderr.write('\n*** --allow-missing 已启用：%s 由放行而非解决得到，本次产物不得作为基线候选。***\n'
                     % ', '.join(sorted(UNRESOLVED_REFS)))
for note in NOTICES:
    sys.stderr.write('提示：%s\n' % note)
if _unref:
    sys.stderr.write('提示：references/ 下有 %d 份缓存未被任何位号引用：%s（保留与否属 Chrome）\n'
                     % (len(_unref), ', '.join(_unref)))
print(json.dumps({'components':len(components),'nets':len(set(n for c in components for n in c['nets'].values() if n)),
                  'native_schematic':str(OUT/'mosaico-dock-schematic.json'),'status':'DRAFT - NOT ROUTED - NOT FOR FABRICATION',
                  'out_dir':str(OUT),
                  'libraries_referenced':len([k for k in REFS_BY_CODE if k]),
                  'libraries_available':len([k for k in REFS_BY_CODE if k and resolve_code(k)['state']=='OK']),
                  'libraries_unavailable':sorted(k for k in REFS_BY_CODE if k and resolve_code(k)['state']!='OK'),
                  'placeholder_refdes':[r['refdes'] for r in _ph],
                  'allow_missing':bool(ARGS.allow_missing),
                  'allow_missing_released':sorted(UNRESOLVED_REFS),
                  'unreferenced_cache_files':_unref,
                  'lock':rel(LOCK_PATH),'policy':rel(POLICY_PATH)},ensure_ascii=False))
