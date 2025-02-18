#####################
# The Network Scene #
#####################

#
# A 'View' to represent a network of nodes, connected by inlets and outlets
#

# In QT ModelView terminology this is a 'View'.
# It is responsible to present the model.
# these widgets are responsible to reference the graphscene,
# and the represented nodes, edge and ports.
#

# TODO:
# - implement cancelling an ongoing drag event
#   eg with esc or right click etc.

# - consider allowing any QAbstractItemModel for the _edges_.
#   Currently only the _.edgeItem_, and _.addEdgeItem_ methods are used internally.
#   factoring out edgeItem is easy.
#   to factor out .addEdgeItem, 
#   we need to implement inserRows for the edge model.
#   inserRows are the default appending method but!
#   but! it will insert empty rows.
#   the View must be able to handle incomplete or empty edges.

# - consider using dragEnter instead of dragMovem since that seems to be the 
#   standard event to handle if dragging is accaptable.
#   this is more obvous on a mac.

# - consider refactoring drag and drop events since they are pretty repetitive.

# - refactor in v2 the delegate methods.
#   instead of createing widget within the delegate provide paint, sizeHint, shape
#   methods to define the node, item, edge visuals.
#   This will potentially lead to a GraphView that is able to use the builtin StyledItemDelegates

# - consider adding editors for column cell inside the node,
#   as if a node would be a row in a table, but in a different _view_


from typing import *
import typing
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from bidict import bidict
from collections import defaultdict
from pylive.utils.qt import distribute_items_horizontal, signalsBlocked

from pylive.VisualCode_v4.graph_editor.standard_graph_delegate import StandardGraphDelegate
from pylive.VisualCode_v4.graph_editor.standard_edges_model import StandardEdgesModel, StandardEdgeItem

# @runtime_checkable
# class NodesModelProtocol(Protocol):
#     def inlets(self, row)->Sequence[str]:
#         ...

#     def outlets(self, row)->Sequence[str]:
#         ...



