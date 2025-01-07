from enum import StrEnum
from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.QtGraphEditor.text_widget import TextWidget
from pylive.QtGraphEditor.circle_widget import CircleWidget
from pylive.QtGraphEditor.NetrowkXGraphEditor.link_graphics_items import (
    makeLineBetweenShapes,
)
from pylive.QtGraphEditor.NetrowkXGraphEditor.qgraphics_arrow_item import (
    QGraphicsArrowItem,
    makeArrowShape,
)

ConnectionEnterType = QEvent.Type(QEvent.registerEventType())
ConnectionLeaveType = QEvent.Type(QEvent.registerEventType())
ConnectionMoveType = QEvent.Type(QEvent.registerEventType())
ConnectionDropType = QEvent.Type(QEvent.registerEventType())

import numpy as np
import networkx as nx


##################
# GRAPHICS ITEMS #
##################

# class BaseItem(QGraphicsItem):
#     def __init__(self, parent=None):
#         super().__init__(parent=parent)
#         self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
#         self.setAcceptHoverEvents(True)
#         self._isHighlighted = False
#         self._hoverMousePos: QPointF | None = None

#     def setHighlighted(self, value):
#         self._isHighlighted = value
#         self.update()

#     def isHighlighted(self):
#         return self._isHighlighted

#     def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
#         self.setHighlighted(True)

#     def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
#         self._hoverMousePos = event.pos()
#         self.update()

#     def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
#         self.setHighlighted(False)

#     def font(self):
#         if font:=getattr(self, "_font", None):
#             return font
#         elif parentWidget := self.parentWidget():
#             return parentWidget.font()
#         elif scene := self.scene():
#             return scene.font()
#         elif app := QApplication.instance():
#             if isinstance(app, QGuiApplication):
#                 return app.font()

#         return QFont()

#     def palette(self) -> QPalette:
#         if palette := getattr(self, "_palette", None):
#             return palette
#         elif parentWidget := self.parentWidget():
#             return parentWidget.palette()
#         elif scene := self.scene():
#             return scene.palette()
#         elif app := QApplication.instance():
#             if isinstance(app, QGuiApplication):
#                 return app.palette()

#         return QPalette()

#     def brush(self):
#         baseColor = self.palette().base().color()
#         baseColor.setAlpha(255)
#         brush = QBrush(baseColor)
#         return brush

#     def pen(self):
#         palette = self.palette()

#         pen = QPen(palette.text().color())

#         if self.isSelected():
#             pen.setColor(palette.highlight().color())  # Color for selected

#         if self.isHighlighted():
#             pen.setColor(palette.accent().color())  # Color for hover

#         return pen


# class GraphicsVertexItem(BaseItem):
#     """A graph 'Vertex' graphics item. no inlets or outlets."""

#     def __init__(
#         self,
#         title: str = "Node",
#         parent: QGraphicsItem | None = None,
#     ):
#         super().__init__(parent)
#         # private variables
#         self._title: str = title
#         self._isHighlighted: bool = False

#         # Enable selection and movement
#         self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsSelectable, True)
#         self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsMovable, True)
#         self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsFocusable, True)
#         self.setFlag(
#             QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
#         )
#         self.setAcceptHoverEvents(True)

#     def __repr__(self):
#         return f"{self.__class__.__name__}({self._title!r})"

#     @override
#     def boundingRect(self) -> QRectF:
#         fm = QFontMetrics(self.font())

#         text_width = fm.horizontalAdvance(self._title)
#         text_height = fm.height()
#         return QRectF(0, 0, text_width + 8, text_height + 4)

#     def paint(
#         self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None
#     ):
#         painter.setBrush(self.brush())
#         painter.setPen(self.pen())
#         painter.drawRoundedRect(self.boundingRect(), 4, 4)

#         fm = QFontMetrics(self.font())
#         painter.drawText(4, fm.height() - 1, self._title)

#     def title(self):
#         return self._title

