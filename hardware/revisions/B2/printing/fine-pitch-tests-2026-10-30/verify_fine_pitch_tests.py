#!/usr/bin/env python3
"""Independently audit the labelled spacing meshes and actual Orca output.

Read-only for every source/project/G-code file; writes only verification.json.
No dependency on the plate generator's implementation or claimed hole table.
"""
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import hashlib
import itertools
import json
import math
import re
import struct
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
B2 = HERE.parents[1]
ROOT = B2.parents[2]
CORE = '{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
PROD = '{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
EXPECTED = [('D', Decimal('12.825')), ('E', Decimal('12.850')), ('F', Decimal('12.875'))]
JOB = 'LED_Pitch_DEF_Fine_KE04_HyperPLA'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_stl(path):
    data = path.read_bytes()
    if len(data) >= 84 and 84 + 50 * struct.unpack('<I', data[80:84])[0] == len(data):
        result = []
        for off in range(84, len(data), 50):
            values = struct.unpack('<12fH', data[off:off + 50])
            result.append([tuple(values[j:j + 3]) for j in (3, 6, 9)])
        return result
    vertices = [tuple(map(float, line.split()[1:4])) for line in data.decode().splitlines()
                if line.lstrip().startswith('vertex ')]
    assert len(vertices) % 3 == 0
    return [vertices[i:i + 3] for i in range(0, len(vertices), 3)]


def bounds(triangles):
    vertices = [p for t in triangles for p in t]
    return [[min(p[i] for p in vertices) for i in range(3)],
            [max(p[i] for p in vertices) for i in range(3)]]


def components(adjacency):
    remaining = set(adjacency)
    result = []
    while remaining:
        first = remaining.pop()
        queue = [first]
        found = {first}
        while queue:
            for nxt in adjacency[queue.pop()]:
                if nxt not in found:
                    found.add(nxt)
                    remaining.remove(nxt)
                    queue.append(nxt)
        result.append(found)
    return result


def check_label_source(path, pitch):
    source = path.with_suffix('.scad').read_text()
    letter = path.name[0]
    expected = [letter, 'P' + format(pitch, '.3f'), '+' + format(pitch-Decimal('12.700'), '.3f')]
    actual = re.findall(r'text\("([^"\n]+)"', source)
    assert actual == expected, (path.name, actual, expected)
    return {'actual_SCAD_text': actual, 'three_decimal_pitch_and_increment': True}


