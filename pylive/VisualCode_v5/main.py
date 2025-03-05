from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from pathlib import Path

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# from pylive.QtGraphEditor.definitions_model import DefinitionsModel

### DATA ###
# 
# from pylive.QtGraphEditor.py_functions_model import PyFunctionsModel
from pylive.VisualCode_v5.py_graph_model import PyGraphModel
from pylive.VisualCode_v5.py_proxy_node_model import PyProxyNodeModel
from pylive.VisualCode_v5.py_proxy_link_model import PyProxyLinkModel
from pylive.VisualCode_v5.py_graph_view import PyGraphView
from pylive.QtScriptEditor.script_edit import ScriptEdit

from pylive.utils.unique import make_unique_id
import pylive.utils.qtfactory as qf


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
        self.graph_model = PyGraphModel()
        self._document_connections = [
            (self.graph_model.nodesAdded, lambda: self.setModified(True)),
            (self.graph_model.nodesRemoved, lambda: self.setModified(True)),
            (self.graph_model.dataChanged, lambda: self.setModified(True)),
            (self.graph_model.nodesLinked, lambda: self.setModified(True)),
            (self.graph_model.nodesUnlinked, lambda: self.setModified(True))
        ]
        for signal, slot in self._document_connections:
            signal.connect(slot)

        # PROXY MODELS
        self.link_proxy_model = PyProxyLinkModel(self.graph_model)
        self.node_proxy_model = PyProxyNodeModel(self.graph_model)
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
        self.graph_view = PyGraphView()
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

        ### Code Editor
        self.code_edit = ScriptEdit()
        self.code_edit.setDisabled(True)
        self.preview_label = QLabel()

        ### STATUS BAR WIDGET
        self.statusbar = QStatusBar()
        self.statusbar.showMessage("status bar")

        ## MENUBAR

        # Actions
        self.open_action = QAction("Open", self)
        self.save_action = QAction("Save", self)
        self.save_as_action = QAction("Save As", self)
        self.add_node_action = QAction("Add New Node", self)
        self.delete_selected_action = QAction("Delete selected", self)
        self.delete_selected_action.setShortcut("Del")
        self.layout_nodes_action = QAction("layout nodes", self)
        self.center_nodes_action = QAction("center nodes", self)

        self.addActions([
            self.save_action,
            self.save_as_action,
            self.open_action,
            self.add_node_action,
            self.delete_selected_action,
            self.layout_nodes_action,
            self.center_nodes_action
        ])

        menubar = QMenuBar(parent=self)

        filemenu = menubar.addMenu("File")
        filemenu.addActions([
            self.open_action, 
            self.save_action,
            self.save_as_action
        ])
        editmenu = menubar.addMenu("Edit")
        editmenu.addActions([
            self.add_node_action, 
            self.delete_selected_action, 
        ])
        viewmenu = menubar.addMenu("View")
        viewmenu.addActions([self.layout_nodes_action, self.center_nodes_action])

        ### Layout
        main_layout = qf.vboxlayout([
            qf.splitter(Qt.Orientation.Horizontal, [
                self.code_edit,
                qf.tabwidget({
                    'graph':self.graph_view,
                    'sheets':qf.widget(qf.vboxlayout([
                        self.nodes_table_view,
                        self.links_table_view,
                    ])),
                }), 
                self.preview_label
            ]),
            self.statusbar
        ])
        self.statusbar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        main_layout.setMenuBar(menubar)
        self.setLayout(main_layout)
        self.updateWindowTitle()

        self.bind_widgets_to_model()

    def bind_widgets_to_model(self):
        ### Bind widgets to model
        def set_model(node:str, hints:list=[]):
            assert isinstance(node, str)
            current = self.node_selection_model.currentIndex()
            if current.isValid():
                node = self.node_proxy_model.mapToSource(current)
                print(f"set model, {node}, {hints}")
                if 'source' in hints or not hints:
                    node_source = self.graph_model.data(node, 'source')
                    if node_source!=self.code_edit.toPlainText():
                        self.graph_model.setData(node, 'source', self.code_edit.toPlainText())

        def set_editors(node:str, hints:list=[]):
            self.code_edit.setEnabled(True)

            if 'source' in hints or not hints:
                node_source = self.graph_model.data(node, 'source')
                if node_source!=self.code_edit.toPlainText():
                    self.code_edit.setPlainText(node_source)

            if 'result' in hints or not hints:
                error, result = self.graph_model.data(node, 'result')

                if error:
                    self.preview_label.setText(f"{error}")
                else:
                    self.preview_label.setText(f"{result}")

        def clear_editors():
            self.code_edit.setPlainText("")
            self.code_edit.setEnabled(False)
            self.preview_label.setText("")

        self.code_edit.textChanged.connect(lambda: 
            set_model(self.node_proxy_model.mapToSource(self.node_selection_model.currentIndex()), ["source"])
            if self.node_selection_model.currentIndex().isValid() 
            else
            None)

        self.graph_model.dataChanged.connect(lambda node, hints: 
            set_editors(node, hints) 
            if node == self.node_proxy_model.mapToSource(self.node_selection_model.currentIndex()) 
            else 
            None)

        self.node_selection_model.currentChanged.connect(lambda current, previous: 
            set_editors(self.node_proxy_model.mapToSource(current), []) 
            if current.isValid() 
            else 
            clear_editors())

        def update_model_selection():
            selected_node_keys = self.graph_view.selectedNodes()
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

        self.graph_view.nodesLinked.connect(lambda source, target, outlet, inlet: 
            self.connect_nodes(self.node_proxy_model.mapToSource(source), self.node_proxy_model.mapToSource(target), inlet))

        self.graph_view.scene().selectionChanged.connect(update_model_selection)
        
        self.node_selection_model.selectionChanged.connect(lambda selected, deselected:
            update_graphview_selection)

        for signal, slot in self.graph_view_connections:
            signal.connect(slot)
            

        menubar_connections = [
            (self.open_action.triggered, lambda: self.openFile()),
            (self.save_action.triggered, lambda: self.saveFile()),
            (self.save_as_action.triggered, lambda: self.saveAsFile()),
            (self.add_node_action.triggered, lambda: self.create_new_node()),
            (self.delete_selected_action.triggered, lambda: self.delete_selected()),
            (self.layout_nodes_action.triggered, lambda: self.graph_view.layoutNodes()),
            (self.center_nodes_action.triggered, lambda: self.graph_view.centerNodes())
        ]
        for signal, slot in menubar_connections:
            signal.connect(slot)

    def sizeHint(self):
        return QSize(2048, 900) 

    ### Commands
    def create_new_node(self, scenepos:QPointF=QPointF()):
        existing_names = list(self.graph_model.nodes())

        func_name = make_unique_id(6)
        self.graph_model.addNode(func_name)

        ### position node widget
        node_graphics_item = self.graph_view.nodeItem(func_name)
        if node_graphics_item := self.graph_view.nodeItem(func_name):
            node_graphics_item.setPos(scenepos-node_graphics_item.boundingRect().center())

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

    def connect_nodes(self, source:str, target:str, inlet:str):
        self.graph_model.linkNodes(source, target, "out", inlet)

    def eventFilter(self, watched, event):
        if watched == self.graph_view:
            if event.type() == QEvent.Type.MouseButtonDblClick:
                event = cast(QMouseEvent, event)
                self.create_new_node(self.graph_view.mapToScene(event.position().toPoint()))
                return True

        return super().eventFilter(watched, event)

    ### Document
    def fileFilter(self):
        return ".yaml"

    def fileSelectFilter(self):
        return "YAML (*.yaml);;Any File (*)"

    def isModified(self):
        return self._is_modified

    def setModified(self, m:bool):
        self._is_modified = m
        self.updateWindowTitle()

    def openFile(self, filepath:Path|str|None=None):
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
                return

        # read and parse existing text file
        try:
            self.graph_model.load(filepath)
        except FileExistsError:
            print("'{filepath}'' does not exist!")
            import traceback
            traceback.print_exc()
        except Exception as err:
            import traceback

            print(f"Error occured while opening {filepath}", err)
            traceback.print_exc()
        else:
            self._filepath = filepath
            print(f"Successfully opened '{filepath}'!")
            self.updateWindowTitle()

    def saveFile(self):
        filepath = self._filepath
        if not filepath:
            filepath, filter_used = QFileDialog.getSaveFileName(self, 
                "Save", self.fileFilter(), self.fileSelectFilter())
            if not filepath:
                return # if no filepath was choosen cancel saving

        """ note
        We must stop watching this file, otherwise it will silently reload the
        script. It reloads silently, because if the document is not modified,
        and the file has been changed, it will silently reload the script.
        """
        self._file_watcher.removePath(str(filepath)) 
        try:
            with open(filepath, 'w') as file:
                file_contents = self.graph_model.serialize()
                file.write(file_contents)
                self.setModified(False)
        except FileNotFoundError as err:
            QMessageBox.warning(None, "Warning", f"{err}")
        else:
            if filepath not in self._file_watcher.files():
                self._file_watcher.addPath(str(filepath))
            self._filepath = filepath
        self.updateWindowTitle()

    def saveAsFile(self):
        filepath, filter_used = QFileDialog.getSaveFileName(self, 
            "SaveAs", self.fileFilter(), self.fileSelectFilter())
        if not filepath:
            return # if no filepath was choosen cancel saving

        try:
            with open(filepath, 'w') as file:
                file_contents = self.graph_model.serialize()
                file.write(file_contents)
                self.setModified(False)
        except FileNotFoundError as err:
            QMessageBox.warning(None, "Warning", f"{err}")
        else:
            if self._filepath:
                self._file_watcher.removePath(str(self._filepath))
            if filepath not in self._file_watcher.files():
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

    def updateWindowTitle(self):
        self.setWindowTitle(f"VisuelCode v4 - {str(Path(self._filepath).name) if self._filepath else 'Untitled'}{' *' if self.isModified() else ''}")

if __name__ == "__main__":
    import sys
    from pathlib import Path
    import pathlib
    parent_folder = pathlib.Path(__file__).parent.resolve()
    print("Python Visual Editor starting...\n  working directory:", Path.cwd())

    app = QApplication()
    window = Window()
    window.setGeometry(QRect(QPoint(), app.primaryScreen().size()).adjusted(40,80,-30,-300))
    window.show()
    sys.exit(app.exec())
# 