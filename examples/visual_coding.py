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

class ExpressionNodeItem(NodeGraphicsItem):
		def __init__(self, parent_graph: "GraphView"):
			# model reference
			# self.persistent_node_index:Optional[NodeRef] = None
			super().__init__(parent_graph)

			# widgets
			self.expressioneditor = EditableTextItem(self)
			self.expressioneditor.setPos(0,0)
			self.expressioneditor.setTextWidth(self.rect.width()-10)

			self.outputlabel = QGraphicsTextItem()
			self.outputlabel.setPos(0,30)
			self.outputlabel.setTextWidth(self.rect.width()-10)

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
		graph = self.model()
		if graph and not self.itemAt(event.position().toPoint()):
			clickpos = self.mapToScene(event.position().toPoint())
			node = graph.addNode(expression="""print""", posx=int(clickpos.x()), posy=int(clickpos.y()))
			graph.addInlet(node, name="in")
			graph.addOutlet(node, name="out")
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
				node_item.outputlabel.setPlainText(new_output)

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
		self.graph.nodesPropertyChanged.connect(self.onNodesPopertyChanged)
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

	def onNodesPopertyChanged(self, nodes:List[NodeRef], properties:List[str]):
		for node in nodes:
			if not properties or 'expression' in properties:
				expression = self.graph.getNodeProperty(node, 'expression')
				print("expression changed", expression)
				
				try:
					result = eval(expression)
					self.graph.setNodeProperty(node, output=str(result))
					print(f"{result} = {expression}")
				except Exception as err:
					print(err)
				# global_vars = globals()
				# print(global_vars)
			
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