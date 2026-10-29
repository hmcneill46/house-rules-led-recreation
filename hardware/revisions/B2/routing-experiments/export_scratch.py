import json,re,shutil,sys
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;p=P/(sys.argv[1] if len(sys.argv)>1 else 'escaped4.kicad_pcb');b=k.LoadBoard(str(p))
for t in b.GetTracks():
 if not isinstance(t,k.PCB_VIA)and t.GetWidth()<110000:t.SetWidth(110000)
b.GetDesignSettings().m_TrackMinWidth=110000
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(p),b)
project=json.loads(p.with_suffix('.kicad_pro').read_text());project['board']['design_settings']['rules']['min_track_width']=.11;p.with_suffix('.kicad_pro').write_text(json.dumps(project,indent=2))
dsn=p.with_suffix('.dsn');assert k.ExportSpecctraDSN(b,str(dsn));s=dsn.read_text()
s=re.sub(r'\(clearance [0-9.]+ \(type smd_smd\)\)','(clearance 150 (type smd_smd))',s)
s=s.replace('(layer In2.Cu\n      (type signal)','(layer In2.Cu\n      (type power)')
start=s.index('    (class kicad_default ');end=s.index('      (circuit',start);head=s[start:end]
for n in ('VBUS','FUSED_VBUS','+5V','VLED_5V'):head=re.sub(r'(?<![^\s])'+re.escape(n)+r'(?=\s)', '', head)
s=s[:start]+head+s[end:];point=s.index('\n  (wiring');close=s.rfind('\n  )',0,point)
s=s[:close]+'\n    (class Power VBUS FUSED_VBUS +5V VLED_5V (circuit (use_via "Via[0-3]_600:300_um")) (rule (width 350) (clearance 150)))'+s[close:];dsn.write_text(s)
print(dsn)
