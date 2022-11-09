# import pytest

from yaost.body import Cube
import yaost.context as ctx


def test_body_ctx():
    cube = Cube(1, 2, 3).t(ctx.body.y)
    assert 'translate([2,0,0])cube([1,2,3]);' == cube.to_scad()


def test_origin_ctx():
    cube = Cube(2, 2, 2).t(ctx.center)
    assert 'translate([-1,0,0])cube([2,2,2]);' == cube.to_scad()
