from importlib.machinery import ModuleSpec
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
from pylive.VisualCode_v6.py_graph_model import PyImportsModel, PyGraphModel
from pylive.VisualCode_v6.py_proxy_node_model import PyProxyNodeModel
from pylive.VisualCode_v6.py_proxy_link_model import PyProxyLinkModel
from pylive.VisualCode_v6.py_graph_view import PyGraphView
from pylive.QtScriptEditor.script_edit import ScriptEdit

from pylive.utils.unique import make_unique_id
import pylive.utils.qtfactory as qf


class ImportsManager(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self.imports_list = QListWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<h1>Imports manager</h1>"))
        self.new_import_edit = QLineEdit()
        layout.addWidget(self.new_import_edit)
        layout.addWidget(self.imports_list)
        self.delete_button = QPushButton("remove")
        layout.addWidget(self.delete_button)
        self.setLayout(layout)

        self._model:PyGraphModel|None = None

        self.completer = QCompleter(self.new_import_edit)
        packages = self._listAvailablePackages()
        packages_modell = QStringListModel(packages)
        self.completer.setModel(packages_modell)
        self.new_import_edit.setCompleter(self.completer)

        self._connections = []

    def setModel(self, model:PyGraphModel|None):
        if self._model:
            for signal, slot in self._connections:
                signal.disconnect(slot)
        if model:
            def appendImport(module_name):
                assert self._model
                self.new_import_edit.clear()
                current_imports = [_ for _ in self._model.imports()]
                current_imports.append(module_name)
                self._model.setImports(current_imports)

            def removeSelectedImports():
                assert self._model
                selected_packages = [item.text() for item in self.imports_list.selectedItems()]
                current_imports = self._model.imports()
                new_imports = [pkg for pkg in current_imports if pkg not in selected_packages]
                self._model.setImports(new_imports)

            self._connections = [
                (model.importsReset, self.refreshImports),
                (self.new_import_edit.returnPressed, lambda: appendImport(self.new_import_edit.text())),
                (self.delete_button.pressed, lambda: removeSelectedImports())
            ]
            for signal, slot in self._connections:
                signal.connect(slot)

        self._model = model
        self.refreshImports()

    def _listAvailablePackages(self):
        import pkgutil
        return [module.name 
            for module in pkgutil.iter_modules() 
            if not module.name.startswith("_")
        ]

    def refreshImports(self):
        assert self._model
        self.imports_list.clear()
        for row, module_name in enumerate(self._model.imports()):
            self.imports_list.insertItem(row, QListWidgetItem(module_name))


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
        self._model:PyGraphModel|None = None
        
        ### bindings
        self._connections = []
        self._document_connections = []
        self._graph_view_connections = []

        # PROXY MODELS
        self.link_proxy_model = PyProxyLinkModel()
        self.node_proxy_model = PyProxyNodeModel()
        self.node_selection_model = QItemSelectionModel(self.node_proxy_model)
        self.link_selection_model = QItemSelectionModel(self.link_proxy_model)

        ### UI
        self.setupUI()

        ### init
        self.setModel(PyGraphModel())

    def showEvent(self, event: QShowEvent) -> None:
        self.graph_view.centerNodes()

    def setupUI(self):
        ### GRAPH View
        self.graph_view = PyGraphView()
        self.graph_view.installEventFilter(self)

        ### Imports manager
        self.import_manager = ImportsManager()

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
        
        ### Inspector
        self.kind_dropdown = QComboBox()
        self.kind_dropdown.insertItems(0, ['operator', 'value', 'expression'])
        self.kind_dropdown.setDisabled(True)
        self.expression_edit = QLineEdit()
        self.expression_edit.setDisabled(True)
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
        self.restart_kernel_action = QAction("restart kernel")
        self.layout_nodes_action = QAction("layout nodes", self)
        self.center_nodes_action = QAction("center nodes", self)

        self.addActions([
            self.save_action,
            self.save_as_action,
            self.open_action,
            self.restart_kernel_action,
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

        filemenu = menubar.addMenu("Kernel")
        filemenu.addActions([
            self.restart_kernel_action
        ])

        editmenu = menubar.addMenu("Edit")
        editmenu.addActions([
            self.add_node_action, 
            self.delete_selected_action, 
        ])

        viewmenu = menubar.addMenu("View")
        viewmenu.addActions([self.layout_nodes_action, self.center_nodes_action])

        ### Layout
        inspector_panel = qf.widget(qf.vboxlayout([
            self.kind_dropdown,
            self.expression_edit,
        ]))
        graphpanel = QWidget()
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.graph_view, 0, 0)
        inspector_panel.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        grid_layout.addWidget(inspector_panel, 0, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        graphpanel.setLayout(grid_layout)

        preview_panel = QScrollArea()
        preview_panel.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter)
        preview_panel.setWidgetResizable(True)
        self.preview_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        preview_panel.setWidget(self.preview_label)

        main_layout = qf.vboxlayout([
            qf.splitter(Qt.Orientation.Horizontal, [
                self.import_manager,
                qf.tabwidget({
                    'graph': graphpanel,
                    'sheets':qf.widget(qf.vboxlayout([
                        self.nodes_table_view,
                        self.links_table_view,
                    ])),
                }),
                preview_panel
            ]),
            self.statusbar
        ])
        self.statusbar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        main_layout.setMenuBar(menubar)
        self.setLayout(main_layout)
        self.updateWindowTitle()
        self.bind_widgets_to_model()

    def setModel(self, model:PyGraphModel|None):
        if self._model:
            for signal, slot in self._document_connections:
                signal.disconnect(slot)
            for signal, slot in self._connections:
                signal.disconnect(slot)

        if model:
            ### subviews
            self.link_proxy_model.setSourceModel(model)
            self.node_proxy_model.setSourceModel(model)
            self.graph_view.setModel(model)

            self.import_manager.setModel(model)

            ### Connections
            self._connections = [
                (model.dataChanged, lambda nodes, hints: 
                    self.set_node_editors(self.node_proxy_model.mapToSource(self.node_selection_model.currentIndex()), hints) 
                    if self.node_proxy_model.mapToSource(self.node_selection_model.currentIndex()) in nodes
                    else 
                    None),

            ]

            for signal, slot in self._connections:
                signal.connect(slot)

            ### document
            self._document_connections = [
                (model.nodesAdded, lambda: self.setModified(True)),
                (model.nodesRemoved, lambda: self.setModified(True)),
                (model.dataChanged, lambda: self.setModified(True)),
                (model.nodesLinked, lambda: self.setModified(True)),
                (model.nodesUnlinked, lambda: self.setModified(True))
            ]
            for signal, slot in self._document_connections:
                signal.connect(slot)

        self._model = model

    def set_node_editors(self, node:str, hints:list=[]):
        assert self._model
        self.expression_edit.setEnabled(True)
        self.kind_dropdown.setEnabled(True)

        if 'kind' in hints or not hints:
            node_kind = self._model.data(node, 'kind')
            if node_kind!=self.kind_dropdown.currentText():
                self.kind_dropdown.setCurrentText(node_kind)

        if 'expression' in hints or not hints:
            node_source = self._model.data(node, 'expression')
            if node_source!=self.expression_edit.text():
                self.expression_edit.setText(node_source)

        if 'result' in hints or not hints:
            error, result = self._model.data(node, 'result')

            if error:
                self.preview_label.setText(f"{error}")
            else:
                self.preview_label.setText(f"{result}")

    def set_node_model(self, node:str, hints:list=[]):
        assert isinstance(node, str)
        assert self._model
        current = self.node_selection_model.currentIndex()
        if current.isValid():
            node = self.node_proxy_model.mapToSource(current)
            if 'kind' in hints or not hints:
                node_kind = self._model.data(node, 'kind')
                if node_kind!=self.kind_dropdown.currentText():
                    self._model.setData(node, 'kind', self.kind_dropdown.currentText())

            if 'expression' in hints or not hints:
                node_source = self._model.data(node, 'expression')
                if node_source!=self.expression_edit.text():
                    self._model.setData(node, 'expression', self.expression_edit.text())

    def clear_node_editors(self):
        self.expression_edit.setText("")
        self.expression_edit.setEnabled(False)
        self.kind_dropdown.setEnabled(False)
        self.preview_label.setText("")

    def bind_widgets_to_model(self):
        ### Bind widgets to model
        self.expression_edit.editingFinished.connect(lambda: 
            self.set_node_model(self.node_proxy_model.mapToSource(self.node_selection_model.currentIndex()), ["expression"])
            if self.node_selection_model.currentIndex().isValid() 
            else
            None)

        self.kind_dropdown.currentIndexChanged.connect(lambda: 
            self.set_node_model(self.node_proxy_model.mapToSource(self.node_selection_model.currentIndex()), ["kind"])
            if self.node_selection_model.currentIndex().isValid() 
            else
            None)

        ### node selection
        self.node_selection_model.currentChanged.connect(lambda current, previous: 
            self.set_node_editors(self.node_proxy_model.mapToSource(current), []) 
            if current.isValid() 
            else 
            self.clear_node_editors())

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

        self.graph_view.scene().selectionChanged.connect(update_model_selection)
        
        self.node_selection_model.selectionChanged.connect(lambda selected, deselected:
            update_graphview_selection)

        self.graph_view.nodesLinked.connect(lambda source, target, outlet, inlet: 
            self.connect_nodes(self.node_proxy_model.mapToSource(source), self.node_proxy_model.mapToSource(target), inlet))

        for signal, slot in self._graph_view_connections:
            signal.connect(slot)

        self._menubar_connections = [
            (self.open_action.triggered, lambda checked: self.openFile()),
            (self.save_action.triggered, lambda checked: self.saveFile()),
            (self.save_as_action.triggered, lambda checked: self.saveAsFile()),
            (self.add_node_action.triggered, lambda checked: self.create_new_node()),
            (self.delete_selected_action.triggered, lambda checked: self.delete_selected()),
            (self.layout_nodes_action.triggered, lambda checked: self.graph_view.layoutNodes()),
            (self.center_nodes_action.triggered, lambda checked: self.graph_view.centerNodes()),
            (self.restart_kernel_action.triggered, lambda checked, model=self._model: self._model.restartKernel() if self._model else None)
        ]
        for signal, slot in self._menubar_connections:
            signal.connect(slot)

    def sizeHint(self):
        return QSize(2048, 900) 

    ### Commands
    def create_new_node(self, scenepos:QPointF=QPointF()):
        assert self._model
        existing_names = list(self._model.nodes())

        func_name = make_unique_id(6)
        self._model.addNode(func_name, "print", kind='operator')

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
        filepath = Path(filepath)
        try:
            self.setWorkingDirectory(filepath.parent)
            import yaml
            text = Path(filepath).read_text()
            data = yaml.load(text, Loader=yaml.SafeLoader)
            graph = PyGraphModel.fromData(data)
            self.setModel(graph)
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

    def setWorkingDirectory(self, path:Path):
        assert path.is_dir()
        import os
        os.chdir(path)
        print("setWorkingDirectory:", Path.cwd())

    def saveFile(self):
        assert self._model
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
                import yaml
                data = self._model.toData()
                text = yaml.dump(self._model.toData(), sort_keys=False)
                Path(filepath).write_text(text)
                self.setModified(False)
        except FileNotFoundError as err:
            QMessageBox.warning(None, "Warning", f"{err}")
        else:
            if filepath not in self._file_watcher.files():
                self._file_watcher.addPath(str(filepath))
            self._filepath = filepath
        self.updateWindowTitle()

    def saveAsFile(self):
        assert self._model
        filepath, filter_used = QFileDialog.getSaveFileName(self, 
            "SaveAs", self.fileFilter(), self.fileSelectFilter())
        if not filepath:
            return # if no filepath was choosen cancel saving

        try:
            with open(filepath, 'w') as file:
                file_contents = self._model.serialize()
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
            match QMessageBox.question(self, "Save changes before closing?", f"{self._filepath or "unititled"}", QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No):
                case QMessageBox.StandardButton.Yes:
                    self.saveFile()
                    return True
                case QMessageBox.StandardButton.No:
                    return True
                case QMessageBox.StandardButton.Cancel:
                    return False
        return True

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.closeFile():
            super().closeEvent(event)

    def filepath(self):
        return self._filepath

    def _onFileChanged(self, path):
        assert path == self._filepath

        def reload_script():
            # reload the file changed on disk
            assert self._filepath
            with open(self._filepath, 'r') as file:
                self._model.deserialize(file.read())
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
    window.openFile(Path.cwd()/"./tests/dissertation_builder.yaml")
    sys.exit(app.exec())
    