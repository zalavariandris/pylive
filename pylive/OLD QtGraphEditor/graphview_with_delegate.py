from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


from nx_graph_model import NXGraphModel

from link_graphics_items import makeLineBetweenShapes
from qgraphics_arrow_item import QGraphicsArrowItem


class StandardNodeWidget(QGraphicsWidget):
	def __init__(self, parent: Optional[QGraphicsItem]=None) -> None:
		QGraphicsWidget.__init__(self, parent=parent)
		self.setGeometry(0,0,50,50)	
		
	def paint(self, painter, option:QStyleOptionGraphicsItem, widget=None):
		palette = self.palette()

		pen = QPen(palette.color(QPalette.ColorRole.Text), 1)
		painter.setPen(pen)
		rect = QRectF(0,0, self.geometry().width(), self.geometry().height())
		# painter.drawEllipse(rect)

		painter.drawRoundedRect(rect, 10, 10)

		if QStyle.StateFlag.State_Selected in option.state:
			pen = QPen(palette.color(QPalette.ColorRole.WindowText), 1, Qt.PenStyle.DashLine)
			painter.setPen(pen)
			painter.drawRoundedRect(rect, 1, 1)


class StandardLinkWidget(QGraphicsArrowItem):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		pen = QPen(QColor("white"), 2)
		self.setPen(pen)


class StandardGraphDelegate(AbstractGraphDelegate):
	def createNodeWidget(self, graph:'NXGraphModel', n:Hashable)->QGraphicsWidget:
		"""create and bind the widget"""
		widget = StandardNodeWidget()
		# widget.setAutoFillBackground(True)
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

	def createEdgeWidget(self, graph:'NXGraphModel', source:QGraphicsWidget, target:QGraphicsWidget)->QGraphicsArrowItem:
		link = StandardLinkWidget()


		def update_link():
			link.setLine( makeLineBetweenShapes(source.geometry(), target.geometry() ) )
		update_link()

		source.geometryChanged.connect(update_link)
		target.geometryChanged.connect(update_link)

		return link

	def setEdgeWidgetProps(self, graph:'NXGraphModel', e:Tuple[Hashable, Hashable], widget:QGraphicsArrowItem, **props):
		...

	def setEdgeModelProps(self, graph:'NXGraphModel', e:Tuple[Hashable, Hashable], widget:QGraphicsArrowItem, **props):
		...


from pylive.utils.unique import make_unique_id
class NXGraphView(QGraphicsView):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setRenderHints(QPainter.Antialiasing)
		self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
		scene = QGraphicsScene()
		scene.setSceneRect(QRect(-9999//2,-9999//2, 9999, 9999))
		self.setScene(scene)
		
		self._item_to_widget_map = dict()
		self._widget_to_item_map = dict()
		self._delegate = StandardGraphDelegate()
		self.setGraphModel( NXGraphModel() )

	def nodeWidget(self, n:Hashable):
		return self._item_to_widget_map[n]
		
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
	view = NXGraphView()


	graph = view.graphModel()
	graph.addEdge("A", "B")
	view.nodeWidget("A").setPos(-75,-10)
	view.nodeWidget("B").setPos(75, 10)

	# add a simple item to the same scene
	ellipse = QGraphicsEllipseItem(0,0,50,50)
	ellipse.setFlag(QGraphicsItem.ItemIsSelectable, True)
	view.scene().addItem(ellipse)

	view.show()
	app.exec()

