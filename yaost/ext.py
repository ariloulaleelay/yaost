from yaost import scad, Vector
from yaost.path import Path

inf = 1000
tol = 0.005


class Nut(object):
    _config = {
        'M3': (2.75, 6.3, 2.6, 5.5),
        'M4': (3.4, 8.0, 3.5, 6.9),
        'M5': (4.34, 8.9, 3.82, 7.83),
    }

    def __init__(self, class_):
        if class_ not in self._config:
            raise Exception('Unknonw nut {}'.format(class_))
        self._class = class_
        self.internal_diameter, self.external_diameter, self.height, self.width = self._config[class_]

    @property
    def screw(self):
        return Screw(self._class)

    @property
    def model(self):
        result = scad.cylinder(d=self.external_diameter, h=self.height, fn=6)
        result -= scad.cylinder(d=self.internal_diameter, h=self.height + tol * 2).tz(-tol)
        return result

    def hole(self, h=inf):
        result = scad.cylinder(d=self.external_diameter, h=h, fn=6)
        return result


class Screw(object):

    _config = {
        'M3': (3.0, 6.0, 2.0),
        'M4': (4.0, 8.0, 3.0),
        'M5': (5.0, 9.9, 4.0),
    }

    def __init__(self, class_, length=inf):
        if class_ not in self._config:
            raise Exception('Unknonw nut {}'.format(class_))
        self.diameter, self.cap_diameter, self.cap_depth = self._config[class_]
        self.length = length
        self.class_ = class_

    @property
    def nut(self):
        return Nut(self.class_)

    @property
    def model(self):
        result = scad.cylinder(d1=self.cap_diameter, d2=self.diameter, h=self.cap_depth)
        result += scad.cylinder(d=self.diameter, h=self.length)
        return result

    def hole(self, h=inf, inf_cap=False, no_cap=False, cap_type='hidden', clearance=0):
        if no_cap:
            return scad.cylinder(d=self.diameter, h=h).tz(-tol)
        if inf_cap:
            result = scad.cylinder(d=self.cap_diameter, h=inf).mz().tz(tol)
        else:
            result = scad.cylinder(d=self.cap_diameter, h=tol * 2).tz(-tol)

        if cap_type == 'hidden':
            result += scad.cylinder(d1=self.cap_diameter, d2=self.diameter, h=self.cap_depth)
        elif cap_type == 'cylinder':
            result += scad.cylinder(d=self.cap_diameter, h=self.cap_depth)

        result += scad.cylinder(d=self.diameter + clearance, h=h)
        return result


class Nema(object):

    def __init__(self, class_=17):
        if class_ == 17:
            self.width = 42.3
            self.ledge_diameter = 22
            self.ledge_height = 2.0
            self.axel_diameter = 5
            self.axel_length = 25
            self.axel_chamfer = 0.5
            self.hole_spacing = 31
            self.screw = Screw('M3')
        else:
            raise Exception('{} class not supported'.format(class_))

    def holes(self, no_cap=False):
        result = scad.cylinder(d=self.ledge_diameter, h=inf).tz(-tol)
        result += self.screw.hole(no_cap=no_cap).t(
            self.hole_spacing / 2,
            self.hole_spacing / 2
        ).mx(clone=True).my(clone=True)
        return result

    @property
    def model(self):
        result = rounded_box(
            self.width, self.width, self.height, r=(self.width - self.hole_spacing) / 2
        ).t('c', 'c', -self.height)
        result += scad.cylinder(d=self.ledge_diameter, h=self.ledge_height + tol).tz(-tol)
        result += (
            scad.cylinder(d=self.axel_diameter, h=self.axel_length)
            - scad.cube(inf, inf, inf).t(
                'c',
                self.axel_diameter / 2 - self.axel_chamfer,
                'c'
            )
        )
        result -= scad.cylinder(d=self.screw.diameter, h=self.inf).t(
            self.hole_spacing / 2,
            self.hole_spacing / 2,
            -self.height / 2
        ).mx(clone=True).my(clone=True)
        return result.module_name('nema17')


class ExtrusionProfile(object):

    def __init__(self, class_='2020'):
        if class_ == '2020':
            self.width = 20
            self.insert_p2 = 9.55
            self.insert_p3 = 6.2
            self.insert_p3_y = 1.8
            self.screw = Screw('M4')
        else:
            raise Exception('class `{}` not found'.format(class_))

    def insert(self, height, length):
        p0 = Vector(self.width / 2, 0)
        p1 = Vector(self.width / 2, height)
        p2 = Vector(self.insert_p2 / 2, p1.y)
        p3 = Vector(self.insert_p3 / 2, p1.y + self.insert_p3_y)
        points = [p0, p1, p2, p3]
        points += [p.mx() for p in reversed(points)]
        result = scad.polygon(points).extrude(length).rx(90).t(
            self.width / 2,
            length
        )
        result.com = scad.cube(self.width, length, height).com
        return result

    # def simple_insert(height, length):
    #     p0 = Vector(width / 2, 0)
    #     p1 = Vector(width / 2, height)
    #     p2 = Vector(6.0 / 2, p1.y)
    #     p3 = Vector(6.0 / 2, p1.y + 1.8)
    #     points = [p0, p1, p2, p3]
    #     points += [p.mx() for p in reversed(points)]
    #     result = Path(points).extrude(length)
    #     return result
