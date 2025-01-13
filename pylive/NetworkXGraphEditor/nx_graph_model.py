from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

import networkx as nx
from numpy import isin

from pylive.utils.geo import intersect_ray_with_rectangle


class NXGraphModel(QObject):
    nodesAdded: Signal = Signal(list)  # List[Hashable]
    nodesAboutToBeRemoved: Signal = Signal(list)  # List[Hashable]
    nodesPropertiesChanged: Signal = Signal(
        dict
    )  # dict[Hashable, dict[str, Any]]
    nodesRemoved: Signal = Signal(list)

    edgesAdded: Signal = Signal(
        list
    )  # List[Tuple[Hashable, Hashable, Hashable]]
    edgesAboutToBeRemoved: Signal = Signal(
        list
    )  # List[Tuple[Hashable, Hashable, Hashable]]
    edgesPropertiesChanged: Signal = Signal(
        dict
    )  # dict[Tuple[Hashable, Hashable, Hashable], dict[str, Any]]
    edgesRemoved: Signal = Signal(
        list
    )  # List[Tuple[Hashable, Hashable, Hashable]]

    def __init__(self, G: nx.MultiDiGraph = nx.MultiDiGraph(), parent=None):
        super().__init__(parent=parent)
        self.G = G

        for n in self.G.nodes:
            node = self.addNode(name=n)

        for e in self.G.edges:
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
        self.nodesPropertiesChanged.emit({n: props})

    def setNodeProperties(self, n: Hashable, /, **props):
        # change guard TODO: find removed props
        change = {}
        for prop, value in props.items():
            if prop not in self.G.nodes[n] or value != self.G.nodes[n][prop]:
                change[prop] = value
        nx.set_node_attributes(self.G, {n: change})
        self.nodesPropertiesChanged.emit({n: change})

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
        self, n: Hashable, /
    ) -> Iterable[tuple[Hashable, Hashable, Hashable]]:
        """retrun incoming edges to the node"""
        for e in self.G.edges(n, keys=True):
            yield e
        # return [(u, v, k) for u, v, k in self.G.out_edges(n, keys=True)]

    def addEdge(
        self, u: Hashable, v: Hashable, k: Hashable | None = None, /, **props
    ) -> None:
        if u not in self.G.nodes:
            self.addNode(u)
        if v not in self.G.nodes:
            self.addNode(v)

        k = self.G.add_edge(
            u, v, k, **props
        )  # note: if k is none, networkx will return a default value for k.
        self.edgesAdded.emit([(u, v, k)])

    def removeEdge(self, u: Hashable, v: Hashable, k: Hashable):
        self.edgesAboutToBeRemoved.emit([(u, v, k)])
        self.G.remove_edge(u, v, k)
        self.edgesRemoved.emit([(u, v, k)])

    def setEdgeProperties(
        self, u: Hashable, v: Hashable, k: Hashable, /, **props
    ):
        nx.set_edge_attributes(self.G, {(u, v, k): props})
        self.edgesPropertiesChanged.emit([(u, v, k)], list(props.keys()))

    def getEdgeProperty(self, u: Hashable, v: Hashable, k: Hashable, prop, /):
        return self.G.edges[u, v, k][prop]

    def isEdgeAllowed(self, u: Hashable, v: Hashable, k: Hashable, /) -> bool:
        if u == v:
            return False
        return True



type NodeId=Hashable
type InletName=str
type OutletName=str
type EdgeId=tuple[NodeId, NodeId, tuple[OutletName, InletName]]

class NXNetworkModel(NXGraphModel):
    def inlets(self, n:NodeId, /)->Iterable[InletName]:
        """override to specify the inlets for a node.
        the default implementation will attempt to return items
        from the 'inlets' node property"""
        if self.hasNodeProperty(n, 'inlets'):
            for key in self.getNodeProperty(n, "inlets"):
                yield key

    def outlets(self, n:Hashable, /)->Iterable[OutletName]:
        """override to specify the outlets for a node.
        the default implementation will attempt to return items
        from the 'outlets' node property"""
        if self.hasNodeProperty(n, 'outlets'):
            for key in self.getNodeProperty(n, "outlets"):
                yield key

    @override
    def addEdge(self, u: Hashable, v: Hashable, k:tuple[str,str], /, **props):
        assert isinstance(k, tuple)
        assert len(k)==2
        assert all(isinstance(_, str) for _ in k)
        super().addEdge(u, v, k, **props)

    @override
    def inEdges(self, n: Hashable, inlet_name:str|None = None, /) -> Iterable[tuple[Hashable, Hashable, Hashable]]:
        """
        return incoming edges to 'n' node.
        if inlet_name is not None return edges directly connectod to the inlet only
        """
        if inlet_name is None:
            """retrun incoming edges to the node"""
            yield from super().inEdges(n)
        else:
            """retrun incoming edges to the inlet"""
            for edge_id in self.G.in_edges(n, keys=True):
                u, v, k = edge_id
                assert isinstance(k, tuple)
                assert len(k)==2
                o, i = k
                if i == inlet_name:
                    yield u, v, k

    @override
    def outEdges(self, n: Hashable, outlet_name:Hashable|None = None, /) -> Iterable[tuple[Hashable, Hashable, Hashable]]:
        """
        return outgoing edges to 'n' node.
        if 'outlet_name' is not None, return edges connectod to the outlet only
        """
        if outlet_name is None:
            """retrun incoming edges to the node"""
            yield from super().outEdges(n)
        else:
            """retrun incoming edges to the inlet"""
            for edge_id in self.G.out_edges(n, keys=True):
                u, v, k = edge_id
                assert isinstance(k, tuple)
                assert len(k)==2
                o, i = k
                if o == outlet_name:
                    yield u, v, k