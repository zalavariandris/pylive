
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


from pathlib import Path

from dataclasses import dataclass, field




@dataclass
class PyNodeItem:
    source:str="def func():    ..."
    fields: dict[str, str] = field(default_factory=dict)
    status:Literal['initalized', 'compiled', 'evaluated', 'error']='initalized'
    error:Exception|None=None
    result:object|None=None

from collections import OrderedDict


class PyDataModel(QObject):
    modelAboutToBeReset = Signal()
    modelReset = Signal()

    nodesAboutToBeAdded = Signal(list) # list of node names
    nodesAdded = Signal(list) # list of node names
    nodesAboutToBeRemoved = Signal(list) # list of node names
    nodesRemoved = Signal(list) # list of node names

    nameChanged = Signal()
    sourceChanged = Signal()
    fieldsChanged = Signal()

    statusChanged = Signal()
    errorChanged = Signal()
    resultChanged = Signal()

    nodesAboutToBeLinked = Signal(list) # list of edges: tuple[source, target, inlet]
    nodesLinked = Signal(list)
    nodesAboutToBeUnlinked = Signal(list)
    nodesUnlinked = Signal(list)

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

    def nodeFields(self, node)->Sequence[str]:
        return [_ for _ in self._nodes[node].fields.keys()]

    def nodeStatus(self, node)->Literal['initalized', 'compiled', 'evaluated', 'error']:
        return self._nodes[node].status

    def nodeError(self, node)->Exception|None:
        return self._nodes[node].error

    def nodeResult(self, node)->Any:
        return self._nodes[node].error

    def compileNode(self, node):
        ...

    def evaluateNode(self, node):
        ...

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
            node_item = PyNodeItem(
                source=node_data['source'],
                fields=fields
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