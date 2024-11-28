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

from pylive.declerative_qt import Splitter, Panel
from pylive.live_preview_widgets.file_textdocument_link import FileTextDocumentLink
from pylive.QtScriptEditor.components.pygments_syntax_highlighter import PygmentsSyntaxHighlighter


class WidgetPreviewApp(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setLayout(QVBoxLayout())
		self.layout().setContentsMargins(0,0,0,0)

		# Set up the palette
		palette = self.palette()
		brush = QBrush(Qt.yellow)  # You can use other colors or gradients
		palette.setBrush(QPalette.Window, palette.color(QPalette.ColorGroup.All, QPalette.ColorRole.Base))
		self.setPalette(palette)
		self.setAutoFillBackground(True)

# |---------LiveFramework---------|
# | |--CodeEditor--|---Preview---| |
# | | cell1        | show widget | |
# | | cell1        |             | |
# | | ...          |---Terminal--| |
# | |              |   log and   | |
# | |              |   interact  | |
# | |--------------|-------------| |
# |--------------------------------|


from io import StringIO
class IPythonWindow(QWidget):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("IPython Console in PySide6")

		### create in process kernel
		self.kernel_manager = QtInProcessKernelManager()
		self.kernel_manager.start_kernel(show_banner=False)
		self.kernel_client = self.kernel_manager.client()

		### IPython Console widget ###
		self.console = RichJupyterWidget(
			style_sheet='dracula', 
			syntax_style='dracula',
			gui_completion = 'droplist', # plain | droplist | ncurses
			complete_while_typing=True,
			enable_history_search=False
		)
		# self.console.style_sheet = "dracula"
		# self.console.syntax_style = "dracula"
		
		# and connect to the kernel
		self.console.kernel_manager = self.kernel_manager # Connect the kernel manager to the console widget
		self.console.kernel_client = self.kernel_client
		self.console.kernel_client.start_channels() # Start the kernel client channels (this is the communication between the UI and the kernel)

		### Script Edit ###
		self.textedit = QPlainTextEdit()
		font = self.textedit.font()
		font.setFamilies(["monospace", "Operator Mono Book"])
		font.setWeight(QFont.Weight.Medium)
		font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
		self.textedit.setFont(font)
		self.textedit.setWordWrapMode(QTextOption.WrapMode.NoWrap)
		highlighter = PygmentsSyntaxHighlighter(self.textedit.document())
		self.textedit.setTabStopDistance(self.textedit.fontMetrics().horizontalAdvance(" ")*4)
		self.textedit.setReadOnly(True)

		### Script Edit ###
		from textwrap import dedent
		placeholder = QLabel(dedent("""
		[preview area]
		use .setAppWidget to show a widget here
		"""))

		self.preview_area = QWidget()
		self.preview_area.setLayout(QVBoxLayout())
		self.preview_area.layout().setContentsMargins(0,0,0,0)

		placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.app = placeholder
		self.app.setLayout(QVBoxLayout())
		# placeholder = QLabel("[preview area]")
		# placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
		# self.preview_area.layout().addWidget(placeholder)

		### Layout ###
		self.console.setFixedHeight(140)
		main_splitter = Splitter(Qt.Orientation.Horizontal, [
			Panel(QBoxLayout.Direction.TopToBottom, [
				self.textedit
			]),
			Panel(QBoxLayout.Direction.TopToBottom, [
				self.preview,
				self.console
			])
		])
		mainLayout = QVBoxLayout()
		mainLayout.setContentsMargins(0,0,0,0)
		mainLayout.addWidget(main_splitter)
		self.setLayout(mainLayout)

		### access preview area from consol ###

	def sizeHint(self):
		return QSize(1200,700)

	def execute_code(self, code_str):
		print("executing code...")
		if not code_str.strip():
			return  # Do nothing if the input is empty

		print("code executed!") 


def main():
	app = QApplication(sys.argv)
	
	window = IPythonWindow()
	window.setApp(WidgetPreviewApp())
	window.show()
	
	# Execute a string of code using the execute_code method to add a widget
	from textwrap import dedent
	code_to_execute = dedent("""\
	from PySide6.QtWidgets import *

	# Create a new QPushButton
	button = QPushButton("Click Me")
	app.layout().addWidget(button)
	""")
	window.textedit.setPlainText(code_to_execute)
	
	window.execute_code(code_to_execute)  # This will add a button to the layout

	help(RichJupyterWidget())

	sys.exit(app.exec())

if __name__ == "__main__":
	main()
