from math import pi, tan
from typing import Optional

from lazy import lazy

from yaost.base import BaseObject
from yaost.bbox import BBox
from yaost.util import full_arguments_line
from yaost.vector import Vector

__all__ = [
    'circle',
    'cube',
    'cylinder',
    'polygon',
    'polyhedron',
    'sphere',
    'square',
    'stl_model',
    'surface',
    'text_model',
]


class BaseBody(BaseObject):
    is_2d = False
    is_body = True


class Group(BaseBody):
    def __init__(
        self,
        child: BaseObject,
        label: Optional[str] = None,
    ):
        self.label = label
        self.bbox = child.bbox
        self.origin = child.origin
        self.child = child

    def to_scad(self) -> str:
        return self.child.to_scad()

    @property
    def is_2d(self):
        return self.child.is_2d


class Cube(BaseBody):
    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        label: Optional[str] = None,
    ):
        self.x = x
        self.y = y
        self.z = z
        self.origin = Vector(x / 2, y / 2, z / 2)
        self.bbox = BBox(Vector(), Vector(x, y, z))
        self.label = label

    def to_scad(self):
        return 'cube({});'.format(full_arguments_line([[self.x, self.y, self.z]]))


class Cylinder(BaseBody):
    def __init__(
        self,
        h: float = 0,
        d: Optional[float] = None,
        r: Optional[float] = None,
        d1: Optional[float] = None,
        d2: Optional[float] = None,
        r1: Optional[float] = None,
        r2: Optional[float] = None,
        fn: Optional[float] = None,
        label: Optional[str] = None,
    ):
        self._d = d
        self._r = r
        self._d1 = d1
        self._d2 = d2
        self._r1 = r1
        self._r2 = r2
        self._h = h
        self._fn = fn

        self.label = label
        self.origin = Vector(0, 0, h / 2)
        self.bbox = BBox(
            Vector(-self.R, -self.R, 0),
            Vector(self.R, self.R, h),
        )

    @lazy
    def r(self):
        return min(self.r1, self.r2)

    @lazy
    def d(self):
        return min(self.d1, self.d2)

    @lazy
    def R(self):
        return max(self.r1, self.r2)

    @lazy
    def D(self):
        return max(self.d1, self.d2)

    @lazy
    def r1(self):
        if self._r1 is not None:
            return self._r1
        if self._d1 is not None:
            return self._d1 / 2
        if self._r is not None:
            return self._r
        if self._d is not None:
            return self._d / 2
        raise RuntimeError('All parameters are undefined')

    @lazy
    def r2(self):
        if self._r2 is not None:
            return self._r2
        if self._d2 is not None:
            return self._d2 / 2
        if self._r is not None:
            return self._r
        if self._d is not None:
            return self._d / 2
        raise RuntimeError('All parameters are undefined')

    @lazy
    def d1(self):
        if self._d1 is not None:
            return self._d1
        if self._r1 is not None:
            return self._r1 * 2
        if self._r is not None:
            return self._r * 2
        if self._d is not None:
            return self._d
        raise RuntimeError('All parameters are undefined')

    @lazy
    def d2(self):
        if self._d2 is not None:
            return self._d2
        if self._r2 is not None:
            return self._r2 * 2
        if self._r is not None:
            return self._r * 2
        if self._d is not None:
            return self._d
        raise RuntimeError('All parameters are undefined')

    @lazy
    def h(self):
        return self._h

    def to_scad(self):
        return 'cylinder({});'.format(
            full_arguments_line(
                (),
                {
                    'd': self._d,
                    'r': self._r,
                    'r1': self._r1,
                    'r2': self._r2,
                    'd1': self._d1,
                    'd2': self._d2,
                    'h': self._h,
                    '$fn': self._fn,
                },
            )
        )


class GenericBody(BaseBody):
    def __init__(
        self,
        name: str,
        *args,
        label: Optional[str] = None,
        **kwargs,
    ):
        self._args = args
        self._kwargs = kwargs
        self._name = name

        self.origin = Vector()
        self.bbox = BBox()

    def to_scad(self):
        return '{}({});'.format(
            self._name,
            full_arguments_line(self._args, self._kwargs),
        )


