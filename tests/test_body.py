# import pytest

from yaost.body import Cylinder, Cube


def test_cube():
    cube = Cube(1, 1, 1)
    assert 'cube([1,1,1]);' == cube.to_scad()


def test_cube_params():
    cube = Cube(2, 4, 6)
    assert cube.origin.x == 1
    assert cube.origin.y == 2
    assert cube.origin.z == 3

    assert cube.x == 2
    assert cube.y == 4
    assert cube.z == 6


def test_cylinder():
    cylinder = Cylinder(d=2, h=1)
    assert 'cylinder(d=2,h=1);' == cylinder.to_scad()

    cylinder = Cylinder(r=1, h=2)
    assert 'cylinder(h=2,r=1);' == cylinder.to_scad()

    cylinder = Cylinder(r1=1, r2=2, h=3)
    assert 'cylinder(h=3,r1=1,r2=2);' == cylinder.to_scad()

    cylinder = Cylinder(r1=1, r2=2, h=3).t(1)
    assert 'translate([1,0,0])cylinder(h=3,r1=1,r2=2);' == cylinder.to_scad()
