import sys
from typing import Optional
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from GraphModel import GraphModel

class InletItem(QGraphicsItem):
    """Graphics item representing a pin (either inlet or outlet)."""
    def __init__(self, parent_node):
        super().__init__(parent=parent_node)
        self.parent_node = parent_node
        self.name = "<inlet name>"
        self.persistent_inlet_index:Optional[QModelIndex]=None

        # Size of the pin and space for the name text
        self.pin_radius = 5
        self.text_margin = 10

        # Font for drawing the name
        self.font = QFont("Arial", 10)

    def boundingRect(self) -> QRectF:
        """Calculate bounding rect to include both pin and name text."""
        text_width = QFontMetrics(self.font).horizontalAdvance(self.name)
        pin_diameter = self.pin_radius * 2
        height = max(pin_diameter, QFontMetrics(self.font).height())

        # Bounding rect includes the pin (left side) and text (right side)
        return QRectF(-text_width - self.text_margin - pin_diameter, -height / 2, text_width + self.text_margin + pin_diameter, height).adjusted(-2,-2,4,4)

    def paint(self, painter, option, widget=None):
        """Draw the pin and the name."""
        # get application color palette
        palette = QApplication.palette()

        # Draw pin (ellipse)
        painter.setBrush(QColor(200, 100, 100))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(-self.pin_radius, -self.pin_radius, self.pin_radius * 2, self.pin_radius * 2)

        # Draw the name
        painter.setFont(self.font)
        text_color = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText)
        painter.setPen(text_color)

        # Inlets have text on the right of the pin
        text_x = -QFontMetrics(self.font).horizontalAdvance(self.name) - self.text_margin
        painter.drawText(text_x, 5, self.name)


class OutletItem(QGraphicsItem):
    """Graphics item representing a pin (either inlet or outlet)."""
    def __init__(self, parent_node):
        super().__init__(parent=parent_node)
        self.parent_node = parent_node
        self.name = "<outlet name>"
        self.persistent_outlet_index:Optional[QModelIndex]=None

        # Size of the pin and space for the name text
        self.pin_radius = 5
        self.text_margin = 10

        # Font for drawing the name
        self.font = QFont("Arial", 10)

    def boundingRect(self) -> QRectF:
        """Calculate bounding rect to include both pin and name text."""
        text_width = QFontMetrics(self.font).horizontalAdvance(self.name)
        pin_diameter = self.pin_radius * 2
        height = max(pin_diameter, QFontMetrics(self.font).height())

        # Bounding rect includes the pin (left side) and text (right side)
        return QRectF(-text_width - self.text_margin - pin_diameter, -height / 2, text_width + self.text_margin + pin_diameter, height).adjusted(-2,-2,4,4)

    def paint(self, painter, option, widget=None):
        """Draw the pin and the name."""
        # get application color palette
        palette = QApplication.palette()

        # Draw pin (ellipse)
        painter.setBrush(QColor(200, 100, 100))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(-self.pin_radius, -self.pin_radius, self.pin_radius * 2, self.pin_radius * 2)

        # Draw the name
        painter.setFont(self.font)
        text_color = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText)
        painter.setPen(text_color)

        # Inlets have text on the right of the pin
        text_x = -QFontMetrics(self.font).horizontalAdvance(self.name) - self.text_margin
        painter.drawText(text_x, 5, self.name)


class NodeItem(QGraphicsItem):
    """Graphics item representing a node."""
    def __init__(self, parent_graph:"GraphView"):
        super().__init__(parent=None)
        self.parent_graph = parent_graph
        self.name = "<node>"
        self.script = "<script>"
        self.rect = QRectF(-50, -30, 100, 60)  # Set size of the node box
        self.persistent_node_index:Optional[QPersistentModelIndex] = None
        # Store pins (inlets and outlets)
        self.inlets = []
        self.outlets = []

        # Enable dragging and selecting
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def addInlet(self):
        inlet = InletItem(parent_node=self,)
        self.inlets.append(inlet)
        self.updatePinPositions()
        return inlet

    def addOutlet(self):
        outlet = OutletItem(parent_node=self)
        self.outlets.append(outlet)
        self.updatePinPositions()
        return outlet

    def updatePinPositions(self):
        # Position the inlets and outlets around the node's rectangle
        for i, inlet in enumerate(self.inlets):
            inlet.setPos(self.rect.left() - 10, self.rect.top() + i * 15)

        for i, outlet in enumerate(self.outlets):
            outlet.setPos(self.rect.right() + 10, self.rect.top() + i * 15)

    def boundingRect(self) -> QRectF:
        return self.rect

    def paint(self, painter, option, widget=None):
        # Draw the node rectangle
        painter.setBrush(QColor(150, 150, 250))
        painter.drawRect(self.rect)

        # Draw the node name text
        painter.setPen(Qt.white)
        painter.drawText(self.rect, Qt.AlignCenter, self.name)

    def itemChange(self, change, value):
        if self.persistent_node_index and change == QGraphicsItem.ItemPositionHasChanged:
            graph = self.parent_graph.graph_model
            node_index = graph.nodes.index(self.persistent_node_index.row(), 0)
            new_pos = self.pos()
            graph.nodes.setData(node_index.siblingAtColumn(2), str(new_pos.x()))
            graph.nodes.setData(node_index.siblingAtColumn(3), str(new_pos.y()))
        return super().itemChange(change, value)


