from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.QtGraphEditor.text_widget import TextWidget
from pylive.QtGraphEditor.circle_widget import CircleWidget




class PinWidget(QGraphicsWidget):
    sceneGeometryChanged = Signal()
    def __init__(self, text, orientation=Qt.Orientation.Horizontal):
        super().__init__()
        # store relations
        self._parent_node: NodeWidget | None = None
        self._edges = []

        # Setup widgets
        self.setAcceptHoverEvents(True)
        self.circle_item = CircleWidget(radius=3)
        self.text_widget = TextWidget(text)
        font = self.text_widget.text_item.document().defaultFont()
        font.setPointSize(6)
        self.text_widget.text_item.document().setDefaultFont(font)

        # layout
        self.main_layout = QGraphicsLinearLayout(Qt.Orientation.Horizontal)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(3)
        self.setLayout(self.main_layout)
        self.setOrientation(orientation)

        # update edge on scenepos or geometry change

        self.geometryChanged.connect(self.updateEdges)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )

    def setOrientation(self, orientation: Qt.Orientation):
        match orientation:
            case Qt.Orientation.Vertical:
                self.main_layout.setOrientation(orientation)
                self.main_layout.removeItem(self.text_widget)
                self.text_widget.hide()
                if isinstance(self, OutletWidget):
                    self.text_widget.moveBy(3, +10)
                else:
                    self.text_widget.moveBy(3, -13)

                self._orientation = orientation

            case Qt.Orientation.Horizontal:
                self.main_layout.setOrientation(orientation)
                if isinstance(self, OutletWidget):
                    self.main_layout.insertItem(0, self.text_widget)
                else:
                    self.main_layout.addItem(self.text_widget)
                self.text_widget.show()
                self._orientation = orientation
            case _:
                ...

        self.updateGeometry()
        self.adjustSize()

    def setHighlight(self, value):
        if value:
            accent_color = self.palette().color(QPalette.ColorRole.Accent)
            self.circle_item.circle_item.setPen(QPen(accent_color, 2))
        else:
            text_color = self.palette().color(QPalette.ColorRole.Text)
            self.circle_item.circle_item.setPen(QPen(text_color, 2))

    def updateEdges(self):
        for edge_item in list(self._edges):
            pass
            # edge_item.updatePosition()

    def itemChange(self, change, value):
        match change:
            case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
                self.sceneGeometryChanged.emit()
                # self.updateEdges()

        return super().itemChange(change, value)

    def shape(self):
        shape = QPainterPath()
        circle_rect = self.circle_item.rect()
        circle_rect.adjust(-5, -5, 5, 5)
        circle_rect.translate(self.circle_item.pos())
        shape.addRect(circle_rect)
        return shape

    def boundingRect(self) -> QRectF:
        return self.shape().boundingRect()

    def orientation(self):
        return self._orientation

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self.setHighlight(True)
        if self.orientation() == Qt.Orientation.Vertical:
            self.text_widget.show()
        return super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self.setHighlight(False)
        if self.orientation() == Qt.Orientation.Vertical:
            self.text_widget.hide()
        return super().hoverLeaveEvent(event)

    # def paint(self, painter, option, widget):
    #   painter.setPen('green')
    #   painter.drawRect(self.boundingRect())
    #   painter.setPen('cyan')
    #   painter.drawPath(self.shape())


class OutletWidget(PinWidget):
    def __init__(
        self, text: str, orientation: Qt.Orientation = Qt.Orientation.Horizontal
    ):
        super().__init__(text, orientation)
        self.main_layout.addItem(self.text_widget)
        self.main_layout.addItem(self.circle_item)
        self.main_layout.setAlignment(
            self.circle_item, Qt.AlignmentFlag.AlignCenter
        )

    def destroy(self):
        for edge in reversed(self._edges):
            edge.destroy()
        self._edges = []

        if self._parent_node:
            self._parent_node.removeOutlet(self)
        self.scene().removeItem(self)


