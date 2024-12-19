from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

import networkx as nx

from pylive.utils.geo import intersect_ray_with_rectangle


class NXGraphModel(QObject):
    nodesAdded = Signal(list)  # List[Hashable]
    nodesAboutToBeRemoved = Signal(list)  # List[Hashable]
    nodesPropertiesChanged = Signal(dict)  # Dict[Hashable, Dict[str, Any]]
    nodesRemoved = Signal(list)

    edgesAdded = Signal(list)  # List[Tuple[Hashable, Hashable, Hashable]]
    edgesAboutToBeRemoved = Signal(
        list
    )  # List[Tuple[Hashable, Hashable, Hashable]]
    edgesPropertiesChanged = Signal(
        dict
    )  # Dict[Tuple[Hashable, Hashable, Hashable], Dict[str, Any]]
    edgesRemoved = Signal(list)  # List[Tuple[Hashable, Hashable, Hashable]]

    def __init__(self, G: nx.MultiDiGraph = nx.MultiDiGraph(), parent=None):
        super().__init__(parent=parent)
        self.G = G

        for n in self.G.nodes:
            node = self.addNode(name=n)

        for e in self.G.edges:
            u, v, k = e

            self.addEdge(u, v, k)

    def patch(self, G: nx.MultiDiGraph):
        ...
        raise NotImplementedError("Not yet implemented")

    def __del__(self):
        del self.G
        # self.nodesAdded.disconnect()
        # self.nodesAboutToBeRemoved.disconnect()
        # self.nodesPropertyChanged.disconnect()
        # self.nodesRemoved.disconnect()
        # self.edgesAdded.disconnect()
        # self.edgesAboutToBeRemoved.disconnect()
        # self.edgesPropertyChanged.disconnect()
        # self.edgesRemoved.disconnect()

    def nodes(self) -> List[Hashable]:
        return [n for n in self.G.nodes]

    def addNode(self, n: Hashable, /, **props):
        print("add node", n)
        self.G.add_node(n, **props)
        self.nodesAdded.emit([n])
        self.nodesPropertiesChanged.emit({n: props})

    def setNodeProperties(self, n: Hashable, /, **props):
        # change guard TODO: find removed props
        change = {}
        for prop, value in props.items():
            if prop not in self.G.nodes[n] or value != self.G.nodes[n][prop]:
                change[prop] = value
        nx.set_node_attributes(self.G, {n: change})
        self.nodesPropertiesChanged.emit({n: change})

    def getNodeProperty(self, n: Hashable, name, /):
        return self.G.nodes[n][name]

    def remove_node(self, n: Hashable):
        self.nodesAboutToBeRemoved.emit([n])
        self.G.remove_node(n)
        self.nodesRemoved.emit([n])

    def edges(self) -> list[Tuple[Hashable, Hashable, Hashable]]:
        return [(u, v, k) for u, v, k in self.G.edges]

    def addEdge(
        self, u: Hashable, v: Hashable, k: Hashable | None = None, /, **props
    ):
        if u not in self.G.nodes:
            self.addNode(u)
        if v not in self.G.nodes:
            self.addNode(v)

        self.G.add_edge(u, v, k, **props)
        self.edgesAdded.emit([(u, v, k)])

    def remove_edge(self, u: Hashable, v: Hashable, k: Hashable):
        self.edgesAboutToBeRemoved.emit([(u, v, k)])
        self.G.remove_edge(u, v, k)
        self.edgesRemoved.emit([(u, v, k)])

    def setEdgeProperties(
        self, u: Hashable, v: Hashable, k: Hashable, /, **props
    ):
        nx.set_edge_attributes(self.G, {(u, v, k): props})
        self.edgesPropertiesChanged.emit([(u, v, k)], list(props.keys()))

    def getEdgeProperty(self, u: Hashable, v: Hashable, k: Hashable, prop, /):
        return self.G.edges[u, v, k][prop]


from pylive.QtGraphEditor.editable_text_item import EditableTextItem


class StandardNodeWidget(QGraphicsWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setGeometry(QRect(0, 0, 100, 26))
        # Enable dragging and selecting
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)

        self.label = EditableTextItem(parent=self)
        self.label.setPos(5, 5)
        self.label.setTextWidth(self.geometry().width() - 10)
        self.label.setText("Hello")

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        # Enable editing subitems on double-click
        """parent node must manually cal the double click event,
        because an item nor slectable nor movable will not receive press events
        """

        # Check if double-click is within the text item’s bounding box
        if self.label.contains(self.mapFromScene(event.scenePos())):
            # Forward the event to label if clicked inside it
            self.label.mouseDoubleClickEvent(event)
        else:
            print("NodeItem->mouseDoubleClickEvent")
            super().mouseDoubleClickEvent(event)

    def paint(
        self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None
    ):
        # option.direction
        # option.fontMetrics
        # option.palette
        # option.rect
        # option.state
        # option.styleObject
        # option.levelOfDetailFromTransform

        # Draw the node rectangle
        palette: QPalette = option.palette  # type: ignore
        state: QStyle.StateFlag = option.state  # type: ignore

        painter.setBrush(palette.base())
        # painter.setBrush(Qt.NoBrush)

        pen = QPen(palette.text().color(), 1)
        pen.setCosmetic(True)
        pen.setWidthF(2)
        if state & QStyle.StateFlag.State_Selected:
            pen.setColor(palette.accent().color())
        painter.setPen(pen)
        painter.drawRoundedRect(
            0.5, 0.5, self.geometry().width(), self.geometry().height(), 3, 3
        )
