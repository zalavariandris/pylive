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


class EdgesModel(QAbstractItemModel):
    def __init__(self, nodes:QAbstractItemModel, parent: QObject|None=None) -> None:
        super().__init__(parent)

        self._related_nodes = nodes
        nodes.rowsRemoved.connect(self._onRelatedModelRowsRemoved)

        self._DAG = nx.MultiDiGraph()
        self._edges_list:list[EdgeItem] = []

    def _onRelatedModelRowsRemoved(self, parent:QModelIndex, first:int, last:int):
        edge_rows_to_remove = []
        for row, edge in enumerate(self._edges_list):
            SourceExists = first > edge.source.row() or edge.source.row() >last
            TargetExists = first > edge.target.row() or edge.target.row() >last

            if not SourceExists or not TargetExists:
                edge_rows_to_remove.append(row)

        edge_row_groups = group_consecutive_numbers(edge_rows_to_remove)

        for first, last in edge_row_groups:
            self.removeRows(first, count=last-first+1)

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

        if role==Qt.ItemDataRole.DisplayRole or role==Qt.ItemDataRole.EditRole:
            match index.column():
                case 0:
                    match role:
                        case Qt.ItemDataRole.DisplayRole:
                            return f"{item.key}"
                        case Qt.ItemDataRole.EditRole:
                            return item.key

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
        if not target_node_index.isValid() or target_node_index.model() != self._related_nodes:
            return []

        return [(u, k) for u, v, k in self._DAG.in_edges([QPersistentModelIndex(target_node_index)], keys=True)]

    #deprecate
    def source(self, index: QModelIndex|QPersistentModelIndex)->QPersistentModelIndex:
        item = self._edges_list[index.row()]
        return item.source

    #deprecate
    def target(self, index: QModelIndex|QPersistentModelIndex)->QPersistentModelIndex:
        item = self._edges_list[index.row()]
        return item.target

    #deprecate
    def ancestors(self, node_index:QModelIndex, topological=True)->Iterable[QPersistentModelIndex]:
        if not nx.is_directed_acyclic_graph(self._DAG):
            raise ValueError("the graph must be a DAG")
        for n in nx.ancestors(self._DAG, QPersistentModelIndex(node_index)):
            yield n

    def insertRows(self, row, count, parent=QModelIndex()):
        raise NotImplementedError()

    def topologicalSort(self, nodes:Iterable[QModelIndex])->Sequence[QPersistentModelIndex]:
        subgraph:nx.MultiDiGraph = self._DAG.subgraph([QPersistentModelIndex(_) for _ in nodes])
        return [cast(QPersistentModelIndex, _) for _ in nx.topological_sort(subgraph)]

    def addEdgeItem(self, edge:EdgeItem):
        assert isinstance(edge.source, (QModelIndex, QPersistentModelIndex)) 
        assert isinstance(edge.target, (QModelIndex, QPersistentModelIndex))
        assert isinstance(edge.key, str)
        assert edge.source.model() == self._related_nodes
        assert edge.target.model() == self._related_nodes

        assert edge.source.column() == 0
        assert edge.target.column() == 0

        """Inserts rows into the model."""
        if not isinstance(edge.source, (QModelIndex, QPersistentModelIndex)):
            return False

        if edge.source.model() != self._related_nodes:
            return False

        if not isinstance(edge.source, (QModelIndex, QPersistentModelIndex)):
            return False
        if edge.target.model() != self._related_nodes:
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

    def edgeItem(self, row):
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

        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled ### | Qt.ItemFlag.ItemIsEditable

    def index(self, row:int, column:int, parent=QModelIndex()):
        if parent.isValid():
            return QModelIndex()

        return self.createIndex(row, column)

    def parent(self, index:QModelIndex|QPersistentModelIndex)->QModelIndex:
        return QModelIndex()  # No parent for this flat model

    def source_nodes(self, node_index:QModelIndex):
        ...

if __name__ == "__main__":
    from nodes_model import NodesModel, NodeItem
    app = QApplication()
    window = QWidget()
    
    # models
    nodes_model = NodesModel()
    edges_model = EdgesModel(nodes_model)
    

    # widgets
    node_list = QTableView()
    node_list.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
    node_list.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
    node_list.setModel(nodes_model)
    for row, name in enumerate(["node1", "node2", "node3"]):
        nodes_model.insertNodeItem(row, NodeItem(name) )

    # links_list = QListView()
    # links_list.setModel(edges_model)
    links_table = QTableView()
    links_table.setModel(edges_model)

    # actions
    def link_selected_nodes():
        source = node_list.currentIndex()

        selected_rows = {index.siblingAtColumn(0) for index in node_list.selectedIndexes()}
        for target in selected_rows:
            if target!=source:
                edges_model.addEdgeItem(EdgeItem(
                    QPersistentModelIndex(source), 
                    QPersistentModelIndex(target), 
                    "in")
                )

    def remove_selected_link():
        print("remove selected link")

    link_selected_action = QAction("link selected", window)
    link_selected_action.triggered.connect(link_selected_nodes)
    remove_link_action = QAction("remove link", window)
    remove_link_action.triggered.connect(remove_selected_link)

    menubar = QMenuBar()
    menubar.addAction(link_selected_action)

    # layout
    main_layout = QHBoxLayout()
    main_layout.setMenuBar(menubar)
    main_layout.addWidget(node_list)
    main_layout.addWidget(links_table)
    # main_layout.addWidget(links_list)
    window.setLayout(main_layout)
    window.show()
    app.exec()
