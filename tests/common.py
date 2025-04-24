from yaost.body import BaseBody
from yaost.util import full_arguments_line


class Node(BaseBody):
    def __init__(
        self,
        name: str,
        *args,
        **kwargs,
    ):
        self._name = name
        self._args = args
        self._kwargs = kwargs

    def to_scad(self):
        return f'{self._name}({full_arguments_line(self._args, self._kwargs)});'
