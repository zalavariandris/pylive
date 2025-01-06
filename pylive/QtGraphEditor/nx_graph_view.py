from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.QtGraphEditor.NetrowkXGraphEditor.link_graphics_items import (
    makeLineBetweenShapes,
)
from pylive.QtGraphEditor.NetrowkXGraphEditor.qgraphics_arrow_item import (
    QGraphicsArrowItem,
)
from pylive.QtGraphEditor.nx_graph_model import NXGraphModel
from pylive.QtGraphEditor.nx_graph_selection_model import NXGraphSelectionModel
from pylive.QtGraphEditor.nx_graph_graphics_scene import (
    NXGraphScene,
    # EdgeWidget,
    GraphicsNodeItem,
    DragLink,
    HighlightMixin,
    ConnectionEvent,
    ConnectionEnterType,
    ConnectionMoveType,
    ConnectionLeaveType,
    ConnectionDropType,
)

from pylive.utils.unique import make_unique_name
import networkx as nx


import random


class LinkWidget(HighlightMixin, QGraphicsArrowItem):
    def __init__(self, source, target):
        super().__init__()
        self._source: LinkableMixin
        self._target: LinkableMixin
        self.setSource(source)
        self.setTarget(target)

    def setSource(self, source):
        self._source = source
        source._edges.append(self)

    def source(self) -> "LinkableMixin":
        return self._source

    def setTarget(self, target: "LinkableMixin"):
        self._target = target
        target._edges.append(self)

    def target(self):
        return self._target

    def updatePosition(self):
        line = makeLineBetweenShapes(self._source, self._target)
        self.setLine(line)


class LinkableMixin:
    "responsible to notify the link if it needs to update"

    def __init__(self, *args, **kwargs):
        self._edges: list[LinkWidget] = []
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )

    ### UPDATE LINKS POSITION ###
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        match change:
            case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
                for edge in self._edges:
                    edge.updatePosition()
            case _:
                return super().itemChange(change, value)


class MyVertexWidget(GraphicsNodeItem, LinkableMixin):
    def __init__(self, title, view):
        super().__init__(title=title)
        self._view = view

        print("MyVertexWidget->init", self.__dict__)

    ### INITIATE LINKS ###
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        # start connection
        if event.modifiers() == Qt.KeyboardModifier.AltModifier:
            connect = DragLink(self)
            connect.exec()
            if target_widget := connect.target():
                u = self._view._widget_to_node_map[self]
                v = self._view._widget_to_node_map[target_widget]

                self._view._model.addEdge(u, v, k="in")
        else:
            return super().mousePressEvent(event)

    ## ACCEPT LINKS ###
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


# class MyEdgeWidget(EdgeWidget):
#     def __init__(
#         self, label, source: LinkableMixin, target: LinkableMixin, view
#     ):
#         super().__init__(label=label)
#         self._view = view
#         self._source = source
#         self._target = target

#     def updatePosition(self):
#         line = makeLineBetweenShapes(self._source, self._target)
#         self.setLine(line)

#     def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
#         u, v, k = self._view._widget_to_edge_map[self]

#         d1 = QLineF(self.line().p1(), event.scenePos()).length()
#         d2 = QLineF(self.line().p2(), event.scenePos()).length()

#         print("mousepress", d1, d2)

#         if d1 > d2:
#             self.hide()
#             connect = DragLink(self._view._node_to_widget_map[u])
#             connect.exec()
#             target_widget = connect.target()

#             if (
#                 target_widget
#                 and v == self._view._widget_to_node_map[target_widget]
#             ):
#                 # dropped onto the same target, than do nothing
#                 self.show()
#                 return

#             elif target_widget is None:
#                 # dropped on to empty canvas, than remove the edge
#                 self._view._model.removeEdge(u, v, k)
#                 return

#             elif target_widget:
#                 # dropped onto another target, than remove this one, and create a new edge
#                 print("dopped on another target")
#                 self._view._model.removeEdge(u, v, k)
#                 self._view._model.addEdge(
#                     u, self._view._widget_to_node_map[target_widget], k=None
#                 )

