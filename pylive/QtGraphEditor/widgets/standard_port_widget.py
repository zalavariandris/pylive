from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

class StandardPortWidget(QGraphicsWidget):
    pressed = Signal()
    def __init__(self, label:str, parent:QGraphicsItem|None):
        super().__init__(parent=parent)
        self.setAcceptHoverEvents(True)

        self._circle_item = QGraphicsEllipseItem(QRectF(-2.5,-2.5,5,5))
        self._circle_item.setBrush(self.palette().text())
        self._circle_item.setPen(Qt.PenStyle.NoPen)
        self._circle_item.setParentItem(self)
        self._circle_item.setAcceptHoverEvents(True)


        self._nameitem = QGraphicsTextItem(f"{label}")
        self._nameitem.setParentItem(self)
        self._nameitem.setPos(-6,-26)
        self._nameitem.hide()
        self._nameitem.setAcceptHoverEvents(True)
        self.setFiltersChildEvents(True)

    def boundingRect(self) -> QRectF:
        ellipse_bbox = QRectF(-6,-6,12,12)
        return ellipse_bbox

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.pressed.emit()
        return super().mousePressEvent(event)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        self._circle_item.setPen(QPen(self.palette().text(), 2))
        self._nameitem.show()

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        self._circle_item.setPen(Qt.PenStyle.NoPen)
        self._nameitem.hide()