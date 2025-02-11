from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


from pylive.VisualCode_NetworkX.UI.nx_network_model import NXNetworkModel
from pylive.utils.unique import make_unique_name

"""
node
- attributes:
  -> _content: Callable
  -> param_name: stored_value
  -> param_name2: stored_value
  -> ...
"""

import time
import logging
logger = logging.getLogger(__name__)

import networkx as nx
import inspect
class PythonGraphModel(NXNetworkModel):
    def __init__(self, name:str, G:nx.MultiDiGraph|None=None, parent:QObject|None=None):
        super().__init__(G=G, parent=parent)
        self._inputs:dict[str, tuple[Hashable, str]] = dict()
        self._output = None
        self.__name__ = name

    def addFunction(self, fn:Callable, **kwargs):
        assert callable(fn), "Fn {fn}!"
        try:
            callable_name = fn.__name__
        except AttributeError:
            callable_name = fn.__class__.__name__
        node_id = make_unique_name(callable_name, [str(n) for n in self.nodes()])
        super().addNode(
            node_id,
            _content=fn,
            **kwargs
        )
        return node_id

    def function(self, node_id)->Callable:
        func = self.getNodeAttribute(node_id, "_content")
        assert callable(func)
        return func

    def parameters(self, node_id)->Iterable[str]:
        """return a specific node function parameters"""
        fn = self.getNodeAttribute(node_id, "_content")
        assert callable(fn), "Node function should have been a callable!"
        if isinstance(fn, PythonGraphModel):
            subgraph = fn
            for input_name, (node, param) in subgraph._inputs.items():
                yield input_name
        else:
            sig = inspect.signature(fn)
            for name, paramteter in sig.parameters.items():
                yield name

    def cache(self, node_id):
        return self.getNodeAttribute(node_id, "cache")

    def error(self, node_id):
        return self.getNodeAttribute(node_id, "error")

    def inlets(self, node_id:Hashable, /)->Iterable[str]:
        """return all parameters as inlets, so they can be connected"""
        yield from self.parameters(node_id)

    def outlets(self, n:Hashable, /)->Iterable[str]:
        """a python function has a single reeturn value"""
        return ['out']

    def parameterValue(self, node_id:Hashable, param:str)->object|None:
        return self.getNodeAttribute(node_id, param)

    def setParameterValue(self, node_id:Hashable, param:str, value:object|None)->None:
        self.updateNodeAttributes(node_id, **{param: value})

    def deleteParameterValue(self, node_id:Hashable, param:str)->None:
        self.deleteNodeAttribute(node_id, param)

    ### Evaluate graph
    def _invalidate(self, node_id):
        """invalidate the specified node, and its dependents (descendants)"""
        from itertools import chain
        for n in chain([node_id], self.descendants(node_id)):
            try:
                self.deleteNodeAttribute(node_id, "cache")
            except KeyError:
                pass
            try:
                self.deleteNodeAttribute(node_id, "error")
            except KeyError:
                pass

    def _evaluate(self, node_id):
        """evaluate the specified node, and its dependencies (anchestors)"""
        from itertools import chain
        import networkx as nx
        # evaluate graph in topological order
        dependencies = self.anchestors(node_id)
        reverse_subgraph = nx.subgraph(self.G, chain([node_id], dependencies))
        topological_sort = [_ for _ in nx.topological_sort(reverse_subgraph)]
        logger.debug("Evaluate:", topological_sort)
        for i, n in enumerate(topological_sort):
            self.updateNodeAttributes(n, evaluation_order=i)
            ### collect arguments
            arguments_by_name:dict[str, object|None] = dict()
            ## from source nodes
            for u, v, (o, i) in self.inEdges(n): 
                param_name:str = i
                source_node:Hashable = u
                source_cache = self.getNodeAttribute(u, "cache")
                arguments_by_name[param_name] = source_cache

            ## from node parameters
            for attr in self.parameters(n):
                if attr not in arguments_by_name:
                    try:
                        value = self.parameterValue(n, attr)
                        arguments_by_name[attr] = value
                    except KeyError:
                        pass # no value was set

            ### call function with arguments_by_name
            fn = self.getNodeAttribute(n, "_content")
            assert callable(fn)
            sig = inspect.signature(fn)
            pos_args = []
            kw_args = {}
            for param_name, param in sig.parameters.items():
                if param.kind == inspect.Parameter.POSITIONAL_ONLY:
                    pos_args.append(arguments_by_name[param_name])
                else:
                    if param_name in arguments_by_name:
                        kw_args[param_name] = arguments_by_name[param_name]

            try:
                # logger.debug(pos_args, kw_args)
                # logger.debug("- call:", fn.__name__+"("+",".join(pos_args+[f"{param}={value}" for param, value in kw_args.items()])+")")
                cache = fn(*pos_args, **kw_args)
                # print("CACHE: ", cache)
                self.updateNodeAttributes(n, cache=cache)
                try:
                    self.deleteNodeAttribute(n, 'error')
                except KeyError:
                    pass
            except Exception as err:
                try:
                    self.deleteNodeAttribute(n, 'cache')
                except KeyError:
                    pass
                self.updateNodeAttributes(n, error=err)
                break

    def setInputs(self, inputs:dict[str, tuple[Hashable, str]]):
        self._inputs = inputs

    outputChanged = Signal()

    def setOutput(self, node_id:Hashable|None):
        if node_id not in self.G.nodes:
            raise KeyError("{node_id} is not in the graph")
            return None
        self._output = node_id

    def output(self)->Hashable|None:
        return self._output

    def __call__(self, *args, **kwargs):
        return self._evaluate(self._output)
            