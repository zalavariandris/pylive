from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


class LinkMixin:
    def __init__(self):
        self.__source: LinkableMixin
        self.__target: LinkableMixin

    def setSource(self, source: "LinkableMixin"):
        source.edges().append(self)
        self.__source = source

    def source(self) -> "LinkableMixin":
        return self.__source

    def setTarget(self, target: "LinkableMixin"):
        self.__target = target

    def target(self):
        return self.__target

    def updatePosition(self):
        ...


class LinkableMixin(QGraphicsItem):
    "responsible to notify the link if it needs to update"

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.__edges: list[LinkMixin] = []
        print("LinkableMixin->__init__")

    def edges(self) -> list[LinkMixin]:
        return self.__edges

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        match change:
            case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
                for edge in self.__edges:
                    edge.updatePosition()
            case _:
                return super().itemChange(change, value)


# class AcceptLinkMixin(QGraphicsItem):
#     """responsible to handle LinkDrag events"""

#     def connectionEnterEvent(self, event):
#         """called when a connection is trying to link to this item
#         ignore the event, to reject the connection.
#         if the event is ignored, further connection events wont be called.
#         """
#         ...

#     def connectionMoveEvent(self, event):
#         ...

#     def connectionDropEvent(self, event):
#         ...


class Vertex(QGraphicsItem, Linkable):
    ...


class MyOutletWidget(QGraphicsItem):
    def __init__(
        self,
        view: "NXGraphView",
        label: str,
        parent: QGraphicsItem | None = None,
    ):
        super().__init__(parent=parent)
        self._view = view
        self._label = label

        self._isHighlighted = False
        self.setAcceptHoverEvents(True)

    def label(self) -> str:
        return self._label

    def setLabel(self, text: str):
        self._label = text

    def setHighlighted(self, value):
        self._isHighlighted = value
        self.update()

    def isHighlighted(self):
        return self._isHighlighted

    def boundingRect(self) -> QRectF:
        try:
            fm = QFontMetrics(self.scene().font())
        except AttributeError:
            fm = QFontMetrics(QApplication.instance().font())

        ellipse_bbox = QRectF(0, 0, 10, 10)
        text_width = fm.horizontalAdvance(self._label)
        text_height = fm.height()

        text_pos = QPointF(12, 0)
        text_bbox = QRectF(text_pos, QSizeF(text_width, text_height))
        return ellipse_bbox.united(text_bbox)

    def hoverEnterEvent(self, event):
        self.setHighlighted(True)

    def hoverLeaveEvent(self, event):
        self.setHighlighted(False)

    def palette(self) -> QPalette:
        if palette := getattr(self, "_palette", None):
            return palette
        elif parentWidget := self.parentWidget():
            return parentWidget.palette()
        elif scene := self.scene():
            return scene.palette()
        elif app := QApplication.instance():
            return app.palette()
        else:
            return QPalette()

    def paint(self, painter, option, widget=None):
        ### draw label
        try:
            fm = QFontMetrics(self.scene().font())
        except AttributeError:
            fm = QFontMetrics(QApplication.instance().font())

        painter.setPen(QPen(self.palette().text(), 1))
        if self.isHighlighted():
            painter.setPen(QPen(self.palette().accent(), 1))

        text_width = fm.horizontalAdvance(self._label)
        text_height = fm.height()

        text_pos = QPointF(0, text_height - 2)
        painter.drawText(text_pos, self._label)

        painter.drawEllipse(QRectF(text_width + 2, 7, 6, 6))

        # painter.setBrush(Qt.NoBrush)
        # painter.drawRect(self.boundingRect())

    ### INITIATE LINKS ###
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        connect = Connect(self)
        connect.exec()

        if target_widget := connect.target():  # TODO: Move To Delegatte
            if isinstance(target_widget, MyInletWidget):
                if not self._view._model:
                    return
                u = self._view._widget_to_node_map[self.parentItem()]
                v = self._view._widget_to_node_map[target_widget.parentItem()]
                k = target_widget.label()
                self._view._model.addEdge(u, v, k)