class InletWidget(PinWidget):
    def __init__(
        self, text: str, orientation: Qt.Orientation = Qt.Orientation.Horizontal
    ):
        super().__init__(text, orientation)
        self.main_layout.addItem(self.circle_item)
        self.main_layout.addItem(self.text_widget)
        self.main_layout.setAlignment(
            self.circle_item, Qt.AlignmentFlag.AlignCenter
        )

    def destroy(self):
        for edge in reversed(self._edges):
            edge.destroy()
        self._edges = []

        if self._parent_node:
            self._parent_node.removeInlet(self)
        self._parent_node = None
        self.scene().removeItem(self)


class NodeWidget(QGraphicsWidget):
    """A widget that holds multiple TextWidgets arranged in a layout."""
    sceneGeometryChanged = Signal()
    def __init__(
        self,
        title="Node",
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
        parent=None,
    ):
        super().__init__(parent)

        # Enable selection and movement
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsFocusable, True)

        self._orientation = Qt.Orientation.Horizontal

        # Create a layout
        self.main_layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)
        self.main_layout.setContentsMargins(8, 3, 8, 3)
        self.main_layout.setSpacing(0)

        # create heading
        self.header = TextWidget(title)
        self.main_layout.addItem(self.header)
        self._badges_layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)
        self.main_layout.addItem(self._badges_layout)

        # Create inlets layout
        self.inlets_layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)
        self.main_layout.addItem(self.inlets_layout)

        # create outlets layout
        self.outlets_layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)
        self.main_layout.addItem(self.outlets_layout)
        self.main_layout.setAlignment(
            self.outlets_layout, Qt.AlignmentFlag.AlignRight
        )

        # Set the layout for the widget
        self.setLayout(self.main_layout)
        self.setOrientation(orientation)

        # Define the bounding geometry
        # self.setGeometry(QRectF(-75, -59, 150, 100))
        self._inlets = []
        self._outlets = []

        self.geometryChanged.connect(self.sceneGeometryChanged)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )

        self.setAcceptDrops(True)

    def itemChange(self, change, value):
        match change:
            case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
                self.sceneGeometryChanged.emit()
                # self.updateEdges()

        return super().itemChange(change, value)

    def title(self):
        return self.header.toPlainText()

    def setTitle(self, text: str):
        self.header.setPlainText(text)

    def orientation(self):
        return self._orientation

    def setOrientation(self, orientation: Qt.Orientation):
        match orientation:
            case Qt.Orientation.Vertical:
                # Set orientation for inlets and outlets
                self.inlets_layout.setOrientation(orientation)
                self.outlets_layout.setOrientation(orientation)
                # self.inlets_layout.setMaximumHeight(1)
                # self.outlets_layout.setMaximumHeight(1)

                # Update orientation for child items

                for i in range(self.inlets_layout.count()):
                    item = cast(InletWidget, self.inlets_layout.itemAt(i))
                    item.setOrientation(orientation)

                for i in range(self.outlets_layout.count()):
                    item = cast(OutletWidget, self.outlets_layout.itemAt(i))
                    item.setOrientation(orientation)

                    # Clear and reorder main_layout: inlets, header, outlets
                while self.main_layout.count() > 0:
                    self.main_layout.removeAt(0)

                self.main_layout.addItem(self.inlets_layout)
                self.main_layout.addItem(self.header)
                self.main_layout.addItem(self.outlets_layout)

                # Align items
                self.main_layout.setAlignment(
                    self.inlets_layout, Qt.AlignmentFlag.AlignCenter
                )
                self.main_layout.setAlignment(
                    self.outlets_layout, Qt.AlignmentFlag.AlignCenter
                )

                self._orientation = orientation

            case Qt.Orientation.Horizontal:
                # Update orientation for inlets and outlets
                self.inlets_layout.setOrientation(orientation)
                self.outlets_layout.setOrientation(orientation)

                for i in range(self.inlets_layout.count()):
                    item = cast(InletWidget, self.inlets_layout.itemAt(i))
                    item.setOrientation(orientation)

                for i in range(self.outlets_layout.count()):
                    item = cast(OutletWidget, self.outlets_layout.itemAt(i))
                    item.setOrientation(orientation)

                # Clear and reorder main_layout: header, inlets, outlets
                while self.main_layout.count() > 0:
                    self.main_layout.removeAt(0)

                self.main_layout.addItem(self.header)
                self.main_layout.addItem(self.inlets_layout)
                self.main_layout.addItem(self.outlets_layout)

                # Align items
                self.main_layout.setAlignment(
                    self.inlets_layout, Qt.AlignmentFlag.AlignLeft
                )
                self.main_layout.setAlignment(
                    self.outlets_layout, Qt.AlignmentFlag.AlignRight
                )

                self._orientation = orientation
            case _:
                ...

        self.adjustSize()

    def addInlet(self, inlet: InletWidget):
        self.inlets_layout.addItem(inlet)
        self.inlets_layout.setAlignment(inlet, Qt.AlignmentFlag.AlignLeft)
        inlet._parent_node = self
        inlet.setParentItem(self)
        self._inlets.append(inlet)

    def removeInlet(self, inlet: InletWidget):
        self.inlets_layout.removeItem(inlet)
        inlet._parent_node = None
        self._inlets.remove(inlet)

    def addOutlet(self, outlet: OutletWidget):
        self.outlets_layout.addItem(outlet)
        self.outlets_layout.setAlignment(outlet, Qt.AlignmentFlag.AlignRight)
        outlet._parent_node = self
        outlet.setParentItem(self)
        self._outlets.append(outlet)

    def removeOutlet(self, outlet: OutletWidget):
        self.outlets_layout.removeItem(outlet)
        outlet._parent_node = None
        self._outlets.remove(outlet)

    def addBadge(self, badge:str|QGraphicsWidget):
        if isinstance(badge, str):
            badge = TextWidget(badge)
        self._badges_layout.addItem(badge)

    def setHighlight(self, value):
        ...

    def paint(
        self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None
    ):
        # Draw the node rectangle
        palette: QPalette = option.palette  # type: ignore
        state: QStyle.StateFlag = option.state  # type: ignore

        painter.setBrush(palette.window())
        # painter.setBrush(Qt.NoBrush)
 
        pen = QPen(palette.text().color(), 1)
        pen.setCosmetic(True)
        pen.setWidthF(1)
        if state & QStyle.StateFlag.State_Selected:
            pen.setWidthF(2)
            pen.setColor(palette.accent().color())
        painter.setPen(pen)

        # painter.setPen(palette.window().color())
        painter.drawRoundedRect(QRectF(QPointF(), self.size()), 10, 10)

    def destroy(self):
        while self._inlets:
            self._inlets[0].destroy()  # Always remove first

        while self._outlets:
            self._outlets[0].destroy()  # Always remove first

        self.scene().removeItem(self)

    def dragEnterEvent(self, event):
        # if event.direction == "backward" and isinstance(event.target, OutletWidget):
        event.setAccepted(True)

    def dropEvent(self, event: QGraphicsSceneDragDropEvent) -> None:
        return super().dropEvent(event)

    @override
    def dragLeaveEvent(self, event):
        print("leave")

    # def connectionLeaveEvent(self, event):
    #     pass


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
        assert source is None or hasattr(
            source, 'sceneGeometryChanged'
        ), f"got: {source}"
        assert target is None or hasattr(
            target, 'sceneGeometryChanged'
        ), f"got: {target}"
        self._source = None
        self._target = None
    

        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self._label_item = QGraphicsTextItem(label, parent=self)
        self.updatePosition()

        # Enable selecting
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        self.setZValue(-1)

        pen = QPen(QApplication.instance().palette().text().color(), 2)
        pen.setCosmetic(True)
        pen.setWidthF(1)

        self.setPen(pen)

        self.is_moving_endpoint = False
        self.GrabThreshold = 10
        self._shape_pen = QPen(Qt.GlobalColor.black, self.GrabThreshold)

        self.setSource(source)
        self.setTarget(target)

    def setLabelText(self, text: str):
        self._label_item.setPlainText(text)

    def labelText(self):
        return self._label_item.toPlainText()

    def source(self) -> OutletWidget | NodeWidget | None:
        return self._source

    def setSource(self, source: OutletWidget | NodeWidget | None):
        assert source is None or hasattr(source, 'sceneGeometryChanged'), f"got: {source}"

        # add or remove edge to pin edges for position update
        if source:
            # pin._edges.append(self)
            source.sceneGeometryChanged.connect(self.updatePosition)
            print("listen to source geometry changes")
        if self._source:
            self._source.sceneGeometryChanged.disconnect(self.updatePosition)
            # self._source_outlet._edges.remove(self)
            print("unlisten to source geometry changes")

        self._source = source
        self.updatePosition()

    def target(self)->InletWidget | NodeWidget | None:
        return self._target

    def setTarget(self, target: InletWidget | NodeWidget | None):
        assert target is None or hasattr(target, 'sceneGeometryChanged'), f"got: {target}"

        # add or remove edge to pin edges for position update
        if target:
            # target._edges.append(self)
            target.sceneGeometryChanged.connect(self.updatePosition)
            print("listen to target geometry changes")
        elif self._target:
            self._target.sceneGeometryChanged.disconnect(self.updatePosition)
            # self._target_inlet._edges.remove(self)
            print("unlisten to target geometry changes")
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
        print("Edge: updatePosition")
        # assert self._source_outlet and self._target_inlet
        # if not (
        #   self.scene
        #   and self._source_outlet.scene()
        #   and self._target_inlet.scene()
        # ):
        #   return # dont update position if not in scene or the pins are not part of the same scene

        # assert self.scene() == self._source_outlet.scene() == self._target_inlet.scene()

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
            self.setLine(line)
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


