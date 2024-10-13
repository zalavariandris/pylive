""" TODOS
- [x] add new nodes
- [x] remove selected nodes
- [x] add new ports
- [x] remove selected ports
- [x] add new edge
- [x] remove selected edges
- [x] remove related items from the models. eg.:
  - ports for nodes
  - and edges for ports
- [x] sync graphview selection
- [x] set current to last selected

- [x] bind edge disconnected event and update the model
- [x] bind edge connected event and update the model

- [ ] create signals for the graphmode (hide implementation details) 

- [ ] create a find node row by its id!
- [ ] remove nodes, ports and edges by rows, and make the id to be equal to the row(Hide the mode implementation)


- [ ] setEditor data when model changes

- [ ] create proxy models for nodes ports and edges to hide implementation details, 
      but keep the compatibility with the TableViews
"""



import sys
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from typing import List, Tuple

from GraphModel import GraphModel
from GraphView import GraphView
from GraphDetailsView import GraphDetailsView

class GraphRunner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setLayout(QVBoxLayout())
        self.title_label = QLabel()
        self.content_frame = QTextEdit()
        self.layout().addWidget(self.title_label)
        self.layout().addWidget(self.content_frame)

        toolbar = QToolBar()
        toolbar.addAction(QAction("restart", self))

        self.layout().setMenuBar(toolbar)

        self.model = None
        self.selectionmodel = None

        self.logs = ""

    def setModel(self, graphmodel:GraphModel):
        self.model = graphmodel

        self.model.nodesInserted.connect(self.run)
        self.model.nodesRemoved.connect(self.run)
        self.model.nodeChanged.connect(self.run)


        self.model.inletChanged.connect(self.run)
        self.model.outletChanged.connect(self.run)

        self.model.edgesInserted.connect(self.run)
        self.model.edgesRemoved.connect(self.run)
        self.model.edgeChanged.connect(self.run)

        self.run()

    def setSelectionModel(self, node_selectionmodel):
        self.selectionmodel = node_selectionmodel

        @self.selectionmodel.currentRowChanged.connect
        def currentRowChanged(current: QModelIndex, previous: QModelIndex):
            self.run()

        @self.selectionmodel.selectionChanged.connect
        def selectionChanged(selected:List[QModelIndex], deselected:List[QModelIndex]):
            self.run()

    def log(self, text="", end="\n"):
        self.logs+=f"{text}{end}"

        self.content_frame.setPlainText(self.logs)

    def clear(self):
        self.logs = ""
        self.content_frame.setPlainText(self.logs)

    @Slot()
    def run(self):
        self.clear()
        

        if self.selectionmodel and self.selectionmodel.hasSelection():
            node = self.selectionmodel.currentIndex()
            self.log(f"{node.siblingAtColumn(1).data()} {node.data()}")
            self.log("Inlets")
            for inlet in self.model.findInlets(node):
                self.log(f"- {inlet.siblingAtColumn(2).data()}, {inlet.data()}")
            self.log("Outlets")
            for outlet in self.model.findOutlets(node):
                self.log(f"- {outlet.siblingAtColumn(2).data()}, {outlet.data()}")
            self.log()
            self.log("Source nodes")
            for source in self.model.findConnectedNodes(node, direction="SOURCE"):
                self.log(f"- {source.siblingAtColumn(1).data()}, {source.data()}")
            self.log()
            self.log("Target nodes")
            for source in self.model.findConnectedNodes(node, direction="TARGET"):
                self.log(f"- {source.siblingAtColumn(1).data()}, {source.data()}")

        else:
            self.log("# Root Nodes")
            for node in self.model.rootRodes():
                self.log(f"- {node.siblingAtColumn(1).data()} {node.data()}")
            self.log()
            self.log("# DFS")
            self.log("## roots")
            for node in self.model.rootRodes():
                self.log(node.data())
            self.log("## path")
            for node in reversed(list(self.model.dfs())):
                self.log(node.data())



        
        # print("root nodes:")
        # for node in self.model.root_nodes():
        #     print(f" -{node}")
        # dfs = self.model.dfs()
        # print(list(dfs))

class Panel(QWidget):
    def __init__(self, direction=QBoxLayout.LeftToRight, children=[], menuBar=None, parent=None):
        super().__init__(parent)
        self.setLayout(QBoxLayout(direction))
        self.layout().setContentsMargins(0,0,0,0)
        if menuBar:
            self.layout().setMenuBar(menuBar)

        for child in children:
            self.layout().addWidget(child)