class MyInletWidget(QGraphicsItem):
    def __init__(
        self,
        view: "NXGraphView",
        label: str,
        parent: QGraphicsItem | None = None,
    ):
        super().__init__(parent=parent)
        self._view = view
        self._label = label

        self._isHighlighted = False

        self.setAcceptHoverEvents(True)

    def setHighlighted(self, value):
        self._isHighlighted = value
        self.update()

    def isHighlighted(self):
        return self._isHighlighted

    def label(self) -> str:
        return self._label

    def setLabel(self, text: str):
        self._label = text

    def boundingRect(self) -> QRectF:
        try:
            fm = QFontMetrics(self.scene().font())
        except AttributeError:
            fm = QFontMetrics(QApplication.instance().font())

        ellipse_bbox = QRectF(0, 0, 10, 10)
        text_width = fm.horizontalAdvance(self._label)
        text_height = fm.height()

        text_pos = QPointF(12, 0)
        text_bbox = QRectF(text_pos, QSizeF(text_width, text_height))
        return ellipse_bbox.united(text_bbox)

    def hoverEnterEvent(self, event):
        self.setHighlighted(True)

    def hoverLeaveEvent(self, event):
        self.setHighlighted(False)

    def palette(self) -> QPalette:
        if palette := getattr(self, "_palette", None):
            return palette
        elif parentWidget := self.parentWidget():
            return parentWidget.palette()
        elif scene := self.scene():
            return scene.palette()
        elif app := QApplication.instance():
            return app.palette()
        else:
            return QPalette()

    def paint(self, painter, option, widget=None):
        ### draw label
        try:
            fm = QFontMetrics(self.scene().font())
        except AttributeError:
            fm = QFontMetrics(QApplication.instance().font())

        painter.setPen(QPen(self.palette().text(), 1))
        if self.isHighlighted():
            painter.setPen(QPen(self.palette().accent(), 1))

        painter.drawEllipse(QRectF(2, 7, 6, 6))

        text_height = fm.height()

        text_pos = QPointF(12, text_height - 2)
        painter.drawText(text_pos, self._label)

    @override
    def sceneEvent(self, event: QEvent) -> bool:
        if event.type() == ConnectionEnterType:
            self.connectionEnterEvent(cast(ConnectionEvent, event))
        elif event.type() == ConnectionLeaveType:
            self.connectionLeaveEvent(cast(ConnectionEvent, event))
        elif event.type() == ConnectionMoveType:
            self.connectionMoveEvent(cast(ConnectionEvent, event))
        elif event.type() == ConnectionDropType:
            self.connectionDropEvent(cast(ConnectionEvent, event))
        else:
            ...

        return super().sceneEvent(event)

    def connectionEnterEvent(self, event: ConnectionEvent) -> None:
        if event.source() != self:
            event.setAccepted(True)
            self.setHighlighted(True)
            return
        event.setAccepted(False)

    def connectionLeaveEvent(self, event: ConnectionEvent) -> None:
        self.setHighlighted(False)

    def connectionMoveEvent(self, event: ConnectionEvent) -> None:
        ...

    def connectionDropEvent(self, event: ConnectionEvent) -> None:
        if event.source() != self:
            self.setHighlighted(False)
            event.setAccepted(True)
            return

        event.setAccepted(False)


class MyNodeWidget(GraphicsNodeItem):
    def __init__(self, title, inlets, outlets, view):
        super().__init__(title=title)
        self._view = view

        self._inlets: list[QGraphicsItem] = []
        self._outlets: list[QGraphicsItem] = []
        for inlet in inlets:
            self._addInlet(inlet)
        for outlet in outlets:
            self._addOutlet(outlet)

    @override
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        match change:
            case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
                graph = cast(NXGraphScene, self.scene())
                graph.updateNodePosition(self)
            case _:
                return super().itemChange(change, value)

    def boundingRect(self) -> QRectF:
        return (
            super()
            .boundingRect()
            .united(self.childrenBoundingRect())
            .adjusted(-4, 0, 4, 2)
        )

    def _addInlet(self, inlet_widget: QGraphicsItem):
        inlet_widget.setParentItem(self)
        self._inlets.append(inlet_widget)
        self.layoutPorts()
        self.update()

    def _removeInlet(self, inlet_widget: QGraphicsItem):
        self._inlets.remove(inlet_widget)
        inlet_widget.setParentItem(None)
        if scene := inlet_widget.scene():
            scene.removeItem(inlet_widget)
        self.layoutPorts()
        self.update()

    def _addOutlet(self, outlet_widget: QGraphicsItem):
        outlet_widget.setParentItem(self)
        self._outlets.append(outlet_widget)
        self.layoutPorts()
        self.update()

    def _removeOutlet(self, outlet_widget: QGraphicsItem):
        self._outlets.remove(outlet_widget)
        outlet_widget.setParentItem(self)
        if scene := outlet_widget.scene():
            scene.removeItem(outlet_widget)
        self.layoutPorts()
        self.update()

    def layoutPorts(self):
        y = 14  # header heighn
        for inlet_widget in self._inlets:
            inlet_widget.setPos(4, y)
            y += inlet_widget.boundingRect().height()

        for outlet_widget in self._outlets:
            outlet_widget.setPos(4, y)
            y += outlet_widget.boundingRect().height()


if __name__ == "__main__":
    app = QApplication()
    view = QGraphicsView()
    scene = QGraphicsScene()
    view.setScene(scene)

    n1 = Vertex()
    n2 = Vertex()

    l1 = Link()
    l1.setSource(n1)
    l1.setTarget(n2)

    scene.addItem(n1)
    scene.addItem(n2)

    view.show()

    app.exec()
