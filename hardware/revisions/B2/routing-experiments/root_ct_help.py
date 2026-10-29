"""Root's separate no-rip CT bridge study; active sibling routing is untouched."""
from pathlib import Path
import json, itertools, shutil
import wx, pcbnew as k
wx.Log.EnableLogging(False); app=wx.App(False)
P=Path(__file__).parent
source=P/'ct-help6.kicad_pcb'; b=k.LoadBoard(str(source))
net=b.FindNet('CT_5V'); objects=[p for f in b.GetFootprints()for p in f.Pads()]+list(b.GetTracks())
def point(p):return k.VECTOR2I(k.FromMM(p[0]),k.FromMM(p[1]))
def check(path,layer):
    collision=[]
    for a,z in zip(path,path[1:]):
        sh=k.SHAPE_SEGMENT(point(a),point(z),110000)
        for o in objects:
            if o.GetNetCode()==net.GetNetCode()or not o.IsOnLayer(layer):continue
            if o.GetEffectiveShape(layer).Collide(sh,149999):
                collision.append({'id':o.m_Uuid.AsString(),'net':o.GetNetname(),'class':o.GetClass()})
    return collision
start=(111.9,58.5); end=(120.7375,57.05)
found=None; attempts=0; best=None
for layer in (k.F_Cu,k.In1_Cu,k.In3_Cu,k.B_Cu):
 for y,x1,x2 in itertools.product((58.65,56.11,61.19,53.57,63.73),(112.0,113.0,114.2),(117.2,118.0,119.0,120.0)):
    path=[start,(x1,start[1]),(x1,y),(x2,y),(x2,end[1]),end]
    bad=check(path,layer);attempts+=1
    if best is None or len(bad)<best['collisions']:
        best={'layer':b.GetLayerName(layer),'path':path,'collisions':len(bad),'objects':bad}
    if not bad:found={'layer':b.GetLayerName(layer),'path':path};break
 if found:break
report={'source':source.name,'attempts':attempts,'found':found,'best':best}
if found:
    layer=b.GetLayerID(found['layer'])
    for a,z in zip(found['path'],found['path'][1:]):
        if a==z:continue
        t=k.PCB_TRACK(b);t.SetStart(point(a));t.SetEnd(point(z));t.SetLayer(layer);t.SetWidth(110000);t.SetNet(net);t.SetLocked(True);b.Add(t)
    out=P/'root-ct-bridge6.kicad_pcb';b.BuildConnectivity();k.SaveBoard(str(out),b)
    for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(source.with_suffix(ext),out.with_suffix(ext))
(P/'root-ct-bridge.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