#     def setTitle(self, text: str):
#         self._title = text
#         self.update()


# class GraphicsLinkItem(BaseItem):
#     """Graphics item representing an edge in a graph."""

#     def __init__(
#         self,
#         label: str = "-link-",
#     ):
#         super().__init__(parent=None)
#         self._label = label

#         # Enable selecting
#         self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
#         self.setAcceptHoverEvents(True)
#         self.setZValue(-1)

#         self._line: QLineF = QLineF()

#     def setLine(self, line: QLineF):
#         self.prepareGeometryChange()
#         self._line = line
#         self.update()

#     def line(self) -> QLineF:
#         return self._line

#     def __repr__(self):
#         return f"{self.__class__.__name__}({self._label!r})"

#     def setLabelText(self, text: str):
#         self._label = text
#         self.update()

#     def labelText(self):
#         return self._label

#     def pen(self):
#         """override to indicate endpoints under mouse"""
#         palette = self.palette()

#         pen = QPen(palette.text().color())

#         if self.isSelected():
#             pen.setColor(palette.highlight().color())  # Color for selected

#         if self.isHighlighted():
#             if self._hoverMousePos:
#                 linearGrad = QLinearGradient(self.line().p1(), self.line().p2())
#                 d1 = QLineF(
#                     self.mapFromParent(self.line().p1()), self._hoverMousePos
#                 ).length()
#                 d2 = QLineF(
#                     self.mapFromParent(self.line().p2()), self._hoverMousePos
#                 ).length()
#                 if d1 < d2:
#                     linearGrad.setColorAt(0.0, palette.accent().color())
#                     linearGrad.setColorAt(0.5, palette.accent().color())
#                     linearGrad.setColorAt(0.55, palette.text().color())
#                 else:
#                     linearGrad.setColorAt(0.45, palette.text().color())
#                     linearGrad.setColorAt(0.5, palette.accent().color())
#                     linearGrad.setColorAt(1, palette.accent().color())
#                 pen.setBrush(QBrush(linearGrad))  # Color for hover
#             else:
#                 pen.setBrush(palette.accent().color())  # Color for hover

#         return pen

#     def paint(
#         self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None
#     ):
#         ### draw arrow shape
#         arrow_shape = makeArrowShape(self.line(), self.pen().widthF())

#         # use the pen as brush to draw the arrow shape
#         painter.setPen(Qt.NoPen)
#         painter.setBrush(self.pen().brush())
#         painter.drawPath(arrow_shape)
#         painter.drawLine(self.line())

#         ### draw label
#         try:
#             fm = QFontMetrics(self.scene().font())
#         except AttributeError:
#             fm = QFontMetrics(QApplication.instance().font())

#         painter.setPen(self.pen())
#         painter.drawText(self.line().center() - self.pos(), self._label)

#     def shape(self) -> QPainterPath:
#         """Override shape to provide a wider clickable area."""
#         path = QPainterPath()
#         path.moveTo(self.line().p1())
#         path.lineTo(self.line().p2())
#         stroker = QPainterPathStroker()
#         stroker.setWidth(10)
#         stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
#         stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
#         return stroker.createStroke(path)

#     def boundingRect(self) -> QRectF:
#         try:
#             fm = QFontMetrics(self.scene().font())
#         except AttributeError:
#             fm = QFontMetrics(QApplication.instance().font())

#         text_width = fm.horizontalAdvance(self._label)
#         text_height = fm.height()

#         shape_bbox = self.shape().boundingRect()
#         text_bbox = QRectF(
#             self.line().center() - self.pos()-QPointF(0,text_height), QSizeF(text_width, text_height)
#         )

#         m = self.pen().widthF()
#         return shape_bbox.united(text_bbox).adjusted(-m, -m, m, m)


# class GraphicsNodeItem(GraphicsVertexItem):
#     def __init__(self, title, inlets, outlets, parent=None):
#         super().__init__(title=title, parent=parent)
#         self._inlets: list[QGraphicsItem] = []
#         self._outlets: list[QGraphicsItem] = []
#         for inlet in inlets:
#             self._addInlet(inlet)
#         for outlet in outlets:
#             self._addOutlet(outlet)

