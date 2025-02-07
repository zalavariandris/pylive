from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

# from pylive.QtLiveApp.live_script_skeleton import LiveScriptWindow
from pylive.NXPythonGraphEditor.python_graph_scene_delegate import PythonGraphDelegate
from pylive.NetworkXGraphEditor.nx_graph_shapes import BaseNodeItem
from pylive.NetworkXGraphEditor.nx_network_model import NXNetworkModel, _NodeId
from pylive.NetworkXGraphEditor.nx_graph_selection_model import NXGraphSelectionModel
from pylive.NetworkXGraphEditor.nx_network_scene_outlet_to_inlet import NXNetworkScene
from pylive.NetworkXGraphEditor.nx_network_scene_delegate import NXNetworkSceneDelegate

from pylive.NetworkXGraphEditor.nx_node_inspector_view import NXNodeInspectorView

from pylive.components.qt_options_dialog import QOptionDialog
from pylive.utils.unique import make_unique_name

from pylive.utils import qtfactory as Q

from python_graph_model import PythonGraphModel
from pylive.NetworkXGraphEditor.nx_node_inspector_view import NXNodeInspectorView, NXNodeInspectorDelegate

from python_data_viewer import PythonDataViewer

from pylive.QtScriptEditor.script_edit import ScriptEdit



from pylive.QtLiveApp.document_file_link import DocumentFileLink

from dataclasses import dataclass

import yaml





class LivePythonGraphWindow(QWidget):
    definitionsChanged = Signal()

    def __init__(self, parent: QWidget|None=None) -> None:
        super().__init__(parent=parent)

        self._model = PythonGraphModel("main_graph")
        self._selection_model = NXGraphSelectionModel(self._model)
        self._selection_model.selectionChanged.connect(self.onSelectionChanged)
        self.document = QTextDocument()
        self.file_link = DocumentFileLink(self.document)

        ### meubar
        menubar = QMenuBar(self)
        file_menu = self.file_link.createFileMenu()
        menubar.addMenu(file_menu)

        # definition editor
        self.document_viewer = QTextEdit()
        font = self.document_viewer.font()
        font.setFamilies(["monospace", "Operator Mono Book"])
        # font.setPointSize(10)
        font.setWeight(QFont.Weight.Medium)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.document_viewer.setFont(font)

        self.document_viewer.setDocument(self.document)
        self.document_viewer.setReadOnly(True)
        self.definition_editor = ScriptEdit()

        ### graph
        self.graphview = QGraphicsView()
        self.graphview.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.graphview.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
        self.graphview.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.graphview.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.graphview.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        self.graphscene = NXNetworkScene(self._model, self._selection_model, delegate=PythonGraphDelegate())
        self.graphscene.setSelectionModel(self._selection_model)
        self.graphscene.setSceneRect(-9999,-9999,9999*2,9999*2)
        self.graphview.setScene(self.graphscene)
        self.graphscene.installEventFilter(self)

        ### inspector
        self.node_inspector = NXNodeInspectorView(self._model, self._selection_model)
        # self.node_inspector2 = NXNodeInspectorView(self._model, self._selection_model)
        
        ### Data Viewer
        self.dataviewer = PythonDataViewer()
        self.dataviewer.setModel(self._model)
        self.dataviewer.setSelectionModel(self._selection_model)

        #### Layout
        grid_layout = QGridLayout()
        
        grid_layout.setMenuBar(menubar)
        grid_layout.addWidget(self.document_viewer,        0, 0, 2, 1)
        grid_layout.addWidget(self.definition_editor, 0, 1, 2, 1)
        grid_layout.addWidget(self.graphview,         0, 2, 2, 1)
        grid_layout.addWidget(self.node_inspector,    0, 3, 1, 1)
        grid_layout.addWidget(self.dataviewer,        1, 4, 1, 1)
        
        grid_layout.setColumnStretch(0, 50)
        grid_layout.setColumnStretch(1, 50)
        grid_layout.setColumnStretch(2, 50)
        grid_layout.setRowStretch(0, 0)
        grid_layout.setRowStretch(1, 100)
        self.setLayout(grid_layout)
        
        # grid_layout.addWidget(self.node_inspector, 1, 0)
        # splitter.addWidget(leftpane)
        # self.node_inspector.setParent(self.graphview.viewport())
        # splitter.addWidget(self.node_inspector)
        # splitter.addWidget(self.node_inspector2)
        # splitter.addWidget(self.dataviewer)
        # splitter.setSizes([splitter.width()//splitter.count() for idx in range(splitter.count())])
        # main_layout.addWidget(splitter)

        self.definition_editor.textChanged.connect(lambda: 
            self.setDefinitions(self.definition_editor.toPlainText()))
        self.definitionsChanged.connect(self.updateDocument)

    def setDefinitions(self, text):
        self._definitions = text
        self.definitionsChanged.emit()

    def updateDocument(self):
        from textwrap import dedent, indent

        # Ensure PyYAML uses the literal block style for multiline strings
        class BlockString(str):
            ...

        def literal_representer(dumper, data:BlockString):
            return dumper.represent_scalar('tag:yaml.org,2002:str', data.strip(), style='|')

        yaml.add_representer(BlockString, literal_representer)

        # Wrap the string with LiteralString to trigger the custom representation
        data = {
            'definitions': BlockString(self.definition_editor.toPlainText())
        }

        # Dump the YAML
        yaml_output = yaml.dump(data, default_flow_style=False)

        self.document.setPlainText(yaml_output)

    def definitions(self):
        return self._definitions

    def updateWindowTitle(self):
        self.setWindowTitle("LiveGraph - {self.file}")

    def onNodeAttributesChanged(self, node_attributes:dict[Hashable, list[str]]):
        assert self._model
        assert self._selection_model
        for node_id, attributes in node_attributes.items():
            if "_result" in attributes:
                continue
            self._model._invalidate(node_id)

    def onSelectionChanged(self, selected, deselected):
        assert self._model
        assert self._selection_model
        if current_node_id := self._selection_model.currentNode():
            self._model._evaluate(current_node_id)

    # @Slot()
    # def invalidate_selected(self):
    #     selected_nodes = self._selection_model.selectedNodes()
    #     print("invalidate_selected", selected_nodes)
    #     if len(selected_nodes)>0:
    #         current_node_id = sselected_nodes[0]
    #         self._model.invalidate(current_node_id)

    # @Slot()
    # def evaluate_selected(self):
    #     selected_nodes = self._selection_model.selectedNodes()
    #     print("evaluate_selected", selected_nodes)
    #     if len(selected_nodes)>0:
    #         current_node_id = selected_nodes[0]
    #         self._model.evaluate(current_node_id)

    

    def graphmodel(self)->PythonGraphModel:
        return self._model

    def selectionModel(self)->NXGraphSelectionModel:
        return self._selection_model

    def sizeHint(self) -> QSize:
        return QSize(1800, 700)

    def setFunctions(self, functions:dict[str, Callable]):
        self._functions = functions

    def functions(self)->Iterable:
        for name, func in self._functions.items():
            yield name, func

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched == self.graphscene:
            def open_nodes_dialog():
                available_nodes = {key: val for key, val in self.functions()}
                dialog = QOptionDialog(items=[_ for _ in available_nodes.keys()], title="Create Nodes", parent=self.graphview)
                result = dialog.exec()

                if result == QDialog.DialogCode.Accepted:
                    if function_name:=dialog.optionValue():
                        all_nodes = [str(_) for _ in self._model.nodes()]
                        fn = available_nodes[function_name]
                        node_id = self._model.addFunction(fn)
                        
                else:
                    print("cancelled")

            if  event.type() == QEvent.Type.KeyPress and cast(QKeyEvent, event).key() == Qt.Key.Key_Tab:
                open_nodes_dialog()
                return True
            elif event.type() == QEvent.Type.GraphicsSceneMouseDoubleClick:
                open_nodes_dialog()
                return True

        return super().eventFilter(watched, event)


