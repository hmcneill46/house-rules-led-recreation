#!/usr/bin/env python3
"""Authorised AD28 escape and BOOT/SWCLK current-limiting resistor update."""
import hashlib,json,shutil,uuid
from pathlib import Path
import apply_checked_fanout_batch as base
k=base.k;ROOT=base.ROOT;CAD=base.CAD;P=base.P;REPORTS=base.REPORTS;LAYERS=base.LAYERS

def shape_conflicts(board, net, via, start):
    footprints={f.GetReference():f for f in board.GetFootprints()}
    footprints['U3'].BuildCourtyardCaches()
    yard=footprints['U3'].GetCourtyard(k.B_CrtYd)
    vs=k.SHAPE_SEGMENT(via,via,400000);stub=k.SHAPE_SEGMENT(start,via,100000)
    found={}
    for obj in [p for f in board.GetFootprints() for p in f.Pads()]+list(board.GetTracks()):
        if obj.GetNetname()==net:continue
        for layer in LAYERS:
            if not obj.IsOnLayer(layer):continue
            shape=obj.GetEffectiveShape(layer)
            local=isinstance(obj,k.PAD) and yard.Collide(vs) and yard.Collide(shape)
            clearance=99999 if local else 149999
            if shape.Collide(vs,clearance) or (layer==k.B_Cu and shape.Collide(stub,149999)):
                found[base.ident(obj)]=obj
                break
    return found

def add_track(board, net, a, c, width=.15):
    t=k.PCB_TRACK(board);t.SetStart(base.v(a));t.SetEnd(base.v(c));t.SetWidth(k.FromMM(width));t.SetLayer(k.B_Cu);t.SetNet(net);t.SetLocked(True);board.Add(t)
    return t

def add_via(board, net, xy):
    via=k.PCB_VIA(board);via.SetPosition(base.v(xy));via.SetWidth(400000);via.SetDrill(200000);via.SetViaType(k.VIATYPE_THROUGH);via.SetLayerPair(k.F_Cu,k.B_Cu);via.SetNet(net);via.SetLocked(True);board.Add(via)
    return via

