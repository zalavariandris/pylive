from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from networkx.classes import graphviews

from pylive.qt_options_dialog import QOptionDialog

from dataclasses import dataclass
@dataclass
class Node:
    display: str
    content: str

@dataclass
class Edge:
    source: Node
    target: Node
    display: str

@dataclass
class Graph:
    nodes:list[Node]
    edges:list[Edge]

@dataclass
class Scene:
    definitions:str
    graph: Graph

    def serialize(self)->str:
        import yaml
        return yaml.dump({
            'definitions': self.definitions,
        })

    def deserialize(self, text:str):
        import yaml
        # parse yaml
        data = yaml.load(text, Loader=yaml.SafeLoader)

        # set definitions
        self.definitions = data['definitions']

        #parse graph
        nodes = [Node(_['name'], _['func']) for _ in data['graph']['nodes']]
        edges = [Edge(_[0], _[1], _[2]) for _ in data['graph']['edges']]
        self.graph = Graph(nodes, edges)


from pylive.QtLiveApp.document_file_link import DocumentFileLink
from qt_graph_editor_scene import QGraphEditorScene
from pylive.QtScriptEditor.script_edit import ScriptEdit

class SceneModel(QObject):
    DefinitionFunctionRole = Qt.ItemDataRole.UserRole
    NodeDefinitionRole = Qt.ItemDataRole.UserRole
    def __init__(self, parent:QObject|None=None):
        super().__init__(parent=parent)
        self.nodes = QStandardItemModel()
        self.nodes.setHeaderData(0, Qt.Orientation.Horizontal, "name")

        self.edges = QStandardItemModel()
        self.edges.setHeaderData(0, Qt.Orientation.Horizontal, "key")

        self.node_selection = QItemSelectionModel(self.nodes)
        self.edge_selection = QItemSelectionModel(self.edges)

        self.definitions_model = QStandardItemModel()
        self.definitions_model.setHeaderData(0, Qt.Orientation.Horizontal, "name")

    def fromData(self, data:Scene):
        self.definitions_model.beginResetModel()
        self.nodes.beginResetModel()
        self.edges.beginResetModel()
        ...

        self.definitions_model.endResetModel()
        self.nodes.endResetModel()
        self.edges.endResetModel()

        self.node_selection.setModel(self.nodes)
        self.edge_selection.setModel(self.edges)


    def toData(self)->Scene:
        ...


