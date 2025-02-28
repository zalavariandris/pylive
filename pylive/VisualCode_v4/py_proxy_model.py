from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from pylive.utils import group_consecutive_numbers

from pylive.VisualCode_v4.py_data_model import Empty, PyDataModel



class PyProxyNodeModel(QAbstractItemModel):
    _headers = ['name', 'source', 'parameters', 'compiled', 'evaluated', 'error', 'result']
    def __init__(self, source_model:PyDataModel, parent:QObject|None=None):
        super().__init__(parent=parent)
        self._nodes:list[str] = list()
        self._source_model:PyDataModel|None=None

        self.setSourceModel(source_model)

    def setSourceModel(self, source_model:PyDataModel):
        if self._source_model:
            self._source_model.modelAboutToBeReset.disconnect(self.modelAboutToBeReset.emit)
            self._source_model.modelReset.disconnect(self._resetModel)
            self._source_model.nodesAboutToBeAdded.disconnect(self._on_source_nodes_about_to_be_added)
            self._source_model.nodesAdded.disconnect(self._on_source_nodes_added)
            self._source_model.nodesAboutToBeRemoved.disconnect(self._on_source_nodes_about_to_be_removed)
            self._source_model.nodesRemoved.disconnect(self._on_source_nodes_removed)

        if source_model:
            source_model.modelAboutToBeReset.connect(self.modelAboutToBeReset.emit)
            source_model.modelReset.connect(self._resetModel)
            source_model.nodesAboutToBeAdded.connect(self._on_source_nodes_about_to_be_added)
            source_model.nodesAdded.connect(self._on_source_nodes_added)
            source_model.nodesAboutToBeRemoved.connect(self._on_source_nodes_about_to_be_removed)
            source_model.nodesRemoved.connect(self._on_source_nodes_removed)

            source_model.sourceChanged.connect(self._on_source_changed)
            source_model.parametersReset.connect(self._on_parameters_reset)
            source_model.compiledChanged.connect(self._on_compiled_changed)
            source_model.evaluatedChanged.connect(self._on_evaluated_changed)
            source_model.errorChanged.connect(self._on_error_changed)
            source_model.resultChanged.connect(self._on_result_changed)

        self._source_model = source_model
        self._resetModel()

    def _on_source_changed(self, node:str):
        index = self.mapFromSource(node).siblingAtColumn(self._headers.index('source'))
        self.dataChanged.emit(index, index, [])

    def _on_parameters_reset(self, node:str):
        index = self.mapFromSource(node).siblingAtColumn(self._headers.index('parameters'))
        self.dataChanged.emit(index, index, [])

    def _on_compiled_changed(self, node:str):
        index = self.mapFromSource(node).siblingAtColumn(self._headers.index('compiled'))
        self.dataChanged.emit(index, index, [])

    def _on_evaluated_changed(self, node:str):
        index = self.mapFromSource(node).siblingAtColumn(self._headers.index('evaluated'))
        self.dataChanged.emit(index, index, [])

    def _on_error_changed(self, node:str):
        index = self.mapFromSource(node).siblingAtColumn(self._headers.index('error'))
        self.dataChanged.emit(index, index, [])

    def _on_result_changed(self, node:str):
        index = self.mapFromSource(node).siblingAtColumn(self._headers.index('result'))
        self.dataChanged.emit(index, index, [])

    def _resetModel(self):
        assert self._source_model
        self.beginResetModel()
        self._nodes.clear()
        for row, node in enumerate(self._source_model.nodes()):
            self._nodes.insert(row, node)

        self.modelReset.emit()
        self.endResetModel()

    def _on_source_nodes_about_to_be_added(self, nodes:list[str]):
        first = len(self._nodes)
        last = first+len(nodes)-1
        self.rowsAboutToBeInserted.emit(QModelIndex(), first, last)

    def _on_source_nodes_added(self, nodes:list[str]):
        first = len(self._nodes)
        last = first+len(nodes)-1
        for row, node in enumerate(nodes, start=first):
            self._nodes.insert(row, node)
        self.rowsInserted.emit(QModelIndex(), first, last)

    def _on_source_nodes_about_to_be_removed(self, nodes:list[str]):
        indexes = [self.mapFromSource(node) for node in nodes]
        rows = set([idx.row() for idx in indexes])
        ranges = list(group_consecutive_numbers(sorted(rows)))
        for r in reversed(ranges):
            self.rowsAboutToBeRemoved.emit(QModelIndex(), r.start, r.stop-1)

    def _on_source_nodes_removed(self, nodes:list[str]):
        indexes = [self.mapFromSource(node) for node in nodes]
        rows = set([idx.row() for idx in indexes])
        ranges = list(group_consecutive_numbers(sorted(rows)))
        for range_group in reversed(ranges):
            for row in reversed(range_group):
                del self._nodes[row]
            self.rowsRemoved.emit(QModelIndex(), range_group.start, range_group.stop-1)

    # Proxy functions
    def mapFromSource(self, node:str)->QModelIndex:
        row = self._nodes.index(node)
        index = self.index(row, 0)
        assert index.isValid()
        return index

    def mapToSource(self, proxy:QModelIndex|QPersistentModelIndex)->str:
        if not proxy.isValid():
            raise ValueError("proxy index is invalid: ", proxy)
        node = self._nodes[proxy.row()]
        return node

    def mapSelectionFromSource(self, nodes:Sequence[str])->QItemSelection:
        rows = sorted([self.mapFromSource(node).row() for node in nodes])
        ranges = group_consecutive_numbers(list(rows))

        item_selection = QItemSelection()
        for r in ranges:
            r.start
            r.stop

            selection_range = QItemSelectionRange(
                self.index(r.start, 0), 
                self.index(r.stop-1, self.columnCount()-1)
            )

            item_selection.append(selection_range)

        return item_selection

    def mapSelectionToSource(self, proxySelection: QItemSelection)->Sequence[str]:
        """on selection model changed"""

        ### update widgets seleection
        selected_indexes = proxySelection.indexes()
        selected_rows = set([idx.row() for idx in selected_indexes])

        selected_nodes = [self.mapToSource(self.index(row, 0)) for row in selected_rows]
        return selected_nodes

    # read functions
    def index(self, row:int, column:int, parent:QModelIndex|QPersistentModelIndex=QModelIndex()):
        if not self._source_model:
            return QModelIndex()
        node = self._nodes[row]
        index = self.createIndex(row, column, node) # consider storing the index of the node
        assert index.isValid()
        return index

    def parent(self, index:QModelIndex)->QModelIndex:
        return QModelIndex()

    def rowCount(self, parent:QModelIndex|QPersistentModelIndex=QModelIndex())->int:
        if not self._source_model:
            return 0
        return len(self._nodes)

    def columnCount(self, parent:QModelIndex|QPersistentModelIndex=QModelIndex())->int:
        return 6

    def headerData(self, section: int, orientation: Qt.Orientation, role:int=Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                return self._headers[section]
        return super().headerData(section, orientation, role)

    def data(self, index:QModelIndex|QPersistentModelIndex, role:int=Qt.ItemDataRole.DisplayRole)->Any:
        if not self._source_model:
            return None

        node_name = self.mapToSource(index)
        if role == GraphDataRole.NodeInletsRole:
            # Todo: consider using map or comprehension
            parameter_names = []
            for i in range(self._source_model.parameterCount(node_name)):
                param_name = self._source_model.parameterName(node_name, i)
                parameter_names.append(param_name)
            return parameter_names

        if role == GraphDataRole.NodeOutletsRole:
            return ['out']

        column_name = self._headers[index.column()]

        match column_name:
            case 'name':
                if role == Qt.ItemDataRole.DisplayRole:
                    return node_name.replace("_", " ").title()

                elif role == Qt.ItemDataRole.EditRole:
                    return node_name

            case 'source':
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return self._source_model.nodeSource(node_name)

            case 'parameters':
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    parameter_names = []
                    for i in range(self._source_model.parameterCount(node_name)):
                        name = self._source_model.parameterName(node_name, i)
                        parameter_names.append(name)
                    return ",".join( parameter_names )

            case 'compiled':
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return self._source_model.isCompiled(node_name)

            case 'evaluated':
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return self._source_model.isEvaluated(node_name)

            case 'error':
                if role == Qt.ItemDataRole.DisplayRole:
                    return f"{self._source_model.nodeError(node_name)}"
                elif role ==  Qt.ItemDataRole.EditRole:
                    return self._source_model.nodeError(node_name)

            case 'result':
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return f"{self._source_model.nodeResult(node_name)}"
            case _:
                raise ValueError(f"column {index.column()} is not in headers: {self._headers}")

        return None

from pylive.VisualCode_v4.graph_editor.graph_data_roles import GraphDataRole
class PyProxyLinkModel(QAbstractItemModel):
    def __init__(self, source_model:PyDataModel, parent:QObject|None=None):
        super().__init__(parent=parent)
        self._links:list[tuple[str, str, str]] = list()

        self._items_model:PyProxyNodeModel|None=None
        self._source_model:PyDataModel|None=None

        self._model_connections = []
        self.setSourceModel(source_model)

        self._headers = ['source', 'target', 'inlet']

    def itemsModel(self)->PyProxyNodeModel|None:
        return self._items_model

    def setSourceModel(self, source_model:PyDataModel|None):
        if self._source_model:
            for signal, slot in self._model_connections:
                signal.disconnect(slot)
            self._model_connections = []
            assert self._items_model
            self._items_model.modelReset.disconnect(self._resetModel)
            self._items_model = None

        if source_model:
            self._items_model = PyProxyNodeModel(source_model)
            self._items_model.modelReset.connect(self._resetModel)
            self._model_connections = [
                (source_model.modelReset, self._resetModel),
                (source_model.nodesAboutToBeLinked, self._on_source_nodes_about_to_be_linked),
                (source_model.nodesLinked, self._on_source_nodes_linked),
                (source_model.nodesAboutToBeUnlinked, self._on_source_nodes_about_to_be_unlinked),
                (source_model.nodesUnlinked, self._on_source_nodes_unlinked)
            ]
            for signal, slot in self._model_connections:
                signal.connect(slot)

        self._source_model = source_model
        self._resetModel()

    def _resetModel(self):
        assert self._source_model
        self.beginResetModel()
        self._links.clear()
        for row, link in enumerate(self._source_model.links()):
            self._links.insert(row, link)
        self.endResetModel()

    def _on_source_nodes_about_to_be_linked(self, links:list[tuple[str,str,str]]):
        first = len(self._links)
        last = first+len(links)-1
        self.rowsAboutToBeInserted.emit(QModelIndex(), first, last)

    def _on_source_nodes_linked(self, links:list[tuple[str,str,str]]):
        first = len(self._links)
        last = first+len(links)-1
        for row, link in enumerate(links, start=first):
            self._links.insert(row, link)
        self.rowsInserted.emit(QModelIndex(), first, last)

    def _on_source_nodes_about_to_be_unlinked(self, links:list[tuple[str,str,str]]):
        indexes = [self.mapFromSource(link) for link in links]
        rows = set([idx.row() for idx in indexes])
        ranges = list(group_consecutive_numbers(sorted(rows)))
        for r in reversed(ranges):
            self.rowsAboutToBeRemoved.emit(QModelIndex(), r.start, r.stop-1)

    def _on_source_nodes_unlinked(self, links:list[tuple[str,str,str]]):
        indexes = [self.mapFromSource(link) for link in links]
        rows = set([idx.row() for idx in indexes])
        ranges = list(group_consecutive_numbers(sorted(rows)))
        for range_group in reversed(ranges):
            for row in reversed(range_group):
                del self._links[row]
            self.rowsRemoved.emit(QModelIndex(), range_group.start, range_group.stop-1)

    # Proxy functions
    def mapFromSource(self, link:tuple[str,str,str])->QModelIndex:
        row = self._links.index(link)
        return self.index(row, 0)

    def mapToSource(self, proxy:QModelIndex|QPersistentModelIndex)->tuple[str, str, str]:
        link = self._links[proxy.row()]
        return link

    def mapSelectionFromSource(self, links:Sequence[tuple[str, str, str]])->QItemSelection:
        rows = sorted([self.mapFromSource(link).row() for link in links])
        ranges = group_consecutive_numbers(list(rows))

        item_selection = QItemSelection()
        for r in ranges:
            r.start
            r.stop

            selection_range = QItemSelectionRange(
                self.index(r.start, 0), 
                self.index(r.stop, self.columnCount()-1)
            )

            item_selection.append(selection_range)

        return item_selection

    def mapSelectionToSource(self, proxySelection: QItemSelection)->Sequence[tuple[str, str,str]]:
        """on selection model changed"""

        ### update widgets seleection
        selected_indexes = proxySelection.indexes()
        selected_rows = set([idx.row() for idx in selected_indexes])

        selected_links = [self.mapToSource(self.index(row, 0)) for row in selected_rows]
        return selected_links

    # read functions
    def index(self, row:int, column:int, parent:QModelIndex|QPersistentModelIndex=QModelIndex()):
        if not self._source_model:
            return QModelIndex()
        link = self._links[row]
        index = self.createIndex(row, column, link) # consider storing the index of the node
        assert index.isValid()
        return index

    def parent(self, index:QModelIndex)->QModelIndex:
        return QModelIndex()

    def rowCount(self, parent:QModelIndex|QPersistentModelIndex=QModelIndex())->int:
        if not self._source_model:
            return 0
        return len(self._links)

    def columnCount(self, parent:QModelIndex|QPersistentModelIndex=QModelIndex())->int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role:int=Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                return self._headers[section]
        return super().headerData(section, orientation, role)

    def data(self, index:QModelIndex|QPersistentModelIndex, role:int=Qt.ItemDataRole.DisplayRole)->Any:
        if not self._source_model:
            return None

        if not self._items_model:
            return None

        source, target, inlet = self.mapToSource(index)

        if role == GraphDataRole.LinkSourceRole:
            return self._items_model.mapFromSource(source), "out"

        if role == GraphDataRole.LinkTargetRole:
            return self._items_model.mapFromSource(target), inlet

        column_name = self._headers[index.column()]
        match column_name:
            case 'source':
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return source

            case 'target':
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return target

            case 'inlet':
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return inlet

            case _:
                raise ValueError("bad column name")

        return None


class PyProxyParameterModel(QAbstractItemModel):
    def __init__(self, source_model:PyDataModel, parent:QObject|None=None):
        super().__init__(parent=parent)
        self._source_model:PyDataModel|None=None
        self._node:str|None = None
        self._headers = ["name", "value"]

        self.setSourceModel(source_model)

    def setSourceModel(self, source_model:PyDataModel):
        if self._source_model:
            self._source_model.modelAboutToBeReset.disconnect(self.modelAboutToBeReset.emit)
            self._source_model.modelReset.disconnect(self._resetModel)

            self._source_model.parametersAboutToBeReset.disconnect(self.modelAboutToBeReset.emit)
            self._source_model.parametersReset.disconnect(self._resetModel)
            self._source_model.parametersAboutToBeInserted.disconnect(self._on_parameters_about_to_be_inserted)
            self._source_model.parametersInserted.disconnect(self._on_parameters_inserted)
            self._source_model.parametersAboutToBeRemoved.disconnect(self._on_parameters_about_to_be_removed)
            self._source_model.parametersRemoved.disconnect(self._on_parameters_removed)
            self._source_model.patametersChanged.disconnect(self._on_parameters_changed)

        if source_model:
            source_model.parametersAboutToBeReset.connect(self.modelAboutToBeReset.emit)
            source_model.parametersReset.connect(self._resetModel)
            source_model.parametersAboutToBeInserted.connect(self._on_parameters_about_to_be_inserted)
            source_model.parametersInserted.connect(self._on_parameters_inserted)
            source_model.parametersAboutToBeRemoved.connect(self._on_parameters_about_to_be_removed)
            source_model.parametersRemoved.connect(self._on_parameters_removed)
            source_model.patametersChanged.connect(self._on_parameters_changed)
            
        self._source_model = source_model
        self._resetModel()

    def _resetModel(self):
        self.beginResetModel()
        self.endResetModel()
        # self.modelAboutToBeReset.emit()
        # self.modelReset.emit()

    def setNode(self, node:str|None):
        self.modelAboutToBeReset.emit()
        self._node = node
        self.modelReset.emit()

    def _on_parameters_about_to_be_inserted(self, node:str, start:int, end:int):
        if self._node and self._node==node:
            self.rowsAboutToBeInserted.emit(QModelIndex(), start, end)

    def _on_parameters_inserted(self, node:str, first:int, last:int):
        if self._node and self._node==node:
            self.rowsInserted.emit(QModelIndex(), first, last)

    def _on_parameters_about_to_be_removed(self, node:str, first:int, last:int):
        if self._node and self._node==node:
            self.rowsAboutToBeRemoved.emit(QModelIndex(), first, last)

    def _on_parameters_removed(self, node:str, first:int, last:int):
        if self._node and self._node==node:
            self.rowsRemoved.emit(QModelIndex(), first, last)

    def _on_parameters_changed(self, node:str, first:int, last:int):
        if self._node and self._node==node:
            self.dataChanged.emit(QModelIndex(), self.index(first, 0), self.index(last, 1))

    def rowCount(self, parent:QModelIndex|QPersistentModelIndex=QModelIndex())->int:
        if not self._source_model or not self._node:
            return 0
        return self._source_model.parameterCount(self._node)

    def columnCount(self, parent:QModelIndex|QPersistentModelIndex=QModelIndex())->int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role:int=Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                return self._headers[section]
        return super().headerData(section, orientation, role)

    def data(self, index:QModelIndex|QPersistentModelIndex, role:int=Qt.ItemDataRole.DisplayRole):
        if not self._source_model or not self._node:
            return None

        parameter = self._source_model.parameterItem(self._node, index.row())
        column_name = self._headers[index.column()]
        match column_name:
            case 'name':
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return parameter.name

            case 'value':
                match role:
                    case Qt.ItemDataRole.DisplayRole:
                        if parameter.value is Empty:
                            return "-Empty-"
                        else:
                            return f"{parameter.value}"

                    case Qt.ItemDataRole.EditRole:
                        return parameter.value

    def flags(self, index: QModelIndex | QPersistentModelIndex, /) -> Qt.ItemFlag:
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        column_name = self._headers[index.column()]
        match column_name:
            case 'value':
                flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def setData(self, index:QModelIndex|QPersistentModelIndex, value:Any, role:int=Qt.ItemDataRole.DisplayRole)->bool:
        if not self._source_model or not self._node:
            return False

        parameter = self._source_model.parameterItem(self._node, index.row())
        column_name = self._headers[index.column()]
        match column_name:
            case 'value':
                if role == Qt.ItemDataRole.EditRole:
                    self._source_model.setParameterValue(self._node, index.row(), value)
                    return True
        return False
                    
    def index(self, row:int, column:int, parent:QModelIndex|QPersistentModelIndex=QModelIndex()):
        if not self._source_model or not self._node:
            return QModelIndex()
        parameter_item = self._source_model.parameterItem(self._node, row)
        return self.createIndex(row, column, parameter_item)

    def parent(self, index:QModelIndex)->QModelIndex:
        return QModelIndex()