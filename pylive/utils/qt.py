from contextlib import contextmanager
from PySide6.QtCore import QAbstractItemModel, QObject

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