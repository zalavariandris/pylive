
from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

# from pylive.QtGraphEditor.definitions_model import DefinitionsModel
from pylive.qt_components.tile_widget import TileWidget
from pylive.qt_components.qt_options_dialog import QOptionDialog


### DATA ###

# from pylive.QtGraphEditor.py_functions_model import PyFunctionsModel
from py_graph_model import PyGraphModel
from graph_editor.standard_edges_model import StandardEdgesModel, StandardEdgeItem


from pylive.VisualCode_v4.graph_editor.graph_editor_view import GraphEditorView
from pylive.QtScriptEditor.script_edit import ScriptEdit
from pylive.utils.qt import logModelSignals


def log_call(fn, *args, **kwargs):
    print(f"{fn.__name__} was called")
    return fn(*args, **kwargs)


class PyInspectorView(QFrame):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._selection:QItemSelectionModel|None=None
        self._nodes:PyNodesModel|None=None
        self._edges:StandardEdgesModel|None=None
        self.setFrameShape(QFrame.Shape.StyledPanel)  # Styled panel for the frame
        self.setFrameShadow(QFrame.Shadow.Raised)

        self.name_edit = QLineEdit()
        self.inspector_header_tile = TileWidget()

        self.property_editor = QTableWidget()
        self.property_editor.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.property_editor.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.property_editor.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.property_editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.property_editor.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.name_edit)
        main_layout.addWidget(self.inspector_header_tile)
        main_layout.addWidget(self.property_editor)
        self.node_function_source_editor = ScriptEdit()
        main_layout.addWidget(self.node_function_source_editor)
        self.setLayout(main_layout)

        # map editors to data
        self.name_edit.textChanged.connect(lambda text:
            self._onEditorChanged(0, self.name_edit.text())
        )
        self.node_function_source_editor.textChanged.connect(lambda:
            self._onEditorChanged(1, self.node_function_source_editor.toPlainText())
        )

    def setModel(self, nodes:PyNodesModel|None, edges:StandardEdgesModel|None):
        if self._nodes:
            self._nodes.dataChanged.disconnect(self._onDataChanged)

        if self._edges:
            ...

        if nodes:
            nodes.dataChanged.connect(self._onDataChanged)

        if edges:
            ...

        self._nodes = nodes
        self._edges = edges

    def setNodeSelectionModel(self, selection:QItemSelectionModel):
        if self._selection:
            self._selection.currentChanged.disconnect(self._onDataChanged)

        if selection:
            selection.currentChanged.connect(self._onCurrentChanged)

        self._selection = selection

    def currentRow(self)->int:
        if not self._selection:
            return -1
        return self._selection.currentIndex().row()

    def _onDataChanged(self, tl, br, roles):
        self.update_node_inspector()

    def _onEditorChanged(self, column:int, value:Any):
        assert self._nodes
        index = self._nodes.index(self.currentRow(), column)
        self._nodes.setData(index, value)

    def _onCurrentChanged(self, current, previous):
        self.update_node_inspector()

    def update_node_inspector(self):
        assert self._selection
        assert self._nodes
        assert self._edges

        current_node_index = self._selection.currentIndex().siblingAtColumn(0)
        if current_node_index.isValid():
            self.show()
            node_item = self._nodes.nodeItemFromIndex(current_node_index)
            assert node_item is not None, f"cant be None, got: {node_item}"

            # update name editor
            name = node_item.name
            if name!=self.name_edit.text():
                self.name_edit.setText(name)

            # update heading
            self.inspector_header_tile.setHeading(self._nodes.data(current_node_index, Qt.ItemDataRole.DisplayRole))
            self.inspector_header_tile.setSubHeading(f"(inline function)")

            # update property editor
            inlets = self._nodes.inlets(current_node_index.row())
            fields = self._nodes.dataByColumnName(current_node_index.row(), 'fields')
            in_edges = self._edges.inEdges(current_node_index.row())

            self.property_editor.setVerticalHeaderLabels([_ for _ in inlets])
            self.property_editor.setRowCount(len(inlets))
            self.property_editor.setColumnCount(1)
            self.property_editor.setHorizontalHeaderLabels(["value"])

            
            for inlet_row, inlet in enumerate(inlets):
                if inlet in [edge_item.inlet for edge_item in in_edges]:
                    sources = [f"{self._nodes.data(edge_item.source)}.{edge_item.outlet}" for edge_item in in_edges]
                    self.property_editor.setItem(inlet_row, 0, QTableWidgetItem(f"linked to: {",".join(sources)}"))
                elif inlet in fields:
                    self.property_editor.setItem(inlet_row, 0, QTableWidgetItem(fields[inlet]))
                else:
                    self.property_editor.setItem(inlet_row, 0, QTableWidgetItem('-no value set-'))

            # update code editor
            code = node_item.code
            if code!= self.node_function_source_editor.toPlainText():
                self.node_function_source_editor.setPlainText(code)

        else:
            self.hide()
            self.inspector_header_tile.setHeading("")
            self.inspector_header_tile.setSubHeading("")
            self.node_function_source_editor.setPlainText("")


