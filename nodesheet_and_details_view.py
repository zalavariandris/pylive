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
        self.nodes.setHorizontalHeaderLabels(['name', 'posx', 'posy', 'script'])

        ### Inlets Model ###
        self.inlets = QStandardItemModel()
        self.inlets.setHorizontalHeaderLabels(['name', "node"])

        ### Outlets Model ###
        self.outlets = QStandardItemModel()
        self.outlets.setHorizontalHeaderLabels(['name', "node"])

        ### Edges Model ###
        self.edges = QStandardItemModel()
        self.edges.setHorizontalHeaderLabels(['source', "outlet", "target", "inlet"])

    def addNode(self, name, posx, posy, script):
        name_item =   QStandardItem(name)
        posx_item =   QStandardItem(posx)
        posy_item = QStandardItem(posy)
        script_item = QStandardItem(script)
        self.nodes.appendRow([name_item, posx_item, posy_item, script_item])

    def addInlet(self, name, node):
        name_item =   QStandardItem(name)
        node_item =   QStandardItem(node)
        self.inlets.appendRow([name_item, node_item])

    def addOutlet(self, name, node):
        name_item =   QStandardItem(name)
        node_item =   QStandardItem(node)
        self.outlets.appendRow([name_item, node_item])

    def addEdge(self, source, outlet, target, inlet):
        source_item =   QStandardItem(source)
        outlet_item =   QStandardItem(outlet)
        target_item =   QStandardItem(target)
        inlet_item =    QStandardItem(inlet)
        self.edges.appendRow([source_item, outlet_item, target_item, inlet_item])


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


class NodeDetailsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._model = None

        policy = QSizePolicy.Minimum

        # create node details editor


        # node data editors
        self.name_edit = QLineEdit()
        self.script_edit = QPlainTextEdit()
        self.posx_edit = QSpinBox()
        self.posy_edit = QSpinBox()

        ### Inlets Table ###
        self.inlets_sheet_editor = MiniTableView()

        
        ### Outlets Table ###
        self.outlets_sheet_editor = MiniTableView()

        # self.setLayout(QFormLayout())
        # self.layout().setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        # self.layout().addRow("Name:", self.name_edit)
        # self.layout().addRow("Pos X:", self.posx_edit)
        # self.layout().addRow("Pos Y:", self.posy_edit)
        # self.layout().addRow("Script:", self.script_edit)
        # self.layout().addRow("Inlets:", self.inlets_sheet_editor)
        # self.layout().addRow("Inlets:", self.outlets_sheet_editor)

        self.setLayout(QVBoxLayout())
        # self.layout().setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        self.layout().addWidget(self.name_edit)
        self.layout().addWidget(self.posx_edit)
        self.layout().addWidget(self.posy_edit)
        self.layout().addWidget(self.script_edit)
        self.layout().addWidget(self.inlets_sheet_editor)
        self.layout().addWidget(self.outlets_sheet_editor)


    def model(self):
        return self._model

    def setModel(self, graphmodel):
        self._model = graphmodel

        # mapper
        self.mapper = QDataWidgetMapper()
        self.mapper.setModel(graphmodel.nodes)

        self.mapper.addMapping(self.name_edit, 0)
        self.mapper.addMapping(self.posx_edit, 1)
        self.mapper.addMapping(self.posy_edit, 2)
        self.mapper.addMapping(self.script_edit, 3)

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

        # set no rows
        self.setCurrentModelIndex(QModelIndex())
        
    def setCurrentModelIndex(self, index):
        if index.isValid():
            self.mapper.setCurrentModelIndex(index)  # Update the mapper's current index
            node_name = self._model.nodes.itemFromIndex(index).text()  # Get the selected node's name
            self.selected_node_inlets.setFilterFixedString(node_name) # update inlet filters
            self.selected_node_outlets.setFilterFixedString(node_name) # update outlet filters
        else:
            # update name and script
            self.name_edit.setText("")
            self.script_edit.setPlainText("")

            self.selected_node_inlets.setFilterFixedString("SOMETHING CMPLICATED ENOUGHT NOT TO MATC ANY NODE NAMES") # update inlet filters
            self.selected_node_outlets.setFilterFixedString("SOMETHING CMPLICATED ENOUGHT NOT TO MATC ANY NODE NAMES") # update outlet filters


