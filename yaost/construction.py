# coding: utf-8
from math import pi, tan, cos, sin
from .local_logging import get_logger
from .scad import cylinder, polyhedron

logger = get_logger(__name__)

# nuts = lambda: None  # noqa
#
# nuts.m4.set(
#     height=3.2,
#     width=7.,
#     diameter=8.,
#     internal_diameter=3.95,
#     screw_diameter=4.1,
# )


def deg2rad(deg):
    return deg * pi / 180


def rounded_box(x, y, z, r=5, fn=32):
    result = cylinder(r=r, h=z, fn=fn).t(r, r, 0).mx(x / 2, clone=True).my(y / 2, clone=True).hull()
    result.com.x = x / 2
    result.com.y = y / 2
    result.com.z = z / 2
    result.size.x = x
    result.size.y = y
    result.size.z = z
    return result


def _thread(length, pitch, diameter, fn=32, tolerance=0, theta=60):
    segments_per_revolution = fn

    if length < pitch / 2:
        raise Exception('Length is too small')

    # internal stuff starts here
    D = diameter
    P = pitch
    H = P / (2 * tan(theta / 2 * pi / 180))

    # TODO change radiuses to match right dimension
    r = (D - H * 5 / 8) / 2
    R = D / 2

    # shift for internal helix
    s = P / 4
    S = P / 8

    # Four points for helixes
    h1 = []
    h2 = []
    H1 = []
    H2 = []

    L = length + P * 2
    revolutions = L / P
    segments = int(revolutions * segments_per_revolution)
    for segment in range(segments + 1):
        angle = segment / segments_per_revolution * pi * 2
        height = segment / segments * L - P

        x, y = (r + tolerance) * cos(angle), (r + tolerance) * sin(angle)
        X, Y = (R + tolerance) * cos(angle), (R + tolerance) * sin(angle)

        h1.append([x, y, height - s / 2])
        h2.append([x, y, height + s / 2])

        H1.append([X, Y, height - S / 2 + P / 2])
        H2.append([X, Y, height + S / 2 + P / 2])

    points = h1 + h2 + H1 + H2
    points.append([0, 0, -P])
    points.append([0, 0, length + P])

    faces = []
    spr = segments_per_revolution
    stot = segments + 1
    for i in range(stot - 1):
        for stot_factor in [0, 1, 2]:
            # current index
            ii = i + stot * stot_factor

            # internal helix line
            faces.append([ii, ii + 1, ii + stot])
            faces.append([ii + 1, ii + stot + 1, ii + stot])

        # external to next internal helix
        if i < stot - spr - 1:
            ii = i + stot * 3
            faces.append([ii, ii + 1, i + spr])
            faces.append([ii + 1, i + spr + 1, i + spr])

    bottom_idx = len(points) - 2
    for i in range(spr):
        faces.append([i + 1, i, bottom_idx])
    for i in range(3):
        faces.append([bottom_idx, i * stot, stot * (i + 1)])
    faces.append([bottom_idx, stot * 3, spr])

    top_idx = len(points) - 1
    for i in range(spr):
        faces.append([stot * 4 - 1 - i - 1, stot * 4 - 1 - i, top_idx])

    lst_idx = stot * 4 - 1
    for i in range(3):
        faces.append([top_idx, lst_idx - stot * i, lst_idx - stot * (i + 1)])
    faces.append([top_idx, lst_idx - stot * 3, lst_idx - spr])

    faces = [reversed(f) for f in faces]
    result = polyhedron(
        points=points,
        faces=faces,
        convexity=revolutions,
    )

    result = result.intersection(cylinder(d=(R + abs(tolerance * 2)) * 2, h=length))
    result.pitch = pitch
    result.D = R * 2
    result.d = r * 2
    return result


def _diameter_to_pitch(diameter):
    # TODO faster search
    table = [
        [0, 0.25],
        [1.4, 0.3],
        [1.6, 0.35],
        [2, 0.4],
        [2.2, 0.45],
        [3, 0.5],
        [3.5, 0.6],
        [4, 0.7],
        [5, 0.8],
        [6, 1],
        [8, 1.25],
        [10, 1.5],
        [12, 1.75],
        [14, 2],
        [18, 2.5],
        [24, 3],
        [30, 3.5],
        [36, 4],
        [42, 4.5],
        [48, 5],
        [56, 5.5],
        [64, 6],
        [10000, 6],
    ]
    prev_pitch = 0.25
    for d, pitch in table:
        if diameter == d:
            return pitch
        if diameter < d:
            return prev_pitch
        prev_pitch = pitch


def _pitch_to_tolerance(pitch):
    return pitch * 0.0866 * 7 / 8 * 0.5 * 0.5  # 2.5% of H


def m_thread_external(d=4, h=10, fn=64):
    pitch = _diameter_to_pitch(d)
    tolerance = -_pitch_to_tolerance(pitch)
    result = _thread(h, pitch, d, tolerance=tolerance, fn=fn)
    return result


def m_thread_internal_hole(d=4, h=10, fn=64):
    pitch = _diameter_to_pitch(d)
    tolerance = _pitch_to_tolerance(pitch)
    result = _thread(h, pitch, d, tolerance=tolerance, fn=fn)
    return result
