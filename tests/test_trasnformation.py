# import pytest

from yaost import join
from yaost.body import Cube, Cylinder

from .common import Node


def test_simple_cube():
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


def test_tree_union_collapses_to_flat_union():
    x = Node('x')
    y = Node('y')

    z = Node('z')
    a = Node('a')

    xy = x + y
    za = z + a
    xyza = xy + za
    assert 'union(){x();y();}' == xy.to_scad()
    assert 'union(){a();z();}' == za.to_scad()
    assert 'union(){a();x();y();z();}' == xyza.to_scad()


def test_union_removes_duplicates():
    x = Node('x')
    y = Node('y')
    z = Node('z')

    xy = x + y
    yz = y + z
    xyz = xy + yz
    assert 'union(){x();y();z();}' == xyz.to_scad()


def test_difference_collapses_unions():
    x = Node('x')
    y = Node('y')
    a = Node('a')

    x_plus_y = x + y
    a_minus_xy = a - x_plus_y

    assert 'difference(){a();x();y();}' == a_minus_xy.to_scad()


def test_simple_join_produces_difference():
    x = Node('x')
    y = Node('y')
    z = Node('z')
    a = Node('a')

    x_plus_y = x + y
    z_minus_a = z - a
    result = join(x_plus_y, z_minus_a)
    assert 'difference(){union(){x();y();z();}a();}' == result.to_scad()

    result = join(z_minus_a, x_plus_y)
    assert 'union(){difference(){z();a();}x();y();}' == result.to_scad()


def test_same_nodes_in_union_deduplicated():
    x = Node('x')
    y = Node('y')
    z = Node('z')

    result = x + y + z + z + y + x
    assert 'union(){x();y();z();}' == result.to_scad()


def test_union_does_not_apply_join_algorightm():
    x = Node('x')
    y = Node('y')
    z = Node('z')

    result = x + (y - z)
    assert 'union(){difference(){y();z();}x();}' == result.to_scad()


def test_complex_optimization_case():
    x = Node('x')
    y = Node('y')
    z = Node('z')
    a = Node('a')

    result = (x + (y - z)) - a
    assert 'difference(){union(){difference(){y();z();}x();}a();}' == result.to_scad()
