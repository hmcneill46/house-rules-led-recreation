import json,collections
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;b=k.LoadBoard(str(P/'final-routed6.kicad_pcb'));paths=json.loads((P/'clock-bus-actions.json').read_text())['paths'];out=[]
for layer in(k.F_Cu,k.In1_Cu,k.In3_Cu):
 collisions={};protected=[]
 for path in paths:
  for p,q in zip(path['polyline'],path['polyline'][1:]):
   shape=k.SHAPE_SEGMENT(k.VECTOR2I(k.FromMM(p[0]),k.FromMM(p[1])),k.VECTOR2I(k.FromMM(q[0]),k.FromMM(q[1])),150000)
   for o in[pp for f in b.GetFootprints()for pp in f.Pads()]+list(b.GetTracks()):
    if o.GetNetname()in('SCLK','CT_5V')or not o.IsOnLayer(layer):continue
    if o.GetEffectiveShape(layer).Collide(shape,149999):
     collisions[str(o.m_Uuid.AsString())]=o
     if isinstance(o,k.PAD)or o.IsLocked()or o.GetNetname().startswith('USB_'):protected.append((o.GetClass(),o.GetNetname()))
 out.append({'layer':b.GetLayerName(layer),'objects':len(collisions),'nets':dict(collections.Counter(o.GetNetname()for o in collisions.values())),'protected':protected})
print(json.dumps(out,indent=2));(P/'clock-layer-comparison.json').write_text(json.dumps(out,indent=2))
