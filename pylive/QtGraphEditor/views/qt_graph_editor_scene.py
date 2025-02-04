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
from pylive.QtGraphEditor.edges_model import EdgeItem, EdgesModel
from pylive.QtGraphEditor.models.abstract_graph_model import AbstractGraphModel
from pylive.QtGraphEditor.qt_graph_editor_delegate import QGraphEditorDelegate

from pylive.utils.qt import modelReset, signalsBlocked

from pylive.QtGraphEditor.models.proxy_graph_model import ProxyGraphModel

class QGraphEditorScene(QGraphicsScene):
    SourceRole = Qt.ItemDataRole.UserRole+1
    TargetRole = Qt.ItemDataRole.UserRole+2

    def __init__(self, ):
        super().__init__()

        # self._nodes: QAbstractItemModel | None = None
        # self._edges: EdgesModel | None = None
        self._graph:ProxyGraphModel|None=None
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
        self._link_loop = QEventLoop(self)

        # self._attribute_editors: bidict[tuple[QPersistentModelIndex, str], QGraphicsItem] = bidict()

        # set model
        # populate with initial model
        # self.setModel(model)
        # self.setSelectionModel(selection_model)
        
    def setModel(self, graph:ProxyGraphModel):
        # if self._nodes:
        #     # Nodes
        #     self._nodes.modelReset.disconnect(self._onNodesReset)
        #     self._nodes.rowsInserted.disconnect(self._onNodesInserted)
        #     self._nodes.rowsAboutToBeRemoved.disconnect(self._onNodesAboutToBeRemoved)
        #     self._nodes.dataChanged.disconnect(self._onNodeDataChanged)

        # if self._edges:
        #     # Nodes
        #     self._edges.modelReset.disconnect(self._onEdgesReset)
        #     self._edges.rowsInserted.disconnect(self._onEdgesInserted)
        #     self._edges.rowsAboutToBeRemoved.disconnect(self._onEdgesAboutToBeRemoved)
        #     self._edges.dataChanged.disconnect(self._onEdgeDataChanged)

        # if nodes:
        #     # Nodes
        #     nodes.modelReset.connect(self._onNodesReset)
        #     nodes.rowsInserted.connect(self._onNodesInserted)
        #     nodes.rowsAboutToBeRemoved.connect(self._onNodesAboutToBeRemoved)
        #     nodes.dataChanged.connect(self._onNodeDataChanged)

        # if edges:
        #     # Nodes
        #     edges.modelReset.connect(self._onEdgesReset)
        #     edges.rowsInserted.connect(self._onEdgesInserted)
        #     edges.rowsAboutToBeRemoved.connect(self._onEdgesAboutToBeRemoved)
        #     edges.dataChanged.connect(self._onEdgeDataChanged)

        # self._nodes = nodes
        # self._edges = edges

        if self._graph:
            graph.nodesReset.disconnect(self._onNodesReset)
            graph.nodesAdded.disconnect(self.addNodes)
            # graph.nodeDataChanged.disconnect(...)
            graph.nodesAboutToBeRemoved.disconnect(self.removeNodes)

            graph.edgesReset.disconnect(self._onEdgesReset)
            graph.edgesAdded.disconnect(self.addEdges)
            graph.edgesAboutToBeRemoved.disconnect(self.removeEdges)
            
        if graph:
            graph.nodesReset.connect(self._onNodesReset)
            graph.nodesAdded.connect(self.addNodes)
            graph.nodesAboutToBeRemoved.connect(self.removeNodes)

            graph.edgesReset.connect(self._onEdgesReset)
            graph.edgesAdded.connect(self.addEdges)
            graph.edgesAboutToBeRemoved.connect(self.removeEdges)
            # graph.nodeDataChanged.connect(self.changeN)
            
        self._graph = graph

        # populate initial scene
        self.addNodes([_ for _ in self._graph.nodes()])
        self.addEdges([_ for _ in self._graph.edges()])

        # layout items
        self.layout()

    def model(self)->ProxyGraphModel|None:
        return self._graph

    def _moveAttachedLinks(self, node_editor:QGraphicsItem):
        assert self._graph
        assert self._graph._edges
        from itertools import chain

        for edge_editor in chain(self._node_in_links[node_editor], self._node_out_links[node_editor]):
            assert edge_editor in self._link_graphics_objects.values(), f"got: {edge_editor} not in {[_ for _ in self._link_graphics_objects.values()]}"
            edge_index = self._link_graphics_objects.inverse[edge_editor]
            source_index = self._graph._edges.source(edge_index)
            target_index = self._graph._edges.target(edge_index)
            source_node = self._node_graphics_objects[source_index]
            target_node = self._node_graphics_objects[target_index]
            self._delegate.updateLinkPosition(edge_editor, source_node, target_node)

    def setDelegate(self, delegate:QGraphEditorDelegate):
        self._delegate = delegate
        self._delegate.nodePositionChanged.connect(self._moveAttachedLinks)

    # def setSelectionModel(self, node_selection:QItemSelectionModel):
    #     if self._node_selection:
    #         self._node_selection.selectionChanged.disconnect(self._onSelectionChanged)
    #         self.selectionChanged.disconnect(self._updateSelectionModel)

    #     if node_selection:
    #         node_selection.selectionChanged.connect(self._onSelectionChanged)
    #         self.selectionChanged.connect(self._updateSelectionModel)

    #     # set selection model
    #     self._node_selection = node_selection

    # def _updateSelectionModel(self):
    #     """called when the graphicsscene selection has changed"""
    #     if not self._node_selection:
    #         return
    #     assert self._graph
    #     assert self._graph._node_selection
  
    #     # get selected rows
    #     selected_rows = []
    #     for item in self.selectedItems():
    #         if index := self._node_graphics_objects.inverse.get(item, None):
    #             selected_rows.append(index.row())
    #     selected_rows.sort()

    #     # group selected rows to QItemSelectionRange
    #     from pylive.utils import group_consecutive_numbers
    #     new_selection = QItemSelection()
    #     if selected_rows:
    #         for row_range in group_consecutive_numbers(selected_rows):
    #             top_left = self._nodes.index(row_range.start, 0)
    #             bottom_right = self._nodes.index(row_range.stop-1, 0)
    #             new_selection.append(QItemSelectionRange(top_left, bottom_right))

    #     # set the selection
    #     if new_selection.count()>0:
    #         self._node_selection.setCurrentIndex(new_selection.at(0).topLeft(), QItemSelectionModel.SelectionFlag.Current)
    #     self._node_selection.select(new_selection, QItemSelectionModel.SelectionFlag.ClearAndSelect)

    ### <<< Handle Model Signals
    def _onNodesReset(self):
        assert self._graph
        assert self._graph._nodes
        ### clear graph
        self._node_graphics_objects.clear()
        self._node_in_links.clear()
        self._node_out_links.clear()

        ### populate graph with nodes
        self.addNodes([_ for _ in self._graph.nodes()])

        # layout items
        self.layout()

    def _onEdgesReset(self):
        assert self._graph
        assert self._graph._edges

        ### clear graph
        self._link_graphics_objects.clear()

        ### populate graph with edges
        self.addEdges([_ for _ in self._graph.edges()])

    # def _onNodesInserted(self, parent:QModelIndex, first:int, last:int):
    #     assert self._nodes
    #     print("on nodes inserted")
    #     indexes = [
    #         QPersistentModelIndex(self._nodes.index(row, 0)) 
    #         for row in range(first, last+1)
    #     ]

    #     self.addNodes(indexes)

    # def _onNodesAboutToBeRemoved(self, parent:QModelIndex, first:int, last:int):
    #     assert self._nodes
    #     indexes = (
    #         QPersistentModelIndex(self._nodes.index(row, 0)) 
    #         for row in range(first, last+1)
    #     )
    #     self.removeNodes(indexes)

    # def _onNodeDataChanged(self, top_left:QModelIndex, bottom_right:QModelIndex, roles:list[int]=[]):
    #     """
    #     The optional roles argument can be used to specify which data roles have actually been modified.
    #     An empty vector in the roles argument means that all roles should be considered modified"""
    #     assert self._nodes
    #     indexes = (
    #         QPersistentModelIndex(self._nodes.index(row, 0)) 
    #         for row in range(top_left.row(), bottom_right.row()+1)
    #     )
    #     self.updateNodes(indexes, roles)

    # def _onEdgesInserted(self, parent:QModelIndex, first:int, last:int):
    #     assert self._edges

    #     indexes = (
    #         QPersistentModelIndex(self._edges.index(row, 0))
    #         for row in range(first, last+1)
    #     )

    #     self.addEdges(indexes)

    # def _onEdgesAboutToBeRemoved(self, parent:QModelIndex, first:int, last:int):
    #     assert self._edges
    #     indexes = (
    #         QPersistentModelIndex(self._edges.index(row, 0))
    #         for row in range(first, last+1)
    #     )
    #     self.removeEdges(indexes)

    # def _onEdgeDataChanged(self, top_left:QModelIndex, bottom_right:QModelIndex, roles:list[int]=[]):
    #     """
    #     The optional roles argument can be used to specify which data roles have actually been modified.
    #     An empty vector in the roles argument means that all roles should be considered modified"""
    #     assert self._edges
    #     indexes = (
    #         QPersistentModelIndex(self._edges.index(row, 0))
    #         for row in range(top_left.row(), bottom_right.row()+1)
    #         )
    #     self.updateEdges(indexes)

    def addNodes(self, indexes:Iterable[QPersistentModelIndex]):
        for node_index in indexes:
            print(node_index)
            if node_editor := self._delegate.createNodeEditor(self, node_index):
                assert node_index.isValid(), "invalid persistent node?"
                self._node_graphics_objects[node_index] = node_editor

                self.addItem( node_editor )

    def removeNodes(self, indexes:Iterable[QPersistentModelIndex]):
        for node_index in indexes:
            node_editor = self._node_graphics_objects[node_index]
            self.removeItem(node_editor)

    def updateNodes(self, indexes:Iterable[QPersistentModelIndex], roles:list[int]):
        for node_index in indexes:
            if editor := self._node_graphics_objects.get(node_index, None):
                self._delegate.updateNodeEditor(node_index, editor)

    def addEdges(self, indexes:Iterable[QPersistentModelIndex]):
        assert self._graph
        assert self._graph._edges
        for edge_index in indexes:
            ### create edge editor
            if edge_editor := self._delegate.createEdgeEditor(edge_index):
                self._link_graphics_objects[edge_index] = edge_editor
                self.addItem( edge_editor )

                #UPDATE LINKS POSITION
                source_node_index:QPersistentModelIndex = self._graph._edges.source(edge_index)
                target_node_index:QPersistentModelIndex = self._graph._edges.target(edge_index)
                source_node_editor = self._node_graphics_objects[source_node_index]
                target_node_editor = self._node_graphics_objects[target_node_index]

                self._node_out_links[source_node_editor].append(edge_editor)
                self._node_in_links[target_node_editor].append(edge_editor)
                self._delegate.updateLinkPosition(edge_editor, source_node_editor, target_node_editor)

    def removeEdges(self, indexes:Iterable[QPersistentModelIndex]):
        assert self._graph
        assert self._graph._edges
        for edge_index in indexes:
            source_index = self._graph._edges.source(edge_index)
            target_index = self._graph._edges.target(edge_index)
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
    def nodeWidget(self, node_index: QModelIndex) -> BaseNodeItem|None:
        assert self._nodes
        # if node_id not in [_ for _ in self._nodes.nodes()]:
        #     raise KeyError(f"model has no node: {node_id}")
        if editor:=self._node_graphics_objects.get(QPersistentModelIndex(node_index)):
            return editor

    def linkWidget(self, edge_index:QModelIndex) -> BaseLinkItem|None:
        assert self._edges
        if not edge_index.isValid():
            raise KeyError()

        if editor:=self._link_graphics_objects.get(edge_index):
            return cast(BaseLinkItem, editor)

    def nodeIndexAt(self, position: QPointF) -> QModelIndex:
        assert self._nodes
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                node_id:QPersistentModelIndex =  self._node_graphics_objects.inverse[item]
                return self._nodes.index(node_id.row(), 0)
            except KeyError:
                continue
        return self._nodes.index(-1, 0)

    def edgeIndexAt(self, position: QPointF) -> QModelIndex:
        assert self._edges
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                edge_id:QPersistentModelIndex =  self._link_graphics_objects.inverse[item]
                return self._edges.index(edge_id.row(), 0)
            except KeyError:
                continue
        return self._edges.index(-1, 0)

    def layout(self):
        assert self._graph
        assert self._graph._edges
        from pylive.utils.graph import hiearchical_layout_with_nx
        import networkx as nx
        G = nx.MultiDiGraph()
        for node_index in self._graph.nodes():
            G.add_node(node_index)

        for row in range(self._graph._edges.rowCount()):
            edge_index = self._graph._edges.index(row, 0)
            source_node_index = self._graph._edges.source(edge_index)
            target_node_index = self._graph._edges.target(edge_index)
            G.add_edge(source_node_index, target_node_index)
        pos = hiearchical_layout_with_nx(G, scale=200)
        for N, (x, y) in pos.items():
            widget = self._node_graphics_objects[N]
            widget.setPos(y, x)

    """DRAG AND DROP"""
    # def eventFilter(self, watched: QObject, event: QEvent) -> bool:
    #     match event.type():
    #         case QEvent.Type.GraphicsSceneMouseMove:
    #             event = cast(QGraphicsSceneMouseEvent, event)
    #             self._delegate.updateLinkPosition(self._draft, QPointF(0,0), event.scenePos())
    #             return True
    #         case QEvent.Type.GraphicsSceneMouseRelease:
    #             self._link_loop.exit()
    #             return True
    #         case _:
    #             pass
    #     return super().eventFilter(watched, event)

    def startDrag(self, supportedActions=[]):
        """ Initiate the drag operation """
        assert self._node_selection
        assert self._nodes
        index = self._node_selection.currentIndex()
        if not index.isValid():
            return

        mimeData = self._nodes.mimeData([index])
        drag = QDrag(self)
        drag.setMimeData(mimeData)

        self._draft_link = self._delegate.createEdgeEditor(QModelIndex())
        self.addItem(self._draft_link)
        
        # Execute drag
        if drag.exec(Qt.DropAction.LinkAction) == Qt.DropAction.LinkAction:
            print("drop")
            # self.model().removeRow(index.row())  # Remove item after move

    def dragEnterEvent(self, event):
        """ Accept drag events """
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        assert self._nodes
        target_index = self.nodeIndexAt(event.scenePos())

        def source_row_from_mime(mimeData)->int:
            mimeData = event.mimeData()
            if mimeData.hasFormat("application/node_row"):
                data = mimeData.data("application/node_row")  # Get QByteArray
                text = bytes(data).decode("utf-8").strip(",")  # Convert to string and remove trailing comma
                rows = [int(row) for row in text.split(",") if row]  # Convert back to integers
                return rows[0]
            return -1

        source_row = source_row_from_mime(event.mimeData())
        source_index = self._nodes.index(source_row, 0)
        source_widget=self.nodeWidget(source_index)

        target_widget = self.nodeWidget(target_index)

        if source_widget and target_widget:
            self._delegate.updateLinkPosition(self._draft_link, source_widget, target_widget)
            event.acceptProposedAction()
            return
        elif source_widget:
            print("no item")
            self._delegate.updateLinkPosition(self._draft_link, source_widget, event.scenePos())

    def dropEvent(self, event):
        node_index = self.nodeIndexAt(event.scenePos())
        if node_index.isValid():
            if target_graphics_object := self.nodeWidget(node_index):
                self._delegate.updateLinkPosition(self._draft_link, QPointF(), target_graphics_object)
                event.acceptProposedAction()
                return
        print("no item")
        self._delegate.updateLinkPosition(self._draft_link, QPointF(), event.scenePos())
        

