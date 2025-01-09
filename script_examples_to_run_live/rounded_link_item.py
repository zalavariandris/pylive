from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.QtLiveApp import display



# %%update
import math


import numpy as np

import math

def makeCircle(A: QPointF, B: QPointF, C: QPointF, D: QPointF, r: float) -> tuple[QPointF, QPointF]:
    def unit_vector(v: QPointF) -> QPointF:
        length = math.sqrt(v.x()**2 + v.y()**2)
        if abs(length) < 1e-10:
            raise ValueError("Zero length vector")
        return QPointF(v.x() / length, v.y() / length)
    
    def perpendicular_vector(v: QPointF) -> QPointF:
        return QPointF(-v.y(), v.x())
    
    def line_equation(point: QPointF, direction: QPointF, offset: float) -> tuple[QPointF, QPointF]:
        normal = perpendicular_vector(direction)
        unit_normal = unit_vector(normal)
        # Offset point in the direction of the normal
        point_offset = QPointF(
            point.x() + offset * unit_normal.x(),
            point.y() + offset * unit_normal.y()
        )
        return point_offset, unit_normal
    
    def intersection(p1: QPointF, n1: QPointF, p2: QPointF, n2: QPointF) -> QPointF:
        # Matrix equation solution for line intersection
        A = [[n1.x(), n1.y()], [n2.x(), n2.y()]]
        b = [n1.x() * p1.x() + n1.y() * p1.y(), 
             n2.x() * p2.x() + n2.y() * p2.y()]
        det = A[0][0] * A[1][1] - A[0][1] * A[1][0]
        if abs(det) < 1e-10:
            raise ValueError("Lines are parallel or nearly parallel")
        x = (b[0] * A[1][1] - b[1] * A[0][1]) / det
        y = (b[1] * A[0][0] - b[0] * A[1][0]) / det
        return QPointF(x, y)

    # Compute unit vectors for both line segments
    dir1 = unit_vector(QPointF(B.x() - A.x(), B.y() - A.y()))
    dir2 = unit_vector(QPointF(D.x() - C.x(), D.y() - C.y()))
    
    # Get offset lines (both directions)
    p1_plus, n1_plus = line_equation(A, dir1, r)
    p1_minus, n1_minus = line_equation(A, dir1, -r)
    p2_plus, n2_plus = line_equation(C, dir2, r)
    p2_minus, n2_minus = line_equation(C, dir2, -r)
    
    # Compute all possible intersections
    circle1 = intersection(p1_plus, n1_plus, p2_plus, n2_plus)
    circle2 = intersection(p1_minus, n1_minus, p2_minus, n2_minus)

    # Return both circle centers
    return circle1, circle2

from typing import Tuple
import math


def fillet(A: QPointF, B: QPointF, C: QPointF, r: float) -> Tuple[QPointF, QPointF, QPointF, float, float]:
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
        painter.setPen(QPen(QBrush("red"), 2, Qt.PenStyle.DotLine))
        debug_path = QPainterPath()
        debug_path.addPolygon(self.polygon)
        # painter.drawPath(debug_path)
        
        ### Fillet polygon
        points = [self.polygon.at(i) for i in range(self.polygon.size())]
        #r = 35
        path = QPainterPath()
        path.moveTo(points[0])
        for A, B, C, r in zip(points, points[1:], points[2:], self.radii):
            # calculate ellipse origin
            tangent1, tangent2, O1, start_angle, sweep_angle= fillet(A, B, C, r)
            rect = QRectF(QPointF(O1.x()-r, O1.y()-r), QSize(2*r,2*r)).normalized()

            if sweep_angle>0:
                path.arcTo(rect, -math.degrees(start_angle), math.degrees(sweep_angle)-180)
            else:
                path.arcTo(rect, -math.degrees(start_angle), math.degrees(sweep_angle)+180)
                
        path.lineTo(points[-1])
        color = QColor("lightblue")
        color.setAlpha(128)
        painter.setPen(QPen(color, 3))
        painter.drawPath(path)
        

    def move(self):
        A = self.source.pos() + self.source.boundingRect().center()
        B = self.target.pos() + self.target.boundingRect().center()
        
        dx = abs(B.x()-A.x())
        dy = abs(B.y()-A.y())
        r1 = min(50, min(dx/2, dy/2))
        r2 = min(dx, dy)-r1
        self.radii = [r1, r2]
        self.polygon = QPolygonF([
            A, 
            QPointF(A.x() + self.radii[0], A.y()), 
            QPointF(A.x() + self.radii[0], B.y()),
            B
        ])
        
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
            for link in self._links:
                link.move()
        return super().itemChange(change, value)


if __name__ == "__live__":
    from pylive.QtLiveApp import display

    view = QGraphicsView()
    scene = QGraphicsScene()
    view.setScene(scene)
    view.resize(800, 600)
    
    print("setup")

    scene.clear()
    n1 = Node()
    n1.setPos(-131, -48)
    scene.addItem(n1)
    n2 = Node()
    n2.setPos(120, 239)
    scene.addItem(n2)
    link = RoundedLink(n1, n2)
    scene.addItem(link)
    link.move()

    display(view)


#%% setup
if __name__ == "__main__":
    app = QApplication()
    view = QGraphicsView()
    scene = QGraphicsScene()
    view.setScene(scene)
    
    print("setup")

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

    view.show()
    app.exec()

