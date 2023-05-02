from typing import Optional, List
from functools import reduce

from lazy import lazy

from yaost.base import BaseObject
from yaost.bbox import BBox
from yaost.vector import Vector
from yaost.util import full_arguments_line

__all__ = [
    'hull',
    'union',
    'difference',
    'intersection',
]


class BaseTransformation(BaseObject):
    pass


class SingleChildTransformation(BaseTransformation):
    child = None

    def _clone_with_another_child(self, another_child: BaseObject):
        raise NotImplementedError


class MultipleChildrenTransformation(BaseTransformation):
    children = ()

    def _children_to_scad(self):
        if not self.children:
            result = ''
        elif len(self.children) == 1:
            result = self.children[0].to_scad()
        else:
            result = '{{{}}}'.format(
                ''.join([child.to_scad() for child in self.children])
            )
        return result


class Translate(SingleChildTransformation):

    def __init__(
        self,
        vector: Vector,
        child: BaseObject,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        self.label = label
        self.child = child
        self._clone = clone
        self._vector = vector

    def _clone_with_another_child(self, another_child: BaseObject):
        return self.__class__(self._vector, another_child, clone=self._clone)

    @lazy
    def origin(self):
        result = self.child.origin + self._vector
        if self._clone:
            result = (result + self.child.origin) / 2
        return result

    @lazy
    def bbox(self):
        # TODO add correct bbox
        result = self.child.bbox + self._vector
        return result

    @property
    def x(self):
        return self._vector.x

    @property
    def y(self):
        return self._vector.y

    @property
    def z(self):
        return self._vector.z

    def to_scad(self):
        child_str = self.child.to_scad()
        translate_str = 'translate({})'.format(
            full_arguments_line([self._vector]),
        )
        result = f'{translate_str}{child_str}'
        if self._clone:
            result = f'union(){{{child_str}{result}}}'
        return result

    def __repr__(self):
        return f'<Translate({self._vector})>'


class Rotate(SingleChildTransformation):

    def __init__(
        self,
        vector: Vector,
        center: Vector,
        child: BaseObject,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        self.label = label
        self.child = child
        self._clone = clone
        self._center = center
        self._vector = vector

    def _clone_with_another_child(self, another_child: BaseObject):
        return self.__class__(self._vector, self._center, another_child, clone=self._clone)

    @lazy
    def origin(self):
        result = (self.child.origin - self._center).rotate(
            self._vector.x,
            self._vector.y,
            self._vector.z
        ) + self._center
        if self._clone:
            result = (result + self.child.origin) / 2
        return result

    @lazy
    def bbox(self):
        # TODO fix this
        return self.child.bbox

    @property
    def x(self):
        return self._vector.x

    @property
    def y(self):
        return self._vector.x

    @property
    def z(self):
        return self._vector.z

    def to_scad(self):
        rotate_str = 'rotate({})'.format(full_arguments_line([self._vector]))
        child_str = self.child.to_scad()
        if self._center:
            translate1_str = 'translate({})'.format(
                full_arguments_line([-self._center])
            )
            translate2_str = 'translate({})'.format(
                full_arguments_line([self._center])
            )
            result = f'{translate2_str}{rotate_str}{translate1_str}{child_str}'
        else:
            result = f'{rotate_str}{child_str}'
        if self._clone:
            result = f'union(){{{child_str}{result}}}'
        return result


class Union(MultipleChildrenTransformation):

    def __init__(
        self,
        children: List[BaseObject],
        label: Optional[str] = None,
    ):
        # TODO calculate bbox properly
        self.bbox = BBox()
        self.label = label
        flat_children = self._get_flat_children(children)
        self.origin = reduce(
            lambda x, y: x + y.origin,
            flat_children,
            Vector()
        ) / len(flat_children)
        self.children = flat_children

    @classmethod
    def _get_flat_children(cls, children):
        result = []
        for child in children:
            if isinstance(child, Union) and child.label is None:
                for subchild in cls._get_flat_children(child.children):
                    result.append(subchild)
            else:
                result.append(child)
        return sorted(result, key=lambda x: x.to_scad())

    def to_scad(self):
        return 'union(){}'.format(self._children_to_scad())


class Hull(MultipleChildrenTransformation):

    def __init__(
        self,
        children: List[BaseObject],
        label: Optional[str] = None,
    ):
        # TODO calculate bbox properly
        self.bbox = BBox()
        self.label = label
        flat_children = self._get_flat_children(children)
        self.origin = reduce(
            lambda x, y: x + y.origin,
            flat_children,
            Vector()
        ) / len(flat_children)
        self.children = flat_children

    @classmethod
    def _get_flat_children(cls, children):
        result = []
        for child in children:
            if isinstance(child, (Union, Hull)) and child.label is None:
                for subchild in cls._get_flat_children(child.children):
                    result.append(subchild)
            else:
                result.append(child)
        return sorted(result, key=lambda x: x.to_scad())

    def to_scad(self):
        return 'hull(){}'.format(self._children_to_scad())


class Intersection(MultipleChildrenTransformation):

    def __init__(
        self,
        children: List[BaseObject],
        label: Optional[str] = None,
    ):
        # TODO calculate bbox properly
        self.bbox = BBox()
        self.label = label
        flat_children = self._get_flat_children(children)
        # TODO calculate origin properly
        self.origin = reduce(
            lambda x, y: x + y.origin,
            flat_children,
            Vector()
        ) / len(flat_children)
        self.children = children

    @classmethod
    def _get_flat_children(cls, children):
        result = []
        for child in children:
            if isinstance(child, Intersection) and child.label is None:
                for subchild in cls._get_flat_children(child.children):
                    result.append(subchild)
            else:
                result.append(child)
        return sorted(result, key=lambda x: x.to_scad())

    def to_scad(self):
        return 'intersection(){}'.format(self._children_to_scad())


class Difference(MultipleChildrenTransformation):

    def __init__(
        self,
        children: List[BaseObject],
        label: Optional[str] = None,
    ):
        assert len(children) >= 2
        # TODO calculate bbox properly
        self.bbox = children[0].bbox
        self.label = label
        first = children[0]
        flat_children = self._get_flat_children(children[1:])

        # TODO calculate origin properly
        self.origin = first.origin
        if len(flat_children) > 1:
            second = Union(flat_children)
        else:
            second = flat_children[0]
        self.children = [first, second]

    @classmethod
    def _get_flat_children(cls, children):
        result = []
        for child in children:
            if isinstance(child, Union) and child.label is None:
                for subchild in cls._get_flat_children(child.children):
                    result.append(subchild)
            else:
                result.append(child)
        return sorted(result, key=lambda x: x.to_scad())

    def to_scad(self):
        return 'difference(){}'.format(self._children_to_scad())


class Mirror(SingleChildTransformation):

    def __init__(
        self,
        vector: Vector,
        center: Vector,
        child: BaseObject,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        self.label = label

        self.child = child
        self._clone = clone
        self._center = center
        self._vector = vector

    def _clone_with_another_child(self, another_child: BaseObject):
        return self.__class__(self._vector, self._center, another_child, clone=self._clone)

    @lazy
    def origin(self):
        result = (self.child.origin - self._center).mirror(
            self._vector.x,
            self._vector.y,
            self._vector.z,
        ) + self._center
        if self._clone:
            result = (result + self.child.origin) / 2
        return result

    @lazy
    def bbox(self):
        # TODO fix this
        return self.child.bbox

    @property
    def x(self):
        return self._vector.x

    @property
    def y(self):
        return self._vector.x

    @property
    def z(self):
        return self._vector.z

    def to_scad(self):
        mirror_str = 'mirror({})'.format(full_arguments_line([self._vector]))
        child_str = self.child.to_scad()
        if self._center:
            translate1_str = 'translate({})'.format(
                full_arguments_line([-self._center])
            )
            translate2_str = 'translate({})'.format(
                full_arguments_line([self._center])
            )
            result = f'{translate2_str}{mirror_str}{translate1_str}{child_str}'
        else:
            result = f'{mirror_str}{child_str}'
        if self._clone:
            result = f'union(){{{child_str}{result}}}'
        return result


class Scale(SingleChildTransformation):

    def __init__(
        self,
        vector: Vector,
        center: Vector,
        child: BaseObject,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        self.label = label
        self.child = child
        self._clone = clone
        self._center = center
        self._vector = vector

    def _clone_with_another_child(self, another_child: BaseObject):
        return self.__class__(self._vector, self._center, another_child, clone=self._clone)

    @lazy
    def origin(self):
        result = (self.child.origin - self._center).scale(
            self._vector.x,
            self._vector.y,
            self._vector.z,
        ) + self._center
        if self._clone:
            result = (result + self.child.origin) / 2
        return result

    @lazy
    def bbox(self):
        # TODO fix this
        return self.child.bbox

    @property
    def x(self):
        return self._vector.x

    @property
    def y(self):
        return self._vector.x

    @property
    def z(self):
        return self._vector.z

    def to_scad(self):
        transform_str = 'scale({})'.format(full_arguments_line([self._vector]))
        child_str = self.child.to_scad()
        if self._center:
            translate1_str = 'translate({})'.format(
                full_arguments_line([-self._center])
            )
            translate2_str = 'translate({})'.format(
                full_arguments_line([self._center])
            )
            result = f'{translate2_str}{transform_str}{translate1_str}{child_str}'
        else:
            result = f'{transform_str}{child_str}'
        if self._clone:
            result = f'union(){{{child_str}{result}}}'
        return result


class LinearExtrude(SingleChildTransformation):
    is_body = True

    def __init__(
        self,
        height: float,
        child: BaseObject,
        convexity: Optional[int] = None,
        twist: Optional[float] = None,
        slices: Optional[int] = None,
        fn: Optional[float] = None,
        label: Optional[str] = None,
    ):
        # TODO make proper bbox
        self.bbox = child.bbox
        self.origin = child.origin.tz(z=height / 2)

        self.label = label
        self.child = child
        self._height = height
        self._convexity = convexity
        self._twist = twist
        self._slices = slices
        self._fn = fn

    def to_scad(self):
        return 'linear_extrude({}){}'.format(
            full_arguments_line(
                (),
                {
                    'height': self._height,
                    'convexity': self._convexity,
                    'twist': self._twist,
                    'slices': self._slices,
                    '$fn': self._fn,
                },
            ),
            self.child.to_scad()
        )


class RotateExtrude(SingleChildTransformation):
    is_body = True

    def __init__(
        self,
        angle: float,
        child: BaseObject,
        convexity: Optional[int] = None,
        fn: Optional[float] = None,
        label: Optional[str] = None,
    ):
        # TODO make proper bbox
        self.bbox = child.bbox
        self.origin = Vector()

        self.label = label
        self.child = child
        self._angle = angle
        self._convexity = convexity
        self._fn = fn

    def to_scad(self):
        args = ','.join(
            f'{k}={v:.6f}'
            for k, v in (
                ('angle', self._angle),
                ('convexity', self._convexity),
                ('$fn', self._fn),
            )
            if v is not None
        )
        return 'rotate_extrude({}){}'.format(args, self.child.to_scad())


class GenericSingleTransformation(SingleChildTransformation):

    def __init__(
        self,
        name: str,
        child: BaseObject,
        *args,
        label: Optional[str] = None,
        is_body: bool = False,
        **kwargs,
    ):
        self.label = label

        # TODO make proper bbox
        self.bbox = child.bbox
        self.origin = child.origin
        self.is_body = is_body

        self.child = child
        self._name = name
        self._args = args
        self._kwargs = kwargs

    def _clone_with_another_child(self, another_child: BaseObject):
        return self.__class__(
            self._name,
            another_child,
            *self._args,
            is_body=self.is_body,
            **self._kwargs,
        )

    def to_scad(self):
        return '{}({}){}'.format(
            self._name,
            full_arguments_line(
                self._args,
                self._kwargs,
            ),
            self.child.to_scad()
        )


class Modifier(SingleChildTransformation):

    def __init__(
        self,
        name: str,
        child: BaseObject,
        label: Optional[str] = None,
    ):
        self.label = label

        # TODO make proper bbox
        self.bbox = child.bbox
        self.origin = child.origin

        self.child = child
        self._name = name

    def _clone_with_another_child(self, another_child: BaseObject):
        return self.__class__(self._name, self.child)

    def to_scad(self):
        return '{}{}'.format(
            self._name,
            self.child.to_scad()
        )


def difference(*args, label: Optional[str] = None):
    return Difference(args, label=label)


def hull(*args, label: Optional[str] = None):
    return Hull(args, label=label)


def union(*args, label: Optional[str] = None):
    return Union(args, label=label)


def intersection(*args, label: Optional[str] = None):
    return Intersection(args, label=label)
