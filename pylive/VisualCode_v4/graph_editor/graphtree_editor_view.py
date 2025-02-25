#####################
# The Network Scene #
#####################

#
# A 'View' to represent a network of nodes, connected by inlets and outlets
#

# In QT ModelView terminology this is a 'View'.
# It is responsible to present the model.
# these widgets are responsible to reference the 'graphscene',
# and the represented nodes, edge and ports.

#
# TODO:
# - implement cancelling an ongoing drag event
#   eg with esc or right click etc.

# - consider allowing any QAbstractItemModel for the _edges_.
#   Currently only the _.edgeItem_, and _.addEdgeItem_ methods are used internally.
#   factoring out edgeItem is easy.
#   to factor out .addEdgeItem, 
#   we need to implement insertRows for the edge model.
#   insertRows are the default appending method but!
#   but! it will insert empty rows.
#   the View must be able to handle incomplete or empty edges.

# - consider using dragEnter instead of dragMove, since that seems to be the
#   standard event to handle if dragging is acceptable.
#   this is more obvious on a Mac.

# - consider refactoring drag and drop events since they are pretty repetitive.

# - refactor in v2 the delegate methods.
#   instead of creating widget within the delegate provide paint, sizeHint, shape
#   methods to define the node, item, edge visuals.
#   This will potentially lead to a GraphView that is able to use the builtin StyledItemDelegates

# - consider adding editors for column cell inside the node,
#   as if a node would be a row in a table, but in a different _view_

import traceback
from pylive.utils.debug import log_caller
from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from bidict import bidict
from collections import defaultdict

from pylive.VisualCode_v4.graph_editor.graph_data_roles import GraphDataRole
from pylive.utils.qt import distribute_items_horizontal, signalsBlocked

from pylive.VisualCode_v4.graph_editor.standard_graph_delegate import StandardGraphDelegate
from pylive.utils.unique import make_unique_name
from pylive.utils.diff import diff_set

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from pylive.utils import group_consecutive_numbers
from textwrap import dedent

from itertools import chain

