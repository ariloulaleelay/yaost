from yaost import (
    cube, polyhedron, cylinder,
    get_logger
)
from math import pi, cos, sin, tan


logger = get_logger(__name__)


def diameter_to_pitch(diameter):
    table = (
        (1.6, 0.35),
        (1.8, 0.35),
        (2, 0.40),
        (2.2, 0.45),
        (2.5, 0.45),
        (3, 0.50),
        (3.5, 0.60),
        (4, 0.70),
        (4.5, 0.75),
        (5, 0.80),
        (6, 1.00),
        (7, 1.00),
        (8, 1.25),
        (10, 1.50),
        (12, 1.75),
        (14, 2.00),
        (16, 2.00),
        (18, 2.50),
        (20, 2.50),
        (22, 2.50),
        (24, 3.00),
        (27, 3.00),
        (30, 3.50),
        (33, 3.50),
        (36, 4.00),
        (39, 4.00),
        (42, 4.50),
        (45, 4.50),
        (48, 5.00),
        (52, 5.00),
        (56, 5.50),
        (60, 5.50),
        (64, 6.00),
        (68, 6.00),
    )
    for table_diameter, table_pitch in table:
        if diameter <= table_diameter:
            return table_pitch
    return table[-1][1]


def triangle_profile(
    diameter,
    pitch,
    clearance=0,
    theta=60,
    top_cut=1 / 8,
    bottom_cut=1 / 4
):
    """
        ISO metric thread profile
        https://en.wikipedia.org/wiki/ISO_metric_screw_thread
    """

    tan_half_theta = tan(theta / 2 * pi / 180)
    H = pitch / (2 * tan_half_theta)

    r_maj = diameter / 2
    r_min = r_maj + H * (bottom_cut - 7 / 8) + clearance
    r_max = r_maj + H * (1 / 8 - top_cut) + clearance
    dp_low = H * bottom_cut * tan_half_theta
    dp_high = H * top_cut * tan_half_theta

    points = []
    if dp_low:
        points.append((r_min, -dp_low))
        points.append((r_min, dp_low))
    else:
        points.append((r_min, 0))

    if dp_high:
        points.append((r_max, pitch / 2 - dp_high))
        points.append((r_max, pitch / 2 + dp_high))
    else:
        points.append((r_max, pitch / 2))

    points.append((r_min, pitch - dp_low))
    return points


