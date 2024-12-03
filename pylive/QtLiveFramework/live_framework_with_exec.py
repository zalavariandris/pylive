import sys

from typing import *

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.QtLiveFramework.live_framework_skeleton import LiveFrameworkWindow, Placeholder
from pylive.QtScriptEditor.components.textedit_completer import TextEditCompleter
from pylive.QtScriptEditor.script_edit import ScriptEdit

import logging
logger = logging.getLogger(__name__)

from io import StringIO


from pylive.QtScriptEditor.components.async_jedi_completer import AsyncJediCompleter
from pylive.QtTerminal.terminal_with_exec import Terminal

import logging
logger = logging.getLogger(__name__)


class CellPreviewWidget(QWidget):
	...

class SupportLiveDisplay(Protocol):
    def _repr_html_(self)->str:
    	...

    def _repr_latex_(self)->str:
    	...

    def _repr_widfget_(self)->QWidget:
    	...


import ast


class SingletonException(Exception):
	...


def display(obj:SupportLiveDisplay):
	# get current framework
	window = FrameworkWindow.instance()
	window.display(obj)


class FrameworkWindow(LiveFrameworkWindow):
	_instance: Optional[Self] = None
	contentChanged = Signal()

	@classmethod
	def instance(cls) -> Self:
		"""
		Factory method to get the singleton instance of FrameworkWindow.
		"""
		if cls._instance is None:
			# Create the instance if it doesn't exist
			cls._instance = cls.__new__(cls)
			cls._instance._setupUI()
		return cls._instance

	def __init__(self, parent: Optional[QWidget] = None) -> None:
		"""
		Disable direct instantiation. Use instance() method instead.
		"""
		raise SingletonException("Singleon can cannot be instantiated directly. Use the 'instance()' static method!")

	def _setupUI(self):
		super().__init__(parent=None)
		self.setWindowTitle("IPython Console in PySide6")

		### IPython Console widget ###
		terminal = Terminal()
		self.setTerminal(terminal)
		self.setEditor(ScriptEdit())

		### Bind Widgets ###
		### bind texteditor to execute cells ###
		self.editor().cellsChanged.connect(lambda indexes: 
			self.execute_cells(indexes))

		terminal.exceptionThrown.connect(lambda exc: 
			self.editor().linter.lintException(exc, 'underline'))

		terminal.setContext({'display': display, "__name__": "__live__"})

		self.preview_area = QWidget()
		self.preview_layout = QVBoxLayout()
		self.preview_area.setLayout(self.preview_layout)
		self.setPreview(self.preview_area)
		self.cell_previews:Dict[int, QVBoxLayout] = {}
		
	@override
	def editor(self)->ScriptEdit:
		return cast(ScriptEdit, super().editor())

	def execute_cells(self, indexes:List[int]):
		for cell in indexes:
			logger.info(f"execute_cell: {cell}")
			if not self.cell_previews.get(cell, None):
				cell_layout = QVBoxLayout()
				self.cell_previews[cell] = cell_layout
				self.preview_layout.addLayout(cell_layout)
			else:
				while self.cell_previews[cell].count():
					item = self.cell_previews[cell].takeAt(0)
					if widget:=item.widget():
						widget.deleteLater()

			first_line = self.editor().cell(cell).split("\n")[0]
			self.cell_previews[cell].addWidget(QLabel(first_line))

			cell_line_offset = 0
			for i in range(cell):
				cell_source = self.editor().cell(cell)
				line_count = len(cell_source.split("\n"))					
				cell_line_offset+=line_count
			cell_source = self.editor().cell(cell)
			cell_source = "\n"*cell_line_offset + cell_source

			logger.info("executing code...")

			terminal = cast(Terminal, self.terminal())
			terminal.clear()

			if cell_source.strip():
				self._current_cell = cell
				terminal.execute(cell_source)
			
			logger.info("code executed!") 

	def display(self, data):
		print("display", data)
		match data:
			case QWidget():
				widget = cast(QWidget, data)
				self.cell_previews[self._current_cell].addWidget(widget)
			case _:
				msg_label = QLabel(f"{data}")
				self.cell_previews[self._current_cell].addWidget(msg_label)


if __name__ == "__main__":
	# configure logging
	import logging
	log_format = '%(levelname)s: %(message)s'
	logging.basicConfig(level=logging.INFO, format=log_format)

	# create livecsript app
	app = QApplication(sys.argv)
	window = FrameworkWindow.instance()
	window.show()
	
	# set initial code
	from textwrap import dedent
	script = dedent("""\
		#%% setup
		from PySide6.QtWidgets import *

		button = QPushButton("Click Me")
		app.setPreview(button)

		#%% update
		button.setText("hello")
	""")
	window.editor().setPlainText(script)

	# launch QApp
	sys.exit(app.exec())