#     def boundingRect(self) -> QRectF:
#         return (
#             super()
#             .boundingRect()
#             .united(self.childrenBoundingRect())
#             .adjusted(-4, 0, 4, 2)
#         )

#     def _addInlet(self, inlet_widget: QGraphicsItem):
#         inlet_widget.setParentItem(self)
#         self._inlets.append(inlet_widget)
#         self.layoutPorts()
#         self.update()

#     def _removeInlet(self, inlet_widget: QGraphicsItem):
#         self._inlets.remove(inlet_widget)
#         inlet_widget.setParentItem(None)
#         if scene := inlet_widget.scene():
#             scene.removeItem(inlet_widget)
#         self.layoutPorts()
#         self.update()

#     def _addOutlet(self, outlet_widget: QGraphicsItem):
#         outlet_widget.setParentItem(self)
#         self._outlets.append(outlet_widget)
#         self.layoutPorts()
#         self.update()

#     def _removeOutlet(self, outlet_widget: QGraphicsItem):
#         self._outlets.remove(outlet_widget)
#         outlet_widget.setParentItem(self)
#         if scene := outlet_widget.scene():
#             scene.removeItem(outlet_widget)
#         self.layoutPorts()
#         self.update()

#     def layoutPorts(self):
#         y = 14  # header heighn
#         for inlet_widget in self._inlets:
#             inlet_widget.setPos(4, y)
#             y += inlet_widget.boundingRect().height()

#         for outlet_widget in self._outlets:
#             outlet_widget.setPos(4, y)
#             y += outlet_widget.boundingRect().height()


# class GraphicsPortItem(BaseItem):
#     def __init__(
#         self,
#         label: str,
#         parent: QGraphicsItem | None = None,
#     ):
#         super().__init__(parent=parent)
#         self._label = label

#     def label(self) -> str:
#         return self._label

#     def setLabel(self, text: str):
#         self._label = text

#     def boundingRect(self) -> QRectF:
#         fm = QFontMetrics(self.font())

#         ellipse_bbox = QRectF(0, 0, 10, 10)
#         text_width = fm.horizontalAdvance(self._label)
#         text_height = fm.height()

#         text_pos = QPointF(12, 0)
#         text_bbox = QRectF(text_pos, QSizeF(text_width, text_height))
#         return ellipse_bbox.united(text_bbox)

#     def paint(self, painter, option, widget=None):
#         ### draw label
#         fm = QFontMetrics(self.font())

#         painter.setPen(self.pen())
#         painter.drawEllipse(QRectF(2, 7, 6, 6))

#         text_height = fm.height()
#         text_pos = QPointF(12, text_height - 2)
#         painter.drawText(text_pos, self._label)


from pylive.QtGraphEditor.nx_graph_graphics_items import (
    GraphicsVertexItem,
    GraphicsNodeItem,
    GraphicsLinkItem,
    GraphicsPortItem,
)

#################
# LINKING TOOLS #
#################


class LinkEvent(QGraphicsSceneEvent):
    """
    the property accepted is set to False by default.
    """

    def __init__(self, type: QEvent.Type, source: QGraphicsItem):
        super().__init__(type)
        self._type = type
        self._source = source
        # by default QEvents are set to accepted.
        # for connection event set this to False
        # https://doc.qt.io/qt-6/qevent.html#accepted-prop
        self.setAccepted(False)

    def source(self) -> QGraphicsItem:
        """graphics item initiated the event"""
        return self._source

    def _type_name(self):
        if self._type == ConnectionEnterType:
            return "ConnectionEnterType"
        if self._type == ConnectionLeaveType:
            return "ConnectionLeaveType"
        if self._type == ConnectionMoveType:
            return "ConnectionMoveType"
        if self._type == ConnectionDropType:
            return "ConnectionDropType"

    def __str__(self):
        return f"LinkEvent({self._type_name()})"


