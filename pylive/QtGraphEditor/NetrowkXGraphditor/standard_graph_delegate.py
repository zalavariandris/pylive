class GraphDelegate(QObject):
	def createNodeWidget(self, graph:NXGraphModel, n:Hashable):
		"""create and bind the widget"""
		widget = StandardNodeWidget()
		widget.label.textChanged.connect(lambda text:
			self.setNodeModelProps(graph, n, widget, label=text))
		return widget

	def setNodeWidgetProps(self, graph:NXGraphModel, n:Hashable, widget:QGraphicsWidget, **props):
		"""update iwdget props from model"""
		if 'label' in props.keys():
			widget.label.document().setPlainText(props['label'])
		
		if 'inlets' in props.keys():
			...

		if 'outlets' in props.keys():
			...

	def setNodeModelProps(self, graph:NXGraphModel, n:Hashable, widget:QGraphicsWidget, **props):
		"""update model props from widget"""
		graph.setNodeProperties(n, **props)

	def createEdgeWidget(self, graph:NXGraphModel, source:QGraphicsWidget, target:QGraphicsWidget):
		widget = EdgeWidget(source, target)

		return widget

	def setEdgeWidgetProps(self, graph:NXGraphModel, e:Tuple[Hashable, Hashable], widget:EdgeWidget, **props):
		...

	def setEdgeModelProps(self, graph:NXGraphModel, e:Tuple[Hashable, Hashable], widget:EdgeWidget, **props):
		...

