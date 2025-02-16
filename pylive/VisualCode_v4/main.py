
from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

# from pylive.QtGraphEditor.definitions_model import DefinitionsModel
from pylive.qt_components.tile_widget import TileWidget
from pylive.qt_components.qt_options_dialog import QOptionDialog


### DATA ###

# from pylive.QtGraphEditor.py_functions_model import PyFunctionsModel
from py_fields_model import PyFieldsModel, PyFieldItem
from py_nodes_model import PyNodesModel, PyNodeItem
from graph_editor.standard_edges_model import StandardEdgesModel, StandardEdgeItem

from py_graph_item import PyGraphItem

from pylive.utils.unique import make_unique_id, make_unique_name
from pylive.VisualCode_v4.graph_editor.graph_editor_view import GraphEditorView
from pylive.QtScriptEditor.script_edit import ScriptEdit


def log_call(fn, *args, **kwargs):
    print(f"{fn.__name__} was called")
    return fn(*args, **kwargs)


class InspectorView(QFrame):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._selection:QItemSelectionModel|None=None
        self._nodes:PyNodesModel|None=None


        self.setFrameShape(QFrame.Shape.StyledPanel)  # Styled panel for the frame
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.inspector_header_tile = TileWidget()
        self.property_editor = QTableView()
        self.property_editor.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.property_editor.setModel(None)
        inspector_layout = QVBoxLayout()
        inspector_layout.addWidget(self.inspector_header_tile)
        inspector_layout.addWidget(self.property_editor)
        self.node_function_source_editor = ScriptEdit()
        inspector_layout.addWidget(self.node_function_source_editor)
        self.setLayout(inspector_layout)

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
        self.update_node_inspector()

    def _onCurrentChanged(self, current, previous):
        self.update_node_inspector()

    def update_node_inspector(self):
        assert self._selection
        assert self._nodes
        current_node_index = self._selection.currentIndex().siblingAtColumn(0)
        if current_node_index.isValid():
            self.show()

            self.inspector_header_tile.setHeading(self._nodes.data(current_node_index, Qt.ItemDataRole.DisplayRole))
            self.inspector_header_tile.setSubHeading(f"(inline function)")
            node_item = self._nodes.nodeItemFromIndex(current_node_index)
            assert node_item is not None, f"cant be None, got: {node_item}"

            if code:= node_item.code:
                self.node_function_source_editor.setPlainText(code)
            else:
                self.node_function_source_editor.setPlainText("")

        else:
            self.hide()
            self.inspector_header_tile.setHeading("")
            self.inspector_header_tile.setSubHeading("")
            self.node_function_source_editor.setPlainText("")


