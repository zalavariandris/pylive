from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.QtGraphEditor.edges_model import EdgesModel
from pylive.QtGraphEditor.models.abstract_graph_model import AbstractGraphModel


class NodeId(QPersistentModelIndex):
    ...


class ProxyGraphModel(AbstractGraphModel):
    def __init__(self, parent:QObject|None=None):
        super().__init__(parent=parent)
        self._nodes = None
        self._edges:EdgesModel|None = None

    def setSourceModel(self, nodes: QAbstractItemModel, edges:EdgesModel):
        if self._nodes:
            # Nodes
            self._nodes.modelReset.disconnect(self.nodesReset.emit)
            self._nodes.rowsInserted.disconnect(self._onNodesInserted)
            self._nodes.rowsAboutToBeRemoved.disconnect(self._onNodesAboutToBeRemoved)
            self._nodes.dataChanged.disconnect(self._onNodeDataChanged)

        if self._edges:
            # Nodes
            self._edges.modelReset.disconnect(self.edgesReset.emit)
            self._edges.rowsInserted.disconnect(self._onEdgesInserted)
            self._edges.rowsAboutToBeRemoved.disconnect(self._onEdgesAboutToBeRemoved)
            self._edges.dataChanged.disconnect(self._onEdgeDataChanged)

        if nodes:
            # Nodes
            nodes.modelReset.connect(self.nodesReset.emit)
            nodes.rowsInserted.connect(self._onNodesInserted)
            nodes.rowsAboutToBeRemoved.connect(self._onNodesAboutToBeRemoved)
            nodes.dataChanged.connect(self._onNodeDataChanged)

        if edges:
            # Nodes
            edges.modelReset.connect(self.edgesReset.emit)
            edges.rowsInserted.connect(self._onEdgesInserted)
            edges.rowsAboutToBeRemoved.connect(self._onEdgesAboutToBeRemoved)
            edges.dataChanged.connect(self._onEdgeDataChanged)

        self._nodes = nodes
        self._edges = edges

    def nodes(self)->Iterable[NodeId]:
        assert self._nodes
        for row in range(self._nodes.rowCount()):
            yield NodeId(self._nodes.index(row, 0))

    def edges(self)->Iterable[NodeId]:
        assert self._edges
        for row in range(self._edges.rowCount()):
            yield NodeId(self._edges.index(row, 0))

    def mapFromSource(self, source_index:QModelIndex)->NodeId:
        ...

    def mapToSource(self, proxyIndex:NodeId)->QModelIndex:
        ...

    def mapSelectionFromSource(self, sourceSelection: QItemSelection)->Iterable[NodeId]:
        ...

    def mapSelectionToSource(self, proxySelection:Iterable[NodeId])->QItemSelection:
        ...

    def sourceModel(self)->tuple[QAbstractItemModel|None, EdgesModel|None]:
        return self._nodes, self._edges

    ### <<< Handle Model Signals
    def _onNodesInserted(self, parent:QModelIndex, first:int, last:int):
        assert self._nodes
        indexes = [
            QPersistentModelIndex(self._nodes.index(row, 0)) 
            for row in range(first, last+1)
        ]
        self.nodesAdded.emit(indexes)

    def _onNodesAboutToBeRemoved(self, parent:QModelIndex, first:int, last:int):
        assert self._nodes
        indexes = [
            QPersistentModelIndex(self._nodes.index(row, 0)) 
            for row in range(first, last+1)
        ]
        self.nodesRemoved.emit(indexes)

    def _onNodeDataChanged(self, top_left:QModelIndex, bottom_right:QModelIndex, roles:list[int]=[]):
        """
        The optional roles argument can be used to specify which data roles have actually been modified.
        An empty vector in the roles argument means that all roles should be considered modified"""
        assert self._nodes
        indexes = [
            QPersistentModelIndex(self._nodes.index(row, 0)) 
            for row in range(top_left.row(), bottom_right.row()+1)
        ]
        self.nodeDataChanged.emit(indexes, roles)

    def _onEdgesInserted(self, parent:QModelIndex, first:int, last:int):
        assert self._edges

        indexes = [
            QPersistentModelIndex(self._edges.index(row, 0))
            for row in range(first, last+1)
        ]

        self.edgesAdded.emit(indexes)

    def _onEdgesAboutToBeRemoved(self, parent:QModelIndex, first:int, last:int):
        assert self._edges
        indexes = [
            QPersistentModelIndex(self._edges.index(row, 0))
            for row in range(first, last+1)
        ]
        self.edgesRemoved.emit(indexes)

    def _onEdgeDataChanged(self, top_left:QModelIndex, bottom_right:QModelIndex, roles:list[int]=[]):
        """
        The optional roles argument can be used to specify which data roles have actually been modified.
        An empty vector in the roles argument means that all roles should be considered modified"""
        assert self._edges
        indexes = [
            QPersistentModelIndex(self._edges.index(row, 0))
            for row in range(top_left.row(), bottom_right.row()+1)
        ]
        self.edgeDataChanged.emit(indexes)