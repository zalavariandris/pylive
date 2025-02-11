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

from pylive.VisualCode_NetworkX.UI.nx_graph_shapes import (
    BaseNodeItem,
    BaseLinkItem
)


##############
# GRAPHSCENE #
##############

from bidict import bidict
from pylive.VisualCode_NetworkX.UI.nx_network_model import NXNetworkModel
from pylive.VisualCode_NetworkX.UI.nx_graph_selection_model import NXGraphSelectionModel
from pylive.VisualCode_NetworkX.UI.nx_network_scene_delegate import NXNetworkSceneDelegate


from pylive.utils.qt import distribute_items_horizontal


# define to NXGraphModel schema
# This is only for typecheckers and debugging
# TODO: check if this is actually messes things up later.
class _NodeId(Hashable):...
class _OutletName(str):...
class _InletName(str):...
class _EdgeId(tuple[_NodeId, _NodeId, tuple[_OutletName, _InletName]]):...


class NXNetworkView(QGraphicsItem):
    def __init__(self, model: NXNetworkModel, delegate=NXNetworkSceneDelegate()):
        super().__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self._model: NXNetworkModel | None = None

        self.delegate = delegate

        # configure QGraphicsScene
        # self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

        # store model widget relations
        self._node_graphics_objects: bidict[_NodeId, QGraphicsItem] = bidict()
        self._outlet_graphics_objects: bidict[tuple[_NodeId, _OutletName], QGraphicsItem] = bidict()
        self._inlet_graphics_objects: bidict[tuple[_NodeId, _InletName], QGraphicsItem] = bidict()
        self._link_graphics_objects: bidict[_EdgeId, QGraphicsItem] = bidict()
        self._attribute_editors: bidict[tuple[_NodeId, str], QGraphicsItem] = bidict()



        # set model
        # populate with initial model
        
        self.setModel(model)

    def boundingRect(self) -> QRectF:
        return QRectF(0,0,100,100)

    def paint(self, painter:QPainter, option, widget=None):
        painter.drawRect(self.boundingRect())


    def setModel(self, model: NXNetworkModel):
        if self._model:
            # Nodes
            self._model.nodesAdded.disconnect(self.onNodesAdded)
            self._model.nodesAboutToBeRemoved.disconnect(self.onNodesRemoved)

            # Edges
            self._model.edgesAdded.disconnect(self.onEdgesAdded)
            self._model.edgesAboutToBeRemoved.disconnect(self.onEdgesRemoved)

            # Node Attributes
            self._model.nodeAttributesAdded.disconnect(self.onNodeAttributesAdded)
            self._model.nodeAttributesAboutToBeRemoved.disconnect(self.onNodeAttributesRemoved)
            self._model.nodeAttributesChanged.disconnect(self.onNodeAttributesChanged)

            # Edge Attributes
            self._model.edgeAttributesAdded.disconnect(self.onEdgeAttributesAdded)
            self._model.edgeAttributesAboutToBeRemoved.disconnect(self.onEdgeAttributesRemoved)
            self._model.edgeAttributesChanged.disconnect(self.onEdgeAttributesChanged)

        if model:
            # Nodes
            model.nodesAdded.connect(self.onNodesAdded)
            model.nodesAboutToBeRemoved.connect(self.onNodesRemoved)
            
            # Edges
            model.edgesAdded.connect(self.onEdgesAdded)
            model.edgesAboutToBeRemoved.connect(self.onEdgesRemoved)

            # Node Attributes
            model.nodeAttributesAdded.connect(self.onNodeAttributesAdded)
            model.nodeAttributesAboutToBeRemoved.connect(self.onNodeAttributesRemoved)
            model.nodeAttributesChanged.connect(self.onNodeAttributesChanged)

            # Edge Attributes
            model.edgeAttributesAdded.connect(self.onEdgeAttributesAdded)
            model.edgeAttributesAboutToBeRemoved.connect(self.onEdgeAttributesRemoved)
            model.edgeAttributesChanged.connect(self.onEdgeAttributesChanged)
        
        self._model = model
        if self._model:
            ### populate graph
            self.onNodesAdded(self._model.nodes())
            edges:list[tuple[_NodeId, _NodeId, tuple[str, str]]] = [e for e in self._model.edges()]
            self.onEdgesAdded( edges )

            # layout items
            self.layout()

    def model(self):
        return self._model

    ### <<< Map the interactive graphics ids to widgets
    def nodeGraphicsObject(self, node_id: _NodeId) -> BaseNodeItem|None:
        assert self._model
        if node_id not in [_ for _ in self._model.nodes()]:
            raise KeyError(f"model has no node: {node_id}")
        if editor:=self._node_graphics_objects.get(node_id):
            return editor

    def outletGraphicsObject(self, node_id:_NodeId, key:_OutletName) -> QGraphicsItem|None:
        assert isinstance(key, str)
        assert self._model
        if node_id not in [_ for _ in self._model.nodes()]:
            raise KeyError(f"model has no node: {node_id}")
        if editor:=self._outlet_graphics_objects.get((node_id, key), None):
            return editor

    def inletGraphicsObject(self, node_id:_NodeId, key: _InletName) -> QGraphicsItem|None:
        assert isinstance(key, str)
        assert self._model
        if node_id not in [_ for _ in self._model.nodes()]:
            raise KeyError(f"model has no node: {node_id}")
        if editor:=self._inlet_graphics_objects.get((node_id, key), None):
            return editor

    def linkGraphicsObject(self, u:_NodeId, v:_NodeId, k:tuple[_OutletName, _InletName]) -> BaseLinkItem|None:
        edge_id = u, v, k
        assert self._model
        if edge_id not in [_ for _ in self._model.edges()]:
            raise KeyError(f"model has no edge: {edge_id}")

        if editor:=self._link_graphics_objects.get(edge_id):
            return cast(BaseLinkItem, editor)

    def attributeEditor(self, node_id:_NodeId, attr:str)->QGraphicsItem|None:
        assert isinstance(attr, str)
        assert self._model
        if node_id not in [_ for _ in self._model.nodes()]:
            raise KeyError(f"model has no node: {node_id}")
        if attr not in [_ for _ in self._model.nodeAttributes(node_id)]:
            raise KeyError(f"node {node_id} has no attribute: {attr}")

        if editor:=self._attribute_editors.get((node_id, attr), None):
            return editor

    def moveAttachedLinks(self, node_id:_NodeId):
        from itertools import chain
        model = self.model()
        assert model
        for e in chain(model.inEdges(node_id), model.outEdges(node_id)):
            u, v, (o, i) = e
            source_node = self.nodeGraphicsObject(u)
            outlet = self.outletGraphicsObject(u, o)
            target_node = self.nodeGraphicsObject(v)
            inlet = self.inletGraphicsObject(v, i)
            link = self.linkGraphicsObject(u, v, (o, i))
            link.move(outlet, inlet)

    ### <<< Handle Model Signals
    def onNodesAdded(self, nodes: list[_NodeId]):
        assert self._model
        for node_id in nodes:
            ### create node editor
            node_editor = self.delegate.createNodeEditor(self._model, node_id)
            node_editor.scenePositionChanged.connect(lambda node_id=node_id: self.moveAttachedLinks(node_id))
            self._node_graphics_objects[node_id] = node_editor

            self.nodeGraphicsObject(node_id).setParentItem(self)
            attributes = [_ for _ in self._model.nodeAttributes(node_id)]
            

            ### create attribute editors
            for attr in attributes:
                editor = self.delegate.createAttributeEditor(node_editor, self._model, node_id, attr)
                if editor:
                    self._attribute_editors[(node_id, attr)] = editor
                    self.delegate.updateAttributeEditor(self._model, node_id, attr, editor)

            ### create inlets
            inlets = []
            for inlet_name in self._model.inlets(node_id):
                node_editor = cast(BaseNodeItem, self.nodeGraphicsObject(node_id))
                inlet = self.delegate.createInletEditor(node_editor, node_id, inlet_name)
                self._inlet_graphics_objects[(node_id, inlet_name)] = inlet
                inlets.append(inlet)
            # position inlet
            for inlet in inlets:
                inlet.setY(node_editor.boundingRect().top()-3)
            distribute_items_horizontal(inlets, node_editor.boundingRect())

            ### create outlets
            outlets = []
            for outlet_name in self._model.outlets(node_id):
                node_editor = cast(BaseNodeItem, self.nodeGraphicsObject(node_id))
                outlet = self.delegate.createOutletEditor(node_editor, node_id, outlet_name)
                self._outlet_graphics_objects[(node_id, outlet_name)] = outlet
                outlets.append(outlet)
            # position outlets
            for outlet in outlets:
                outlet.setY(node_editor.boundingRect().bottom()+3)
            distribute_items_horizontal(outlets, node_editor.boundingRect())

            self.delegate.updateNodeEditor(self._model, node_id, node_editor, attributes)

    def onNodesRemoved(self, nodes: list[_NodeId]):
        for n in nodes:
            if n in self._node_graphics_objects:
                node_graphics_object = self.nodeGraphicsObject(n)
                raise NotImplementedError()

    def onEdgesAdded(self, edges: Iterable[tuple[_NodeId, _NodeId, tuple[str, str]]]):
        for e in edges:
            u, v, (o, i) = e
            link = self.delegate.createLinkEditor(self._model, u, v, (o, i))

            self._link_graphics_objects[e] = link
            link.setParentItem(self)

            u, v, (o, i) = e
            link.move(
                self.outletGraphicsObject(u, o),
                self.inletGraphicsObject(v, i)
            )

    def onEdgesRemoved(self, edges: Iterable[tuple[_NodeId, _NodeId, tuple[str, str]]]):
        for e in edges:
            u, v, (o, i) = e
            self.removeItem(self.linkGraphicsObject(u, v, (o, i)))
            if e in self._link_graphics_objects:
                del self._link_graphics_objects[e]

    def onNodeAttributesAdded(self, node_attributes:dict[_NodeId, list[str]]):
        assert self._model
        for node_id, attributes in node_attributes.items():
            if node_editor := self.nodeGraphicsObject(node_id):
                for attr in attributes:
                    if attr_editor := self.delegate.createAttributeEditor(node_editor, self._model, node_id, attr):
                        self._attribute_editors[(node_id, attr)] = attr_editor
                        

                self.delegate.updateNodeEditor(self._model, node_id, node_editor, attributes)
                for attr in attributes:
                    if attr_editor:=self.attributeEditor(node_id, attr):
                        self.delegate.updateAttributeEditor(self._model, node_id, attr, attr_editor)


    def onNodeAttributesRemoved(self, node_attributes:dict[_NodeId, list[str]]):
        assert self._model
        for node_id, attributes in node_attributes.items():
            if node_editor := self.nodeGraphicsObject(node_id):
                for attr in attributes:
                    if attr_editor := self._attribute_editors.get((node_id, attr)):
                        del self._attribute_editors[(node_id, attr)]
                        scene = attr_editor.scene()
                        scene.removeItem(attr_editor)

                self.delegate.updateNodeEditor(self._model, node_id, node_editor, attributes)

    def onNodeAttributesChanged(self, node_attributes:dict[_NodeId, list[str]]):
        assert self._model
        for node_id, attributes in node_attributes.items():
            if node_editor := self.nodeGraphicsObject(node_id):
                for attr in attributes:
                    if attr_editor := self.attributeEditor(node_id, attr):
                        self.delegate.updateAttributeEditor(self._model, node_id, attr, attr_editor)
                self.delegate.updateNodeEditor(self._model, node_id, node_editor, attributes)

    def onEdgeAttributesAdded(self, edge_attributes:dict[_EdgeId, list[str]]):
        assert self._model
        for edge_id, attributes in edge_attributes.items():
            u, v, k = edge_id
            edge_editor = self.linkGraphicsObject(u, v, k)
            for attr in attributes:
                ...

    def onEdgeAttributesRemoved(self, edge_attributes:dict[_EdgeId, list[str]]):
        assert self._model
        for edge_id, attributes in edge_attributes.items():
            u, v, k = edge_id
            edge_editor = self.linkGraphicsObject(u, v, k)
            for attr in attributes:
                ...

    def onEdgeAttributesChanged(self, edge_attributes:dict[_EdgeId, list[str]]):
        assert self._model
        for edge_id, attributes in edge_attributes.items():
            u, v, k = edge_id
            edge_editor = self.linkGraphicsObject(u, v, k)
            for attr in attributes:
                ...

    def onModelReset(self):
        assert self._model
        ### clear graph
        self._node_graphics_objects.clear()
        self._inlet_graphics_objects.clear()
        self._link_graphics_objects.clear()
        self._node_graphics_objects.clear()
        self.clear()

        ### populate graph
        self.onNodesAdded(self._model.nodes())
        self.onEdgesAdded(self._model.edges())

        # layout items
        self.layout()

    ### <<< Handle Model Signals

    def layout(self):
        assert self._model
        from pylive.utils.graph import hiearchical_layout_with_nx
        pos = hiearchical_layout_with_nx(self._model.G, scale=200)
        for N, (x, y) in pos.items():
            widget = self.nodeGraphicsObject(N)
            widget.setPos(x, y)

    ### Handle Events
    # def nodeAt(self, position: QPointF) -> _NodeId | None:
    #     for item in self.items(position, deviceTransform=QTransform()):
    #         try:
    #             node_id =  self._node_graphics_objects.inverse[item]
    #             return node_id
    #         except KeyError:
    #             continue
    #     return

    # def edgeAt(self, position: QPointF) -> tuple[_NodeId, _NodeId, tuple[str, str]] | None:
    #     for item in self.items(position, deviceTransform=QTransform()):
    #         try:
    #             edge_id =  self._link_graphics_objects.inverse[item]
    #             return edge_id
    #         except KeyError:
    #             continue
    #     return

    # def inletAt(self, position: QPointF) -> tuple[_NodeId, str] | None:
    #     for item in self.items(position, deviceTransform=QTransform()):
    #         try:
    #             inlet_id = self._inlet_graphics_objects.inverse[item]
    #             return inlet_id
    #         except KeyError:
    #             continue

    # def outletAt(self, position: QPointF) -> tuple[_NodeId, str] | None:
    #     for item in self.items(position, deviceTransform=QTransform()):
    #         try:
    #             outlet_id = self._outlet_graphics_objects.inverse[item]
    #             return outlet_id
    #         except KeyError:
    #             continue

    

    # @override
    # def sendEvent(self, item:QGraphicsItem, event:QEvent)->bool:
    #     print("send event")
    #     return super().sendEvent(item, event)

    # def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
    #     if outlet_id:=self.outletAt(event.scenePos()):
    #         node_id, outlet_key = outlet_id
    #         self.tool = GraphLinkTool(self)
    #         self.tool.startFromOutlet(node_id, outlet_key)
    #     elif inlet_id:=self.inletAt(event.scenePos()):
    #         node_id, inlet_key = inlet_id
    #         self.tool = GraphLinkTool(self)
    #         self.tool.startFromInlet(node_id, inlet_key)
    #     elif node_id:=self.nodeAt(event.scenePos()):
    #         super().mousePressEvent(event)
    #     elif edge_id:=self.edgeAt(event.scenePos()):
    #         super().mousePressEvent(event)




