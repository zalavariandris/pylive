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
# TODO: move the model editing capabilities
# from the widgets to a delegate, or the graphsene itself


from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


##############
# GRAPHSCENE #
##############

from bidict import bidict
from collections import defaultdict
from pylive.QtGraphEditor.dag_model import EdgeItem, DAGModel
from pylive.QtGraphEditor.standard_graph_delegate import StandardGraphDelegate

from pylive.utils.qt import modelReset, signalsBlocked
from pylive.utils.unique import make_unique_id

"""
TODO:
- implement cancelling an ongoing drag event
  eg with esc or right click etc.

- consider allowing any QAbstractItemModel for the _edges_.
  Currently only the _.edgeItem_, and _.addEdgeItem_ methods are used internally.
  factoring out edgeItem is easy.
  to factor out .addEdgeItem, 
  we need to implement inserRows for the edge model.
  inserRows are the default appending method but!
  but! it will insert empty rows.
  the View must be able to handle incomplete or empty edges.

- consider using dragEnter instead of dragMovem since that seems to be the 
  standard event to handle if dragging is accaptable.
  this is more obvous on a mac.

- consider refactoring drag and drop events since they are pretty repetitive.

- refactor in v2 the delegate methods.
  instead of createing widget within the delegate provide paint, sizeHint, shape
  methods to define the node, item, edge visuals.
  This will potentially lead to a GraphView that is able to use the builtin StyledItemDelegates

- consider adding editors for column cell inside the node,
  as if a node would be a row in a table, but in a different _view_
"""

