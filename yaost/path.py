# coding: utf8

from math import acos, pi, sqrt

from .base import Node
from .vector import Vector


def point_orientation(a, b, c):
    """Returns the orientation of the triangle a, b, c.

    Return True if a,b,c are oriented clock-wise.
    """
    return (b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y) >= 0


def line_intersection(a, b, c, d):
    a1 = b.y - a.y
    b1 = a.x - b.x
    c1 = a1 * a.x + b1 * a.y

    a2 = d.y - c.y
    b2 = c.x - d.x
    c2 = a2 * c.x + b2 * c.y

    dt = a1 * b2 - a2 * b1
    if dt == 0:
        return (c + d) / 2
    x = (b2 * c1 - b1 * c2) / dt
    y = (a1 * c2 - a2 * c1) / dt
    return Vector(x, y)


class Path(object):

    def __init__(self, points):
        self.points = []
        for p in points:
            if isinstance(p, list):
                p = Vector(*p)
            assert isinstance(p, Vector), 'Point should be vector or [x, y, z] list'
            self.points.append(p)

    @classmethod
    def _sort_ccw(cls, points):
        return points

    def polygon(self, convexity=2):
        return Node('polygon', None, [p.as_array_2d for p in self.points], convexity=convexity)

    def _triples(self):
        points = self._sort_ccw(self.points)
        total = len(points)
        for i in range(total):
            yield points[i], points[(i + 1) % total], points[(i + 2) % total]

    def offset(self, r=0, fn=16, use_z=False):
        # TODO evaluate fn wisely
        result = []
        for p, c, n in self._triples():
            is_convex = point_orientation(p, c, n)
            if use_z:
                r = c.z

            if is_convex == (r < 0):
                b = ((p - c).normed + (n - c).normed).normed
                bcos = (n - c).normed.dot(b)
                bsin = sqrt(1 - bcos ** 2)
                b = b * r / bsin
                result.append(b + c)
            else:
                unit_normal = (c - p).normal.normed
                unit_normal2 = (n - c).normal.normed

                n_prime = c - unit_normal * r
                n_prime2 = c - unit_normal2 * r

                angle = acos((n_prime - c).normed.dot((n_prime2 - c).normed))
                for i in range(fn + 1):
                    alpha = float(i) / fn
                    result.append(
                        (n_prime - c).rz(alpha * angle * 180 / pi) + c
                    )
        return Path(result)

    def round_corners(self, r=0, fn=16):
        # TODO evaluate fn wisely
        if r <= 0:
            return self
        result = []

        for p, c, n in self._triples():
            p_normal = (c - p).normal.normed * r
            n_normal = (n - c).normal.normed * r

            bisect = ((p - c).normed + (n - c).normed).normed
            bcos = (n - c).normed.dot(bisect)
            bsin = sqrt(1 - bcos ** 2)
            bisect = bisect * r / bsin

            center = c + bisect

            is_convex = point_orientation(p, c, n)

            angle = acos(p_normal.normed.dot(n_normal.normed))
            # result.append(center)
            for i in range(fn + 1):
                alpha = float(i) / fn
                if is_convex:
                    result.append(center - p_normal.rz(alpha * angle * 180 / pi))
                else:
                    result.append(center + p_normal.rz(-alpha * angle * 180 / pi))
        return Path(result)

    def translate(self, x=0, y=0, z=0):
        return Path([p.translate(x, y, z) for p in self.points])

    def tx(self, x):
        return self.translate(x=x)

    def ty(self, y):
        return self.translate(y=y)

    def tz(self, z):
        return self.translate(z=z)

    def extrude(self, *args, **kwargs):
        return self.polygon().extrude(*args, **kwargs)


def stitch_slices(slices, convexity=10):
    slice_count = len(slices)
    points_per_slice = len(slices[0].points)
    z0 = slices[0].points[0].z
    z1 = slices[-1].points[0].z

    points = []
    faces = []
    # TODO add assertion for all data (flat, z increasing)
    for s in slices:
        assert len(s.points) == points_per_slice, 'Slices should be same size'
        for p in s.points:
            points.append(p.as_array)

    points.append([0, 0, z0])
    points.append([0, 0, z1])

    z0idx = len(points) - 2
    z1idx = len(points) - 1

    for i in range(points_per_slice):
        faces.append([z0idx, (i + 1) % points_per_slice, i])
        faces.append([
            z1idx,
            points_per_slice * (slice_count - 1) + ((i - 1) % points_per_slice),
            points_per_slice * (slice_count - 1) + i,
        ])

    for layer in range(slice_count - 1):
        for i in range(points_per_slice):
            faces.append([
                points_per_slice * layer + i,
                points_per_slice * layer + (i + 1) % points_per_slice,
                points_per_slice * (layer + 1) + i,
            ])
            faces.append([
                points_per_slice * (layer + 1) + i,
                points_per_slice * layer + (i + 1) % points_per_slice,
                points_per_slice * (layer + 1) + (i + 1) % points_per_slice,
            ])

    return Node('polyhedron', None, points=points, faces=faces, convexity=convexity)


def blend_polar(a, b, alpha):
    points = []
    for p in a.points:
        points.append((p.alpha, p, None))
    for p in b.points:
        points.append((p.alpha, None, p))
    points.sort(key=lambda x: x[0])

    result = []

    def _nearest(points, i, idx):
        j = i
        pl = None
        while pl is None:
            pl = points[j][idx]
            j = (j - 1) % len(points)

        j = i
        pr = None
        while pr is None:
            pr = points[j][idx]
            j = (j + 1) % len(points)
        return pl, pr

    def _intersection(a, b, c, d):
        a1 = b.y - a.y
        b1 = a.x - b.x
        c1 = a1 * a.x + b1 * a.y

        a2 = d.y - c.y
        b2 = c.x - d.x
        c2 = a2 * c.x + b2 * c.y

        dt = a1 * b2 - a2 * b1
        if dt == 0:
            return (c + d) / 2
        x = (b2 * c1 - b1 * c2) / dt
        y = (a1 * c2 - a2 * c1) / dt
        return Vector(x, y)

    result = []
    for i, (angle, p1, p2) in enumerate(points):
        if p1 is not None:
            pl, pr = _nearest(points, i, 2)
            prj = _intersection(Vector(), p1 * 10000, pl, pr)
            x = p1.x * (1.0 - alpha) + prj.x * alpha
            y = p1.y * (1.0 - alpha) + prj.y * alpha
            z = p1.z * (1.0 - alpha) + (pl.z + pr.z) * 0.5 * alpha
        elif p2 is not None:
            pl, pr = _nearest(points, i, 1)
            prj = _intersection(Vector(), p2 * 10000, pl, pr)
            x = p2.x * alpha + prj.x * (1.0 - alpha)
            y = p2.y * alpha + prj.y * (1.0 - alpha)
            z = p2.z * alpha + (pl.z + pr.z) * 0.5 * (1.0 - alpha)

        result.append(Vector(x, y, z))

    return Path(result)


def extrude_blend_polar(path1, path2, h=1, fn=16):
    slices = []
    for i in range(fn + 1):
        alpha = float(i) / fn
        z = h * alpha
        slices.append(blend_polar(path1, path2, alpha).tz(z))
    return stitch_slices(slices)