def cube(
    x: float = 1,
    y: float = 0,
    z: float = 0,
    r: float = 0,
    chamfer_top: float = 0,
    chamfer_bottom: float = 0,
    label: Optional[str] = None,
) -> Cube:
    from yaost.transformation import Hull

    if not y:
        y = x
    if not z:
        z = x

    assert r * 2 <= min(x, y)

    simple_cube = Cube(x, y, z, label=label)
    if not r:
        return simple_cube

    if chamfer_top < 0:
        pillar_chamfer_top = 0
    else:
        pillar_chamfer_top = chamfer_top

    if chamfer_bottom < 0:
        pillar_chamfer_bottom = 0
    else:
        pillar_chamfer_bottom = chamfer_bottom

    pillar = cylinder(
        r=r,
        h=z,
        chamfer_top=pillar_chamfer_top,
        chamfer_bottom=pillar_chamfer_bottom,
    ).t(r, r)
    result = Hull(
        [
            pillar,
            pillar.t(x - 2 * r),
            pillar.t(x - 2 * r, y - 2 * r),
            pillar.t(0, y - 2 * r),
        ]
    )

    if chamfer_top < 0:
        top_cap = cylinder(
            d1=r * 2,
            d2=r * 2 - chamfer_top * 2,
            h=-chamfer_top,
        ).t(
            r,
            r,
            z + chamfer_top,
        )
        result += Hull(
            [
                top_cap,
                top_cap.t(x - 2 * r),
                top_cap.t(x - 2 * r, y - 2 * r),
                top_cap.t(0, y - 2 * r),
            ]
        )

    if chamfer_bottom < 0:
        bottom_cap = cylinder(
            d1=r * 2 - chamfer_bottom * 2,
            d2=r * 2,
            h=-chamfer_bottom,
        ).t(
            r,
            r,
            0,
        )
        result += Hull(
            [
                bottom_cap,
                bottom_cap.t(x - 2 * r),
                bottom_cap.t(x - 2 * r, y - 2 * r),
                bottom_cap.t(0, y - 2 * r),
            ]
        )

    result.origin = simple_cube.origin
    result.bbox = simple_cube.bbox
    result.is_body = True
    result.label = label
    result.x = x
    result.y = y
    result.z = z
    return result


def cylinder(
    h: float = 0,
    h_angle: float = 0,
    d: Optional[float] = None,
    r: Optional[float] = None,
    d1: Optional[float] = None,
    d2: Optional[float] = None,
    r1: Optional[float] = None,
    r2: Optional[float] = None,
    fn: Optional[float] = None,
    chamfer_top: float = 0,
    chamfer_bottom: float = 0,
    label: Optional[str] = None,
) -> BaseBody:
    from yaost.transformation import Hull

    if not h and h_angle and ((d1 and d2) or (r1 and r2)):
        if d1 and d2:
            h = abs(d2 - d1) / 2 * tan(h_angle * pi / 180)
        elif r1 and r2:
            h = abs(r1 - r2) / 2 * tan(h_angle * pi / 180)

    simple_cylinder = Cylinder(
        h=h,
        d=d,
        r=r,
        d1=d1,
        d2=d2,
        r1=r1,
        r2=r2,
        fn=fn,
        label=label,
    )
    if not chamfer_top and not chamfer_bottom:
        return simple_cylinder

    bottom_cap = Cylinder(d=simple_cylinder.d1, h=min(0.0001, h / 2), fn=fn)
    top_cap = Cylinder(d=simple_cylinder.d2, h=min(0.0001, h / 2), fn=fn).tz(h - min(0.0001, h / 2))

    result = simple_cylinder
    if chamfer_bottom:
        bottom = Cylinder(
            d1=simple_cylinder.d1 - chamfer_bottom * 2,
            d2=simple_cylinder.d1,
            h=abs(chamfer_bottom),
            fn=fn,
        )
    else:
        bottom = bottom_cap

    if chamfer_top:
        top = Cylinder(
            d1=simple_cylinder.d2,
            d2=simple_cylinder.d2 - chamfer_top * 2,
            h=abs(chamfer_top),
            fn=fn,
        ).tz(h - abs(chamfer_top))
    else:
        top = top_cap

    if chamfer_top >= 0 and chamfer_bottom >= 0:
        result = Hull([top, bottom], label=label)
    elif chamfer_top < 0 and chamfer_bottom >= 0:
        result = Hull([top_cap, bottom], label=label)
        result += top

    elif chamfer_top >= 0 and chamfer_bottom < 0:
        result = Hull([top, bottom_cap], label=label)
        result += bottom
    elif chamfer_top < 0 and chamfer_bottom < 0:
        result = Hull([top_cap, bottom_cap], label=label)
        result += bottom
        result += top
    else:
        raise Exception('Unhandled chamfers combination, this should not happen')

    result.origin = simple_cylinder.origin
    result.bbox = simple_cylinder.bbox
    result.is_body = True
    result.r = simple_cylinder.r
    result.R = simple_cylinder.R
    result.d = simple_cylinder.d
    result.D = simple_cylinder.D
    result.h = simple_cylinder.h
    return result


