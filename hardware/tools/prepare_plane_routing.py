#!/usr/bin/env python3
"""Reserve the two internal layers for solid ground and 5 V distribution.

Keeps the completed outer-layer signal routes from the first routing pass and
adds explicit short power escapes. This avoids long narrow supply traces.
"""
from pathlib import Path
import re
import wx,pcbnew as k
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'hardware/kicad';app=wx.App(False)
mm=k.FromMM
def pt(x,y):return k.VECTOR2I(mm(x+50),mm(y+50))

def strip_inner_copper(path):
    # KiCad 10's legacy SWIG Remove() corrupts wrapper ownership in this build.
    # Filter complete top-level S-expressions, then load a fresh native board.
    source=path.read_text(); depth=0; quoted=False;escaped=False;start=None;blocks=[]
    for i,c in enumerate(source):
        if quoted:
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c=='"':quoted=False
            continue
        if c=='"':quoted=True;continue
        if c=='(':
            if depth==1:start=i
            depth+=1
        elif c==')':
            depth-=1
            if depth==1 and start is not None:blocks.append((start,i+1));start=None
    changes=[]
    for a,z in blocks:
        block=source[a:z];token=block.split(None,1)[0][1:]
        if token=='zone':
            changes.append((a,z,''))
        elif token=='segment':
            m=re.search(r'\(width ([0-9.]+)\)',block)
            if m and float(m[1])<.1:changes.append((a,z,block[:m.start()]+ '(width 0.1)' +block[m.end():]))
    for a,z,new in reversed(changes):source=source[:a]+new+source[z:]
    path.write_text(source)

def main():
    p=D/'house-rules-main.kicad_pcb';strip_inner_copper(p);b=k.LoadBoard(str(p))
    b.SetCopperLayerCount(6)
    # Preserve the first pass's signal routing while adding two dedicated planes.
    for t in b.GetTracks():
        if not isinstance(t,k.PCB_VIA):
            if t.GetLayer()==k.In1_Cu:t.SetLayer(k.In2_Cu)
            elif t.GetLayer()==k.In2_Cu:t.SetLayer(k.In3_Cu)
    parts={f.GetReference():f for f in b.GetFootprints()}
    nets={name:b.FindNet(name) for name in ['GND','+5V']}
    def seg(net,a,c,width=.15):
        t=k.PCB_TRACK(b);t.SetStart(pt(*a));t.SetEnd(pt(*c));t.SetLayer(k.B_Cu);t.SetWidth(mm(width));t.SetNet(nets[net]);t.SetLocked(True);b.Add(t)
    def via(net,x,y):
        v=k.PCB_VIA(b);v.SetPosition(pt(x,y));v.SetWidth(mm(.4));v.SetDrill(mm(.2));v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(nets[net]);v.SetLocked(True);b.Add(v)
    # Thermal vias sit in the gaps between stencil windows on the exposed pads.
    for ref in ['U1','U2','U3','U4']:
        f=parts[ref];x=f.GetX()/1e6-50;y=f.GetY()/1e6-50
        for dy in [-.75,.75]:via('GND',x,y+dy)
        vcc=next(p for p in f.Pads() if p.GetNumber()=='23');a=(vcc.GetX()/1e6-50,vcc.GetY()/1e6-50)
        c=(a[0]-.75,a[1]);seg('+5V',a,c);via('+5V',*c)
    for dx in [-.575,.575]:
        for dy in [-.575,.575]:via('GND',44.2+dx,8.65+dy)
    for ref in [f'C{i}' for i in range(1,10)]:
        f=parts[ref];pad=next(p for p in f.Pads() if p.GetNumber()=='1')
        a=(pad.GetX()/1e6-50,pad.GetY()/1e6-50);c=(a[0],a[1]-.9)
        seg('+5V',a,c);via('+5V',*c)
    for ref,pin,delta in [('U6','1',(.85,0)),('U6','3',(.85,0)),('C13','1',(.85,0)),('TP6','1',(0,-.95)),('F1','2',(.85,0))]:
        pad=next(p for p in parts[ref].Pads() if p.GetNumber()==pin)
        a=(pad.GetX()/1e6-50,pad.GetY()/1e6-50);c=(a[0]+delta[0],a[1]+delta[1]);seg('+5V',a,c,.2 if ref=='F1' else .15);via('+5V',*c)
    for layer,net in [(k.In1_Cu,'GND'),(k.In4_Cu,'+5V')]:
        z=k.ZONE(b);z.SetLayer(layer);z.SetNet(nets[net]);z.SetLocalClearance(mm(.15));z.SetThermalReliefGap(mm(.2));z.SetThermalReliefSpokeWidth(mm(.25));poly=z.Outline();poly.NewOutline()
        for x,y in [(.3,.3),(88.1,.3),(88.1,17.0),(.3,17.0)]:poly.Append(mm(x+50),mm(y+50))
        b.Add(z)
    b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(p),b)
    dst=D/'house-rules-main-planes.dsn';k.ExportSpecctraDSN(b,str(dst))
    s=dst.read_text().replace('(clearance 50 (type smd_smd))','(clearance 150 (type smd_smd))')
    for l in ['In1.Cu','In4.Cu']:s=s.replace(f'(layer {l}\n      (type signal)',f'(layer {l}\n      (type power)')
    dst.write_text(s)
    print('Prepared solid internal planes, thermal vias and short 5V escapes.')

if __name__=='__main__':main()
