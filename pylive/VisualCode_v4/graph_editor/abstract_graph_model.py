from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

NodeId = Hashable
InletId = tuple[Hashable, str]
OutletId = tuple[Hashable, str]
EdgeId = tuple[OutletId, InletId]


class AbstractGraphModel(QObject):
    nodesReset = Signal()
    nodesInserted = Signal(QModelIndex, int, int)
    nodesAboutToBeRemoved = Signal(QModelIndex, int, int)
    nodeChanged = Signal(QModelIndex, QModelIndex, list)

    edgesReset = Signal()
    edgesInserted = Signal(QModelIndex, int, int)
    edgesAboutToBeRemoved = Signal(QModelIndex, int, int)
    edgeChanged = Signal(QModelIndex, QModelIndex, list)

    inletsReset = Signal(QModelIndex)
    outletsReset = Signal(QModelIndex)

    def nodes(self)->Sequence[NodeId]:
        ...

    def nodeCount(self)->int:
        ...

    def nodeData(self, node:NodeId):
        ...

    def inlets(self, node:NodeId)->Sequence[str]:
        ...

    def outlets(self, node:NodeId)->Sequence[str]:
        ...

    def edges(self)->Sequence[EdgeId]:
        ...

    def edgeCount(self)->int:
        ...

    def edgeData(self, edge:EdgeId):
        ...

    def inEdges(self, target:InletId):
        ...

    def outEdges(self, source:OutletId):
        ...

    def edgeSource(self, row:int)->OutletId:
        ...

    def edgeTarget(self, row:int)->InletId:
        ...