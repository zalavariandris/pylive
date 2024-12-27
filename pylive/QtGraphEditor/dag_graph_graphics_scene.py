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
    def __init__(self, type:QEvent.Type, source:'NodeWidget'):
        super().__init__( type )
        self._type = type
        self._source = source

    def source(self):
        return self._source

    def __str__(self):
        return f"ConnectionEvent({self._source})"


class Connection(QObject):
    targetChanged = Signal()
    def __init__(self, source:'NodeWidget', parent=None):
        super().__init__(parent=parent)
        self._source = source
        self._loop = QEventLoop()

        self._arrow = None
        self._target:QGraphicsItem|None = None
        self._entered_items = []

    def source(self)->QGraphicsItem:
        return self._source

    def target(self)->QGraphicsItem|None:
        return self._target

    def exec(self):
        scene = self._source.scene()
        assert scene
        
        self._arrow = QGraphicsArrowItem(QLineF(self._source.pos(), self._source.pos()))
        self._arrow.setPen(QPen(scene.palette().color(QPalette.ColorRole.Text), 1))
        self._source.scene().addItem(self._arrow )
        scene.installEventFilter(self)
        self._loop.exec()
        scene.removeEventFilter(self)
        self._source.scene().removeItem(self._arrow)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.GraphicsSceneMouseMove:
            event = cast(QGraphicsSceneMouseEvent, event)

            ### Move arrow ####
            assert self._arrow
            line = makeLineBetweenShapes(self.source(), event.scenePos())
            self._arrow.setLine(line)
            
            # manage connection enter and leave event
            scene = self._source.scene()
            entered_items = [item for item in self._entered_items]
            itemsUnderMouse = [item for item in scene.items(event.scenePos()) if hasattr(item, 'connectionEnterEvent')]
            for item in itemsUnderMouse:
                if item not in entered_items:
                    self._entered_items.append(item)
                    event = ConnectionEvent(ConnectionEnterType, self._source)
                    scene.sendEvent(item, event)
                    if event.isAccepted():
                        self._target = item
                        self.targetChanged.emit()
                        break

            for item in entered_items:
                if item not in itemsUnderMouse:
                    self._entered_items.remove(item)
                    event = ConnectionEvent(ConnectionLeaveType, self._source)
                    scene.sendEvent(item, event)

            # send ConnectionMove event
            for item in self._entered_items:
                event = ConnectionEvent(ConnectionMoveType, self._source)
                scene.sendEvent(item, event)

            return True

        if event.type() == QEvent.Type.GraphicsSceneMouseRelease:
            
            if self._target:
                scene = self._source.scene()
                event = ConnectionEvent(ConnectionDropType, self._source)
                scene.sendEvent(self._target, event)
            self._loop.exit()
            return True
        return super().eventFilter(watched, event)


class PinWidget(QGraphicsItem):
    sceneGeometryChanged = Signal()
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

    def itemChange(self, change, value):
        match change:
            case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
                for edge in self._edges:
                    edge.updatePosition()

        return super().itemChange(change, value)

    def destroy(self):
        for edge in reversed(self._edges):
            edge.destroy()
        self._edges = []

        if self._parent_node:
            self._parent_node.removeOutlet(self)
        self.scene().removeItem(self)

    def boundingRect(self) -> QRectF:
        return QRectF(-self.radius, -self.radius, self.radius*2, self.radius*2)

    def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem, widget=None):
        palette:QPalette = option.palette #type: ignore
        state = option.state #type: ignore

        print("PinWidget->paint", state)

        # Check the item's state
        baseColor = palette.base().color()
        baseColor.setAlpha(255)
        brush = QBrush(baseColor)
        pen = QPen(palette.text().color())
        if state & QStyle.StateFlag.State_MouseOver:
            pen.setColor(palette.brightText().color())  # Color for hover
        elif state & QStyle.StateFlag.State_Selected:
            pen.setColor(palette.accent().color())  # Color for selected

        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(0,0), self.radius, self.radius)


class OutletWidget(PinWidget):
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        print("PinWidget->mousePressEvent")
        # the default implementation of QGraphicsItem::mousePressEvent() ignores the event
        # docs: https://www.qtcentre.org/threads/21256-QGraphicsItem-no-mouse-events-called

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        print("PinWidget->mouseMoveEvent")
        if QLineF(event.screenPos(), event.buttonDownScreenPos(Qt.MouseButton.LeftButton)).length() < QApplication.startDragDistance():
            return
        print("start drag event")

        # start connection
        connection = Connection(self)
        connection.exec()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        print("PinWidget->mouseReleaseEvent")
        return super().mouseReleaseEvent(event)


