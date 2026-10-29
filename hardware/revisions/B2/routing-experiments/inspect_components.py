import json,sys
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;stem=sys.argv[1]if len(sys.argv)>1 else'fine4';b=k.LoadBoard(str(P/(stem+'.kicad_pcb')));b.BuildConnectivity();objects={str(o.m_Uuid.AsString()):o for o in [p for f in b.GetFootprints()for p in f.Pads()]+list(b.GetTracks())}
d=json.loads((P/(stem+'-drc.json')).read_text())
for u in d['unconnected_items']:
 desc=[]
 for entry in u['items']:
  o=objects[entry['uuid']];comp=b.GetConnectivity().GetConnectedItems(o);pads=[x.GetParentFootprint().GetReference()+'.'+x.GetNumber()for x in comp if isinstance(x,k.PAD)];vias=sum(isinstance(x,k.PCB_VIA)for x in comp)
  desc.append({'item':entry['description'],'pads':pads,'vias':vias,'objects':len(comp)})
 print(json.dumps(desc))
