
import functools
from sys import exec_prefix
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


from pathlib import Path
from dataclasses import dataclass, field
import inspect
from collections import OrderedDict, defaultdict
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

import networkx as nx

Empty = inspect.Parameter.empty

@dataclass
class PyParameterItem:
    name: str
    default: Any=Empty #TODO: object|None|inspect.Parameter.empty
    annotation: str|Any='' # TODO str|inspect.Parameter.empty
    kind:inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD
    value: object|None|Any=Empty #TODO: object|None|inspect.Parameter.empty


class Value:
    def __init__(self, getter):
        self.getter = getter
        self.setter_func = None
        self.deleter_func = None

    def __get__(self, instance, owner):
        if instance is None:
            return self  # When accessed from the class, return the descriptor itself
        return self.getter(instance)

    def setter(self, setter_func):
        self.setter_func = setter_func
        return self  # Return self to allow method chaining

    def deleter(self, deleter_func):
        self.deleter_func = deleter_func
        return self

    def __set__(self, instance, value):
        if self.setter_func is None:
            raise AttributeError("Can't set attribute")
        self.setter_func(instance, value)

    def __delete__(self, instance):
        if self.deleter_func is None:
            raise AttributeError("Can't delete attribute")
        self.deleter_func(instance)


# @dataclass 
class PyNodeItem:
    def __init__(self, source:str="def func(x:int):\n    ...", parameters:list[PyParameterItem]=[]):
        self._source = source
        self._parameters: list[PyParameterItem] = parameters
        self._needs_compilation:bool=True
        self._needs_evaluation:bool=True
        self._position:QPointF=QPointF()
        self._error:Exception|None=None
        self._result:object|None=None
        self._func:Callable|None=None # cache compiled function

    @property
    def source(self)->str:
        return self._source

    @source.setter
    def source(self, value:str):
        self._source = value

    @property
    def parameters(self):
        return self._parameters

    @parameters.setter
    def parameters(self, value):
        self._parameters = value

    def compile(self):
        new_parameters:list[PyParameterItem]|None = None

        try:
            from pylive.utils.evaluate_python import compile_python_function
            func = compile_python_function(self.source)
        except SyntaxError as err:
            self._needs_compilation = True
            self._needs_evaluation = True
            self._error = err
            self._func = None
            self._result = None
        except Exception as err:
            self._needs_compilation = True
            self._needs_evaluation = True
            self._error = err
            self._func = None
            self._result = None
        else:
            self._needs_compilation = False
            self._needs_evaluation = True
            self._func = func
            sig = inspect.signature(func)

            new_parameters = []
            for idx, param in enumerate(sig.parameters.values()):
                # find stored field value
                value = Empty # default parameter value
                for parameter in self.parameters:
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
            self._parameters = new_parameters
            self._error = None
            self._result = None

        if self._error is None:
            return True
        else:
            return False

    @property
    def needs_compilation(self)->bool:
        return self._needs_compilation

    def evaluate(self)->bool:
        ...

    @property
    def needs_evaluated(self)->bool:
        return self._needs_evaluation

    @property
    def result(self):
        return self._result


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
    needsCompilationChanged = Signal(str)
    needsEvaluationChanged = Signal(str)
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

    def nodeAt(self, index:int)->str:
        node = list(self._nodes.keys())[index]
        return node

    def linkCount(self):
        return len(self._links)

    def links(self)->Collection[tuple[str,str,str]]:
        return [_ for _ in self._links]

    def inLinks(self, node:str)->Sequence[tuple[str,str,str]]:
        #TODO: optimize, by using networkx graph to store nodes and edges
        return list(filter(lambda link: link[1]==node, self._links))

    def outLinks(self, node:str)->Sequence[tuple[str,str,str]]:
        #TODO: optimize, by using networkx graph to store nodes and edges
        return list(filter(lambda link: link[0]==node, self._links))

    ### Nodes
    def addNode(self, name:str, node_item:PyNodeItem):
        if name in self._nodes:
            raise ValueError("nodes must have a unique name")
        self.nodesAboutToBeAdded.emit([name])
        self._nodes[name] = node_item
        self.nodesAdded.emit([name])

    def removeNode(self, name:str):
        ### remove links
        for source, target, inlet in self.inLinks(name):
            self.unlinkNodes(source, target, inlet)
        for source, target, inlet in self.outLinks(name):
            self.unlinkNodes(source, target, inlet)
        ### remove parameters

        self.nodesAboutToBeRemoved.emit([name])
        del self._nodes[name]
        self.nodesRemoved.emit([name])

    ### Links
    def linkNodes(self, source:str, target:str, inlet:str):
        if source not in self._nodes.keys():
            raise ValueError(f"graph has no node named: '{source}'")
        if target not in self._nodes.keys():
            raise ValueError(f"graph has no node named: '{target}'")
        parameter_names = set(map(lambda item:item.name, self._nodes[target].parameters))

        if inlet not in parameter_names:
            raise ValueError(f"node '{target}' has no parameter named: '{inlet}'!")
        self.nodesAboutToBeLinked.emit( [(source, target, inlet)] )
        self._links.add( (source, target, inlet) )
        self.nodesLinked.emit([(source, target, inlet)])

    def unlinkNodes(self, source:str, target:str, inlet:str):
        self.nodesAboutToBeUnlinked.emit([(source, target, inlet)])
        self._links.remove( (source, target, inlet) )
        self.nodesUnlinked.emit([(source, target, inlet)])

    ### Node Data
    def nodePosition(self, name:str)->QPointF:
        return self._nodes[name]._position

    def nodeSource(self, name:str)->str:
        return self._nodes[name].source

    def setNodeSource(self, node:str, value:str):
        if self._nodes[node].source != value:
            self._nodes[node].source = value
            self._nodes[node]._needs_compilation = True
            self._nodes[node]._needs_evaluation = False
            self._nodes[node]._error = None
            self._nodes[node]._parameters = []

            self.sourceChanged.emit(node)
            self.needsCompilationChanged.emit(node)
            self.needsCompilationChanged.emit(node)
            self.errorChanged.emit(node)
            self.parametersReset.emit(node)

    def compileNodes(self, nodes:Iterable[str])->bool:
        """compile all nodes
        if all nodes were compiled succeslfully return 'True'!
        if any node gails to compile will return 'False'!

        TODO: test compilation succes with multiple nodes, and each scenario: all compiles, a few fail, all fails...
        """

        # if all nodes compiled succesfully return True, otherwise return False
        success_by_node = dict()
        for node_key in nodes:
            node_item = self._nodes[node_key]

            prev_compiled = node_item._needs_compilation
            prev_func = node_item._func
            prev_evaluated = node_item._needs_evaluation
            prev_error = node_item._error
            prev_result = node_item._result
            prev_parameters = node_item._parameters
            success = node_item.compile()
            success_by_node[node_key]=success
            if prev_compiled != node_item._needs_compilation:
                self.needsCompilationChanged.emit(node_key)
            # if prev_func != node_item._func:
            #     self.funcChanged.emit(node_key)
            if prev_evaluated != node_item._needs_evaluation:
                self.needsEvaluationChanged.emit(node_key)
            if prev_error != node_item._error:
                self.errorChanged.emit(node_key)
            if prev_result != node_item._result:
                self.resultChanged.emit(node_key)
            if prev_parameters != node_item._parameters:
                self.parametersReset.emit(node_key)

        success = all(success_by_node.values())
        return success

    def evaluateNodes(self, nodes:Sequence[str], ancestors=True, autocompile=True):
        ### build temporary nx graph (TODO: store nodes and edges in a graph!)

        ### append ancestors
        G = self._toNetworkX()
        nodes = list(_ for _ in nodes)

        if ancestors:
            dependency_nodes = []
            for node in nodes:
                dependency_nodes+= self.ancestors(node)
            nodes+=dependency_nodes

        ### create subgraph
        subgraph = cast(nx.MultiDiGraph, G.subgraph(nodes))
        
        ### sort nodes in topological order
        ordered_nodes = list(nx.topological_sort(subgraph))

        # compile nodes if necessary
        nodes_need_compilation = filter(lambda node: self.needsCompilation(node), ordered_nodes)
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
                assert not self.needsEvaluation(source) and self.nodeError(source) is None, "at this point dependencies must have been evaluated without errors!"
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
                new_needs_evaluation = True
                new_error = err
                new_result = None
            except Exception as err:
                new_needs_evaluation = True
                new_error = err
                new_result = None
            else:
                new_needs_evaluation = False
                new_error = None
                new_result = result

            if node_item._needs_evaluation != new_needs_evaluation:
                node_item._needs_evaluation = new_needs_evaluation
                self.needsEvaluationChanged.emit(node)
            if node_item._error != new_error:
                node_item._error = new_error
                self.errorChanged.emit(node)
            if node_item._result != new_result:
                node_item._result = new_result
                print(f"emit result changed fro node: '{node}'")
                self.resultChanged.emit(node)

            if new_error is not None:
                return False
            else:
                return True

        for node in ordered_nodes:
            success = _evaluate_node(node)
            if not success:
                return False
        return True

    def parameterCount(self, node)->int:
        if not self._nodes:
            return 0
        return len(self._nodes[node].parameters)

    def hasParameter(self, node, param:str)->int:
        parameter_names = set()
        for i in range(self.parameterCount(node)):
            parameter_names.add(self.parameterName(node, i))

        return param in parameter_names

    def setParameters(self, node:str, parameters:list[PyParameterItem]):
        self.parametersAboutToBeReset.emit(node)
        self._nodes[node].parameters = parameters
        self.parametersReset.emit(node)

    def insertParameter(self, node:str, index:int, parameter:PyParameterItem)->bool:
        self.parametersAboutToBeInserted.emit(node, index, index)
        self._nodes[node].parameters.insert(index, parameter)
        self.parametersInserted.emit(node, index, index)
        return True

    def removeParameter(self, node:str, index:int):
        self.parametersAboutToBeRemoved.emit(node, index, index)
        del self._nodes[node].parameters[index]
        self.parametersRemoved.emit(node, index, index)

    def setParameterValue(self, node:str, index:int, value:object|None|Empty):
        if self._nodes[node].parameters[index].value != value:
            self._nodes[node].parameters[index].value = value
            self.patametersChanged.emit(node, index, index)

    def parameterItem(self, node:str, index:int)->PyParameterItem:
        return self._nodes[node].parameters[index]

    def parameterName(self, node:str, index:int)->str:
        return self._nodes[node].parameters[index].name

    def parameterValue(self, node:str, index:int)->object|None|Empty:
        return self._nodes[node].parameters[index].value

    def needsCompilation(self, node)->bool:
        return self._nodes[node]._needs_compilation

    def needsEvaluation(self, node:str)->bool:
        return self._nodes[node]._needs_evaluation

    def nodeError(self, node)->Exception|None:
        return self._nodes[node]._error

    def nodeResult(self, node)->Any:
        return self._nodes[node]._result

    def _toNetworkX(self)->nx.MultiDiGraph:
        G = nx.MultiDiGraph()
        for node, item in self._nodes.items():
            G.add_node(node, item=item)
        for source, target, inlet in self._links:
            G.add_edge(source, target, inlet)
        return G

    def ancestors(self, source:str)->set[str]:
        G = self._toNetworkX()
        return nx.ancestors(G, source) # | {node} # source 

    def descendants(self, source:str)->set[str]:
        G = self._toNetworkX()
        return nx.descendants(G, source) # | {node} # source 

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


