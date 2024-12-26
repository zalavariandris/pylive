from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import * 

from pylive.QtGraphEditor.nx_graph_model import NXGraphModel
from pylive.QtGraphEditor.nx_graph_selection_model import NXGraphSelectionModel
from pylive.QtGraphEditor.dag_graph_graphics_scene import (
    DAGScene,
    EdgeWidget,
    NodeConnectionTool,
    # NodeWidget,
    InletWidget,
    OutletWidget,
)
from pylive.QtGraphEditor.infinite_graphicsview_optimized import (
    InfiniteGraphicsView,
)
from pylive.QtGraphEditor.text_widget import TextWidget

from pylive.utils.unique import make_unique_name
import networkx as nx

QGraphicsSceneEvent.Type.User


from pylive.QtGraphEditor.NetrowkXGraphEditor.link_graphics_items import (
    makeLineBetweenShapes,
)
from pylive.QtGraphEditor.NetrowkXGraphEditor.qgraphics_arrow_item import (
    QGraphicsArrowItem,
)


class ConnectionEvent(QGraphicsSceneEvent):
    def __init__(self, source:'NodeWidget'):
        super().__init__(QGraphicsSceneEvent.Type.User)
        self._source = source

    def source(self):
        return self._source

    def __str__(self):
        return f"ConnectionEvent({self._source})"


class Connection(QObject):
    def __init__(self, source:'NodeWidget', parent=None):
        super().__init__(parent=parent)
        self._source = source
        self._loop = QEventLoop()

        self._arrow = None

    def source(self):
        return self._source

    def exec(self):
        app = QApplication.instance()
        assert app
        app.installEventFilter(self)
        self._arrow = QGraphicsArrowItem(QLineF(self._source.pos(), self._source.pos()))
        self._source.scene().addItem(self._arrow )
        self._loop.exec()
        self._source.scene().removeItem(self._arrow)
        app.removeEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.GraphicsSceneMouseMove:  
            line = self._arrow.line()
            line.setP2(event.scenePos())
            self._arrow.setLine(line)
            connectionEvent = ConnectionEvent(self._source)
            scene = self._source.scene()
            for item in scene.items(event.scenePos()):
                scene.sendEvent(item, connectionEvent)
            return True
        if event.type()==QGraphicsSceneEvent.Type.User:
            print("user event captured", event)
            return True
        if event.type() == QEvent.Type.MouseButtonRelease:
            self._loop.exit()
            return True
        return super().eventFilter(watched, event)


class NodeWidget(QGraphicsWidget):
    sceneGeometryChanged = Signal()
    def __init__(
        self,
        title="Node",
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
        parent=None,
    ):
        super().__init__(parent)

        # Enable selection and movement
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsFocusable, True)

        # Create a layout
        self.main_layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)
        self.main_layout.setContentsMargins(8, 3, 8, 3)
        self.main_layout.setSpacing(0)

        # create heading
        self.header = TextWidget(title)
        self.main_layout.addItem(self.header)

        # Set the layout for the widget
        self.setLayout(self.main_layout)

        # Define the bounding geometry
        # self.setGeometry(QRectF(-75, -59, 150, 100))
        self._inlets = []
        self._outlets = []

        self.geometryChanged.connect(self.sceneGeometryChanged)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )

        self.setAcceptDrops(True)

        self._dragline = None

    def itemChange(self, change, value):
        match change:
            case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
                self.sceneGeometryChanged.emit()

        return super().itemChange(change, value)

    def paint(
        self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None
    ):
        # Draw the node rectangle
        palette: QPalette = option.palette  # type: ignore
        state: QStyle.StateFlag = option.state  # type: ignore

        painter.setBrush(palette.window())
        # painter.setBrush(Qt.NoBrush)
 
        pen = QPen(palette.text().color(), 1)
        pen.setCosmetic(True)
        pen.setWidthF(1)
        if state & QStyle.StateFlag.State_Selected:
            pen.setWidthF(2)
            pen.setColor(palette.accent().color())
        painter.setPen(pen)

        # painter.setPen(palette.window().color())
        painter.drawRoundedRect(QRectF(QPointF(), self.size()), 10, 10)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if QLineF(event.screenPos(), event.buttonDownScreenPos(Qt.MouseButton.LeftButton)).length() < QApplication.startDragDistance():
            return
        print("start drag event")

        # start connection
        connection = Connection(self)
        connection.exec()
        # Start drag
        # view = cast(QGraphicsView, event.widget())
        # drag = QDrag(self)
        # mime = QMimeData()

        # mime.setData("node-graph-nx", bytes(self.header.toPlainText(), 'utf-8')) # TODO: research memoryview for arbitrary python object as darta
        # drag.setMimeData(mime)line

        # QApplication.instance().installEventFilter(self)
        # line = QLineF(self.geometry().center(), self.geometry().center())
        # self._dragline = QGraphicsLineItem(line)
        # print(line)
        # self.scene().addItem(self._dragline)
        
        # drag.exec()
        # self.scene().removeItem(self._dragline)
        # self._dragline = None
        # QApplication.instance().removeEventFilter(self)
        # self.setCursor(Qt.CursorShape.OpenHandCursor)

        # return super().mouseMoveEvent(event)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # print(event)
        if event.type() == QEvent.Type.DragMove:
            # print("drag move event")
            ...
        if event.type() == QEvent.Type.GraphicsSceneDragMove:
            # print("mouse move event")
            dragMoveEvent = cast(QGraphicsSceneDragDropEvent, event)
            line = self._dragline.line()
            line.setP2(dragMoveEvent.scenePos())
            self._dragline.setLine(line)
            self.update()

        return super().eventFilter(watched, event)

    # def dragEnterEvent(self, event):
    #     mime = event.mimeData()
    #     print("dragEnterEvent", mime, mime.data("node-graph-nx"))
    #     if qbytearray:=mime.data("node-graph-nx"):
    #         n = str(qbytearray.data(), encoding='utf-8')
    #         if n !=self.header.toPlainText():
    #             print(n)
    #             event.setAccepted(True)
    #             return
    #     event.setAccepted(False)

    # def dropEvent(self, event: QGraphicsSceneDragDropEvent) -> None:
    #     mime = event.mimeData()
    #     print("dragEnterEvent", mime, mime.data("node-graph-nx"))

    #     if qbytearray:=mime.data("node-graph-nx"):
    #         n = str(qbytearray.data(), encoding='utf-8')
    #         if n !=self.header.toPlainText():
    #             print("dropped:", event.source())
    #             event.setAccepted(True)
    #             view = cast(NXGraphView, self.parentWidget())
    #             # view._model.addEdge(self.header.toPlainText(), n)
    #             return
    #     event.setAccepted(False)
    #     return super().dropEvent(event)

    # @override
    # def dragLeaveEvent(self, event):
    #     print("leave")


