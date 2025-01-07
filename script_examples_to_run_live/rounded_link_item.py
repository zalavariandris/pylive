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

#%%update
import math

def fillet(points, radii) -> QPainterPath:
    if len(points) < 2:
        raise ValueError("At least 2 points needed")
    
    path = QPainterPath()
    path.moveTo(points[0])  # Start at the first point

    for p, r in zip(points[1:-1], radii):
        path.lineTo(p)

    # Add the final line to the last point
    path.lineTo(points[-1])

    return path

class RoundedLink(QGraphicsPathItem):
    def __init__(self, source, target):
        super().__init__(parent=None)
        source._links.append(self)
        target._links.append(self)
        self._source = source
        self._target = target
        self.setPen(QPen(QColor("white"), 3))
        self.move()
        
    def move(self):
        A = self._source.boundingRect().center()+self._source.pos()
        B = self._target.boundingRect().center()+self._target.pos()
        r1=min(23, (B.y()-A.y())/2)
        r2=min(36, (B.y()-A.y())/2)
        path = QPainterPath()
        path.moveTo(A)
        path.arcTo(QRectF(A.x()-r1,A.y(),r1*2,r1*2), 90, -90)
        path.lineTo(A.x()+r1, B.y()-r2)
        path.lineTo(B)
        self.setPath(path)
        
        
class Node(QGraphicsEllipseItem):
    def __init__(self):
        super().__init__(0,0,25,25)
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
n1.setPos(-131,-48)
scene.addItem(n1)
n2 = Node()
n2.setPos(120,187)
scene.addItem(n2)
link = RoundedLink(n1, n2)
scene.addItem(link)

