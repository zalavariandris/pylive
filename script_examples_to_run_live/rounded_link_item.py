from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.QtLiveApp import display


# %%update
import math


import numpy as np

import math


from typing import Tuple
import math

def makeHorizontalRoundedPath(line: QLineF):
    """Creates a rounded path between two points with automatic radius adjustment.
    
    Args:
        line: QLineF defining start and end points
        direction: Layout direction (default: LeftToRight)
    
    Returns:
        QPainterPath: A path with rounded corners connecting the points
    """
    A, B = line.p1(), line.p2()
    dx = B.x() - A.x()
    dy = B.y() - A.y()
    
    path = QPainterPath()
    path.moveTo(A)
    
    # Base radius with constraints
    r = 27
    is_leftward = dx < 0
    
    if is_leftward:
        r1 = min(r, min(abs(dx/4), abs(dy/4)))
        r2 = min(abs(dx), abs(dy) - r1 * 3)
    else:
        r1 = min(r, min(abs(dx/2), abs(dy/2)))
        r2 = min(abs(dx), abs(dy)) - r1
    
    # Define arc parameters based on direction
    if is_leftward:
        create_leftward_path(path, A, B, r1, r2, dy > 0)
    else:
        create_rightward_path(path, A, B, r1, r2, dy > 0)
    
    path.lineTo(B)
    return path

def create_leftward_path(path: QPainterPath, A: QPointF, B: QPointF, r1: float, r2: float, is_downward: bool):
    """Creates the path segments for leftward movement."""
    if is_downward:
        path.arcTo(A.x() - r1, A.y(), r1 * 2, r1 * 2, 90, -180)
        path.arcTo(B.x() - r1, A.y() + r2 * 2 + r1 * 2, r2 * 2, -r2 * 2, -90, -90)
        path.arcTo(B.x() + r1, B.y() - r1 * 2, -r1 * 2, r1 * 2, 0, -90)
    else:
        path.arcTo(A.x() - r1, A.y(), r1 * 2, -r1 * 2, 90, -180)
        path.arcTo(B.x() - r1, A.y() - r2 * 2 - r1 * 2, r2 * 2, r2 * 2, -90, -90)
        path.arcTo(B.x() + r1, B.y() + r1 * 2, -r1 * 2, -r1 * 2, 0, -90)

def create_rightward_path(path: QPainterPath, A: QPointF, B: QPointF, r1: float, r2: float, is_downward: bool):
    """Creates the path segments for rightward movement."""
    if is_downward:
        path.arcTo(A.x() - r1, A.y(), r1 * 2, r1 * 2, 90, -90)
        path.arcTo(A.x() + r1, B.y() - r2 * 2, r2 * 2, r2 * 2, 180, 90)
    else:
        path.arcTo(A.x() - r1, A.y(), r1 * 2, -r1 * 2, 90, -90)
        path.arcTo(A.x() + r1, B.y() + r2 * 2, r2 * 2, -r2 * 2, 180, 90)

def makeVerticalRoundedPath(line: QLineF):
    """Creates a rounded path between two points with automatic radius adjustment.
    
    Args:
        line: QLineF defining start and end points
        direction: Layout direction (default: TopToBottom)
    
    Returns:
        QPainterPath: A path with rounded corners connecting the points
    """
    A, B = line.p1(), line.p2()
    dx = B.x() - A.x()
    dy = B.y() - A.y()
    
    path = QPainterPath()
    path.moveTo(A)
    
    # Base radius with constraints
    r = 27
    is_upward = dy < 0
    
    if is_upward:
        r1 = min(r, min(abs(dy/4), abs(dx/4)))
        r2 = min(abs(dy), abs(dx) - r1 * 3)
    else:
        r1 = min(r, min(abs(dy/2), abs(dx/2)))
        r2 = min(abs(dy), abs(dx)) - r1
    
    # Define arc parameters based on direction
    if is_upward:
        create_upward_path(path, A, B, r1, r2, dx > 0)
    else:
        create_downward_path(path, A, B, r1, r2, dx > 0)
    
    path.lineTo(B)
    return path

def create_downward_path(path: QPainterPath, A: QPointF, B: QPointF, r1: float, r2: float, is_rightward: bool):
    """Creates the path segments for downward movement."""
    if is_rightward:
        path.arcTo(A.x(), A.y() - r1, r1 * 2, r1 * 2, 180, 90)
        path.arcTo(B.x()-r2*2,  A.y() + r1, r2 * 2, r2 * 2, 90, -90)
    else:
        path.arcTo(A.x(), A.y() - r1, -r1 * 2, r1 * 2, 180, 90)
        path.arcTo(B.x() + r2 * 2, A.y() + r1, -r2 * 2, r2 * 2, 90, -90)

def create_upward_path(path: QPainterPath, A: QPointF, B: QPointF, r1: float, r2: float, is_rightward: bool):
    """Creates the path segments for upward movement."""
    if is_rightward:
        path.arcTo(A.x(), A.y() - r1, r1 * 2, r1 * 2, 180, 180)
        path.arcTo(A.x() + r2 * 2 + r1 * 2, B.y() - r1, -r2 * 2, r2 * 2, 0, 90)
        path.arcTo(B.x() - r1 * 2, B.y() + r1, r1 * 2, -r1 * 2, 270, 90)
    else:
        path.arcTo(A.x(), A.y() - r1, -r1 * 2, r1 * 2, 180, 180)
        path.arcTo(A.x() - r2 * 2 - r1 * 2, B.y() - r1, r2 * 2, r2 * 2, 0, 90)
        path.arcTo(B.x() + r1 * 2, B.y() + r1, -r1 * 2, -r1 * 2, 270, 90)


class HoizontalLink(QAbstractGraphicsShapeItem):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._links = []
        self.setBrush(QColor("orange"))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

    def makeRoundedPath(self):
        return makeHorizontalRoundedPath(QLineF(
            self.mapFromParent(QPointF()), 
            self.mapFromParent(self.pos())
        ))

    def boundingRect(self) -> QRectF:
        return self.makeRoundedPath().boundingRect().adjusted(-20, -20, 100, 20)

    def paint(self, painter, option, widget=None):
        # painter.drawRect(self.boundingRect())
        painter.drawPath(self.makeRoundedPath())
        painter.drawText(0,0, "Horizontal target")\

class VerticalLink(QAbstractGraphicsShapeItem):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._links = []
        self.setBrush(QColor("orange"))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

    def makeRoundedPath(self):
        return makeVerticalRoundedPath(QLineF(
            self.mapFromParent(QPointF()), 
            self.mapFromParent(self.pos())
        ))

    def boundingRect(self) -> QRectF:
        return self.makeRoundedPath().boundingRect().adjusted(-20, -20, 100, 20)

    def paint(self, painter, option, widget=None):
        # painter.drawRect(self.boundingRect())
        painter.drawPath(self.makeRoundedPath())
        painter.drawText(0,0, "Vertical target")


def main()->QWidget:
    view = QGraphicsView()
    scene = QGraphicsScene()
    scene.setSceneRect(-9999, -9999, 9999*2, 9999*2)
    view.setScene(scene)
    view.resize(800, 600)
    scene.clear()
    horizontal = HoizontalLink()
    horizontal.setPos(300, -100)
    scene.addItem(horizontal)

    vertical = VerticalLink()
    vertical.setPos(276, 93)
    scene.addItem(vertical)

    return view

if __name__ == "__live__":
    from pylive.QtLiveApp import display
    display(main())


# %% setup
if __name__ == "__main__":
    app = QApplication()
    view = main()
    view.show()
    app.exec()