class InletWidget(PinWidget):
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
        print("connection enter")
        if True:
            event.setAccepted(True)
            self._is_hovered = True
            self.update()
            return
        event.setAccepted(False)

    def connectionMoveEvent(self, event:ConnectionEvent)->None:
        print("connection move")

    def connectionLeaveEvent(self, event:ConnectionEvent)->None:
        print("connection leave")
        self._is_hovered = False
        self.update()
    
    def connectionDropEvent(self, event:ConnectionEvent):
        if True:
            print(f"connection dropped from: {event.source()} onto: {self}!")
            event.setAccepted(True)
            graphscene = cast(DAGScene, self.scene())
            edge = EdgeWidget(event._source, self)
            graphscene.addEdge(edge)

        event.setAccepted(False)


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

    def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem, widget=None):
        palette:QPalette = option.palette #type: ignore
        state = option.state #type: ignore
        print("NodeWidget->paint", state)
        # Check the item's state

        baseColor = palette.base().color()
        baseColor.setAlpha(255)
        brush = QBrush(baseColor)
        pen = QPen(palette.dark().color(), 1)
        # if state & QStyle.StateFlag.State_MouseOver:
        #     pen.setColor( palette.brightText().color() )
        if state & QStyle.StateFlag.State_Selected:
            pen.setColor( palette.accent().color() )

        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawRoundedRect(self.boundingRect(), 4, 4)
        
        pen = QPen(palette.text().color(), 1)
        painter.setPen(pen)
        fm = QFontMetrics( self.scene().font() )
        painter.drawText(4,fm.height()-1,self._title)

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

        return super().itemChange(change, value)

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

    def removeInlet(self, inlet: InletWidget):
        inlet._parent_node = None
        inlet.scene().removeItem(inlet)
        self._inlets.remove(inlet)
        self.updatePins()

    def addOutlet(self, outlet: OutletWidget):
        outlet._parent_node = self
        outlet.setParentItem(self)
        self._outlets.append(outlet)
        self.updatePins()

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
    GrabThreshold = 15
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


        self.is_moving_endpoint = False
        self.GrabThreshold = 10
        self._shape_pen = QPen(Qt.GlobalColor.black, self.GrabThreshold)

        self.setSource(source)
        self.setTarget(target)

        self.setAcceptHoverEvents(True)

    def highlightColor(self):
        return self.scene().palette().color(QPalette.ColorRole.Accent)

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
        self._shape_pen.setCosmetic(True)
        path = QPainterPath()
        path.moveTo(self.line().p1())
        path.lineTo(self.line().p2())
        stroker = QPainterPathStroker()
        stroker.setWidth(self.GrabThreshold)
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        return stroker.createStroke(path)

    def boundingRect(self) -> QRectF:
        """Override boundingRect to account for the wider collision shape."""
        self._shape_pen = QPen(Qt.GlobalColor.black, self.GrabThreshold)
        extra = (self._shape_pen.width() + self.pen().width()) / 2.0
        p1 = self.line().p1()
        p2 = self.line().p2()
        return (
            QRectF(p1, QSizeF(p2.x() - p1.x(), p2.y() - p1.y()))
            .normalized()
            .adjusted(-extra, -extra, extra, extra)
        )

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

    # def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem, widget=None):
    #     palette:QPalette = option.palette #type: ignore
    #     state = option.state #type: ignore

    #     # Check the item's state
    #     if state & QStyle.StateFlag.State_MouseOver:
    #         painter.setBrush(palette.brightText().color())  # Color for hover
    #     elif state & QStyle.StateFlag.State_Selected:
    #         painter.setBrush(palette.accent().color())  # Color for selected
    #     else:
    #         painter.setBrush(palette.text().color())  # Default color

    #     arrow_shape = makeArrowShape(self.line(), 1.0)
    #     painter.setPen(Qt.NoPen)
    #     painter.drawPath(arrow_shape)
    #     painter.drawLine(self.line())

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        gradient = QLinearGradient(self.line().p1(), self.line().p2())

        d1 = (self.line().p1() - event.scenePos() ).manhattanLength() # TODO: measure distance in line item local space
        d2 = (self.line().p2() - event.scenePos() ).manhattanLength()
        if d1>d2:
            gradient.setColorAt(0.0, self.scene().palette().text().color())
            gradient.setColorAt(1.0, self.scene().palette().brightText().color())
        else:
            gradient.setColorAt(0.0, self.scene().palette().brightText().color())
            gradient.setColorAt(1.0, self.scene().palette().text().color())

        self.setPen(QPen(gradient, 1))
        # event.accept()

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        print("hoverMoveEvent")
        gradient = QLinearGradient(self.line().p1(), self.line().p2())

        d1 = (self.line().p1() - event.scenePos() ).manhattanLength() # TODO: measure distance in line item local space
        d2 = (self.line().p2() - event.scenePos() ).manhattanLength()
        print(d1, d2)
        if d1>d2:
            gradient.setColorAt(0.0, self.scene().palette().text().color())
            gradient.setColorAt(1.0, self.scene().palette().brightText().color())
        else:
            gradient.setColorAt(0.0, self.scene().palette().brightText().color())
            gradient.setColorAt(1.0, self.scene().palette().text().color())

        self.setPen(QPen(gradient, 1))

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self.setPen( QPen(self.scene().palette().text().color(), 1) )
        # return super().hoverLeaveEvent(event)


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
