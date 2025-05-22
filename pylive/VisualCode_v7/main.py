from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QHBoxLayout, QTreeView
from graphview import GraphView



class LinkTableDelegate(QStyledItemDelegate):
    def displayText(self, value: Any, locale: QLocale | QLocale.Language, /) -> str:
        print("display text for", value)
        match value:
            case QPersistentModelIndex():
                text = ""
                index = value
                path  = []
                while index.isValid():
                    path.append(index)
                    # text = f"{index.data(Qt.ItemDataRole.DisplayRole)}.{text}"
                    index = index.parent()



                return ".".join( map(lambda index: index.data(Qt.ItemDataRole.DisplayRole), reversed(path)) )
            case _:
                return super().displayText(value, locale)
        

class MainWindow(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)

        ### Setup base model
        self.nodes = QStandardItemModel()
        self.nodes.setHorizontalHeaderLabels(["name", "kind", "content", "pos"])
        self.links = QStandardItemModel()
        self.links.setHorizontalHeaderLabels(["source", "target"])

        node1 = [QStandardItem("node1"), QStandardItem("node"), QStandardItem("content"), QStandardItem("[0,0]")]
        self.nodes.appendRow(node1)
        node1[0].appendRow([QStandardItem("in"), QStandardItem("inlet")])
        node1[0].appendRow([QStandardItem("out"), QStandardItem("outlet")])

        node2 = [QStandardItem("node2"), QStandardItem("node"), QStandardItem("content"), QStandardItem("[0,100]")]
        self.nodes.appendRow(node2)
        node2[0].appendRow([QStandardItem("in"), QStandardItem("inlet")])
        node2[0].appendRow([QStandardItem("out"), QStandardItem("outlet")])

        ### Setup table views
        self.node_tree = QTreeView()
        self.node_tree.setModel(self.nodes)
        self.node_tree.expandAll()

        self.link_table = QTableView()
        link_table_delegate = LinkTableDelegate()
        self.link_table.setItemDelegate(link_table_delegate)
        self.link_table.setModel(self.links)
        source_item = QStandardItem()
        source_item.setFlags(source_item.flags() & ~Qt.ItemIsEditable)
        # source_item.setData("node1", Qt.ItemDataRole.DisplayRole)
        source_item.setData(QPersistentModelIndex(node1[0].child(1,0).index()), Qt.ItemDataRole.EditRole)
        target_item = QStandardItem()
        target_item.setFlags(target_item.flags() & ~Qt.ItemIsEditable)
        # target_item.setData("node2", Qt.ItemDataRole.DisplayRole)
        target_item.setData(QPersistentModelIndex(node2[0].child(0,0).index()), Qt.ItemDataRole.EditRole)
        self.links.appendRow([source_item, target_item])

        ### Setup Graphview
        self.graphview = GraphView()
        self.graphview.setModel( self.nodes, self.links )

        ### Setup Lazout
        layout = QHBoxLayout()
        layout.addWidget(self.node_tree)
        layout.addWidget(self.link_table)
        layout.addWidget(self.graphview)
        self.setLayout(layout)

    def sizeHint(self):
        return QSize(2048, 900) 

    ### Commands
    def create_new_node(self, scenepos:QPointF=QPointF()):
        assert self._model
        existing_names = list(self._model.nodes())

        func_name = make_unique_id(6)
        self._model.addNode(func_name, "None", kind='expression')

        ### position node widget
        node_graphics_item = self.graph_view.nodeItem(func_name)
        if node_graphics_item := self.graph_view.nodeItem(func_name):
            node_graphics_item.setPos(scenepos-node_graphics_item.boundingRect().center())

    def delete_selected(self):
        assert self._model
        # delete selected links
        link_indexes:list[QModelIndex] = self.link_selection_model.selectedIndexes()
        link_rows = set(index.row() for index in link_indexes)
        for link_row in sorted(link_rows, reverse=True):
            source, target, outlet, inlet = self.link_proxy_model.mapToSource(self.link_proxy_model.index(link_row, 0))
            self._model.unlinkNodes(source, target, outlet, inlet)

        # delete selected nodes
        node_indexes:list[QModelIndex] = self.node_selection_model.selectedRows(column=0)
        for node_index in sorted(node_indexes, key=lambda idx:idx.row(), reverse=True):
            node = self.node_proxy_model.mapToSource(node_index)
            self._model.removeNode(node)

    def connect_nodes(self, source:str, target:str, inlet:str):
        assert self._model
        self._model.linkNodes(source, target, "out", inlet)

    def eventFilter(self, watched, event):
        if watched == self.graph_view:
            ### Create node on double click
            if event.type() == QEvent.Type.MouseButtonDblClick:
                event = cast(QMouseEvent, event)
                self.create_new_node(self.graph_view.mapToScene(event.position().toPoint()))
                return True

        return super().eventFilter(watched, event)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    import pathlib
    parent_folder = pathlib.Path(__file__).parent.resolve()
    print("Python Visual Editor starting...\n  working directory:", Path.cwd())

    app = QApplication([])

    window = MainWindow()
    window.setGeometry(QRect(QPoint(), app.primaryScreen().size()).adjusted(40,80,-30,-300))
    window.show()
    app.exec()
    # window.openFile(Path.cwd()/"./tests/dissertation_builder.yaml")

    