class PyPreviewView(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._nodes: PyNodesModel|None=None
        self._selection:QItemSelectionModel|None=None

    
        self._status_label = QLabel(self)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)        
        self._result_label = QLabel(self)
        self._result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label = QLabel(self)
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self._status_label)
        main_layout.addWidget(self._result_label)
        main_layout.addWidget(self._error_label)
        self.setLayout(main_layout)

    def setNodesModel(self, nodes:PyNodesModel):
        if self._nodes:
            nodes.dataChanged.disconnect(self._onDataChanged)

        if nodes:
            nodes.dataChanged.connect(self._onDataChanged)

        self._nodes = nodes

    def setNodeSelectionModel(self, selection:QItemSelectionModel):
        if self._selection:
            self._selection.currentChanged.disconnect(self._onDataChanged)

        if selection:
            selection.currentChanged.connect(self._onCurrentChanged)

        self._selection = selection

    def _onDataChanged(self, tl, br, roles):
        assert self._selection
        assert self._nodes
        if not self._selection.currentIndex().isValid():
            return

        current_index = self._selection.currentIndex()
        headers = [self._nodes.headerData(col, Qt.Orientation.Horizontal) for col in range(self._nodes.columnCount())]

        status_column = headers.index("status")
        result_column = headers.index("result")
        error_column = headers.index("error")

        CurrentRowChanged = tl.row() <= current_index.row() <= br.row()
        StatusColumChanged = tl.column() <= status_column <= br.column()
        ResultColumChanged = tl.column() <= result_column <= br.column()
        ErrorColumChanged = tl.column() <= error_column <= br.column()

        CurrentStatusChaned = CurrentRowChanged and StatusColumChanged
        CurrentResultChaned = CurrentRowChanged and ResultColumChanged
        CurrentErrorChaned = CurrentRowChanged and ErrorColumChanged

        if CurrentStatusChaned:
            status_data = current_index.siblingAtColumn(status_column).data()
            self._status_label.setText( f"{status_data}" )

        if CurrentResultChaned:
            result_data = current_index.siblingAtColumn(result_column).data()
            self._result_label.setText( f"{result_data}" )

        if CurrentErrorChaned:
            error_data = current_index.siblingAtColumn(error_column).data()
            self._error_label.setText( f"{error_data}" )

    def _onCurrentChanged(self, current, previous):
        if current.isValid():
            assert self._nodes
            headers = [self._nodes.headerData(col, Qt.Orientation.Horizontal) for col in range(self._nodes.columnCount())]
            status_column = headers.index("status")
            result_column = headers.index("result")
            error_column = headers.index("error")
            
            status_data = current.siblingAtColumn(status_column).data()
            result_data = current.siblingAtColumn(result_column).data()
            error_data = current.siblingAtColumn(error_column).data()

            self._status_label.setText( f"{status_data}" )
            self._result_label.setText( f"{result_data}" )
            self._error_label.setText( f"{error_data}" )
        else:
            self._status_label.setText( f"- no selection -" )
            self._result_label.setText( f"- no result -" )
            self._error_label.setText( f"- no error -" )


