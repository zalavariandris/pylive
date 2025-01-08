from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.QtLiveApp import display

view = QGraphicsView()
scene = QGraphicsScene()
view.setScene(scene)
display(view)
print("setup")

# %%update
import math


def fillet_polygon(polygon: QPolygonF, r: float) -> QPainterPath:
    points = [polygon.at(i) for i in range(polygon.size())]
    # Start the path
    path = QPainterPath()
    path.moveTo(points[0])
    for A, B, C in zip(points, points[1:], points[2:]):
        a1 = math.atan2(B.y() - A.y(), B.x() - A.x())
        a2 = -math.atan2(C.y() - B.y(), C.x() - B.x())
        rect = QRectF(B, B + QPointF(r * 2, r * 2))
        path.arcTo(rect, 0, 1)
    path.lineTo(points[-1])

    # Close the path
    return path


class RoundedLink(QGraphicsItem):
    def __init__(self, source, target):
        super().__init__(parent=None)
        source._links.append(self)
        target._links.append(self)
        self.source = source
        self.target = target

        self.polygon = QPolygonF()
        self.move()

    def boundingRect(self):
        m = 50
        return self.polygon.boundingRect().adjusted(-m, -m, m, m)

    def paint(self, painter, option, widget=None):
        rounded_path = fillet_polygon(self.polygon, r=30)
        painter.setPen(QPen(QColor("lightblue"), 5))
        painter.drawPath(rounded_path)

        painter.setPen(QPen(QBrush("red"), 2, Qt.PenStyle.DashLine))
        debug_path = QPainterPath()
        debug_path.addPolygon(self.polygon)
        painter.drawPath(debug_path)

    def move(self):
        A = self.source.pos() + self.source.boundingRect().center()
        B = self.target.pos() + self.target.boundingRect().center()
        self.polygon = QPolygonF(
            [A, QPointF(A.x() + 50, A.y()), QPointF(B.x() - 50, B.y()), B]
        )
        self.prepareGeometryChange()
        self.update()


class Node(QGraphicsEllipseItem):
    def __init__(self):
        super().__init__(0, 0, 25, 25)
        self._links = []
        self.setBrush(QColor("orange"))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            print("changed", self._links)
            for link in self._links:
                link.move()
        return super().itemChange(change, value)


scene.clear()
n1 = Node()
n1.setPos(-131, -48)
scene.addItem(n1)
n2 = Node()
n2.setPos(120, 187)
scene.addItem(n2)
link = RoundedLink(n1, n2)
scene.addItem(link)
link.move()