class AppEditor(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GraphEditor")
        self.resize(1600, 500)

        ### SETUP MODEL ###
        self.graphmodel = GraphModel()
        model = self.graphmodel.nodes
        new_column_index = model.columnCount()  # This will be 2 (0-indexed)
        model.setColumnCount(new_column_index + 1)  # Add an extra column (making it 3 total columns)
        model.setHeaderData(new_column_index, Qt.Horizontal, "Script")  # Set header name

        self.nodes_selectionmodel = QItemSelectionModel(self.graphmodel.nodes)
        self.inlets_selectionmodel = QItemSelectionModel(self.graphmodel.inlets)
        self.outlets_selectionmodel = QItemSelectionModel(self.graphmodel.outlets)
        self.edges_selectionmodel = QItemSelectionModel(self.graphmodel.edges)

        ### CREATE NODES ###
        ticknode_id =      self.graphmodel.addNode(name="ticknode",    posx=0, posy=0)
        preview_id =       self.graphmodel.addNode(name="previewnode", posx=260, posy=0)
        tick_outlet_id =   self.graphmodel.addOutlet(owner_id=ticknode_id, name="tick")
        display_inlet_id = self.graphmodel.addInlet(owner_id=preview_id, name="display")
        self.graphmodel.addEdge(tick_outlet_id, display_inlet_id)

        ### SETUP ACTIONS ###
        self.setupActions()


        ### SETUP VIEWS ###
        
        ### Table Views ###
        def setup_table_view(model, selectionmodel=None):
            table_view = QTableView()
            table_view.setSelectionBehavior(QTableView.SelectRows)
            table_view.setModel(self.graphmodel.nodes)
            table_view.setSelectionModel(self.nodes_selectionmodel)
            table_view.resizeColumnsToContents()
            return table_view

        self.nodes_sheet_view =   setup_table_view(self.graphmodel.nodes,   self.nodes_selectionmodel)
        self.inlets_sheet_view =  setup_table_view(self.graphmodel.inlets,  self.inlets_selectionmodel)
        self.outlets_sheet_view = setup_table_view(self.graphmodel.outlets, self.outlets_selectionmodel)
        self.edges_sheet_view =   setup_table_view(self.graphmodel.nodes,   self.edges_selectionmodel)

        ### Graph View ###
        self.graphview = GraphView()
        self.graphview.setModel(self.graphmodel)
        self.graphview.setNodeSelectionModel(self.nodes_selectionmodel)

        ### Node Details View ###
        self.details_view = GraphDetailsView()
        self.details_view.setModel(self.graphmodel)

        self.nodes_selectionmodel.selectionChanged.connect(lambda selected, deselected: # Update details view when the selection changes 
            self.details_view.setCurrentModelIndex(
                selected.indexes()[0] if selected.indexes() else QModelIndex()
            )
        )

        # Layout Widgets
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(QHBoxLayout())
        self.centralWidget().layout().setContentsMargins (0,0,0,0)

        nodes_toolbar = QToolBar()
        nodes_toolbar.addAction(self.new_node_action)
        nodes_toolbar.addAction(self.remove_node_action)

        nodes_tab = Panel(
            menuBar=nodes_toolbar,
            children=[
                self.nodes_sheet_view
            ]
        )

        inlets_toolbar = QToolBar()
        inlets_toolbar.addAction(self.new_inlet_action)
        inlets_toolbar.addAction(self.remove_inlet_action)
        inlets_toolbar.addAction(self.new_edge_action)


        outlets_toolbar = QToolBar()
        outlets_toolbar.addAction(self.new_outlet_action)
        outlets_toolbar.addAction(self.remove_outlet_action)

        ports_tab = Panel(
            direction=QBoxLayout.LeftToRight,
            children=[
                Panel(
                    menuBar=outlets_toolbar,
                    children=[
                        self.outlets_sheet_view
                    ]
                ),
                Panel(
                    menuBar=inlets_toolbar,
                    children=[
                        self.inlets_sheet_view
                    ]
                )
            ]
        )

        edges_toolbar = QToolBar()
        edges_toolbar.addAction(self.remove_edge_action)
        edges_tab = Panel(
            menuBar=edges_toolbar,
            children=[
                self.edges_sheet_view
            ]
        )

        sheets_widget = QTabWidget()
        sheets_widget.addTab(nodes_tab, "nodes")
        sheets_widget.addTab(ports_tab, "ports")
        sheets_widget.addTab(edges_tab, "edges")


        self.graph_runner = GraphRunner()
        self.graph_runner.setModel(self.graphmodel)
        self.graph_runner.setSelectionModel(self.nodes_selectionmodel)
        self.centralWidget().layout().addWidget(sheets_widget, 1)
        self.centralWidget().layout().addWidget(self.graphview, 1)
        self.centralWidget().layout().addWidget(self.details_view, 1)
        self.centralWidget().layout().addWidget(self.graph_runner, 1)

    def setupActions(self):
        ### Setup Action ###
        self.new_node_action = QAction("new node", self)
        @self.new_node_action.triggered.connect
        def add_new_node():
            node_id = self.graphmodel.addNode("new node", "0", "0")
            # Select the new node in the table view
            new_index = self.graphmodel.nodes.index(self.graphmodel.nodes.rowCount()-1, 0)  # Select the last node added
            self.nodes_selectionmodel.clearSelection()
            self.nodes_selectionmodel.setCurrentIndex(new_index, QItemSelectionModel.Select | QItemSelectionModel.Rows)

            self.graphmodel.addInlet(node_id, "in")
            self.graphmodel.addOutlet(node_id, "out")

        self.remove_node_action = QAction("remove selected nodes", self)
        @self.remove_node_action.triggered.connect
        def remove_selected_nodes():
            selected_indexes = self.nodes_selectionmodel.selectedIndexes() # Get the selected indexes from the node selection model
            if not selected_indexes:
                return  # No node is selected, exit the function
            self.graphmodel.removeNodes(selected_indexes) # remove the nodes from the graphmodel
            self.nodes_selectionmodel.clearSelection() # Clear any remaining selection in the nodes view

        self.new_outlet_action = QAction("new outlet", self)
        @self.new_outlet_action.triggered.connect
        def add_new_outlet():
            current_index = self.nodes_selectionmodel.currentIndex()
            if not current_index.isValid():
                return
            owner_id = self.graphmodel.nodes.item(current_index.row(), 0).text()

            self.graphmodel.addOutlet(owner_id=owner_id, name="out")

        self.remove_outlet_action = QAction("remove outlet", self)
        @self.remove_outlet_action.triggered.connect
        def remove_selected_outlets():
            selected_indexes = self.outlets_selectionmodel.selectedIndexes() # Get the selected indexes from the node selection model
            if not selected_indexes:
                return  # No node is selected, exit the function
            self.graphmodel.removeOutlets(index.row() for index in selected_indexes) # remove the nodes from the graphmodel
            self.outlets_selectionmodel.clearSelection() # Clear any remaining selection in the nodes view

        self.new_inlet_action = QAction("new inlet", self)
        @self.new_inlet_action.triggered.connect
        def add_new_inlet():
            current_index = self.nodes_selectionmodel.currentIndex()
            if not current_index.isValid():
                return
            owner_id = self.graphmodel.nodes.item(current_index.row(), 0).text()
            self.graphmodel.addInlet(owner_id=owner_id, name="in")

        self.remove_inlet_action = QAction("remove inlet", self)
        @self.remove_inlet_action.triggered.connect
        def remove_selected_inlets():
            selected_indexes = self.inlets_selectionmodel.selectedIndexes() # Get the selected indexes from the node selection model
            if not selected_indexes:
                return  # No node is selected, exit the function
            self.graphmodel.removeInlets(index.row() for index in selected_indexes) # remove the nodes from the graphmodel
            self.inlets_selectionmodel.clearSelection() # Clear any remaining selection in the nodes view

        self.new_edge_action = QAction("new edge", self)
        @self.new_edge_action.triggered.connect
        def add_new_edge_to_current_ports():
            current_outlet_index = self.outlets_selectionmodel.currentIndex()
            current_inlet_index = self.inlets_selectionmodel.currentIndex()
            if not current_outlet_index.isValid() or not current_inlet_index.isValid():
                return
            outlet_id = self.graphmodel.outlets.item(current_outlet_index.row(), 0).text()
            inlet_id =  self.graphmodel.inlets.item(current_inlet_index.row(), 0).text()
            self.graphmodel.addEdge(outlet_id, inlet_id)

        self.remove_edge_action = QAction("remove selected edges", self)
        @self.remove_edge_action.triggered.connect
        def remove_selected_edges():
            selected_indexes = self.edges_selectionmodel.selectedIndexes() # Get the selected indexes from the node selection model
            if not selected_indexes:
                return  # No node is selected, exit the function
            self.graphmodel.removeEdges(index.row() for index in selected_indexes) # remove the nodes from the graphmodel
            self.edges_selectionmodel.clearSelection() # Clear any remaining selection in the nodes view




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppEditor()
    window.show()
    sys.exit(app.exec())