#             else:
#                 raise ValueError()
#         else:
#             self.hide()
#             connect = DragLink(
#                 self._view._node_to_widget_map[v], direction="backward"
#             )
#             connect.exec()
#             target_widget = connect.target()

#             if (
#                 target_widget
#                 and u == self._view._widget_to_node_map[target_widget]
#             ):
#                 # dropped onto the same target, than do nothing
#                 self.show()
#                 return

#             elif target_widget is None:
#                 # dropped on to empty canvas, than remove the edge
#                 self._view._model.removeEdge(u, v, k)
#                 return

#             elif target_widget:
#                 # dropped onto another target, than remove this one, and create a new edge
#                 print("dopped on another target")
#                 self._view._model.removeEdge(u, v, k)
#                 self._view._model.addEdge(
#                     self._view._widget_to_node_map[target_widget], v, k=None
#                 )

#             else:
#                 raise ValueError()


class NXGraphView(QGraphicsView):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        self._graphscene = NXGraphScene()
        self.setScene(self._graphscene)
        self._model: NXGraphModel | None = None
        self._selectionModel: NXGraphSelectionModel | None = None

        self._node_to_widget_map: dict[Hashable, QGraphicsItem] = dict()
        self._widget_to_node_map: dict[QGraphicsItem, Hashable] = dict()
        self._edge_to_widget_map: dict[
            tuple[Hashable, Hashable, Hashable], QGraphicsItem
        ] = dict()
        self._widget_to_edge_map: dict[
            QGraphicsItem, tuple[Hashable, Hashable, Hashable]
        ] = dict()
        self._attribute_to_widget_map: dict[
            tuple[Hashable, Hashable], QGraphicsItem
        ] = dict()
        self._widget_to_attribute_map: dict[
            QGraphicsItem, tuple[Hashable, Hashable]
        ] = dict()

        self._acceptLinkEvents = set()

        # self.scene().installEventFilter(self)

    ### DELEGATE >>
    def createNodeEditor(self, n: Hashable) -> QGraphicsItem:
        assert self._model
        node_widget = MyVertexWidget(title=f"{n}", view=self)
        return node_widget

    def createEdgeEditor(
        self, source_widget, target_widget, k: tuple[Hashable, Hashable] | None
    ) -> LinkWidget:
        edge_widget = LinkWidget(
            source=source_widget,
            target=target_widget,
        )
        return edge_widget

    def updateNodePosition(self, node_widget):
        for edge in node_widget._edges:
            edge.updateEdgePosition()

    # def setNodeEditor(...):
    #     ...
    # def setNodeModel(...):
    #     ...
    # def setEdgeEditor(...):
    #     ...
    # def setEdgeModel(...):
    #     ...
    # def setNodeAttributeEditor(...):
    #     ...
    # def setNodeAttributeModel(...):
    #     ...
    # def setEdgeAttributeEditor(...):
    #     ...
    # def setEdgeAttributeModel(...):
    #     ...
    # def updateEdgeEditorPosition(self, source, target, k):
    #     ...

    ### << DELEGATE

    # def mousePressEvent(self, event: QMouseEvent) -> None:
    #     for item in self.items(event.position().toPoint()):
    #         if self._widget_to_attribute_map.get(item):
    #             drag = QDrag(self)
    #             drag.exec()
    #             print("attribute press")
    #             break
    #         elif self._widget_to_node_map.get(item):
    #             print("node press")
    #             break
    #         elif self._widget_to_edge_map.get(item):
    #             print("edge press")
    #             break
    #         else:
    #             ...

    # def mouseMoveEvent(self, event: QMouseEvent) -> None:
    #     return super().mouseMoveEvent(event)

    # def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    #     return super().mouseReleaseEvent(event)

    def nodeAt(self, point: QPoint) -> Hashable | None:
        """Returns the model node of the item at the viewport coordinates point."""
        """If there are several nodes at this position, this function returns the topmost node."""
        for item in self.items(point):
            if n := self._widget_to_node_map.get(item):
                return n

    def edgeAt(
        self, point: QPoint
    ) -> tuple[Hashable, Hashable, Hashable] | None:
        """Returns the model node of the item at the viewport coordinates point."""
        """If there are several nodes at this position, this function returns the topmost node."""
        for item in self.items(point):
            if e := self._widget_to_edge_map.get(item):
                return e

    def attributeAt(self, point: QPoint) -> tuple[Hashable, Hashable] | None:
        """Returns the model node of the item at the viewport coordinates point."""
        """If there are several nodes at this position, this function returns the topmost node."""
        for item in self.items(point):
            if a := self._widget_to_attribute_map.get(item):
                return a

    def setAcceppLinkEvents(self, item: QGraphicsItem, accept: bool):
        if accept:
            self._acceptLinkEvents.add(item)
        else:
            self._acceptLinkEvents.remove(item)

    def setModel(self, model: NXGraphModel):
        model.nodesAdded.connect(self.handleNodesAdded)
        model.nodesAboutToBeRemoved.connect(self.handleNodesRemoved)
        model.edgesAdded.connect(self.handleEdgesAdded)
        model.edgesAboutToBeRemoved.connect(self.handleEdgesRemoved)
        model.nodesPropertiesChanged.connect(self.handleNodesPropertiesChanged)

        model.nodesAdded.connect(self.updateGraphLayout)
        model.nodesRemoved.connect(self.updateGraphLayout)
        model.edgesAdded.connect(self.updateGraphLayout)
        model.edgesRemoved.connect(self.updateGraphLayout)

        self._model = model

    @Slot()
    def updateGraphLayout(self):
        assert self._model
        G = self._model.G
        # pos = nx.forceatlas2_layout(G, max_iter=100, scaling_ratio=1800, strong_gravity=True)
        # pos = nx.kamada_kawai_layout(G, scale=200)

        def hiearchical_layout_with_grandalf(G, scale=1):
            import grandalf
            from grandalf.layouts import SugiyamaLayout

            g = grandalf.utils.convert_nextworkx_graph_to_grandalf(G)

            class defaultview(object):  # see README of grandalf's github
                w, h = scale, scale

            for v in g.C[0].sV:
                v.view = defaultview()
            sug = SugiyamaLayout(g.C[0])
            sug.init_all()  # roots=[V[0]])
            sug.draw()
            return {
                v.data: (v.view.xy[0], v.view.xy[1]) for v in g.C[0].sV
            }  # Extracts the positions

        def hiearchical_layout_with_nx(G, scale=100):
            for layer, nodes in enumerate(
                reversed(tuple(nx.topological_generations(G)))
            ):
                # `multipartite_layout` expects the layer as a node attribute, so add the
                # numeric layer value as a node attribute
                for node in nodes:
                    G.nodes[node]["layer"] = -layer

            # Compute the multipartite_layout using the "layer" node attribute
            pos = nx.multipartite_layout(
                G, subset_key="layer", align="horizontal"
            )
            for n, p in pos.items():
                pos[n] = p[0] * scale, p[1] * scale
            return pos

        # print(pos)
        pos = hiearchical_layout_with_nx(G, scale=100)
        for N, (x, y) in pos.items():
            widget = self._node_to_widget_map[N]
            widget.setPos(x, y)

    @Slot(list)
    def handleNodesAdded(self, nodes: List[Hashable]):
        for n in nodes:
            widget = self.createNodeEditor(n)
            self._node_to_widget_map[n] = widget
            self._widget_to_node_map[widget] = n
            self._graphscene.addNode(widget)

    def handleNodesPropertiesChanged(
        self, changes: dict[Hashable, dict[str, Any]]
    ):
        ...
        # for n, change in changes.items():
        #     for attr, value in change.items():
        #         node_widget = cast(
        #             MyVertexWidgetWithPorts, self._node_to_widget_map[n]
        #         )
        #         if attr not in node_widget._inlets:
        #             # add a new port for the attribute
        #             inlet_widget = self.createAttributeEditor(node_widget, attr)
        #             self._attribute_to_widget_map[(n, attr)] = inlet_widget
        #             self._widget_to_attribute_map[inlet_widget] = (n, attr)

        #         # set the port label to the value
        #         inlet_widget = cast(
        #             MyInletWidget, self._attribute_to_widget_map[(n, attr)]
        #         )
        #         inlet_widget.setLabel(attr)

    @Slot(list)
    def handleNodesRemoved(self, nodes: List[Hashable]):
        for n in nodes:
            widget = self._node_to_widget_map[n]
            self._graphscene.removeNode(widget)
            del self._node_to_widget_map[n]
            del self._widget_to_node_map[widget]

    @Slot(list)
    def handleEdgesAdded(self, edges: List[Tuple[Hashable, Hashable, str]]):
        print("handleEdgesAdded")
        for u, v, k in edges:
            if (u, v, k) not in self._edge_to_widget_map:
                source = self._node_to_widget_map[u]
                target = self._node_to_widget_map[v]
                edge_widget = self.createEdgeEditor(source, target, k)
                self._edge_to_widget_map[(u, v, k)] = edge_widget
                self._widget_to_edge_map[edge_widget] = (u, v, k)
                self._graphscene.addEdge(edge_widget, source, target)

    @Slot(list)
    def handleEdgesRemoved(self, edges: List[Tuple[Hashable, Hashable, str]]):
        for u, v, k in edges:
            paramname = k
            edge_widget = self._edge_to_widget_map[u, v, k]
            self._graphscene.removeEdge(edge_widget)
            del self._edge_to_widget_map[(u, v, k)]
            del self._widget_to_edge_map[edge_widget]

    def model(self):
        return self._model

    def setSelectionModel(self, selectionModel: NXGraphSelectionModel):
        @self._graphscene.selectionChanged.connect
        def update_selection_model():
            assert self._selectionModel
            selected_nodes = [
                self._widget_to_node_map[widget]
                for widget in self._graphscene.selectedItems()
                if widget in self._widget_to_node_map
            ]
            self._selectionModel.setSelectedNodes(selected_nodes)

        @selectionModel.selectionChanged.connect
        def update_scene_selection(
            selected: set[Hashable], deselected: set[Hashable]
        ):
            selected_widgets = [self._node_to_widget_map[n] for n in selected]
            deselected_widgets = [
                self._node_to_widget_map[n] for n in deselected
            ]
            self._graphscene.blockSignals(True)
            for widget in selected_widgets:
                widget.setSelected(True)

            for widget in deselected_widgets:
                widget.setSelected(False)
            self._graphscene.blockSignals(False)
            self._graphscene.selectionChanged.emit()

        self._selectionModel = selectionModel

    def selectionModel(self) -> NXGraphSelectionModel | None:
        return self._selectionModel

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if not self._model:
            return
        itemAtMouse = self.itemAt(event.position().toPoint())
        if itemAtMouse:
            return super().mouseDoubleClickEvent(event)

        clickpos = self.mapToScene(event.position().toPoint())

        n = make_unique_name("N1", self._model.nodes())
        self._model.addNode(n)

    def contextMenuEvent(self, event: QContextMenuEvent):
        def create_vertex_at(scenePos: QPointF):
            model = self.model()
            assert model
            n = make_unique_name("N1", [f"{n}" for n in model.nodes()])
            model.addNode(n)
            widget = self._node_to_widget_map[n]
            widget.setPos(scenePos)

        def connect_selected_nodes():
            model = self.model()
            assert model
            selection = [item for item in self.scene().selectedItems()]
            if len(selection) < 2:
                return

            for item in selection[1:]:
                u = self._widget_to_node_map[selection[0]]
                v = self._widget_to_node_map[item]
                model.addEdge(u, v)

        menu = QMenu(self)

        create_vertex_action = QAction(self)
        create_vertex_action.setText("create vertex")
        create_vertex_action.triggered.connect(
            lambda: create_vertex_at(
                self.mapToScene(self.mapFromGlobal(event.globalPos()))
            )
        )
        menu.addAction(create_vertex_action)

        connect_action = QAction(self)
        connect_action.setText("connect")

        connect_action.triggered.connect(lambda: connect_selected_nodes())
        menu.addAction(connect_action)

        menu.exec(event.globalPos())

    # def mouseMoveEvent(self, event: QMouseEvent) -> None:
    #     return super().mouseMoveEvent(event)


