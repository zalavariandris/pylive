import sys
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from typing import List, Tuple

class MiniTableView(QTableView):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
		self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
		self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
		
		# self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

from pylive.Panel import Panel
from graphmodel_columnbased import GraphModel, NodeIndex, EdgeIndex, InletIndex, OutletIndex
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

		self.inlets_menubar = QMenuBar()
		addInletAction = QAction("＋", self)
		addInletAction.triggered.connect(self.addInletToCurrentNode)
		removeInletAction = QAction("－", self)
		removeInletAction.triggered.connect(self.removeSelectedInlets)
		self.inlets_menubar.addAction(addInletAction)
		self.inlets_menubar.addAction(removeInletAction)

		
		### Outlets Table ###
		self.outlets_sheet_editor = MiniTableView()

		self.outlets_menubar = QMenuBar()
		addOutletAction = QAction("＋", self)
		addOutletAction.triggered.connect(self.addOutletToCurrentNode)
		addOutletAction.triggered.connect(self.removeSelectedOutlets)
		removeOutletAction = QAction("－", self)
		self.outlets_menubar.addAction(addOutletAction)
		self.outlets_menubar.addAction(removeOutletAction)
		

		formLayout = QFormLayout()
		# self.layout().setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
		formLayout.addRow("Name:", self.name_edit)
		formLayout.addRow("Pos X:", self.posx_edit)
		formLayout.addRow("Pos Y:", self.posy_edit)
		formLayout.addRow("Inlets:", Panel(direction=QBoxLayout.Direction.TopToBottom,
			children=[
				self.inlets_sheet_editor
			],
			menuBar=self.inlets_menubar
		))
		formLayout.addRow("Outlets:", Panel(direction=QBoxLayout.Direction.TopToBottom,
			children=[
				self.outlets_sheet_editor
			],
			menuBar=self.outlets_menubar
		))
		self.panel = QWidget()
		self.panel.setLayout(formLayout)

		self.mapper = QDataWidgetMapper()
		self.mapper.setSubmitPolicy(QDataWidgetMapper.SubmitPolicy.AutoSubmit)

		# self.panel = Panel(
		# 	direction=QBoxLayout.TopToBottom,
		# 	children=[
		# 		self.id_label,
		# 		self.name_edit,
		# 		self.posx_edit,
		# 		self.posy_edit,
		# 		self.inlets_sheet_editor,
		# 		self.outlets_sheet_editor,
		# 	]
		# )

		main_layout = QVBoxLayout()
		self.setLayout(main_layout)
		main_layout.addWidget(self.panel)
		main_layout.addStretch()

	def addOutletToCurrentNode(self):
		if self._model and self.nodes_selectionmodel:
			node = NodeIndex(self.nodes_selectionmodel.currentIndex())
			outlet = self._model.addOutlet(node, "<out>")
			self.outlets_sheet_editor.selectRow(outlet.row())
			self.outlets_sheet_editor.setCurrentIndex(outlet)

	def addInletToCurrentNode(self):
		if self._model and self.nodes_selectionmodel:
			node = NodeIndex(self.nodes_selectionmodel.currentIndex())
			inlet = self._model.addInlet(node, "<in>")
			self.inlets_sheet_editor.selectRow(inlet.row())
			self.inlets_sheet_editor.setCurrentIndex(inlet)

	def removeSelectedInlets(self):
		if self._model:
			inlets = [InletIndex(idx) for idx in self.inlets_sheet_editor.selectedIndexes() if idx.column()==0]
			print("removeSelectedInlets: {selectedIndexes}")
			self._model.removeInlets(inlets)

	def removeSelectedOutlets(self):
		if self._model:
			outlets = [OutletIndex(idx) for idx in self.outlets_sheet_editor.selectedIndexes() if idx.column()==0]
			self._model.removeOutlets(outlets)

	def model(self):
		return self._model

	def setModel(self, graphmodel:GraphModel):
		self._model = graphmodel

		# mapper
		
		self.mapper.setModel(graphmodel.nodeTable)
		# self.mapper.addMapping(self.id_label, 0)
		self.mapper.addMapping(self.name_edit, 1)
		self.mapper.addMapping(self.posx_edit, 2)
		self.mapper.addMapping(self.posy_edit, 3)

		# inlets list
		self.selected_node_inlets = QSortFilterProxyModel()  # Node column is 1 (for node name)
		self.selected_node_inlets.setSourceModel(graphmodel.inletTable)
		self.selected_node_inlets.setFilterKeyColumn(1)
		self.inlets_sheet_editor.setModel(self.selected_node_inlets)
		

		# outlets list
		self.selected_node_outlets = QSortFilterProxyModel()  # Node column is 1 (for node name)
		self.selected_node_outlets.setSourceModel(graphmodel.outletTable)
		self.selected_node_outlets.setFilterKeyColumn(1)
		self.outlets_sheet_editor.setModel(self.selected_node_outlets)

		# set no rows
		self.setCurrentModelIndex(NodeIndex())

	def setNodesSelectionModel(self, nodes_selectionmodel:QItemSelectionModel):
		self.nodes_selectionmodel = nodes_selectionmodel
		self.nodes_selectionmodel.currentRowChanged.connect(self.setCurrentModelIndex)

	def setCurrentModelIndex(self, index:NodeIndex):
		if not self._model:
			return

		index = NodeIndex(index.siblingAtColumn(0))
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
	from graphtableview_columnbased import GraphTableView
	class MainWindow(QWidget):
		def __init__(self):
			super().__init__()

			self.setWindowTitle("Graph Details View Example")

			# Initialize the GraphModel
			self.graph_model = GraphModel()
			self.nodes_selectionmodel = QItemSelectionModel(self.graph_model.nodeTable)

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
			
			main_layout = QHBoxLayout()
			self.setLayout(main_layout)
			main_layout.addWidget(self.graph_table_view, 1)
			main_layout.addWidget(self.graph_details_view, 1)

	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	sys.exit(app.exec())