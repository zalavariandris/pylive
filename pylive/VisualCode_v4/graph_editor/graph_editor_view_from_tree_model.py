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

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from textwrap import dedent

class NodeItem:
    def widget(self):
        ...

    def ptr(self)->QPersistentModelIndex:
        ...

class LinkItem:
    def widget(self):
        ...

    def ptr(self)->QPersistentModelIndex:
        ...

class InletItem:
    def widget(self):
        ...

    def ptr(self)->QPersistentModelIndex:
        ...

class OutletItem:
    def ptr(self)->QPersistentModelIndex:
        ...


class _GraphEditorView(QGraphicsView):
    SourceRole = Qt.ItemDataRole.UserRole+1
    TargetRole = Qt.ItemDataRole.UserRole+2
    InletsRole = Qt.ItemDataRole.UserRole+3
    OutletsRole = Qt.ItemDataRole.UserRole+4

    nodesLinked = Signal(QModelIndex, QModelIndex, str, str)

    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._nodes: QAbstractItemModel | None = None
        self._edges: QAbstractItemModel | None = None
        self._delegate: StandardGraphDelegate|None=None
        self._node_model_connections = []
        self._edge_model_connections = []

        # store model widget relations
        self._node_widgets:   bidict[QPersistentModelIndex, QGraphicsItem] = bidict()
        self._edge_widgets:   bidict[QPersistentModelIndex, QGraphicsItem] = bidict()
        self._inlet_widgets:  bidict[tuple[QPersistentModelIndex, str], QGraphicsItem] = bidict()
        self._outlet_widgets: bidict[tuple[QPersistentModelIndex, str], QGraphicsItem] = bidict()
        self._node_inlets:    dict[QPersistentModelIndex, list[str]] = defaultdict(list)
        self._node_outlets:   dict[QPersistentModelIndex, list[str]] = defaultdict(list)

        self._node_in_links:defaultdict[QGraphicsItem, list[QGraphicsItem]] = defaultdict(list) # Notes: store attached links, because the underlzing model has to find the relevant edges  and thats is O(n)
        self._node_out_links:defaultdict[QGraphicsItem, list[QGraphicsItem]] = defaultdict(list) # Notes: store attached links, because the underlzing model has to find the relevant edges  and thats is O(n)

        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        scene = QGraphicsScene()
        scene.setSceneRect(QRectF(-9999,-9999,9999*2, 9999*2))
        self.setScene(scene)

        self.setDelegate(StandardGraphDelegate())

    def centerNodes(self):
        logger.debug("centerNodes")
        self.centerOn(self.scene().itemsBoundingRect().center())

    def setModel(self, nodes:QAbstractItemModel|None, edges:QAbstractItemModel|None):
        logger.debug(f"setModel {nodes} {edges}")
        if self._nodes:
            for signal, slot in self._node_model_connections:
                signal.disconnect(slot)

        if self._edges:
            for signal, slot in self._edge_model_connections:
                signal.disconnect(slot)

        if nodes:
            self._node_model_connections = [
                (nodes.modelReset, self._resetWidgets),
                (nodes.rowsInserted, self._onNodesInserted),
                (nodes.rowsAboutToBeRemoved, self._onNodesAboutToBeRemoved),
                (nodes.dataChanged, self._onNodeDataChanged)
            ]
            for signal, slot in self._node_model_connections:
                signal.connect(slot)
            
        if edges:
            self._edge_model_connections = [
                (edges.modelReset, self._resetWidgets),
                (edges.rowsInserted, self._onEdgesInserted),
                (edges.rowsAboutToBeRemoved, self._onEdgesAboutToBeRemoved),
                (edges.dataChanged, self._onEdgeDataChanged)
            ]
            for signal, slot in self._edge_model_connections:
                signal.connect(slot)
            
        self._nodes:QAbstractItemModel|None = nodes
        self._edges:QAbstractItemModel|None = edges

        # populate initial scene
        if self._nodes and self._nodes.rowCount()>0:
            self._onNodesInserted(QModelIndex(), 0, self._nodes.rowCount()-1)

        if self._edges and self._edges.rowCount() > 0:
            self._onEdgesInserted(QModelIndex(), 0, self._edges.rowCount()-1)

    def model(self)->tuple[QAbstractItemModel|None, QAbstractItemModel|None]:
        return self._nodes, self._edges

    def setDelegate(self, delegate:StandardGraphDelegate):
        logger.debug(f"setDelegate {delegate}")
        self._delegate = delegate
        self._delegate.nodePositionChanged.connect(self._moveAttachedLinks)

    ### Handle Model Signals
    def _onNodesInserted(self, parent:QModelIndex, first:int, last:int):
        logger.debug(f"_onNodesInserted {first}-{last}")
        assert self._nodes, "self._nodes is None"
        self._addNodes(range(first, last+1))

    def _onNodesAboutToBeRemoved(self, parent:QModelIndex, first:int, last:int):
        logger.debug(f"_onNodesAboutToBeRemoved {first}-{last}")
        assert self._nodes, "self._nodes is None"
        self._removeNodes(range(first, last+1))

    def _onNodeDataChanged(self, top_left:QModelIndex, bottom_right:QModelIndex, roles:list[int]=[]):
        """
        The optional roles argument can be used to specify which data roles have actually been modified.
        An empty vector in the roles argument means that all roles should be considered modified"""
        assert self._nodes, "self._nodes is None"
        logger.debug(f"_onNodeDataChanged {top_left}-{bottom_right}")
        rows = range(top_left.row(), bottom_right.row()+1)
        self._updateNodes(rows, roles)

    def _onEdgesInserted(self, parent:QModelIndex, first:int, last:int):
        assert self._edges, "self._edges is None"
        logger.debug(f"_onEdgesInserted {first}-{last}")
        self._addEdges(  [_ for _ in range(first, last+1)]  )

    def _onEdgesAboutToBeRemoved(self, parent:QModelIndex, first:int, last:int):
        logger.debug(f"_onEdgesAboutToBeRemoved {first}-{last}")
        assert self._edges, "self._edges is None"
        self._removeEdges(range(first, last+1))

    def _onEdgeDataChanged(self, top_left:QModelIndex, bottom_right:QModelIndex, roles:list[int]=[]):
        """
        The optional roles argument can be used to specify which data roles have actually been modified.
        An empty vector in the roles argument means that all roles should be considered modified"""
        logger.debug(f"_onEdgeDataChanged {top_left}-{bottom_right} {roles}")
        assert self._edges, "self._edges is None"
        self._updateEdges(range(top_left.row(), bottom_right.row()+1))

    ### CRUD WIDGETS
    def _resetWidgets(self):
        logger.debug(f"_resetWidgets")
        assert self._nodes, "self._nodes is None"
        ### clear graph

        for inlet_id in self._inlet_widgets.keys():
            inlet_widget = self._inlet_widgets[inlet_id]
            self.scene().removeItem(inlet_widget)

        for outlet_id in self._outlet_widgets.keys():
            outlet_widget = self._outlet_widgets[outlet_id]
            self.scene().removeItem(outlet_widget)

        for node_index in self._node_widgets.keys():
            node_widget = self._node_widgets[node_index]
            self.scene().removeItem(node_widget)

        for edge_index in self._edge_widgets.keys():
            edge_widget = self._edge_widgets[edge_index]
            self.scene().removeItem(edge_widget)

        self._node_widgets.clear()
        self._node_in_links.clear()
        self._node_out_links.clear()

        ### populate graph with nodes
        self._addNodes( range(self._nodes.rowCount()) )

        # if nodes were reset, then the links are not linking to a valid widget
        assert self._edges, "self._edge is None"
        ### clear graph
        self._edge_widgets.clear()

        ### populate graph with edges
        if self._edges.rowCount()>0:
            self._onEdgesInserted(QModelIndex(), 0, self._edges.rowCount()-1)



    def _addNodes(self, rows:Iterable[int]):
        logger.debug(f"_addNodes {rows}")
        assert self._nodes

        for row in rows:
            node_index = self._nodes.index(row, 0)
            assert node_index.isValid(), "invalid persistent node?"
            node_widget = self._delegate.createNodeWidget(self.scene(), node_index)
            node_id = QPersistentModelIndex(node_index)
            self._node_widgets[node_id] = node_widget
            self._node_out_links[node_widget] = []
            self._node_in_links[node_widget] = []
            self._node_inlets[node_id] = list()
            self._node_outlets[node_id] = list()

            if inlets := self._nodes.data(node_index, GraphDataRole.NodeInletsRole):
                self._insertInlets(node_index, 0, inlets)

            if outlets := self._nodes.data(node_index, GraphDataRole.NodeOutletsRole):
                self._insertOutlets(node_index, 0, outlets)

    def _updateNodes(self, rows:Iterable[int], roles:list[int]):
        logger.debug(f"_updateNodes rows:{rows}, roles: {roles}")
        assert self._nodes, "self._edges cant be None"
        for row in rows:
            node_index = self._nodes.index(row, 0)
            node_id = QPersistentModelIndex(node_index)
            if node_id not in self._node_widgets:
                print(f"while updating, node widget does not exist for index: {node_id}")
                continue

            node_widget = self.nodeWidget(node_id)
            self._delegate.updateNodeWidget(node_index, node_widget)
            self._resetInlets(node_index)
            self._resetOutlets(node_index)

    def _removeNodes(self, rows:Iterable[int]):
        logger.debug(f"_removeNodes rows:{rows}")
        assert self._nodes, "self._noded cant be None"
        for row in rows:
            node_index = self._nodes.index(row, 0)
            node_id = QPersistentModelIndex(node_index)
            node_widget = self.nodeWidget(node_index)
            self.scene().removeItem(node_widget)
            
            del self._node_out_links[node_widget]
            del self._node_in_links[node_widget]
            del self._node_widgets[node_id]

    def _insertInlets(self, node_index:QModelIndex, start:int, inlets:Iterable[str]):
        logger.debug(f"_insertInlets {node_index}, {start} {inlets}")
        node_id = QPersistentModelIndex(node_index)
        node_widget = self.nodeWidget(node_index)
        for i, inlet in enumerate(inlets, start=start):
            inlet_widget = self._delegate.createInletWidget(node_widget, node_index, inlet, i)
            inlet_widget.setParentItem(node_widget)
            inlet_id = node_id, inlet
            assert node_id.isValid() and isinstance(inlet, str)
            self._inlet_widgets[inlet_id] = inlet_widget
            self._node_inlets[node_id].insert(i, inlet)

        # layout inlets
        inlet_widgets = [self.inletWidget(node_index, inlet) for inlet in self._node_inlets[node_id]]
        distribute_items_horizontal(inlet_widgets, node_widget.boundingRect())

        # layout edges
        self._moveAttachedLinks(node_widget)

    def _removeInlets(self, node_index:QModelIndex, inlets:Iterable[str]):
        logger.debug(f"_removeInlets {node_index}, {inlets}")
        node_id = QPersistentModelIndex(node_index)
        node_widget = self.nodeWidget(node_id)
        for inlet in inlets:
            inlet_id = QPersistentModelIndex(node_index), inlet
            inlet_item = self._inlet_widgets[inlet_id]
            self.scene().removeItem(inlet_item)
            del self._inlet_widgets[inlet_id]
            self._node_inlets[node_id].remove(inlet)
        
        # layout inlets
        inlet_widgets = [self.inletWidget(node_index, inlet) for inlet in self._node_inlets[node_id]]
        distribute_items_horizontal(inlet_widgets, node_widget.boundingRect())

        # layout edges
        self._moveAttachedLinks(node_widget)

    def _resetInlets(self, node_index:QModelIndex):
        logger.debug(f"_resetInlets {node_index}")
        assert self._nodes, "self._edges cant be None"
        node_id = QPersistentModelIndex(node_index)
        self._removeInlets(node_index, self._node_inlets[node_id])
        inlets = self._nodes.data(node_index, GraphDataRole.NodeInletsRole)
        self._insertInlets(node_index, 0, inlets)

    def _insertOutlets(self, node_index:QModelIndex, start:int, outlets:Iterable[str]):
        logger.debug(f"_insertOutlets {node_index} {start} {outlets}")
        node_id = QPersistentModelIndex(node_index)
        node_widget = self.nodeWidget(node_id)
        for i, outlet in enumerate(outlets, start=start):
            outlet_widget = self._delegate.createOutletWidget(node_widget, node_index, outlet, i)
            outlet_id = QPersistentModelIndex(node_index), outlet
            self._outlet_widgets[outlet_id] = outlet_widget
            self._node_outlets[node_id].insert(i, outlet)
        
        # layout inlets
        outlet_widgets = [self.outletWidget(node_index, outlet) for outlet in self._node_outlets[node_id]]
        for outlet_widget in outlet_widgets:
            outlet_widget.setY(node_widget.boundingRect().bottom())
        distribute_items_horizontal(outlet_widgets, node_widget.boundingRect())

        # layout edges
        self._moveAttachedLinks(node_widget)

    def _removeOutlets(self, node_index:QModelIndex, outlets:Iterable[str]):
        logger.debug(f"_removeOutlets {node_index} {outlets}")
        node_id = QPersistentModelIndex(node_index)
        node_widget = self.nodeWidget(node_id)
        for outlet in outlets:
            outlet_id = node_id, outlet
            outlet_item = self._outlet_widgets[outlet_id]
            self.scene().removeItem(outlet_item)
            del self._outlet_widgets[outlet_id]
            self._node_outlets[node_id].remove(outlet)
        
        # layout inlets
        outlet_widgets = [self.outletWidget(node_index, outlet) for outlet in self._node_outlets[node_id]]
        distribute_items_horizontal(outlet_widgets, node_widget.boundingRect())

        # layout edges
        self._moveAttachedLinks(node_widget)

    def _resetOutlets(self, node_index:QModelIndex):
        logger.debug(f"_resetOutlets")
        assert self._nodes, "self._edges cant be None"
        node_id = QPersistentModelIndex(node_index)
        self._removeOutlets(node_index, self._node_outlets[node_id])
        outlets = self._nodes.data(node_index, GraphDataRole.NodeOutletsRole)
        self._insertOutlets(node_index, 0, outlets)
        
    def _addEdges(self, rows:Iterable[int]):
        logger.debug(f"_addEdges {rows}")
        assert self._edges, f"bad self._edges, got{self._edges}"
        assert self._delegate
        rows = list(rows)
        assert all(row>=0 for row in rows)
        for row in sorted(rows):
            edge_index = self._edges.index(row, 0)
            assert edge_index.isValid()
            ### create edge editor
            edge_id = QPersistentModelIndex(edge_index)
            edge_widget = self._delegate.createEdgeWidget(edge_index)
            self._edge_widgets[edge_id] = edge_widget
            self.scene().addItem( edge_widget )

            #UPDATE LINKS POSITION
            source_node_index, outlet = self._edges.data(edge_index, GraphDataRole.LinkSourceRole)
            target_node_index, inlet = self._edges.data(edge_index, GraphDataRole.LinkTargetRole)
            assert source_node_index.isValid(), f"got: {source_node_index}"
            assert target_node_index.isValid(), f"got: {target_node_index}"

            source_node_widget = self.nodeWidget(source_node_index)
            target_node_widget = self.nodeWidget(target_node_index)

            self._node_out_links[source_node_widget].append(edge_widget)
            self._node_in_links[target_node_widget].append(edge_widget)


            try:
                source_widget = self.outletWidget(source_node_index, outlet)
            except KeyError:
                logger.debug(f"no outlet widget for {source_node_index}.{outlet}, link to node")
                source_widget = target_node_widget

            try:
                target_widget = self.inletWidget(target_node_index, inlet)
            except KeyError:
                logger.debug(f"no inlet widget for  {target_node_index}.{inlet}, link to node")
                target_widget = target_node_widget


            self._delegate.updateEdgePosition(edge_widget, source_widget, target_widget)

    def _updateEdges(self, rows:Iterable[int]):
        assert self._edges
        assert self._delegate
        for row in rows:
            edge_index = self._edges.index(row, 0)
            editor = self.linkWidget(edge_index)
            self._delegate.updateEdgeWidget(edge_index, editor)

    def _removeEdges(self, rows:Iterable[int]):
        assert self._edges
        rows = set(_ for _ in rows)
        for row in sorted(rows, reverse=True):
            edge_index = self._edges.index(row, 0)
            edge_id = QPersistentModelIndex(edge_index)
            edge_widget = self.linkWidget(edge_index)
            assert edge_widget, "edge_widget is None"
            source_node_index, outlet = self._edges.data(edge_index, GraphDataRole.LinkSourceRole)
            target_node_index, inlet = self._edges.data(edge_index, GraphDataRole.LinkTargetRole)
            source_node_editor = self.nodeWidget(source_node_index)
            target_node_editor = self.nodeWidget(target_node_index)
            self._node_out_links[source_node_editor].remove(edge_widget)
            self._node_in_links[target_node_editor].remove(edge_widget)
            self.scene().removeItem(edge_widget)
            del self._edge_widgets[edge_id]
        
    def _moveAttachedLinks(self, node_widget:QGraphicsItem):
        assert self._edges
        assert self._delegate
        from itertools import chain

        for edge_widget in chain(self._node_in_links[node_widget], self._node_out_links[node_widget]):
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
    def nodeWidgets(self)->Collection[QGraphicsItem]:
        return [item for item in self._node_widgets.values()]

    def edgeWidgets(self)->Collection[QGraphicsItem]:
        return [item for item in self._edge_widgets.values()]

    def nodeWidget(self, node_index: QModelIndex|QPersistentModelIndex) -> QGraphicsItem:
        assert self._edges, "self._edges was not defined"
        assert node_index.isValid() and node_index.model() == self._nodes, f"bad node_index, got: {node_index}"
        node_id = QPersistentModelIndex(node_index)
        widget=self._node_widgets[node_id]
        return widget

    def outletWidget(self, node_index: QModelIndex|QPersistentModelIndex, outlet:str) -> QGraphicsItem:
        assert self._edges, "self._edges was not defined"
        outlet_id = QPersistentModelIndex(node_index), outlet
        assert node_index.isValid(), f"invalid index, got: {node_index}"
        widget=self._outlet_widgets[outlet_id]
        return widget

    def inletWidget(self, node_index: QModelIndex|QPersistentModelIndex, inlet:str) -> QGraphicsItem:
        assert self._edges
        assert node_index.isValid()
        inlet_id = QPersistentModelIndex(node_index), inlet
        widget=self._inlet_widgets[inlet_id]
        return widget

    def linkWidget(self, edge_index:QModelIndex|QPersistentModelIndex) -> QGraphicsItem:
        assert self._edges, "self._edges was not defined"
        if not edge_index.isValid():
            raise KeyError()

        edge_id = QPersistentModelIndex(edge_index)
        widget = self._edge_widgets[edge_id]
        return widget

    ### Widgets At Position
    def nodeIndexAt(self, pos: QPoint) -> QModelIndex|None:
        """Returns the topmost node at position pos, which is in viewport coordinates."""
        assert self._nodes, "self._nodes was not defined"
        for item in self.items(pos.x()-4,pos.y()-4,8,8):
            if item in self._node_widgets.values():
                node_id =  self._node_widgets.inverse[item]
                return self._nodes.index(node_id.row(), 0)

    def inletIndexAt(self, pos: QPoint)->tuple[QModelIndex, str]|None:
        """Returns the topmost inlet at position pos, which is in viewport coordinates."""
        assert self._nodes, "self._nodes was not defined"
        for item in self.items(pos.x()-4,pos.y()-4,8,8):
            if item in self._inlet_widgets.values():
                inlet_id = self._inlet_widgets.inverse[item]
                node_id, inlet = inlet_id
                return self._nodes.index(node_id.row(), 0), inlet

    def outletIndexAt(self, pos: QPoint)->tuple[QModelIndex, str]|None:
        """Returns the topmost outlet at position pos, which is in viewport coordinates."""
        assert self._nodes, "self._nodes was not defined"
        for item in self.items(pos.x()-4,pos.y()-4,8,8):
            if item in self._outlet_widgets.values():
                outlet_it = self._outlet_widgets.inverse[item]
                node_id, outlet = outlet_it
                return self._nodes.index(node_id.row(), 0), outlet

    def edgeIndexAt(self, pos: QPoint) -> QModelIndex|None:
        """Returns the topmost edge at position pos, which is in viewport coordinates."""
        assert self._edges, "_edges was not defined"
        for item in self.items(pos.x()-4,pos.y()-4,8,8):
            if item in self._edge_widgets.values():
                edge_id =  self._edge_widgets.inverse[item]
                return self._edges.index(edge_id.row(), 0)


