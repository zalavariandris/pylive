from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


from pathlib import Path
from pylive.utils.evaluate_python import parse_python_function


class PyGraphModel(QObject):
    modelReset = Signal()
    nodesInserted = Signal(QModelIndex, int, int)
    nodesAboutToBeRemoved = Signal(QModelIndex, int, int)
    nodeChanged = Signal(QModelIndex, QModelIndex, list)

    edgesReset = Signal()
    edgesInserted = Signal(QModelIndex, int, int)
    edgesAboutToBeRemoved = Signal(QModelIndex, int, int)
    edgeChanged = Signal(QModelIndex, QModelIndex, list)

    def __init__(self, parent:QObject|None=None):
        super().__init__(parent=parent)
        ### document state
        
    def nodes(self)->PyNodesModel:
        return self._nodes_model

    def edges(self)->StandardEdgesModel:
        return self._edges_model

    def nodeCount(self)->int:
        return self._nodes_model.rowCount()

    def edgeSource(self, node_row:int)->int:
        ...

    def edgeTarget(self, node_row:int)->int:
        ...

    def insertNodeItem(self, row:int, item:PyNodeItem):
        self._nodes_model.insertNodeItem(row, item)

    def nodeItem(self, row)->PyNodeItem:
        return self._nodes_model.nodeItem(row)

    def removeNodes(self, row:int, count:int):
        self._nodes_model.removeRows(row, count)

    def deserialize(self, text:str)->bool:
        import yaml
        data = yaml.load(text, Loader=yaml.SafeLoader)

        ### create node items
        _node_row_by_name = dict() # keep node name as references for the edge relations
        self._nodes_model.blockSignals(True)
        for row, node in enumerate(data['nodes']):
            if node['kind']!='UniqueFunction':
                raise NotImplementedError("for now, only 'UniqueFunction's are supported!")

            fields = node.get('fields') or dict({'f': 1})
            node_item = PyNodeItem(
                name=node['name'],
                code=node['source'],
                fields=fields
            )
            self._nodes_model.insertNodeItem(row, node_item)

            _node_row_by_name[node['name']] = row

        self._nodes_model.blockSignals(False)
        self._nodes_model.modelReset.emit()

        self._edges_model.blockSignals(True)
        if data.get('edges', None):
            for row, edge in enumerate(data['edges']):
                source_node_id = edge['source']
                target_node_id = edge['target']
                source_row = _node_row_by_name[source_node_id]
                target_row = _node_row_by_name[target_node_id]

                edge = StandardEdgeItem(
                    QPersistentModelIndex(self._nodes_model.index(source_row, 0)), 
                    QPersistentModelIndex(self._nodes_model.index(target_row, 0)), 
                    "out",
                    edge['inlet']
                )
                self._edges_model.appendEdgeItem(edge)

            self._edges_model.blockSignals(False)
        self._edges_model.modelReset.emit()

        return True

    def serialize(self)->str:
        import yaml
        return yaml.dump({
            'nodes': [],
            'edges': []
        })

    def load(self, path:Path|str):
        text = Path(path).read_text()
        self.deserialize(text)

    def save(self, path:Path|str):
        text = self.serialize()
        Path(path).write_text(text)

    def compileNode(self, row:int):
        node_item = self._nodes_model.nodeItem(row)

        try:
            func = parse_python_function(node_item.code)
        except SyntaxError as err:
            self._nodes_model.setDataByColumnName(row, "status", 'error')
            self._nodes_model.setDataByColumnName(row, 'func', None)
            self._nodes_model.setDataByColumnName(row, 'inlets', [])
            self._nodes_model.setDataByColumnName(row, 'error', err)
            self._nodes_model.setDataByColumnName(row, 'result', None)
            return False
        except Exception as err:
            self._nodes_model.setDataByColumnName(row, "status", 'error')
            self._nodes_model.setDataByColumnName(row, 'func', None)
            self._nodes_model.setDataByColumnName(row, 'inlets', [])
            self._nodes_model.setDataByColumnName(row, 'error', err)
            self._nodes_model.setDataByColumnName(row, 'result', None)
            return False
        else:
            self._nodes_model.setDataByColumnName(row, "status", 'compiled')
            self._nodes_model.setDataByColumnName(row, 'func', func)
            import inspect
            sig = inspect.signature(func)
            self._nodes_model.setDataByColumnName(row, 'inlets', [name for name, param in sig.parameters.items()])
            self._nodes_model.setDataByColumnName(row, 'error', None)
            return True

    def evaluateNode(self, row:int):
        """recursively evaluate nodes, from top to bottom"""
        from pylive.utils.evaluate_python import parse_python_function, call_function_with_stored_args
        node_item = self._nodes_model.nodeItem(row)

        ### load arguments from achestors
        kwargs = dict()
        for edge_item in self._edges_model.inEdges(row):
            kwargs[edge_item.inlet] = self.evaluateNode(edge_item.source.row())
            
        ### load arguments from fields
        for name, value in node_item.fields.items():
            if name in kwargs:
                continue # skip connected fields
            kwargs[name] = value

        # evaluate functions with 
        if not node_item.func:
            success = self.compileNode(row)
            if not success:
                return

        node_item = self._nodes_model.nodeItem(row)
        assert node_item.func
        try:
            result = call_function_with_stored_args(node_item.func, kwargs)
        except SyntaxError as err:
            self._nodes_model.setDataByColumnName(row, "status", 'error')
            self._nodes_model.setDataByColumnName(row, "result", None)
            self._nodes_model.setDataByColumnName(row, "error", err)
        except Exception as err:
            self._nodes_model.setDataByColumnName(row, "status", 'error')
            self._nodes_model.setDataByColumnName(row, "result", None)
            self._nodes_model.setDataByColumnName(row, "error", err)
        else:
            self._nodes_model.setDataByColumnName(row, "status", 'evaluated')
            self._nodes_model.setDataByColumnName(row, "result", result)
            self._nodes_model.setDataByColumnName(row, "error", None)
            return result