class PyGraphView(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self.graphview = GraphEditorView()

    def setModel(self, model:PyGraphModel):
        self._model = model


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
        self.graph_model = PyGraphModel()
        self.proxy_nodes_model = PyGraphNodesTableProxyModel(self.graph_model)
        # self.nodes_model = self.graph_model.nodes()
        self.edges_model = self.graph_model.edges()
        
        self.node_selection = QItemSelectionModel(self.proxy_nodes_model)
        self.edge_selection = QItemSelectionModel(self.edges_model)

        # logModelSignals(self.graph_model._nodes_model)

        # compile nodes when inserted
        @self.graph_model.nodesReset.connect
        def _():
            for row in range(self.graph_model.nodeCount()):
                self.graph_model.compileNode(row) 
        
        @self.graph_model.nodesInserted.connect
        def _(parent, first, last): 
            for row in range(first, last+1):
                self.graph_model.compileNode(row) 

        # on source change, compile node
        @self.graph_model.nodeChanged.connect
        def _(tl:QModelIndex, br:QModelIndex, roles:list=[]):
            headers = [self.graph_model._nodes_model.headerData(col, Qt.Orientation.Horizontal) for col in range(self.graph_item._nodes_model.columnCount())]
            source_column = headers.index("code")
            if source_column in range(tl.column(), br.column()+1):
                for row in range(tl.row(), br.row()+1):
                    self.graph_model.compileNode(row)
                    self.graph_model.evaluateNode(row)


        @self.node_selection.currentChanged.connect
        def _(current:QModelIndex, previous:QModelIndex):
            if current.isValid():
                self.graph_model.evaluateNode(current.row())
            else:
                pass
            # for row in range(first, last+1):
            #     self.graph_model.evaluateNode(row) 
        
        ### Widgets
        self.nodes_sheet_table_view = QTableView()
        self.nodes_sheet_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.nodes_sheet_table_view.setModel(self.proxy_nodes_model)
        
        # self.nodes_sheet_table_view.setSelectionModel(self.node_selection)
        self.nodes_sheet_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.nodes_sheet_table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.nodes_sheet_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.edges_sheet_table_view = QTableView(self)
        self.edges_sheet_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.edges_sheet_table_view.setModel(self.graph_model.edges())
        self.edges_sheet_table_view.setSelectionModel(self.edge_selection)
        self.edges_sheet_table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.edges_sheet_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.edges_sheet_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.graph_view = GraphEditorView()
        self.graph_view.installEventFilter(self)
        self.graph_view.setModel(self.graph_model.edges())
        self.graph_view.setSelectionModel(self.node_selection)

        ### NODEINSPECTOR
        self.node_inspector = PyInspectorView()
        self.node_inspector.setModel(self.graph_model._nodes_model, self.graph_model.edges())
        self.node_inspector.setNodeSelectionModel(self.node_selection)

        ### PREVIEW WIDGET
        self.preview = PyPreviewView()
        self.preview.setNodesModel(self.graph_model._nodes_model)
        self.preview.setNodeSelectionModel(self.node_selection)


        # self.preview.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)

        ### STATUS BAR WIDGET
        self.statusbar = QStatusBar()
        self.statusbar.showMessage("status bar")

        ### DEFINITION CODE EDITOR
        self.definition_script_editor = ScriptEdit()

        # Actions
        open_action = QAction("open", self)
        open_action.triggered.connect(lambda: self.openFile())
        save_action = QAction("save", self)
        save_action.triggered.connect(lambda: self.saveFile())
        add_node_action = QAction("add new node", self)
        add_node_action.triggered.connect(lambda: self.create_new_node())
        delete_node_action = QAction("delete node", self)
        delete_node_action.triggered.connect(lambda: self.delete_selected_nodes())
        remove_edge_action = QAction("remove edge", self)
        remove_edge_action.triggered.connect(lambda: self.delete_selected_edges())
        compile_node_action = QAction("compile selected node", self)
        compile_node_action.triggered.connect(lambda: self.graph_item.compileNode(self.node_selection.currentIndex().row()))
        evaluate_node_action = QAction("evaluate selected node", self)
        evaluate_node_action.triggered.connect(lambda: self.graph_item.evaluateNode(self.node_selection.currentIndex().row()))

        self.addActions([
            save_action,
            open_action,
            add_node_action,
            delete_node_action,
            remove_edge_action,
            compile_node_action,
            evaluate_node_action
        ])

        ### menubar
        menubar = QMenuBar(parent=self)
        menubar.addActions(self.actions())

        ### Layout
        import pylive.utils.qtfactory as qf
        def create_graph_panel():
            panel = QWidget()
            grid_layout = QGridLayout()
            panel.setLayout(grid_layout)

            grid_layout.addWidget(self.graph_view, 0, 0)
            grid_layout.addWidget(self.node_inspector,0,0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
            # self.node_inspector.hide()
            panel.setLayout(grid_layout)
            return panel

        def create_graph_sheets():
            return qf.widget(qf.vboxlayout([
                qf.vboxlayout([QLabel("nodes"), self.nodes_sheet_table_view]),
                qf.vboxlayout([QLabel("edges"), self.edges_sheet_table_view]),
            ]))

        main_layout = qf.vboxlayout([
            qf.splitter(Qt.Orientation.Horizontal, [
                # qf.tabwidget({
                #     'graph': create_graph_panel(),
                #     'sheets': create_graph_sheets()
                # }),
                create_graph_sheets(),
                create_graph_panel(),
                self.preview
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

    def setIsModified(self, m:bool):
        self._is_modified = m

    @Slot()
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
            self.graph_view.centerNodes()
            print(f"Successfully opened '{filepath}'!")
            return True
        except FileExistsError:
            print("'{filepath}'' does not exist!")
            return False
        except Exception as err:
            print(f"Error occured while opening {filepath}", err)
            return False

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

    @Slot()
    def saveFile(self):
        ...

    @Slot()
    def create_new_node(self, position:QPointF=QPointF()):
        dialog = QDialog()
        dialog.setWindowTitle("Create Node")
        dialog.setModal(True)
        layout = QVBoxLayout()

        ## popup definition selector
        node_item = PyNodeItem(
            name="",
            code="""def func():\n  ..."""
        )
        self.graph_model.insertNodeItem(0, node_item)

        #
        node_index = self.graph_model.nodes().index(self.graph_model.nodeCount()-1)
        node_graphics_item = self.graph_view.nodeWidget(node_index)
        if node_graphics_item := self.graph_view.nodeWidget(node_index):
            node_graphics_item.setPos(position)

    @Slot()
    def delete_selected_nodes(self):
        indexes:list[QModelIndex] = self.node_selection.selectedRows(column=0)
        for index in sorted(indexes, key=lambda idx:idx.row(), reverse=True):
            self.graph_model.removeNodes(index.row(), 1)

    @Slot()
    def delete_selected_edges(self):
        indexes:list[QModelIndex] = self.edge_selection.selectedRows(column=0)
        for index in sorted(indexes, key=lambda idx:idx.row(), reverse=True):
            self.graph_model.edges().removeRows(index.row(), 1)


if __name__ == "__main__":
    app = QApplication()
    screen_size = app.primaryScreen().size()
    window = Window()
    rect = QRect(QPoint(), screen_size).adjusted(40,80,-30,-100)
    print(rect)
    window.setGeometry(rect)
    # window.resize(screen_size)
    window.show()
    from pathlib import Path
    import pathlib
    parent_folder = pathlib.Path(__file__).parent.resolve()
    print("working directory:", Path.cwd())
    window.openFile(parent_folder/"tests/website_builder.yaml")
    app.exec()

