# import pytest

from yaost.base import Node


def test_serialization():
    n = Node('x', None, int_value=1)
    assert 'x(int_value=1);' == n.to_string()

    n = Node('x', None, bool_value=True)
    assert 'x(bool_value=true);' == n.to_string()

    n = Node('x', None, str_value='abc')
    assert 'x(str_value="abc");' == n.to_string()

    n = Node('x', None, float_value=0.00001)
    assert 'x(float_value=0.000010);' == n.to_string()

    n = Node('x', None, array_value=[1, 2, 3, 'x'])
    assert 'x(array_value=[1,2,3,"x"]);' == n.to_string()

    n = Node('x', None, fn=1)
    assert 'x($fn=1);' == n.to_string()

    n = Node('x', None, 1, 2, 3, 4)
    assert 'x(1,2,3,4);' == n.to_string()

    n = Node('x', None, 1, a=2)
    assert 'x(1,a=2);' == n.to_string()


def test_union_collapse():
    x = Node('x', None)
    y = Node('y', None)
    z = Node('z', None)

    xy = x + y
    xyz = xy + z
    assert 'union(){x();y();}' == xy.to_string()
    assert 'union(){x();y();z();}' == xyz.to_string()