def profile_helix(
    profile, length, fn=32, er1=0, er2=0, direction=1,
    chamfer_top=0,
    chamfer_bottom=0,
):
    pitch = profile[-1][1] - profile[0][1]
    assert profile[0][0] == profile[-1][0], 'Starting and finishing points should match in x'
    profile = profile[:-1]

    assert pitch > 0, 'Pitch should be greater than zero'
    revolutions = (length + 4 * pitch) / pitch
    segments = int(fn * revolutions)
    assert segments > 2, 'Length is too small or pitch is too high'
    points = [[] for _ in profile]
    max_r = None
    for idx, (pr, pz) in enumerate(profile):
        for segment in range(segments + 1):
            alpha = segment / segments
            theta = alpha * revolutions * 2 * pi
            if segment <= fn:
                beta = segment / fn
                vr = beta * pr + (1 - beta) * profile[0][0]
            elif segment >= segments - fn:
                beta = (segments - segment) / fn
                vr = beta * pr + (1 - beta) * profile[0][0]
            else:
                vr = pr
            r = vr + (er2 * alpha + er1 * (1. - alpha))
            if max_r is None or r > max_r:
                max_r = r
            h = (length + 4 * pitch) * alpha - 2 * pitch
            points[idx].append((
                r * sin(theta),
                - r * cos(theta) * direction,
                h + pz
            ))
    chunks = []
    vectors = []
    faces = []

    for row in points:
        for x, y, z in row:
            chunks.append(cube(1, 1, 1).t(x, y, z))
            vectors.append((x, y, z))

    vectors.append((0, 0, points[0][0][2]))
    bottom_point_idx = len(vectors) - 1

    vectors.append((0, 0, points[-1][-1][2]))
    top_point_idx = len(vectors) - 1

    for row_idx in range(len(points)):
        for point_idx in range(segments):
            p00 = row_idx * (segments + 1) + point_idx
            p01 = row_idx * (segments + 1) + point_idx + 1

            if row_idx < len(points) - 1:
                p10 = (row_idx + 1) * (segments + 1) + point_idx
                p11 = (row_idx + 1) * (segments + 1) + point_idx + 1
            elif point_idx + fn < segments:
                p10 = point_idx + fn
                p11 = point_idx + 1 + fn
            else:
                continue

            faces.append((p00, p10, p01))
            faces.append((p01, p10, p11))

    # bottom seal
    for i in range(fn):
        faces.append((i, i + 1, bottom_point_idx))

    for idx in range(len(profile)):
        p0 = idx * (segments + 1)
        if idx == len(profile) - 1:
            p1 = fn
        else:
            p1 = (idx + 1) * (segments + 1)
        faces.append((bottom_point_idx, p1, p0))

    # top seal
    top_count_from = len(vectors) - 3 - fn
    for i in range(fn):
        i += top_count_from
        faces.append((i + 1, i, top_point_idx))

    for idx in range(len(profile)):
        p0 = len(vectors) - 3 - idx * (segments + 1)
        if idx == len(profile) - 1:
            p1 = len(vectors) - 3 - fn
        else:
            p1 = len(vectors) - 3 - (idx + 1) * (segments + 1)
        faces.append((top_point_idx, p1, p0))

    if direction < 0:
        faces = [(f1, f3, f2) for f1, f2, f3 in faces]

    result = polyhedron(
        points=vectors,
        faces=faces,
        convexity=revolutions * 1,
    )
    result = result.intersection(
        cylinder(
            d=max_r * 2 + 1, h=length,
            chamfer_top=chamfer_top,
            chamfer_bottom=chamfer_bottom,
        ) # .tz(profile[0][1])
    )
    return result


def external_thread(l=None, pitch=None, d=None, d1=None, d2=None, fn=64, clearance=0, theta=90):
    if d1 is None:
        d1 = d
    if d2 is None:
        d2 = d1
    if pitch is None:
        pitch = diameter_to_pitch(d1)

    profile = triangle_profile(
        d1 + clearance, pitch,
        theta=theta,
        bottom_cut=0
    )
    er2 = (d2 - d1) / 2 + clearance
    result = profile_helix(profile, l, fn=fn, er2=er2, direction=1)
    return result


def internal_thread(
    l=None,
    pitch=None,
    d=None,
    d1=None,
    d2=None,
    fn=64,
    clearance=0,
    theta=90,
    chamfer_top=False,
    chamfer_bottom=False,
    debug=False,
):
    if d1 is None:
        d1 = d
    if d2 is None:
        d2 = d1
    if pitch is None:
        pitch = diameter_to_pitch(d1)

    profile = triangle_profile(
        d1 + clearance, pitch,
        theta=theta,
        top_cut=0
    )
    er2 = (d2 - d1) / 2 + clearance
    result = profile_helix(profile, l, fn=fn, er2=er2, direction=1)
    origin = result.origin

    r_max = max([abs(x) for x, _ in profile]) + pitch / 4
    r_min = min([abs(x) for x, _ in profile])

    if debug:
        logger.debug(f'r_max {r_max} r_min {r_min} d_max {r_max * 2} d_min {r_min * 2}')

    chamfer = cylinder(
        d1=r_max * 2,
        d2=r_min * 2,
        h=pitch,
    )

    if chamfer_top:
        result += chamfer.mz(l / 2)

    if chamfer_bottom:
        result += chamfer

    result.origin = origin
    result.r_min = r_min
    result.d_min = r_min * 2
    result.r_max = r_max
    result.d_max = r_max * 2
    return result