# class PyGraphNodesTableProxyModel(QAbstractItemModel):
#     def __init__(self, source_model:PyGraphModel, parent:QObject|None=None):
#         super().__init__(parent=parent)
#         self._source_model:PyGraphModel|None=None
#         self.setSourceModel(source_model)

#     def sourceModel(self)->PyGraphModel|None:
#         return self._source_model

#     def setSourceModel(self, source_model:PyGraphModel|None):
#         if self._source_model:
#             self._source_model.nodesReset.connect(self.modelReset.emit)
#             self._source_model.nodesInserted.disconnect(self.rowsInserted.emit)
#             self._source_model.nodesAboutToBeRemoved.disconnect(self.rowsAboutToBeRemoved.emit)
#             self._source_model.nodeChanged.disconnect(self.dataChanged.emit)

#         if source_model:
#             source_model.nodesReset.connect(self.modelReset.emit)
#             source_model.nodesInserted.connect(self.rowsInserted.emit)
#             source_model.nodesAboutToBeRemoved.connect(self.rowsAboutToBeRemoved.emit)
#             source_model.nodeChanged.connect(self._onSourceNodeChanged)

#         self._source_model = source_model
#         self.modelReset.emit()

#     def inlets(self, row:int)->Sequence[str]:
#         if not self._source_model:
#             return []
#         node_item = self._source_model.nodeItem(row)
#         return node_item.inlets

#     def outlets(self, row:int):
#         return ['out']

#     def rowCount(self, parent:QModelIndex|QPersistentModelIndex=QModelIndex())->int:
#         if self._source_model:
#             return self._source_model.nodeCount()
#         else:
#             return 0

#     def columnCount(self, parent:QModelIndex|QPersistentModelIndex=QModelIndex()):
#         return 9

#     def _onSourceNodeChanged(self, tl:QModelIndex, br:QModelIndex, roles=[]):
#         tl = self.index(tl.row(), tl.column())
#         br = self.index(br.row(), br.column())
#         self.dataChanged.emit(tl, br, roles)
            
#     def index(self, row:int, column:int, parent:QModelIndex|QPersistentModelIndex=QModelIndex()):
#         return self.createIndex(row, column)

#     def parent(self, child:QModelIndex|QPersistentModelIndex=QModelIndex())->QModelIndex:
#         return QModelIndex()

#     def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
#         if orientation == Qt.Orientation.Horizontal and role==Qt.ItemDataRole.DisplayRole:
#             return ["name", "code", "fields", "dirty", "status", "func", "inlets", "result", "error"][section]
#         else:
#             return super().headerData(section, orientation, role)

#     def data(self, index: QModelIndex|QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
#         if not self._source_model:
#             return None

#         if not index.isValid():# or not 0 <= index.row() < self.rowCount():
#             return None

#         node_item = self._source_model.nodeItem(index.row())

#         if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
#             attr = self.headerData(index.column(), Qt.Orientation.Horizontal)
#             value = getattr(node_item, attr)
#             return f"{value}"
           
#         return None


# class PyGraphEdgesTableProxyModel(QAbstractItemModel):
#     def __init__(self, source_model:PyGraphModel, parent:QObject|None=None):
#         super().__init__(parent=parent)
#         self._source_model:PyGraphModel|None=None
#         self.setSourceModel(source_model)

#     def sourceModel(self)->PyGraphModel|None:
#         return self._source_model

#     def setSourceModel(self, source_model:PyGraphModel|None):
#         if self._source_model:
#             self._source_model.edgesReset.connect(self.modelReset.emit)
#             self._source_model.edgesInserted.disconnect(self.rowsInserted.emit)
#             self._source_model.edgesAboutToBeRemoved.disconnect(self.rowsAboutToBeRemoved.emit)
#             self._source_model.edgeChanged.disconnect(self.dataChanged.emit)

#         if source_model:
#             source_model.nodesReset.connect(self.modelReset.emit)
#             source_model.nodesInserted.connect(self.rowsInserted.emit)
#             source_model.nodesAboutToBeRemoved.connect(self.rowsAboutToBeRemoved.emit)
#             source_model.nodeChanged.connect(self._onSourceNodeChanged)

#         self._source_model = source_model
#         self.modelReset.emit()

#     def _onSourceNodeChanged(self, tl:QModelIndex, br:QModelIndex, roles=[]):
#         tl = self.index(tl.row(), tl.column())
#         br = self.index(br.row(), br.column())
#         self.dataChanged.emit(tl, br, roles)