if __name__ == "__main__":
    app = QApplication()

    ### model state

    nodes = QStandardItemModel()
    nodes.setHeaderData(0, Qt.Orientation.Horizontal, "name")
    edges = EdgesModel(nodes=nodes)
    node_selection = QItemSelectionModel(nodes)
    edge_selection = QItemSelectionModel(edges)
    proxy_graph = ProxyGraphModel()
    proxy_graph.setSourceModel(nodes, edges)

    proxy_graph.nodesAdded.connect(lambda _:print("nodesAdded", _))
    proxy_graph.nodesAboutToBeRemoved.connect(lambda _:print("nodesAboutToBeRemoved", _))
    proxy_graph.nodesRemoved.connect(lambda _:print("nodesRemoved", _))

    proxy_graph.edgesAdded.connect(lambda _:print("edgesAdded", _))
    proxy_graph.edgesAboutToBeRemoved.connect(lambda _:print("edgesAboutToBeRemoved", _))
    proxy_graph.edgesRemoved.connect(lambda _:print("edgesRemoved", _))
    
    ### actions, commands
    row = 0
    def create_new_node():
        global row
        print("create node {row}")
        row+=1
        item = QStandardItem()
        item.setData(f"node{row}", Qt.ItemDataRole.DisplayRole)
        nodes.insertRow(nodes.rowCount(), item)

    def delete_selected_nodes():
        indexes:list[QModelIndex] = node_selection.selectedRows(column=0)
        for index in sorted(indexes, key=lambda row:index.row(), reverse=True):
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
            edges.addEdgeItem(EdgeItem(
                source=QPersistentModelIndex(source_node),
                target=QPersistentModelIndex(target_node),
                key="edge"
            ))

    def delete_selected_edges():
        indexes:list[QModelIndex] = edge_selection.selectedRows(column=0)
        for index in sorted(indexes, key=lambda index:index.row(), reverse=True):
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
    graph_scene.setModel(proxy_graph)
    graph_scene.setSceneRect(QRectF(-400, -400, 800, 800))
    # graph_scene.setSelectionModel(node_selection)
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