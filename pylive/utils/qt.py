from contextlib import contextmanager
from PySide6.QtCore import QObject
@contextmanager
def signalsBlocked(obj:QObject):
    WereSignalsBlocked = obj.signalsBlocked()
    obj.blockSignals(True)
    try:
        yield None
    finally:
        obj.blockSignals(WereSignalsBlocked)