from ast import Call, arguments
from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.examples.python_function_graph.graph_model import GraphModel
from pylive.QtScriptEditor.script_edit import ScriptEdit

from pathlib import Path


from pylive.QtGraphEditor.dag_graph_graphics_scene import (
    DAGScene,
    EdgeWidget,
    NodeWidget,
    InletWidget,
    OutletWidget,
)
from pylive.QtGraphEditor.infinite_graphicsview_optimized import (
    InfiniteGraphicsView,
)

from pylive.QtGraphEditor.nx_graph_selection_model import NXGraphSelectionModel
from pylive.utils.unique import make_unique_name

#########
# UTILS #
#########
import inspect


#########
# MODEL #
#########
app = QApplication()

from pylive.examples.python_function_graph.python_graph_model import (
    PythonGraphModel,
)


#########
# VIEWS #
#########
class OperatorInspectorView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self._model = PythonGraphModel()

        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)

    def setModel(self, model: PythonGraphModel):
        self._model = model

    def model(self):
        return self._model

    def setSelectionModel(self, selectionmodel: NXGraphSelectionModel):
        selectionmodel.modelChanged.connect(self.handleModelChanged)
        selectionmodel.selectionChanged.connect(self.handleSelectionChanged)
        self._selectionModel = selectionmodel

    def handleModelChanged(self, model: PythonGraphModel):
        ...

    def handleSelectionChanged(
        self, selected: set[Hashable], deselected: set[Hashable]
    ):
        if len(self._selectionModel.selectedNodes()) > 0:
            currentNode = self._selectionModel.selectedNodes()[0]
            layout = cast(QBoxLayout, self.layout())
            # clear inspector
            self.clear()

            # add heading
            label = QLabel(f"{currentNode}")
            layout.addWidget(label)

            # add properties
            fn = self._model.getNodeProperty(currentNode, "fn")
            sig = inspect.signature(fn)
            for param in sig.parameters.values():
                value = self.model().getParamValue(currentNode, param.name)
                param_label = QLabel(f"{param.name}: {value}")

                layout.addWidget(param_label)
            layout.addStretch()

        else:
            self.clear()

    def clear(self):
        while self.layout().count() > 0:
            layoutItem = self.layout().takeAt(0)
            if widget := layoutItem.widget():
                widget.deleteLater()

    def selectionModel(self):
        return self._selectionModel

    def widgetForValue(self, value: object | None):
        match value:
            case str():
                ...
            case int(), float(), complex():
                ...
            case list(), tuple(), range():
                ...
            case dict():
                ...
            case set(), frozenset():
                ...
            case bool():
                ...
            case bytes(), bytearray(), memoryview():
                ...
            case None:
                ...
            case _:
                return QLabel(f"{value}")


