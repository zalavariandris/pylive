
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from networkx import find_induced_nodes
# from pylive.QtLiveApp.live_script_skeleton import LiveScriptWindow
from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel
from pylive.NetworkXGraphEditor.nx_graph_selection_model import NXGraphSelectionModel
from pylive.NetworkXGraphEditor.nx_network_scene_outlet_to_inlet import NXNetworkScene
from pylive.NetworkXGraphEditor.nx_node_inspector_view import NXNodeInspectorView

from pylive.options_dialog import OptionDialog
from pylive.utils.unique import make_unique_name

def get_available_nodes():
	for name in dir(__builtins__):
		if not name.startswith("_"):
			item = getattr(__builtins__, name)
			if callable(item):
				yield name, item

	import pathlib
	for name in dir(pathlib):
		if not name.startswith("_"):
			item = getattr(pathlib, name)
			if callable(item):
				yield name, item

def get_inlets(fn:Callable):
	import inspect
	sig = inspect.signature(fn)
	for name, paramteter in sig.parameters.items():
		print("param name", name)
		yield name

class FunctionInspectorView(QWidget):
	...


class LivePythonGraphWindow(QWidget):
	def __init__(self, parent: QWidget|None=None) -> None:
		super().__init__(parent=parent)
		self.setWindowTitle("LiveGraph")
		main_layout = QVBoxLayout()
		self.setLayout(main_layout)

		self.graphmodel = NXGraphModel()
		self.selectionmodel = NXGraphSelectionModel(self.graphmodel)
		self.graphview = QGraphicsView()
		self.graphview.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
		self.graphview.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
		self.graphview.setRenderHint(QPainter.RenderHint.Antialiasing, True)
		self.graphview.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
		self.graphview.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

		self.graphscene = NXNetworkScene(self.graphmodel, self.selectionmodel)
		self.graphscene.setSelectionModel(self.selectionmodel)
		self.graphscene.setSceneRect(-9999,-9999,9999*2,9999*2)
		self.graphview.setScene(self.graphscene)

		self.inspector_panel = QWidget()
		self.inspector_panel.setLayout(QVBoxLayout())
		self.nodeinspector = NXNodeInspectorView()
		self.nodeinspector.setModel(self.graphmodel)
		self.nodeinspector.setSelectionModel(self.selectionmodel)
		self.inspector_panel.layout().addWidget(self.nodeinspector)

		def on_selection_changed(selected, deselected):
			if len(self.selectionmodel.selectedNodes()):
				self.nodeinspector.show()
			else:
				self.nodeinspector.hide()

		self.selectionmodel.selectionChanged.connect(on_selection_changed)

		self.graphscene.installEventFilter(self)

		splitter = QSplitter()
		splitter.addWidget(self.graphview)
		splitter.addWidget(self.inspector_panel)
		splitter.setSizes([splitter.width()//splitter.count() for idx in range(splitter.count())])
		main_layout.addWidget(splitter)

	def sizeHint(self) -> QSize:
		return QSize(900, 500)

	def eventFilter(self, watched: QObject, event: QEvent) -> bool:
		if watched == self.graphscene:
			if event.type() == QEvent.Type.GraphicsSceneMouseDoubleClick:
				available_nodes = {key: val for key, val in get_available_nodes()}
				dialog = OptionDialog(options=[_ for _ in available_nodes.keys()], title="Create Nodes", parent=self.graphview)
				result = dialog.exec()

				if result == QDialog.DialogCode.Accepted:
					if function_name:=dialog.optionValue():
						all_nodes = [str(_) for _ in self.graphmodel.nodes()]
						new_node_name = make_unique_name(function_name, all_nodes)
						fn = available_nodes[function_name]
						inlet_names = [_ for _ in get_inlets(fn)]
						print("inlet names:", inlet_names)
						self.graphmodel.addNode(new_node_name, inlets=get_inlets(fn), outlets=["result"])
				else:
					print("cancelled")

		return super().eventFilter(watched, event)





if __name__ == "__main__":
	app = QApplication()
	window = LivePythonGraphWindow()
	window.show()
	app.exec()
