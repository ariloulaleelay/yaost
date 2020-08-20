#!/usr/bin/env python

from yaost.project import Project
from yaost import scad

p = Project('example')
tol = 0.01  # tolerance
inf = 10000  # infinity


@p.add_part
def base_plate_with_holes():
    size = 60
    thickness = 3
    hole_diameter = 10
    hole_position = hole_diameter / 2 + thickness

    # create plate
    plate = scad.cube(size, size, thickness)

    # hole
    holes = scad.cylinder(d=hole_diameter, h=inf)
    holes = holes.tz('c')  # translate along Z to center of object
    holes = holes.t(hole_position, hole_position, 0)  # translate hole
    holes = holes.mx(plate.com.x, clone=True)  # mirror holes along x with center in plate.com
    holes = holes.my(plate.com.y, clone=True)

    # all transformations above can be written as single chain:
    # holes = scad.cylinder(
    #   d=hole_diameter, h=inf
    # ).t(
    #   hole_position, hole_position, 'c'
    # ).mx(
    #   plate.com.x, clone=True
    # ).my(
    #   plate.com.y, clone=True
    # )

    result = plate - holes
    # or result = plate.difference(holes)
    # or result = scad.difference(plate, holes)
    return result


@p.add_part
def transate_example():
    result = scad.cube(10, 10, 10)
    result = result.translate(1, 1, 1)  # translate x, y, z
    result = result.t(1, 1, 1)  # alias to translate
    result = result.tx(1)  # translate along x
    result = result.ty(10, clone=True)  # same as result = union(result, result.tx(10))
    return result


if __name__ == '__main__':
    p.run()
