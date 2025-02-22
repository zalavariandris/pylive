
from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# from pylive.QtGraphEditor.definitions_model import DefinitionsModel

import pdb

### DATA ###

# from pylive.QtGraphEditor.py_functions_model import PyFunctionsModel
from pylive.VisualCode_v4.py_data_model import PyDataModel, PyNodeItem
from pylive.VisualCode_v4.py_proxy_model import PyProxyNodeModel, PyProxyLinkModel, PyProxyParameterModel


from pylive.VisualCode_v4.graph_editor.graph_editor_view import GraphEditorView
from pylive.QtScriptEditor.script_edit import ScriptEdit
import pylive.utils.qtfactory as qf


from pylive.utils.debug import log_function_call

def log_call(fn, *args, **kwargs):
    print(f"{fn.__name__} was called")
    return fn(*args, **kwargs)

import pylive.utils.qtfactory as qf


class PyInspectorView(QFrame):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._model:PyDataModel|None=None
        self._current_node:str|None=None
        self._parameter_model: PyProxyParameterModel|None=None
        self._model_connections = []
        self._view_connections = []
        self.setupUI()

    def showEvent(self, event: QShowEvent, /) -> None:
        for signal, slot in self._model_connections:
            signal.connect(slot)
        for signal, slot in self._view_connections:
            signal.connect(slot)

        return super().showEvent(event)

    def hideEvent(self, event: QHideEvent, /) -> None:
        print("hideEvent")
        for signal, slot in self._model_connections:
            signal.disconnect(slot)
        for signal, slot in self._view_connections:
            signal.disconnect(slot)


    def setupUI(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)  # Styled panel for the frame
        self.setFrameShadow(QFrame.Shadow.Raised)

        self.name_label = QLabel()

        self.parameter_editor = QTableView()
        self.parameter_editor.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.parameter_editor.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.parameter_editor.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.parameter_editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.parameter_editor.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)

        self.source_editor = QTextEdit()
        self.source_editor.setPlaceholderText("source...")

        main_layout = qf.vboxlayout([
            self.name_label,
            QLabel("<h2>Parameters</h2>"),
            self.parameter_editor,
            QLabel("<h2>Source</h2>"),
            self.source_editor
        ])

        self.setLayout(main_layout)

        # bind view to model
        self._view_connections = [
            (self.source_editor.textChanged, lambda: self._syncModelData('source'))
        ]
        for signal, slot in self._view_connections:
            signal.connect(slot)
        
    def setModel(self, model: PyDataModel|None):
        if self._model:
            for signal, slot in self._model_connections:
                signal.disconnect(slot)

            self._parameter_model = None

        if model:
            self._model_connections = [
                (model.sourceChanged, lambda: self._syncEditorData(attr='source'))
            ]
            for signal, slot in self._model_connections:
                signal.connect(slot)

            self._parameter_model = PyProxyParameterModel(model)


        self._model = model
        self.parameter_editor.setModel(self._parameter_model)
        if self._parameter_model:
            self._parameter_model.setNode(self._current_node)

    def _syncEditorData(self, attr:Literal['name', 'source']):
        if not self._model or not self._current_node:
            self.name_label.setText("<h1>- no selection -</h1>")
            self.source_editor.setPlainText('')
            return

        match attr:
            case 'name':
                pretty_name = self._current_node or '- no selection -'
                pretty_name = pretty_name.replace("_", " ").title()
                self.name_label.setText(f"<h1>{pretty_name}<h1>")
            case 'source':
                value = self._model.nodeSource(self._current_node)
                if value != self.source_editor.toPlainText():
                    self.source_editor.setPlainText(value)

    def _syncModelData(self, attr='source'):
        if not self._model or not self._current_node:
            return

        match attr:
            case 'source':
                self._model.setNodeSource(self._current_node, self.source_editor.toPlainText())

    def setCurrent(self, node:str|None):
        self._current_node = node

        self._syncEditorData('name')
        self._syncEditorData('source')
        # if self._parameter_model:
        #     self._parameter_model.setNode(node)