from dataclasses import dataclass
@dataclass
class ConnectionEvent:
    direction:Literal['forward', 'backward']
    edge: EdgeWidget
    source:OutletWidget|NodeWidget|None
    target:InletWidget|NodeWidget|None
    scenePos:QPointF



class MouseTool(QObject):
    ...

class PinConnectionTool(MouseTool):
    def __init__(self, dagscene: 'DAGScene') -> None:
        super().__init__(parent=dagscene)

        # handle mouse dragging events
        self._drag_threshold = 5
        self._mouse_is_dragging = False # indicate that the mouse is pressed, (press and move has passed the drag threeshold) and dragging.
        
        # handle connection events
        self._current_connection_event:ConnectionEvent|None = None
        
        dagscene.installEventFilter(self)
        self._dagscene = dagscene

        self.loop = QEventLoop()

    def eventFilter(self, watched:QObject, event:QEvent):
        # """
        # Override eventFilter to handle connections
        # """
        if watched == self._dagscene:
            match event.type():
                case QEvent.Type.GraphicsSceneMousePress:
                    mousePressEvent = cast(QGraphicsSceneMouseEvent, event)
                    if mousePressEvent.button() == Qt.MouseButton.LeftButton:
                        self.mousePressScenePos = mousePressEvent.scenePos()

                        if pin := self._dagscene.pinAt(mousePressEvent.scenePos()):
                            ## Start connection from Pin
                            match pin:
                                case OutletWidget():
                                    connectionEvent = ConnectionEvent(
                                        source=pin,
                                        target=None,
                                        direction="forward",
                                        edge=EdgeWidget(source=pin, target=None),
                                        scenePos=mousePressEvent.scenePos()
                                    )

                                case InletWidget():
                                    connectionEvent = ConnectionEvent(
                                        source=None,
                                        target=pin,
                                        direction="backward",
                                        edge=EdgeWidget(source=None, target=pin),
                                        scenePos=mousePressEvent.scenePos()
                                    )
                                case _:
                                    raise ValueError()
                            self._dagscene.addItem(connectionEvent.edge)
                            self._current_connection_event = connectionEvent
                            self.connectionStartEvent(connectionEvent)
                            mousePressEvent.accept()
                            return True

                        elif edge := self._dagscene.edgeAt(mousePressEvent.scenePos()):
                            ## Start connection from Edge
                            delta1 = edge.line().p1() - mousePressEvent.scenePos()
                            d1 = delta1.manhattanLength()
                            delta2 = edge.line().p2() - mousePressEvent.scenePos()
                            d2 = delta2.manhattanLength()

                            if d1 < d2:
                                connectionEvent = ConnectionEvent(
                                    source=edge.source(),
                                    target=edge.target(),
                                    direction="backward",
                                    edge=edge,
                                    scenePos=mousePressEvent.scenePos()
                                )
                            else:
                                connectionEvent = ConnectionEvent(
                                    source=edge.source(),
                                    target=edge.target(),
                                    direction="forward",
                                    edge=edge,
                                    scenePos=mousePressEvent.scenePos()
                                )

                            self.connectionStartEvent(connectionEvent)
                            self._current_connection_event = connectionEvent
                            event.accept()
                            return True

                case QEvent.Type.GraphicsSceneMouseMove:
                    mouseMoveEvent = cast(QGraphicsSceneMouseEvent, event)
                    if self._mouse_is_dragging == False:
                        mouseDelta = mouseMoveEvent.scenePos() - mouseMoveEvent.buttonDownScenePos(Qt.MouseButton.LeftButton)
                        IsThresholdSurpassed = mouseDelta.manhattanLength() > self._drag_threshold
                        if IsThresholdSurpassed:
                            self._mouse_is_dragging = True
                            if edge:=self._dagscene.edgeAt(mouseMoveEvent.buttonDownScenePos(Qt.MouseButton.LeftButton)):
                                assert self._current_connection_event is None
                                ## start connection from existing edge
                                delta1 = edge.line().p1() - mouseMoveEvent.scenePos()
                                d1 = delta1.manhattanLength()
                                delta2 = edge.line().p2() - mouseMoveEvent.scenePos()
                                d2 = delta2.manhattanLength()

                                if d1 < d2:
                                    connectionEvent = ConnectionEvent(
                                        source=edge.source(),
                                        target=edge.target(),
                                        direction="backward",
                                        edge=edge,
                                        scenePos=mouseMoveEvent.scenePos()
                                    )
                                else:
                                    connectionEvent = ConnectionEvent(
                                        source=edge.source(),
                                        target=edge.target(),
                                        direction="forward",
                                        edge=edge,
                                        scenePos=mouseMoveEvent.scenePos()
                                    )
                                self.connectionStartEvent(connectionEvent)
                                self._current_connection_event = connectionEvent
                                mouseMoveEvent.accept()
                                return True

                    if self._mouse_is_dragging and mouseMoveEvent.buttons()==Qt.MouseButton.LeftButton:
                        if self._current_connection_event:
                            connectionEvent = self._current_connection_event
                            connectionEvent.scenePos = mouseMoveEvent.scenePos()
                            self.connectionMoveEvent(connectionEvent)
                            return True

                case QEvent.Type.GraphicsSceneMouseRelease:
                    mouseReleaseEvent = cast(QGraphicsSceneMouseEvent, event)
                    if self._mouse_is_dragging and self._current_connection_event:
                        connectionEvent = self._current_connection_event
                        connectionEvent.scenePos = mouseReleaseEvent.scenePos()
                        self.connectionDropEvent(connectionEvent)
                        self._current_connection_event = None

                        self._mouse_is_dragging = False
                        mouseReleaseEvent.accept()
                        return True

        return super().eventFilter(watched, event)

    def connectionStartEvent(self, event: ConnectionEvent):
        event.edge.updatePosition()
        pen = event.edge.pen()
        pen.setStyle(Qt.DashLine)
        event.edge.setPen(pen)

    def connectionMoveEvent(self, event: ConnectionEvent):
        # Move free endpoint
        line = event.edge.line()
        match event.direction:
            case 'forward':
                line.setP2(event.scenePos)
            case 'backward':
                line.setP1(event.scenePos)
        event.edge.setLine(line)

        # Attach free endpoint to closeby items
        if pin:=self._dagscene.pinAt(event.scenePos):
            #todo: highlight pin
            match event.direction:
                case 'forward':
                    event.edge.setTarget(pin)
                case 'backward':
                    event.edge.setSource(pin)

    def connectionDropEvent(self, event:ConnectionEvent):
        """this is called after an edge was moved, and dropped somewhere"""
        match event.direction:
            case 'forward':
                target = self._dagscene.pinAt(event.scenePos) or None
                self._dagscene.edgeDropped.emit(event.edge, event.edge.source(), target)
            case 'backward':
                source = self._dagscene.pinAt(event.scenePos) or None
                self._dagscene.edgeDropped.emit(event.edge, source, event.edge.target())

        # restore moved edge connection
        if event.source and event.target:
            event.edge.setSource(event.source)
            event.edge.setTarget(event.target)
        else:
            self._dagscene.removeItem(event.edge)

    def exec(self):

        self.loop.exec()


