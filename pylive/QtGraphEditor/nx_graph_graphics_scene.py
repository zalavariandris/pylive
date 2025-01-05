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
    QGraphicsArrowItem, makeArrowShape
)

ConnectionEnterType = QEvent.Type( QEvent.registerEventType() )
ConnectionLeaveType = QEvent.Type( QEvent.registerEventType() )
ConnectionMoveType  = QEvent.Type( QEvent.registerEventType() )
ConnectionDropType  = QEvent.Type( QEvent.registerEventType() )

import numpy as np
import networkx as nx



class ConnectionEvent(QGraphicsSceneEvent):
    """
    the property accepted is set to False by default.
    """
    def __init__(self, type:QEvent.Type, source:QGraphicsItem):
        super().__init__( type )
        self._type = type
        self._source = source
        # by default QEvents are set to accepted.
        # for connection event set this to False
        # https://doc.qt.io/qt-6/qevent.html#accepted-prop
        self.setAccepted(False)

    def source(self)->QGraphicsItem:
        """graphics item initiated the event"""
        return self._source

    def _type_name(self):
        if self._type == ConnectionEnterType:
            return "ConnectionEnterType"
        if self._type == ConnectionLeaveType:
            return "ConnectionLeaveType"
        if self._type == ConnectionMoveType :
            return "ConnectionMoveType" 
        if self._type == ConnectionDropType :
            return "ConnectionDropType" 

    def __str__(self):
        return f"ConnectionEvent({self._type_name()})"


class MouseTool(QObject):
    def __init__(self):
        self._loop = QEventLoop()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        ...

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        ...

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        ...

    def keyPressEvent(self, event: QKeyEvent) -> None:
        ...

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        ...


@final
class Connect(QObject):
    """
    source: the widget the connection was initiated by.
    direction: the arrow direction. 
      _forward_ points to the _target_.
      _backward_ points to the _source_.
    """

    targetChanged = Signal()
    """signal to notify when the drop target has changed"""

    def __init__(self, source: 'QGraphicsItem', direction: Literal['forward', 'backward'] = 'forward', parent:QObject|None=None):
        super().__init__(parent=parent)
        self._source: QGraphicsItem = source
        self._target:QGraphicsItem|None = None

        self._direction:Literal['forward', 'backward'] = direction

        self._loop = QEventLoop() # event loop to capture all events while executing this tool
        self._arrow = None # the arrow QGraphicsItem
        self._entered_items:list[QGraphicsItem] = [] # keep track of entered items

    def __str__(self):
        return f"Connect({self.source()},{self.target()})"

    def source(self) -> QGraphicsItem|None:
        """the widget the connection was initiated by."""
        return self._source

    def target(self) -> QGraphicsItem | None:
        """the actual drop target if any"""
        return self._target

    def exec(self):
        """initiate connection, and enter the eventloop"""
        scene = self._source.scene()
        assert scene

        self._arrow = QGraphicsArrowItem(QLineF(self._source.pos(), self._source.pos()))
        self._arrow.setPen(QPen(scene.palette().color(QPalette.ColorRole.Text), 1))
        scene.addItem(self._arrow)
        scene.installEventFilter(self)
        _ = self._loop.exec()
        scene.removeEventFilter(self)
        scene.removeItem(self._arrow)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """
        capture all mouse event here, convert to connection events, and
        send these to potential target items
        """
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
            # assert line, f"got: {line}"
            self._arrow.setLine(line)

            # manage connection enter and leave event
            scene = self._source.scene()
            entered_items = [item for item in self._entered_items]

            itemsUnderMouse = [item for item in scene.items(event.scenePos())]
            # print(itemsUnderMouse)
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
                _=scene = self._source.scene()
                event = ConnectionEvent(ConnectionDropType, self._source)
                _=scene.sendEvent(self._target, event)
            self._loop.exit()
            return True

        return super().eventFilter(watched, event)