class Window(QWidget):
    DefinitionFunctionRole = Qt.ItemDataRole.UserRole
    NodeDefinitionRole = Qt.ItemDataRole.UserRole
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        ### model state
        self.nodes = QStandardItemModel()
        self.nodes.setHeaderData(0, Qt.Orientation.Horizontal, "name")
        self.edges = QStandardItemModel()
        self.edges.setHeaderData(0, Qt.Orientation.Horizontal, "key")
        self.node_selection = QItemSelectionModel(self.nodes)
        self.edge_selection = QItemSelectionModel(self.edges)

        self.document = QTextDocument()
        self.document.setDocumentLayout(QPlainTextDocumentLayout(self.document))
        self.document_viewer = ScriptEdit()
        self.document_viewer.setReadOnly(True)
        self.document_viewer.setDocument(self.document)
        self.filelink = DocumentFileLink(self.document)
        self.filelink.setFileFilter(".yaml")
        self.filelink.setFileSelectFilter("YAML (*.yaml);;Any File (*)")
        self.filelink.filepathChanged.connect(self.onFilepathChanged)

        self.definitions_model = QStandardItemModel()

        ### update document on graph change
        self.nodes.rowsInserted.connect(self._update_document)
        self.nodes.rowsRemoved.connect(self._update_document)
        self.nodes.dataChanged.connect(self._update_document)
        self.nodes.modelReset.connect(self._update_document)
        self.edges.rowsInserted.connect(self._update_document)
        self.edges.rowsRemoved.connect(self._update_document)
        self.edges.dataChanged.connect(self._update_document)
        self.edges.modelReset.connect(self._update_document)
        
        ### actions, commands
        self.nodes.rowsInserted.connect(lambda: print("rows inserted"))
        ### view

        
        self.definitions_editor = ScriptEdit()
        self.definitions_editor.textChanged.connect(self.init_definitions)

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
        
        graph_scene = QGraphEditorScene()
        graph_scene.setModel(self.nodes, self.edges)
        graph_scene.setSceneRect(QRectF(-400, -400, 800, 800))
        graph_scene.setSelectionModel(self.node_selection)
        self.graph_view.setScene(graph_scene)

        # Actions
        # init_definitions_action = QAction("Init definitions", self)
        # init_definitions_action.triggered.connect(self.init_definitions)

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
        menubar.addMenu(self.filelink.createFileMenu())
        # menubar.addAction(init_definitions_action)
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
        grid_layout.addWidget(self.graph_view,         0, 1, 1, 1)
        grid_layout.addWidget(self.document_viewer,    0, 2, 1, 1)
        self.statusbar = QStatusBar(self)
        grid_layout.addWidget(self.statusbar, 1,0,1,3)
        self.setLayout(grid_layout)

        self.init_definitions()

    def loadScene(self, scene:Scene):
        ...

    def onFilepathChanged(self):
        print(f"on open {self.filelink.filepath()}")


    # def _pathlib_module_functions(self):
    #     import pathlib
    #     import string
    #     for key in dir(pathlib):
    #         if key[0] in string.ascii_letters: 
    #             item = getattr(pathlib,key)
    #             if callable(item):
    #                 yield key

    @Slot()
    def init_definitions(self):
        ### add builtin functions
        import inspect
        for name in dir(__builtins__):
            if not name.startswith("_"):
                attribute = getattr(__builtins__, name)
                if callable(attribute) and not inspect.isclass(attribute):
                    item = QStandardItem()
                    item.setData(name, Qt.ItemDataRole.DisplayRole)
                    item.setData(attribute, self.DefinitionFunctionRole)
                    self.definitions_model.appendRow(item)

        ### execute definition script
        definitions_script = self.definitions_editor.toPlainText()

        try:
            capture = {'__builtins__': __builtins__}
            exec(definitions_script, capture)

            for name, attribute in capture.items():
                if name!='__builtins__':
                    if callable(attribute) and not inspect.isclass(attribute):
                        fn_item = QStandardItem()
                        fn_item.setData(name, Qt.ItemDataRole.DisplayRole)
                        fn_item.setData(name, self.DefinitionFunctionRole)
                        self.definitions_model.insertRow(self.definitions_model.rowCount(), fn_item)

            self._update_document()
            self.statusbar.showMessage(f"definitions initalized")
        except Exception as err:
            self.statusbar.showMessage(f"error: {err}")
            # QMessageBox.critical(self, "Error", f"{err}")

    def _update_document(self):
        print("update document")
        import json

        definitions = self.definitions_editor.toPlainText()

        nodes = dict()
        for row in range(self.nodes.rowCount()):
            index = self.nodes.index(row, 0)
            name = self.nodes.data(index, Qt.ItemDataRole.DisplayRole)
            definition_index = self.nodes.data(index, self.NodeDefinitionRole)
            definition_name = self.definitions_model.data(definition_index, Qt.ItemDataRole.DisplayRole)
            nodes[name] = definition_name

        edges = []
        for row in range(self.edges.rowCount()):
            index = self.edges.index(row, 0)
            source_idx = self.edges.data(index, QGraphEditorScene.SourceRole)
            target_idx = self.edges.data(index, QGraphEditorScene.TargetRole)
            source_name = self.nodes.data(source_idx, Qt.ItemDataRole.DisplayRole)
            target_name = self.nodes.data(target_idx, Qt.ItemDataRole.DisplayRole)
            edges.append( (source_name, target_name) )

        import yaml
        class LiteralString(str):
            pass

        def literal_representer(dumper, data):
            # Use `|` without `-` to keep trailing newlines intact
            value = data if data.endswith('\n') else f"{data}\n"
            return dumper.represent_scalar('tag:yaml.org,2002:str', value, style='|')

        yaml.add_representer(LiteralString, literal_representer)

        document_text = yaml.dump({
            'definitions': LiteralString(definitions),
            'nodes': nodes,
            'edges': edges
        }, indent=4)

        self.document.setPlainText(document_text)


    @Slot()
    def create_new_node(self):
        ###
        if self.definitions_model.rowCount()==0:
            QMessageBox.warning(self, "No definiions!", "Please create function definitions!")
            return

        from itertools import chain
        # node_name, accepted =  QOptionDialog.getItem(self , "Title", "label", ['print', "write"], 0, editable=True)
        definitions = dict()
        for row in range(self.definitions_model.rowCount()):
            definition_index = self.definitions_model.index(row, 0)
            name = definition_index.data(Qt.ItemDataRole.DisplayRole)
            func = definition_index.data(self.DefinitionFunctionRole)
            definitions[name]  = definition_index
       
        definition_key, accepted =  QOptionDialog.getItem(self , "Title", "label", [_ for _ in definitions.keys()] , 0)
        if definition_key and accepted:
            from pylive.utils.unique import make_unique_name
            node_names = [self.nodes.data(self.nodes.index(row, 0), Qt.ItemDataRole.DisplayRole) for row in  range(self.nodes.rowCount())]
            node_key = make_unique_name(f"{definition_key}1", node_names)
            item = QStandardItem()
            item.setData(f"{node_key}", Qt.ItemDataRole.DisplayRole)
            item.setData(definitions[definition_key], self.NodeDefinitionRole)
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

