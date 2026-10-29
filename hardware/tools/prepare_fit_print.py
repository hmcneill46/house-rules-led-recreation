#!/usr/bin/env python3
"""Create a dimensional Hyper PLA fit-test project from the user's Orca copy.

Preserves machine start/end code, meshes and transforms. The result must be
sliced in Orca and inspected; this tool does not operate or start the printer.
"""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'hardware/printing'
source=D/'pin-fit-KE-original.3mf';dest=D/'HouseRules_Fit_KE04_PLA.3mf'
with zipfile.ZipFile(source)as z:
 entries={i.filename:(i,z.read(i))for i in z.infolist()}
config=json.loads(entries['Metadata/project_settings.config'][1])
assert config['printer_settings_id']=='Creality Ender-3 V3 KE 0.4 nozzle'
assert config['nozzle_diameter']==['0.4'] and config['gcode_flavor']=='klipper'
models=entries['Metadata/model_settings.config'][1].decode()
assert 'pin-fit-plate.stl'in models and 'pin-fit-scale-50mm.stl'in models
machine_code={k:config[k]for k in['machine_start_gcode','machine_end_gcode']}
scalar={
 'print_settings_id':'House Rules Fit 0.20mm @Ender-3 V3 KE 0.4',
 'layer_height':'0.2','initial_layer_print_height':'0.2',
 'wall_loops':'3','top_shell_layers':'5','bottom_shell_layers':'5',
 'top_shell_thickness':'0','bottom_shell_thickness':'0',
 'initial_layer_speed':'20','initial_layer_infill_speed':'20',
 'outer_wall_speed':'40','inner_wall_speed':'80','sparse_infill_speed':'100',
 'internal_solid_infill_speed':'100','top_surface_speed':'40','gap_infill_speed':'40',
 'small_perimeter_threshold':'2','small_perimeter_speed':'50%',
 'default_acceleration':'2000','inner_wall_acceleration':'2000',
 'outer_wall_acceleration':'1000','top_surface_acceleration':'1000',
 'initial_layer_acceleration':'500','travel_acceleration':'2000','travel_speed':'200',
 'xy_hole_compensation':'0','xy_contour_compensation':'0',
 'elefant_foot_compensation':'0.05','elefant_foot_compensation_layers':'1',
 'enable_support':'0','raft_layers':'0','brim_type':'no_brim','skirt_loops':'0',
 'enable_prime_tower':'0','enable_arc_fitting':'0',
}
arrays={
 'filament_settings_id':['House Rules Hyper PLA Grey @Ender-3 V3 KE'],
 'filament_vendor':['Creality'],'filament_type':['PLA'],
 'filament_colour':['#808080'],'filament_multi_colour':['#808080'],
 'nozzle_temperature':['215'],'nozzle_temperature_initial_layer':['220'],
 'filament_max_volumetric_speed':['10'],
 'fan_min_speed':['100'],'fan_max_speed':['100'],
 'close_fan_the_first_x_layers':['1'],'first_x_layer_fan_speed':['0'],
 'full_fan_speed_layer':['2'],'additional_cooling_fan_speed':['0'],
 'slow_down_for_layer_cooling':['1'],'slow_down_layer_time':['8'],
 'slow_down_min_speed':['10'],'dont_slow_down_outer_wall':['0'],
}
for bed in ['hot_plate','eng_plate','textured_plate']:
 arrays[bed+'_temp']=['55'];arrays[bed+'_temp_initial_layer']=['60']
config.update(scalar);config.update(arrays)
assert all(config[k]==v for k,v in machine_code.items())
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED)as z:
 for name,(info,data)in entries.items():
  if name=='Metadata/project_settings.config':data=json.dumps(config,indent=2).encode()
  z.writestr(info,data)
with zipfile.ZipFile(dest)as z:
 assert z.testzip()is None
 preserved={n:hashlib.sha256(data).hexdigest()for n,(_,data)in entries.items()if n!='Metadata/project_settings.config'}
 assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in preserved.items())
record={'source':str(source.relative_to(ROOT)),'output':str(dest.relative_to(ROOT)),
 'printer':config['printer_settings_id'],'filament':'Creality Hyper PLA grey 1.75 mm',
 'models_and_placement_preserved':True,'machine_start_end_preserved':True,
 'unmodified_entry_sha256':preserved,'settings_overrides':{**scalar,**arrays},
 'note':'PLA fit-test only. Do not use this G-code with PETG. Physical print/caliper check still required.'}
(D/'fit-print-settings.json').write_text(json.dumps(record,indent=2)+'\n')
print(dest)
