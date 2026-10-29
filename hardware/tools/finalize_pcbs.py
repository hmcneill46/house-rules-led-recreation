#!/usr/bin/env python3
"""Import local routing sessions, synchronise native schematic metadata, fill GND.

Run with KiCad's bundled Python. --metadata-only preserves any manual route fixes.
Native KiCad DRC is the authority after this step, not an autorouter score.
"""
import argparse,json,uuid
from pathlib import Path
import wx,pcbnew as k
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'hardware/kicad'
app=wx.App(False)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',choices=['main','usb']);ap.add_argument('--metadata-only',action='store_true');ap.add_argument('--session',type=Path);a=ap.parse_args()
    if a.session and not a.board:ap.error('--session requires --board')
    spec=json.loads((OUT/'circuit-spec.json').read_text())
    for name in spec['boards']:
        if a.board and a.board!=name:continue
        stem='house-rules-'+name; path=OUT/(stem+'.kicad_pcb'); b=k.LoadBoard(str(path))
        if not a.metadata_only:
            ses=a.session or OUT/(stem+'.ses')
            if not ses.exists():raise FileNotFoundError(ses)
            if not k.ImportSpecctraSES(b,str(ses)):raise RuntimeError('Session import failed')
        byref={p['ref']:p for p in spec['parts'] if p['board']==name}
        for f in b.GetFootprints():
            p=byref[f.GetReference()];lib,fp=p['footprint'].split(':');f.SetFPID(k.LIB_ID(lib,fp));f.SetValue(p['value'])
            for key,value in [('MPN',p['mpn']),('LCSC',p.get('lcsc','')),('Datasheet',p.get('datasheet','')),('Description',p.get('role',''))]:
                f.SetField(key,value);f.GetField(key).SetVisible(False)
            rootid=uuid.uuid5(uuid.NAMESPACE_URL,'house-rules:'+name+':sheet')
            sid=uuid.uuid5(uuid.NAMESPACE_URL,'house-rules:'+name+':'+p['ref'])
            ip=k.KIID_PATH();ip.push_back(k.KIID(str(rootid)));ip.push_back(k.KIID(str(sid)));f.SetPath(ip)
        # Specctra import labels some full-stack vias blind/buried. The physical
        # design uses ordinary plated through vias exclusively, without HDI.
        for t in b.GetTracks():
            if isinstance(t,k.PCB_VIA):
                if t.TopLayer()!=k.F_Cu or t.BottomLayer()!=k.B_Cu:
                    raise ValueError('Unexpected non-through via span')
                t.SetViaType(k.VIATYPE_THROUGH)
                if name=='main':
                    # Six-layer manufacturing selection: resin fill + copper cap
                    # (IPC-4761 type VII). LED PTH pads are not vias and stay open.
                    t.SetFillingMode(k.FILLING_MODE_FILLED)
                    t.SetCappingMode(k.CAPPING_MODE_CAPPED)
        b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(path),b)
        print(name,'tracks/vias',len(b.GetTracks()),'footprints',len(b.GetFootprints()))

if __name__=='__main__':main()
