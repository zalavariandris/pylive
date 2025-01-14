from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel

type _NodeId=Hashable
type _OutletName=str
type _InletName=str
type _EdgeId=tuple[_NodeId, _NodeId, tuple[_OutletName, _InletName]]


class NXNetworkModel(NXGraphModel):
    def inlets(self, n:_NodeId, /)->Iterable[_InletName]:
        """override to specify the inlets for a node.
        the default implementation will attempt to return items
        from the 'inlets' node property"""
        if self.hasNodeProperty(n, 'inlets'):
            for key in self.getNodeProperty(n, "inlets"):
                yield key

    def outlets(self, n:_NodeId, /)->Iterable[_OutletName]:
        """override to specify the outlets for a node.
        the default implementation will attempt to return items
        from the 'outlets' node property"""
        if self.hasNodeProperty(n, 'outlets'):
            for key in self.getNodeProperty(n, "outlets"):
                yield key

    @override
    def addEdge(self, u: _NodeId, v: _NodeId, k:tuple[str,str], /, **props):
        assert isinstance(k, tuple)
        assert len(k)==2
        assert all(isinstance(_, str) for _ in k)
        super().addEdge(u, v, k, **props)

    @override
    def inEdges(self, n: _NodeId, inlet_name:_InletName|None = None, /) -> Iterable[tuple[_NodeId, _NodeId, Hashable]]:
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
    def outEdges(self, n: _NodeId, outlet_name:_OutletName|None = None, /) -> Iterable[tuple[_NodeId, _NodeId, Hashable]]:
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