class SceneMouseTool(QObject):
    accepted = Signal()
    finished = Signal(object)  # result
    rejected = Signal()
    targetChanged = Signal()

    def __init__(self, scene, parent: QObject | None = None):
        super().__init__(parent=parent)
        self._loop = QEventLoop()
        self._result: Any = None

        self._entered_items = []
        self._target: QGraphicsItem | None = None
        self.scene = scene

    def _trackTargetItem(
        self, scene: QGraphicsScene, event: QGraphicsSceneMouseEvent
    ):
        entered_items = [item for item in self._entered_items]

        itemsUnderMouse = [
            item for item in scene.items(event.scenePos()) if item.isEnabled()
        ]
        print("itemsUnderMouse", itemsUnderMouse)
        for item in itemsUnderMouse:
            if item not in entered_items:
                self._entered_items.append(item)
                self.itemHoverEnterEvent(item)
                if event.isAccepted():
                    self._target = item
                    self.targetChanged.emit()
                    break

        for item in entered_items:
            if item not in itemsUnderMouse:
                self._entered_items.remove(item)
                self.itemHoverLeaveEvent(item)
        if self._target and self._target not in self._entered_items:
            self._target = None
            self.targetChanged.emit()

        # send ConnectionMove event
        for item in self._entered_items:
            self.itemHoverMoveEvent(item)

    def start(self):
        app = QApplication.instance()
        assert isinstance(app, QGuiApplication)
        app.installEventFilter(self)
        _ = self._loop.exec()
        app.removeEventFilter(self)

    def exit(self):
        self._loop.exit()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        match event.type():
            case QEvent.Type.GraphicsSceneMousePress:
                self.mousePressEvent(cast(QGraphicsSceneMouseEvent, event))
                return True
            case QEvent.Type.GraphicsSceneMouseMove:
                self._trackTargetItem(
                    self.scene, cast(QGraphicsSceneMouseEvent, event)
                )
                self.mouseMoveEvent(cast(QGraphicsSceneMouseEvent, event))
                return True
            case QEvent.Type.GraphicsSceneMouseRelease:
                self.mouseReleaseEvent(cast(QGraphicsSceneMouseEvent, event))
                return True

        return super().eventFilter(watched, event)

    def mouseDoubleClickEvent(
        self, mouseEvent: QGraphicsSceneMouseEvent
    ) -> None:
        ...

    def mouseMoveEvent(self, mouseEvent: QGraphicsSceneMouseEvent) -> None:
        ...

    def mousePressEvent(self, mouseEvent: QGraphicsSceneMouseEvent) -> None:
        ...

    def mouseReleaseEvent(self, mouseEvent: QGraphicsSceneMouseEvent) -> None:
        self.exit()

    def wheelEvent(self, wheelEvent: QGraphicsSceneWheelEvent) -> None:
        ...

    def itemHoverEnterEvent(self, item: QGraphicsItem):
        ...

    def itemHoverLeaveEvent(self, item: QGraphicsItem):
        ...

    def itemHoverMoveEvent(self, item: QGraphicsItem):
        ...

    # def keyPressEvent(self, event: QKeyEvent) -> None:
    #     ...

    # def keyReleaseEvent(self, event: QKeyEvent) -> None:
    #     ...

    # def mouseDoubleClickEvent(self, event: QMouseEvent):
    #     ...

    # def mouseMoveEvent(self, event: QMouseEvent) -> None:
    #     ...

    # def mousePressEvent(self, event: QMouseEvent) -> None:
    #     self.exit()

    # def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    #     self.exit()

    # def wheelEvent(self, event: QWheelEvent) -> None:
    #     ...


# @final
# class DragLink(QObject):
#     """
#     source: the widget the connection was initiated by.
#     direction: the arrow direction.
#       _forward_ points to the _target_.
#       _backward_ points to the _source_.
#     """

