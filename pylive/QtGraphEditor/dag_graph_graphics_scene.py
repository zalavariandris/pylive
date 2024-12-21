from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from typing import *


class TextWidget(QGraphicsWidget):
    """A simple widget that contains a QGraphicsTextItem."""

    def __init__(self, text, parent=None):
        super().__init__(parent)
        # Create the text item
        self.text_item = QGraphicsTextItem(text, self)
        self.text_item.document().setDocumentMargin(0)
        self.text_item.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextEditorInteraction
        )
        self.text_item.setAcceptedMouseButtons(
            Qt.MouseButton.NoButton
        )  # Transparent to mouse events
        self.text_item.setEnabled(False)

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.set_line_height(1.1)

    def toPlainText(self):
        return self.text_item.toPlainText()

    def setPlainText(self, text: str):
        return self.text_item.setPlainText(text)

    def set_line_height(self, line_height):
        """Set the line height for the text."""
        cursor = QTextCursor(self.text_item.document())
        cursor.select(QTextCursor.SelectionType.Document)

        # Configure block format
        block_format = QTextBlockFormat()
        block_format.setLineHeight(100, 1)
        cursor.mergeBlockFormat(block_format)

    def sizeHint(self, which, constraint=QSizeF()):
        text_size = QSize(self.text_item.document().size().toSize())
        return text_size


class CircleWidget(QGraphicsWidget):
    def __init__(self, radius: float, parent=None):
        super().__init__()
        self.circle_item = QGraphicsEllipseItem(
            QRectF(0, 0, radius * 2, radius * 2), self
        )
        text_color = self.palette().color(QPalette.ColorRole.Text)
        self.circle_item.setBrush(Qt.BrushStyle.NoBrush)
        self.circle_item.setPen(QPen(text_color, 1.4))

    def sizeHint(self, which, constraint=QSizeF()):
        circle_rect = self.circle_item.rect()
        return circle_rect.size()


class PinWidget(QGraphicsWidget):
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
            edge_item.updatePosition()

    def itemChange(self, change, value):
        match change:
            case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
                self.updateEdges()

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
    """A widget that holds multiple TextWidgets arranged in a vertical layout."""

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
            pen.setColor(palette.accent().color())
        painter.setPen(pen)

        # painter.setPen(palette.window().color())
        painter.drawRoundedRect(QRectF(QPointF(), self.size()), 3, 3)

    def destroy(self):
        while self._inlets:
            self._inlets[0].destroy()  # Always remove first

        while self._outlets:
            self._outlets[0].destroy()  # Always remove first

        self.scene().removeItem(self)


