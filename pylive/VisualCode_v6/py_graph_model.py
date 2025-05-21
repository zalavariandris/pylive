from types import ModuleType
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from pylive.VisualCode_v4._ARCHIVE import node_tree_model
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

KindType = Literal["operator", 'value-int', 'value-float', 'value-str', 'value-path', 'expression']


class _PyGraphItem:
    def __init__(self, model:'PyGraphModel',
        content:str="print", 
        kind:KindType="operator"
    ):
        assert isinstance(content, str)
        assert kind in ("operator", 'value-int', 'value-float', 'value-str', 'value-path', 'expression')
        self.kind:KindType = kind
        self.content:Callable|str|int|float|pathlib.Path = content


import pathlib
from enum import StrEnum
class GraphMimeData(StrEnum):
    OutletData = 'application/outlet'
    InletData = 'application/inlet'
    LinkSourceData = 'application/link/source'
    LinkTargetData = 'application/link/target'


import importlib
import importlib.util
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
        self._compile_cache:dict[str, Callable] = dict()
        self._result_cache:dict[str, Any] = dict()

        self._links:set[tuple[str,str,str,str]] = set()

        self._imports: list[str] = []
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
                    self.invalidate([_ for _ in self.nodes()])) #TODO: invalidate only nodes from this module
            ]
            for signal, slot in self.module_watcher_connections:
                signal.connect(slot)

        self._module_watcher = module_watcher

        node_keys = [_ for _ in self.nodes()]
        # TODO invalidate effected nodes only!
        self.invalidate(node_keys)

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

    def inlets(self, node:str)->List[str]:
        node_item = self._node_data[node]
        match node_item.kind:
            case 'operator':
                try:
                    func = node_item.content
                    assert callable(func)
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
                try:
                    unbound_names = find_unbounded_names(node_item.content)
                    return [name for name in unbound_names]
                except SyntaxError:
                    return []
            case 'value-int' | 'value-float' | 'value-str' | 'value-path':
                return []
            case _:
                raise ValueError()

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
        node_item = self._node_data[node]
        match node_item.kind:
            case 'operator':
                try:
                    func = node_item.content
                    assert callable(func)
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

    def inletData(self, node:str, inlet:str, attr:Literal['annotation', 'default']):
        node_item = self._node_data[node]
        match node_item.kind:
            case 'operator':
                try:
                    func = node_item.content
                    assert callable(func)
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
        self.invalidate([target])
        self.dataChanged.emit([target], ['result'])
        
    def unlinkNodes(self, source:str, target:str, outlet:str, inlet:str):
        self.nodesAboutToBeUnlinked.emit([(source, target, outlet, inlet)])
        self._links.remove( (source, target, outlet, inlet) )
        self.nodesUnlinked.emit([(source, target, outlet, inlet)])
        self.invalidate([target])
        self.dataChanged.emit([target], ['result'])
        
    ### Node Data
    def data(self, node_key:str, attr:str, role:int=Qt.ItemDataRole.DisplayRole)->Any:
        node_item = self._node_data[node_key]
        match attr:
            case 'name':
                if role == Qt.ItemDataRole.DisplayRole:
                    return f"{node_key}"
                return None

            case 'label':
                if role == Qt.ItemDataRole.DisplayRole:
                    match node_item.kind:
                        case 'operator':
                            assert isinstance(node_item.content, str)
                            return f"𝒇 {node_item.content}"
                        case 'expression':
                            return f"⅀ {node_item.content}"
                        case 'value-float' | 'value-int' | 'value-str' | 'value-path':
                            return f"𝕍 {node_item.content}"
                        case _:
                            return f"{node_key}"

            case 'kind':
                return node_item.kind

            case 'content':
                if role == Qt.ItemDataRole.EditRole:
                    return node_item.content

                if role == Qt.ItemDataRole.DisplayRole:
                    match node_item.kind:
                        case 'operator':
                            assert isinstance(node_item.content, str)
                            return node_item.content
                        case _:
                            return f"{node_item.content}"
                return None

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
                    def evaluate_node(node, named_args:dict):
                        if node not in self._result_cache:
                            node_item = self._node_data[node]
                            match node_item.kind:
                                case 'value-int' | 'value-float'| 'value-str'| 'value-path':
                                    self._result_cache[node] = node_item.content

                                case 'operator':
                                    assert isinstance(node_item.content, str)
                                    if node not in self._compile_cache:
                                        function_path = node_item.content
                                        assert isinstance(function_path, str)
                                        func = eval(function_path, self._context)
                                        self._compile_cache[node] = func
                                    assert callable(self._compile_cache[node])
                                    self._result_cache[node] = call_function_with_named_args(self._compile_cache[node], named_args)

                                case 'expression':
                                    assert isinstance(node_item.content, str)
                                    ctx = {key: value for key, value in self._context.items()}
                                    ctx.update(named_args)
                                    self._result_cache[node] = eval(node_item.content, ctx)

                        return self._result_cache[node]
                    value = evaluate_node(node_key, named_args)

                except SyntaxError as err:
                    return err, None
                except Exception as err:
                    return err, None
                else:
                    return None, value

            case 'help':
                match node_item.kind:
                    case 'operator':
                        try:
                            func = node_item.content
                            assert callable(func)
                        except Exception:
                            return ""
                        else:
                            return pydoc.render_doc(func)
                    case _:
                        return ""

            case _:
                raise ValueError()

    def invalidate(self, nodes:list[str]):
        """invalidate nodes results
        adn all of their dependents
        """
        assert isinstance(nodes, list)
        for node in nodes:  # this will rigger multiple times for when multiple nodes invalidated at  once: handle overlapping depednencies
            self.inletsReset.emit([node])
            self.outletsReset.emit([node])


            ## invalidate node and dependent cache
            if node in self._result_cache:
                del self._result_cache[node]
            dependents = [_ for _ in self.descendants(node)]

            for dep in dependents:
                del self._result_cache[dep]

            self.dataChanged.emit([node] + dependents, ['result'])

    def setData(self, node:str, attr:str, value:Any, role:int=Qt.ItemDataRole.EditRole)->bool:
        node_item = self._node_data[node]

        match attr:
            case 'kind':
                assert value in ('operator', 'expression', 'value-int', 'value-float', 'value-str', 'value-path')
                if value != node_item.kind:
                    node_item.kind = value
                    match node_item.kind:
                        case 'operator':
                            node_item.content = "print"
                        case 'expression':
                            node_item.content = "x"
                        case 'value-int':
                            node_item.content = 0
                        case 'value-float':
                            node_item.content = 0.0
                        case 'value-str':
                            node_item.content = "text"
                        case 'value-path':
                            node_item.content = Path.cwd()

                    self.dataChanged.emit([node], ['kind', 'content'])
                    self.invalidate([node])
                    return True

            case 'content':
                if value != node_item.content:
                    match node_item.kind:
                        case 'operator':
                            assert isinstance(value, str)
                            node_item.content = value
                        case 'expression':
                            assert isinstance(value, str)
                            node_item.content = value
                        case 'value-int':
                            assert isinstance(value, int)
                            node_item.content = value
                        case 'value-float':
                            assert isinstance(value, float)
                            node_item.content = value
                        case 'value-str':
                            assert isinstance(value, str)
                            node_item.content = value
                        case 'value-path':
                            assert isinstance(value, pathlib.Path)
                            node_item.content = value
                        case _:
                            raise ValueError()

                    self.dataChanged.emit([node], ['content'])
                    self.invalidate([node])
                    return True

            case _:
                raise ValueError()
                return False

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
            node_item = _PyGraphItem(graph, node_data['content'], node_data['kind'])
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
            node_data:dict[Literal['name', 'kind', 'content'], Any] = {
                'name': node_key,
                'kind':node_item.kind,
                'content': node_item.content
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