#     targetChanged = Signal()
#     """signal to notify when the drop target has changed"""

#     def __init__(
#         self,
#         source: "QGraphicsItem",
#         direction: Literal["forward", "backward"] = "forward",
#         parent: QObject | None = None,
#     ):
#         super().__init__(parent=parent)
#         self._source: QGraphicsItem = source
#         self._target: QGraphicsItem | None = None

#         self._direction: Literal["forward", "backward"] = direction

#         self._loop = (
#             QEventLoop()
#         )  # event loop to capture all events while executing this tool
#         self._arrow = None  # the arrow QGraphicsItem
#         self._entered_items: list[
#             QGraphicsItem
#         ] = []  # keep track of entered items

#     def __str__(self):
#         return f"DragLink({self.source()},{self.target()})"

#     def source(self) -> QGraphicsItem | None:
#         """the widget the connection was initiated by."""
#         return self._source

#     def target(self) -> QGraphicsItem | None:
#         """the actual drop target if any"""
#         return self._target

#     def start(self):
#         """initiate connection, and enter the eventloop"""
#         scene = self._source.scene()
#         assert scene

#         self._arrow = QGraphicsArrowItem(
#             QLineF(self._source.pos(), self._source.pos())
#         )
#         self._arrow.setPen(
#             QPen(scene.palette().color(QPalette.ColorRole.Text), 1)
#         )
#         scene.addItem(self._arrow)
#         app = QApplication.instance()
#         assert app is not None
#         app.installEventFilter(self)
#         _ = self._loop.exec()
#         app.removeEventFilter(self)
#         scene.removeItem(self._arrow)

#     def eventFilter(self, watched: QObject, event: QEvent) -> bool:
#         """
#         capture all mouse event here, convert to connection events, and
#         send these to potential target items
#         """
#         if event.type() == QEvent.Type.GraphicsSceneMouseMove:
#             event = cast(QGraphicsSceneMouseEvent, event)

#             ### Move arrow ####
#             assert self._arrow
#             match self._direction:
#                 case "forward":
#                     assert self._source
#                     line = makeLineBetweenShapes(self._source, event.scenePos())
#                 case "backward":
#                     assert self._source
#                     line = makeLineBetweenShapes(event.scenePos(), self._source)
#             # assert line, f"got: {line}"
#             self._arrow.setLine(line)

#             # manage connection enter and leave event
#             scene = self._source.scene()
#             entered_items = [item for item in self._entered_items]

#             itemsUnderMouse = [item for item in scene.items(event.scenePos())]
#             # print(itemsUnderMouse)
#             for item in itemsUnderMouse:
#                 if item not in entered_items:
#                     self._entered_items.append(item)
#                     event = LinkEvent(ConnectionEnterType, self._source)
#                     _ = scene.sendEvent(item, event)
#                     if event.isAccepted():
#                         self._target = item
#                         self.targetChanged.emit()
#                         break

#             for item in entered_items:
#                 if item not in itemsUnderMouse:
#                     self._entered_items.remove(item)
#                     event = LinkEvent(ConnectionLeaveType, self._source)
#                     _ = scene.sendEvent(item, event)
#             if self._target and self._target not in self._entered_items:
#                 self._target = None
#                 self.targetChanged.emit()

#             # send ConnectionMove event
#             for item in self._entered_items:
#                 event = LinkEvent(ConnectionMoveType, self._source)
#                 _ = scene.sendEvent(item, event)

#             return True

#         if event.type() == QEvent.Type.GraphicsSceneMouseRelease:
#             if self._target:
#                 _ = scene = self._source.scene()
#                 event = LinkEvent(ConnectionDropType, self._source)
#                 _ = scene.sendEvent(self._target, event)
#             self._loop.exit()
#             return True

#         return super().eventFilter(watched, event)


