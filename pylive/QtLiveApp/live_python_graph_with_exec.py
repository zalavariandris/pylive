from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

# from pylive.QtLiveApp.live_script_skeleton import LiveScriptWindow
from pylive.NetworkXGraphEditor.nx_graph_shapes import BaseNodeItem
from pylive.NetworkXGraphEditor.nx_network_model import NXNetworkModel
from pylive.NetworkXGraphEditor.nx_network_model import _NodeId
from pylive.NetworkXGraphEditor.nx_graph_selection_model import NXGraphSelectionModel
from pylive.NetworkXGraphEditor.nx_network_scene_outlet_to_inlet import NXNetworkScene, StandardNetworkDelegte, StandardNodeItem
from pylive.NetworkXGraphEditor.nx_node_inspector_view import NXNodeInspectorView

from pylive.options_dialog import OptionDialog
from pylive.utils.unique import make_unique_name

from pylive.utils import qtfactory as Q

class PythonGraphDelegate(StandardNetworkDelegte):
    @override
    def createPropertyEditor(self, parent_node: QGraphicsItem, model: NXNetworkModel, node_id: _NodeId, prop: str)->QGraphicsItem|None:
        assert isinstance(model, PythonGraphModel)
        if func:=model.getNodeFunction(node_id):
            if func == forEach:
                print("itr a foreach")
        return super().createPropertyEditor(parent_node, model, node_id, prop)

    def setNodePropertyEditor(self, model: NXNetworkModel, node_id:Hashable, prop:str, editor: QGraphicsItem):
        # value = model.getNodeProperty(node_id, prop)
        # editor = cast(QGraphicsTextItem, editor)
        # editor.setPlainText(f"{prop}: {value}")
        if prop=="fn":
            fn = model.getNodeProperty(node_id, prop)
            print(f"its a foreach with {fn}")

        super().setNodePropertyEditor(model, node_id, prop, editor)

    # def setNodePropertyModel(self, model:NXNetworkModel, node_id:Hashable, prop:str, editor: QGraphicsItem):
    #     ...


import inspect
class PythonGraphModel(NXNetworkModel):
    EMPTY = object()
    def addFunction(self, fn:Callable, **kwargs):
        assert callable(fn), "Fn {fn}!"
        node_id = make_unique_name(fn.__name__, [str(n) for n in self.nodes()])
        super().addNode(
            node_id, 
            _fn=fn,
            **kwargs
        )
        return node_id

    def addExpression(self, expression:str, name:str|None=None):
        raise NotImplementedError

    def setNodeFunction(self, node_id:Hashable, fn:Callable)->Callable:
        return cast(Callable, self.updateNodeProperties(node_id, _fn=fn))

    def getNodeFunction(self, node_id:Hashable)->Callable:
        return cast(Callable, self.getNodeProperty(node_id, "_fn"))

    def getNodeResult(self, node_id:Hashable)->object|None:
        return self.getNodeProperty(node_id, "_result")

    def setArgumentExpression(self, node_id, arg:str, expression:str):
        self.updateNodeProperties(node_id, **{arg:expression})
        # self.invalidate(node_id)

    def getArgumentExpression(self, node_id, arg:str)->str:
        expression = self.getNodeProperty(node_id, arg)
        assert isinstance(expression, str)
        return expression

    def arguments(self, node_id)->Iterable[str]:
        fn = self.getNodeFunction(node_id)
        assert callable(fn), "Node function should have been a callable!"
        sig = inspect.signature(fn)
        for name, paramteter in sig.parameters.items():
            yield name

    def inlets(self, node_id:Hashable, /)->Iterable[str]:
        yield from self.arguments(node_id)

    def outlets(self, n:Hashable, /)->Iterable[str]:
        return ['out']

    def invalidate(self, node_id, recursive=True):
        self.deleteNodeProperty(node_id, "_result")
        if recursive:
            for u, v, k in self.outEdges(node_id):
                self.invalidate(v)

    def evaluate(self, node_id):
        import networkx as nx
        from pylive.utils.graph import dependencies, dependents

        dependencies = dependencies(self.G, node_id)
        topological_dependencies = nx.topological_sort(nx.subgraph(self.G, dependencies))

        for i, n in enumerate(topological_dependencies):
            self.updateNodeProperties(n, idx=i)

        def execute(fn:Callable):
            return fn()
        fn = self.getNodeFunction(node_id)
        result = execute(fn)
        self.updateNodeProperties(node_id, result=result)


