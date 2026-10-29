#!/usr/bin/env python3
import argparse,re
from pathlib import Path
import wx,pcbnew as k
ap=argparse.ArgumentParser();ap.add_argument('pcb',type=Path);ap.add_argument('dsn',type=Path);ap.add_argument('--signal-width',type=float);a=ap.parse_args()
app=wx.App(False);b=k.LoadBoard(str(a.pcb));k.ExportSpecctraDSN(b,str(a.dsn))
s=re.sub(r'\(clearance [0-9.]+ \(type smd_smd\)\)','(clearance 150 (type smd_smd))',a.dsn.read_text())
if a.signal_width:
    # Width rules only; preserve every existing locked wire's actual width and
    # the separate 350 um power class. Native DRC remains the authority.
    s=s.replace('(width 150)',f'(width {a.signal_width*1000:g})')
if b.GetCopperLayerCount()==6:
    for layer in ['In1.Cu','In4.Cu']:s=s.replace(f'(layer {layer}\n      (type signal)',f'(layer {layer}\n      (type power)')
a.dsn.write_text(s)
print('Exported',a.dsn)