class LinkTool(SceneMouseTool):
    def __init__(self, source: QGraphicsItem):
        super().__init__(source.scene())
        self.draft = GraphicsLinkItem()
        self.draft.setAcceptedMouseButtons(Qt.NoButton)
        self.draft.setAcceptHoverEvents(False)
        self.draft.setEnabled(False)
        self.draft.setActive(False)
        self.source = source
        assert self.scene is not None
        self.scene.addItem(self.draft)
        self.draft.setLine(makeLineBetweenShapes(source, source))

    @override
    def mousePressEvent(self, mouseEvent: QGraphicsSceneMouseEvent) -> None:
        assert self.draft is not None
        self.draft.setLine(
            makeLineBetweenShapes(self.source, mouseEvent.scenePos())
        )

    @override
    def mouseMoveEvent(self, mouseEvent: QGraphicsSceneMouseEvent) -> None:
        self.draft.setLine(
            makeLineBetweenShapes(self.source, mouseEvent.scenePos())
        )

    @override
    def mouseReleaseEvent(self, mouseEvent: QGraphicsSceneMouseEvent) -> None:
        self.scene.removeItem(self.draft)
        self.exit()

    def itemHoverEnterEvent(self, item: QGraphicsItem):
        print("item entered:", item)
        return super().itemHoverEnterEvent(item)


###########################
# Active Graphics Objects #
###########################

type PortId = Hashable
type NodeId = Hashable
type LinkId = tuple[
    NodeId, NodeId, PortId | tuple[PortId, PortId]
]  # outNodeId, inNodeId, edge_key


class NodeGraphicsObject(GraphicsNodeItem):
    def __init__(
        self,
        n: NodeId,
        inlets: list[str],
        outlets: list[str],
        parent: QGraphicsItem | None = None,
    ):
        self._inlet_graphics_objects: dict[str, GraphicsPortItem] = {
            name: GraphicsPortItem(name) for name in inlets
        }
        self._outlet_graphics_objects: dict[str, GraphicsPortItem] = {
            name: GraphicsPortItem(name) for name in outlets
        }
        super().__init__(
            title=f"'{n}'",
            inlets=self._inlet_graphics_objects.values(),
            outlets=self._outlet_graphics_objects.values(),
            parent=parent,
        )
        self._n = n

    def inletGraphicsObject(self, p: str):
        return self._inlet_graphics_objects[p]

    def outletGraphicsObject(self, p: str):
        return self._inlet_graphics_objects[p]

    def itemChange(
        self, change: QGraphicsItem.GraphicsItemChange, value: Any
    ) -> Any:
        if (
            change
            == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged
        ):
            self.moveLinks()
        return super().itemChange(change, value)

    def graphscene(self) -> "NXGraphScene":
        return cast(NXGraphScene, self.scene())

    def moveLinks(self):
        """responsible to update connected link position"""
        for e in self.graphscene()._model.inEdges(
            self._n
        ) + self.graphscene()._model.outEdges(self._n):
            edge = self.graphscene().linkGraphicsObject(e)
            edge.move()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        LinkTool(self).start()


class LinkGraphicsObject(GraphicsLinkItem):
    def __init__(self, e: LinkId, parent: QGraphicsItem | None = None):
        super().__init__(label=f"{e}", parent=parent)
        self._e = e

    def graphscene(self) -> "NXGraphScene":
        return cast(NXGraphScene, self.scene())

    def move(self):
        u, v, k = self._e  # todo: handle non multiedge graphs
        source_graphics = self.graphscene().nodeGraphicsObject(u)
        target_graphics = self.graphscene().nodeGraphicsObject(v)
        # TODO get prots from the 'k'

        if isinstance(k, tuple):
            outletId, inletId = k
            if source_port := source_graphics._outlet_graphics_objects.get(
                outletId
            ):
                source_graphics = source_port
            if target_port := target_graphics._inlet_graphics_objects.get(
                inletId
            ):
                target_graphics = target_port
        elif target_port := target_graphics._inlet_graphics_objects.get(k):
            target_graphics = target_port

        line = makeLineBetweenShapes(source_graphics, target_graphics)
        self.setLine(line)

        # elif :
        #     ...
        # else:
        #     ...
        # match k:
        #     case int():
        #         # by default networkx adds a unique for multigraph edges
        #         line = makeLineBetweenShapes(source_node, target_node)
        #         self.setLine(line)
        #     case str() if k: # check if a port widged actually exist...
        #         raise NotImplementedError(f"Unsupported port identifier: {k}")
        #     case tuple():
        #         raise NotImplementedError(f"Unsupported port identifier: {k}")
        #     case _:
        #         # consider support everything, by connecting the nodes,
        #         # and displaying the edge k on the edge label
        #         raise NotImplementedError(f"Unsupported port identifier: {k}")

    def boundingRect(self) -> QRectF:
        return super().boundingRect().adjusted(-50, -50, 50, 50)


