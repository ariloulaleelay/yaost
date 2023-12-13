from typing import Optional
from lazy import lazy

from yaost.vector import Vector
from yaost.bbox import BBox
from yaost.base import BaseObject
from yaost.util import full_arguments_line


__all__ = [
    'cube',
    'cylinder',
    'sphere',
    'polygon',
    'polyhedron',
    'stl_model',
    'text_model',
    'circle',
    'square',
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
        return 'cube({});'.format(
            full_arguments_line([[self.x, self.y, self.z]])
        )


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
                }
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

    pillar = cylinder(
        r=r,
        h=z,
        chamfer_top=chamfer_top,
        chamfer_bottom=chamfer_bottom,
    ).t(
        r, r
    )
    result = Hull([
        pillar,
        pillar.t(x - 2 * r),
        pillar.t(x - 2 * r, y - 2 * r),
        pillar.t(0, y - 2 * r),
    ]).hull()
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
    d: Optional[float] = None,
    r: Optional[float] = None,
    d1: Optional[float] = None,
    d2: Optional[float] = None,
    r1: Optional[float] = None,
    r2: Optional[float] = None,
    fn: Optional[float] = None,
    chamfer_top: Optional[float] = 0,
    chamfer_bottom: Optional[float] = 0,
    label: Optional[str] = None,
) -> BaseBody:
    from yaost.transformation import Hull

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

    result = simple_cylinder
    if chamfer_bottom:
        bottom = Cylinder(
            d1=simple_cylinder.d1 - chamfer_bottom * 2,
            d2=simple_cylinder.d1,
            h=chamfer_bottom
        )
    else:
        bottom = Cylinder(
            d=simple_cylinder.d1,
            h=0.0001
        )

    if chamfer_top:
        top = Cylinder(
            d1=simple_cylinder.d2,
            d2=simple_cylinder.d2 - chamfer_top * 2,
            h=chamfer_top
        ).tz(h - chamfer_top)
    else:
        top = Cylinder(
            d=simple_cylinder.d1,
            h=0.0001
        ).tz(h - 0.0001)

    result = Hull([top, bottom])

    result.origin = simple_cylinder.origin
    result.bbox = simple_cylinder.bbox
    result.is_body = True
    return result


def sphere(*args, **kwargs):
    return GenericBody('sphere', *args, **kwargs)


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


def stl_model(filename, convexity=10):
    return GenericBody('import', filename, convexity=convexity)


def text_model(txt, size=10, halign='left', valign='baseline', **kwargs):
    return GenericBody('text', txt, size=size, halign=halign, valign=valign, **kwargs)