class _GraphSelectionMixin(_GraphEditorView):
    ### Node SELECTION
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._node_selection:QItemSelectionModel|None = None
        
    def setSelectionModel(self, node_selection:QItemSelectionModel):
        # assert id(node_selection.model()) != id(self._nodes), f"trying to set selection model, that works on a different model\n  {node_selection.model()}\n  !=\n  {self._nodes}"

        if self._node_selection:
            self._node_selection.selectionChanged.disconnect(self._onNodeSelectionChanged)
            self.scene().selectionChanged.disconnect(self._syncNodeSelectionModel)

        if node_selection:
            node_selection.selectionChanged.connect(self._onNodeSelectionChanged)
            self.scene().selectionChanged.connect(self._syncNodeSelectionModel)

        # set selection model
        self._node_selection = node_selection

    def _onNodeSelectionChanged(self, selected: QItemSelection, deselected: QItemSelection):
        """on selection model changed"""
        assert self._node_selection, "_node_selection is None"

        ### update widgets selection
        selected_node_indexes = set([
            index.siblingAtColumn(0) 
            for index in self._node_selection.selectedIndexes()
        ])

        new_node_widgets_selection = set([
            self.nodeWidget(index) 
            for index in selected_node_indexes
        ])

        current_node_widgets_selection = set([
            item for item in self.scene().selectedItems() 
            if item in self._node_widgets.inverse
        ])

        from pylive.utils.diff import diff_set
        node_widget_selection_change = diff_set(current_node_widgets_selection, new_node_widgets_selection)

        with signalsBlocked(self.scene()):
            for node_widget in node_widget_selection_change.added:
                node_widget.setSelected(True)

            for node_widget in node_widget_selection_change.removed:
                node_widget.setSelected(False)

    def _syncNodeSelectionModel(self):
        """called when the graphicsScene selection has changed"""
        assert self._node_selection, "_node_selection is None"
        assert self._nodes, "_nodes is None"
  
        selected_items = list(self.scene().selectedItems())
        selected_node_widgets = list(filter(lambda item: item in self._node_widgets.inverse, selected_items))
        selected_node_indexes = [self._node_widgets.inverse[node_widget] for node_widget in selected_node_widgets]
        selected_node_rows = sorted(node_index.row() for node_index in selected_node_indexes)

        from pylive.utils import group_consecutive_numbers
        selected_row_ranges = list( group_consecutive_numbers(selected_node_rows) )

        new_selection = QItemSelection()
        for row_range in selected_row_ranges:
            top_left = self._nodes.index(row_range.start, 0)
            bottom_right = self._nodes.index(row_range.stop-1, self._nodes.columnCount()-1)
            selection_range = QItemSelectionRange(top_left, bottom_right)
            new_selection.append(selection_range)

        if new_selection.count()>0:
            self._node_selection.setCurrentIndex(new_selection.at(0).topLeft(), QItemSelectionModel.SelectionFlag.Current)
        else:
            self._node_selection.setCurrentIndex(QModelIndex(), QItemSelectionModel.SelectionFlag.Clear)
        self._node_selection.select(new_selection, QItemSelectionModel.SelectionFlag.ClearAndSelect)