class GraphEditorView(QGraphicsView):
    # SourceRole = Qt.ItemDataRole.UserRole+1
    # TargetRole = Qt.ItemDataRole.UserRole+2
    # InletsRole = Qt.ItemDataRole.UserRole+3
    # OutletsRole = Qt.ItemDataRole.UserRole+4
    nodesLinked = Signal(int, str, int, str)

    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._edges: StandardEdgesModel | None = None
        self._node_selection:QItemSelectionModel|None = None
        self._delegate: StandardGraphDelegate

        # store model widget relations
        self._node_widgets:   bidict[QPersistentModelIndex, QGraphicsItem] = bidict()
        self._edge_widgets:   bidict[QPersistentModelIndex, QGraphicsItem] = bidict()
        self._inlet_widgets:  bidict[tuple[QPersistentModelIndex, str], QGraphicsItem] = bidict()
        self._outlet_widgets: bidict[tuple[QPersistentModelIndex, str], QGraphicsItem] = bidict()
        self._node_inlets:    dict[QPersistentModelIndex, list[str]] = defaultdict(list)
        self._node_outlets:   dict[QPersistentModelIndex, list[str]] = defaultdict(list)

        self._node_in_links:defaultdict[QGraphicsItem, list[QGraphicsItem]] = defaultdict(list) # Notes: store attached links, because the underlzing model has to find the relevant edges  and thats is O(n)
        self._node_out_links:defaultdict[QGraphicsItem, list[QGraphicsItem]] = defaultdict(list) # Notes: store attached links, because the underlzing model has to find the relevant edges  and thats is O(n)

        self._draft_link: QGraphicsItem | None = None

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
        self.centerOn(self.scene().itemsBoundingRect().center())

    def setModel(self, edges:StandardEdgesModel|None):
        assert isinstance(edges, StandardEdgesModel), f"bad edges: {edges}"
        if self._edges:
            # Nodes
            self._edges.nodes().modelReset.disconnect(self._onNodesReset)
            self._edges.nodes().rowsInserted.disconnect(self._onNodesInserted)
            self._edges.nodes().rowsAboutToBeRemoved.disconnect(self._onNodesAboutToBeRemoved)
            self._edges.nodes().dataChanged.disconnect(self._onNodeDataChanged)

            # Edges
            self._edges.modelReset.disconnect(self._onEdgesReset)
            self._edges.rowsInserted.disconnect(self._onEdgesInserted)
            self._edges.rowsAboutToBeRemoved.disconnect(self._onEdgesAboutToBeRemoved)
            self._edges.dataChanged.disconnect(self._onEdgeDataChanged)

        if edges:
            # Nodes
            edges.nodes().modelReset.connect(self._onNodesReset)
            edges.nodes().rowsInserted.connect(self._onNodesInserted)
            edges.nodes().rowsAboutToBeRemoved.connect(self._onNodesAboutToBeRemoved)
            edges.nodes().dataChanged.connect(self._onNodeDataChanged)

            # Edges
            edges.modelReset.connect(self._onEdgesReset)
            edges.rowsInserted.connect(self._onEdgesInserted)
            edges.rowsAboutToBeRemoved.connect(self._onEdgesAboutToBeRemoved)
            edges.dataChanged.connect(self._onEdgeDataChanged)

        self._edges = edges

        # populate initial scene
        if self._edges.nodes() and self._edges.nodes().rowCount()>0:
            self._onNodesInserted(QModelIndex(), 0, self._edges.nodes().rowCount()-1)

        if self._edges and self._edges.rowCount() > 0:
            self._onEdgesInserted(QModelIndex(), 0, self._edges.nodes().rowCount()-1)

        # layout items
        self.layoutNodes()

    def model(self)->StandardEdgesModel|None:
        return self._edges

    def _moveAttachedLinks(self, node_widget:QGraphicsItem):
        assert self._edges and isinstance(self._edges, StandardEdgesModel)
        from itertools import chain

        for edge_widget in chain(self._node_in_links[node_widget], self._node_out_links[node_widget]):
            edge_index = self._edge_widgets.inverse[edge_widget]
            assert edge_widget in self._edge_widgets.values(), f"got: {edge_widget} not in {[_ for _ in self._edge_widgets.values()]}"
            edge_index = self._edge_widgets.inverse[edge_widget]

            source, outlet = self._edges.source(edge_index.row())
            target, inlet = self._edges.target(edge_index.row())

            try:
                source_widget = self.outletWidget(source, outlet)
            except KeyError:
                source_widget = self.nodeWidget(source)

            try:
                target_widget = self.inletWidget(target, inlet)
            except KeyError:
                target_widget = self.nodeWidget(target)

            self._delegate.updateEdgePosition(edge_widget, source_widget, target_widget)

    def setDelegate(self, delegate:StandardGraphDelegate):
        self._delegate = delegate
        self._delegate.nodePositionChanged.connect(self._moveAttachedLinks)

    def setSelectionModel(self, node_selection:QItemSelectionModel):
        if self._node_selection:
            self._node_selection.selectionChanged.disconnect(self._onNodeSelectionChanged)
            self.scene().selectionChanged.disconnect(self._syncNodeSelectionModel)

        if node_selection:
            node_selection.selectionChanged.connect(self._onNodeSelectionChanged)
            self.scene().selectionChanged.connect(self._syncNodeSelectionModel)

        # set selection model
        self._node_selection = node_selection

    ### <<< Handle Model Signals
    def _onNodesReset(self):
        assert self._edges, "self._edges is None"
        ### clear graph
        self._node_widgets.clear()
        self._node_in_links.clear()
        self._node_out_links.clear()

        ### populate graph with nodes
        indexes = [
            self._edges.nodes().index(row, 0)
            for row in range(self._edges.nodes().rowCount())
        ]

        self._addNodes(indexes)

        # layout items
        self.layoutNodes()

    def _onEdgesReset(self):
        assert self._edges, "self._edge is None"
        ### clear graph
        self._edge_widgets.clear()

        ### populate graph with edges
        if self._edges.rowCount()>0:
            self._onEdgesInserted(QModelIndex(), 0, self._edges.rowCount()-1)

        # layout items
        self.layoutNodes()

    def _onNodesInserted(self, parent:QModelIndex, first:int, last:int):
        assert self._edges, "self._edges is None"
        indexes = [
            self._edges.nodes().index(row, 0)
            for row in range(first, last+1)
        ]

        self._addNodes(indexes)

    def _onNodesAboutToBeRemoved(self, parent:QModelIndex, first:int, last:int):
        assert self._edges, "self._edges is None"
        indexes = (
            self._edges.nodes().index(row, 0)
            for row in range(first, last+1)
        )
        self._removeNodes(indexes)

    def _onNodeDataChanged(self, top_left:QModelIndex, bottom_right:QModelIndex, roles:list[int]=[]):
        """
        The optional roles argument can be used to specify which data roles have actually been modified.
        An empty vector in the roles argument means that all roles should be considered modified"""
        assert self._edges, "self._edges is None"

        indexes = [
            self._edges.nodes().index(row, 0)
            for row in range(top_left.row(), bottom_right.row()+1)
        ]

        self._updateNodes(indexes, roles)

    def _onEdgesInserted(self, parent:QModelIndex, first:int, last:int):
        assert self._edges, "self._edges is None"

        indexes = (
            self._edges.index(row, 0)
            for row in range(first, last+1)
        )

        self._addEdges(indexes)

    def _onEdgesAboutToBeRemoved(self, parent:QModelIndex, first:int, last:int):
        assert self._edges, "self._edges is None"
        indexes = (
            self._edges.index(row, 0)
            for row in range(first, last+1)
        )
        self._removeEdges(indexes)

    def _onEdgeDataChanged(self, top_left:QModelIndex, bottom_right:QModelIndex, roles:list[int]=[]):
        """
        The optional roles argument can be used to specify which data roles have actually been modified.
        An empty vector in the roles argument means that all roles should be considered modified"""
        assert self._edges, "self._edges is None"
        indexes = (
            self._edges.index(row, 0)
            for row in range(top_left.row(), bottom_right.row()+1)
        )
        self._updateEdges(indexes)

    def _addNodes(self, indexes:Iterable[QModelIndex]):
        assert self._edges, "no self._edges"
        for node_index in indexes:
            assert node_index.isValid(), "invalid persistent node?"
            node_widget = self._delegate.createNodeWidget(self.scene(), node_index)
            node_id = QPersistentModelIndex(node_index)
            self._node_widgets[node_id] = node_widget
            self._node_out_links[node_widget] = []
            self._node_in_links[node_widget] = []

            if inlets := self._edges.inlets(node_index):
                self._insertInlets(node_index, 0, inlets)

            if outlets := self._edges.outlets(node_index):
                self._insertOutlets(node_index, 0, outlets)

    def _insertInlets(self, node_index:QModelIndex, start:int, inlets:Iterable[str]):
        node_id = QPersistentModelIndex(node_index)
        node_widget = self.nodeWidget(node_index)
        for i, inlet in enumerate(inlets, start=start):
            inlet_widget = self._delegate.createInletWidget(node_widget, node_index, inlet, i)
            inlet_widget.setParentItem(node_widget)
            inlet_id = node_id, inlet
            self._inlet_widgets[inlet_id] = inlet_widget
            self._node_inlets[node_id].insert(i, inlet)

        # layout inlets
        inlet_widgets = [self.inletWidget(node_index, inlet) for inlet in self._node_inlets[node_id]]
        distribute_items_horizontal(inlet_widgets, node_widget.boundingRect())

        # layout edges
        self._moveAttachedLinks(node_widget)

    def _removeInlets(self, node_index:QModelIndex, inlets:Iterable[str]):
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

    def _insertOutlets(self, node_index:QModelIndex, start:int, outlets:Iterable[str]):
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

    def _removeNodes(self, indexes:Iterable[QModelIndex]):
        assert self._edges, "self._noded cant be None"
        for node_index in indexes:
            node_id = QPersistentModelIndex(node_index)
            node_widget = self.nodeWidget(node_index)
            self.scene().removeItem(node_widget)
            
            del self._node_out_links[node_widget]
            del self._node_in_links[node_widget]
            del self._node_widgets[node_id]

    def _updateNodes(self, indexes:Iterable[QModelIndex], roles:list[int]):
        assert self._edges, "self._edges cant be None"
        for node_index in filter(lambda idx: QPersistentModelIndex(idx) in self._node_widgets, indexes):

            node_id = QPersistentModelIndex(node_index)
            node_widget = self.nodeWidget(node_id)
            self._delegate.updateNodeWidget(node_index, node_widget)

    def _resetInlets(self, node_index:QModelIndex):
        assert self._edges, "self._edges cant be None"
        node_id = QPersistentModelIndex(node_index)
        self._removeInlets(node_index, self._node_inlets[node_id])
        inlets = self._edges.inlets(node_index)
        self._insertInlets(node_index, 0, inlets)

    def _resetOutlets(self, node_index:QModelIndex):
        assert self._edges, "self._edges cant be None"
        node_id = QPersistentModelIndex(node_index)
        outlets = self._edges.outlets(node_index)
        self._insertOutlets(node_index, 0, outlets)
        self._removeOutlets(node_index, self._node_outlets[node_id])

    def _addEdges(self, indexes:Iterable[QModelIndex]):
        assert self._edges and isinstance(self._edges, StandardEdgesModel), f"bad self._edges, got{self._edges}"
        indexes = list(indexes)
        assert all(index.model() == self._edges for index in indexes), f"got: {indexes}"
        for edge_index in indexes:
            ### create edge editor
            edge_id = QPersistentModelIndex(edge_index)
            edge_widget = self._delegate.createEdgeWidget(edge_index)
            self._edge_widgets[edge_id] = edge_widget
            self.scene().addItem( edge_widget )

            #UPDATE LINKS POSITION
            source_node_index, outlet = self._edges.source(edge_index.row())
            target_node_index, inlet = self._edges.target(edge_index.row())

            
            source_node_widget = self.nodeWidget(source_node_index)
            target_node_widget = self.nodeWidget(target_node_index)

            self._node_out_links[source_node_widget].append(edge_widget)
            self._node_in_links[target_node_widget].append(edge_widget)


            try:
                source_widget = self.outletWidget(source_node_index, outlet)
            except KeyError:
                source_widget = target_node_widget

            try:
                target_widget = self.inletWidget(target_node_index, inlet)
            except KeyError:
                target_widget = target_node_widget


            self._delegate.updateEdgePosition(edge_widget, source_widget, target_widget)

    def _removeEdges(self, indexes:Iterable[QModelIndex]):
        assert self._edges
        for edge_index in indexes:
            edge_id = QPersistentModelIndex(edge_index)
            edge_widget = self.linkWidget(edge_index)
            assert edge_widget, "edge_widget is None"
            source_node_index, outlet = self._edges.source(edge_index.row())
            target_node_index, inlet = self._edges.target(edge_index.row())
            source_node_editor = self.nodeWidget(source_node_index)
            target_node_editor = self.nodeWidget(target_node_index)
            self._node_out_links[source_node_editor].remove(edge_widget)
            self._node_in_links[target_node_editor].remove(edge_widget)
            self.scene().removeItem(edge_widget)
            del self._edge_widgets[edge_id]
        
    def _updateEdges(self, indexes:Iterable[QModelIndex]):
        for edge_index in indexes:
            editor = self.linkWidget(edge_index)
            self._delegate.updateEdgeWidget(edge_index, editor)

    def _onNodeSelectionChanged(self, selected: QItemSelection, deselected: QItemSelection):
        """on selection model changed"""
        assert self._node_selection, "_node_selection is None"

        ### update widgets seleection
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
        """called when the graphicsscene selection has changed"""
        assert self._node_selection, "_node_selection is None"
        assert self._edges, "_edges is None"
  
        selected_items = list(self.scene().selectedItems())
        selected_node_widgets = list(filter(lambda item: item in self._node_widgets.inverse, selected_items))
        selected_node_indexes = [self._node_widgets.inverse[node_widget] for node_widget in selected_node_widgets]
        selected_node_rows = sorted(node_index.row() for node_index in selected_node_indexes)

        from pylive.utils import group_consecutive_numbers
        selected_row_ranges = list( group_consecutive_numbers(selected_node_rows) )

        new_selection = QItemSelection()
        for row_range in selected_row_ranges:
            top_left = self._edges.nodes().index(row_range.start, 0)
            bottom_right = self._edges.nodes().index(row_range.stop-1, self._edges.nodes().columnCount()-1)
            selection_range = QItemSelectionRange(top_left, bottom_right)
            new_selection.append(selection_range)

        if new_selection.count()>0:
            self._node_selection.setCurrentIndex(new_selection.at(0).topLeft(), QItemSelectionModel.SelectionFlag.Current)
        else:
            self._node_selection.setCurrentIndex(QModelIndex(), QItemSelectionModel.SelectionFlag.Clear)
        self._node_selection.select(new_selection, QItemSelectionModel.SelectionFlag.ClearAndSelect)

    ### <<< Handle Model Signals

    ### Map the interactive graphics ids to widgets >>>

    def nodeWidgets(self)->Collection[QGraphicsItem]:
        return [item for item in self._node_widgets.values()]

    def edgeWidgets(self)->Collection[QGraphicsItem]:
        return [item for item in self._edge_widgets.values()]

    def nodeWidget(self, node_index: QModelIndex|QPersistentModelIndex) -> QGraphicsItem:
        assert self._edges, "self._edges was not defined"
        assert node_index.isValid() and node_index.model() == self._edges.nodes(), f"bad node_index, got: {node_index}"
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

    def nodeIndexAt(self, pos: QPoint) -> QModelIndex|None:
        """Returns the topmost node at position pos, which is in viewport coordinates."""
        assert self._edges, "self._edges was not defined"
        for item in self.items(pos.x()-4,pos.y()-4,8,8):
            if item in self._node_widgets.values():
                node_id =  self._node_widgets.inverse[item]
                return self._edges.nodes().index(node_id.row(), 0)

    def inletIndexAt(self, pos: QPoint)->tuple[QModelIndex, str]|None:
        """Returns the topmost inlet at position pos, which is in viewport coordinates."""
        assert self._edges, "self._edges was not defined"
        for item in self.items(pos.x()-4,pos.y()-4,8,8):
            if item in self._inlet_widgets.values():
                inlet_id = self._inlet_widgets.inverse[item]
                node_id, inlet = inlet_id
                return self._edges.nodes().index(node_id.row(), 0), inlet

    def outletIndexAt(self, pos: QPoint)->tuple[QModelIndex, str]|None:
        """Returns the topmost outlet at position pos, which is in viewport coordinates."""
        assert self._edges, "self._edges was not defined"
        for item in self.items(pos.x()-4,pos.y()-4,8,8):
            if item in self._outlet_widgets.values():
                outlet_it = self._outlet_widgets.inverse[item]
                node_id, outlet = outlet_it
                return self._edges.nodes().index(node_id.row(), 0), outlet

    def edgeIndexAt(self, pos: QPoint) -> QModelIndex|None:
        """Returns the topmost edge at position pos, which is in viewport coordinates."""
        assert self._edges, "_edges was not defined"
        for item in self.items(pos.x()-4,pos.y()-4,8,8):
            if item in self._edge_widgets.values():
                edge_id =  self._edge_widgets.inverse[item]
                return self._edges.index(edge_id.row(), 0)

    def layoutNodes(self, orientation=Qt.Orientation.Vertical, scale=100):
        assert self._edges and isinstance(self._edges, StandardEdgesModel), f"bad _edges, got: {self._edges}"
        from pylive.utils.graph import hiearchical_layout_with_nx
        import networkx as nx
        G = nx.MultiDiGraph()
        for row in range(self._edges.nodes().rowCount()):
            persistent_node_index = QPersistentModelIndex( self._edges.nodes().index(row, 0) )
            G.add_node(persistent_node_index)

        for row in range(self._edges.rowCount()):
            edge_index = self._edges.index(row, 0)
            source_node_index, _ = self._edges.source(edge_index.row())
            target_node_index, _ = self._edges.target(edge_index.row())

            G.add_edge(source_node_index, target_node_index)
        pos:dict[QModelIndex, tuple[float, float]] = hiearchical_layout_with_nx(G, scale=scale)
        for node_index, (x, y) in pos.items():
            if node_widget := self.nodeWidget(node_index):
                match orientation:
                    case Qt.Orientation.Vertical:
                        node_widget.setPos(x, y)
                    case Qt.Orientation.Horizontal:
                        node_widget.setPos(y, x)

    ### DRAG inlets, outlets, edges
    def _createDraftLink(self):
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
        
        try:
            action = drag.exec(Qt.DropAction.LinkAction)
        finally:
            # Always cleanup
            self._cleanupDraftLink()

    def startDragInlet(self, node_row:int, inlet_name:str):
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
        try:
            action = drag.exec(Qt.DropAction.LinkAction)
        finally:
            # Always cleanup
            self._cleanupDraftLink()

    def startDragEdgeSource(self, edge_index:QModelIndex|QPersistentModelIndex):
        """ Initiate the drag operation """
        assert self._node_selection, "self._node_selection was not defined"
        assert self._edges and isinstance(self._edges, StandardEdgesModel), f"bad self._edges, got{self._edges}"

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
        try:
            action = drag.exec(Qt.DropAction.LinkAction)
        finally:
            # Always cleanup
            self._cleanupDraftLink()

    def startDragEdgeTarget(self, edge_index:QModelIndex|QPersistentModelIndex):
        """ Initiate the drag operation """
        assert self._node_selection, "self._node_selection was not defined"
        assert self._edges and isinstance(self._edges, StandardEdgesModel), f"bad self._edges, got{self._edges}"

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
        try:
            action = drag.exec(Qt.DropAction.LinkAction)
        finally:
            # Always cleanup
            self._cleanupDraftLink()

    @override
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter with state tracking"""
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

    @override
    def dragMoveEvent(self, event: QDragMoveEvent):
        """Handle drag move with state validation"""
        if not self._drag_valid or not self._current_drag_type:
            event.ignore()
            return
            
        # Use state to determine handler
        match self._current_drag_type:
            case 'outlet':
                self.dragMoveOutletEvent(event)
            case 'inlet':
                self.dragMoveInletEvent(event)
            case 'edge_source':
                self.dragMoveEdgeSourceEvent(event)
            case 'edge_target':
                self.dragMoveEdgeTargetEvent(event)

    def dragMoveOutletEvent(self, event:QDragMoveEvent):
        assert self._edges, "_edges was not defined"
        assert self._draft_link, "self._draft_link was not defined"
        source = event.mimeData().data('application/outlet').toStdString().split("/")
        source_row, source_outlet = int(source[0]), source[1]
        source_node_index = self._edges.nodes().index(source_row, 0)
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
        assert self._edges
        assert self._draft_link
        source = event.mimeData().data('application/inlet').toStdString().split("/")
        source_row, source_outlet = int(source[0]), source[1]
        source_node_index = self._edges.nodes().index(source_row, 0)
        source_inlet_widget = self.inletWidget(source_node_index, source_outlet)

        assert isinstance(source_row, int)
        assert source_node_index.isValid()
        assert source_inlet_widget

        target_node_index, outlet = self.outletIndexAt(event.position().toPoint()) or (None, None)
        target_outlet_widget = self.outletWidget(target_node_index, outlet) if (target_node_index and outlet) else None

        if source_inlet_widget and target_outlet_widget:
            self._delegate.updateEdgePosition(self._draft_link, target_outlet_widget, source_inlet_widget)
        elif source_inlet_widget:
            scene_pos = self.mapToScene(event.position().toPoint())
            self._delegate.updateEdgePosition(self._draft_link, scene_pos, source_inlet_widget)

    def dragMoveEdgeTargetEvent(self, event:QDragMoveEvent):
        assert self._edges and isinstance(self._edges, StandardEdgesModel)
        assert not self._draft_link
        edge_row = int(event.mimeData().data('application/edge/target').toStdString())
        
        source_node_index, outlet = self._edges.source(edge_row)
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
        assert self._edges and isinstance(self._edges, StandardEdgesModel)
        assert not self._draft_link

        edge_row = int(event.mimeData().data('application/edge/source').toStdString())

        target_node_index, inlet = self._edges.target(int(edge_row))

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

    @override
    def dropEvent(self, event: QDropEvent):
        """Handle drop with state cleanup"""
        if not self._drag_valid or not self._current_drag_type:
            event.ignore()
            return
            
        try:
            match self._current_drag_type:
                case 'outlet':
                    self.dropOutletEvent(event)
                case 'inlet':
                    self.dropInletEvent(event)
                case 'edge_source':
                    self.dropEdgeSourceEvent(event)
                case 'edge_target':
                    self.dropEdgeTargetEvent(event)
        finally:
            # Always clean up state
            self._drag_started = False
            self._drag_valid = False
            self._current_drag_type = None

    def dropOutletEvent(self, event:QDropEvent):
        if event.proposedAction() == Qt.DropAction.LinkAction:
            assert self._edges and isinstance(self._edges, StandardEdgesModel), f"bad self._edges, got{self._edges}"
            source = event.mimeData().data('application/outlet').toStdString().split("/")
            source_row, source_outlet = int(source[0]), source[1]
            source_node_index = self._edges.nodes().index(source_row, 0)

            target_inlet_id = self.inletIndexAt(event.position().toPoint())


            if source_node_index and target_inlet_id:
                assert self._edges, "self._edges is None"
                target_node_index, inlet_name = target_inlet_id
                self._edges.appendEdgeItem(StandardEdgeItem(
                    QPersistentModelIndex(source_node_index), 
                    QPersistentModelIndex(target_node_index),
                    "out",
                    inlet_name
                ))
                event.acceptProposedAction()

    def dropInletEvent(self, event:QDropEvent):
        if event.proposedAction() == Qt.DropAction.LinkAction:
            assert self._edges and isinstance(self._edges, StandardEdgesModel), f"bad self._edges, got{self._edges}"
            # parse mime data
            source_data = event.mimeData().data('application/inlet').toStdString().split("/")
            source_row, source_inlet_name = int(source_data[0]), source_data[1]
            source_node_index = self._edges.nodes().index(source_row, 0)

            source_inlet_id = source_node_index, source_inlet_name
            target_outlet_id = self.outletIndexAt(event.position().toPoint())

            if source_inlet_id and target_outlet_id:
                # new edge
                target_node_index, outlet_name = target_outlet_id
                self._edges.appendEdgeItem(StandardEdgeItem(
                    QPersistentModelIndex(target_node_index),
                    QPersistentModelIndex(source_node_index), 
                    outlet_name,
                    source_inlet_name
                ))
                event.acceptProposedAction()
            else:
                # cancel
                pass

    def dropEdgeTargetEvent(self, event:QDropEvent):
        assert self._edges and isinstance(self._edges, StandardEdgesModel), "bad self._edges"
        edge_row = int(event.mimeData().data('application/edge/target').toStdString())
        edge_source_node_index, outlet = self._edges.source(edge_row)
        edge_target_node_index, inlet = self._edges.target(edge_row)

        inlet_at_mouse = self.inletIndexAt(event.position().toPoint()) or None

        if inlet_at_mouse:
            if inlet_at_mouse == (edge_target_node_index, inlet):
                # do nothing
                pass
            else:
                #remove
                self._edges.removeRow(edge_row)
                # create
                self._edges.appendEdgeItem(StandardEdgeItem(
                    source = QPersistentModelIndex(edge_source_node_index),
                    target= QPersistentModelIndex(inlet_at_mouse[0]),
                    outlet=outlet,
                    inlet=inlet_at_mouse[1]
                ))
        else:
            # remove
            self._edges.removeRow(edge_row)

    def dropEdgeSourceEvent(self, event:QDropEvent):
        assert self._edges and isinstance(self._edges, StandardEdgesModel), "bad self._edges"
        edge_row = int(event.mimeData().data('application/edge/source').toStdString())
        edge_source_node_index, outlet = self._edges.source(edge_row)
        edge_target_node_index, inlet = self._edges.target(edge_row)
        outlet_at_mouse = self.outletIndexAt(event.position().toPoint()) or None

        if outlet_at_mouse:
            if outlet_at_mouse == (edge_source_node_index, outlet):
                # do nothing
                pass
            else:
                #remove
                self._edges.removeRow(edge_row)
                # create
                self._edges.appendEdgeItem(StandardEdgeItem(
                    source = QPersistentModelIndex(outlet_at_mouse[0]),
                    target= QPersistentModelIndex(edge_target_node_index),
                    outlet=outlet,
                    inlet=inlet
                ))
        else:
            # remove
            self._edges.removeRow(edge_row)

    @override
    def dragLeaveEvent(self, event: QDragLeaveEvent)->None:
        """Handle drag leave with state cleanup"""
        if self._draft_link and self._drag_started:
            # Only clean up if we actually started the drag
            self._cleanupDraftLink()
            
        self._drag_started = False
        self._drag_valid = False
        self._current_drag_type = None
        
        event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self._handleMouseEvent(event):
            return super().mousePressEvent(event)

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
                kind, item_id=item_kind(item)
                if kind:
                    item_event_handler = getattr(self, f"{kind}{action}Event")
                    return item_event_handler(item_id, event)
        return False

    def nodePressEvent(self, index:QPersistentModelIndex, event: QMouseEvent) -> bool:
        return False

    def outletPressEvent(self, outlet_id:tuple[QPersistentModelIndex, str], event: QMouseEvent) -> bool:
        node_index, outlet_name = outlet_id
        self.startDragOutlet(node_index.row(), outlet_name)
        return True

    def inletPressEvent(self, inlet_id:tuple[QPersistentModelIndex, str], event: QMouseEvent) -> bool:
        node_index, inlet_name = inlet_id
        self.startDragInlet(node_index.row(), inlet_name)
        return True

    def edgePressEvent(self, index:QModelIndex|QPersistentModelIndex, event: QMouseEvent) -> bool:
        assert self._edges and isinstance(self._edges, StandardEdgesModel)


        # source_node_index = index.data(self.SourceRole)
        # target_node_index = index.data(self.TargetRole)
        outlet_id = self._edges.source(index.row())
        inlet_id = self._edges.target(index.row())


        outlet_widget = self.outletWidget(*outlet_id)
        inlet_widget = self.inletWidget(*inlet_id)
        assert outlet_widget
        assert inlet_widget
        mouse_pos = self.mapToScene(event.position().toPoint())

        d1 = (mouse_pos-outlet_widget.pos()).manhattanLength()
        d2 = (mouse_pos-inlet_widget.pos()).manhattanLength()
        if d1>d2:
            self.startDragEdgeSource(index)
        else:
            self.startDragEdgeTarget(index)
        return True

    def nodeReleaseEvent(self, item:QGraphicsItem, event: QMouseEvent) -> bool:
        return False

    def outletReleaseEvent(self, item:QGraphicsItem, event: QMouseEvent) -> bool:
        return False

    def inletReleaseEvent(self, item:QGraphicsItem, event: QMouseEvent) -> bool:
        return False

    def edgeReleaseEvent(self, item:QGraphicsItem, event: QMouseEvent) -> bool:
        return False

def main():
    from pylive.VisualCode_v4.graph_editor.standard_edges_model import StandardEdgeItem, StandardEdgesModel

    app = QApplication()

    ### model state
    class MyNodesModel(QStandardItemModel):
        def __init__(self, parent:QObject|None=None):
            super().__init__(parent)

        # def inlets(self, row:int)->Sequence[str]:
        #     return [inlet.strip() 
        #         for inlet in self.data(self.index(row, 1), Qt.ItemDataRole.DisplayRole).split(";")
        #     ]

        # def outlets(self, row:int)->Sequence[str]:
        #     return [outlet.strip() 
        #         for outlet in self.data(self.index(row, 2), Qt.ItemDataRole.DisplayRole).split(";")
        #     ]

    class MyEdgesModel(StandardEdgesModel):
        def inlets(self, node:QModelIndex, /)->Sequence[str]:
            assert nodes
            assert node.isValid()
            return [inlet.strip() 
                for inlet in self.nodes().data(self.nodes().index(node.row(), 1), Qt.ItemDataRole.DisplayRole).split(";")
            ]

        def outlets(self, node:QModelIndex, /)->Sequence[str]:
            assert node.isValid()
            return [outlet.strip() 
                for outlet in self.nodes().data(self.nodes().index(node.row(), 2), Qt.ItemDataRole.DisplayRole).split(";")
            ]

    nodes = MyNodesModel()
    nodes.setHeaderData(0, Qt.Orientation.Horizontal, "name")
    
    edges = MyEdgesModel(nodes=nodes)
    node_selection = QItemSelectionModel(nodes)
    edge_selection = QItemSelectionModel(edges)

    def listen(model):
        model.modelReset.connect(lambda: print("modelReset"))
        model.dataChanged.connect(lambda tl, br, roles: print("dataChanged", tl, br, roles))
        model.rowsInserted.connect(lambda parent, first, last: print("rowsInserted", parent, first, last))
        model.rowsRemoved.connect(lambda parent, first, last: print("rowsRemoved", parent, first, last))
    
    # listen(nodes)
    # listen(edges)
    ### actions, commands
    row = 0
    def create_new_node():
        nonlocal row
        row+=1
        item = QStandardItem()
        nodes.insertRow(nodes.rowCount(), [
            QStandardItem(f"node{row}"),
            QStandardItem(f"in1; in2"),
            QStandardItem(f"out")
        ])

    def delete_selected_nodes():
        indexes:list[QModelIndex] = node_selection.selectedRows(column=0)
        indexes.sort(key=lambda index:index.row())
        for index in reversed(indexes):
            nodes.removeRows(index.row(), 1)

    def connect_selected_nodes():
        selected_rows = set([index.row() for index in node_selection.selectedIndexes()])
        if len(selected_rows)<2:
            return

        target_node_index = node_selection.currentIndex().siblingAtColumn(0)
        assert target_node_index.isValid(), "invalid target node"
        inlets = edges.inlets(target_node_index)
        assert len(inlets)>0
        for source_node_row in selected_rows:
            if target_node_index.row() == source_node_row:
                continue

            source_node_index = nodes.index(source_node_row, 0)
            assert source_node_index.isValid(), "invalid source node"

            edges.appendEdgeItem(StandardEdgeItem(
                source=QPersistentModelIndex(source_node_index),
                target=QPersistentModelIndex(target_node_index),
                outlet="out",
                inlet=inlets[0]
            ))

    def delete_selected_edges():
        indexes:list[QModelIndex] = edge_selection.selectedRows(column=0)
        for index in sorted(indexes, key=lambda index:index.row(), reverse=True):
            edges.removeRows(index.row(), 1)

    ### view
    nodelist = QListView()
    nodelist.setModel(nodes)
    nodelist.setSelectionModel(node_selection)
    nodelist.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

    edgelist = QTableView()
    edgelist.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    edgelist.setModel(edges)
    edgelist.setSelectionModel(edge_selection)
    edgelist.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    edgelist.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

    graph_view = GraphEditorView()
    graph_view.setWindowTitle("NXNetworkScene")
    graph_view.setModel(edges)
    graph_view.setSelectionModel(node_selection)
    graph_view.centerNodes()


    ### ACTIONS
    window = QWidget()
    add_node_action = QPushButton("add new node", window)
    add_node_action.pressed.connect(create_new_node)
    delete_node_action = QPushButton("delete node", window)
    delete_node_action.pressed.connect(delete_selected_nodes)
    connect_selected_nodes_action = QPushButton("connect selected nodes", window)
    connect_selected_nodes_action.pressed.connect(connect_selected_nodes)
    remove_edge_action = QPushButton("remove edge", window)
    remove_edge_action.pressed.connect(delete_selected_edges)
    layout_action = QPushButton("layout nodes", window)
    layout_action.pressed.connect(graph_view.layoutNodes)

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

    app.exec()

if __name__ == "__main__":
    main()

