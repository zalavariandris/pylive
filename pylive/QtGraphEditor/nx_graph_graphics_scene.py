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
    QGraphicsArrowItem, makeArrowShape
)

ConnectionEnterType = QEvent.Type( QEvent.registerEventType() )
ConnectionLeaveType = QEvent.Type( QEvent.registerEventType() )
ConnectionMoveType  = QEvent.Type( QEvent.registerEventType() )
ConnectionDropType  = QEvent.Type( QEvent.registerEventType() )

import numpy as np
import networkx as nx



class ConnectionEvent(QGraphicsSceneEvent):
    def __init__(self, type:QEvent.Type, source:QGraphicsItem):
        super().__init__( type )
        self._type = type
        self._source = source

    def source(self)->QGraphicsItem:
        """graphics item initiated the event"""
        return self._source

    def __str__(self):
        return f"ConnectionEvent({self._source})"


@final
class Connect(QObject):
    targetChanged = Signal()

    def __init__(self, item: 'QGraphicsItem', direction: Literal['forward', 'backward'] = 'forward', parent:QObject|None=None):
        super().__init__(parent=parent)
        self._source: QGraphicsItem = item
        self._target:QGraphicsItem|None = None

        self._direction:Literal['forward', 'backward'] = direction

        self._loop = QEventLoop()
        self._arrow = None
        self._active_item: QGraphicsItem = item
        self._entered_items:list[QGraphicsItem] = []

    def source(self) -> QGraphicsItem|None:
        return self._source

    def target(self) -> QGraphicsItem | None:
        return self._target

    def exec(self):
        scene = self._active_item.scene()
        assert scene

        self._arrow = QGraphicsArrowItem(QLineF(self._active_item.pos(), self._active_item.pos()))
        self._arrow.setPen(QPen(scene.palette().color(QPalette.ColorRole.Text), 1))
        scene.addItem(self._arrow)
        scene.installEventFilter(self)
        _ = self._loop.exec()
        scene.removeEventFilter(self)
        scene.removeItem(self._arrow)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.GraphicsSceneMouseMove:
            event = cast(QGraphicsSceneMouseEvent, event)

            ### Move arrow ####
            assert self._arrow
            match self._direction:
                case 'forward':
                    assert self._source
                    line = makeLineBetweenShapes(self._source, event.scenePos())
                case 'backward':
                    assert self._source
                    line = makeLineBetweenShapes(event.scenePos(), self._source)
            assert line
            self._arrow.setLine(line)

            # manage connection enter and leave event
            scene = self._active_item.scene()
            entered_items = [item for item in self._entered_items]
            itemsUnderMouse = [item for item in scene.items(event.scenePos()) if hasattr(item, 'connectionEnterEvent')]

            for item in itemsUnderMouse:
                if item not in entered_items:
                    self._entered_items.append(item)
                    event = ConnectionEvent(ConnectionEnterType, self._source)
                    _ = scene.sendEvent(item, event)
                    if event.isAccepted():
                        self._target = item
                        self.targetChanged.emit()
                        break

            for item in entered_items:
                if item not in itemsUnderMouse:
                    self._entered_items.remove(item)
                    event = ConnectionEvent(ConnectionLeaveType, self._source)
                    _=scene.sendEvent(item, event)
            if self._target and self._target not in self._entered_items:
                self._target = None
                self.targetChanged.emit()

            # send ConnectionMove event
            for item in self._entered_items:
                event = ConnectionEvent(ConnectionMoveType, self._source)
                _=scene.sendEvent(item, event)

            return True

        if event.type() == QEvent.Type.GraphicsSceneMouseRelease:
            if self._target:
                _=scene = self._active_item.scene()
                event = ConnectionEvent(ConnectionDropType, self._source)
                _=scene.sendEvent(self._target, event)
            self._loop.exit()
            return True

        return super().eventFilter(watched, event)


