from enum import Enum
from math import sqrt

from yaost import cylinder, hull
from yaost.ext import thread

inf = 1000
tol = 0.01


class CapType(Enum):
    flat = 'flat'
    nut = 'nut'
    oval = 'oval'
    truss = 'truss'
    round_ = 'round'
    hex = 'hex'
    hex_washer = 'hex_washer'
    socket = 'socket'
    button = 'button'


class Nut(object):

    _config = {
        2.5: (5.45, 2.0),
        3.0: (6.01, 2.40),
        4.0: (7.66, 3.20),
        5.0: (8.79, 4.7),
        6.0: (11.05, 5.20),
        8.0: (14.38, 6.80),
        10.0: (17.77, 8.40),
        12.0: (21.70, 10.80),
        14.0: (23.36, 12.80),
        16.0: (26.75, 14.80),
        18.0: (29.56, 15.80),
        20.0: (32.95, 18.00),
        22.0: (37.29, 19.40),
        24.0: (39.55, 21.50),
        27.0: (45.20, 23.80),
        30.0: (50.85, 25.60),
    }

    def __init__(
        self,
        diameter: float,
        clearance: float = 0,
    ):
        self.diameter = float(diameter)
        if self.diameter not in self._config:
            raise Exception(f'Unknonw nut {self.diameter}')
        self.external_diameter, self.length = self._config[self.diameter]

        # https://en.wikipedia.org/wiki/ISO_metric_screw_thread
        pitch = thread.diameter_to_pitch(self.diameter)
        self.internal_diameter = self.diameter - 1.082532 * pitch
        self.width = self.external_diameter * sqrt(3) / 2
        self.clearance = clearance

    @property
    def screw(self):
        return Screw(self.diameter)

    @property
    def model(self):
        result = cylinder(d=self.external_diameter, h=self.height, fn=6)
        result -= cylinder(d=self.internal_diameter, h=self.height + tol * 2).tz(-tol)
        return result

    def hole(self, length=inf, clearance=None):
        if length is None:
            length = self.length
        if clearance is None:
            clearance = self.clearance

        result = cylinder(
            d=self.external_diameter + clearance,
            h=length,
            fn=6,
        )
        return result


class Screw(object):

    _config = {
        2.5: {
            CapType.socket: (4.5, 2.5),
        },
        3.0: {
            CapType.socket: (5.5, 3.0),
        },
        4.0: {
            CapType.nut: (8.0, 3.5),
            CapType.socket: (7.0, 4.0),
            CapType.flat: (8.0, 3.0),
        },
        5.0: {
            CapType.socket: (8.75, 5.0),
            CapType.flat: (9.9, 4.0),
        },
        6.0: {
            CapType.socket: (11, 6.0),
            CapType.flat: (12.0, 4.5),
        },
        12.0: {},
        14.0: {},
    }

    def __init__(
        self,
        diameter: float,
        cap: CapType = CapType.socket,
        length: float = inf,
        clearance: float = 0,
        cap_clearance: float = 0,
        nut_clearance: float = 0,
    ):
        self.diameter = float(diameter)
        if self.diameter not in self._config:
            raise Exception(f'Unknonw diameter {self.diameter}')

        if cap == CapType.hex:
            nut = Nut(diameter)
            self.cap_diameter, self.cap_depth = nut.external_diameter, nut.length
        else:
            diameter_config = self._config[self.diameter]
            if cap not in diameter_config:
                raise Exception(f'Cap type {cap} for diameter {self.diameter} not found')

            self.cap_diameter, self.cap_depth = diameter_config[cap]

        self.cap_type = cap
        self.length = length
        self.clearance = clearance
        self.cap_clearance = cap_clearance
        self.nut_clearance = nut_clearance

    @property
    def nut(self):
        return Nut(self.diameter)

    def hole(  # noqa
        self,
        no_cap: bool = False,
        length: float = None,
        clearance: float = None,
        cap_clearance: float = None,
        cap_cone: bool = False,
        nut_clearance: bool = None,
        inf_cap: bool = False,
        sacrificial: float = 0,
        z_align: str = 'root',
        nut: bool = False,
        nut_cone: bool = False,
    ):
        if length is None:
            length = self.length

        if clearance is None:
            clearance = self.clearance

        if cap_clearance is None:
            cap_clearance = self.cap_clearance

        if nut_clearance is None:
            nut_clearance = self.nut_clearance

        if inf_cap:
            cap_depth = inf
        else:
            cap_depth = self.cap_depth

        body = cylinder(
            d=self.diameter + clearance,
            h=length + tol * 2
        )

        if sacrificial:
            body = body.tz(sacrificial)
        else:
            body = body.tz(-tol)

        cap = None
        if not no_cap:
            if self.cap_type == CapType.socket:
                cap = cylinder(
                    d=self.cap_diameter + cap_clearance, h=cap_depth + tol
                ).mz()
            elif self.cap_type == CapType.flat:
                cap = cylinder(
                    d1=self.diameter + clearance,
                    d2=self.cap_diameter,
                    h=self.cap_depth + tol
                ).mz()
                if inf_cap:
                    cap = hull(
                        cap,
                        cylinder(
                            d=self.cap_diameter, h=tol
                        ).tz(-inf - tol)
                    )
            else:
                raise Exception(f'cap of type {self.cap_type} not supported yet')

            if cap_cone:
                d1 = self.cap_diameter + cap_clearance
                d2 = self.diameter + clearance
                cap += cylinder(
                    d1=d1,
                    d2=d2,
                    h=(d1 - d2) / 2 + tol
                ).tz(-tol)

        result = body
        if cap is not None:
            result += cap

        if nut:
            nut = cylinder(
                d=self.nut.external_diameter + nut_clearance,
                h=inf,
                fn=6
            ).tz(
                length - self.nut.height
            )
            if nut_cone:
                nut += cylinder(
                    d=self.diameter + clearance,
                    h=tol
                ).tz(
                   length - self.nut.height - self.diameter
                )
                nut = nut.hull()
            result += nut

        if z_align == 'cap':
            result = result.tz(self.cap_depth)
        elif z_align == 'center':
            length_ = self.length
            if nut:
                length_ -= self.nut.height
            result = result.tz(-length_ / 2)

        return result
