from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel
from enum import StrEnum


class NXGraphSelectionModel(QObject):
    # SIGNALS
    modelChanged = Signal(NXGraphModel)
    """This signal is emitted when the model
    is successfully set withsetModel()."""

    selectionChanged = Signal(set, set)
    """This signal is emitted whenever the selection changes.
    selected:set[Hashable], deselected: set[Hashable
    """

    def __init__(self, model: NXGraphModel | None = None, parent=None):
        super().__init__(parent=parent)
        self._model: NXGraphModel | None = model
        self._selectedNodes: list[Hashable] = []

    # Public Types
    ...

    # Public Functions
    def hasSelection(self) -> bool:
        """Returns true if the selection model contains any selected item,
        otherwise returns false."""
        return len(self._selectedNodes) > 0

    def isSelected(self, n: Hashable) -> bool:
        """Returns true if the given node is selected"""
        return n in self._selectedNodes

    def model(self):
        """Returns the item model operated on by the selection model."""
        return self._model

    def setModel(self, model: NXGraphModel):
        """Sets the model to model. The modelChanged() signal will be emitted."""
        self._model = model
        self.modelChanged.emit(model)

    # Public Slots
    def clear(self):
        oldSelection = [n for n in self._selectedNodes]
        self._selectedNodes = []
        self.__emitSelectionChanged(self._selectedNodes, oldSelection)

    def select(
        self,
        selection: set[Hashable],
        command: Literal["select", "toggle", "deselect"],
    ):
        """Selects the nodes, and emits selectionChanged()."""
        match command:
            case "select":
                oldSelection = [n for n in self._selectedNodes]
                newSelection = oldSelection + [n for n in selection]
                self._selectedNodes = newSelection
                self.__emitSelectionChanged(oldSelection, newSelection)
            case "toggle":
                oldSelection = [n for n in self._selectedNodes]
                newSelection = [n for n in self._selectedNodes]
                for n in selection:
                    if n in oldSelection:
                        newSelection.remove(n)
                    else:
                        newSelection.append(n)
                self._selectedNodes = newSelection
                self.__emitSelectionChanged(oldSelection, newSelection)
            case "deselect":
                oldSelection = [n for n in self._selectedNodes]
                newSelection = [n for n in self._selectedNodes]
                for n in selection:
                    newSelection.remove(n)
                self._selectedNodes = newSelection
                self.__emitSelectionChanged(oldSelection, newSelection)
            case _:
                raise ValueError("Command '{command}' is not supported.")

    # Properties
    def selectedNodes(self) -> list[Hashable]:
        return [n for n in self._selectedNodes]

    def setSelectedNodes(self, nodes: list[Hashable]):
        oldSelection = [n for n in self._selectedNodes]
        newSelection = [n for n in nodes]
        self._selectedNodes = newSelection
        self.__emitSelectionChanged(newSelection, oldSelection)

    def currentNode(self)->Hashable|None:
        if len(self._selectedNodes)>0:
            return self._selectedNodes[0]
        else:
            return None

    # Protected
    def __emitSelectionChanged(
        self, newSelection: list[Hashable], oldSelection: list[Hashable]
    ):
        newSelectionSet = set(newSelection)
        oldSelectionSet = set(oldSelection)
        selected = newSelectionSet - oldSelectionSet
        deselected = oldSelectionSet - newSelectionSet

        # change guard
        if len(selected) > 0 or len(deselected) > 0:
            self.selectionChanged.emit(selected, deselected)