class NXGraphView(InfiniteGraphicsView):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._graphScene = DAGScene()
        # self._graphScene.setMouseTool(NodeConnectionTool(self._graphScene))
        self.setScene(self._graphScene)
        self._model:NXGraphModel|None = None
        self._selectionModel:NXGraphSelectionModel|None = None

        self._node_to_widget_map = dict()
        self._widget_to_node_map = dict()
        self._edge_to_widget_map = dict()
        self._widget_to_edge_map = dict()

        @self._graphScene.edgeDropped.connect
        def on_edge_dropped(edge_widget:EdgeWidget, source:OutletWidget|EdgeWidget|None, target:InletWidget|NodeWidget|None):
            print("on_edge_dropped", edge_widget, source, target)
            if not self._model:
                return
            if source and target:
                if edge_widget in self._widget_to_edge_map:
                    # reconnect
                    edge = self._widget_to_edge_map[edge_widget]
                    self._model.removeEdge(*edge)
                    u = self._widget_to_node_map[source]
                    v = self._widget_to_node_map[target]
                    self._model.addEdge(u, v)
                    
                else:
                    # new connection
                    u = self._widget_to_node_map[source]
                    v = self._widget_to_node_map[target]
                    self._model.addEdge(u, v)
            else:
                if edge_widget in self._edge_to_widget_map:
                    # disconnect
                    edge = self._widget_to_edge_map[edge_widget]
                    self._model.removeEdge(*edge)
                else:
                    # do nothing
                    pass

    def setModel(self, model:NXGraphModel):
        model.nodesAdded.connect(self.handleNodesAdded)
        model.edgesAdded.connect(self.handleEdgesAdded)

        model.nodesAdded.connect(self.updateLayout)
        model.nodesRemoved.connect(self.updateLayout)
        model.edgesAdded.connect(self.updateLayout)
        model.edgesRemoved.connect(self.updateLayout)

        self._model = model

    def updateLayout(self):
        assert self._model
        positions = nx.spring_layout(self._model.G, scale=100, iterations=100)
        for N, (x, y) in positions.items():
            widget = self._node_to_widget_map[N]
            widget.setPos(x, y)
        print("layout updated")

    @Slot(list)
    def handleNodesAdded(self, nodes: List[Hashable]):
        print("nodes added")
        for n in nodes:
            widget = NodeWidget(title=f"{n}")
            self._graphScene.addNode(widget)
            self._node_to_widget_map[n] = widget
            self._widget_to_node_map[widget] = n

    @Slot(list)
    def handleNodesRemoved(self, nodes: List[Hashable]):
        for n in nodes:
            widget = self._node_to_widget_map[n]
            self._graphScene.removeNode(widget)
            del self._node_to_widget_map[n]
            del self._widget_to_node_map[widget]

    @Slot(list)
    def handleEdgesAdded(self, edges: List[Tuple[Hashable, Hashable, str]]):
        print("edges added", edges)
        for u, v, k in edges:
            source = self._node_to_widget_map[u]
            target = self._node_to_widget_map[v]
            edge_widget = EdgeWidget(source, target)
            edge_widget.setLabelText(f"{k}")
            self._graphScene.addEdge(edge_widget)
            self._edge_to_widget_map[(u, v, k)] = edge_widget
            self._widget_to_edge_map[edge_widget] = (u, v, k)

    @Slot(list)
    def handleEdgesRemoved(self, edges: List[Tuple[Hashable, Hashable, str]]):
        print("edges removed", edges)
        for u, v, k in edges:
            paramname = k
            edge_widget = self._edge_to_widget_map[u, v, k]
            self._graphScene.removeEdge(edge_widget)
            del self._edge_to_widget_map[(u, v, k)]
            del self._widget_to_edge_map[edge_widget]

    def model(self):
        return self._model

    def setSelectionModel(self, selectionModel:NXGraphSelectionModel):
        @self._graphScene.selectionChanged.connect
        def update_selection_model():
            assert self._selectionModel
            print("dagscene->selectionChanged")
            selected_nodes = [
                self._widget_to_node_map[widget]
                for widget in self._graphScene.selectedItems()
                if isinstance(widget, NodeWidget)
            ]
            print("  -", selected_nodes)
            self._selectionModel.setSelectedNodes(selected_nodes)

        @selectionModel.selectionChanged.connect
        def update_scene_selection(selected: set[Hashable], deselected: set[Hashable]):
            selected_widgets = [self._node_to_widget_map[n] for n in selected]
            deselected_widgets = [self._node_to_widget_map[n] for n in deselected]
            self._graphScene.blockSignals(True)
            for widget in selected_widgets:
                widget.setSelected(True)

            for widget in deselected_widgets:
                widget.setSelected(False)
            self._graphScene.blockSignals(False)
            self._graphScene.selectionChanged.emit()

        self._selectionModel = selectionModel

    def selectionModel(self)->NXGraphSelectionModel|None:
        return self._selectionModel

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if not self._model:
            return 
        itemAtMouse = self.itemAt(event.position().toPoint())
        print("itemAtMouse", itemAtMouse)
        if itemAtMouse:
            return super().mouseDoubleClickEvent(event)

        clickpos = self.mapToScene(event.position().toPoint())
        
        n = make_unique_name("N1", self._model.nodes())
        self._model.addNode(n)

        # widget = self._node_to_widget_map[n]
        # widget.setPos(clickpos)
        # print("move node to clickpos")

    def contextMenuEvent(self, event:QContextMenuEvent):
        def create_node_at(scenePos:QPointF):
            n = make_unique_name("N1", self.model().nodes())
            self.model().addNode(n)
            widget = self._node_to_widget_map[n]
            widget.setPos(scenePos)

        def connect_selected_nodes():
            selection = [item for item in self.scene().selectedItems()]
            print("connect_selected_nodes:", selection)
            if len(selection) < 2:
                return

            for item in selection[1:]:
                u = self._widget_to_node_map[selection[0]]
                v = self._widget_to_node_map[item]
                self.model().addEdge(u, v)

        menu = QMenu(self)

        create_action = QAction(self)
        create_action.setText("create node")
        
        create_action.triggered.connect(lambda: create_node_at( self.mapToScene(self.mapFromGlobal(event.globalPos()) )))
        menu.addAction(create_action)

        connect_action = QAction(self)
        connect_action.setText("connect")

        connect_action.triggered.connect(lambda: connect_selected_nodes())
        menu.addAction(connect_action)

        menu.exec(event.globalPos())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        return super().mouseMoveEvent(event)


