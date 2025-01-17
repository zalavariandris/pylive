from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


from pylive.NetworkXGraphEditor.nx_network_model import NXNetworkModel
from pylive.utils.unique import make_unique_name

"""
node
- attributes:
  -> _fn: Callable
  -> param_name: stored_value
  -> param_name2: stored_value
  -> ...
"""

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