def main():
    backup=CAD/'backups/final-protection-before';backup.mkdir(parents=True,exist_ok=False)
    for ext in ['kicad_pcb','kicad_pro','kicad_dru','kicad_sch']:shutil.copy2(CAD/f'house-rules-main.{ext}',backup/f'house-rules-main.{ext}')
    for p in [CAD/'circuit-spec.json',ROOT/'hardware/tools/circuit_spec.py']:shutil.copy2(p,backup/p.name)
    preserved={p:p.read_bytes() for p in [CAD/'house-rules-main.kicad_pro',CAD/'house-rules-main.kicad_dru']}
    board=k.LoadBoard(str(P));fp={f.GetReference():f for f in board.GetFootprints()};board.BuildConnectivity();conn=board.GetConnectivity()
    mcu=next(p for p in fp['U5'].Pads() if p.GetNumber()=='25');tp=next(iter(fp['TP4'].Pads()))
    assert base.ident(tp) in {base.ident(o) for o in conn.GetConnectedItems(mcu)},'Pre-existing MCU/SWCLK testpad connection missing'
    ad_start=base.v((106.7,56.7));ad_via=base.v((106.7,56.95));remove=shape_conflicts(board,'SDA',ad_via,ad_start)
    bad=[o for o in remove.values() if isinstance(o,k.PAD) or o.IsLocked()]
    if bad:raise RuntimeError('AD28 protected collision: '+str([(base.ident(o),o.GetNetname()) for o in bad]))
    # The two physical pad1s share a copper bridge. Preserve that bridge on the
    # new button-side net and cut only its outgoing clock branch.
    bridge='1643baf6-2728-4b3b-9673-bf65ba53730c';branch='bd2188f5-2b80-4e0a-9560-3431b5097c39'
    byid={base.ident(o):o for o in board.GetTracks()}
    assert bridge in byid and branch in byid
    assert byid[branch].GetNetname()=='BOOT_SWCLK' and not byid[branch].IsLocked()
    remove[branch]=byid[branch]
    actions={'AD28_removed':[{ 'uuid':base.ident(o),'net':o.GetNetname()} for key,o in remove.items() if key!=branch], 'BOOT_branch_removed':branch,'BOOT_bridge_renetted':bridge}
    P.write_text(base.filter_objects(P.read_text(),set(remove)))
    board=k.LoadBoard(str(P));fp={f.GetReference():f for f in board.GetFootprints()}
    btn=k.NETINFO_ITEM(board,'BOOT_BUTTON');board.Add(btn)
    for pad in fp['SW1'].Pads():
        if pad.GetNumber()=='1':pad.SetNet(btn)
    for track in board.GetTracks():
        if base.ident(track)==bridge:track.SetNet(btn)
    add_track(board,board.FindNet('SDA'),(106.7,56.7),(106.7,56.95),.1);add_via(board,board.FindNet('SDA'),(106.7,56.95))
    resistor=k.FootprintLoad(str(CAD/'footprints/Resistor_SMD.pretty'),'R_0603_1608Metric');board.Add(resistor)
    resistor.SetFPID(k.LIB_ID('Resistor_SMD','R_0603_1608Metric'));resistor.SetReference('R14');resistor.SetValue('2k2 1%');resistor.SetOrientationDegrees(0);resistor.Flip(k.VECTOR2I(0,0),k.FLIP_DIRECTION_LEFT_RIGHT);resistor.SetPosition(base.v((64.3,50.9)))
    resistor.Reference().SetVisible(False);resistor.Value().SetVisible(False)
    fields={'MPN':'0603WAF2201T5E','LCSC':'C4190','Datasheet':'','Description':'BOOT button current limiting; SWD clock stays directly connected to MCU'}
    for name,value in fields.items():resistor.SetField(name,value);resistor.GetField(name).SetVisible(False)
    for model in resistor.Models():model.m_Filename='${KIPRJMOD}/3d/Resistor_SMD__R_0603_1608Metric.step'
    path=k.KIID_PATH();path.push_back(k.KIID(str(uuid.uuid5(uuid.NAMESPACE_URL,'house-rules:main:sheet'))));path.push_back(k.KIID(str(uuid.uuid5(uuid.NAMESPACE_URL,'house-rules:main:R14'))));resistor.SetPath(path)
    pads={p.GetNumber():p for p in resistor.Pads()};pads['1'].SetNet(btn);pads['2'].SetNet(board.FindNet('BOOT_SWCLK'))
    # Short, explicit local wiring. The old PA14/TP4 island is left as a single
    # new connection for the parent routing pass. The large 0603 pad gives a
    # routing endpoint; do not prescribe a via without a fresh all-layer check.
    add_track(board,btn,(65.125,50.9),(67.0,51.38),.15)
    board.BuildConnectivity();conn=board.GetConnectivity();fp={f.GetReference():f for f in board.GetFootprints()}
    mcu=next(p for p in fp['U5'].Pads() if p.GetNumber()=='25');tp=next(iter(fp['TP4'].Pads()))
    assert base.ident(tp) in {base.ident(o) for o in conn.GetConnectedItems(mcu)},'MCU/TP4 clock connection changed'
    for pad in fp['SW1'].Pads():
        if pad.GetNumber()=='2':assert pad.GetNetname()=='+3V3'
    k.ZONE_FILLER(board).Fill(board.Zones());k.SaveBoard(str(P),board)
    for path,raw in preserved.items():path.write_bytes(raw)
    actions['MCU25_TP4_preserved']=True;actions['main_parts']=len(board.GetFootprints());actions['board_sha256']=hashlib.sha256(P.read_bytes()).hexdigest()
    (REPORTS/'final-protection-actions.json').write_text(json.dumps(actions,indent=2)+'\n')
    print('AD28 via/stub and R14 applied; native MCU25/TP4 connectivity retained; project rules unchanged.',flush=True)
if __name__=='__main__':main()
