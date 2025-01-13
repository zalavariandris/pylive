
from random import sample
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from networkx import find_induced_nodes
# from pylive.QtLiveApp.live_script_skeleton import LiveScriptWindow
from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel, NXNetworkModel
from pylive.NetworkXGraphEditor.nx_graph_selection_model import NXGraphSelectionModel
from pylive.NetworkXGraphEditor.nx_network_scene_outlet_to_inlet import NXNetworkScene, NodeId
from pylive.NetworkXGraphEditor.nx_node_inspector_view import NXNodeInspectorView

from pylive.options_dialog import OptionDialog
from pylive.utils.unique import make_unique_name

import inspect
class PythonGraphModel(NXNetworkModel):
    EMPTY = object()
    def addFunction(self, fn:Callable, name:str|None=None):
        assert callable(fn), "Fn {fn}!"
        node_id = make_unique_name(name if name else fn.__name__, [str(n) for n in self.nodes()])
        super().addNode(
            node_id, 
            fn=fn,
            cache=EMPTY
        )
        return node_id

    def getFunction(self, node_id:Hashable)->Callable:
        return cast(Callable, self.getNodeProperty(node_id, "fn"))

    def setArgumentExpression(self, node_id, arg:str, expression:str):
        self.setNodeProperties(node_id, **{arg:expression})
        def invalidate(self, node_id)

    def getArgumentExpression(self, node_id, arg:str)->str:
        return self.getNodeProperty(node_id, arg)

    def arguments(self, node_id)->Iterable[str]:
        fn = self.getNodeProperty(node_id, "fn")
        assert callable(fn), "Node function should have been a callable!"
        sig = inspect.signature(fn)
        for name, paramteter in sig.parameters.items():
            print("param name", name)
            yield name

    def inlets(self, node_id:Hashable, /)->Iterable[str]:
        yield from self.arguments(node_id)

    def outlets(self, n:Hashable, /)->Iterable[str]:
        return ['out']

    def invalidate(self, node_id, recursive=True):
        del self.G.nodes[node_id]['cache'] # todo: NXGraphModel is missing a delete node attribute
        for u, v, _ in self.outEdges(node_id):
            self.invalidate(v)

    def evaluate(self, node_id):
        try:
            return self.getNodeProperty(node_id, 'cache')
        except KeyError:
            fn = self.getFunction()
            for arg_name in self.arguments():
                arg_value = self.inEdges()
            args = self.arguments()
            sources = 

            args.update(sources)

            value = fn(*arguments)
            self.setNodeProperty(node_id, cache=value)
        for u, v, k in self.inEdges(node_id):

        ...





class FunctionInspector(QWidget):
    paramTextChanged = Signal(str, str) #parameter name, editor text
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self._model: NXGraphModel | None = None
        self._selection_model: NXGraphSelectionModel | None = None

        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0,0,0,0)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(0)
        header_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(QLabel("<h2>Node</h2>"))
        main_layout.addLayout(header_layout)

        self.module_label = QLabel("-module-") # eg: pathlib or networkx
        self.kind_label = QLabel("-kind-")   # eg: function, Class, Class.method
        self.name_label = QLabel("-name-")   # eg: map, print, setText...b
        header_layout.addWidget(self.module_label)
        header_layout.addWidget(self.kind_label)
        header_layout.addWidget(self.name_label)

        self.body_layout = QVBoxLayout()
        self.body_layout.setSpacing(0)
        self.body_layout.setContentsMargins(0,0,0,0)
        
        main_layout.addLayout(self.body_layout)

        main_layout.addStretch()

        self.setLayout(main_layout)

    def setFunction(self, fn:Callable|None, argument_expressions:dict[str,str]=dict(), input_nodes:dict[str,object|None]=dict()):
        # clear head
        self.module_label.setText("")
        self.kind_label.setText("")
        self.name_label.setText("")

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

        # clear body
        def clear_layout_recursive(layout):
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    clear_layout_recursive(item.layout())  # This is actual recursion
                del item


        clear_layout_recursive(self.body_layout)

        if fn:
            import inspect
            self.module_label.setText(f"{inspect.getmodule(fn).__name__}")
            self.kind_label.setText(f"{fn.__class__.__name__}")
            self.name_label.setText(f"{fn.__qualname__}")
            params_layout = QFormLayout()
            params_layout.setSpacing(0)
            params_layout.setContentsMargins(0,0,0,0)
            self.body_layout.addWidget(QLabel("<h2>Parameters<h2>"))
            self.body_layout.addLayout(params_layout)

            from pathlib import Path
            
            sig = inspect.signature(fn)
            SENTINEL = object()
            for name, param in sig.parameters.items():
                value = argument_expressions.get(name, SENTINEL)
                match param.kind:
                    case inspect.Parameter.VAR_POSITIONAL:
                        name_label = QLabel("*"+param.name)
                    case inspect.Parameter.VAR_KEYWORD:
                        name_label = QLabel("**"+param.name)
                    case _:
                        name_label = QLabel(""+param.name)

                if param.annotation is not inspect.Parameter.empty:
                    print("param annotation:", param.annotation)
                    name_label.setText(name_label.text() + f":{format_type(param.annotation)}")


                param_editor = QLineEdit()
                if param.default is not inspect.Parameter.empty:
                    param_editor.setPlaceholderText(f"{param.default!r}")
                if value != SENTINEL:
                    param_editor.setText(f"{value!r}")
                param_editor.textChanged.connect(lambda text, param=param: self.paramTextChanged.emit(param.name, text))

                params_layout.addRow(name_label, param_editor)

            import pydoc
            import html
            doc = pydoc.render_doc(fn)

            self.body_layout.addWidget(QLabel("<h2>Help</h2>"))
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setText(doc)
            self.body_layout.addWidget(text_edit)
            # self.body_layout.addWidget(QLabel(f"{doc!s}"))


