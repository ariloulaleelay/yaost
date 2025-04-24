from typing import Any


class Variable:
    def __init__(self, name: str, default: Any):
        self.name = name
        self.default = default
