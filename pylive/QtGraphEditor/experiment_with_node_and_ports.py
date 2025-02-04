
from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from networkx import reverse

from dataclasses import dataclass


class Port:
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent


class Node:
    def __init__(self, name):
        self.name = name
        self.inlets = []
        self.outlets = []


class NodeTreeModel(QAbstractItemModel):
    def __init__(self, data:dict[str, list[str]], parent:QObject|None=None):
        super().__init__(parent=parent)
        self._nodes = []
        for node_name, port_names in data.items():
            node = Node(node_name)

            for port_name in port_names:
                port = Port(port_name, node)
                node.inlets.append(port)
            self._nodes.append(node)

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            node = parent.internalPointer()
            return len(node.inlets) if isinstance(node, Node) else 0
        else:
            return len(self._nodes)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return 1

    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        node = index.internalPointer()
        
        if role in {Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole}:
            if isinstance(node, Port):  # Inlet
                return node.name
            elif isinstance(node, Node):  # Node name
                return node.name

        return None

    def parent(self, index: QModelIndex | QPersistentModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        node = index.internalPointer()

        if isinstance(node, Port):  # If it's a port, return its parent node
            parent_node = node.parent
            row = self._nodes.index(parent_node) if parent_node in self._nodes else 0
            return self.createIndex(row, 0, parent_node)

        return QModelIndex()  # Root-level nodes have no parent

    def index(self, row: int, column: int, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> QModelIndex:
        if parent.isValid():
            node = parent.internalPointer()
            return self.createIndex(row, column, node.inlets[row])
        else:
            return self.createIndex(row, column, self._nodes[row])

    def flags(self, index:QModelIndex|QPersistentModelIndex):
        if not index.isValid():
            return None

        node = index.internalPointer()

        flags = Qt.ItemFlag.ItemIsEnabled
        if isinstance(node, Port):  # Inlet
            flags |= Qt.ItemFlag.ItemIsSelectable
        elif isinstance(node, Node):  # Node name
            flags |= Qt.ItemFlag.ItemIsSelectable

        return flags


if __name__ == "__main__":
    app = QApplication()
    window = QWidget()

    nodes = NodeTreeModel({
        "node1": ["in1", "in2"],
        "node2": ["in1", "in2"],
        "node3": ["in1", "in2"]
    })

    selection = QItemSelectionModel(nodes)
    node_list = QListView()
    node_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    node_list.setModel(nodes)
    node_list.setSelectionModel(selection)
    node_tree = QTreeView()
    node_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    node_tree.setModel(nodes)
    node_tree.setSelectionModel(selection)

    layout = QHBoxLayout()
    layout.addWidget(node_list)
    layout.addWidget(node_tree)
    window.setLayout(layout)
    window.show()
    app.exec()