class NodeItem(QGraphicsItem):
    def __init__(self, index:QPersistentModelIndex, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self.index:QPersistentModelIndex = index
        self.in_links:set[LinkItem] = set()
        self.out_links:set[LinkItem] = set()

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

    def boundingRect(self) -> QRectF:
        return QRectF(0,0,120,32)

    def paint(self, painter:QPainter, option:QStyleOption, widget:QWidget|None=Nonce):
        painter.drawRoundedRect(self.boundingRect(), 5, 5)
        painter.drawText(QPointF(0, 20), f"{self.index.data()}")


class PortItem(QGraphicsItem):
    def __init__(self, index:QPersistentModelIndex, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self.index:QPersistentModelIndex = index
        self.in_links:set[LinkItem] = set()
        self.out_links:set[LinkItem] = set()


class LinkItem(QGraphicsItem):
    def __init__(self, source: NodeItem|PortItem, target: NodeItem|PortItem, index:tuple[QPersistentModelIndex, QPersistentModelIndex], parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self.index:tuple[QPersistentModelIndex, QPersistentModelIndex] = index
        self.source:NodeItem|PortItem = source
        self.target:NodeItem|PortItem = target

        self.source.out_links.add(self)
        self.target.in_links.add(self)


class _GraphEditorView(QGraphicsView):
    SourceRole = Qt.ItemDataRole.UserRole+1
    TargetRole = Qt.ItemDataRole.UserRole+2
    InletsRole = Qt.ItemDataRole.UserRole+3
    OutletsRole = Qt.ItemDataRole.UserRole+4

    nodesLinked = Signal(QModelIndex, QModelIndex, str, str)

    def __init__(self, delegate=None, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._tree: QAbstractItemModel | None = None
        self._delegate: StandardGraphDelegate|None=None
        self._tree_model_connections = []

        # store model widget relations
        # map item index to widgets
        self._item_widgets:dict[QPersistentModelIndex, NodeItem|PortItem] = dict()
        # map (source, target) index to widgets
        self._link_widgets:dict[tuple[QPersistentModelIndex, QPersistentModelIndex], LinkItem] = dict()
        # self._port_widgets:dict[QPersistentModelIndex, QGraphicsItem] = dict()

        self._node_in_links:defaultdict[QPersistentModelIndex, list[QPersistentModelIndex]] = defaultdict(list) # Notes: store attached links, because the underlzing model has to find the relevant edges  and thats is O(n)
        self._node_out_links:defaultdict[QPersistentModelIndex, list[QPersistentModelIndex]] = defaultdict(list) # Notes: store attached links, because the underlzing model has to find the relevant edges  and thats is O(n)

        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        scene = QGraphicsScene()
        scene.setSceneRect(QRectF(-9999,-9999,9999*2, 9999*2))
        self.setScene(scene)

        self.setDelegate(delegate or StandardGraphDelegate())

    def centerNodes(self):
        logger.debug("centerNodes")
        self.centerOn(self.scene().itemsBoundingRect().center())

    def setModel(self, tree:QAbstractItemModel|None):
        logger.debug(f"setModel {tree}")
        if self._tree:
            for signal, slot in self._tree_model_connections:
                signal.disconnect(slot)

        if tree:
            self._tree_model_connections = [
                (tree.modelReset, self._onModelReset),
                (tree.rowsInserted, self._onRowsInserted),
                (tree.rowsAboutToBeRemoved, self._onRowsAboutToBeRemoved),
                (tree.dataChanged, self._onDataChanged)
            ]
            for signal, slot in self._tree_model_connections:
                signal.connect(slot)
            
            
        self._tree:QAbstractItemModel|None = tree

        # populate initial scene
        self._onModelReset()

    def model(self)->QAbstractItemModel|None:
        return self._tree

    def setDelegate(self, delegate:StandardGraphDelegate):
        logger.debug(f"setDelegate {delegate}")
        self._delegate = delegate
        self._delegate.nodePositionChanged.connect(lambda widget: self._moveAttachedLinks(self._node_widgets.inverse[widget].row()))

    ### Handle Model Signals
    def _onModelReset(self):
        assert self._tree
        node_count = self._tree.rowCount()
        self._onRowsInserted(parent=QModelIndex(), first=0, last=node_count-1)

        for node_row in range(node_count):
            node_index = self._tree.index(node_row, 0, QModelIndex())
            child_count = len(self._tree.children())
            self._onRowsInserted(parent=node_index, first=0, last=child_count-1)


    def _onRowsInserted(self, parent:QModelIndex, first:int, last:int):
        logger.debug(f"_onRowsInserted {parent}, {first}-{last}")
        assert self._tree, "self._nodes is None"
        assert self._delegate
        if not parent.isValid():
            ### create nodes from root indexes
            for row in range(first, last+1):
                node_id = QPersistentModelIndex(self._tree.index(row, 0, QModelIndex()))
                node_widget = NodeItem(node_id)
                self._item_widgets[node_id] = node_widget
                self.scene().addItem(node_widget)
        else:
            ### create ports from children
            for row in range(first, last+1):
                port_id = QPersistentModelIndex(self._tree.index(row, 0, parent))
                port_widget = PortItem(port_id)
                self._item_widgets[port_id] = port_widget
                node_widget = self._item_widgets[QPersistentModelIndex(parent)]
                port_widget.setParentItem(node_widget)

        ### create links to source node from children GraphDataRole.SourceRole
        # collect link from index data
        for row in range(first, last+1):
            item_index = self._tree.index(row, 0, parent)
            source_indexes:Collection[QModelIndex]|None = self._tree.data(item_index, GraphDataRole.LinkSourceRole)
            if source_indexes is None or len(source_indexes)==0:
                continue
            if any(idx.model() != self._tree for idx in source_indexes):
                raise ValueError(f"Sources containes index not in this model! got: {source_indexes}")
            if any(not idx.isValid() for idx in source_indexes):
                raise ValueError(f"Sources containes invalid indexes! got: {source_indexes}")

            item_widget = self._item_widgets[QPersistentModelIndex(item_index)]
            for source_index in sorted(source_indexes, key=lambda idx: idx.row()):
                source_widget = self._item_widgets[QPersistentModelIndex(source_index)]
                link_id = (QPersistentModelIndex(source_index), QPersistentModelIndex(item_index))
                link_widget = LinkItem(source_widget, item_widget, link_id)
                self._link_widgets[link_id] = link_widget
                self.scene().addItem(link_widget)

    def _onRowsAboutToBeRemoved(self, parent:QModelIndex, first:int, last:int):
        logger.debug(f"_onRowsInserted {parent}, {first}-{last}")
        assert self._tree, "self._nodes is None"
        assert self._delegate
        if not parent.isValid():
            ### delete nodes for root indexes
            for row in range(first, last+1):
                item_id = QPersistentModelIndex(self._tree.index(row, 0, parent))
                item_widget = self._item_widgets[item_id]
                del self._item_widgets[item_id]
                self.scene().removeItem(item_widget)
        else:
            ### delete ports for children
            for row in range(first, last+1):
                item_id = QPersistentModelIndex(self._tree.index(row, 0, parent))
                item_widget = self._item_widgets[item_id]
                del self._item_widgets[item_id]
                self.scene().removeItem(item_widget)

        ### delete links to nodes
        for row in range(first, last+1):
            item_index = QPersistentModelIndex(self._tree.index(row, 0, parent))
            item_widget = self._item_widgets[item_index]

            # item widget has links
            for link_widget in chain(item_widget.in_links, item_widget.out_links):
                assert link_widget in self._link_widgets
                link_widget.source.out_links.remove(link_widget)
                link_widget.target.in_links.remove(link_widget)
                del self._link_widgets[link_widget.index]
                self.scene().removeItem(link_widget)

    def _onDataChanged(self, top_left:QModelIndex, bottom_right:QModelIndex, roles:list[int]=[]):
        """The optional roles argument can be used to specify which data roles have actually been modified.
        An empty vector in the roles argument means that all roles should be considered modified"""
        assert self._tree
        if (GraphDataRole.LinkSourceRole in roles) or not roles:
            rows = set(range(top_left.row(), bottom_right.row()+1))
            for row in sorted(rows, reverse=True):
                item_index = self._tree.index(row, 0)
                item_id = QPersistentModelIndex(item_index)
                item_widget = self._item_widgets[item_id]
                new_source_indexes = self._tree.data(item_index, GraphDataRole.LinkSourceRole) or []
            
                # remove invalid links
                new_source_ids = [QPersistentModelIndex(idx) for idx in new_source_indexes] if new_source_indexes else []
                for link_widget in item_widget.in_links:
                    link_id = link_widget.index
                    current_source_id = link_id[0]
                    if current_source_id not in new_source_ids:
                        # remove that link widget
                        link_widget.source.out_links.remove(link_widget)
                        link_widget.target.in_links.remove(link_widget)
                        self.scene().removeItem(link_widget)
                        del self._link_widgets[link_id]

                # add new links
                for source_index in  sorted(new_source_indexes, key=lambda idx: idx.row()):
                    source_id = QPersistentModelIndex(source_index)
                    source_widget = self._item_widgets[source_id]
                    link_id = (source_id, item_id)
                    link_widget = LinkItem(source_widget, item_widget, link_id)
                    self._link_widgets[link_id] = link_widget
                    self.scene().addItem(link_widget)

    ### CRUD WIDGETS
    def _moveAttachedLinks(self, node_row:int):
        assert self._edges
        assert self._delegate
        assert isinstance(node_row, int)
        from itertools import chain
        node_id = QPersistentModelIndex(self._nodes.index(node_row, 0))
        for edge_id in chain(self._node_in_links[node_id], self._node_out_links[node_id]):
            edge_widget = self.linkWidget(edge_id)
            assert edge_widget in self._edge_widgets.values(), f"got: {edge_widget} not in {[_ for _ in self._edge_widgets.values()]}"
            edge_index = self._edge_widgets.inverse[edge_widget]

            source, outlet = self._edges.data(edge_index, GraphDataRole.LinkSourceRole)
            target, inlet = self._edges.data(edge_index, GraphDataRole.LinkTargetRole)

            try:
                source_widget = self.outletWidget(source, outlet)
            except KeyError:
                logger.debug("no outlet widget, link to node")
                source_widget = self.nodeWidget(source)

            try:
                target_widget = self.inletWidget(target, inlet)
            except KeyError:
                logger.debug("no inlet widget, link to node")
                target_widget = self.nodeWidget(target)

            self._delegate.updateEdgePosition(edge_widget, source_widget, target_widget)

    ### Map widgets to model
    def itemWidgets(self)->Collection[NodeItem|PortItem]:
        return [item for item in self._item_widgets.values()]

    def linkWidgets(self)->Collection[LinkItem]:
        return [item for item in self._link_widgets.values()]

    def itemWidget(self, index: QModelIndex) -> NodeItem|PortItem:
        assert self._tree, "self._edges was not defined"
        assert index.isValid() and index.model() == self._tree, f"bad index, got: {index}"
        item_id = QPersistentModelIndex(index)
        item_widget = self._item_widgets[item_id]
        return item_widget

    def linkWidget(self, source_index: QModelIndex, target_index:QModelIndex) -> LinkItem:
        assert self._tree, "self._edges was not defined"
        if not source_index.isValid():
            raise ValueError(f"Source {source_index} is invalid!")
        if source_index.model()!=self._tree:
            raise ValueError(f"Source {source_index} is not in this model!")
        if not target_index.isValid():
            raise ValueError(f"Target {target_index} is invalid!")
        if target_index.model()!=self._tree:
            raise ValueError(f"Target {target_index} is not in this model!")

        source_id = QPersistentModelIndex(source_index)
        target_id = QPersistentModelIndex(target_index)
        link_id = (source_id, target_id)
        link_widget = self._link_widgets[link_id]
        return link_widget

    ### Widgets At Position
    def itemIndexAt(self, pos: QPoint) -> QModelIndex|None:
        """Returns the topmost node at position pos, which is in viewport coordinates."""
        assert self._tree, "self._nodes was not defined"
        for item in self.items(pos.x()-4,pos.y()-4,8,8):
            if item in self._item_widgets.values():
                assert isinstance(item, (NodeItem, PortItem))
                item_id:QPersistentModelIndex =  item.index
                item_index = self._tree.index(item_id.row(), 0, item_id.parent())
                return item_index

    def linkIndexesAt(self, pos: QPoint) -> tuple[QModelIndex, QModelIndex]|None:
        """Returns the topmost edge at position pos, which is in viewport coordinates."""
        assert self._tree, "_edges was not defined"
        for item in self.items(pos.x()-4,pos.y()-4,8,8):
            if item in self._link_widgets.values():
                assert isinstance(item, LinkItem)
                link_id =  item.index
                source_id, target_id = link_id
                source_index = self._tree.index(source_id.row(), 0, source_id.parent())
                target_index = self._tree.index(target_id.row(), 0, target_id.parent())
                return source_index, target_index


from dataclasses import dataclass

@dataclass
class InternalDragController:
    mode: Literal['inlet', 'outlet', 'edge_source', 'edge_target']
    source_widget: QGraphicsItem
    draft: QGraphicsItem


class _InternalDragMixin(_GraphEditorView):
    def __init__(self, delegate=None, parent: QWidget | None = None):
        super().__init__(delegate, parent)
        self._drag_controller:InternalDragController|None = None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        assert self._delegate
        for item in self.items(event.position().toPoint()):
            if item in self._outlet_widgets.values():
                draft_link_item = self._delegate.createEdgeWidget(QModelIndex())
                self._drag_controller = InternalDragController(
                    mode='outlet',
                    source_widget= item,
                    draft=draft_link_item
                )
                self.scene().addItem(self._drag_controller.draft)
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        assert self._delegate
        if self._drag_controller:
            match self._drag_controller.mode:
                case 'outlet':
                    if inlet_id := self.inletIndexAt(event.position().toPoint()):
                        node_index, inlet = inlet_id
                        drop_widget = self.inletWidget(node_index, inlet)

                        # self._drag_controller.draft.move(
                        #     self._drag_controller.source_widget, 
                        #     drop_widget
                        # )
                        self._delegate.updateEdgePosition(
                            self._drag_controller.draft,
                            self._drag_controller.source_widget, 
                            drop_widget
                        )
                        return
                    else:
                        # self._drag_controller.draft.move(
                        #     self._drag_controller.source_widget, 
                        #     self.mapToScene(event.position().toPoint())
                        # )
                        self._delegate.updateEdgePosition(
                            self._drag_controller.draft,
                            self._drag_controller.source_widget, 
                            self.mapToScene(event.position().toPoint())
                        )
                        return
                case  _:
                     ...

        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        assert self._delegate
        if self._drag_controller:
            match self._drag_controller.mode:
                case 'outlet':
                    if inlet_id := self.inletIndexAt(event.position().toPoint()):
                        source_node_index, source_outlet = self._outlet_widgets.inverse[self._drag_controller.source_widget]
                        drop_node_index, drop_inlet = inlet_id
                        self.nodesLinked.emit(
                            source_node_index,
                            drop_node_index,
                            source_outlet,
                            drop_inlet
                        )

                    else:
                        #cancel connection
                        ...
                case _:
                    ...

            self.scene().removeItem(self._drag_controller.draft)
            self._drag_controller = None
        else:
            super().mouseReleaseEvent(event)



class GraphEditorView(
    # _GraphDragAndDropMixin,
    # _InternalDragMixin,
    # _GraphSelectionMixin, 
    # _GraphLayoutMixin,
     _GraphEditorView
    ):
    ...


def main():
    app = QApplication()

    class Window(QWidget):
        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent=parent)
            self._model:QStandardItemModel|None=QStandardItemModel()

            self.setupUI()
            self.action_connections = []
            self.bindView()

        def setupUI(self):
            self.nodelist = QListView()
            self.nodelist.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

            self.nodetree = QTreeView()
            self.nodetree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

            self.graphview = _GraphEditorView()
            self.graphview.setWindowTitle("NXNetworkScene")

            self.create_action = QPushButton("create node", self)
            self.delete_action = QPushButton("delete", self)
            self.link_selected_action = QPushButton("connect selected", self)
            self.layout_action = QPushButton("layout nodes", self)
            self.layout_action.setDisabled(True)

            buttons_layout = QGridLayout()
            buttons_layout.addWidget(self.create_action, 0, 0)
            buttons_layout.addWidget(self.delete_action, 0, 1)
            buttons_layout.addWidget(self.link_selected_action, 1, 0, 1, 2)
            buttons_layout.addWidget(self.layout_action, 3, 0, 1, 2)
            grid_layout = QGridLayout()
            grid_layout.addLayout(buttons_layout, 0, 0)
            grid_layout.addWidget(self.nodelist, 1, 0)
            grid_layout.addWidget(self.nodetree, 2, 0)
            grid_layout.addWidget(self.graphview, 0, 1, 3, 1)

            self.setLayout(grid_layout)

        def bindView(self):
            self.nodelist.setModel(self._model)
            self.nodetree.setModel(self._model)
            self.graphview.setModel(self._model)

            self.action_connections = [
                (self.create_action.clicked, lambda: self.create_node()),
                (self.delete_action.clicked, lambda: self.delete_selected()),
                (self.link_selected_action.clicked, lambda: self.link_selected()),
                # (self.layout_action.clicked, lambda: self.graphview.layoutNodes())
            ]
            for signal, slot in self.action_connections:
                signal.connect(slot)

        ### commands
        @Slot()
        def create_node(self):
            assert self._model
            
            def getItemName(row, model=self._model):
                return model.data(model.index(row, 0), Qt.ItemDataRole.EditRole)

            node_count = self._model.rowCount()
            node_names = list(map(getItemName, range(node_count))) 
            unique_name = make_unique_name("node1", node_names)

            item = QStandardItem()
            item.setData(unique_name, Qt.ItemDataRole.DisplayRole)
            self._model.insertRow(node_count, item)

        @Slot()
        def create_inlet(self):
            ...

        @Slot()
        def link_selected(self):
            ...

        @Slot()
        def delete_selected(self):
            # either a node or an inlet
            ...

        @Slot()
        def create_outlet(self):
            ...


        


    window = Window()
    window.show()
    app.exec()

if __name__ == "__main__":
    main()

