from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from networkx.classes import graphviews

from pylive.qt_options_dialog import QOptionDialog
from pylive.utils.qt import modelReset, signalsBlocked

# from dataclasses import dataclass
# @dataclass
# class Node:
#     name: str
#     #content
#     func: str
#     args:dict[str,str]
    
#     def __call__(self):
#         ...

#     def serialize(self)->dict:
#         ...

#     def deserialize(self, data):
#         self.name = data['name']
#         self.func = data['func']
#         for name, expression in data['args'].items():
#             self.args[name] =  expression


# @dataclass
# class Edge:
#     source: Node
#     target: Node
#     inlet: str

# @dataclass
# class Graph:
#     name:str
#     # content
#     nodes:list[Node]
#     edges:list[Edge]
#     args:dict[str, str]

#     def serialize(self)->dict:
#         ...

#         return {
#             'name': self.name
#         }

#     def deserialize(self, data:dict):
#         ...


# @dataclass
# class Scene:
#     definitions:str
#     graph: Graph

#     def serialize(self)->str:
#         import yaml
#         return yaml.dump({
#             'definitions': self.definitions,
#         })

#     def deserialize(self, text:str):
#         import yaml
#         # parse yaml
#         data = yaml.load(text, Loader=yaml.SafeLoader)

#         # set definitions
#         self.definitions = data['definitions']

#         #parse graph
#         nodes = [Node(_['name'], _['func']) for _ in data['graph']['nodes']]
#         edges = [Edge(_[0], _[1], _[2]) for _ in data['graph']['edges']]
#         self.graph = Graph(nodes, edges)


from qt_graph_editor_scene import QGraphEditorScene
from pylive.QtScriptEditor.script_edit import ScriptEdit

# class SceneModel(QObject):
#     DefinitionFunctionRole = Qt.ItemDataRole.UserRole
#     NodeDefinitionRole = Qt.ItemDataRole.UserRole
#     def __init__(self, parent:QObject|None=None):
#         super().__init__(parent=parent)
#         self.definitions_source:str=""

#         self.nodes = QStandardItemModel()
#         self.nodes.setHeaderData(0, Qt.Orientation.Horizontal, "name")

#         self.edges = QStandardItemModel()
#         self.edges.setHeaderData(0, Qt.Orientation.Horizontal, "key")

#         self.node_selection = QItemSelectionModel(self.nodes)
#         self.edge_selection = QItemSelectionModel(self.edges)

#         self._cache_definitions:dict[str, Callable]=None

#     def setDefinitionsSource(self, source:str):
#         self.definitions_source = source

#     def definitions(self):
#         ...


# class AbstractLinkModel(QAbstractItemModel):
#     def __init__(self, sourceModel, parent=None):
#         super().__init__(parent=parent)

#     def link(self, sourceIndex, targetIndex):
#         self.insertRow
#         ...

#     def unlink(self, sourceIndex, targetIndex):
#         ...

#     def source(self, index):
#         ...

#     def target(self, index):
#         ...

#     def links(self, sourceIndex, targetIndes)->Iterable[QModelIndex]:
#         ...


# class StandardLinkModel(QStandardItemModel):
#     ...

class DefinitionsEditorDelegate(QStyledItemDelegate):
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex) -> QWidget:
        editor = super().createEditor(parent, option, index)
        print("editor created", editor)
        text_edit = QTextEdit(parent)
        text_edit.setPlainText(index.data(Qt.ItemDataRole.EditRole))
        return text_edit

    def setEditorData(self, editor: QWidget, index: QModelIndex | QPersistentModelIndex) -> None:
        editor = cast(QTextEdit, editor)
        model = cast(QStandardItemModel, index.model())
        editor.setPlainText(index.data(Qt.ItemDataRole.EditRole))

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex | QPersistentModelIndex) -> None:
        editor = cast(QTextEdit, editor)
        model = cast(QStandardItemModel, index.model())
        model.setData(index, editor.toPlainText(), Qt.ItemDataRole.EditRole)


