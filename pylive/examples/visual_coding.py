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
from pylive.QtGraphEditor.option_dialog import OptionDialog

from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from datetime import datetime
import inspect

from pylive.QtScriptEditor.components.PygmentsSyntaxHighlighter import PygmentsSyntaxHighlighter

class Read:
	pass

class Write:
	pass


from typing import *
def sample_function(a: int, b: str, c: float = 5.0, props:List=[]) -> bool:
	return True


class ExpressionNodeItem(StandardNodeItem):
	def __init__(self, parent_graph: "GraphView"):
		# model reference
		# self.persistent_node_index:Optional[NodeRef] = None
		super().__init__(parent_graph)

		# widgets
		self.expressioneditor = EditableTextItem(self)
		self.highlighter = PygmentsSyntaxHighlighter(self.expressioneditor.document())
		self.expressioneditor.setPos(0,0)
		self.expressioneditor.setTextWidth(self.rect.width()-10)

		self.outputlabel = QGraphicsTextItem(self)
		self.outputlabel.setPos(0,30)

class SearchDialog(QDialog):
	def __init__(self, options, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Search and Navigate Options")
		self.setModal(True)
		# self.setWindowFlags(Qt.FramelessWindowHint)
		# Set border radius and background color with Qt Style Sheet
		self.setStyleSheet("""
			SearchDialog {
				border-radius: 15px;  /* Rounded corners */
			}
			QLineEdit {
				border-radius: 5px;
				padding: 5px;
			}
			QListWidget {
				border: none;
				border-radius: 5px;
				padding: 5px;
			}
		""")
		# Store the options
		self.options = options

		# Set up layout
		layout = QVBoxLayout(self)
		layout.setContentsMargins(5, 5, 5, 5)
		layout.setSpacing(10)

		self.move(QCursor.pos().x() - self.size().width() // 2, QCursor.pos().y() - 10)

		# Create search input field
		self.line_edit = QLineEdit(self)
		self.line_edit.setPlaceholderText("Search...")
		self.line_edit.textChanged.connect(self.update_list)  # Connect search to list update

		# Create list widget for displaying options
		self.list_widget = QListWidget(self)
		self.list_widget.addItems(self.options)  # Initially add all options
		self.list_widget.itemActivated.connect(self.item_selected)  # Connect item selection

		# Set size policy for automatic resizing
		self.list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
		self.list_widget.setMaximumHeight(200)  # Cap max height at 200

		# Add widgets to layout
		layout.addWidget(self.line_edit)
		layout.addWidget(self.list_widget)

		# Focus on the line edit when the dialog opens
		self.line_edit.setFocus()
		self.update_list_widget_height()

	def update_list(self):
		"""Filter and display items based on search text."""
		search_text = self.line_edit.text().lower()
		self.list_widget.clear()  # Clear current items

		# Add items that match the search text
		for option in self.options:
			if search_text in option.lower():
				item = QListWidgetItem(option)
				self.list_widget.addItem(item)

		# Select the first item automatically if there are any results
		if self.list_widget.count() > 0:
			self.list_widget.setCurrentRow(0)
		
		# Update dialog height to fit content
		self.update_list_widget_height()

	def update_list_widget_height(self):
		"""Adjust dialog height to fit content based on list items."""
		# Calculate height needed for list items, up to a max of 200px
		item_height = self.list_widget.sizeHintForRow(0)  # Approximate height of a single item
		list_height = min(item_height * self.list_widget.count(), 200)
		
		# Set the QListWidget's height to show only necessary items
		# self.list_widget.setFixedHeight(list_height)
		
		# Adjust the dialog's height to fit updated contents
		self.adjustSize()

	def item_selected(self, item):
		"""Handle item selection."""
		selected_option = item.text()
		print(f"Selected: {selected_option}")
		self.accept()  # Close the dialog

	def keyPressEvent(self, event):
		"""Handle Enter key for item selection."""
		if event.key() == Qt.Key.Key_Down:
			row = self.list_widget.currentRow() + 1
			if row >= self.list_widget.count():
				row = 0
			self.list_widget.setCurrentRow(row)

		elif event.key() == Qt.Key.Key_Up:
			row = self.list_widget.currentRow() - 1
			if row < 0:
				row = self.list_widget.count() - 1
			self.list_widget.setCurrentRow(row)

		elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
			if current_item := self.list_widget.currentItem():
				self.item_selected(current_item)  # Select the current item
		else:
			super().keyPressEvent(event)  # Pass other events to the base class

	@staticmethod
	def getItem(options):
		"""Show the search dialog and return selected option."""
		dialog = SearchDialog(options)
		if dialog.exec_() == QDialog.Accepted:
			current_item = dialog.list_widget.currentItem()
			if current_item:
				return current_item.text()
		return None


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

class ExpressionsGraphView(StandardGraphView):
	@override
	def nodeFactory(self, node:NodeRef)->QGraphicsItem:
		node_item = ExpressionNodeItem(parent_graph=self)
		
		node_item.expressioneditor.document().contentsChanged.connect(lambda: 
			self.onNodeEditorChange(node, node_item, ['name'])
		)

		node_item.positionChanged.connect(lambda: 
			self.onNodeEditorChange(node, node_item, ['posx', 'posy'])
		)

		return node_item

	@override
	def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
		expressions = ["print", "Path.read_text", "Path.write_text", "sample_function"]
		selected_expression = SearchDialog.getItem(expressions)
		if not selected_expression:
			return

		graph = self.model()
		if not graph or self.itemAt(event.position().toPoint()):
			return super().mouseDoubleClickEvent(event)

		clickpos = self.mapToScene(event.position().toPoint())
		node = graph.addNode(name="operator", posx=int(clickpos.x()), posy=int(clickpos.y()))
		graph.addInlet(node, name="in")
		graph.addOutlet(node, name="out")
			
	@override
	def onNodePropertyChange(self, node:NodeRef, node_item:QGraphicsItem, properties:List[str]|None):
		graph = self.model()
		node_item = cast(StandardNodeItem, node_item)
		if not graph:
			return

		if not properties or 'name' in properties:
			new_expression = node.graph().getNodeProperty(node, 'name')
			old_expression = node_item.expressioneditor.toPlainText()
			if new_expression != old_expression:
				node_item.expressioneditor.setPlainText(new_expression)

		if not properties or 'output' in properties:
			new_expression = node.graph().getNodeProperty(node, 'output')
			node_item.outputlabel.setPlainText(new_expression)

		if not properties or 'posx' in properties or 'posy' in properties:
			x = int(node.graph().getNodeProperty(node, 'posx'))
			y = int(node.graph().getNodeProperty(node, 'posy'))
			node_item.setPos(x,y)

	@override
	def onNodeEditorChange(self, node:NodeRef, node_item:QGraphicsItem, properties:List[str]|None):
		graph = self.model()
		node_item = cast(StandardNodeItem, self.index_to_item_map[node])
		if not graph:
			return

		if not properties or "name" in properties:
			graph.setNodeProperty(node, name=node_item.expressioneditor.toPlainText())

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
		self.graph.nodesPropertyChanged.connect(self.updateNodeBasedOnExpression)
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
		# self.graphview.installEventFilter(self)

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


	# def eventFilter(self, watched, event:QEvent)->bool:
	# 	IsGraphView = watched == self.graphview
	# 	IsDoubleClick = event.type() == 4
	# 	if IsGraphView:
	# 		print("capture event")
	# 	return False

	def updateNodeBasedOnExpression(self, nodes:List[NodeRef], properties:List[str]|None=None):
		graph = self.graph
		if not graph:
			return

		for node in nodes:
			if not properties or 'name' in properties:
				new_expression = node.graph().getNodeProperty(node, 'name')
				print("name changed")
				try:
					result = eval(new_expression)
				except Exception as e:
					result = e

				if isinstance(result, Exception):
					#update_inlets
					self.graph.removeInlets( list(self.graph.getNodeInlets(node) ))

					# update output
					import traceback
					tb = traceback.TracebackException.from_exception(result)
					graph.setNodeProperty(node, output=''.join(tb.format()))
				else:
					#update_inlets
					self.graph.removeInlets( list(self.graph.getNodeInlets(node) ))
					if callable(result):
						params = list(inspect.signature(result).parameters.values())
						for param in params:
							self.graph.addInlet(node, name=param.name)

					# update output
					content = str(result)
					if callable(result):
						params = list(inspect.signature(result).parameters.values())
						for param in params:
							content += f"\n{param.name}, {param.kind}"
					
					graph.setNodeProperty(node, output=content)

				

			
	def onModelChanged(self):
		self.compose()
		self.execute()
		...

	def compose(self):
		lines:List[str] = []
		for node in reversed(list(self.graph.dfs())):
			node_id = str(node._index)
			expression = self.graph.getNodeProperty(node, 'name')
			arguments = dict()
			for inlet in self.graph.getNodeInlets(node):
				arg_name = self.graph.getInletProperty(inlet, 'name')
				edges = list(self.graph.getInletEdges(inlet))
				if edges:
					source_node = self.graph.getEdgeSource(edges[-1])
					arguments[arg_name] = source_node._index


			lines.append( f"{node_id} = {expression}({", ".join(f"{key}={value}" for key, value in arguments.items())})" )
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