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

from pylive.QtGraphEditor.qgraphics_arrow_item import (
    makeArrowShape,
)
from pylive.utils.geo import makeLineBetweenShapes


class AbstractShape(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self._isHighlighted = False
        self._hoverMousePos: QPointF | None = None

    def setHighlighted(self, value):
        self._isHighlighted = value
        self.update()

    def isHighlighted(self):
        return self._isHighlighted

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        self.setHighlighted(True)

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._hoverMousePos = event.pos()
        self.update()

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        self.setHighlighted(False)

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


class VertexShape(AbstractShape):
    """A graph 'Vertex' graphics item. no inlets or outlets."""

    def __init__(
        self,
        title: str = "Node",
        parent: QGraphicsItem | None = None,
    ):
        super().__init__(parent)
        # private variables
        self._title: str = title
        self._isHighlighted: bool = False

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

    def brush(self):
        baseColor = self.palette().base().color()
        baseColor.setAlpha(200)
        brush = QBrush(baseColor)
        return brush

    @override
    def boundingRect(self) -> QRectF:
        fm = QFontMetrics(self.font())

        text_width = fm.horizontalAdvance(self._title)
        text_height = fm.height()
        return QRectF(0, 0, text_width + 8, text_height + 4)

    def paint(
        self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None
    ):
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRoundedRect(self.boundingRect(), 4, 4)

        fm = QFontMetrics(self.font())
        painter.drawText(4, fm.height() - 1, self._title)

    def title(self):
        return self._title

    def setTitle(self, text: str):
        self._title = text
        self.update()


class LinkShape(AbstractShape):
    """Graphics item representing an edge in a graph."""

    def __init__(
        self, label: str = "-link-", parent: QGraphicsItem | None = None
    ):
        super().__init__(parent=None)
        self._label = label

        # Enable selecting
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        # self.setZValue(-1)

        self._line: QLineF = QLineF()

    # def setLine(self, line: QLineF):
    #     self.prepareGeometryChange()
    #     self._line = line
    #     self.update()

    # def _line(self) -> QLineF:
    #     return self._line

    def __repr__(self):
        return f"{self.__class__.__name__}({self._label!r})"

    def setLabelText(self, text: str):
        self._label = text
        self.update()

    def labelText(self):
        return self._label

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
        ### draw arrow shape
        arrow_shape = makeArrowShape(self._line, self.pen().widthF())

        # use the pen as brush to draw the arrow shape
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.pen().brush())
        painter.drawPath(arrow_shape)
        painter.drawLine(self._line)

        ### draw label
        fm = QFontMetrics(self.font())

        painter.setPen(self.pen())
        painter.drawText(self._line.center() - self.pos(), self._label)

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
        fm = QFontMetrics(self.font())

        text_width = fm.horizontalAdvance(self._label)
        text_height = fm.height()

        shape_bbox = self.shape().boundingRect()
        text_bbox = QRectF(
            self._line.center() - self.pos() - QPointF(0, text_height),
            QSizeF(text_width, text_height),
        )

        m = self.pen().widthF()
        return shape_bbox.united(text_bbox).adjusted(-m, -m, m, m)

    def move(
        self,
        source_graphics_item: QGraphicsItem | QPainterPath | QRectF | QPointF,
        target_graphics_item: QGraphicsItem | QPainterPath | QRectF | QPointF,
    ):
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

        line = makeLineBetweenShapes(source_graphics_item, target_graphics_item)
        length = line.length()
        if length > 0:
            offset = min(8, length / 2)
            line = QLineF(
                line.pointAt(offset / length),
                line.pointAt((length - offset) / length),
            )

        self.prepareGeometryChange()
        self._line = line
        self.update()


class NodeShape(VertexShape):
    def __init__(self, title, inlets, outlets, parent=None):
        super().__init__(title=title, parent=parent)
        self._inlets: list[QGraphicsItem] = []
        self._outlets: list[QGraphicsItem] = []
        self.ports_margin = -5

        for inlet in inlets:
            self._addInlet(inlet)
        for outlet in outlets:
            self._addOutlet(outlet)

        self.ports_margin = -40

    def boundingRect(self) -> QRectF:
        return (
            super()
            .boundingRect()
            .united(self.childrenBoundingRect())
            .adjusted(-4, 0, 4, 2)
        )

    def _addInlet(self, inlet_widget: QGraphicsItem):
        inlet_widget.setParentItem(self)
        self._inlets.append(inlet_widget)
        self.layoutPorts()
        self.update()

    def _removeInlet(self, inlet_widget: QGraphicsItem):
        self._inlets.remove(inlet_widget)
        if scene := inlet_widget.scene():
            scene.removeItem(inlet_widget)
        self.layoutPorts()
        self.update()

    def _addOutlet(self, outlet_widget: QGraphicsItem):
        outlet_widget.setParentItem(self)
        self._outlets.append(outlet_widget)
        self.layoutPorts()
        self.update()

    def _removeOutlet(self, outlet_widget: QGraphicsItem):
        self._outlets.remove(outlet_widget)
        outlet_widget.setParentItem(self)
        if scene := outlet_widget.scene():
            scene.removeItem(outlet_widget)
        self.layoutPorts()
        self.update()

    def layoutPorts(self):
        y = 14  # header heighn
        for inlet_widget in self._inlets:
            inlet_widget.setPos(4, y)
            y += inlet_widget.boundingRect().height()

        for outlet_widget in self._outlets:
            outlet_widget.setPos(4, y)
            y += outlet_widget.boundingRect().height()


class PortShape(AbstractShape):
    def __init__(
        self,
        label: str,
        parent: QGraphicsItem | None = None,
    ):
        super().__init__(parent=parent)
        self._label = label

    def label(self) -> str:
        return self._label

    def setLabel(self, text: str):
        self._label = text

    def boundingRect(self) -> QRectF:
        fm = QFontMetrics(self.font())

        ellipse_bbox = QRectF(0, 0, 10, 10)
        text_width = fm.horizontalAdvance(self._label)
        text_height = fm.height()

        text_pos = QPointF(12, 0)
        text_bbox = QRectF(text_pos, QSizeF(text_width, text_height))
        return ellipse_bbox.united(text_bbox)

    def paint(self, painter, option, widget=None):
        ### draw label
        fm = QFontMetrics(self.font())

        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawEllipse(QRectF(2, 7, 6, 6))

        text_height = fm.height()
        text_pos = QPointF(12, text_height - 2)
        painter.drawText(text_pos, self._label)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    graphview = QGraphicsView()
    graphview.setWindowTitle("HraphicsItem for NodeEditor")
    graphview.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    graphview.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    graphview.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    # create graph scene
    graphscene = QGraphicsScene()
    graphscene.setSceneRect(QRectF(-400, -400, 800, 800))
    graphview.setScene(graphscene)

    ## create graphics
    vertex_item_1 = VertexShape("GraphicsVertexItem1")
    graphscene.addItem(vertex_item_1)
    vertex_item_1.setPos(0, -150)

    node_item_1 = NodeShape(
        "GraphicsNodeItem1",
        inlets=[PortShape("GraphicsPortItemm")],
        outlets=[PortShape("GraphicsPortItem")],
    )
    graphscene.addItem(node_item_1)
    node_item_1.setPos(0, -120)

    link_item_1 = LinkShape("link1")
    link_item_1.move(QPointF(0, -50), QPointF(100, -20))
    graphscene.addItem(link_item_1)

    graphview.show()
    app.exec()
