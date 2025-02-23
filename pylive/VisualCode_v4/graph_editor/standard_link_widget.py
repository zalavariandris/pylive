from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

# from pylive.QtGraphEditor.widgets.graph_shapes import BaseNodeItem
from pylive.utils.qt import distribute_items_horizontal

from pylive.utils.geo import makeHorizontalRoundedPath, makeVerticalRoundedPath

from pylive.utils.geo import makeArrowShape
class StandardLinkPath(QGraphicsLineItem):
    def __init__(self, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)

    def boundingRect(self):
        margin = self.pen().widthF()/2.0
        return self.shape().boundingRect().adjusted(-margin, -margin, margin, margin)

    def paint(self, painter:QPainter, option:QStyleOption, widget:QWidget|None=None):
        path = makeArrowShape(self.line(), 2)
        palette = widget.palette() if widget else QPalette()
        painter.setBrush(palette.text())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)

class RoundedLinkPath(QGraphicsLineItem):
    def __init__(self, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)

    def paint(self, painter:QPainter, option:QStyleOption, widget:QWidget|None=None):
        path = makeVerticalRoundedPath(self.line())
        # path = makeArrowShape(self.line(), 2)

        palette = widget.palette() if widget else QPalette()
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(palette.text(), 1))
        painter.drawPath(path)



    # def move(self, source:QGraphicsItem|QPointF, target:QGraphicsItem|QPointF):
    #     line = QLineF()

    #     match source:
    #         case QGraphicsItem():
    #             line.setP1(source.scenePos())
    #         case QPointF():
    #             line.setP1(source)
    #         case _:
    #             raise ValueError()

    #     match target:
    #         case QGraphicsItem():
    #             line.setP2(target.scenePos())
    #         case QPointF():
    #             line.setP2(target)
    #         case _:
    #             raise ValueError(f"target is not a widget or a point, got{target}")

    #     self._line = line
    #     self.prepareGeometryChange()
    #     self.update()


# class RoundedLinkWidget(QGraphicsItem):
#     def __init__(self, parent:QGraphicsItem|None=None):
#         super().__init__(parent=parent)
#         self._line = QLineF()

#     def boundingRect(self, /) -> QRectF:
#         rect = QRectF(self._line.p1(), self._line.p2()).normalized()
#         return rect

#     # def shape(self):
#     #     ...

#     def paint(self, painter:QPainter, option:QStyleOption, widget:QWidget|None=None):
#         pen = painter.pen()
#         pen.setColor(QColor("white"))
#         # if widget:
#         #     pen.setBrush(widget.palette().text())
#         painter.setPen(pen)
#         path = QPainterPath()
#         path.moveTo(self._line.p1())
#         path.lineTo(self._line.p2())
#         painter.drawPath(path)

#     def move(self, source:QGraphicsItem|QPointF, target:QGraphicsItem|QPointF):
#         line = QLineF()

#         match source:
#             case QGraphicsItem():
#                 line.setP1(source.scenePos())
#             case QPointF():
#                 line.setP1(source)
#             case _:
#                 raise ValueError()

#         match target:
#             case QGraphicsItem():
#                 line.setP2(target.scenePos())
#             case QPointF():
#                 line.setP2(target)
#             case _:
#                 raise ValueError(f"target is not a widget or a point, got{target}")

#         self._line = line
#         self.prepareGeometryChange()
#         self.update()


        # self.setPath( makeVerticalRoundedPath(line) )