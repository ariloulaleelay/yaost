# coding: utf8

from lazy import lazy
from math import acos, pi, sin

from .base import Node
from .vector import Vector


class Path(object):

    def __init__(self, points, ccw=False):
        self.points = points
        self.ccw = ccw

    @lazy
    def polygon(self):

        if len(self.points) < 2:
            return Node()

        pts = self.points
        extended_points = []
        for idx in range(len(pts)):
            pt = Vector(pts[idx])
            if idx == 0:
                v1 = Vector(pts[idx]) - Vector(pts[idx + 1])
            else:
                v1 = Vector(pts[idx - 1]) - Vector(pts[idx])

            if idx == len(pts) - 1:
                v2 = Vector(pts[idx]) - Vector(pts[idx - 1])
            else:
                v2 = Vector(pts[idx + 1]) - Vector(pts[idx])

            v1.z = 0
            v2.z = 0
            v1 = v1.normed
            v2 = v2.normed
            ptz = pt.z
            if self.ccw:
                ptz = -ptz
            sign = 1 if ptz >= 0 else -1

            dotproduct = v1.dot(v2)
            crossproduct = v1.cross(v2)
            if dotproduct < -1:
                dotproduct = -1
            elif dotproduct > 1:
                dotproduct = 1
            theta = acos(dotproduct) * 180 / pi

            if crossproduct.z * sign < 0:
                theta = 360 - theta

            while theta > 360:
                theta -= 360

            # print(v1, v2, dotproduct, theta, crossproduct)

            if theta > 180:
                if theta - 180 > 90:
                    sections = 16
                elif theta - 180 > 45:
                    sections = 8
                elif theta - 180 > 15:
                    sections = 2
                elif theta - 180 > 5:
                    sections = 1
                else:
                    sections = 0

                for sec in range(sections + 1):
                    angle = (theta - 180) * sign * sec
                    if sections > 0:
                        angle /= sections
                    vc = v1.rz(90 + angle)
                    rp = pt + vc * ptz
                    rp.z = 0
                    extended_points.append(rp.as_array)
            else:
                rp = pt + v1.rz(theta / 2 * sign) * sign * (ptz / sin(theta / 2 * pi / 180))

                rp.z = 0
                extended_points.append(rp.as_array)

        points = self.points + list(reversed(extended_points))
        points = [pt[:2] for pt in points]
        # print(points)

        return Node('polygon', None, points, faces=[idx for idx, _ in enumerate(points)], convexity=10)
