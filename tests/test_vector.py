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
