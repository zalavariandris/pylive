from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import * 

from pylive.QtGraphEditor.nx_graph_model import NXGraphModel
from pylive.QtGraphEditor.nx_graph_selection_model import NXGraphSelectionModel
from pylive.QtGraphEditor.nx_graph_graphics_scene import (
    NXGraphScene,
    EdgeWidget,
    NodeWidget
)

from pylive.utils.unique import make_unique_name
import networkx as nx


import random


class NXGraphView(QGraphicsView):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        self._graphScene:NXGraphScene = NXGraphScene()

        self.setScene(self._graphScene)
        self._model:NXGraphModel|None = None
        self._selectionModel:NXGraphSelectionModel|None = None

        self._node_to_widget_map:dict[Hashable, QGraphicsItem] = dict()
        self._widget_to_node_map:dict[QGraphicsItem, Hashable] = dict()
        self._edge_to_widget_map:dict[tuple[Hashable,Hashable,Hashable], QGraphicsItem] = dict()
        self._widget_to_edge_map:dict[QGraphicsItem, tuple[Hashable,Hashable,Hashable]] = dict()

        def on_edge_connected(edge_widget:EdgeWidget):
            if not self._model:
                return
            source_widget = edge_widget.source()
            target_widget = edge_widget.target()
            assert source_widget and target_widget
            u = self._widget_to_node_map[source_widget]
            v = self._widget_to_node_map[target_widget]
            self._model.addEdge(u, v)

        self._graphScene.connected.connect(on_edge_connected)

        @self._graphScene.disconnected.connect
        def on_edge_disconnected(edge_widget:EdgeWidget):
            if not self._model:
                return
            u, v, k = self._widget_to_edge_map[edge_widget]
            self._model.removeEdge(u, v, k)

    @override
    def event(self, event)->bool:
        return super().event(event)

    def setModel(self, model:NXGraphModel):
        model.nodesAdded.connect(self.handleNodesAdded)
        model.nodesAboutToBeRemoved.connect(self.handleNodesRemoved)
        model.edgesAdded.connect(self.handleEdgesAdded)
        model.edgesAboutToBeRemoved.connect(self.handleEdgesRemoved)

        model.nodesAdded.connect(self.updateLayout)
        model.nodesRemoved.connect(self.updateLayout)
        model.edgesAdded.connect(self.updateLayout)
        model.edgesRemoved.connect(self.updateLayout)
 
        self._model = model

    def updateLayout(self):
        assert self._model
        G = self._model.G
        # pos = nx.forceatlas2_layout(G, max_iter=100, scaling_ratio=1800, strong_gravity=True)
        # pos = nx.kamada_kawai_layout(G, scale=200)

        def hiearchical_layout_with_grandalf(G, scale=1):
            import grandalf
            from grandalf.layouts import SugiyamaLayout

            g = grandalf.utils.convert_nextworkx_graph_to_grandalf(G)
            class defaultview(object): # see README of grandalf's github
                w, h = scale, scale

            for v in g.C[0].sV:
                v.view = defaultview()
            sug = SugiyamaLayout(g.C[0])
            sug.init_all() # roots=[V[0]])
            sug.draw()
            return {v.data: (v.view.xy[0], v.view.xy[1]) for v in g.C[0].sV} # Extracts the positions

        def hiearchical_layout_with_nx(G, scale=100):
            for layer, nodes in enumerate(reversed(tuple(nx.topological_generations(G)))):
                # `multipartite_layout` expects the layer as a node attribute, so add the
                # numeric layer value as a node attribute
                for node in nodes:
                    G.nodes[node]["layer"] = -layer

            # Compute the multipartite_layout using the "layer" node attribute
            pos = nx.multipartite_layout(G, subset_key="layer", align='horizontal')
            for n, p in pos.items():
                pos[n] = p[0]*scale, p[1]*scale
            return pos

        # print(pos)
        pos = hiearchical_layout_with_nx(G, scale=100)
        for N, (x, y) in pos.items():
            widget = self._node_to_widget_map[N]
            widget.setPos(x, y)

    @Slot(list)
    def handleNodesAdded(self, nodes: List[Hashable]):
        for n in nodes:
            widget = NodeWidget(title=f"{n}")
            self._node_to_widget_map[n] = widget
            self._widget_to_node_map[widget] = n
            self._graphScene.addNode(widget)
            

    @Slot(list)
    def handleNodesRemoved(self, nodes: List[Hashable]):
        for n in nodes:
            widget = self._node_to_widget_map[n]
            self._graphScene.removeNode(widget)
            del self._node_to_widget_map[n]
            del self._widget_to_node_map[widget]

    @Slot(list)
    def handleEdgesAdded(self, edges: List[Tuple[Hashable, Hashable, str]]):
        for u, v, k in edges:
            if (u,v,k) not in self._edge_to_widget_map:
                source = self._node_to_widget_map[u]
                target = self._node_to_widget_map[v]
                edge_widget = EdgeWidget(source, target)
                edge_widget.setLabelText(f"{k}")
                self._edge_to_widget_map[(u, v, k)] = edge_widget
                self._widget_to_edge_map[edge_widget] = (u, v, k)
                self._graphScene.addEdge(edge_widget)

    @Slot(list)
    def handleEdgesRemoved(self, edges: List[Tuple[Hashable, Hashable, str]]):
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
            selected_nodes = [
                self._widget_to_node_map[widget]
                for widget in self._graphScene.selectedItems()
                if isinstance(widget, NodeWidget)
            ]
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
        if itemAtMouse:
            return super().mouseDoubleClickEvent(event)

        clickpos = self.mapToScene(event.position().toPoint())
        
        n = make_unique_name("N1", self._model.nodes())
        self._model.addNode(n)

    def contextMenuEvent(self, event:QContextMenuEvent):
        def create_node_at(scenePos:QPointF):
            n = make_unique_name("N1", self.model().nodes())
            self.model().addNode(n)
            widget = self._node_to_widget_map[n]
            widget.setPos(scenePos)

        def connect_selected_nodes():
            selection = [item for item in self.scene().selectedItems()]
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


