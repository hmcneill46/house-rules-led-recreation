#!/usr/bin/env python3
"""Create and audit the print-only 84-hole fit plate, without OpenSCAD.

Requires numpy and mapbox-earcut. This creates a test jig, not fabrication data.
The print default is 1.0 holes; the PCB finished hole is 0.9. A print cannot
certify PCB hole or body tolerances, even if all seven modules fit it.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import struct
import numpy as np
import mapbox_earcut

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'hardware/mechanical'


def write_mesh(path, vertices, faces, label):
    data = bytearray(label.encode()[:80].ljust(80, b' '))
    data += struct.pack('<I', len(faces))
    edges = Counter()
    volume = 0.0
    for face in faces:
        a, b, c = (vertices[i] for i in face)
        normal = np.cross(b-a, c-a)
        assert np.linalg.norm(normal) > 1e-10
        normal /= np.linalg.norm(normal)
        volume += np.dot(a, np.cross(b,c))/6
        data += struct.pack('<12fH', *normal, *a, *b, *c, 0)
        for i,j in [(face[0],face[1]),(face[1],face[2]),(face[2],face[0])]:
            edges[tuple(sorted((int(i),int(j))))] += 1
    assert set(edges.values()) == {2}, Counter(edges.values())
    assert volume > 0
    path.write_bytes(data)
    return {'vertices': len(vertices), 'triangles': len(faces),
            'edges': len(edges), 'each_edge_shared_by_two_triangles': True,
            'euler_characteristic': len(vertices)-len(edges)+len(faces),
            'signed_volume_mm3': float(volume),
            'min_xyz': vertices.min(axis=0).tolist(),
            'max_xyz': vertices.max(axis=0).tolist()}


def extrude(rings, height):
    ends=np.cumsum([len(r) for r in rings]).astype(np.uint32)
    xy=np.array([p for ring in rings for p in ring],dtype=np.float64)
    triangles=mapbox_earcut.triangulate_float64(xy,ends).reshape((-1,3))
    count=len(xy)
    vertices=np.concatenate([np.c_[xy,np.zeros(count)],np.c_[xy,np.full(count,height)]])
    faces=[]
    for face in triangles:
        a,b,c=(xy[i] for i in face)
        area=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        if area < 0:face=face[::-1]
        faces.append(tuple(int(i)+count for i in face))
        faces.append(tuple(int(i) for i in face[::-1]))
    start=0
    for ring in rings:
        for i in range(len(ring)):
            a=start+i; b=start+(i+1)%len(ring)
            faces.extend([(a,b,b+count),(a,b+count,a+count)])
        start+=len(ring)
    return vertices,faces


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--print-hole-diameter',type=float,default=1.0)
    args=ap.parse_args()
    assert 0 < args.print_hole_diameter < 2
    spec=json.loads((ROOT/'hardware/kicad/circuit-spec.json').read_text())
    modules=sorted((p for p in spec['parts'] if p['board']=='main' and p['ref'].startswith('DS')),key=lambda p:int(p['ref'][2:]))
    assert len(modules)==7
    holes=[]
    rings=[[(0,0),(88.4,0),(88.4,17.3),(0,17.3)]]
    for part in modules:
        for side in [-1,1]:
            for row in range(6):
                x=round(part['x']+side*3.81,6)
                y=round(part['y']-6.35+2.54*row,6)
                number=row+1 if side<0 else 12-row
                holes.append({'module':part['ref'],'pin':number,'x':x,'y':y})
                rings.append([(x+args.print_hole_diameter/2*math.cos(-2*math.pi*i/32),y+args.print_hole_diameter/2*math.sin(-2*math.pi*i/32)) for i in range(32)])
    assert len(holes)==84 and len({(p['x'],p['y']) for p in holes})==84
    vertices,faces=extrude(rings,1.0)
    report={'status':'print-only test tool; no fit has been performed',
            'pcb_finished_hole_diameter_mm':.9,
            'print_hole_diameter_mm':args.print_hole_diameter,
            'round_hole_facets':32,'hole_centres':holes,
            'plate':write_mesh(OUT/'pin-fit-plate.stl',vertices,faces,f'House Rules TEST TOOL: {args.print_hole_diameter:g} print holes; PCB holes 0.9; no fit guarantee')}
    assert report['plate']['euler_characteristic']==2-2*84
    v,f=extrude([[(0,0),(50,0),(50,10),(0,10)]],1.0)
    report['separate_scale_coupon']=write_mesh(OUT/'pin-fit-scale-50mm.stl',v,f,'Separate 50 x 10 x 1 mm print-scale check coupon')
    # Same watertight extrusion method, supplied on its broad side for printing.
    v,f=extrude([[(-15,0),(92,0),(92,1),(-8,1),(-8,3),(-15,3)]],3.0)
    v=np.array([(x+15,3-z,y) for x,y,z in v])
    report['removable_3mm_spacer']=write_mesh(OUT/'led-standoff-spacer-3mm.stl',v,f,'Print TWO. Removable100x1x3 working bar plus7mm handle; turn on edge to use')
    report['spacer_usage']={'working_bar_xyz_mm':[100,1,3],
                           'board_local_centre_y_mm':[3.57,13.73],
                           'board_local_min_y_mm':[3.07,13.23],
                           'assembly_z_mm':[6.3,9.3],
                           'nearest_nominal_0_5mm_pin_edge_clearance_mm':.52,
                           'remove_direction':'left, along minusX after soldering',
                           'quantity_to_print':2}
    report['mesh_closed_manifold']=True
    (ROOT/'hardware/reports/pin-fit-plate-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Printed test plate: 88.4 x 17.3 x1.0; 84 holes at',args.print_hole_diameter,'nominal print diameter. Closed manifold, genus84. Separate scale coupon50x10.')


if __name__=='__main__':main()
