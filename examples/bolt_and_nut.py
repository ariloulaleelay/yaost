#!/usr/bin/env python

from yaost.ext.thread import internal_thread, external_thread
from yaost.project import Project
from yaost import (
    cylinder
)

p = Project('bolt and nut')


@p.add_part
def bolt(diameter=18, length=20):
    h = diameter * 0.4
    solid = external_thread(l=length + h, d1=diameter)
    solid += cylinder(d=diameter * 1.9, h=h, fn=6)
    return solid


@p.add_part
def nut(diameter=18, length=15, tol=0.01):
    h = diameter * 0.4
    solid = cylinder(d=diameter * 1.9, h=h, fn=6)
    solid -= internal_thread(d=diameter, l=h + tol * 2).tz(-tol)
    return solid


@p.add_part
def bigger_bolt():
    return bolt(length=40)


if __name__ == '__main__':
    p.run()
