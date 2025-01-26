from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

# from dataclasses import dataclass
# @dataclass
# class Node:
#     name:str
#     func:str

# @dataclass
# class Edge:
#     source: Node
#     target: Node
#     inlet: str

# @dataclass
# class Graph:
#     nodes:list[Node]
#     edges:list[Edge]

# @dataclass
# class Scene:
#     definitions:str
#     graph: Graph

#     def serialize(self)->str:
#         return yaml.dump({
#             'definitions': self.definitions,
#         })

#     def deserialize(self, text:str):
#         # parse yaml
#         data = yaml.load(text, Loader=yaml.SafeLoader)

#         # set definitions
#         self.definitions = data['definitions']

#         #parse graph
#         nodes = [Node(_['name'], _['func']) for _ in data['graph']['nodes']]
#         edges = [Edge(_[0], _[1], _[2]) for _ in data['graph']['edges']]
#         self.graph = Graph(nodes, edges)


from qt_graph_editor_scene import QGraphEditorScene


