"""Scratch-only clearance-checked A* completion, ordinary .6/.3mm vias."""
import argparse,collections,heapq,json,math,shutil,subprocess,time
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,default=P/'grounded4.kicad_pcb');ap.add_argument('--output',type=Path,default=P/'grid4.kicad_pcb');ap.add_argument('--max-routes',type=int,default=70);a=ap.parse_args()
b=k.LoadBoard(str(a.input));LAYERS=[k.F_Cu,k.In1_Cu,k.In3_Cu,k.B_Cu];STEP=50000;MINX=50350000;MAXX=138050000;MINY=50350000;MAXY=66950000
for ext in('kicad_pro','kicad_dru'):shutil.copy2(a.input.with_suffix('.'+ext),a.output.with_suffix('.'+ext))
def ident(o):return str(o.m_Uuid.AsString())
def vec(p):return k.VECTOR2I(int(p[0]),int(p[1]))
def gridvec(n):return k.VECTOR2I(n[0]*STEP,n[1]*STEP)
def board_objects():return [p for f in b.GetFootprints()for p in f.Pads()]+list(b.GetTracks())
def index_objects():
 objects=board_objects();ix={l:collections.defaultdict(list)for l in list(dict.fromkeys(LAYERS+[k.In2_Cu,k.In4_Cu]))};holes=collections.defaultdict(list);padix=collections.defaultdict(list)
 for o in objects:
  net=o.GetNetCode();bb=o.GetBoundingBox();xmin=(bb.GetLeft()-500000)//1000000;xmax=(bb.GetRight()+500000)//1000000;ymin=(bb.GetTop()-500000)//1000000;ymax=(bb.GetBottom()+500000)//1000000
  for layer in ix:
   if not o.IsOnLayer(layer):continue
   shape=o.GetEffectiveShape(layer)
   for x in range(xmin,xmax+1):
    for y in range(ymin,ymax+1):ix[layer][x,y].append((net,shape,o))
  drill=max(o.GetDrillSize().x,o.GetDrillSize().y)if isinstance(o,k.PAD)else o.GetDrill()if isinstance(o,k.PCB_VIA)else 0
  if drill:
   pos=o.GetPosition()
   for x in range((pos.x-1000000)//1000000,(pos.x+1000000)//1000000+1):
    for y in range((pos.y-1000000)//1000000,(pos.y+1000000)//1000000+1):holes[x,y].append((pos.x,pos.y,drill))
 return ix,holes,objects

def route(first,second,firstOnly=False,secondOnly=False,protected_ids=None):
 net=first.GetNetCode();name=first.GetNetname();width=150000 if name in('VBUS','FUSED_VBUS','+5V','VLED_5V','+3V3','SW_3V3')or(name.startswith('COL')and name.endswith('_A'))or name.startswith('USB_')else 110000
 ix,holes,objects=index_objects();clear_cache={};via_cache={};forbidden=set()
 protected_ids=set(protected_ids or []);source_pos=first.GetPosition()
 def blocked(code,obj,p,q):
  if code!=net:return True
  if ident(obj)not in protected_ids:return False
  # A shared joint is allowed only within0.4mm of the actual ESD output land.
  return (p-source_pos).EuclideanNorm()>400000 or(q-source_pos).EuclideanNorm()>400000
 def clear(n):
  if n in clear_cache:return clear_cache[n]
  p=gridvec(n)
  if not(MINX<=p.x<=MAXX and MINY<=p.y<=MAXY):clear_cache[n]=False;return False
  shape=k.SHAPE_SEGMENT(p,p,width)
  result=not any(blocked(oc,o,p,p)and sh.Collide(shape,149999)for oc,sh,o in ix[LAYERS[n[2]]][p.x//1000000,p.y//1000000]);clear_cache[n]=result;return result
 def segment(p,q,layer):
  shape=k.SHAPE_SEGMENT(p,q,width);mx=(p.x+q.x)//2;my=(p.y+q.y)//2
  return not any(blocked(oc,o,p,q)and sh.Collide(shape,149999)for oc,sh,o in ix[layer][mx//1000000,my//1000000])
 def via_ok(n):
  xy=n[:2]
  if xy in via_cache:return via_cache[xy]
  p=gridvec(n);shape=k.SHAPE_SEGMENT(p,p,450000);drill_shape=k.SHAPE_SEGMENT(p,p,300000);okay=50475000<=p.x<=137925000 and 50475000<=p.y<=66825000;seen=set()
  for layer in ix:
   for oc,sh,o in ix[layer][p.x//1000000,p.y//1000000]:
    if blocked(oc,o,p,p)and sh.Collide(shape,149999):okay=False;break
    # Through-hole via must stay outside every solderable land, even same net.
    # This6L candidate requires filled/capped vias; same-net SMD land capture is permitted.
   if not okay:break
  if okay:
   for x,y,drill in holes[p.x//1000000,p.y//1000000]:
    if math.hypot(p.x-x,p.y-y)<(300000+drill)/2+(450000 if drill>300000 else 250000):okay=False;break
  via_cache[xy]=okay;return okay
 def seeds(item,only=False):
  out={}
  comp=list(b.GetConnectivity().GetConnectedItems(item))
  if only:
   center=item.GetPosition()
   comp=[item]+[o for o in comp if o.GetClass()=='PCB_VIA'and(o.GetPosition()-center).EuclideanNorm()<=400000]
  for obj in comp:
   points=[obj.GetPosition()]if isinstance(obj,(k.PAD,k.PCB_VIA))else[obj.GetStart(),obj.GetEnd()]if isinstance(obj,k.PCB_TRACK)else[]
   for p in points:
    for li,l in enumerate(LAYERS):
     if not obj.IsOnLayer(l):continue
     for ox in(-1,0,1):
      for oy in(-1,0,1):
       n=(round(p.x/STEP)+ox,round(p.y/STEP)+oy,li)
       if clear(n)and segment(p,gridvec(n),l):out[n]=p
  return out
 starts=seeds(first,firstOnly);goals=seeds(second,secondOnly)
 if not starts or not goals:return {'net':name,'result':'no accessible grid seeds','starts':len(starts),'goals':len(goals)}
 targets=list(goals);g={n:0 for n in starts};parent={};queue=[];serial=0
 # Exact obstacle-free Manhattan distance to the nearest target, then a
 #7x lower bound for8-neighbour movement. O(1) heuristic avoids rescanning
 # thousands of endpoint targets for every A* node on fragmented old nets.
 from array import array
 hx0=MINX//STEP;hy0=MINY//STEP;hw=MAXX//STEP-hx0+1;hh=MAXY//STEP-hy0+1
 distance=array('H',[65535])*(hw*hh)
 for x,y,_ in targets:distance[(y-hy0)*hw+x-hx0]=0
 for y in range(hh):
  base=y*hw
  for x in range(hw):
   i=base+x;z=distance[i]
   if x and distance[i-1]+1<z:z=distance[i-1]+1
   if y and distance[i-hw]+1<z:z=distance[i-hw]+1
   distance[i]=z
 for y in range(hh-1,-1,-1):
  base=y*hw
  for x in range(hw-1,-1,-1):
   i=base+x;z=distance[i]
   if x+1<hw and distance[i+1]+1<z:z=distance[i+1]+1
   if y+1<hh and distance[i+hw]+1<z:z=distance[i+hw]+1
   distance[i]=z
 def h(n):return int(distance[(n[1]-hy0)*hw+n[0]-hx0])*7
 for n in starts:heapq.heappush(queue,(h(n),0,serial,n));serial+=1
 visit=0;start=time.time();end=None
 while queue and visit<1500000 and time.time()-start<55:
  _,cost,_,n=heapq.heappop(queue)
  if g.get(n)!=cost:continue
  visit+=1
  if n in goals:end=n;break
  for dx,dy in((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
   z=(n[0]+dx,n[1]+dy,n[2]);nc=cost+(14 if dx and dy else 10)
   if nc>=g.get(z,10**12)or not clear(z):continue
   if dx and dy and(not clear((n[0]+dx,n[1],n[2]))or not clear((n[0],n[1]+dy,n[2]))):continue
   if not segment(gridvec(n),gridvec(z),LAYERS[n[2]]):continue
   g[z]=nc;parent[z]=n;heapq.heappush(queue,(nc+h(z),nc,serial,z));serial+=1
  # A layer transition is only allowed at a native-shape and drill-safe site.
  for li in range(len(LAYERS)):
   if li==n[2]:continue
   z=(n[0],n[1],li);nc=cost+400
   if nc>=g.get(z,10**12)or not clear(z)or not via_ok(n):continue
   g[z]=nc;parent[z]=n;heapq.heappush(queue,(nc+h(z),nc,serial,z));serial+=1
 if end is None:return {'net':name,'result':'search exhausted','visited':visit,'seconds':round(time.time()-start,2)}
 path=[end]
 while path[-1]in parent:path.append(parent[path[-1]])
 path.reverse();moves=[]
 moves.append((starts[path[0]],gridvec(path[0]),LAYERS[path[0][2]]))
 vias=set()
 for p,q in zip(path,path[1:]):
  if p[2]!=q[2]:vias.add(p[:2]);continue
  moves.append((gridvec(p),gridvec(q),LAYERS[p[2]]))
 moves.append((gridvec(path[-1]),goals[path[-1]],LAYERS[path[-1][2]]))
 # Merge consecutive collinear segments; leave native coordinates exact.
 merged=[]
 for p,q,l in moves:
  if p==q:continue
  if merged and merged[-1][2]==l and merged[-1][1]==p:
   old=merged[-1];u=old[1]-old[0];v=q-p
   if u.x*v.y==u.y*v.x and u.x*v.x+u.y*v.y>0:merged[-1]=(old[0],q,l);continue
  merged.append((p,q,l))
 new_ids=[]
 for p,q,l in merged:
  assert segment(p,q,l)
  t=k.PCB_TRACK(b);t.SetStart(p);t.SetEnd(q);t.SetWidth(width);t.SetLayer(l);t.SetNet(first.GetNet());b.Add(t);new_ids.append(ident(t))
 for x,y in vias:
  v=k.PCB_VIA(b);v.SetPosition(vec((x*STEP,y*STEP)));v.SetWidth(450000);v.SetDrill(300000);v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(first.GetNet());b.Add(v);new_ids.append(ident(v))
 b.BuildConnectivity()
 return {'net':name,'result':'connected','visited':visit,'seconds':round(time.time()-start,2),'segments':len(merged),'vias':len(vias),'trace_length_mm':sum((q-p).EuclideanNorm()for p,q,l in merged)/1e6,'new_object_ids':new_ids,'polyline':[[p.x/1e6,p.y/1e6,b.GetLayerName(l),q.x/1e6,q.y/1e6]for p,q,l in merged]}

log=[];failed=set()
for iteration in range(a.max_routes):
 b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(a.output),b)
 report=a.output.with_name(a.output.stem+'-drc.json')
 subprocess.run([CLI,'pcb','drc','--format','json','--severity-all','-o',str(report),str(a.output)],check=True,stdout=subprocess.DEVNULL)
 d=json.loads(report.read_text());items={ident(o):o for o in board_objects()};pairs=[]
 for u in d['unconnected_items']:
  one,two=[items.get(i['uuid'])for i in u['items']]
  if one is None or two is None:continue
  key=tuple(sorted((ident(one),ident(two))))
  if key not in failed and not one.GetNetname().startswith('USB_'):pairs.append((key,one,two))
 if not pairs:print('No remaining searchable pairs; unconnected',len(d['unconnected_items']),flush=True);break
 # Short breaks first reduce obstacles for the harder remaining nets.
 pairs.sort(key=lambda x:(x[1].GetPosition()-x[2].GetPosition()).EuclideanNorm())
 key,first,second=pairs[0];result=route(first,second);result['iteration']=iteration;log.append(result);print(json.dumps({k:v for k,v in result.items()if k not in('new_object_ids','polyline')}),flush=True)
 if result['result']!='connected':failed.add(key)
 (P/'grid-routing-log.json').write_text(json.dumps(log,indent=2))
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(a.output),b)
