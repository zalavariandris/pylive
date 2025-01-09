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
    NodeShape,
    LinkShape, RoundedLinkShape,
    PortShape,
)

##############
# GRAPHSCENE #
##############

from bidict import bidict
from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel
from pylive.NetworkXGraphEditor.nx_graph_selection_model import (
    NXGraphSelectionModel,
)

from dataclasses import dataclass

# define to NXGraphModel schema
type NodeId = Hashable
type SourceId = Hashable
type TargetId = tuple[Hashable, Hashable]
type EdgeId = tuple[Hashable, Hashable, Hashable]


class NXNetworkScene(QGraphicsScene):
    def __init__(self, model: NXGraphModel, selection_model: NXGraphSelectionModel):
        super().__init__()
        # configure QGraphicsScene
        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

        # store model widget relations
        self._node_graphics_objects: bidict[NodeId, NodeGraphicsObject] = bidict()
        self._target_graphics_objects: bidict[TargetId, InletGraphicsObject] = bidict()
        self._link_graphics_objects: bidict[EdgeId, LinkGraphicsObject] = bidict()
        self._draft_link: LinkGraphicsObject | None = None

        # draft link: # TODO: consider moving it to the GraphView.
        # GraphView is supposed to be responsible for user interactions
        self.draft: LinkShape | None = None  # todo use the widget itself?

        # set model
        # populate with initial model
        self._model:NXGraphModel|None = None
        self.setModel(model)
        
        # set selection model
        self._selection_model = selection_model

        @self.selectionChanged.connect
        def update_selection_model():
            assert self._selection_model
            selected_nodes = [
                self._node_graphics_objects.inverse[cast(NodeGraphicsObject, node)]
                for node in self.selectedItems()
                if node in self._node_graphics_objects.values()
            ]
            self._selection_model.setSelectedNodes(selected_nodes)

        @selection_model.selectionChanged.connect
        def update_scene_selection(selected: set[Hashable], deselected: set[Hashable]):
            selected_widgets = [self.nodeGraphicsObject(n) for n in selected]
            deselected_widgets = [self.nodeGraphicsObject(n) for n in deselected]
            self.blockSignals(True)
            for widget in selected_widgets:
                widget.setSelected(True)

            for widget in deselected_widgets:
                widget.setSelected(False)
            self.blockSignals(False)
            self.selectionChanged.emit()

    def setModel(self, model:NXGraphModel):
        if self._model:
            model.nodesAdded.disconnect(self.onNodesCreated)
            model.nodesAboutToBeRemoved.disconnect(self.onNodesDeleted)
            model.edgesAdded.disconnect(self.onEdgesCreated)
            model.edgesAboutToBeRemoved.disconnect(self.onEdgesDeleted)
        
        if model:
            _ = model.nodesAdded.connect(self.onNodesCreated)
            _ = model.nodesAboutToBeRemoved.connect(self.onNodesDeleted)
            _ = model.edgesAdded.connect(self.onEdgesCreated)
            _ = model.edgesAboutToBeRemoved.connect(self.onEdgesDeleted)
        self._model = model

        ### populate graph
        self.onNodesCreated([n for n in self._model.nodes()])
        self.onEdgesCreated([e for e in self._model.edges()])
            
        # layout items
        self.layout()

    ### <<< Map the interactive graphics ids to widgets
    def nodeGraphicsObject(self, nodeId: NodeId) -> QGraphicsItem:
        return self._node_graphics_objects[nodeId]

    def targetGraphicsObject(self, targetId: TargetId) -> QGraphicsItem:
        return self._target_graphics_objects[targetId]

    def linkGraphicsObject(self, e: EdgeId) -> "LinkGraphicsObject":
        return self._link_graphics_objects[e]

    ### handle interactions

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        return super().mouseDoubleClickEvent(event)

    ### <<< Handle Model Signals
    def onNodesCreated(self, nodes: list[Hashable]):
        assert self._model
        for n in nodes:
            node = NodeGraphicsObject(n, inlets=[])
            self._node_graphics_objects[n] = node
            self.addItem(self.nodeGraphicsObject(n))

            if self._model.hasNodeProperty(n, "inlets"):
                inletNames = self._model.getNodeProperty(n, "inlets")
                assert isinstance(inletNames, list) and all(
                    isinstance(_, str) for _ in inletNames
                )
                for inletName in inletNames:
                    target_id: TargetId = (n, inletName)
                    node = cast(NodeGraphicsObject, self.nodeGraphicsObject(n))
                    inlet = InletGraphicsObject(target_id)
                    node._addInlet(inlet)
                    self._target_graphics_objects[target_id] = inlet

    def onEdgesDeleted(self, edges: list[EdgeId]):
        for e in edges:
            self.removeItem(self.linkGraphicsObject(e))
            if e in self._link_graphics_objects:
                del self._link_graphics_objects[e]

    def onEdgesCreated(self, edges: list[EdgeId]):
        for e in edges:
            link = LinkGraphicsObject(e)
            link.setLabelText(f"{e[2]}")

            self._link_graphics_objects[e] = link
            self.addItem(link)

            u, v, k = e
            link.move(
                self.nodeGraphicsObject(u),
                self.targetGraphicsObject( (v, k) ),
            )

    def onNodesDeleted(self, nodes: list[Hashable]):
        for n in nodes:
            if n in self._node_graphics_objects:
                node_graphics_object = self.nodeGraphicsObject(n)
                raise NotImplementedError()

    def onModelReset(self):
        assert self._model
        ### clear graph
        self._node_graphics_objects.clear()
        self._target_graphics_objects.clear()
        self._link_graphics_objects.clear()
        self._node_graphics_objects.clear()
        self.clear()

        ### populate graph
        self.onNodesCreated([n for n in self._model.nodes()])
        self.onEdgesCreated([e for e in self._model.edges()])
            
        # layout items
        self.layout()

    ### <<< Handle Model Signals

    ### linking tools ###
    def makeDraftLink(self):
        self.draft = LinkShape()
        self.draft.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.draft.setAcceptHoverEvents(False)
        self.draft.setEnabled(False)
        self.draft.setActive(False)
        self.addItem(self.draft)

    def resetDraftLink(self):
        assert self.draft is not None
        self.removeItem(self.draft)
        self.draft = None

    def nodeAt(self, position: QPointF) -> SourceId | None:
        # find source (model) under mouse
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                return self._node_graphics_objects.inverse[
                    cast(NodeGraphicsObject, item)
                ]
            except KeyError:
                return None

    def targetAt(self, position: QPointF) -> TargetId | None:
        # find source (model) under mouse
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                return self._target_graphics_objects.inverse[
                    cast(InletGraphicsObject, item)
                ]
            except KeyError:
                return None

    def layout(self):
        from pylive.utils.graph_layout import hiearchical_layout_with_nx

        pos = hiearchical_layout_with_nx(self._model.G, scale=100)
        for N, (x, y) in pos.items():
            widget = self.nodeGraphicsObject(N)
            widget.setPos(x, y)

    # def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
    #     item = self.itemAt(event.scenePos(), QTransform())
    #     if item in self._node_graphics_objects.values():
    #         print("node clicked")
    #     else:
    #         return super().mousePressEvent(event)


