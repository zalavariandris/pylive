#####################
# The Network Scene #
#####################

#
# A 'View' to represent a network of nodes, connected by inlets and outlets
#

# In QT ModelView terminology this is a 'View'.
# It is responsible to present (and potentially edit) the NXGraphModel
# GraphScene 'internaly' uses subclasses of GraphShapes that are also 'views'.
# these widgets are responsible to reference the graphscene,
# and the represented nodes, edge and ports.
#
# TODO: move the model editing capabilities
# from the widgets to a delegate, or the graphsene itself


from typing import *
from typing import override
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


##############
# GRAPHSCENE #
##############

from bidict import bidict
from collections import defaultdict
from pylive.QtGraphEditor.edges_model import EdgeItem, EdgesModel
from pylive.QtGraphEditor.standard_graph_delegate import StandardGraphDelegate

from pylive.utils.qt import modelReset, signalsBlocked
from pylive.utils.unique import make_unique_id

# define to NXGraphModel schema
# This is only for typecheckers and debugging
# TODO: check if this is actually messes things up later.
# class _NodeId(Hashable):...
# class _OutletName(str):...
# class _InletName(str):...
# class _EdgeId(tuple[_NodeId, _NodeId, tuple[_OutletName, _InletName]]):...


class QGraphEditorScene(QGraphicsScene):
    SourceRole = Qt.ItemDataRole.UserRole+1
    TargetRole = Qt.ItemDataRole.UserRole+2
    InletsRole = Qt.ItemDataRole.UserRole+3
    OutletsRole = Qt.ItemDataRole.UserRole+4

    def __init__(self, ):
        super().__init__()

        self._nodes: QAbstractItemModel | None = None
        self._edges: EdgesModel | None = None
        self._node_selection:QItemSelectionModel|None = None
        self._delegate: StandardGraphDelegate
        self.setDelegate(StandardGraphDelegate())

        # configure QGraphicsScene
        # self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

        # store model widget relations
        self._node_graphics_objects: bidict[QPersistentModelIndex, QGraphicsItem] = bidict()
        self._link_graphics_objects: bidict[QPersistentModelIndex, QGraphicsItem] = bidict()
        self._inlet_graphics_objects: bidict[tuple[QPersistentModelIndex, str], QGraphicsItem] = bidict()
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
        # self.setSelectionModel(selection_model)
        

    def setModel(self, nodes: QAbstractItemModel, edges:EdgesModel):
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
        self.layout()

    def model(self)->tuple[QAbstractItemModel|None, EdgesModel|None]:
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
            self._delegate.updateLinkPosition(edge_editor, source_outlet_widget, target_inlet_widget)

    def setDelegate(self, delegate:StandardGraphDelegate):
        self._delegate = delegate
        self._delegate.nodePositionChanged.connect(self._moveAttachedLinks)

    def setSelectionModel(self, node_selection:QItemSelectionModel):
        if self._node_selection:
            self._node_selection.selectionChanged.disconnect(self._onSelectionChanged)
            self.selectionChanged.disconnect(self._updateSelectionModel)

        if node_selection:
            node_selection.selectionChanged.connect(self._onSelectionChanged)
            self.selectionChanged.connect(self._updateSelectionModel)

        # set selection model
        self._node_selection = node_selection

    def _updateSelectionModel(self):
        """called when the graphicsscene selection has changed"""
        if not self._node_selection:
            return
        assert self._nodes
  
        # get selected rows
        selected_rows = []
        for item in self.selectedItems():
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
        self.layout()

    def _onEdgesReset(self):
        assert self._edges
        ### clear graph
        self._link_graphics_objects.clear()

        ### populate graph with edges
        if self._edges.rowCount()>0:
            self._onEdgesInserted(QModelIndex(), 0, self._edges.rowCount()-1)

        # layout items
        self.layout()

    def _onNodesInserted(self, parent:QModelIndex, first:int, last:int):
        assert self._nodes
        print("on nodes inserted")
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
            if node_editor := self._delegate.createNodeEditor(self, node_index):
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
            if inlet_editor := self._delegate.createInletEditor(node_editor, node_index, inlet):
                inlet_id = QPersistentModelIndex(node_index), inlet
                self._inlet_graphics_objects[inlet_id] = inlet_editor

    def _addOutlets(self, node_index:QModelIndex|QPersistentModelIndex, outlets:list[str]):
        node_editor = self._node_graphics_objects[QPersistentModelIndex(node_index)]
        for outlet in outlets:
            if outlet_editor := self._delegate.createOutletEditor(node_editor, node_index, outlet):
                outlet_id = QPersistentModelIndex(node_index), outlet
                self._outlet_graphics_objects[outlet_id] = outlet_editor

    def removeNodes(self, indexes:Iterable[QPersistentModelIndex]):
        assert self._nodes
        for node_index in indexes:
            node_editor = self._node_graphics_objects[node_index]
            self.removeItem(node_editor)

    def updateNodes(self, indexes:Iterable[QPersistentModelIndex], roles:list[int]):
        assert self._nodes
        for node_index in indexes:
            if editor := self._node_graphics_objects.get(node_index, None):
                self._delegate.updateNodeEditor(node_index, editor)

    def addEdges(self, indexes:Iterable[QPersistentModelIndex]):
        assert self._edges
        for edge_index in indexes:
            ### create edge editor
            if edge_editor := self._delegate.createEdgeEditor(edge_index):
                self._link_graphics_objects[edge_index] = edge_editor
                self.addItem( edge_editor )

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
                self._delegate.updateLinkPosition(edge_editor, source_outlet_widget, target_inlet_widget)

    def removeEdges(self, indexes:Iterable[QPersistentModelIndex]):
        assert self._edges
        for edge_index in indexes:
            source_index = self._edges.data(edge_index, self.SourceRole)
            target_index = self._edges.data(edge_index, self.TargetRole)
            source_node_editor = self._node_graphics_objects[source_index]
            target_node_editor = self._node_graphics_objects[target_index]

            edge_editor = self._link_graphics_objects[edge_index]
            self.removeItem(edge_editor)
        
    def updateEdges(self, indexes:Iterable[QPersistentModelIndex]):
        for edge_index in indexes:
            if editor := self._link_graphics_objects.get(edge_index, None):
                self._delegate.updateEdgeEditor(edge_index, editor)

    def changeNodeSelection(self, select: Iterable[QPersistentModelIndex], deselect:Iterable[QPersistentModelIndex]):
        with signalsBlocked(self):
            for node_index in select:
                editor = self._node_graphics_objects[node_index]
                editor.setSelected(True)

            for node_index in deselect:
                editor = self._node_graphics_objects[node_index]
                editor.setSelected(False)

            self.selectionChanged.emit()

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

    def nodeIndexAt(self, position: QPointF) -> QModelIndex|None:
        assert self._nodes
        rect = QRectF(position.x()-4,position.y()-4,8,8)
        for item in self.items(rect, deviceTransform=QTransform()):
            if node_id :=  self._node_graphics_objects.inverse.get(item, None):
                return self._nodes.index(node_id.row(), 0)

    def inletIndexAt(self, position: QPointF)->tuple[QModelIndex, str]|None:
        assert self._nodes
        rect = QRectF(position.x()-4,position.y()-4,8,8)
        for item in self.items(rect, deviceTransform=QTransform()):
            if node_inlet :=  self._inlet_graphics_objects.inverse.get(item, None):
                node_id, inlet = node_inlet
                return self._nodes.index(node_id.row(), 0), inlet

    def outletIndexAt(self, position: QPointF)->tuple[QModelIndex, str]|None:
        assert self._nodes
        rect = QRectF(position.x()-4,position.y()-4,8,8)
        for item in self.items(rect, deviceTransform=QTransform()):
            if node_outlet :=  self._outlet_graphics_objects.inverse.get(item, None):
                node_id, outlet = node_outlet
                return self._nodes.index(node_id.row(), 0), outlet

    def edgeIndexAt(self, position: QPointF) -> QModelIndex|None:
        assert self._edges
        rect = QRectF(position.x()-4,position.y()-4,8,8)
        for item in self.items(rect, deviceTransform=QTransform()):
            if edge_id :=  self._link_graphics_objects.inverse.get(item, None):
                return self._edges.index(edge_id.row(), 0)

    def layout(self, orientation=Qt.Orientation.Vertical, scale=100):
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
            source_node_index = self._edges.data(edge_index, QGraphEditorScene.SourceRole)
            target_node_index = self._edges.data(edge_index, QGraphEditorScene.TargetRole)
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

    def startDragOutlet(self, node_row:int):
        """ Initiate the drag operation """
        assert self._node_selection
        assert self._nodes



        mime = QMimeData()
        mime.setData('application/outlet', f"{node_row}/out".encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)

        self._draft_link = self._delegate.createEdgeEditor(QModelIndex())
        self.addItem(self._draft_link)
        
        # Execute drag
        action = drag.exec(Qt.DropAction.LinkAction)
        if action == Qt.DropAction.LinkAction:
            print("link aciton")
        self.removeItem(self._draft_link)
        self._draft_link = None

    def dragEnterEvent(self, event):
        """ Accept drag events """
        if event.mimeData().hasFormat('application/outlet'):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        assert self._nodes
        
        if event.mimeData().hasFormat('application/outlet'):
            source = event.mimeData().data('application/outlet').toStdString().split("/")
            source_row, source_outlet = int(source[0]), source[1]
            source_node_index = self._nodes.index(source_row, 0)
            source_outlet_widget = self.outletWidget(source_node_index, source_outlet)

            assert isinstance(source_row, int)
            assert source_outlet == "out"
            assert source_node_index.isValid()
            assert source_outlet_widget


            target_node_index, inlet = self.inletIndexAt(event.scenePos()) or (None, None)
            target_inlet_widget = self.inletWidget(target_node_index, inlet) if (target_node_index and inlet) else None

            if source_outlet_widget and target_inlet_widget:
                self._delegate.updateLinkPosition(self._draft_link, source_outlet_widget, target_inlet_widget)
            elif source_outlet_widget:
                self._delegate.updateLinkPosition(self._draft_link, source_outlet_widget, event.scenePos())
  


    def dropEvent(self, event):
        assert self._nodes
        if event.mimeData().hasFormat('application/outlet'):
            source = event.mimeData().data('application/outlet').toStdString().split("/")
            source_row, source_outlet = int(source[0]), source[1]
            source_node_index = self._nodes.index(source_row, 0)

            target_node_index = self.nodeIndexAt(event.scenePos())

            if source_node_index and target_node_index:
                assert self._edges
                self._edges.addEdgeItem(EdgeItem(
                    QPersistentModelIndex(source_node_index), 
                    QPersistentModelIndex(target_node_index),
                    "key"
                ))
        
    

