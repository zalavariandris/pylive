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


class ConnectionEvent(QGraphicsSceneEvent):
    def __init__(self, type:QEvent.Type, source:object|None=None):
        super().__init__( type )
        self._type = type
        self._source = source

    def source(self)->QGraphicsItem:
        """graphics item initiated the event"""
        return self._source

    def __str__(self):
        return f"ConnectionEvent({self._source})"


class Connect(QObject):
    targetChanged = Signal()

    def __init__(self, item: 'QGraphicsItem', direction: Literal['forward', 'backward'] = 'forward', parent=None):
        super().__init__(parent=parent)
        self._source: QGraphicsItem|None = item if direction == 'forward' else None
        self._target: QGraphicsItem|None = item if direction == 'backward' else None
        self._direction = direction

        self._loop = QEventLoop()
        self._arrow = None
        self._active_item: QGraphicsItem = item
        self._entered_items = []

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
        self._loop.exec()
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
                    assert self._target
                    line = makeLineBetweenShapes(event.scenePos(), self._target)
            assert line
            self._arrow.setLine(line)

            # manage connection enter and leave event
            scene = self._active_item.scene()
            entered_items = [item for item in self._entered_items]
            itemsUnderMouse = [item for item in scene.items(event.scenePos()) if hasattr(item, 'connectionEnterEvent')]

            for item in itemsUnderMouse:
                if item not in entered_items:
                    self._entered_items.append(item)
                    connection_event_source = self._source if self._direction == 'forward' else self._target
                    event = ConnectionEvent(ConnectionEnterType, connection_event_source)
                    scene.sendEvent(item, event)
                    if event.isAccepted():
                        if self._direction == 'forward':
                            self._target = item
                        else:
                            self._source = item
                        self.targetChanged.emit()
                        break

            for item in entered_items:
                if item not in itemsUnderMouse:
                    self._entered_items.remove(item)
                    connection_event_source = self._source if self._direction == 'forward' else self._target
                    event = ConnectionEvent(ConnectionLeaveType, connection_event_source)
                    scene.sendEvent(item, event)

            # send ConnectionMove event
            for item in self._entered_items:
                connection_event_source = self._source if self._direction == 'forward' else self._target
                event = ConnectionEvent(ConnectionMoveType, connection_event_source)
                scene.sendEvent(item, event)

            return True

        if event.type() == QEvent.Type.GraphicsSceneMouseRelease:
            if self._direction == 'forward' and self._target or self._direction == 'backward' and self._source:
                scene = self._active_item.scene()
                connection_event_source = self._source if self._direction == 'forward' else self._target
                event = ConnectionEvent(ConnectionDropType, connection_event_source)
                scene.sendEvent(self._target if self._direction == 'forward' else self._source, event)
            self._loop.exit()
            return True

        return super().eventFilter(watched, event)



class PinWidget(QGraphicsItem):
    def __init__(self, text:str, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        # store relations
        self._parent_node: NodeWidget | None = None
        self._edges = []

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)
        self.radius = 3.5
        self._isHighlighted = False

    def destroy(self):
        for edge in reversed(self._edges):
            edge.destroy()
        self._edges = []

        if self._parent_node:
            self._parent_node.removeOutlet(self)
        self.scene().removeItem(self)

    def itemChange(self, change, value):
        match change:
            case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
                for edge in self._edges:
                    edge.updatePosition()

        return super().itemChange(change, value)

    def shape(self):
        r = self.radius+3
        path = QPainterPath()
        path.addEllipse(QPointF(), r, r)
        return path

    def boundingRect(self) -> QRectF:
        r = self.radius+3
        return QRectF(-r, -r, r*2, r*2)

    def pen(self):
        palette = QApplication.instance().palette()
        if self.scene():
            palette = self.scene().palette()

        pen = QPen(palette.text().color())
        

        if self.isSelected() or self.parentItem().isSelected():
            pen.setColor(palette.highlight().color())  # Color for selected

        if self.isHighlighted():
            pen.setColor(palette.accent().color())  # Color for hover

        return pen

    def brush(self):
        palette = QApplication.instance().palette()
        if self.scene():
            palette = self.scene().palette()

        baseColor = palette.base().color()
        baseColor.setAlpha(255)
        brush = QBrush(baseColor)
        return brush

    def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem, widget=None):
        # Check the item's state
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawEllipse(QPointF(0,0), self.radius, self.radius)

        # painter.drawPath(self.shape())
        # painter.drawRect(self.boundingRect())

    def setHighlighted(self, value):
        self._isHighlighted = value
        self.update()

    def isHighlighted(self):
        return self._isHighlighted

    def hoverEnterEvent(self, event):
        self.setHighlighted(True)

    def hoverLeaveEvent(self, event):
        self.setHighlighted(False)


