from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

# from pylive.QtGraphEditor.widgets.graph_shapes import BaseNodeItem
import qtawesome as qta

class IconFA(QGraphicsItem):
    def __init__(self, name:str, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self._name = name

    def boundingRect(self) -> QRectF:
        return QRectF(0.0, 0.0, 16.0, 16.0)

    def paint(self, painter:QPainter, option:QStyleOption, widget:QWidget|None=None):
        icon = qta.icon(self._name)
        icon.paint(painter, QRect(0,0,16,16))
        # icon = MaterialIcon(name=self._name)
        # pixmap = icon.pixmap(QSize(16,16))
        # painter.drawPixmap(pixmap)


class PyDebugWidget(QGraphicsItem):
    def __init__(self, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self._compiled: bool=True
        self._evaluated: bool=True
        self._error:Exception|None=None

        self._message_label = QGraphicsTextItem()
        self._message_label.setParentItem(self)
        self._message_label.setPos(16,28)


        ### compiled icon
        # ei.bulb, ei.idea-alt, ei.fire, ei.hourglass, ei.ok, ei.repeat, ei.refresh, ei.wrench, fa.gear, fa.warning

    def boundingRect(self)->QRectF:
        return QRectF(0,0,100, 56)

    def compiled(self):
        return self._compiled

    def setCompiled(self, compiled:bool):
        self._compiled = compiled
        self.update()

    def evaluated(self):
        return self._evaluated

    def setEvaluated(self, evaluated:bool):
        self._evaluated = evaluated
        self.update()

    def showError(self, error:Exception|None):
        self._error = error
        self.update()
        self._message_label.setHtml(f"<p style='color: red'>{error}</p>")

    def clearError(self):
        self._error = None
        self.update()
        self._message_label.setHtml("")
        
    def paint(self, painter:QPainter, option:QStyleOption, widget:QWidget|None=None):
        # painter.drawRoundedRect(self.boundingRect(), 5, 5)
        if self._compiled:
            color = QColor("lightgreen")
            painter.setPen(QPen(color, 1))
            painter.drawText(16,12, "compiled")
            icon = qta.icon('ph.flag-fill', color=color)
            icon.paint(painter, QRect(0,0,16,16))

        if self._evaluated:
            color = QColor("orange")
            painter.setPen(QPen(color, 1))
            painter.drawText(16,26, "evaluated")
            icon = qta.icon('mdi.lightbulb', color=color)
            icon.paint(painter, QRect(0,14,16,16))

        if self._error:
            icon = qta.icon('fa5s.exclamation-circle', color='red')
            icon.paint(painter, QRect(0,28,16,16))


class PyNodeWidget(QGraphicsWidget):
    pressed = Signal()
    scenePositionChanged = Signal()
    def __init__(self, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

        ### style
        self._pen = None

        ### label
        self._heading_label = QGraphicsTextItem(f"Heading")
        self._heading_label.setPos(0,-2)
        self._heading_label.setParentItem(self)
        self._heading_label.adjustSize()
        self.setGeometry(QRectF(0, 0, self._heading_label.textWidth(), 150))

        ###
        self.debug_widget = PyDebugWidget()
        self.debug_widget.setParentItem(self)
        self.debug_widget.setPos(self.boundingRect().right(), 0)

        ###
        self.setHeading("Heading")

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.scenePositionChanged.emit()
        return super().itemChange(change, value)

    def paint(self, painter, option:QStyleOption, widget=None):
        rect = self.geometry()

        pen = painter.pen()

        pen.setBrush(self.palette().text())
        if self.isSelected():
            pen.setBrush(self.palette().accent())

        painter.setPen(pen)

        rect.moveTo(QPoint(0,0))
        painter.drawRoundedRect(rect, 6,6)

    def setHeading(self, text:str):
        self._heading_label.setPlainText(text)
        self._heading_label.adjustSize()
        self.setPreferredSize(self._heading_label.textWidth(), 20)
        self.adjustSize()
        self.debug_widget.setPos(self.boundingRect().right(), 0)
        
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.pressed.emit()
        return super().mousePressEvent(event)


if __name__ == "__main__":
    app = QApplication()

    ### model state
    from pylive.VisualCode_v4.graph_editor.standard_port_widget import StandardPortWidget

    view = QGraphicsView()
    view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
    view.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
    view.setWindowTitle("NXNetworkScene")
    view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    view.resize(1024, 768)

    ### NODES
    node_item = PyNodeWidget()


    # node_item.clearMessages()

    scene = QGraphicsScene()
    scene.addItem(node_item)

    node_item.pressed.connect(lambda: print("node pressed"))

    view.setScene(scene)

    view.show()
    app.exec()