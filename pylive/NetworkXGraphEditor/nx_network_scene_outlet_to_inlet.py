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
    distribute_items_horizontal
)

##############
# GRAPHSCENE #
##############

from bidict import bidict
from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel
from pylive.NetworkXGraphEditor.nx_network_model import NXNetworkModel
from pylive.NetworkXGraphEditor.nx_graph_selection_model import NXGraphSelectionModel
from pylive.NetworkXGraphEditor.nx_standard_network_delegate import StandardNetworkDelegte

from dataclasses import dataclass

from pylive.utils.qt import signalsBlocked

# define to NXGraphModel schema

type _NodeId=Hashable
type _OutletName = str
type _InletName = str
type _EdgeId=tuple[_NodeId, _NodeId, tuple[_OutletName, _InletName]]



class NXNetworkScene(QGraphicsScene):
    def __init__(self, model: NXNetworkModel, selection_model: NXGraphSelectionModel, delegate=StandardNetworkDelegte()):
        super().__init__()

        self._model: NXNetworkModel | None = None
        self._selection_model:NXGraphSelectionModel|None = None

        self.delegate = delegate

        # configure QGraphicsScene
        # self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

        # store model widget relations
        self._node_graphics_objects: bidict[_NodeId, QGraphicsItem] = bidict()
        self._outlet_graphics_objects: bidict[tuple[_NodeId, _OutletName], QGraphicsItem] = bidict()
        self._inlet_graphics_objects: bidict[tuple[_NodeId, _InletName], QGraphicsItem] = bidict()
        self._link_graphics_objects: bidict[_EdgeId, QGraphicsItem] = bidict()
        self._draft_link: BaseLinkItem | None = None

        self._attribute_editors: bidict[tuple[_NodeId, str], QGraphicsItem] = bidict()

        # draft link: # TODO: consider moving it to the GraphView.
        # GraphView is supposed to be responsible for user interactions
        # self.draft: RoundedLinkShape | None = None  # todo use the widget itself?

        # set model
        # populate with initial model
        
        self.setModel(model)
        self.setSelectionModel(selection_model)

        self.selectionChanged.connect(self.selectionChangedEvent)

    def attributeEditor(self, node_id:_NodeId, key:str)->QGraphicsItem:
        return self._attribute_editors[(node_id, key)]

    def setSelectionModel(self, selection_model:NXGraphSelectionModel):
        if self._selection_model:
            self._selection_model.selectionChanged.disconnect(self.onSelectionChanged)

        if selection_model:
            selection_model.selectionChanged.connect(self.onSelectionChanged)

        # set selection model
        self._selection_model = selection_model

    def selectionChangedEvent(self):
        if not self._selection_model:
            return

        selected_nodes = [
            self._node_graphics_objects.inverse[cast(BaseNodeItem, node)]
            for node in self.selectedItems()
            if node in self._node_graphics_objects.values()
        ]
        self._selection_model.setSelectedNodes(selected_nodes)

    def setModel(self, model: NXNetworkModel):
        if self._model:
            # Nodes
            model.nodesAdded.disconnect(self.onNodesAdded)
            model.nodesAboutToBeRemoved.disconnect(self.onNodesRemoved)

            # Edges
            model.edgesAdded.disconnect(self.onEdgesAdded)
            model.edgesAboutToBeRemoved.disconnect(self.onEdgesRemoved)

            # Node Attributes
            model.nodeAttributesAdded.disconnect(self.onNodeAttributesAdded)
            model.nodeAttributesAboutToBeRemoved.disconnect(self.onNodeAttributesRemoved)
            model.nodeAttributesChanged.disconnect(self.onNodeAttributesChanged)

            # Edge Attributes
            model.edgeAttributesAdded.disconnect(self.onEdgeAttributesAdded)
            model.edgeAttributesAboutToBeRemoved.disconnect(self.onEdgeAttributesRemoved)
            model.edgeAttributesChanged.disconnect(self.onEdgeAttributesChanged)

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
    def nodeGraphicsObject(self, nodeId: _NodeId) -> BaseNodeItem:
        return cast(BaseNodeItem, self._node_graphics_objects[nodeId])

    def outletGraphicsObject(self, node_id:_NodeId, key:_OutletName) -> QGraphicsItem:
        assert isinstance(key, str)
        return self._outlet_graphics_objects[(node_id, key)]

    def inletGraphicsObject(self, node_id:_NodeId, key: _InletName) -> QGraphicsItem:
        assert isinstance(key, str)
        return self._inlet_graphics_objects[(node_id, key)]
