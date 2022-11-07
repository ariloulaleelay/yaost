# coding: utf-8
import logging
from math import pi, tan
try:
    from shapely.ops import unary_union
    from shapely import affinity, geometry
except ImportError:
    logging.getLogger(__name__).exception('You should install shapely to use gears module')

from . import scad

inf = 10000


def base_rack_trap(
    module,
    depth,
    pressure,
):
    pitch = pi * module
    dd = module * depth

    points = [
        [0, 0],
        [dd * tan(pressure * pi / 180), dd],
        [pitch / 4, dd]
    ]
    return points


def gear_profile(
    radius,
    module=2,
    addendum=1,
    dedendum=1.2,
    pressure=22,
    backlash=0,
    frames=32,
    shift=0,
    coupling_radius=None,
    coupling_factor=10,
    internal=False,
    hole=False,
    radius_small=None,
    external_radius=None,
):
    inf = radius * 10000
    if coupling_radius is None:
        coupling_radius = radius * coupling_factor
    pitch = module * pi
    points = base_rack_trap(module, dedendum, pressure)
    points = [(-x, -y) for x, y in reversed(points[1:])] + points
    points = [(x - pitch / 4, y) for x, y in points]
    points = points + [(-x, y) for x, y in reversed(points[:-1])]
    if backlash:
        points = [(x + backlash if x > 0 else x - backlash, y) for x, y in points]

    ad = addendum * module
    dd = dedendum * module
    diameter = abs(radius * 2)
    teeth_count = int(diameter / module + 0.5)
    assert abs(teeth_count * module - diameter) < 0.00001, "diameter and module should match"
    pitch_angle = module / diameter * 360
    coupling_pitch_angle = module / coupling_radius * 180

    tooth_polygon = geometry.Polygon(points)
    holes = []
    for i in range(-frames, frames + 1):
        alpha = float(i) / frames
        holes.append(
            affinity.rotate(
                affinity.rotate(
                    tooth_polygon,
                    -coupling_pitch_angle / 2 * alpha,
                    (0, -coupling_radius)
                ),
                -pitch_angle / 2 * alpha, (0, radius)
            )
        )
    holes = unary_union(holes).simplify(0.01)
    if isinstance(holes, geometry.MultiPolygon):
        best_hole = None
        for hole_ in holes.geoms:
            if best_hole is None or len(hole_.exterior.coords) > len(best_hole.exterior.coords):
                best_hole = hole_
        holes = best_hole
    coords = holes.exterior.coords
    tooth = scad.polygon(points=coords)
    if internal:
        tooth = tooth.my()
    tooth = tooth.ty(-radius - shift)

    holes = []
    for i in range(teeth_count):
        holes.append(tooth.rz(360 * i / teeth_count))
    teeth = scad.union(*holes).render()
    if hole:
        if internal:
            result = teeth + scad.circle(r=radius - ad)
        else:
            result = scad.circle(r=inf) - scad.circle(r=radius + ad) + teeth
    else:
        if internal:
            if external_radius is None:
                external_radius = radius + dd + 1
            result = scad.circle(r=external_radius) - teeth - scad.circle(r=radius - ad + shift)
        else:
            result = scad.circle(r=radius + ad + shift) - teeth
    return result.render()
