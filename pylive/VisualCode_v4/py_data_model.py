
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

from shiboken6 import invalidate
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
        self.source = source
        self.parameters: list[PyParameterItem] = parameters
        self.needs_compilation:bool=True
        self.needs_evaluation:bool=True
        self.position:QPointF=QPointF()
        self.error:Exception|None=None
        self.result:object|None=None
        self.func:Callable|None=None # cache compiled function

    # @property
    # def source(self)->str:
    #     return self._source

    # @source.setter
    # def source(self, value:str):
    #     self._source = value

    # @property
    # def parameters(self):
    #     return self._parameters

    # @parameters.setter
    # def parameters(self, value):
    #     self._parameters = value

    # @property
    # def needs_compilation(self)->bool:
    #     return self._needs_compilation

    # def evaluate(self)->bool:
    #     ...

    # @property
    # def needs_evaluated(self)->bool:
    #     return self._needs_evaluation

    # @property
    # def result(self):
    #     return self._result


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

    invalidated = Signal(list)

    # Node Links
    nodesAboutToBeLinked = Signal(list) # list of edges: tuple[source, target, outlet, inlet]
    nodesLinked = Signal(list) # list[str,str,str, str]
    nodesAboutToBeUnlinked = Signal(list) # list[str,str,str,str]
    nodesUnlinked = Signal(list) # list[str,str,str,str]

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
        self._links:set[tuple[str,str,str,str]] = set()

    def nodeCount(self)->int:
        return len(self._nodes)

    def nodes(self)->Collection[str]:
        return [_ for _ in self._nodes.keys()]

    def nodeAt(self, index:int)->str:
        node = list(self._nodes.keys())[index]
        return node

    def linkCount(self):
        return len(self._links)

    def links(self)->Collection[tuple[str,str,str,str]]:
        return [_ for _ in self._links]

    def inLinks(self, node:str)->Sequence[tuple[str,str,str,str]]:
        #TODO: optimize, by using networkx graph to store nodes and edges
        return list(filter(lambda link: link[1]==node, self._links))

    def outLinks(self, node:str)->Sequence[tuple[str,str,str,str]]:
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
        for source, target, outlet, inlet in self.inLinks(name):
            self.unlinkNodes(source, target, outlet, inlet)
        for source, target, outlet, inlet in self.outLinks(name):
            self.unlinkNodes(source, target, outlet, inlet)
        ### remove parameters

        self.nodesAboutToBeRemoved.emit([name])
        del self._nodes[name]
        self.nodesRemoved.emit([name])

    ### Links
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
        self._setNeedsEvaluation(target, True)
        self.nodesLinked.emit([(source, target, outlet, inlet)])
        
    def unlinkNodes(self, source:str, target:str, outlet:str, inlet:str):
        self.nodesAboutToBeUnlinked.emit([(source, target, outlet, inlet)])
        self._links.remove( (source, target, outlet, inlet) )
        self._setNeedsEvaluation(target, True)
        self.nodesUnlinked.emit([(source, target, outlet, inlet)])
        
    ### Node Data
    def position(self, name:str)->QPointF:
        return self._nodes[name].position

    def source(self, name:str)->str:
        return self._nodes[name].source

    def setSource(self, node:str, value:str):
        if self._nodes[node].source != value:
            self._nodes[node].source = value
            self.sourceChanged.emit(node)

            self._setNeedsCompilation(node, True)
            self._setNeedsEvaluation(node,  False)
            self._setError(node, None)
            self._setParameters(node,  [])

    def compile(self, node:str, force=False)->bool:
        """compile all nodes
        if the node has compiled succeslfully return 'True', otherwise return 'False'!
        """

        if not self.needsCompilation(node):
            return True

        try:
            from pylive.utils.evaluate_python import compile_python_function
            func = compile_python_function(self._nodes[node].source)
        except SyntaxError as err:
            self._setNeedsCompilation(node, True)
            self._setNeedsEvaluation(node, True)
            self._setError(node, err)
            self._nodes[node].func = None
            self._setResult(node, None)
            return False
        except Exception as err:
            self._setNeedsCompilation(node, True)
            self._setNeedsEvaluation(node, True)
            self._setError(node, err)
            self._nodes[node].func = None
            self._setResult(node, None)
            return False
        else:
            self._setNeedsCompilation(node, False)
            self._setNeedsEvaluation(node, True)
            self._nodes[node].func = func

            sig = inspect.signature(func)
            new_parameters = []
            for idx, param in enumerate(sig.parameters.values()):
                # find stored field value
                value = Empty # default parameter value
                for parameter in self._nodes[node].parameters:
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
            self._setParameters(node, new_parameters)
            self._setError(node, None)
            self._setResult(node, None)
            return True

    def evaluate(self, nodes:Iterable[str], force=False)->bool:
        ### build temporary nx graph (TODO: store nodes and edges in a graph!)
        if isinstance(nodes, str):
            logger.warn("{nodes} is a string.")
        nodes = set(n for n in nodes)
        if not any(self.needsEvaluation(node) for node in nodes) and not force:
            return True

        ### append ancestors
        ### create subgraph
        G = self._toNetworkX()
        nodes = set(n for n in nodes)
        subgraph = cast(nx.MultiDiGraph, 
            G.subgraph( 
                nodes.union( 
                    *[nx.ancestors(G, n) for n in nodes]
                )
            )
        )
        
        ### sort nodes in topological order
        ordered_nodes = list(nx.topological_sort(subgraph))

        # make sure nodes are compiled
        for ancestor in ordered_nodes:
            success = self.compile(ancestor, force=False)
            if not success:
                return False

        ### evaluate nodes in reverse topological order
        from pylive.utils.evaluate_python import call_function_with_named_args
        for node in ordered_nodes:
            if not self.needsEvaluation(node) and not force:
                print(f"continue node: {node}")
                continue
            print(f"PyDataModel->evaluateNode {node}...")
            """evaluate nodes in topological order
            Stop and return _False_ when evaluation Fails.
            """
            ### Get function
            node_item = self._nodes[node]
            func = node_item.func
            assert func is not None, "if compilation as succesfull, func cant be None"

            ### GET FUNCTION ARGUMENTS
            ### from links
            named_args = dict()
            for source, target, outlet, inlet in self.inLinks(node):
                assert not self.needsEvaluation(source) and self.error(source) is None, "at this point dependencies must have been evaluated without errors!"
                named_args[inlet] = self.result(source)

            ### from fields
            for param_item in node_item.parameters:
                if param_item.name in named_args:
                    continue # skip connected fields
                if param_item.value != Empty:
                    named_args[param_item.name] = param_item.value

            ### Evaluate function
            try:
                result = call_function_with_named_args(func, named_args)
            except SyntaxError as err:
                self._setNeedsEvaluation(node, True)
                self._setError(node, err)
                self._setResult(node, None)
                print(f"             evaluateNode {node} ...failed!")
                return False
            except Exception as err:
                self._setNeedsEvaluation(node, True)
                self._setError(node, err)
                self._setResult(node, None)
                print(f"             evaluateNode {node} ...failed!")
                return False
            else:
                self._setNeedsEvaluation(node, False)
                self._setError(node, None)
                self._setResult(node, result)
            print(f"             evaluateNode {node} ...done!")

        return True

    def needsCompilation(self, node)->bool:
        return self._nodes[node].needs_compilation

    def _setNeedsCompilation(self, node:str, value:bool):
        if self._nodes[node].needs_compilation != value:
            self._nodes[node].needs_compilation = value
            self.needsCompilationChanged.emit(node)
            if value:
                self._setNeedsEvaluation(node, True)

    def needsEvaluation(self, node:str)->bool:
        return self._nodes[node].needs_evaluation

    def _setNeedsEvaluation(self, node:str, value:bool):
        if self._nodes[node].needs_evaluation != value:
            self._nodes[node].needs_evaluation = value
            self.needsEvaluationChanged.emit(node)
        if value:

            self.invalidated.emit([_ for _ in self.ancestors(node) | {node}])

    def error(self, node)->Exception|None:
        return self._nodes[node].error

    def result(self, node)->Any:
        return self._nodes[node].result

    def _setResult(self, node:str, value:Any):
        if self._nodes[node].result != value:
            self._nodes[node].result = value
            self.resultChanged.emit(node) 

    def _setError(self, node:str, value:Exception|None):
        if self._nodes[node].error != value:
            self._nodes[node].error = value
            self.errorChanged.emit(node)

    # Node parameters
    def parameterCount(self, node)->int:
        if not self._nodes:
            return 0
        return len(self._nodes[node].parameters)

    def hasParameter(self, node, param:str)->int:
        parameter_names = set()
        for i in range(self.parameterCount(node)):
            parameter_names.add(self.parameterName(node, i))

        return param in parameter_names

    def _setParameters(self, node:str, parameters:list[PyParameterItem]):
        self.parametersAboutToBeReset.emit(node)
        self._nodes[node].parameters = parameters
        self.parametersReset.emit(node)
        self._setNeedsEvaluation(node, True)

    def _insertParameter(self, node:str, index:int, parameter:PyParameterItem)->bool:
        self.parametersAboutToBeInserted.emit(node, index, index)
        self._nodes[node].parameters.insert(index, parameter)
        self.parametersInserted.emit(node, index, index)
        self._setNeedsEvaluation(node, True)
        return True

    def _removeParameter(self, node:str, index:int):
        self.parametersAboutToBeRemoved.emit(node, index, index)
        del self._nodes[node].parameters[index]
        self.parametersRemoved.emit(node, index, index)
        self._setNeedsEvaluation(node, True)

    def setParameterValue(self, node:str, index:int, value:object|None|Empty):
        if self._nodes[node].parameters[index].value != value:
            self._nodes[node].parameters[index].value = value
            self.patametersChanged.emit(node, index, index)
            self.setNeedsEvaluation(node, True)

    def _parameterItem(self, node:str, index:int)->PyParameterItem:
        return self._nodes[node].parameters[index]

    def parameterName(self, node:str, index:int)->str:
        return self._nodes[node].parameters[index].name

    def parameterValue(self, node:str, index:int)->object|None|Empty:
        return self._nodes[node].parameters[index].value

    ### helpers
    def _toNetworkX(self)->nx.MultiDiGraph:
        G = nx.MultiDiGraph()
        for node, item in self._nodes.items():
            G.add_node(node, item=item)
        for source, target, outlet, inlet in self._links:
            G.add_edge(source, target, (outlet, inlet))
        return G

    def ancestors(self, source:str)->set[str]:
        G = self._toNetworkX()
        return nx.ancestors(G, source) # | {node} # source 

    def descendants(self, source:str)->set[str]:
        G = self._toNetworkX()
        return nx.descendants(G, source) # | {node} # source 

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
        self._nodes = OrderedDict()

        links_from_parameters:set[tuple[str,str,str, str]] = set()
        for node_data in data['nodes']:
            parameters = []
            
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
                        item = PyParameterItem(name=name, value=value)
                        parameters.append(item)
        
            node_item = PyNodeItem(
                source=node_data['source'],
                parameters = parameters
            )
            self._nodes[node_data['name'].strip()] = node_item

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

        for node_name, node_item in self._nodes.items():
            node_data:dict[Literal['name', 'source', 'fields'], Any] = {
                'name': node_name,
                'source':node_item.source
            }

            fields_data = dict()
            for item in node_item.parameters:
                if item.value != Empty:
                    fields_data[item.name] = item.value

            
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

    def setAutoEvaluate(self, auto:bool):
        def autoEvaluateOnChange(changed:list[str]):
            dependencies = set()
            for node in changed:
                dependencies |= self.ancestors(node) | {node}

            if self._auto_evaluate_filter == None:
                self.evaluate(changed)
            else:
                if self._auto_evaluate_filter.intersection(changed):
                    self.evaluate(changed)

        self._auto_evaluate_connections = [
            # (self.graph_model.needsEvaluationChanged, lambda n: keepCurrentUpToDate(changed=[n]))
            (self.modelReset, lambda: autoEvaluateOnChange),
            (self.sourceChanged, lambda n: autoEvaluateOnChange([n])),
            (self.parametersReset, lambda n: autoEvaluateOnChange([n])),
            (self.parametersInserted, lambda n, f, l: autoEvaluateOnChange([n])),
            (self.patametersChanged,  lambda n, f, l: autoEvaluateOnChange([n])),
            (self.parametersRemoved,  lambda n, f, l: autoEvaluateOnChange([n])),

            (self.nodesLinked, lambda links: autoEvaluateOnChange( [link[1] for link in links] )),
            (self.nodesUnlinked, lambda links: autoEvaluateOnChange( [link[1] for link in links] ))
        ]

        for signal, slot in self._auto_evaluate_connections:
            signal.connect(slot)

    def setAutoEvaluateFilter(self, nodes:Iterable[str]):
        self._auto_evaluate_filter = set(n for n in nodes)
