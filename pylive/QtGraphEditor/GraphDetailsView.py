import sys
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from typing import List, Tuple

class MiniTableView(QTableView):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
		self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
		self.setSelectionBehavior(QTableView.SelectRows)
		self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

	def sizeHint(self):
		width = self.verticalHeader().size().width()
		height = self.horizontalHeader().size().height()
		return QSize(134,height)

from Panel import Panel
from GraphModel import GraphModel
class GraphDetailsView(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)

		self._model = None
		# create node details editor

		# node data editors
		self.id_label =  QLabel()
		self.name_edit = QLineEdit()
		self.posx_edit = QSpinBox()
		self.posx_edit.setRange(-9999, 9999)
		self.posy_edit = QSpinBox()
		self.posy_edit.setRange(-9999, 9999)

		### Inlets Table ###
		self.inlets_sheet_editor = MiniTableView()

		
		### Outlets Table ###
		self.outlets_sheet_editor = MiniTableView()

		# self.setLayout(QFormLayout())
		# # self.layout().setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
		# self.layout().addRow("Name:", self.name_edit)
		# self.layout().addRow("Pos X:", self.posx_edit)
		# self.layout().addRow("Pos Y:", self.posy_edit)
		# self.layout().addRow("Inlets:", self.inlets_sheet_editor)
		# self.layout().addRow("Script:", self.script_editor)

		self.mapper = QDataWidgetMapper()
		self.mapper.setSubmitPolicy(QDataWidgetMapper.AutoSubmit)

		self.panel = Panel(
			direction=QBoxLayout.TopToBottom,
			children=[
				self.id_label,
				self.name_edit,
				self.posx_edit,
				self.posy_edit,
				self.inlets_sheet_editor,
				self.outlets_sheet_editor,
			]
		)

		self.setLayout(QVBoxLayout())
		self.layout().addWidget(self.panel)
		self.layout().addStretch()


	def model(self):
		return self._model

	def setModel(self, graphmodel:GraphModel):
		self._model = graphmodel

		# mapper
		
		self.mapper.setModel(graphmodel.nodes)
		# self.mapper.addMapping(self.id_label, 0)
		self.mapper.addMapping(self.name_edit, 1)
		self.mapper.addMapping(self.posx_edit, 2)
		self.mapper.addMapping(self.posy_edit, 3)

		# inlets list
		self.selected_node_inlets = QSortFilterProxyModel()  # Node column is 1 (for node name)
		self.selected_node_inlets.setSourceModel(graphmodel.inlets)
		self.inlets_sheet_editor.setModel(self.selected_node_inlets)
		self.selected_node_inlets.setFilterKeyColumn(1)

		# outlets list
		self.selected_node_outlets = QSortFilterProxyModel()  # Node column is 1 (for node name)
		self.selected_node_outlets.setSourceModel(graphmodel.outlets)
		self.outlets_sheet_editor.setModel(self.selected_node_outlets)
		self.selected_node_outlets.setFilterKeyColumn(1)

		# set no rows
		self.setCurrentModelIndex(QModelIndex())

	def setNodesSelectionModel(self, nodes_selectionmodel:QItemSelectionModel):
		self.nodes_selectionmodel = nodes_selectionmodel
		self.nodes_selectionmodel.currentRowChanged.connect(self.setCurrentModelIndex)
		
	def setCurrentModelIndex(self, index:QModelIndex):
		index = index.siblingAtColumn(0)
		if index.isValid():
			self.id_label.setText(index.data())
			self.mapper.setCurrentModelIndex(index)  # Update the mapper's current index
			node_name = self._model.nodes.itemFromIndex(index).text()  # Get the selected node's name
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
	from GraphTableView import GraphTableView
	class MainWindow(QWidget):
		def __init__(self):
			super().__init__()

			self.setWindowTitle("Graph Details View Example")

			# Initialize the GraphModel
			self.graph_model = GraphModel()
			self.nodes_selectionmodel = QItemSelectionModel(self.graph_model.nodes)

			# Add some example nodes and edges
			node1_id = self.graph_model.addNode("Node 1", 0, 0, "Script 1")
			node2_id = self.graph_model.addNode("Node 2", 10, 200, "Script 2")
			outlet_id = self.graph_model.addOutlet(node1_id, "Out1")
			inlet_id = self.graph_model.addInlet(node2_id, "In1")
			edge = self.graph_model.addEdge(outlet_id, inlet_id)

			# Set up the node editor view
			self.graph_table_view = GraphTableView()
			self.graph_table_view.setModel(self.graph_model)
			self.graph_table_view.setNodesSelectionModel(self.nodes_selectionmodel)
			self.graph_details_view = GraphDetailsView()
			self.graph_details_view.setModel(self.graph_model)
			self.graph_details_view.setNodesSelectionModel(self.nodes_selectionmodel)
			
			self.setLayout(QHBoxLayout())
			self.layout().addWidget(self.graph_table_view, 1)
			self.layout().addWidget(self.graph_details_view, 1)



	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	sys.exit(app.exec())