def mesh_audit(path, pitch, canonical):
    ts = read_stl(path)
    edges = Counter()
    directed = Counter()
    adjacency = defaultdict(set)
    bottom_edges = Counter()
    volume = 0.0
    for t in ts:
        a, b, c = t
        volume += (a[0] * (b[1] * c[2] - b[2] * c[1])
            + a[1] * (b[2] * c[0] - b[0] * c[2])
            + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
        for i in range(3):
            p, q = t[i], t[(i + 1) % 3]
            edges[tuple(sorted((p, q)))] += 1
            directed[(p, q)] += 1
            adjacency[p].add(q)
            adjacency[q].add(p)
        if all(abs(p[2]) < 1e-8 for p in t):
            for i in range(3):
                bottom_edges[tuple(sorted((t[i][:2], t[(i + 1) % 3][:2])))] += 1
    assert all(n == 2 for n in edges.values()), path.name + ': nonmanifold edge'
    assert all(directed[(a, b)] == directed[(b, a)] for a, b in edges), path.name + ': winding'
    assert volume > 0
    assert len(components(adjacency)) == 1
    euler = len(adjacency) - len(edges) + len(ts)
    assert euler == -166, (path.name, euler)
    boundary = defaultdict(set)
    for (a, b), n in bottom_edges.items():
        if n == 1:
            boundary[a].add(b)
            boundary[b].add(a)
    assert all(len(neighbours) == 2 for neighbours in boundary.values())
    loops = components(boundary)
    assert len(loops) == 85
    hole_loops = [p for p in loops if len(p) == 32]
    assert len(hole_loops) == 84
    centres = []
    for loop in hole_loops:
        size = [max(p[i] for p in loop) - min(p[i] for p in loop) for i in range(2)]
        assert max(abs(s - 1) for s in size) < .0001
        centres.append(tuple(sum(p[i] for p in loop) / len(loop) for i in range(2)))
    used = set()
    errors = []
    for key, original in canonical.items():
        module = int(key.split('.')[0][2:]) - 1
        ox, oy = [v / 1e6 for v in original['relative_position_nm']]
        delta_nm = int((pitch - Decimal('12.700')) * 1_000_000)
        expected = ((original['relative_position_nm'][0] + module * delta_nm) / 1e6, oy)
        index = min(range(84), key=lambda j: math.dist(centres[j], expected))
        error = math.dist(centres[index], expected)
        assert error < .0001 and index not in used, (key, error)
        used.add(index)
        errors.append(error)
    raised = [p for t in ts for p in t if p[2] > 1.6001]
    assert raised and max(p[0] for p in raised) < -.5
    assert abs(max(p[2] for p in raised) - 2.2) < .00001
    raised_rows = {}
    for row, ymin, ymax in (('letter',11,16), ('pitch',6.5,10.5), ('increment',2,5.5)):
        pts = [p for p in raised if ymin <= p[1] <= ymax]
        assert pts, (path.name, row)
        raised_rows[row] = [[min(p[i] for p in pts) for i in range(3)],
                            [max(p[i] for p in pts) for i in range(3)]]
    assert sum(len([p for p in raised if ymin <= p[1] <= ymax])
               for ymin,ymax in ((11,16),(6.5,10.5),(2,5.5))) == len(raised)
    # Recovered geometry is independent of the generator's JSON claims.
    measured_centres = {}
    for key, original in canonical.items():
        module = int(key.split('.')[0][2:])-1
        expected = ((original['relative_position_nm'][0] + module * delta_nm)/1e6,
                    original['relative_position_nm'][1]/1e6)
        measured_centres[key] = min(centres, key=lambda p: math.dist(p, expected))
    measured_steps = []
    internal_errors = []
    for module in range(1,8):
        for pin in range(1,13):
            key = f'DS{module}.{pin}'
            basekey = f'DS1.{pin}'
            measured = measured_centres[key]
            base = measured_centres[basekey]
            internal_errors.append(abs((measured[0]-base[0])-(module-1)*float(pitch)))
            internal_errors.append(abs(measured[1]-base[1]))
            if module < 7:
                nxt = measured_centres[f'DS{module+1}.{pin}']
                measured_steps.append(nxt[0]-measured[0])
    assert max(internal_errors)<.0001
    assert max(abs(s-float(pitch)) for s in measured_steps)<.0001
    br = bounds(ts)
    width = float(Decimal('88.400') + 6 * (pitch - Decimal('12.700')))
    assert max(abs(a - b) for a, b in zip(br[0], (-18, 0, 0))) < .0001
    assert max(abs(a - b) for a, b in zip(br[1], (width, 17.3, 2.2))) < .0001
    return {'STL': str(path.relative_to(HERE)), 'STL_sha256': sha(path),
        'label_source_strings': check_label_source(path, pitch),
        'closed_manifold': True, 'consistent_winding': True,
        'connected_solid_bodies': 1, 'positive_volume_mm3': volume,
        'Euler_characteristic': euler, 'independent_bottom_boundary_holes': 84,
        'circular_hole_polygon_vertices': 32, 'nominal_print_holes_mm': 1,
        'maximum_hole_centre_error_mm': max(errors),
        'nominal_pitch_mm': float(pitch), 'pitch_increment_from_12p700_mm': float(pitch-Decimal('12.700')),
        'coordinate_arithmetic': 'Independent expected centres computed in integer nanometres, then compared with actual STL bottom boundaries.',
        'canonical_intramodule_pattern_plus_only_pitch_translation': True,
        'raised_labels_exist_entirely_on_external_negative_X_tab': True,
        'physical_raised_text_row_bounds_mm': raised_rows,
        'measured_adjacent_module_pitch_mm_range': [min(measured_steps),max(measured_steps)],
        'maximum_rigid_intramodule_pattern_error_mm':max(internal_errors),
        'actual_bounds_mm': br}


def sliced_objects(archive):
    names = {int(o.attrib['id']): o.find("metadata[@key='name']").attrib['value']
             for o in ET.fromstring(archive.read('Metadata/model_settings.config')).findall('object')}

    def identity_translation(text):
        values = list(map(float, text.split())) if text else [1,0,0,0,1,0,0,0,1,0,0,0]
        assert len(values) == 12
        assert max(abs(a-b) for a,b in zip(values[:9], [1,0,0,0,1,0,0,0,1])) < 1e-9
        return values[9:]

    def object_mesh(path, objid, translation):
        root = ET.fromstring(archive.read(path))
        obj = next(o for o in root.find(CORE + 'resources') if o.attrib.get('id') == str(objid))
        mesh = obj.find(CORE + 'mesh')
        if mesh is not None:
            points = [tuple(float(v.attrib[a]) + translation[i] for i,a in enumerate('xyz'))
                      for v in mesh.find(CORE + 'vertices')]
            return [[points[int(t.attrib['v' + str(i)])] for i in (1,2,3)]
                    for t in mesh.find(CORE + 'triangles')]
        triangles = []
        for c in obj.find(CORE + 'components'):
            delta = identity_translation(c.attrib.get('transform'))
            child_path = c.attrib.get(PROD + 'path', path).lstrip('/')
            triangles += object_mesh(child_path, c.attrib['objectid'],
                                     [a+b for a,b in zip(translation,delta)])
        return triangles

    root = ET.fromstring(archive.read('3D/3dmodel.model'))
    return {names[int(item.attrib['objectid'])]: object_mesh('3D/3dmodel.model',
        item.attrib['objectid'], identity_translation(item.attrib.get('transform')))
        for item in root.find(CORE + 'build')}


def compare_meshes(source, actual):
    """Map actual float32 vertices to independently read STL vertices, then faces."""
    expected = read_stl(source)
    assert len(expected) == len(actual)
    eb, ab = bounds(expected), bounds(actual)
    expected_points = list(set(tuple(p[i]-eb[0][i] for i in range(3)) for t in expected for p in t))
    bins = defaultdict(list)
    cell = .0001
    for index,p in enumerate(expected_points):
        bins[tuple(math.floor(v/cell) for v in p)].append(index)
    lookup = {p: index for index,p in enumerate(expected_points)}
    mapping = {}
    maximum = 0
    for p in set(p for t in actual for p in t):
        shifted = tuple(p[i]-ab[0][i] for i in range(3))
        key = tuple(math.floor(v/cell) for v in shifted)
        candidates = [j for delta in itertools.product((-1,0,1),repeat=3)
                      for j in bins.get(tuple(key[i]+delta[i] for i in range(3)), [])]
        assert candidates
        found = min(candidates,key=lambda j: math.dist(shifted,expected_points[j]))
        error = math.dist(shifted,expected_points[found])
        assert error < .00002, (source.name,error)
        mapping[p] = found
        maximum = max(maximum,error)
    expected_faces = Counter(tuple(sorted(lookup[tuple(p[i]-eb[0][i] for i in range(3))] for p in t)) for t in expected)
    actual_faces = Counter(tuple(sorted(mapping[p] for p in t)) for t in actual)
    assert expected_faces == actual_faces
    assert max(abs((eb[1][i]-eb[0][i])-(ab[1][i]-ab[0][i])) for i in range(3)) < .00002
    return {'source_mesh_geometry_retained': True, 'scale_percent': 100,
            'rotation_identity': True, 'triangles':len(actual),
            'maximum_float32_vertex_roundtrip_error_mm':maximum,'actual_plate_bounds_mm':ab}


def gcode_audit(path):
    text = path.read_text()
    config = dict(re.findall(r'^; ([A-Za-z0-9_]+) = (.*)$', text, re.M))
    for key, value in {'printer_settings_id':'Creality Ender-3 V3 KE 0.4 nozzle',
        'nozzle_diameter':'0.4','filament_type':'PLA','filament_diameter':'1.75',
        'layer_height':'0.2','initial_layer_print_height':'0.2','enable_support':'0',
        'brim_type':'no_brim','xy_hole_compensation':'0','xy_contour_compensation':'0',
        'nozzle_temperature':'215','nozzle_temperature_initial_layer':'220',
        'first_layer_bed_temperature':'60'}.items():
        assert config.get(key) == value, (key,config.get(key))
    with zipfile.ZipFile(ROOT/'hardware/printing/HouseRules_Fit_KE04_PLA.3mf') as z:
        original = json.loads(z.read('Metadata/project_settings.config'))
    for key in ('machine_start_gcode','machine_end_gcode'):
        assert config[key].replace('\\n','\n') == original[key]
    for token in ('M104 S220','M109 S220','M140 S60','M190 S60','M104 S215','M140 S55','M104 S0','M140 S0','M106 S0','M106 S255'):
        assert re.search(r'^'+re.escape(token)+r'(?:\s|$)',text,re.M),token
    executable = text.split('; CONFIG_BLOCK_START',1)[0]
    heaters = {'M104':{0.0,215.0,220.0},'M109':{220.0},'M140':{0.0,55.0,60.0},'M190':{60.0}}
    heater_commands = []
    for code,value in re.findall(r'^(M104|M109|M140|M190) S([0-9.]+)',executable,re.M):
        assert float(value) in heaters[code], (code,value)
        heater_commands.append([code,float(value)])
    for command in ('G28 X Y','G28 Z','BED_MESH_CALIBRATE PROBE_COUNT=5,5'):
        assert re.search(r'^'+re.escape(command)+r'(?:\s|$)',executable,re.M)
    assert not re.search(r'^;TYPE:(?:Support|Brim)',text,re.M)
    layer_z = list(map(float,re.findall(r'^;Z:([0-9.]+)',text,re.M)))
    assert len(layer_z)==11 and max(abs(z-.2*(i+1)) for i,z in enumerate(layer_z))<1e-8
    xyz = [0.0,0.0,0.0];e=0.0;relative_e=False;relative_xyz=False
    started=False;kind='';obj=None
    all_moves=[];extrusions=[];labels=defaultdict(list);label_rows=defaultdict(Counter)
    objects=Counter();features=Counter();first_layer=set()
    for line in text.splitlines():
        if line.startswith('; CONFIG_BLOCK_START'):break
        if line.startswith(';LAYER_CHANGE'):started=True
        if line.startswith(';TYPE:'):kind=line[6:]
        if line.startswith('EXCLUDE_OBJECT_START NAME='):obj=line.split('=',1)[1]
        if line.startswith('EXCLUDE_OBJECT_END'):obj=None
        command=line.split(';')[0].strip()
        if not command:continue
        code=command.split()[0]
        params={k:float(v) for k,v in re.findall(r'([XYZEF])(-?(?:\d+(?:\.\d*)?|\.\d+))',command)}
        if code=='M83':relative_e=True
        elif code=='M82':relative_e=False
        elif code=='G90':relative_xyz=False
        elif code=='G91':relative_xyz=True
        elif code=='G92':
            if 'E'in params:e=params['E']
        elif code in ('G0','G1'):
            before=xyz[:]
            for i,a in enumerate('XYZ'):
                if a in params:xyz[i]=xyz[i]+params[a]if relative_xyz else params[a]
            de=params.get('E',0)if relative_e else params.get('E',e)-e
            if'E'in params:e=e+de if relative_e else params['E']
            if any(a in params for a in 'XYZ'):all_moves.append(xyz[:])
            if started and de>0 and math.dist(before[:2],xyz[:2])>0:
                extrusions.extend([before[:],xyz[:]])
                objects[obj]+=1;features[kind]+=1
                if abs(xyz[2]-.2)<1e-6:first_layer.add(obj)
                if xyz[2]>1.6001:
                    assert obj and obj.startswith(('D_pitch','E_pitch','F_pitch'))
                    letter=obj[0];index='DEF'.index(letter);miny=62+32*index
                    assert max(before[0],xyz[0])<73.01
                    labels[letter].extend([before[:],xyz[:]])
                    cy=(before[1]+xyz[1])/2-miny
                    row=min((3.8,8.4,13.4),key=lambda y:abs(cy-y))
                    label_rows[letter][str(row)]+=1
    assert len(objects)==4 and len(first_layer)==4
    assert set(labels)==set('DEF')
    assert all(set(counts)=={'3.8','8.4','13.4'} and min(counts.values())>5 for counts in label_rows.values())
    assert extrusions and all(0<=p[0]<=220 and 0<=p[1]<=220 and 0<p[2]<=2.21 for p in extrusions)
    assert all(-2.001<=p[0]<=220 and 0<=p[1]<=220 and 0<=p[2]<=245 for p in all_moves)
    assert max(p[2] for p in all_moves)<30
    assert abs(min(p[0] for p in all_moves)+2.0)<1e-8
    assert any(abs(p[0]+1.7)<1e-8 for p in all_moves)
    assert abs(all_moves[-1][0]-2)<1e-8 and abs(all_moves[-1][1]-218)<1e-8
    return {'actual_config_verified':True,'native_start_end_preserved':True,
        'temperatures_C':{'nozzle':[220,215],'bed':[60,55]},'actual_heater_commands':heater_commands,'fan_PWM_sequence':[0,255],
        'model_layer_z_mm':layer_z,'supports':False,'brim':False,
        'object_extrusion_segment_counts':dict(objects),'all_four_objects_print_first_layer':True,
        'actual_raised_label_segment_counts_by_row':{k:dict(v)for k,v in label_rows.items()},
        'raised_label_extrusion_confined_to_external_tabs':True,
        'label_extrusion_scope':'Above 1.6 mm, only D/E/F external-tab text extrudes; every label row has executable extrusion.',
        'model_extrusion_bounds_mm':[[min(p[i] for p in extrusions)for i in range(3)],[max(p[i]for p in extrusions)for i in range(3)]],
        'all_motion_bounds_mm':[[min(p[i]for p in all_moves)for i in range(3)],[max(p[i]for p in all_moves)for i in range(3)]],
        'stock_negative_X_purge_preserved':True,
        'estimated_time':re.search(r'^; estimated printing time \(normal mode\) = (.+)$',text,re.M).group(1),
        'estimated_filament_g':float(re.search(r'^; filament used \[g\] = ([0-9.]+)',text,re.M).group(1))}


def main():
    source_audit=json.loads((B2/'reports/board-audit.json').read_text())
    report={'result':'PASS','date_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Independent actual STL boundary measurements, sliced3MF and executable Gcode checks; software inspection only, not a physical fit guarantee.',
        'canonical_PCB_unchanged':sha(B2/'kicad/house-rules-main-B2.kicad_pcb')==source_audit['board_sha256'],
        'canonical_PCB_sha256':source_audit['board_sha256'],
        'canonical_geometry_audit_sha256':sha(B2/'reports/board-audit.json'),
        'mesh_checks':{},'sliced_project_checks':{},'errors':[]}
    for letter,pitch in EXPECTED:
        p=HERE/'models'/(letter+'_pitch_'+format(pitch,'.3f').replace('.','p')+'.stl')
        report['mesh_checks'][letter]=mesh_audit(p,pitch,source_audit['LED_geometry'])
    gcode=HERE/'gcode'/(JOB+'.gcode');project=HERE/'sliced-projects'/(JOB+'.3mf')
    report['Gcode_sha256']=sha(gcode);report['sliced_project_sha256']=sha(project)
    with zipfile.ZipFile(project)as z:
        assert z.read('Metadata/plate_1.gcode')==gcode.read_bytes()
        report['embedded_Gcode_byte_identical']=True
        actual=sliced_objects(z)
    assert len(actual)==4
    for index,(letter,pitch)in enumerate(EXPECTED):
        name=letter+'_pitch_'+format(pitch,'.3f').replace('.','p')
        check=compare_meshes(HERE/'models'/(name+'.stl'),actual[name])
        expected_lo=[55,62+32*index,0]
        expected_hi=[55+18+float(Decimal('88.400')+6*(pitch-Decimal('12.700'))),79.3+32*index,2.2]
        assert max(abs(a-b)for a,b in zip(check['actual_plate_bounds_mm'][0],expected_lo))<.00002
        assert max(abs(a-b)for a,b in zip(check['actual_plate_bounds_mm'][1],expected_hi))<.00002
        report['sliced_project_checks'][letter]=check
    report['sliced_project_checks']['50mm_scale']=compare_meshes(ROOT/'hardware/mechanical/pin-fit-scale-50mm.stl',actual['pin-fit-scale-50mm'])
    report['Gcode_checks']=gcode_audit(gcode)
    report['limitations']=['Photos cannot establish exact required pitch or distinguish all printing warpage.','Nominal 0.025 mm CAD increments are not an assertion of FDM dimensional accuracy; across six joins the variants differ by 0.150 mm.','Check each empty strip is flat before fitting all seven LEDs without force.','Printed 1.0 mm holes do not establish 0.90 mm finished PCB hole tolerance.','Label-tab test widths are not final PCB/case outlines; recheck hardware after selecting the pitch.']
    assert report['canonical_PCB_unchanged']
    (HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: three labelled seven-module trials, all84 holes each, nativeKEHyperPLA, bedbounds, source meshes and exactembeddedGcode.')


if __name__=='__main__':
    main()