class EdgeWidget(QGraphicsLineItem):
    """Graphics item representing an edge (connection)."""

    GrabThreshold = 15

    def __init__(
        self,
        source_outlet: OutletWidget | None,
        target_inlet: InletWidget | None,
        label: str = "-edge-",
    ):
        super().__init__(parent=None)
        assert source_outlet is None or isinstance(
            source_outlet, OutletWidget
        ), f"got: {source_outlet}"
        assert target_inlet is None or isinstance(
            target_inlet, InletWidget
        ), f"got: {target_inlet}"
        self._source_outlet = source_outlet
        self._target_inlet = target_inlet

        if source_outlet:
            source_outlet._edges.append(self)
        if target_inlet:
            target_inlet._edges.append(self)

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

    def setLabelText(self, text: str):
        self._label_item.setPlainText(text)

    def labelText(self):
        return self._label_item.toPlainText()

    def sourceOutlet(self) -> OutletWidget | None:
        return self._source_outlet

    def setSourceOutlet(self, pin: OutletWidget | None):
        assert pin is None or isinstance(pin, OutletWidget), f"got: {pin}"

        # add or remove edge to pin edges for position update
        if pin:
            pin._edges.append(self)
        elif self._source_outlet:
            self._source_outlet._edges.remove(self)

        self._source_outlet = pin
        self.updatePosition()

    def targetInlet(self):
        return self._target_inlet

    def setTargetInlet(self, pin: InletWidget | None):
        assert pin is None or isinstance(pin, InletWidget), f"got: {pin}"

        # add or remove edge to pin edges for position update
        if pin:
            pin._edges.append(self)
        elif self._target_inlet:
            self._target_inlet._edges.remove(self)
        self._target_inlet = pin
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
        # assert self._source_outlet and self._target_inlet
        # if not (
        #   self.scene
        #   and self._source_outlet.scene()
        #   and self._target_inlet.scene()
        # ):
        #   return # dont update position if not in scene or the pins are not part of the same scene

        # assert self.scene() == self._source_outlet.scene() == self._target_inlet.scene()

        line = self.line()
        sourcePin = self._source_outlet
        targetPin = self._target_inlet

        def getConnectionPoint(widget):
            # try:
            #   return widget.getConnectionPoint()
            # except AttributeError:
            return widget.scenePos() + widget.boundingRect().center()

        if sourcePin and targetPin:
            line.setP1(getConnectionPoint(sourcePin))
            line.setP2(getConnectionPoint(targetPin))
            self.setLine(line)
        elif sourcePin:
            line.setP1(getConnectionPoint(sourcePin))
            line.setP2(getConnectionPoint(sourcePin))
            self.setLine(line)
        elif targetPin:
            line.setP1(getConnectionPoint(targetPin))
            line.setP2(getConnectionPoint(targetPin))
            self.setLine(line)
        else:
            return  # nothing to update

    def destroy(self):
        # Safely remove from source pin
        if self._source_outlet:
            try:
                self._source_outlet._edges.remove(self)
            except ValueError:
                pass  # Already removed
            self._source_outlet = None

        # Safely remove from target pin
        if self._target_inlet:
            try:
                self._target_inlet._edges.remove(self)
            except ValueError:
                pass  # Already removed
            self._target_inlet = None

        # Safely remove from scene
        if self.scene():
            self.scene().removeItem(self)


