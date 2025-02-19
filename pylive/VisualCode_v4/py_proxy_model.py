from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from bidict import bidict
from pylive.utils import group_consecutive_numbers

from pylive.VisualCode_v4.py_data_model import PyDataModel

class PyNodeProxyModel(QAbstractItemModel):
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
            
        self._source_model = source_model
        self._resetModel()

    def _resetModel(self):
        assert self._source_model
        self._nodes.clear()
        for row, node in enumerate(self._source_model.nodes()):
            self._nodes.insert(row, node)
        self.modelReset.emit()

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
            self.rowsAboutToBeRemoved.emit(QModelIndex(), r.start, r.stop)

    def _on_source_nodes_removed(self, nodes:list[str]):
        indexes = [self.mapFromSource(node) for node in nodes]
        rows = set([idx.row() for idx in indexes])
        ranges = list(group_consecutive_numbers(sorted(rows)))
        for range_group in reversed(ranges):
            for row in reversed(range_group):
                del self._nodes[row]
            self.rowsRemoved.emit(QModelIndex(), range_group.start, range_group.stop)

    # Proxy functions
    def mapFromSource(self, node:str)->QModelIndex:
        row = self._nodes.index(node)
        return self.index(row, 0)

    def mapToSource(self, proxy:QModelIndex|QPersistentModelIndex)->str:
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
                self.index(r.stop, self.columnCount()-1)
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
        return self.createIndex(row, column, node) # consider storing the index of the node

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
            return ['name', 'source', 'fields', 'status', 'error', 'result'][section]
        return super().headerData(section, orientation, role)

    def data(self, index:QModelIndex|QPersistentModelIndex, role:int=Qt.ItemDataRole.DisplayRole)->Any:
        if not self._source_model:
            return None

        node_name = self.mapToSource(index)

        if role == GraphDataRole.NodeInletsRole:
            return ['in']

        if role == GraphDataRole.NodeOutletsRole:
            return ['out']

        match index.column():
            case 0:
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return node_name

            case 1:
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return self._source_model.nodeSource(node_name)

            case 2:
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return ",".join( self._source_model.nodeFields(node_name) )

            case 3:
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return self._source_model.nodeStatus(node_name)

            case 4:
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return f"{self._source_model.nodeError(node_name)}"

            case 5:
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return f"{self._source_model.nodeResult(node_name)}"

        return None

from pylive.VisualCode_v4.graph_editor.graph_data_roles import GraphDataRole
class PyLinkProxyModel(QAbstractItemModel):
    def __init__(self, source_model:PyDataModel, parent:QObject|None=None):
        super().__init__(parent=parent)
        self._links:list[tuple[str, str, str]] = list()

        self._items_model:PyNodeProxyModel|None=None
        self._source_model:PyDataModel|None=None

        self.setSourceModel(source_model)

    def itemsModel(self)->PyNodeProxyModel|None:
        return self._items_model

    def setSourceModel(self, source_model:PyDataModel|None):
        if self._source_model:
            self._source_model.modelAboutToBeReset.disconnect(self.modelAboutToBeReset.emit)
            self._source_model.modelReset.disconnect(self._resetModel)

            self._source_model.nodesAboutToBeLinked.disconnect(self._on_source_nodes_about_to_be_linked)
            self._source_model.nodesLinked.disconnect(self._on_source_nodes_linked)
            self._source_model.nodesAboutToBeUnlinked.disconnect(self._on_source_nodes_about_to_be_unlinked)
            self._source_model.nodesUnlinked.disconnect(self._on_source_nodes_unlinked)

            self._items_model = None

        if source_model:
            self._items_model = PyNodeProxyModel(source_model)

            source_model.modelAboutToBeReset.connect(self.modelAboutToBeReset.emit)
            source_model.modelReset.connect(self._resetModel)

            source_model.nodesAboutToBeLinked.connect(self._on_source_nodes_about_to_be_linked)
            source_model.nodesLinked.connect(self._on_source_nodes_linked)
            source_model.nodesAboutToBeUnlinked.connect(self._on_source_nodes_about_to_be_unlinked)
            source_model.nodesUnlinked.connect(self._on_source_nodes_unlinked)

        self._source_model = source_model
        self._resetModel()

    def _resetModel(self):
        assert self._source_model
        self._links.clear()
        for row, link in enumerate(self._source_model.links()):
            self._links.insert(row, link)
        self.modelReset.emit()

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
            self.rowsAboutToBeRemoved.emit(QModelIndex(), r.start, r.stop)

    def _on_source_nodes_unlinked(self, links:list[tuple[str,str,str]]):
        indexes = [self.mapFromSource(link) for link in links]
        rows = set([idx.row() for idx in indexes])
        ranges = list(group_consecutive_numbers(sorted(rows)))
        for range_group in reversed(ranges):
            for row in reversed(range_group):
                del self._links[row]
            self.rowsRemoved.emit(QModelIndex(), range_group.start, range_group.stop)

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
        return self.createIndex(row, column, link) # consider storing the index of the node

    def parent(self, index:QModelIndex)->QModelIndex:
        return QModelIndex()

    def rowCount(self, parent:QModelIndex|QPersistentModelIndex=QModelIndex())->int:
        if not self._source_model:
            return 0
        return len(self._links)

    def columnCount(self, parent:QModelIndex|QPersistentModelIndex=QModelIndex())->int:
        return 3

    def headerData(self, section: int, orientation: Qt.Orientation, role:int=Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal:
            return ['source', 'target', 'inlet'][section]
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

        match index.column():
            case 0:
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return source

            case 1:
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return target

            case 2:
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return inlet

        return None