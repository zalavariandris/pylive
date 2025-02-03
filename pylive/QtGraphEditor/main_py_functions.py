
from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from networkx import reverse


# from pylive.QtGraphEditor.definitions_model import DefinitionsModel
from pylive.components.tile_widget import TileWidget
from pylive.components.qt_options_dialog import QOptionDialog


### DATA ###



# from pylive.QtGraphEditor.py_functions_model import PyFunctionsModel
from pylive.QtGraphEditor.fields_model import FieldsModel, FieldItem
from pylive.QtGraphEditor.nodes_model import NodesModel, UniqueFunctionItem
from pylive.QtGraphEditor.edges_model import EdgesModel, EdgeItem

from pylive.utils.unique import make_unique_id, make_unique_name
from pylive.QtGraphEditor.qt_graph_editor_scene import QGraphEditorScene
from pylive.QtScriptEditor.script_edit import ScriptEdit


class Window(QWidget):
    # DefinitionFunctionRole = Qt.ItemDataRole.UserRole
    # DefinitionErrorRole = Qt.ItemDataRole.UserRole+1
    # NodeFunctionRole = Qt.ItemDataRole.UserRole+2
    # NodeErrorRole = Qt.ItemDataRole.UserRole+3
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        ### document state
        self._is_modified = False
        self._filepath = "None"

        ### MODEL
        # self.local_definitions = PyFunctionsModel()
        self.nodes = NodesModel()
        self.edges = EdgesModel(nodes=self.nodes)
        self.node_selection = QItemSelectionModel(self.nodes)
        
        # configure model
        self.node_selection = QItemSelectionModel(self.nodes)

        ### Widgets
        self.definitions_table_view = QTableView()
        self.definitions_table_view.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        # self.definitions_table_view.setItemDelegate(DefinitionsEditorDelegate())
        # self.definitions_table_view.setModel(self.local_definitions)
        self.definitions_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.nodes_sheet_table_view = QTableView()
        self.nodes_sheet_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.nodes_sheet_table_view.setModel(self.nodes)
        self.nodes_sheet_table_view.setSelectionModel(self.node_selection)
        self.nodes_sheet_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.edges_sheet_table_view = QTableView(self)
        self.edges_sheet_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.edges_sheet_table_view.setModel(self.edges)
        self.edges_sheet_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.graph_view = QGraphicsView()
        self.graph_view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.graph_view.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
        self.graph_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.graph_view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.graph_view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.graph_view.installEventFilter(self)
        graph_scene = QGraphEditorScene()
        graph_scene.setModel(self.nodes, self.edges)
        graph_scene.setSceneRect(QRectF(-400, -400, 800, 800))
        graph_scene.setSelectionModel(self.node_selection)
        self.graph_view.setScene(graph_scene)

        ### NODEINSPECTOR
        self.node_inspector = QFrame()
        self.node_inspector.setFrameShape(QFrame.Shape.StyledPanel)  # Styled panel for the frame
        self.node_inspector.setFrameShadow(QFrame.Shadow.Raised)
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
        self.node_inspector.setLayout(inspector_layout)

        def create_field():
            current_node_index = self.node_selection.currentIndex()
            if self.node_selection.hasSelection() and current_node_index.isValid():
                node_item = self.nodes.data(current_node_index.siblingAtColumn(0), Qt.ItemDataRole.UserRole)
                new_field = FieldItem(make_unique_id(), "value")
                node_item.fields.insertFieldItem(node_item.fields.rowCount(), new_field)
        create_button.clicked.connect(lambda: create_field())

        def delete_fields():
            current_node_index = self.node_selection.currentIndex()
            if self.node_selection.hasSelection() and current_node_index.isValid():
                node_item = self.nodes.data(current_node_index.siblingAtColumn(0), Qt.ItemDataRole.UserRole)
                selected_rows = list(set(_.row() for _ in property_editor.selectedIndexes()))
                for row in sorted(selected_rows, reverse=True):
                    node_item.fields.removeRows(row, 1)
        delete_button.clicked.connect(lambda: delete_fields())

        def update_source():
            current_node_index = self.node_selection.currentIndex()
            if self.node_selection.hasSelection() and current_node_index.isValid():
                new_source = node_function_source_editor.toPlainText()
                self.nodes.setUniqueFunctionSource(current_node_index, new_source)
                print("set source")

        
        node_function_source_editor.textChanged.connect(update_source)
        def show_node_inspector():
            current_node_index = self.node_selection.currentIndex()
            if self.node_selection.hasSelection() and current_node_index.isValid():
                self.node_inspector.show()

                
                inspector_header_tile.setHeading(self.nodes.data(current_node_index, Qt.ItemDataRole.DisplayRole))
                # inspector_header_tile.setSubHeading(f"{node_item.definition.data(Qt.ItemDataRole.DisplayRole)}")
                node_item = self.nodes.nodeItemFromIndex(current_node_index)
                assert node_item
                property_editor.setModel(node_item.fields())

                if source:= node_item.source():
                    node_function_source_editor.setPlainText(source)
                else:
                    node_function_source_editor.setPlainText("")
                self.nodes.dataChanged.connect(print)

            else:
                self.node_inspector.hide()
                property_editor.setModel(None)
                self.nodes.dataChanged.connect(print)

        self.node_selection.currentChanged.connect(show_node_inspector)
        self.node_selection.selectionChanged.connect(show_node_inspector)


        self.node_selection.currentChanged.connect(self.evaluate)
        self.node_selection.selectionChanged.connect(self.evaluate)

        self.nodes.dataChanged.connect(self.evaluate)

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
        add_node_action.triggered.connect(self.create_new_node)
        delete_node_action = QAction("delete node", self)
        delete_node_action.triggered.connect(self.delete_selected_nodes)
        connect_selected_nodes_action = QAction("connect selected nodes", self)
        connect_selected_nodes_action.triggered.connect(self.connect_selected_nodes)
        remove_edge_action = QAction("remove edge", self)
        remove_edge_action.triggered.connect(self.delete_selected_edges)

        self.addActions([
            save_action,
            open_action,
            add_node_action,
            delete_node_action,
            connect_selected_nodes_action,
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

        main_layout = qf.vboxlayout([
            qf.splitter(Qt.Orientation.Horizontal, [
                qf.tabwidget({
                    'graph': create_graph_panel(),
                    'sheets': qf.widget(qf.hboxlayout([
                        qf.vboxlayout([QLabel("nodes"), self.nodes_sheet_table_view]),
                        qf.vboxlayout([QLabel("edges"), self.edges_sheet_table_view]),
                        # qf.vboxlayout([QLabel("edges"), self.fields_sheet_table_view])
                    ])),
                    'definitions': qf.widget(qf.hboxlayout([
                        self.definitions_table_view,
                        self.definition_script_editor,
                    ], stretch=(1,1)))
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
            return False

        ### prompt file name
        if not filepath:
            filepath, _ = QFileDialog.getOpenFileName(self, 
                "Open", self.fileFilter(), self.fileSelectFilter())
            if filepath is None: # cancelled
                return False

        # read and parse existing text file
        from pathlib import Path
        text = Path(filepath).read_text()
        return self.deserialize(text)

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


    def deserialize(self, text:str)->bool:
        import yaml
        data = yaml.load(text, Loader=yaml.SafeLoader)

        

        # Clear and load data into the new model!
        ### create definition items
        # _definition_row_by_name:dict[str, int] = dict() # keep definition name as references for the node relations #TODO: multiple function definitions with the same name will shadow preceeding functions with the same name
        # self.local_definitions.blockSignals(True)
        # self.local_definitions.removeRows(0, self.local_definitions.rowCount())
        # import inspect
        # for row, code in enumerate(data['definitions']):
        #     ### get python function from string
        #     # the string should contain a single function definition
        #     try:
        #         name, func = parse_python_function(code)
        #         self.local_definitions.insertFunction(self.local_definitions.rowCount(), func)
        #         _definition_row_by_name[name] = row
        #     except Exception as err:
        #         self.statusbar.showMessage(f"error: {err}")
        # self.local_definitions.blockSignals(False)
        # self.local_definitions.modelReset.emit()

        ### create node items
        _nodes_with_id = dict() # keep node name as references for the edge relations
        self.nodes.blockSignals(True)
        for row, node in enumerate(data['nodes']):
            if node['kind']!='UniqueFunction':
                raise NotImplementedError("for now only 'UniqueFunction's are supported!")


            fields_model = FieldsModel()
            if fields:=node.get("fields", None):
                for row, (name, value) in enumerate(fields.items()):
                    field_item = FieldItem(name, value, editable=True)
                    fields_model.insertFieldItem(row, field_item)

            self.nodes.addNodeItem(
                UniqueFunctionItem(node['source'], fields_model)
            )
            if node['label'].startswith("#"):
                _nodes_with_id[node['label']] = row

        self.nodes.blockSignals(False)
        self.nodes.modelReset.emit()

        self.edges.blockSignals(True)
        for row, edge in enumerate(data['edges']):
            source_node_id = edge['source']
            target_node_id = edge['target']
            source_row = _nodes_with_id[source_node_id]
            target_row = _nodes_with_id[target_node_id]
            source_index = self.nodes.index(source_row, 0)
            target_index = self.nodes.index(target_row, 0)
            edge = EdgeItem(QPersistentModelIndex(source_index), QPersistentModelIndex(target_index), edge['inlet'])
            self.edges.addEdgeItem(edge)

        self.edges.blockSignals(False)
        self.edges.modelReset.emit()

        return True

    
    def serialize(self)->str:
        import yaml
        return yaml.dump({
            'nodes': [],
            'edges': []
        })

    @Slot()
    def saveFile(self):
        ...

    def _evaluate_node(self, node_index:QModelIndex|QPersistentModelIndex):
        from pylive.utils.evaluate_python import parse_python_function, call_function_with_stored_args
        node_item = self.nodes.nodeItem(node_index.row())
        assert node_item.kind == "UniqueFunction"
        node_item = cast(UniqueFunctionItem, node_item)
        """recursively evaluate nodes, from top to bottom"""
        ### load arguments achestors
        kwargs = dict()
        inputs = [_ for _ in self.edges.inputs(node_index)]
        print("in edges:", inputs)
        for source_node_index, inlet in self.edges.inputs(node_index):
            print(f"EVALUATE SOURCE {inlet}: {source_node_index}")
            kwargs[inlet] = self._evaluate_node(source_node_index)
            

        ### load arguments from fields
        for row in range(node_item.fields.rowCount()):
            field_item = node_item.fields.fieldItem(row)
            if field_item.name in kwargs:
                continue # skip connected fields
            
            kwargs[field_item.name] = field_item.value

        print("_evaluate", node_index, kwargs)
        # evaluate functions with 
        func_name, func = parse_python_function(node_item.source)
        result = call_function_with_stored_args(func, kwargs)
        return result

    @Slot()
    def evaluate(self)->bool:
        current_node_index = self.node_selection.currentIndex()
        if not current_node_index.isValid():
            return True

        try:
            result = self._evaluate_node(current_node_index)
            self.preview.setText(str(result))
            self.preview.setStyleSheet("")
        except SyntaxError as err:
            self.preview.setText(str(err))
            self.preview.setStyleSheet("color: red")
            return False
        except Exception as err:
            self.preview.setText(str(err))
            self.preview.setStyleSheet("color: red")
            return False

        return True

    @Slot()
    def create_new_node(self, position:QPointF=QPointF()):
        dialog = QDialog()
        dialog.setWindowTitle("Create Node")
        dialog.setModal(True)
        layout = QVBoxLayout()

        ## popup definition selector
        self.nodes.addNodeItem(UniqueFunctionItem(
            source="""def func():\n  ...""",
        ))

        #
        node_index = self.nodes.index(self.nodes.rowCount()-1, 0)
        scene = cast(QGraphEditorScene, self.graph_view.scene())
        node_graphics_item = scene.nodeGraphicsObject(node_index)
        if node_graphics_item := scene.nodeGraphicsObject(node_index):
            node_graphics_item.setPos(position)

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

    


if __name__ == "__main__":
    app = QApplication()
    window = Window()
    window.show()
    from pathlib import Path
    print(Path.cwd())
    window.openFile("tests/website_builder.yaml")
    app.exec()

