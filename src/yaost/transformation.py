from functools import reduce
from typing import Iterable, Optional

from lazy import lazy

from yaost.base import BaseObject
from yaost.bbox import BBox
from yaost.util import full_arguments_line
from yaost.vector import Vector

__all__ = [
    'difference',
    'hull',
    'intersection',
    'join',
    'minkowski',
    'union',
]


class BaseTransformation(BaseObject):
    pass


class SingleChildTransformation(BaseTransformation):
    def _clone_with_another_child(self, another_child: BaseObject):
        raise NotImplementedError

    def solids(self):
        for solid in self.child.solids():
            yield self._clone_with_another_child(solid)

    def holes(self):
        for hole in self.child.holes():
            yield self._clone_with_another_child(hole)

    def collapse(self, *classes_to_collapse):
        for collapsed in self.child.collapse(*classes_to_collapse):
            yield self._clone_with_another_child(collapsed)


class MultipleChildrenTransformation(BaseTransformation):
    __can_order_children__ = True
    __first_child_fixed__ = False
    __deduplicate__ = True

    @classmethod
    def _maybe_list_to_scad(cls, nodes):
        nodes = list(nodes)

        chunks = [node.to_scad() for node in nodes]
        if cls.__can_order_children__:
            if cls.__first_child_fixed__:
                chunks = chunks[:1] + list(sorted(chunks[1:]))
            else:
                chunks.sort()

        if cls.__deduplicate__:
            tmp, chunks = chunks, []
            if cls.__first_child_fixed__:
                chunks.append(tmp[0])
                tmp = tmp[1:]

            seen = set()
            for chunk in tmp:
                if chunk in seen:
                    continue
                seen.add(chunk)
                chunks.append(chunk)

        if not chunks:
            return ''

        if len(chunks) == 1:
            return chunks[0]

        return '{{{}}}'.format(''.join(chunks))

    def _children_to_scad(self):
        return self._maybe_list_to_scad(self.children)

    def collapse(self, *classes_to_collapse):
        if isinstance(self, classes_to_collapse):
            for child in self.children:
                yield from child.collapse(*classes_to_collapse)
        else:
            yield self