if __name__ == "__main__":
    app = QApplication()
    window = LivePythonGraphWindow()

    def get_available_nodes():
        for name in dir(__builtins__):
            if not name.startswith("_"):
                item = getattr(__builtins__, name)
                if callable(item):
                    yield name, item

        import pathlib
        for name in dir(pathlib):
            if not name.startswith("_"):
                item = getattr(pathlib, name)
                if callable(item):
                    yield name, item


        def sample_function(x:int, y:int)->int:
            return x + y

        yield 'sample_function', sample_function

    from pathlib import Path
    def ls(path=Path.cwd()):
        return [_ for _ in path.iterdir()]

    def read_text(path:Path|str):
        return Path(path).read_text()

    def process_text(text:str):
        return f"processed {text}"

    def print_text(text:str):
        # print("SHOW_TEST:")
        from textwrap import indent
        # print(indent(text, "   |"))

    def write_text(text:str, path:Path):
        pass
        # print(text)

    def forEach(fn:Callable, items:list)->list:
        return [fn(item) for item in items]

    window.setFunctions({fn.__name__:fn for fn in [
        ls, read_text, process_text, print_text, write_text, forEach
    ]})

    # n0 = window._model.addFunction(ls)

    subgraph = PythonGraphModel("process_subgraph")
    proc1 = subgraph.addFunction(process_text)
    proc2 = subgraph.addFunction(process_text)
    subgraph.setInputs({"text": (proc1, "text")} )
    subgraph.setOutput(proc2)

    read_node = window._model.addFunction(read_text, path="index.html")
    process_node1 = window._model.addFunction(process_text)
    write_node = window._model.addFunction(write_text)
    process_node2 = window._model.addFunction(process_text)
    print_node = window._model.addFunction(print_text)
    
    window._model.addEdge(read_node, process_node1, ("out", "text"))
    window._model.addEdge(read_node, process_node2, ("out", "text"))
    window._model.addEdge(process_node1, write_node, ("out", "text"))
    window._model.addEdge(process_node2, print_node, ("out", "text"))

    # window._model.addFunction(subgraph)

    # subgraph
    subgraph1 = window._model.addFunction(subgraph)

    window.graphscene.layout()

    window.show()
    app.exec()