if __name__ == "__main__":
    app = QApplication()

    ### model state
    nodes = QStandardItemModel()
    nodes.setHeaderData(0, Qt.Orientation.Horizontal, "name")
    edges = EdgesModel(nodes=nodes)
    node_selection = QItemSelectionModel(nodes)
    edge_selection = QItemSelectionModel(edges)
    
    ### actions, commands
    row = 0
    def create_new_node():
        global row
        print("create node {row}")
        row+=1
        item = QStandardItem()
        item.setData(f"node{row}", Qt.ItemDataRole.DisplayRole)
        item.setData(["in1", "in2"], QGraphEditorScene.InletsRole)
        item.setData(["out"], QGraphEditorScene.OutletsRole)
        nodes.insertRow(nodes.rowCount(), item)

    def delete_selected_nodes():
        indexes:list[QModelIndex] = node_selection.selectedRows(column=0)
        indexes.sort(key=lambda index:index.row())
        for index in reversed(indexes):
            nodes.removeRows(index.row(), 1)

    def connect_selected_nodes():
        print("connect selected nodes")

        if len(node_selection.selectedRows(0))<2:
            return

        target_node_index = node_selection.currentIndex().siblingAtColumn(0)
        assert target_node_index.isValid()
        inlets = nodes.data(target_node_index, QGraphEditorScene.InletsRole)
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

    nodes.rowsInserted.connect(lambda: print("rows inserted"))
    ### view

    nodelist = QListView()
    nodelist.setModel(nodes)
    nodelist.setSelectionModel(node_selection)
    nodelist.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)

    edgelist = QTableView()
    edgelist.setModel(edges)

    graph_view = QGraphicsView()
    graph_view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
    graph_view.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
    graph_view.setWindowTitle("NXNetworkScene")
    graph_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    graph_view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    graph_view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    graph_scene = QGraphEditorScene()
    graph_scene.setModel(nodes, edges)
    graph_scene.setSceneRect(QRectF(-400, -400, 800, 800))
    graph_scene.setSelectionModel(node_selection)
    graph_view.setScene(graph_scene)

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
    layout_action = QPushButton("layout", window)
    layout_action.pressed.connect(graph_scene.layout)

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

