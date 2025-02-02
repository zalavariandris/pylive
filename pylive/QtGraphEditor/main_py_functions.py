
from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


# from pylive.QtGraphEditor.definitions_model import DefinitionsModel
from pylive.components.tile_widget import TileWidget
from pylive.components.qt_options_dialog import QOptionDialog


### DATA ###



# from pylive.QtGraphEditor.py_functions_model import PyFunctionsModel
from pylive.QtGraphEditor.fields_model import FieldsModel, FieldItem
from pylive.QtGraphEditor.nodes_model import NodesModel, NodeItem, UniqueFunctionItem
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
        # definition_editor.setSizeAdjustPolicy(QScrollArea.SizeAdjustPolicy.AdjustToContents)
        # definition_editor.setMaximumSize(QSize(256,256))
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

        def show_node_inspector():
            current_node_index = self.node_selection.currentIndex()
            if self.node_selection.hasSelection() and current_node_index.isValid():
                self.node_inspector.show()
                node_item = self.nodes.nodeItemFromIndex(current_node_index)
                assert node_item
                inspector_header_tile.setHeading(f"{node_item.label}")
                # inspector_header_tile.setSubHeading(f"{node_item.definition.data(Qt.ItemDataRole.DisplayRole)}")
                property_editor.setModel(node_item.fields)

                if source:= node_item.source:
                    node_function_source_editor.setPlainText(source)
                else:
                    node_function_source_editor.setPlainText("")
            else:
                self.node_inspector.hide()
                property_editor.setModel(None)

        self.node_selection.currentChanged.connect(show_node_inspector)
        self.node_selection.selectionChanged.connect(show_node_inspector)

        ### PREVIEW WIDGET
        self.preview = QWidget()
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(QLabel("Preview Area"), alignment=Qt.AlignmentFlag.AlignCenter)
        self.preview.setLayout(preview_layout)

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

    def eventFilter(self, watched, event):
        if watched == self.graph_view:
            if event.type() == QEvent.Type.MouseButtonDblClick:
                self.create_new_node()
                return True

        return super().eventFilter(watched, event)

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

        def parse_python_function(code:str)->tuple[str, Callable]:
            import inspect
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

            self.nodes.addNodeItem(
                UniqueFunctionItem(
                    kind="UniqueFunction",
                    label=node['label'],
                    source= node['source']
                )
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
            'definitions': self.definitions,
        })

    @Slot()
    def saveFile(self):
        ...

    @Slot()
    def create_new_node(self):
        dialog = QDialog()
        dialog.setWindowTitle("Create Node")
        dialog.setModal(True)
        layout = QVBoxLayout()

        ## popup definition selector
        dialog = QOptionDialog(self.definitions)
        dialog.setAllowEmptySelection(True)
        result = dialog.exec() # consider using open and the finished signal
        print(result)
        if result == QDialog.DialogCode.Accepted:
            selected_definition_index = dialog.selectedOption()
            if selected_definition_index.isValid():
                definition_name = selected_definition_index.data(Qt.ItemDataRole.DisplayRole)
                all_node_names = [self.nodes.nodeItem(row).name for row in range(self.nodes.rowCount())]
                print(selected_definition_index)
                node_item = NodeItem(
                    name = make_unique_name(f"{definition_name}1", all_node_names), 
                    definition=QPersistentModelIndex(selected_definition_index), 
                    fields=FieldsModel(), 
                    dirty=True
                )
                self.nodes.addNodeItem(node_item)
            else:
                from textwrap import dedent

                new_definition_name = dialog.filterText()
                assert new_definition_name not in [self.definitions.index(row, 0).data(Qt.ItemDataRole.DisplayRole) for row in range(self.definitions.rowCount())]
                source  = dedent(f"""\
                def {new_definition_name}():
                  ...
                """)
                definition_item = DefinitionItem(new_definition_name, source, None)
                row = self.definitions.rowCount()
                self.definitions.insertDefinitionItem(row, definition_item)
                new_definition_index = self.definitions.index(row, 0)
                assert new_definition_index.isValid()

                all_node_names = [self.nodes.nodeItem(row).name for row in range(self.nodes.rowCount())] 
                node_item = NodeItem(
                    make_unique_name(f"{new_definition_name}1", all_node_names), 
                    QPersistentModelIndex(new_definition_index), 
                    FieldsModel(), 
                    dirty=True
                )
                self.nodes.addNodeItem(node_item)
                print("create new definition", dialog.filterText())


        """Static method to open dialog and return selected option."""
        # options_model = QStringListModel([f"{item}" for item in options])
        # dialog = QOptionDialog(options_model, parent=parent)
        # result = dialog.exec()
        # if result == QDialog.DialogCode.Accepted:
        #     indexes = dialog._listview.selectedIndexes()
        #     return indexes[0].data()
        # else:
        #     return None

        # ###
        # if self.definitions.rowCount()==0:
        #     QMessageBox.warning(self, "No definions!", "Please create function definitions!")
        #     return

        # from itertools import chain
        # # node_name, accepted =  QOptionDialog.getItem(self , "Title", "label", ['print', "write"], 0, editable=True)
        # definitions = dict()
        # for row in range(self.definitions.rowCount()):
        #     definition_index = self.definitions.index(row, 0)
        #     name = definition_index.data(Qt.ItemDataRole.DisplayRole)
        #     func = definition_index.data(self.DefinitionFunctionRole)
        #     definitions[name]  = definition_index
       
        # definition_key, accepted =  QOptionDialog.getItem(self , "Title", "label", [_ for _ in definitions.keys()] , 0)
        # if definition_key and accepted:
        #     from pylive.utils.unique import make_unique_name
        #     node_names = [self.nodes.data(self.nodes.index(row, 0), Qt.ItemDataRole.DisplayRole) for row in  range(self.nodes.rowCount())]
        #     node_key = make_unique_name(f"{definition_key}1", node_names)
        #     item = QStandardItem()
        #     item.setData(f"{node_key}", Qt.ItemDataRole.DisplayRole)
        #     item.setData(definitions[definition_key], self.NodeDefinitionRole)
        #     self.nodes.insertRow(self.nodes.rowCount(), item)

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

