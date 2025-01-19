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

    def parameters(self, node_id)->Iterable[str]:
        """return a specific node function parameters"""
        fn = self.getNodeAttribute(node_id, "_fn")
        assert callable(fn), "Node function should have been a callable!"
        sig = inspect.signature(fn)
        for name, paramteter in sig.parameters.items():
            yield name

    def result(self, node_id):
        return self.getNodeAttribute(node_id, "result")

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

    def delParameterValue(self, node_id:Hashable, param:str)->None:
        self.deleteNodeAttribute(node_id, param)
    
    ### Evaluate graph
    def invalidate(self, node_id, recursive=True):
        try:
            self.deleteNodeAttribute(node_id, "result")
        except KeyError:
            pass
        try:
            self.deleteNodeAttribute(node_id, "error")
        except KeyError:
            pass
        if recursive:
            for u, v, k in self.outEdges(node_id):
                self.invalidate(v)

    def evaluate(self, node_id):
        import networkx as nx
        from pylive.utils.graph import dependencies, dependents

        # evaluate graph in topological order
        dependencies = dependencies(self.G, node_id)
        topological_dependencies = [_ for _ in nx.topological_sort(nx.subgraph(self.G, dependencies))]
        print(topological_dependencies)
        for i, n in enumerate(topological_dependencies):
            self.updateNodeAttributes(n, evaluation_order=i)
            ### collect arguments
            arguments_by_name:dict[str, object|None] = dict()
            ## from source nodes
            for u, v, (o, i) in self.inEdges(n): 
                param_name:str = i
                source_node:Hashable = u
                source_result = self.getNodeAttribute(u, "result")
                arguments_by_name[param_name] = source_node

            ## from node parameters
            for attr in self.parameters(n):
                if attr not in arguments_by_name:
                    try:
                        value = self.parameterValue(n, attr)
                        arguments_by_name[attr] = value
                    except KeyError:
                        pass # no value was set

            ### call function with arguments_by_name
            fn = self.getNodeAttribute(n, "_fn")
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
                print("call", fn,  pos_args, kw_args)
                result = fn(*pos_args, **kw_args)
                self.updateNodeAttributes(n, result=result)
            except Exception as err:
                self.updateNodeAttributes(n, error=err)
                break
            