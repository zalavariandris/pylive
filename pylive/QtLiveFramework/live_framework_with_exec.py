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
from pylive.QtLiveFramework.terminal_with_exec import Terminal

import logging
log_format = '%(levelname)s: %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)


import ast
class FrameworkWindow(LiveFrameworkWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("IPython Console in PySide6")

		### IPython Console widget ###
		terminal = Terminal()
		self.setTerminal(terminal)
		self.setEditor(ScriptEdit())

		### Bind Widgets ###
		### bind texteditor to execute cells ###
		@self.editor().cellsChanged.connect
		def execute_cells(indexes):
			for idx in indexes:
				logger.info(f"execute_cell: {idx}")
				cell_line_offset = 0
				for i in range(idx):
					cell_source = self.editor().cell(idx)
					line_count = len(cell_source.split("\n"))					
					cell_line_offset+=line_count
				cell_source = self.editor().cell(idx)
				cell_source = "\n"*cell_line_offset + cell_source
				self._execute_code( cell_source )

		terminal.exceptionThrown.connect(lambda exc: 
			self.editor().linter.lintException(exc, 'underline'))

		terminal.setContext({'app': self})
		
	@override
	def editor(self)->ScriptEdit:
		return cast(ScriptEdit, super().editor())

	def _execute_code(self, source):
		logger.info("executing code...")
		if not source.strip():
			return  # Do nothing if the input is empty

		terminal = cast(Terminal, self.terminal())
		terminal.clear()
		terminal.execute(source)
		
		logger.info("code executed!") 


def main():
	import logging
	log_format = '%(levelname)s: %(message)s'
	# logging.basicConfig(level=logging.INFO, format=log_format)
	app = QApplication(sys.argv)
	
	window = FrameworkWindow()
	# window.setApp(WidgetPreviewApp())
	window.show()
	
	# Execute a string of code using the execute_code method to add a widget
	from textwrap import dedent
	code_to_execute = dedent("""\
	#%% setup
	from PySide6.QtWidgets import *

	# Create a new QPushButton
	button = QPushButton("Click Me")
	app.setPreview(button)

	# %% update
	button.setText("hello")
	""")
	window.editor().setPlainText(code_to_execute)

	def print_cells():
		print("==CELLS==")
		for cell in window.editor()._cells:
			print("---------")
			print(cell)
		print("=========\n")
	# window.editor().textChanged.connect(print_cells)
	
	# window.execute_code(code_to_execute)  # This will add a button to the layout

	sys.exit(app.exec())

if __name__ == "__main__":
	main()
