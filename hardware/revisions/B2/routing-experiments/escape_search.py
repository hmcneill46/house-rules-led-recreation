"""No-rip, no-rule-change local escape to an ordinary outside-land via."""
import collections,heapq,json,math,shutil
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;source=P/'fine4.kicad_pcb';dest=P/'escaped-final4.kicad_pcb';b=k.LoadBoard(str(source));LAYERS=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.B_Cu];STEP=50000
for ext in('kicad_pro','kicad_dru'):shutil.copy2(source.with_suffix('.'+ext),dest.with_suffix('.'+ext))
def v(n):return k.VECTOR2I(n[0]*STEP,n[1]*STEP)
plans=[]
for ref,pin in [('U2','4'),('U3','5'),('U3','12'),('U4','8'),('J9','1')]:
 f=next(f for f in b.GetFootprints()if f.GetReference()==ref);pad=next(p for p in f.Pads()if p.GetNumber()==pin);net=pad.GetNetCode();start=pad.GetPosition();ix={l:collections.defaultdict(list)for l in LAYERS};holes=collections.defaultdict(list)
 for o in[p for f in b.GetFootprints()for p in f.Pads()]+list(b.GetTracks()):
  bb=o.GetBoundingBox();xmin=(bb.GetLeft()-500000)//1000000;xmax=(bb.GetRight()+500000)//1000000;ymin=(bb.GetTop()-500000)//1000000;ymax=(bb.GetBottom()+500000)//1000000
  for l in LAYERS:
   if o.IsOnLayer(l):
    sh=o.GetEffectiveShape(l)
    for x in range(xmin,xmax+1):
     for y in range(ymin,ymax+1):ix[l][x,y].append((o.GetNetCode(),sh,o))
  d=max(o.GetDrillSize().x,o.GetDrillSize().y)if isinstance(o,k.PAD)else o.GetDrill()if isinstance(o,k.PCB_VIA)else 0
  if d:
   p=o.GetPosition()
   for x in range((p.x-1000000)//1000000,(p.x+1000000)//1000000+1):
    for y in range((p.y-1000000)//1000000,(p.y+1000000)//1000000+1):holes[x,y].append((p.x,p.y,d))
 cache={};vc={}
 def segment(p,q):
  sh=k.SHAPE_SEGMENT(p,q,110000);mp=((p.x+q.x)//2000000,(p.y+q.y)//2000000)
  return not any(n!=net and s.Collide(sh,149999)for n,s,o in ix[k.B_Cu][mp])
 def clear(n):
  if n in cache:return cache[n]
  p=v(n)
  if not(50350000<=p.x<=138050000 and 50350000<=p.y<=66950000)or abs(p.x-start.x)>4000000 or abs(p.y-start.y)>4000000:cache[n]=False;return False
  cache[n]=segment(p,p);return cache[n]
 def via(n):
  if n in vc:return vc[n]
  p=v(n);key=(p.x//1000000,p.y//1000000);sh=k.SHAPE_SEGMENT(p,p,600000);drill=k.SHAPE_SEGMENT(p,p,300000);okay=50550000<=p.x<=137850000 and 50550000<=p.y<=66750000
  if okay:
   for l in LAYERS:
    for no,s,o in ix[l][key]:
     if no!=net and s.Collide(sh,149999):okay=False;break
     if isinstance(o,k.PAD)and no==net and s.Collide(drill,49999):okay=False;break
    if not okay:break
  if okay:
   for x,y,d in holes[key]:
    if math.hypot(p.x-x,p.y-y)<(300000+d)/2+250000:okay=False;break
  vc[n]=okay;return okay
 seeds={}
 for dx in(-1,0,1):
  for dy in(-1,0,1):
   n=(round(start.x/STEP)+dx,round(start.y/STEP)+dy)
   if clear(n)and segment(start,v(n)):seeds[n]=start
 heap=[(0,n)for n in seeds];heapq.heapify(heap);cost={n:0 for n in seeds};parents={};end=None;visited=0
 while heap:
  c,n=heapq.heappop(heap)
  if cost[n]!=c:continue
  visited+=1
  if via(n):end=n;break
  for dx,dy in((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
   z=(n[0]+dx,n[1]+dy);nc=c+(14 if dx and dy else 10)
   if nc>=cost.get(z,10**12)or not clear(z):continue
   if not segment(v(n),v(z)):continue
   cost[z]=nc;parents[z]=n;heapq.heappush(heap,(nc,z))
 if end is None:plans.append({'ref':ref,'pin':pin,'status':'no no-rip escape','visited':visited});print(ref,pin,'NO ESCAPE',visited,flush=True);continue
 path=[end]
 while path[-1]in parents:path.append(parents[path[-1]])
 path.reverse();poly=[start]+[v(n)for n in path]
 for p,q in zip(poly,poly[1:]):
  if p==q:continue
  t=k.PCB_TRACK(b);t.SetStart(p);t.SetEnd(q);t.SetWidth(110000);t.SetLayer(k.B_Cu);t.SetNet(pad.GetNet());t.SetLocked(True);b.Add(t)
 vv=k.PCB_VIA(b);vv.SetPosition(v(end));vv.SetWidth(600000);vv.SetDrill(300000);vv.SetViaType(k.VIATYPE_THROUGH);vv.SetLayerPair(k.F_Cu,k.B_Cu);vv.SetNet(pad.GetNet());vv.SetLocked(True);b.Add(vv)
 plans.append({'ref':ref,'pin':pin,'status':'escaped','visited':visited,'poly':[[k.ToMM(p.x),k.ToMM(p.y)]for p in poly]});print(ref,pin,'escaped',visited,[k.ToMM(v(end).x),k.ToMM(v(end).y)],flush=True)
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(dest),b);(P/'final-escape-plans.json').write_text(json.dumps(plans,indent=2))
