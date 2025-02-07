from contextlib import contextmanager
from PySide6.QtCore import QAbstractItemModel, QObject, QRectF

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

def distribute_items_horizontal(items, rect:QRectF):
    num_items = len(items)
    
    if num_items < 1:
        return

    if num_items <2:
        items[0].setX(rect.center().x())
        return

    # Calculate horizontal spacing
    spacing = rect.width() / (num_items - 1)
    for i, item in enumerate(items):
        x = rect.left() + i * spacing
        item.setX(x)