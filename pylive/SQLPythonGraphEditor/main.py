#main.py

from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtSql import *


from sql_graph_model import SQLGraphModel
from sql_graph_view import SQLGraphScene


class NodesOfGraphProxyModel(QSortFilterProxyModel):
    def __init__(self, parent: QObject|None=None) -> None:
        super().__init__(parent=parent)
        self._graph_key:int|None = None

    def setSourceGraph(self, graph_key:int):
        self._graph_key = graph_key

    # @override
    # def filterAcceptsRow(self, source_row:int, source_parent:QModelIndex|QPersistentModelIndex):
    #     source_model = self.sourceModel()
    #     graph_key = self._graph_key
    #     print("filter accepts row")
    #     if source_model is None or graph_key is None:
    #         return False
    #     assert source_model
    #     assert graph_key

    #     filter_column = source_model.record().indexOf("graph")
    #     print(filter_column)
    #     graphIdIndex = source_model.index(source_row, 
    #         filter_column, 
    #         source_parent)
        
    #     print(graphIdIndex)
    #     return True
    #     return self.sourceModel().data(graphIdIndex).toInt() == self._graph_key;



class GraphInspector(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        ### database inspector
        node_inspector = QWidget()
        # self._proxy_model = QSortFilterProxyModel()
        self._node_of_graph_proxy = NodesOfGraphProxyModel()

        self._nodes_table = QTableView()
        self._nodes_table.setModel(self._node_of_graph_proxy)

        main_layout = QVBoxLayout()
        main_layout.addWidget(QLabel("GraphInspector"))
        main_layout.addWidget(self._nodes_table)
        self.setLayout(main_layout)

    def setModel(self, source_model:SQLGraphModel):
        self._node_of_graph_proxy.setSourceModel(source_model.nodes)

    def setGraph(self, graph_key:int):
        self._node_of_graph_proxy.setSourceGraph(graph_key)


class Window(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__()
        self.setWindowTitle("SQLGraphEditor")

        self.model = SQLGraphModel()
        self.graph_selection = QItemSelectionModel(self.model.graphs)
        self.node_selection = QItemSelectionModel(self.model.nodes)
        self.edge_selection = QItemSelectionModel(self.model.edges)
        
        ### Views
        self.graphs_table = QTableView()
        self.graphs_table.setModel(self.model.graphs)
        self.graphs_table.setSelectionModel(self.graph_selection)
        self.graphs_table.setItemDelegate(QSqlRelationalDelegate(self.graphs_table))

        self.nodes_table = QTableView()
        self.nodes_table.setModel(self.model.nodes)
        self.nodes_table.setSelectionModel(self.node_selection)
        self.nodes_table.setItemDelegate(QSqlRelationalDelegate(self.nodes_table))

        self.edges_table = QTableView()
        self.edges_table.setModel(self.model.edges)
        self.edges_table.setSelectionModel(self.edge_selection)
        self.edges_table.setItemDelegate(QSqlRelationalDelegate(self.edges_table))

        # self.graph_editor_scene = SQLGraphScene()
        # self.graph_editor_scene.setModel(self.model)
        # self.graph_editor_view = QGraphicsView()
        # self.graph_editor_view.setScene(self.graph_editor_scene)

        ### actions 
        add_graph_action = QAction("add new graph", self)
        add_graph_action.triggered.connect(lambda: self.create_new_graph())
        remove_graphs_action = QAction("remove graphs", self)
        remove_graphs_action.triggered.connect(lambda: self.remove_selected_graphs())

        add_node_action = QAction("add new node", self)
        add_node_action.triggered.connect(lambda: self.create_new_node())
        remove_nodes_action = QAction("remove nodes", self)
        remove_nodes_action.triggered.connect(lambda: self.remove_selected_nodes())

        add_edge_action = QAction("add new edge", self)
        add_edge_action.triggered.connect(lambda: self.create_new_edge())
        remove_edges_action = QAction("remove edge", self)
        remove_edges_action.triggered.connect(lambda: self.remove_selected_edges())

        ### menubar
        menubar = QMenuBar(self)
        menubar.addAction(add_graph_action)
        menubar.addAction(remove_graphs_action)
        menubar.addAction(add_node_action)
        menubar.addAction(remove_nodes_action)
        menubar.addAction(add_edge_action)
        menubar.addAction(remove_edges_action)

        ### holistic database viewer
        database_viewer = QSplitter()
        database_viewer.addWidget(self.graphs_table)
        database_viewer.addWidget(self.nodes_table)
        database_viewer.addWidget(self.edges_table)
        database_viewer.setSizes([database_viewer.width()//database_viewer.count() for _ in range(database_viewer.count())])

        ### database inspector
        self.graph_inspector = GraphInspector()
        self.graph_inspector.setModel(self.model)
        self.graph_inspector.setGraph(1)

        ###
        main_layout = QVBoxLayout()
        main_layout.setMenuBar(menubar)
        main_layout.addWidget(database_viewer)
        # main_layout.addWidget(self.graph_inspector)
        # main_layout.addWidget(self.graph_editor_view)

        self.setLayout(main_layout)

    @Slot()
    def create_new_graph(self):
        self.model.create_graph("new graph")

    @Slot()
    def remove_selected_graphs(self):
        for index in self.graph_selection.selectedIndexes():
            graph_key =  self.model.graphs.record(index.row()).value("key")
            self.model.delete_graph(graph_key)

    @Slot()
    def create_new_node(self):
        current = self.graph_selection.currentIndex()
        graph_key = 1#self.model.graphs.record(current.row()).value("key")
        self.model.add_node(graph_key, "new node")

    @Slot()
    def remove_selected_nodes(self):
        for index in self.node_selection.selectedIndexes():
            node_key = self.model.nodes.record(index.row()).value("key")
            self.model.delete_node(node_key)

    @Slot()
    def create_new_edge(self):
        current_node = self.node_selection.currentIndex()
        selected_nodes = self.node_selection.selectedIndexes()
        
        current_node_key = self.model.nodes.record(current_node.row()).value("key")
        selected_node_keys = [self.model.nodes.record(_.row()).value("key") for _ in selected_nodes]

        for source_node_key in selected_node_keys:
            if source_node_key !=current_node_key:
                self.model.add_edge(source_node_key, current_node_key)

        print(current_node_key)
        print("-", selected_node_keys)

    @Slot()
    def remove_selected_edges(self):
        for index in self.edge_selection.selectedIndexes():
            edge_key = self.model.edges.record(index.row()).value("key")
            self.model.delete_edge(edge_key)
            



if __name__ == "__main__":
    app = QApplication()
    window = Window()
    window.show()
    app.exec()