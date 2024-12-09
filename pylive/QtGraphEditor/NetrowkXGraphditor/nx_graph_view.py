from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from standard_graph_delegate import AbstractGraphDelegate
from nx_graph_model import NXGraphModel

from link_graphics_items import makeLineBetweenShapes

class BoundingRectEffect(QGraphicsEffect):
    def __init__(self, parent=None):
        super().__init__(parent)

    def draw(self, painter):
        # Draw the base item (widget)
        self.drawSource(painter)
        
        # Access the item and check if it's selected
        # item = self.sourceItem()
        # if item and item.isSelected():
        #     # Get the bounding rect of the item
        rect = self.boundingRect()
        
        # Customize the selection rectangle
        pen = QPen(QColor(255, 0, 0), 3)  # Red pen with 3px width
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        painter.drawRect(rect)

class StandardGraphDelegate(AbstractGraphDelegate):
	def createNodeWidget(self, graph:'NXGraphModel', n:Hashable)->QGraphicsWidget:
		"""create and bind the widget"""
		widget = QGraphicsWidget()
		widget.setAutoFillBackground(True)
		palette = widget.palette()
		palette.setColor(QPalette.Window, Qt.darkGray)
		widget.setPalette(palette)
		widget.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
		widget.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
		widget.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)

		return widget

	def setNodeWidgetProps(self, graph:'NXGraphModel', n:Hashable, widget:QGraphicsWidget, **props):
		...
		"""update iwdget props from model"""
		# if 'label' in props.keys():
		# 	widget.label.document().setPlainText(props['label'])
		
		# if 'inlets' in props.keys():
		# 	...

		# if 'outlets' in props.keys():
		# 	...

	def setNodeModelProps(self, graph:'NXGraphModel', n:Hashable, widget:QGraphicsWidget, **props):
		"""update model props from widget"""
		graph.setNodeProperties(n, **props)

	def createEdgeWidget(self, graph:'NXGraphModel', source:QGraphicsWidget, target:QGraphicsWidget)->QGraphicsLineItem:
		link = QGraphicsLineItem()
		pen = QPen(QColor("white"), 2)
		link.setPen(pen)

		def update_link():
			link.setLine( makeLineBetweenShapes(source.geometry(), target.geometry() ) )
		update_link()

		source.geometryChanged.connect(update_link)
		target.geometryChanged.connect(update_link)

		return link

	def setEdgeWidgetProps(self, graph:'NXGraphModel', e:Tuple[Hashable, Hashable], widget:QGraphicsLineItem, **props):
		...

	def setEdgeModelProps(self, graph:'NXGraphModel', e:Tuple[Hashable, Hashable], widget:QGraphicsLineItem, **props):
		...


from pylive.utils.unique import make_unique_id
class NXGraphView(QGraphicsView):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
		scene = QGraphicsScene()
		scene.setSceneRect(QRect(-9999//2,-9999//2, 9999, 9999))
		self.setScene(scene)


		self.ellipse = QGraphicsEllipseItem(50,50,50,50)
		self.ellipse.setFlag(QGraphicsItem.ItemIsSelectable, True)
		scene.addItem(self.ellipse)
		
		self._item_to_widget_map = dict()
		self._widget_to_item_map = dict()
		self._delegate = StandardGraphDelegate()
		self.setGraphModel( NXGraphModel() )
		
	def delegate(self):
		return self._delegate

	def graphModel(self):
		return self._graphmodel

	def setGraphModel(self, graphmodel:NXGraphModel):
		self._graphmodel = graphmodel

		self._graphmodel.nodesAdded.connect(self.handleNodesAdded)
		self._graphmodel.nodesPropertiesChanged.connect(self.handleNodesPropertiesChanged)
		self._graphmodel.edgesAdded.connect(self.handleEdgesAdded)
	
	def handleNodesAdded(self, nodes:List[Hashable]):
		for n in nodes:
			widget = self.delegate().createNodeWidget(self.graphModel(), n)
			self._item_to_widget_map[n]=widget
			self._widget_to_item_map[widget]=n
			self.scene().addItem(widget)

	def handleNodesRemoved(self, nodes:List[Hashable]):
		for n in nodes:
			widget = self._item_to_widget_map[n]
			self.scene().removeItem(widget)
			del self._item_to_widget_map[n]
			del self._widget_to_item_map[widget]

	def handleEdgesAdded(self, edges:List[Tuple[Hashable, Hashable]]):
		for u, v in edges:
			source_node = self._item_to_widget_map[u]
			target_node = self._item_to_widget_map[v]
			print(source_node, target_node)
			widget = self.delegate().createEdgeWidget(self, source_node, target_node)
			# widget.setSource(source_node)
			# widget.setTarget(target_node)
			self._item_to_widget_map[(u,v)]=widget
			self._widget_to_item_map[widget]=(u,v)
			self.scene().addItem(widget)

	def handleEdgesRemoed(self, edges:List[Tuple[Hashable, Hashable]]):
		for u,v in edges:
			widget = self._item_to_widget_map[(u,v)]
			widget.setSource(None)
			widget.setTarget(None)
			self.scene().removeItem(widget)
			del self._item_to_widget_map[(u, v)]
			del self._widget_to_item_map[widget]

	def handleNodesPropertiesChanged(self, nodesProperies):
		for n, properties in nodesProperies.items():
			widget = self._item_to_widget_map[n]
			self.delegate().setNodeWidgetProps(self, n, widget, **properties)

	def handleEdgesPropertiesChanged(self, edgesProperties):
		for edge, properties in edgesProperties.items():
			widget = self._item_to_widget_map[edge]
			self.delegate().setEdgeWidgetProps(self, edge, widget, **properties)

	def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
		print("doubleclick")
		itemAtMouse = self.itemAt(event.position().toPoint())
		print("itemAtMouse", itemAtMouse)
		if itemAtMouse:
			return super().mouseDoubleClickEvent(event)

		clickpos = self.mapToScene(event.position().toPoint())
		
		n = make_unique_id()
		self.graphModel().addNode(n, label="new node")
		widget = self._item_to_widget_map[n]
		widget.setPos(clickpos)

	def contextMenuEvent(self, event:QContextMenuEvent):
		def create_node_at(scenePos:QPointF):
			n = make_unique_id()
			self.graphModel().addNode(n, label="new node")
			widget = self._item_to_widget_map[n]
			widget.setPos(scenePos)

		def connect_selected_nodes():
			selection = [item for item in self.scene().selectedItems()]
			print("connect_selected_nodes:", selection)
			if len(selection) < 2:
				return

			for item in selection[1:]:
				u = self._widget_to_item_map[selection[0]]
				v = self._widget_to_item_map[item]
				self.graphModel().addEdge(u, v)

		menu = QMenu(self)

		create_action = QAction(self)
		create_action.setText("create node")
		
		create_action.triggered.connect(lambda: create_node_at( self.mapToScene(self.mapFromGlobal(event.globalPos()) )))
		menu.addAction(create_action)

		connect_action = QAction(self)
		connect_action.setText("connect")

		connect_action.triggered.connect(lambda: connect_selected_nodes())
		menu.addAction(connect_action)

		menu.exec(event.globalPos())



if __name__ == "__main__":
	app = QApplication.instance() or QApplication()
	window = NXGraphView()
	# window.scene().addItem( QGraphicsRectItem(QRect(0,0,100,100)) )
	graph = window.graphModel()
	# graph.addNode("A")
	# graph.addNode("B")
	graph.addEdge("A", "B")

	window.show()
	app.exec()

