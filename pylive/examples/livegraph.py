from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.QtGraphEditor.GraphModel import GraphModel, NodeIndex
from pylive.QtScriptEditor.ScriptEdit import ScriptEdit
from pylive.QtGraphEditor.GraphView import GraphView
from pylive.QtGraphEditor.GraphTableView import GraphTableView

class AppWidget(QWidget):
	def evaluate(self, script:str):
		pass

class LiveGraph(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		# setup window
		self.setWindowTitle("LiveScript")
		self.resize(1240,600)

		# setup model
		self.scriptgraph = GraphModel()
		self.node_selection = QItemSelectionModel(self.scriptgraph.nodes)
		self.node_selection.currentRowChanged.connect(
			lambda current, previous: self.on_current_changed(NodeIndex(current), NodeIndex(previous))
		)

		self.scriptgraph.nodes.rowsInserted.connect(self.joinScripts)
		self.scriptgraph.nodes.rowsRemoved.connect(self.joinScripts)
		self.scriptgraph.nodes.dataChanged.connect(self.joinScripts)
		self.scriptgraph.edges.rowsInserted.connect(self.joinScripts)
		self.scriptgraph.edges.rowsRemoved.connect(self.joinScripts)
		self.scriptgraph.nodes.dataChanged.connect(self.joinScripts)
		
		# setup views
		self.graph_edit = GraphView()
		self.graph_edit.setModel(self.scriptgraph)
		self.graph_edit.setNodesSelectionModel(self.node_selection)

		self.script_edit = ScriptEdit()
		self.script_edit.textChanged.connect(self.on_text_changed)

		# self.table_view = GraphTableView()
		# self.table_view.setModel(self.scriptgraph)

		self.app_widget = AppWidget()

		self.composed_script_widget = ScriptEdit()
		# self.composed_script_widget.setReadOnly(True)

		"""setup layout"""
		self.splitter = QSplitter(self)
		self.splitter.addWidget(self.graph_edit)
		# self.splitter.addWidget(self.table_view)
		self.splitter.addWidget(self.script_edit)
		output_tabs = QTabWidget()
		output_tabs.addTab(self.app_widget, "Preview")
		output_tabs.addTab(self.composed_script_widget, "Output Script")
		self.splitter.addWidget(output_tabs)
		self.splitter.setSizes([self.width()//self.splitter.count() for i in range(self.splitter.count())])

		self.setLayout(QHBoxLayout())
		self.layout().setContentsMargins(0,0,0,0)
		self.menubar = QMenuBar()

		self.layout().addWidget(self.splitter)
		self.setupMenuBar()

	def setupMenuBar(self):
		# setup menubar
		self.menubar = QMenuBar()
		self.menubar.setStyleSheet("""
			QMenuBar::item {
				padding: 0px 8px;  /* Adjust padding for the normal state */
			}
			QMenuBar::item:selected {  /* Hover state */
				padding: 0px 0px;  /* Ensure the same padding applies to the hover state */
			}
		""")
		self.layout().setMenuBar(self.menubar)

		# setup file actions
		open_action = QAction("Open", self)
		open_action.triggered.connect(self.open)
		open_action.setShortcut(QKeySequence(Qt.Key.Key_Control | Qt.Key.Key_S))
		save_action = QAction("Save", self)
		save_action.triggered.connect(self.save)
		save_action.setShortcut(QKeySequence(Qt.Key.Key_Control | Qt.Key.Key_S))

		# node actions
		add_node_action = QAction("new node", self)
		add_node_action.triggered.connect(self.createNode)
		delete_node_action = QAction("delete selected", self)

		# setup filemenu
		file_menu  = self.menubar.addMenu("File")
		file_menu.addAction(open_action)
		file_menu.addAction(save_action)

		# setup create
		create_menu  = self.menubar.addMenu("Create")
		create_menu.addAction(add_node_action)
		create_menu.addAction(delete_node_action)

	def on_current_changed(self, current:NodeIndex, previous:NodeIndex):
		if current and current.isValid():
			node_attributes = self.scriptgraph.getNode(current)
			the_script = self.scriptgraph.nodes.data(current, Qt.ItemDataRole.UserRole+1)
			self.script_edit.setReadOnly(False)
			self.script_edit.setPlainText(the_script)
		else:
			self.script_edit.setPlainText("")
			self.script_edit.setReadOnly(True)

	def on_text_changed(self):
		script = self.script_edit.toPlainText()
		current = self.node_selection.currentIndex()
		if current and current.isValid():
			self.scriptgraph.nodes.setData(current, script, Qt.ItemDataRole.UserRole+1)

	def joinScripts(self):
		joined = ""
		for node in reversed(list(self.scriptgraph.dfs())):
			node_name = self.scriptgraph.getNode(node)["name"]
			node_script = self.scriptgraph.nodes.data(node, Qt.ItemDataRole.UserRole+1)
			joined += f"\n#%% {node_name}\n" + str(node_script) + "\n"
		self.composed_script_widget.setPlainText(joined)

	def createNode(self):
		node = self.scriptgraph.addNode("<new node>", 0,0, "#the script")
		self.scriptgraph.addInlet(node, "prev")
		self.scriptgraph.addOutlet(node, "next")
		self.scriptgraph.nodes.setData(node, "#THE SCRIPT ROLE", Qt.ItemDataRole.UserRole+1)

	def open(self):
		pass

	def save(self):
		pass


if __name__ == "__main__":
	from textwrap import dedent
	import pylive
	import sys
	import subprocess
	app = QApplication(sys.argv)
	window = LiveGraph()


	window.show()
	sys.exit(app.exec())