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


class NXGraphView(QGraphicsView):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        self._graphScene:NXGraphScene = NXGraphScene()

        self.setScene(self._graphScene)
        self._model:NXGraphModel|None = None
        self._selectionModel:NXGraphSelectionModel|None = None

        self._node_to_widget_map:dict[Hashable, QGraphicsItem] = dict()
        self._widget_to_node_map:dict[Hashable, QGraphicsItem] = dict()
        self._edge_to_widget_map:dict[Hashable, QGraphicsItem] = dict()
        self._widget_to_edge_map:dict[Hashable, QGraphicsItem] = dict()

        def on_edge_connected(edge_widget:EdgeWidget):
            if not self._model:
                return

            u = self._widget_to_node_map[edge_widget.source()]
            v = self._widget_to_node_map[edge_widget.target()]
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
        pos = nx.kamada_kawai_layout(G, scale=200)

        # pos = nx.multipartite_layout(G, scale=200)
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


class NXInspectorView(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._model:NXGraphModel|None = None
        self._selectionModel:NXGraphSelectionModel|None = None

        # widgets
        self.kind_label = QLabel()
        self.name_label = QLabel()
        self.add_button = QPushButton("add attribute")
        self.add_button.clicked.connect(lambda: self.addAttribute())
        self.remove_button = QPushButton("remove attribute")
        self.remove_button.clicked.connect(lambda: self.removeSelectedAttribute())


        # self.header = QLabel()

        # self.attributesEditor = QWidget()
        # attriubteLayout = QVBoxLayout()
        # self.attributesEditor.setLayout(attriubteLayout)

        # menuBar = QMenuBar()
        # addAttributeAction = QAction("add", self)
        # addAttributeAction.triggered.connect(lambda: self.addAttribute())
        # removeAttributeAction = QAction("remove", self)
        # menuBar.addAction(addAttributeAction)
        # menuBar.addAction(removeAttributeAction)
        # self.attribTable = QTableWidget()
        # self.attribTable.setColumnCount(2)
        # self.attribTable.setHorizontalHeaderLabels(["name", "value"])

        # attriubteLayout.setMenuBar(menuBar)
        
        # attriubteLayout.addWidget(self.attribTable)
        # attriubteLayout.addStretch()

        # layout
        mainLayout = QVBoxLayout()
        header_layout = QHBoxLayout()
        header_layout.addWidget(self.kind_label)
        header_layout.addWidget(self.name_label)
        mainLayout.addLayout(header_layout)

        mainLayout.addWidget(QLabel("attributes"))
        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(self.add_button)
        buttonsLayout.addWidget(self.remove_button)
        mainLayout.addLayout(buttonsLayout)
        mainLayout.addWidget(self.attributesTable)
        mainLayout.addStretch()

        self.setLayout(mainLayout)

        self._attribute_to_row:dict[str, int] = dict()
        self._row_to_attribute:dict[int, str] = dict()

    def setModel(self, model:NXGraphModel):
        self._model = model
        self._model.nodesPropertiesChanged.connect(self.handleNodesPropertiesChanged)

    @Slot()
    def addAttribute(self):
        print("addAttribute", self._model, self._get_current_node())
        if not self._model:
            return

        n = self._get_current_node()

        if not n:
            return

        attribs = self._model.G.nodes[n]
        attr = make_unique_name("attrib1", attribs.keys())

        props = {
            attr: None
        }
        self._model.setNodeProperties(n, **props)

    def removeSelectedAttribute(self):
        ...

    def handleCurrentChange(self, currentNode:Hashable):
        if not currentNode:
            self.kind_label.setText("-")
            self.name_label.setText("no selection")
            return

        #### Update header
        attributes = self._model.G.nodes[currentNode]
        self.kind_label.setText(f"{currentNode.__class__}")
        self.name_label.setText(f"{currentNode}, attributes: {len(attributes)}")


        ### Update attriubtes
        # clear form
        while self.attributesForm.count():
            item = self.attributesForm.takeAt(0)
            if widget:=item.widget():
                widget.deleteLater()

        # add attributes to form
        for row, (attr, value) in enumerate(attributes.items()):
            print("add attributes form")
            self.attributesForm.addRow(attr, QLabel(f"{value}"))
            self._row_to_attribute[row] = attr
            self._attribute_to_row[attr] = row


    def handleNodesPropertiesChanged(self, changes:dict[Hashable, dict[str,Any]]):
        n = self._get_current_node()
        if n not in changes:
            return
        
        attributes = self._model.G.nodes[n]
        self.handleCurrentChange(n)


    def _get_current_node(self):
        if not self._selectionModel:
            return None
        selection = self._selectionModel.selectedNodes()
        return selection[0] if selection else None

    def setSelectionModel(self, selectionModel:NXGraphSelectionModel):
        @selectionModel.selectionChanged.connect
        def update_scene_selection(selected: set[Hashable], deselected: set[Hashable]):
            self.handleCurrentChange(self._get_current_node())

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

            self.nodelist = NodesListProxyModel()
            self.nodelist.setSourceModel(self.model)
            self.nodelistview = QListView()
            self.nodelistview.setModel(self.nodelist)

            # self.inspector = NXInspectorView()
            # self.inspector.setModel(self.model)
            # self.inspector.setSelectionModel(self.selectionmodel)

            mainLayout = QVBoxLayout()
            splitter = QSplitter()
            mainLayout.addWidget(splitter)
            splitter.addWidget(self.graphview)
            # splitter.addWidget(self.inspector)
            splitter.addWidget(self.nodelistview)
            splitter.setSizes([splitter.width()//splitter.count() for _ in range(splitter.count())])
            self.setLayout(mainLayout)

    app = QApplication()
    window = NXWindow()
    window.show()
    app.exec()