class PythonGraphWindow(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        ### Setup widgets ###
        self.setWindowTitle("Python Graph")

        # graphview
        graphview = InfiniteGraphicsView()
        dagscene = DAGScene()
        graphview.setScene(dagscene)
        self.dagscene = dagscene

        # scriptview
        result_script_edit = ScriptEdit()
        result_script_edit.setReadOnly(True)
        self.result_script_edit = result_script_edit

        # inspector
        inspector = OperatorInspectorView(parent=self)
        self.inspector = inspector

        # menubar
        menubar = QMenuBar(self)
        add_menu = QMenu("add", self)
        for fn in [print, len, Path, Path.cwd, Path.iterdir]:
            create_operator_action = QAction(fn.__qualname__, self)
            create_operator_action.triggered.connect(
                lambda checked, fn=fn: self.createOperator(fn)
            )
            add_menu.addAction(create_operator_action)
        menubar.addMenu(add_menu)
        run_action = menubar.addAction("run")
        run_action.triggered.connect(lambda checked: self.evaluateGraph())

        # statusbar
        statusbar = QStatusBar(self)
        statusbar.showMessage("Welcome!")
        statusbar.setSizeGripEnabled(False)

        # create layout
        mainlayout = QVBoxLayout()
        mainlayout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter()
        splitter.addWidget(graphview)
        splitter.addWidget(inspector)
        splitter.addWidget(result_script_edit)
        splitter.setSizes(
            [
                splitter.width() // splitter.count()
                for i in range(splitter.count())
            ]
        )
        mainlayout.addWidget(splitter)
        mainlayout.setMenuBar(menubar)
        mainlayout.addWidget(statusbar)
        self.setLayout(mainlayout)

        #### create and bind models ###
        # graphmodel
        graphmodel = PythonGraphModel()
        graphmodel.nodesAdded.connect(self.handleNodesAdded)
        graphmodel.nodesPropertiesChanged.connect(
            self.handleNodesPropertiesChanged
        )
        graphmodel.nodesAboutToBeRemoved.connect(self.handleNodesRemoved)

        graphmodel.edgesAdded.connect(self.handleEdgesAdded)
        graphmodel.edgesPropertiesChanged.connect(
            self.handleEdgesPropertiesChanged
        )
        graphmodel.edgesAboutToBeRemoved.connect(self.handleEdgesRemoved)

        # selection model
        selectionmodel = NXGraphSelectionModel()
        selectionmodel.setModel(graphmodel)

        @dagscene.selectionChanged.connect
        def on_dagscene_selection_changed():
            print("dagscene->selectionChanged")
            selected_nodes = [
                self._widget_to_operator[widget]
                for widget in dagscene.selectedItems()
                if isinstance(widget, NodeWidget)
            ]
            print("  -", selected_nodes)
            selectionmodel.setSelectedNodes(selected_nodes)

        selectionmodel.selectionChanged.connect(self.handleSelectionChanged)

        # trigger evaluate
        graphmodel.nodesAdded.connect(self.evaluateGraph)
        graphmodel.nodesRemoved.connect(self.evaluateGraph)
        graphmodel.edgesAdded.connect(self.evaluateGraph)
        graphmodel.edgesRemoved.connect(self.evaluateGraph)
        self._graphmodel = graphmodel

        inspector.setModel(graphmodel)
        inspector.setSelectionModel(selectionmodel)

        # widget model mappings
        self._operator_to_widget: dict[Hashable, NodeWidget] = dict()
        self._widget_to_operator: dict[NodeWidget, Hashable] = dict()

        self._edge_to_widget: dict[
            Tuple[Hashable, Hashable, str], EdgeWidget
        ] = dict()
        self._widget_to_edge: dict[
            EdgeWidget, Tuple[Hashable, Hashable, str]
        ] = dict()

        self._param_to_widget: dict[Tuple[Hashable, str], InletWidget] = dict()
        self._widget_to_param: dict[InletWidget, Tuple[Hashable, str]] = dict()

        self._return_to_widget: dict[Hashable, OutletWidget] = dict()
        self._widget_to_return: dict[OutletWidget, Hashable] = dict()

        # bind view
        dagscene.connected.connect(self.onConnect)
        dagscene.disconnected.connect(self.onDisconnect)

    @Slot()
    def parseGraphToScript(self):
        script = parse_graph_to_script(self._graphmodel.G)
        self.result_script_edit.setPlainText(script)

    @Slot()
    def evaluateGraph(self):
        result = self._graphmodel()
        print("graphEvaluated:", result)

    @Slot(object)
    def createOperator(self, fn: Callable):
        unique_node_id = make_unique_name(
            f"{fn.__name__ }1", self._graphmodel.nodes()
        )
        self._graphmodel.addNode(unique_node_id, fn=fn)

    @Slot(EdgeWidget)
    def onConnect(self, edge: EdgeWidget):
        """called when pins are connected by the widget"""
        outlet = edge.sourceOutlet()
        inlet = edge.targetInlet()

        assert outlet and inlet
        self.dagscene.removeEdge(edge)
        source_operator = self._widget_to_return[outlet]
        target_operator, paramname = self._widget_to_param[inlet]
        print(f"connected: {source_operator} -> {target_operator}.{paramname}")
        self._graphmodel.addEdge(source_operator, target_operator, paramname)

    @Slot(EdgeWidget)
    def onDisconnect(self, edge: EdgeWidget):
        """called when pins are disconnected by the widget,
        right before the edge is destroyed"""
        outlet = edge.sourceOutlet()
        inlet = edge.targetInlet()
        assert outlet and inlet

        source_operator = self._widget_to_return[outlet]
        target_operator, paramname = self._widget_to_param[inlet]
        print(
            f"disconnected: {source_operator} -> {target_operator}.{paramname}"
        )
        self._graphmodel.remove_edge(
            source_operator, target_operator, paramname
        )

    @Slot(list)
    def handleNodesAdded(self, nodes: List[Hashable]):
        print("nodes added")
        for n in nodes:
            widget = NodeWidget(title=f"{n}")
            self.dagscene.addNode(widget)
            self._operator_to_widget[n] = widget
            self._widget_to_operator[widget] = n

    @Slot(list)
    def handleNodesRemoved(self, nodes: List[Hashable]):
        for n in nodes:
            widget = self._operator_to_widget[n]
            self.dagscene.removeNode(widget)
            del self._operator_to_widget[n]
            del self._widget_to_operator[widget]

    @Slot(dict)
    def handleNodesPropertiesChanged(
        self, change: dict[Hashable, dict[str, object | None]]
    ):
        print("nodes changed:", change)
        for n, props in change.items():
            node_widget = cast(NodeWidget, self._operator_to_widget[n])
            for prop, value in props.items():
                match prop:
                    case "fn":
                        fn = self._graphmodel.getNodeProperty(n, "fn")
                        sig = inspect.signature(fn)
                        for param in sig.parameters.values():
                            inlet_widget = InletWidget(param.name)
                            node_widget.addInlet(inlet_widget)
                            self._param_to_widget[
                                (n, param.name)
                            ] = inlet_widget
                            self._widget_to_param[inlet_widget] = (
                                n,
                                param.name,
                            )
                        outlet_widget = OutletWidget("out")
                        node_widget.addOutlet(outlet_widget)
                        self._return_to_widget[n] = outlet_widget
                        self._widget_to_return[outlet_widget] = n

    @Slot(list)
    def handleEdgesAdded(self, edges: List[Tuple[Hashable, Hashable, str]]):
        print("edges added", edges)
        for u, v, k in edges:
            paramname = k
            outlet_widget = self._return_to_widget[u]
            inlet_widget = self._param_to_widget[(v, paramname)]
            edge_widget = EdgeWidget(outlet_widget, inlet_widget)
            edge_widget.setLabelText(f"{paramname}")
            self.dagscene.addEdge(edge_widget)
            self._edge_to_widget[(u, v, k)] = edge_widget
            self._widget_to_edge[edge_widget] = (u, v, k)

    @Slot(list)
    def handleEdgesRemoved(self, edges: List[Tuple[Hashable, Hashable, str]]):
        print("edges removed", edges)
        for u, v, k in edges:
            paramname = k
            edge_widget = self._edge_to_widget[u, v, k]
            self.dagscene.removeEdge(edge_widget)
            del self._edge_to_widget[(u, v, k)]
            del self._widget_to_edge[edge_widget]

    @Slot(dict)
    def handleEdgesPropertiesChanged(
        self, change: dict[Hashable, dict[str, object | None]]
    ):
        print("edges changed:", change)

    @Slot(set, set)
    def handleSelectionChanged(
        self, selected: set[Hashable], deselected: set[Hashable]
    ):
        selected_widgets = [self._operator_to_widget[n] for n in selected]
        deselected_widgets = [self._operator_to_widget[n] for n in deselected]
        self.dagscene.blockSignals(True)
        for widget in selected_widgets:
            widget.setSelected(True)

        for widget in deselected_widgets:
            widget.setSelected(False)
        self.dagscene.blockSignals(False)
        self.dagscene.selectionChanged.emit()


window = PythonGraphWindow()
window.show()
app.exec()