class PreviewView(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._nodes: PyNodesModel|None=None
        self._selection:QItemSelectionModel|None=None


        main_layout = QVBoxLayout()
        self._preview_widget = QLabel(self)
        self._preview_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(self._preview_widget)
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
        if not self._selection.currentIndex().isValid():
            return

        current_index = self._selection.currentIndex()
        headers = [self._nodes.headerData(col, Qt.Orientation.Horizontal) for col in range(self._nodes.columnCount())]
        result_column = headers.index("result")

        CurrentRowChanged = tl.row() <= current_index.row() <= br.row()
        ResultColumChanged = tl.column() <= result_column <= br.column()
        CurrentResultChaned = CurrentRowChanged and ResultColumChanged

        if CurrentResultChaned:
            result_data = current_index.siblingAtColumn(result_column).data()
            self.displayData(result_data)

    def _onCurrentChanged(self, current, previous):
        if current.isValid():
            headers = [self._nodes.headerData(col, Qt.Orientation.Horizontal) for col in range(self._nodes.columnCount())]
            result_column = headers.index("result")
            result_data = current.siblingAtColumn(result_column).data()
            self.displayData(result_data)
        else:
            self.displayData("-no selection-")

    def displayData(self, data:Any):
        self._preview_widget.setText( f"{data}" )


class PreviewView(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._nodes: PyNodesModel|None=None
        self._selection:QItemSelectionModel|None=None


        main_layout = QVBoxLayout()
        self._preview_widget = QLabel(self)
        self._preview_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self._preview_widget)
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
        if not self._selection.currentIndex().isValid():
            return

        current_index = self._selection.currentIndex()
        headers = [self._nodes.headerData(col, Qt.Orientation.Horizontal) for col in range(self._nodes.columnCount())]
        result_column = headers.index("result")

        CurrentRowChanged = tl.row() <= current_index.row() <= br.row()
        ResultColumChanged = tl.column() <= result_column <= br.column()
        CurrentResultChaned = CurrentRowChanged and ResultColumChanged

        if CurrentResultChaned:
            result_data = current_index.siblingAtColumn(result_column).data()
            self.displayData(result_data)

    def _onCurrentChanged(self, current, previous):
        if current.isValid():
            headers = [self._nodes.headerData(col, Qt.Orientation.Horizontal) for col in range(self._nodes.columnCount())]
            result_column = headers.index("result")
            result_data = current.siblingAtColumn(result_column).data()
            self.displayData(result_data)
        else:
            self.displayData("-no selection-")

    def displayData(self, data:Any):
        self._preview_widget.setText( f"{data}" )
        


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
        self.graph_item = PyGraphItem()
        self.node_selection = QItemSelectionModel(self.graph_item.nodes())
        self.edge_selection = QItemSelectionModel(self.graph_item.edges())

        # compile nodes when inserted
        @self.graph_item.nodes().modelReset.connect
        def _():
            print("modelReset->Compil nodes")
            for row in range(self.graph_item.nodes().rowCount()):
                self.graph_item.nodes().compileNode(row) 
        
        @self.graph_item.nodes().rowsInserted.connect
        def _(parent, first, last): 
            for row in range(first, last+1):
                self.graph_item.nodes().compileNode(row) 

        @self.node_selection.currentChanged.connect
        def _(current:QModelIndex, previous:QModelIndex):
            print('currentChanged', current, previous) 
            if current.isValid():
                self.graph_item.evaluateNode(current)
            else:
                pass
            # for row in range(first, last+1):
            #     self.graph_item.evaluateNode(row) 
        
        ### Widgets
        self.nodes_sheet_table_view = QTableView()
        self.nodes_sheet_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.nodes_sheet_table_view.setModel(self.graph_item.nodes())
        self.nodes_sheet_table_view.setSelectionModel(self.node_selection)
        self.nodes_sheet_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.nodes_sheet_table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.nodes_sheet_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.edges_sheet_table_view = QTableView(self)
        self.edges_sheet_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.edges_sheet_table_view.setModel(self.graph_item.edges())
        self.edges_sheet_table_view.setSelectionModel(self.edge_selection)
        self.edges_sheet_table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.edges_sheet_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.edges_sheet_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.graph_view = GraphEditorView()
        self.graph_view.installEventFilter(self)
        self.graph_view.setModel(self.graph_item.nodes(), self.graph_item.edges())
        self.graph_view.setSelectionModel(self.node_selection)

        ### NODEINSPECTOR
        self.node_inspector = InspectorView()
        self.node_inspector.setNodesModel(self.graph_item.nodes())
        self.node_inspector.setNodeSelectionModel(self.node_selection)

        ### PREVIEW WIDGET
        self.preview = PreviewView()
        self.preview.setNodesModel(self.graph_item.nodes())
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
        compile_node_action.triggered.connect(lambda: self.graph_item.nodes().compileNode(self.node_selection.currentIndex().row()))
        evaluate_node_action = QAction("evaluate selected node", self)
        evaluate_node_action.triggered.connect(lambda: self.graph_item.evaluateNode(self.node_selection.currentIndex()))

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
            return qf.widget(qf.hboxlayout([
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
            self.graph_item.load(filepath)
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
        self.graph_item.nodes().insertNodeItem(0, node_item)

        #
        node_index = self.graph_item.nodes().index(self.graph_item.nodes().rowCount()-1, 0)
        node_graphics_item = self.graph_view.nodeWidget(node_index)
        if node_graphics_item := self.graph_view.nodeWidget(node_index):
            node_graphics_item.setPos(position)

    @Slot()
    def delete_selected_nodes(self):
        indexes:list[QModelIndex] = self.node_selection.selectedRows(column=0)
        for index in sorted(indexes, key=lambda idx:idx.row(), reverse=True):
            self.graph_item.nodes().removeRows(index.row(), 1)

    @Slot()
    def delete_selected_edges(self):
        indexes:list[QModelIndex] = self.edge_selection.selectedRows(column=0)
        for index in sorted(indexes, key=lambda idx:idx.row(), reverse=True):
            self.graph_item.edges().removeRows(index.row(), 1)


if __name__ == "__main__":
    app = QApplication()
    window = Window()
    window.show()
    from pathlib import Path
    print("working directory:", Path.cwd())
    window.openFile("tests/website_builder.yaml")
    app.exec()

