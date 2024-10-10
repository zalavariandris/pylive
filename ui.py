#pip install git+https://github.com/C3RV1/NodeGraphQt-PySide6


from core import Node
import types
from textwrap import dedent

import inspect
import sys
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pathlib import Path
from core import Graph, Node, TriggerInPort, TriggerOutPort

from datetime import datetime

from NodeGraphQt import NodeGraph, BaseNode

class AppContainer(QWidget):
	logChanged = Signal(str)
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setLayout(QHBoxLayout())
		self.label = QLabel(self)
		self.label.setText("<output>")
		self.layout().addWidget(self.label)

	def setCode(self, code:str):
		self.code = code

	def log(self, *messages):
		print("!!!!!!!!!!!!", messages)
		self.logChanged.emit(" ".join([str(msg) for msg in messages]))

	def execute(self):
		self.log("executing...")
		# create MainNode class
		if self.main_node:
			self.main_node.destroy()
		self.main_node = Node()
		self.global_vars = globals()
		self.local_vars = locals()

		import ticknode

		# ticknode.main(self.main_node, self)
		# self.main_node.out_ports['output'].subscribe(self.display)
		# try:
		# 	self.log("compiling...")
		# 	compiled_code = compile(self.code, "main_function", "exec")
		# 	self.log("done compiling")

		# 	try:
		# 		self.log("executing...")
		# 		exec(compiled_code, self.global_vars, self.local_vars)
		# 		self.main_function = self.local_vars["main"]
		# 		self.log("done executing")

		# 		try:
		# 			self.log("run 'main' function...")
		# 			self.main_function(self.main_node, self)
		# 			self.main_node.out_ports['output'].subscribe(self.display)
		# 			self.log("done running 'main' function")

		# 		except Exception as err:
		# 			self.log("error while running 'main' function:", err)

		# 	except Exception as err:
		# 		self.log("error while executing:", err)

		# except Exception as err:
		# 	self.log("error while compiling:", err)

		from PySide6.QtCore import QTimer



		def main(node, container):
			print("main evaluate")
			from PySide6.QtCore import QTimer
			node.output = node.triggerOut("output")

			k = 0
			def tick():
				nonlocal k
				node.output.trigger(k)
				k+=0

			timer = QTimer(container)
			timer.timeout.connect(tick)
			timer.start(1000/60)

			@node.event
			def on_destroy():
				nonlocal timer
				timer.stop()

		main(self.main_node, self)

	def display(self, props=None):
		self.label.setText(f"display [{datetime.now()}]: {str(props)}")

	def exit(self):
		if self.main_node:
			self.main_node.destroy()



from pathlib import Path
from highlighters import PythonSyntaxHighlighter
class CodeEditor(QWidget):
	codeChanged = Signal()
	def __init__(self, parent=None):
		super().__init__(parent)
		
		self.textEditor = QPlainTextEdit()
		self.textEditor.setFont(QFont("Operator Mono", 10))
		self.textEditor.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
		self.textEditor.setLineWrapMode(QPlainTextEdit.NoWrap)
		self.textEditor.highlighter = PythonSyntaxHighlighter(self.textEditor.document())

		self.setLayout(QVBoxLayout())
		self.layout().setContentsMargins(0,0,0,0)
		self.layout().addWidget(self.textEditor)

		self.textEditor.textChanged.connect(self.codeChanged.emit)

	def setCode(self, code:str):
		self.textEditor.setPlainText(code)

	def code(self):
		return self.textEditor.toPlainText()
		
	def lineNumberAreaPaintEvent(self, event):
		# You can extend this to add line numbers
		pass
		
	def resizeEvent(self, event):
		super().resizeEvent(event)


class AppEditor(QMainWindow):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		# Set window properties
		self.setWindowTitle("AppEditor")

		self.G = Graph("main")
		self.edgemap = {}
		self.nodemap = {}
		self.portmap = {}
		ticknode = self.G.node("ticknode")
		outlet = ticknode.outlet("out")
		prevnode = self.G.node("prevnode")
		inlet = prevnode.inlet("in")
		outlet.connect(inlet)

		# create central layout
		self.setCentralWidget(QWidget())
		self.centralWidget().setLayout(QVBoxLayout())

		# left pane
		self.leftpane = QWidget()
		self.leftpane.setLayout(QHBoxLayout())
		self.centralWidget().layout().addWidget(self.leftpane, 1)
		self.lefttabwidget = QTabWidget()
		self.leftpane.layout().addWidget(self.lefttabwidget)

		# right pane
		self.rightpane = QWidget()
		self.rightpane.setLayout(QVBoxLayout())
		self.centralWidget().layout().addWidget(self.rightpane, 1)

		# create toolbar
		toolbar = self.addToolBar("main")

		add_node_button = QPushButton("add")
		add_node_button.clicked.connect(self.add_node)
		toolbar.addWidget(add_node_button)

		restartButton = QPushButton("restart")
		restartButton.clicked.connect(self.restart)
		toolbar.addWidget(restartButton)

		# create grapheditor
		self.grapheditor = NodeGraph()

		for n in self.G.nodes:
			node = BaseNode()
			for port in n.outlets:
				outlet = node.add_output(port.name)
				self.portmap[port] = outlet

			for port in n.inlets:
				inlet = node.add_input(port.name)
				self.portmap[port] = inlet

			self.grapheditor.add_node(node)
			node.set_name(n.name)
			self.nodemap[n]=node

		for n in self.G.nodes:
			for outlet in n.outlets:
				for inlet in outlet.targets:
					self.portmap[outlet].connect_to(self.portmap[inlet])

		@self.G.event
		def on_node(n):
			node = BaseNode()
			for port in n.outlets:
				outlet = node.add_output(port.name)
				self.portmap[port] = outlet
			self.grapheditor.add_node(node)
			node.set_name(n.name)
			self.nodemap[n]=node


		self.lefttabwidget.addTab(self.grapheditor.widget, "graph")

		# create codeeditor
		self.codeeditor = CodeEditor()
		self.codeeditor.setCode("")
		self.codeeditor.codeChanged.connect(self.update)
		self.lefttabwidget.addTab(self.codeeditor, "code")

		# create appcontainer
		self.appcontainer = AppContainer()
		self.appcontainer.setCode("")
		self.appcontainer.logChanged.connect(self.setStatus)
		self.rightpane.layout().addWidget(self.appcontainer)
		

		# self.main_node = None
		
		# self.appcontainer.execute()
		# def update_app_code():
		# 	self.appcontainer.setCode(self.codeeditor.code())
		# 	self.appcontainer.execute()
		# self.codeeditor.codeChanged.connect(update_app_code)

		self.statusBar().showMessage("started")

	@Slot()
	def add_node(self):
		try:
			self.G.node("node")
		except AssertionError as err:
			print(err)

	def setStatus(self, msg):
		self.statusBar().showMessage(msg)
		
	def restart(self):
		self.rightpane.layout().removeWidget(self.appcontainer)
		self.appcontainer.exit()
		self.appcontainer = AppContainer()
		self.appcontainer.setCode(self.codeeditor.code())
		self.rightpane.layout().addWidget(self.appcontainer)
		self.appcontainer.execute()

	def setMainNode(self, node):
		self.mainNode = node


# def get_imported_modules():
# 	all_globals = list( globals().items() )
# 	for name, val in all_globals:
# 		if isinstance(val, types.ModuleType):
# 			yield val


if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = AppEditor()
	window.show()
	sys.exit(app.exec())