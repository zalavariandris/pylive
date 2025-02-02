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
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.NetworkXGraphEditor.nx_graph_shapes import (
    BaseNodeItem,
    BaseLinkItem,
)

##############
# GRAPHSCENE #
##############

from bidict import bidict
from collections import defaultdict
from pylive.QtGraphEditor.edges_model import EdgesModel
from pylive.QtGraphEditor.qt_graph_editor_delegate import QGraphEditorDelegate

from pylive.utils.qt import signalsBlocked

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

    def __init__(self, ):
        super().__init__()

        self._nodes: QStandardItemModel | None = None
        self._edges: EdgesModel | None = None
        self._node_selection:QItemSelectionModel|None = None
        self._delegate: QGraphEditorDelegate
        self.setDelegate(QGraphEditorDelegate())

        # configure QGraphicsScene
        # self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

        # store model widget relations
        self._node_graphics_objects: bidict[QPersistentModelIndex, QGraphicsItem] = bidict()
        self._link_graphics_objects: bidict[QPersistentModelIndex, QGraphicsItem] = bidict()
        self._node_in_links:defaultdict[QGraphicsItem, list[QGraphicsItem]] = defaultdict(list) # Notes: store attached links, because the underlzing model has to find the relevant edges  and thats is O(n)
        self._node_out_links:defaultdict[QGraphicsItem, list[QGraphicsItem]] = defaultdict(list) # Notes: store attached links, because the underlzing model has to find the relevant edges  and thats is O(n)
        # self._outlet_graphics_objects: bidict[tuple[QPersistentModelIndex, str], QGraphicsItem] = bidict()
        # self._inlet_graphics_objects: bidict[tuple[QPersistentModelIndex, str], QGraphicsItem] = bidict()
        
        self._draft_link: BaseLinkItem | None = None

        # self._attribute_editors: bidict[tuple[QPersistentModelIndex, str], QGraphicsItem] = bidict()

        # set model
        # populate with initial model
        # self.setModel(model)
        # self.setSelectionModel(selection_model)
            
        @self.selectionChanged.connect
        def _():
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

    def model(self)->tuple[QStandardItemModel|None, EdgesModel|None]:
        return self._nodes, self._edges

    def _moveAttachedLinks(self, node_editor:QGraphicsItem):
        assert self._edges
        from itertools import chain

        for edge_editor in chain(self._node_in_links[node_editor], self._node_out_links[node_editor]):
            assert edge_editor in self._link_graphics_objects.values(), f"got: {edge_editor} not in {[_ for _ in self._link_graphics_objects.values()]}"
            edge_index = self._link_graphics_objects.inverse[edge_editor]
            source_index = self._edges.source(edge_index)
            target_index = self._edges.target(edge_index)
            source_node = self._node_graphics_objects[source_index]
            target_node = self._node_graphics_objects[target_index]
            self._delegate.updateLinkPosition(edge_editor, source_node, target_node)

    def setDelegate(self, delegate:QGraphEditorDelegate):
        self._delegate = delegate
        self._delegate.nodePositionChanged.connect(self._moveAttachedLinks)

    def setSelectionModel(self, node_selection:QItemSelectionModel):
        if self._node_selection:
            self._node_selection.selectionChanged.disconnect(self._onSelectionChanged)

        if node_selection:
            node_selection.selectionChanged.connect(self._onSelectionChanged)

        # set selection model
        self._node_selection = node_selection

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

        for row in range(first, last+1):
            ### create node editor
            node_idx = self._nodes.index(row, 0)
            if node_editor := self._delegate.createNodeEditor(node_idx):
                persistent_node = QPersistentModelIndex(node_idx)
                assert persistent_node.isValid(), "invalid persistent node?"
                self._node_graphics_objects[persistent_node] = node_editor
                self.addItem( node_editor )

    def _onNodesAboutToBeRemoved(self, parent:QModelIndex, first:int, last:int):
        assert self._nodes
        for row in range(first, last+1):
            persistent_idx = QPersistentModelIndex(self._nodes.index(row, 0))
            node_editor = self._node_graphics_objects[persistent_idx]
            self.removeItem(node_editor)

    def _onNodeDataChanged(self, top_left:QModelIndex, bottom_right:QModelIndex, roles:list[int]=[]):
        """
        The optional roles argument can be used to specify which data roles have actually been modified.
        An empty vector in the roles argument means that all roles should be considered modified"""
        assert self._nodes
        for row in range(top_left.row(), bottom_right.row()+1):
            persistent = QPersistentModelIndex(self._nodes.index(row, 0))
            editor = self._node_graphics_objects[persistent]
            self._delegate.updateNodeEditor(persistent, editor)

    def _onEdgesInserted(self, parent:QModelIndex, first:int, last:int):
        assert self._edges

        for row in range(first, last+1):
            ### create edge editor
            edge_index = self._edges.index(row, 0)
            if edge_editor := self._delegate.createEdgeEditor(edge_index):
                persistent_edge_index = QPersistentModelIndex(edge_index)
                self._link_graphics_objects[persistent_edge_index] = edge_editor
                self.addItem( edge_editor )

                #UPDATE LINKS POSITION
                source_node_index:QPersistentModelIndex = self._edges.source(persistent_edge_index)
                target_node_index:QPersistentModelIndex = self._edges.target(persistent_edge_index)
                source_node_editor = self._node_graphics_objects[source_node_index]
                target_node_editor = self._node_graphics_objects[target_node_index]

                self._node_out_links[source_node_editor].append(edge_editor)
                self._node_in_links[target_node_editor].append(edge_editor)
                self._delegate.updateLinkPosition(edge_editor, source_node_editor, target_node_editor)

    def _onEdgesAboutToBeRemoved(self, parent:QModelIndex, first:int, last:int):
        assert self._edges
        for row in range(first, last+1):
            persistent_idx = QPersistentModelIndex(self._edges.index(row, 0))

            source_index = self._edges.data(persistent_idx, self.SourceRole)
            target_index = self._edges.data(persistent_idx, self.TargetRole)
            source_node_editor = self._node_graphics_objects[source_index]
            target_node_editor = self._node_graphics_objects[target_index]

            edge_editor = self._link_graphics_objects[persistent_idx]
            self.removeItem(edge_editor)

    def _onEdgeDataChanged(self, top_left:QModelIndex, bottom_right:QModelIndex, roles:list[int]=[]):
        """
        The optional roles argument can be used to specify which data roles have actually been modified.
        An empty vector in the roles argument means that all roles should be considered modified"""
        assert self._edges
        for row in range(top_left.row(), bottom_right.row()+1):
            persistent = QPersistentModelIndex(self._edges.index(row, 0))
            editor = self._link_graphics_objects[persistent]
            self._delegate.updateEdgeEditor(persistent, editor)

    def _onSelectionChanged(self, selected: QItemSelection, deselected: QItemSelection):
        """on selection model changed"""
        if selected.count()>0 or deselected.count()>0:
            with signalsBlocked(self):
                for index in selected.indexes():
                    persistent = QPersistentModelIndex(index)
                    editor = self._node_graphics_objects[persistent]
                    editor.setSelected(True)

                for index in deselected.indexes():
                    persistent = QPersistentModelIndex(index)
                    editor = self._node_graphics_objects[persistent]
                    editor.setSelected(False)

                self.selectionChanged.emit()

    ### <<< Handle Model Signals

    ### <<< Map the interactive graphics ids to widgets
    def nodeGraphicsObject(self, node_idx: QModelIndex) -> BaseNodeItem|None:
        assert self._nodes
        # if node_id not in [_ for _ in self._nodes.nodes()]:
        #     raise KeyError(f"model has no node: {node_id}")
        if editor:=self._node_graphics_objects.get(QPersistentModelIndex(node_idx)):
            return editor

    def linkGraphicsObject(self, edge_idx:QModelIndex) -> BaseLinkItem|None:
        assert self._edges
        if not edge_idx.isValid():
            raise KeyError()

        if editor:=self._link_graphics_objects.get(edge_idx):
            return cast(BaseLinkItem, editor)

    def edgeSourceGraphicsObject(self, edge_idx):
        ...

    def edgeTargetGraphicsObject(self, edge_idx):
        ...

    def inEdgeGraphicsObjects(self, node_idx):
        ...

    def outEdgeGraphicsobject(self, node_idx):
        ...

    def nodeAt(self, position: QPointF) -> QPersistentModelIndex | None:
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                node_id =  self._node_graphics_objects.inverse[item]
                return node_id
            except KeyError:
                continue
        return

    def edgeAt(self, position: QPointF) -> QPersistentModelIndex | None:
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                edge_id =  self._link_graphics_objects.inverse[item]
                return edge_id
            except KeyError:
                continue
        return

    def layout(self):
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
            source_node_index = self._edges.source(edge_index)
            target_node_index = self._edges.target(edge_index)
            G.add_edge(source_node_index, target_node_index)
        pos = hiearchical_layout_with_nx(G, scale=200)
        for N, (x, y) in pos.items():
            widget = self._node_graphics_objects[N]
            widget.setPos(y, x)

    # @override
    # def sendEvent(self, item:QGraphicsItem, event:QEvent)->bool:
    #     print("send event")
    #     return super().sendEvent(item, event)

    # def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
    #     if outlet_id:=self.outletAt(event.scenePos()):
    #         node_id, outlet_key = outlet_id
    #         self.tool = NXNetworkLinkTool(self)
    #         self.tool.startFromOutlet(node_id, outlet_key)
    #     elif inlet_id:=self.inletAt(event.scenePos()):
    #         node_id, inlet_key = inlet_id
    #         self.tool = NXNetworkLinkTool(self)
    #         self.tool.startFromInlet(node_id, inlet_key)
    #     elif node_id:=self.nodeAt(event.scenePos()):
    #         super().mousePressEvent(event)
    #     elif edge_id:=self.edgeAt(event.scenePos()):
    #         super().mousePressEvent(event)


