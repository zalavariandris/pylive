from ast import Call
from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.examples.python_function_graph.graph_model import GraphModel
from pylive.QtScriptEditor.script_edit import ScriptEdit

from pathlib import Path

app = QApplication()
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
from pylive.QtGraphEditor.nx_graph_model import NXGraphModel
from pylive.utils.unique import make_unique_name

import inspect


def is_multi_param(fn: Callable, paramname: str):
    signature = inspect.signature(fn)
    param = signature.parameters[paramname]
    return param.kind == inspect.Parameter.VAR_POSITIONAL


import networkx as nx


def parse_graph_to_script(G: nx.MultiDiGraph) -> str:
    print("parse_graph_to_script")
    import networkx as nx
    import ast

    nodes = nx.topological_sort(G)

    def get_lines(nodes):
        for n in nodes:
            fn = G.nodes[n]["fn"]
            formatted_params = ", ".join(
                [f"{u}" for u, v, k in G.in_edges(n, keys=True)]
            )
            yield f"{n} = {fn.__qualname__ }({formatted_params})"

    script = "\n".join(get_lines(nodes))
    script = "from pathlib import Path\n\n" + script
    return script


def parse_graph_to_ast(G: nx.MultiDiGraph):
    print("parse_graph_to_script")
    import networkx as nx
    import ast

    import_node = ast.ImportFrom(
        module="pathlib", names=[ast.alias(name="Path", asname=None)], level=0
    )

    assignements: list[ast.stmt] = []
    nodes = nx.topological_sort(G)
    for n in nodes:
        assignment = ast.Assign(
            targets=[
                ast.Name(id="cwd1", ctx=ast.Store(), lineno=2, col_offset=0)
            ],
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(
                        id="Path", ctx=ast.Load(), lineno=2, col_offset=8
                    ),
                    attr="cwd",
                    ctx=ast.Load(),
                    lineno=2,
                    col_offset=8,
                ),
                args=[],
                keywords=[],
                lineno=2,
                col_offset=8,
            ),
            lineno=2,
            col_offset=0,
        )
        assignements.append(assignment)

    module = ast.Module(body=[import_node] + assignements, type_ignores=[])


class PythonGraphModel(NXGraphModel):
    @override
    def addEdge(self, u: Hashable, v: Hashable, k: str, **props):
        fn: Callable = self.getNodeProperty(v, "fn")
        IsMultiInlet = is_multi_param(fn, k)
        if not IsMultiInlet:
            edges_to_remove = []
            in_edges = self.G.in_edges(v, keys=True)
            for edge in in_edges:
                if edge[2] == k:
                    edges_to_remove.append(edge)
            for edge in edges_to_remove:
                super().remove_edge(*edge)
            print(
                "IsMultiInlet",
                IsMultiInlet,
                "edges_to_remove:",
                edges_to_remove,
            )

        return super().addEdge(u, v, k, **props)


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

        # menubar
        menubar = QMenuBar(self)
        add_menu = QMenu("add", self)
        for fn in [print, len, Path.cwd, Path.iterdir]:
            create_operator_action = QAction(fn.__qualname__, self)
            create_operator_action.triggered.connect(
                lambda checked, fn=fn: self.create_operator(fn)
            )
            add_menu.addAction(create_operator_action)
        menubar.addMenu(add_menu)
        run_action = menubar.addAction("run")
        run_action.triggered.connect(lambda checked: self.runScript())

        # statusbar
        statusbar = QStatusBar(self)
        statusbar.showMessage("Welcome!")
        statusbar.setSizeGripEnabled(False)

        # create layout
        mainlayout = QVBoxLayout()
        mainlayout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter()
        splitter.addWidget(graphview)
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

        # trigger evaluate
        graphmodel.nodesAdded.connect(self.parseGraph)
        graphmodel.nodesRemoved.connect(self.parseGraph)
        graphmodel.edgesAdded.connect(self.parseGraph)
        graphmodel.edgesRemoved.connect(self.parseGraph)
        self.graphmodel = graphmodel

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
    def parseGraph(self):
        script = parse_graph_to_script(self.graphmodel.G)
        self.result_script_edit.setPlainText(script)

    @Slot()
    def runScript(self):
        script = parse_graph_to_script(self.graphmodel.G)
        self.result_script_edit.setPlainText(script)
        from textwrap import dedent

        exec(dedent(script))

    @Slot(object)
    def create_operator(self, fn: Callable):
        unique_node_id = make_unique_name(
            f"{fn.__name__ }1", self.graphmodel.nodes()
        )
        self.graphmodel.addNode(unique_node_id, fn=fn)

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
        self.graphmodel.addEdge(source_operator, target_operator, paramname)

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
        self.graphmodel.remove_edge(source_operator, target_operator, paramname)

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
                        fn = self.graphmodel.getNodeProperty(n, "fn")
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


window = PythonGraphWindow()

window.show()
app.exec()
