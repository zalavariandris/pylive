import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat, QFont, QTextCursor
from PySide6.QtCore import QRegularExpression, QTimer

from pathlib import Path
from highlighters import PythonSyntaxHighlighter

class CodeEditor(QPlainTextEdit):
	def __init__(self, source_file=None, parent=None):
		super().__init__(parent)
		self.setFont(QFont("Operator Mono", 10))
		self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
		
		# Syntax highlighting
		self.highlighter = PythonSyntaxHighlighter(self.document())

		if source_file:
			source_code = Path(source_file).read_text()
			self.setPlainText(source_code)
		
	def lineNumberAreaPaintEvent(self, event):
		# You can extend this to add line numbers
		pass
		
	def resizeEvent(self, event):
		super().resizeEvent(event)


class PreviewWidget(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setLayout(QHBoxLayout())


from core import Node



import types
from textwrap import dedent
import inspect
class MainWindow(QWidget):
	def __init__(self, parent=None, project=None, definitions=[]):
		super().__init__(parent=parent)

		# self.main_script = Path(main_script).read_text()

		self.editor = CodeEditor()
		self.editor.setPlainText(dedent(dedent("""\
		from PySide6.QtWidgets import QLabel
		from core import Node

		class Main(Node):
			def __init__(self, window):
				self.message = "hello"
				self.label = QLabel()
				self.label.setText("hello")
				window.preview.layout().addWidget(self.label)

			def destroy(self):
				self.label.deleteLater()

		""")))

		self.editor.textChanged.connect(self.update)
		self.preview = PreviewWidget()
		self.consol = QLabel()

		self.setLayout(QHBoxLayout())
		editor_pane = QWidget()
		editor_pane.setLayout(QVBoxLayout())
		editor_pane.layout().addWidget(self.editor)
		editor_pane.layout().addWidget(self.consol)
		self.layout().addWidget(editor_pane, 1)
		self.layout().addWidget(self.preview, 1)

		self.restartButton = QPushButton("restart")
		self.restartButton.clicked.connect(self.restart)
		self.layout().addWidget(self.restartButton)
		
		# Set window properties
		self.setWindowTitle("Simple PySide6 Code Editor")
		self.setGeometry(200, 200, 800, 600)

		self.main_node = None
		self.update()
		

	def restart(self):
		raise NotImplementedError

	def on_reset(self, cb):
		self.reset_callbacks.append(cb)

	# def event(self, fn):
	# 	fn.__name__

	def update(self):
		code = self.editor.toPlainText()
		try:
			global_vars = {}
			local_vars = {'window': self}
			result = exec(code, globals(), locals())

			# collect node definitions
			node_definitions = []
			for key, value in locals().items():
				if inspect.isclass(value):
					if issubclass(value, Node):
						print(key)
						node_definitions.append(value)
			self.main_node_class = node_definitions[-1]
			print("main node:", self.main_node_class, Node)

			if self.main_node is not None:
				self.main_node.destroy()
			self.main_node = self.main_node_class(self)
			self.consol.setText(f"{self.main_node_class}")
			
		except Exception as err:
			self.consol.setText(str(err))

	def setMainNode(self, node):
		self.mainNode = node


# def get_imported_modules():
# 	all_globals = list( globals().items() )
# 	for name, val in all_globals:
# 		if isinstance(val, types.ModuleType):
# 			yield val


if __name__ == "__main__":
	import sys
	# for module in sys.modules:
	# 	print(module.__name__)
	# for module in get_imported_modules():
	# 	print(module)