import sys
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


class NodeFilterProxyModel(QSortFilterProxyModel):
	def __init__(self, node_column, parent=None):
		super().__init__(parent)
		self.node_column = node_column
		self.node_name = ""

	def setNodeName(self, node_name):
		self.node_name = node_name
		self.invalidateFilter()

	def filterAcceptsRow(self, source_row, source_parent):
		index = self.sourceModel().index(source_row, self.node_column, source_parent)
		return self.sourceModel().data(index) == self.node_name


class AppEditor(QMainWindow):
	def __init__(self, parent=None):
		super().__init__(parent)

		
		### CREATE QT MODELS ###
		### Nodes Model ###
		self.nodesmodel = QStandardItemModel()
		self.nodesmodel.setHorizontalHeaderLabels(['name', 'script'])
		self.nodes_selectionmodel = QItemSelectionModel(self.nodesmodel)

		for n in [{"name": "ticknode"}, {"name": "previewnode"}]:
			name_item =   QStandardItem(n['name'])
			script_item = QStandardItem(f"#{n['name']}")
			self.nodesmodel.appendRow([name_item, script_item])

		### Inlets Model ###
		self.inletsmodel = QStandardItemModel()
		self.inletsmodel.setHorizontalHeaderLabels(['name', "node"])

		for inlet in [{"name": "input", "node": "previewnode"}]:
			name_item =   QStandardItem(inlet['name'])
			node_item =   QStandardItem(inlet['node'])

			self.inletsmodel.appendRow([name_item, node_item])

		### Outlets Model ###
		self.outletsmodel = QStandardItemModel()
		self.outletsmodel.setHorizontalHeaderLabels(['name', "node"])

		for outlet in [{"name": "output", "node": "ticknode"}]:
			name_item =   QStandardItem(outlet['name'])
			node_item =   QStandardItem(outlet['node'])

			self.outletsmodel.appendRow([name_item, node_item])

		### Edges Model ###
		self.edgesmodel = QStandardItemModel()
		self.edgesmodel.setHorizontalHeaderLabels(['source', "outlet", "target", "inlet"])
		for edge in [{"source":"ticknode", "outlet": "out", "target": "previewnode", "inlet":"display"}]:
			source_item =   QStandardItem(edge['source'])
			outlet_item =   QStandardItem(edge['outlet'])
			target_item =   QStandardItem(edge['target'])
			inlet_item =   QStandardItem(edge['inlet'])

			self.edgesmodel.appendRow([source_item, outlet_item, target_item, inlet_item])

		### CREATE TABLE VIEWS ###
		### Nodes Table ###
		self.nodes_sheet_editor = QTableView()
		self.nodes_sheet_editor.setModel(self.nodesmodel)
		self.nodes_sheet_editor.setSelectionModel(self.nodes_selectionmodel)

		### Inlets Table ###
		self.inlets_proxy_model = NodeFilterProxyModel(node_column=1)  # Node column is 1 (for node name)
		self.inlets_proxy_model.setSourceModel(self.inletsmodel)

		self.inlets_sheet_editor = QTableView()
		self.inlets_sheet_editor.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
		self.inlets_sheet_editor.setModel(self.inlets_proxy_model)

		### Outlets Table ###
		self.outlets_proxy_model = NodeFilterProxyModel(node_column=1)  # Node column is 1 (for node name)
		self.outlets_proxy_model.setSourceModel(self.outletsmodel)

		self.outlets_sheet_editor = QTableView()
		self.outlets_sheet_editor.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
		self.outlets_sheet_editor.setModel(self.outlets_proxy_model)

		### CREATE DETAILS VIEW ###

		# create node details editor
		self.details_widget = QWidget()
		self.details_widget.setLayout(QFormLayout())

		# node data mapper
		self.name_edit = QLineEdit()
		self.script_edit = QLineEdit()
		self.details_widget.layout().addRow("Name:", self.name_edit)
		self.details_widget.layout().addRow("Script:", self.script_edit)

		self.mapper = QDataWidgetMapper()
		self.mapper.setModel(self.nodesmodel)
		self.mapper.addMapping(self.name_edit, 0)  # Map column 0 (name) to name_edit
		self.mapper.addMapping(self.script_edit, 1)  # Map column 1 (script) to script_edit
		self.mapper.setSubmitPolicy(QDataWidgetMapper.AutoSubmit)

		# selected node inlets
		self.details_widget.layout().addWidget(self.inlets_sheet_editor)
		# selected node outlets
		self.details_widget.layout().addWidget(self.outlets_sheet_editor)

		# Update mapper when the selection changes
		self.nodes_selectionmodel.selectionChanged.connect(self.update_mapper_selection)

		# add widgets to layout
		self.setCentralWidget(QWidget())
		self.centralWidget().setLayout(QHBoxLayout())
		self.centralWidget().layout().addWidget(self.nodes_sheet_editor)
		self.centralWidget().layout().addWidget(self.details_widget)



		### EDGES EDITOR ###

	def update_mapper_selection(self, selected, deselected):
		if selected.indexes():
			current_index = selected.indexes()[0]
			self.mapper.setCurrentModelIndex(current_index)  # Update the mapper's current index
			node_name = self.nodesmodel.itemFromIndex(current_index).text()  # Get the selected node's name

			# Update the filter for inlets and outlets
			self.inlets_proxy_model.setNodeName(node_name)
			self.outlets_proxy_model.setNodeName(node_name)


if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = AppEditor()
	window.show()
	sys.exit(app.exec())