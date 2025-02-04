from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

class AbstractGraphModel(QObject):
    nodesReset = Signal()
    edgesReset = Signal()

    nodesAdded = Signal(list)
    nodesAboutToBeRemoved = Signal(list)
    nodesRemoved = Signal(list)
    nodeDataChanged = Signal(list, list)

    portsAdded = Signal(list)
    portsAboutToBeRemoved = Signal(list)
    portsRemoved = Signal(list)
    portDataChanged = Signal(list, list)

    edgesAdded = Signal(list)
    edgesAboutToBeRemoved = Signal(list)
    edgesRemoved = Signal(list)
    edgeDataChanged = Signal(list, list)

    def nodes(self)->Iterable:
        ...

    def edges(self)->Iterable:
        ...

    def nodeData(self, index, role):
        ...

    def setNodeData(self, index, value, role):
        ...

    
    def nodeCount(self):
        ...

    def edgeCount(self):
        ...

    def portCount(self):
        ...