from math import pi, tan

from yaost import Vector, cylinder, get_logger, polyhedron

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
    diameter: float,
    pitch: float,
    clearance: float = 0,
    theta: float = 60,
    top_cut: float = 1 / 8,
    bottom_cut: float = 1 / 4,
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
    profile,
    length,
    fn=32,
    er1=0,
    er2=0,
    direction=1,
    bottom_diameter=None,
    bottom_height=0,
    top_diameter=None,
    top_height=0,
):
    pitch = profile[-1][1] - profile[0][1]
    assert profile[0][0] == profile[-1][0], 'Starting and finishing points should match in x'
    # profile = profile[:-1]

    assert pitch > 0, 'Pitch should be greater than zero'

    just_thread_length = length - bottom_height - top_height
    assert just_thread_length > 0, 'Thread length should be greater than zero'

    assert fn > 2

    revolutions = (just_thread_length + 4 * pitch) / pitch

    if bottom_height and not bottom_diameter:
        bottom_diameter = profile[0][0] + er1

    if top_height and not top_diameter:
        top_diameter = profile[0][0] + er2

    colrow_map = {}
    bottom_points = []
    top_points = []

    for angular_segment in range(fn):
        alpha = angular_segment / fn
        theta = alpha * 360

        z_idx = -1
        z_shift = alpha * pitch

        while profile[0][1] + z_idx * pitch <= length:
            for subrow_idx, (p1, p2) in enumerate(zip(profile, profile[1:])):
                r1_base, z1_base = p1
                r2_base, z2_base = p2

                z1 = z1_base + z_idx * pitch + z_shift
                z2 = z2_base + z_idx * pitch + z_shift

                if z1 > length - top_height:
                    continue
                if z2 < bottom_height:
                    continue

                alpha1 = z1 / length
                r1 = (er1 * (1.0 - alpha1) + er2 * alpha1) + r1_base

                alpha2 = z2 / length
                r2 = (er1 * (1.0 - alpha2) + er2 * alpha2) + r2_base

                if z1 >= bottom_height and z1 <= length - top_height:
                    point = Vector(r1, 0, z1).rz(theta)

                elif z1 < bottom_height and z2 >= bottom_height:
                    gamma = (bottom_height - z1) / (z2 - z1)
                    r = r1 * (1.0 - gamma) + r2 * gamma
                    point = Vector(r, 0, bottom_height).rz(theta)
                else:
                    continue

                point._col = angular_segment
                point._row = z_idx * (len(profile) - 1) + subrow_idx
                colrow_map[(point._col, point._row)] = point

                if point.z == bottom_height:
                    if bottom_diameter and bottom_height:
                        bottom_point = Vector(bottom_diameter / 2, 0).rz(theta)
                        bottom_point._col = point._col
                        bottom_point._row = point._row - 1
                        colrow_map[(bottom_point._col, bottom_point._row)] = bottom_point
                    else:
                        bottom_point = point

                    bottom_points.append(bottom_point)

                # add top extra point
                if z1 < length - top_height and z2 >= length - top_height:
                    gamma = ((length - top_height) - z1) / (z2 - z1)
                    r = r1 * (1.0 - gamma) + r2 * gamma
                    point = Vector(r, 0, length - top_height).rz(theta)

                    point._col = angular_segment
                    point._row = z_idx * (len(profile) - 1) + subrow_idx + 1
                    colrow_map[(point._col, point._row)] = point

                if point.z == length - top_height:
                    if top_diameter and top_height:
                        top_point = Vector(top_diameter / 2, 0, length).rz(theta)
                        top_point._col = point._col
                        top_point._row = point._row + 1
                        colrow_map[(top_point._col, top_point._row)] = top_point
                    else:
                        top_point = point
                    top_points.append(top_point)

            z_idx += 1

    faces = []

    for (col, row), point in colrow_map.items():
        if col < fn - 1:
            right_point = colrow_map.get((col + 1, row))
            top_point = colrow_map.get((col, row + 1))
            bottom_right_point = colrow_map.get((col + 1, row - 1))
        else:
            right_point = colrow_map.get((0, row + len(profile) - 1))
            top_point = colrow_map.get((col, row + 1))
            bottom_right_point = colrow_map.get((0, row + len(profile) - 2))

        if right_point is not None and top_point is not None:
            faces.append([point, top_point, right_point])

        if right_point is not None and bottom_right_point is not None:
            faces.append([point, right_point, bottom_right_point])

    faces.append([p for p in sorted(bottom_points, key=lambda x: x._col)])
    faces.append([p for p in sorted(top_points, key=lambda x: x._col, reverse=True)])

    result_points = []
    result_faces = []
    seen_points = {}
    for face in faces:
        result_face = []
        for p in face:
            key = (p._col, p._row)
            if key in seen_points:
                idx = seen_points[key]
            else:
                idx = len(seen_points)
                seen_points[key] = idx
                result_points.append(p)
            result_face.append(idx)
        result_faces.append(result_face)

    result = polyhedron(
        points=result_points,
        faces=result_faces,
        convexity=revolutions * 1,
    )
    result.length = length
    result.origin = Vector(0, 0, length / 2)
    result.r_max = max(r for r, _ in profile) + max(er1, er2)
    result.r_min = min(r for r, _ in profile) + min(er1, er2)
    result.d_max = result.r_max * 2
    result.d_min = result.r_min * 2
    return result


def external_thread(
    length=None,
    pitch=None,
    d=None,
    d1=None,
    d2=None,
    fn=64,
    clearance=0,
    theta=90,
    chamfer_top=0,
    chamfer_bottom=0,
    top_height=0,
    top_diameter=0,
    bottom_height=0,
    bottom_diameter=0,
):
    if d1 is None:
        d1 = d
    if d2 is None:
        d2 = d1
    if pitch is None:
        pitch = diameter_to_pitch(d1)

    profile = triangle_profile(d1 + clearance, pitch, theta=theta, bottom_cut=0)

    if chamfer_top:
        top_diameter = d2 + clearance + chamfer_top * 2
        top_height = abs(chamfer_top)

    if chamfer_bottom:
        bottom_diameter = d1 + clearance + chamfer_bottom * 2
        bottom_height = abs(chamfer_top)

    er2 = (d2 - d1) / 2
    result = profile_helix(
        profile,
        length,
        fn=fn,
        er2=er2,
        top_diameter=top_diameter,
        top_height=top_height,
        bottom_diameter=bottom_diameter,
        bottom_height=bottom_height,
    )
    return result


def internal_thread(
    length=None,
    pitch=None,
    d=None,
    d1=None,
    d2=None,
    fn=64,
    clearance=0,
    theta=90,
    chamfer_top=0,
    chamfer_bottom=0,
    top_height=0,
    top_diameter=0,
    bottom_height=0,
    bottom_diameter=0,
):
    if d1 is None:
        d1 = d
    if d2 is None:
        d2 = d1
    if pitch is None:
        pitch = diameter_to_pitch(d1)

    profile = triangle_profile(d1 + clearance, pitch, theta=theta, top_cut=0)
    er2 = (d2 - d1) / 2

    if chamfer_top:
        top_diameter = d2 + clearance + chamfer_top * 2
        top_height = abs(chamfer_top)

    if chamfer_bottom:
        bottom_diameter = d1 + clearance + chamfer_bottom * 2
        bottom_height = abs(chamfer_top)

    result = profile_helix(
        profile,
        length,
        fn=fn,
        er2=er2,
        top_diameter=top_diameter,
        top_height=top_height,
        bottom_diameter=bottom_diameter,
        bottom_height=bottom_height,
    )

    return result
