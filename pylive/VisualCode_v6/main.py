from importlib.machinery import ModuleSpec
import inspect
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *



from pathlib import Path

import logging



from pylive.qt_components.QPathEdit import QPathEdit
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# from pylive.QtGraphEditor.definitions_model import DefinitionsModel

### DATA ###
# 
# from pylive.QtGraphEditor.py_functions_model import PyFunctionsModel
from pylive.VisualCode_v6.py_graph_model import PyGraphModel
from pylive.VisualCode_v6.py_proxy_node_model import PyProxyNodeModel
from pylive.VisualCode_v6.py_proxy_link_model import PyProxyLinkModel
from pylive.VisualCode_v6.py_graph_view import PyGraphView

from pylive.utils.unique import make_unique_id
import pylive.utils.qtfactory as qf
from pylive.VisualCode_v6.imports_manger import ImportsManager



# class InspectorView(QWidget):
#     def __init__(self, parent:QWidget|None=None):
#         super().__init__(parent=parent)
#         # private
#         self._model:PyGraphModel|None=None
#         self.node_proxy_model:PyProxyNodeModel|None = None
#         self.node_selection_model:QItemSelectionModel|None=None
#         self._current:str|None=None
#         self._model_connections = []
#         self._selection_connections = []

#         self.setupUI()

#     def setupUI(self):
#         # setup UI
#         self.kind_dropdown = QComboBox()
#         self.kind_dropdown.insertItems(0, ['operator', 'value-int', 'value-float', 'value-str', 'value-path', 'expression'])
#         self.kind_dropdown.setDisabled(True)
#         self._content_editor = QLabel("-data editor -")

#         # Layout
#         main_layout = QVBoxLayout()
#         main_layout.addWidget(self.kind_dropdown)
#         main_layout.addWidget(self._content_editor)
#         self.setLayout(main_layout)

#     def patchUI(self):
#         layout = cast(QVBoxLayout, self.layout())
#         if not self._model or not self._current:
#             self.kind_dropdown.setCurrentText("")
#             self.kind_dropdown.setEnabled(False)
#             new_editor = QLabel("-data editor -")
#             layout.replaceWidget(self._content_editor, new_editor)
#             self._content_editor = new_editor

#         if self._model and self._current:
#             kind = self._model.data(self._current, 'kind')
#             if self.kind_dropdown.currentText() != kind:
#                 self.kind_dropdown.setCurrentText(kind)

#             kind_editor_map = {
#                 'operator':    QLineEdit,
#                 'expression':  QLineEdit,
#                 'value-int':   QSpinBox,
#                 'value-float': QDoubleSpinBox,
#                 'value-str':   QLineEdit,
#                 'value-path':  QPathEdit
#             }

#             if not isinstance(self._content_editor, kind_editor_map[kind]):

#                 new_editor = kind_editor_map[kind]()
#                 layout.replaceWidget(self._content_editor, new_editor)
#                 self._content_editor = new_editor


#     def setModel(self, model:PyGraphModel|None):
#         if self._model:
#             for signal, slot in self._model_connections:
#                 signal.disconnect(slot)

#         if model:
#             assert isinstance(model, PyGraphModel)
#             self._model_connections = [
#                 (model.dataChanged, 
#                     lambda nodes, hints: self._setEditorData(hints) 
#                     if self._current in nodes
#                     else 
#                     None)
#             ]
#         for signal, slot in self._model_connections:
#             signal.connect(slot)

#         self._model = model
#         self._setCurrent(None)

#     def setSelectionModel(self, selection:QItemSelectionModel|None, proxy:PyProxyNodeModel|None):
#         assert all([selection is None, proxy is None]) or all([selection is not None, proxy is not None])
        
#         if self.node_proxy_model and self.node_selection_model:
#             for signal, slot in self._selection_connections:
#                 signal.disconnect(slot)

