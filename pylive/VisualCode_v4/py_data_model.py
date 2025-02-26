
import functools
from sys import exec_prefix
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from pathlib import Path

from dataclasses import dataclass, field
import inspect

import inspect

Empty = inspect.Parameter.empty

import networkx as nx

from yaml import resolver
@dataclass
class PyParameterItem:
    name: str
    default: Any=Empty #TODO: object|None|inspect.Parameter.empty
    annotation: str|Any='' # TODO str|inspect.Parameter.empty
    kind:inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD
    value: object|None|Any=Empty #TODO: object|None|inspect.Parameter.empty


@dataclass
class PyNodeItem:
    source:str="def func(x:int):\n    ..."
    parameters: list[PyParameterItem] = field(default_factory=list)
    position:QPointF=field(default_factory=QPointF)
    is_compiled:bool=False
    is_evaluated:bool=False
    error:Exception|None=None
    result:object|None=None
    _func:Callable|None=None # cache compiled function

from collections import OrderedDict, defaultdict


class PyDataModel(QObject):
    modelAboutToBeReset = Signal()
    modelReset = Signal()

    # Node Collection
    nodesAboutToBeAdded = Signal(list) # list of node names
    nodesAdded = Signal(list) # list of node names
    nodesAboutToBeRemoved = Signal(list) # list of node names
    nodesRemoved = Signal(list) # list of node names

    # Node data
    positionChanged = Signal(str)
    sourceChanged = Signal(str)
    compiledChanged = Signal(str)
    evaluatedChanged = Signal(str)
    errorChanged = Signal(str)
    resultChanged = Signal(str)

    # Node Links
    nodesAboutToBeLinked = Signal(list) # list of edges: tuple[source, target, inlet]
    nodesLinked = Signal(list) # list[str,str,str]
    nodesAboutToBeUnlinked = Signal(list) # list[str,str,str]
    nodesUnlinked = Signal(list) # list[str,str,str]

    # Node Parameters
    parametersAboutToBeReset = Signal(str)
    parametersReset = Signal(str)
    parametersAboutToBeInserted = Signal(str, int, int) # node, start, end
    parametersInserted = Signal(str, int, int) # node, start, end
    patametersChanged = Signal(str, int, int) # node, first, last
    parametersAboutToBeRemoved = Signal(str, int, int) # node, start, end
    parametersRemoved = Signal(str, int, int) # node, start, end


    def __init__(self, parent:QObject|None=None):
        super().__init__(parent=parent)
        """
        PyDataModel is model for a python computation graph.
        Each node has a unique name. Nodes has unique inlets.
        Source nodes and inlets are connected by links.
        To evaluate a node in the gaph, cal _evaluateNodes_ with the specific nodes.
        All dependencies are automatically evaluated, unless specified otherwise.
        """

        """TODO: store nodes and edges with networkx, 
        # but keep an eye on the proxy model implementation, which refers to nodes by index
        """
        self._nodes:OrderedDict[str, PyNodeItem] = OrderedDict()
        self._links:set[tuple[str,str,str]] = set()

    def nodeCount(self)->int:
        return len(self._nodes)

    def nodes(self)->Collection[str]:
        return [_ for _ in self._nodes.keys()]

    def links(self)->Collection[tuple[str,str,str]]:
        return [_ for _ in self._links]

    def inLinks(self, node:str)->Sequence[tuple[str,str,str]]:
        #TODO: optimize, by using networkx graph to store nodes and edges
        return list(filter(lambda link: link[1]==node, self._links))

    def outLinks(self, node:str)->Sequence[tuple[str,str,str]]:
        #TODO: optimize, by using networkx graph to store nodes and edges
        return list(filter(lambda link: link[0]==node, self._links))

    def nodeAt(self, index:int)->str:
        node = list(self._nodes.keys())[index]
        return node

    def addNode(self, name:str, node_item:PyNodeItem):
        if name in self._nodes:
            raise ValueError("nodes must have a unique name")
        self.nodesAboutToBeAdded.emit([name])
        self._nodes[name] = node_item
        self.nodesAdded.emit([name])

    def removeNode(self, name:str):
        logger.debug(f"removeNode: {name}")
        ### remove links
        for source, target, inlet in self.inLinks(name):
            self.unlinkNodes(source, target, inlet)
        for source, target, inlet in self.outLinks(name):
            self.unlinkNodes(source, target, inlet)
        ### remove parameters

        self.nodesAboutToBeRemoved.emit([name])
        del self._nodes[name]
        self.nodesRemoved.emit([name])

    def linkCount(self):
        return len(self._links)

    def linkNodes(self, source:str, target:str, inlet:str):
        logger.debug(f"PyDataModel->linkNodes {source}, {target}, {inlet}")
        if source not in self._nodes.keys():
            raise ValueError(f"graph has no node named: '{source}'")
        if target not in self._nodes.keys():
            raise ValueError(f"graph has no node named: '{target}'")
        if inlet not in map(lambda item:item.name, self._nodes[target].parameters):
            raise ValueError(f"node '{target}' has no parameter named: '{inlet}'!")
        self.nodesAboutToBeLinked.emit( [(source, target, inlet)] )
        self._links.add( (source, target, inlet) )
        self.nodesLinked.emit([(source, target, inlet)])

    def unlinkNodes(self, source:str, target:str, inlet:str):
        self.nodesAboutToBeUnlinked.emit([(source, target, inlet)])
        self._links.remove( (source, target, inlet) )
        self.nodesUnlinked.emit([(source, target, inlet)])

    def nodePosition(self, name:str)->QPointF:
        return self._nodes[name].position

    def nodeSource(self, name:str)->str:
        return self._nodes[name].source

    def setNodeSource(self, node:str, value:str):
        if self._nodes[node].source != value:
            logger.debug(f"setNodeSource: {node}, {value}")
            self._nodes[node].source = value
            self.sourceChanged.emit(node)

    def compileNodes(self, nodes:Iterable[str])->bool:
        """compile all nodes
        if all nodes were compiled succeslfully return 'True'!
        if any node gails to compile will return 'False'!

        TODO: test compilation succes with multiple nodes, and each scenario: all compiles, a few fail, all fails...
        """
        def _compile_node(node):
            logger.debug(f"_compile_node: {node}")
            node_item = self._nodes[node]
            new_parameters:list[PyParameterItem]|None = None

            try:
                from pylive.utils.evaluate_python import compile_python_function
                func = compile_python_function(node_item.source)
            except SyntaxError as err:
                new_compiled = False
                new_evaluated = False
                new_error = err
                new_func = None
                new_result = None
            except Exception as err:
                new_compiled = False
                new_evaluated = False
                new_error = err
                new_func = None
                new_result = None
            else:
                new_compiled = True
                new_evaluated = False
                new_func = func
                sig = inspect.signature(func)

                new_parameters = []
                for idx, param in enumerate(sig.parameters.values()):
                    # find stored field value
                    value = Empty # default parameter value
                    for parameter in node_item.parameters:
                        if parameter.name==param.name:
                            value = parameter.value
                    
                    param_item = PyParameterItem(
                        name=param.name, 
                        default=param.default,
                        annotation=param.annotation, 
                        kind=param.kind,
                        value=value
                    )
                    new_parameters.append(param_item)

                new_error = None
                new_result = None

            if node_item.is_compiled != new_compiled:
                node_item.is_compiled = new_compiled
                self.compiledChanged.emit(node)

            if node_item._func != new_func:
                node_item._func = new_func
            if node_item.is_evaluated != new_evaluated:
                node_item.is_evaluated = new_evaluated
                self.evaluatedChanged.emit(node)
            if node_item.error != new_error:
                node_item.error = new_error
                self.errorChanged.emit(node)
            if node_item.result != new_result:
                node_item.result = new_result
                self.resultChanged.emit(node)
            if new_parameters is not None:
                node_item.parameters = new_parameters
                self.parametersReset.emit(node)

            if new_error is None:
                return True
            else:
                return False

        # if all nodes compiled succesfully return True, otherwise return False
        success_by_node = dict()
        for node in nodes:
            success = _compile_node(node)
            success_by_node[node]=success
        success = all(success_by_node.values())
        return success

    def evaluateNodes(self, nodes:Sequence[str], ancestors=True, autocompile=True):
        ### build temporary nx graph (TODO: store nodes and edges in a graph!)
        G = nx.MultiDiGraph()
        for node, item in self._nodes.items():
            G.add_node(node, item=item)
        for source, target, inlet in self._links:
            G.add_edge(source, target, inlet)

        ### append ancestors
        nodes = list(_ for _ in nodes)
        if ancestors:
            dependency_nodes = []
            for node in nodes:
                dependency_nodes+= nx.ancestors(G, node)
            nodes+=dependency_nodes

        ### create subgraph
        subgraph = cast(nx.MultiDiGraph, G.subgraph(nodes))
        
        ### sort nodes in topological order
        ordered_nodes = list(nx.topological_sort(subgraph))

        # compile nodes if necessary
        nodes_need_compilation = filter(lambda node: not self.isCompiled(node), ordered_nodes)
        compile_success = self.compileNodes(nodes_need_compilation)
        if not compile_success:
            return False
        ### evaluate nodes in reverse topological order
        from pylive.utils.evaluate_python import call_function_with_named_args
        def _evaluate_node(node:str)->bool:
            """evaluate nodes in topological order
            Stop and return _False_ when evaluation Fails.
            """

            ### Get functions
            node_item = self._nodes[node]
            func = node_item._func
            assert func is not None, "if compilation as succesfull, func cant be None"

            ### Get parameters
            ### load arguments from sources
            named_args = dict()
            for source, target, inlet in self.inLinks(node):
                assert self.isEvaluated(source) and self.nodeError(source) is None, "at this point dependencies must have been evaluated without errors!"
                named_args[inlet] = self.nodeResult(source)

            ### load arguments from parameters
            for param_item in node_item.parameters:
                if param_item.name in named_args:
                    continue # skip connected fields
                if param_item.value != Empty:
                    named_args[param_item.name] = param_item.value
            try:
                result = call_function_with_named_args(func, named_args)
            except SyntaxError as err:
                new_evaluated = True
                new_error = err
                new_result = None
            except Exception as err:
                new_evaluated = True
                new_error = err
                new_result = None
            else:
                new_evaluated = True
                new_error = None
                new_result = result

            if node_item.is_evaluated != new_evaluated:
                node_item.is_evaluated = new_evaluated
                self.evaluatedChanged.emit(node)
            if node_item.error != new_error:
                node_item.error = new_error
                self.errorChanged.emit(node)
            if node_item.result != new_result:
                node_item.result = new_result
                self.resultChanged.emit(node)

            if new_error is not None:
                return False
            else:
                return True

        for node in ordered_nodes:
            logger.debug(f"- {node}") 
            success = _evaluate_node(node)
            if not success:
                return False
        return True

    def parameterCount(self, node)->int:
        if not self._nodes:
            return 0
        return len(self._nodes[node].parameters)

    def setParameters(self, node:str, parameters:list[PyParameterItem]):
        logger.debug(f"setParameters: {node}, {parameters}")
        self.parametersAboutToBeReset.emit(node)
        self._nodes[node].parameters = parameters
        self.parametersReset.emit(node)

    def insertParameter(self, node:str, index:int, parameter:PyParameterItem)->bool:
        logger.debug(f"insertParameter: {node}, {index}, {parameter}")
        self.parametersAboutToBeInserted.emit(node, index, index)
        self._nodes[node].parameters.insert(index, parameter)
        self.parametersInserted.emit(node, index, index)
        return True

    def removeParameter(self, node:str, index:int):
        logger.debug(f"removeParameter: {node}, {index}")
        self.parametersAboutToBeRemoved.emit(node, index, index)
        del self._nodes[node].parameters[index]
        self.parametersRemoved.emit(node, index, index)

    def setParameterValue(self, node:str, index:int, value:object|None|Empty):
        logger.debug(f"setParameterValue: {node}, {index}, {value}")
        if self._nodes[node].parameters[index].value != value:
            self._nodes[node].parameters[index].value = value
            self.patametersChanged.emit(node, index, index)

    def parameterItem(self, node:str, index:int)->PyParameterItem:
        return self._nodes[node].parameters[index]

    def parameterName(self, node:str, index:int)->str:
        return self._nodes[node].parameters[index].name

    def parameterValue(self, node:str, index:int)->object|None|Empty:
        return self._nodes[node].parameters[index].value

    def isCompiled(self, node)->bool:
        return self._nodes[node].is_compiled

    def isEvaluated(self, node:str)->bool:
        return self._nodes[node].is_evaluated

    def nodeError(self, node)->Exception|None:
        return self._nodes[node].error

    def nodeResult(self, node)->Any:
        return self._nodes[node].result

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
        self._nodes = OrderedDict()

        links_from_parameters:set[tuple[str,str,str]] = set()
        for node_data in data['nodes']:
            parameters = []
            
            if fields:=node_data.get('fields'):
                for name, value in fields.items():
                    if isinstance(value, str) and value.strip().startswith("->"):
                        source = value.strip()[2:].strip()
                        target = node_data['name'].strip()
                        inlet = name.strip()
                        assert isinstance(source, str)
                        assert isinstance(target, str)
                        assert isinstance(inlet, str)
                        self._links.add( (source, target, inlet) )
                    else:
                        item = PyParameterItem(name=name, value=value)
                        parameters.append(item)
        
            node_item = PyNodeItem(
                source=node_data['source'],
                parameters = parameters
            )
            self._nodes[node_data['name'].strip()] = node_item

        ### iterate explicit edges
        def linkFromData(data:dict)->tuple[str,str,str]:
            return (
                data['source'],
                data['target'],
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

        for node_name, node_item in self._nodes.items():
            node_data:dict[Literal['name', 'source', 'fields'], Any] = {
                'name': node_name,
                'source':node_item.source
            }

            fields_data = dict()
            for item in node_item.parameters:
                if item.value != Empty:
                    fields_data[item.name] = item.value

            
            for source, target, inlet in self.inLinks(node_name):
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


