
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
    source:str="def func():    ..."
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

    nameChanged = Signal(str)
    sourceChanged = Signal(str)
    fieldsChanged = Signal(str)

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

    def links(self)->Iterable[tuple[str,str,str]]:
        for source, target, inlet in self._links:
            yield source, target, inlet

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

    def setNodeName(self, node:str, new_name:str):
        raise NotImplementedError

    def setNodeSource(self, node:str, value:str):
        self._nodes[node].source = value

    def compileNode(self, node:str)->bool:
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
            for name, param in sig.parameters.items():
                param_item = PyParameterItem(
                    name=name, 
                    default=param.default,
                    annotation=param.annotation, 
                    kind=param.kind,
                    value=Empty
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

    def parameterValue(self, node:str, index:int, value:object|None|Empty)->object|None|Empty:
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
        self.blockSignals(True)
        self._node_index_by_name = dict() # keep node name as references for the edge relations
        for node_data in data['nodes']:
            if node_data['kind']!='UniqueFunction':
                raise NotImplementedError("for now, only 'UniqueFunction's are supported!")

            fields:dict = node_data.get('fields') or dict()
            parameters = []
            for name, value in fields.items():
                parameter_item = PyParameterItem(
                    name=name, 
                    default=Empty,
                    annotation=Empty,
                    kind='POSITIONAL_OR_KEYWORD',
                    value=value
                )
                parameters.append(parameter_item)

            fields:dict = node_data.get('fields') or dict()
            node_item = PyNodeItem(
                source=node_data['source'],
                parameters=parameters
            )
            self._nodes[node_data['name']] = node_item

        ### create edge items
        if data.get('edges', None):
            for edge in data['edges']:
                edge_item = (
                    edge['source'],
                    edge['target'],
                    edge['inlet']
                )
                self._links.add(edge_item)

        self.blockSignals(False)
        self.modelReset.emit()

        return True

    def serialize(self)->str:
        import yaml
        return yaml.dump({
            'nodes': [],
            'edges': []
        })


# class PyNodeSelectionModel(QObject):
#     modelChanged = Signal()
#     currentChanged = Signal(str, str) # current, previous
#     selectionChanged = Signal(list[str], list[str]) # selected, deselected

#     def __init__(self, model:PyDataModel, parent:QObject|None=None):
#         super().__init__(parent=parent)
#         self._model = model
#         self._nodes:list[str] = []

#     def setModel(self, model:PyDataModel):
#         if self._model:
#             self._model.nodesRemoved.disconnect(self._on_nodes_removed)

#         iel:
#             model.nodesRemoved.connect(self._on_nodes_removed)

#         self._model = model

#     def _on_nodes_removed(self):
#         assert self._model
#         nodes = self._model.nodes()
#         node_set = set(nodes)
#         new_selection = [name for name in nodes if name in node_set]
#         self.setSelection( new_selection )

#     def setSelection(self, selection:Sequence[str]):
#         selected = set(selection) - set(self._nodes)
#         deselected = set(self._nodes) - set(selection)
#         previous = self.currentNode()
#         self._nodes = [_ for _ in selection]

#         if len(selected)>0 or len(deselected)>0:
#             self.selectionChanged.emit(selected, deselected)
#         if previous != self.currentNode():
#             self.currentChanged.emit(self.currentNode(), previous)

#     def currentNode(self):
#         return self._nodes[-1]

#     def selectedNodes(self):
#         return [_ for _ in self._nodes]


# class PyNodeTableSelectionModel(QItemSelectionModel):
#     def __init__(self, model: PyNodeProxyModel, node_selection: PyNodeSelectionModel, parent: QObject | None = None):
#         super().__init__(model, parent)
#         self._node_selection = node_selection
#         self._proxy_model = model
        
#         # Connect QItemSelectionModel signals to update PyNodeSelectionModel
#         self.selectionChanged.connect(self._on_selection_changed)
#         self.currentChanged.connect(self._on_current_changed)
        
#         # Connect PyNodeSelectionModel signals to update QItemSelectionModel
#         self._node_selection.selectionChanged.connect(self._on_node_selection_changed)
#         self._node_selection.currentChanged.connect(self._on_node_current_changed)
        
#     def _on_selection_changed(self, selected: QItemSelection, deselected: QItemSelection):
#         """Handle changes in the table selection"""
#         # Block signals to prevent recursion
#         self._node_selection.blockSignals(True)
        
#         # Convert QItemSelection to node names
#         selected_nodes = self._proxy_model.mapSelectionToSource(selected)
        
#         # Update the node selection model
#         if selected_nodes:
#             self._node_selection.setSelection(selected_nodes)
            
#         self._node_selection.blockSignals(False)
        
#     def _on_current_changed(self, current: QModelIndex, previous: QModelIndex):
#         """Handle changes in the current item"""
#         if not current.isValid():
#             return
            
#         # Block signals to prevent recursion
#         self._node_selection.blockSignals(True)
        
#         # Get the node name from the proxy model
#         current_node = self._proxy_model.mapToSource(current)
        
#         # Update the current node in the node selection model
#         if current_node:
#             self._node_selection.setSelection([current_node])
            
#         self._node_selection.blockSignals(False)
        
#     def _on_node_selection_changed(self, selected: list[str], deselected: list[str]):
#         """Handle changes in the node selection model"""
#         # Block signals to prevent recursion
#         self.blockSignals(True)
        
#         # Convert node names to QItemSelection
#         selection = self._proxy_model.mapSelectionFromSource(selected)
        
#         # Update the table selection
#         self.select(selection, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        
#         self.blockSignals(False)
        
#     def _on_node_current_changed(self, current: str, previous: str):
#         """Handle changes in the current node"""
#         # Block signals to prevent recursion
#         self.blockSignals(True)
        
#         # Convert node name to model index
#         current_index = self._proxy_model.mapFromSource(current)
        
#         # Update the current index
#         self.setCurrentIndex(
#             current_index,
#             QItemSelectionModel.SelectionFlag.Current
#         )
        
#         self.blockSignals(False)