#         if selection and proxy:
#             self._selection_connections = [
#                 (selection.currentChanged, 
#                     lambda current, previous: self._setCurrent(proxy.mapToSource(current)))
#             ]

#             for signal, slot in self._selection_connections:
#                 signal.connect(slot)

#         self.node_proxy_model = proxy
#         self.node_selection_model = selection


#     def _setCurrent(self, node:str|None):
#         assert self._model
#         self._current = node

#         layout = cast(QVBoxLayout, self.layout())

#         ### create editor
#         if self._current:
#             # update kind dropdown
#             self.kind_dropdown.setEnabled(True)

#             # update content editor
#             new_content_editor = self._createContentEditor(self._model, self._current)
#             item = layout.replaceWidget(self._content_editor, new_content_editor)
#             self._content_editor.deleteLater()
#             self._content_editor = new_content_editor
#             self._setEditorData(self._content_editor, self._model, self._current, hints=[])
#         else:
#             self.kind_dropdown.setEnabled(False)
#             new_content_editor = QLabel("-no editor-")
#             item = layout.replaceWidget(self._content_editor, new_content_editor)
#             self._content_editor.deleteLater()
#             self._content_editor = new_content_editor

        
#     def _createContentEditor(self, model:PyGraphModel, node:str)->QWidget:
#         kind = model.data(node, 'kind')
#         match kind:
#             case 'operator':
#                 editor = QLineEdit()
#                 editor.setText(model.data(node, 'content'))
#                 editor.editingFinished.connect(lambda editor=editor, model=model, node=node:
#                     self._setModelData(editor, model, node, ['content']))

#             case 'expression':
#                 editor = QLineEdit()
#                 editor.setText(model.data(node, 'content'))
#                 editor.editingFinished.connect(lambda editor=editor, model=model, node=node:
#                     self._setModelData(editor, model, node, ['content']))

#             case 'value-int':
#                 editor = QSpinBox()
#                 editor.setValue(int(model.data(node, 'content')))
#                 editor.valueChanged.connect(lambda editor=editor, model=model, node=node:
#                     self._setModelData(editor, model, node, ['content']))

#             case 'value-float':
#                 editor = QDoubleSpinBox()
#                 editor.setValue(float(model.data(node, 'content')))

#                 editor.valueChanged.connect(lambda editor=editor, model=model, node=node:
#                     self._setModelData(editor, model, node, ['content']))

#             case 'value-str':
#                 editor = QLineEdit()
#                 editor.setText(model.data(node, 'content'))
#                 editor.editingFinished.connect(lambda editor=editor, model=model, node=node:
#                     self._setModelData(editor, model, node, ['content']))

#             case 'value-path':
#                 editor = QPathEdit()
#                 editor.setPath(str(model.data(node, 'content')))
#                 editor.editingFinished.connect(lambda editor=editor, model=model, node=node:
#                     self._setModelData(editor, model, node, ['content']))
#             case _:
#                 raise ValueError()

#         return editor

#     def _setEditorData(self, editor:QWidget, model:PyGraphModel, node:str, hints:list=[]):
#         if not self._model or not self._current:
#             self.kind_dropdown.setEnabled(False)
#             self._content_editor.setEnabled(False)
#             return

#         self.kind_dropdown.setEnabled(True)
#         node = self._current
#         if 'kind' in hints or not hints:
#             node_kind = self._model.data(node, 'kind')
#             if node_kind!=self.kind_dropdown.currentText():
#                 self.kind_dropdown.setCurrentText(node_kind)

