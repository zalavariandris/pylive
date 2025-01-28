##################
# GRAPHICS ITEMS #
##################

# QGraphicsItem shapes. purely visual, but interactive.
# thes are the superclass of the ModelView Widgets for the NXGraphScene
# ther are no supposed to interact with the model in any way
# responsible to paint ui items,
# and can react to mouse or keyboard event, strictly in a vosual way.
# in MVC these would be the views.
# in QT ModelView terminology these are self contained widgets,
# that can be used by the 'Views'


from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel
from pylive.utils.geo import makeArrowShape
from pylive.utils.geo import getShapeCenter, getShapeRight, getShapeLeft, makeLineBetweenShapes, makeVerticalRoundedPath, makeHorizontalRoundedPath


class InteractiveShape(QGraphicsItem):
    def __init__(self, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        # self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self._isHighlighted = False
        self._hoverMousePos: QPointF | None = None
        self._debug = False

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def setHighlighted(self, value):
        self._isHighlighted = value
        self.prepareGeometryChange()
        self.update()

    def isHighlighted(self):
        return self._isHighlighted

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        self.setHighlighted(True)
        return super().hoverEnterEvent(event)

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._hoverMousePos = event.pos()
        self.update()
        return super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        self.setHighlighted(False)
        super().hoverLeaveEvent(event)

    def font(self):
        if font := getattr(self, "_font", None):
            return font
        elif parentWidget := self.parentWidget():
            return parentWidget.font()
        elif scene := self.scene():
            return scene.font()
        elif app := QApplication.instance():
            if isinstance(app, QGuiApplication):
                return app.font()

        return QFont()

    def palette(self) -> QPalette:
        if palette := getattr(self, "_palette", None):
            return palette
        elif parentWidget := self.parentWidget():
            return parentWidget.palette()
        elif scene := self.scene():
            return scene.palette()
        elif app := QApplication.instance():
            if isinstance(app, QGuiApplication):
                return app.palette()

        return QPalette()

    def brush(self):
        baseColor = self.palette().base().color()
        baseColor.setAlpha(255)
        brush = QBrush(baseColor)
        return brush

    def pen(self):
        palette = self.palette()

        pen = QPen(palette.text().color())

        if self.isSelected():
            pen.setColor(palette.highlight().color())  # Color for selected

        if self.isHighlighted():
            pen.setColor(palette.accent().color())  # Color for hover

        return pen

    def paint(self, painter, option, widget=None):
        painter.setBrush(self.brush())
        painter.setPen(self.pen())


class BaseLinkItem(QGraphicsItem):
    def move(
            self,
            source: QGraphicsItem | QPointF,
            target: QGraphicsItem | QPointF,
            /
        )->None:
            raise NotImplementedError("link subclasses must implement move method")


class BaseNodeItem(QGraphicsWidget):
    scenePositionChanged = Signal()
    def __init__(self, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)


    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.scenePositionChanged.emit()
        return super().itemChange(change, value)


class VertexShape(InteractiveShape):
    def __init__(self, name:str, parent=None):
        super().__init__(parent=parent)
        self._nameitem = QGraphicsTextItem(f"{name}")
        self._nameitem.setParentItem(self)
        self._nameitem.installSceneEventFilter(self)

    """A graph 'Vertex' graphics item. no inlets or outlets."""
    def brush(self):
        color = self.palette().window().color()
        color.setAlpha(255)
        return QBrush(color)
        return self.palette().base()

    @override
    def boundingRect(self) -> QRectF:
        return self.childrenBoundingRect().adjusted(-4,-2,4,2)

    def paint(
        self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None
    ):
        
        super().paint(painter, option, widget)
        painter.drawRoundedRect(self.boundingRect(), 4, 4)




def distribute_items_horizontal(items, rect:QRectF):
            num_items = len(items)
            
            if num_items < 1:
                return

            if num_items <2:
                items[0].setX(rect.center().x())
                return

            # Calculate horizontal spacing
            spacing = rect.width() / (num_items - 1)
            for i, item in enumerate(items):
                x = rect.left() + i * spacing
                item.setX(x)


class PortShape(InteractiveShape):
    def __init__(self, name:str, parent:QGraphicsItem|None=None):
        super().__init__(parent)
        self._nameitem = QGraphicsTextItem(f"{name}")
        self._nameitem.setParentItem(self)
        self._nameitem.setPos(-6,-26)
        self._nameitem.hide()
        self.setFiltersChildEvents(True)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        self._nameitem.show()

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        self._nameitem.hide()

    def boundingRect(self) -> QRectF:
        ellipse_bbox = QRectF(-6,-6,12,12)
        return ellipse_bbox

    def brush(self):
        return QBrush( self.palette().text() )

    def paint(self, painter, option, widget=None):
        # painter.drawLine(-5, 0, 5, 0)
        # painter.drawLine(0, -5, 0, 5)
        # painter.drawRect(self.boundingRect())

        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        r = 2
        painter.drawEllipse(-r,-r, r*2, r*2)



class ArrowLinkShape(InteractiveShape, BaseLinkItem):
    """Graphics item representing an edge in a graph."""

    def __init__(
        self, label:str, parent: QGraphicsItem | None = None
    ):
        super().__init__(parent=None)
        self._line: QLineF = QLineF()
        self._label = label

    def setLabelText(self, text):
        self._label = text

    def pen(self):
        """override to indicate endpoints under mouse"""
        palette = self.palette()

        pen = QPen(palette.text().color())

        if self.isSelected():
            pen.setColor(palette.highlight().color())  # Color for selected

        if self.isHighlighted():
            if self._hoverMousePos:
                linearGrad = QLinearGradient(self._line.p1(), self._line.p2())
                d1 = QLineF(
                    self.mapFromParent(self._line.p1()), self._hoverMousePos
                ).length()
                d2 = QLineF(
                    self.mapFromParent(self._line.p2()), self._hoverMousePos
                ).length()
                if d1 < d2:
                    linearGrad.setColorAt(0.0, palette.accent().color())
                    linearGrad.setColorAt(0.5, palette.accent().color())
                    linearGrad.setColorAt(0.55, palette.text().color())
                else:
                    linearGrad.setColorAt(0.45, palette.text().color())
                    linearGrad.setColorAt(0.5, palette.accent().color())
                    linearGrad.setColorAt(1, palette.accent().color())
                pen.setBrush(QBrush(linearGrad))  # Color for hover
            else:
                pen.setBrush(palette.accent().color())  # Color for hover

        return pen

    def paint(
        self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None
    ):
        import math

        ### draw label
        fm = QFontMetrics(self.font())
        ellipse_bbox = fm.boundingRect(
            self.boundingRect().toRect(),
            Qt.AlignmentFlag.AlignCenter,
            self._label,
        )
        f = 1 / math.sin(math.radians(45))

        ellipse_bbox.setSize(
            QSizeF(ellipse_bbox.width() * f, ellipse_bbox.height() * f).toSize()
        )
        ellipse_bbox.moveCenter(self.boundingRect().center().toPoint())
        # painter.drawEllipse(text_bbox)

        text_clip = QRegion(self.boundingRect().toRect()) - QRegion(
            ellipse_bbox, QRegion.RegionType.Ellipse
        )

        painter.setPen(self.pen())
        painter.drawText(
            self.boundingRect(),
            self._label,
            QTextOption(Qt.AlignmentFlag.AlignCenter),
        )

        ### draw arrow shape
        arrow_shape = makeArrowShape(self._line, self.pen().widthF())

        # use the pen as brush to draw the arrow shape
        import math

        # painter.drawRect(ellipse_bbox)
        # painter.drawEllipse(ellipse_bbox)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.pen().brush())
        if self._label:
            painter.setClipRegion(text_clip)
        painter.drawPath(arrow_shape)

    def shape(self) -> QPainterPath:
        """Override shape to provide a wider clickable area."""
        path = QPainterPath()
        path.moveTo(self._line.p1())
        path.lineTo(self._line.p2())
        stroker = QPainterPathStroker()
        stroker.setWidth(10)
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        return stroker.createStroke(path)

    def boundingRect(self) -> QRectF:
        shape_bbox = self.shape().boundingRect()
        m = self.pen().widthF()
        return shape_bbox.adjusted(-m, -m, m, m)

    def move(
        self,
        source: QGraphicsItem | QPointF,
        target: QGraphicsItem | QPointF,
        /
    )->None:
        """Moves the link to the source and target items

        comments:

        I couldn find a nice way (ther is probalby no nice way) 
        to catch QGraphicsItem scene movements!

        I think the link is responsible (and the target items are not) to move
        the link to the linked shapes. (This way supporting all QGraphicsItems.)
        Therefore, to actually update the link geometry, you must call this
        function.

        There are several ways to cath items moving
        e.g.: subclassing a QGraphicsItem:
        - storing connected link, then use the 'itemChange' callback.
        - or by using QGraphicsWidgets, and connect
          to the geometryChange signal, (pay attention as this is a local position)
        """

        line = makeLineBetweenShapes(source, target)
        length = line.length()
        if length > 0:
            offset = min(0, length / 2)
            line = QLineF(
                line.pointAt(offset / length),
                line.pointAt((length - offset) / length),
            )

        self.setLine(line)

    def line(self)->QLineF:
        return self._line

    def setLine(self, line:QLineF):
        self.prepareGeometryChange()
        self._line = line
        self.update()


class RoundedLinkShape(InteractiveShape, BaseLinkItem):
    def __init__(
        self, label: str = "link-", orientation:Qt.Orientation=Qt.Orientation.Vertical, parent: QGraphicsItem | None = None
    ):
        super().__init__(parent=None)
        self._orientation = orientation
        self._path:QPainterPath = QPainterPath()
        self._labelitem = QGraphicsTextItem(label)
        self._labelitem.setParentItem(self)

    def path(self):
        return self._path

    def setPath(self, path:QPainterPath):
        self._path = path
        P = self.path().pointAtPercent(0.5)
        self._labelitem.setPos(P)
        self._labelitem.adjustSize()
        size = self._labelitem.boundingRect().size()
        self._labelitem.moveBy(-size.width()/2, -size.height()/2)
        self.prepareGeometryChange()
        self.update()

    def setLabelText(self, text:str):
        self._labelitem.setPlainText(text)

    def labelText(self):
        return self._labelitem.toPlainText()

    def boundingRect(self):
        m = 2
        return self.shape().boundingRect().adjusted(-m, -m, m, m)

    def shape(self)->QPainterPath:
        path = self.path()

        stroker = QPainterPathStroker()
        stroker.setWidth(10)
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        return stroker.createStroke(path)
        return path

    def paint(
        self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None
    ):
        path = self.path()
        painter.setPen(self.pen())
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if self._labelitem:
            ### clip text
            text_rect = self.mapFromItem(self._labelitem, self._labelitem.boundingRect()).boundingRect()
            text_clip = QRegion(self.boundingRect().toRect()) - QRegion(
                text_rect.toRect(), QRegion.RegionType.Ellipse
            )
            painter.setClipRegion(text_clip)
        painter.drawPath(path)

        triangle = QPolygonF([
            QPointF(-4, 4),
            QPointF(0,0),
            QPointF(-4, -4)
        ])
        tr = QTransform()
        P = path.pointAtPercent(1)
        tr.translate(P.x(), P.y())
        tr.rotate(-path.angleAtPercent(1))
        painter.setBrush(painter.pen().color())
        painter.drawPolygon(tr.map(triangle))
        
    def move(
        self,
        source: QGraphicsItem | QPointF,
        target: QGraphicsItem | QPointF,
        /
    ):
        line = QLineF()
        match self._orientation:
            case Qt.Orientation.Vertical:
                match source:
                    case QGraphicsItem():
                        rect = source.boundingRect()
                        line.setP1(source.mapToScene(
                            rect.center().x(),
                            rect.bottom()
                        ))
                    case QPointF():
                        line.setP1(source)

                match target:
                    case QGraphicsItem():
                        rect = target.boundingRect()
                        line.setP2(target.mapToScene(
                            rect.center().x(),
                            rect.top()
                        ))
                    case QPointF():
                        line.setP2(target)

                self.setPath(makeVerticalRoundedPath(line))
            case Qt.Orientation.Horizontal:
                match source:
                    case QGraphicsItem():
                        rect = source.boundingRect()
                        line.setP1(source.mapToScene(
                            rect.right(),
                            rect.center().y()
                        ))
                    case QPointF():
                        line.setP1(source)

                match target:
                    case QGraphicsItem():
                        rect = target.boundingRect()
                        line.setP2(target.mapToScene(
                            rect.left(),
                            rect.center().y()
                        ))
                    case QPointF():
                        line.setP2(target)

                self.setPath(makeHorizontalRoundedPath(line))


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    view = QGraphicsView()
    view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
    view.setWindowTitle("HraphicsItem for NodeEditor")
    view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    # create graph scene
    scene = QGraphicsScene()
    scene.setSceneRect(QRectF(-400, -400, 800, 800))
    view.setScene(scene)

    ## create graphics
    # vertex_item_1 = VertexShape("GraphicsVertexItem1")
    # graphscene.addItem(vertex_item_1)
    # vertex_item_1.setPos(0, -150)
    # vertex_item_1.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

    def node_factory(name="node", pos=QPointF()):
        node = NodeShape(name=name,
            inlets=[
                PortShape("in1"), 
                PortShape("in2"),
                PortShape("in2")
            ],
            outlets=[
                PortShape("out")
            ],
        )
        node.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        scene.addItem(node)
        node.setPos(pos)
        return node

    # link_item_1 = LinkShape("link1")
    # link_item_1.move(QPointF(0, -50), QPointF(100, -20))
    # graphscene.addItem(link_item_1)

    node1 = node_factory("N1")
    node2 = node_factory("N2", QPointF(100, 300))

    link = RoundedLinkShape("link2")
    link.move(node1, node2)
    scene.addItem(link)

    view.show()
    app.exec()