###########
# EXAMPLE #
###########
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # setup main window
    view = QGraphicsView()
    view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
    view.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
    view.setWindowTitle("NXNetworkScene")
    view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    # create graph scene
    graph = NXNetworkModel()
    graph.addNode("N1", inlets=["in"], outlets=["out"])
    graph.addNode("N2", inlets=["in"], outlets=["out"])
    graph.addNode("N3", inlets=["in"], outlets=["out"])
    graph.addEdge("N1", "N2", ("out", "in"))
    selection = NXGraphSelectionModel(graph)


    scene = QGraphicsScene()
    graph_view_item = NXNetworkView(graph)
    scene.addItem(graph_view_item)
    scene.setSceneRect(QRectF(-400, -400, 800, 800))
    view.setScene(scene)

    # from pylive.utils.graph import dependencies, dependents
    # import networkx as nx
    # def on_selection_changed(selected, deselected):
    #     for n in graph.nodes():
    #         graph.updateNodeAttributes(n, dep=-1)

    #     selected_nodes = selection.selectedNodes()
    #     if len(selected_nodes)>0:
    #         node_id = selected_nodes[0]
    #         deps = dependencies(graph.G, node_id)
    #         topological_deps = nx.topological_sort(nx.subgraph(graph.G, deps))
    #         for idx, dep in enumerate(topological_deps):
    #             graph.updateNodeAttributes(dep, dep=idx)

    # selection.selectionChanged.connect(on_selection_changed)



    # show window
    view.show()
    sys.exit(app.exec())
