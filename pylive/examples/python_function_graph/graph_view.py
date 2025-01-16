from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

# from standard_graph_delegate import StandardGraphDelegate
from pylive.QtGraphEditor.dag_graph_graphics_scene import TextWidget
from pylive.utils.unique import make_unique_id, make_unique_name

from graph_model import GraphModel

from pylive.QtGraphEditor.NetrowkXGraphEditor.link_graphics_items import (
    makeLineBetweenShapes,
)
from pylive.QtGraphEditor.NetrowkXGraphEditor.qgraphics_arrow_item import (
    QGraphicsArrowItem,
)


class PinWidget(QGraphicsWidget):
    def __init__(
        self,
        i: Hashable,
        node: Optional["NodeWidget"],
        view: "GraphView",
    ) -> None:
        QGraphicsWidget.__init__(self, parent=node)

        self._node = node
        self._view = view
        self._i = i

    @override
    def sizeHint(
        self, which: Qt.SizeHint, constraint: QSizeF | QSize = QSizeF()
    ) -> QSizeF:
        return QSizeF(20, 20)

    def paint(
        self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None
    ):
        r = 10
        painter.drawEllipse(0, 0, r, r)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self._view.initiateConnection(self)


class NodeWidget(QGraphicsWidget):
    def __init__(
        self,
        n: Hashable,
        view: "GraphView",
        parent: Optional[QGraphicsItem] = None,
    ) -> None:
        QGraphicsWidget.__init__(self, parent=parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)

        self._view = view
        self._n = n

    @override
    def sizeHint(
        self, which: Qt.SizeHint, constraint: QSizeF | QSize = QSizeF()
    ) -> QSizeF:
        padding = 4
        fm = QFontMetrics(self.font())
        text_width = fm.horizontalAdvance(f"{self._n}")
        return QSizeF(
            padding + text_width + padding, padding + fm.ascent() + padding
        )

    def paint(
        self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None
    ):
        padding = 4
        # draw outline
        painter.drawRoundedRect(option.rect, 4, 4)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        print("press")
        return super().mousePressEvent(event)


class GraphDelegate(QObject):
    def nodeFactory(self, view, graph, n) -> QGraphicsItem:
        widget = NodeWidget(view=view, n=n)
        widget.setLayout(QGraphicsLinearLayout())
        header = TextWidget(f"{n}")
        widget.layout().addItem(header)
        return widget

    def edgeFactory(
        self, view, graph, source_node, target_node
    ) -> QGraphicsItem:
        arrow = QGraphicsArrowItem()
        pen = QPen(view.palette().color(QPalette.ColorRole.Text), 1.5)
        arrow.setPen(pen)

        def update_link():
            arrow.setLine(
                makeLineBetweenShapes(
                    source_node.geometry(), target_node.geometry()
                )
            )

        update_link()

        source_node.geometryChanged.connect(update_link)
        target_node.geometryChanged.connect(update_link)
        return arrow


