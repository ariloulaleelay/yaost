from enum import Enum
from yaost import cylinder, hull

inf = 1000
tol = 0.01


class CapType(Enum):
    flat = 'flat'
    nut = 'nut'
    oval = 'oval'
    truss = 'truss'
    round_ = 'round'
    hex_ = 'hex'
    hex_washer = 'hex_washer'
    socket = 'socket'
    button = 'button'


class Nut(object):

    _config = {
        3.0: (2.75, 6.3, 2.6, 5.5),
        4.0: (3.4, 8.0, 3.5, 6.9),
        5.0: (4.34, 8.9, 3.82, 7.83),
        6.0: (5, 11.1, 5, 10),
    }

    def __init__(
        self,
        diameter: float,
        clearance: float = 0,
    ):
        self.diameter = float(diameter)
        if self.diameter not in self._config:
            raise Exception(f'Unknonw nut {self.diameter}')
        (
            self.internal_diameter,
            self.external_diameter,
            self.length,
            self.width,
        ) = self._config[self.diameter]
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