###########################
# Active Graphics Objects #
###########################

class InletGraphicsObject(PortShape):
    def __init__(self, targetId: TargetId):
        super().__init__(label=f"{targetId}")
        self.targetId = targetId

    def graphscene(self) -> "NXNetworkScene":
        return cast(NXNetworkScene, self.scene())

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.graphscene().makeDraftLink()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        draft = self.graphscene().draft
        assert draft is not None

        if nodeId := self.graphscene().nodeAt(event.scenePos()):
            draft.move(self.graphscene().nodeGraphicsObject(nodeId), self)
        else:
            draft.move(event.scenePos(), self)
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.graphscene().resetDraftLink()

        if nodeId := self.graphscene().nodeAt(event.scenePos()):
            scene = self.graphscene()
            scene._model.addEdge(node_)

        return super().mouseReleaseEvent(event)


class NodeGraphicsObject(NodeShape):
    def __init__(
        self,
        n: NodeId,
        inlets: list[InletGraphicsObject],
        parent: QGraphicsItem | None = None,
    ):
        super().__init__(
            title=f"'{n}'",
            inlets=inlets,
            outlets=[],
            parent=parent,
        )
        self.nodeId = n
        self.setAcceptHoverEvents(False)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.moveLinks()
        return super().itemChange(change, value)

    def graphscene(self) -> "NXNetworkScene":
        return cast(NXNetworkScene, self.scene())

    def moveLinks(self):
        """responsible to update connected link position"""
        model = self.graphscene()._model
        in_out_edges = model.inEdges(self.nodeId) + model.outEdges(self.nodeId)
        for edgeId in in_out_edges:
            u, v, k = edgeId
            self.graphscene()
            node = self.graphscene().nodeGraphicsObject(u)
            inlet = self.graphscene().targetGraphicsObject( (v, k) )
            edge = self.graphscene().linkGraphicsObject(edgeId)
            edge.move(node, inlet)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if not self.isSelected():
            self.graphscene().makeDraftLink()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if draft:=self.graphscene().draft:
            # if inletId := self.graphscene()._inletEditorAt(event.scenePos()):
            if inletId := self.graphscene().targetAt(event.scenePos()):
                draft.move(self, self.graphscene().targetGraphicsObject(inletId))
            else:
                draft.move(self, event.scenePos())
        else:
            return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if draft:=self.graphscene().draft:
            self.graphscene().resetDraftLink()

            if targetId := self.graphscene().targetAt(event.scenePos()):
                scene = self.graphscene()

                scene._model.addEdge(self.nodeId, targetId[0], targetId[1])
        else:
            return super().mouseReleaseEvent(event)


