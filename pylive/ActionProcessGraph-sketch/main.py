from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

### Model Controllers
class Action(QObject):
	def __init__(self, function:Callable, parent:QObject|None=None):
		super().__init__(parent=parent)
		self.function = function

	def __call__(self, *args, **kwargs):
		self.function(*args, **kwargs)


class Process(QObject):
	actionAdded = Signal(str)
	actionRemoved = Signal(str)
	linked = Signal()
	unlinkied = Signal()
	
	def __init__(self, parent:QObject|None=None):
		super().__init__(parent=parent)
		self.output:Action|None = None
		self._actions = {}

	def addAction(self, name:str, action:Action):
		self._actions[name] = action

	def removeAction(self, name:str):
		del self._actions[name]
	
	def __call__(self, *args, **kwargs):
		# call topological sorted output anchestors


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    main = Process()
    read_action = Action(read_text)
    main.addAction(read_text)
    sys.exit(app.exec())