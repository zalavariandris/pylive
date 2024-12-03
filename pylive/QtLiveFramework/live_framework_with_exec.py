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

		terminal.setContext({'live': self, "__name__": "__live__"})
		
	@override
	def editor(self)->ScriptEdit:
		return cast(ScriptEdit, super().editor())

	def _execute_code(self, source):
		logger.info("executing code...")

		terminal = cast(Terminal, self.terminal())
		terminal.clear()

		if source.strip():
			terminal.execute(source)
		
		logger.info("code executed!") 


if __name__ == "__main__":
	# configure logging
	import logging
	log_format = '%(levelname)s: %(message)s'
	logging.basicConfig(level=logging.INFO, format=log_format)

	# create livecsript app
	app = QApplication(sys.argv)
	window = FrameworkWindow()
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
