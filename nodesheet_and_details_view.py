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


class GraphModel(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        ### CREATE QT MODELS ###

        ### Nodes Model ###
        self.nodes = QStandardItemModel()
        self.nodes.setHorizontalHeaderLabels(['name', 'script'])

        ### Inlets Model ###
        self.inlets = QStandardItemModel()
        self.inlets.setHorizontalHeaderLabels(['name', "node"])

        ### Outlets Model ###
        self.outlets = QStandardItemModel()
        self.outlets.setHorizontalHeaderLabels(['name', "node"])

        ### Edges Model ###
        self.edges = QStandardItemModel()
        self.edges.setHorizontalHeaderLabels(['source', "outlet", "target", "inlet"])

    def addNode(self, name, script):
        name_item =   QStandardItem(name)
        script_item = QStandardItem(script)
        self.nodes.appendRow([name_item, script_item])

    def addInlet(self, name, node):
        name_item =   QStandardItem(name)
        node_item =   QStandardItem(node)
        self.inlets.appendRow([name_item, node_item])

    def addOutlet(self, name, node):
        name_item =   QStandardItem(name)
        node_item =   QStandardItem(node)
        self.outlets.appendRow([name_item, node_item])

    def addEdge(self, source, outlet, target, inlet):
        source_item =   QStandardItem('source')
        outlet_item =   QStandardItem('outlet')
        target_item =   QStandardItem('target')
        inlet_item =    QStandardItem('inlet')
        self.edges.appendRow([source_item, outlet_item, target_item, inlet_item])

    # def update_selection(self, selected, deselected):
    #   if selected.indexes():
    #       current_index = selected.indexes()[0]
    #       node_name = self.nodes.itemFromIndex(current_index).text()  # Get the selected node's name

    #       # Update the filter for inlets and outlets
    #       self.inlets_proxy_model.setNodeName(node_name)
    #       self.outlets_proxy_model.setNodeName(node_name)


class NodeDetailsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._model = None

        policy = QSizePolicy.Fixed

        # create node details editor


        # node data editors
        self.name_edit = QLineEdit()
        self.script_edit = QLineEdit()

        ### Inlets Table ###
        self.inlets_sheet_editor = QTableView()
        self.inlets_sheet_editor.setSelectionBehavior(QTableView.SelectRows)
        self.inlets_sheet_editor.resize(QSize(50, 50))
        self.inlets_sheet_editor.setMinimumSize(QSize(50, 50))
        self.inlets_sheet_editor.setSizePolicy(policy, policy)
        
        ### Outlets Table ###
        self.outlets_sheet_editor = QTableView()
        self.outlets_sheet_editor.setSelectionBehavior(QTableView.SelectRows)
        self.outlets_sheet_editor.resize(QSize(50, 50))
        self.outlets_sheet_editor.setMinimumSize(QSize(50, 50))
        self.outlets_sheet_editor.setSizePolicy(policy, policy)

        # layout widgets
        # self.setLayout(QVBoxLayout())
        # self.layout().addWidget(self.name_edit)
        # self.layout().addWidget(self.script_edit)
        # self.layout().addWidget(self.inlets_sheet_editor)
        # self.layout().addWidget(self.outlets_sheet_editor)
        # self.layout().addStretch()

        self.setLayout(QFormLayout())
        self.layout().setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        self.layout().addRow("Name:", self.name_edit)
        self.layout().addRow("Script:", self.script_edit)
        self.layout().addRow("Inlets:", self.inlets_sheet_editor)
        self.layout().addRow("Inlets:", self.outlets_sheet_editor)


        
    def model(self):
        return self._model

    def setModel(self, graphmodel):
        self._model = graphmodel

        # mapper
        self.mapper = QDataWidgetMapper()
        self.mapper.setModel(graphmodel.nodes)
        self.mapper.addMapping(self.name_edit, 0)  # Map column 0 (name) to name_edit
        self.mapper.addMapping(self.script_edit, 1)  # Map column 1 (script) to script_edit
        self.mapper.setSubmitPolicy(QDataWidgetMapper.AutoSubmit)

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
        
    def setCurrentModelIndex(self, index):
        if index.isValid():
            self.mapper.setCurrentModelIndex(index)  # Update the mapper's current index
            node_name = self._model.nodes.itemFromIndex(index).text()  # Get the selected node's name
            self.selected_node_inlets.setFilterFixedString(node_name) # update inlet filters
            self.selected_node_outlets.setFilterFixedString(node_name) # update outlet filters
        else:
            # update name and script
            self.name_edit.setText("")
            self.script_edit.setText("")


        # else:

        #     self.selected_node_inlets.setFilterFixedString("")
        #     self.selected_node_outlets.setFilterFixedString("")

class AppEditor(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.graphmodel = GraphModel()
        self.nodes_selectionmodel = QItemSelectionModel(self.graphmodel.nodes)
        for node in [{"name": "ticknode"}, {"name": "previewnode"}]:
            self.graphmodel.addNode(node["name"], f"#{node['name']}")

        for inlet in [{"name": "input", "node": "previewnode"}]:
            self.graphmodel.addInlet(inlet["name"], inlet["node"])

        for outlet in [{"name": "output", "node": "ticknode"}]:
            self.graphmodel.addOutlet(outlet["name"], outlet["node"])

        for edge in [{"source":"ticknode", "outlet": "out", "target": "previewnode", "inlet":"display"}]:
            self.graphmodel.addEdge(edge["source"], edge["outlet"], edge["target"], edge["inlet"])

        ### CREATE TABLE VIEWS ###
        ### Nodes Table ###
        self.nodes_sheet_editor = QTableView()
        self.nodes_sheet_editor.setSelectionBehavior(QTableView.SelectRows)
        self.nodes_sheet_editor.setModel(self.graphmodel.nodes)
        self.nodes_sheet_editor.setSelectionModel(self.nodes_selectionmodel)


        ### CREATE DETAILS VIEW ###

        self.details_widget = NodeDetailsView()
        self.details_widget.setModel(self.graphmodel)

        # # selected node inlets
        # self.details_widget.layout().addWidget(self.inlets_sheet_editor)
        # # selected node outlets
        # self.details_widget.layout().addWidget(self.outlets_sheet_editor)

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
            current_node_index = selected.indexes()[0]

            # update mapper
            self.details_widget.setCurrentModelIndex(current_node_index)  # Update the mapper's current index
        else:
            self.details_widget.setCurrentModelIndex(QModelIndex())  # Update the mapper's current index

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppEditor()
    window.show()
    sys.exit(app.exec())