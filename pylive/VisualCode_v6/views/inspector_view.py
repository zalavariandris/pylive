from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from pylive.VisualCode_v6.py_graph_model import PyGraphModel
from pylive.VisualCode_v6.py_proxy_node_model import PyProxyNodeModel
from pylive.VisualCode_v6.py_proxy_link_model import PyProxyLinkModel

PropsDict = dict[str, Any]
PropsDiff = dict[str, tuple[Any, Any]]

class InspectorView(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)

        self._model:PyProxyNodeModel|None=None
        self._node_selection_model:QItemSelectionModel|None=None
        self._current:str|None=None
        self._model_connections = []
        self._selection_connections = []

        self.createWidgets()
        
    def setModel(self, model:PyProxyNodeModel|None):
        if self._model:
            for signal, slot in self._model_connections:
                signal.disconnect(slot)

        if model:
            self._model_connections = [
                (model.dataChanged, self.updateWidget),
            ]
            for signal, slot in self._model_connections:
                signal.connect(slot)
        self._model = model

    def setSelectionModel(self, selection:QItemSelectionModel):
        assert self._model is not None, "cant set selection model without a model"

        if self._node_selection_model:
            for signal, slot in self._selection_connections:
                signal.disconnect(slot)

        if selection:
            self._selection_connections = [
                (selection.currentChanged, self.updateWidget)
            ]

            for signal, slot in self._selection_connections:
                signal.connect(slot)

        self._node_selection_model = selection

    def createWidgets(self):
        layout = QFormLayout()
        self.name_label = QLabel(self, text="-node name-")
        layout.addRow("name", self.name_label)
        self.kind_dropdown = QComboBox()
        self.kind_dropdown.insertItems(0, ['operator', 'value-int', 'value-float', 'value-str', 'value-path', 'expression'])
        self.kind_dropdown.setDisabled(False)
        layout.addRow("kind", self.kind_dropdown)
        self.content_edit = QLineEdit(self)
        layout.addRow("content", self.content_edit)
        self.setLayout(layout)

        def updateModelKind(new_kind:str):
            current_index = self._node_selection_model.currentIndex()
            kind_index = current_index.siblingAtColumn(1)
            print(current_index, kind_index)
            self._model.setData(
                kind_index, new_kind,
                Qt.ItemDataRole.DisplayRole
            )
        self.kind_dropdown.currentTextChanged.connect(lambda text: updateModelKind(text))

        def updateModelContent(new_content:str):
              self._model.setData(
                  self._node_selection_model.currentIndex().siblingAtColumn(2), new_content,
                  Qt.ItemDataRole.DisplayRole
              )

        self.content_edit.textChanged.connect(lambda text: updateModelContent(text))

        # self.content_editor = QLabel("-data editor -")
        # mapper = QDataWidgetMapper()
        # operator_editor = QLineEdit() #operator
        # expression_editor = QLineEdit() #expression
        # int_editor = QSpinBox() #value-int
        # float_editor = QDoubleSpinBox() #value-float
        # str_editor = QLineEdit() #value-str
        # path_editor = QPathEdit() #value-path100100
        # self.stacked_widget = QStackedWidget()
        # self.stacked_widget.addWidget(operator_editor)
        # self.stacked_widget.addWidget(expression_editor)
        # self.stacked_widget.addWidget(int_editor)
        # self.stacked_widget.addWidget(float_editor)
        # self.stacked_widget.addWidget(str_editor)
        # self.stacked_widget.addWidget(path_editor)

    def updateWidget(self):
        assert self._model
        assert self._node_selection_model
        # compare widget state to model state
        current_row = self._node_selection_model.currentIndex().row()

        PropsDiff = dict[str, tuple[Any, Any]]
        def props_diff(old: dict[str, Any], new: dict[str, Any]) -> PropsDiff:
            """
            Calculate the difference between two PropsDicts, except for "children".

            Will never return a value of (None, None).
            """
            diff = {}
            for key in set(old) | set(new):
                if key != "children":
                    if key not in old:
                        new_val = new[key]
                        if new_val is not None:
                            diff[key] = (None, new_val)
                    elif key not in new:
                        old_val = old[key]
                        if old_val is not None:
                            diff[key] = (old_val, None)
                    elif old[key] != new[key]:
                        diff[key] = (old[key], new[key])
            return diff

        new_props = {
            "name": self._model.index(current_row, 0).data(Qt.ItemDataRole.DisplayRole),
            "kind": self._model.index(current_row, 1).data(Qt.ItemDataRole.DisplayRole),
            "content": self._model.index(current_row, 2).data(Qt.ItemDataRole.DisplayRole),
        }

        old_props = {
            "name": self.name_label.text(),
            "kind": self.kind_dropdown.currentText(),
            "content": None
        }

        diff_props = props_diff(old_props, new_props)

        # compare widget state to model state
        print("update widget", diff_props)
        
        match diff_props.get("name"):
            case (old_name, new_name):
                print("name changed")
                self.name_label.setText(new_name)
        all_kinds = ['operator', 'expression']

        match diff_props.get("kind"):
            case old_kind, new_kind:
                print("kind changed")
                self.kind_dropdown.setCurrentText(new_kind)
                # print(new_kind)
                # match new_kind:
                #     case None:
                #         self.kind_dropdown.setCurrentIndex(-1)
                #     case 'operator'|'value-int'|'value-float'|'value-str'|'value-path'|'expression':
                #         self.kind_dropdown.setCurrentText(new_kind)
                #     case _:
                #         print("warning unknown kind", new_kind)
                #         self.kind_dropdown.setCurrentIndex(-1)

        match diff_props.get("content"):
            case (old_content, new_content):
                self.content_edit.setText(new_content)
                print("param content changed")


    # def _setCurrent(self, node:str|None):
    #     self._current = node
            
    #     if node:
    #         self._setEditorData()
    #     else:
    #         self._clearEditorData()

    # def _setEditorData(self, hints:list=[]):
    #     assert self._model
    #     assert self._current
    #     ### Previews
    #     if 'result' in hints or not hints:
    #         error, result = self._model.data(self._current, 'result')

    #         if error:
    #             self.preview_label.setText(f"{error}")
    #         else:
    #             match result:
    #                 case QWidget():
    #                     raise NotImplementedError("QWidgets are not yet supported")
    #                 case _:
    #                     self.preview_label.setText(f"{result}")

    # def _clearEditorData(self):
    #     self.preview_label.setText("")


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

#             if not isinstance(self._content_editor, kind_editocontentr_map[kind]):

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
