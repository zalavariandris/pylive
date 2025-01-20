from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel

class NXNodeProxyModel(QObject):
	modelReset = Signal()
	nodeReset = Signal()
	def __init__(self, parent:QObject|None=None):
		self._model:NXGraphModel|None
		self._node_id:Hashable|None
		super().__init__(parent=parent)

	def setModel(self, model:NXGraphModel):
		self._model = model
		self.modelReset.emit()

	def model(self)->NXGraphModel|None:
		return self._model

	def setNode(self, node_id:Hashable):
		self._node_

