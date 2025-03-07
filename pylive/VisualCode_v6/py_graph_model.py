from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from pylive.VisualCode_v5.abstract_graph_model import AbstractGraphModel
from pylive.utils.evaluate_python import call_function_with_named_args, compile_python_function
import inspect
import networkx as nx
from pathlib import Path

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def say_hello(name:str):
    return f"Hello {name}!"

class _PyGraphItem:
    def __init__(self, expression:str="print", kind:Literal["operator", 'value', 'expression']="operator", ):
        assert isinstance(expression, str)
        assert kind in ("operator", 'value')
        self._kind:Literal["operator", 'value', 'expression'] = kind
        self._expression = expression
        self._compile_cache = None
        self._cache = None

    def clearCache(self):
        self._cache = None

    @property
    def expression(self)->str:
        return self._expression

    @expression.setter
    def expression(self, value:str):
        self._expression = value
        self._compile_cache = None
        self._cache = None

    @property
    def kind(self)->Literal["operator", 'value', 'expression']:
        return self._kind

    @kind.setter
    def kind(self, value:Literal["operator", 'value', 'expression']="operator"):
        self._kind = value
        self._compile_cache = None
        self._cache = None

    def _compile(self):
        if not self._compile_cache:
            self._compile_cache = eval(self._expression)

        return self._compile_cache

    def inlets(self)->list[str]:
        match self._kind:
            case 'value':
                return []
            case 'operator':
                try:
                    func = self._compile()
                except Exception:
                    return []
                else:
                    sig = inspect.signature(func)
                    return [name for name in sig.parameters.keys()]

    def evaluate(self, named_args:dict):
        if not self._cache:
            match self._kind:
                case 'value':
                    self._cache = self._compile()
                case 'operator':
                    func = self._compile()
                    self._cache = call_function_with_named_args(func, named_args)

        return self._cache



    def __str__(self):
        from textwrap import shorten
        match self._kind:
            case 'operator':
                return f"𝒇 {self._compile_cache.__name__ if self._compile_cache else "(not compiled)"})"
            case 'value':
                return f"I {shorten(str(self._cache), 8)}"
            case 'expression':
                return f"∑ {shorten(str(self._expression), 8)}"
        


import pathlib


