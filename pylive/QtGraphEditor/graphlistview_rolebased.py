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

- edit node data
- edit inlets data
- edit outlets data
- edit edges data


# - [ ] create signals for the graphmodel (hide implementation details) 

# - [ ] create a find node row by its id!



# - [ ] setEditor data when model changes

# - [ ] create proxy models for nodes ports and edges to hide implementation details, 
#       but keep the compatibility with the TableViews
"""



import sys
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from typing import List, Tuple

from shiboken6 import isValid

from pylive.Panel import Panel

from pylive.QtGraphEditor.graphmodel_rolebased import GraphModel, NodeIndex, InletIndex, OutletIndex, EdgeIndex
from pathlib import Path

class GraphListView(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("GraphListView")
		# self.resize(1600, 500)


		### SETUP ACTIONS ###
		self.setupActions()

		### SETUP VIEWS ###
		
		### List Views ###
		self.nodes_list_view = QListView()
		self.inlets_list_view = QListView()
		self.outlets_list_view = QListView()
		self.edges_list_view = QListView()

		# Layout Widgets
		main_layout = QHBoxLayout()
		self.setLayout(main_layout)
		self.layout().setContentsMargins (0,0,0,0)

		nodes_toolbar = QToolBar()
		nodes_toolbar.addAction(self.new_node_action)
		nodes_toolbar.addAction(self.remove_node_action)

		nodes_tab = Panel(
			menuBar=nodes_toolbar,
			children=[
				self.nodes_list_view
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
			direction=QBoxLayout.Direction.LeftToRight,
			children=[
				Panel(
					menuBar=outlets_toolbar,
					children=[
						self.outlets_list_view
					]
				),
				Panel(
					menuBar=inlets_toolbar,
					children=[
						self.inlets_list_view
					]
				)
			]
		)

		edges_toolbar = QToolBar()
		edges_toolbar.addAction(self.remove_edge_action)
		edges_tab = Panel(
			menuBar=edges_toolbar,
			children=[
				self.edges_list_view
			]
		)

		sheets_widget = QTabWidget()
		sheets_widget.addTab(nodes_tab, "nodes")
		sheets_widget.addTab(ports_tab, "ports")
		sheets_widget.addTab(edges_tab, "edges")


		### layout all panels
		main_layout.addWidget(sheets_widget, 1)

	def setModel(self, graphmodel:GraphModel):
		self.graphmodel = graphmodel

		# bind table views
		self.nodes_list_view.setModel(self.graphmodel.nodeList)
		self.inlets_list_view.setModel(self.graphmodel.inletList)
		self.outlets_list_view.setModel(self.graphmodel.outletList)
		self.edges_list_view.setModel(self.graphmodel.edgeList)

	def setNodesSelectionModel(self, nodes_selectionmodel:QItemSelectionModel):
		self.nodes_list_view.setSelectionModel(nodes_selectionmodel)

	def setInletsSelectionModel(self, inlets_selectionmodel:QItemSelectionModel):
		self.inlets_list_view.setSelectionModel(inlets_selectionmodel)

	def setOutletsSelectionModel(self, outlets_selectionmodel:QItemSelectionModel):
		self.outlets_list_view.setSelectionModel(outlets_selectionmodel)

	def setEdgesSelectionModel(self, edges_selectionmodel:QItemSelectionModel):
		self.edges_list_view.setSelectionModel(edges_selectionmodel)

	def setupActions(self):
		### Setup Action ###
		self.new_node_action = QAction("new node", self)
		@self.new_node_action.triggered.connect
		def add_new_node():
			node = self.graphmodel.addNode("new node", 0, 0)
			# Select the new node in the list view
			self.graphmodel.addInlet(node, "in")
			self.graphmodel.addOutlet(node, "out")

		self.remove_node_action = QAction("remove selected nodes", self)
		@self.remove_node_action.triggered.connect
		def remove_selected_nodes():
			selected_indexes = [NodeIndex(idx) for idx in self.nodes_list_view.selectedIndexes()] # Get the selected indexes from the node selection model
			self.graphmodel.removeNodes(selected_indexes) # remove the nodes from the graphmodel
		self.new_outlet_action = QAction("new outlet", self)

		@self.new_outlet_action.triggered.connect
		def add_outlet_for_current_node():
			current_index = NodeIndex(self.nodes_list_view.currentIndex())
			if current_index.isValid():
				self.graphmodel.addOutlet(current_index, name="out")

		self.remove_outlet_action = QAction("remove outlet", self)
		@self.remove_outlet_action.triggered.connect
		def remove_selected_outlets():
			selected_indexes = [OutletIndex(idx) for idx in self.outlets_list_view.selectedIndexes()] # Get the selected indexes from the node selection model
			if not selected_indexes:
				return  # No node is selected, exit the function
			self.graphmodel.removeOutlets(selected_indexes) # remove the nodes from the graphmodel

		self.new_inlet_action = QAction("new inlet", self)
		@self.new_inlet_action.triggered.connect
		def add_inlet_for_current_node():
			current_index = NodeIndex(self.nodes_list_view.currentIndex())
			if current_index.isValid():
				self.graphmodel.addInlet(node=current_index, name="in")

		self.remove_inlet_action = QAction("remove inlet", self)
		@self.remove_inlet_action.triggered.connect
		def remove_selected_inlets():
			selected_indexes = [InletIndex(idx) for idx in self.inlets_list_view.selectedIndexes()] # Get the selected indexes from the node selection model
			self.graphmodel.removeInlets(selected_indexes) # remove the nodes from the graphmodel

		self.new_edge_action = QAction("new edge", self)
		@self.new_edge_action.triggered.connect
		def add_edge_to_current_ports():
			print("add new edge")
			current_outlet_index = OutletIndex(self.outlets_list_view.currentIndex())
			current_inlet_index = InletIndex(self.inlets_list_view.currentIndex())
			print("add new edge", current_outlet_index, current_inlet_index)
			self.graphmodel.addEdge(current_outlet_index, current_inlet_index)

		self.remove_edge_action = QAction("remove selected edges", self)
		@self.remove_edge_action.triggered.connect
		def remove_selected_edges():
			selected_indexes = [EdgeIndex(idx) for idx in self.edges_list_view.selectedIndexes()] # Get the selected indexes from the node selection model
			self.graphmodel.removeEdges(selected_indexes) # remove the nodes from the graphmodel


if __name__ == "__main__":
	app = QApplication(sys.argv)
	graph_model = GraphModel()
	node1_id = graph_model.addNode("Node 1", 100, 100)
	node2_id = graph_model.addNode("Node 2", 300, 150)
	outlet_id = graph_model.addOutlet(node1_id, "Out1")
	inlet_id = graph_model.addInlet(node2_id, "In1")
	edge = graph_model.addEdge(outlet_id, inlet_id)

	nodes_selectionmodel =   QItemSelectionModel(graph_model.nodeList)
	inlets_selectionmodel =  QItemSelectionModel(graph_model.inletList)
	outlets_selectionmodel = QItemSelectionModel(graph_model.outletList)
	edges_selectionmodel =   QItemSelectionModel(graph_model.edgeList)

	graph_view1 = GraphListView()
	graph_view1.setModel(graph_model)
	graph_view1.setNodesSelectionModel(nodes_selectionmodel)
	graph_view1.setInletsSelectionModel(inlets_selectionmodel)
	graph_view1.setOutletsSelectionModel(outlets_selectionmodel)
	graph_view1.setEdgesSelectionModel(edges_selectionmodel)

	graph_view2 = GraphListView()
	graph_view2.setModel(graph_model)
	graph_view2.setNodesSelectionModel(nodes_selectionmodel)
	graph_view2.setInletsSelectionModel(inlets_selectionmodel)
	graph_view2.setOutletsSelectionModel(outlets_selectionmodel)
	graph_view2.setEdgesSelectionModel(edges_selectionmodel)
	
	window = QWidget()
	window.setWindowTitle("GraphListView for role based graphmodel")
	layout = QVBoxLayout()
	window.setLayout(layout)
	layout.addWidget(graph_view1, 1)
	layout.addWidget(graph_view2, 1)
	window.show()
	sys.exit(app.exec())