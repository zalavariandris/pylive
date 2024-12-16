from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

TGraphModel = TypeVar('TGraphModel')
TNodeWidget = TypeVar('TNodeWidget')  # Represents the type of a node widget
TEdgeWidget = TypeVar('TEdgeWidget')  # Represents the type of an edge widget

class AbstractGraphDelegate(Generic[TNodeWidget, TEdgeWidget], QObject):
	def createNodeWidget(self, graph: TGraphModel, n: Hashable) -> TNodeWidget:
		"""create widget and bind thw widget signals to update the model"""
		...

	def setNodeWidgetProps(self, graph: TGraphModel, n: Hashable, widget: TNodeWidget, **props):
		"""update widget when model changes"""
		...

	def setNodeModelProps(self, graph: TGraphModel, n: Hashable, widget: TNodeWidget, **props):
		"""
		Update the model when widget emits signals.
		This is a convenient function and not called automatically.
		It shoul be connected when the widget is created.
		"""
		...

	def createEdgeWidget(self, graph: TGraphModel, source: TNodeWidget, target: TNodeWidget) -> TEdgeWidget:
		"""create widget to connect the nodes."""
		...

	def setEdgeWidgetProps(self, graph: TGraphModel, e: Tuple[Hashable, Hashable], widget: TEdgeWidget, **props):
		"""update link widget with the edge properties"""
		...

	def setEdgeModelProps(self, graph: TGraphModel, e: Tuple[Hashable, Hashable], widget: TEdgeWidget, **props):
		"""
		Update the edge properties when the edge widget emits signals.
		This is a convenient function and not called automatically.
		It shoul be connected when the widget is created.
		"""
		...