class Window(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        ### document state

        self._is_modified = False
        self._filepath = "None"

        self._autocompile_connections = []
        self._autoevaluate_connections = []
        self.graph_view_connections = []
        self.graph_model = PyDataModel()
        self.link_proxy_model = PyProxyLinkModel(self.graph_model)
        self.node_proxy_model:PyProxyNodeModel = self.link_proxy_model.itemsModel()
        assert self.node_proxy_model
        self.node_selection_model = QItemSelectionModel(self.node_proxy_model)

        self.setupUI()
        self.setAutoCompile(True)
        self.setAutoEvaluate(False)

    def setupUI(self):        
        ### SheetsView
        self.nodes_table_view = QTableView()
        # self.nodes_table_view.horizontalHeader().setVisible(True)
        # self.nodes_table_view.verticalHeader().setVisible(False)
        self.nodes_table_view.setModel(self.node_proxy_model)
        self.nodes_table_view.setSelectionModel(self.node_selection_model)
        
        
        self.links_table_view = QTableView()
        # self.links_table_view.horizontalHeader().setVisible(True)
        # self.links_table_view.verticalHeader().setVisible(False)s
        self.links_table_view.setModel(self.link_proxy_model)
        

        ### GRAPH View
        self.graph_view = GraphEditorView()
        self.graph_view.installEventFilter(self)
        self.graph_view.setModel(self.node_proxy_model, self.link_proxy_model)
        self.graph_view.setSelectionModel(self.node_selection_model)

        self.graph_view_connections = [
            (
                self.graph_view.nodesLinked, lambda source, target, outlet, inlet: 
                self.connect_nodes(self.node_proxy_model.mapToSource(source), self.node_proxy_model.mapToSource(target), inlet)
            )
        ]
        for signal, slot in self.graph_view_connections:
            signal.connect(slot)


        # self.graph_view.setSelectionModel(self.node_selection_model)
        # self.graph_view.setSelectionModel(self.selection_model)

        # ### NODEINSPECTOR
        self.inspector_view = PyInspectorView()
        self.inspector_view.setModel(self.graph_model)
        def set_inspector_node(current:QModelIndex, previous:QModelIndex):
            if current.isValid():
                node = self.node_proxy_model.mapToSource(current)
                self.inspector_view.setCurrent(node)
            else:
                self.inspector_view.setCurrent(None)


        self.node_selection_model.currentChanged.connect(set_inspector_node)


        # ### PREVIEW WIDGET
        # self.preview = PyPreviewView()
        # self.preview.setModel(self.graph_model)
        # self.preview.setSelectionModel(self.node_selection_model)


        # self.preview.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)

        ### STATUS BAR WIDGET
        self.statusbar = QStatusBar()
        self.statusbar.showMessage("status bar")

        ## MENUBAR

        # Actions
        open_action = QAction("open", self)
        save_action = QAction("save", self)
        add_node_action = QAction("add new node", self)
        delete_node_action = QAction("delete node", self)
        create_edge_action = QAction("connect selected nodes", self)
        remove_edge_action = QAction("remove edge", self)
        compile_node_action = QAction("compile selected node", self)
        evaluate_node_action = QAction("evaluate selected node", self)

        self.addActions([
            save_action,
            open_action,
            add_node_action,
            create_edge_action,
            delete_node_action,
            remove_edge_action,
            compile_node_action,
            evaluate_node_action
        ])

        menubar = QMenuBar(parent=self)
        menubar.addActions(self.actions())

        menubar_connections = [
            (open_action.triggered, lambda: self.openFile()),
            (save_action.triggered, lambda: self.saveFile()),
            (add_node_action.triggered, lambda: self.create_new_node()),
            (delete_node_action.triggered, lambda: self.delete_selected_nodes()),
            (create_edge_action.triggered, lambda: self.connect_selected_nodes()),
            (remove_edge_action.triggered, lambda: self.delete_selected_edges()),
            (compile_node_action.triggered, lambda: self.compile_selected_node()),
            (evaluate_node_action.triggered, lambda: self.graph_model.evaluateNode(self.node_selection_model.currentIndex().row()))
        ]
        for signal, slot in menubar_connections:
            signal.connect(slot)

        ### Layout
        main_layout = qf.vboxlayout([
            qf.splitter(Qt.Orientation.Horizontal, [
                qf.widget(qf.vboxlayout([
                    self.nodes_table_view,
                    self.links_table_view,
                ])),
                self.graph_view,
                self.inspector_view
                # self.preview
            ]),
            self.statusbar
        ])
        self.statusbar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        main_layout.setMenuBar(menubar)
        self.setLayout(main_layout)


    def setAutoCompile(self, auto: bool):
        if auto:
            # compile all nodes
            self.graph_model.compileNodes(self.graph_model.nodes())

            # compile nodes on changes
            self._autocompile_connections = [
                (self.graph_model.modelReset, lambda:         self.graph_model.compileNodes(self.graph_model.nodes())),
                (self.graph_model.nodesAdded, lambda nodes:   self.graph_model.compileNodes(nodes)),
                (self.graph_model.sourceChanged, lambda node: self.graph_model.compileNodes([node]))
            ]
            for signal, slot in self._autocompile_connections:
                signal.connect(slot)

        else:
            for signal, slot in self._autocompile_connections:
                signal.disconnect(slot)
            self._autocompile_connections = []

    def setAutoEvaluate(self, auto:bool):
        if auto:
            self._autoevaluate_connections = [
                (
                    self.node_selection_model.currentChanged, 
                    lambda current, previous: self.graph_model.evaluateNode(
                        self.node_proxy_model.mapToSource(current))
                )
            ]
            for signal, slot in self._autoevaluate_connections:
                signal.connect(slot)
        else:
            for signal, slot in self._autoevaluate_connections:
                signal.disconnect(slot)
            self._autoevaluate_connections = []

    def sizeHint(self):
        return QSize(2048, 900) 

    def fileFilter(self):
        return ".yaml"

    def fileSelectFilter(self):
        return "YAML (*.yaml);;Any File (*)"

    def setIsModified(self, m:bool):
        self._is_modified = m

    def openFile(self, filepath:str|None=None)->bool:
        ### close current file
        if not self.closeFile():
            print("Current file was not closed. Cancel opening file!")
            return False

        ### prompt file name
        if not filepath:
            filepath, _ = QFileDialog.getOpenFileName(self, 
                "Open", self.fileFilter(), self.fileSelectFilter())
            if filepath is None: # cancelled
                print("No file was selected. Cancel opening file!")
                return False

        # read and parse existing text file
        try:
            self.graph_model.load(filepath)
            print(f"Successfully opened '{filepath}'!")
            return True
        except FileExistsError:
            print("'{filepath}'' does not exist!")
            import traceback
            traceback.print_exc()
            return False
        except Exception as err:
            import traceback

            print(f"Error occured while opening {filepath}", err)
            traceback.print_exc()
            return False

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

    def saveFile(self):
        ...

    def create_new_node(self, scenepos:QPointF=QPointF()):
        from pylive.utils.unique import make_unique_name
        existing_names = list(self.graph_model.nodes())
        func_name = make_unique_name("func1", existing_names)
        self.graph_model.addNode(func_name, PyNodeItem())

        ### position node widget
        node_index = self.node_proxy_model.mapFromSource(func_name)
        node_graphics_item = self.graph_view.nodeWidget(node_index)
        if node_graphics_item := self.graph_view.nodeWidget(node_index):
            node_graphics_item.setPos(scenepos-node_graphics_item.boundingRect().center())

    def compile_selected_node(self):
        if not self.node_selection_model:
            return

        nodes = map(self.node_proxy_model.mapToSource, self.node_selection_model.selectedIndexes())
        self.graph_model.compileNodes(nodes)

    def delete_selected_nodes(self):
        indexes:list[QModelIndex] = self.node_selection_model.selectedRows(column=0)
        for index in sorted(indexes, key=lambda idx:idx.row(), reverse=True):
            node = self.node_proxy_model.mapToSource(index)
            self.graph_model.removeNode(node)

    def delete_selected_edges(self):
        indexes:list[QModelIndex] = self.links_table_view.selectedIndexes()

        rows = set(index.row() for index in indexes)
        for row in sorted(rows, reverse=True):
            source, target, inlet = self.link_proxy_model.mapToSource(self.link_proxy_model.index(row, 0))
            self.graph_model.unlinkNodes(source, target, inlet)

    def connect_selected_nodes(self):
        selected_nodes = set(map(self.node_proxy_model.mapToSource, self.node_selection_model.selectedIndexes()))
        print(selected_nodes)
        if len(selected_nodes)<2:
            return

        target_node_index = self.node_selection_model.currentIndex().siblingAtColumn(0)
        assert target_node_index.isValid(), "invalid target node"
        target_node = self.node_proxy_model.mapToSource(target_node_index)
        
        for source_node in selected_nodes:
            if source_node != target_node:
                print("connect", source_node, target_node)
                if self.graph_model.parameterCount(target_node)>0:
                    inlet = self.graph_model.parameterName(target_node, 0)
                    self.graph_model.linkNodes(source_node, target_node, inlet)

    def connect_nodes(self, source:str, target:str, inlet:str):
        self.graph_model.linkNodes(source, target, inlet)

    def eventFilter(self, watched, event):
        if watched == self.graph_view:
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

    app = QApplication()
    window = Window()
    window.openFile(parent_folder/"tests/website_builder.yaml")
    window.setGeometry(QRect(QPoint(), app.primaryScreen().size()).adjusted(40,80,-30,-100))
    window.show()
    sys.exit(app.exec())
# 