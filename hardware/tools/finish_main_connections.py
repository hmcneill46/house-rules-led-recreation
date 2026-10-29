#!/usr/bin/env python3
"""Conservative native-shape grid routing for remaining short connections.

Adds 0.10 mm signal traces and 0.4/0.2 through vias only, preserving existing
copper. Uses KiCad's effective shapes for collision checks at 0.152 mm spacing.
Native DRC after each batch remains authoritative. Run with bundled KiCad Python.
"""
import argparse,heapq,json,math,time
from collections import defaultdict
from pathlib import Path
import wx,pcbnew as k
app=wx.App(False)
STEP=50000; CELL=1000000; CLEAR=152000; WIDTH=100000
LAYERS=[k.F_Cu,k.In2_Cu,k.In3_Cu,k.B_Cu]
def vec(x,y):return k.VECTOR2I(int(x),int(y))
def gpos(q):return vec(q[0]*STEP,q[1]*STEP)
def node(p,l):return(round(p.x/STEP),round(p.y/STEP),l)
def cells(x0,y0,x1,y1):
 for x in range(x0//CELL,x1//CELL+1):
  for y in range(y0//CELL,y1//CELL+1):yield x,y
class Router:
 def __init__(self,b):
  self.b=b;self.index=defaultdict(list);self.byid={};self.n=0;self.holes=[];self.vias=[];self.width=WIDTH
  for f in b.GetFootprints():
   for p in f.Pads():
    self.byid[str(p.m_Uuid.AsString())]=p
    drill=p.GetDrillSize()
    if drill.x:self.holes.append((p.GetPosition(),max(drill.x,drill.y)))
    for l in LAYERS:
     if p.IsOnLayer(l):self.addshape(p.GetEffectiveShape(l),p.GetNetCode(),l)
  for t in b.GetTracks():self.additem(t)
 def addshape(self,s,net,l):
  bb=s.BBox();rec=(self.n,net,s);self.n+=1
  for x,y in cells(bb.GetX()-400000,bb.GetY()-400000,bb.GetRight()+400000,bb.GetBottom()+400000):self.index[l,x,y].append(rec)
 def additem(self,t):
  self.byid[str(t.m_Uuid.AsString())]=t
  if isinstance(t,k.PCB_VIA):self.holes.append((t.GetPosition(),t.GetDrill()));self.vias.append(t)
  for l in LAYERS:
   if t.IsOnLayer(l):self.addshape(t.GetEffectiveShape(l),t.GetNetCode(),l)
 def clear(self,a,c,l,net,diam=None):
  if diam is None:diam=self.width
  # Shape includes its copper width; clearance is applied to the other copper.
  x0=min(a.x,c.x);x1=max(a.x,c.x);y0=min(a.y,c.y);y1=max(a.y,c.y)
  if min(x0,y0)<50350000 or x1>138050000 or y1>66950000:return False
  shape=k.SHAPE_SEGMENT(a,c,diam);seen=set()
  for x,y in cells(x0,y0,x1,y1):
   for uid,n,s in self.index[l,x,y]:
    if uid in seen or n==net:continue
    seen.add(uid)
    if s.Collide(shape,CLEAR):return False
  return True
 def via_ok(self,p,net):
  if any(math.hypot(p.x-h.x,p.y-h.y)<(200000+d)/2+250000 for h,d in self.holes):return False
  return all(self.clear(p,p,l,net,400000)for l in LAYERS)
 def endpoint(self,i):
  o=self.byid[i['uuid']];p=vec(i['pos']['x']*1e6,i['pos']['y']*1e6)
  if isinstance(o,k.PAD):ls=[l for l in LAYERS if o.IsOnLayer(l)]
  elif isinstance(o,k.PCB_VIA):ls=LAYERS
  else:ls=[o.GetLayer()] if o.GetLayer()in LAYERS else []
  # Report positions at a through-via belong to every signal layer, even when
  # KiCad describes the incident track rather than the via itself.
  if any(v.GetNetCode()==o.GetNetCode()and math.hypot(p.x-v.GetX(),p.y-v.GetY())<1000 for v in self.vias):ls=LAYERS
  return p,ls,o.GetNetCode()
 def route(self,items,timeout):
  pa,la,net=self.endpoint(items[0]);pc,lc,nc=self.endpoint(items[1]);assert net==nc
  self.width=150000 if self.b.FindNet(net).GetNetname()in['+5V','VBUS']else WIDTH
  self.b.BuildConnectivity();conn=self.b.GetConnectivity()
  def island(item):
   result={};obj=self.byid[item['uuid']]
   for raw in conn.GetConnectedItems(obj):
    o=self.byid.get(str(raw.m_Uuid.AsString()))
    if o is None:continue
    if isinstance(o,k.PAD):points=[o.GetPosition()];ls=[l for l in LAYERS if o.IsOnLayer(l)]
    elif isinstance(o,k.PCB_VIA):points=[o.GetPosition()];ls=LAYERS
    else:
     ls=[o.GetLayer()]if o.GetLayer()in LAYERS else []
     a=o.GetStart();c=o.GetEnd();n=max(1,int((c-a).EuclideanNorm()/250000));points=[vec(a.x+(c.x-a.x)*j/n,a.y+(c.y-a.y)*j/n)for j in range(n+1)]
    for p in points:
     for l in ls:
      q=node(p,l)
      if self.clear(p,gpos(q),l,net):result[q]=p
   return result
  startpoints=island(items[0]);goalpoints=island(items[1]);starts=list(startpoints);goals=set(goalpoints)
  if not starts or not goals:return False,'blocked endpoint'
  if goals.intersection(starts):return False,'already connected'
  # Smaller goal sets make the multi-source heuristic cheaper.
  if len(goals)>len(starts):startpoints,goalpoints=goalpoints,startpoints;starts=list(startpoints);goals=set(goalpoints)
  gl=list(goals)
  def h(q):return min(math.hypot(q[0]-t[0],q[1]-t[1])+(0 if q[2]==t[2]else 12)for t in gl)
  queue=[];best={};prev={};counter=0;starttime=time.monotonic();cache={};v_cache={}
  for q in starts:best[q]=0;heapq.heappush(queue,(h(q),0,counter,q));counter+=1
  directions=[(1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,math.sqrt(2)),(-1,1,math.sqrt(2)),(1,-1,math.sqrt(2)),(-1,-1,math.sqrt(2))]
  found=None
  while queue:
   _,cost,_,q=heapq.heappop(queue)
   if cost!=best.get(q):continue
   if q in goals:found=q;break
   if counter%500==0 and time.monotonic()-starttime>timeout:return False,'timeout %s'%counter
   a=gpos(q);x,y,l=q
   neighbors=[]
   for dx,dy,w in directions:
    r=(x+dx,y+dy,l);key=(q,r)
    ok=cache.get(key)
    if ok is None:ok=self.clear(a,gpos(r),l,net);cache[key]=ok
    if ok:neighbors.append((r,w))
   key=(x,y)
   vok=v_cache.get(key)
   if vok is None:vok=self.via_ok(a,net);v_cache[key]=vok
   if vok:
    for ll in LAYERS:
     if ll!=l:neighbors.append(((x,y,ll),18))
   for r,w in neighbors:
    new=cost+w
    if new+1e-8<best.get(r,float('inf')):
     best[r]=new;prev[r]=q;heapq.heappush(queue,(new+1.05*h(r),new,counter,r));counter+=1
  if found is None:return False,'no path'
  path=[found]
  while path[-1]in prev:path.append(prev[path[-1]])
  path.reverse()
  # Compress collinear runs without altering the checked geometry.
  clean=[path[0]]
  for i in range(1,len(path)-1):
   a,c,d=path[i-1:i+2]
   if (c[0]-a[0],c[1]-a[1],c[2]-a[2])!=(d[0]-c[0],d[1]-c[1],d[2]-c[2]):clean.append(c)
  clean.append(path[-1])
  ni=self.b.FindNet(net)
  def seg(a,c,l):
   if a==c:return
   t=k.PCB_TRACK(self.b);t.SetStart(a);t.SetEnd(c);t.SetLayer(l);t.SetWidth(self.width);t.SetNet(ni);self.b.Add(t);self.additem(t)
  seg(startpoints[clean[0]],gpos(clean[0]),clean[0][2]);addedvias=set()
  for a,c in zip(clean,clean[1:]):
   if a[2]!=c[2]:
    key=a[:2]
    if key not in addedvias:
     v=k.PCB_VIA(self.b);v.SetPosition(gpos(a));v.SetWidth(400000);v.SetDrill(200000);v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(ni);self.b.Add(v);self.additem(v);addedvias.add(key)
   else:seg(gpos(a),gpos(c),a[2])
  seg(gpos(clean[-1]),goalpoints[clean[-1]],clean[-1][2]);return True,f'{len(clean)} corners,{len(addedvias)} vias,{counter} nodes'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('pcb',type=Path);ap.add_argument('report',type=Path);ap.add_argument('--seconds',type=float,default=12);ap.add_argument('--only');a=ap.parse_args()
 b=k.LoadBoard(str(a.pcb));r=Router(b);data=json.loads(a.report.read_text());n=0
 for issue in data['unconnected_items']:
  items=issue['items']
  if a.only and a.only not in items[0]['description']:continue
  label=items[0]['description'].split('[')[-1].split(']')[0]
  ok,why=r.route(items,a.seconds);print(label,ok,why,flush=True);n+=ok
  if ok:k.SaveBoard(str(a.pcb),b)
 b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(a.pcb),b);print('Added',n,'connections; rerun native DRC.',flush=True)
if __name__=='__main__':main()
