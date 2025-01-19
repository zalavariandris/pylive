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
    # Nodes
    nodesAdded = Signal(list)            #list[_NodeId])
    nodesAboutToBeRemoved = Signal(list) #list[_NodeId])
    nodesRemoved = Signal(list)          #list[_NodeId])

    # Edges
    edgesAdded = Signal(list)            #list[_EdgeId]
    edgesAboutToBeRemoved = Signal(list) #list[_EdgeId]
    edgesRemoved = Signal(list)          #list[_EdgeId]

    ### Node Attributes
    nodeAttributesAdded = Signal(dict)          #dict[_NodeId, list[str]]
    nodeAttributesRemoved = Signal(dict)        #dict[_NodeId, list[str]]
    nodeAttributesAboutToBeRemoved=Signal(dict) #dict[_NodeId, list[str]]
    nodeAttributesChanged = Signal(dict)        #dict[_NodeId, list[str]]

    ### Edge Attributes
    edgeAttributesAdded = Signal(dict)          #dict[_EdgeId, list[str]]
    edgeAttributesAboutToBeRemoved=Signal(dict) #dict[_EdgeId, list[str]]
    edgeAttributesRemoved = Signal(dict)        #dict[_EdgeId, list[str]]
    edgeAttributesChanged = Signal(dict)        #dict[_EdgeId, list[str]]


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

    ### Nodes
    def nodes(self) -> List[Hashable]:
        return [n for n in self.G.nodes]

    def addNode(self, node_id: Hashable, /, **attrs) -> None:
        # print("add node: '{n}'")
        self.G.add_node(node_id, **attrs)
        self.nodesAdded.emit([node_id])
        self.nodeAttributesAdded.emit({node_id: attrs.keys()})

    def removeNode(self, n: Hashable, /):
        self.nodeAttributesAboutToBeRemoved.emit({n: self.nodeAttributes(n)})
        self.nodesAboutToBeRemoved.emit([n])
        self.G.remove_node(n)
        self.nodeAttributesRemoved.emit({n: self.nodeAttributes(n)})
        self.nodesRemoved.emit([n])

    ### EDGES
    def edges(self) -> Iterable[Tuple[Hashable, Hashable, Hashable]]:
        return [(u, v, k) for u, v, k in self.G.edges]

    def inEdges(self, node_id: Hashable, /) -> Iterable[tuple[Hashable, Hashable, Hashable]]:
        """retrun incoming edges to the node"""
        for edge_id in self.G.in_edges(node_id, keys=True):
            yield edge_id
        # return [(u, v, k) for u, v, k in self.G.in_edges(n, keys=True)]

    def outEdges(
        self, node_id: _NodeId, /
    ) -> Iterable[_EdgeId]:
        """retrun incoming edges to the node"""
        for edge_id in self.G.edges(node_id, keys=True):
            yield edge_id
        # return [(u, v, k) for u, v, k in self.G.out_edges(n, keys=True)]

    def addEdge(
        self, u: _NodeId, v: _NodeId, k: Hashable | None = None, /, **attrs
    ) -> None:
        # if u not in self.G.nodes:
        #     self.addNode(u)
        # if v not in self.G.nodes:
        #     self.addNode(v)

        k = self.G.add_edge(
            u, v, k, **attrs
        )  # note: if k is none, networkx will return a default value for k.
        self.edgesAdded.emit([(u, v, k)])
        self.edgeAttributesAdded.emit({(u, v, k): attrs.keys()})

    def removeEdge(self, u: _NodeId, v: _NodeId, k: Hashable):
        edge_id = (u, v, k)
        self.edgeAttributesAboutToBeRemoved.emit({
            edge_id: self.edgeAttributes(*edge_id)
        })
        self.edgesAboutToBeRemoved.emit([edge_id])
        self.G.remove_edge(*edge_id)
        self.edgeAttributesRemoved.emit({
            edge_id: self.edgeAttributes(*edge_id)
        })
        self.edgesRemoved.emit([edge_id])

    def isEdgeAllowed(self, u: _NodeId, v: _NodeId, k: Hashable, /) -> bool:
        if u == v:
            return False
        return True

    ### Node Attributes
    def nodeAttributes(self, node_id: Hashable, /) -> Iterable[str]:
        for key in self.G.nodes[node_id].keys():
            yield key

    def hasNodeAttribute(self, node_id: Hashable, attr, /) -> bool:
        return attr in self.G.nodes[node_id]

    def getNodeAttribute(self, node_id: Hashable, attr, /) -> object:
        return self.G.nodes[node_id][attr]

    def updateNodeAttributes(self, node_id: Hashable, /, **attrs):
        # change guard TODO: find removed attrs
        added_attributes = list()
        changed_attributes = list()
        for attr, value in attrs.items():
            if attr not in self.G.nodes[node_id]:
                self.G.nodes[node_id][attr] = value 
                added_attributes.append(attr)

            if value != self.G.nodes[node_id][attr]:
                self.G.nodes[node_id][attr] = value 
                changed_attributes.append(attr)
        if len(added_attributes)>0:
            self.nodeAttributesAdded.emit({node_id: added_attributes})
        if len(changed_attributes)>0:
            print("changed_attributes", changed_attributes)
            self.nodeAttributesChanged.emit({node_id: changed_attributes})

    def deleteNodeAttribute(self, node_id:Hashable, attr:str, /)->None:
        if attr not in self.G.nodes[node_id]:
            raise KeyError(attr)
        self.nodeAttributesAboutToBeRemoved.emit({
            node_id: [attr]
        })
        del self.G.nodes[node_id][attr]
        self.nodeAttributesRemoved.emit({
            node_id: [attr]
        })

    ### Edge Attributes
    def edgeAttributes(
        self, u: _NodeId, v: _NodeId, k: Hashable, /, **attrs
    )-> Iterable[str]:
        for key in self.G.edges[(u, v, k)].keys():
            yield key

    def hasEdgeAttribute(self, edge_id: _EdgeId, attr, /) -> bool:
        return attr in self.G.edges[edge_id]

    def getEdgeAttribute(self, edge_id: _EdgeId, attr, /) -> object:
        return self.G.edges[edge_id][attr]

    def updateEdgeAttributes(self, edge_id: _EdgeId, /, **attrs):
        # change guard TODO: find removed attrs
        added_attributes = list()
        changed_attributes = list()
        for attr, value in attrs.items():
            if attr not in self.G.edges[edge_id]:
                self.G.edges[edge_id][attr] = value 
                added_attributes.append(attr)

            if value != self.G.edges[edge_id][attr]:
                self.G.edges[edge_id][attr] = value 
                changed_attributes.append(attr)
        if len(added_attributes)>0:
            self.edgeAttributesAdded.emit({edge_id: added_attributes})
        if len(changed_attributes)>0:
            print("changed_attributes", changed_attributes)
            self.edgeAttributesChanged.emit({edge_id: changed_attributes})

    def deleteEdgeAttribute(self, edge_id:_EdgeId, attr:str, /)->None:
        self.edgeAttributesAboutToBeRemoved.emit({
            edge_id: [attr]
        })
        del self.G.edges[edge_id][attr]
        self.edgeAttributesRemoved.emit({
            edge_id: [attr]
        })

