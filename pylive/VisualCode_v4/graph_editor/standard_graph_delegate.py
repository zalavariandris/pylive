from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.VisualCode_NetworkX.UI.nx_graph_shapes import RoundedLinkShape


from pylive.VisualCode_v4.graph_editor.standard_node_widget import StandardNodeWidget
from pylive.VisualCode_v4.graph_editor.standard_port_widget import StandardPortWidget



class StandardGraphDelegate(QObject):
    """Any QGraphicsItem can be used as a node or an edge graphics
    the delegate must emit a nodePositionchanged Signal, when a node position changed
    updateLinkPosition will be called when a linked node position changed"""

    ### NODE DELEGATE
    nodePositionChanged = Signal(QGraphicsItem)
    def createNodeWidget(self, parent:QGraphicsScene, index:QModelIndex)->QGraphicsItem:
        node_widget = StandardNodeWidget()
        node_widget.setHeading(f"{index.data(Qt.ItemDataRole.DisplayRole)}")
        node_widget.scenePositionChanged.connect(lambda node=node_widget: self.nodePositionChanged.emit(node))
        parent.addItem(node_widget)
        return node_widget

    def createInletWidget(self, parent:QGraphicsItem, node_index:QModelIndex, inlet:object)->QGraphicsItem:
        port_editor = StandardPortWidget(f"{inlet}", parent)
        parent = cast(StandardNodeWidget, parent)
        parent.insertInlet(0, port_editor)
        # item.pressed.connect(lambda name=name: self.inletPressed.emit(name))
        return port_editor

    def createOutletWidget(self, parent:QGraphicsItem, node_index:QModelIndex, outlet:object)->QGraphicsItem:
        port_editor = StandardPortWidget(f"{outlet}", parent)
        port_editor._nameitem.setPos(-24,0)
        parent = cast(StandardNodeWidget, parent)
        parent.insertOutlet(0, port_editor)

        # def on_press(node_index=node_index, port_editor=port_editor):
        #     scene = cast('QGraphEditorScene', port_editor.scene())
        #     scene.startDragOutlet(node_index.row())
            
        # port_editor.pressed.connect(on_press)
        return port_editor

    def updateNodeWidget(self, index:QModelIndex, node_widget:QGraphicsItem)->None:
        node_widget = cast(StandardNodeWidget, node_widget)
        node_widget.setHeading( index.data(Qt.ItemDataRole.DisplayRole) )

    ### EDGE DELEGATE
    def createEdgeWidget(self, edge_idx:QModelIndex)->QGraphicsItem:
        label = edge_idx.data(Qt.ItemDataRole.DisplayRole)
        link = RoundedLinkShape(label if label else "", orientation=Qt.Orientation.Vertical)
        link.setZValue(-1)
        return link

    def updateEdgeWidget(self, edge_idx:QModelIndex, editor:QGraphicsItem)->None:
        ...

    def updateEdgePosition(self, 
        edge_editor: QGraphicsItem, 
        source:QGraphicsItem|QPointF, 
        target:QGraphicsItem|QPointF
    ):
        edge_widget = cast(RoundedLinkShape, edge_editor)
        edge_widget.move(source, target)


