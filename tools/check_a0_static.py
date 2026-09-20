#!/usr/bin/env python3
"""Read-only file correspondence checks. Not an EasyEDA import, ERC, DRC or electrical approval."""
import argparse, collections, csv, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path


def attrs(s):
    a=s.split('`'); return dict(zip(a[::2],a[1::2]))


def check(root, schematic_path=None):
    root=Path(root); d=root/'design'
    net=json.loads((d/'design-netlist.json').read_text()); sch=json.loads((d/'mosaico-dock-schematic.json').read_text()); pcb=json.loads((d/'mosaico-dock-placement.json').read_text())
    if schematic_path:
        sch=json.loads(Path(schematic_path).read_text())
        if 'schematics' in sch:
            if len(sch['schematics'])!=1:raise ValueError('This bounded checker expects exactly one schematic sheet')
            sch=sch['schematics'][0]['dataStr']
    byref={c['ref']:c for c in net}; errors=[]; normalizations=[]
    if len(byref)!=len(net):errors.append('duplicate component reference')
    schpins={}; pcbpads={}; wires=[]; labels=collections.defaultdict(list); ncs=collections.defaultdict(list)
    for s in sch['shape']:
        a=s.split('~')
        if a[0]=='LIB':
            ss=s.split('#@$'); h=ss[0].split('~'); ref=attrs(h[3])['pre']; pins={}
            for p in ss[1:]:
                if p.startswith('P~'):
                    z=p.split('^^'); pa=z[0].split('~'); dot=tuple(map(float,z[1].split('~')))
                    if pa[3] in pins:errors.append(f'duplicate schematic pin {ref}.{pa[3]}')
                    pins[pa[3]]={'dot':dot,'electrical_type':pa[2],'name':z[3].split('~')[4]}
            if ref in schpins:errors.append(f'duplicate schematic ref {ref}')
            schpins[ref]=pins
            observed=attrs(h[3])['package'];expected=byref[ref]['package']
            if observed!=expected:
                if observed.upper()==expected.upper():normalizations.append({'ref':ref,'attribute':'package','original':expected,'editor':observed,'kind':'case only'})
                else:errors.append(f'schematic package mismatch {ref}: {observed} != {expected}')
        elif a[0]=='W':
            ps=list(map(float,a[1].split())); wires.append([tuple(ps[i:i+2]) for i in range(0,len(ps),2)])
        elif a[0]=='N':labels[tuple(map(float,a[1:3]))].append(a[5])
        elif a[0]=='O':ncs[tuple(map(float,a[1:3]))].append(a[3])
    # Coordinate graph splits each segment at every pin dot, label and endpoint.
    # This reveals collinear overlaps that endpoint-only matching would miss.
    graph=collections.defaultdict(set)
    points=set(labels)|set(ncs)|{p['dot'] for pins in schpins.values() for p in pins.values()}|{p for w in wires for p in w}
    for w in wires:
        for a,b in zip(w,w[1:]):
            on=[p for p in points if abs((p[0]-a[0])*(b[1]-a[1])-(p[1]-a[1])*(b[0]-a[0]))<1e-8 and min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1])]
            on.sort()
            for p,q in zip(on,on[1:]):graph[p].add(q);graph[q].add(p)
    for ref,pins in schpins.items():
        c=byref[ref]
        if set(pins)!=set(c['pins']):errors.append(f'schematic pin-number set mismatch {ref}')
        for num,p in pins.items():
            seen={p['dot']};todo=[p['dot']]
            while todo:
                for q in graph[todo.pop()]:
                    if q not in seen:seen.add(q);todo.append(q)
            found=[n for q in seen for n in labels[q]]
            want=c['nets'][num]
            if want is None:
                if found or not ncs[p['dot']]:errors.append(f'NC mismatch {ref}.{num}: {found}')
            elif set(found)!={want}:errors.append(f'wire-label mismatch {ref}.{num}: {found} != {want}')
    # Identify footprints by their native prefix text; compare every copper pad number/net.
    pcb_shape_counts=collections.Counter(); copper_tracks=0
    pcb_ids=collections.defaultdict(list)
    invalid_layers=[];invalid_times=[];invalid_hole_centers=[];distant_hole_centers=[]
    id_positions={'LIB':6,'PAD':12,'TEXT':13,'TRACK':5,'CIRCLE':6,'HOLE':4}
    for s in pcb['shape']:
        for j,p in enumerate(s.split('#@$')):
            a=p.split('~');idx=id_positions.get(a[0])
            if idx is not None and len(a)>idx:pcb_ids[a[idx]].append({'type':a[0],'nested':j>0})
    for s in pcb['shape']:
        if s.startswith('LIB~'):
            ss=s.split('#@$'); h=ss[0].split('~'); prefix=[p.split('~')[10] for p in ss[1:] if p.startswith('TEXT~P~')]
            if len(prefix)!=1:errors.append(f'footprint prefix count {len(prefix)}');continue
            ref=prefix[0];pads=collections.defaultdict(list)
            if len(h)<=7 or h[7] not in ('1','2'):invalid_layers.append({'ref':ref,'value':h[7] if len(h)>7 else None})
            if len(h)>9 and h[9] and not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?',h[9]):invalid_times.append({'ref':ref,'value':h[9]})
            for p in ss[1:]:
                a=p.split('~');pcb_shape_counts[a[0]]+=1
                if a[0]=='PAD':
                    pads[a[8]].append(a[7] or None)
                    if len(a)>19 and a[19]:
                        hc=a[19].split(',')
                        if len(hc)!=2:invalid_hole_centers.append({'ref':ref,'pin':a[8],'value':a[19]})
                        else:
                            try:
                                delta=[float(hc[0])-float(a[2]),float(hc[1])-float(a[3])]
                                if max(abs(v) for v in delta)>100:distant_hole_centers.append({'ref':ref,'pin':a[8],'pad_xy':a[2:4],'hole_center':hc,'hole_size':a[9]})
                            except ValueError:invalid_hole_centers.append({'ref':ref,'pin':a[8],'value':a[19]})
                if a[0]=='TRACK' and a[2] in ('1','2'):copper_tracks+=1
            pcbpads[ref]=dict(pads)
            if attrs(h[3])['package']!=byref[ref]['package']:errors.append(f'PCB package mismatch {ref}')
            if set(pads)!=set(byref[ref]['nets']):errors.append(f'PCB pad-number set mismatch {ref}')
            for num,ns in pads.items():
                if any(n!=byref[ref]['nets'][num] for n in ns):errors.append(f'PCB pad net mismatch {ref}.{num}')
        elif s.startswith('TRACK~') and s.split('~')[2] in ('1','2'):copper_tracks+=1
    for k,v in [('schematic',schpins),('PCB',pcbpads)]:
        if set(v)!=set(byref):errors.append(k+' reference set mismatch')
    bom=list(csv.DictReader((d/'bom-review.csv').open(encoding='utf-8-sig')))
    pin_csv=list(csv.DictReader((d/'pin-net-review.csv').open(encoding='utf-8-sig')))
    expected_pins=[{'Reference':c['ref'],'Pin':p,'Pin name':name,'Net':c['nets'][p] or 'NC','Notes':c['note']} for c in net for p,name in c['pins'].items()]
    expected_bom=[dict(zip(['Designator','Value','LCSC','Footprint','Geometry status','Notes'],[c['ref'],c['value'],c['code'],c['package'],c['footprint_status'],c['note']])) for c in net]
    if pin_csv!=expected_pins:errors.append('pin CSV != design-netlist')
    if bom!=expected_bom:errors.append('BOM CSV != design-netlist')
    cache_package_differences=[];missing=[]
    for c in net:
        if not c['code']:continue
        p=root/'references'/(c['code']+'.json')
        if not p.exists():missing.append({'ref':c['ref'],'code':c['code']});continue
        lib=json.loads(p.read_text(encoding='utf-8-sig'))['result']
        pkg=lib['dataStr']['head']['c_para'].get('package')
        if c['package']!=pkg:cache_package_differences.append({'ref':c['ref'],'saved':c['package'],'cache':pkg})
    # Record potential wire overlaps, requiring geometry/editor review, independently of intended net IDs.
    overlaps=[]
    for i,w in enumerate(wires):
        if len(w)!=2:continue
        a,b=w
        for j,v in enumerate(wires[:i]):
            if len(v)!=2:continue
            c,e=v
            if a[1]==b[1]==c[1]==e[1] and max(min(a[0],b[0]),min(c[0],e[0]))<=min(max(a[0],b[0]),max(c[0],e[0])):
                overlaps.append({'wire_indices':[j,i],'segments':[v,w]})
    return {'root':str(root),'schematic_path':str(schematic_path or d/'mosaico-dock-schematic.json'),'scope':'static generated-file correspondence only; not EDA/ ERC/DRC/electrical validation','counts':{'components':len(net),'nets':len({n for c in net for n in c['nets'].values() if n}),'logical_pins':sum(len(c['pins']) for c in net),'schematic_pins':sum(map(len,schpins.values())),'schematic_wires':len(wires),'schematic_labels':sum(map(len,labels.values())),'schematic_nc_flags':sum(map(len,ncs.values())),'pcb_pads':sum(len(ns) for pads in pcbpads.values() for ns in pads.values()),'pcb_copper_tracks':copper_tracks,'bom_rows':len(bom),'pin_csv_rows':len(pin_csv)},'correspondence_errors':errors,'observed_normalizations':normalizations,'pin_electrical_type_counts':dict(collections.Counter(p['electrical_type'] for pins in schpins.values() for p in pins.values())),'missing_library_caches':missing,'library_package_differences':cache_package_differences,'wire_overlaps':overlaps,'pcb_nested_shape_counts':dict(pcb_shape_counts),'pcb_format_findings':{'basis':'Current official Standard Format; not proof of which field causes editor import failure','invalid_footprint_layer_count':len(invalid_layers),'invalid_footprint_layer_examples':invalid_layers[:3],'nonnumeric_footprint_utime_count':len(invalid_times),'nonnumeric_footprint_utime_examples':invalid_times[:3],'invalid_pad_hole_center_count':len(invalid_hole_centers),'invalid_pad_hole_center_examples':invalid_hole_centers[:3],'distant_pad_hole_center_count':len(distant_hole_centers),'distant_pad_hole_center_examples':distant_hole_centers[:3],'duplicate_object_ids':{k:v for k,v in pcb_ids.items() if len(v)>1},'drc_default_object_present':isinstance(pcb.get('DRCRULE',{}).get('Default'),dict)}}


