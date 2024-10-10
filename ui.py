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

		# create test DATA
		self.G = Graph("main")
		self.views = {}
		ticknode = self.G.node("ticknode")
		outlet = ticknode.outlet("out")
		prevnode = self.G.node("prevnode")
		inlet = prevnode.inlet("in")
		outlet.connect(inlet)

		self.scripts = {
			"ticknode": """#ticknode""",
			"prevnode": """#prevnode"""
		}

		self.selection = QStringListModel(self)
		self.selection.setStringList([])

		@self.selection.rowsInserted.connect
		def nodes_added_to_selection(parent, first, last):
			print("rowsInserted", parent, first, last)

		@self.selection.rowsRemoved.connect
		def nodes_added_to_selection(parent, first, last):
			print("rowsRemoved", parent, first, last)

		@self.selection.rowsRemoved.connect
		def nodes_added_to_selection(parent, first, last):
			print("rowsRemoved", parent, first, last)

		# Set window properties
		self.setWindowTitle("AppEditor")
		self.resize(1500, 800)

		# create toolbar
		toolbar = self.addToolBar("main")

		add_node_button = QPushButton("create node")
		add_node_button.clicked.connect(lambda: self.G.node("node"))
		toolbar.addWidget(add_node_button)

		restartButton = QPushButton("restart")
		restartButton.clicked.connect(self.restart)
		toolbar.addWidget(restartButton)

		# crate statusbar
		self.statusBar().showMessage("started")

		# create central layout
		self.setCentralWidget(QWidget())
		self.centralWidget().setLayout(QHBoxLayout())

		# create codeeditor
		self.codeeditor = CodeEditor()
		self.codeeditor.setCode("")
		self.codeeditor.codeChanged.connect(self.update)
		
		# create grapheditor
		self.grapheditor = self.add_view(self.G)

		# create node list editor
		self.nodesheeteditor = QTableView()
		self.nodesmodel = QStandardItemModel()
        self.nodesmodel.setHorizontalHeaderLabels(['name', 'xpos', 'ypos', 'script'])
        for n in self.G.nodes:
        	name_item =   QStandardItem(n.name)
            posx_item =   QStandardItem(0)
            posy_item =   QStandardItem(0)
            script_item = QStandardItem(scripts[name])
        	self.model.appendRow([n.name, 0, 0, f"#{n.name}"])

		# create appcontainer
		self.appcontainer = AppContainer()
		self.appcontainer.setCode("")
		self.appcontainer.logChanged.connect(self.setStatus)

		# add editors to layout
		self.centralWidget().layout().addWidget(self.codeeditor, 1)
		self.centralWidget().layout().addWidget(self.nodesheeteditor, 1)
		self.centralWidget().layout().addWidget(self.grapheditor.widget, 1)
		self.centralWidget().layout().addWidget(self.appcontainer, 1)

	def add_view(self, obj):
		match obj:
			case Graph():
				grapheditor = NodeGraph()
				grapheditor.data = obj
				self.views[obj] = grapheditor

				# add nodes
				for n in obj.nodes:
					node = self.add_view(n)

				# connect nodes
				for n in obj.nodes:
					for outlet in n.outlets:
						for inlet in outlet.targets:
							self.views[outlet].connect_to(self.views[inlet])

				# observer model
				@obj.event
				def on_node(n):
					self.add_view(n)

				#listen to view events
				@grapheditor.port_connected.connect
				def connect_ports(inlet, outlet):
					print(f"user connected ports: {outlet} to {inlet}")
					outlet.data.connect(inlet.data)

				@grapheditor.port_disconnected.connect
				def disconnect_ports(inlet, outlet):
					print(f"user disconnected ports: {outlet} to {inlet}")
					outlet.data.disconnect(inlet.data)

				# Correctly connect the selection changed signal
				@grapheditor.node_selection_changed.connect
				def select_node(nodes_selected, nodes_unselected):
					if nodes_selected:
						n = nodes_selected[0].data  # Ensure this retrieves the correct node data
						self.selection.setStringList([n.name])
						print(f"Selected Node: {n.name}")  # Debug output to confirm selection

					
				return grapheditor

			case Node():
				node = BaseNode()
				node.data = obj
				self.views[obj]=node
				for p in obj.outlets:
					self.add_view(p)

				for p in obj.inlets:
					self.add_view(p)

				self.views[obj.graph].add_node(node)
				node.set_name(obj.name)
				return node

			case TriggerOutPort():
				outlet = self.views[obj.node].add_output(obj.name)
				outlet.data = obj
				self.views[obj] = outlet
				return outlet
			case TriggerInPort():
				inlet = self.views[obj.node].add_input(obj.name)
				inlet.data = obj
				self.views[obj] = inlet
				return inlet

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