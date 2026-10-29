#!/usr/bin/env python3
"""Separate 6-layer cost/routing candidate; never writes A1 or the 4-layer input."""
from pathlib import Path
import shutil,re
import wx,pcbnew as k
app=wx.App(False);B2=Path(__file__).resolve().parents[1];D=B2/'kicad'
b=k.LoadBoard(str(D/'house-rules-main-B2.kicad_pcb'))
assert b.GetCopperLayerCount()==4, 'Historical 4L-to-6L experiment only; do not apply to the final six-layer board'
b.SetCopperLayerCount(6)
for z in b.Zones():z.SetLayer(k.In4_Cu)
for f in b.GetFootprints():
 if f.GetReference()not in ('U1','U2','U3','U4'):continue
 ep=next(p for p in f.Pads()if p.GetNumber()=='25');c=ep.GetPosition()
 for x,y in ((-.55,0),(.55,0),(0,.55)):
  v=k.PCB_VIA(b);v.SetPosition(k.VECTOR2I(c.x+k.FromMM(x),c.y+k.FromMM(y)));v.SetWidth(k.FromMM(.6));v.SetDrill(k.FromMM(.3));v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(ep.GetNet());v.SetLocked(True);b.Add(v)
for v in b.GetTracks():
 if isinstance(v,k.PCB_VIA):v.SetFillingMode(k.FILLING_MODE_FILLED);v.SetCappingMode(k.CAPPING_MODE_CAPPED)
b.BuildConnectivity();name='house-rules-main-B2-6L';file=D/(name+'.kicad_pcb');k.SaveBoard(str(file),b)
shutil.copy2(D/'house-rules-main-B2.kicad_pro',D/(name+'.kicad_pro'));shutil.copy2(D/'house-rules-main-B2.kicad_dru',D/(name+'.kicad_dru'))
dsn=D/(name+'.dsn');assert k.ExportSpecctraDSN(b,str(dsn));s=dsn.read_text()
s=re.sub(r'\(clearance [0-9.]+ \(type smd_smd\)\)','(clearance 150 (type smd_smd))',s)
s=s.replace('(layer In4.Cu\n      (type signal)','(layer In4.Cu\n      (type power)')
start=s.index('    (class kicad_default ');end=s.index('      (circuit',start);head=s[start:end]
for n in ('VBUS','FUSED_VBUS','+5V','VLED_5V'):head=re.sub(r'(?<![^\s])'+re.escape(n)+r'(?=\s)', '', head)
s=s[:start]+head+s[end:];point=s.index('\n  (wiring');close=s.rfind('\n  )',0,point)
s=s[:close]+'\n    (class Power VBUS FUSED_VBUS +5V VLED_5V (circuit (use_via "Via[0-5]_600:300_um")) (rule (width 350) (clearance 150)))'+s[close:];dsn.write_text(s)
print(file)
