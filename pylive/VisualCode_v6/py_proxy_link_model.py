from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


from pylive.VisualCode_v5.py_graph_model import PyGraphModel
from pylive.utils import group_consecutive_numbers


class PyProxyLinkModel(QAbstractItemModel):
    def __init__(self, source_model:PyGraphModel, parent:QObject|None=None):
        super().__init__(parent=parent)
        self._links:list[tuple[str, str, str, str]] = list()
        self._source_model:PyGraphModel|None=None

        self._model_connections = []
        self.setSourceModel(source_model)

        self._headers = ['source', 'target', 'outlet', 'inlet']

    def setSourceModel(self, source_model:PyGraphModel|None):
        if self._source_model:
            for signal, slot in self._model_connections:
                signal.disconnect(slot)
            self._model_connections = []

        if source_model:
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

    def _on_source_nodes_about_to_be_linked(self, links:list[tuple[str,str,str,str]]):
        first = len(self._links)
        last = first+len(links)-1
        self.rowsAboutToBeInserted.emit(QModelIndex(), first, last)

    def _on_source_nodes_linked(self, links:list[tuple[str,str,str,str]]):
        first = len(self._links)
        last = first+len(links)-1
        for row, link in enumerate(links, start=first):
            self._links.insert(row, link)
        self.rowsInserted.emit(QModelIndex(), first, last)

    def _on_source_nodes_about_to_be_unlinked(self, links:list[tuple[str,str,str,str]]):
        indexes = [self.mapFromSource(link) for link in links]
        rows = set([idx.row() for idx in indexes])
        ranges = list(group_consecutive_numbers(sorted(rows)))
        for r in reversed(ranges):
            self.rowsAboutToBeRemoved.emit(QModelIndex(), r.start, r.stop-1)

    def _on_source_nodes_unlinked(self, links:list[tuple[str,str,str,str]]):
        indexes = [self.mapFromSource(link) for link in links]
        rows = set([idx.row() for idx in indexes])
        ranges = list(group_consecutive_numbers(sorted(rows)))
        for range_group in reversed(ranges):
            for row in reversed(range_group):
                del self._links[row]
            self.rowsRemoved.emit(QModelIndex(), range_group.start, range_group.stop-1)

    # Proxy functions
    def mapFromSource(self, link:tuple[str,str,str,str])->QModelIndex:
        row = self._links.index(link)
        return self.index(row, 0)

    def mapToSource(self, proxy:QModelIndex|QPersistentModelIndex)->tuple[str, str, str, str]:
        link = self._links[proxy.row()]
        return link

    def mapSelectionFromSource(self, links:Sequence[tuple[str, str, str, str]])->QItemSelection:
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

    def mapSelectionToSource(self, proxySelection: QItemSelection)->Sequence[tuple[str, str, str, str]]:
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

        source, target, outlet, inlet = self.mapToSource(index)

        column_name = self._headers[index.column()]
        match column_name:
            case 'source':
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return source

            case 'target':
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return target

            case 'outlet':
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return outlet

            case 'inlet':
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return inlet

            case _:
                raise ValueError("bad column name")

        return None