class LivePythonGraphWindow(QWidget):
    def __init__(self, parent: QWidget|None=None) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle("Live Python function Graph")

        self._model = PythonGraphModel()
        self._selection_model = NXGraphSelectionModel(self._model)

        ### create and layout widgets
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        ### menu
        menubar = QMenuBar()
        evaluate_action = QAction("evaluate", self)
        evaluate_action.triggered.connect(lambda: self.evaluate_selected())
        menubar.addAction(evaluate_action)
        invalidate_action = QAction("invalidate", self)
        invalidate_action.triggered.connect(lambda: self.invalidate_selected())
        menubar.addAction(invalidate_action)
        main_layout.setMenuBar(menubar)

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
        self.inspector_panel = QWidget()
        self.inspector_panel.setLayout(QVBoxLayout())
        self.function_inspector = FunctionInspectorView(self._model, self._selection_model)
        self.function_inspector.paramTextChanged.connect(lambda param_name, expression: 
            self.graphmodel().setArgumentExpression(self.selectionModel().currentNode(), param_name, expression))

        self.inspector_panel.layout().addWidget(self.function_inspector)
        
        ### Previewer
        self.dataviewer = DataViewer(self._model, self._selection_model)

        ### main splitter
        splitter = QSplitter()
        splitter.addWidget(self.graphview)
        splitter.addWidget(self.inspector_panel)
        splitter.addWidget(self.dataviewer)
        splitter.setSizes([splitter.width()//splitter.count() for idx in range(splitter.count())])
        main_layout.addWidget(splitter)

    @Slot()
    def evaluate_selected(self):
        selected_nodes = self._selection_model.selectedNodes()
        print("evaluate_selected", selected_nodes)
        if len(selected_nodes)>0:
            current_node_id = selected_nodes[0]
            self._model.evaluate(current_node_id)

    @Slot()
    def invalidate_selected(self):
        selected_nodes = self._selection_model.selectedNodes()
        print("invalidate_selected", selected_nodes)
        if len(selected_nodes)>0:
            current_node_id = selected_nodes[0]
            self._model.invalidate(current_node_id)

    def graphmodel(self)->PythonGraphModel:
        return self._model

    def selectionModel(self)->NXGraphSelectionModel:
        return self._selection_model

    def sizeHint(self) -> QSize:
        return QSize(900, 500)

    def setFunctions(self, functions:dict[str, Callable]):
        self._functions = functions

    def functions(self)->Iterable:
        for name, func in self._functions.items():
            yield name, func

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched == self.graphscene:
            def open_nodes_dialog():
                available_nodes = {key: val for key, val in self.functions()}
                dialog = OptionDialog(options=[_ for _ in available_nodes.keys()], title="Create Nodes", parent=self.graphview)
                result = dialog.exec()

                if result == QDialog.DialogCode.Accepted:
                    if function_name:=dialog.optionValue():
                        all_nodes = [str(_) for _ in self._model.nodes()]
                        fn = available_nodes[function_name]
                        self._model.addFunction(fn)
                        
                else:
                    print("cancelled")

            if  event.type() == QEvent.Type.KeyPress and cast(QKeyEvent, event).key() == Qt.Key.Key_Tab:
                open_nodes_dialog()
                return True
            elif event.type() == QEvent.Type.GraphicsSceneMouseDoubleClick:
                open_nodes_dialog()
                return True

        return super().eventFilter(watched, event)


class FunctionInspectorView(QWidget):
    paramTextChanged = Signal(str, str) #parameter name, editor text
    def __init__(self, model:PythonGraphModel, selectionmodel:NXGraphSelectionModel, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._model = None
        self._selection_model = None

        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0,0,0,0)

        self.header_layout = QVBoxLayout()
        self.header_layout.setSpacing(0)
        self.header_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(QLabel("<h4>Node</h4>"))
        main_layout.addLayout(self.header_layout)

        self.body_layout = QVBoxLayout()
        self.body_layout.setSpacing(0)
        self.body_layout.setContentsMargins(0,0,0,0)
        
        main_layout.addLayout(self.body_layout)

        main_layout.addStretch()

        self.setLayout(main_layout)

        ### setup
        self.setModel(model)
        self.setSelectionModel(selectionmodel)

    def setModel(self, model:PythonGraphModel):
        self._model = model

    def model(self):
        return self._model

    def setSelectionModel(self, selectionmodel:NXGraphSelectionModel):
        self._selection_model = selectionmodel
        selectionmodel.selectionChanged.connect(self.onSelectionChanged)

    def selectionModel(self):
        return self._selection_model

    def onSelectionChanged(self, selected, deselected):
        assert self._model
        assert self._selection_model
        node_id = self._selection_model.currentNode()
        if node_id:
            func = self._model.getNodeFunction(node_id)
            self._showFunction(func)
        else:
            self.clear()

    def clear(self):
        def clear_layout_recursive(layout):
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    clear_layout_recursive(item.layout())  # This is actual recursion
                del item

        clear_layout_recursive(self.header_layout)
        clear_layout_recursive(self.body_layout)

    def _showFunction(self, fn:Callable|None, argument_expressions:dict[str,str]=dict(), input_nodes:dict[str,object|None]=dict()):
        # clear head
        self.clear()

        if fn:
            import inspect
            try:
                module_label = Q.label(f"{inspect.getmodule(fn).__name__}")
            except:
                module_label = Q.label(f"cant find module for fn: {fn}")
            kind_label = Q.label(f"{fn.__class__.__name__}")
            name_label = Q.label(f"{fn.__qualname__}")

            self.header_layout.addWidget(module_label)
            self.header_layout.addWidget(kind_label)
            self.header_layout.addWidget(name_label)

            ### Parametere  
            def format_param(param)->str:
                text = ""
                match param.kind:
                    case inspect.Parameter.VAR_POSITIONAL:
                        text = "*"+param.name
                    case inspect.Parameter.VAR_KEYWORD:
                        text = "**"+param.name
                    case _:
                        text = param.name

                if param.annotation is not inspect.Parameter.empty:
                    def format_type(annotation)->str:
                        """Helper function to format type annotations as readable strings."""
                        if hasattr(annotation, '__name__'):  # For built-in types like int, float
                            return annotation.__name__
                        elif hasattr(annotation, '__origin__'):  # For generic types like List, Dict
                            origin = annotation.__origin__
                            args = ", ".join(format_type(arg) for arg in annotation.__args__) if annotation.__args__ else ""
                            return f"{origin.__name__}[{args}]" if args else origin.__name__
                        else:
                            return str(annotation)  # Fallback for unusual cases
                    print("param annotation:", param.annotation)
                    text += f":{format_type(param.annotation)}"
                return text

            sig = inspect.signature(fn)
            SENTINEL = object()
            def parameter_to_row(param:inspect.Parameter)->tuple[QLabel, QLineEdit]:
                assert self._model
                assert self._selection_model
                name_label = Q.label(format_param(param))
                node_id = self._selection_model.currentNode()
                try:
                    value = self._model.getNodeProperty(node_id, param.name)
                except:
                    value = ""
                param_editor = Q.lineedit(
                    f"{value!r}" if value !=SENTINEL else "", 
                    placeholder=f"{param.default!r}" if param.default is not inspect.Parameter.empty else "",
                    onTextChanged=lambda text, param=param.name: self.onParameterChanged(param, text)
                )
                return name_label, param_editor

            params_layout = Q.formlayout(*map(parameter_to_row, sig.parameters.values()))
            self.body_layout.addWidget(Q.label("<h2>Parameters<h2>"))
            self.body_layout.addLayout(params_layout)

            ### HELP
            import pydoc
            import html
            doc = pydoc.render_doc(fn)
            self.body_layout.addWidget(QLabel("<h2>Help</h2>"))
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setText(doc)
            self.body_layout.addWidget(text_edit)

    def onParameterChanged(self, param_name:str, text:str):
        print("on param changed")
        assert self._model
        assert self._selection_model
        node_id = self._selection_model.currentNode()
        self._model.updateNodeProperties(node_id, **{param_name: text})


class DataViewer(QWidget):
    def __init__(self, model:PythonGraphModel, selectionmodel:NXGraphSelectionModel, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._model = None
        self._selection_model = None

        main_layout = QVBoxLayout()
        self._label = QLabel()
        self._label.setWordWrap(True)
        main_layout.addWidget(self._label)
        self.setLayout(main_layout)

        self.setModel(model)
        self.setSelectionModel(selectionmodel)

    def setModel(self, model:PythonGraphModel):
        if model:
            @model.nodesPropertiesChanged.connect
            def _(changes):
                assert self._selection_model
                if current_node_id:=self._selection_model.currentNode():
                    if current_node_id in changes.keys():
                        self.showNode(current_node_id)
        self._model = model

    def model(self):
        return self._model

    def setSelectionModel(self, selectionmodel:NXGraphSelectionModel):
        if selectionmodel:
            @selectionmodel.selectionChanged.connect
            def _(selected, deselected):
                assert self._selection_model
                self.showNode(self._selection_model.currentNode())

        self._selection_model = selectionmodel

    def selectionModel(self):
        return self._selection_model

    @Slot()
    def showNode(self, node_id:Hashable|None):
        assert self._model
        assert self._selection_model

        if node_id := self._selection_model.currentNode():
            try:
                result = self._model.getNodeResult(node_id)
                match result:
                    case list():
                        self._label.setText(f"{result}")
                    case _:
                        self._label.setText(f"{result}")
            except Exception as err:
                self._label.setText(f"{err}")
        else:
            self._label.setText(f"-no selection-")



if __name__ == "__main__":
    import mypy
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

    def read_text(path:Path):
        return path.read_text()

    def process_text(text:str):
        return f"processed {text}"

    def show_text(text:str):
        print(text)

    def write_text(text:str, path:Path):
        print(text)

    def forEach(fn:Callable, items:list)->list:
        return [fn(item) for item in items]

    window.setFunctions({
        'read': read_text,
        'process_text': process_text,
        'write_text': write_text,
        # 'forEach': forEach
    })

    # n0 = window._model.addFunction(ls)

    n1 = window._model.addFunction(read_text, path="index.html")
    n2 = window._model.addFunction(process_text)
    n3 = window._model.addFunction(show_text)
    n4 = window._model.addFunction(write_text)
    window._model.addEdge(n1, n2, ("out", "text"))
    window._model.addEdge(n2, n3, ("out", "text"))
    window._model.addEdge(n2, n4, ("out", "text"))
    window.graphscene.layout()

    window.show()
    app.exec()