#         self._content_editor.setEnabled(True)
#         if 'content' in hints or not hints:
#             kind = self._model.data(node, 'kind')
#             content = self._model.data(node, 'content')
#             match kind:
#                 case 'operator':
#                     editor = cast(QLineEdit, self._content_editor)
#                     editor.setText(self._model.data(node, 'content', Qt.ItemDataRole.DisplayRole))
#                 case 'expression':
#                     editor = cast(QLineEdit, self._content_editor)
#                     editor.setText(self._model.data(node, 'content', Qt.ItemDataRole.DisplayRole))
#                 case 'value-int':
#                     editor = cast(QSpinBox, self._content_editor)
#                     editor.setValue(self._model.data(node, 'content', Qt.ItemDataRole.EditRole))
#                 case 'value-float':
#                     editor = cast(QDoubleSpinBox, self._content_editor)
#                     editor.setValue(self._model.data(node, 'content', Qt.ItemDataRole.EditRole))
#                 case 'value-str':
#                     editor = cast(QLineEdit, self._content_editor)
#                     editor.setText(self._model.data(node, 'content', Qt.ItemDataRole.EditRole))
#                 case 'value-path':
#                     editor = cast(QPathEdit, self._content_editor)
#                     editor.setText(self._model.data(node, 'content', Qt.ItemDataRole.EditRole))
#                 case _:
#                     pass

#     def _setModelData(self, editor:QWidget, model:PyGraphModel, node:str, hints:list=[]):
#         assert isinstance(node, str)
#         if not self._model:
#             return

#         if not self._current:
#             return

#         if self._current:
#             node = self._current
#             if 'kind' in hints or not hints:
#                 node_kind = self._model.data(node, 'kind')
#                 if node_kind!=self.kind_dropdown.currentText():
#                     self._model.setData(node, 'kind', self.kind_dropdown.currentText())

#             if 'content' in hints or not hints:
#                 kind = self._model.data(node, 'kind')
#                 content = self._model.data(node, 'content')
#                 match kind:
#                     case 'operator':
#                         editor = cast(QLineEdit, self._content_editor)
#                         self._model.setData(node, 'content', editor.text())
#                     case 'expression':
#                         editor = cast(QLineEdit, self._content_editor)
#                         self._model.setData(node, 'content', editor.text())
#                     case 'value-int':
#                         editor = cast(QSpinBox, self._content_editor)
#                         self._model.setData(node, 'content', str(editor.value()))
#                     case 'value-float':
#                         editor = cast(QDoubleSpinBox, self._content_editor)
#                         self._model.setData(node, 'content', str(editor.value()))
#                     case 'value-str':
#                         editor = cast(QLineEdit, self._content_editor)
#                         self._model.setData(node, 'content', editor.text())
#                     case 'value-path':
#                         editor = cast(QPathEdit, self._content_editor)
#                         self._model.setData(node, 'content', editor.text())
#                     case _:
#                         pass


class PreView(QScrollArea):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter)
        self.setWidgetResizable(True)
        self._previous_parent:QObject|None = None

        self.preview_label = QLabel()
        self.setWidget(self.preview_label)

        self._model:PyGraphModel|None=None
        self.node_proxy_model:PyProxyNodeModel|None = None
        self.node_selection_model:QItemSelectionModel|None=None
        self._current:str|None=None
        self._model_connections = []
        self._selection_connections = []
        
    def setModel(self, model:PyGraphModel|None):
        if self._model:
            for signal, slot in self._model_connections:
                signal.disconnect(slot)

        if model:
            self._model_connections = [
                (model.dataChanged, 
                    lambda nodes, hints: self._setEditorData(hints) 
                    if self._current in nodes
                    else 
                    None),
            ]
            for signal, slot in self._model_connections:
                signal.connect(slot)
        self._model = model

    def setSelectionModel(self, selection:QItemSelectionModel|None, proxy:PyProxyNodeModel|None):
        assert all([selection is None, proxy is None]) or all([selection is not None, proxy is not None])
        
        if self.node_proxy_model and self.node_selection_model:
            for signal, slot in self._selection_connections:
                signal.disconnect(slot)

        if selection and proxy:
            self._selection_connections = [
                (selection.currentChanged, 
                    lambda current, previous: self._setCurrent(proxy.mapToSource(current)))
            ]

            for signal, slot in self._selection_connections:
                signal.connect(slot)

        self.node_proxy_model = proxy
        self.node_selection_model = selection

    def _setCurrent(self, node:str|None):
        self._current = node
            
        if node:
            self._setEditorData()
        else:
            self._clearEditorData()

    def _setEditorData(self, hints:list=[]):
        assert self._model
        assert self._current
        ### Previews
        if 'result' in hints or not hints:
            error, result = self._model.data(self._current, 'result')

            if error:
                self.preview_label.setText(f"{error}")
            else:
                match result:
                    case QWidget():
                        raise NotImplementedError("QWidgets are not yet supported")
                    case _:
                        self.preview_label.setText(f"{result}")

    def _clearEditorData(self):
        self.preview_label.setText("")


class NodeKindDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        if index.column()==1:
            combo = QComboBox(parent)
            combo.addItems(["operator", 'value-int', 'value-float', 'value-str', 'value-path', 'expression'])
            return combo
        else:
            return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if index.column()==1:
            value = index.model().data(index, role=Qt.ItemDataRole.DisplayRole)
            editor.setCurrentText(value)
        else:
            return super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if index.column()==1:
            model.setData(index, editor.currentText(), role=Qt.ItemDataRole.EditRole)
        else:
            return super().setModelData(editor, model, index)


class NodeContentDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index:QModelIndex|QPersistentModelIndex)->QWidget:
        print("createEditor")
        kind = index.model().index(index.row(), 1).data(Qt.ItemDataRole.EditRole)
        print(f"createEditor for {kind}")
        match kind:
            case 'operator':
                return QLineEdit(parent=parent)
            case 'value-int':
                return QSpinBox(parent=parent)
            case 'value-float':
                return QDoubleSpinBox(parent=parent)
            case 'value-str':
                return QLineEdit(parent=parent)
            case 'value-path':
                return QPathEdit(parent=parent)
            case 'expression':
                return QLineEdit(parent=parent)
            case _:
                return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        kind = index.model().index(index.row(), 1).data(Qt.ItemDataRole.EditRole)
        match kind:
            case 'operator':
                editor = cast(QLineEdit, editor)
                editor.setText(index.data(Qt.ItemDataRole.EditRole))
            case 'value-int':
                editor = cast(QSpinBox, editor)
                editor.setValue(index.data(Qt.ItemDataRole.EditRole))
            case 'value-float':
                editor = cast(QDoubleSpinBox, editor)
                editor.setValue(index.data(Qt.ItemDataRole.EditRole))
            case 'value-str':
                editor = cast(QLineEdit, editor)
                editor.setText(index.data(Qt.ItemDataRole.EditRole))
            case 'value-path':
                editor = cast(QPathEdit, editor)
                editor.setPath(index.data(Qt.ItemDataRole.EditRole))
            case 'expression':
                editor = cast(QLineEdit, editor)
                editor.setText(index.data(Qt.ItemDataRole.EditRole))
            case _:
                super().setEditorData(editor, index)

    def setModelData(self, editor, model:QAbstractItemModel, index:QModelIndex|QPersistentModelIndex):
        kind = index.model().index(index.row(), 1).data(Qt.ItemDataRole.EditRole)
        match kind:
            case 'operator':
                editor = cast(QLineEdit, editor)
                model.setData(index, editor.text(), Qt.ItemDataRole.EditRole)
            case 'value-int':
                editor = cast(QSpinBox, editor)
                model.setData(index, int(editor.value()), Qt.ItemDataRole.EditRole)
            case 'value-float':
                editor = cast(QDoubleSpinBox, editor)
                model.setData(index, float(editor.value()), Qt.ItemDataRole.EditRole)
            case 'value-str':
                editor = cast(QLineEdit, editor)
                model.setData(index, str(editor.text()), Qt.ItemDataRole.EditRole)
            case 'value-path':
                editor = cast(QPathEdit, editor)
                model.setData(index, pathlib.Path(editor.path()), Qt.ItemDataRole.EditRole)
            case 'expression':
                editor = cast(QLineEdit, editor)
                model.setData(index, str(editor.text()), Qt.ItemDataRole.EditRole)
            case _:
                super().setEditorData(editor, index)

    # This is critical - it prevents the editor from closing when focus is lost
    def eventFilter(self, obj, event):
        # Skip closing the editor for certain event types (like FocusOut)
        if event.type() in [QEvent.Type.FocusOut] and isinstance(obj, QPathEdit):
            # Check if there's a modal dialog open
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QFileDialog) and widget.isModal():
                    return True  # Block the event
                    
        return super().eventFilter(obj, event)

    def initStyleOption(self, option:QStyleOptionViewItem, index:QModelIndex|QPersistentModelIndex):
        super().initStyleOption(option, index);
        option.textElideMode = Qt.TextElideMode.ElideLeft;
    


