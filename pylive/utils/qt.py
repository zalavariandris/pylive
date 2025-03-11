from contextlib import contextmanager
from PySide6.QtCore import QAbstractItemModel, QObject, QRectF
from PySide6.QtWidgets import QGraphicsItem

@contextmanager
def signalsBlocked(obj:QObject):
    WereSignalsBlocked = obj.signalsBlocked()
    obj.blockSignals(True)
    try:
        yield None
    finally:
        obj.blockSignals(WereSignalsBlocked)

@contextmanager
def modelReset(model:QAbstractItemModel):
    model.beginResetModel()
    try:
        yield None
    finally:
        model.endResetModel()

def distribute_items_horizontal(items:list[QGraphicsItem], rect:QRectF, equal_spacing=True):
    num_items = len(items)
    
    if num_items < 1:
        return

    if num_items <2:
        items[0].setX(rect.center().x())
        return

    if equal_spacing:
        items_overal_width = 0
        for item in items:
            items_overal_width+=item.boundingRect().width() #TODO use reduce?

        spacing = ( rect.width() - items_overal_width) / (num_items-1)
        position = 0
        for i, item in enumerate(items):
            item.setX(position)
            position+=item.boundingRect().width()+spacing

    else:
        distance = rect.width() / (num_items - 1)
        for i, item in enumerate(items):
            x = rect.left() + i * distance
            item.setX(x)

def logModelSignals(model:QAbstractItemModel, prefix:str=""):
    model.columnsAboutToBeInserted.connect(lambda *args: print(f"{prefix}, columnsAboutToBeInserted {args}"))
    model.columnsAboutToBeMoved.connect(lambda *args: print(f"{prefix}, columnsAboutToBeMoved {args}"))
    model.columnsAboutToBeRemoved.connect(lambda *args: print(f"{prefix}, columnsAboutToBeRemoved {args}"))
    model.columnsInserted.connect(lambda *args: print(f"{prefix}, columnsInserted {args}"))
    model.columnsMoved.connect(lambda *args: print(f"{prefix}, columnsMoved {args}"))
    model.columnsRemoved.connect(lambda *args: print(f"{prefix}, columnsRemoved {args}"))
    model.dataChanged.connect(lambda *args: print(f"{prefix}, dataChanged {args}"))
    model.headerDataChanged.connect(lambda *args: print(f"{prefix}, headerDataChanged {args}"))
    model.layoutAboutToBeChanged.connect(lambda *args: print(f"{prefix}, layoutAboutToBeChanged {args}"))
    model.layoutChanged.connect(lambda *args: print(f"{prefix}, layoutChanged {args}"))
    model.modelAboutToBeReset.connect(lambda *args: print(f"{prefix}, modelAboutToBeReset {args}"))
    model.modelReset.connect(lambda *args: print(f"{prefix}, modelReset {args}"))
    model.rowsAboutToBeInserted.connect(lambda *args: print(f"{prefix}, rowsAboutToBeInserted {args}"))
    model.rowsAboutToBeMoved.connect(lambda *args: print(f"{prefix}, rowsAboutToBeMoved {args}"))
    model.rowsAboutToBeRemoved.connect(lambda *args: print(f"{prefix}, rowsAboutToBeRemoved {args}"))
    model.rowsInserted.connect(lambda *args: print(f"{prefix}, rowsInserted {args}"))
    model.rowsMoved.connect(lambda *args: print(f"{prefix}, rowsMoved {args}"))
    model.rowsRemoved.connect(lambda *args: print(f"{prefix}, rowsRemoved {args}"))

def getWidgetByName(name:str):
    app = QApplication.instance()
    if not app:
        raise Exception("No QApplication instance!")

    # find widget
    for widget in QApplication.allWidgets():
        if widget.objectName() == name:
            return widget
    return None
