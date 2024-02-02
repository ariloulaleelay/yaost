# coding: utf-8
from typing import Iterable


class Operation(object):
    def __call__(self, node, **kwargs):
        raise NotImplementedError

    def _find_body(self, node):
        from yaost.transformation import (
            MultipleChildrenTransformation,
            SingleChildTransformation,
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

    def _find_first(self, node, callback):
        from yaost.transformation import (
            MultipleChildrenTransformation,
            SingleChildTransformation,
        )

        result = callback(node)
        if result is not None:
            return result

        if isinstance(node, MultipleChildrenTransformation):
            for child in node.children:
                result = self._find_first(child, callback)
                if result is not None:
                    return result
        elif isinstance(node, SingleChildTransformation):
            return self._find_first(node.child, callback)
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

    def __neg__(self):
        return UnaryOperation(self, operator=lambda x: -x)

    def __rmul__(self, other):
        return BinaryOperation(other, self, operator=lambda x, y: x * y)

    def __truediv__(self, other):
        return BinaryOperation(self, other, operator=lambda x, y: x / y)

    def __rtruediv__(self, other):
        return BinaryOperation(other, self, operator=lambda x, y: x / y)

    def __floordiv__(self, other):
        return BinaryOperation(self, other, operator=lambda x, y: x // y)


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


class UnaryOperation(Operation):
    def __init__(self, operand, operator):
        if isinstance(operand, Operation):
            self._operand = operand
        else:
            self._operand = ConstOperation(operand)
        self._operator = operator

    def __call__(self, node, **kwargs):
        return self._operator(self._operand(node, **kwargs))


class NodeByLabel(Operation):
    def __init__(self, path=None):
        self._path = []
        if path is not None:
            self._path = list(path)

    def __call__(self, obj, **kwargs):
        label, path = self._path[0], self._path[1:]

        def _filter(node):
            if node.label == label:
                return node
            return None

        result = self._find_first(obj, _filter)
        if result is None:
            raise RuntimeError('Could not find node')

        for attr in path:
            result = getattr(result, attr)
        return result

    def __getattr__(self, key):
        return self.__class__(self._path + [key])

    def __getitem__(self, key):
        return self.__class__(self._path + [key])


class BodyContext(Operation):
    def __init__(self, path: Iterable[str] = ()):
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
    def __call__(self, obj, **kwargs):
        axis = kwargs.get('axis')
        if axis is None or axis not in ('xyz'):
            raise RuntimeError(f'Wrong axis `{axis}`')
        return -getattr(obj.origin, axis)


class Inspector:
    def __init__(self, obj: 'BaseObject'):
        self._obj = obj

    def get_body(self):
        obj = self._find_first(self._obj, lambda x: x.is_obj)
        return obj

    def get_by_label(self, label: str):
        obj = self._find_first(self._obj, lambda x: x.label == label)
        return obj

    def _find_first(self, obj, filter_function):
        from yaost.transformation import (
            MultipleChildrenTransformation,
            SingleChildTransformation,
        )

        if filter_function(obj):
            return obj

        if isinstance(obj, MultipleChildrenTransformation):
            for child in obj.children:
                result = self._find_first(child, filter_function)
                if result is not None:
                    return result
        elif isinstance(obj, SingleChildTransformation):
            return self._find_first(obj.child, filter_function)
        return None


class QProxy:
    def __init__(self, obj: 'BaseObject'):
        self._obj = obj

    def __getattr__(self, key: str):
        return Inspector(self._obj).get_by_label(key)

    def __getitem__(self, key: str):
        return Inspector(self._obj).get_by_label(key)


by_label = NodeByLabel()
body = BodyContext()
center = CenterContext()