class EdgeItem(QGraphicsLineItem):
    """Graphics item representing an edge (connection)."""
    def __init__(self, start_pin, end_pin, parent=None):
        super().__init__(parent)
        self.start_pin = start_pin
        self.end_pin = end_pin
        self.setPen(QPen(Qt.GlobalColor.white, 2))

    def updatePosition(self):
        line = QLineF(self.start_pin.scenePos(), self.end_pin.scenePos())
        self.setLine(line)


class GraphView(QGraphicsView):
    """A view that displays the node editor."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Create a scene to hold the node and edge graphics
        self.setScene(QGraphicsScene(self))
        self.nodes = []
        self.index_to_item_map = dict()

    def setModel(self, graph_model:GraphModel):
        self.graph_model = graph_model
        """Load nodes"""
        self.handleNodesInserted(QModelIndex(), 0, self.graph_model.nodes.rowCount()-1)
        self.handleInletsInserted(QModelIndex(), 0, self.graph_model.inlets.rowCount()-1)
        self.handleOutletsInserted(QModelIndex(), 0, self.graph_model.outlets.rowCount()-1)
        self.handleEdgesInserted(QModelIndex(), 0, self.graph_model.edges.rowCount()-1)
        self.graph_model.nodes.rowsInserted.connect(self.handleNodesInserted)
        self.graph_model.nodes.dataChanged.connect(self.handleNodesDataChanged)
        self.graph_model.inlets.rowsInserted.connect(self.handleInletsInserted)
        self.graph_model.inlets.dataChanged.connect(self.handleInletsDataChanged)
        self.graph_model.outlets.rowsInserted.connect(self.handleOutletsInserted)
        self.graph_model.outlets.dataChanged.connect(self.handleOutletsDataChanged)

    def addNode(self):
        node_item = NodeItem(parent_graph=self)
        self.nodes.append(node_item)
        self.scene().addItem(node_item)
        return node_item

    def handleNodesInserted(self, parent:QModelIndex, first:int, last:int):
        if parent.isValid():
            raise NotImplementedError("Subgraphs are not implemented yet!")

        for row in range(first, last+1):
            # get node and create the gaphics item
            node = self.graph_model.nodes.index(row, 0)
            node_item = self.addNode()

            # map node to graphics item
            persistent_node_index = QPersistentModelIndex(node)
            node_item.persistent_node_index = persistent_node_index
            self.index_to_item_map[persistent_node_index] = node_item

            # update gaphics item
            self.handleNodesDataChanged(node, node.siblingAtColumn(4))
            
    def handleInletsInserted(self, parent:QModelIndex, first:int, last:int):
        if parent.isValid():
            raise ValueError("inlets are flat table, not a tree model")

        for row in range(first, last+1):
            # get inlet and create the gaphics item
            inlet = self.graph_model.inlets.index(row, 0) # get the inlet reference
            inlet_node = self.graph_model.getInlet(inlet)["node"] # get the node reference
            parent_node_item = self.index_to_item_map[QPersistentModelIndex(inlet_node)] # get the node graphics item
            inlet_item = parent_node_item.addInlet()

            # map inlet to graphics item
            persistent_inlet_index = QPersistentModelIndex(inlet)
            inlet_item.persistent_inlet_index = persistent_inlet_index
            self.index_to_item_map[persistent_inlet_index] = inlet_item

            # update graphics item and add to scene
            self.handleInletsDataChanged(inlet, inlet.siblingAtColumn(2))

    def handleOutletsInserted(self, parent:QModelIndex, first:int, last:int):
        if parent.isValid():
            raise ValueError("inlets are flat table, not a tree model")

        for row in range(first, last+1):
            # get inlet and create the gaphics item
            outlet = self.graph_model.outlets.index(row, 0) # get the inlet reference
            outlet_node = self.graph_model.getInlet(outlet)["node"] # get the node reference
            parent_node_item = self.index_to_item_map[QPersistentModelIndex(outlet_node)] # get the node graphics item
            outlet_item = parent_node_item.addOutlet()

            # map inlet to graphics item
            persistent_outlet_index = QPersistentModelIndex(outlet)
            outlet_item.persistent_outlet_index = persistent_outlet_index
            self.index_to_item_map[persistent_outlet_index] = outlet_item

            # update graphics item and add to scene
            self.handleOutletsDataChanged(outlet, outlet.siblingAtColumn(2))

    def handleEdgesInserted(self, parent:QModelIndex, first:int, last:int):
        pass

    def handleNodesDataChanged(self, topLeft:QModelIndex, bottomRight:QModelIndex, roles=[]):
        for row in range(topLeft.row(), bottomRight.row()+1):
            node_index = self.graph_model.nodes.index(row, 0)
            persistent_node_index = QPersistentModelIndex(node_index)
            node_item = self.index_to_item_map[persistent_node_index]
            for col in range(topLeft.column(), bottomRight.column()+1):
                match col:
                    case 0:
                        pass
                    case 1:
                        node_item.name = str(node_index.siblingAtColumn(1).data())
                        node_item.update()
                    case 2:
                        node_item.setX(float(node_index.siblingAtColumn(2).data()))
                    case 3:
                        node_item.setY(float(node_index.siblingAtColumn(3).data()))
                    case 4:
                        "set script"

    def handleInletsDataChanged(self, topLeft:QModelIndex, bottomRight:QModelIndex, roles=[]):
        for row in range(topLeft.row(), bottomRight.row()+1):
            inlet = self.graph_model.inlets.index(row, 0)
            persistent_index = QPersistentModelIndex(inlet)
            graphics_item = self.index_to_item_map[persistent_index]
            for col in range(topLeft.column(), bottomRight.column()+1):
                match col:
                    case 0:
                        """unique id changed"""
                        pass
                    case 1:
                        pass
                    case 2:
                        """name changed"""
                        graphics_item.name = str(inlet.siblingAtColumn(2).data())
                        graphics_item.update()

    def handleOutletsDataChanged(self, topLeft:QModelIndex, bottomRight:QModelIndex, roles=[]):
        for row in range(topLeft.row(), bottomRight.row()+1):
            outlet = self.graph_model.outlets.index(row, 0)
            persistent_index = QPersistentModelIndex(outlet)
            graphics_item = self.index_to_item_map[persistent_index]
            for col in range(topLeft.column(), bottomRight.column()+1):
                match col:
                    case 0:
                        """unique id changed"""
                        # raise NotImplementedError("Setting the inlet's unique id is not supported!")
                        pass
                    case 1:
                        """parent node changed"""
                        # raise NotImplementedError("Setting the inlet's parent node is not supported!")
                        pass
                    case 2:
                        """name changed"""
                        graphics_item.name = str(outlet.siblingAtColumn(2).data())
                        graphics_item.update()

    def handleEdgesDataChanged(self, topLeft:QModelIndex, bottomRight:QModelIndex, roles=[]):
        pass

from GraphTableView import GraphTableView
from GraphDetailsView import GraphDetailsView
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Graph Viewer Example")
        self.resize(1500, 700)

        # Initialize the GraphModel
        self.graph_model = GraphModel()
        self.nodes_selectionmodel = QItemSelectionModel(self.graph_model.nodes)

        # Add some example nodes and edges
        node1_id = self.graph_model.addNode("Node 1", 100, 100, "Script 1")
        node2_id = self.graph_model.addNode("Node 2", 300, 150, "Script 2")
        outlet_id = self.graph_model.addOutlet(node1_id, "Out1")
        inlet_id = self.graph_model.addInlet(node2_id, "In1")
        self.graph_model.addEdge(outlet_id, inlet_id)

        # Set up the node editor view
        self.graph_table_view = GraphTableView()
        self.graph_table_view.setModel(self.graph_model)
        self.graph_table_view.setNodesSelectionModel(self.nodes_selectionmodel)
        self.graph_view = GraphView()
        self.graph_view.setModel(self.graph_model)
        # self.graph_view.setNodesSelectionModel(self.nodes_selectionmodel)
        self.graph_details_view = GraphDetailsView()
        self.graph_details_view.setModel(self.graph_model)
        self.graph_details_view.setNodesSelectionModel(self.nodes_selectionmodel)
        
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.graph_table_view, 1)
        self.layout().addWidget(self.graph_view, 1)
        self.layout().addWidget(self.graph_details_view, 1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
