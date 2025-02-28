from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


from pylive.VisualCode_v4.py_data_model import PyDataModel



class PySubgraphProxyModel(QObject):
    modelAboutToBeReset = Signal()
    modelReset = Signal()

    # Node data
    positionChanged = Signal(str)
    sourceChanged = Signal(str)
    compiledChanged = Signal(str)
    evaluatedChanged = Signal(str)
    errorChanged = Signal(str)
    resultChanged = Signal(str)

    # Node Parameters
    parametersAboutToBeReset = Signal(str)
    parametersReset = Signal(str)
    parametersAboutToBeInserted = Signal(str, int, int) # node, start, end
    parametersInserted = Signal(str, int, int) # node, start, end
    patametersChanged = Signal(str, int, int) # node, first, last
    parametersAboutToBeRemoved = Signal(str, int, int) # node, start, end
    parametersRemoved = Signal(str, int, int) # node, start, end

    # Node Links
    nodesAboutToBeLinked = Signal(list) # tuple[source, target, inlet]
    nodesLinked = Signal(list) # list[str,str,str]
    nodesAboutToBeUnlinked = Signal(list) # list[str,str,str]
    nodesUnlinked = Signal(list) # list[str,str,str]


    def __init__(self, source_model:PyDataModel|None=None, parent:QObject|None=None):
        super().__init__(parent=parent)
        self._source_model = source_model
        self._nodes = set()
        self._source_connections = []
        self.setSourceModel(source_model)

    def setSourceModel(self, sourceModel:PyDataModel|None):
        self.modelAboutToBeReset.emit()
        if self._source_model:
            for signal, slot in self._source_connections:
                signal.disconnect(slot)

        if sourceModel:
            def filterDataChangeSignal(signal, n, *args):
                if n in self._nodes:
                    signal.emit(n, *args)

            def filterLinkSignal(signal, links:list[tuple[str,str,str]]):
                filtered_links = [(src, dst, inlet) for src,dst,inlet in links if src in self._nodes or dst in self._nodes]
                if len(links)>0:
                    signal.emit(filtered_links)

            self._source_connections = [
                # model
                (sourceModel.modelAboutToBeReset, self.modelAboutToBeReset),
                (sourceModel.modelReset, self.modelReset),

                # nodes
                (sourceModel.positionChanged, lambda n: filterDataChangeSignal(self.positionChanged, n)),
                (sourceModel.sourceChanged, lambda n: filterDataChangeSignal(self.sourceChanged, n)),
                (sourceModel.compiledChanged, lambda n: filterDataChangeSignal(self.compiledChanged, n)),
                (sourceModel.evaluatedChanged, lambda n: filterDataChangeSignal(self.evaluatedChanged, n)),
                (sourceModel.errorChanged, lambda n: filterDataChangeSignal(self.errorChanged, n)),
                (sourceModel.resultChanged, lambda n: filterDataChangeSignal(self.resultChanged, n)),

                # parameters
                (sourceModel.parametersAboutToBeReset, lambda n: filterDataChangeSignal(self.parametersAboutToBeReset, n)),
                (sourceModel.parametersReset, lambda n: filterDataChangeSignal(self.parametersReset, n)),
                (sourceModel.parametersAboutToBeInserted, lambda n, first, last: filterDataChangeSignal(self.parametersAboutToBeInserted, n, first, last)),
                (sourceModel.parametersInserted, lambda n, first, last: filterDataChangeSignal(self.parametersInserted, n, first, last)),
                (sourceModel.patametersChanged, lambda n, first, last: filterDataChangeSignal(self.patametersChanged, n, first, last)),
                (sourceModel.parametersAboutToBeRemoved, lambda n, first, last: filterDataChangeSignal(self.parametersAboutToBeRemoved, n, first, last)),
                (sourceModel.parametersRemoved, lambda n, first, last: filterDataChangeSignal(self.parametersRemoved, n, first, last)),

                # links
                (sourceModel.nodesAboutToBeLinked, lambda links: filterLinkSignal(self.nodesAboutToBeLinked, links)),
                (sourceModel.nodesLinked, lambda links: filterLinkSignal(self.nodesLinked, links)),
                (sourceModel.nodesAboutToBeUnlinked, lambda links: filterLinkSignal(self.nodesAboutToBeUnlinked, links)),
                (sourceModel.nodesUnlinked, lambda links: filterLinkSignal(self.nodesUnlinked, links))
            ]

            for signal, slot in self._source_connections:
                signal.connect(slot)
        self._source_model = sourceModel
        self.modelReset.emit()

    def setNodes(self, nodes:Iterable[str]):
        self.modelAboutToBeReset.emit()
        self._nodes = set([n for n in nodes])
        self.modelReset.emit()

    def nodeCount(self)->int:
        return len(self._nodes)

    def nodes(self)->Collection[str]:
        if not self._source_model:
            return []
        return [n for n in self._source_model._nodes.keys() if n in self._nodes]

    def links(self)->Collection[tuple[str,str,str]]:
        if not self._source_model:
            return []
        return [(source, target, inlet) 
            for source, target, inlet in self._source_model.links() 
            if source in self._nodes or target in self._nodes]

    def linkCount(self):
        return len(self.links())