class DAGScene(QGraphicsScene):
    connected = Signal(EdgeWidget)
    disconnected = Signal(EdgeWidget)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create a scene to hold the node and edge graphics
        self.setSceneRect(QRect(-9999 // 2, -9999 // 2, 9999, 9999))

        self.original_edge_pins:None|Tuple[PinWidget, PinWidget] = None
        self.interactive_edge: EdgeWidget | None = None
        self.interactive_edge_fixed_pin: PinWidget | None = None
        self.interactive_edge_moving_pin: PinWidget | None = (
            None  # keep track of original connection
        )
        self.is_dragging_edge = False  # indicate that an edge is being moved

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

    def mousePressEvent(self, event) -> None:
        self.mousePressScenePos = event.scenePos()

        if pin := self.pinAt(event.scenePos()):
            self.initiateConnection(pin)
            event.accept()
            return

        if edge := self.edgeAt(event.scenePos()):
            delta1 = edge.line().p1() - event.scenePos()
            d1 = delta1.manhattanLength()
            delta2 = edge.line().p2() - event.scenePos()
            d2 = delta2.manhattanLength()

            if d1 < d2:
                self.interactive_edge_fixed_pin = edge._target_inlet
                self.interactive_edge_moving_pin = edge._source_outlet
            else:
                self.interactive_edge_fixed_pin = edge._source_outlet
                self.interactive_edge_moving_pin = edge._target_inlet

            self.interactive_edge = edge
            self.is_dragging_edge = False
            event.accept()
            return

        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        GrabThreshold = 15

        if self.interactive_edge and not self.is_dragging_edge:
            mouseDelta = event.scenePos() - self.mousePressScenePos
            IsThresholdSurpassed = mouseDelta.manhattanLength() > GrabThreshold
            if IsThresholdSurpassed:
                self.is_dragging_edge = True
                outlet = self.interactive_edge.sourceOutlet()
                inlet = self.interactive_edge.targetInlet()
                assert outlet, inlet
                self.original_edge_pins = outlet, inlet

        if self.is_dragging_edge and self.interactive_edge:
            self.moveConnection(event.scenePos())
            return

        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Override mouseReleaseEvent to filter events when the mouse is released in the scene.
        """
        if self.is_dragging_edge:
            pin = self.pinAt(event.scenePos())
            self.finishConnection(pin)

        self.is_dragging_edge = False
        self.interactive_edge_fixed_pin = None
        self.interactive_edge = None
        self.interactive_edge_moving_pin = None

        return super().mouseReleaseEvent(event)

    def initiateConnection(self, pin):
        if isinstance(pin, OutletWidget):
            self.interactive_edge = EdgeWidget(
                source_outlet=pin, target_inlet=None
            )
            self.interactive_edge_fixed_pin = pin
        elif isinstance(pin, InletWidget):
            self.interactive_edge = EdgeWidget(
                source_outlet=None, target_inlet=pin
            )
            self.interactive_edge_fixed_pin = pin

        assert self.interactive_edge
        self.interactive_edge.updatePosition()
        self.addItem(self.interactive_edge)
        pen = self.interactive_edge.pen()
        pen.setStyle(Qt.DashLine)
        self.interactive_edge.setPen(pen)
        self.is_dragging_edge = True

    def moveConnection(self, scenepos: QPointF):
        assert isinstance(scenepos, QPointF), f"got: {scenepos}"
        assert self.interactive_edge

        # move free endpoint
        line = self.interactive_edge.line()
        if isinstance(self.interactive_edge_fixed_pin, OutletWidget):
            line.setP2(scenepos)
        elif isinstance(self.interactive_edge_fixed_pin, InletWidget):
            line.setP1(scenepos)
        self.interactive_edge.setLine(line)

        # attach free endpoint to closeby pin
        pinUnderMouse = self.pinAt(scenepos)

        if current_inlet := self.interactive_edge.targetInlet():
            current_inlet.setHighlight(False)
        if current_outlet := self.interactive_edge.sourceOutlet():
            current_outlet.setHighlight(False)

        if isinstance(
            self.interactive_edge_fixed_pin, OutletWidget
        ) and isinstance(pinUnderMouse, InletWidget):
            pinUnderMouse.setHighlight(True)
            self.interactive_edge.setTargetInlet(pinUnderMouse)
            self.interactive_edge.updatePosition()
        elif isinstance(
            self.interactive_edge_fixed_pin, InletWidget
        ) and isinstance(pinUnderMouse, OutletWidget):
            pinUnderMouse.setHighlight(True)
            self.interactive_edge.setSourceOutlet(pinUnderMouse)
            self.interactive_edge.updatePosition()

    def cancelConnection(self):
        assert (
            self.is_dragging_edge
            and self.interactive_edge
            and self.interactive_edge_fixed_pin
        )

        if self.interactive_edge_moving_pin:
            # restore edge pin connections
            if isinstance(self.interactive_edge_moving_pin, InletWidget):
                self.interactive_edge.setTargetInlet(
                    self.interactive_edge_moving_pin
                )
            if isinstance(self.interactive_edge_moving_pin, OutletWidget):
                self.interactive_edge.setSourceOutlet(
                    self.interactive_edge_moving_pin
                )
        else:
            self.interactive_edge.destroy()
            # remove cancelled edge creation

    def canConnect(self, start_pin: PinWidget, end_pin: PinWidget) -> bool:
        # Check if start_pin is an OutletWidget and end_pin is an InletWidget, or vice versa
        if isinstance(start_pin, OutletWidget) and isinstance(
            end_pin, InletWidget
        ):
            return True
        elif isinstance(start_pin, InletWidget) and isinstance(
            end_pin, OutletWidget
        ):
            return True

        # You can add additional checks here (e.g., same node, already connected, etc.)

        return False

    def finishConnection(self, pin: PinWidget | None):
        """this is called after an edge was moved, and dropped somewhere"""
        assert self.interactive_edge_fixed_pin
        assert self.interactive_edge

        start_pin: PinWidget = self.interactive_edge_fixed_pin
        end_pin = pin

        if pin and self.canConnect(start_pin, pin):
            """establish connection"""
            if isinstance(self.interactive_edge_fixed_pin, InletWidget):
                outlet = cast(OutletWidget, pin)
                self.interactive_edge.setSourceOutlet(outlet)
                self.connected.emit(self.interactive_edge)

            elif isinstance(self.interactive_edge_fixed_pin, OutletWidget):
                inlet = cast(InletWidget, pin)
                self.interactive_edge.setTargetInlet(inlet)
                self.connected.emit(self.interactive_edge)
        else:
            """remove interactive edge"""
            if self.original_edge_pins is not None:
                self.disconnected.emit(self.interactive_edge)
            else: # if edge creation was cancelled
                self.interactive_edge.destroy()

        self.interactive_edge = None
        self.interactive_edge_fixed_pin = None
        self.original_edge_pins = None


if __name__ == "__main__":

    class GraphView(QGraphicsView):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("DAGScene example")
            self.setRenderHint(QPainter.RenderHint.Antialiasing)
            self.setInteractive(True)
            self.setDragMode(
                QGraphicsView.DragMode.RubberBandDrag
            )  # optional, default mouse behaviour

        def contextMenuEvent(self, event: QContextMenuEvent) -> None:
            # Create the context menu
            context_menu = QMenu(self)

            # Add actions to the context menu
            delete_selection_action = QAction("delete selection", self)
            context_menu.addAction(delete_selection_action)
            delete_selection_action.triggered.connect(self.deleteSelectedNodes)

            create_node_action = QAction("create node", self)
            context_menu.addAction(create_node_action)
            clickpos = self.mapToScene(event.pos())
            create_node_action.triggered.connect(
                lambda: self.createNode(clickpos)
            )

            horizontal_orientation_action = QAction(
                f"horizontal orientation", self
            )
            context_menu.addAction(horizontal_orientation_action)
            horizontal_orientation_action.triggered.connect(
                self.flipOrientation
            )

            flip_orientation_action = QAction(f"flip orientation", self)
            context_menu.addAction(flip_orientation_action)
            flip_orientation_action.triggered.connect(self.flipOrientation)

            # Show the context menu at the position of the mouse event
            context_menu.exec(event.globalPos())

        def setOrientation(self):
            graphscene = cast(DAGScene, self.scene())
            for item in graphscene.items():
                if isinstance(item, NodeWidget):
                    node = cast(NodeWidget, item)
                    if node.orientation() == Qt.Orientation.Vertical:
                        node.setOrientation(Qt.Orientation.Horizontal)
                    elif node.orientation() == Qt.Orientation.Horizontal:
                        node.setOrientation(Qt.Orientation.Vertical)

        def flipOrientation(self):
            graphscene = cast(DAGScene, self.scene())
            for item in graphscene.items():
                if isinstance(item, NodeWidget):
                    node = cast(NodeWidget, item)
                    if node.orientation() == Qt.Orientation.Vertical:
                        node.setOrientation(Qt.Orientation.Horizontal)
                    elif node.orientation() == Qt.Orientation.Horizontal:
                        node.setOrientation(Qt.Orientation.Vertical)

        def createNode(self, scenepos=QPointF(0, 0), /):
            graphscene = cast(DAGScene, self.scene())
            node = NodeWidget("<new node>")
            node.setPos(scenepos)
            graphscene.addNode(node)
            node.addInlet(InletWidget("in"))
            node.addOutlet(OutletWidget("out"))

        def deleteSelectedNodes(self):
            for node in (
                item
                for item in self.scene().selectedItems()
                if isinstance(item, NodeWidget)
            ):
                node.destroy()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # setup main window
    window = QWidget()
    mainLayout = QVBoxLayout()
    mainLayout.setContentsMargins(0, 0, 0, 0)
    window.setLayout(mainLayout)
    graphview = QGraphicsView()
    mainLayout.addWidget(graphview)

    # create graph scene
    graphscene = DAGScene()
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

    # set nodes orientation
    for node in (
        item for item in graphscene.items() if isinstance(item, NodeWidget)
    ):
        node.setOrientation(Qt.Orientation.Vertical)

    # show window
    window.show()
    sys.exit(app.exec())
