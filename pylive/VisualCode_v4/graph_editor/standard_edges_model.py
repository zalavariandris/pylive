from re import sub
from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from dataclasses import dataclass

from pylive.utils import group_consecutive_numbers

@dataclass
class StandardEdgeItem:
    source: QPersistentModelIndex
    target: QPersistentModelIndex
    outlet: str
    inlet:str
    

import networkx as nx


class StandardEdgesModel(QAbstractItemModel):
    def __init__(self, nodes:QAbstractItemModel, parent: QObject|None=None) -> None:
        super().__init__(parent)
        self._nodes = nodes
        nodes.rowsRemoved.connect(self._onRelatedModelRowsRemoved)

        self._DAG:nx.MultiDiGraph[T] = nx.MultiDiGraph()
        self._edges_list:list[StandardEdgeItem] = []

    def nodes(self)->QAbstractItemModel|None:
        return self._nodes

    def source(self, row:int)->tuple[QModelIndex, str]:
        edge_item = self.edgeItem(row)
        return self._nodes.index(edge_item.source.row(), 0), edge_item.outlet

    def target(self, row:int)->tuple[QModelIndex, str]:
        edge_item = self.edgeItem(row)
        return self._nodes.index(edge_item.target.row(), 0), edge_item.inlet

    def appendEdgeItem(self, edge:StandardEdgeItem):
        assert isinstance(edge.source, (QModelIndex, QPersistentModelIndex)) 
        assert isinstance(edge.target, (QModelIndex, QPersistentModelIndex))
        assert isinstance(edge.outlet, str)
        assert isinstance(edge.inlet, str)
        assert edge.source.model() == self._nodes
        assert edge.target.model() == self._nodes

        assert edge.source.column() == 0
        assert edge.target.column() == 0

        """Inserts rows into the model."""
        if not isinstance(edge.source, (QModelIndex, QPersistentModelIndex)):
            return False

        if edge.source.model() != self._nodes:
            return False

        if not isinstance(edge.source, (QModelIndex, QPersistentModelIndex)):
            return False
        if edge.target.model() != self._nodes:
            return False

        parent = QModelIndex()
        row = self.rowCount()
        count=1
        self.beginInsertRows(parent, row, row + count - 1)
        for _ in range(count):
            source = QPersistentModelIndex(edge.source)
            target = QPersistentModelIndex(edge.target)
            self._edges_list.insert(row, edge)
            self._DAG.add_edge(edge.source, edge.target, (edge.outlet, edge.inlet), item=edge )
        self.endInsertRows()
        return True

    def edgeItem(self, row:int):
        return self._edges_list[row]

    def removeRows(self, row:int, count:int, parent=QModelIndex()):
        """Removes rows from the model."""
        if row < 0 or row + count > len(self._edges_list):
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        for row in reversed(range(row, row+count)):
            edge = self._edges_list[row]
            self._DAG.remove_edge(edge.source, edge.target, (edge.outlet, edge.inlet))
            del self._edges_list[row]
        self.endRemoveRows()
        return True

    def _onRelatedModelRowsRemoved(self, parent:QModelIndex, first:int, last:int):
        edge_rows_to_remove = []
        for row, edge in enumerate(self._edges_list):
            SourceExists = first <= edge.source.row() <= last
            TargetExists = first <= edge.target.row() <= last
            if SourceExists or TargetExists:
                edge_rows_to_remove.append(row)

        edge_row_groups = [_ for _ in group_consecutive_numbers(edge_rows_to_remove)]
        print(edge_row_groups)
        for edge_range in edge_row_groups:
            self.removeRows(edge_range.start, count=edge_range.stop-edge_range.start)

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows in the model."""
        return len(self._edges_list)
        # return len(self._edges)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role==Qt.ItemDataRole.DisplayRole:
            return ["source", "outlet", "target", "inlet"][section]
        else:
            return super().headerData(section, orientation, role)

    def columnCount(self, parent: QModelIndex|QPersistentModelIndex = QModelIndex()) -> int:
        return 4

    def setData(self, index: QModelIndex|QPersistentModelIndex, value:Any, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        raise NotImplementedError("edges are immutable and not allow to edit")

    def data(self, index: QModelIndex|QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._edges_list):
            return None

        item = self._edges_list[index.row()]
        from pylive.VisualCode_v4.graph_editor.graph_editor_view import GraphEditorView
        # if role==Qt.ItemDataRole.DisplayRole or role==Qt.ItemDataRole.EditRole:
        match index.column():
            case 0: # source node
                match role:
                    case Qt.ItemDataRole.DisplayRole:
                        return self._nodes.data(item.source, Qt.ItemDataRole.DisplayRole)

            case 1: # source outlet
                match role:
                    case Qt.ItemDataRole.DisplayRole:
                        return f"{item.outlet}"

            case 2: # target node
                match role:
                    case Qt.ItemDataRole.DisplayRole:
                        return self._nodes.data(item.target, Qt.ItemDataRole.DisplayRole)
                
            case 3: # target inlet
                match role:
                    case Qt.ItemDataRole.DisplayRole:
                        return f"{item.inlet}"

        return None

    def in_edges(self, target_node_index:QModelIndex|QPersistentModelIndex)->Sequence[StandardEdgeItem]:
        if not target_node_index.isValid() or target_node_index.model() != self._nodes:
            return []

        edge_items:list[StandardEdgeItem] = []
        for u, v, k in self._DAG.in_edges([QPersistentModelIndex(target_node_index)], keys=True):
            edge_item = self._DAG.edges[ (u,v,k) ]["item"]
            assert isinstance(edge_item, StandardEdgeItem), f"got: {edge_item}"
            edge_items.append( edge_item )

        return edge_items

    # #deprecate
    # def source(self, index: QModelIndex|QPersistentModelIndex)->QPersistentModelIndex:
    #     item = self._edges_list[index.row()]
    #     return item.source

    # #deprecate
    # def target(self, index: QModelIndex|QPersistentModelIndex)->QPersistentModelIndex:
    #     item = self._edges_list[index.row()]
    #     return item.target

    # #deprecate
    # def ancestors(self, node_index:QModelIndex, topological=True)->Iterable[QPersistentModelIndex]:
    #     if not nx.is_directed_acyclic_graph(self._DAG):
    #         raise ValueError("the graph must be a DAG")
    #     for n in nx.ancestors(self._DAG, QPersistentModelIndex(node_index)):
    #         yield n


    def topologicalSort(self, nodes:Iterable[QModelIndex])->Sequence[QPersistentModelIndex]:
        subgraph:nx.MultiDiGraph = self._DAG.subgraph([QPersistentModelIndex(_) for _ in nodes])
        return [cast(QPersistentModelIndex, _) for _ in nx.topological_sort(subgraph)]

    def flags(self, index):
        """Returns the item flags for the given index."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        return flags

    def index(self, row:int, column:int, parent=QModelIndex()):
        if parent.isValid():
            return QModelIndex()

        return self.createIndex(row, column)

    def parent(self, index:QModelIndex|QPersistentModelIndex)->QModelIndex:
        return QModelIndex()  # No parent for this flat model



