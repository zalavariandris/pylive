from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

# from pylive.QtGraphEditor.widgets.graph_shapes import BaseNodeItem
from pylive.utils.qt import distribute_items_horizontal
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


        ### error label
        self._messages_label = QGraphicsTextItem(f"no errors")
        # self._messages_label.setDefaultTextColor("red")
        self._messages_label.setParentItem(self)
        self._messages_label.setParentItem(self)
        self._messages_label.adjustSize()
        self._messages_label.setPos(self.boundingRect().center().x(), self.boundingRect().bottom())
        self.message_timer:QTimer|None = None

        ###
        self.setHeading("Heading")
        self._color:None|Literal['primary', 'warning', 'error']|QColor = None

    def setColor(self, color:None|Literal['primary', 'warning', 'error']|QColor):
        self._color = color

    def showMessage(self, message:str, level:None|Literal['primary', 'warning', 'error']=None, timeout:float=0.0):
        match level:
            case None:
                self._messages_label.setHtml(f"<p>{message}</p>")
            case 'primary':
                self._messages_label.setHtml(f"<p style='color: palette(accent)'>{message}</p>")
            case 'warning':
                self._messages_label.setHtml(f"<p style='color: orange'>{message}</p>")
            case 'error':
                self._messages_label.setHtml(f"<p style='color: red'>{message}</p>")

        self._messages_label.adjustSize()

        if timeout>0.0:
            if self.message_timer:
                self.message_timer.stop()

            self.message_timer = QTimer()
            self.message_timer.setSingleShot(True)
            self.message_timer.timeout.connect(lambda: self.clearMessages())
            self.message_timer.start(int(timeout*1000))

    def clearMessages(self):
        self._messages_label.setHtml("")
        if self.message_timer:
            self.message_timer.stop()
            self.message_timer = None

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

        if self._color:
            match self._color:
                case QColor():
                    pen.setColor(self._color)
                case 'primary':
                    pen.setColor(self.palette().accent())
                case 'warning':
                    pen.setColor(QColor('orange'))
                case 'error':
                    pen.setColor(QColor('red'))

            if self.isSelected():
                pen.setWidth(2)

        painter.setPen(pen)

        rect.moveTo(QPoint(0,0))
        painter.drawRoundedRect(rect, 6,6)

    def setHeading(self, text:str):
        self._heading_label.setPlainText(text)
        self._heading_label.adjustSize()
        self.setPreferredSize(self._heading_label.textWidth(), 20)
        self.adjustSize()
        self._messages_label.setPos(self.boundingRect().center().x(), self.boundingRect().bottom())
        
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
    node_item.showMessage("info", level=None, timeout=1.0)

    node_item2 = PyNodeWidget()
    node_item2.showMessage("error", level='error')
    node_item2.setColor('error')
    node_item2.setPos(0,100)

    # node_item.clearMessages()

    scene = QGraphicsScene()
    scene.addItem(node_item)
    scene.addItem(node_item2)

    node_item.pressed.connect(lambda: print("node pressed"))

    view.setScene(scene)

    view.show()
    app.exec()