from pylive.QtGraphEditor.nx_graph_model import NXGraphModel


class NXGraphScene(QGraphicsScene):
    # connected = Signal(QGraphicsItem, QGraphicsItem)  # source, target
    # disconnected = Signal(QGraphicsItem, QGraphicsItem)  # edge

    def __init__(self, model: NXGraphModel):
        super().__init__()
        self._model = model
        self._node_graphics_objects: dict[NodeId, NodeGraphicsObject] = dict()
        self._link_graphics_objects: dict[LinkId, LinkGraphicsObject] = dict()
        self._draft_link: LinkGraphicsObject | None = None

        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

        self._model.edgesAdded.connect(
            lambda edges: [self.onLinkCreated(e) for e in edges]
        )
        self._model.edgesRemoved.connect(
            lambda edges: [self.onLinkDeleted(e) for e in edges]
        )
        self._model.nodesAdded.connect(
            lambda nodes: [self.onNodeCreated(n) for n in nodes]
        )
        self._model.nodesRemoved.connect(
            lambda nodes: [self.onNodeDeleted(n) for n in nodes]
        )
        # self._model.nodesPropertiesChanged.connect(self.onNodeUpdated)
        # connect(this, &BasicGraphicsScene::nodeClicked, this, &BasicGraphicsScene::onNodeClicked);)
        # connect(&_graphModel, &AbstractGraphModel::modelReset, this, &BasicGraphicsScene::onModelReset);

        self.traverseGraphAndPopulateGraphicsObjects()
        self.layout()

    def traverseGraphAndPopulateGraphicsObjects(self):
        allNodeIds: list[NodeId] = self._model.nodes()

        # First create all the nodes.
        for nodeId in allNodeIds:
            inlet_names = (
                self._model.getNodeProperty(nodeId, "inlets")
                if self._model.hasNodeProperty(nodeId, "inlets")
                else []
            )
            outlet_names = (
                self._model.getNodeProperty(nodeId, "outlets")
                if self._model.hasNodeProperty(nodeId, "outlets")
                else []
            )
            assert isinstance(inlet_names, list) and all(
                isinstance(_, str) for _ in inlet_names
            )
            assert isinstance(outlet_names, list) and all(
                isinstance(_, str) for _ in outlet_names
            )
            self._node_graphics_objects[nodeId] = NodeGraphicsObject(
                nodeId, inlets=inlet_names, outlets=outlet_names
            )
            self.addItem(self.nodeGraphicsObject(nodeId))

        for e in self._model.edges():
            link = LinkGraphicsObject(e)
            self._link_graphics_objects[e] = link
            self.addItem(link)

    def linkGraphicsObject(self, e: LinkId) -> LinkGraphicsObject:
        return self._link_graphics_objects[e]

    def nodeGraphicsObject(self, n: NodeId) -> NodeGraphicsObject:
        return self._node_graphics_objects[n]

    def updateAttachedNodes(self, e: LinkId, kind: Literal["in", "out"]):
        u, v, k = e
        match kind:
            case "in":
                if node := self._node_graphics_objects.get(u, None):
                    node.update()
            case "out":
                if node := self._node_graphics_objects.get(v, None):
                    node.update()

    ### Handle Model Signals >>>
    def onLinkDeleted(self, e: LinkId):
        self.removeItem(self.linkGraphicsObject(e))
        if e in self._link_graphics_objects:
            del self._link_graphics_objects[e]

        if self._draf_link._e == e:
            self._draft_link.reset()

        self.updateAttachedNodes(e, "in")
        self.updateAttachedNodes(e, "out")

    def onLinkCreated(self, e: LinkId):
        self._link_graphics_objects[e] = LinkGraphicsObject(e)
        self.addItem(self.linkGraphicsObject(e))
        self.updateAttachedNodes(e, "in")
        self.updateAttachedNodes(e, "out")

    def onNodeCreated(self, n: NodeId):
        print("onNodeCreated")
        inlet_names = (
            self._model.getNodeProperty(n, "inlets")
            if self._model.hasNodeProperty(n, "inlets")
            else []
        )
        outlet_names = (
            self._model.getNodeProperty(n, "outlets")
            if self._model.hasNodeProperty(n, "outlets")
            else []
        )
        assert isinstance(inlet_names, list) and all(
            isinstance(_, str) for _ in inlet_names
        )
        assert isinstance(outlet_names, list) and all(
            isinstance(_, str) for _ in outlet_names
        )
        self._node_graphics_objects[n] = NodeGraphicsObject(
            n, inlets=inlet_names, outlets=inlet_names
        )
        self.addItem(self.nodeGraphicsObject(n))

    def onNodeDeleted(self, n: NodeId):
        if n in self._node_graphics_objects:
            self._node_graphics_objects[n]

    def onModelReset(self):
        self._link_graphics_objects.clear()
        self._node_graphics_objects.clear()
        self.clear()

        self.traverseGraphAndPopulateGraphicsObjects()

    ### <<< Handle Model Signals
    def layout(self):
        def hiearchical_layout_with_grandalf(G, scale=1):
            import grandalf
            from grandalf.layouts import SugiyamaLayout

            g = grandalf.utils.convert_nextworkx_graph_to_grandalf(G)

            class defaultview(object):  # see README of grandalf's github
                w, h = scale, scale

            for v in g.C[0].sV:
                v.view = defaultview()
            sug = SugiyamaLayout(g.C[0])
            sug.init_all()  # roots=[V[0]])
            sug.draw()
            return {
                v.data: (v.view.xy[0], v.view.xy[1]) for v in g.C[0].sV
            }  # Extracts the positions

        def hiearchical_layout_with_nx(G, scale=100):
            for layer, nodes in enumerate(
                reversed(tuple(nx.topological_generations(G)))
            ):
                # `multipartite_layout` expects the layer as a node attribute, so add the
                # numeric layer value as a node attribute
                for node in nodes:
                    G.nodes[node]["layer"] = -layer

            # Compute the multipartite_layout using the "layer" node attribute
            pos = nx.multipartite_layout(
                G, subset_key="layer", align="horizontal"
            )
            for n, p in pos.items():
                pos[n] = p[0] * scale, p[1] * scale
            return pos

        # print(pos)
        pos = hiearchical_layout_with_nx(self._model.G, scale=100)
        for N, (x, y) in pos.items():
            widget = self.nodeGraphicsObject(N)
            widget.setPos(x, y)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # setup main window
    view = QGraphicsView()
    view.setWindowTitle("NXGraphScene")
    view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    # create graph scene
    graph = NXGraphModel()
    graph.addNode("N1")
    graph.addNode("N2", inlets=["in"])
    graph.addEdge("N1", "N2", "in")
    graphscene = NXGraphScene(graph)
    graphscene.setSceneRect(QRectF(-400, -400, 800, 800))
    view.setScene(graphscene)

    graphscene.addItem(GraphicsVertexItem("HWELLO"))

    # show window
    view.show()
    sys.exit(app.exec())
