# import pytest

from yaost.body import Cylinder, Cube


def test_translate():
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
    assert (
        'translate([1,0,0])cylinder(h=3,r1=1,r2=2);'
        ==
        cylinder.to_scad()
    )

# def test_serialization():
#     n = Node('x', None, int_value=1)
#     assert 'x(int_value=1);' == n.to_string()
#
#     n = Node('x', None, bool_value=True)
#     assert 'x(bool_value=true);' == n.to_string()
#
#     n = Node('x', None, str_value='abc')
#     assert 'x(str_value="abc");' == n.to_string()
#
#     n = Node('x', None, float_value=0.00001)
#     assert 'x(float_value=0.000010);' == n.to_string()
#
#     n = Node('x', None, array_value=[1, 2, 3, 'x'])
#     assert 'x(array_value=[1,2,3,"x"]);' == n.to_string()
#
#     n = Node('x', None, fn=1)
#     assert 'x($fn=1);' == n.to_string()
#
#     n = Node('x', None, 1, 2, 3, 4)
#     assert 'x(1,2,3,4);' == n.to_string()
#
#     n = Node('x', None, 1, a=2)
#     assert 'x(1,a=2);' == n.to_string()
#
#
# def test_union_collapse():
#     x = Node('x', None)
#     y = Node('y', None)
#     z = Node('z', None)
#
#     xy = x + y
#     xyz = xy + z
#     assert 'union(){x();y();}' == xy.to_string()
#     assert 'union(){x();y();z();}' == xyz.to_string()
