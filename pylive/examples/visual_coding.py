from pylive.QtGraphEditor.graphmodel_databased import (
	GraphModel,
	NodeRef, InletRef, OutletRef, EdgeRef
)

from pylive.QtGraphEditor.graphview_databased import (
	GraphView, NodeGraphicsItem,
	StandardGraphView, StandardNodeItem,
	EditableTextItem
)

from pylive.QtScriptEditor.ScriptEdit import ScriptEdit
from pylive.logwindow import LogWindow

from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from datetime import datetime
import inspect

from typing import *
def sample_function(a: int, b: str, c: float = 5.0, props:List=[]) -> bool:
	return True

class ExpressionNodeItem(NodeGraphicsItem):
		def __init__(self, parent_graph: "GraphView"):
			# model reference
			# self.persistent_node_index:Optional[NodeRef] = None
			super().__init__(parent_graph)

			# widgets
			self.expressioneditor = EditableTextItem(self)
			self.expressioneditor.setPos(0,0)
			self.expressioneditor.setTextWidth(self.rect.width()-10)

			self.outputlabel = QGraphicsTextItem(self)
			self.outputlabel.setPos(0,30)
			# self.outputlabel.setTextWidth(self.rect.width()*2)
			self.outputlabel.setPlainText("outputlabel")

		@override
		def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
			# Enable editing subitems on double-click
			"""parent node must manually cal the double click event,
			because an item nor slectable nor movable will not receive press events"""

			# Check if double-click is within the text item’s bounding box
			if self.expressioneditor.contains(self.mapFromScene(event.scenePos())):
				# Forward the event to nameedit if clicked inside it
				self.expressioneditor.mouseDoubleClickEvent(event)
			else:
				print("NodeItem->mouseDoubleClickEvent")
				super().mouseDoubleClickEvent(event)



