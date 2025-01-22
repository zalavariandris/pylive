from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.NetworkXGraphEditor.nx_graph_model import _NodeId, _EdgeId
# from pylive.NetworkXGraphEditor.nx_network_scene_outlet_to_inlet import NXNetworkScene
from pylive.NetworkXGraphEditor.nx_graph_shapes import BaseLinkItem

class NXNetworkLinkTool(QObject):
    def __init__(self, graphscene:'NXNetworkScene'):
        super().__init__(parent=graphscene)
        import typing
        self._graphscene = graphscene
        self.loop = QEventLoop()
        self.draft:BaseLinkItem|None = None
        self.source_node_id:_NodeId
        self.source_key:str
        self.direction:Literal['forward', 'backward'] = 'forward'

    def graphscene(self)->'NXNetworkScene':
        return self._graphscene

    def startFromOutlet(self, node_id:_NodeId, key:str):
        model = self.graphscene().model()
        link = self.graphscene().delegate.createLinkEditor(model, node_id, None, (key, None))
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
        model = self.graphscene().model()
        self.draft = self.graphscene().delegate.createLinkEditor(model, None, node_id, (None, key))
        assert self.draft
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
                    edge_id:_EdgeId = outlet_node_id, self.source_node_id, (outlet_key, self.source_key)
                    model.addEdge(*edge_id)
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