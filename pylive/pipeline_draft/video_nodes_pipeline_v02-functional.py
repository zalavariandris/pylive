from typing import Generic, TypeVar, Tuple, List
import numpy as np
import image_utils

from functools import partial

def read_sequence(path: str, frame:int, roi:Tuple[float, float, float, float]) -> np.ndarray:
    video = image_utils.read_image(path % frame)
    return video[frame]


def execute(node:Callable, *args, **kwargs):
    cache = dict()
    ...

class Graph:
    def __init__(self):
        self.nodes = []

    def node(self, func:Callable, *args, **kwargs):
        self.nodes.append((func, args, kwargs))
        return func

if __name__ == "__main__":
    ...