class OutletWidget(PinWidget):
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        event.accept()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if QLineF(event.screenPos(), event.buttonDownScreenPos(Qt.MouseButton.LeftButton)).length() < QApplication.startDragDistance():
            return
        print("start drag event")

        # start connection
        connect = Connect(self)
        connect.exec()
        
        graphscene = cast(DAGScene, self.scene())
        if connect.target():
            edge = EdgeWidget(connect.source(), connect.target())
            graphscene.addEdge(edge)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        return super().mouseReleaseEvent(event)

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
        inlet = event.source()
        if inlet.parentItem()!=self.parentItem():
            event.setAccepted(True)
            self.setHighlighted(True)
            return
        event.setAccepted(False)

    def connectionLeaveEvent(self, event:ConnectionEvent)->None:
        self.setHighlighted(False)

    def connectionMoveEvent(self, event:ConnectionEvent)->None:
        ...
    
    def connectionDropEvent(self, event:ConnectionEvent):
        if event.source().parentItem()!=self.parentItem():
            self.setHighlighted(False)
            event.setAccepted(True)

        event.setAccepted(False)


class InletWidget(PinWidget):
    ...
    # def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
    #     event.accept()

    # def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
    #     if QLineF(event.screenPos(), event.buttonDownScreenPos(Qt.MouseButton.LeftButton)).length() < QApplication.startDragDistance():
    #         return
    #     print("start drag event")

    #     # start connection
    #     connect = Connect(self, direction='backward')
    #     connect.exec()
        
    #     graphscene = cast(DAGScene, self.scene())
    #     if connect.source():
    #         edge = EdgeWidget(connect.source(), connect.target())
    #         graphscene.addEdge(edge)

    # def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
    #     return super().mouseReleaseEvent(event)

    # @override
    # def sceneEvent(self, event: QEvent) -> bool:
    #     if event.type() == ConnectionEnterType:
    #         self.connectionEnterEvent(cast(ConnectionEvent, event))
    #     elif event.type() == ConnectionLeaveType:
    #         self.connectionLeaveEvent(cast(ConnectionEvent, event))
    #     elif event.type() == ConnectionMoveType:
    #         self.connectionMoveEvent(cast(ConnectionEvent, event))
    #     elif event.type() == ConnectionDropType:
    #         self.connectionDropEvent(cast(ConnectionEvent, event))
    #     else:
    #         ...

    #     return super().sceneEvent(event)

    # def connectionEnterEvent(self, event:ConnectionEvent) -> None:
    #     outlet = event.source()
    #     if outlet.parentItem()!=self.parentItem():
    #         event.setAccepted(True)
    #         self.setHighlighted(True)
    #         return
    #     event.setAccepted(False)

    # def connectionLeaveEvent(self, event:ConnectionEvent)->None:
    #     self.setHighlighted(False)

    # def connectionMoveEvent(self, event:ConnectionEvent)->None:
    #     ...
    
    # def connectionDropEvent(self, event:ConnectionEvent):
    #     if event.source().parentItem()!=self.parentItem():
    #         self.setHighlighted(False)
    #         event.setAccepted(True)

    #     event.setAccepted(False)


