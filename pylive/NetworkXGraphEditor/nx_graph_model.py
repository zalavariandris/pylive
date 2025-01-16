from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

import networkx as nx
from numpy import iterable

from pylive.utils.geo import intersect_ray_with_rectangle

from dataclasses import dataclass, field

type _NodeId=Hashable
type _EdgeId=tuple[_NodeId, _NodeId, Hashable]

class NXGraphModel(QObject):
    # Signal: List[_NodeId])
    nodesAdded: Signal = Signal(list)
    # Signal: List[_NodeId]
    nodesAboutToBeRemoved: Signal = Signal(list)
    # Signal: List[_NodeId]
    nodesRemoved: Signal = Signal(list)

    # Signal: List[_EdgeId]
    edgesAdded: Signal = Signal(list)  
    # Signal: List[_EdgeId]
    edgesAboutToBeRemoved: Signal = Signal(list)
    # Signal: List[_EdgeId]
    edgesRemoved: Signal = Signal(list)

    # Signal: dict[_NodeId, list]
    nodesChanged: Signal = Signal(dict)  
    # Signal: dict[_EdgeId, list]
    edgesPropertiesChanged: Signal = Signal(dict)  

    # @dataclass
    # class Change:
    #     added: set = field(default_factory=set)
    #     removed: set = field(default_factory=set)
    #     changed: set = field(default_factory=set)
    #     unchanged: set = field(default_factory=set)

    def __init__(self, G: nx.MultiDiGraph = nx.MultiDiGraph(), parent=None):
        super().__init__(parent=parent)
        self.G = G

        for n in self.G.nodes():
            node = self.addNode(n)

        for e in self.G.edges():
            u, v, k = e
            self.addEdge(u, v, k)

    def patch(self, G: nx.MultiDiGraph):
        ...
        raise NotImplementedError("Not yet implemented")

    def __del__(self):
        del self.G
        # self.nodesAdded.disconnect()
        # self.nodesAboutToBeRemoved.disconnect()
        # self.nodesPropertyChanged.disconnect()
        # self.nodesRemoved.disconnect()
        # self.edgesAdded.disconnect()
        # self.edgesAboutToBeRemoved.disconnect()
        # self.edgesPropertyChanged.disconnect()
        # self.edgesRemoved.disconnect()

    def nodes(self) -> List[Hashable]:
        return [n for n in self.G.nodes]

    def addNode(self, n: Hashable, /, **props) -> None:
        # print("add node: '{n}'")
        self.G.add_node(n, **props)
        self.nodesAdded.emit([n])
        self.nodesChanged.emit({n: props.keys()})

    def updateNodeProperties(self, n: Hashable, /, **props):
        # change guard TODO: find removed props
        change = list()
        for prop, value in props.items():
            if prop not in self.G.nodes[n]:
                self.G.nodes[n][prop] = value 
                change.append(prop)

            if value != self.G.nodes[n][prop]:
                self.G.nodes[n][prop] = value 
                change.append(prop)
        self.nodesChanged.emit({n: change})

    def deleteNodeProperty(self, n:Hashable, name, /)->None:
        del self.G.nodes[n][name]
        self.nodesChanged.emit({
            n:[name]
        })

    def hasNodeProperty(self, n: Hashable, name, /) -> bool:
        return name in self.G.nodes[n]

    def getNodeProperty(self, n: Hashable, name, /) -> object:
        return self.G.nodes[n][name]

    def getNodeProperties(self, n: Hashable, /) -> list[str]:
        return [key for key in self.G.nodes[n].keys()]

    def removeNode(self, n: Hashable, /):
        self.nodesAboutToBeRemoved.emit([n])
        self.G.remove_node(n)
        self.nodesRemoved.emit([n])

    def edges(self) -> Iterable[Tuple[Hashable, Hashable, Hashable]]:
        return [(u, v, k) for u, v, k in self.G.edges]

    def inEdges(self, n: Hashable, /) -> Iterable[tuple[Hashable, Hashable, Hashable]]:
        """retrun incoming edges to the node"""
        for e in self.G.in_edges(n, keys=True):
            yield e
        # return [(u, v, k) for u, v, k in self.G.in_edges(n, keys=True)]

    def outEdges(
        self, n: _NodeId, /
    ) -> Iterable[_EdgeId]:
        """retrun incoming edges to the node"""
        for e in self.G.edges(n, keys=True):
            yield e
        # return [(u, v, k) for u, v, k in self.G.out_edges(n, keys=True)]

    def addEdge(
        self, u: _NodeId, v: _NodeId, k: Hashable | None = None, /, **props
    ) -> None:
        if u not in self.G.nodes:
            self.addNode(u)
        if v not in self.G.nodes:
            self.addNode(v)

        k = self.G.add_edge(
            u, v, k, **props
        )  # note: if k is none, networkx will return a default value for k.
        self.edgesAdded.emit([(u, v, k)])

    def removeEdge(self, u: _NodeId, v: _NodeId, k: Hashable):
        self.edgesAboutToBeRemoved.emit([(u, v, k)])
        self.G.remove_edge(u, v, k)
        self.edgesRemoved.emit([(u, v, k)])

    def setEdgeProperties(
        self, u: _NodeId, v: _NodeId, k: Hashable, /, **props
    ):
        nx.set_edge_attributes(self.G, {(u, v, k): props})
        self.edgesPropertiesChanged.emit([(u, v, k)], list(props.keys()))

    def getEdgeProperty(self, u: _NodeId, v: _NodeId, k: Hashable, prop, /)->object|None:
        return self.G.edges[u, v, k][prop]

    def isEdgeAllowed(self, u: _NodeId, v: _NodeId, k: Hashable, /) -> bool:
        if u == v:
            return False
        return True



