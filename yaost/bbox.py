import typing
from yaost.vector import Vector


class BBox:
    def __init__(
        self,
        vmin: typing.Optional[Vector] = None,
        vmax: typing.Optional[Vector] = None
    ):
        if vmin is None:
            vmin = Vector()
        if vmax is None:
            vmax = Vector()

        self.vmin = vmin
        self.vmax = vmax

    @classmethod
    def _new_order(self, v1: Vector, v2: Vector):
        vmin = Vector(
            min(v1.x, v2.x),
            min(v1.y, v2.y),
            min(v1.z, v2.z),
        )
        vmax = Vector(
            max(v1.x, v2.x),
            max(v1.y, v2.y),
            max(v1.z, v2.z),
        )
        return vmin, vmax


    def mirror(self, x: float, y: float, z: float):
        vmin, vmax = self._new_order(
            self.vmin.mirror(x, y, z),
            self.vmax.mirror(x, y, z)
        )
        return BBox(vmin, vmax)

    def scale(self, x: float, y: float, z: float):
        vmin, vmax = self._new_order(
            self.vmin.scale(x, y, z),
            self.vmax.scale(x, y, z)
        )
        return BBox(vmin, vmax)

    def __add__(self, other):
        if isinstance(other, Vector):
            return BBox(
                self.vmin + other,
                self.vmax + other,
            )
        elif isinstance(other, BBox):
            return BBox(self.vmin, self.vmax)
        else:
            raise RuntimeError(f'Unknown type `{type(other)}`')


