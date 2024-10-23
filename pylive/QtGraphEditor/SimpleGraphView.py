import sys
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from GraphModel import GraphModel

class NodeItem(QGraphicsItem):
    """Graphics item representing a node."""
    def __init__(self, persistent_node_index, graph_model:GraphModel, parent=None):
        super().__init__(parent)
        self.persistent_node_index = persistent_node_index
        self.name = "<node>"
        self.script = "<script>"
        self.graph_model = graph_model
        self.rect = QRectF(-50, -30, 100, 60)  # Set size of the node box

        # Store pins (inlets and outlets)
        self.inlets = []
        self.outlets = []

        # Enable dragging and selecting
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def addInlet(self, name):
        inlet = PinItem(self, 'inlet', name, self)
        self.inlets.append(inlet)
        self.updatePinPositions()

    def addOutlet(self, name):
        outlet = PinItem(self, 'outlet', name, self)
        self.outlets.append(outlet)
        self.updatePinPositions()

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
        if change == QGraphicsItem.ItemPositionHasChanged:   
            node_index = self.graph_model.nodes.index(self.persistent_node_index.row(), 0)
            new_pos = self.pos()
            self.graph_model.nodes.setData(node_index.siblingAtColumn(2), str(new_pos.x()))
            self.graph_model.nodes.setData(node_index.siblingAtColumn(3), str(new_pos.y()))
        return super().itemChange(change, value)


class PinItem(QGraphicsItem):
    """Graphics item representing a pin (either inlet or outlet)."""
    def __init__(self, owner_node, pin_type, name, parent=None):
        super().__init__(parent)
        self.owner_node = owner_node
        self.pin_type = pin_type  # 'inlet' or 'outlet'
        self.name = name

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

        if self.pin_type == 'inlet':
            # Bounding rect includes the pin (left side) and text (right side)
            return QRectF(-text_width - self.text_margin - pin_diameter, -height / 2, text_width + self.text_margin + pin_diameter, height)
        else:
            # Bounding rect includes the pin (right side) and text (left side)
            return QRectF(-pin_diameter, -height / 2, text_width + self.text_margin + pin_diameter, height)

    def paint(self, painter, option, widget=None):
        """Draw the pin and the name."""
        # Draw pin (ellipse)
        painter.setBrush(QColor(200, 100, 100) if self.pin_type == 'inlet' else QColor(100, 200, 100))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(-self.pin_radius, -self.pin_radius, self.pin_radius * 2, self.pin_radius * 2)

        # Draw the name
        painter.setFont(self.font)
        painter.setPen(Qt.white)

        if self.pin_type == 'inlet':
            # Inlets have text on the right of the pin
            text_x = -QFontMetrics(self.font).horizontalAdvance(self.name) - self.text_margin
            painter.drawText(text_x, 5, self.name)
        else:
            # Outlets have text on the left of the pin
            text_x = self.pin_radius + self.text_margin
            painter.drawText(text_x, 5, self.name)



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
        self.index_to_item_map = dict()

    def setModel(self, graph_model:GraphModel):
        self.graph_model = graph_model
        """Load nodes"""
        self.handleNodesInserted(QModelIndex(), 0, self.graph_model.nodes.rowCount()-1)
        self.handleInletsInserted(QModelIndex(), 0, self.graph_model.inlets.rowCount()-1)
        self.graph_model.nodes.rowsInserted.connect(self.handleNodesInserted)
        self.graph_model.nodes.dataChanged.connect(self.handleNodeDataChanged)
        self.graph_model.inlets.rowsInserted.connect(self.handleInletsInserted)

    def handleNodesInserted(self, parent:QModelIndex, first:int, last:int):
        if parent.isValid():
            raise NotImplementedError("Subgraphs are not implemented yet!")

        for row in range(first, last+1):        
            node_index = self.graph_model.nodes.index(row, 0)
            persistent_node_index = QPersistentModelIndex(node_index)
            node_item = NodeItem(persistent_node_index=persistent_node_index, 
                                 graph_model=self.graph_model)

            self.index_to_item_map[persistent_node_index] = node_item
            self.handleNodeDataChanged(node_index, node_index.siblingAtColumn(4))
            self.scene().addItem(node_item)

    def handleNodeDataChanged(self, topLeft:QModelIndex, bottomRight:QModelIndex, roles=[]):
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

    def handleInletsInserted(self, parent:QModelIndex, first:int, last:int):
        if parent.isValid():
            raise ValueError("inlets are flat table, not a tree model")

        # for row in range(first, last+1):        
        #     inlet_index = self.graph_model.nodes.index(row, 0)
        #     persistent_inlet_index = QPersistentModelIndex(inlet_index)
        #     self.graph_model.nodes.findItems()
        #     inlet_item = PinItem(
        #     inlet_item = NodeItem(persistent_node_index=persistent_inlet_index, 
        #                          graph_model=self.graph_model)

        #     self.index_to_item_map[persistent_inlet_index] = inlet_item
        #     self.handleInletDataChanged(inlet_index, inlet_index.siblingAtColumn(3))
        #     self.scene().addItem(inlet_item)

    def handleInletDataChanged(self, topLeft:QModelIndex, bottomRight:QModelIndex, roles=[]):
        for row in range(topLeft.row(), bottomRight.row()+1):
            inlet_index = self.graph_model.nodes.index(row, 0)
            persistent_inlet_index = QPersistentModelIndex(inlet_index)
            inlet_item = self.index_to_item_map[persistent_inlet_index]
            for col in range(topLeft.column(), bottomRight.column()+1):
                match col:
                    case 0:
                        "unique id changed"
                    case 1:
                        "owner node changed"
                    case 2:
                        "name changed"
                        inlet_item.name = str(inlet_index.siblingAtColumn(2).data())
                        inlet_item.update()

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
