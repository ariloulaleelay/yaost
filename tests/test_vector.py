from yaost.vector import Vector


def test_translate():
    v = Vector(0, 0, 0)

    vt = v.tx(1)
    assert (1, 0, 0) == (vt.x, vt.y, vt.z)

    vt = v.ty(1)
    assert (0, 1, 0) == (vt.x, vt.y, vt.z)

    vt = v.tz(1)
    assert (0, 0, 1) == (vt.x, vt.y, vt.z)

    vt = v.t(1, 2, 3)
    assert (1, 2, 3) == (vt.x, vt.y, vt.z)


def test_projection():
    for i in range(360):
        v = Vector(0, 0)
        pl = Vector(10, -10).rz(i * 0.1)
        pr = Vector(10, 10).rz(i * 0.1)

        for ll, r in ((pl, pr), (pr, pl)):
            projection = v.projection(ll, r)

            assert (ll - projection).norm <= (ll - v).norm
            assert (r - projection).norm <= (r - v).norm
            assert abs((v - projection).dot(ll - r)) < 10e-6
