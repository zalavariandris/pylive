from ast import Expression
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


from pylive.VisualCode_v6.py_graph_model import PyGraphModel
from pylive.utils import group_consecutive_numbers


class PyProxyNodeModel(QAbstractItemModel):
    _headers = ['name', 'kind', 'content', 'inlets', 'outlets', 'result']
    def __init__(self, source_model:PyGraphModel|None=None, parent:QObject|None=None):
        super().__init__(parent=parent)
        self._nodes:list[str] = list()
        self._source_model:PyGraphModel|None=None

        self._connections = []
        if source_model:
            self.setSourceModel(source_model)

    def setSourceModel(self, source_model:PyGraphModel|None):
        if self._source_model:
            for signal, slot in self._connections:
                signal.disconnect(slot)

        if source_model:
            def emit_inlets_changed(nodes):
                for node in nodes:
                    row = self.mapFromSource(node).row()
                    index = self.index(row, self._headers.index('inlets'))
                    self.dataChanged.emit(index, index, [])

            self._connections = [
                (source_model.modelAboutToBeReset, self.modelAboutToBeReset.emit),
                (source_model.modelReset, self._resetModel),
                (source_model.nodesAboutToBeAdded, self._on_source_nodes_about_to_be_added),
                (source_model.nodesAdded, self._on_source_nodes_added),
                (source_model.nodesAboutToBeRemoved, self._on_source_nodes_about_to_be_removed),
                (source_model.nodesRemoved, self._on_source_nodes_removed),
                (source_model.dataChanged, lambda nodes, hints: self._on_data_changed(nodes, hints)),
                (source_model.inletsReset, lambda nodes: emit_inlets_changed(nodes))
            ]

            for signal, slot in self._connections:
                signal.connect(slot)

        self._source_model = source_model
        self._resetModel()

    def _on_data_changed(self, nodes:list[str], hints:list[str]):
        for node in nodes:
            row = self.mapFromSource(node).row()
            if not hints:
                self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount()-1), [])
            else:
                columns = []
                for hint in hints:
                    column = self._headers.index(hint)
                    columns.append(column)
                columns.sort()
                self.dataChanged.emit(self.index(row, columns[0]), self.index(row, columns[-1]), [])

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

    def mapToSource(self, proxy:QModelIndex|QPersistentModelIndex)->str|None:
        if not proxy.isValid():
            return None
        node = self._nodes[proxy.row()]
        return node

    def mapSelectionFromSource(self, nodes:Sequence[str])->QItemSelection:
        rows = sorted([self.mapFromSource(node).row() for node in nodes])
        ranges = group_consecutive_numbers(list(rows))

        item_selection = QItemSelection()
        for r in ranges:
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
        # assert index.isValid()
        return index

    def parent(self, index:QModelIndex)->QModelIndex:
        return QModelIndex()

    def rowCount(self, parent:QModelIndex|QPersistentModelIndex=QModelIndex())->int:
        if not self._source_model:
            return 0
        return len(self._nodes)

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

        if not index.isValid():
            return None

        node_name = self.mapToSource(index)
        column_name = self._headers[index.column()]

        match column_name:
            case 'name':
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return node_name

            case 'kind':
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return self._source_model.data(node_name, 'kind')

            case 'content':
                kind = self._source_model.data(node_name, 'kind', Qt.ItemDataRole.EditRole)
                value = self._source_model.data(node_name, 'content', Qt.ItemDataRole.EditRole)

                if role == Qt.ItemDataRole.DisplayRole:
                    return f"{value}"

                if role == Qt.ItemDataRole.EditRole:
                    return value

            case 'inlets':
                if role == Qt.ItemDataRole.DisplayRole:
                    return ",".join( self._source_model.inlets(node_name) )

                elif role == Qt.ItemDataRole.EditRole:
                    return self._source_model.inlets(node_name)

            case 'outlets':
                if role == Qt.ItemDataRole.DisplayRole:
                    return ",".join( self._source_model.outlets(node_name) )

                elif role == Qt.ItemDataRole.EditRole:
                    return self._source_model.outlets(node_name)

            case 'result':
                if role == Qt.ItemDataRole.DisplayRole:
                    return f"{self._source_model.data(node_name, 'result')}"
                if role == Qt.ItemDataRole.EditRole:
                    return self._source_model.data(node_name, 'result', Qt.ItemDataRole.EditRole)

            case _:
                raise ValueError(f"column {index.column()} is not in headers: {self._headers}")

        return None

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

        if index.column()==self._headers.index('kind'):
            flags|=Qt.ItemFlag.ItemIsEditable

        if index.column()==self._headers.index('content'):
            flags|=Qt.ItemFlag.ItemIsEditable
            
        return flags

    def setData(self, index: QModelIndex | QPersistentModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not self._source_model:
            return False

        node_name = self.mapToSource(index)
        column_name = self._headers[index.column()]

        match column_name:
            case 'kind':
                if role == Qt.ItemDataRole.EditRole:
                    self._source_model.setData(node_name, 'kind', value)
                    return True

            case 'content':
                if role == Qt.ItemDataRole.EditRole:
                    self._source_model.setData(node_name, 'content', value)
                    return True

            case _:
                raise ValueError(f"column {index.column()} is not editable")

        return False