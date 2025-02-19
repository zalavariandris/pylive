
from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from shiboken6 import getAllValidWrappers

# from pylive.QtGraphEditor.definitions_model import DefinitionsModel
from pylive.VisualCode_v4.graph_editor.graph_data_roles import GraphDataRole
from pylive.qt_components.tile_widget import TileWidget
from pylive.qt_components.qt_options_dialog import QOptionDialog


### DATA ###

# from pylive.QtGraphEditor.py_functions_model import PyFunctionsModel
from pylive.VisualCode_v4.py_data_model import PyDataModel, PyNodeItem
from pylive.VisualCode_v4.py_proxy_model import PyNodeProxyModel, PyLinkProxyModel
from pylive.VisualCode_v4.graph_editor.standard_edges_model import StandardEdgeItem, StandardEdgesModel


from pylive.VisualCode_v4.graph_editor.graph_editor_view import GraphEditorView
from pylive.QtScriptEditor.script_edit import ScriptEdit
from pylive.utils import group_consecutive_numbers
from pylive.utils.qt import logModelSignals
import pylive.utils.qtfactory as qf

from bidict import bidict

def log_call(fn, *args, **kwargs):
    print(f"{fn.__name__} was called")
    return fn(*args, **kwargs)

import pylive.utils.qtfactory as qf


class PyInspectorView(QFrame):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._model:PyDataModel|None=None
        self._selection:QItemSelectionModel|None=None
        self.setupUI()

    def setupUI(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)  # Styled panel for the frame
        self.setFrameShadow(QFrame.Shadow.Raised)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("name...")

        self.parameter_editor = QTableWidget()
        self.parameter_editor.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.parameter_editor.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.parameter_editor.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.parameter_editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.parameter_editor.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)

        self.source_editor = ScriptEdit()
        self.source_editor.setPlaceholderText("source...")

        main_layout = qf.vboxlayout([
            QLabel("<h2>Name</h2>"),
            self.name_edit,
            QLabel("<h2>Parameters</h2>"),
            self.parameter_editor,
            QLabel("<h2>Source</h2>"),
            self.source_editor
        ])

        self.setLayout(main_layout)

        # map editors to data
        def setNodeName():
            assert self._model
            if not self._current_node:
                return
            ...
            # self._model.setNodeName(self._current_node, self.source_editor.toPlainText())

        self.name_edit.textChanged.connect(setNodeName)

        def setNodeSource():
            assert self._model
            if not self._current_node:
                return
            self._model.setNodeSource(self._current_node, self.source_editor.toPlainText())

        self.source_editor.textChanged.connect(setNodeSource)

    def setModel(self, model: PyDataModel|None):
        if self._model:
            self._model.nameChanged.disconnect(self._on_node_name_changed)
            self._model.sourceChanged.disconnect(self._on_node_source_changed)
            # self._model.fieldsChanged.disconnect(self._onNodeChange)

        if model:
            model.nameChanged.connect(self._on_node_name_changed)
            model.sourceChanged.connect(self._on_node_source_changed)
            # model.fieldsChanged.connect(self._onNodeChange)

        self._model = model

    def _on_node_name_changed(self):
        self.name_edit.setText(self._current_node or '')

    def _on_node_source_changed(self):
        if not self._current_node:
            self.source_editor.setPlainText('')
        self.source_editor.setPlainText(self._model.nodeSource(self._current_node))

    def setCurrent(self, node:str|None):
        self._current_node = node
        self._on_node_name_changed()
        self._on_node_source_changed()
        # self._update_editors()

    def currentRow(self)->int:
        if not self._selection:
            return -1
        return self._selection.currentIndex().row()


    # def update_node_inspector(self):
    #     assert self._selection
    #     assert self._nodes
    #     assert self._edges

    #     current_node_index = self._selection.currentIndex().siblingAtColumn(0)
    #     if current_node_index.isValid():
    #         self.show()
    #         node_item = self._nodes.nodeItemFromIndex(current_node_index)
    #         assert node_item is not None, f"cant be None, got: {node_item}"

    #         # update name editor
    #         name = node_item.name
    #         if name!=self.name_edit.text():
    #             self.name_edit.setText(name)

    #         # update heading
    #         self.inspector_header_tile.setHeading(self._nodes.data(current_node_index, Qt.ItemDataRole.DisplayRole))
    #         self.inspector_header_tile.setSubHeading(f"(inline function)")

    #         # update property editor
    #         inlets = self._nodes.inlets(current_node_index.row())
    #         fields = self._nodes.dataByColumnName(current_node_index.row(), 'fields')
    #         in_edges = self._edges.inEdges(current_node_index.row())

    #         self.property_editor.setVerticalHeaderLabels([_ for _ in inlets])
    #         self.property_editor.setRowCount(len(inlets))
    #         self.property_editor.setColumnCount(1)
    #         self.property_editor.setHorizontalHeaderLabels(["value"])

            
    #         for inlet_row, inlet in enumerate(inlets):
    #             if inlet in [edge_item.inlet for edge_item in in_edges]:
    #                 sources = [f"{self._nodes.data(edge_item.source)}.{edge_item.outlet}" for edge_item in in_edges]
    #                 self.property_editor.setItem(inlet_row, 0, QTableWidgetItem(f"linked to: {",".join(sources)}"))
    #             elif inlet in fields:
    #                 self.property_editor.setItem(inlet_row, 0, QTableWidgetItem(fields[inlet]))
    #             else:
    #                 self.property_editor.setItem(inlet_row, 0, QTableWidgetItem('-no value set-'))

    #         # update code editor
    #         code = node_item.code
    #         if code!= self.node_function_source_editor.toPlainText():
    #             self.node_function_source_editor.setPlainText(code)

    #     else:
    #         self.hide()
    #         self.inspector_header_tile.setHeading("")
    #         self.inspector_header_tile.setSubHeading("")
    #         self.node_function_source_editor.setPlainText("")


