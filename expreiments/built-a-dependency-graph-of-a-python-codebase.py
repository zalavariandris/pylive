"""
resources: https://www.python.org/success-stories/building-a-dependency-graph-of-our-python-codebase/


given a source python file, visualize import dependencies
"""
from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

import networkx as nx
from pylive.QtGraphEditor.dag_graph_graphics_scene import DAGScene, NodeWidget
from pylive.QtGraphEditor.graphmodel_databased import EdgeRef, GraphModel, InletRef, NodeRef, OutletRef

