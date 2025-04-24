# coding: utf-8
import logging
from typing import Optional
from typing import Union as TUnion

import yaost.context as ctx
from yaost.bbox import BBox
from yaost.context import Operation
from yaost.vector import Vector

logger = logging.getLogger(__name__)


class BaseObject:
    origin = Vector()
    bbox = BBox()
    label: Optional[str] = None
    is_body: bool = False
    is_2d = False

    def to_scad(self):
        raise NotImplementedError

    def traverse_all(self):
        from yaost.transformation import (
            MultipleChildrenTransformation,
            SingleChildTransformation,
        )

        if isinstance(self, MultipleChildrenTransformation):
            for child in self.children:
                for subchild in child.traverse_all():
                    yield subchild
        elif isinstance(self, SingleChildTransformation):
            for subchild in self.child.traverse_all():
                yield subchild
        yield self

    def _get_body_stack(self, label: Optional[str] = None):
        from yaost.transformation import (
            MultipleChildrenTransformation,
            SingleChildTransformation,
        )

        if self.is_body and (label is None or label == self.label):
            return [self]

        result = None
        if isinstance(self, MultipleChildrenTransformation):
            for child in self.children:
                result = child._get_body_stack(label)
                if result:
                    break
        elif isinstance(self, SingleChildTransformation):
            result = self.child._get_body_stack(label)
        if result is None:
            return result
        return result + [self]

    def solids(self):
        yield self

    def holes(self):
        return
        yield self

    def collapse(self, *classes_to_collapse):
        yield self

    def same_moves(
        self,
        obj_or_label: 'BaseObject',
        label: Optional[str] = None,
    ) -> 'BaseObject':
        from yaost.transformation import SingleChildTransformation

        result = self

        if isinstance(obj_or_label, str):
            label = obj_or_label
            obj_or_label = self

        stack = obj_or_label._get_body_stack(label=label)

        if stack is None:
            raise RuntimeError('Could not find body transformation stack')

        for transformation in stack[1:]:
            if not isinstance(transformation, SingleChildTransformation):
                break
            result = transformation._clone_with_another_child(result)
        return result

    def _eval_operation(
        self,
        value: Optional[TUnion[float, Vector, Operation]],
        axis: Optional[str] = None,
    ):
        if value == 'c':
            value = ctx.center

        if isinstance(value, Operation):
            value = value(self, axis=axis)
        return value

    def group(self, label: Optional[str] = None) -> 'BaseObject':
        """Group elements. Interpret as single body."""
        from yaost.body import Group

        return Group(self, label=label)

    def l(self, key: str):
        return ctx.NodeByLabel([key])(self)

    @property
    def q(self):
        return ctx.QProxy(self)

    @property
    def body(self):
        return ctx.Inspector(self).get_body()

    def t(
        self,
        x: TUnion[float, Operation] = 0,
        y: TUnion[float, Operation] = 0,
        z: TUnion[float, Operation] = 0,
        clone: bool = False,
        label: Optional[str] = None,
    ) -> 'BaseObject':
        from yaost.transformation import Translate

        x = self._eval_operation(x, 'x')
        y = self._eval_operation(y, 'y')
        z = self._eval_operation(z, 'z')

        if not x and not y and not z and not label:
            return self

        result = Translate(
            Vector(x, y, z),
            self,
            clone=clone,
            label=label,
        )
        return result

    def tv(
        self,
        v: TUnion[Vector] = 0,
        clone: bool = False,
        label: Optional[str] = None,
    ) -> 'BaseObject':
        from yaost.transformation import Translate

        v = self._eval_operation(v)
        if not v:
            return self

        result = Translate(
            v,
            self,
            clone=clone,
            label=label,
        )
        return result

    def c(
        self,
        x: TUnion[float, Operation] = 0,
        y: TUnion[float, Operation] = 0,
        z: TUnion[float, Operation] = 0,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        x = self._eval_operation(x, 'x')
        y = self._eval_operation(y, 'y')
        z = self._eval_operation(z, 'z')

        if x:
            x = -self.origin.x
        if y:
            y = -self.origin.y
        if z:
            z = -self.origin.z

        return self.t(x, y, z, clone=clone, label=label)

    def rotate(
        self,
        x: TUnion[float, Operation] = 0,
        y: TUnion[float, Operation] = 0,
        z: TUnion[float, Operation] = 0,
        xc: TUnion[float, Operation] = 0,
        yc: TUnion[float, Operation] = 0,
        zc: TUnion[float, Operation] = 0,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        from yaost.transformation import Rotate

        x = self._eval_operation(x, 'x')
        y = self._eval_operation(y, 'y')
        z = self._eval_operation(z, 'z')

        xc = self._eval_operation(xc, 'x')
        yc = self._eval_operation(yc, 'y')
        zc = self._eval_operation(zc, 'z')

        if not x and not y and not z and not label:
            return self

        result = Rotate(Vector(x, y, z), Vector(xc, yc, zc), self, clone=clone, label=label)
        return result

    def m(
        self,
        x: TUnion[float, Operation] = 0,
        y: TUnion[float, Operation] = 0,
        z: TUnion[float, Operation] = 0,
        xc: TUnion[float, Operation] = 0,
        yc: TUnion[float, Operation] = 0,
        zc: TUnion[float, Operation] = 0,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        from yaost.transformation import Mirror

        x = self._eval_operation(x, 'x')
        y = self._eval_operation(y, 'y')
        z = self._eval_operation(z, 'z')

        xc = self._eval_operation(xc, 'x')
        yc = self._eval_operation(yc, 'y')
        zc = self._eval_operation(zc, 'z')

        if not x and not y and not z and not label:
            return self

        result = Mirror(
            Vector(x, y, z),
            Vector(xc, yc, zc),
            self,
            clone=clone,
            label=label,
        )
        return result

    def s(
        self,
        x: TUnion[float, Operation] = 0,
        y: TUnion[float, Operation] = 0,
        z: TUnion[float, Operation] = 0,
        xc: TUnion[float, Operation] = 0,
        yc: TUnion[float, Operation] = 0,
        zc: TUnion[float, Operation] = 0,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        from yaost.transformation import Scale

        x = self._eval_operation(x, 'x')
        y = self._eval_operation(y, 'y')
        z = self._eval_operation(z, 'z')

        xc = self._eval_operation(xc, 'x')
        yc = self._eval_operation(yc, 'y')
        zc = self._eval_operation(zc, 'z')

        if not x and not y and not z and not label:
            return self

        result = Scale(
            Vector(x, y, z),
            Vector(xc, yc, zc),
            self,
            clone=clone,
            label=label,
        )
        return result

    def mx(
        self,
        xc: TUnion[float, Operation] = 0,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        return self.m(x=1, xc=xc, clone=clone, label=label)

    def my(
        self,
        yc: TUnion[float, Operation] = 0,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        return self.m(y=1, yc=yc, clone=clone, label=label)

    def mz(
        self,
        zc: TUnion[float, Operation] = 0,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        return self.m(z=1, zc=zc, clone=clone, label=label)

    def tx(
        self,
        x: TUnion[float, Operation] = 0,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        return self.t(x=x, clone=clone, label=label)

    def ty(
        self,
        y: TUnion[float, Operation] = 0,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        return self.t(y=y, clone=clone, label=label)

    def tz(
        self,
        z: TUnion[float, Operation] = 0,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        return self.t(z=z, clone=clone, label=label)

    def cx(
        self,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        return self.c(x=1, clone=clone, label=label)

    def cy(
        self,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        return self.c(y=1, clone=clone, label=label)

    def cz(
        self,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        return self.c(z=1, clone=clone, label=label)

    def rx(
        self,
        x: TUnion[float, Operation] = 0,
        xc: TUnion[float, Operation] = 0,
        yc: TUnion[float, Operation] = 0,
        zc: TUnion[float, Operation] = 0,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        return self.rotate(x=x, xc=xc, yc=yc, zc=zc, clone=clone, label=label)

    def ry(
        self,
        y: TUnion[float, Operation] = 0,
        xc: TUnion[float, Operation] = 0,
        yc: TUnion[float, Operation] = 0,
        zc: TUnion[float, Operation] = 0,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        return self.rotate(y=y, xc=xc, yc=yc, zc=zc, clone=clone, label=label)

    def rz(
        self,
        z: TUnion[float, Operation] = 0,
        xc: TUnion[float, Operation] = 0,
        yc: TUnion[float, Operation] = 0,
        zc: TUnion[float, Operation] = 0,
        clone: bool = False,
        label: Optional[str] = None,
    ):
        return self.rotate(z=z, xc=xc, yc=yc, zc=zc, clone=clone, label=label)

    def __add__(self, other):
        return self.union(other)

    def __sub__(self, other):
        return self.difference(other)

    def __mul__(self, other):
        return self.intersection(other)

    def join(self, other: 'BaseObject', label: Optional[str] = None):
        from yaost.transformation import Join

        return Join([self, other], label=label)

    def union(self, other: 'BaseObject', label: Optional[str] = None):
        from yaost.transformation import Union

        return Union([self, other], label=label)

    def difference(self, other: 'BaseObject', label: Optional[str] = None):
        from yaost.transformation import Difference

        return Difference([self, other], label=label)

    def intersection(self, other: 'BaseObject', label: Optional[str] = None):
        from yaost.transformation import Intersection

        return Intersection([self, other], label=label)

    def linear_extrude(self, height: float, **kwargs):
        from yaost.transformation import LinearExtrude

        return LinearExtrude(height, self, **kwargs)

    def rotate_extrude(self, angle: Optional[float] = None, **kwargs):
        from yaost.transformation import RotateExtrude

        kwargs = dict(kwargs)
        if angle is not None:
            kwargs['angle'] = angle
        return RotateExtrude(self, **kwargs)

    def extrude(self, height: float, **kwargs):
        return self.linear_extrude(height, **kwargs)

    def offset(self, r=None, **kwargs):
        from yaost.transformation import GenericSingleTransformation

        if r is not None:
            kwargs['r'] = r
        return GenericSingleTransformation('offset', self, **kwargs)

    def render(self, **kwargs):
        from yaost.transformation import GenericSingleTransformation

        return GenericSingleTransformation('render', self, **kwargs)

    def projection(self, **kwargs):
        from yaost.transformation import GenericSingleTransformation

        return GenericSingleTransformation('projection', self, **kwargs)

    def hull(self, **kwargs):
        from yaost.transformation import Hull

        return Hull([self], **kwargs)

    def color(self, *args, **kwargs):
        from yaost.transformation import GenericSingleTransformation

        return GenericSingleTransformation('color', self, *args, **kwargs)

    def debug(self, label: Optional[str] = None):
        from yaost.transformation import Modifier

        return Modifier('#', self, label=label)

    def background(self, label: Optional[str] = None):
        from yaost.transformation import Modifier

        return Modifier('%', self, label=label)

    def show_only(self, label: Optional[str] = None):
        from yaost.transformation import Modifier

        return Modifier('!', self, label=label)

    def disable(self, label: Optional[str] = None):
        from yaost.transformation import Modifier

        return Modifier('*', self, label=label)
