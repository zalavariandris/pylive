from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from pathlib import Path

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# from pylive.QtGraphEditor.definitions_model import DefinitionsModel

import pdb

### DATA ###
# 
# from pylive.QtGraphEditor.py_functions_model import PyFunctionsModel
from pylive.VisualCode_v4.py_data_model import PyDataModel
from pylive.VisualCode_v4.py_proxy_model import PyProxyNodeModel, PyProxyLinkModel, PyProxyParameterModel
from pylive.VisualCode_v4.py_subgraph_proxy_model import PySubgraphProxyModel

from pylive.VisualCode_v4.py_data_graph_view import PyDataGraphEditorView


import pylive.utils.qtfactory as qf

from pylive.VisualCode_v4.py_inspector_view import PyInspectorView
from pylive.VisualCode_v4.py_preview_view import PyPreviewView


class Window(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)

        ### Track file document change
        self._is_modified = False
        self._filepath = None
        self._file_watcher = QFileSystemWatcher()
        self._file_watcher.fileChanged.connect(lambda:
            self._onFileChanged(self._filepath))

        # MODEL
        self.graph_model = PyDataModel()

        # PROXY MODELS
        self.link_proxy_model = PyProxyLinkModel(self.graph_model)
        self.node_proxy_model:PyProxyNodeModel = self.link_proxy_model.itemsModel()
        assert self.node_proxy_model
        self.node_selection_model = QItemSelectionModel(self.node_proxy_model)
        self.link_selection_model = QItemSelectionModel(self.link_proxy_model)

        ### UI
        self.graph_view_connections = []
        self.setupUI()

    def showEvent(self, event: QShowEvent) -> None:
        self.graph_view.centerNodes()

    def setupUI(self):
        ### GRAPH View
        self.graph_view = PyDataGraphEditorView()
        self.graph_view.installEventFilter(self)
        self.graph_view.setModel(self.graph_model)

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
        self.links_table_view.setSelectionModel(self.link_selection_model)

        def update_model_selection():
            selected_node_keys = self.graph_view.selectedNodes()
            print("selected_node_keys", selected_node_keys)
            selection = self.node_proxy_model.mapSelectionFromSource(selected_node_keys)
            
            if selection.count()>0:
                self.node_selection_model.select(selection, QItemSelectionModel.SelectionFlag.ClearAndSelect)
                self.node_selection_model.setCurrentIndex(selection.indexes()[0], QItemSelectionModel.SelectionFlag.Current)
            else:
                self.node_selection_model.clearSelection()
                self.node_selection_model.clearCurrentIndex()

        def update_graphview_selection():
            model_selection = self.node_selection_model.selection()

            selected_node_keys = self.node_proxy_model.mapSelectionToSource(model_selection)
            self.graph_view.selectNodes(selected_node_keys)

        
        self.graph_view_connections = [
            (self.graph_view.nodesLinked, lambda source, target, outlet, inlet: 
                self.connect_nodes(self.node_proxy_model.mapToSource(source), self.node_proxy_model.mapToSource(target), inlet)
            ),
            (self.graph_view.scene().selectionChanged, update_model_selection),
            (self.node_selection_model.selectionChanged, update_graphview_selection)
        ]

        for signal, slot in self.graph_view_connections:
            signal.connect(slot)

        # ### NODEINSPECTOR
        self.inspector_view = PyInspectorView()
        self.inspector_view.setModel(self.graph_model)


        # ### PREVIEW WIDGET
        self.result_view = PyPreviewView()
        self.result_view.setModel(self.graph_model)
        self.result_view.setCurrent(None)

        # bind model to current change
        def onCurrentChanged(current:QModelIndex, previous:QModelIndex):
            node = self.node_proxy_model.mapToSource(current) if current.isValid() else None
            self.result_view.setCurrent(node)
            self.inspector_view.setCurrent(node)
    

        self.node_selection_model.currentChanged.connect(onCurrentChanged)
            

        ### STATUS BAR WIDGET
        self.statusbar = QStatusBar()
        self.statusbar.showMessage("status bar")

        ## MENUBAR

        # Actions
        open_action = QAction("open", self)
        save_action = QAction("save", self)
        add_node_action = QAction("add new node", self)
        delete_selected_action = QAction("delete selected", self)
        delete_selected_action.setShortcut("Del")
        create_edge_action = QAction("connect selected nodes", self)
        compile_node_action = QAction("compile selected node", self)
        evaluate_node_action = QAction("evaluate selected node", self)
        layout_nodes_action = QAction("layout nodes", self)
        center_nodes_action = QAction("center nodes", self)

        self.addActions([
            save_action,
            open_action,
            add_node_action,
            create_edge_action,
            delete_selected_action,
            compile_node_action,
            evaluate_node_action,
            layout_nodes_action,
            center_nodes_action
        ])

        menubar = QMenuBar(parent=self)

        filemenu = menubar.addMenu("File")
        filemenu.addActions([
            open_action, 
            save_action
        ])
        editmenu = menubar.addMenu("Edit")
        editmenu.addActions([
            add_node_action, 
            delete_selected_action, 
            create_edge_action, 
            compile_node_action, 
            evaluate_node_action
        ])
        viewmenu = menubar.addMenu("View")
        viewmenu.addActions([layout_nodes_action, center_nodes_action])

        # menubar.addActions(self.actions())

        menubar_connections = [
            (open_action.triggered, lambda: self.openFile()),
            (save_action.triggered, lambda: self.saveFile()),
            (add_node_action.triggered, lambda: self.create_new_node()),
            (delete_selected_action.triggered, lambda: self.delete_selected()),
            (create_edge_action.triggered, lambda: self.connect_selected_nodes()),
            (compile_node_action.triggered, lambda: self.compile_selected_nodes()),
            (evaluate_node_action.triggered, lambda: self.evaluate_selected_nodes()),
            (layout_nodes_action.triggered, lambda: self.graph_view.layoutNodes()),
            (center_nodes_action.triggered, lambda: self.graph_view.centerNodes())
        ]
        for signal, slot in menubar_connections:
            signal.connect(slot)

        ### Layout
        main_layout = qf.vboxlayout([
            qf.splitter(Qt.Orientation.Horizontal, [
                self.inspector_view,
                qf.widget(qf.vboxlayout([
                        self.nodes_table_view,
                        self.links_table_view,
                    ])),
                qf.tabwidget({
                    'graph':self.graph_view,
                    # 'sheets':
                }), 
                self.result_view
            ]),
            self.statusbar
        ])
        self.statusbar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        main_layout.setMenuBar(menubar)
        self.setLayout(main_layout)

    def sizeHint(self):
        return QSize(2048, 900) 

    def fileFilter(self):
        return ".yaml"

    def fileSelectFilter(self):
        return "YAML (*.yaml);;Any File (*)"

    def isModified(self):
        return self._is_modified

    def setModified(self, m:bool):
        self._is_modified = m

    def openFile(self, filepath:Path|str|None=None)->bool:
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

    def saveFile(self, filepath:str|None=None):
        assert filepath is None or isinstance(filepath, str), f"got:, {filepath}"
        DoSaveAs = self._filepath!=filepath

        if DoSaveAs:
            ...
        if not self._filepath or not filepath:
            choosen_filepath, filter_used = QFileDialog.getSaveFileName(self, 
                "Save", self.fileFilter(), self.fileSelectFilter())
            if not choosen_filepath:
                return # if no filepath was choosen cancel saving
            filepath = choosen_filepath

        elif self._filepath:
            filepath = self._filepath

        if not filepath:
            return

        """ note
        We must stop watching this file, otherwise it will silently reload the
        script. It reloads silently, because if the document is not modified,
        and the file has been changed, it will silently reload the script.
        """
        self._file_watcher.removePath(filepath) 
        try:
            with open(filepath, 'w') as file:
                file_contents = self.graph_model.serialize()
                file.write(file_contents)
                self.setModified(False)
        except FileNotFoundError:
            pass
        self._file_watcher.addPath(filepath)
        self._filepath = filepath

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

    def filepath(self):
        return self._filepath

    def _onFileChanged(self, path):
        assert path == self._filepath

        def reload_script():
            # reload the file changed on disk
            assert self._filepath
            with open(self._filepath, 'r') as file:
                self.graph_model.deserialize(file.read())
                self.setModified(False)

        # ignore file changes, while prompt is open
        from pylive.utils.qt import signalsBlocked
        with signalsBlocked(self._file_watcher):
            if not self.isModified() or QMessageBox.StandardButton.Yes==QMessageBox.information(window, 
                "File has changed on disk!", 
                f"Do you want to reaload '{self.filepath()}'?", 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel):

                reload_script() 

    def create_new_node(self, scenepos:QPointF=QPointF()):
        from pylive.utils.unique import make_unique_name
        existing_names = list(self.graph_model.nodes())
        func_name = make_unique_name("func1", existing_names)
        self.graph_model.addNode(func_name, PyNodeItem())

        ### position node widget
        node_graphics_item = self.graph_view.nodeItem(func_name)
        if node_graphics_item := self.graph_view.nodeItem(func_name):
            node_graphics_item.setPos(scenepos-node_graphics_item.boundingRect().center())

    def compile_selected_nodes(self):
        if not self.node_selection_model:
            return

        nodes = map(self.node_proxy_model.mapToSource, self.node_selection_model.selectedIndexes())
        for node in nodes:
            self.graph_model.compile(node)

    def evaluate_selected_nodes(self):
        if not self.node_selection_model:
            return

        nodes = list(map(self.node_proxy_model.mapToSource, self.node_selection_model.selectedIndexes()))
        raise NotImplementedError("node should be evaluated in topological order")
        for node in nodes:
            self.graph_model.evaluateNode(node)

    def delete_selected(self):
        # delete selected links
        link_indexes:list[QModelIndex] = self.link_selection_model.selectedIndexes()
        link_rows = set(index.row() for index in link_indexes)
        for link_row in sorted(link_rows, reverse=True):
            source, target, outlet, inlet = self.link_proxy_model.mapToSource(self.link_proxy_model.index(link_row, 0))
            self.graph_model.unlinkNodes(source, target, outlet, inlet)

        # delete selected nodes
        node_indexes:list[QModelIndex] = self.node_selection_model.selectedRows(column=0)
        for node_index in sorted(node_indexes, key=lambda idx:idx.row(), reverse=True):
            node = self.node_proxy_model.mapToSource(node_index)
            self.graph_model.removeNode(node)

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
                    self.graph_model.linkNodes(source_node, target_node, "out", inlet)

    def connect_nodes(self, source:str, target:str, inlet:str):
        self.graph_model.linkNodes(source, target, "out", inlet)

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
    window.openFile(parent_folder/"tests/hello_masa.yaml")
    window.setGeometry(QRect(QPoint(), app.primaryScreen().size()).adjusted(40,80,-30,-300))
    window.show()
    sys.exit(app.exec())
# 