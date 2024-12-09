from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from link_graphics_items import makeLineBetweenShapes

TNodeWidget = TypeVar('TNodeWidget')  # Represents the type of a node widget
TEdgeWidget = TypeVar('TEdgeWidget')  # Represents the type of an edge widget



class AbstractGraphDelegate(Generic[TNodeWidget, TEdgeWidget], QObject):
	def createNodeWidget(self, graph: 'NXGraphModel', n: Hashable) -> TNodeWidget:
		"""create and bind the widget"""
		widget = TNodeWidget()  # You will need a factory or type here
		widget.label.textChanged.connect(lambda text:
			self.setNodeModelProps(graph, n, widget, label=text))
		return widget

	def setNodeWidgetProps(self, graph: 'NXGraphModel', n: Hashable, widget: TNodeWidget, **props):
		...

	def setNodeModelProps(self, graph: 'NXGraphModel', n: Hashable, widget: TNodeWidget, **props):
		...

	def createEdgeWidget(self, graph: 'NXGraphModel', source: TNodeWidget, target: TNodeWidget) -> TEdgeWidget:
		...

	def setEdgeWidgetProps(self, graph: 'NXGraphModel', e: Tuple[Hashable, Hashable], widget: TEdgeWidget, **props):
		...

	def setEdgeModelProps(self, graph: 'NXGraphModel', e: Tuple[Hashable, Hashable], widget: TEdgeWidget, **props):
		...



