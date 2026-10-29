#!/usr/bin/env python3
"""Rip up unlocked autorouter segments colliding with newly reserved power vias.

Never removes pads, outlines, locked routes, or either hand-routed USB net.
Prints every removed segment UUID; KiCad DRC must be rerun after use.
"""
import argparse,json,re
from pathlib import Path

def blocks(source):
    depth=0;quoted=False;escaped=False;start=None
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
            if depth==1 and start is not None:
                yield start,i+1,source[start:i+1];start=None

def main():
    ap=argparse.ArgumentParser();ap.add_argument('pcb',type=Path);ap.add_argument('report',type=Path);a=ap.parse_args()
    source=a.pcb.read_text();index={}
    for start,end,block in blocks(source):
        u=re.search(r'\(uuid "?([a-f0-9-]+)"?\)',block)
        if u:index[u[1]]=(start,end,block)
    remove=set();unresolved=[]
    for violation in json.loads(a.report.read_text())['violations']:
        if violation['type'] not in ['shorting_items','tracks_crossing','clearance']:continue
        candidates=[]
        for item in violation['items']:
            entry=index.get(item.get('uuid'))
            if not entry:continue
            block=entry[2]
            if not block.startswith('(segment') or '(locked yes)' in block or 'USB_D' in item['description']:continue
            candidates.append(item['uuid'])
        if candidates:remove.add(candidates[0])
        else:unresolved.append(violation)
    for start,end,_ in sorted((index[u] for u in remove),reverse=True):source=source[:start]+source[end:]
    a.pcb.write_text(source)
    print('Removed',len(remove),'unlocked segments:',','.join(sorted(remove)))
    if unresolved:
        print('Unresolved protected conflicts:',json.dumps(unresolved))
        raise SystemExit(1)

if __name__=='__main__':main()
