from ast import MatchSingleton
from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

import sys
from IPython.core.interactiveshell import InteractiveShell
from io import StringIO

class NotebookPreview(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		# self.setObjectName("NotebookPreview")

		# Initialize an InteractiveShell instance
		self.shell = InteractiveShell.instance()

		# Layout for the widget
		layout = QVBoxLayout(self)

		preview = QWidget()
		preview.setObjectName("NotebookPreview")
		preview.setLayout(QVBoxLayout())
		layout.addWidget(preview)

		# Create a QTextEdit for output display
		self.output_display = QTextEdit(self)
		self.output_display.setReadOnly(True)
		layout.addWidget(self.output_display)

	def execute(self, code):
		print("execute", code)
		"""Execute the code entered in the QLineEdit."""
		if not code.strip():
			return  # Do nothing if the input is empty

		# Redirect stdout and stderr
		old_stdout = sys.stdout
		old_stderr = sys.stderr
		sys.stdout = StringIO()
		sys.stderr = StringIO()

		self.output_display.clear()
		try:
			# Execute the code
			result = self.shell.run_cell(code)
			stdout_content = sys.stdout.getvalue()
			stderr_content = sys.stderr.getvalue()

			# Display output or errors
			if result.error_in_exec is not None:
				self.output_display.append(f"Error:\n{stderr_content}")
			else:
				self.output_display.append(stdout_content)
		except Exception as e:
			self.output_display.append(f"Exception: {str(e)}")
		finally:
			# Restore stdout and stderr
			sys.stdout = old_stdout
			sys.stderr = old_stderr


if __name__ == "__main__":
	from pylive.QtScriptEditor.script_edit import ScriptEdit
	app = QApplication()
	def execute_cell(index:QPersistentModelIndex):
		print("execute_cell", index.data())


	shell = InteractiveShell.instance()

	# Main Layout
	window = QWidget()
	mainLayout = QHBoxLayout()
	mainLayout.setContentsMargins(0,0,0,0)

	cells_panel = QWidget()
	cells_layout = QVBoxLayout()
	cells_layout.addStretch()
	cells_layout.setContentsMargins(0,0,0,0)
	cells_panel.setLayout(cells_layout)

	cells = QStandardItemModel(parent=app)
	def addCellItems(parent:QModelIndex, first, last):
		for row in range(first, last+1):
			print("add cell items", row)
			cell_layout = QVBoxLayout()
			# cell_layout.setSpacing(0)
			cell_layout.setContentsMargins(0,0,0,0)
			index = QPersistentModelIndex(cells.index(row, 0))
			code = index.data(Qt.ItemDataRole.DisplayRole)
			script_edit = ScriptEdit()
			script_edit.setPlainText(code)
			cell_layout.addWidget(script_edit)

			btn = QPushButton("+")
			btn.clicked.connect(lambda row=row: (
				print("btn clicked"),
				cells.insertRow(row+1, QStandardItem("#code"))
			))
			cell_layout.addWidget( btn )
			cells_layout.insertLayout(row, cell_layout)
			# script_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
			script_edit.textChanged.connect(lambda index=index: 
				cells.setData(index, script_edit.toPlainText()),
			)

	window.setLayout(mainLayout)
	splitter = QSplitter()
	mainLayout.addWidget(splitter)

	# Lef cells
	splitter.addWidget(cells_panel)

	notebook_preview = NotebookPreview()
	splitter.addWidget(notebook_preview)

	splitter.setSizes([400,400])
	
	# script_edit.textChanged.connect(lambda: (
	# 	notebook_preview.execute( script_edit.toPlainText() )
	# ))

	cells.rowsInserted.connect(addCellItems)
	from textwrap import dedent
	cells.insertRow(0, QStandardItem(dedent("""\
	# setup
	from PySide6.QtWidgets import *

	def getPreview():
		for w in QApplication.allWidgets():
			if w.objectName() == "NotebookPreview":
				return w
				
	prev = getPreview()
	print(prev)

	lbl = QLabel("hello")
	prev
	""")))
	cells.insertRow(1, QStandardItem("# live"))

	def onDataChanged(topLeft, bottomright, roles):
		for row in range(topLeft.row(), bottomright.row()+1):
			idx = cells.index(row, 0)
			code = idx.data(Qt.ItemDataRole.DisplayRole)
			notebook_preview.execute(code)

	cells.dataChanged.connect(onDataChanged)

	prev = QApplication.instance().findChild(QWidget, "NotebookPreview")
	print(prev)

	window.show()
	app.exec()