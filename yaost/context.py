# coding: utf-8
import copy
import hashlib
import logging
from typing import Optional, List
from lazy import lazy


class Operation(object):

    def __call__(self, node, **kwargs):
        raise NotImplemented

    def _find_body(self, node):
        from yaost.transformation import (
            SingleChildTransformation,
            MultipleChildrenTransformation,
        )
        if node.is_body:
            return node

        if isinstance(node, MultipleChildrenTransformation):
            for child in node.children:
                result = self._find_body(child)
                if result is not None:
                    return result
        elif isinstance(node, SingleChildTransformation):
            return self._find_body(node.child)
        return None

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

    def __call__(self, node, **kwargs):
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

    def __call__(self, node, **kwargs):
        return self._operator(self._left(node, **kwargs), self._right(node, **kwargs))


class NodeByLabel(Operation):

    def __init__(self, path=None):
        self._path = []
        if path is not None:
            self._path = list(path)

    def __call__(self, node, **kwargs):
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


class BodyContext(Operation):

    def __init__(self, path: List[str] = ()):
        self._path = list(path)

    def __call__(self, obj, **kwargs):
        body = self._find_body(obj)

        if body is None:
            raise RuntimeError('Could not find body')

        result = body
        for attr in self._path:
            result = getattr(result, attr)
        return result

    def __getattr__(self, key):
        return self.__class__(self._path + [key])


class CenterContext(Operation):

    def __call__(self, obj, axis: str = None, **kwargs):
        if axis not in ('xyz'):
            raise RuntimeError(f'Wrong axis `{axis}`')
        return -getattr(obj.origin, axis)


by_label = NodeByLabel()
body = BodyContext()
center = CenterContext()
