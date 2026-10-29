#!/usr/bin/env python3
"""Remove abandoned autorouter islands which connect no component pad.

Locked/manual copper and all pads/planes are retained. Native DRC afterwards.
"""
from pathlib import Path
import argparse,sys
import wx,pcbnew as k
from clear_route_conflicts import blocks
app=wx.App(False)
a=argparse.ArgumentParser();a.add_argument('pcb',type=Path);args=a.parse_args()
b=k.LoadBoard(str(args.pcb));b.BuildConnectivity();conn=b.GetConnectivity()
items={str(t.m_Uuid.AsString()):t for t in b.GetTracks()}
for f in b.GetFootprints():
 for p in f.Pads():items[str(p.m_Uuid.AsString())]=p
seen=set();remove=set()
for uid,t in list(items.items()):
 if uid in seen or isinstance(t,k.PAD):continue
 group=[items.get(str(raw.m_Uuid.AsString()))for raw in conn.GetConnectedItems(t)];group=[o for o in group if o is not None]
 ids={str(o.m_Uuid.AsString())for o in group};seen|=ids
 if group and not any(isinstance(o,k.PAD)or o.IsLocked()for o in group):remove|=ids
s=args.pcb.read_text()
for a,z,block in reversed(list(blocks(s))):
 if block.startswith(('(segment','(via'))and any(u in block for u in remove):s=s[:a]+s[z:]
args.pcb.write_text(s);print('Removed',len(remove),'floating auto-copper objects; no pads or locked routes removed.')