class NXInspectorView(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._model:NXGraphModel|None = None
        self._selectionModel:NXGraphSelectionModel|None = None

    def setModel(self, model:NXGraphModel):
        self._model = model

    def setSelectionModel(self, selectionModel:NXGraphSelectionModel):
        self._selectionModel = selectionModel


if __name__ == "__main__":
    class NXWindow(QWidget):
        def __init__(self, parent: QWidget|None=None) -> None:
            super().__init__(parent)
            self.setWindowTitle("NX Graph Editor")
            self.model = NXGraphModel()
            self.selectionmodel = NXGraphSelectionModel()

            self.graphview = NXGraphView()
            self.graphview.setModel(self.model)
            self.graphview.setSelectionModel(self.selectionmodel)

            self.inspector = NXInspectorView()
            self.inspector.setModel(self.model)
            self.inspector.setSelectionModel(self.selectionmodel)

            mainLayout = QVBoxLayout()
            splitter = QSplitter()
            mainLayout.addWidget(splitter)
            splitter.addWidget(self.graphview)
            splitter.addWidget(self.inspector)
            splitter.setSizes([splitter.width()//splitter.count() for _ in range(splitter.count())])
            self.setLayout(mainLayout)

    app = QApplication()
    window = NXWindow()
    window.show()
    app.exec()