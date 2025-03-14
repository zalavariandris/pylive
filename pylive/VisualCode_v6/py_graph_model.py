from types import ModuleType
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


from pylive.VisualCode_v6.py_import_model import PyImportsModel
from pylive.utils.evaluate_python import find_unbounded_names
import pydoc

class _PyGraphItem:
    def __init__(self, model:'PyGraphModel', data:str="print", kind:Literal["operator", 'value-int', 'value-float', 'value-str', 'value-path', 'expression']="operator"):
        assert isinstance(data, str)
        assert kind in ("operator", 'value-int', 'value-float', 'value-str', 'value-path', 'expression')
        self._model = model
        self._kind:Literal["operator", 'value-int', 'value-float', 'value-str', 'value-path', 'expression'] = kind
        self._data = data
        self._compile_cache = None
        self._cache = None
        self._fields:list[Any] = []

    def clearCache(self):
        self._cache = None

    @property
    def help(self)->str:
        match self._kind:
            case 'operator':
                try:
                    func = self._compile()
                except Exception:
                    return ""
                else:
                    return pydoc.render_doc(func)
            case _:
                return ""

    @property
    def fields(self)->list[Any]:
        return self._fields

    @fields.setter
    def fields(self, value:list[Any]):
        self._fields = value

    @property
    def data(self)->str:
        return self._data

    @data.setter
    def expression(self, value:str):
        self._data = value
        self._compile_cache = None
        self._cache = None

    @property
    def kind(self)->Literal["operator", 'value-int', 'value-float', 'value-str', 'value-path', 'expression']:
        return self._kind

    @kind.setter
    def kind(self, value:Literal["operator", 'value-int', 'value-float', 'value-str', 'value-path', 'expression']="operator"):
        self._kind = value
        self._compile_cache = None
        self._cache = None

    def _compile(self,):
        if not self._compile_cache:
            self._compile_cache = eval(self._data, self._model._context)

        return self._compile_cache

    def inlets(self)->list[str]:
        match self._kind:
            case 'operator':
                try:
                    func = self._compile()
                except Exception:
                    return []
                else:
                    try:
                        sig = inspect.signature(func)
                    except (ValueError, TypeError):
                        return []
                    else:
                        return [name for name in sig.parameters.keys()]
            case 'expression':
                unbound_names = find_unbounded_names(self._data)
                return [name for name in unbound_names]
            case "operator" | 'value-int' | 'value-float' | 'value-str' | 'value-path' | 'expression':
                return []
            case _:
                raise ValueError()

    def inletFlags(self, inlet:str)->set:
        match self._kind:
            case 'operator':
                try:
                    func = self._compile()
                except Exception:
                    return set()
                else:
                    try:
                        sig = inspect.signature(func)
                    except ValueError:
                        return set()
                    else:
                        parameters = {key:param for key, param in sig.parameters.items() }
                        assert inlet in parameters.keys(), f"{inlet} not in {parameters}"
                        param = parameters[inlet]
                        flags = set()

                        match param.kind:
                            case inspect.Parameter.POSITIONAL_ONLY:
                                if param.default is param.empty:
                                    flags.add('required')
                            case inspect.Parameter.POSITIONAL_OR_KEYWORD:
                                if param.default is param.empty:
                                    flags.add('required')
                            case inspect.Parameter.VAR_POSITIONAL:
                                flags.add('multi')
                            case inspect.Parameter.KEYWORD_ONLY:
                                if param.default is param.empty:
                                    flags.add('required')
                            case inspect.Parameter.VAR_KEYWORD:
                                flags.add('extra')

                        return flags
            case _:
                return set(['required'])

    def inletData(self, inlet:str, attr:Literal['annotation', 'default'])->Any:
        match self._kind:
            case 'operator':
                try:
                    func = self._compile()
                except Exception:
                    return set()
                else:
                    try:
                        sig = inspect.signature(func)
                    except ValueError:
                        return None
                    else:
                        parameters = {key:param for key, param in sig.parameters.items() }
                        assert inlet in parameters.keys(), f"{inlet} not in {parameters}"
                        param = parameters[inlet]
                        match attr:
                            case 'annotation':
                                return param.annotation
                            case 'default':
                                return param.default

        return None

    def evaluate(self, named_args:dict):
        if not self._cache:
            match self._kind:
                case 'value-int' | 'value-float'| 'value-str'| 'value-path':
                    self._cache = self._compile()

                case 'operator':
                    func = self._compile()
                    self._cache = call_function_with_named_args(func, named_args)

                case 'expression':
                    ctx = {key: value for key, value in self._model._context.items()}
                    ctx.update(named_args)
                    self._cache = eval(self._data, ctx)

        return self._cache

    def __str__(self):
        from textwrap import shorten
        match self._kind:
            case 'operator':
                return f"𝒇 {self._compile_cache.__name__ if self._compile_cache else f"{self._data}"}"
            case 'value-int' | 'value-float' | 'value-str' | 'value-path':
                return f"𝕍 {self._cache!r}"
            case 'expression':
                return f"⅀ {self._data}"
            case _:
                raise ValueError()