class OptionDialog(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Choose an Option")
		self.setModal(True)  # Set dialog to be modal

		# Create layout
		layout = QVBoxLayout()

		# Instruction label
		label = QLabel("Please choose one of the following options:")
		layout.addWidget(label)

		options = [
			"print", "Path.read_text", "Path.write_text", "sample_function"
		]

		# Button group for options
		self.button_group = QButtonGroup(self)
		for option in options:
			radio_button = QRadioButton(option)
			self.button_group.addButton(radio_button)
			layout.addWidget(radio_button)

		# OK and Cancel buttons
		button_layout = QHBoxLayout()
		ok_button = QPushButton("OK")
		cancel_button = QPushButton("Cancel")
		button_layout.addWidget(ok_button)
		button_layout.addWidget(cancel_button)

		# Connect buttons
		ok_button.clicked.connect(self.accept)
		cancel_button.clicked.connect(self.reject)

		self.nodelist_model = QStringListModel(options)
		self.selectionmodel = QItemSelectionModel(self.nodelist_model)

		self.filtered_model = QSortFilterProxyModel(self)
		self.filtered_model.setSourceModel(self.nodelist_model)

		self.lineedit = QLineEdit()
		self.listview = QListView()
		self.listview.setModel(self.nodelist_model)
		self.listview.setSelectionModel(self.selectionmodel)
		self.lineedit.textChanged.connect(self.filter_items)

		layout.addWidget(self.lineedit)
		layout.addWidget(self.listview)
		layout.addLayout(button_layout)

		self.setLayout(layout)

	def filter_items(self):
		# Get the current text from the lineedit
		filter_text = self.lineedit.text()
		
		# Apply the filter on the source model
		self.filtered_model.setFilterFixedString(filter_text)

	def get_selected_option(self):
		"""Return the selected option text or None if no option is selected."""
		if self.selectionmodel.hasSelection():
			return self.selectionmodel.currentIndex().data()
		return None

	@staticmethod
	def getOption(parent=None):
		"""Static method to open dialog and return selected option."""
		dialog = OptionDialog(parent)
		result = dialog.exec()
		return dialog.get_selected_option() if result == QDialog.DialogCode.Accepted else None

class ExpressionsGraphView(GraphView):
	@override
	def nodeFactory(self, node:NodeRef)->QGraphicsItem:
		node_item = ExpressionNodeItem(parent_graph=self)
		
		node_item.expressioneditor.document().contentsChanged.connect(lambda: 
			self.onNodeEditorChange(node, node_item, ['expression'])
		)

		node_item.positionChanged.connect(lambda: 
			self.onNodeEditorChange(node, node_item, ['posx', 'posy'])
		)

		return node_item

	@override
	def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
		selected_expression = OptionDialog.getOption()
		if not selected_expression:
			return

		graph = self.model()
		if graph and not self.itemAt(event.position().toPoint()):
			clickpos = self.mapToScene(event.position().toPoint())
			node = graph.addNode(expression=selected_expression, posx=int(clickpos.x()), posy=int(clickpos.y()))
			expression = graph.getNodeProperty(node, 'expression')
			try:
				result = eval(expression)
				params = list(inspect.signature(result).parameters.values())

				# update output label
				content = f"{result}"
				graph.setNodeProperty(node, output=str(result))

				# setup inlets
				for param in params:
					graph.addInlet(node, name=param.name)

				# setup outlets
				graph.addOutlet(node, name="out")

			except Exception as err:
				graph.setNodeProperty(node, output=f"Error: {err}")
				print(f"Error in node: {node}: {err}")


			# graph.addInlet(node, name="in")
			# graph.addOutlet(node, name="out")
		else:
			return super().mouseDoubleClickEvent(event)

	@override
	def onNodePropertyChange(self, node:NodeRef, node_item:QGraphicsItem, properties:List[str]|None):
		graph = self.model()
		node_item = cast(ExpressionNodeItem, node_item)
		if not graph:
			return

		if not properties or 'expression' in properties:
			new_expression = node.graph().getNodeProperty(node, 'expression')
			old_expression = node_item.expressioneditor.toPlainText()
			if new_expression != old_expression:
				node_item.expressioneditor.setPlainText(new_expression)

		if not properties or 'output' in properties:
			new_output = node.graph().getNodeProperty(node, 'output')
			old_output = node_item.outputlabel.toPlainText()
			if new_output != old_output:
				node_item.outputlabel.setPlainText(f"{new_output}")

		if not properties or 'posx' in properties or 'posy' in properties:
			x = int(node.graph().getNodeProperty(node, 'posx'))
			y = int(node.graph().getNodeProperty(node, 'posy'))
			node_item.setPos(x,y)

	@override
	def onNodeEditorChange(self, node:NodeRef, node_item:QGraphicsItem, properties:List[str]|None):
		graph = self.model()
		node_item = cast(ExpressionNodeItem, self.index_to_item_map[node])
		if not graph:
			return

		if not properties or "expression" in properties:
			graph.setNodeProperty(node, expression=node_item.expressioneditor.toPlainText())

		if not properties or 'posx' in properties or 'posy' in properties:
			graph.blockSignals(True)
			graph.setNodeProperty(node, posx=int(node_item.x()))
			graph.setNodeProperty(node, posy=int(node_item.y()))
			graph.blockSignals(False)
			graph.nodesPropertyChanged.emit([node], ['posx', 'posy'])


from textwrap import dedent
class MainWindow(QWidget):
	def __init__(self, parent: Optional[QWidget]=None) -> None:
		super().__init__(parent)

		# setup window
		self.setWindowTitle("VisualCoding")

		# self.terminal = sys.stdout
		# sys.stdout = self

		# setup models
		self.graph = GraphModel()
		self.graph.nodesAdded.connect(self.onModelChanged)
		# self.graph.nodesPropertyChanged.connect(self.onNodesPopertyChanged)
		self.graph.nodesPropertyChanged.connect(self.onModelChanged)
		self.graph.nodesRemoved.connect(self.onModelChanged)
		self.graph.edgesAdded.connect(self.onModelChanged)
		self.graph.edgesRemoved.connect(self.onModelChanged)

		self.definitions = QStringListModel()
		self.definitions.setStringList([
			dedent("""\
				def read_text(path:Path)->str:
					return "# Hello file content"
			"""),
			dedent("""\
				def markdown_to_html(markdown:str)->str:
					return "<h1>Hello file content</h1>"
			"""),
			dedent("""\
				def write_text(content:str, path:Path)->None:
					Path(path).write_text(content)
			""")
		])

		#setup views
		self.statusBar = QStatusBar(self)
		self.definitionseditor = ScriptEdit()
		self.definition_list_view = QListView()
		self.definition_list_view.setModel(self.definitions)
		self.graphview = ExpressionsGraphView()
		self.graphview.setModel(self.graph)
		self.exportscript_view = QPlainTextEdit()
		doc = self.exportscript_view.document()
		font = doc.defaultFont();
		font.setFamily("Courier New");
		self.exportscript_view.document().setDefaultFont(font)
		self.preview = QWidget()
		self.logwindow = LogWindow()

		"""setup layout"""
		self.splitter = QSplitter(self)
		definition_tabs = QTabWidget()
		definition_tabs.addTab(self.definition_list_view, "All Definitions")
		definition_tabs.addTab(self.definitionseditor, "Definition")
		self.splitter.addWidget(definition_tabs)
		self.splitter.addWidget(self.graphview)
		output_tabs = QTabWidget()
		output_tabs.addTab(self.preview, "Output Preview")
		output_tabs.addTab(self.exportscript_view, "Output Script")
		self.splitter.addWidget(output_tabs)
		self.splitter.addWidget(self.logwindow)
		self.splitter.setSizes([self.width()//self.splitter.count() for i in range(self.splitter.count())])

		# layout
		mainLayout = QVBoxLayout(self)
		self.setLayout(mainLayout)
		mainLayout.addWidget(self.splitter)
		mainLayout.addWidget(self.statusBar)
		self.statusBar.showMessage("started")

		# center window on primary screen
		screen = QApplication.primaryScreen()
		width = int(screen.availableSize().width()*0.9)
		height = int(width* 1/2.9)
		self.resize(width, height)
		self.move( (screen.availableSize().width()-width)//2, (screen.availableSize().height()-height)//2-height//16)

	# def patchInlets(self, node, function):
	# 	raise NotImplementedError()
	# 	# patch inlets
	# 	params = list(inspect.signature(result).parameters.values())
	# 	inlets = list(self.graph.getNodeInlets(node))
	# 	# if param_names != inlet_names:
	# 	# 	self.graph.removeInlets()
	# 	print(f"patch node inlets: {inlets}=>{params}")

	# 	change = {
	# 		'added':[],
	# 		'removed':[],
	# 		'changed': []
	# 	}
	# 	for param, inlet in reversed(list(zip_longest(params, inlets, fillvalue=None))):
	# 		if param is None and inlet is not None:
	# 			change['removed'].append(inlet)
	# 		elif inlet is None and param is not None:
	# 			change['added'].append(param.name)
	# 		elif param is not None and inlet is not None and self.graph.getInletProperty(inlet, 'name') != param.name:
	# 			change['changed'].append((inlet, param.name))

	# 		print(" +", change['added'])
	# 		print(" -", change['removed'])
	# 		print("!=", change['changed'])


	# def onNodesPopertyChanged(self, nodes:List[NodeRef], properties:List[str]):
	# 	...
	# 	from itertools import zip_longest
	# 	sentinel = object()

	# 	for node in nodes:
	# 		if not properties or 'expression' in properties:
	# 			expression = self.graph.getNodeProperty(node, 'expression')
	# 			print("expression changed", expression)
				
	# 			try:
	# 				result = eval(expression)
	# 				content = f"{result}"
	# 				for param in inspect.signature(result).parameters.values():
	# 					content+=f"\n {param.name}:{param.annotation}={param.default}"

	# 				self.graph.setNodeProperty(node, output=str(result)+f"\n{content}")
	# 				print(f"{result} = {expression}")

	# 			except Exception as err:
	# 				self.graph.setNodeProperty(node, output=f"Error: {err}")
	# 				print(f"Error in node: {node}: {err}")
			
	def onModelChanged(self):
		self.compose()
		self.execute()

	def compose(self):
		lines:List[str] = []
		for node in reversed(list(self.graph.dfs())):
			name = str(node._index)
			expression = self.graph.getNodeProperty(node, 'expression')
			lines.append( f"{name} = {expression}" )
		script = "\n".join(lines)
		self.exportscript_view.setPlainText(script)

	def execute(self):
		...
		# print("execute")


if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	sys.exit(app.exec())