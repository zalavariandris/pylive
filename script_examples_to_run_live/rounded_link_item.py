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

def makeRoundedPath(line:QLineF):
    A = line.p1()
    B = line.p2()
    Ax, Ay = A.x(), A.y()
    Bx, By = B.x(), B.y()
    dx = Bx - Ax
    dy = By - Ay

    path = QPainterPath()
    path.moveTo(A)
    r = 27
    if dx < 0:
        r1 = min(r, min(abs(dx/4), abs(dy/4)))
        r2 = min(abs(dx), abs(dy)-r1*3)
        # angle = abs(angle)
        if dy > 0:
            # pen.setColor("cyan") # upper left DONE
            angle = math.degrees(math.atan2(dy-(r1+r2)*2, dx-(r1+r2)))
            path.arcTo(
                Ax-r1, Ay, r1*2,r1*2, 90, -180
            )
            path.arcTo(
                Bx-r1, 
                Ay+r2*2+r1*2, 
                r2*2,
                -r2*2, 
                -90, -90
            )
            path.arcTo(
                Bx+r1,
                By-r1*2,
                -r1*2,
                r1*2,
                0,-90
            )
        else:
            # pen.setColor("yellow") # upper left DONE
            angle = math.degrees(math.atan2(dy-(r1+r2)*2, dx-(r1+r2)))
            path.arcTo(
                Ax-r1, Ay, r1*2,-r1*2, 90, -180
            )
            path.arcTo(
                Bx-r1, 
                Ay-r2*2-r1*2, 
                r2*2,
                r2*2, 
                -90, -90
            )
            path.arcTo(
                Bx+r1,
                By+r1*2,
                -r1*2,
                -r1*2,
                0,-90
            )
    else:
        r1 = min(r, min(abs(dx/2), abs(dy/2)))
        r2 = min(abs(dx), abs(dy))-r1
        # angle = abs(angle)
        if dy > 0:
            # pen.setColor("red") # lower right DONE
            path.arcTo(
                Ax-r1, Ay, r1*2,r1*2, 90, -90
            )
            path.arcTo(
                Ax+r1,
                By-r2*2,
                r2*2,
                r2*2,
                180,
                90
            )
        else:
            # pen.setColor("green") #upper right DONE
            r1 = min(r, min(abs(dx/2), abs(dy/2)))
            r2 = min(abs(dx), abs(dy))-r1
            path.arcTo(
                Ax-r1, Ay, r1*2,-r1*2, 90, -90
            )
            path.arcTo(
                Ax+r1,
                By+r2*2,
                r2*2,
                -r2*2,
                180,
                90
            )
    path.lineTo(B)
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
        m = 200
        return self.polygon.boundingRect().adjusted(-m, -m, m, m)

    def paint(self, painter, option, widget=None):
        pen = QPen()
        pen.setColor("white")
        A = self.source.pos() + self.source.boundingRect().center()
        B = self.target.pos() + self.target.boundingRect().center()
        # Ax, Ay = A.x(), A.y()
        # Bx, By = B.x(), B.y()
        # dx = Bx - Ax
        # dy = By - Ay

        # path = QPainterPath()
        # path.moveTo(A)
        # r = 27
        # if dx < 0:
        #     r1 = min(r, min(abs(dx/4), abs(dy/4)))
        #     r2 = min(abs(dx), abs(dy)-r1*3)
        #     # angle = abs(angle)
        #     if dy > 0:
        #         pen.setColor("cyan") # upper left DONE
        #         angle = math.degrees(math.atan2(dy-(r1+r2)*2, dx-(r1+r2)))
        #         path.arcTo(
        #             Ax-r1, Ay, r1*2,r1*2, 90, -180
        #         )
        #         path.arcTo(
        #             Bx-r1, 
        #             Ay+r2*2+r1*2, 
        #             r2*2,
        #             -r2*2, 
        #             -90, -90
        #         )
        #         path.arcTo(
        #             Bx+r1,
        #             By-r1*2,
        #             -r1*2,
        #             r1*2,
        #             0,-90
        #         )
        #     else:
        #         pen.setColor("yellow") # upper left DONE
        #         angle = math.degrees(math.atan2(dy-(r1+r2)*2, dx-(r1+r2)))
        #         path.arcTo(
        #             Ax-r1, Ay, r1*2,-r1*2, 90, -180
        #         )
        #         path.arcTo(
        #             Bx-r1, 
        #             Ay-r2*2-r1*2, 
        #             r2*2,
        #             r2*2, 
        #             -90, -90
        #         )
        #         path.arcTo(
        #             Bx+r1,
        #             By+r1*2,
        #             -r1*2,
        #             -r1*2,
        #             0,-90
        #         )
        # else:
        #     r1 = min(r, min(abs(dx/2), abs(dy/2)))
        #     r2 = min(abs(dx), abs(dy))-r1
        #     # angle = abs(angle)
        #     if dy > 0:
        #         pen.setColor("red") # lower right DONE
        #         path.arcTo(
        #             Ax-r1, Ay, r1*2,r1*2, 90, -90
        #         )
        #         path.arcTo(
        #             Ax+r1,
        #             By-r2*2,
        #             r2*2,
        #             r2*2,
        #             180,
        #             90
        #         )
        #     else:
        #         pen.setColor("green") #upper right DONE
        #         r1 = min(r, min(abs(dx/2), abs(dy/2)))
        #         r2 = min(abs(dx), abs(dy))-r1
        #         path.arcTo(
        #             Ax-r1, Ay, r1*2,-r1*2, 90, -90
        #         )
        #         path.arcTo(
        #             Ax+r1,
        #             By+r2*2,
        #             r2*2,
        #             -r2*2,
        #             180,
        #             90
        #         )
        # path.lineTo(B)
        path = makeRoundedPath(QLineF(A, B))

        painter.setPen(pen)
        painter.drawPath(path)

    def move(self):
        A = self.source.pos() + self.source.boundingRect().center()
        B = self.target.pos() + self.target.boundingRect().center()

        dx = abs(B.x() - A.x())
        dy = abs(B.y() - A.y())
        r1 = min(50, min(dx / 2, dy / 2))
        r2 = min(dx, dy) - r1
        self.radii = [r1, r2]
        self.polygon = QPolygonF(
            [
                A,
                QPointF(A.x() + self.radii[0], A.y()),
                QPointF(A.x() + self.radii[0], B.y()),
                B,
            ]
        )

        self.prepareGeometryChange()
        self.update()


class Node(QGraphicsPolygonItem):
    def __init__(self):
        super().__init__(
            QPolygonF([QPointF(0, 0), QPointF(-20, -20), QPointF(-20, 20)])
        )
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
    t1 = QGraphicsTextItem("n1", n1)
    n1.setPos(0, 0)
    scene.addItem(n1)
    n2 = Node()
    t2 = QGraphicsTextItem("n2", n2)
    n2.setPos(-228, 338)
    scene.addItem(n2)
    link = RoundedLink(n1, n2)
    scene.addItem(link)
    link.move()

    display(view)


# %% setup
if __name__ == "__main__":
    app = QApplication()
    view = QGraphicsView()
    scene = QGraphicsScene()
    view.setScene(scene)

    print("setup")

    scene.clear()
    n1 = Node()
    t1 = QGraphicsTextItem("n1", n1)
    n1.setPos(-131, -155)
    scene.addItem(n1)
    n2 = Node()
    t1 = QGraphicsTextItem("n2", n1)
    n2.setPos(120, 55)
    scene.addItem(n2)
    link = RoundedLink(n1, n2)
    scene.addItem(link)
    link.move()

    view.show()
    app.exec()