class Window(QWidget):
    DefinitionFunctionRole = Qt.ItemDataRole.UserRole
    DefinitionErrorRole = Qt.ItemDataRole.UserRole+1
    NodeFunctionRole = Qt.ItemDataRole.UserRole+2
    NodeErrorRole = Qt.ItemDataRole.UserRole+3
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        ### document state
        self._is_modified = False
        self._filepath = "None"

        ### MODEL
        self.definitions = QStandardItemModel()
        self.nodes = QStandardItemModel()
        self.edges = QStandardItemModel()
        
        # configure model
        self.nodes.setHeaderData(0, Qt.Orientation.Horizontal, "name")
        self.edges.setHeaderData(0, Qt.Orientation.Horizontal, "key")
        self.node_selection = QItemSelectionModel(self.nodes)
        self.edge_selection = QItemSelectionModel(self.edges)

        ### Widgets
        self.definitions_list_view = QListView(self)
        self.definitions_list_view.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.definitions_list_view.setItemDelegate(DefinitionsEditorDelegate())
        self.definitions_list_view.setModel(self.definitions)

        self.nodes_list_view = QListView(self)
        self.nodes_list_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.nodes_list_view.setModel(self.nodes)

        self.edges_list_view = QListView(self)
        self.edges_list_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.edges_list_view.setModel(self.edges)

        self.graph_view = QGraphicsView()
        self.graph_view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.graph_view.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
        self.graph_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.graph_view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.graph_view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        # self.graph_view.installEventFilter(self)
        graph_scene = QGraphEditorScene()
        graph_scene.setModel(self.nodes, self.edges)
        graph_scene.setSceneRect(QRectF(-400, -400, 800, 800))
        graph_scene.setSelectionModel(self.node_selection)
        self.graph_view.setScene(graph_scene)

        # nodelist = QListView()
        # nodelist.setModel(self.nodes)
        # nodelist.setSelectionModel(self.node_selection)
        # nodelist.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        # edgelist = QListView()
        # edgelist.setModel(self.edges)

        # Actions
        # init_definitions_action = QAction("Init definitions", self)
        # init_definitions_action.triggered.connect(self.init_definitions)
        open_action = QAction("open", self)
        open_action.triggered.connect(lambda: self.openFile())
        save_action = QAction("save", self)
        save_action.triggered.connect(lambda: self.saveFile())
        add_node_action = QAction("add new node", self)
        add_node_action.triggered.connect(self.create_new_node)
        delete_node_action = QAction("delete node", self)
        delete_node_action.triggered.connect(self.delete_selected_nodes)
        connect_selected_nodes_action = QAction("connect selected nodes", self)
        connect_selected_nodes_action.triggered.connect(self.connect_selected_nodes)
        remove_edge_action = QAction("remove edge", self)
        remove_edge_action.triggered.connect(self.delete_selected_edges)
        # layout_action = QAction("layout", self)
        # layout_action.triggered.connect(graph_scene.layout)

        menubar = QMenuBar(parent=self)
        menubar.addAction(save_action)
        menubar.addAction(open_action)
        menubar.addAction(add_node_action)
        menubar.addAction(delete_node_action)
        menubar.addAction(connect_selected_nodes_action)
        menubar.addAction(remove_edge_action)
        # menubar.addAction(layout_action)

        ### Layout
        grid_layout = QGridLayout()
        grid_layout.setMenuBar(menubar)
        # grid_layout.addWidget(nodelist, 1, 0)
        # grid_layout.addWidget(edgelist, 1, 1)
        grid_layout.addWidget(self.definitions_list_view, 0, 0, 1, 1)
        grid_layout.addWidget(self.nodes_list_view, 0, 1, 1, 1)
        grid_layout.addWidget(self.edges_list_view, 0, 2, 1, 1)
        grid_layout.addWidget(self.graph_view, 0,3,1,1)
        # grid_layout.addWidget(self.graph_view,         0, 1, 1, 1)
        # grid_layout.addWidget(self.document_viewer,    0, 2, 1, 1)
        self.statusbar = QStatusBar(self)
        grid_layout.addWidget(self.statusbar, 1,0,1,3)
        self.setLayout(grid_layout)

        # self.init_definitions()

    ### The python script flow documents
    def fileFilter(self):
        return ".yaml"

    def fileSelectFilter(self):
        return "YAML (*.yaml);;Any File (*)"

    def setIsModified(self, m:bool):
        self._is_modified = m

    @Slot()
    def openFile(self, filepath:str|None=None)->bool:
        ### close current file
        if not self.closeFile():
            return False

        ### prompt file name
        if not filepath:
            filepath, _ = QFileDialog.getOpenFileName(self, 
                "Open", self.fileFilter(), self.fileSelectFilter())
            if filepath is None: # cancelled
                return False

        ### try to load
        try:
            from pathlib import Path
            import yaml
            # parse yaml
            text = Path(filepath).read_text()
            data = yaml.load(text, Loader=yaml.SafeLoader)

            def get_python_function_from_string(code:str)->tuple[str, Callable]:
                capture = {'__builtins__':__builtins__}
                try:
                    exec(code, capture)
                except SyntaxError as err:
                    raise err
                except Exception as err:
                    raise err
                functions:list[tuple[str, Callable]] = []
                for name, attribute in capture.items():
                    if name!='__builtins__':
                        if callable(attribute) and not inspect.isclass(attribute):
                            functions.append( (name, attribute) )

                if len(functions)!=1:
                    raise ValueError("")
                return functions[0]

            # Delete the current model and load data into the new model!
            with modelReset(self.definitions):

                # self.definitions.clear()
                import inspect
                for code in data['definitions']:
                    ### get python function from string
                    # the string should contain a single function definition
                    try:
                        name, func = get_python_function_from_string(code)
                        item = QStandardItem()
                        item.setData(name, Qt.ItemDataRole.DisplayRole)
                        item.setData(code, Qt.ItemDataRole.EditRole)
                        self.definitions.insertRow(self.definitions.rowCount(), item)
                    except Exception as err:
                        print("ERROR", err)
                        self.statusbar.showMessage(f"error: {err}")

            _node_items_by_name = dict()
            with modelReset(self.nodes):
                with signalsBlocked(self.nodes):
                    for node_data in data['nodes']:
                        node_item = QStandardItem()
                        node_item.setData(node_data['name'], Qt.ItemDataRole.DisplayRole)
                        node_item.setData(node_data['func'], self.NodeFunctionRole)
                        _node_items_by_name[node_data['name']] = node_item
                        self.nodes.insertRow(self.nodes.rowCount(), node_item)
            
            # with modelReset(self.edges):
            #     # self.edges.clear()
            #     for edge_data in data['edges']:
            #         edge_item = QStandardItem()
            #         source_node_item = _node_items_by_name[edge_data['source']]
            #         edge_item.setData(source_node_item, QGraphEditorScene.SourceRole)
            #         target_node_item = _node_items_by_name[edge_data['target']]
            #         edge_item.setData(target_node_item, QGraphEditorScene.TargetRole)
            #         edge_item.setData(edge_data['inlet'], Qt.ItemDataRole.DisplayRole)

            #         self.edges.insertRow(self.edges.rowCount(), edge_item)


            return True
        except Exception:
            return False
        

        # self.filelink = DocumentFileLink(self.document)
        # self.filelink.setFileFilter(".yaml")
        # self.filelink.setFileSelectFilter("YAML (*.yaml);;Any File (*)")
        ...

    def deserialize(self, text:str):
        ...

        # # set definitions
        # self.definitions = data['definitions']

        # #parse graph
        # nodes = [Node(_['name'], _['func']) for _ in data['graph']['nodes']]
        # edges = [Edge(_[0], _[1], _[2]) for _ in data['graph']['edges']]
        # self.graph = Graph(nodes, edges)

    @Slot()
    def closeFile(self)->bool:
        """return False, if the user cancelled, otherwise true"""
        if self._is_modified:
            match QMessageBox.question(self, "Save changes before closing?", f"{self._filepath or "unititled"}", QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel):
                case QMessageBox.StandardButton.Yes:
                    self.saveFile()
                    return True
                case QMessageBox.StandardButton.No:
                    return True
                case QMessageBox.StandardButton.Cancel:
                    return False
        return True

    def serialize(self)->str:
        import yaml
        return yaml.dump({
            'definitions': self.definitions,
        })



    @Slot()
    def saveFile(self):
        ...


    # def _pathlib_module_functions(self):
    #     import pathlib
    #     import string
    #     for key in dir(pathlib):
    #         if key[0] in string.ascii_letters: 
    #             item = getattr(pathlib,key)
    #             if callable(item):
    #                 yield key

    # @Slot()
    # def init_definitions(self):
    #     ### add builtin functions
    #     import inspect
    #     for name in dir(__builtins__):
    #         if not name.startswith("_"):
    #             attribute = getattr(__builtins__, name)
    #             if callable(attribute) and not inspect.isclass(attribute):
    #                 item = QStandardItem()
    #                 item.setData(name, Qt.ItemDataRole.DisplayRole)
    #                 item.setData(attribute, self.DefinitionFunctionRole)
    #                 self.definitions_model.appendRow(item)

    #     ### execute definition script
    #     definitions_script = self.definitions_editor.toPlainText()

    #     try:
    #         capture = {'__builtins__': __builtins__}
    #         exec(definitions_script, capture)

    #         for name, attribute in capture.items():
    #             if name!='__builtins__':
    #                 if callable(attribute) and not inspect.isclass(attribute):
    #                     fn_item = QStandardItem()
    #                     fn_item.setData(name, Qt.ItemDataRole.DisplayRole)
    #                     fn_item.setData(name, self.DefinitionFunctionRole)
    #                     self.definitions_model.insertRow(self.definitions_model.rowCount(), fn_item)

    #         self._update_document()
    #         self.statusbar.showMessage(f"definitions initalized")
    #     except Exception as err:
    #         self.statusbar.showMessage(f"error: {err}")
    #         # QMessageBox.critical(self, "Error", f"{err}")

    # def _update_document(self):
    #     print("update document")
    #     import json

    #     definitions = self.definitions_editor.toPlainText()

    #     nodes = dict()
    #     for row in range(self.nodes.rowCount()):
    #         index = self.nodes.index(row, 0)
    #         name = self.nodes.data(index, Qt.ItemDataRole.DisplayRole)
    #         definition_index = self.nodes.data(index, self.NodeDefinitionRole)
    #         definition_name = self.definitions_model.data(definition_index, Qt.ItemDataRole.DisplayRole)
    #         nodes[name] = definition_name

    #     edges = []
    #     for row in range(self.edges.rowCount()):
    #         index = self.edges.index(row, 0)
    #         source_idx = self.edges.data(index, QGraphEditorScene.SourceRole)
    #         target_idx = self.edges.data(index, QGraphEditorScene.TargetRole)
    #         source_name = self.nodes.data(source_idx, Qt.ItemDataRole.DisplayRole)
    #         target_name = self.nodes.data(target_idx, Qt.ItemDataRole.DisplayRole)
    #         edges.append( (source_name, target_name) )

    #     import yaml
    #     class LiteralString(str):
    #         pass

    #     def literal_representer(dumper, data):
    #         # Use `|` without `-` to keep trailing newlines intact
    #         value = data if data.endswith('\n') else f"{data}\n"
    #         return dumper.represent_scalar('tag:yaml.org,2002:str', value, style='|')

    #     yaml.add_representer(LiteralString, literal_representer)

    #     document_text = yaml.dump({
    #         'definitions': LiteralString(definitions),
    #         'nodes': nodes,
    #         'edges': edges
    #     }, indent=4)

    #     self.document.setPlainText(document_text)


    @Slot()
    def create_new_node(self):
        ###
        if self.definitions_model.rowCount()==0:
            QMessageBox.warning(self, "No definions!", "Please create function definitions!")
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