class _GraphLayoutMixin(_GraphEditorView):
    ### Layout
    def layoutNodes(self, orientation=Qt.Orientation.Vertical, scale=100):
        logger.debug('layoutNodes')
        assert self._edges, f"bad _edges, got: {self._edges}"
        assert self._nodes
        from pylive.utils.graph import hiearchical_layout_with_nx
        import networkx as nx
        G = nx.MultiDiGraph()
        for row in range(self._nodes.rowCount()):
            persistent_node_index = QPersistentModelIndex( self._nodes.index(row, 0) )
            G.add_node(persistent_node_index)

        for row in range(self._edges.rowCount()):
            edge_index = self._edges.index(row, 0)
            source_node_index, outlet = self._edges.data(edge_index, GraphDataRole.LinkSourceRole)
            target_node_index, inlet = self._edges.data(edge_index, GraphDataRole.LinkTargetRole)

            G.add_edge(source_node_index, target_node_index)
        pos:dict[QModelIndex, tuple[float, float]] = hiearchical_layout_with_nx(G, scale=scale)
        for node_index, (x, y) in pos.items():
            if node_widget := self.nodeWidget(node_index):
                match orientation:
                    case Qt.Orientation.Vertical:
                        node_widget.setPos(x, y)
                    case Qt.Orientation.Horizontal:
                        node_widget.setPos(y, x)

    def _resetWidgets(self):
        super()._resetWidgets()
        self.layoutNodes()


