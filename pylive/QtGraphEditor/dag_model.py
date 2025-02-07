from re import sub
from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from dataclasses import dataclass

from pylive.utils import group_consecutive_numbers

@dataclass
class EdgeItem:
    source: QPersistentModelIndex
    target: QPersistentModelIndex
    key: str
    

import networkx as nx


class DAGModel(QAbstractItemModel):
    def __init__(self, nodes:QAbstractItemModel, parent: QObject|None=None) -> None:
        super().__init__(parent)
        self._nodes = nodes
        # nodes.rowsRemoved.connect(self._onRelatedModelRowsRemoved)
        # nodes.rowsMoved.connect(self._onRelatedModelRowsMoved)

        self._DAG:nx.MultiDiGraph = nx.MultiDiGraph()
        self._edges_list:list[EdgeItem] = []

    def nodes(self):
        return self._nodes

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

    def _onRelatedModelRowsMoved(self, parent: QModelIndex, start: int, end: int, destinationParent: QModelIndex, destinationRow: int):
        """
        Adjusts edge references when nodes are moved.
        
        - `start`: First moved row
        - `end`: Last moved row
        - `destinationRow`: New starting position
        """

        if parent != destinationParent:
            return  # Ignore moves across different parents

        moved_range = set(range(start, end + 1))
        offset = destinationRow - start
        index_map = {}

        for edge in self._edges_list:
            old_source_row = edge.source.row()
            old_target_row = edge.target.row()

            # Update source index
            if old_source_row in moved_range:
                new_source_row = old_source_row + offset
                index_map[old_source_row] = new_source_row
                edge.source = self._nodes.index(new_source_row, 0)

            # Update target index
            if old_target_row in moved_range:
                new_target_row = old_target_row + offset
                index_map[old_target_row] = new_target_row
                edge.target = self._nodes.index(new_target_row, 0)

        # Rebuild DAG with updated indices
        self._DAG.clear()
        for edge in self._edges_list:
            self._DAG.add_edge(edge.source, edge.target, edge.key)

        self.dataChanged.emit(QModelIndex(), QModelIndex())  # Notify views of the change


    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows in the model."""
        return len(self._edges_list)
        # return len(self._edges)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role==Qt.ItemDataRole.DisplayRole:
            return ["key", "source", "target"][section]
        else:
            return super().headerData(section, orientation, role)

    def columnCount(self, parent: QModelIndex|QPersistentModelIndex = QModelIndex()) -> int:
        return 3

    def setData(self, index: QModelIndex|QPersistentModelIndex, value:Any, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._edges_list):
            return None

        # item = self._edges_list[index.row()]
        # if role==Qt.ItemDataRole.DisplayRole or role==Qt.ItemDataRole.EditRole:
        #     match index.column():
        #         case 0:
        #             item.key = value
        #             self.dataChanged.emit(index, index, [role])
        #             return True

        #         case 1:
        #             item.source = value
        #             self.dataChanged.emit(index, index, [role])
        #             return True
                    
        #         case 2:
        #             item.target = value
        #             self.dataChanged.emit(index, index, [role])
        #             return True  
                    
        # return False

    def data(self, index: QModelIndex|QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._edges_list):
            return None

        item = self._edges_list[index.row()]
        from pylive.QtGraphEditor.dag_editor_view import DAGEditorView
        # if role==Qt.ItemDataRole.DisplayRole or role==Qt.ItemDataRole.EditRole:
        match index.column():
            case 0:
                match role:
                    case Qt.ItemDataRole.DisplayRole:
                        return f"{item.key}"
                    case Qt.ItemDataRole.EditRole:
                        return item.key
                    case DAGEditorView.SourceRole:
                        return item.source
                    case DAGEditorView.TargetRole:
                        return item.target

            case 1:
                match role:
                    case Qt.ItemDataRole.DisplayRole:
                        return f"{item.source.data(Qt.ItemDataRole.DisplayRole)}"
                    case Qt.ItemDataRole.EditRole:
                        return item.source
                
            case 2:
                match role:
                    case Qt.ItemDataRole.DisplayRole:
                        return f"{item.target.data(Qt.ItemDataRole.DisplayRole)}"
                    case Qt.ItemDataRole.EditRole:
                        return item.target

                

        return None

    def inputs(self, target_node_index:QModelIndex|QPersistentModelIndex)->Sequence[tuple[QModelIndex, str]]:
        if not target_node_index.isValid() or target_node_index.model() != self._nodes:
            return []

        return [(u, k) for u, v, k in self._DAG.in_edges([QPersistentModelIndex(target_node_index)], keys=True)]

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

    def addEdgeItem(self, edge:EdgeItem):
        assert isinstance(edge.source, (QModelIndex, QPersistentModelIndex)) 
        assert isinstance(edge.target, (QModelIndex, QPersistentModelIndex))
        assert isinstance(edge.key, str)
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
            self._DAG.add_edge(edge.source, edge.target, edge.key)
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
            self._DAG.remove_edge(edge.source, edge.target, edge.key)
            del self._edges_list[row]
        self.endRemoveRows()
        return True

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



