from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


from enum import StrEnum
class GraphMimeData(StrEnum):
    OutletData = 'application/outlet'
    InletData = 'application/inlet'
    LinkSourceData = 'application/link/source'
    LinkTargetData = 'application/link/target'


_NodeKey = str
class AbstractGraphModel(QObject):
    modelAboutToBeReset = Signal()
    modelReset = Signal()

    # Nodes
    nodesAboutToBeAdded = Signal(list) # list of NodeKey
    nodesAdded = Signal(list) # list of NodeKey
    nodesAboutToBeRemoved = Signal(list) # list of NodeKey
    nodesRemoved = Signal(list) # list of NodeKey

    # 
    dataChanged = Signal(str, list) # key:Hashable, hints:list[str], node key and list of data name hints. if hints is empty consider all data changed

    # Links
    nodesAboutToBeLinked = Signal(list) # list of edges: tuple[source, target, outlet, inlet]
    nodesLinked = Signal(list) # list[NodeKey,NodeKey,NodeKey, NodeKey]
    nodesAboutToBeUnlinked = Signal(list) # list[NodeKey,NodeKey,NodeKey,NodeKey]
    nodesUnlinked = Signal(list) # list[NodeKey,NodeKey,NodeKey,NodeKey]

    # Inlets
    inletsReset = Signal(_NodeKey) # 
    outletsReset = Signal(_NodeKey)

    def nodes(self)->Collection[Hashable]:
        raise NotImplementedError("Abstract base method not implemented!")

    def inlets(self, node:_NodeKey)->Collection[_NodeKey]:
        raise NotImplementedError("Abstract base method not implemented!")

    def outlets(self, node:_NodeKey)->Collection[_NodeKey]:
        raise NotImplementedError("Abstract base method not implemented!")

    def links(self)->Collection[tuple[_NodeKey,_NodeKey,_NodeKey,_NodeKey]]:
        raise NotImplementedError("Abstract base method not implemented!")

    def inLinks(self, node:_NodeKey)->Collection[tuple[_NodeKey,_NodeKey,_NodeKey,_NodeKey]]:
        raise NotImplementedError("Abstract base method not implemented!")

    def outLinks(self, node:_NodeKey)->Collection[tuple[_NodeKey,_NodeKey,_NodeKey,_NodeKey]]:
        raise NotImplementedError("Abstract base method not implemented!")

    def linkNodes(self, source:_NodeKey, target:_NodeKey, outlet, inlet):
        raise NotImplementedError("Abstract base method not implemented!")

    def unlinkNodes(self, source:_NodeKey, target:_NodeKey, outlet, inlet):
        raise NotImplementedError("Abstract base method not implemented!")