class _GraphDragAndDropMixin(_GraphEditorView):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._draft_link: QGraphicsItem | None = None
        self._drag_started = True
        self._drag_valid = False
        self._current_drag_type = None

    ### Widget Event Handlers
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self._handleMouseEvent(event):
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if not self._handleMouseEvent(event):
            return super().mouseReleaseEvent(event)

    def _handleMouseEvent(self, event: QMouseEvent) -> bool:
        def event_action(event: QMouseEvent):
            match event.type():
                case event.Type.MouseButtonPress:
                    return "Press"
                case event.Type.MouseButtonRelease:
                    return "Release"
                case _:
                    return None

        def item_kind(item):
            if item in self._outlet_widgets.inverse:
                return 'outlet', self._outlet_widgets.inverse[item]
            elif item in self._inlet_widgets.inverse:
                return 'inlet', self._inlet_widgets.inverse[item]
            elif item in self._node_widgets.inverse:
                return 'node', self._node_widgets.inverse[item]
            elif item in self._edge_widgets.inverse:
                return 'edge', self._edge_widgets.inverse[item]
            return None, None

        if action := event_action(event):
            for item in self.items(event.position().toPoint()):
                kind, item_id = item_kind(item)
                if kind:
                    item_event_handler = getattr(self, f"{kind}{action}Event")
                    return item_event_handler(item_id, event)
        return False

    def nodePressEvent(self, index: QPersistentModelIndex, event: QMouseEvent) -> bool:
        return False

    def outletPressEvent(self, outlet_id: tuple[QPersistentModelIndex, str], event: QMouseEvent) -> bool:
        node_index, outlet_name = outlet_id
        self.startDragOutlet(node_index.row(), outlet_name)
        return True

    def inletPressEvent(self, inlet_id: tuple[QPersistentModelIndex, str], event: QMouseEvent) -> bool:
        node_index, inlet_name = inlet_id
        self.startDragInlet(node_index.row(), inlet_name)
        return True

    def edgePressEvent(self, index: QModelIndex | QPersistentModelIndex, event: QMouseEvent) -> bool:
        assert self._edges

        # source_node_index = index.data(self.SourceRole)
        # target_node_index = index.data(self.TargetRole)
        outlet_id = self._edges.data(self._edges.index(index.row(), 0), GraphDataRole.LinkSourceRole)
        source_node_index, outlet = outlet_id
        inlet_id = self._edges.data(self._edges.index(index.row(), 0), GraphDataRole.LinkTargetRole)
        target_node_index, inlet = inlet_id

        outlet_widget = self.outletWidget(source_node_index, outlet)
        inlet_widget = self.inletWidget(target_node_index, inlet)
        assert outlet_widget
        assert inlet_widget
        mouse_pos = self.mapToScene(event.position().toPoint())

        d1 = (mouse_pos - outlet_widget.pos()).manhattanLength()
        d2 = (mouse_pos - inlet_widget.pos()).manhattanLength()
        if d1 > d2:
            self.startDragEdgeSource(index)
        else:
            self.startDragEdgeTarget(index)
        return True

    def nodeReleaseEvent(self, item: QGraphicsItem, event: QMouseEvent) -> bool:
        return False

    def outletReleaseEvent(self, item: QGraphicsItem, event: QMouseEvent) -> bool:
        return False

    def inletReleaseEvent(self, item: QGraphicsItem, event: QMouseEvent) -> bool:
        return False

    def edgeReleaseEvent(self, item: QGraphicsItem, event: QMouseEvent) -> bool:
        return False

    ### DRAG links and ports
    def _createDraftLink(self):
        assert self._delegate
        """Safely create draft link with state tracking"""
        if self._draft_link:
            # Clean up any existing draft
            self.scene().removeItem(self._draft_link)
            self._draft_link = None
            
        self._draft_link = self._delegate.createEdgeWidget(QModelIndex())
        self.scene().addItem(self._draft_link)

    def _cleanupDraftLink(self):
        """Safely cleanup draft link"""
        if self._draft_link:
            self.scene().removeItem(self._draft_link)
            self._draft_link = None

    def startDragOutlet(self, node_row:int, outlet_name:str):
        """Start outlet drag"""
        logger.debug(f"startDragOutlet")
        assert self._edges, "self._edges was not defined"
        
        # Clean any existing state
        self._drag_started = False
        self._drag_valid = False
        self._current_drag_type = None
        self._cleanupDraftLink()

        # Setup new drag
        mime = QMimeData()
        mime.setData('application/outlet', f"{node_row}/{outlet_name}".encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)

        # Create visual feedback
        self._createDraftLink()
        
        # try
        action = drag.exec(Qt.DropAction.LinkAction)

        # cleanup
        self._cleanupDraftLink()
        logger.debug(f"startDragOutlet ended: {action}")

    def startDragInlet(self, node_row:int, inlet_name:str):
        logger.debug(f"startDragInlet")
        """ Initiate the drag operation """
        assert self._edges, "self._edges was not defined"
        
        # Clean any existing state
        self._drag_started = False
        self._drag_valid = False
        self._current_drag_type = None
        self._cleanupDraftLink()

        # Setup new drag
        mime = QMimeData()
        mime.setData('application/inlet', f"{node_row}/{inlet_name}".encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)

        # Create visual feedback
        self._createDraftLink()
        
        # Execute drag
        # try:
        action = drag.exec(Qt.DropAction.LinkAction)
        # finally:
        # Always cleanup
        self._cleanupDraftLink()
        logger.debug(f"startDragInlet ended: {action}")

    def startDragEdgeSource(self, edge_index:QModelIndex|QPersistentModelIndex):
        logger.debug(f"startDragEdgeSource")
        """ Initiate the drag operation """
        assert self._node_selection, "self._node_selection was not defined"
        assert self._edges, f"bad self._edges, got{self._edges}"

        # Clean any existing state
        self._drag_started = False
        self._drag_valid = False
        self._current_drag_type = None
        self._cleanupDraftLink()

        # Setup new drag
        mime = QMimeData()
        mime.setData('application/edge/source', f"{edge_index.row()}".encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)
        
        # Execute drag
        # try:
        action = drag.exec(Qt.DropAction.LinkAction)
        # finally:
        # Always cleanup
        self._cleanupDraftLink()
        logger.debug(f"end startDragEdgeSource")

    def startDragEdgeTarget(self, edge_index:QModelIndex|QPersistentModelIndex):
        logger.debug(f"startDragEdgeTarget")
        """ Initiate the drag operation """
        assert self._node_selection, "self._node_selection was not defined"
        assert self._edges, f"bad self._edges, got{self._edges}"

        # Clean any existing state
        self._drag_started = False
        self._drag_valid = False
        self._current_drag_type = None
        self._cleanupDraftLink()

        # Setup new drag
        mime = QMimeData()
        mime.setData('application/edge/target', f"{edge_index.row()}".encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)
        
        # Execute drag
        # try:
        action = drag.exec(Qt.DropAction.LinkAction)
        # finally:
        # Always cleanup
        self._cleanupDraftLink()
        logger.debug(f"end startDragEdgeTarget")

    def dragEnterEvent(self, event: QDragEnterEvent):
        logger.debug(f"dragEnterEvent")
        """Handle drag enter with state tracking"""
        # log_caller()
        mime = event.mimeData()
        
        # Reset state
        self._drag_started = True
        self._drag_valid = False
        self._current_drag_type = None
        
        # Check valid mime types
        if mime.hasFormat('application/outlet'):
            self._current_drag_type = 'outlet'
            self._drag_valid = True
        elif mime.hasFormat('application/inlet'):
            self._current_drag_type = 'inlet' 
            self._drag_valid = True
        elif mime.hasFormat('application/edge/source'):
            self._current_drag_type = 'edge_source'
            self._drag_valid = True
        elif mime.hasFormat('application/edge/target'):
            self._current_drag_type = 'edge_target'
            self._drag_valid = True
            
        if self._drag_valid:
            event.accept()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        """Handle drag move with state validation"""
        logger.debug(f"dragMoveEvent")
        if not self._drag_valid or not self._current_drag_type:
            event.ignore()
            return
            
        # Use state to determine handler
        match self._current_drag_type:
            case 'outlet':
                self.dragMoveOutletEvent(event)
                event.accept()
            case 'inlet':
                self.dragMoveInletEvent(event)
                event.accept()
            case 'edge_source':
                self.dragMoveEdgeSourceEvent(event)
                event.accept()
            case 'edge_target':
                self.dragMoveEdgeTargetEvent(event)
                event.accept()
            case _:
                print(f"bad current_drag_type, {self._current_drag_type}")
                raise ValueError(f"bad drag type: {self._current_drag_type}")

    def dragMoveOutletEvent(self, event:QDragMoveEvent):
        logger.debug(f"dragMoveOutletEvent")
        assert self._nodes, "_edges was not defined"
        assert self._draft_link, "self._draft_link was not defined"
        assert self._delegate
        source = event.mimeData().data('application/outlet').toStdString().split("/")
        source_row, source_outlet = int(source[0]), source[1]
        source_node_index = self._nodes.index(source_row, 0)
        source_outlet_widget = self.outletWidget(source_node_index, source_outlet)

        assert isinstance(source_row, int), f"source_row is not an int!, got: {source_row}"
        assert source_node_index.isValid()
        assert source_outlet_widget

        target_node_index, inlet = self.inletIndexAt(event.position().toPoint()) or (None, None)
        target_inlet_widget = self.inletWidget(target_node_index, inlet) if (target_node_index and inlet) else None

        if source_outlet_widget and target_inlet_widget:
            self._delegate.updateEdgePosition(self._draft_link, source_outlet_widget, target_inlet_widget)
        elif source_outlet_widget:
            scene_pos = self.mapToScene(event.position().toPoint())
            self._delegate.updateEdgePosition(self._draft_link, source_outlet_widget, scene_pos)

    def dragMoveInletEvent(self, event:QDragMoveEvent):
        logger.debug(f"dragMoveInletEvent")
        try:
            assert self._nodes, "self._nodes does not exist"
            assert self._draft_link, "self._draft_link does not exist"
            assert self._delegate, "self._delegate does not exist"
            source = event.mimeData().data('application/inlet').toStdString().split("/")
            print(source)
            source_row, source_outlet = int(source[0]), source[1]
            source_node_index = self._nodes.index(source_row, 0)
            source_inlet_widget = self.inletWidget(source_node_index, source_outlet)

            assert isinstance(source_row, int), "source_row must be an int"
            assert source_node_index.isValid(), "source_node_index is not valid"
            assert source_inlet_widget, "source_inlet_widget is None"

            target_node_index, outlet = self.outletIndexAt(event.position().toPoint()) or (None, None)
            target_outlet_widget = self.outletWidget(target_node_index, outlet) if (target_node_index and outlet) else None

            if source_inlet_widget and target_outlet_widget:
                self._delegate.updateEdgePosition(self._draft_link, target_outlet_widget, source_inlet_widget)

            if source_inlet_widget:
                scene_pos = self.mapToScene(event.position().toPoint())
                self._delegate.updateEdgePosition(self._draft_link, scene_pos, source_inlet_widget)
        except Exception as err:
            traceback.print_exc()

    def dragMoveEdgeTargetEvent(self, event:QDragMoveEvent):
        logger.debug(f"dragMoveEdgeTargetEvent")
        assert self._edges
        assert not self._draft_link
        assert self._delegate
        edge_row = int(event.mimeData().data('application/edge/target').toStdString())
        
        source_node_index, outlet = self._edges.data(self._edges.index(edge_row, 0), GraphDataRole.LinkSourceRole)
        source_outlet_widget = self.outletWidget(source_node_index, outlet)

        assert source_node_index.isValid()
        assert source_outlet_widget

        target_node_index, inlet_name = self.inletIndexAt(event.position().toPoint()) or (None, None)
        target_inlet_widget = self.inletWidget(target_node_index, inlet_name) if (target_node_index and inlet_name) else None

        if source_outlet_widget and target_inlet_widget:
            edge_index = self._edges.index(edge_row, 0)
            edge_widget = self.linkWidget(edge_index)
            self._delegate.updateEdgePosition(edge_widget, source_outlet_widget, target_inlet_widget)

        elif source_outlet_widget:
            edge_index = self._edges.index(edge_row, 0)
            edge_widget = self.linkWidget(edge_index)
            scene_pos = self.mapToScene(event.position().toPoint())
            self._delegate.updateEdgePosition(edge_widget, source_outlet_widget, scene_pos)

    def dragMoveEdgeSourceEvent(self, event:QDragMoveEvent):
        logger.debug(f"dragMoveEdgeSourceEvent")
        assert self._edges
        assert not self._draft_link
        assert self._delegate

        edge_row = int(event.mimeData().data('application/edge/source').toStdString())

        target_node_index, inlet = self._edges.data(self._edges.index(edge_row, 0), GraphDataRole.LinkTargetRole)

        target_inlet_widget = self.inletWidget(target_node_index, inlet)

        assert target_node_index.isValid()
        assert target_inlet_widget

        source_node_index, outlet_name = self.outletIndexAt(event.position().toPoint()) or (None, None)
        source_outlet_widget = self.outletWidget(source_node_index, outlet_name) if (source_node_index and outlet_name) else None

        if source_outlet_widget and target_inlet_widget:
            edge_index = self._edges.index(edge_row, 0)
            edge_widget = self.linkWidget(edge_index)
            self._delegate.updateEdgePosition(edge_widget, source_outlet_widget, target_inlet_widget)

        elif target_inlet_widget:
            edge_index = self._edges.index(edge_row, 0)
            edge_widget = self.linkWidget(edge_index)
            scene_pos = self.mapToScene(event.position().toPoint())
            self._delegate.updateEdgePosition(edge_widget, scene_pos, target_inlet_widget)

    def dropEvent(self, event: QDropEvent):
        logger.debug(f"dropEvent")
        """Handle drop with state cleanup"""
        if not self._drag_valid or not self._current_drag_type:
            event.ignore()
            return
            
        # try:
        match self._current_drag_type:
            case 'outlet':
                self.dropOutletEvent(event)
            case 'inlet':
                self.dropInletEvent(event)
            case 'edge_source':
                self.dropEdgeSourceEvent(event)
            case 'edge_target':
                self.dropEdgeTargetEvent(event)
        # finally:
        # Always clean up state
        self._drag_started = False
        self._drag_valid = False
        self._current_drag_type = None

    def dropOutletEvent(self, event:QDropEvent):
        logger.debug(f"dropOutletEvent")
        if event.proposedAction() == Qt.DropAction.LinkAction:
            assert self._edges, f"bad self._edges, got{self._edges}"
            assert self._nodes, f"bad self._nodes, got{self._nodes}"
            source = event.mimeData().data('application/outlet').toStdString().split("/")
            source_row, source_outlet = int(source[0]), source[1]
            source_node_index = self._nodes.index(source_row, 0)

            target_inlet_id = self.inletIndexAt(event.position().toPoint())


            if source_node_index and target_inlet_id:
                assert self._edges, "self._edges is None"
                target_node_index, inlet_name = target_inlet_id
                self.nodesLinked.emit(
                    source_node_index, 
                    target_node_index,
                    "out",
                    inlet_name
                )
                event.acceptProposedAction()

    def dropInletEvent(self, event:QDropEvent):
        logger.debug(f"dropInletEvent")
        if event.proposedAction() == Qt.DropAction.LinkAction:
            assert self._edges, f"bad self._edges, got{self._edges}"
            assert self._nodes, f"bad self._nodes, got{self._nodes}"
            # parse mime data
            source_data = event.mimeData().data('application/inlet').toStdString().split("/")
            source_row, new_source_inlet_name = int(source_data[0]), source_data[1]
            new_source_node_index = self._nodes.index(source_row, 0)

            new_source_inlet_id = new_source_node_index, new_source_inlet_name
            target_outlet_id = self.outletIndexAt(event.position().toPoint())

            if new_source_inlet_id and target_outlet_id:
                # new edge
                target_node_index, outlet_name = target_outlet_id
                self.nodesLinked.emit(
                    target_node_index,
                    new_source_node_index,
                    outlet_name,
                    new_source_inlet_name
                )
                event.acceptProposedAction()
            else:
                # cancel
                pass

    def dropEdgeTargetEvent(self, event:QDropEvent):
        logger.debug(f"dropEdgeTargetEvent")
        assert self._edges, "bad self._edges"
        edge_row = int(event.mimeData().data('application/edge/target').toStdString())
        edge_source_node_index, outlet = self._edges.data(self._edges.index(edge_row, 0), GraphDataRole.LinkSourceRole)
        edge_target_node_index, inlet = self._edges.data(self._edges.index(edge_row, 0), GraphDataRole.LinkTargetRole)

        inlet_id_at_mouse = self.inletIndexAt(event.position().toPoint()) or None

        if inlet_id_at_mouse:
            if inlet_id_at_mouse == (edge_target_node_index, inlet):
                # do nothing
                pass
            else:
                #remove
                self._edges.removeRow(edge_row)
                # create
                self.nodesLinked.emit(
                    edge_source_node_index,
                    inlet_id_at_mouse[0],
                    outlet,
                    inlet_id_at_mouse[1]
                )
        else:
            # remove
            self._edges.removeRow(edge_row)

    def dropEdgeSourceEvent(self, event:QDropEvent):
        logger.debug(f"dropEdgeSourceEvent")
        assert self._edges, "bad self._edges"
        edge_row = int(event.mimeData().data('application/edge/source').toStdString())
        edge_source_node_index, outlet = self._edges.data(self._edges.index(edge_row, 0), GraphDataRole.LinkSourceRole)
        edge_target_node_index, inlet = self._edges.data(self._edges.index(edge_row, 0), GraphDataRole.LinkTargetRole)
        outlet_at_mouse = self.outletIndexAt(event.position().toPoint()) or None

        if outlet_at_mouse:
            new_source_node_index, new_outlet = outlet_at_mouse  # Get both new values
            if outlet_at_mouse == (edge_source_node_index, outlet):
                # do nothing
                pass
            else:
                #remove
                self._edges.removeRow(edge_row)
                # create
                self.nodesLinked.emit(
                    new_source_node_index,
                    edge_target_node_index,
                    new_outlet,
                    inlet
                )
        else:
            # remove
            self._edges.removeRow(edge_row)

    def dragLeaveEvent(self, event: QDragLeaveEvent)->None:
        logger.debug(f"dragLeaveEvent")
        """Handle drag leave with state cleanup"""
        if self._draft_link and self._drag_started:
            # Only clean up if we actually started the drag
            self._cleanupDraftLink()
            
        self._drag_started = False
        self._drag_valid = False
        self._current_drag_type = None
        
        event.accept()


