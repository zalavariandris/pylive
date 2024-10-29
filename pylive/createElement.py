from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

def createElement(widgetType, layout=None, children=None, stretch=0):
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

if __name__ == "__main__":
	import sys
	h = createElement
	window = h(QWidget, layout=QHBoxLayout(), children=[
		(h(QLabel, text="hello"), 1),
		(h(QLabel, text="hello2"), 1)
	])

	app = QApplication(sys.argv)
	window.show()
	sys.exit(app.exec())