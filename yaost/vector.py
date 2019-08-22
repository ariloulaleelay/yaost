# coding: utf-8
from lazy import lazy
from math import sin, cos, pi, sqrt, atan2


class Vector(object):

    def __init__(self, x=None, y=None, z=None):
        if isinstance(x, list) and len(x) == 3 and y is None and z is None:
            x, y, z = x[0], x[1], x[2]

        self.x = x or 0
        self.y = y or 0
        self.z = z or 0

    @classmethod
    def com_for_children(cls, children):
        result = Vector()
        for child in children:
            result += child.com
        if children:
            result /= len(children)
        return result

    @classmethod
    def com_for_linear_extrude(cls, children, *args, **kwargs):
        result = cls.com_for_children(children)
        height = kwargs.get('h', args[0])
        return Vector(
            result.x,
            result.y,
            result.z + height / 2
        )

    @classmethod
    def com_for_cube(self, children, *args, **kwargs):
        x, y, z = args[0]
        return Vector(x / 2, y / 2, z / 2)

    @classmethod
    def com_for_cylinder(cls, children, *args, **kwargs):
        return Vector(0, 0, kwargs['h'] / 2)

    @classmethod
    def com_for_translate(cls, children, *args, **kwargs):
        result = cls.com_for_children(children)
        if kwargs.get('clone'):
            return (result + result.translate(*args[0])) / 2
        return result.translate(*args[0])

    @classmethod
    def com_for_mirror(cls, children, *args, **kwargs):
        result = cls.com_for_children(children)
        if kwargs.get('clone'):
            return (result + result.mirror(*args[0])) / 2
        return result.mirror(*args[0])

    @classmethod
    def com_for_rotate(cls, children, *args, **kwargs):
        result = cls.com_for_children(children)
        if kwargs.get('clone'):
            return (result + result.rotate(*args[0])) / 2
        return result.rotate(*args[0])

    @classmethod
    def com_for_scale(cls, children, *args, **kwargs):
        result = cls.com_for_children(children)
        if kwargs.get('clone'):
            return (result + result.scale(*args[0])) / 2
        return result.scale(*args[0])

    @classmethod
    def com_for_union(cls, children, *args, **kwargs):
        return cls.com_for_children(children)

    @classmethod
    def com_for_hull(cls, children, *args, **kwargs):
        return cls.com_for_children(children)

    def translate(self, x, y, z):
        return Vector(self.x + x, self.y + y, self.z + z)

    def scale(self, x, y, z):
        return Vector(self.x * x, self.y * y, self.z * z)

    def mirror(self, x, y, z):
        return Vector(
            self.x * (-1 if x else 1),
            self.y * (-1 if y else 1),
            self.z * (-1 if z else 1),
        )

    def mx(self):
        return self.mirror(1, 0, 0)

    def my(self):
        return self.mirror(0, 1, 0)

    def mz(self):
        return self.mirror(0, 0, 1)

    def rotate(self, ax=0, ay=0, az=0):
        a_sin = sin(ax * pi / 180)
        a_cos = cos(ax * pi / 180)
        x1 = self.x
        y1 = self.y * a_cos - self.z * a_sin
        z1 = self.y * a_sin + self.z * a_cos

        a_sin = sin(ay * pi / 180)
        a_cos = cos(ay * pi / 180)
        x2 = x1 * a_cos + z1 * a_sin
        y2 = y1
        z2 = -x1 * a_sin + z1 * a_cos

        a_sin = sin(az * pi / 180)
        a_cos = cos(az * pi / 180)
        x3 = x2 * a_cos - y2 * a_sin
        y3 = x2 * a_sin + y2 * a_cos
        z3 = z2
        return Vector(x3, y3, z3)

    def rx(self, ax):
        return self.rotate(ax=ax)

    def ry(self, ay):
        return self.rotate(ay=ay)

    def rz(self, az):
        return self.rotate(az=az)

    @lazy
    def norm(self):
        return sqrt(self.x**2 + self.y**2 + self.z**2)

    @lazy
    def normed(self):
        if self.norm == 0:
            return Vector(0, 0, 0)
        return Vector(self.x / self.norm, self.y / self.norm, self.z / self.norm)

    @lazy
    def normal(self):
        return Vector(-self.y, self.x, self.z)

    @lazy
    def as_array(self):
        return [self.x, self.y, self.z]

    @lazy
    def as_array_2d(self):
        return [self.x, self.y]

    @lazy
    def alpha(self):
        return atan2(self.x, self.y)

    def t(self, x=0, y=0, z=0):
        return self.translate(x, y, z)

    def tx(self, x):
        return self.translate(x, 0, 0)

    def ty(self, y):
        return self.translate(0, y, 0)

    def tz(self, z):
        return self.translate(0, 0, z)

    def dot(a, b):
        return a.x * b.x + a.y * b.y + a.z * b.z

    def cross(a, b):
        return Vector(
            a.y * b.z - a.z * b.y,
            a.z * b.x - a.x * b.z,
            a.x * b.y - a.y * b.x,
        )

    def projection(self, pl, pr):
        v1 = pr - pl
        v2 = self - pl

        if v2.norm == 0:
            return self

        new_length = v1.dot(v2) / v1.norm
        result = Vector(
            pl.x + new_length * v1.x / v1.norm,
            pl.y + new_length * v1.y / v1.norm
        )
        return result

    def __sub__(a, b):
        return Vector(a.x - b.x, a.y - b.y, a.z - b.z)

    def __add__(a, b):
        return Vector(a.x + b.x, a.y + b.y, a.z + b.z)

    def __mul__(self, scale):
        return Vector(self.x * scale, self.y * scale, self.z * scale)

    def __truediv__(self, scale):
        return Vector(self.x / scale, self.y / scale, self.z / scale)

    def __floordiv__(self, scale):
        return Vector(self.x // scale, self.y // scale, self.z // scale)

    def __str__(self):
        return "Vector(%f, %f, %f)" % (self.x, self.y, self.z)