from dataclasses import dataclass

@dataclass
class InternalDragController:
    mode: Literal['inlet', 'outlet', 'edge_source', 'edge_target']
    source_widget: QGraphicsItem
    draft: QGraphicsItem


class _InternalDragMixin(_GraphEditorView):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
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
    _InternalDragMixin,
    _GraphSelectionMixin, 
    _GraphLayoutMixin,
     _GraphEditorView
    ):
    ...


def main():
    app = QApplication()

    # model
    nodes = QStandardItemModel()
    nodes.setHeaderData(0, Qt.Orientation.Horizontal, "name")
    
    edges = QStandardItemModel()
    node_selection = QItemSelectionModel(nodes)
    edge_selection = QItemSelectionModel(edges)

    ### views
    nodelist = QListView()
    nodelist.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    nodelist.setModel(nodes)
    nodelist.setSelectionModel(node_selection)

    edgelist = QListView()
    edgelist.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    edgelist.setModel(edges)
    edgelist.setSelectionModel(edge_selection)

    graph_view = GraphEditorView()
    graph_view.setWindowTitle("NXNetworkScene")
    graph_view.setModel(nodes, edges)
    graph_view.setSelectionModel(node_selection)
    graph_view.centerNodes()

    ### ACTIONS
    window = QWidget()
    add_node_action = QPushButton("add new node", window)
    delete_node_action = QPushButton("delete node", window)
    connect_selected_nodes_action = QPushButton("connect selected nodes", window)
    remove_edge_action = QPushButton("remove edge", window)
    layout_action = QPushButton("layout nodes", window)

    buttons_layout = QGridLayout()
    buttons_layout.addWidget(add_node_action, 0, 0)
    buttons_layout.addWidget(delete_node_action, 0, 1)
    buttons_layout.addWidget(connect_selected_nodes_action, 1, 0)
    buttons_layout.addWidget(remove_edge_action, 1, 1)
    buttons_layout.addWidget(layout_action, 2, 0, 1, 2)

    grid_layout = QGridLayout()
    grid_layout.addLayout(buttons_layout, 0, 0)
    grid_layout.addWidget(nodelist, 1, 0)
    grid_layout.addWidget(edgelist, 2, 0)
    grid_layout.addWidget(graph_view, 0, 1, 3, 1)

    window.setLayout(grid_layout)
    window.show()

    ### commands
    def create_new_node():
        item = QStandardItem()
        node_names = map(lambda row: 
            nodes.data(nodes.index(row, 0), Qt.ItemDataRole.EditRole), 
            range(nodes.rowCount())
        )
        node_name = make_unique_name("node1", node_names)
        item.setData(node_name, Qt.ItemDataRole.DisplayRole)
        item.setData(["in1", "in2"], GraphDataRole.NodeInletsRole)
        item.setData(["out"], GraphDataRole.NodeOutletsRole)
        nodes.insertRow(nodes.rowCount(), item)

    def delete_selected_nodes():
        indexes:list[QModelIndex] = node_selection.selectedRows(column=0)
        indexes.sort(key=lambda index:index.row())
        for index in reversed(indexes):
            nodes.removeRows(index.row(), 1)

    def create_link(source_node_index:QModelIndex, target_node_index:QModelIndex, outlet:str, inlet:str):
        # source_node_index = edges.index(source_node_row, 0)
        # target_node_index = edges.index(target_node_row, 0)

        print(f"""create_link: {source_node_index} {target_node_index} {outlet} {inlet}

            """)
        edge_item = QStandardItem()
        outlet_id = QPersistentModelIndex(source_node_index), outlet
        inlet_id = QPersistentModelIndex(target_node_index), inlet
        edge_item.setData("edge", Qt.ItemDataRole.DisplayRole)
        edge_item.setData(outlet_id, GraphDataRole.LinkSourceRole)
        edge_item.setData(inlet_id, GraphDataRole.LinkTargetRole)
        edges.insertRow(edges.rowCount(), edge_item)

    def connect_selected_nodes():
        selected_rows = set([index.row() for index in node_selection.selectedIndexes()])
        if len(selected_rows)<2:
            return

        target_node_index = node_selection.currentIndex().siblingAtColumn(0)
        assert target_node_index.isValid(), "invalid target node"
        inlets = nodes.data(target_node_index, GraphDataRole.NodeInletsRole)
        assert len(inlets)>0
        for source_node_row in selected_rows:
            if target_node_index.row() == source_node_row:
                continue

            source_node_index = nodes.index(source_node_row, 0)
            assert source_node_index.isValid(), "invalid source node"
            create_link(source_node_index, target_node_index, "out", inlets[0])

    def delete_selected_edges():
        indexes:list[QModelIndex] = edge_selection.selectedRows(column=0)
        for index in sorted(indexes, key=lambda index:index.row(), reverse=True):
            edges.removeRows(index.row(), 1)

    ### bind view
    view_connections = [
        (add_node_action.pressed, create_new_node),
        (delete_node_action.pressed, delete_selected_nodes),
        (connect_selected_nodes_action.pressed, connect_selected_nodes),
        (remove_edge_action.pressed, delete_selected_edges),
        (layout_action.pressed, graph_view.layoutNodes),
        (graph_view.nodesLinked, create_link)
    ]
    for signal, slot in view_connections:
        signal.connect(slot)


    app.exec()

if __name__ == "__main__":
    main()