class GraphicsNodeItem(QGraphicsItem):
    """A Node GraphicsItems"""
    def __init__(
        self,
        title:str="Node",
        parent:QGraphicsItem|None=None,
    ):
        super().__init__(parent)
        # private variables
        self._title:str = title
        self._isHighlighted:bool = False
        

        # Enable selection and movement
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsFocusable, True)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._title!r})"

    @override
    def boundingRect(self) -> QRectF:
        try:
            fm = QFontMetrics( self.scene().font() )
        except AttributeError:
            fm = QFontMetrics(QApplication.instance().font())

        text_width = fm.horizontalAdvance(self._title)
        text_height = fm.height()
        return QRectF(0,0,text_width+8, text_height+4)

    def palette(self)->QPalette:
        if palette:=getattr(self, '_palette', None):
            return palette
        elif parentWidget:=self.parentWidget():
            return parentWidget.palette()
        elif scene:=self.scene():
            return scene.palette()
        elif app:=QApplication.instance():
            return app.palette()
        else:
            return QPalette()

    def brush(self):
        baseColor = self.palette().base().color()
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

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        # d1 = QLineF(self.line().p1(), event.scenePos()).length()
        # d2 = QLineF(self.line().p2(), event.scenePos()).length()
        self.update()

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


class NodeWidget(GraphicsNodeItem):
    @override
    def itemChange(self, change:QGraphicsItem.GraphicsItemChange, value):
        match change:
            case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
                graph = cast(NXGraphScene, self.scene())
                graph.updateNodePosition(self)
            case _:
                return super().itemChange(change, value)

    def __str__(self):
        return f"{self.__class__.__name__}({self._title})"

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

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        # start connection
        if event.modifiers()==Qt.KeyboardModifier.AltModifier:
            connect = Connect(self)
            connect.exec()
            graphscene = cast(NXGraphScene, self.scene())
            # if target:=connect.target():
            #     source = connect.source()
            #     assert source
            #     graphscene.addEdge(EdgeWidget(), source, target)
        else:
            return super().mousePressEvent(event)

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
    
    def connectionDropEvent(self, event:ConnectionEvent)->None:
        if event.source()!=self:
            self.setHighlighted(False)
            event.setAccepted(True)
            return

        event.setAccepted(False)


class EdgeWidget(QGraphicsLineItem):
    """Graphics item representing an edge in a graph."""
    def __init__(
        self,
        label: str = "-edge-",
    ):
        super().__init__(parent=None)
        self._label = label
        self.setPen(QPen(Qt.GlobalColor.black, 1.5))

        # Enable selecting
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setZValue(-1)
        self.setAcceptHoverEvents(True)

        self._isHighlighted = False
        self._hoverMousePos:QPointF|None = None

    def __repr__(self):
        return f"{self.__class__.__name__}({self._label!r})"

    def setLabelText(self, text: str):
        self._label = text
        self.update()

    def labelText(self):
        return self._label

    def setHighlighted(self, value):
        self._isHighlighted = value
        self.update()

    def isHighlighted(self):
        return self._isHighlighted

    def hoverEnterEvent(self, event):
        self.setHighlighted(True)

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._hoverMousePos = event.pos()
        self.update()

    def hoverLeaveEvent(self, event):
        self.setHighlighted(False)

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
            if self._hoverMousePos:
                linearGrad = QLinearGradient(self.line().p1(), self.line().p2())
                d1 = QLineF(self.mapFromParent(self.line().p1()), self._hoverMousePos).length()
                d2 = QLineF(self.mapFromParent(self.line().p2()), self._hoverMousePos).length()
                if d1<d2:
                    linearGrad.setColorAt(0, palette.accent().color())
                    linearGrad.setColorAt(0.5, palette.accent().color())
                    linearGrad.setColorAt(1, palette.text().color())
                else:
                    linearGrad.setColorAt(0, palette.text().color())
                    linearGrad.setColorAt(0.5, palette.accent().color())
                    linearGrad.setColorAt(1, palette.accent().color())
                pen.setBrush(QBrush(linearGrad))  # Color for hover
            else:
                pen.setBrush(palette.accent().color())  # Color for hover

        return pen

    # def line(self):
    #     jiggle the line a little 
    #     from random import random
    #     line = super().line()
    #     line.setP1(line.p1()+QPointF(random()*5, random()*5))
    #     line.setP2(line.p2()+QPointF(random()*5, random()*5))
    #     return line

    def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem, widget=None):
        ### draw arrow shape
        arrow_shape = makeArrowShape(self.line(), self.pen().widthF())
        painter.setPen(Qt.NoPen)  # use the pen instead of the brush, to mimic QGRaphicsLineItem
        painter.setBrush(self.pen().brush())
        painter.drawPath(arrow_shape)
        painter.drawLine(self.line())

        ### draw label
        try:
            fm = QFontMetrics( self.scene().font() )
        except AttributeError:
            fm = QFontMetrics(QApplication.instance().font())

        painter.setPen(self.pen())
        painter.drawText(self.line().center()-self.pos(), self._label)

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
        try:
            fm = QFontMetrics( self.scene().font() )
        except AttributeError:
            fm = QFontMetrics(QApplication.instance().font())

        text_width = fm.horizontalAdvance(self._label)
        text_height = fm.height()

        shape_bbox = self.shape().boundingRect()
        text_bbox = QRectF(self.line().center()-self.pos(), QSizeF(text_width, text_height))
        return shape_bbox.united(text_bbox)





