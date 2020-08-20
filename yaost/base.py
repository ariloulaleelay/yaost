# coding: utf-8
import copy
import hashlib
import logging
from lazy import lazy
from .vector import Vector

logger = logging.getLogger(__name__)


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
        self.args = copy.deepcopy(args)
        self.kwargs = copy.deepcopy(kwargs)
        self.os = DialectProxy(self)
        self.kwargs.pop('clone', None)

    def __argument_to_string(self, arg):
        if isinstance(arg, str):
            # TODO fix this crutch
            if arg == '$preview':
                return arg
            return '"{}"'.format(arg)

        if isinstance(arg, bool):
            return str(arg).lower()

        if isinstance(arg, int):
            return '{}'.format(arg)

        if isinstance(arg, float):
            return '{:.6f}'.format(arg)

        if isinstance(arg, list) or hasattr(arg, '__iter__'):
            return '[{}]'.format(','.join(self.__argument_to_string(v) for v in arg))

        raise Exception('Unknown argument type {} ({})'.format(type(arg), arg))

    def __magic_keys(self, k):
        if k in {'fa', 'fs', 'fn'}:
            return '$' + k
        return k

    def traverse_children_deep_first(self):
        depths = []
        for c in self._children:
            depths.append((c.depth, c))
        for _, child in sorted(depths, key=lambda x: -x[0]):
            for descendant in child.traverse_children_deep_first():
                yield descendant
        yield self

    def to_string(self, cache=None):
        if cache is not None and self.id in cache:
            return cache[self.id]
        args = [self.__argument_to_string(v) for v in self.args]
        kwargs = [
            '{}={}'.format(self.__magic_keys(k), self.__argument_to_string(v))
            for k, v in sorted(self.kwargs.items())
            if not k.startswith('_')
        ]

        children = ''.join(c.to_string(cache=cache) for c in self._children)
        tail = ';'
        if children:
            tail = ''
            if len(self._children) > 1:
                children = '{' + children + '}'

        if self._name in {'#', '*', '!', '%'}:
            return '{}{}{}'.format(self._name, children, tail)

        return '{}({}){}{}'.format(self._name, ','.join(args + kwargs), children, tail)

    def module_name(self, name):
        kwargs = copy.deepcopy(self.kwargs)
        kwargs['_module_name'] = name
        return Node(self._name, self._children, *self.args, **kwargs)

    def preview(self):
        return Node('if', [self], '$preview')

    def color(self, *args, **kwargs):
        return Node('color', [self], *args, **kwargs)

    def debug(self, *args, **kwargs):
        return Node('#', [self])

    def root(self, *args, **kwargs):
        return Node('!', [self])

    def disable(self, *args, **kwargs):
        return Node('*', [self])

    def background(self, *args, **kwargs):
        return Node('%', [self])

    def render(self, *args, **kwargs):
        return Node('render', [self], *args, **kwargs)

    def _assert_numeric(self, *args):
        for arg in args:
            if isinstance(arg, (float, int)):
                continue
            raise Exception("%s neither float nor int" % (arg))

    @lazy
    def is_2d(self):
        return self._name in {
            'projection',
            'offset',
            'text',
            'polyton',
            'square',
            'circle'
        }

    @lazy
    def id(self):
        # TODO do hashing a little bit smarter
        result = hashlib.md5()
        result.update(self.to_string().encode('utf-8'))
        return result.hexdigest()

    @lazy
    def depth(self):
        if not self._children:
            return 0
        return max(c.depth for c in self._children) + 1

    @lazy
    def com(self):
        attr = 'com_for_{}'.format(self._name)
        if hasattr(Vector, attr):
            return getattr(Vector, attr)(self._children, *self.args, **self.kwargs)
        return Vector.com_for_children(self._children)

    @lazy
    def size(self):
        attr = 'size_for_{}'.format(self._name)
        if hasattr(Vector, attr):
            return getattr(Vector, attr)(self._children, *self.args, **self.kwargs)
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

    def extrude(self, *args, **kwargs):
        return self.linear_extrude(*args, **kwargs)

    def linear_extrude(self, *args, **kwargs):
        return TransformationNode('linear_extrude', self, *args, **kwargs)

    def rotate_extrude(self, *args, **kwargs):
        return TransformationNode('rotate_extrude', self, *args, **kwargs)

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
        return DistributiveNode('union', [self] + list(other))

    def intersection(self, *other):
        return DistributiveNode('intersection', [self] + list(other))

    def hull(self, *other):
        return DistributiveNode('hull', [self] + list(other))

    def offset(self, *args, **kwargs):
        return Node('offset', [self], *args, **kwargs)

    def projection(self, *args, **kwargs):
        return Node('projection', [self], *args, **kwargs)

    def _apply_same_transformations_to(self, other_object):
        return other_object

    def same_moves(self, other_object):
        return other_object._apply_same_transformations_to(self)

    def __add__(self, other):
        return self.union(other)

    def __sub__(self, other):
        return self.difference(other)

    def __getattr__(self, key):
        if len(self._children) == 0 and key in self.kwargs:
            return self.kwargs[key]

        if len(self._children) != 1:
            raise AttributeError(key)

        return getattr(self._children[0], key)


class TransformationNode(Node):

    def __new__(cls, *args, **kwargs):
        new_kwargs = copy.copy(kwargs)
        is_clone = new_kwargs.pop('clone', False)
        if is_clone:
            clone = cls(*args, **new_kwargs)
            union = DistributiveNode('union', clone._children + [clone])
            return union
        return super(TransformationNode, cls).__new__(cls)

    def _apply_same_transformations_to(self, other_object):
        return self.__class__(
            self._name,
            [c._apply_same_transformations_to(other_object) for c in self._children],
            *self.args,
            **self.kwargs,
        )

    @lazy
    def is_2d(self):
        if self._name in {'linear_extrude', 'rotate_extrude'}:
            return False
        return all(child.is_2d for child in self._children)


class DistributiveNode(Node):

    def __init__(self, name, children, *args, **kwargs):
        flat_children = []
        for child in children:
            if child._name == name:
                for grandchild in child._children:
                    flat_children.append(grandchild)
            else:
                flat_children.append(child)
        super(DistributiveNode, self).__init__(name, flat_children, *args, **kwargs)
