
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class PyDataModel(QObject):
	nodesInserted = Signal()
	nodesAboutToBeRemoved = Signal()
	nodesRemoved = Signal()

	linksInserted = Signal()
	linksAboutToBeRemoved = Signal()
	linksRemoved = Signal()

	fieldsReset = Signal()
	fieldChanged = Signal()

	nameChanged = Signal()
	sourceChanged = Signal()
	errorChanged = Signal()
	statusChanged = Signal()
	resultChanged = Signal()

	def nodeCount(self):
		...

	def linkCount(self):
		...

	def insertNode(self, node_name, func):
		...

	def removeNode(self, node_name):
		...

	def link(self, source_node_name, target_node_name, inlet_name, outlet_name):
		...

	def unlink(self, source_node_name, target_node_name, inlet_name, outlet_name):
		...

	def name(self, node_name):
		...

	def source(self, node_name):
		...

	def inlets(self, node_name):
		...

	def outlets(self, node_name):
		return ['out']

	def error(self, node_name):
		...

	def result(self, node_name):
		...

	def compile(self, node_name):
		...

	def setField(self, node, field_name, value):
		...

	def field(self, node_name, field_name):
		...

	def evaluate(self, node_name):
		...
