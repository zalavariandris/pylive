
from typing import *
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject, Signal
from dataclasses import dataclass
from bidict import bidic

class Item:...

class ItemEditor(QWidget):
    valueChanged=Signal() # there are workarounds, in case the editor is not a subclass of an QWidget

@dataclass
class Model(QObject):
    items:list[Item]
    itemsAdded=Signal()

    def updateItem(self, item:Item, value:Any):
        ...

    def updateSubitem(self, subitem[tuple[Item,SubItem]], value:Any):
        # it is also possible that this can be handled by the uppadeItem.
        # also the view and the delegate can create subItem handlers as well.
        # TODO: create an example with subitems
        ...

class Delegate:
    def createItemEditor(self, model:Model, item:Item|tuple[Item,SubItem])->ItemEditor|None:
        ...

    def updateItemEditor(self, model:Model, item:Item|tuple[Item,SubItem])->ItemEditor:
        ...

@dataclass
class View(QWidget):
    model:'Model'
    delegate:'Delegate'
    _item_editors:bidict[Item, ItemEditor]

    def itemEditor(self, item:Item)->ItemEditor:
        # optional
        return self._item_editors[item]

    def onItemsAdded(self, items: Iterable[Item|tuple[Item,SubItem]]):
        for item in items:
            ### create item editor if 
            if item_editor := self.delegate.createItemEditor(self.model, item)
                item_editor.setParent(self) # here you can add it eg to a layout. as well

                ### make sure the editor is in the current state of the item
                # you can use the updateEditor delegate method can be used here,
                # or the createItemEditor should be implemented
                # to reflect the current state of the item
                self.delegate.updateItemEditor(self._model, item, item_editor)

                # connect to item editor signals
                item_editor.valueChanged.connect(self.model.updateItem(item, "any value"))

                # create a one-to-one relationship between the item and its editor
                self._item_editors[item] = item_editor
            

    def onItemsChange(self, items:Iterable[Item]):
        for item in items:
            item_editor = self._item_editors[item]
            self.delegate.updateItemEditor(self.model:Model, item:Item, editor:ItemEditor)

    def onItemsRemoved(self, items: Iterable[Item]):
        for item in items:
            if item in self._item_editors:
                item_editor = self._item_editors[item]
                item_editor.deleteLater() # remove the editor