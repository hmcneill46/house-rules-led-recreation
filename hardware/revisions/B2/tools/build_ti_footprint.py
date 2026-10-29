#!/usr/bin/env python3
"""TI RGE0024C land pattern from TLC59282 datasheet pp.22-24.

No via-in-pad. Exposed copper is 2.10 mm square, stencil four .94 mm
windows at (+/-.57,+/-.57), giving 80.1% paste coverage.
"""
from pathlib import Path
import wx, pcbnew as k
B2=Path(__file__).resolve().parents[1];app=wx.App(False)
def v(x,y):return k.VECTOR2I(k.FromMM(x),k.FromMM(y))
def layers(*args):
 z=k.LSET()
 for layer in args:z.AddLayer(layer)
 return z
f=k.FOOTPRINT(None);f.SetFPID(k.LIB_ID('TI','RGE0024C'));f.SetAttributes(k.FP_SMD)
f.SetLibDescription('TI TLC59282RGER RGE0024C: 4x4, 0.5 pitch, 2.1 EP; TI 4224376/C land/stencil, no thermal holes')
f.SetKeywords('TLC59282RGER RGE0024C B2 no-via-in-pad')
for i in range(24):
 n=i+1
 if n<=6:x,y,sx,sy=-1.9,-1.25+.5*i,.6,.24
 elif n<=12:x,y,sx,sy=-1.25+.5*(n-7),1.9,.24,.6
 elif n<=18:x,y,sx,sy=1.9,1.25-.5*(n-13),.6,.24
 else:x,y,sx,sy=1.25-.5*(n-19),-1.9,.24,.6
 p=k.PAD(f);p.SetNumber(str(n));p.SetAttribute(k.PAD_ATTRIB_SMD);p.SetShape(k.PAD_SHAPE_ROUNDRECT)
 p.SetSize(v(sx,sy));p.SetPosition(v(x,y));p.SetRoundRectRadiusRatio(.05/min(sx,sy));p.SetLayerSet(layers(k.F_Cu,k.F_Mask,k.F_Paste));p.SetLocalSolderMaskMargin(k.FromMM(.07));f.Add(p)
p=k.PAD(f);p.SetNumber('25');p.SetAttribute(k.PAD_ATTRIB_SMD);p.SetShape(k.PAD_SHAPE_RECT);p.SetSize(v(2.1,2.1));p.SetPosition(v(0,0));p.SetLayerSet(layers(k.F_Cu,k.F_Mask));p.SetLocalSolderMaskMargin(k.FromMM(.07));f.Add(p)
for x in (-.57,.57):
 for y in (-.57,.57):
  p=k.PAD(f);p.SetAttribute(k.PAD_ATTRIB_SMD);p.SetShape(k.PAD_SHAPE_RECT);p.SetSize(v(.94,.94));p.SetPosition(v(x,y));p.SetLayerSet(layers(k.F_Paste));f.Add(p)
for layer,size,width in [(k.F_Fab,4,.1),(k.F_CrtYd,4.9,.05)]:
 s=k.PCB_SHAPE(f);s.SetShape(k.SHAPE_T_RECT);s.SetStart(v(-size/2,-size/2));s.SetEnd(v(size/2,size/2));s.SetLayer(layer);s.SetWidth(k.FromMM(width));f.Add(s)
s=k.PCB_SHAPE(f);s.SetShape(k.SHAPE_T_CIRCLE);s.SetStart(v(-1.6,-1.6));s.SetEnd(v(-1.45,-1.6));s.SetLayer(k.F_Fab);s.SetWidth(k.FromMM(.1));f.Add(s)
f.Reference().SetText('REF**');f.Reference().SetPosition(v(0,-3));f.Reference().SetLayer(k.F_SilkS)
f.Value().SetText('TLC59282RGER');f.Value().SetPosition(v(0,3));f.Value().SetLayer(k.F_Fab)
model=k.FP_3DMODEL();model.m_Filename='${KICAD10_3DMODEL_DIR}/Package_DFN_QFN.3dshapes/Texas_RGE0024C_VQFN-24-1EP_4x4mm_P0.5mm_EP2.1x2.1mm.step';f.Models().push_back(model)
out=B2/'kicad/footprints/TI.pretty';out.mkdir(parents=True,exist_ok=True)
k.PCB_IO_MGR.FindPlugin(k.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(out),f)
print(out/'RGE0024C.kicad_mod')
