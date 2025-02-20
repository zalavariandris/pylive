
from sys import exec_prefix
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


from pathlib import Path

from dataclasses import dataclass, field
import inspect

import inspect

Empty = inspect.Parameter.empty

from yaml import resolver
@dataclass
class PyParameterItem:
    name: str
    default: Any=Empty #TODO: object|None|inspect.Parameter.empty
    annotation: str|Any='' # TODO str|inspect.Parameter.empty
    kind:inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD
    value: Any=Empty #TODO: object|None|inspect.Parameter.empty


@dataclass
class PyNodeItem:
    source:str="def func():\n    ..."
    parameters: list[PyParameterItem] = field(default_factory=list)
    status:Literal['initalized', 'compiled', 'evaluated', 'error']='initalized'
    error:Exception|None=None
    result:object|None=None
    _func:Callable|None=None # cache compiled function



from collections import OrderedDict, defaultdict


class PyDataModel(QObject):
    modelAboutToBeReset = Signal()
    modelReset = Signal()

    nodesAboutToBeAdded = Signal(list) # list of node names
    nodesAdded = Signal(list) # list of node names
    nodesAboutToBeRemoved = Signal(list) # list of node names
    nodesRemoved = Signal(list) # list of node names

    sourceChanged = Signal(str)

    statusChanged = Signal(str)
    errorChanged = Signal(str)
    resultChanged = Signal(str)

    nodesAboutToBeLinked = Signal(list) # list of edges: tuple[source, target, inlet]
    nodesLinked = Signal(list)
    nodesAboutToBeUnlinked = Signal(list)
    nodesUnlinked = Signal(list)

    parametersAboutToBeReset = Signal(str)
    parametersReset = Signal(str)
    parametersAboutToBeInserted = Signal(str, int, int) # node, start, end
    parametersInserted = Signal(str, int, int) # node, start, end
    patametersChanged = Signal(str, int, int) # node, first, last
    parametersAboutToBeRemoved = Signal(str, int, int) # node, start, end
    parametersRemoved = Signal(str, int, int) # node, start, end

    def __init__(self, parent:QObject|None=None):
        super().__init__(parent=parent)
        self._nodes:OrderedDict[str, PyNodeItem] = OrderedDict()
        self._links:set[tuple[str,str,str]] = set()

    def nodeCount(self)->int:
        return len(self._nodes)

    def nodes(self)->Collection[str]:
        return [_ for _ in self._nodes.keys()]

    def links(self)->Collection[tuple[str,str,str]]:
        return [_ for _ in self._links]

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
        self.nodesAboutToBeRemoved.emit([name])
        del self._nodes[name]
        self.nodesRemoved.emit([name])

    def linkCount(self):
        return len(self._links)

    def linkNodes(self, source:str, target:str, inlet:str):
        self.nodesAboutToBeLinked.emit( [(source, target, inlet)] )
        self._links.add( (source, target, inlet) )
        self.nodesLinked.emit([(source, target, inlet)])

    def unlinkNodes(self, source:str, target:str, inlet:str):
        self.nodesAboutToBeUnlinked.emit([(source, target, inlet)])
        self._links.remove( (source, target, inlet) )
        self.nodesUnlinked.emit([(source, target, inlet)])

    def nodeSource(self, name:str)->str:
        return self._nodes[name].source

    def setNodeSource(self, node:str, value:str):
        if self._nodes[node].source != value:
            self._nodes[node].source = value
            self.sourceChanged.emit(node)

    def compileNodes(self, nodes:Iterable[str]):
        def _compile_node(node):
            node_item = self._nodes[node]
            new_parameters:list[PyParameterItem]|None = None

            try:
                from pylive.utils.evaluate_python import parse_python_function
                func = parse_python_function(node_item.source)
            except SyntaxError as err:
                new_status = 'error'
                new_error = err
                new__func = None
                new_result = None
            except Exception as err:
                new_status = 'error'
                new_error = err
                new__func = None
                new_result = None
            else:
                new_status = 'compiled'
                new__func = func
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

            if node_item.status != new_status:
                node_item.status = new_status
                self.statusChanged.emit(node)
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

        for node in nodes:
            _compile_node(node)


    def parameterCount(self, node)->int:
        if not self._nodes:
            return 0
        return len(self._nodes[node].parameters)

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
        self._nodes[node].parameters[index].value = value
        self.patametersChanged.emit(node, index, index)

    def parameterItem(self, node:str, index:int)->PyParameterItem:
        return self._nodes[node].parameters[index]

    def parameterName(self, node:str, index:int)->object|None|Empty:
        return self._nodes[node].parameters[index].name

    def parameterValue(self, node:str, index:int)->object|None|Empty:
        return self._nodes[node].parameters[index].value

    def nodeStatus(self, node)->Literal['initalized', 'compiled', 'evaluated', 'error']:
        return self._nodes[node].status

    def evaluateNode(self, node):
        ...

    def nodeError(self, node)->Exception|None:
        return self._nodes[node].error

    def nodeResult(self, node)->Any:
        return self._nodes[node].error

    def load(self, path:Path|str):
        text = Path(path).read_text()
        self.deserialize(text)

    def save(self, path:Path|str):
        text = self.serialize()
        Path(path).write_text(text)

    def deserialize(self, text:str)->bool:
        import yaml
        data = yaml.load(text, Loader=yaml.SafeLoader)
        self.modelAboutToBeReset.emit()

        ### create node items
        self._nodes = OrderedDict()

        for node_data in data['nodes']:
            if fields:=node_data.get('fields'):
                parameters = list(map(lambda name: PyParameterItem(name=name, value=fields[name]), fields))
            else:
                parameters = []
        
            node_item = PyNodeItem(
                source=node_data['source'],
                parameters=parameters
            )
            self._nodes[node_data['name']] = node_item

        ### create edge items
        def linkFromData(data:dict)->tuple[str,str,str]:
            return (
                data['source'],
                data['target'],
                data['inlet']
            )

        if data.get('edges', None):
            self._links = set( map(linkFromData, data.get('edges')) )
        else:
            self._links = set()

        self.modelReset.emit()

        return True

    def serialize(self)->str:
        import yaml
        return yaml.dump({
            'nodes': [],
            'edges': []
        })


