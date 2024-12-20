from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


from pylive.QtGraphEditor.nx_graph_model import NXGraphModel
import networkx as nx
import inspect


def is_multi_param(fn: Callable, paramname: str) -> bool:
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
                [f"{u}" for u, v, k in G.in_edges(n, keys=True)]  # type: ignore
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
    def __init__(self, parent: QObject | None = None):
        super().__init__(G=nx.MultiDiGraph(), parent=parent)
        self._output_operator: Hashable | None = None

    def output(self) -> Hashable:
        return self._output_operator

    def setOutput(self, n: Hashable):
        if n not in self.nodes():
            raise KeyError(f"Operator '{n}' is not part of this graph!")

        self._output_operator = n

    @override
    def addEdge(self, u: Hashable, v: Hashable, k: str, **props):  # type: ignore
        """connect operator to parameter
        @u: source operator
        @v: target operator
        @k: target parameter name
        this method is overloaded, so k must be set"""

        if u not in self.nodes() or v not in self.nodes():
            raise KeyError("Nodes does not exist")

        # remove currently connected edges if parameter
        # kind is not VAR_POSITIONAL (*args)
        fn: Callable = self.getNodeProperty(v, "fn")
        IsMultiInlet = is_multi_param(fn, k)
        if not IsMultiInlet:
            edges_to_remove = []
            in_edges = self.in_edges(v)
            for edge in in_edges:
                if edge[2] == k:
                    edges_to_remove.append(edge)
            for edge in edges_to_remove:
                super().remove_edge(*edge)

        super().addEdge(u, v, k, **props)

    @override
    def addNode(self, n: Hashable, fn: Callable, /):
        """add new operator
        this method will set _arguments and _result node properties to default.
        _arguments is 'dict()''
        _result is 'None'
        Anytime the graph is evaluated by calling it, the attributes for each
        affected node will be updated.
        """
        if n in self.G.nodes:
            raise ValueError(
                f"Node '{n}' is already in the graph. All nodes must be a unique!"
            )
        super().addNode(n, fn=fn, _arguments={}, _result=None)

    def sources(
        self, name: Hashable, prop: str | None = None
    ) -> Iterable[Hashable]:
        for u, v, k in self.G.in_edges(n, keys=True):
            if prop is None or k == prop:
                yield u

    def isConnected(self, n: Hashable, propname: str) -> bool:
        for u, v, k in self.G.in_edges(n, keys=True):
            if k == prop:
                return True
        return False

    def getParamValue(
        self, n, paramname
    ) -> object | List[object] | dict[str, object]:
        arguments = self.getNodeProperty("_arguments")
        assert isinstance(arguments, dict)
        return arguments[paramname]

    def _getParamValueFromSource(self, n, paramname):
        fn = self.getNodeProperty(n, "fn")
        sig = inspect.signature(fn)
        param = sig.parameters[paramname]
        # docs: https://docs.python.org/3/library/inspect.html#inspect.Parameter.kind
        match param.kind:
            case inspect.Parameter.POSITIONAL_ONLY:
                return [
                    self.getNodeProperty(u, "result")
                    for u in self.sources(n, param.name)
                ][0]

            case inspect.Parameter.POSITIONAL_OR_KEYWORD | inspect.Parameter.KEYWORD_ONLY:
                return [
                    self.getNodeProperty(u, "result")
                    for u in self.sources(n, param.name)
                ][0]

            case inspect.Parameter.VAR_POSITIONAL:  # *args
                return [
                    self.getNodeProperty(u, "result")
                    for u in self.sources(n, param.name)
                ]

            case inspect.Parameter.VAR_KEYWORD:  # **kwargs
                return [
                    self.getNodeProperty(u, "result")
                    for u in self.sources(n, param.name)
                ]

    def setNodeProperties(self, n, **props):
        if "_arguments" in props or "_result" in props:
            raise KeyError(
                "'_arguments' and '_result' are protected properties!"
            )
        else:
            super().setNodeProperties(n, **props)

    def __call__(self) -> Exception | object | None:
        print("PythonGraphModel->call")
        if not self._output_operator:
            return
        """evalute the graph from the output operator"""
        nodes = nx.topological_sort(self.G)

        for n in nodes:
            fn = self.getNodeProperty(n, "fn")
            sig = inspect.signature(fn)

            # collect arguments
            args = list()
            kwargs = dict()
            for param in sig.parameters.values():
                value = self.getParamValue(n, param.name, self._cache)
                # get value from the nodes or properties
                match param.kind:
                    # docs: https://docs.python.org/3/library/inspect.html#inspect.Parameter.kind
                    case inspect.Parameter.POSITIONAL_ONLY:
                        args.append(value)
                    case inspect.Parameter.POSITIONAL_OR_KEYWORD | inspect.Parameter.KEYWORD_ONLY:
                        kwargs[param.name] = value

                    case inspect.Parameter.VAR_POSITIONAL:  # *args
                        assert isinstance(value, list)
                        args += value

                    case inspect.Parameter.VAR_KEYWORD:  # **kwargs
                        assert isinstance(value, dict)
                        for keyword in value.keys():
                            # Note: could use the update method.
                            kwargs[keyword] = value[keyword]
            try:
                self._cache[n] = fn(*args, **kwargs)
            except Exception as err:
                return err

        result = self._cache[self._output_operator]
        print("  output:{self._output_operator}->{result}")
        return result
