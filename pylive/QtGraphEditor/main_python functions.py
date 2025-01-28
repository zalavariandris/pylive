from collections import defaultdict
from typing import *
from typing_extensions import deprecated
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from networkx.classes import graphviews

from pylive.qt_options_dialog import QOptionDialog
from pylive.utils import group_consecutive_numbers
from pylive.utils.qt import modelReset, signalsBlocked

class NodeModel(QAbstractItemModel):
    DefinitionRole = Qt.ItemDataRole.UserRole+1
    NameRole = Qt.ItemDataRole.UserRole+2

    def __init__(self, definitions:QAbstractItemModel, parent: QObject|None=None) -> None:
        super().__init__(parent)
        self._nodes:list[dict] = []
        self._related_definitions = definitions

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows in the model."""
        return len(self._nodes)

    def columnCount(self, parent: QModelIndex|QPersistentModelIndex=QModelIndex()) -> int:
        return 1

    def data(self, index:QModelIndex|QPersistentModelIndex, role:Qt.ItemDataRole):
        """Returns the data for the given index and role."""
        if not index.isValid() or not 0 <= index.row() < len(self._nodes):
            return None

        node = self._nodes[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            return self._nodes[index.row()]['name']
        elif role == Qt.ItemDataRole.UserRole:
            return node  # Return the entire person dictionary for custom use
        elif role == self.NameRole:
            return self._nodes[index.row()]['name']
        elif role == self.DefinitionRole:
            return self._nodes[index.row()]['definition']

        return None

    def roleNames(self)->dict[int, bytes]:
        """Returns a dictionary mapping custom role numbers to role names."""
        return {
            Qt.ItemDataRole.DisplayRole: b'name',
            self.DefinitionRole:         b'definition'
        }

    def insertRows(self, row:int, count:int, parent=QModelIndex()):
        if len(self._nodes) <= row or row < 0:
            return False

        parent = QModelIndex()
        row = self.rowCount()
        count=1
        self.beginInsertRows(parent, row, row + count - 1)
        for _ in range(count):
            node = {}
            self._nodes.append(node)
        self.endInsertRows()
        return True

    def addNewNode(self, name:str, definition:QModelIndex):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())

        self._nodes.append({
            'name': name, 
            'definition': QPersistentModelIndex(definition)
        })
        self.endInsertRows()

    def removeRows(self, row:int, count:int, parent=QModelIndex()):
        """Removes rows from the model."""
        if row < 0 or row + count > len(self.nodes):
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        for row in range(row+count-1, row, -1):
            del self._nodes[row]
        self.endRemoveRows()
        return True

    def clear(self):
        self.blockSignals(True)
        self.removeRows(0, self.rowCount(), QModelIndex())
        self.blockSignals(False)
        self.modelReset.emit()

    def flags(self, index):
        """Returns the item flags for the given index."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled ### | Qt.ItemFlag.ItemIsEditable

    def index(self, row:int, column:int, parent=QModelIndex()):
        if parent.isValid():
            return QModelIndex()

        return self.createIndex(row, column)

    def parent(self, index:QModelIndex):
        return QModelIndex()  # No parent for this flat model


class GraphModel(QAbstractListModel):
    SourceRole = Qt.ItemDataRole.UserRole+1
    TargetRole = Qt.ItemDataRole.UserRole+2
    KeyRole = Qt.ItemDataRole.EditRole

    def __init__(self, nodes:QAbstractItemModel, parent: QObject|None=None) -> None:
        super().__init__(parent)

        self._related_nodes = nodes
        nodes.rowsRemoved.connect(self._onRelatedModelRowsRemoved)

        self._edges:list[tuple[QPersistentModelIndex, QPersistentModelIndex, str]] = []

    def _onRelatedModelRowsRemoved(self, parent:QModelIndex, first:int, last:int):
        edge_rows_to_remove = []
        for row, edge in enumerate(self._edges):
            source, target, key = edge
            WasEdgeSourceRemoed = first <= source.row() and source.row() <=last
            WasEdgeTargetRemoed = first <= target.row() and target.row() <=last
            if WasEdgeSourceRemoed or WasEdgeTargetRemoed:
                edge_rows_to_remove.append(row)

        edge_row_groups = group_consecutive_numbers(edge_rows_to_remove)

        for first, last in edge_row_groups:
            self.removeRows(first, count=last-first+1)

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows in the model."""
        return len(self._edges)

    def data(self, index:QModelIndex|QPersistentModelIndex, role:Qt.ItemDataRole):
        """Returns the data for the given index and role."""
        if not index.isValid() or not 0 <= index.row() < len(self._edges):
            return None

        edge = self._edges[index.row()]
        source, target, key = edge

        if role == Qt.ItemDataRole.DisplayRole:
            return f"{source.data(Qt.ItemDataRole.DisplayRole)}\n|--{key}->\n{target.data(Qt.ItemDataRole.DisplayRole)}"
        elif role == Qt.ItemDataRole.UserRole:
            return edge  # Return the entire person dictionary for custom use
        elif role == self.SourceRole:
            return source
        elif role == self.TargetRole:
            return target
        elif role == self.KeyRole:
            return key

        return None

    def roleNames(self):
        """Returns a dictionary mapping custom role numbers to role names."""
        return {
            Qt.ItemDataRole.DisplayRole: b'display',
            self.SourceRole:             b'source',
            self.TargetRole:             b'target',
            self.KeyRole:                b'key'
        }

    def insertRows(self, row, count, parent=QModelIndex()):
        raise NotImplementedError()

    def addEdge(self, source: QModelIndex|QPersistentModelIndex, target:QModelIndex|QPersistentModelIndex, key:str):
        assert isinstance(source, (QModelIndex, QPersistentModelIndex)) 
        assert isinstance(target, (QModelIndex, QPersistentModelIndex))
        assert isinstance(key, str)
        assert source.model() == self._related_nodes
        assert target.model() == self._related_nodes

        """Inserts rows into the model."""
        if not isinstance(source, (QModelIndex, QPersistentModelIndex)):
            return False
        if source.model() != self._related_nodes:
            return False

        if not isinstance(source, (QModelIndex, QPersistentModelIndex)):
            return False
        if target.model() != self._related_nodes:
            return False

        print("add edge")

        parent = QModelIndex()
        row = self.rowCount()
        count=1
        print("beginInsertRows", row, row + count - 1)
        self.beginInsertRows(parent, row, row + count - 1)
        for _ in range(count):
            source = QPersistentModelIndex(source)
            target = QPersistentModelIndex(target)
            edge = source, target, key
            self._edges.insert(row, edge)
        self.endInsertRows()
        return True

    def removeRows(self, row:int, count:int, parent=QModelIndex()):
        """Removes rows from the model."""
        if row < 0 or row + count > len(self._edges):
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        for row in range(row+count-1, row, -1):
            edge = self._edges[row]
            source, target, key = edge
            del self._edges[row]
        self.endRemoveRows()
        return True

    def flags(self, index):
        """Returns the item flags for the given index."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled ### | Qt.ItemFlag.ItemIsEditable



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


class ListTileDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter: QPainter, option:QStyleOption, index: QModelIndex):
        painter.save()

        # Get data from the model
        heading = index.data(Qt.ItemDataRole.DisplayRole)  # DisplayRole for the heading
        subheading = index.data(Qt.ItemDataRole.ToolTipRole)  # ToolTipRole for the subheading

        # Define the rectangle areas
        rect:QRect = option.rect
        heading_rect = rect.adjusted(10, 5, -10, -rect.height() // 2)
        subheading_rect = rect.adjusted(10, rect.height() // 2, -10, -5)

        # Access the palette for standard colors
        palette:QPalette = option.palette

        # Background color for selected items
        if option.state & QStyle.State_Selected:
            painter.fillRect(rect, palette.button())
            painter.fillRect(QRect(rect.left(), rect.top(), 1, rect.height()), palette.highlight())

        # Heading text color
        heading_color = palette.highlightedText() if option.state & QStyle.State_Selected else palette.text()

        # Subheading text color
        subheading_color = palette.highlightedText() if option.state & QStyle.State_Selected else palette.mid()

        # Draw the heading (uses default font)
        painter.setPen(heading_color.color())
        painter.drawText(heading_rect, Qt.AlignLeft | Qt.AlignVCenter, heading or "")

        # Draw the subheading (uses default font)
        painter.setPen(subheading_color.color())
        painter.drawText(subheading_rect, Qt.AlignLeft | Qt.AlignVCenter, subheading or "")

        painter.restore()

    def sizeHint(self, option, index):
        # Set the height of the item to accommodate both heading and subheading
        return QSize(option.rect.width(), 50)


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
        self.nodes = NodeModel(definitions=self.definitions)
        self.edges = GraphModel(nodes=self.nodes)
        
        # configure model
        self.nodes.setHeaderData(0, Qt.Orientation.Horizontal, "name")
        self.edges.setHeaderData(0, Qt.Orientation.Horizontal, "edge")
        self.edges.rowsInserted.connect(lambda parent, first, last:  print(parent, first, last))
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
        self.edges_list_view.setItemDelegate(ListTileDelegate())
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

        # Clear and load data into the new model!
        _definition_index_by_name = dict()
        self.definitions.blockSignals(True)
        self.definitions.clear()
        import inspect
        for row, code in enumerate(data['definitions']):
            ### get python function from string
            # the string should contain a single function definition
            try:
                name, func = get_python_function_from_string(code)
                item = QStandardItem()
                item.setData(name, Qt.ItemDataRole.DisplayRole)
                item.setData(code, Qt.ItemDataRole.EditRole)
                self.definitions.insertRow(row, item)
                _definition_index_by_name[name] = row
            except Exception as err:
                print("ERROR", err)
                self.statusbar.showMessage(f"error: {err}")
        self.definitions.blockSignals(False)
        self.definitions.modelReset.emit()

        _node_row_by_name = dict()
        self.nodes.blockSignals(True)
        for row, node in enumerate(data['nodes']):
            print(node)
            func_name = node['func']
            def_row = _definition_index_by_name[func_name]

            self.nodes.addNewNode(node['name'], definition=self.definitions.index(def_row, 0))
            _node_row_by_name[node['name']] = row
        self.nodes.blockSignals(False)
        self.nodes.modelReset.emit()

        self.edges.blockSignals(True)
        for row, edge in enumerate(data['edges']):
            source_name = edge['source']
            target_name = edge['target']
            source_row = _node_row_by_name[source_name]
            target_row = _node_row_by_name[target_name]
            source_index = self.nodes.index(source_row, 0)
            target_index = self.nodes.index(target_row, 0)
            self.edges.addEdge(source_index, target_index, edge['inlet'])

        self.edges.blockSignals(False)
        self.edges.modelReset.emit()


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
    window.openFile("./website_builder.yaml")
    app.exec()

