"""Route explicit USB series legs between native-checked staggered escapes."""
import ast,collections,heapq,json,math,shutil,time
from pathlib import Path
import wx,pcbnew as k
wx.Log.EnableLogging(False);app=wx.App(False)
P=Path(__file__).parent;source=P/'usb-escaped6.kicad_pcb';dest=P/'usb-done6.kicad_pcb';b=k.LoadBoard(str(source));LAYERS=[k.F_Cu,k.In1_Cu,k.In3_Cu,k.B_Cu];STEP=50000;MINX=50350000;MAXX=138050000;MINY=50350000;MAXY=66950000
for ext in('kicad_pro','kicad_dru'):shutil.copy2(source.with_suffix('.'+ext),dest.with_suffix('.'+ext))
names={'ident','vec','gridvec','board_objects','index_objects','route'};tree=ast.parse((P/'grid_finish.py').read_text());node=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names],type_ignores=[]);exec(compile(node,str(P/'grid_finish.py'),'exec'),globals())
escapes={p['label']:p for p in json.loads((P/'usb-escape-plan.json').read_text())};log=[];protected={}
def pad(ref,number):return next(p for f in b.GetFootprints()if f.GetReference()==ref for p in f.Pads()if p.GetNumber()==number)
def via(label):return next(t for t in b.GetTracks()if ident(t)==escapes[label]['via_uuid'])
def leg(label,start,end,protect=()):
 result=route(via(start),via(end),True,True,protect);result.update(label=label,source_escape=start,target_escape=end);log.append(result);print(label,result['result'],result.get('trace_length_mm'),result.get('vias'),flush=True)
 b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(dest),b);(P/'usb-route-actions.json').write_text(json.dumps(log,indent=2))
 if result['result']!='connected':raise RuntimeError(label+' failed; preserve candidate and inspect before proceeding')
 return result
for channel,wire,esdTop in[('DM','J17','10'),('DP','J18','9')]:
 result=leg(channel+'_connector_to_ESD',channel+'_WIRE',channel+'_ESD_TOP');protected[channel]=result['new_object_ids']+[ident(pad(wire,'1')),ident(pad('U7',esdTop))]
 for label in(channel+'_WIRE',channel+'_ESD_TOP'):
  protected[channel]+=[escapes[label]['via_uuid']]
  if escapes[label]['stub_uuid']:protected[channel].append(escapes[label]['stub_uuid'])
for channel in('DM','DP'):leg(channel+'_ESD_to_BC_CON',channel+'_ESD_BOTTOM',channel+'_BC_CON',protected[channel])
for channel in('DM','DP'):leg(channel+'_BC_HOST_to_MCU',channel+'_BC_HOST',channel+'_MCU')
summary={}
for channel in('DM','DP'):
 rows=[r for r in log if r['label'].startswith(channel+'_')];escape_labels=[channel+s for s in('_WIRE','_ESD_TOP','_ESD_BOTTOM','_BC_CON','_BC_HOST','_MCU')];stub=sum(escapes[e]['stub_length_mm']for e in escape_labels);hops=0
 for r in rows:
  poly=r['polyline'];hops+=r['vias']+int(poly[0][2]!='B.Cu')+int(poly[-1][2]!='B.Cu')
 summary[channel]={'trace_length_mm':sum(r['trace_length_mm']for r in rows)+.77+stub,'ESD_join_mm':.77,'escape_stubs_mm':stub,'via_layer_transitions':hops,'legs':[{'label':r['label'],'length_mm':r['trace_length_mm'],'routing_layers':list(dict.fromkeys(p[2]for p in r['polyline']))}for r in rows]}
summary['Dplus_minus_length_difference_mm']=abs(summary['DP']['trace_length_mm']-summary['DM']['trace_length_mm']);summary['scope']='PCB copper XY only. Excludes via vertical barrel lengths, external wires, XIAO traces and the internal BQ switch. No USB capture/eye test performed.'
(P/'usb-path-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)
