from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

def createWidget(widgetType, layout=None, children=None, stretch=0):
	"""
	A helper function to create PySide widgets with layouts and children.

	Parameters:
	- widgetType: The type of the QWidget (e.g., QWidget, QVBoxLayout, QHBoxLayout).
	- layout: An optional layout to set for the widget.
	- children: A list of tuples, where each tuple contains:
		(child_widget, stretch, tab_name) - 'tab_name' only for QTabWidget.
	- stretch: Stretch factor for the widget (optional).
	"""
	widget = widgetType()

	if layout:
		widget.setLayout(layout)

	if children:
		for child in children:
			if isinstance(layout, (QVBoxLayout, QHBoxLayout)):
				child_widget, child_stretch = child[:2]
				layout.addWidget(child_widget, child_stretch)
			elif isinstance(widget, QTabWidget):
				child_widget, tab_name = child
				widget.addTab(child_widget, tab_name)
	
	return widget

def createAction(label:str, callback:Callable|None=None):
	action = QAction(label)
	if callback:
		action.triggered.connect(lambda: callback())
	else:
		action.setEnabled(False)
	return action

def createSeparator():
	separator = QAction()
	separator.setSeparator(True)
	return separator

def createMenu(label:str, actions:List[QAction]):
	menu = QMenu(label)
	for action in actions:
		action.setParent(menu)
		menu.addAction(action)
	return menu

class Panel(QWidget):
	def __init__(self, direction=QBoxLayout.Direction.LeftToRight, children=[], menuBar=None):
		super().__init__(parent=None)
		self.setLayout(QBoxLayout(direction))
		self.layout().setContentsMargins(0,0,0,0)
		if menuBar:
			self.layout().setMenuBar(menuBar)

		for child in children:
			self.layout().addWidget(child)

class Splitter(QSplitter):
	def __init__(self, orientation=Qt.Orientation.Horizontal, children=[]):
		super().__init__(orientation=orientation, parent=None)
		for child in children:
			self.addWidget(child)
			
		self.setSizes([self.width()//self.count() for i in range(self.count())])		
		self.setStyleSheet("QSplitter::handle{background: palette(window);}");

if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)

	from pylive import livescript
	main_widget = Splitter(orientation=Qt.Orientation.Horizontal, children=[
		QLabel("split1"),
		QLabel("split2")
	])
	# livescript.display(main_widget)
	
	h = createWidget
	window = h(QWidget, layout=QHBoxLayout(), children=[
		(h(QLabel, text="hello"), 1),
		(h(QLabel, text="hello2"), 1)
	])

	
	window.show()
	sys.exit(app.exec())