class NXGraphScene(QGraphicsScene):
    connected = Signal(QGraphicsItem, QGraphicsItem) # source, target
    disconnected = Signal(QGraphicsItem, QGraphicsItem)  # edge
    # reconnected = Signal(EdgeWidget)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create am 'infinite' scene to hold the node and edge graphics
        self.setSceneRect(QRect(-9999 // 2, -9999 // 2, 9999, 9999))
        self._nodes:set[QGraphicsItem] = set()
        self._edges:set[QGraphicsItem] = set()

        self._endpoints:dict[QGraphicsItem, tuple[QGraphicsItem, QGraphicsItem]] = dict()
        self._node_edges:dict[QGraphicsItem, set[QGraphicsItem]] = dict()

    def addNode(self, node: QGraphicsItem):
        self._nodes.add(node)
        self._node_edges[node] = set()
        self.addItem(node)

    def removeNode(self, node: QGraphicsItem, remove_connected_nodes=True):
        if remove_connected_nodes:
            for edge in self._node_edges:
                self.removeEdge(edge)
                # self.removeItem(edge)
        self._nodes.remove(node)
        del self._node_edges[node]
        self.removeItem(node)

    def addEdge(self, edge: QGraphicsItem, source:QGraphicsItem, target:QGraphicsItem):
        self._endpoints[edge] = source, target
        self._edges.add(edge)
        self._endpoints[edge] = source, target
        self._node_edges[source].add(edge)
        self._node_edges[target].add(edge)
        self.addItem(edge)
        self.updateEdgePosition(edge, source, target)

    def removeEdge(self, edge: QGraphicsItem):
        
        source, target = self._endpoints[edge]
        self._edges.remove(edge)
        self._node_edges[source].remove(edge)
        self._node_edges[target].remove(edge)
        del self._endpoints[edge]
        self.removeItem(edge)

    def updateNodePosition(self, node:QGraphicsItem):
        for edge in self._node_edges[node]:
            source, target = self._endpoints[edge]
            self.updateEdgePosition(edge, source, target)

    def updateEdgePosition(self, edge:QGraphicsItem, source:QGraphicsItem, target:QGraphicsItem):
        edge = cast(QGraphicsArrowItem, edge)
        line = makeLineBetweenShapes(source, target)
        edge.setLine(line)

    def nodeAt(self, pos: QPoint | QPointF) -> QGraphicsItem | None:
        for item in self.items(pos, deviceTransform=QTransform()):
            if item in self._nodes:
                return item
        return None

    def edgeAt(self, pos: QPoint | QPointF) -> QGraphicsItem | None:
        for item in self.items(pos, deviceTransform=QTransform()):
            if any(item in edges for edges in self._node_edges.values()):
                return item
        return None

    # def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
    #     self._buttonDownItem = self.itemAt(event.buttonDownScenePos(Qt.MouseButton.LeftButton), QTransform())
    #     return super().mousePressEvent(event)

    # def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
    #     if event.buttons()==Qt.MouseButton.LeftButton:
    #         if item:=self._buttonDownItem:
    #             if item in self._nodes
    #                 if event.modifiers()==Qt.KeyboardModifier.AltModifier:
    #                     if QLineF(event.screenPos(), event.buttonDownScreenPos(Qt.MouseButton.LeftButton)).length() < QApplication.startDragDistance():
    #                         return

    #                     # start connection
    #                     connect = Connect(item)
    #                     connect.exec()
                        
    #                     if connect.target():
    #                         self.connected.emit(connect.source(), connect.target())

    #                     return

    #             elif item in self._edges:
    #                 edge = cast(QGraphicsArrowItem, item)
    #                 scene = self
    #                 if QLineF(event.screenPos(), event.buttonDownScreenPos(Qt.MouseButton.LeftButton)).length() < QApplication.startDragDistance():
    #                     return

    #                 # # start connection
    #                 d1 = QLineF(edge.line().p1(), event.buttonDownScenePos(Qt.MouseButton.LeftButton)).length()
    #                 d2 = QLineF(edge.line().p2(), event.buttonDownScenePos(Qt.MouseButton.LeftButton)).length()

    #                 edge.hide()
    #                 if d1>d2:
    #                     connect = Connect(edge.source())
    #                     connect.exec()
    #                     if not connect.target():
    #                         graphscene = cast(NXGraphScene, scene)
    #                         # graphscene.removeEdge(edge)
    #                         self.disconnected.emit(edge)
    #                     elif connect.target() != edge.target():
    #                         # self.removeEdge(edge)
    #                         self.disconnected.emit(edge)
    #                         new_edge = EdgeWidget(connect.source(), connect.target())
    #                         # self.addEdge(new_edge)
    #                         self.connected.emit(new_edge)
    #                 else:
    #                     connect = Connect(edge.target(), direction='backward')
    #                     connect.exec()
    #                     if not connect.target():
    #                         graphscene = cast(NXGraphScene, scene)
    #                         self.disconnected.emit(edge)
    #                         # graphscene.removeEdge(edge)
    #                     elif connect.target() != edge.source():
    #                         # self.removeEdge(edge)
    #                         self.disconnected.emit(edge)
    #                         new_edge = EdgeWidget(connect.target(), connect.source())
    #                         # self.addEdge(new_edge)
    #                         self.connected.emit(new_edge)
    #                 edge.show()
    #                 return
        
    #     super().mouseMoveEvent(event)


class PortWidget(QGraphicsWidget):
    class Kind(StrEnum):
        Inlet="INLET"
        Outlet="OUTLET"

    def __init__(self, node: 'NodeWidget2', kind:Kind) -> None:
        super().__init__(parent=node)
        self.setAcceptHoverEvents(True)
        self._isHighlighted = False
        self._kind = kind
        self._node = node

    def sizeHint(self, which: Qt.SizeHint, constraint: QSizeF|QSize) -> QSizeF:
        return QSizeF(6,6)

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
        painter.drawEllipse(self.boundingRect().adjusted(-1, -1, 1, 1))
        # painter.drawRoundedRect(self.boundingRect().adjusted(-1, -1, 1, 1), 4, 4)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        connect = Connect(self)
        connect.exec()
        return super().mousePressEvent(event)

    # def event(self, event)->bool:
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

    #     return super().event(event)

    # def connectionEnterEvent(self, event:ConnectionEvent) -> None:
    #     if event.source()!=self:
    #         event.setAccepted(True)
    #         self.setHighlighted(True)
    #         return
    #     event.setAccepted(False)

    # def connectionLeaveEvent(self, event:ConnectionEvent)->None:
    #     self.setHighlighted(False)

    # def connectionMoveEvent(self, event:ConnectionEvent)->None:
    #     ...
    
    # def connectionDropEvent(self, event:ConnectionEvent):
    #     if event.source()!=self:
    #         self.setHighlighted(False)
    #         event.setAccepted(True)
    #         return

    #     event.setAccepted(False)


class NodeWidget2(QGraphicsWidget):
    def __init__(self, text:str, inlets:list[str]=[], parent: Optional[QGraphicsItem]=None) -> None:
        super().__init__(parent)


        main_layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(4)
        self.setLayout(main_layout)

        ### Header
        header_widget = QGraphicsWidget()
        main_layout.addItem(header_widget)
        header_layout = QGraphicsLinearLayout()
        header_layout.setContentsMargins(0,0,0,0)
        header_widget.setLayout(header_layout)
        name_label_proxy = QGraphicsProxyWidget()
        name_label_proxy.setWidget(QLabel(text))
        header_layout.addItem(name_label_proxy)

        ### Inlets
        self.inlets = []
        inlets_widget = QGraphicsWidget()
        main_layout.addItem(inlets_widget)
        inlets_layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)
        inlets_layout.setContentsMargins(0,0,0,0)
        inlets_layout.setSpacing(0)
        inlets_widget.setLayout(inlets_layout)
        for inlet_name in inlets:
            inlet_row = QGraphicsWidget()
            inlet_row_layout = QGraphicsLinearLayout()
            inlet_row_layout.setContentsMargins(0,0,0,0)
            inlet_row_layout.setSpacing(4)

            inlet_row.setLayout(inlet_row_layout)
            port = PortWidget(self, PortWidget.Kind.Inlet)
            port.installEventFilter(self)
            inlet_row_layout.addItem(port)
            inlet_row_layout.setAlignment(port, Qt.AlignVCenter)
            proxy_label = QGraphicsProxyWidget()
            proxy_label.setWidget(QLabel(inlet_name))
            inlet_row_layout.addItem(proxy_label)
            inlet_row_layout.setAlignment(proxy_label, Qt.AlignVCenter)
            inlets_layout.addItem(inlet_row)
            self.inlets.append(port)


        ### Outlets
        self.outlets = []
        outlets_widget = QGraphicsWidget()
        main_layout.addItem(outlets_widget)
        outlets_layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)
        outlets_layout.setContentsMargins(0,0,0,0)
        outlets_layout.setSpacing(0)
        outlets_widget.setLayout(outlets_layout)
        for outlet_name in ["out"]:
            outlet_row = QGraphicsWidget()
            outlet_row_layout = QGraphicsLinearLayout()
            outlet_row_layout.setContentsMargins(0,0,0,0)
            outlet_row_layout.setSpacing(4)
            outlet_row.setLayout(outlet_row_layout)
            proxy_label = QGraphicsProxyWidget()
            label = QLabel(outlet_name)
            # label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
            label.setAlignment(Qt.AlignmentFlag.AlignRight)
            proxy_label.setWidget(label)
            outlet_row_layout.addItem(proxy_label)
            outlet_row_layout.setAlignment(proxy_label, Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignRight)
            port = PortWidget(self, PortWidget.Kind.Outlet)
            outlet_row_layout.addItem(port)
            outlet_row_layout.setAlignment(port, Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignRight)
            outlets_layout.addItem(outlet_row)
            self.outlets.append(port)


        # Enable selection and movement
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsFocusable, True)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched in self.inlets:
            inlet = cast(PortWidget, watched)
            if event.type() == ConnectionEnterType:
                event = cast(ConnectionEvent, event)
                source_port = cast(PortWidget, event.source())
                if source_port._kind == PortWidget.Kind.Outlet and source_port._node != self:
                    event.setAccepted(True)
                    inlet.setHighlighted(True)
                else:
                    ...
                    # event.setAccepted(False)

            elif event.type() == ConnectionLeaveType:
                inlet.setHighlighted(False)

            elif event.type() == ConnectionDropType:
                print("Drop")

        return super().eventFilter(watched, event)


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
    # graphscene.connected.connect(lambda edge, source, target: graphscene.addEdge(edge, source, target))
    # graphscene.disconnected.connect(lambda edge, source, target: graphscene.removeEdge(edge, source, target))
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

    read_widget = NodeWidget2("Read")
    graphscene.addNode(read_widget)
    read_widget.moveBy(-100,100)

    print_widget = NodeWidget2("Print", ["args", "end", "sep"])
    graphscene.addNode(print_widget)
    print_widget.moveBy(-20,100)

    # create edge1
    edge1 = EdgeWidget()
    graphscene.addEdge(edge1, read_text_node, convert_node)

    # show window
    window.show()
    sys.exit(app.exec())
