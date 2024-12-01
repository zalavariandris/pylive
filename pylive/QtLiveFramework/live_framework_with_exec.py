import sys
from typing import *

from typing import *

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


from pylive.QtLiveFramework.live_framework_skeleton import LiveFrameworkWindow, Placeholder
from pylive.QtScriptEditor.script_edit import ScriptEdit

import logging
logger = logging.getLogger(__name__)

from io import StringIO
from pylive.logwindow import LogWindow

class Terminal(QWidget):
	exceptionThrown = Signal(Exception)
	messageSent = Signal(str)

	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setContext({})

		self.output = LogWindow()
		self.output.setReadOnly(True)
		self.input = QLineEdit()
		self.input.setPlaceholderText("type something...")

		self.input.returnPressed.connect(lambda: (
			self._execute(self.input.text(), 'single'),
			self.input.clear(),
			self.output.verticalScrollBar().setValue(self.output.verticalScrollBar().maximum())
		))

		layout = QVBoxLayout()
		layout.setContentsMargins(0,0,0,0)
		self.setLayout(layout)
		layout.addWidget(self.output)
		layout.addWidget(self.input)


		self.exceptionThrown.connect(lambda exc: print(f"{exc}"))

	def execute(self, source:str):
		self._execute(source)

	def context(self):
		return self._context

	def setContext(self, context:dict):
		self._context = context
		self._context['__builtins__'] = __builtins__

	def _execute(self, source:str, mode:Literal["exec","single"]="exec"):
		try:
			tree = ast.parse(source)
			try:
				code = compile(source, "<script>", mode=mode)
				try:
					result = exec(code, self.context())
					if result:
						print(result)
				except SyntaxError as err:
					self.exceptionThrown.emit(err) #label
				except Exception as err:
					self.exceptionThrown.emit(err) #label
			except SyntaxError as err:
				self.exceptionThrown.emit(err) # underline
			except Exception as err:
				self.exceptionThrown.emit(err) # underline

		except SyntaxError as err:
			self.exceptionThrown.emit(err) # underline
		except Exception as err:
			self.exceptionThrown.emit(err) # underline

	def print(self, msg):
		...

	def error(self, exception:Exception):
		pass

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
			logger.info(f"execute_cells: {indexes}")
			for idx in indexes:
				self._execute_code( self.editor().cell(idx) )

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
	
	# window.execute_code(code_to_execute)  # This will add a button to the layout

	sys.exit(app.exec())

if __name__ == "__main__":
	main()
