from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from networkx.classes import graphviews

from pylive.qt_options_dialog import QOptionDialog

# from dataclasses import dataclass
# @dataclass
# class Node:
#     display: str
#     content: str

# @dataclass
# class Edge:
#     source: Node
#     target: Node
#     display: str

# @dataclass
# class Graph:
#     nodes:list[Node]
#     edges:list[Edge]

# @dataclass
# class Scene:
#     definitions:str
#     graph: Graph

#     def serialize(self)->str:
#         return yaml.dump({
#             'definitions': self.definitions,
#         })

#     def deserialize(self, text:str):
#         # parse yaml
#         data = yaml.load(text, Loader=yaml.SafeLoader)

#         # set definitions
#         self.definitions = data['definitions']

#         #parse graph
#         nodes = [Node(_['name'], _['func']) for _ in data['graph']['nodes']]
#         edges = [Edge(_[0], _[1], _[2]) for _ in data['graph']['edges']]
#         self.graph = Graph(nodes, edges)


class Window(QWidget):
    FunctionRole = Qt.ItemDataRole.UserRole
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        ### model state
        self.nodes = QStandardItemModel()
        self.nodes.setHeaderData(0, Qt.Orientation.Horizontal, "name")
        self.edges = QStandardItemModel()
        self.edges.setHeaderData(0, Qt.Orientation.Horizontal, "key")
        self.node_selection = QItemSelectionModel(self.nodes)
        self.edge_selection = QItemSelectionModel(self.edges)

        self.definitions_model = QStandardItemModel()
        
        ### actions, commands
        self.nodes.rowsInserted.connect(lambda: print("rows inserted"))
        ### view

        from pylive.QtScriptEditor.script_edit import ScriptEdit
        self.definitions_editor = ScriptEdit()

        self.graph_view = QGraphicsView()
        self.graph_view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.graph_view.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
        self.graph_view.setWindowTitle("NXNetworkScene")
        self.graph_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.graph_view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.graph_view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.graph_view.installEventFilter(self)

        nodelist = QListView()
        nodelist.setModel(self.nodes)
        nodelist.setSelectionModel(self.node_selection)
        nodelist.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        edgelist = QListView()
        edgelist.setModel(self.edges)

        ### Grahp editor
        from qt_graph_editor_scene import QGraphEditorScene
        graph_scene = QGraphEditorScene()
        graph_scene.setModel(self.nodes, self.edges)
        graph_scene.setSceneRect(QRectF(-400, -400, 800, 800))
        graph_scene.setSelectionModel(self.node_selection)
        self.graph_view.setScene(graph_scene)

        # Actions
        execute_definitions_action = QAction("Execute definitions", self)
        execute_definitions_action.triggered.connect(self.execute_definitions)

        add_node_action = QAction("add new node", self)
        add_node_action.triggered.connect(self.create_new_node)
        delete_node_action = QAction("delete node", self)
        delete_node_action.triggered.connect(self.delete_selected_nodes)
        connect_selected_nodes_action = QAction("connect selected nodes", self)
        connect_selected_nodes_action.triggered.connect(self.connect_selected_nodes)
        remove_edge_action = QAction("remove edge", self)
        remove_edge_action.triggered.connect(self.delete_selected_edges)
        layout_action = QAction("layout", self)
        layout_action.triggered.connect(graph_scene.layout)

        menubar = QMenuBar(parent=self)
        menubar.addAction(execute_definitions_action)
        menubar.addAction(add_node_action)
        menubar.addAction(delete_node_action)
        menubar.addAction(connect_selected_nodes_action)
        menubar.addAction(remove_edge_action)
        menubar.addAction(layout_action)

        ### Layout
        grid_layout = QGridLayout()
        grid_layout.setMenuBar(menubar)
        # grid_layout.addWidget(nodelist, 1, 0)
        # grid_layout.addWidget(edgelist, 1, 1)
        grid_layout.addWidget(self.definitions_editor, 0, 0, 1, 1)
        grid_layout.addWidget(self.graph_view, 0, 1, 1, 1)
        self.setLayout(grid_layout)

    # def _builtins(self):
    #     # display module members
    #     for key in dir(__builtins__):
    #         if not key.startswith("_"):
    #             item = getattr(__builtins__, key)
    #             if callable(item):
    #                 yield key

    # def _pathlib_module_functions(self):
    #     import pathlib
    #     import string
    #     for key in dir(pathlib):
    #         if key[0] in string.ascii_letters: 
    #             item = getattr(pathlib,key)
    #             if callable(item):
    #                 yield key

    @Slot()
    def execute_definitions(self):
        definitions_script = self.definitions_editor.toPlainText()

        try:
            capture = {'__builtins__': __builtins__}
            exec(definitions_script, capture)


            for key, value in capture.items():
                if key!='__builtins__':
                    if callable(value):
                        fn_item = QStandardItem()
                        fn_item.setData(key, Qt.ItemDataRole.DisplayRole)
                        fn_item.setData(key, self.FunctionRole)
                        self.definitions_model.insertRow(self.definitions_model.rowCount(), fn_item)
                        print(f"- {key}: {value}")
        except Exception as err:
            QMessageBox.critical(self, "Error", f"{err}")

    @Slot()
    def create_new_node(self):
        ###
        if self.definitions_model.rowCount()==0:
            QMessageBox.warning(self, "No definiions!", "please create function definitions!")
            return

        from itertools import chain
        # node_name, accepted =  QOptionDialog.getItem(self , "Title", "label", ['print', "write"], 0, editable=True)
        items = {self.definitions_model.index(row, 0).data(Qt.DisplayRole): self.definitions_model.index(row, 0).data(self.FunctionRole) for row in range(self.definitions_model.rowCount())}

        node_key, accepted =  QOptionDialog.getItem(self , "Title", "label", items.keys() , 0)
        if node_key and accepted:
            from pylive.utils.unique import make_unique_name
            node_names = [self.nodes.data(self.nodes.index(row, 0), Qt.ItemDataRole.DisplayRole) for row in  range(self.nodes.rowCount())]
            node_key = make_unique_name(node_key, node_names)
            item = QStandardItem()
            item.setData(f"{node_key}", Qt.ItemDataRole.DisplayRole)
            item.setData(items[node_key], self.FunctionRole)
            self.nodes.insertRow(self.nodes.rowCount(), item)

    @Slot()
    def delete_selected_nodes(self):
        indexes:list[QModelIndex] = self.node_selection.selectedRows(column=0)
        for index in sorted(indexes, key=lambda idx:idx.row(), reverse=True):
            self.nodes.removeRows(index.row(), 1)

    @Slot()
    def connect_selected_nodes(self):
        print("connect selected nodes")

        if len(self.node_selection.selectedRows(0))<2:
            return

        target_node = self.node_selection.currentIndex().siblingAtColumn(0)
        assert target_node.isValid()
        for source_node in self.node_selection.selectedRows(0):
            if target_node == source_node:
                continue

            assert source_node.isValid()

            item = QStandardItem()
            item.setData(QPersistentModelIndex(source_node), QGraphEditorScene.SourceRole)
            item.setData(QPersistentModelIndex(target_node), QGraphEditorScene.TargetRole)
            item.setData("in", Qt.ItemDataRole.DisplayRole)
            self.edges.insertRow(self.edges.rowCount(), item)

    @Slot()
    def delete_selected_edges(self):
        indexes:list[QModelIndex] = self.edge_selection.selectedRows(column=0)
        for index in sorted(indexes, key=lambda idx:idx.row(), reverse=True):
            self.edges.removeRows(index.row(), 1)

    def eventFilter(self, watched, event):
        if watched == self.graph_view:
            if event.type() == QEvent.Type.MouseButtonDblClick:
                self.create_new_node()
                return True

        return super().eventFilter(watched, event)

if __name__ == "__main__":
    app = QApplication()
    window = Window()
    

    window.show()

    app.exec()

