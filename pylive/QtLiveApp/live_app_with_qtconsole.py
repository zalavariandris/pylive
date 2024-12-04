import sys
from typing import *

from typing import *
from IPython.core.interactiveshell import ExecutionResult
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from ipykernel.inprocess.ipkernel import InProcessKernel
from ipykernel.zmqshell import ZMQInteractiveShell
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager


from pylive.QtLiveApp.live_app_skeleton import LiveAppWindow
from pylive.QtScriptEditor.script_edit import ScriptEdit

import logging
logger = logging.getLogger(__name__)

from io import StringIO


class IPythonWindow(LiveAppWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("IPython Console in PySide6")

		### IPython Console widget ###
		jupyter = RichJupyterWidget(
			style_sheet='dracula', 
			syntax_style='dracula',
			gui_completion = 'droplist', # plain | droplist | ncurses
			complete_while_typing=True,
			enable_history_search=False
		)
		self.setTerminal(jupyter)

		self.setEditor(ScriptEdit())

		### Bind Widgets ###
		### Create in-process kernel
		self.kernel_manager = QtInProcessKernelManager()
		self.kernel_manager.start_kernel(show_banner=False)
		self.kernel_client = self.kernel_manager.client()

		# connect qtconsole to the kernel
		jupyter.kernel_manager = self.kernel_manager # Connect the kernel manager to the console widget
		jupyter.kernel_client = self.kernel_client
		jupyter.kernel_client.start_channels() # Start the kernel client channels (this is the communication between the UI and the kernel)

		### expose this widget to the kernel ###
		self.kernel_manager.kernel.shell.user_ns['app'] = self

		### bind texteditor to execute ###
		def execute_cells(indexes):
			logger.info(f"execute_cells: {indexes}")
			for idx in indexes:
				self._execute_code( self.editor().cell(idx) )

		self.editor().cellsChanged.connect(execute_cells)
		

	def _execute_code(self, code_str):
		logger.info("executing code...")
		if not code_str.strip():
			return  # Do nothing if the input is empty

		try:
			# Execute the code
			# result = self.kernel_manager.kernel.shell.run_cell(code_str)

			def execute_in_console():
				"""
				Execute a command in the frame of the console widget
				"""
				self.terminal().execute(code_str, hidden=True)
				# self.terminal()._append_plain_text("EXECUTED")

			def run_cell_with_shell()->ExecutionResult:
				kernel:InProcessKernel = self.kernel_manager.kernel
				shell:ZMQInteractiveShell = kernel.shell
				return shell.run_cell(code_str)

			execute_in_console()
			
		except Exception as e:
			logger.error(f"Exception: {str(e)}")
		finally:
			...

		logger.info("code executed!") 


def main():
	import logging
	log_format = '%(levelname)s: %(message)s'
	# logging.basicConfig(level=logging.INFO, format=log_format)
	app = QApplication(sys.argv)
	
	window = IPythonWindow()
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
