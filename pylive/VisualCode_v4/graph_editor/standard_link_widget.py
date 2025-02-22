from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

# from pylive.QtGraphEditor.widgets.graph_shapes import BaseNodeItem
from pylive.utils.qt import distribute_items_horizontal

from pylive.utils.geo import makeHorizontalRoundedPath, makeVerticalRoundedPath

class RoundedLinkWidget(QGraphicsPathItem):
    def __init__(self, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self.setPen( QPen(QColor('white'), 1) )

    def move(self, source:QGraphicsItem|QPointF, target:QGraphicsItem|QPointF):
        line = QLineF()

        match source:
            case QGraphicsItem():
                line.setP1(source.scenePos())
            case QPointF():
                line.setP1(source)
            case _:
                raise ValueError()

        match target:
            case QGraphicsItem():
                line.setP2(target.scenePos())
            case QPointF():
                line.setP2(target)
            case _:
                raise ValueError(f"target is not a widget or a point, got{target}")

        self.setPath( makeVerticalRoundedPath(line) )