OUTPUT_NAMES=['mosaico-dock-schematic.json','mosaico-dock-placement.json','design-netlist.json','bom-review.csv','pin-net-review.csv']


def hashes(root):
    return {n:hashlib.sha256((Path(root)/'design'/n).read_bytes()).hexdigest() for n in OUTPUT_NAMES}


def rebuild(root, destination):
    root=Path(root).resolve();destination=Path(destination).resolve()
    # Never write inside the source tree and never reuse an existing destination.
    if destination==root or root in destination.parents:raise ValueError('Rebuild destination must be outside source tree')
    destination.mkdir(parents=True,exist_ok=False)
    for n in ['design','references']:shutil.copytree(root/n,destination/n)
    p=subprocess.run([sys.executable,'design/build_design.py'],cwd=destination,capture_output=True,text=True)
    result={'destination':str(destination),'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    if p.returncode:return result
    before=hashes(root);after=hashes(destination)
    result['file_comparison']={}
    for n in OUTPUT_NAMES:
        old=root/'design'/n;new=destination/'design'/n
        if n.endswith('.csv'):
            a=list(csv.DictReader(old.open(encoding='utf-8-sig')));b=list(csv.DictReader(new.open(encoding='utf-8-sig')))
        else:a=json.loads(old.read_text());b=json.loads(new.read_text())
        result['file_comparison'][n]={'original_sha256':before[n],'rebuilt_sha256':after[n],'byte_equal':before[n]==after[n],'semantic_equal':a==b}
    a={c['ref']:c for c in json.loads((root/'design/design-netlist.json').read_text())};b={c['ref']:c for c in json.loads((destination/'design/design-netlist.json').read_text())}
    result['component_changes']={r:{k:{'original':a[r].get(k),'rebuilt':b[r].get(k)} for k in sorted(a[r].keys()|b[r].keys()) if a[r].get(k)!=b[r].get(k)} for r in sorted(a.keys()&b.keys()) if a[r]!=b[r]}
    q=subprocess.run([sys.executable,'design/build_design.py'],cwd=destination,capture_output=True,text=True)
    result['repeat_build']={'returncode':q.returncode,'byte_identical_to_first_build':after==hashes(destination)}
    result['static_check']=check(destination)
    return result


def check_native_altium(root, path):
    text=Path(path).read_text(encoding='utf-8-sig')
    nets={};component_refs=[]
    for m in re.finditer(r'^\(\n(.*?)^\)',text,re.M|re.S):
        block=m.group(1).splitlines()
        nets[block[0].strip()]=[p.strip() for p in block[1:] if p.strip()]
    for m in re.finditer(r'^\[\n(.*?)^\]',text,re.M|re.S):component_refs.append(m.group(1).splitlines()[0].strip())
    components=json.loads((Path(root)/'design/design-netlist.json').read_text())
    expected={c['ref']+'-'+pin:net for c in components for pin,net in c['nets'].items()}
    actual=collections.defaultdict(list)
    for net,pins in nets.items():
        for pin in pins:actual[pin].append(net)
    mismatches={p:{'design':n,'eda':actual.get(p,[])} for p,n in expected.items() if ([n] if n is not None else [])!=actual.get(p,[])}
    return {'path':str(path),'format':'Altium/Protel netlist exported by actual editor','counts':{'expected_components':len(components),'eda_components':len(component_refs),'expected_named_nets':len(set(n for n in expected.values() if n)),'eda_named_nets':len(nets),'expected_pins_total':len(expected),'expected_connected_pins':sum(n is not None for n in expected.values()),'eda_connected_pins':len(actual),'expected_nc_pins':sum(n is None for n in expected.values()),'mismatched_pins':len(mismatches)},'mismatches':mismatches,'unexpected_pins':sorted(set(actual)-set(expected)),'component_reference_set_matches':set(component_refs)=={c['ref'] for c in components},'duplicate_pin_memberships':{p:n for p,n in actual.items() if len(n)>1},'missing_expected_nets':sorted(set(n for n in expected.values() if n)-set(nets)),'BOOST_SW_members':nets.get('BOOST_SW',[]),'POGO_5V_members':nets.get('POGO_5V',[])}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root');p.add_argument('--output');p.add_argument('--rebuild-dir');p.add_argument('--imported-schematic');p.add_argument('--native-altium-netlist');args=p.parse_args()
    results={'original':check(args.root)}
    if args.rebuild_dir:results['rebuild']=rebuild(args.root,args.rebuild_dir)
    if args.imported_schematic:results['actual_editor_import']=check(args.root,args.imported_schematic)
    if args.native_altium_netlist:results['native_netlist_comparison']=check_native_altium(args.root,args.native_altium_netlist)
    data=json.dumps(results,indent=2,ensure_ascii=False)
    if args.output:Path(args.output).write_text(data+'\n')
    print(data)

if __name__=='__main__':main()