class NodeConnectionTool(QObject):
    def __init__(self, dagscene: 'DAGScene') -> None:
        super().__init__(parent=dagscene)

        # handle mouse dragging events
        self._drag_threshold = 5
        self._mouse_is_dragging = False # indicate that the mouse is pressed, (press and move has passed the drag threeshold) and dragging.
        
        # handle connection events
        self._current_connection_event:ConnectionEvent|None = None
        
        dagscene.installEventFilter(self)
        self._dagscene = dagscene

    def eventFilter(self, watched:QObject, event:QEvent):
        # """
        # Override eventFilter to handle connections
        # """
        if watched == self._dagscene:
            match event.type():
                case QEvent.Type.GraphicsSceneMousePress:
                    mousePressEvent = cast(QGraphicsSceneMouseEvent, event)
                    if mousePressEvent.button() == Qt.MouseButton.LeftButton:
                        self.mousePressScenePos = mousePressEvent.scenePos()
                        if node:=self._dagscene.nodeAt(mousePressEvent.scenePos()):
                            connectionEvent = ConnectionEvent(
                                source=node,
                                target=None,
                                direction="forward",
                                edge=EdgeWidget(source=node, target=None),
                                scenePos=mousePressEvent.scenePos()
                            )
                            self._dagscene.addItem(connectionEvent.edge)
                            self._current_connection_event = connectionEvent
                            self.connectionStartEvent(connectionEvent)
                            mousePressEvent.accept()
                            return True

                case QEvent.Type.GraphicsSceneMouseMove:
                    mouseMoveEvent = cast(QGraphicsSceneMouseEvent, event)
                    if self._mouse_is_dragging == False:
                        mouseDelta = mouseMoveEvent.scenePos() - mouseMoveEvent.buttonDownScenePos(Qt.MouseButton.LeftButton)
                        IsThresholdSurpassed = mouseDelta.manhattanLength() > self._drag_threshold
                        if IsThresholdSurpassed:
                            self._mouse_is_dragging = True
                            if edge:=self._dagscene.edgeAt(mouseMoveEvent.buttonDownScenePos(Qt.MouseButton.LeftButton)):
                                assert self._current_connection_event is None
                                delta1 = edge.line().p1() - mouseMoveEvent.scenePos()
                                d1 = delta1.manhattanLength()
                                delta2 = edge.line().p2() - mouseMoveEvent.scenePos()
                                d2 = delta2.manhattanLength()

                                if d1 < d2:
                                    connectionEvent = ConnectionEvent(
                                        source=edge.source(),
                                        target=edge.target(),
                                        direction="backward",
                                        edge=edge,
                                        scenePos=mouseMoveEvent.scenePos()
                                    )
                                else:
                                    connectionEvent = ConnectionEvent(
                                        source=edge.source(),
                                        target=edge.target(),
                                        direction="forward",
                                        edge=edge,
                                        scenePos=mouseMoveEvent.scenePos()
                                    )
                                self.connectionStartEvent(connectionEvent)
                                self._current_connection_event = connectionEvent
                                mouseMoveEvent.accept()
                                return True

                    if self._mouse_is_dragging and mouseMoveEvent.buttons()==Qt.MouseButton.LeftButton:
                        if self._current_connection_event:
                            connectionEvent = self._current_connection_event
                            connectionEvent.scenePos = mouseMoveEvent.scenePos()
                            self.connectionMoveEvent(connectionEvent)
                            return True

                case QEvent.Type.GraphicsSceneMouseRelease:
                    mouseReleaseEvent = cast(QGraphicsSceneMouseEvent, event)
                    if self._mouse_is_dragging and self._current_connection_event:
                        connectionEvent = self._current_connection_event
                        connectionEvent.scenePos = mouseReleaseEvent.scenePos()
                        self.connectionDropEvent(connectionEvent)
                        self._current_connection_event = None

                    self._mouse_is_dragging = False
                    mouseReleaseEvent.accept()
                    return True

        return super().eventFilter(watched, event)


    def connectionStartEvent(self, event: ConnectionEvent):
        event.edge.updatePosition()
        pen = event.edge.pen()
        pen.setStyle(Qt.DashLine)
        event.edge.setPen(pen)

    def connectionMoveEvent(self, event: ConnectionEvent):
        # Move free endpoint
        line = event.edge.line()
        match event.direction:
            case 'forward':
                line.setP2(event.scenePos)
            case 'backward':
                line.setP1(event.scenePos)
        event.edge.setLine(line)

        # Attach free endpoint to closeby items

        if node:=self._dagscene.nodeAt(event.scenePos):
            #todo: highlight node
            match event.direction:
                case 'forward':
                    event.edge.setTarget(node)
                case 'backward':
                    event.edge.setSource(node)

    def connectionDropEvent(self, event:ConnectionEvent):
        """this is called after an edge was moved, and dropped somewhere"""
        match event.direction:
            case 'forward':
                target = self._dagscene.pinAt(event.scenePos) or self._dagscene.nodeAt(event.scenePos) or None
                self._dagscene.edgeDropped.emit(event.edge, event.edge.source(), target)
            case 'backward':
                source = self._dagscene.pinAt(event.scenePos) or self._dagscene.nodeAt(event.scenePos) or None
                self._dagscene.edgeDropped.emit(event.edge, source, event.edge.target())

        # restore moved edge connection
        if event.source and event.target:
            event.edge.setSource(event.source)
            event.edge.setTarget(event.target)
        else:
            self._dagscene.removeItem(event.edge)

    def canConnect(self, start_pin: PinWidget, end_pin: PinWidget) -> bool:
        # todo: implemenmt connection allowed
        ...


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

