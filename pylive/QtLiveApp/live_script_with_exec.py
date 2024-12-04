import sys

from typing import *

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.QtLiveApp.live_app_skeleton import LiveAppWindow, Placeholder
from pylive.QtScriptEditor.components.textedit_completer import TextEditCompleter
from pylive.QtScriptEditor.script_edit import ScriptEdit

import logging
logger = logging.getLogger(__name__)

from io import StringIO

from pylive.QtScriptEditor.cell_support import cell_at_line, split_cells

from pylive.QtScriptEditor.components.async_jedi_completer import AsyncJediCompleter
from pylive.QtTerminal.terminal_with_exec import Terminal
from pylive.QtLiveApp.file_link import FileLink

import logging
logger = logging.getLogger(__name__)



import ast
from pathlib import Path
class LiveAppWithExec(LiveAppWindow):
	@override
	def setupUI(self):
		super().setupUI()
		

		### IPython Console widget ###
		terminal = Terminal()
		self.setTerminal(terminal)
		editor = ScriptEdit()
		self.setEditor(editor)

		self.fileLink = FileLink(editor.document())
		self.fileLink.filePathChanged.connect(self.updateWindowTitle)
		editor.document().modificationChanged.connect(self.updateWindowTitle)

		filemenu = self.fileLink.createFileMenu()
		if self.menuBar().actions():
			self.menuBar().insertMenu(self.menuBar().actions()[0], filemenu)
		else:
			self.menuBar().addMenu(filemenu)

		### Bind Widgets ###
		### bind texteditor to execute cells ###
		self.editor().cellsChanged.connect(lambda indexes: 
			self.execute_cells(indexes))

		terminal.exceptionThrown.connect(lambda exc: 
			self.editor().linter.lintException(exc, 'underline'))

		terminal.setContext({"__name__": "__live__"})

		self.updateWindowTitle()

		editor.installEventFilter(self)

	def eventFilter(self, watched: QObject, event: QEvent) -> bool:
		if watched == self.editor() and event.type()==QEvent.Type.KeyPress:
			keypress = cast(QKeyEvent, event)
			if keypress.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter}:
				if keypress.modifiers() == Qt.KeyboardModifier.ShiftModifier:
					cell = self.editor().cellAtCursor()
					cell_content = self.editor().cell(cell)
					return True

		return super().eventFilter(watched, event)
		
	@override
	def editor(self)->ScriptEdit:
		return cast(ScriptEdit, super().editor())

	def execute_cells(self, indexes:List[int]):
		self.editor().linter.clear()
		for cell in indexes:
			logger.info(f"execute_cell: {cell}")


			# first_line = self.editor().cell(cell).split("\n")[0]

			# prepend empty lines, so when an exception occures, the linnumber will match the while script lines
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
			self.statusBar().showMessage(f"cells executed {indexes}")
			
			logger.info("code executed!")

	def updateWindowTitle(self):
		file_title = "untitled"
		if self.fileLink.filepath:
			file_title = Path(self.fileLink.filepath).name

		modified_mark = ""
		if self.editor().document().isModified():
			modified_mark = "*"

		self.setWindowTitle(f"{file_title} {modified_mark} - LiveScript (using exec)")

	def closeEvent(self, event):
			DoCloseFile = self.fileLink.closeFile()
			if not DoCloseFile:
				event.ignore()
				return

			event.accept()

if __name__ == "__main__":
	# configure logging
	import logging
	log_format = '%(levelname)s: %(message)s'
	logging.basicConfig(level=logging.INFO, format=log_format)

	# create livecsript app
	app = QApplication(sys.argv)

	window = LiveAppWithExec.instance()
	live = LiveAppWindow.instance()
	live = LiveAppWindow.instance()
	window.show()
	
	# set initial code
	from textwrap import dedent

	script = dedent('''\
		#%% setup
		from PySide6.QtWidgets import *
		from pylive.QtLiveApp import display

		#%% update
		print(f"Print this {28} to the console!")

		display("""\\
		Display this *text* or any *QWidget* in the preview area.
		""")
	''')
	window.editor().setPlainText(script)

	# launch QApp
	sys.exit(app.exec())