class GraphView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setRenderHints(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        scene = QGraphicsScene()
        scene.setSceneRect(QRect(-9999 // 2, -9999 // 2, 9999, 9999))
        self.setScene(scene)
        # scene.installEventFilter(self)
        self._delegate = GraphDelegate()
        self._item_to_widget_map = dict()
        self._widget_to_item_map = dict()
        self._graphmodel: GraphModel | None = None

    def nodeWidget(self, n: Hashable):
        return self._item_to_widget_map[n]

    def model(self) -> GraphModel | None:
        return self._graphmodel

    def setModel(self, graphmodel: GraphModel):
        self._graphmodel = graphmodel

        self._graphmodel.nodesAdded.connect(self.handleNodesAdded)
        self._graphmodel.nodesAboutToBeRemoved.connect(self.handleNodesRemoved)
        self._graphmodel.nodesChanged.connect(
            self.handleNodesPropertiesChanged
        )

        self._graphmodel.edgesAdded.connect(self.handleEdgesAdded)
        self._graphmodel.edgesAboutToBeRemoved.connect(self.handleEdgesRemoved)
        self._graphmodel.edgesPropertiesChanged.connect(
            self.handleEdgesPropertiesChanged
        )

    def handleNodesAdded(self, nodes: List[Hashable]):
        for n in nodes:
            widget = self._delegate.nodeFactory(
                view=self, graph=self._graphmodel, n=n
            )

            self._item_to_widget_map[n] = widget
            self._widget_to_item_map[widget] = n
            self.scene().addItem(widget)

    def handleNodesRemoved(self, nodes: List[Hashable]):
        for n in nodes:
            widget = self._item_to_widget_map[n]
            self.scene().removeItem(widget)
            del self._item_to_widget_map[n]
            del self._widget_to_item_map[widget]

    def handleNodesPropertiesChanged(self, nodesProperies):
        for n, properties in nodesProperies.items():
            node_widget = self._item_to_widget_map[n]

            for prop, value in properties.items():
                match prop:
                    case "label":
                        ...
                    case "inlets":
                        for inlet in value:
                            pin = PinWidget(inlet, node_widget, self)
                            layout = cast(
                                QGraphicsLinearLayout, node_widget.layout()
                            )
                            layout.addItem(pin)

                    case "outlets":
                        print(prop, value)

    def handleEdgesAdded(self, edges: List[Tuple[Hashable, Hashable]]):
        for u, v in edges:
            source_node = self._item_to_widget_map[u]
            target_node = self._item_to_widget_map[v]

            widget = self._delegate.edgeFactory(
                self, self._graphmodel, source_node, target_node
            )

            self._item_to_widget_map[(u, v)] = widget
            self._widget_to_item_map[widget] = (u, v)
            self.scene().addItem(widget)

    def handleEdgesRemoved(self, edges: List[Tuple[Hashable, Hashable]]):
        for u, v in edges:
            widget = self._item_to_widget_map[(u, v)]
            widget.setSource(None)
            widget.setTarget(None)
            self.scene().removeItem(widget)
            del self._item_to_widget_map[(u, v)]
            del self._widget_to_item_map[widget]

    def handleEdgesPropertiesChanged(self, edgesProperties):
        for edge, properties in edgesProperties.items():
            widget = self._item_to_widget_amp[edge]
            # self.delegate().setEdgeWidgetProps(self, edge, widget, **properties)

    def initiateConnection(self, source: QGraphicsItem):
        print("initiateConnection")


if __name__ == "__main__":
    from graph_model import GraphModel

    class ExampleGraphView(GraphView):
        def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
            if not self._graphmodel:
                return
            itemAtMouse = self.itemAt(event.position().toPoint())
            if itemAtMouse:
                return super().mouseDoubleClickEvent(event)

            clickpos = self.mapToScene(event.position().toPoint())

            # n = make_unique_id(length=12)
            n = make_unique_name("NODE", [n for n in self._graphmodel.nodes()])
            self._graphmodel.addNode(
                n, label="new node", inlets=["in"], outlets=["out"]
            )
            widget = self._item_to_widget_map[n]
            widget.setPos(clickpos)

        def createStandardContextMenu(self, scenePos: QPointF | None = None):
            """This function creates the standard context menu which is shown when
            the user clicks on the text edit with the right mouse button. It is
            called from the default contextMenuEvent() handler and it takes the
            position in document coordinates where the mouse click was. This can
            enable actions that are sensitive to the position where the user
            clicked. The popup menu's ownership is transferred to the caller."""

            def create_node(scenePos: QPointF | None):
                if not self._graphmodel:
                    return
                n = make_unique_name(
                    "NODE", [n for n in self._graphmodel.nodes()]
                )
                self._graphmodel.addNode(
                    n, label="new node", inlets=["in"], outlets=["out"]
                )
                widget = self._item_to_widget_map[n]
                widget.setPos(scenePos or QPointF(0, 0))

            def connect_selected_nodes():
                if not self._graphmodel:
                    return
                selection = [item for item in self.scene().selectedItems()]
                if len(selection) < 2:
                    return

                for item in selection[1:]:
                    u = self._widget_to_item_map[selection[0]]
                    v = self._widget_to_item_map[item]
                    self._graphmodel.addEdge(u, v)

            menu = QMenu(self)

            def nudge_selected_nodes():
                for item, widget in self._item_to_widget_map.items():
                    widget.moveBy(10, 10)

            nudge_action = QAction(self)
            nudge_action.setText("nudge nodes")
            nudge_action.triggered.connect(lambda: nudge_selected_nodes())
            menu.addAction(nudge_action)

            create_action = QAction(self)
            create_action.setText("create node")
            create_action.triggered.connect(lambda: create_node(scenePos))
            menu.addAction(create_action)

            connect_action = QAction(self)
            connect_action.setText("connect")
            connect_action.triggered.connect(lambda: connect_selected_nodes())
            menu.addAction(connect_action)
            return menu

        def contextMenuEvent(self, event: QContextMenuEvent):
            viewpos = self.mapFromGlobal(event.globalPos())
            scenepos = self.mapToScene(viewpos)
            menu = self.createStandardContextMenu(scenepos)

            menu.exec(event.globalPos())

    app = QApplication()
    view = ExampleGraphView()
    model = GraphModel()
    view.setModel(model)
    view.show()
    app.exec()