class PyGraphModel(AbstractGraphModel):
    # Node data

    def __init__(self, parent:QObject|None=None):
        super().__init__(parent=parent)
        """
        PyGraphModel is model for a python computation graph.
        Each node has a unique name. Nodes has unique inlets.
        Source nodes and inlets are connected by links.
        To evaluate a node in the gaph, cal _evaluateNodes_ with the specific nodes.
        All dependencies are automatically evaluated, unless specified otherwise.
        """

        """TODO: store nodes and edges with networkx, 
        # but keep an eye on the proxy model implementation, which refers to nodes by index
        """
        self._node_data:OrderedDict[str, _PyGraphItem] = OrderedDict()
        self._links:set[tuple[str,str,str,str]] = set()
        self._auto_evaluate_filter = None

    ### Graph imlpementation
    def nodes(self)->Collection[Hashable]:
        return [_ for _ in self._node_data.keys()]

    def links(self)->Collection[tuple[str,str,str,str]]:
        return [_ for _ in self._links]

    def inLinks(self, node:str)->Collection[tuple[str,str,str,str]]:
        #TODO: optimize, by using networkx graph to store nodes and edges
        return list(filter(lambda link: link[1]==node, self._links))

    def outLinks(self, node:str)->Collection[tuple[str,str,str,str]]:
        #TODO: optimize, by using networkx graph to store nodes and edges
        return list(filter(lambda link: link[0]==node, self._links))

    def ancestors(self, source:str)->Collection[str]:
        G = self._toNetworkX()
        return nx.ancestors(G, source) # | {node} # source 

    def descendants(self, source:str)->Collection[str]:
        G = self._toNetworkX()
        return nx.descendants(G, source) # | {node} # source 

    def inlets(self, node:str)->Collection[str]:
        return self._node_data[node].inlets()

    def outlets(self, node:str)->Collection[str]:
        return ['out']

    def addNode(self, name:str, expression:str, kind:Literal['operator', 'value', 'expression']='operator'):
        if name in self._node_data:
            raise ValueError("nodes must have a unique name")
        self.nodesAboutToBeAdded.emit([name])
        self._node_data[name] = _PyGraphItem(expression, kind)
        self.nodesAdded.emit([name])

    def removeNode(self, name:str):
        ### remove links
        for source, target, outlet, inlet in self.inLinks(name):
            self.unlinkNodes(source, target, outlet, inlet)
        for source, target, outlet, inlet in self.outLinks(name):
            self.unlinkNodes(source, target, outlet, inlet)
        ### remove parameters

        self.nodesAboutToBeRemoved.emit([name])
        del self._node_data[name]
        self.nodesRemoved.emit([name])

    def linkNodes(self, source:str, target:str, outlet:str, inlet:str):
        # if source not in self._nodes.keys():
        #     raise ValueError(f"graph has no node named: '{source}'")
        # if target not in self._nodes.keys():
        #     raise ValueError(f"graph has no node named: '{target}'")
        # parameter_names = set(map(lambda item:item.name, self._nodes[target].parameters))

        # if inlet not in parameter_names:
        #     raise ValueError(f"node '{target}' has no parameter named: '{inlet}'!")

        self.nodesAboutToBeLinked.emit( [(source, target, outlet, inlet)] )
        self._links.add( (source, target, outlet, inlet) )
        self.nodesLinked.emit([(source, target, outlet, inlet)])
        self._node_data[target].clearCache()
        self.dataChanged.emit(target, ['result'])
        
    def unlinkNodes(self, source:str, target:str, outlet:str, inlet:str):
        self.nodesAboutToBeUnlinked.emit([(source, target, outlet, inlet)])
        self._links.remove( (source, target, outlet, inlet) )
        self.nodesUnlinked.emit([(source, target, outlet, inlet)])
        self._node_data[target].clearCache()
        self.dataChanged.emit(target, ['result'])
        
    ### Node Data
    def data(self, node_key:str, attr:str)->Any:
        node_item = self._node_data[node_key]
        match attr:
            case 'name':
                return f"{node_key}"

            case 'expression':
                return f"{node_item.expression}"

            case 'kind':
                return f"{node_item.kind}"

            case 'result':
                ### GET FUNCTION ARGUMENTS
                ### from links
                named_args = dict()
                for source_node, target, outlet, inlet in self.inLinks(node_key):
                    error, value = self.data(source_node, 'result')
                    if error:
                        return error, None
                    named_args[inlet] = value
                try:
                    value = self._node_data[node_key].evaluate(named_args)
                except SyntaxError as err:
                    import traceback
                    # traceback.print_exc()
                    return err, None
                except Exception as err:
                    import traceback
                    # traceback.print_exc()
                    return err, None
                else:
                    return None, value

            case _:
                return getattr(node_item, attr)

    def setData(self, node:str, attr:str, value:str):
        node_item = self._node_data[node]

        match attr:
            case 'kind':
                node_item.kind = value
                self.dataChanged.emit(node, ['kind'])
                self.inletsReset.emit(node)
                self.outletsReset.emit(node)
                self.dataChanged.emit(node, ['result'])

            case 'expression':
                node_item.expression = value
                self.dataChanged.emit(node, ['expression'])
                self.inletsReset.emit(node)
                self.outletsReset.emit(node)
                self.dataChanged.emit(node, ['result'])

    ### Helpers
    def _toNetworkX(self)->nx.MultiDiGraph:
        G = nx.MultiDiGraph()
        for node, item in self._node_data.items():
            G.add_node(node, item=item)
        for source, target, outlet, inlet in self._links:
            G.add_edge(source, target, (outlet, inlet))
        return G

    ### Serialization
    def load(self, path:Path|str):
        text = Path(path).read_text()
        self.deserialize(text)

    def save(self, path:Path|str):
        text = self.serialize()
        Path(path).write_text(text)

    def fromData(self, data:dict)->bool:
        self.modelAboutToBeReset.emit()

        ### iterate nodes (with potential links using @ syntax)
        self._links = set()
        self._node_data = OrderedDict()

        for node_data in data['nodes']:        
            if fields:=node_data.get('fields'):
                for name, value in fields.items():
                    if isinstance(value, str) and value.strip().startswith("->"):
                        source = value.strip()[2:].strip()
                        target = node_data['name'].strip()
                        outlet = 'out'
                        inlet = name.strip()
                        assert isinstance(source, str)
                        assert isinstance(target, str)
                        assert isinstance(inlet, str)
                        self._links.add( (source, target, outlet, inlet) )
                    else:
                        logger.warning("field values are not implemented yet!")
        
            node_item = _PyGraphItem(
                source=node_data['source'],
            )
            self._node_data[node_data['name'].strip()] = node_item

        ### iterate explicit edges
        def linkFromData(data:dict)->tuple[str,str,str,str]:
            return (
                data['source'],
                data['target'],
                'out',
                data['inlet']
            )

        if data.get('edges', None):
            edges_data:Sequence[dict[str, str]] = data.get('edges', [])
            self._links |= set( map(linkFromData, edges_data ) )


        self.modelReset.emit()

        return True

    def toData(self)->dict:
        data = dict({
            'nodes': []
        })

        for node_name, node_item in self._node_data.items():
            node_data:dict[Literal['name', 'source', 'fields'], Any] = {
                'name': node_name,
                'source':node_item.source
            }

            fields_data = dict()        
            for source, target, outlet, inlet in self.inLinks(node_name):
                assert target == node_name
                fields_data[inlet] = f" -> {source}"

            if len(fields_data)>0:
                node_data['fields'] = fields_data

            data['nodes'].append(node_data)

        return data

    def deserialize(self, text:str)->bool:
        import yaml
        data = yaml.load(text, Loader=yaml.SafeLoader)
        return self.fromData(data)

    def serialize(self)->str:
        import yaml
        return yaml.dump(self.toData(), sort_keys=False)

