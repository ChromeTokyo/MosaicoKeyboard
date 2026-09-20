"""Generate the editable electrical draft and placement study. NOT manufacturing data."""
from pathlib import Path
import json, re, uuid, math, csv, html, collections

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / 'references'
OUT = ROOT / 'design'
REV = 'A0-DRAFT'
components = []
libraries = {}

def uid(s): return 'gge' + uuid.uuid5(uuid.NAMESPACE_URL, 'mosaico-handheld/'+s).hex
def fmt(v): return ('%.5f' % float(v)).rstrip('0').rstrip('.')
def esc(v): return str(v).replace('~','-').replace('`', "'")

def library(code):
    if code not in libraries:
        p = REF / (code+'.json')
        if not p.exists(): return None
        d = json.loads(p.read_text(encoding='utf-8-sig'))
        if not d.get('success') or not d.get('result'): return None
        libraries[code] = d['result']
    return libraries[code]

def add(ref, code, value, nets, group, xy, kind='ic', note='', pins=None, package=None):
    d = library(code) if code else None
    if pins is None:
        if not d: raise ValueError('Missing verified library: '+code)
        pins = {}
        for s in d['dataStr']['shape']:
            if s.startswith('P~'):
                a = s.split('^^'); pins[a[0].split('~')[3]] = a[3].split('~')[4]
    assert set(nets) == set(pins), (ref, set(nets)^set(pins))
    c = dict(ref=ref,code=code,value=value,nets=nets,pins=pins,group=group,xy=xy,
             kind=kind,note=note,package=package or (d['dataStr']['head']['c_para']['package'] if d else 'TBD'))
    components.append(c)
    return c

def passive(ref,value,code,a,b,group,xy,kind='res',note=''):
    d=library(code) if code else None
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
    d=library(c['code']) if c['code'] else None
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
for group,title,gx,gy,gw,gh in groups:
    shapes += [f'R~{gx}~{gy}~~~{gw}~{gh}~#A0ADBB~1~0~none~{uid(group)}~0',text(gx+20,gy+35,title,18)]
    big=[c for c in components if c['group']==group and c['kind'] in ('ic','slide')]
    small=[c for c in components if c['group']==group and c not in big]
    for i,c in enumerate(big):
        cols=3;x=gx+260+(i%cols)*490;y=gy+270+(i//cols)*320
        shapes+=sym(c,x,y)
    start=gy+(610 if len(big)>3 else 530)
    for i,c in enumerate(small):
        x=gx+210+(i%5)*300;y=start+(i//5)*90
        shapes+=sym(c,x,y)
for i,c in enumerate(c for c in components if c['group']=='test'):
    shapes+=sym(c,230+(i%6)*520,2380+(i//6)*150)
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
    ref=c['ref'];x,y=[v/.254 for v in c['xy']];d=library(c['code']) if c['code'] else None;b=[]
    if d and d.get('packageDetail'):
        pd=d['packageDetail']['dataStr'];hx=float(pd['head']['x']);hy=float(pd['head']['y']);dx=x-hx;dy=y-hy
        for j,s in enumerate(pd['shape']):
            a=s.split('~');t=a[0]
            if t=='PAD':
                a[2]=fmt(float(a[2])+dx);a[3]=fmt(float(a[3])+dy)
                if a[10]:a[10]=points_move(a[10],dx,dy)
                if len(a)>14 and a[14]:a[14]=points_move(a[14],dx,dy)
                assert a[8] in c['nets'],(ref,'pad without pin',a[8])
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
    pp='`'.join(['package',c['package'],'Manufacturer Part',c['value'],'Supplier Part',c['code']])
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
OUT.mkdir(exist_ok=True)
for name,obj in [('mosaico-dock-schematic.json',sch),('mosaico-dock-placement.json',pcb),('design-netlist.json',components)]:
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'bom-review.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['Designator','Value','LCSC','Footprint','Geometry status','Notes'])
    for c in components:w.writerow([c['ref'],c['value'],c['code'],c['package'],c['footprint_status'],c['note']])
with (OUT/'pin-net-review.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['Reference','Pin','Pin name','Net','Notes'])
    for c in components:
        for n,v in c['pins'].items():w.writerow([c['ref'],n,v,c['nets'][n] or 'NC',c['note']])
print(json.dumps({'components':len(components),'nets':len(set(n for c in components for n in c['nets'].values() if n)),
                  'native_schematic':str(OUT/'mosaico-dock-schematic.json'),'status':'DRAFT - NOT ROUTED - NOT FOR FABRICATION'}))