class LivePythonGraphWindow(QWidget):
    def __init__(self, parent: QWidget|None=None) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle("Live Python function Graph")
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self._model = PythonGraphModel()
        self._selection_model = NXGraphSelectionModel(self._model)
        self.graphview = QGraphicsView()
        self.graphview.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.graphview.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
        self.graphview.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.graphview.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.graphview.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        self.graphscene = NXNetworkScene(self._model, self._selection_model)
        self.graphscene.setSelectionModel(self._selection_model)
        self.graphscene.setSceneRect(-9999,-9999,9999*2,9999*2)
        self.graphview.setScene(self.graphscene)

        self.inspector_panel = QWidget()
        self.inspector_panel.setLayout(QVBoxLayout())
        self.function_inspector = FunctionInspector()
        self.function_inspector.paramTextChanged.connect(lambda param_name, expression: 
            self.graphmodel().setArgumentExpression(self.selectionModel().selectedNodes()[0], param_name, expression))

        self.inspector_panel.layout().addWidget(self.function_inspector)
        self._selection_model.selectionChanged.connect(self.onSelectionChanged)

        self.graphscene.installEventFilter(self)

        splitter = QSplitter()
        splitter.addWidget(self.graphview)
        splitter.addWidget(self.inspector_panel)
        splitter.setSizes([splitter.width()//splitter.count() for idx in range(splitter.count())])
        main_layout.addWidget(splitter)

    def graphmodel(self)->PythonGraphModel:
        return self._model

    def selectionModel(self)->NXGraphSelectionModel:
        return self._selection_model


    def sizeHint(self) -> QSize:
        return QSize(900, 500)

    def onSelectionChanged(self, selected:set[NodeId], deselected:set[NodeId]):
        selected_nodes = self._selection_model.selectedNodes()
        if len(selected_nodes)>0:
            node_id = self._selection_model.selectedNodes()[0]
            fn:Callable = self._model.getFunction(node_id)

            argument_expressions = dict()
            for arg_name in self.graphmodel().arguments(node_id):
                try:
                    expression = self.graphmodel().getArgumentExpression(node_id, arg_name)
                    argument_expressions[arg_name] = expression
                except KeyError:
                    pass
            self.function_inspector.setFunction(fn, argument_expressions=argument_expressions)
        else:
            self.function_inspector.setFunction(None)

    def setNodePropertyEditor(self, param_name, expression, editor):
        ...

    def setNodePropertyModel(self, node_id, param_name, expression):
        ...

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched == self.graphscene:
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

            def open_nodes_dialog():
                available_nodes = {key: val for key, val in get_available_nodes()}
                dialog = OptionDialog(options=[_ for _ in available_nodes.keys()], title="Create Nodes", parent=self.graphview)
                result = dialog.exec()

                if result == QDialog.DialogCode.Accepted:
                    if function_name:=dialog.optionValue():
                        all_nodes = [str(_) for _ in self._model.nodes()]
                        fn = available_nodes[function_name]
                        self._model.addFunction(fn)
                        
                else:
                    print("cancelled")

            if  event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Tab:
                open_nodes_dialog()
                return True
            elif event.type() == QEvent.Type.GraphicsSceneMouseDoubleClick:
                open_nodes_dialog()
                return True

        return super().eventFilter(watched, event)



if __name__ == "__main__":
    app = QApplication()
    window = LivePythonGraphWindow()
    window.show()
    app.exec()
