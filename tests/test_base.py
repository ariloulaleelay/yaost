# import pytest
from .common import Node


def test_serialization():
    n = Node('x', int_value=1)
    assert 'x(int_value=1);' == n.to_scad()

    n = Node('x', bool_value=True)
    assert 'x(bool_value=true);' == n.to_scad()

    n = Node('x', str_value='abc')
    assert 'x(str_value="abc");' == n.to_scad()

    n = Node('x', float_value=0.00001)
    assert 'x(float_value=0.00001);' == n.to_scad()

    n = Node('x', array_value=[1, 2, 3, 'x'])
    assert 'x(array_value=[1,2,3,"x"]);' == n.to_scad()

    n = Node('x', fn=1)
    assert 'x($fn=1);' == n.to_scad()

    n = Node('x', 1, 2, 3, 4)
    assert 'x(1,2,3,4);' == n.to_scad()

    n = Node('x', 1, a=2)
    assert 'x(1,a=2);' == n.to_scad()


def test_union_collapse():
    x = Node('x')
    y = Node('y')
    z = Node('z')

    xy = x + y
    xyz = xy + z
    assert 'union(){x();y();}' == xy.to_scad()
    assert 'union(){x();y();z();}' == xyz.to_scad()
