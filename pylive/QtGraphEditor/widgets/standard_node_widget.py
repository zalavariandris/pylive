from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.NetworkXGraphEditor.nx_graph_shapes import BaseNodeItem, PortShape, distribute_items_horizontal
from pylive.QtGraphEditor.widgets.standard_port_widget import StandardPortWidget

class StandardNodeWidget(BaseNodeItem):
    pressed = Signal()
    inletPressed = Signal(str)
    outletPressed = Signal(str)
    def __init__(self, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        ### ports
        self._inlets:list[tuple[StandardPortWidget, QMetaObject.Connection]] = []
        self._outlets:list[tuple[StandardPortWidget, QMetaObject.Connection]] = []
        self.geometryChanged.connect(self._layout_ports)
        
        ### label
        self._heading_label = QGraphicsTextItem(f"Heading")
        self._heading_label.setPos(0,-2)
        self._heading_label.setParentItem(self)
        self._heading_label.adjustSize()
        self.setGeometry(QRectF(0, 0, self._heading_label.textWidth(), 20))


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
        self.setPreferredSize(self._heading_label.textWidth(),20)
        self.adjustSize()

    def insertInlet(self, idx, name):
        item = StandardPortWidget(name, self)
        connection = item.pressed.connect(lambda name=name: self.inletPressed.emit(name))
        self._inlets.append( (item, connection) )
        self._layout_ports()
        
    def removeInlet(self, idx:int):
        item, connection = self._inlets[idx]
        item.pressed.disconnect(connection)
        if scene:=item.scene():
            scene.removeItem(item)
        del self._inlets[idx]

    def insertOutlet(self, idx, name):
        item = StandardPortWidget(name, self)
        connection = item.pressed.connect(lambda name=name: self.outletPressed.emit(name))
        self._outlets.append( (item, connection) )
        self._layout_ports()
        
    def removeOutlet(self, idx:int):
        item, connection = self._outlets[idx]
        item.pressed.disconnect(connection)
        if scene:=item.scene():
            scene.removeItem(item)
        del self._outlets[idx]

    def _layout_ports(self):
        for item, connection in self._inlets:
            item.setPos(0, -4)
        distribute_items_horizontal([item for item, _ in self._inlets], self.boundingRect().adjusted(6,0,-6,0))
        
        for item, connection in self._outlets:
            item.setPos(0, self.geometry().height()+4)
        distribute_items_horizontal([item for item, _ in self._outlets], self.boundingRect().adjusted(6,0,-6,0))
        
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.pressed.emit()
        return super().mousePressEvent(event)


if __name__ == "__main__":
    app = QApplication()

    ### model state


    view = QGraphicsView()
    view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
    view.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
    view.setWindowTitle("NXNetworkScene")
    view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    node_item = StandardNodeWidget()
    for idx, name in enumerate(["in1", "in2", "in3"]):
        node_item.insertInlet(idx, name)

    for idx, name in enumerate(["out"]):
        node_item.insertOutlet(idx, name)
    scene = QGraphicsScene()
    scene.addItem(node_item)

    node_item.pressed.connect(lambda: print("node pressed"))
    node_item.inletPressed.connect(lambda name: print(f"inlet pressed: {name}"))
    node_item.outletPressed.connect(lambda name: print(f"outlet pressed: {name}"))

    view.setScene(scene)

    view.show()
    app.exec()