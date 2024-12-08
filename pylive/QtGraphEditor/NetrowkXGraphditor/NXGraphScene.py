


class MyNodeWidget(QGraphicsWidget):
	def __init__(self, parent=None):
		# model reference
		# self.persistent_node_index:Optional[NodeRef] = None
		super().__init__(parent)
		# # widgets
		self.nameedit = EditableTextItem(self)
		self.nameedit.setPos(0,0)
		self.nameedit.setTextWidth(self.geometry().width()-10)

	def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
		# Enable editing subitems on double-click
		"""parent node must manually cal the double click event,
		because an item nor slectable nor movable will not receive press events"""

		# Check if double-click is within the text item’s bounding box
		if self.nameedit.contains(self.mapFromScene(event.scenePos())):
			# Forward the event to nameedit if clicked inside it
			self.nameedit.mouseDoubleClickEvent(event)
		else:
			print("NodeItem->mouseDoubleClickEvent")
			super().mouseDoubleClickEvent(event)


class MyEdgeWidget(QGraphicsItem):
	def __init__(self, parent=None):
		super().__init__(parent=parent)


class ConnectableProtocol(Protocol):
	geometryChanged = Signal()

class EdgeWidgetProtocol(Protocol):
	def setSourcePin(self, source_outlet:ConnectableProtocol):
		...

	def setTargetPin(self, target_inlet:ConnectableProtocol):
		...