class NodeWidget(QGraphicsItem):
    """A widget that holds multiple TextWidgets arranged in a layout."""
    def __init__(
        self,
        title="Node",
        parent=None,
    ):
        super().__init__(parent)
        self._title = title
        # Enable selection and movement
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsFocusable, True)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)

        # Define the bounding geometry
        self._inlets:List[InletWidget] = []
        self._outlets:List[OutletWidget] = []
        self._edges:List[EdgeWidget] = []

    def boundingRect(self) -> QRectF:
        try:
            fm = QFontMetrics( self.scene().font() )
        except AttributeError:
            fm = QFontMetrics(QApplication.instance().font())

        text_width = fm.horizontalAdvance(self._title)
        text_height = fm.height()
        return QRectF(0,0,text_width+8, text_height+4)

    def destroy(self):
        while self._inlets:
            self._inlets[0].destroy()  # Always remove first

        while self._outlets:
            self._outlets[0].destroy()  # Always remove first

        self.scene().removeItem(self)

    def itemChange(self, change, value):
        match change:
            case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
                for edge in self._edges:
                    edge.updatePosition()
            case QGraphicsItem.GraphicsItemChange.ItemSceneHasChanged:
                self.updatePins()
            case QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
                for pin in self._inlets+self._outlets:
                    pin.update()

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

        pen = QPen(palette.dark().color(), 1)

        if self.isSelected():
            pen.setColor( palette.highlight().color() )
        return pen

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

    def addInlet(self, inlet: InletWidget):
        inlet._parent_node = self
        inlet.setParentItem(self)
        self._inlets.append(inlet)
        self.updatePins()
        if self.scene():
            inlet.installSceneEventFilter(self)

    def removeInlet(self, inlet: InletWidget):
        inlet._parent_node = None
        inlet.scene().removeItem(inlet)
        self._inlets.remove(inlet)
        self.updatePins()
        inlet.removeSceneEventFilter(self)

    def addOutlet(self, outlet: OutletWidget):
        outlet._parent_node = self
        outlet.setParentItem(self)
        self._outlets.append(outlet)
        self.updatePins()
        outlet.installSceneEventFilter(self)

    def removeOutlet(self, outlet: OutletWidget):
        outlet._parent_node = None
        self._outlets.remove(outlet)
        outlet.scene().removeItem(outlet)
        self.updatePins()

    def updatePins(self):
        inletCount = len(self._inlets)
        for idx, inlet in enumerate(self._inlets):
            inlet.setPos(idx/inletCount+(inletCount-1)/2*self.boundingRect().width()+self.boundingRect().width()/2, 0)

        outletCount = len(self._outlets)
        for idx, outlet in enumerate(self._outlets):
            outlet.setPos(idx/outletCount+(outletCount-1)/2*self.boundingRect().width()+self.boundingRect().width()/2, self.boundingRect().height())


class EdgeWidget(QGraphicsLineItem):
    """Graphics item representing an edge in a graph."""
    def __init__(
        self,
        source: OutletWidget | NodeWidget | None,
        target: InletWidget | NodeWidget | None,
        label: str = "-edge-",
    ):
        super().__init__(parent=None)

        self._source = None
        self._target = None
    

        self.setPen(QPen(Qt.GlobalColor.black, 1))
        self._label_item = QGraphicsTextItem(label, parent=self)
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

    def source(self) -> OutletWidget | NodeWidget | None:
        return self._source

    def setSource(self, source: OutletWidget | NodeWidget | None):
        assert source is None or hasattr(source, '_edges'), f"got: {source}"
        if self._source:
            self._source._edges.remove(self)
        if source:
            source._edges.append(self)
        self._source = source
        self.updatePosition()

    def target(self)->InletWidget | NodeWidget | None:
        return self._target

    def setTarget(self, target: InletWidget | NodeWidget | None):
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

    def destroy(self):
        # Safely remove from source pin
        if self._source:
            try:
                self._source._edges.remove(self)
            except ValueError:
                pass  # Already removed
            self._source_outlet = None

        # Safely remove from target pin
        if self._target:
            try:
                self._target._edges.remove(self)
            except ValueError:
                pass  # Already removed
            self._target = None

        # Safely remove from scene
        if self.scene():
            self.scene().removeItem(self)

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

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        event.accept()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        print("PinWidget->mouseMoveEvent")
        if QLineF(event.screenPos(), event.buttonDownScreenPos(Qt.MouseButton.LeftButton)).length() < QApplication.startDragDistance():
            return
        print("start drag event from edge")

        # # start connection
        d1 = QLineF(self.line().p1(), event.scenePos()).length()
        d2 = QLineF(self.line().p2(), event.scenePos()).length()

        self.hide()
        if d1>d2:
            connect = Connect(self.source())
            connect.exec()
            if not connect.target():
                graphscene = cast(DAGScene, self.scene())
                graphscene.removeEdge(self)
            elif connect.target() != self.target():
                self.setTarget(connect.target())
        else:
            ...
        self.show()