class PyPreviewView(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._nodes: PyNodesModel|None=None
        self._selection:QItemSelectionModel|None=None

        self.setupUI()

    def setupUI(self):
        self._status_label = QLabel("Status")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)        
        self._result_label = QLabel("Results")
        self._result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label = QLabel("Errors")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self._status_label)
        main_layout.addWidget(self._result_label)
        main_layout.addWidget(self._error_label)
        self.setLayout(main_layout)

    def setModel(self, model:PyDataModel):
        if self._nodes:
            nodes.dataChanged.disconnect(self._onDataChanged)

        if nodes:
            nodes.dataChanged.connect(self._onDataChanged)

        self._nodes = nodes

    def setCurrent(self, node:str):
        ...

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



class Window(QWidget):

    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        ### document state
        self._is_modified = False
        self._filepath = "None"

        ### MODEL
        self.graph_model = PyDataModel()
        self.link_proxy_model = PyLinkProxyModel(self.graph_model)
        self.node_proxy_model:PyNodeProxyModel = self.link_proxy_model.itemsModel()
        assert self.node_proxy_model
        self.node_selection_model = QItemSelectionModel(self.node_proxy_model)


        self.setupUI()

    def setupUI(self):
        ...
        # self.nodes_model = self.graph_model.nodes()

        # self.edges_model = self.graph_model.edges()
        
        
        # self.edge_selection = QItemSelectionModel(self.edges_model)

        # logModelSignals(self.graph_model._nodes_model)

        # # compile nodes when inserted
        # @self.graph_model.nodesReset.connect
        # def _():
        #     for row in range(self.graph_model.nodeCount()):
        #         self.graph_model.compileNode(row) 
        
        # @self.graph_model.nodesInserted.connect
        # def _(parent, first, last): 
        #     for row in range(first, last+1):
        #         self.graph_model.compileNode(row) 

        # # on source change, compile node
        # @self.graph_model.nodeChanged.connect
        # def _(tl:QModelIndex, br:QModelIndex, roles:list=[]):
        #     headers = [self.graph_model._nodes_model.headerData(col, Qt.Orientation.Horizontal) for col in range(self.graph_item._nodes_model.columnCount())]
        #     source_column = headers.index("code")
        #     if source_column in range(tl.column(), br.column()+1):
        #         for row in range(tl.row(), br.row()+1):
        #             self.graph_model.compileNode(row)
        #             self.graph_model.evaluateNode(row)


        # @self.node_selection.currentChanged.connect
        # def _(current:QModelIndex, previous:QModelIndex):
        #     if current.isValid():
        #         self.graph_model.evaluateNode(current.row())
        #     else:
        #         pass
        #     # for row in range(first, last+1):
        #     #     self.graph_model.evaluateNode(row) 
        
        ### SheetsView
        self.nodes_table_view = QTableView()
        self.nodes_table_view.setModel(self.node_proxy_model)
        self.nodes_table_view.setSelectionModel(self.node_selection_model)
        self.links_table_view = QTableView()
        self.links_table_view.setModel(self.link_proxy_model)

        ### GRAPH View
        self.graph_view = GraphEditorView()
        self.graph_view.setModel(self.node_proxy_model, self.link_proxy_model)
        self.graph_view.installEventFilter(self)
        self.graph_view.setSelectionModel(self.node_selection_model)
        # self.graph_view.setSelectionModel(self.node_selection_model)
        # self.graph_view.setSelectionModel(self.selection_model)

        # ### NODEINSPECTOR
        self.inspector_view = PyInspectorView()
        self.inspector_view.setModel(self.graph_model)
        self.node_selection_model.currentChanged.connect(lambda current, prev: 
            self.inspector_view.setCurrent(self.node_proxy_model.mapToSource(current)))
        # self.inspector_view.setModel(self.graph_model)
        # self.inspector_view.setNodeSelectionModel(self.node_selection_model)

        # ### PREVIEW WIDGET
        self.preview = PyPreviewView()
        # self.preview.setModel(self.graph_model)
        # self.preview.setSelectionModel(self.node_selection_model)


        # self.preview.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)

        ### STATUS BAR WIDGET
        self.statusbar = QStatusBar()
        self.statusbar.showMessage("status bar")

        ## MENUBAR

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
        compile_node_action.triggered.connect(lambda: self.graph_model.compileNode(self.selection_model.currentIndex().row()))
        evaluate_node_action = QAction("evaluate selected node", self)
        evaluate_node_action.triggered.connect(lambda: self.graph_model.evaluateNode(self.selection_model.currentIndex().row()))

        self.addActions([
            save_action,
            open_action,
            add_node_action,
            delete_node_action,
            remove_edge_action,
            compile_node_action,
            evaluate_node_action
        ])

        menubar = QMenuBar(parent=self)
        menubar.addActions(self.actions())

        ### Layout
        def create_graph_panel():
            panel = QWidget()
            grid_layout = QGridLayout()
            panel.setLayout(grid_layout)

            grid_layout.addWidget(self.graph_view, 0, 0)
            grid_layout.addWidget(self.inspector_view, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
            # self.node_inspector.hide()
            panel.setLayout(grid_layout)
            return panel

        main_layout = qf.vboxlayout([
            qf.splitter(Qt.Orientation.Horizontal, [
                # qf.tabwidget({
                #     'graph': create_graph_panel(),
                #     'sheets': create_graph_sheets()
                # }),
                self.nodes_table_view,
                self.links_table_view,
                self.graph_view,
                self.inspector_view,
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
    def create_new_node(self, scenepos:QPointF=QPointF()):
        ## popup definition selector
        from pylive.utils.unique import make_unique_name
        existing_names = list()
        print(existing_names)
        func_name = make_unique_name("func1", self.graph_model.nodes())
        self.graph_model.addNode(func_name, PyNodeItem())

        ### position node widget
        node_index = self.node_proxy_model.mapFromSource(func_name)
        node_graphics_item = self.graph_view.nodeWidget(node_index)
        if node_graphics_item := self.graph_view.nodeWidget(node_index):
            node_graphics_item.setPos(scenepos-node_graphics_item.boundingRect().center())

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

    def eventFilter(self, watched, event):
        if watched == self.graph_view:
            if event.type() == QEvent.Type.MouseButtonDblClick:
                self.create_new_node(self.graph_view.mapToScene(event.position().toPoint()))


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









# class PyGraphView(QWidget):
#     def __init__(self, parent:QWidget|None=None):
#         super().__init__(parent=parent)
#         self._model: PyDataModel|None=None
#         self._selection:PyNodeSelectionModel|None=None

#         self._item_by_node:bidict[str, QModelIndex] = bidict()

#         self.setupUI()

#     def setupUI(self):
#         self.graph_view = GraphEditorView()
#         self._item_model = QStandardItemModel()
#         self._item_selection_model = QItemSelectionModel(self._item_model)
#         self._edges_model = StandardEdgesModel(self._item_model)
#         self.graph_view.setSelectionModel(self._item_selection_model)
#         self.graph_view.setModel(self._edges_model)

#         self.graph_view.installEventFilter(self)
#         main_layout = QVBoxLayout()
#         main_layout.addWidget(self.graph_view)
#         self.setLayout(main_layout)

#         self._connections = []

#     def setModel(self, model:PyDataModel|None):
#         if self._model:
#             ...
#         if model:
#             model.modelReset.connect(self.resetUI)
            

#         self._model = model
#         self.resetUI()

#     def resetUI(self):
#         assert self._model

#         self._edges_model.blockSignals(True)
#         self._item_model.blockSignals(True)
#         for row, name in enumerate(self._model.nodes()):
#             node_item = QStandardItem()
#             node_item.setText(name)
#             node_item.setData(self._model.nodeFields(name), GraphDataRole.NodeInletsRole)
#             node_item.setData(['out'], GraphDataRole.NodeOutletsRole)
#             self._item_model.insertRow(row, [
#                 QStandardItem(name)
#             ])
#             node_index = self._item_model.index(row, 0)
#             self._item_by_node[name] = node_index

#         for i, (source, target, inlet) in enumerate(self._model.links()):
#             source_index = QPersistentModelIndex(self._item_by_node[source])
#             target_index = QPersistentModelIndex(self._item_by_node[target])
#             edge_item = StandardEdgeItem(
#                 source=source_index,
#                 target=target_index,
#                 outlet="out",
#                 inlet=inlet
#             )
#             self._edges_model.appendEdgeItem(edge_item)

#         self._item_model.blockSignals(False)
#         self._edges_model.blockSignals(False)
#         self._item_model.modelReset.emit()
#         self._edges_model.modelReset.emit()

#         self.graph_view.centerNodes()


# class PySheetsView(QWidget):
#     def __init__(self, parent:QWidget|None=None):
#         super().__init__(parent=parent)
#         self._model:PyDataModel|None=None
#         self._selection:PyNodeSelectionModel|None=None

#         self.setupUI()

#     def setupUI(self):
#         self.nodes_sheet = QTableWidget()
#         self.nodes_sheet.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
#         # self.nodes_sheet_table_view.setSelectionModel(self.node_selection)
#         self.nodes_sheet.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
#         self.nodes_sheet.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
#         self.nodes_sheet.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
#         self.edges_sheet = QTableWidget()
#         self.edges_sheet.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        

#         self.edges_sheet.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
#         self.edges_sheet.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
#         self.edges_sheet.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

#         self.setLayout(qf.vboxlayout([
#             qf.vboxlayout([QLabel("nodes"), self.nodes_sheet]),
#             qf.vboxlayout([QLabel("edges"), self.edges_sheet]),
#         ]))

#     def setModel(self, model:PyDataModel|None):
#         signals = [
#             'modelReset',

#             'nodesAdded', 
#             'nodesRemoved', 

#             'nodesLinked',
#             'nodesUnlinked',

#             'nameChanged',
#             'sourceChanged',
#             'fieldsChanged',
#             'statusChanged',
#             'errorChanged',
#             'resultChanged'
#         ]
#         if self._model:
#             for signal in signals:
#                 getattr(self._model, signal).disconnect(self.resetUI)

#         if model:
#             for signal in signals:
#                 getattr(model, signal).connect(self.resetUI)

#         self._model = model


#     def resetUI(self):
#         self.nodes_sheet.clear()
#         if not self._model:
#             return

#         # reset nodes_sheet
#         self.nodes_sheet.setRowCount(self._model.nodeCount())
#         self.nodes_sheet.setColumnCount(6)
#         self.nodes_sheet.setHorizontalHeaderLabels([
#             "name", 'source', "fields", "status", "error", "result"
#         ])

#         for i, name in enumerate(self._model.nodes()):
#             source = self._model.nodeSource(name)
#             fields = self._model.nodeFields(name)
#             status = self._model.nodeStatus(name)
#             error = self._model.nodeError(name)
#             result = self._model.nodeResult(name)
            
#             self.nodes_sheet.setItem(i, 0, QTableWidgetItem(name))
#             self.nodes_sheet.setItem(i, 1, QTableWidgetItem(source))
#             self.nodes_sheet.setItem(i, 2, QTableWidgetItem(",".join(fields)))
#             self.nodes_sheet.setItem(i, 3, QTableWidgetItem(status))
#             self.nodes_sheet.setItem(i, 4, QTableWidgetItem(f"{error}"))
#             self.nodes_sheet.setItem(i, 5, QTableWidgetItem(f"{result}"))

#         # reset edges
#         self.edges_sheet.setRowCount(self._model.linkCount())
#         self.edges_sheet.setColumnCount(3)
#         self.edges_sheet.setHorizontalHeaderLabels([
#             "source", 'target', "inlet"
#         ])

#         for i, (source, target, inlet) in enumerate(self._model.links()):
#             self.edges_sheet.setItem(i, 0, QTableWidgetItem(source))
#             self.edges_sheet.setItem(i, 1, QTableWidgetItem(target))
#             self.edges_sheet.setItem(i, 2, QTableWidgetItem(inlet))
            