from NodeGraphQt import NodeGraph, BaseNode
class GraphView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.graph = NodeGraph()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.graph.widget)

    def setModel(self, model):
        self._model = model

        # setup nodes
        node_by_name = {}
        for row in range(model.nodes.rowCount()):
            # get data from node table model
            name =   model.nodes.item(row, 0).text()
            posx =   model.nodes.item(row, 1).text()
            posy =   model.nodes.item(row, 2).text()
            script = model.nodes.item(row, 3).text()
            
            # add node to nodegraph
            node = BaseNode()
            self.graph.add_node(node)
            node.set_name(name)
            node.set_x_pos(float(posx))
            node.set_y_pos(float(posy))
            node_by_name[name]=node

        # setup inlets
        inlet_by_name = {}
        for row in range(model.inlets.rowCount()):
            name = model.inlets.item(row, 0).text()
            owner = model.inlets.item(row, 1).text()

            node = node_by_name[owner]
            inlet = node.add_input(name)
            inlet_by_name[(name, owner)] = inlet

        # setup outlets
        outlet_by_name = {}
        for row in range(model.outlets.rowCount()):
            name = model.outlets.item(row, 0).text()
            owner = model.outlets.item(row, 1).text()

            node = node_by_name[owner]
            outlet = node.add_output(name)
            outlet_by_name[(name, owner)] = outlet

        # setup edges
        for row in range(model.edges.rowCount()):
            source = model.edges.item(row, 0).text()
            outlet = model.edges.item(row, 1).text()
            target = model.edges.item(row, 2).text()
            inlet =  model.edges.item(row, 3).text()

            # connect ports
            source_port = outlet_by_name[(outlet, source)]
            target_port = inlet_by_name[(inlet, target)]
            source_port.connect_to(target_port)


    def setSelectionModel(self, selectionmodel):
        self._selection_model = selectionmodel



class AppEditor(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GraphEditor")
        self.resize(1600, 500)

        self.graphmodel = GraphModel()
        self.nodes_selectionmodel = QItemSelectionModel(self.graphmodel.nodes)
        for node in [
            {"name": "ticknode",    "posx": "0", "posy": "0"}, 
            {"name": "previewnode", "posx": "260", "posy": "0"}
        ]:
            self.graphmodel.addNode(
                node["name"],
                node["posx"],
                node["posy"],
                f"#{node['name']}")

        for inlet in [{"name": "display", "node": "previewnode"}]:
            self.graphmodel.addInlet(inlet["name"], inlet["node"])

        for outlet in [{"name": "out", "node": "ticknode"}]:
            self.graphmodel.addOutlet(outlet["name"], outlet["node"])

        for edge in [{"source":"ticknode", "outlet": "out", "target": "previewnode", "inlet":"display"}]:
            self.graphmodel.addEdge(edge["source"], edge["outlet"], edge["target"], edge["inlet"])

        ### CREATE TABLE VIEWS ###
        ### Nodes Table ###
        self.nodes_sheet_view = QTableView()
        self.nodes_sheet_view.setSelectionBehavior(QTableView.SelectRows)
        self.nodes_sheet_view.setModel(self.graphmodel.nodes)
        self.nodes_sheet_view.setSelectionModel(self.nodes_selectionmodel)

        ### Edges Table ###
        self.edges_sheet_view = QTableView()
        self.edges_sheet_view.setSelectionBehavior(QTableView.SelectRows)
        self.edges_sheet_view.setModel(self.graphmodel.edges)

        ### CREATE GRAPH VIEW ###
        self.graphview = GraphView()
        self.graphview.setModel(self.graphmodel)
        self.graphview.setSelectionModel(self.nodes_selectionmodel)

        ### CREATE DETAILS VIEW ###
        self.details_view = NodeDetailsView()
        self.details_view.setModel(self.graphmodel)

        self.nodes_selectionmodel.selectionChanged.connect(lambda selected, deselected: # Update details view when the selection changes 
            self.details_view.setCurrentModelIndex(
                selected.indexes()[0] if selected.indexes() else QModelIndex()
            )
        )

        # add widgets to layout
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(QHBoxLayout())
        sheets_widget = QTabWidget()
        sheets_widget.addTab(self.nodes_sheet_view, "nodes")
        sheets_widget.addTab(self.edges_sheet_view, "edges")

        self.centralWidget().layout().addWidget(sheets_widget)
        self.centralWidget().layout().addWidget(self.graphview)
        self.centralWidget().layout().addWidget(self.details_view)




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppEditor()
    window.show()
    sys.exit(app.exec())