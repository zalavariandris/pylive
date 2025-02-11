from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from numpy import isin

from pylive.VisualCode_NetworkX.UI.nx_graph_model import NXGraphModel

type _NodeId=Hashable
type _OutletName=str
type _InletName=str
type _EdgeId=tuple[_NodeId, _NodeId, tuple[_OutletName, _InletName]]


class NXNetworkModel(NXGraphModel):
    def inlets(self, node_id:_NodeId, /)->Iterable[_InletName]:
        """override to specify the inlets for a node.
        the default implementation will attempt to return items
        from the 'inlets' node attribute"""
        if self.hasNodeAttribute(node_id, 'inlets'):
            attributes = self.getNodeAttribute(node_id, "inlets")
            assert hasattr(attributes, '__iter__')
            for key in attributes: #type: ignore
                yield key

    def outlets(self, node_id:_NodeId, /)->Iterable[_OutletName]:
        """override to specify the outlets for a node.
        the default implementation will attempt to return items
        from the 'outlets' node attribute"""
        if self.hasNodeAttribute(node_id, 'outlets'):
            attributes = self.getNodeAttribute(node_id, "outlets")
            assert hasattr(attributes, '__iter__')
            for key in attributes: #type: ignore
                yield key

    # @override
    # def addNode(self, node_id: Hashable, /,*, inlets:list[Hashable], outlets:list[Hashable], **attrs) -> None:
    #     return super().addNode(node_id, _inlets=inlets, _outlets=outlets, **attrs)

    # @override
    # def nodeAttributes(self, node_id: Hashable, /) -> Iterable[str]:
    #     for attr in super().nodeAttributes(node_id):
    #         if  isinstance(attr, str) and attr.startswith("_"):
    #             ...
    #         else:
    #             yield attr

    @override
    def addEdge(self, u: _NodeId, v: _NodeId, k:tuple[str,str], /, **attrs):
        assert isinstance(k, tuple)
        assert len(k)==2
        assert all(isinstance(_, str) for _ in k)
        super().addEdge(u, v, k, **attrs)

    @override
    def inEdges(self, node_id: _NodeId, inlet_name:_InletName|None = None, /) -> Iterable[tuple[_NodeId, _NodeId, Hashable]]:
        """
        return incoming edges to 'n' node.
        if inlet_name is not None return edges directly connectod to the inlet only
        """
        if inlet_name is None:
            """retrun incoming edges to the node"""
            yield from super().inEdges(node_id)
        else:
            """retrun incoming edges to the inlet"""
            assert node_id is not None
            for edge_id in self.G.in_edges(node_id, keys=True):
                assert isinstance(edge_id, tuple) and len(edge_id)==3
                u, v, k = edge_id
                assert isinstance(k, tuple)
                assert len(k)==2
                o, i = k
                if i == inlet_name:
                    yield u, v, k

    @override
    def outEdges(self, node_id: _NodeId, outlet_name:_OutletName|None = None, /) -> Iterable[tuple[_NodeId, _NodeId, Hashable]]:
        """
        return outgoing edges to 'n' node.
        if 'outlet_name' is not None, return edges connectod to the outlet only
        """
        if outlet_name is None:
            """retrun incoming edges to the node"""
            yield from super().outEdges(node_id)
        else:
            """retrun incoming edges to the inlet"""
            assert node_id is not None
            for edge_id in self.G.out_edges(node_id, keys=True):
                assert isinstance(edge_id, tuple) and len(edge_id)==3
                u, v, k = edge_id
                assert isinstance(k, tuple)
                assert len(k)==2
                o, i = k
                if o == outlet_name:
                    yield u, v, k