class DropTarget(QGraphicsWidget):
    ...

class DraggableItem(QGraphicsWidget):
    def __init__(self, parent:QGraphicsRectItem=None):
        super().__init__(parent=parent)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setGeometry(0,0,100,100)

        self._dragline:QGraphicsLineItem|None = None

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if QLineF(event.screenPos(), event.buttonDownScreenPos(Qt.MouseButton.LeftButton)).length() < QApplication.startDragDistance():
            return

        # Start dtrag
        view = cast(QGraphicsView, event.widget())
        drag = QDrag(view)
        mime = QMimeData()
        drag.setMimeData(mime)

        QApplication.instance().installEventFilter(self)
        line = QLineF(self.boundingRect().center(), self.boundingRect().center())
        self._dragline = QGraphicsLineItem(line)
        self.scene().addItem(self._dragline)
        
        drag.exec()
        self.scene().removeItem(self._dragline)
        self._dragline = None
        QApplication.instance().removeEventFilter(self)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # print(event)
        if event.type() == QEvent.Type.DragMove:
            # print("drag move event")
            ...
        if event.type() == QEvent.Type.GraphicsSceneDragMove:
            # print("mouse move event")
            dragMoveEvent = cast(QGraphicsSceneDragDropEvent, event)
            line = self._dragline.line()
            line.setP2(dragMoveEvent.scenePos())
            self._dragline.setLine(line)
            self.update()

        return super().eventFilter(watched, event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.setCursor(Qt.CursorShape.OpenHandCursor);

    def paint(self, painter:QPainter, option: QStyleOptionGraphicsItem, widget: QWidget|None=None):
        painter.setBrush(QBrush("purple"))
        painter.drawRect(self.geometry())



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
    mainLayout.addWidget(graphview)

    # create graph scene
    graphscene = DAGScene()
    graphscene.edgeDropped.connect(lambda edge, source, target: print("edge dropped"))
    graphscene.setSceneRect(QRectF(-400, -400, 800, 800))
    draggable_rect = DraggableItem()
    graphscene.addItem(draggable_rect)
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

    # set nodes orientation
    for node in (
        item for item in graphscene.items() if isinstance(item, NodeWidget)
    ):
        node.setOrientation(Qt.Orientation.Vertical)

    # show window
    window.show()
    sys.exit(app.exec())