class NodeWidget(QGraphicsItem):
    """A widget that holds multiple TextWidgets arranged in a layout."""
    def __init__(
        self,
        title:str="Node",
        parent:QGraphicsItem|None=None,
    ):
        super().__init__(parent)
        # private variables
        self._title:str = title
        self._isHighlighted:bool = False
        self._edges:list[EdgeWidget] = []

        # Enable selection and movement
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsFocusable, True)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)

    def __str__(self):
        return f"{self.__class__.__name__}({self._title})"

    @override
    def boundingRect(self) -> QRectF:
        try:
            fm = QFontMetrics( self.scene().font() )
        except AttributeError:
            fm = QFontMetrics(QApplication.instance().font())

        text_width = fm.horizontalAdvance(self._title)
        text_height = fm.height()
        return QRectF(0,0,text_width+8, text_height+4)

    @override
    def itemChange(self, change:QGraphicsItem.GraphicsItemChange, value):
        match change:
            case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
                for edge in self._edges:
                    edge.updatePosition()
            case _:
                return super().itemChange(change, value)

    def brush(self):
        palette = QApplication.instance().palette()
        if self.scene():
            palette = self.scene().palette()

        baseColor = palette.base().color()
        baseColor.setAlpha(255)
        brush = QBrush(baseColor)
        return brush

    def pen(self):
        palette = QApplication.instance().palette()
        if self.scene():
            palette = self.scene().palette()

        pen = QPen(palette.text().color())
        
        if self.isSelected():
            pen.setColor(palette.highlight().color())  # Color for selected

        if self.isHighlighted():
            pen.setColor(palette.accent().color())  # Color for hover

        return pen

    def setHighlighted(self, value):
        self._isHighlighted = value
        self.update()

    def isHighlighted(self):
        return self._isHighlighted

    def hoverEnterEvent(self, event):
        self.setHighlighted(True)

    def hoverLeaveEvent(self, event):
        self.setHighlighted(False)

    def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem, widget=None):
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRoundedRect(self.boundingRect(), 4, 4)
        
        fm = QFontMetrics( self.scene().font() )
        painter.drawText(4,fm.height()-1,self._title)

    def title(self):
        return self._title

    def setTitle(self, text: str):
        self._title = text
        self.update()

    @override
    def sceneEvent(self, event: QEvent) -> bool:
        if event.type() == ConnectionEnterType:
            self.connectionEnterEvent(cast(ConnectionEvent, event))
        elif event.type() == ConnectionLeaveType:
            self.connectionLeaveEvent(cast(ConnectionEvent, event))
        elif event.type() == ConnectionMoveType:
            self.connectionMoveEvent(cast(ConnectionEvent, event))
        elif event.type() == ConnectionDropType:
            self.connectionDropEvent(cast(ConnectionEvent, event))
        else:
            ...

        return super().sceneEvent(event)

    def connectionEnterEvent(self, event:ConnectionEvent) -> None:
        if event.source()!=self:
            event.setAccepted(True)
            self.setHighlighted(True)
            return
        event.setAccepted(False)

    def connectionLeaveEvent(self, event:ConnectionEvent)->None:
        self.setHighlighted(False)

    def connectionMoveEvent(self, event:ConnectionEvent)->None:
        ...
    
    def connectionDropEvent(self, event:ConnectionEvent):
        if event.source()!=self:
            self.setHighlighted(False)
            event.setAccepted(True)

        event.setAccepted(False)


