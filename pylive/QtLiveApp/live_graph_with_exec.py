# from pathlib import Path

# # definition2
# def read_page(page):
# 	return "html"+page

# def apply(items, fn):
# 	for item in items:
# 		yield fn(item)


# # Node1
# paths = [Path(".").glob("*")]

# # node2
# pages = [read_page(path) for path in paths]

# #node3
# apply(pages, lambda page: page.uppercase())


from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from pylive.QtLiveApp.live_script_skeleton import LiveScriptWindow
from pylive.QtGraphEditor.dag_graph_graphics_scene import DAGScene

class LiveGraphWindow(LiveScriptWindow):
	def setupUI(self):
		super().setupUI()

		self.scripteditor = self.editor()

		self.editor_layout = QVBoxLayout()
		self.editor_layout.addWidget(self.scripteditor)

		self.left = QWidget()
		self.left.setLayout(self.editor_layout)

		# self.graphview = QGraphicsView()
		# self.editor_layout.addWidget(self.graphview)
		self.setEditor(self.scripteditor)

if __name__ == "__main__":
	app = QApplication()
	window = LiveGraphWindow.instance()
	window.show()
	app.exec()