class MainWindow(QWidget):
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
        self._menubar_connections = []
        # self._inspector_connections = []
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
        ### SheetsView
        self.nodes_table_view = QTableView()
        self.nodes_table_view.setModel(self.node_proxy_model)
        self.nodes_table_view.setSelectionModel(self.node_selection_model)
        self.nodes_table_view.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
        self.nodes_table_view.setTextElideMode(Qt.TextElideMode.ElideLeft)
        self.nodes_table_view.setWordWrap(False)
        self.kind_delegate = NodeKindDelegate(parent=self)
        self.nodes_table_view.setItemDelegateForColumn(1, self.kind_delegate)
        self.content_delegate = NodeContentDelegate(parent=self)
        self.nodes_table_view.setItemDelegateForColumn(2, self.content_delegate)
        self.links_table_view = QTableView()
        self.links_table_view.setModel(self.link_proxy_model)
        self.links_table_view.setSelectionModel(self.link_selection_model)

        ### Imports manager
        self.import_manager = ImportsManager()

        self._setupGraphview()
        
        ### inspector
        self.inspector = QWidget()
        self.inspector_layout = QFormLayout()
        self.kind_dropdown = QComboBox()
        self.kind_dropdown.insertItems(0, ['operator', 'value-int', 'value-float', 'value-str', 'value-path', 'expression'])
        self.kind_dropdown.setDisabled(True)
        self.content_editor = QLabel("-data editor -")
        mapper = QDataWidgetMapper()
        operator_editor = QLineEdit() #operator
        expression_editor = QLineEdit() #expression   
        int_editor = QSpinBox() #value-int
        float_editor = QDoubleSpinBox() #value-float
        str_editor = QLineEdit() #value-str
        path_editor = QPathEdit() #value-path100100
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(operator_editor)
        self.stacked_widget.addWidget(expression_editor)
        self.stacked_widget.addWidget(int_editor)
        self.stacked_widget.addWidget(float_editor)
        self.stacked_widget.addWidget(str_editor)
        self.stacked_widget.addWidget(path_editor)
        
        # content editors for different node type
        # def update_detail_view(current:QModelIndex, previous):
        #     kind = self.node_proxy_model.index(current.row(), 1).data(Qt.ItemDataRole.DisplayRole)
        #     content = self.node_proxy_model.index(current.row(), 2).data(Qt.ItemDataRole.EditRole)
        #     match kind:
        #         case 'operator':
        #             assert isinstance(content, str)
        #             self.stacked_widget.setCurrentWidget(operator_editor)
        #             mapper.addMapping(operator_editor, 2)
        #             operator_editor.setText(content)
        #         case 'expression':
        #             assert isinstance(content, str)
        #             self.stacked_widget.setCurrentWidget(expression_editor)
        #             mapper.addMapping(expression_editor, 2)
        #             expression_editor.setText(content)
        #         case 'value-int':
        #             assert isinstance(content, int)
        #             self.stacked_widget.setCurrentWidget(int_editor)
        #             mapper.addMapping(int_editor, 2)
        #             int_editor.setValue(content)
        #         case 'value-float':
        #             assert isinstance(content, float)
        #             self.stacked_widget.setCurrentWidget(float_editor)
        #             mapper.addMapping(float_editor, 2)
        #             float_editor.setValue(...)
        #         case 'value-str':
        #             assert isinstance(content, str)
        #             self.stacked_widget.setCurrentWidget(str_editor)
        #             mapper.addMapping(str_editor, 2)
        #             str_editor.setText(...)
        #         case 'value-path':
        #             assert isinstance(content, pathlib.Path)
        #             self.stacked_widget.setCurrentWidget(path_editor)
        #             mapper.addMapping(path_editor, 2)
        #             path_editor.setPath(content)

        # self.node_selection_model.currentRowChanged.connect(update_detail_view)
        ### Preview
        self._setupPreivewPanel()
        self._setupMenubar()

        ### STATUS BAR WIDGET
        self.statusbar = QStatusBar()
        self.statusbar.showMessage("status bar")

        ### Layout
        graphpanel = QWidget()
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.graph_view, 0, 0)
        # self.inspector.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        # grid_layout.addWidget(self.inspector, 0, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        graphpanel.setLayout(grid_layout)

        main_layout = qf.vboxlayout([
            qf.splitter(Qt.Orientation.Horizontal, [
                self.import_manager,
                qf.widget(qf.vboxlayout([
                    self.nodes_table_view,
                    self.links_table_view,
                ])),
                qf.tabwidget({
                    'graph': graphpanel
                }),
                self.preview_panel
            ]),
            self.statusbar
        ])
        self.statusbar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        main_layout.setMenuBar(self.menubar)
        self.setLayout(main_layout)
        self.updateWindowTitle()

    def _setupMenubar(self):
        ## MENUBAR
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

        self.menubar = QMenuBar(parent=self)

        filemenu = self.menubar.addMenu("File")
        filemenu.addActions([
            self.open_action, 
            self.save_action,
            self.save_as_action
        ])

        filemenu = self.menubar.addMenu("Kernel")
        filemenu.addActions([
            self.restart_kernel_action
        ])

        editmenu = self.menubar.addMenu("Edit")
        editmenu.addActions([
            self.add_node_action, 
            self.delete_selected_action, 
        ])

        viewmenu = self.menubar.addMenu("View")
        viewmenu.addActions([self.layout_nodes_action, self.center_nodes_action])

    def _bindMenubar(self):
        ### Bind Menubar
        self._menubar_connections = [
            (self.open_action.triggered, 
                lambda checked: self.openFile()),
            (self.save_action.triggered, 
                lambda checked: self.saveFile()),
            (self.save_as_action.triggered, 
                lambda checked: self.saveAsFile()),
            (self.add_node_action.triggered, 
                lambda checked: self.create_new_node()),
            (self.delete_selected_action.triggered, 
                lambda checked: self.delete_selected()),
            (self.layout_nodes_action.triggered, 
                lambda checked: self.graph_view.layoutNodes()),
            (self.center_nodes_action.triggered, 
                lambda checked: self.graph_view.centerNodes()),
            (self.restart_kernel_action.triggered, 
                lambda checked, model=self._model: self._model.restartKernel() if self._model else None)
        ]
        for signal, slot in self._menubar_connections:
            signal.connect(slot)

    def _unbindMenubar(self):
        for signal, slot in self._menubar_connections:
                signal.disconnect(slot)

    def _setupGraphview(self):
        ### GRAPH View
        self.graph_view = PyGraphView()
        self.graph_view.installEventFilter(self)

    def _bindGraphView(self, model):
        self.graph_view.setModel(model)

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

        self._graph_view_connections = [
            (self.graph_view.scene().selectionChanged, 
                update_model_selection),

            (self.node_selection_model.selectionChanged, 
                lambda selected, deselected:
                update_graphview_selection),

            (self.graph_view.nodesLinked, 
                lambda source, target, outlet, inlet: 
                self.connect_nodes(self.node_proxy_model.mapToSource(source), self.node_proxy_model.mapToSource(target), inlet))
        ]

        for signal, slot in self._graph_view_connections:
            signal.connect(slot)

    def _unbindGraphView(self):
        for signal, slot in self._graph_view_connections:
            signal.disconnect(slot)

    # def _setupInspector(self):
    #     self.inspector = InspectorView()

    # def _bindInspector(self, model):
    #     self.inspector.setModel(model)
    #     self.inspector.setSelectionModel(self.node_selection_model, self.node_proxy_model)

    def _setupPreivewPanel(self):
        self.preview_panel = PreView()
        self.preview_panel.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

    def _bindPreviewPanel(self, model):
        self.preview_panel.setModel(model)
        self.preview_panel.setSelectionModel(self.node_selection_model, self.node_proxy_model)

    def _bindDocument(self, model):
        ### Bind Document
        self._document_connections = [
            (model.nodesAdded, 
                lambda: self.setModified(True)),
            (model.nodesRemoved, 
                lambda: self.setModified(True)),
            (model.dataChanged, 
                lambda: self.setModified(True)),
            (model.nodesLinked, 
                lambda: self.setModified(True)),
            (model.nodesUnlinked, 
                lambda: self.setModified(True))
        ]
        for signal, slot in self._document_connections:
            signal.connect(slot)

    def _unbindDocument(self):
        for signal, slot in self._document_connections:
            signal.disconnect(slot)

    def setModel(self, model:PyGraphModel|None):
        if self._model:
            self._unbindGraphView()
            self._unbindMenubar()
            self._unbindDocument()
            
        if model:
            ### proxy models
            self.link_proxy_model.setSourceModel(model)
            self.node_proxy_model.setSourceModel(model)

            ### bind Import Manager
            self.import_manager.setModel(model)

            self._bindGraphView(model)
            # self._bindInspector(model)
            self._bindPreviewPanel(model)
            self._bindMenubar()
            self._bindDocument(model)

        self._model = model

    def sizeHint(self):
        return QSize(2048, 900) 

    ### Commands
    def create_new_node(self, scenepos:QPointF=QPointF()):
        assert self._model
        existing_names = list(self._model.nodes())

        func_name = make_unique_id(6)
        self._model.addNode(func_name, "None", kind='expression')

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
            QMessageBox.warning(self, "Warning", f"{err}")
        else:
            if filepath not in self._file_watcher.files():
                self._file_watcher.addPath(str(filepath))
            self._filepath = filepath
            self.setModified(False)
        self.updateWindowTitle()

    def saveAsFile(self):
        assert self._model
        filepath, filter_used = QFileDialog.getSaveFileName(self, 
            "SaveAs", self.fileFilter(), self.fileSelectFilter())
        if not filepath:
            return # if no filepath was choosen cancel saving

        try:
            with open(filepath, 'w') as file:
                import yaml
                data = self._model.toData()
                text = yaml.dump(self._model.toData(), sort_keys=False)
                Path(filepath).write_text(text)
                
        except FileNotFoundError as err:
            QMessageBox.warning(self, "Warning", f"{err}")
        else:
            if self._filepath:
                self._file_watcher.removePath(str(self._filepath))
            if filepath not in self._file_watcher.files():
                self._file_watcher.addPath(filepath)
            self._filepath = filepath
            self.setModified(False)
            self.setWorkingDirectory(Path(filepath).parent)
        self.updateWindowTitle()

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
            self._unbindGraphView()
            self._unbindMenubar()
            self._unbindDocument()
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

    app = QApplication([])

    window = MainWindow()
    window.setGeometry(QRect(QPoint(), app.primaryScreen().size()).adjusted(40,80,-30,-300))
    window.show()
    app.exec()
    # window.openFile(Path.cwd()/"./tests/dissertation_builder.yaml")

    