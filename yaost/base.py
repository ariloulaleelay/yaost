# coding: utf-8
import copy
from lazy import lazy
from .vector import Vector


class DialectProxy(object):

    def __init__(self, node=None):
        self._node = node

    def __getattr__(self, key):
        def callback(*args, **kwargs):
            return Node(key, self._node, *args, **kwargs)
        return callback


class Node(object):

    def __init__(self, name, children, *args, **kwargs):
        if children is None:
            children = []
        elif not isinstance(children, list):
            children = [children]
        self._name = name
        self._children = children
        self._args = args
        self._kwargs = kwargs
        self.os = DialectProxy(self)

    def __argument_to_string(self, arg):
        if isinstance(arg, str):
            return '"{}"'.format(arg)

        if isinstance(arg, int):
            return '{}'.format(arg)

        if isinstance(arg, float):
            return '{:.6f}'.format(arg)

        if isinstance(arg, bool):
            return str(arg).lower()

        if isinstance(arg, list) or hasattr(arg, '__iter__'):
            return '[{}]'.format(','.join(self.__argument_to_string(v) for v in arg))

        raise Exception('Unknown argument type {} ({})'.format(type(arg), arg))

    def __magic_keys(self, k):
        if k == 'fn':
            return '$fn'
        return k

    def to_string(self):
        args = [self.__argument_to_string(v) for v in self._args]
        kwargs = [
            '{}={}'.format(self.__magic_keys(k), self.__argument_to_string(v))
            for k, v in self._kwargs.items()
        ]

        children = ''.join(c.to_string() for c in self._children)
        tail = ';'
        if children:
            tail = ''
            if len(self._children) > 1:
                children = '{' + children + '}'

        return '{}({}){}{}'.format(
            self._name,
            ','.join(args + kwargs),
            children,
            tail,
        )

    def _assert_numeric(self, *args):
        for arg in args:
            if isinstance(arg, (float, int)):
                continue
            raise Exception("%s neither float nor int" % (arg))

    @lazy
    def com(self):
        if hasattr(Vector, 'com_for_{}'.format(self._name)):
            return getattr(Vector, 'com_for_{}'.format(self._name))(
                self._children, *self._args, **self._kwargs
            )
        return Vector(0., 0., 0.)

    @lazy
    def size(self):
        if hasattr(Vector, 'size_for_{}'.format(self._name)):
            return getattr(Vector, 'size_for_{}'.format(self._name))(
                self._children, *self._args, **self._kwargs
            )
        return Vector(0., 0., 0.)

    def t(self, x=0, y=0, z=0, **kwargs):
        if x == y == z == 0:
            return self

        if x in {'c', 'com'}:
            x = -self.com.x
        if y in {'c', 'com'}:
            y = -self.com.y
        if z in {'c', 'com'}:
            z = -self.com.z
        return TransformationNode('translate', self, [x, y, z], **kwargs)

    def r(self, x=0, y=0, z=0, xc=0, yc=0, zc=0, **kwargs):
        if x == y == z == 0:
            return self

        result = self
        if xc != 0 or yc != 0 or zc != 0:
            result = result.t(-xc, -yc, -zc)
            result = TransformationNode('rotate', result, [x, y, z], **kwargs)
            result = result.t(xc, yc, zc)
        else:
            result = TransformationNode('rotate', result, [x, y, z], **kwargs)
        return result

    def s(self, x=1.0, y=1.0, z=1.0, **kwargs):
        return TransformationNode('scale', self, [x, y, z], **kwargs)

    def m(self, x=0, y=0, z=0, xc=0, yc=0, zc=0, **kwargs):
        result = self
        if xc != 0 or yc != 0 or zc != 0:
            result = result.t(-xc, -yc, -zc)
            result = TransformationNode('mirror', result, [x, y, z], **kwargs)
            result = result.t(xc, yc, zc)
        else:
            result = TransformationNode('mirror', result, [x, y, z], **kwargs)
        return result

    def extrude(self, height, **kwargs):
        return TransformationNode('extrude', self, height, **kwargs)

    def tx(self, x, **kwargs):
        return self.t(x=x, **kwargs)

    def ty(self, y, **kwargs):
        return self.t(y=y, **kwargs)

    def tz(self, z, **kwargs):
        return self.t(z=z, **kwargs)

    def rx(self, x, **kwargs):
        return self.r(x=x, **kwargs)

    def ry(self, y, **kwargs):
        return self.r(y=y, **kwargs)

    def rz(self, z, **kwargs):
        return self.r(z=z, **kwargs)

    def mx(self, center=0, **kwargs):
        return self.m(x=1, xc=center, **kwargs)

    def my(self, center=0, **kwargs):
        return self.m(y=1, yc=center, **kwargs)

    def mz(self, center=0, **kwargs):
        return self.m(z=1, zc=center, **kwargs)

    def difference(self, other):
        return Node('difference', [self, other])

    def union(self, *other):
        return DisitributiveNode('union', [self] + list(other))

    def intersection(self, *other):
        return DisitributiveNode('intersection', [self] + list(other))

    def hull(self, *other):
        return DisitributiveNode('hull', [self] + list(other))

    def offset(self, r, chamfer=True):
        return Node('offset', [self], r, chamfer=chamfer)

    def _apply_same_transformations_to(self, other_object):
        return other_object

    def same_moves(self, other_object):
        return other_object._apply_same_transformations_to(self)

    def __add__(self, other):
        return self.union(other)

    def __sub__(self, other):
        return self.difference(other)

    def __getattr__(self, key):
        if 'child' in self.__dict__:
            return getattr(self.child, key)
        raise AttributeError(key)


class TransformationNode(Node):

    def _apply_same_transformations_to(self, other_object):
        return self.__class__(
            self._name,
            [c._apply_same_transformations_to(other_object) for c in self._children],
            *self._args,
            **self._kwargs,
        )

    def to_string(self):
        if not self._kwargs.get('clone', False):
            return super(TransformationNode, self).to_string()
        kwargs = copy.copy(self._kwargs)
        kwargs.pop('clone')
        clone = self.__class__(self._name, self._children, *self._args, **kwargs)
        union = DisitributiveNode('union', self._children + [clone])
        return union.to_string()


class DisitributiveNode(Node):

    def __init__(self, name, children, *args, **kwargs):
        flat_children = []
        for child in children:
            if child._name == name:
                for grandchild in child._children:
                    flat_children.append(grandchild)
            else:
                flat_children.append(child)
        super(DisitributiveNode, self).__init__(name, flat_children, *args, **kwargs)