import pathlib
from enum import StrEnum
class GraphMimeData(StrEnum):
    OutletData = 'application/outlet'
    InletData = 'application/inlet'
    LinkSourceData = 'application/link/source'
    LinkTargetData = 'application/link/target'


import importlib
_NodeKey = str
class PyGraphModel(QObject):
    modelAboutToBeReset = Signal()
    modelReset = Signal()

    # Imports
    importsReset = Signal()

    # Nodes
    nodesAboutToBeAdded = Signal(list) # list of NodeKey
    nodesAdded = Signal(list) # list of NodeKey
    nodesAboutToBeRemoved = Signal(list) # list of NodeKey
    nodesRemoved = Signal(list) # list of NodeKey
    dataChanged = Signal(list, list) # keys:list[str], hints:list[str], node key and list of data name hints. if hints is empty consider all data changed

    # Links
    nodesAboutToBeLinked = Signal(list) # list of edges: tuple[source, target, outlet, inlet]
    nodesLinked = Signal(list) # list[NodeKey,NodeKey,NodeKey, NodeKey]
    nodesAboutToBeUnlinked = Signal(list) # list[NodeKey,NodeK ey,NodeKey,NodeKey]
    nodesUnlinked = Signal(list) # list[NodeKey,NodeKey,NodeKey,NodeKey]

    # Inlets
    inletsReset = Signal(list) # list[_NodeKey]
    outletsReset = Signal(list) # list[_NodeKey]

    def __init__(self, parent:QObject|None=None):
        """
        PyGraphModel is model for a python computation graph.
        Each node has a unique name. Nodes has unique inlets.
        Source nodes and inlets are connected by links.
        To evaluate a node in the gaph, cal _evaluateNodes_ with the specific nodes.
        All dependencies are automatically evaluated, unless specified otherwise.
        """
        super().__init__(parent=parent)
        """TODO: store nodes and edges with networkx, 
        # but keep an eye on the proxy model implementation, which refers to nodes by index
        """

        self._node_data:OrderedDict[str, _PyGraphItem] = OrderedDict()
        self._links:set[tuple[str,str,str,str]] = set()
        self._auto_evaluate_filter = None

        self._imports: list[str] = []
        self._context_script:str = ""
        self._context:dict[str, ModuleType] = {'__builtins__': __builtins__}

        self._module_watcher = QFileSystemWatcher()
        self.module_watcher_connections = []

    def setImports(self, imports:list[str]):
        self._imports = imports
        self.importsReset.emit()
        self.restartKernel()

    def imports(self):
        return [_ for _ in self._imports]

    def restartKernel(self):
        import traceback

        context:dict[str, ModuleType] = {
            '__builtins__': __builtins__
        }

        for module_name in self._imports:
            # try:
            import os
            from pathlib import Path
            cwd = Path.cwd()
            try:
                spec = importlib.util.spec_from_file_location(module_name, cwd/f"{module_name}.py")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            except FileNotFoundError:
                module = importlib.import_module(module_name)


            context[module_name] = module

        self._context = context

        if self._module_watcher:
            for signal, slot in self.module_watcher_connections:
                signal.disconnect(slot)

        module_watcher = QFileSystemWatcher()
        for name, module in context.items():
            if isinstance(module, ModuleType) and module.__file__:
                module_watcher.addPath(module.__file__)

        if module_watcher:
            self.module_watcher_connections = [
                (module_watcher.fileChanged, lambda: 
                    self.invalidate([_ for _ in self.nodes()], compilation=True)) #TODO: invalidate only nodes from this module
            ]
            for signal, slot in self.module_watcher_connections:
                signal.connect(slot)

        self._module_watcher = module_watcher

        node_keys = [_ for _ in self.nodes()]
        # TODO invalidate effected nodes only!
        self.invalidate(node_keys, compilation=True)

    ### Graph imlpementation
    def nodes(self)->Collection[str]:
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

    def isInletLinked(self, node:str, inlet:str)->bool:
        #TODO: use ap proper graph structure eg.: networkx because this as well
        for u, v, o, i in self._links:
            if v == node and i == inlet:
                return True
        return False

    def isOutletLinked(self, node:str, outlet:str)->bool:
        #TODO: use ap proper graph structure eg.: networkx because this as well
        for u, v, o, i in self._links:
            if u == node and o == outlet:
                return True
        return False

    def inletFlags(self, node:str, inlet:str)->set:
        return self._node_data[node].inletFlags(inlet)

    def inletData(self, node:str, inlet:str, attr:str):
        return self._node_data[node].inletData(inlet, attr)

    def outlets(self, node:str)->Collection[str]:
        return ['out']

    def addNode(self, name:str, data:str, kind:Literal['operator', 'value-int', 'value-float', 'value-str', 'value-path', 'expression']='operator'):
        if name in self._node_data:
            raise ValueError("nodes must have a unique name")
        self.nodesAboutToBeAdded.emit([name])
        self._node_data[name] = _PyGraphItem(self, data, kind)
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

        # if inlet not in parameter_names
        #     raise ValueError(f"node '{target}' has no parameter named: '{inlet}'!")

        if 'multi' not in self.inletFlags(target, inlet) and self.isInletLinked(target, inlet):
            links_to_remove = []
            for u, v, o, i in self._links:
                if v == target and i==inlet:
                    links_to_remove.append( (u,v,o,i) )
            for u, v, o, i in links_to_remove:
                self.unlinkNodes(u, v, o, i)

        self.nodesAboutToBeLinked.emit( [(source, target, outlet, inlet)] )
        self._links.add( (source, target, outlet, inlet) )
        self.nodesLinked.emit([(source, target, outlet, inlet)])
        self._node_data[target].clearCache()
        self.dataChanged.emit([target], ['result'])
        
    def unlinkNodes(self, source:str, target:str, outlet:str, inlet:str):
        self.nodesAboutToBeUnlinked.emit([(source, target, outlet, inlet)])
        self._links.remove( (source, target, outlet, inlet) )
        self.nodesUnlinked.emit([(source, target, outlet, inlet)])
        self._node_data[target].clearCache()
        self.dataChanged.emit([target], ['result'])
        
    ### Node Data
    def data(self, node_key:str, attr:str)->Any:
        node_item = self._node_data[node_key]
        match attr:
            case 'name':
                return f"{node_item}"

            case 'data':
                return f"{node_item.data}"

            case 'kind':
                return f"{node_item.kind}"

            case 'result':
                ### GET FUNCTION ARGUMENTS
                named_args = dict()
                for source_node, target, outlet, inlet in self.inLinks(node_key):
                    error, value = self.data(source_node, 'result')
                    if error:
                        return error, None
                    named_args[inlet] = value

                ### Evaluate node with arguments
                try:
                    value = self._node_data[node_key].evaluate(named_args)

                except SyntaxError as err:
                    return err, None
                except Exception as err:
                    return err, None

                else:
                    return None, value

            case 'fields':
                return node_item.fields

            case 'help':
                return node_item.help

            case _:
                return getattr(node_item, attr)

    def invalidate(self, nodes:list[str], compilation:bool=True):
        # invalidate node results including ancestors.
        # if compilation is true, invalidate nodes compile_cache
        assert isinstance(nodes, list)
        for node_key in nodes:
            node_item = self._node_data[node_key]
            if compilation:
                node_item._compile_cache = None
                self.inletsReset.emit([node_key])
                self.outletsReset.emit([node_key])

            dependents = [n for n in self.descendants(node_key)]
            dependents.insert(0, node_key)

            for dep in dependents:
                self._node_data[dep]._cache = None
            self.dataChanged.emit(dependents, ['result'])

    def setData(self, node:str, attr:str, value:str):
        node_item = self._node_data[node]

        match attr:
            case 'kind':
                assert value in ('operator', 'expression', 'value-int', 'value-float', 'value-str', 'value-path')
                node_item.kind = value
                self.dataChanged.emit([node], ['kind'])
                self.invalidate([node], compilation=True)

            case 'data':
                match node_item.kind:
                    case 'operator':
                        node_item._data = value
                        self.dataChanged.emit([node], ['data'])
                        self.invalidate([node], compilation=True)
                    case 'expression':
                        node_item._data = value
                        self.dataChanged.emit([node], ['data'])
                        self.invalidate([node], compilation=True)
                    case 'value-int':
                        node_item._data = value
                        self.dataChanged.emit([node], ['data'])
                        self.invalidate([node], compilation=True)
                    case 'value-float':
                        node_item._data = value
                        self.dataChanged.emit([node], ['data'])
                        self.invalidate([node], compilation=True)
                    case 'value-str':
                        node_item._data = value
                        self.dataChanged.emit([node], ['data'])
                        self.invalidate([node], compilation=True)
                    case 'value-path':
                        node_item._data = value
                        self.dataChanged.emit([node], ['data'])
                        self.invalidate([node], compilation=True)
                    case _:
                        raise ValueError()

            case _:
                raise ValueError()

    ### Helpers
    def _toNetworkX(self)->nx.MultiDiGraph:
        G = nx.MultiDiGraph()
        for node, item in self._node_data.items():
            G.add_node(node, item=item)
        for source, target, outlet, inlet in self._links:
            G.add_edge(source, target, (outlet, inlet))
        return G

    ### Serialization
    @classmethod
    def fromData(klass, data:dict)->Self:
        graph = klass()

        graph.modelAboutToBeReset.emit()

        ### iterate nodes (with potential links using @ syntax)
        graph._links = set()
        graph._node_data = OrderedDict()

        for node_data in data['nodes']:
            node_item = _PyGraphItem(graph, node_data['data'], node_data['kind'])
            graph._node_data[node_data['name']] = node_item

        for link_data in data['links']:
            edge_entry = link_data['source'], link_data['target'], 'out', link_data['inlet']
            graph._links.add( edge_entry )


        graph.modelReset.emit()
        if imports:=data.get('imports'):
            graph.setImports(imports)
        graph.restartKernel()

        return graph

    def toData(self)->dict:
        data:dict[str, Any] = dict({
            'imports': "",
            'nodes': [],
            'links': []
        })

        data['imports'] = self.imports()

        for node_key, node_item in self._node_data.items():
            node_data:dict[Literal['name', 'kind', 'data'], Any] = {
                'name': node_key,
                'kind':node_item.kind,
                'data': node_item.data
            }

            data['nodes'].append(node_data)

        for source, target, outlet, inlet in self._links:
            edge_data = {
                'source': source,
                'target': target,
                'inlet': inlet
            }
            data['links'].append(edge_data)

        return data