class DAGScene(QGraphicsScene):
    connected = Signal(EdgeWidget) # source, target
    disconnected = Signal(EdgeWidget)  # edge
    edgeDropped = Signal(EdgeWidget, object, object) # source, target

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create am 'infinite' scene to hold the node and edge graphics
        self.setSceneRect(QRect(-9999 // 2, -9999 // 2, 9999, 9999))

    def addNode(self, node: NodeWidget):
        self.addItem(node)

    def removeNode(self, node: NodeWidget):
        node.destroy()

    def addEdge(self, edge: EdgeWidget):
        self.addItem(edge)

    def removeEdge(self, edge: EdgeWidget):
        edge.destroy()

    def pinAt(self, pos: QPoint | QPointF) -> PinWidget | None:
        for item in self.items(pos, deviceTransform=QTransform()):
            if isinstance(item, PinWidget):
                return item
        return None

    def nodeAt(self, pos: QPoint | QPointF) -> NodeWidget | None:
        for item in self.items(pos, deviceTransform=QTransform()):
            if isinstance(item, NodeWidget):
                return item
        return None

    def edgeAt(self, pos: QPoint | QPointF) -> EdgeWidget | None:
        for item in self.items(pos, deviceTransform=QTransform()):
            if isinstance(item, EdgeWidget):
                return item
        return None


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # setup main window
    window = QWidget()
    window.setWindowTitle("DAGScene")
    mainLayout = QVBoxLayout()
    mainLayout.setContentsMargins(0, 0, 0, 0)
    window.setLayout(mainLayout)
    graphview = QGraphicsView()
    graphview.setRenderHint(QPainter.Antialiasing, True)
    graphview.setRenderHint(QPainter.TextAntialiasing, True)
    graphview.setRenderHint(QPainter.SmoothPixmapTransform, True)
    mainLayout.addWidget(graphview)

    # create graph scene
    graphscene = DAGScene()
    graphscene.edgeDropped.connect(lambda edge, source, target: print("edge dropped"))
    graphscene.setSceneRect(QRectF(-400, -400, 800, 800))
    graphview.setScene(graphscene)

    # Create nodes
    read_text_node = NodeWidget("Read Text")
    outlet = OutletWidget("text out")
    read_text_node.addOutlet(outlet)
    graphscene.addNode(read_text_node)
    read_text_node.moveBy(-70, -70)

    convert_node = NodeWidget("Markdown2Html")
    inlet = InletWidget("Markdown in")
    convert_node.addInlet(inlet)
    convert_node.addOutlet(OutletWidget("HTML out"))
    graphscene.addNode(convert_node)
    convert_node.moveBy(0, 0)

    write_text_node = NodeWidget("Write Text")
    write_text_node.addInlet(InletWidget("text in"))
    graphscene.addNode(write_text_node)
    write_text_node.moveBy(70, 100)

    # create edge1
    edge1 = EdgeWidget(outlet, inlet)
    graphscene.addEdge(edge1)

    # show window
    window.show()
    sys.exit(app.exec())
