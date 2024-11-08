from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from typing import *

from graphmodel_rolebased import GraphModel, NodeIndex
from graphlistview_rolebased import GraphListView
from pylive.Panel import Panel

class NodeDetailsView(QWidget):
	def __init__(self, parent: Optional[QWidget] = None) -> None:
		super().__init__(parent)
		self.graph = None

		# setup widget layout
		main_layout = QVBoxLayout()
		self.setLayout(main_layout)
		# main_layout.addStretch()

		# setup main panel
		formLayout = QFormLayout()
		self.panel = QWidget()
		self.panel.setLayout(formLayout)
		main_layout.insertWidget(0, self.panel)

		# setup node data editors
		self.id_label =  QLabel()
		self.name_edit = QLineEdit()
		self.posx_edit = QSpinBox()
		self.posx_edit.setRange(-9999, 9999)
		self.posy_edit = QSpinBox()
		self.posy_edit.setRange(-9999, 9999)

		formLayout.addRow("Name:", self.name_edit)
		formLayout.addRow("Pos X:", self.posx_edit)
		formLayout.addRow("Pos Y:", self.posy_edit)

		self.mapper = QDataWidgetMapper()
		self.mapper.setSubmitPolicy(QDataWidgetMapper.SubmitPolicy.AutoSubmit)

		# setup relation editors

	def setModel(self, graph_model:GraphModel):
		self.graph = graph_model

		self.mapper.setModel(self.graph.nodeList)
		# self.mapper.addMapping(self.id_label, 0)
		self.mapper.addMapping(self.name_edit, 1)
		self.mapper.addMapping(self.posx_edit, 2)
		self.mapper.addMapping(self.posy_edit, 3)

	def setNodesSelectionModel(self, nodes_selectionmodel:QItemSelectionModel):
		if nodes_selectionmodel.model() !=self.graph.nodeList:
			raise ValueError("selection model is not the graph nodes list")
		self.nodes_selectionmodel = nodes_selectionmodel
		self.nodes_selectionmodel.currentChanged.connect(lambda index:
			self.handleCurrentNodeChanged(NodeIndex(index))
		)

	def handleCurrentNodeChanged(self, index:NodeIndex):
		if not self.graph:
			return

		# index = NodeIndex(index.siblingAtColumn(0))
		if index.isValid():
			self.id_label.setText(index.data())
			self.mapper.setCurrentModelIndex(index)  # Update the mapper's current index
			node_name = self._model.nodeTable.itemFromIndex(index).text()  # Get the selected node's name
			self.selected_node_inlets.setFilterFixedString(node_name) # update inlet filters
			self.selected_node_outlets.setFilterFixedString(node_name) # update outlet filters
			self.panel.show()
		else:
			self.panel.hide()
			# clear widgets
			self.name_edit.setText("")
			self.selected_node_inlets.setFilterFixedString("SOMETHING COMPLICATED ENOUGHT NOT TO MATC ANY NODE NAMES") # update inlet filters
			self.selected_node_outlets.setFilterFixedString("SOMETHING COMPLICATED ENOUGHT NOT TO MATC ANY NODE NAMES") # update outlet filters

		self.layout().invalidate()

if __name__ == "__main__":
	import sys
	from graphlistview_rolebased import GraphListView
	class MainWindow(QWidget):
		def __init__(self):
			super().__init__()

			self.setWindowTitle("Graph Details View Example")

			# Initialize the GraphModel
			self.graph_model = GraphModel()
			self.nodes_selectionmodel = QItemSelectionModel(self.graph_model.nodeList)

			# Add some example nodes and edges
			node1_id = self.graph_model.addNode("Node 1", 0, 0)
			node2_id = self.graph_model.addNode("Node 2", 10, 200)
			outlet_id = self.graph_model.addOutlet(node1_id, "Out1")
			inlet_id = self.graph_model.addInlet(node2_id, "In1")
			edge = self.graph_model.addEdge(outlet_id, inlet_id)

			# Set up the node editor view
			self.graph_list_view = GraphListView()
			self.graph_list_view.setModel(self.graph_model)
			self.graph_list_view.setNodesSelectionModel(self.nodes_selectionmodel)
			self.graph_details_view = NodeDetailsView()
			self.graph_details_view.setModel(self.graph_model)
			self.graph_details_view.setNodesSelectionModel(self.nodes_selectionmodel)
			
			main_layout = QHBoxLayout()
			self.setLayout(main_layout)
			main_layout.addWidget(self.graph_list_view, 1)
			main_layout.addWidget(self.graph_details_view, 1)

	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	sys.exit(app.exec())