class Translate(SingleChildTransformation):
    def __init__(
        self,
        vector: Vector,
        child: BaseObject,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        self.label: Optional[str] = label
        self.child = child
        self._clone = clone
        self._vector = vector

    def _clone_with_another_child(self, another_child: BaseObject):
        return self.__class__(self._vector, another_child, clone=self._clone)

    def collapse(self, *classes_to_collapse):
        for collapsed in self.child.collapse(*classes_to_collapse):
            if isinstance(collapsed, Translate) and self._clone == collapsed._clone:
                yield self.__class__(
                    self._vector + collapsed._vector,
                    collapsed.child,
                )
            else:
                yield self._clone_with_another_child(collapsed)

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
        translate_str = f'translate({full_arguments_line([self._vector])})'
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
            self._vector.x, self._vector.y, self._vector.z
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
        return self._vector.y

    @property
    def z(self):
        return self._vector.z

    def to_scad(self):
        rotate_str = f'rotate({full_arguments_line([self._vector])})'
        child_str = self.child.to_scad()
        if self._center:
            translate1_str = f'translate({full_arguments_line([-self._center])})'
            translate2_str = f'translate({full_arguments_line([self._center])})'
            result = f'{translate2_str}{rotate_str}{translate1_str}{child_str}'
        else:
            result = f'{rotate_str}{child_str}'
        if self._clone:
            result = f'union(){{{child_str}{result}}}'
        return result


class Union(MultipleChildrenTransformation):
    def __init__(
        self,
        children: Iterable[BaseObject],
        label: Optional[str] = None,
    ):
        self.children = list(children)

        flat_children = list(self.collapse(Union, Hull))
        self.origin = reduce(lambda x, y: x + y.origin, flat_children, Vector()) / len(flat_children)
        # TODO calculate bbox properly
        self.bbox = BBox()
        self.label = label

    def to_scad(self):
        children = list(self.collapse(Union))

        if len(children) == 0:
            return ''

        if len(children) == 1:
            return children[0].to_scad()

        return f'union(){self._maybe_list_to_scad(children)}'


class Minkowski(MultipleChildrenTransformation):
    def __init__(
        self,
        children: Iterable[BaseObject],
        label: Optional[str] = None,
    ):
        children = list(children)
        self.bbox = BBox()
        self.label = label
        self.children = children

    def to_scad(self):
        return f'minkowski(){self._children_to_scad()}'


class Hull(MultipleChildrenTransformation):
    def __init__(
        self,
        children: Iterable[BaseObject],
        label: Optional[str] = None,
    ):
        self.children = list(children)
        flat_children = list(self.collapse(Union, Hull))
        self.origin = reduce(lambda x, y: x + y.origin, flat_children, Vector()) / len(flat_children)
        # TODO calculate bbox properly
        self.bbox = BBox()
        self.label = label

    def to_scad(self):
        children = self.collapse(Union, Hull)
        return f'hull(){self._maybe_list_to_scad(children)}'


class Intersection(MultipleChildrenTransformation):
    def __init__(
        self,
        children: Iterable[BaseObject],
        label: Optional[str] = None,
    ):
        self.children = list(children)
        flat_children = list(self.collapse(Intersection))
        # TODO calculate bbox properly
        self.bbox = BBox()
        self.label = label
        # TODO calculate origin properly
        self.origin = reduce(lambda x, y: x + y.origin, flat_children, Vector()) / len(flat_children)

    def to_scad(self):
        children = self.collapse(Intersection)
        return f'intersection(){self._maybe_list_to_scad(children)}'


class Difference(MultipleChildrenTransformation):
    __first_child_fixed__ = True

    def __init__(
        self,
        children: Iterable[BaseObject],
        label: Optional[str] = None,
    ):
        self.children = list(children)
        assert len(self.children) > 1

        # TODO calculate origin properly
        self.origin = children[0].origin
        self.bbox = children[0].bbox
        self.label = label

    def solids(self):
        for solid in self.children[0].solids():
            yield from solid.collapse(Union)

    def holes(self):
        for hole in self.children[0].holes():
            yield from hole.collapse(Union)
        for hole in self.children[1:]:
            yield from hole.collapse(Union)

    def collapse(self, *classes_to_collapse):
        if isinstance(self, classes_to_collapse):
            yield self.children[0]

            for child in self.children[1:]:
                yield from child.collapse(Union)

        else:
            yield self

    def to_scad(self):
        children = self.collapse(Difference)
        return f'difference(){self._maybe_list_to_scad(children)}'


class Join(MultipleChildrenTransformation):
    __first_child_fixed__ = True

    def __init__(
        self,
        children: Iterable[BaseObject],
        label: Optional[str] = None,
    ):
        self.children = list(children)
        assert len(self.children) > 1

        # TODO calculate origin properly
        self.origin = self.children[0].origin
        self.bbox = self.children[0].bbox
        self.label = label

    def collapse(self, *classes_to_collapse):
        if isinstance(self, classes_to_collapse):
            holes = []
            solids = []

            solids.extend(self.children[0].collapse(Union))

            for child in self.children[1:]:
                for subchild in child.collapse(Union):
                    chunks = list(subchild.collapse(Difference))
                    if not chunks:
                        continue
                    solids.extend(chunks[:1])
                    holes.extend(chunks[1:])

            if len(solids) > 1:
                solids = [Union(solids)]

            yield from solids
            yield from holes

        else:
            yield self

    def to_scad(self):
        chunks = list(self.collapse(Join))
        solids = chunks[:1]
        holes = chunks[1:]

        if not solids:
            return ''

        if not holes:
            return solids[0].to_scad()

        children = solids + holes

        return f'difference(){self._maybe_list_to_scad(children)}'


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
        mirror_str = f'mirror({full_arguments_line([self._vector])})'
        child_str = self.child.to_scad()
        if self._center:
            translate1_str = f'translate({full_arguments_line([-self._center])})'
            translate2_str = f'translate({full_arguments_line([self._center])})'
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
        transform_str = f'scale({full_arguments_line([self._vector])})'
        child_str = self.child.to_scad()
        if self._center:
            translate1_str = f'translate({full_arguments_line([-self._center])})'
            translate2_str = f'translate({full_arguments_line([self._center])})'
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

    def _clone_with_another_child(self, another_child: BaseObject):
        return self.__class__(
            self._height,
            self.child,
            self._convexity,
            self._twist,
            self._slices,
            self._fn,
        )

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
            self.child.to_scad(),
        )


class RotateExtrude(SingleChildTransformation):
    is_body = True

    def __init__(
        self,
        child: BaseObject,
        angle: Optional[float] = None,
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

    def _clone_with_another_child(self, another_child: BaseObject):
        return self.__class__(
            self.child,
            angle=self._angle,
            convexity=self._convexity,
            fn=self._fn,
        )

    def to_scad(self):
        args = full_arguments_line(
            args=(),
            kwargs=dict(
                angle=self._angle,
                convexity=self._convexity,
                fn=self._fn,
            ),
        )
        return f'rotate_extrude({args}){self.child.to_scad()}'


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
            self.child.to_scad(),
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
        return f'{self._name}{self.child.to_scad()}'


def difference(*args, label: Optional[str] = None):
    return Difference(args, label=label)


def hull(*args, label: Optional[str] = None):
    return Hull(args, label=label)


def intersection(*args, label: Optional[str] = None):
    return Intersection(args, label=label)


def minkowski(*args, label: Optional[str] = None):
    return Minkowski(args, label=label)


def union(*args, label: Optional[str] = None):
    return Union(args, label=label)


def join(*args, label: Optional[str] = None):
    return Join(args, label=label)