class EdgeWidget(QGraphicsLineItem):
    """Graphics item representing an edge in a graph."""
    def __init__(
        self,
        source: QGraphicsItem | None,
        target: QGraphicsItem | None,
        label: str = "-edge-",
    ):
        super().__init__(parent=None)

        self._source:QGraphicsItem|None = None
        self._target:QGraphicsItem|None = None
    

        self.setPen(QPen(Qt.GlobalColor.black, 1))
        self._label_item = QGraphicsTextItem(label, parent=self)
        self._label_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.updatePosition()

        # Enable selecting
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        self.setZValue(-1)

        # self.is_moving_endpoint = False
        self.setSource(source)
        self.setTarget(target)

        self.setAcceptHoverEvents(True)

    def setLabelText(self, text: str):
        self._label_item.setPlainText(text)

    def labelText(self):
        return self._label_item.toPlainText()

    def source(self) -> QGraphicsItem | None:
        return self._source

    def setSource(self, source: QGraphicsItem | None):
        assert source is None or hasattr(source, '_edges'), f"got: {source}"
        if self._source:
            self._source._edges.remove(self)
        if source:
            source._edges.append(self)
        self._source = source
        self.updatePosition()

    def target(self)->QGraphicsItem | None:
        return self._target

    def setTarget(self, target: QGraphicsItem | None):
        assert target is None or hasattr(target, '_edges'), f"got: {target}"
        if self._target:
            self._target._edges.remove(self)
        if target:
            target._edges.append(self)
        self._target = target
        self.updatePosition()

    def shape(self) -> QPainterPath:
        """Override shape to provide a wider clickable area."""
        path = QPainterPath()
        path.moveTo(self.line().p1())
        path.lineTo(self.line().p2())
        stroker = QPainterPathStroker()
        stroker.setWidth(10)
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        return stroker.createStroke(path)

    def boundingRect(self) -> QRectF:
        return self.shape().boundingRect()

    @overload
    def setLine(self, line: QLine | QLineF) -> None:
        ...

    @overload
    def setLine(self, x1: float, y1: float, x2: float, y2: float) -> None:
        ...

    def setLine(self, *args: QLine | QLineF | float) -> None:
        # Implementing the logic
        if len(args) == 1 and isinstance(args[0], (QLine, QLineF)):
            line = args[0]
            super().setLine(line)
        elif len(args) == 4 and all(isinstance(arg, float) for arg in args):
            x1, y1, x2, y2 = args
            super().setLine(x1, y1, x2, y2)
        else:
            super().setLine(*args)

        self._label_item.setPos(self.line().center())

    def updatePosition(self):
        line = self.line()
        source = self._source
        target = self._target

        def getConnectionPoint(widget):
            # try:
            #   return widget.getConnectionPoint()
            # except AttributeError:
            return widget.scenePos() + widget.boundingRect().center()

        if source and target:
            line.setP1(getConnectionPoint(source))
            line.setP2(getConnectionPoint(target))
            self.setLine( makeLineBetweenShapes(source, target) )
        elif source:
            line.setP1(getConnectionPoint(source))
            line.setP2(getConnectionPoint(source))
            self.setLine(line)
        elif target:
            line.setP1(getConnectionPoint(target))
            line.setP2(getConnectionPoint(target))
            self.setLine(line)
        else:
            return  # nothing to update

    def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem, widget=None):
        palette:QPalette = option.palette #type: ignore
        state = option.state #type: ignore

        # Check the item's state
        pen = Qt.NoPen
        brush = QBrush(palette.text().color())
        if state & QStyle.StateFlag.State_MouseOver:
            brush.setColor(palette.accent().color())  # Color for hover
        elif state & QStyle.StateFlag.State_Selected:
            brush.setColor(palette.highlight().color())  # Color for selected

        arrow_shape = makeArrowShape(self.line(), 1.0)
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawPath(arrow_shape)
        painter.drawLine(self.line())