class LinkGraphicsObject(RoundedLinkShape):
    def __init__(self, e: EdgeId, parent: QGraphicsItem | None = None):
        super().__init__(label=f"{e}", parent=parent)
        self.edgeId = e
        self.setZValue(-1)

    def graphscene(self) -> "NXNetworkScene":
        return cast(NXNetworkScene, self.scene())

    def boundingRect(self) -> QRectF:
        return super().boundingRect().adjusted(-50, -50, 50, 50)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        ...
        # if event.button() == Qt.MouseButton.LeftButton:
        #     self.grabMouse()
        # else:
        #     self.ungrabMouse()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        print("mouse move event")
        
        if nodeId := self.graphscene().nodeAt(event.scenePos()):
            self.move(self.graphscene().nodeGraphicsObject(nodeId), self)
        else:
            u, v, k= self.edgeId
            self.move(
                event.scenePos(),
                self.graphscene().targetGraphicsObject( (v, k) ),
            )
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        model = self.graphscene()._model
        target = self.graphscene().targetAt(event.scenePos())
        u, v, k = self.edgeId
        if Qt.MouseButton.RightButton in event.buttons():
            # cancel
            self.move(
                self.graphscene().nodeGraphicsObject(u),
                self.graphscene().targetGraphicsObject( (v, k) ),
            )
            self.ungrabMouse()
        else:
            # TODO: add an addMethod to the graphview, to convert from the graph edge representation to the model;s
            u, v, k = self.edgeId
            if target and target != (v, k):
                model.removeEdge(u, v, k)
                model.addEdge(u, target[0], target[1])

            elif target == None:
                model.removeEdge(u, v, k)

            elif target == (v, k):
                # cancel
                self.move(
                    self.graphscene().nodeGraphicsObject(u),
                    self.graphscene().targetGraphicsObject( (v, k) ),
                )
            else:
                raise Exception("")

            return super().mouseReleaseEvent(event)


###########
# EXAMPLE #
###########
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # setup main window
    view = QGraphicsView()
    view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
    view.setWindowTitle("NXNetworkScene")
    view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    # create graph scene
    graph = NXGraphModel()
    graph.addNode("N1")
    graph.addNode("N2", inlets=["in"])
    graph.addNode("N3", inlets=["in"])
    graph.addEdge("N1", "N2", "in")
    graphscene = NXNetworkScene(graph, NXGraphSelectionModel(graph))
    graphscene.setSceneRect(QRectF(-400, -400, 800, 800))
    view.setScene(graphscene)

    # graphscene.addItem(GraphicsVertexItem("HWELLO"))

    # show window
    view.show()
    sys.exit(app.exec())