if __name__ == "__main__":
    app = QApplication()

    ### model state

    nodes = QStandardItemModel()
    nodes.setHeaderData(0, Qt.Orientation.Horizontal, "name")
    edges = QStandardItemModel()
    edges.setHeaderData(0, Qt.Orientation.Horizontal, "key")
    node_selection = QItemSelectionModel(nodes)
    edge_selection = QItemSelectionModel(edges)
    
    ### actions, commands
    idx = 0
    def create_new_node():
        global idx
        print("create node {idx}")
        idx+=1
        item = QStandardItem()
        item.setData(f"node{idx}", Qt.ItemDataRole.DisplayRole)
        nodes.insertRow(nodes.rowCount(), item)

    def delete_selected_nodes():
        indexes:list[QModelIndex] = node_selection.selectedRows(column=0)
        for index in sorted(indexes, key=lambda idx:idx.row(), reverse=True):
            nodes.removeRows(index.row(), 1)

    def connect_selected_nodes():
        print("connect selected nodes")

        if len(node_selection.selectedRows(0))<2:
            return

        target_node = node_selection.currentIndex().siblingAtColumn(0)
        assert target_node.isValid()
        for source_node in node_selection.selectedRows(0):
            if target_node == source_node:
                continue

            assert source_node.isValid()

            item = QStandardItem()
            item.setData(QPersistentModelIndex(source_node), QGraphEditorScene.SourceRole)
            item.setData(QPersistentModelIndex(target_node), QGraphEditorScene.TargetRole)
            item.setData("in", Qt.ItemDataRole.DisplayRole)
            edges.insertRow(edges.rowCount(), item)

    def delete_selected_edges():
        indexes:list[QModelIndex] = edge_selection.selectedRows(column=0)
        for index in sorted(indexes, key=lambda idx:idx.row(), reverse=True):
            edges.removeRows(index.row(), 1)

    nodes.rowsInserted.connect(lambda: print("rows inserted"))
    ### view

    window = QWidget()

    nodelist = QListView()
    nodelist.setModel(nodes)
    nodelist.setSelectionModel(node_selection)
    nodelist.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)

    edgelist = QListView()
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

    add_node_action = QAction("add new node", window)
    add_node_action.triggered.connect(create_new_node)
    delete_node_action = QAction("delete node", window)
    delete_node_action.triggered.connect(delete_selected_nodes)
    connect_selected_nodes_action = QAction("connect selected nodes", window)
    connect_selected_nodes_action.triggered.connect(connect_selected_nodes)
    remove_edge_action = QAction("remove edge", window)
    remove_edge_action.triggered.connect(delete_selected_edges)
    layout_action = QAction("layout", window)
    layout_action.triggered.connect(graph_scene.layout)

    menubar = QMenuBar()
    menubar.addAction(add_node_action)
    menubar.addAction(delete_node_action)
    menubar.addAction(connect_selected_nodes_action)
    menubar.addAction(remove_edge_action)
    menubar.addAction(layout_action)

    grid_layout = QGridLayout()
    grid_layout.setMenuBar(menubar)
    grid_layout.addWidget(nodelist, 1, 0)
    grid_layout.addWidget(edgelist, 1, 1)
    grid_layout.addWidget(graph_view, 0, 0, 1, 3)

    window.setLayout(grid_layout)
    window.show()

    app.exec()