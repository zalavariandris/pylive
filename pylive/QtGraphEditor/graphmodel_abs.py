from abc import ABC, abstractmethod

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from typing import *

from pylive.QtGraphEditor.graphmodel_columnbased import NodeRef

class GraphModelABC(ABC, QObject):
	nodesAdded = Signal(list) #List[NodeRef]
	nodesAboutToBeRemoved = Signal(list) #List[NodeRef]
	nodesDataChanged = Signal(list, list) #List[NodeRef], List[NodeDataColumn]

	inletsAdded = Signal(list) #List[InletRef]
	inletsAboutToBeRemoved = Signal(list) #List[InletRef]
	inletsDataChanged = Signal(list, list) #List[InletRef], List[InletDataColumn]

	outletsAdded = Signal(list) #List[OutletIndex]
	outletsAboutToBeRemoved = Signal(list) #List[OutletRef]
	outletsDataChanged = Signal(list, list) #List[OutletRef], List[OutletDataColumn]

	edgesAdded = Signal(list) #List[EdgeRef]
	edgesAboutToBeRemoved = Signal(list) #List[EdgeRef]
	edgesDataChanged = Signal(list, list) #List[EdgeRef], List[EdgeDataColumn]

	@abstractmethod
	def get_nodes(self)->Iterable[NodeRef]:
		...


class GraphModel_databased(GraphModelABC):
	def get_nodes(self)->Iterable[NodeRef]:
		return None