class NXGraphScene(QGraphicsScene):
    connected = Signal(EdgeWidget) # source, target
    disconnected = Signal(EdgeWidget)  # edge
    reconnected = Signal(EdgeWidget)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create am 'infinite' scene to hold the node and edge graphics
        self.setSceneRect(QRect(-9999 // 2, -9999 // 2, 9999, 9999))
        self._nodes:set[NodeWidget] = set()
        self._edges:set[EdgeWidget] = set()

    def addNode(self, node: NodeWidget):
        self._nodes.add(node)
        self.addItem(node)

    def removeNode(self, node: NodeWidget, remove_connected_nodes=True):
        if remove_connected_nodes:
            for edge in node._edges:
                self.removeItem(edge)
        self._nodes.remove(node)
        self.removeItem(node)

    def addEdge(self, edge: EdgeWidget):
        self._edges.add(edge)
        self.addItem(edge)

    def removeEdge(self, edge: EdgeWidget):
        self._edges.remove(edge)
        self.removeItem(edge)

    def nodeAt(self, pos: QPoint | QPointF) -> NodeWidget | None:
        for item in self.items(pos, deviceTransform=QTransform()):
            if item in self._nodes:
                return item
        return None

    def edgeAt(self, pos: QPoint | QPointF) -> EdgeWidget | None:
        for item in self.items(pos, deviceTransform=QTransform()):
            if item in self._edges:
                return item
        return None

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self._buttonDownItem = self.itemAt(event.buttonDownScenePos(Qt.MouseButton.LeftButton), QTransform())
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.buttons()==Qt.MouseButton.LeftButton:
            if item:=self._buttonDownItem:
                if event.modifiers()==Qt.KeyboardModifier.AltModifier and item in self._nodes:
                    if QLineF(event.screenPos(), event.buttonDownScreenPos(Qt.MouseButton.LeftButton)).length() < QApplication.startDragDistance():
                        return

                    # start connection
                    connect = Connect(item)
                    connect.exec()
                    
                    if connect.target():
                        edge = EdgeWidget(connect.source(), connect.target())
                        # self.addEdge(edge)
                        self.connected.emit(edge)
                    return

                elif item in self._edges:
                    edge = item
                    scene = self
                    if QLineF(event.screenPos(), event.buttonDownScreenPos(Qt.MouseButton.LeftButton)).length() < QApplication.startDragDistance():
                        return

                    # # start connection
                    d1 = QLineF(edge.line().p1(), event.buttonDownScenePos(Qt.MouseButton.LeftButton)).length()
                    d2 = QLineF(edge.line().p2(), event.buttonDownScenePos(Qt.MouseButton.LeftButton)).length()

                    edge.hide()
                    if d1>d2:
                        connect = Connect(edge.source())
                        connect.exec()
                        if not connect.target():
                            graphscene = cast(NXGraphScene, scene)
                            # graphscene.removeEdge(edge)
                            self.disconnected.emit(edge)
                        elif connect.target() != edge.target():
                            # self.removeEdge(edge)
                            self.disconnected.emit(edge)
                            new_edge = EdgeWidget(connect.source(), connect.target())
                            # self.addEdge(new_edge)
                            self.connected.emit(new_edge)
                    else:
                        connect = Connect(edge.target(), direction='backward')
                        connect.exec()
                        if not connect.target():
                            graphscene = cast(NXGraphScene, scene)
                            self.disconnected.emit(edge)
                            # graphscene.removeEdge(edge)
                        elif connect.target() != edge.source():
                            # self.removeEdge(edge)
                            self.disconnected.emit(edge)
                            new_edge = EdgeWidget(connect.target(), connect.source())
                            # self.addEdge(new_edge)
                            self.connected.emit(new_edge)
                    edge.show()
                    return
        
        super().mouseMoveEvent(event)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # setup main window
    window = QWidget()
    window.setWindowTitle("NXGraphScene")
    mainLayout = QVBoxLayout()
    mainLayout.setContentsMargins(0, 0, 0, 0)
    window.setLayout(mainLayout)
    graphview = QGraphicsView()
    graphview.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    graphview.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    graphview.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    mainLayout.addWidget(graphview)

    # create graph scene
    graphscene = NXGraphScene()
    graphscene.connected.connect(lambda edge: graphscene.addEdge(edge))
    graphscene.disconnected.connect(lambda edge: graphscene.removeEdge(edge))
    graphscene.setSceneRect(QRectF(-400, -400, 800, 800))
    graphview.setScene(graphscene)

    # Create nodes
    read_text_node = NodeWidget("Read Text")
    graphscene.addNode(read_text_node)
    read_text_node.moveBy(-70, -70)

    convert_node = NodeWidget("Markdown2Html")
    graphscene.addNode(convert_node)
    convert_node.moveBy(0, 0)

    write_text_node = NodeWidget("Write Text")
    graphscene.addNode(write_text_node)
    write_text_node.moveBy(70, 100)

    # create edge1
    edge1 = EdgeWidget(read_text_node, convert_node)
    graphscene.addEdge(edge1)

    # show window
    window.show()
    sys.exit(app.exec())
