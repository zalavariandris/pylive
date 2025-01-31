from collections import defaultdict
from typing import *
from typing_extensions import deprecated
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from networkx.classes import graphviews

from pylive.QtGraphEditor.definitions_model import DefinitionItem, DefinitionsModel
from pylive.QtGraphEditor.tile_widget import TileWidget
from pylive.qt_options_dialog import QOptionDialog
from pylive.utils import group_consecutive_numbers
from pylive.utils.qt import modelReset, signalsBlocked


### DATA ###


from dataclasses import dataclass

from fields_model import FieldsModel, FieldItem
from nodes_model import NodesModel, NodeItem
from edges_model import EdgesModel, EdgeItem


from pylive.utils.qtfactory import gridlayout
from pylive.utils.unique import make_unique_id
from qt_graph_editor_scene import QGraphEditorScene
from pylive.QtScriptEditor.script_edit import ScriptEdit


class DefinitionsEditorDelegate(QStyledItemDelegate):
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex) -> QWidget:
        editor = super().createEditor(parent, option, index)
        print("editor created", editor)
        text_edit = QTextEdit(parent)
        text_edit.setPlainText(index.data(Qt.ItemDataRole.EditRole))
        return text_edit

    def setEditorData(self, editor: QWidget, index: QModelIndex | QPersistentModelIndex) -> None:
        editor = cast(QTextEdit, editor)
        model = cast(QStandardItemModel, index.model())
        editor.setPlainText(index.data(Qt.ItemDataRole.EditRole))

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex | QPersistentModelIndex) -> None:
        editor = cast(QTextEdit, editor)
        model = cast(QStandardItemModel, index.model())
        model.setData(index, editor.toPlainText(), Qt.ItemDataRole.EditRole)


class ListTileDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter: QPainter, option:QStyleOption, index: QModelIndex):
        painter.save()

        # Get data from the model
        heading = index.data(Qt.ItemDataRole.DisplayRole)  # DisplayRole for the heading
        subheading = index.data(Qt.ItemDataRole.ToolTipRole)  # ToolTipRole for the subheading

        # Define the rectangle areas
        rect:QRect = option.rect
        heading_rect = rect.adjusted(10, 5, -10, -rect.height() // 2)
        subheading_rect = rect.adjusted(10, rect.height() // 2, -10, -5)

        # Access the palette for standard colors
        palette:QPalette = option.palette

        # Background color for selected items
        if option.state & QStyle.State_Selected:
            painter.fillRect(rect, palette.button())
            painter.fillRect(QRect(rect.left(), rect.top(), 1, rect.height()), palette.highlight())

        # Heading text color
        heading_color = palette.highlightedText() if option.state & QStyle.State_Selected else palette.text()

        # Subheading text color
        subheading_color = palette.highlightedText() if option.state & QStyle.State_Selected else palette.mid()

        # Draw the heading (uses default font)
        painter.setPen(heading_color.color())
        painter.drawText(heading_rect, Qt.AlignLeft | Qt.AlignVCenter, heading or "")

        # Draw the subheading (uses default font)
        painter.setPen(subheading_color.color())
        painter.drawText(subheading_rect, Qt.AlignLeft | Qt.AlignVCenter, subheading or "")

        painter.restore()

    def sizeHint(self, option, index):
        # Set the height of the item to accommodate both heading and subheading
        return QSize(option.rect.width(), 50)


from PySide6.QtCore import Qt, QSortFilterProxyModel, QModelIndex, QItemSelectionModel


class FilterCurrentProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selection_model = None

    def setSelectionModel(self, selection_model: QItemSelectionModel):
        """Set the selection model to use for filtering"""
        if self._selection_model:
            selection_model.selectionChanged.disconnect(self.invalidateFilter)

        if selection_model:
            selection_model.selectionChanged.connect(self.invalidateFilter)

        self._selection_model = selection_model

    def _is_index_selected(self, source_row, source_parent):
        """Check if the given source row is selected"""
        if not self._selection_model:
            return True

        index = self.sourceModel().index(source_row, 0, source_parent)
        return self._selection_model.isSelected(index)

    def _is_index_current(self, source_row, source_parent):
        """Check if the given source row is selected"""
        if not self._selection_model:
            return True

        return self._selection_model.currentIndex() == self.sourceModel().index(source_row, 0, source_parent)

    def filterAcceptsRow(self, source_row, source_parent):
        """Override method to implement custom filtering logic"""
        return self._is_index_selected(source_row, source_parent)

from enum import IntEnum


# class NodeInspector(QWidget):
#     def __init__(self, parent:QWidget|None=None):
#         super().__init__(parent=parent)
#         self._node : NodeItem|None = None

#         main_layout = QVBoxLayout()
#         self._header_label = QLabel()
#         self._fields_form = QFormLayout()

#         self._fields_list = QListView()

#         menubar = QMenuBar(self)
#         add_field_action = QAction("add field", self)
#         add_field_action.triggered.connect(lambda: self._add_new_field())
#         menubar.addAction(add_field_action)
#         remove_field_action = QAction("remove field", self)
#         remove_field_action.triggered.connect(lambda: self._remove_selected_field())
#         menubar.addAction(remove_field_action)

#         main_layout.setMenuBar(menubar)
#         main_layout.addWidget(self._header_label)
#         main_layout.addWidget(self._fields_list)
#         # main_layout.addLayout(self._fields_form)


#         self.setLayout(main_layout)
    
#     def setNode(self, node:NodeItem):
#         definitions_model = node.definition.model()
#         definition_name = definitions_model.data(node.definition, Qt.ItemDataRole.DisplayRole)
#         self._header_label.setText(f"<h1>{node.name}</h1><p>{definition_name}</p>")
#         self._fields_list.setModel(node.fields)
#         self._node = node



#         # for row in range(node.fields.rowCount()):
#         #     index = node.fields.index(row, 0)
#         #     name = index.data(Qt.ItemDataRole.DisplayRole)
#         #     value = FieldsListModel.Roles.Value
#         #     self._fields_form.addRow(name, QLabel(f"{value}"))

#     @Slot()
#     def _add_new_field(self):
#         if not self._node:
#             return False
#         print("add new field")
#         field_item = FieldItem("new field", "no value")
#         self._node.fields.insertFieldItem(self._node.fields.rowCount(), field_item)


#     @Slot()
#     def _remove_selected_field(self):
#         if not self._node:
#             return False


class PropertyTableView(QTableView):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)





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
        self.definitions = DefinitionsModel()
        self.nodes = NodesModel()
        self.node_selection = QItemSelectionModel(self.nodes)
        self.edges = EdgesModel(nodes=self.nodes)
        
        # configure model
        self.node_selection = QItemSelectionModel(self.nodes)

        ### Widgets
        self.definitions_table_view = QTableView()
        self.definitions_table_view.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.definitions_table_view.setItemDelegate(DefinitionsEditorDelegate())
        self.definitions_table_view.setModel(self.definitions)
        self.definitions_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.nodes_sheet_table_view = QTableView()
        self.nodes_sheet_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.nodes_sheet_table_view.setModel(self.nodes)
        self.nodes_sheet_table_view.setSelectionModel(self.node_selection)
        self.nodes_sheet_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.edges_sheet_table_view = QTableView(self)
        self.edges_sheet_table_view.setItemDelegate(ListTileDelegate())
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
        # self.node_inspector = QWidget()
        self.node_inspector = QFrame(self)
        self.node_inspector.setFrameShape(QFrame.Shape.StyledPanel)  # Styled panel for the frame
        self.node_inspector.setFrameShadow(QFrame.Shadow.Raised)
        inspector_header_tile = TileWidget()
        property_editor = PropertyTableView()
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
                node_item = self.nodes.data(current_node_index.siblingAtColumn(0), Qt.ItemDataRole.UserRole)
                print(node_item.name, "")
                inspector_header_tile.setHeading(f"#{current_node_index.row()} {node_item.name}")
                property_editor.setModel(node_item.fields)
                
                    
            else:
                print("hide inspector")
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
        # init_definitions_action = QAction("Init definitions", self)
        # init_definitions_action.triggered.connect(self.init_definitions)
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
        # layout_action = QAction("layout", self)
        # layout_action.triggered.connect(graph_scene.layout)

        menubar = QMenuBar(parent=self)
        menubar.addAction(save_action)
        menubar.addAction(open_action)
        menubar.addAction(add_node_action)
        menubar.addAction(delete_node_action)
        menubar.addAction(connect_selected_nodes_action)
        menubar.addAction(remove_edge_action)
        # menubar.addAction(layout_action)

        ### Layout
        import pylive.utils.qtfactory as qf

        # def show_node_in_inspector(index):
        #     node_item = index.data(Qt.ItemDataRole.UserRole)
        #     self.node_inspector.setNode(node_item)
        # self.node_selection.currentChanged.connect(show_node_in_inspector)

        def create_graph_panel():
            panel = QWidget()
            grid_layout = QGridLayout()
            panel.setLayout(grid_layout)

            grid_layout.addWidget(self.graph_view, 0, 0)
            grid_layout.addWidget(self.node_inspector,0,0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
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



        # grid_layout = QGridLayout()
        # grid_layout.setMenuBar(menubar)
        # # grid_layout.addWidget(nodelist, 1, 0)
        # # grid_layout.addWidget(edgelist, 1, 1)
        # grid_layout.addWidget(self.definitions_list_view, 0, 0, 1, 1) #row, col, row span, col spn
        # grid_layout.addWidget(self.nodes_list_view,       0, 1, 1, 1)
        # grid_layout.addWidget(self.node_inspector,        0, 3, 1, 1)
        # grid_layout.addWidget(self.graph_view,            1, 0, 1, 4)
        # self.statusbar = QStatusBar(self)
        # grid_layout.addWidget(self.statusbar, 2,0,1,4)
        # self.setLayout(grid_layout)

        # self.init_definitions()

    ### The python script flow documents
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

        ### try to load
        from pathlib import Path
        import yaml
        # parse yaml
        text = Path(filepath).read_text()
        data = yaml.load(text, Loader=yaml.SafeLoader)

        def get_python_function_from_string(code:str)->tuple[str, Callable]:
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
        _definition_index_by_name = dict()
        self.definitions.blockSignals(True)
        self.definitions.removeRows(0, self.definitions.rowCount())
        import inspect
        for row, code in enumerate(data['definitions']):
            ### get python function from string
            # the string should contain a single function definition
            try:
                name, func = get_python_function_from_string(code)
                self.definitions.insertDefinitionItem(row, 
                    DefinitionItem(name=name,source=code))
                _definition_index_by_name[name] = row
            except Exception as err:
                print("ERROR", err)
                self.statusbar.showMessage(f"error: {err}")
        self.definitions.blockSignals(False)
        self.definitions.modelReset.emit()

        _node_row_by_name = dict()
        self.nodes.blockSignals(True)
        for row, node in enumerate(data['nodes']):
            print(node)
            func_name = node['func']
            def_row = _definition_index_by_name[func_name]

            self.nodes.addNodeItem(
                NodeItem(
                    name=node['name'], 
                    definition=QPersistentModelIndex( self.definitions.index(def_row, 0) )
                )
            )
            _node_row_by_name[node['name']] = row
        self.nodes.blockSignals(False)
        self.nodes.modelReset.emit()

        self.edges.blockSignals(True)
        for row, edge in enumerate(data['edges']):
            source_name = edge['source']
            target_name = edge['target']
            source_row = _node_row_by_name[source_name]
            target_row = _node_row_by_name[target_name]
            source_index = self.nodes.index(source_row, 0)
            target_index = self.nodes.index(target_row, 0)
            edge = EdgeItem(QPersistentModelIndex(source_index), QPersistentModelIndex(target_index), edge['inlet'])
            self.edges.addEdgeItem(edge)

        self.edges.blockSignals(False)
        self.edges.modelReset.emit()

        return True


    def deserialize(self, text:str):
        ...

        # # set definitions
        # self.definitions = data['definitions']

        # #parse graph
        # nodes = [Node(_['name'], _['func']) for _ in data['graph']['nodes']]
        # edges = [Edge(_[0], _[1], _[2]) for _ in data['graph']['edges']]
        # self.graph = Graph(nodes, edges)

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

    def serialize(self)->str:
        import yaml
        return yaml.dump({
            'definitions': self.definitions,
        })

    @Slot()
    def saveFile(self):
        ...

    # def _pathlib_module_functions(self):
    #     import pathlib
    #     import string
    #     for key in dir(pathlib):
    #         if key[0] in string.ascii_letters: 
    #             item = getattr(pathlib,key)
    #             if callable(item):
    #                 yield key

    # @Slot()
    # def init_definitions(self):
    #     ### add builtin functions
    #     import inspect
    #     for name in dir(__builtins__):
    #         if not name.startswith("_"):
    #             attribute = getattr(__builtins__, name)
    #             if callable(attribute) and not inspect.isclass(attribute):
    #                 item = QStandardItem()
    #                 item.setData(name, Qt.ItemDataRole.DisplayRole)
    #                 item.setData(attribute, self.DefinitionFunctionRole)
    #                 self.definitions_model.appendRow(item)

    #     ### execute definition script
    #     definitions_script = self.definitions_editor.toPlainText()

    #     try:
    #         capture = {'__builtins__': __builtins__}
    #         exec(definitions_script, capture)

    #         for name, attribute in capture.items():
    #             if name!='__builtins__':
    #                 if callable(attribute) and not inspect.isclass(attribute):
    #                     fn_item = QStandardItem()
    #                     fn_item.setData(name, Qt.ItemDataRole.DisplayRole)
    #                     fn_item.setData(name, self.DefinitionFunctionRole)
    #                     self.definitions_model.insertRow(self.definitions_model.rowCount(), fn_item)

    #         self._update_document()
    #         self.statusbar.showMessage(f"definitions initalized")
    #     except Exception as err:
    #         self.statusbar.showMessage(f"error: {err}")
    #         # QMessageBox.critical(self, "Error", f"{err}")

    # def _update_document(self):
    #     print("update document")
    #     import json

    #     definitions = self.definitions_editor.toPlainText()

    #     nodes = dict()
    #     for row in range(self.nodes.rowCount()):
    #         index = self.nodes.index(row, 0)
    #         name = self.nodes.data(index, Qt.ItemDataRole.DisplayRole)
    #         definition_index = self.nodes.data(index, self.NodeDefinitionRole)
    #         definition_name = self.definitions_model.data(definition_index, Qt.ItemDataRole.DisplayRole)
    #         nodes[name] = definition_name

    #     edges = []
    #     for row in range(self.edges.rowCount()):
    #         index = self.edges.index(row, 0)
    #         source_idx = self.edges.data(index, QGraphEditorScene.SourceRole)
    #         target_idx = self.edges.data(index, QGraphEditorScene.TargetRole)
    #         source_name = self.nodes.data(source_idx, Qt.ItemDataRole.DisplayRole)
    #         target_name = self.nodes.data(target_idx, Qt.ItemDataRole.DisplayRole)
    #         edges.append( (source_name, target_name) )

    #     import yaml
    #     class LiteralString(str):
    #         pass

    #     def literal_representer(dumper, data):
    #         # Use `|` without `-` to keep trailing newlines intact
    #         value = data if data.endswith('\n') else f"{data}\n"
    #         return dumper.represent_scalar('tag:yaml.org,2002:str', value, style='|')

    #     yaml.add_representer(LiteralString, literal_representer)

    #     document_text = yaml.dump({
    #         'definitions': LiteralString(definitions),
    #         'nodes': nodes,
    #         'edges': edges
    #     }, indent=4)

    #     self.document.setPlainText(document_text)

    @Slot()
    def create_new_node(self):
        ###
        if self.definitions_model.rowCount()==0:
            QMessageBox.warning(self, "No definions!", "Please create function definitions!")
            return

        from itertools import chain
        # node_name, accepted =  QOptionDialog.getItem(self , "Title", "label", ['print', "write"], 0, editable=True)
        definitions = dict()
        for row in range(self.definitions_model.rowCount()):
            definition_index = self.definitions_model.index(row, 0)
            name = definition_index.data(Qt.ItemDataRole.DisplayRole)
            func = definition_index.data(self.DefinitionFunctionRole)
            definitions[name]  = definition_index
       
        definition_key, accepted =  QOptionDialog.getItem(self , "Title", "label", [_ for _ in definitions.keys()] , 0)
        if definition_key and accepted:
            from pylive.utils.unique import make_unique_name
            node_names = [self.nodes.data(self.nodes.index(row, 0), Qt.ItemDataRole.DisplayRole) for row in  range(self.nodes.rowCount())]
            node_key = make_unique_name(f"{definition_key}1", node_names)
            item = QStandardItem()
            item.setData(f"{node_key}", Qt.ItemDataRole.DisplayRole)
            item.setData(definitions[definition_key], self.NodeDefinitionRole)
            self.nodes.insertRow(self.nodes.rowCount(), item)

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

    def eventFilter(self, watched, event):
        if watched == self.graph_view:
            if event.type() == QEvent.Type.MouseButtonDblClick:
                self.create_new_node()
                return True

        return super().eventFilter(watched, event)

    def sizeHint(self):
        return QSize(2048, 900)


if __name__ == "__main__":
    app = QApplication()
    window = Window()
    window.show()
    window.openFile("./website_builder.yaml")
    app.exec()

