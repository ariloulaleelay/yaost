# yaost

Yet another openscad translator.

Yaost - is python to openscad translator.

## Prerequisites
  - python >= 3.5
  - openscad >= 2019

## Quickstart
Create file example.py:

```python
#!/usr/bin/env python
from yaost import project, cube

p = Project('example project')

@p.add_part
def simple_cube():
    return cube(10, 10, 10)

if __name__ == '__main__':
    p.run()
```
Build scad file:

```bash
$ python3 example.py build-scad
```

Now you can see your scad model:
```
$ openscad scad/simple-cube.scad
```

To build stl, run:
```
$ python3 example.py build-stl
```
Your model will be at ```stl/simple-cube.stl```

You can run yaost in watch mode, it regenerates scad each time when you save python file:
```
$ python example.py watch
```
The open file with
```
$ openscad scad/simple-cube.scad
```
Change something in example.py (eg. ```cube(30, 10, 10)```) you should see changes in openscad viewer immediately.

See more in examples section.
