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
from pylive.utils.geo import getShapeCenter, getShapeRight, getShapeLeft, makeLineBetweenShapes


class AbstractShape(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self._isHighlighted = False
        self._hoverMousePos: QPointF | None = None
        self._debug = False

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
        self, label: str = "link-", parent: QGraphicsItem | None = None
    ):
        super().__init__(parent=None)
        self._label = label

        # Enable selecting
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        # self.setZValue(-1)

        self._line: QLineF = QLineF()

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
        painter.drawLine(self._line)

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
        /
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

import math
def fillet(A: QPointF, B: QPointF, C: QPointF, r: float) -> tuple[QPointF, QPointF, QPointF, float, float]:
    """
    Calculate fillet between two lines defined by points A-B and B-C, including arc angles.
    
    Args:
        A: First point of first line
        B: Corner point (intersection of lines)
        C: Second point of second line
        r: Radius of the fillet
        
    Returns:
        Tuple of (tangent_point1, tangent_point2, center_point, start_angle, sweep_angle)
        Angles are in radians. Sweep angle is positive for counterclockwise direction.
    """
    def unit_vector(v: QPointF) -> QPointF:
        length = math.sqrt(v.x()**2 + v.y()**2)
        if abs(length) < 1e-10:
            raise ValueError("Zero length vector")
        return QPointF(v.x() / length, v.y() / length)
    
    def dot_product(v1: QPointF, v2: QPointF) -> float:
        return v1.x() * v2.x() + v1.y() * v2.y()
    
    def vector_angle(v: QPointF) -> float:
        """Calculate angle of vector from positive x-axis in radians."""
        angle = math.atan2(v.y(), v.x())
        return angle if angle >= 0 else angle + 2 * math.pi

    # Input validation
    if r <= 0:
        raise ValueError("Radius must be positive")
    
    # Get direction vectors for both lines
    dir1 = unit_vector(QPointF(A.x() - B.x(), A.y() - B.y()))
    dir2 = unit_vector(QPointF(C.x() - B.x(), C.y() - B.y()))
    
    # Calculate angle between lines
    cos_theta = dot_product(dir1, dir2)
    if abs(cos_theta - 1) < 1e-10:
        raise ValueError("Lines are parallel or nearly parallel")
    
    # Calculate tangent distance from corner
    angle = math.acos(cos_theta)
    tan_distance = r / math.tan(angle / 2)
    
    # Calculate tangent points
    tangent1 = QVector2D(
        B.x() + dir1.x() * tan_distance,
        B.y() + dir1.y() * tan_distance
    )
    
    tangent2 = QVector2D(
        B.x() + dir2.x() * tan_distance,
        B.y() + dir2.y() * tan_distance
    )
    
    # Calculate center point
    center_dir = unit_vector(QVector2D(
        dir1.x() + dir2.x(),
        dir1.y() + dir2.y()
    ))
    
    center_distance = r / math.sin(angle / 2)
    
    center = QPointF(
        B.x() + center_dir.x() * center_distance,
        B.y() + center_dir.y() * center_distance
    )
    
    # Calculate arc angles
    # Vector from center to first tangent point
    radius_vector1 = QPointF(
        tangent1.x() - center.x(),
        tangent1.y() - center.y()
    )
    
    # Calculate start angle (from positive x-axis to first radius vector)
    start_angle = vector_angle(radius_vector1)
    
    # Calculate sweep angle
    sweep_angle = angle
    
    # Determine if we need to sweep clockwise or counterclockwise
    # Cross product of radius vectors to determine orientation
    cross_product = (radius_vector1.x() * (tangent2.y() - center.y()) - 
                    radius_vector1.y() * (tangent2.x() - center.x()))
    if cross_product < 0:
        sweep_angle = -sweep_angle
    
    return tangent1, tangent2, center, start_angle, sweep_angle


class RoundedLinkShape(LinkShape):
    def __init__(self, label: str = "link-", parent: QGraphicsItem | None = None):
        super().__init__(parent=None)

        self.polygon = QPolygonF()

    def boundingRect(self):
        m = 50
        return self.polygon.boundingRect().adjusted(-m, -m, m, m)

    def paint(self, painter, option, widget=None):
        if self._debug or True:
            painter.setPen(QPen(QBrush("red"), 0.5, Qt.PenStyle.DotLine))
            debug_path = QPainterPath()
            debug_path.addPolygon(self.polygon)
            painter.drawPath(debug_path)
        
        ### Fillet polygon
        points = [self.polygon.at(i) for i in range(self.polygon.size())]
        #r = 35
        path = QPainterPath()
        path.moveTo(points[0])
        for A, B, C, r in zip(points, points[1:], points[2:], self.radii):
            # calculate ellipse origin
            try:
                tangent1, tangent2, O, start_angle, sweep_angle= fillet(A, B, C, r)
                rect = QRectF(
                    QPointF(O.x()-r, O.y()-r), 
                    QSizeF(2*r,2*r)
                ).normalized()

                if sweep_angle>0:
                    path.arcTo(rect, -math.degrees(start_angle), math.degrees(sweep_angle)-180)
                else:
                    path.arcTo(rect, -math.degrees(start_angle), math.degrees(sweep_angle)+180)
            except ValueError:
                path.lineTo(B)
                
        path.lineTo(points[-1])
        color = QColor("lightblue")
        color.setAlpha(128)
        painter.setPen(self.pen())
        painter.drawPath(path)
        

    def move(
        self,
        source: QGraphicsItem | QPainterPath | QRectF | QPointF,
        target: QGraphicsItem | QPainterPath | QRectF | QPointF,
        /
    ):
        A = getShapeRight(source)
        B = getShapeLeft(target)
        
        dx = B.x()-A.x()
        dy = B.y()-A.y()
        if dx>50:
            r1 = min(50, min(abs(dx)/2, abs(dy)/2))
            r2 = min(abs(dx), abs(dy))-r1
            self.radii = [r1, r2]
            self.polygon = QPolygonF([
                A, 
                QPointF(A.x() + self.radii[0], A.y()), 
                QPointF(A.x() + self.radii[0], B.y()),
                B
            ])
        else:
            r1 = min(50, abs(dy)/2)
            r2 = min(abs(dx), abs(dy) )-r1
            self.radii = [r1, r2]
            self.polygon = QPolygonF([
                A, 
                QPointF(A.x() + r1, A.y()), 
                QPointF(A.x() + r1, A.y()+2*r1), 
                QPointF(B.x() - r1, A.y()+2*r1), 
                QPointF(B.x() - r1, B.y()), 
                B
            ])

        self.prepareGeometryChange()
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