class DAGEditorView(QGraphicsView):
    SourceRole = Qt.ItemDataRole.UserRole+1
    TargetRole = Qt.ItemDataRole.UserRole+2
    InletsRole = Qt.ItemDataRole.UserRole+3
    OutletsRole = Qt.ItemDataRole.UserRole+4

    def __init__(self, ):
        super().__init__()

        scene = QGraphicsScene()
        scene.setSceneRect(QRectF(-9999,-9999,9999*2, 9999*2))
        self.setScene(scene)

        self._nodes: QAbstractItemModel | None = None
        self._edges: DAGModel | None = None
        self._node_selection:QItemSelectionModel|None = None
        self._delegate: StandardGraphDelegate
        self.setDelegate(StandardGraphDelegate())

        # configure QGraphicsScene
        # self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

        # store model widget relations
        self._node_graphics_objects:   bidict[QPersistentModelIndex, QGraphicsItem] = bidict()
        self._link_graphics_objects:   bidict[QPersistentModelIndex, QGraphicsItem] = bidict()
        self._inlet_graphics_objects:  bidict[tuple[QPersistentModelIndex, str], QGraphicsItem] = bidict()
        self._outlet_graphics_objects: bidict[tuple[QPersistentModelIndex, str], QGraphicsItem] = bidict()

        self._node_in_links:defaultdict[QGraphicsItem, list[QGraphicsItem]] = defaultdict(list) # Notes: store attached links, because the underlzing model has to find the relevant edges  and thats is O(n)
        self._node_out_links:defaultdict[QGraphicsItem, list[QGraphicsItem]] = defaultdict(list) # Notes: store attached links, because the underlzing model has to find the relevant edges  and thats is O(n)
        # self._outlet_graphics_objects: bidict[tuple[QPersistentModelIndex, str], QGraphicsItem] = bidict()
        # self._inlet_graphics_objects: bidict[tuple[QPersistentModelIndex, str], QGraphicsItem] = bidict()
        
        self._draft_link: QGraphicsItem | None = None
        self._link_loop = QEventLoop(self)

        # self._attribute_editors: bidict[tuple[QPersistentModelIndex, str], QGraphicsItem] = bidict()

        # set model
        # populate with initial model
        # self.setModel(model)
        # self.setSelectionModel(selection_model
        

    def setModel(self, nodes: QAbstractItemModel, edges:DAGModel):
        if self._nodes:
            # Nodes
            self._nodes.modelReset.disconnect(self._onNodesReset)
            self._nodes.rowsInserted.disconnect(self._onNodesInserted)
            self._nodes.rowsAboutToBeRemoved.disconnect(self._onNodesAboutToBeRemoved)
            self._nodes.dataChanged.disconnect(self._onNodeDataChanged)

        if self._edges:
            # Nodes
            self._edges.modelReset.disconnect(self._onEdgesReset)
            self._edges.rowsInserted.disconnect(self._onEdgesInserted)
            self._edges.rowsAboutToBeRemoved.disconnect(self._onEdgesAboutToBeRemoved)
            self._edges.dataChanged.disconnect(self._onEdgeDataChanged)

        if nodes:
            # Nodes
            nodes.modelReset.connect(self._onNodesReset)
            nodes.rowsInserted.connect(self._onNodesInserted)
            nodes.rowsAboutToBeRemoved.connect(self._onNodesAboutToBeRemoved)
            nodes.dataChanged.connect(self._onNodeDataChanged)

        if edges:
            # Nodes
            edges.modelReset.connect(self._onEdgesReset)
            edges.rowsInserted.connect(self._onEdgesInserted)
            edges.rowsAboutToBeRemoved.connect(self._onEdgesAboutToBeRemoved)
            edges.dataChanged.connect(self._onEdgeDataChanged)

        self._nodes = nodes
        self._edges = edges

        # populate initial scene
        if self._nodes.rowCount()>0:
            self._onNodesInserted(QModelIndex(), 0, self._nodes.rowCount()-1)
        if self._edges.rowCount()>0:
            self._onEdgesInserted(QModelIndex(), 0, self._edges.rowCount()-1)

        # layout items
        self.layoutNodes()

    def model(self)->tuple[QAbstractItemModel|None, DAGModel|None]:
        return self._nodes, self._edges

    def _moveAttachedLinks(self, node_editor:QGraphicsItem):
        assert self._edges
        from itertools import chain

        for edge_editor in chain(self._node_in_links[node_editor], self._node_out_links[node_editor]):
            edge_index = self._link_graphics_objects.inverse[edge_editor]
            assert edge_editor in self._link_graphics_objects.values(), f"got: {edge_editor} not in {[_ for _ in self._link_graphics_objects.values()]}"
            edge_index = self._link_graphics_objects.inverse[edge_editor]
            edge_item = self._edges.edgeItem(edge_index.row())
            source_index = edge_item.source
            target_index = edge_item.target
            edge_key = edge_item.key
            source_outlet_widget = self._outlet_graphics_objects[(source_index, "out")]
            target_inlet_widget = self._inlet_graphics_objects[(target_index, edge_key)]
            self._delegate.updateEdgePosition(edge_editor, source_outlet_widget, target_inlet_widget)

    def setDelegate(self, delegate:StandardGraphDelegate):
        self._delegate = delegate
        self._delegate.nodePositionChanged.connect(self._moveAttachedLinks)

    def setSelectionModel(self, node_selection:QItemSelectionModel):
        if self._node_selection:
            self._node_selection.selectionChanged.disconnect(self._onSelectionChanged)
            self.scene().selectionChanged.disconnect(self._updateSelectionModel)

        if node_selection:
            node_selection.selectionChanged.connect(self._onSelectionChanged)
            self.scene().selectionChanged.connect(self._updateSelectionModel)

        # set selection model
        self._node_selection = node_selection

    def _updateSelectionModel(self):
        """called when the graphicsscene selection has changed"""
        if not self._node_selection:
            return
        assert self._nodes
  
        # get selected rows
        selected_rows = []
        for item in self.scene().selectedItems():
            if index := self._node_graphics_objects.inverse.get(item, None):
                selected_rows.append(index.row())
        selected_rows.sort()

        # group selected rows to QItemSelectionRange
        from pylive.utils import group_consecutive_numbers
        new_selection = QItemSelection()
        if selected_rows:
            for row_range in group_consecutive_numbers(selected_rows):
                top_left = self._nodes.index(row_range.start, 0)
                bottom_right = self._nodes.index(row_range.stop-1, 0)
                new_selection.append(QItemSelectionRange(top_left, bottom_right))

        # set the selection
        if new_selection.count()>0:
            self._node_selection.setCurrentIndex(new_selection.at(0).topLeft(), QItemSelectionModel.SelectionFlag.Current)
        self._node_selection.select(new_selection, QItemSelectionModel.SelectionFlag.ClearAndSelect)

    ### <<< Handle Model Signals
    def _onNodesReset(self):
        assert self._nodes
        ### clear graph
        self._node_graphics_objects.clear()
        self._node_in_links.clear()
        self._node_out_links.clear()

        ### populate graph with nodes
        if self._nodes.rowCount()>0:
            self._onNodesInserted(QModelIndex(), 0, self._nodes.rowCount()-1)

        # layout items
        self.layoutNodes()

    def _onEdgesReset(self):
        assert self._edges
        ### clear graph
        self._link_graphics_objects.clear()

        ### populate graph with edges
        if self._edges.rowCount()>0:
            self._onEdgesInserted(QModelIndex(), 0, self._edges.rowCount()-1)

        # layout items
        self.layoutNodes()

    def _onNodesInserted(self, parent:QModelIndex, first:int, last:int):
        assert self._nodes
        indexes = [
            QPersistentModelIndex(self._nodes.index(row, 0)) 
            for row in range(first, last+1)
        ]

        self.addNodes(indexes)

    def _onNodesAboutToBeRemoved(self, parent:QModelIndex, first:int, last:int):
        assert self._nodes
        indexes = (
            QPersistentModelIndex(self._nodes.index(row, 0)) 
            for row in range(first, last+1)
        )
        self.removeNodes(indexes)

    def _onNodeDataChanged(self, top_left:QModelIndex, bottom_right:QModelIndex, roles:list[int]=[]):
        """
        The optional roles argument can be used to specify which data roles have actually been modified.
        An empty vector in the roles argument means that all roles should be considered modified"""
        assert self._nodes
        indexes = (
            QPersistentModelIndex(self._nodes.index(row, 0)) 
            for row in range(top_left.row(), bottom_right.row()+1)
        )
        self.updateNodes(indexes, roles)

    def _onEdgesInserted(self, parent:QModelIndex, first:int, last:int):
        assert self._edges

        indexes = (
            QPersistentModelIndex(self._edges.index(row, 0))
            for row in range(first, last+1)
        )

        self.addEdges(indexes)

    def _onEdgesAboutToBeRemoved(self, parent:QModelIndex, first:int, last:int):
        assert self._edges
        indexes = (
            QPersistentModelIndex(self._edges.index(row, 0))
            for row in range(first, last+1)
        )
        self.removeEdges(indexes)

    def _onEdgeDataChanged(self, top_left:QModelIndex, bottom_right:QModelIndex, roles:list[int]=[]):
        """
        The optional roles argument can be used to specify which data roles have actually been modified.
        An empty vector in the roles argument means that all roles should be considered modified"""
        assert self._edges
        indexes = (
            QPersistentModelIndex(self._edges.index(row, 0))
            for row in range(top_left.row(), bottom_right.row()+1)
            )
        self.updateEdges(indexes)

    def addNodes(self, indexes:Iterable[QPersistentModelIndex]):
        assert self._nodes
        for node_index in indexes:
            if node_editor := self._delegate.createNodeWidget(self.scene(), node_index):
                assert node_index.isValid(), "invalid persistent node?"
                self._node_graphics_objects[node_index] = node_editor

                if inlets := node_index.data(self.InletsRole):
                    assert isinstance(inlets, list)
                    self._addInlets(node_index, inlets)

                if outlets := node_index.data(self.OutletsRole):
                    assert isinstance(outlets, list)
                    self._addOutlets(node_index, outlets)
                    
    def _addInlets(self, node_index:QModelIndex|QPersistentModelIndex, inlets:list[str]):
        node_editor = self._node_graphics_objects[QPersistentModelIndex(node_index)]
        for inlet in inlets:
            if inlet_editor := self._delegate.createInletWidget(node_editor, node_index, inlet):
                inlet_id = QPersistentModelIndex(node_index), inlet
                self._inlet_graphics_objects[inlet_id] = inlet_editor

    def _addOutlets(self, node_index:QModelIndex|QPersistentModelIndex, outlets:list[str]):
        node_editor = self._node_graphics_objects[QPersistentModelIndex(node_index)]
        for outlet in outlets:
            if outlet_editor := self._delegate.createOutletWidget(node_editor, node_index, outlet):
                outlet_id = QPersistentModelIndex(node_index), outlet
                self._outlet_graphics_objects[outlet_id] = outlet_editor

    def removeNodes(self, indexes:Iterable[QPersistentModelIndex]):
        assert self._nodes
        for node_index in indexes:
            node_editor = self._node_graphics_objects[node_index]
            self.scene().removeItem(node_editor)

    def updateNodes(self, indexes:Iterable[QPersistentModelIndex], roles:list[int]):
        assert self._nodes
        for node_index in indexes:
            if editor := self._node_graphics_objects.get(node_index, None):
                self._delegate.updateNodeWidget(node_index, editor)

    def addEdges(self, indexes:Iterable[QPersistentModelIndex]):
        assert self._edges
        for edge_index in indexes:
            ### create edge editor
            if edge_editor := self._delegate.createEdgeWidget(edge_index):
                self._link_graphics_objects[edge_index] = edge_editor
                self.scene().addItem( edge_editor )

                #UPDATE LINKS POSITION
                edge_item = self._edges.edgeItem(edge_index.row())
                source_node_index = edge_item.source
                target_node_index = edge_item.target

                source_node_editor = self._node_graphics_objects[source_node_index]
                target_node_editor = self._node_graphics_objects[target_node_index]

                self._node_out_links[source_node_editor].append(edge_editor)
                self._node_in_links[target_node_editor].append(edge_editor)
                

                
                edge_key = edge_item.key
                source_outlet_widget = self._outlet_graphics_objects[(source_node_index, "out")]
                target_inlet_widget = self._inlet_graphics_objects[(target_node_index, edge_key)]
                self._delegate.updateEdgePosition(edge_editor, source_outlet_widget, target_inlet_widget)

    def removeEdges(self, indexes:Iterable[QPersistentModelIndex]):
        assert self._edges
        for edge_index in indexes:
            source_index = self._edges.data(edge_index, self.SourceRole)
            target_index = self._edges.data(edge_index, self.TargetRole)
            source_node_editor = self._node_graphics_objects[source_index]
            target_node_editor = self._node_graphics_objects[target_index]

            edge_editor = self._link_graphics_objects[edge_index]
            self.scene().removeItem(edge_editor)
        
    def updateEdges(self, indexes:Iterable[QPersistentModelIndex]):
        for edge_index in indexes:
            if editor := self._link_graphics_objects.get(edge_index, None):
                self._delegate.updateEdgeWidget(edge_index, editor)

    def changeNodeSelection(self, select: Iterable[QPersistentModelIndex], deselect:Iterable[QPersistentModelIndex]):
        with signalsBlocked(self):
            for node_index in select:
                editor = self._node_graphics_objects[node_index]
                editor.setSelected(True)

            for node_index in deselect:
                editor = self._node_graphics_objects[node_index]
                editor.setSelected(False)

        self.scene().selectionChanged.emit()

    def _onSelectionChanged(self, selected: QItemSelection, deselected: QItemSelection):
        """on selection model changed"""
        if selected.count()>0 or deselected.count()>0:
            selected_indexes = (
                QPersistentModelIndex(index)
                for index in selected.indexes()
            )

            deselected_indexes = (
                QPersistentModelIndex(index)
                for index in deselected.indexes()
            )
            self.changeNodeSelection(selected_indexes, deselected_indexes)

    ### <<< Handle Model Signals

    ### <<< Map the interactive graphics ids to widgets
    def nodeWidget(self, node_index: QModelIndex) -> QGraphicsItem|None:
        assert self._nodes
        if editor:=self._node_graphics_objects.get(QPersistentModelIndex(node_index)):
            return editor

    def outletWidget(self, node_index: QModelIndex, outlet:str) -> QGraphicsItem|None:
        assert self._nodes
        outlet_id = QPersistentModelIndex(node_index), outlet
        assert node_index.isValid(), f"got: {node_index}"
        assert outlet == "out"
        if editor:=self._outlet_graphics_objects.get(outlet_id):
            return editor
        else:
            print("all outlet widget:", self._outlet_graphics_objects)

    def inletWidget(self, node_index: QModelIndex, inlet:str) -> QGraphicsItem|None:
        assert self._nodes
        inlet_id = QPersistentModelIndex(node_index), inlet
        if editor:=self._inlet_graphics_objects.get(inlet_id):
            return editor

    def linkWidget(self, edge_index:QModelIndex) -> QGraphicsItem|None:
        assert self._edges
        if not edge_index.isValid():
            raise KeyError()

        if editor:=self._link_graphics_objects.get(QPersistentModelIndex(edge_index), None):
            return editor

    def nodeIndexAt(self, pos: QPoint) -> QModelIndex|None:
        """Returns the topmost node at position pos, which is in viewport coordinates."""
        assert self._nodes
        for item in self.items(pos.x()-4,pos.y()-4,8,8):
            if node_id :=  self._node_graphics_objects.inverse.get(item, None):
                return self._nodes.index(node_id.row(), 0)

    def inletIndexAt(self, pos: QPoint)->tuple[QModelIndex, str]|None:
        """Returns the topmost inlet at position pos, which is in viewport coordinates."""
        assert self._nodes
        for item in self.items(pos.x()-4,pos.y()-4,8,8):
            if node_inlet :=  self._inlet_graphics_objects.inverse.get(item, None):
                node_id, inlet = node_inlet
                return self._nodes.index(node_id.row(), 0), inlet

    def outletIndexAt(self, pos: QPoint)->tuple[QModelIndex, str]|None:
        """Returns the topmost outlet at position pos, which is in viewport coordinates."""
        assert self._nodes
        for item in self.items(pos.x()-4,pos.y()-4,8,8):
            if node_outlet :=  self._outlet_graphics_objects.inverse.get(item, None):
                node_id, outlet = node_outlet
                return self._nodes.index(node_id.row(), 0), outlet

    def edgeIndexAt(self, pos: QPoint) -> QModelIndex|None:
        """Returns the topmost edge at position pos, which is in viewport coordinates."""
        assert self._edges
        for item in self.items(pos.x()-4,pos.y()-4,8,8):
            if edge_id :=  self._link_graphics_objects.inverse.get(item, None):
                return self._edges.index(edge_id.row(), 0)

    def layoutNodes(self, orientation=Qt.Orientation.Vertical, scale=100):
        assert self._nodes
        assert self._edges
        from pylive.utils.graph import hiearchical_layout_with_nx
        import networkx as nx
        G = nx.MultiDiGraph()
        for row in range(self._nodes.rowCount()):
            persistent_node_index = QPersistentModelIndex( self._nodes.index(row, 0) )
            G.add_node(persistent_node_index)

        for row in range(self._edges.rowCount()):
            edge_index = self._edges.index(row, 0)
            source_node_index = self._edges.data(edge_index, DAGEditorView.SourceRole)
            target_node_index = self._edges.data(edge_index, DAGEditorView.TargetRole)
            assert source_node_index
            assert target_node_index
            G.add_edge(source_node_index, target_node_index)
        pos = hiearchical_layout_with_nx(G, scale=scale)
        for N, (x, y) in pos.items():
            widget = self._node_graphics_objects[N]
            match orientation:
                case Qt.Orientation.Vertical:
                    widget.setPos(x, y)
                case Qt.Orientation.Horizontal:
                    widget.setPos(y, x)

    ### DRAG inlets, outlets, edges
    def startDragOutlet(self, node_row:int, outlet_name:str):
        """ Initiate the drag operation """
        assert self._node_selection
        assert self._nodes

        mime = QMimeData()
        mime.setData('application/outlet', f"{node_row}/{outlet_name}".encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)

        self._draft_link = self._delegate.createEdgeWidget(QModelIndex())
        self.scene().addItem(self._draft_link)
        
        # Execute drag
        action = drag.exec(Qt.DropAction.LinkAction)
        if action == Qt.DropAction.LinkAction:
            print("link aciton")
        self.scene().removeItem(self._draft_link)
        self._draft_link = None

    def startDragInlet(self, node_row:int, inlet_name:str):
        """ Initiate the drag operation """
        assert self._node_selection
        assert self._nodes

        mime = QMimeData()
        mime.setData('application/inlet', f"{node_row}/{inlet_name}".encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)

        self._draft_link = self._delegate.createEdgeWidget(QModelIndex())
        self.scene().addItem(self._draft_link)
        
        # Execute drag
        action = drag.exec(Qt.DropAction.LinkAction)
        if action == Qt.DropAction.LinkAction:
            print("link aciton")
        self.scene().removeItem(self._draft_link)
        self._draft_link = None

    def startDragEdge(self, index:QModelIndex, endpoint:Literal['source', 'target'])->None:
        """ Initiate the drag operation """
        assert self._node_selection
        assert self._nodes
        source_node_index = index.data(self.SourceRole)
        target_node_index = index.data(self.TargetRole)
        outlet_name = "out"
        inlet_name = index.data(Qt.ItemDataRole.EditRole)

        mime = QMimeData()
        match endpoint:
            case 'source':
                mime.setData('application/edge/outlet', f"{source_node_index.row()}/{outlet_name}".encode("utf-8"))
            case 'target':
                mime.setData('application/edge/inlet', f"{target_node_index.row()}/{inlet_name}".encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)

        self._draft_link = self.linkWidget(index)
        
        # Execute drag
        action = drag.exec(Qt.DropAction.LinkAction)
        if action == Qt.DropAction.LinkAction:
            print("link aciton")
        self._draft_link = None

    def startDragEdgeSource(self, edge_index:QModelIndex):
        source_node_index = cast(QModelIndex, edge_index.data(self.SourceRole))
        target_node_index = cast(QModelIndex, edge_index.data(self.TargetRole))
        inlet_name = cast(str, edge_index.data(Qt.ItemDataRole.EditRole))
        outlet_name = "out"

        mime = QMimeData()
        mime.setData('application/edge/source', f"{edge_index.row()}".encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)

        self._draft_link = self.linkWidget(edge_index)
        
        # Execute drag
        action = drag.exec(Qt.DropAction.LinkAction)
        if action == Qt.DropAction.LinkAction:
            print("link aciton")
        self._draft_link = None

    def startDragEdgeTarget(self, edge_index:QModelIndex):
        """ Initiate the drag from edge inlet operation """
        target_node_index = cast(QModelIndex, edge_index.data(self.TargetRole))
        inlet_name = cast(str, edge_index.data(Qt.ItemDataRole.EditRole))

        mime = QMimeData()

        mime.setData('application/edge/target', f"{edge_index.row()}".encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)

        self._draft_link = self.linkWidget(edge_index)
        
        # Execute drag
        action = drag.exec(Qt.DropAction.LinkAction)
        if action == Qt.DropAction.LinkAction:
            print("link aciton")
        self._draft_link = None

    def dragEnterEvent(self, event:QDragEnterEvent):
        """ Accept drag events """
        if event.mimeData().hasFormat('application/outlet'):
            event.acceptProposedAction()
        elif event.mimeData().hasFormat('application/inlet'):
            event.acceptProposedAction()
        elif event.mimeData().hasFormat('application/edge/source'):
            event.acceptProposedAction()
        elif event.mimeData().hasFormat('application/edge/target'):
            event.acceptProposedAction()

        print("drag enter event")

    @override
    def dragMoveEvent(self, event:QDragMoveEvent):
        assert self._nodes
        if event.mimeData().hasFormat('application/outlet'):
            self.dragMoveOutletEvent(event)
            
        if event.mimeData().hasFormat('application/inlet'):
            self.dragMoveInletEvent(event)

        if event.mimeData().hasFormat('application/edge/source'):
            self.dragMoveEdgeSourceEvent(event)

        if event.mimeData().hasFormat('application/edge/target'):
            self.dragMoveEdgeTargetEvent(event)

    def dragMoveOutletEvent(self, event:QDragMoveEvent):
        assert self._nodes
        source = event.mimeData().data('application/outlet').toStdString().split("/")
        source_row, source_outlet = int(source[0]), source[1]
        source_node_index = self._nodes.index(source_row, 0)
        source_outlet_widget = self.outletWidget(source_node_index, source_outlet)

        assert isinstance(source_row, int)
        assert source_outlet == "out"
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
        assert self._nodes
        source = event.mimeData().data('application/inlet').toStdString().split("/")
        source_row, source_outlet = int(source[0]), source[1]
        source_node_index = self._nodes.index(source_row, 0)
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
        print("dragMoveEdgeTargetEvent")
        assert self._nodes
        assert self._edges
        edge_row = int(event.mimeData().data('application/edge/target').toStdString())
        edges_index = self._edges.index(edge_row, 0)

        source_outlet_name = "out"
        source_node_index = edges_index.data(self.SourceRole)
        source_outlet_widget = self.outletWidget(source_node_index, source_outlet_name)

        assert source_node_index.isValid()
        assert source_outlet_widget

        target_node_index, inlet_name = self.inletIndexAt(event.position().toPoint()) or (None, None)
        target_inlet_widget = self.inletWidget(target_node_index, inlet_name) if (target_node_index and inlet_name) else None

        if source_outlet_widget and target_inlet_widget:
            self._delegate.updateEdgePosition(self._draft_link, source_outlet_widget, target_inlet_widget)
        elif source_outlet_widget:
            scene_pos = self.mapToScene(event.position().toPoint())
            self._delegate.updateEdgePosition(self._draft_link, source_outlet_widget, scene_pos)

    def dragMoveEdgeSourceEvent(self, event:QDragMoveEvent):
        print("dragMoveEdgeSourceEvent")
        assert self._nodes
        assert self._edges
        edge_row = int(event.mimeData().data('application/edge/source').toStdString())
        edges_index = self._edges.index(int(edge_row), 0)

        target_inlet_name = edges_index.data(Qt.ItemDataRole.EditRole)
        target_node_index = edges_index.data(self.TargetRole)
        target_inlet_widget = self.inletWidget(target_node_index, target_inlet_name)

        assert target_node_index.isValid()
        assert target_inlet_widget

        source_node_index, outlet_name = self.outletIndexAt(event.position().toPoint()) or (None, None)
        source_outlet_widget = self.outletWidget(source_node_index, outlet_name) if (source_node_index and outlet_name) else None

        if source_outlet_widget and target_inlet_widget:
            self._delegate.updateEdgePosition(self._draft_link, source_outlet_widget, target_inlet_widget)
        elif target_inlet_widget:
            scene_pos = self.mapToScene(event.position().toPoint())
            self._delegate.updateEdgePosition(self._draft_link, scene_pos, target_inlet_widget)

    def dropEvent(self, event:QDropEvent):
        if event.mimeData().hasFormat('application/outlet'):
            self.dropOutletEvent(event)

        elif event.mimeData().hasFormat('application/inlet'):
            self.dropInletEvent(event)

        elif event.mimeData().hasFormat('application/edge/source'):
            self.dropEdgeSourceEvent(event)

        elif event.mimeData().hasFormat('application/edge/target'):
            self.dropEdgeTargetEvent(event)

    def dropOutletEvent(self, event:QDropEvent):
        if event.proposedAction() == Qt.DropAction.LinkAction:
            assert self._nodes
            source = event.mimeData().data('application/outlet').toStdString().split("/")
            source_row, source_outlet = int(source[0]), source[1]
            source_node_index = self._nodes.index(source_row, 0)

            target_inlet_id = self.inletIndexAt(event.position().toPoint())


            if source_node_index and target_inlet_id:
                assert self._edges
                target_node_index, inlet_name = target_inlet_id
                self._edges.addEdgeItem(EdgeItem(
                    QPersistentModelIndex(source_node_index), 
                    QPersistentModelIndex(target_node_index),
                    inlet_name
                ))
                event.acceptProposedAction()

    def dropInletEvent(self, event:QDropEvent):
        if event.proposedAction() == Qt.DropAction.LinkAction:
            assert self._nodes
            # parse mime data
            source_data = event.mimeData().data('application/inlet').toStdString().split("/")
            source_row, source_inlet_name = int(source_data[0]), source_data[1]
            source_node_index = self._nodes.index(source_row, 0)

            source_inlet_id = source_node_index, source_inlet_name
            target_outlet_id = self.outletIndexAt(event.position().toPoint())

            if source_inlet_id and target_outlet_id:
                # new edge
                assert self._edges
                target_node_index, outlet_name = target_outlet_id
                self._edges.addEdgeItem(EdgeItem(
                    QPersistentModelIndex(target_node_index),
                    QPersistentModelIndex(source_node_index), 
                    source_inlet_name
                ))
                event.acceptProposedAction()
            else:
                # cancel
                pass

    def dropEdgeTargetEvent(self, event:QDropEvent):
        print("dragMoveEdgeTargetEvent")
        assert self._nodes
        assert self._edges
        edge_row = int(event.mimeData().data('application/edge/target').toStdString())
        edge_item = self._edges.edgeItem(edge_row)
        target_at_mouse = self.inletIndexAt(event.position().toPoint()) or None

        if target_at_mouse:
            if target_at_mouse == (edge_item.source, edge_item.key):
                # do nothing
                pass
            else:
                #remove
                self._edges.removeRow(edge_row)
                # create
                self._edges.addEdgeItem(EdgeItem(
                    source = edge_item.source,
                    target= QPersistentModelIndex(target_at_mouse[0]),
                    key=target_at_mouse[1]
                ))
        else:
            # remove
            self._edges.removeRow(edge_row)

    def dropEdgeSourceEvent(self, event:QDropEvent):
        print("drop edge source event")
        assert self._nodes
        assert self._edges
        edge_row = int(event.mimeData().data('application/edge/target').toStdString())
        edge_item = self._edges.edgeItem(edge_row)
        outlet_at_mouse = self.outletIndexAt(event.position().toPoint()) or None

        if outlet_at_mouse:
            if outlet_at_mouse == (edge_item.target, "out"):
                # do nothing
                pass
            else:
                #remove
                self._edges.removeRow(edge_row)
                # create
                self._edges.addEdgeItem(EdgeItem(
                    source = QPersistentModelIndex(outlet_at_mouse[0]),
                    target= edge_item.target,
                    key=edge_item.key
                ))
        else:
            # remove
            self._edges.removeRow(edge_row)

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
            if item in self._outlet_graphics_objects.inverse:
                return 'outlet', self._outlet_graphics_objects.inverse[item]
            elif item in self._inlet_graphics_objects.inverse:
                return 'inlet', self._inlet_graphics_objects.inverse[item]
            elif item in self._node_graphics_objects.inverse:
                return 'node', self._node_graphics_objects.inverse[item]
            elif item in self._link_graphics_objects.inverse:
                return 'edge', self._link_graphics_objects.inverse[item]
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

    def edgePressEvent(self, index:QModelIndex, event: QMouseEvent) -> bool:
        source_node_index = index.data(self.SourceRole)
        target_node_index = index.data(self.TargetRole)
        outlet_id = source_node_index, "out"
        inlet_id = target_node_index, index.data(Qt.ItemDataRole.EditRole)
        assert outlet_id in self._outlet_graphics_objects, f"got {outlet_id}"
        assert inlet_id in self._inlet_graphics_objects, f"got {inlet_id}"
        outlet_widget = self._outlet_graphics_objects[outlet_id]
        inlet_widget = self._inlet_graphics_objects[inlet_id]
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
    app = QApplication()

    ### model state
    nodes = QStandardItemModel()
    nodes.setHeaderData(0, Qt.Orientation.Horizontal, "name")
    edges = DAGModel(nodes=nodes)
    node_selection = QItemSelectionModel(nodes)
    edge_selection = QItemSelectionModel(edges)

    def listen(model):
        model.modelReset.connect(lambda: print("modelReset"))
        model.dataChanged.connect(lambda tl, br, roles: print("dataChanged", tl, br, roles))
        model.rowsInserted.connect(lambda parent, first, last: print("rowsInserted", parent, first, last))
        model.rowsRemoved.connect(lambda parent, first, last: print("rowsRemoved", parent, first, last))
    
    listen(nodes)
    listen(edges)
    ### actions, commands
    row = 0
    def create_new_node():
        nonlocal row
        row+=1
        item = QStandardItem()
        item.setData(f"node{row}", Qt.ItemDataRole.DisplayRole)
        item.setData(["in1", "in2"], DAGEditorView.InletsRole)
        item.setData(["out"], DAGEditorView.OutletsRole)
        nodes.insertRow(nodes.rowCount(), item)

    def delete_selected_nodes():
        indexes:list[QModelIndex] = node_selection.selectedRows(column=0)
        indexes.sort(key=lambda index:index.row())
        for index in reversed(indexes):
            nodes.removeRows(index.row(), 1)

    def connect_selected_nodes():
        if len(node_selection.selectedRows(0))<2:
            return

        target_node_index = node_selection.currentIndex().siblingAtColumn(0)
        assert target_node_index.isValid()
        inlets = nodes.data(target_node_index, DAGEditorView.InletsRole)
        assert len(inlets)>0
        for source_node_index in node_selection.selectedRows(0):
            if target_node_index == source_node_index:
                continue

            assert source_node_index.isValid()
            edges.addEdgeItem(EdgeItem(
                source=QPersistentModelIndex(source_node_index),
                target=QPersistentModelIndex(target_node_index),
                key=inlets[0]
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
    # nodelist.setMovement(QListView.Movement.Snap)
    nodelist.setDragEnabled(True)
    nodelist.setAcceptDrops(True)
    nodelist.setDropIndicatorShown(True)
    nodelist.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove) 


    edgelist = QListView()
    edgelist.setModel(edges)
    edgelist.setSelectionModel(edge_selection)
    edgelist.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    edgelist.setDragEnabled(True)
    edgelist.setAcceptDrops(True)
    edgelist.setDropIndicatorShown(True)
    edgelist.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove) 


    # graph_view = QGraphicsView()
    graph_view = DAGEditorView()
    graph_view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
    graph_view.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
    graph_view.setWindowTitle("NXNetworkScene")
    graph_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    graph_view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    graph_view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    graph_view.setModel(nodes, edges)
    # graph_scene.setSceneRect(QRectF(-400, -400, 800, 800))
    graph_view.setSelectionModel(node_selection)
    # graph_view.setScene(graph_scene)

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

