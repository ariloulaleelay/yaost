#!/usr/bin/env python

from yaost import Vector, cylinder, polygon

inf = 10000
tol = 0.005


class ExtrusionProfile:
    def __init__(self, class_='2020'):
        if class_ == '2020':
            self.width = 20
            self.insert_wide_width = 9.4
            self.insert_narrow_width = 6.1
            self.insert_depth = 1.8
        else:
            raise Exception('class `{class_}` not found')

    def insert(
        self,
        length,
        style='V',
        screw=None,
        on_side=False,
    ):
        points = [
            Vector(self.insert_wide_width / 2, -tol),
            Vector(self.insert_wide_width / 2, 0),
            Vector(self.insert_narrow_width / 2, self.insert_depth),
        ]
        points += [p.mx() for p in reversed(points)]
        result = polygon(points).extrude(length)
        if screw is not None:
            result -= (
                screw.hole(
                    clearance=0.3,
                    cap_clearance=0.3,
                    inf_cap=True,
                )
                .rx(-90)
                .t(
                    0,
                    -screw.length + 5,
                    length / 2,
                )
            )
            result -= (
                cylinder(d1=8, d2=12, h=self.insert_depth + tol)
                .rx(-90)
                .tz(
                    length / 2,
                )
            )
        result.origin = Vector(0, self.insert_depth / 2, length / 2)
        return result

    def insert_part(self, length=None, hole_depth=inf, hole_diameter=4.3):
        if length is None:
            length = self.width
        points = [
            Vector(self.insert_wide_width / 2, -tol),
            Vector(self.insert_wide_width / 2, 0),
            Vector(self.insert_narrow_width / 2, self.insert_depth),
        ]
        points += [p.mx() for p in reversed(points)]
        solid = polygon(points).extrude(length)
        hole = cylinder(d1=8, d2=12, h=self.insert_depth + tol).mz()
        if hole_depth:
            hole += cylinder(d=hole_diameter, h=self.insert_depth + tol + hole_depth).tz(-tol)
        hole = hole.rx(90).tz(length / 2)
        return solid, hole

    def insert_part_simple(self, length=None, hole_depth=inf, hole_diameter=4.3):
        if length is None:
            length = self.width
        insert_depth = 1.7
        points = [
            Vector(7.25 / 2, -tol),
            Vector(7.25 / 2, 0.7),
            Vector(6.0 / 2, 0.7),
            Vector(6.0 / 2, insert_depth),
        ]
        points += [p.mx() for p in reversed(points)]
        solid = polygon(points).extrude(length, convexity=4)
        hole = cylinder(d1=8, d2=12, h=insert_depth + tol).mz()
        if hole_depth:
            hole += cylinder(d=hole_diameter, h=insert_depth + tol + hole_depth).tz(-tol)
        hole = hole.rx(90).tz(length / 2)
        return solid, hole

    # def simple_insert(height, length):
    #     p0 = Vector(width / 2, 0)
    #     p1 = Vector(width / 2, height)
    #     p2 = Vector(6.0 / 2, p1.y)
    #     p3 = Vector(6.0 / 2, p1.y + 1.8)
    #     points = [p0, p1, p2, p3]
    #     points += [p.mx() for p in reversed(points)]
    #     result = Path(points).extrude(length)
    #     return result