# 
    def linkGraphicsObject(self, u:_NodeId, v:_NodeId, k:tuple[_OutletName, _InletName]) -> BaseLinkItem:
        edge_id = u, v, k
        return cast(BaseLinkItem, self._link_graphics_objects[edge_id])

    def moveAttachedLinks(self, node_id:_NodeId):
        from itertools import chain
        model = self.model()
        assert model
        for e in chain(model.inEdges(node_id), model.outEdges(node_id)):
            u, v, (o, i) = e
            outlet = self.outletGraphicsObject(u, o)
            inlet = self.inletGraphicsObject(v, i)
            link = self.linkGraphicsObject(u, v, (o, i))
            link.move(outlet, inlet)

    ### <<< Handle Model Signals
    def onNodesAdded(self, nodes: list[Hashable]):
        assert self._model
        for node_id in nodes:
            ### create node editor
            node_editor = self.delegate.createNode(node_id)
            node_editor.scenePositionChanged.connect(lambda node_id=node_id: self.moveAttachedLinks(node_id))
            self._node_graphics_objects[node_id] = node_editor
            self.addItem(self.nodeGraphicsObject(node_id))

            ### create attribute editors
            for attr in self._model.nodeAttributes(node_id):
                editor = self.delegate.createAttributeEditor(node_editor, self._model, node_id, attr)
                if editor:
                    self._attribute_editors[(node_id, attr)] = editor

            ### create inlets
            inlets = []
            for inlet_name in self._model.inlets(node_id):
                node_editor = cast(BaseNodeItem, self.nodeGraphicsObject(node_id))
                inlet = self.delegate.createInlet(node_editor, node_id, inlet_name)
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
                outlet = self.delegate.createOutlet(node_editor, node_id, outlet_name)
                self._outlet_graphics_objects[(node_id, outlet_name)] = outlet
                outlets.append(outlet)
            # position outlets
            for outlet in outlets:
                outlet.setY(node_editor.boundingRect().bottom()+3)
            distribute_items_horizontal(outlets, node_editor.boundingRect())

    def onNodesRemoved(self, nodes: list[_NodeId]):
        for n in nodes:
            if n in self._node_graphics_objects:
                node_graphics_object = self.nodeGraphicsObject(n)
                raise NotImplementedError()

    def onEdgesAdded(self, edges: Iterable[tuple[_NodeId, _NodeId, tuple[str, str]]]):
        for e in edges:
            u, v, (o, i) = e
            link = self.delegate.createLink(u, v, (o, i))

            self._link_graphics_objects[e] = link
            self.addItem(link)

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
            node_editor = self.nodeGraphicsObject(node_id)
            for attr in attributes:
                if attr_editor := self.delegate.createAttributeEditor(node_editor, self._model, node_id, attr):
                    self._attribute_editors[(node_id, attr)] = attr_editor
                    self.delegate.updateAttributeEditor(self._model, node_id, attr, attr_editor)

    def onNodeAttributesRemoved(self, node_attributes:dict[_NodeId, list[str]]):
        assert self._model
        for node_id, attributes in node_attributes.items():
            node_editor = self.nodeGraphicsObject(node_id)
            for attr in attributes:
                if attr_editor := self._attribute_editors[(node_id, attr)]:
                    del self._attribute_editors[(node_id, attr)]
                    scene = attr_editor.scene()
                    scene.removeItem(attr_editor)

    def onNodeAttributesChanged(self, node_attributes:dict[_NodeId, list[str]]):
        assert self._model
        for node_id, attributes in node_attributes.items():
            node_editor = self.nodeGraphicsObject(node_id)
            for attr in attributes:
                if attr_editor := self._attribute_editors[(node_id, attr)]:
                    self.delegate.updateAttributeEditor(self._model, node_id, attr, attr_editor)

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

    def onSelectionChanged(self, selected: set[_NodeId], deselected: set[_NodeId]):
        if len(selected)>0 or len(deselected)>0:
            selected_widgets = [self.nodeGraphicsObject(n) for n in selected]
            deselected_widgets = [self.nodeGraphicsObject(n) for n in deselected]

            with signalsBlocked(self):
                for widget in selected_widgets :
                    widget.setSelected(True)

                for widget in deselected_widgets:
                    widget.setSelected(False)

            self.selectionChanged.emit()

    ### <<< Handle Model Signals
    def nodeAt(self, position: QPointF) -> _NodeId | None:
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                node_id =  self._node_graphics_objects.inverse[item]
                return node_id
            except KeyError:
                continue
        return

    def edgeAt(self, position: QPointF) -> tuple[_NodeId, _NodeId, tuple[str, str]] | None:
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                edge_id =  self._link_graphics_objects.inverse[item]
                return edge_id
            except KeyError:
                continue
        return

    def inletAt(self, position: QPointF) -> tuple[_NodeId, str] | None:
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                inlet_id = self._inlet_graphics_objects.inverse[item]
                return inlet_id
            except KeyError:
                continue

    def outletAt(self, position: QPointF) -> tuple[_NodeId, str] | None:
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                outlet_id = self._outlet_graphics_objects.inverse[item]
                return outlet_id
            except KeyError:
                continue

    def layout(self):
        assert self._model
        from pylive.utils.graph import hiearchical_layout_with_nx
        pos = hiearchical_layout_with_nx(self._model.G, scale=100)
        for N, (x, y) in pos.items():
            widget = self.nodeGraphicsObject(N)
            widget.setPos(x, y)

    @override
    def sendEvent(self, item:QGraphicsItem, event:QEvent)->bool:
        print("send event")
        return super().sendEvent(item, event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if outlet_id:=self.outletAt(event.scenePos()):
            node_id, outlet_key = outlet_id
            self.tool = GraphLinkTool(self)
            self.tool.startFromOutlet(node_id, outlet_key)
        elif inlet_id:=self.inletAt(event.scenePos()):
            node_id, inlet_key = inlet_id
            self.tool = GraphLinkTool(self)
            self.tool.startFromInlet(node_id, inlet_key)
        elif node_id:=self.nodeAt(event.scenePos()):
            super().mousePressEvent(event)
        elif edge_id:=self.edgeAt(event.scenePos()):
            super().mousePressEvent(event)


class GraphLinkTool(QObject):
    def __init__(self, graphscene:NXNetworkScene):
        super().__init__(parent=graphscene)
        import typing
        self._graphscene = graphscene
        self.loop = QEventLoop()
        self.draft:BaseLinkItem|None = None
        self.source_node_id:_NodeId
        self.source_key:str
        self.direction:Literal['forward', 'backward'] = 'forward'

    def graphscene(self)->NXNetworkScene:
        return self._graphscene

    def startFromOutlet(self, node_id:_NodeId, key:str):
        link = self.graphscene().delegate.createLink(node_id, None, (key, None))
        self.draft = link
        assert self.draft
        self.draft.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.draft.setAcceptHoverEvents(False)
        self.draft.setEnabled(False)
        self.draft.setActive(False)
        self.graphscene().addItem(self.draft)

        self.source_node_id = node_id
        self.source_key = key

        ### start event loop
        app = QApplication.instance()
        assert isinstance(app, QGuiApplication)
        self.direction = 'forward'
        app.installEventFilter(self)
        self.loop.exec()
        app.removeEventFilter(self)

    def startFromInlet(self, node_id:_NodeId, key:str):
        self.draft = self.graphscene().delegate.createLink(None, node_id, (None, key))
        assert self.draft
        # self.draft.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        # self.draft.setAcceptHoverEvents(False)
        # self.draft.setEnabled(False)
        # self.draft.setActive(False)
        self.graphscene().addItem(self.draft)
        
        self.source_node_id = node_id
        self.source_key = key

        ### start event loop
        app = QApplication.instance()
        assert isinstance(app, QGuiApplication)
        self.direction = 'backward'
        app.installEventFilter(self)
        self.loop.exec()
        app.removeEventFilter(self)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        ...

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        assert self.draft is not None
        match self.direction:
            case 'forward':
                assert self.source_node_id is not None
                if target := self.graphscene().inletAt(event.scenePos()):
                    target_node_id, target_key = target
                    self.draft.move(
                        self.graphscene().outletGraphicsObject(self.source_node_id, self.source_key),
                        self.graphscene().inletGraphicsObject(target_node_id, target_key)
                    )
                else:
                    self.draft.move(
                        self.graphscene().outletGraphicsObject(self.source_node_id, self.source_key), 
                        event.scenePos()
                    )

            case 'backward':
                assert self.source_node_id is not None
                if target := self.graphscene().outletAt(event.scenePos()):
                    target_node_id, target_key = target
                    self.draft.move(
                        self.graphscene().outletGraphicsObject(target_node_id, target_key),
                        self.graphscene().inletGraphicsObject(self.source_node_id, self.source_key)
                    )
                else:
                    self.draft.move(
                        event.scenePos(),
                        self.graphscene().inletGraphicsObject(self.source_node_id, self.source_key)
                    )

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        assert self.draft is not None
        scene = self.graphscene()
        self.graphscene().removeItem(self.draft)
        model = scene.model()
        assert model is not None
        match self.direction:
            case 'forward':
                assert self.source_node_id is not None
                if inlet_id := self.graphscene().inletAt(event.scenePos()):
                    inlet_node_id, inlet_key = inlet_id
                    model.addEdge(self.source_node_id, inlet_node_id, (self.source_key, inlet_key))
                else:
                    pass

            case 'backward':
                assert self.source_node_id is not None
                if outlet_id := self.graphscene().outletAt(event.scenePos()):
                    outlet_node_id, outlet_key = outlet_id
                    
                    model.addEdge(outlet_id, self.source_node_id, (outlet_key, self.source_key))
                else:
                    pass

        
        self.loop.exit()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        match event.type():
            case QEvent.Type.GraphicsSceneMouseMove:
                self.mouseMoveEvent(cast(QGraphicsSceneMouseEvent, event))
                return True
            case QEvent.Type.GraphicsSceneMouseRelease:
                self.mouseReleaseEvent(cast(QGraphicsSceneMouseEvent, event))
                return True
            case _:
                pass
        return super().eventFilter(watched, event)


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


    scene = NXNetworkScene(graph, selection)
    scene.setSceneRect(QRectF(-400, -400, 800, 800))
    view.setScene(scene)

    from pylive.utils.graph import dependencies, dependents
    import networkx as nx
    def on_selection_changed(selected, deselected):
        for n in graph.nodes():
            graph.updateNodeAttributes(n, dep=-1)

        selected_nodes = selection.selectedNodes()
        if len(selected_nodes)>0:
            node_id = selected_nodes[0]
            deps = dependencies(graph.G, node_id)
            topological_deps = nx.topological_sort(nx.subgraph(graph.G, deps))
            for idx, dep in enumerate(topological_deps):
                graph.updateNodeAttributes(dep, dep=idx)

    selection.selectionChanged.connect(on_selection_changed)



    # show window
    view.show()
    sys.exit(app.exec())