class AttributesTable(QAbstractTableModel):
    def __init__(self, parent: Optional[QObject]) -> None:
        super().__init__(parent)
        self._model:NXGraphModel = None

    def setSourceModel(self, model:NXGraphModel):
        self._sourceModel = model

    def setSourceSelectionModel(self, selectionModel:NXGraphSelectionModel):
        self._selectionModel = selectionModel

    def _get_current_node(self)->Hashable|None:
        if not self._selectionModel:
            return None
        selection = self._selectionModel.selectedNodes()
        return selection[0] if selection else None

    @override
    def columnCount(self, parent: QModelIndex | QPersistentModelIndex=QModelIndex())->int:
        return 2

    @override
    def rowCount(self, parent: QModelIndex | QPersistentModelIndex=QModelIndex()) -> int:
        n = self._get_current_node()
        if not n:
            return 0

        attributes = self._sourceModel.G.nodes[n]
        return len(attributes)

    def data(self, index: QModelIndex|QPersistentModelIndex, role=Qt.ItemDataRole.DisplayRole)->Any:
        n = self._get_current_node()
        if not n:
            return None

        attributes = self._model.G.nodes[n]
        attribute_list = [(attr, value) for attr, value in attributes.items()]

        row = index.row()
        col = index.column()

        return f"{attribute_list[row][col]}"

    @override
    def flags(self, index: QModelIndex|QPersistentModelIndex)->Qt.ItemFlag:
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemNeverHasChildren

    @override
    def setData(self, index:QModelIndex|QPersistentModelIndex, value:object|None, role:int=Qt.ItemDataRole.EditRole)->bool:
        # Editable models need to implement setData(), and implement flags() to return a value containing Qt::ItemIsEditable.
        ...

    @override
    def headerData(self, section:int, orientation:Qt.Orientation, role:int=Qt.ItemDataRole.DisplayRole)->object|None:
        match orientation:
            case Qt.Orientation.Horizontal:
                match section:
                    case 0:
                        return 'attribute'
                    case 1:
                        return 'value'
                    case _:
                        return ""
            case Qt.Orientation.Vertical:
                return ""
            case _:
                pass

    # beginInsertRows()    endInsertRows()
    # beginInsertColumns() endInsertColumns()
    # beginRemoveRows()    endRemoveRows()
    # beginRemoveColumns() endRemoveColumns()

