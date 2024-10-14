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

from Panel import Panel

from GraphModel import GraphModel
from GraphView import GraphView
from GraphDetailsView import GraphDetailsView
from GraphRunner import GraphRunner
from pathlib import Path

class AppEditor(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GraphEditor")
        self.resize(1600, 500)

        ### SETUP MODEL ###
        self.graphmodel = GraphModel()
        model = self.graphmodel.nodes

        self.nodes_selectionmodel =   QItemSelectionModel(self.graphmodel.nodes)
        self.inlets_selectionmodel =  QItemSelectionModel(self.graphmodel.inlets)
        self.outlets_selectionmodel = QItemSelectionModel(self.graphmodel.outlets)
        self.edges_selectionmodel =   QItemSelectionModel(self.graphmodel.edges)

        self.read("script_cache_test.py")

        self.autosave = False

        ### SETUP ACTIONS ###
        self.setupActions()


        ### SETUP VIEWS ###
        
        ### Table Views ###
        def setup_table_view(model, selectionmodel=None):
            table_view = QTableView()
            table_view.setSelectionBehavior(QTableView.SelectRows)
            table_view.setModel(model)
            table_view.setSelectionModel(selectionmodel)
            table_view.resizeColumnsToContents()
            return table_view

        self.nodes_sheet_view =   setup_table_view(self.graphmodel.nodes,   self.nodes_selectionmodel)
        self.inlets_sheet_view =  setup_table_view(self.graphmodel.inlets,  self.inlets_selectionmodel)
        self.outlets_sheet_view = setup_table_view(self.graphmodel.outlets, self.outlets_selectionmodel)
        self.edges_sheet_view =   setup_table_view(self.graphmodel.edges,   self.edges_selectionmodel)

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

        ### crate preview widget
        self.preview_widget = QLabel()
        
        ### layout all panels
        self.centralWidget().layout().addWidget(sheets_widget, 1)
        self.centralWidget().layout().addWidget(self.graphview, 1)
        self.centralWidget().layout().addWidget(self.details_view, 1)
        self.centralWidget().layout().addWidget(self.preview_widget, 1)

        # bind make script when graph changes
        self.graphmodel.nodesInserted.connect(self.run)
        self.graphmodel.nodesRemoved.connect(self.run)
        self.graphmodel.nodeChanged.connect(self.run)
        self.graphmodel.inletChanged.connect(self.run)
        self.graphmodel.outletChanged.connect(self.run)
        self.graphmodel.edgesInserted.connect(self.run)
        self.graphmodel.edgesRemoved.connect(self.run)
        self.graphmodel.edgeChanged.connect(self.run)

    def run(self):
        script = "# Script\n"
        for node in reversed(list(self.graphmodel.dfs())):
            script += "#%%" + "\n" # add new cell
            script += node.siblingAtColumn(4).data() + "\n"

        self.preview_widget.setText(script)
        if self.autosave:
            self.write(script, "script_cache_test.py")

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

    def read(self, path: Path):
        path = Path(path)
        script = path.read_text(encoding="utf-8")
        cells = []
        for line_number, line in enumerate(script.split("\n")):
            isNewCell = line.startswith("#%%") or line_number==0
            if isNewCell:
                cells.append("")
            cells[-1]+=line+"\n"

        chain = []
        for i, cell in enumerate(cells):
            cell_content = "\n".join([line for line in cell.split("\n") if not line.startswith("#%%")])
            node_id = self.graphmodel.addNode(name="<node>", posx=0, posy=i*100, script=cell_content)
            chain.append(node_id)

        # create the ports
        for source_id, target_id in zip(chain, chain[1:]):
            print("connect nodes", source_id, target_id)
            outlet_id = self.graphmodel.addOutlet(source_id, "out")
            inlet_id = self.graphmodel.addInlet(target_id, "in")
            print("-", outlet_id, inlet_id)
            self.graphmodel.addEdge(outlet_id, inlet_id)

        # ### CREATE NODES ###
        # ticknode_id =      self.graphmodel.addNode(name="ticknode",    posx=0, posy=0, script="#%%\n")
        # preview_id =       self.graphmodel.addNode(name="previewnode", posx=260, posy=0, script="#%%\n")
        # tick_outlet_id =   self.graphmodel.addOutlet(owner_id=ticknode_id, name="tick")
        # display_inlet_id = self.graphmodel.addInlet(owner_id=preview_id, name="display")
        # self.graphmodel.addEdge(tick_outlet_id, display_inlet_id)

    def write(self, script:str, path: Path):
        path = Path(path)
        path.write_text(script, encoding="utf-8")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppEditor()
    window.show()
    sys.exit(app.exec())