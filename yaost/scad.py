from math import cos, sin, pi
from .base import Node, DistributiveNode


def union(*args):
    return DistributiveNode('union', args)


def hull(*args):
    return DistributiveNode('hull', args)


def intersection(*args):
    return DistributiveNode('intersection', args)


def difference(x, y):
    return Node('difference', [x, y])


def cube(x=0, y=0, z=0):
    result = Node('cube', None, [x, y, z])
    result.x = x
    result.y = y
    result.z = z
    return result


def cylinder(*args, **kwargs):
    return Node('cylinder', None, *args, **kwargs)


def sphere(*args, **kwargs):
    return Node('sphere', None, *args, **kwargs)


def polygon(*args, **kwargs):
    return Node('polygon', None, *args, **kwargs)


def polyhedron(points, faces=None, **kwargs):
    if faces is not None:
        kwargs['faces'] = faces
    return Node('polyhedron', None, points, **kwargs)


def circle(*args, **kwargs):
    return Node('circle', None, *args, **kwargs)


def square(*args, **kwargs):
    return Node('square', None, *args, **kwargs)


def sector(d=None, d1=None, d2=None, h=None, a=None, fn=None):
    if d is not None:
        d1 = d2 = d
    if fn is None:
        fn = 64
    assert(d1 is not None and d2 is not None and h is not None and a is not None)
    assert(d1 > 0 and d2 > 0 and h > 0 and a > 0 and fn > 0)
    bottom_points = [[0, 0, 0]]
    top_points = [[0, 0, h]]
    for i in range(fn + 1):
        angle = float(i) * a / fn
        angle_rad = angle * pi / 180
        x = d1 / 2 * cos(angle_rad)
        y = d1 / 2 * sin(angle_rad)
        bottom_points.append([x, y, 0])

        x = d2 / 2 * cos(angle_rad)
        y = d2 / 2 * sin(angle_rad)
        top_points.append([x, y, h])

    faces = []
    points = bottom_points + top_points
    top_start = len(bottom_points)
    for i in range(fn):
        bottom_idx = 1 + i
        top_idx = top_start + 1 + i
        faces.append([top_start, top_idx, top_idx + 1])
        faces.append([0, bottom_idx + 1, bottom_idx])

        faces.append([bottom_idx, bottom_idx + 1, top_idx + 1])
        faces.append([top_idx + 1, top_idx, bottom_idx])

    faces.append([0, 1, top_start + 1, top_start])
    faces.append([0, top_start, top_start + fn + 1, fn + 1])
    return polyhedron(points, [reversed(f) for f in faces], convexity=2)


def stl_model(filename, convexity=10):
    return Node('import', None, filename, convexity=convexity)


def text_model(txt, size=10, halign='left', valign='baseline', **kwargs):
    return Node('text', None, txt, size=size, halign=halign, valign=valign, **kwargs)