def sphere(
    d: Optional[float] = None,
    r: Optional[float] = None,
    fn: Optional[float] = None,
    label: Optional[str] = None,
):
    kwargs = {}
    if d is not None:
        kwargs['d'] = d
        r = d / 2
    elif r is not None:
        kwargs['r'] = r
        d = r * 2
    else:
        raise RuntimeError('Please provide d or r for shpere')

    if fn is not None:
        kwargs['fn'] = fn

    if label is not None:
        kwargs['label'] = label

    result = GenericBody('sphere', **kwargs)
    result.origin = Vector()
    result.r = r
    result.d = d
    result.bbox = BBox(
        Vector(-r, -r, -r),
        Vector(r, r, r),
    )
    return result


def polygon(points, paths=None, **kwargs):
    if paths is not None:
        kwargs['paths'] = paths
    tmp = []
    for p in points:
        if isinstance(p, Vector):
            tmp.append([p.x, p.y])
        else:
            tmp.append(p)
    points = tmp
    result = GenericBody('polygon', points, **kwargs)
    result.is_2d = True
    return result


def polyhedron(points, faces=None, **kwargs):
    if faces is not None:
        kwargs['faces'] = faces
    return GenericBody('polyhedron', points, **kwargs)


def circle(*args, **kwargs):
    result = GenericBody('circle', *args, **kwargs)
    result.is_2d = True
    return result


def square(*args, **kwargs):
    result = GenericBody('square', *args, **kwargs)
    result.is_2d = True
    return result


# def sector(d=None, d1=None, d2=None, h=None, a=None, fn=None):
#     if d is not None:
#         d1 = d2 = d
#     if fn is None:
#         fn = 64
#     assert(d1 is not None and d2 is not None and h is not None and a is not None)
#     assert(d1 > 0 and d2 > 0 and h > 0 and a > 0 and fn > 0)
#     bottom_points = [[0, 0, 0]]
#     top_points = [[0, 0, h]]
#     for i in range(fn + 1):
#         angle = float(i) * a / fn
#         angle_rad = angle * pi / 180
#         x = d1 / 2 * cos(angle_rad)
#         y = d1 / 2 * sin(angle_rad)
#         bottom_points.append([x, y, 0])
#
#         x = d2 / 2 * cos(angle_rad)
#         y = d2 / 2 * sin(angle_rad)
#         top_points.append([x, y, h])
#
#     faces = []
#     points = bottom_points + top_points
#     top_start = len(bottom_points)
#     for i in range(fn):
#         bottom_idx = 1 + i
#         top_idx = top_start + 1 + i
#         faces.append([top_start, top_idx, top_idx + 1])
#         faces.append([0, bottom_idx + 1, bottom_idx])
#
#         faces.append([bottom_idx, bottom_idx + 1, top_idx + 1])
#         faces.append([top_idx + 1, top_idx, bottom_idx])
#
#     faces.append([0, 1, top_start + 1, top_start])
#     faces.append([0, top_start, top_start + fn + 1, fn + 1])
#     return polyhedron(points, [reversed(f) for f in faces], convexity=2)


def stl_model(file=None, convexity=10, **kwargs):
    kwargs = dict(kwargs)
    kwargs['file'] = file
    return GenericBody('import', convexity=convexity, **kwargs)


def surface(file=None, convexity=10, **kwargs):
    kwargs = dict(kwargs)
    kwargs['file'] = file
    return GenericBody('surface', convexity=convexity, **kwargs)


def text_model(txt, size=10, halign='left', valign='baseline', **kwargs):
    return GenericBody('text', txt, size=size, halign=halign, valign=valign, **kwargs)
