#!/usr/bin/env python3
"""Build a routed candidate for the owner's confirmed F pitch.

Never scales a footprint or pad. Existing component banks move rigidly, while
only the empty X corridors between banks widen. Copper segments are split at
every mapping breakpoint, preserving the actual mapped route instead of drawing
a shortcut. The X map is monotonic with slope at least one: represented centre
distances do not shrink. Native DRC and physical drill checks must still pass.
No rule, track width, drill, layer or via process is relaxed.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shutil

import pcbnew as k
import wx

B2 = Path(__file__).resolve().parents[1]
CAD = B2 / 'kicad'
SOURCE_SHA = '90018f786599e140bdc7ed6a75be65f574c2691c98f3b2d91a7383906dbe0b04'
DELTA = 175000


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path,
                        default=B2 / 'manufacturing/B2_review/source/house-rules-main-B2.kicad_pcb')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    wx.Log.EnableLogging(False)
    app = wx.App(False)
    source = args.source.resolve()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA
    assert args.output.resolve() != source.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    board = k.LoadBoard(str(source))
    origin = board.GetDesignSettings().GetAuxOrigin()

    banks = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith('J'):
            continue  # Single-pad wire lands need no rigid multi-pad interval.
        bank = (int(ref[2:])-1)*2 if ref.startswith('DS') else round(Fraction(fp.GetX()-origin.x-6100000,6350000))
        assert 0 <= bank <= 12
        row = banks.setdefault(bank, {'left': None, 'right': None, 'refs': []})
        row['refs'].append(ref)
        for pad in fp.Pads():
            bb = pad.GetBoundingBox()
            row['left'] = min(row['left'] if row['left'] is not None else bb.GetX(),bb.GetX())
            row['right'] = max(row['right'] if row['right'] is not None else bb.GetRight(),bb.GetRight())
    assert set(banks) == set(range(13))
    knots = []
    for index, row in sorted(banks.items()):
        shift = index * DELTA // 2
        row['shift_nm'] = shift
        if knots:
            assert knots[-1][0] < row['left'], 'Rigid component banks overlap in X'
            assert knots[-1][1] <= shift
        knots.extend([(row['left'],shift),(row['right'],shift)])

    def shift_at(x):
        if x <= knots[0][0]:
            return knots[0][1]
        for (left, dlo),(right, dhi) in zip(knots,knots[1:]):
            if left <= x <= right:
                return round(Fraction(dlo) + Fraction((x-left)*(dhi-dlo),right-left))
        return knots[-1][1]

    def mapped(point):
        return k.VECTOR2I(point.x+shift_at(point.x),point.y)

    original_tracks = len(board.GetTracks())
    inserted_segments = 0
    for item in list(board.GetTracks()):
        if isinstance(item, k.PCB_VIA):
            item.SetPosition(mapped(item.GetPosition()))
        else:
            assert not isinstance(item, k.PCB_ARC), 'Arc requires an explicit review'
            start, end = item.GetStart(),item.GetEnd()
            samples = [(Fraction(0),start),(Fraction(1),end)]
            if start.x != end.x:
                for x,shift in knots:
                    t = Fraction(x-start.x,end.x-start.x)
                    if 0 < t < 1:
                        y = round(Fraction(start.y)+t*(end.y-start.y))
                        samples.append((t,k.VECTOR2I(x,y)))
            points = [mapped(point) for t,point in sorted(samples,key=lambda row:row[0])]
            item.SetStart(points[0])
            item.SetEnd(points[1])
            for a,z in zip(points[1:],points[2:]):
                track = k.PCB_TRACK(board)
                track.SetStart(a);track.SetEnd(z);track.SetWidth(item.GetWidth())
                track.SetLayer(item.GetLayer());track.SetNet(item.GetNet())
                track.SetLocked(item.IsLocked());board.Add(track)
                inserted_segments += 1
    fp_shifts = {}
    for fp in board.GetFootprints():
        shift = shift_at(fp.GetX())
        fp_shifts[fp.GetReference()] = shift
        if not fp.GetReference().startswith('J'):
            for pad in fp.Pads():
                assert shift_at(pad.GetBoundingBox().GetX()) == shift
                assert shift_at(pad.GetBoundingBox().GetRight()) == shift
        fp.SetPosition(k.VECTOR2I(fp.GetX()+shift,fp.GetY()))
    edges = [d for d in board.GetDrawings() if d.GetLayer() == k.Edge_Cuts]
    assert len(edges) == 1 and isinstance(edges[0], k.PCB_SHAPE)
    assert edges[0].GetShape() == k.SHAPE_T_RECT
    edge = edges[0]
    assert edge.GetStart() == origin
    assert edge.GetEnd() == k.VECTOR2I(origin.x+88400000, origin.y+17300000)
    edge.SetEnd(k.VECTOR2I(origin.x+89450000, origin.y+17300000))
    for drawing in board.GetDrawings():
        if isinstance(drawing, k.PCB_TEXT) and drawing.GetText() != 'HOUSE RULES B2':
            point = drawing.GetPosition()
            drawing.SetPosition(mapped(point))
    for zone in board.Zones():
        outline = zone.Outline()
        for i in range(outline.OutlineCount()):
            chain = outline.Outline(i)
            for j in range(chain.PointCount()):
                point = chain.CPoint(j)
                if point.x > origin.x + 88000000:
                    chain.SetPoint(j, k.VECTOR2I(point.x + 1050000, point.y))
    board.BuildConnectivity()
    k.ZONE_FILLER(board).Fill(board.Zones())
    k.SaveBoard(str(args.output), board)
    for extension in ('.kicad_pro', '.kicad_dru', '.kicad_sch'):
        shutil.copy2(source.with_suffix(extension), args.output.with_suffix(extension))
    shutil.copy2(CAD / 'fp-lib-table', args.output.parent / 'fp-lib-table')
    shutil.copytree(CAD / 'footprints', args.output.parent / 'footprints', dirs_exist_ok=True)
    report = {'status': 'candidate only; native DRC and independent audit required',
              'source_sha256': SOURCE_SHA, 'pitch_nm': 12875000,
              'per_join_increment_nm': DELTA, 'outline_mm': [89.45, 17.3],
              'rigid_footprint_shift_nm': fp_shifts,
              'rigid_component_banks': banks,
              'mapping_knots_absolute_X_nm_and_shift_nm': knots,
              'mapping_slope_at_least_one': True,
              'original_copper_objects': original_tracks,
              'inserted_polyline_segments': inserted_segments,
              'footprints_scaled': False,
              'candidate_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}
    args.output.with_suffix('.pitch-update.json').write_text(json.dumps(report, indent=2)+'\n')
    print(args.output)


if __name__ == '__main__':
    main()
