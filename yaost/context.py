# coding: utf-8
import copy
import hashlib
import logging
from lazy import lazy


class Operation(object):

    def _eval(self, node):
        raise NotImplemented

    def __add__(self, other):
        return BinaryOperation(self, other, operator=lambda x, y: x + y)

    def __radd__(self, other):
        return BinaryOperation(other, self, operator=lambda x, y: x + y)

    def __sub__(self, other):
        return BinaryOperation(self, other, operator=lambda x, y: x - y)

    def __rsub__(self, other):
        return BinaryOperation(other, self, operator=lambda x, y: x - y)

    def __mul__(self, other):
        return BinaryOperation(self, other, operator=lambda x, y: x * y)

    def __rmul__(self, other):
        return BinaryOperation(other, self, operator=lambda x, y: x * y)

    def __truediv__(self, other):
        return BinaryOperation(self, other, operator=lambda x, y: x / y)

    def __rtruediv__(self, other):
        return BinaryOperation(other, self, operator=lambda x, y: x / y)

    def __floordiv__(self, other):
        return BinaryOperation(self, other, operator=lambda x, y: x // y)

    def __floordiv__(self, other):
        return BinaryOperation(other, self, operator=lambda x, y: x / y)


class ConstOperation(Operation):

    def __init__(self, value):
        self._value = value

    def _eval(self, node):
        return self._value


class BinaryOperation(Operation):

    def __init__(self, left, right, operator):
        if not isinstance(left, Operation):
            left = ConstOperation(left)
        if not isinstance(right, Operation):
            right = ConstOperation(right)
        self._left = left
        self._right = right
        self._operator = operator

    def _eval(self, node):
        return self._operator(self._left._eval(node), self._right._eval(node))


class NodeByLabel(Operation):

    def __init__(self, path=None):
        self._path = []
        if path is not None:
            self._path = list(path)

    def _eval(self, node):
        from yaost.base import Node

        assert self._path, 'Path should be greater than 0'
        label, keys = self._path[0], self._path[1:]
        value = node.get_child_by_label(label)
        for key in keys:
            if hasattr(value, key):
                value = getattr(value, key)
                continue
            elif isinstance(value, Node) and key in value._kwargs:
                value = value._kwargs[key]
            else:
                raise Exception(f'Could not find value for {key}')
        return value

    def __getattr__(self, key):
        return NodeByLabel(self._path + [key])


by_label = NodeByLabel()