class NodesListProxyModel(QAbstractListModel):
    def __init__(self, parent: QObject|None=None) -> None:
        super().__init__(parent)
        self._model:NXGraphModel|None = None

    def setSourceModel(self, model:NXGraphModel):
        self._sourceModel = model
        self.resetInternalData()
        model.nodesAdded.connect(lambda: self.resetInternalData())

    def setSourceSelectionModel(self, selectionModel:NXGraphSelectionModel):
        self._selectionModel = selectionModel

    @override
    def columnCount(self, parent: QModelIndex | QPersistentModelIndex=QModelIndex())->int:
        return 1

    @override
    def rowCount(self, parent: QModelIndex | QPersistentModelIndex=QModelIndex()) -> int:
        if not self._model:
            return 0
        nodes = [n for n in self._model.nodes()]
        return len(nodes)

    def data(self, index: QModelIndex|QPersistentModelIndex, role=Qt.ItemDataRole.DisplayRole)->Any:
        if not self._model:
            return 0

        nodes = [n for n in self._model.nodes()]

        return f"{nodes[index.row()]}"

    @override
    def flags(self, index: QModelIndex|QPersistentModelIndex)->Qt.ItemFlag:
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemNeverHasChildren

    def setData(self, index:QModelIndex|QPersistentModelIndex, value:object|None, role:int=Qt.ItemDataRole.EditRole)->bool:
        # Editable models need to implement setData(), and implement flags() to return a value containing Qt::ItemIsEditable.
        ...

    @override
    def headerData(self, section:int, orientation:Qt.Orientation, role:int=Qt.ItemDataRole.DisplayRole)->object|None:
        match orientation:
            case Qt.Orientation.Horizontal:
                match section:
                    case 0:
                        return 'name'
                    case _:
                        return ""
            case Qt.Orientation.Vertical:
                return f"{section}"


if __name__ == "__main__":
    from pylive.QtGraphEditor.nx_inspector_view import NXInspectorView
    class NXWindow(QWidget):
        def __init__(self, parent: QWidget|None=None) -> None:
            super().__init__(parent)
            self.setWindowTitle("NX Graph Editor")
            self.model = NXGraphModel()
            self.selectionmodel = NXGraphSelectionModel()

            self.graphview = NXGraphView()
            self.graphview.setModel(self.model)
            self.graphview.setSelectionModel(self.selectionmodel)

            self.nodelist = NodesListProxyModel()
            self.nodelist.setSourceModel(self.model)
            self.nodelistview = QListView()
            self.nodelistview.setModel(self.nodelist)

            self.inspector = NXInspectorView()
            self.inspector.setModel(self.model)
            self.inspector.setSelectionModel(self.selectionmodel)

            mainLayout = QVBoxLayout()
            splitter = QSplitter()
            mainLayout.addWidget(splitter)
            splitter.addWidget(self.graphview)
            splitter.addWidget(self.inspector)
            # splitter.addWidget(self.nodelistview)
            splitter.setSizes([splitter.width()//splitter.count() for _ in range(splitter.count())])
            self.setLayout(mainLayout)

        def sizeHint(self) -> QSize:
            return QSize(920, 520)

    app = QApplication()
    window = NXWindow()
    window.show()
    app.exec()