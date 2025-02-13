
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
from py_nodes_model import PyNodesModel, UniqueFunctionItem
from graph_editor.standard_edges_model import StandardEdgesModel, StandardEdgeItem

from py_graph_item import PyGraphItem

from pylive.utils.unique import make_unique_id, make_unique_name
from pylive.VisualCode_v4.graph_editor.graph_editor_view import GraphEditorView
from pylive.QtScriptEditor.script_edit import ScriptEdit

def log_call(fn, *args, **kwargs):
    print(f"{fn.__name__} was called")
    return fn(*args, **kwargs)

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
        
        ### Widgets
        self.nodes_sheet_table_view = QTableView()
        self.nodes_sheet_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.nodes_sheet_table_view.setModel(self.graph_item.nodes())
        self.nodes_sheet_table_view.setSelectionModel(self.node_selection)
        self.nodes_sheet_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.nodes_sheet_table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        self.edges_sheet_table_view = QTableView(self)
        self.edges_sheet_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.edges_sheet_table_view.setModel(self.graph_item.edges())
        self.edges_sheet_table_view.setSelectionModel(self.edge_selection)
        self.edges_sheet_table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.edges_sheet_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.graph_view = GraphEditorView()
        self.graph_view.installEventFilter(self)
        self.graph_view.setModel(self.graph_item.nodes(), self.graph_item.edges())
        self.graph_view.setSelectionModel(self.node_selection)

        ### NODEINSPECTOR

        node_inspector = QFrame()
        node_inspector.setFrameShape(QFrame.Shape.StyledPanel)  # Styled panel for the frame
        node_inspector.setFrameShadow(QFrame.Shadow.Raised)
        inspector_header_tile = TileWidget()
        property_editor = QTableView()
        property_editor.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        property_editor.setModel(None)
        inspector_layout = QVBoxLayout()
        inspector_layout.addWidget(inspector_header_tile)
        inspector_layout.addWidget(property_editor)
        create_button = QPushButton("create")
        delete_button = QPushButton("delete")
        button_layout = QHBoxLayout()
        button_layout.addWidget(create_button)
        button_layout.addWidget(delete_button)
        inspector_layout.addLayout(button_layout)
        help_label = QLabel("Help")
        node_function_source_editor = ScriptEdit()
        inspector_layout.addWidget(node_function_source_editor)
        inspector_layout.addWidget(help_label)
        node_inspector.setLayout(inspector_layout)

        def create_field():
            current_node_index = self.node_selection.currentIndex()
            if self.node_selection.hasSelection() and current_node_index.isValid():
                node_item = self.graph_item.nodes().data(current_node_index.siblingAtColumn(0), Qt.ItemDataRole.UserRole)
                new_field = PyFieldItem(make_unique_id(), "value")
                node_item.fields.insertFieldItem(node_item.fields.rowCount(), new_field)
        create_button.clicked.connect(lambda: create_field())

        def delete_fields():
            current_node_index = self.node_selection.currentIndex()
            if self.node_selection.hasSelection() and current_node_index.isValid():
                node_item = self.graph_item.nodes().data(current_node_index.siblingAtColumn(0), Qt.ItemDataRole.UserRole)
                selected_rows = list(set(_.row() for _ in property_editor.selectedIndexes()))
                for row in sorted(selected_rows, reverse=True):
                    node_item.fields.removeRows(row, 1)
        delete_button.clicked.connect(lambda: delete_fields())

        def update_source():
            current_node_index = self.node_selection.currentIndex()
            if self.node_selection.hasSelection() and current_node_index.isValid():
                new_source = node_function_source_editor.toPlainText()
                self.graph_item.nodes().setUniqueFunctionSource(current_node_index, new_source)
        node_function_source_editor.textChanged.connect(lambda: update_source())

        self.node_inspector = node_inspector

        def update_node_inspector():
            current_node_index = self.node_selection.currentIndex()
            if self.node_selection.hasSelection() and current_node_index.isValid():
                self.node_inspector.show()

                
                inspector_header_tile.setHeading(self.graph_item.nodes().data(current_node_index, Qt.ItemDataRole.DisplayRole))
                # inspector_header_tile.setSubHeading(f"{node_item.definition.data(Qt.ItemDataRole.DisplayRole)}")
                node_item = self.graph_item.nodes().nodeItemFromIndex(current_node_index)
                assert node_item is not None, f"cant be None, got: {node_item}"
                property_editor.setModel(node_item.fields())

                if source:= node_item.source():
                    node_function_source_editor.setPlainText(source)
                else:
                    node_function_source_editor.setPlainText("")
                # self.nodes.dataChanged.connect(print)

            else:
                self.node_inspector.hide()
                property_editor.setModel(None)
                # self.nodes.dataChanged.connect(print)

        self.node_selection.currentChanged.connect(lambda: update_node_inspector())
        self.node_selection.selectionChanged.connect(lambda: update_node_inspector())
        self.node_selection.currentChanged.connect(lambda: self.evaluate())
        self.node_selection.selectionChanged.connect(lambda: self.evaluate())
        self.graph_item.nodes().dataChanged.connect(lambda: self.evaluate())

        self.graph_item.edges().rowsInserted.connect(lambda: self.evaluate())
        self.graph_item.edges().rowsRemoved.connect(lambda: self.evaluate())
        self.graph_item.edges().dataChanged.connect(lambda: self.evaluate())

        ### PREVIEW WIDGET
        self.preview = QLabel("Preview Label")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

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

        self.addActions([
            save_action,
            open_action,
            add_node_action,
            delete_node_action,
            remove_edge_action
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
            self.node_inspector.hide()
            panel.setLayout(grid_layout)
            return panel

        def create_graph_sheets():
            return qf.widget(qf.hboxlayout([
                qf.vboxlayout([QLabel("nodes"), self.nodes_sheet_table_view]),
                qf.vboxlayout([QLabel("edges"), self.edges_sheet_table_view]),
            ]))

        main_layout = qf.vboxlayout([
            qf.splitter(Qt.Orientation.Horizontal, [
                qf.tabwidget({
                    'graph': create_graph_panel(),
                    'sheets': create_graph_sheets()
                }),
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

    def evaluate(self)->bool:
        current_node_index = self.node_selection.currentIndex()

        if not current_node_index.isValid():
            self.preview.setText(f"-no selection ")
            self.preview.setStyleSheet("")
            return True

        import textwrap
        try:
            result = self.graph_item.evaluateNode(current_node_index)
            self.preview.setText(f"{result}")
            self.preview.setStyleSheet("")
        except SyntaxError as err:
            import traceback
            error_message = traceback.format_exc()
            self.preview.setText(f"<h1>{err}</h1><p style='white-space: pre;'>{error_message}</p>")
            self.preview.setStyleSheet("color: red")
            print("evaluate Exception:", error_message)
            return False
        except Exception as err:
            import traceback
            error_message = traceback.format_exc()
            self.preview.setText(f"<h1>{err}</h1><p style='white-space: pre;'>{error_message}</p>")
            self.preview.setStyleSheet("color: red")
            print("evaluate Exception:", error_message)
            return False

        return True

    @Slot()
    def create_new_node(self, position:QPointF=QPointF()):
        dialog = QDialog()
        dialog.setWindowTitle("Create Node")
        dialog.setModal(True)
        layout = QVBoxLayout()

        ## popup definition selector
        self.graph_item.nodes().addNodeItem(UniqueFunctionItem(
            source="""def func():\n  ...""",
        ))

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

