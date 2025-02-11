

from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

class CircleWidget(QGraphicsWidget):
    """A simple Circle QGraphicsWidget that can be useed with QGraphicsLayouts"""
    def __init__(self, radius: float, parent=None):
        super().__init__()
        self.circle_item = QGraphicsEllipseItem(
            QRectF(0, 0, radius * 2, radius * 2), self
        )
        text_color = self.palette().color(QPalette.ColorRole.Text)
        self.circle_item.setBrush(Qt.BrushStyle.NoBrush)
        self.circle_item.setPen(QPen(text_color, 1.4))

    def sizeHint(self, which, constraint=QSizeF()):
        circle_rect = self.circle_item.rect()
        return circle_rect.size()
