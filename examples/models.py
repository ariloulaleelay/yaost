#!/usr/bin/env python

from yaost import Project, sphere

p = Project('example')


def cube_soft_edges(x, y, z, r=1, fn=24):
    return sphere(
        r=r, fn=fn
    ).t(
        r, r, r
    ).mx(
        x / 2, clone=True
    ).my(
        y / 2, clone=True
    ).mz(
        z / 2, clone=True
    ).hull()


@p.add_part
def cube_example():
    return cube_soft_edges(20, 20, 20)


if __name__ == '__main__':
    p.run()