class NodesListProxyModel(QAbstractListModel):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._model: NXGraphModel | None = None

    def setSourceModel(self, model: NXGraphModel):
        self._sourceModel = model
        self.resetInternalData()
        model.nodesAdded.connect(lambda: self.resetInternalData())

    def setSourceSelectionModel(self, selectionModel: NXGraphSelectionModel):
        self._selectionModel = selectionModel

    @override
    def columnCount(
        self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()
    ) -> int:
        return 1

    @override
    def rowCount(
        self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()
    ) -> int:
        if not self._model:
            return 0
        nodes = [n for n in self._model.nodes()]
        return len(nodes)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role=Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not self._model:
            return 0

        nodes = [n for n in self._model.nodes()]

        return f"{nodes[index.row()]}"

    @override
    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemNeverHasChildren

    def setData(
        self,
        index: QModelIndex | QPersistentModelIndex,
        value: object | None,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        # Editable models need to implement setData(), and implement flags() to return a value containing Qt::ItemIsEditable.
        ...

    @override
    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object | None:
        match orientation:
            case Qt.Orientation.Horizontal:
                match section:
                    case 0:
                        return "name"
                    case _:
                        return ""
            case Qt.Orientation.Vertical:
                return f"{section}"


if __name__ == "__main__":
    from pylive.QtGraphEditor.nx_inspector_view import NXInspectorView
    from pylive.QtTerminal.terminal_with_exec import Terminal

    # LinkWidget(lambda source, target:)

    class NXWindow(QWidget):
        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self.setWindowTitle("NX Graph Editor")
            self.model = NXGraphModel()
            self.selectionmodel = NXGraphSelectionModel()

            self.graphview = NXGraphView()
            menubar = QToolBar()
            menubar.setOrientation(Qt.Orientation.Vertical)
            menubar.setStyleSheet(
                """
            QToolBar{
                background-color: rgba(128,128,128,24); 
                border-radius: 8px;
                margin:6px;
            }"""
            )

            self.currentTool = None
            select_action = QAction("Select", self.graphview)
            select_action.triggered.connect(lambda: self.setTool(None))
            menubar.addAction(select_action)

            create_action = QAction("Create", self.graphview)
            create_action.triggered.connect(lambda: self.setTool(None))
            menubar.addAction(create_action)

            link_action = QAction("Link", self.graphview)
            link_action.triggered.connect(lambda: self.setTool(MyLinkTool()))
            menubar.addAction(link_action)

            menubar.setParent(self.graphview)
            self.graphview.setModel(self.model)
            self.graphview.setSelectionModel(self.selectionmodel)

            self.nodelist = NodesListProxyModel()
            self.nodelist.setSourceModel(self.model)
            self.nodelistview = QListView()
            self.nodelistview.setModel(self.nodelist)

            self.inspector = NXInspectorView()
            self.inspector.setModel(self.model)
            self.inspector.setSelectionModel(self.selectionmodel)

            self.terminal = Terminal()
            self.terminal.setContext({"app": self})

            mainLayout = QVBoxLayout()
            mainLayout.setContentsMargins(0, 0, 0, 0)
            splitter = QSplitter()
            mainLayout.addWidget(splitter)
            splitter.addWidget(self.graphview)
            splitter.addWidget(self.inspector)
            splitter.addWidget(self.terminal)
            # splitter.addWidget(self.nodelistview)
            splitter.setSizes(
                [
                    splitter.width() // splitter.count()
                    for _ in range(splitter.count())
                ]
            )
            self.setLayout(mainLayout)

            """initial graph"""
            # self.model.addNode("N1")
            # self.model.addNode("N2")
            # self.model.addNode("N3")
            # self.model.setNodeProperties("N2", attr=None)
            # self.model.addEdge("N1", "N2")

        # def setTool(self, tool:QObject|None):
        #     print("set tool: ", tool)
        #     if self.currentTool:
        #         self.graphview.scene().removeEventFilter(self.currentTool)

        #     if tool:
        #         self.graphview.scene().installEventFilter(tool)
        #         self.currentTool = tool

        def sizeHint(self) -> QSize:
            return QSize(1200, 520)

    app = QApplication()
    window = NXWindow()
    window.show()
    app.exec()
