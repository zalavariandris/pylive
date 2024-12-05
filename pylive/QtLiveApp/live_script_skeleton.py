
from typing import *

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


class Placeholder(QLabel):
	def __init__(self, text, parent=None):
		super().__init__(text, parent=parent)
		self.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.setFrameStyle(QFrame.Shape.StyledPanel)


class SingletonException(Exception):
	...


class LiveScriptWindow(QWidget):
	# |---------LiveFramework----------|
	# |--menubar-----------------------|
	# | |----Editor----|---Preview---| |
	# | | cell1        | show widget | |
	# | | cell1        |             | |
	# | | ...          |---Terminal--| |
	# | |              |   log and   | |
	# | |              |   interact  | |
	# | |--------------|-------------| |
	# |--statusbar---------------------|


	_instance: Optional[Self] = None
	@classmethod
	def instance(cls) -> Self:
		"""
		Factory method to get the singleton instance of LiveScriptWindow.
		"""
		
		if LiveScriptWindow._instance is None:
			# Create the instance if it doesn't exist
			LiveScriptWindow._instance = cls.__new__(cls)
			super().__init__(LiveScriptWindow._instance, parent=None)
			LiveScriptWindow._instance.setupUI()
		return LiveScriptWindow._instance

	def __init__(self, parent: Optional[QWidget] = None) -> None:
		"""Disable direct instantiation. Use instance() method instead."""
		raise SingletonException("Singleon can cannot be instantiated directly. Use the 'instance()' static method!")

	def setupUI(self):
		self.setWindowTitle("Live (skeleton)")
		### Layout ###
		self._editor = QPlainTextEdit("[Editor]")
		self._preview = Placeholder("[Preview]")
		self._terminal = Placeholder("[Terminal]")

		self.splitter = QSplitter(Qt.Orientation.Horizontal)
		self.splitter.addWidget(self._editor)
		self.right_pane = QSplitter(Qt.Orientation.Vertical)
		self._preview_area = QFrame()
		self._preview_area_layout = QVBoxLayout()
		self._preview_area_layout.setContentsMargins(0,0,0,0)
		self._preview_area.setLayout(self._preview_area_layout)
		self._preview_area_layout.addWidget(self._preview)
		self.right_pane.addWidget(self._preview_area)
		self.right_pane.addWidget(self._terminal)
		self.setTerminalHeight(120)
		self.right_pane.setStretchFactor(0,1)
		self.right_pane.setStretchFactor(1,0)
		self.splitter.addWidget(self.right_pane)
		self.splitter.setSizes([
			self.splitter.width()//self.splitter.count() 
			for _ in range(self.splitter.count())
		])

		mainLayout = QVBoxLayout()
		mainLayout.setContentsMargins(0,0,0,0)
		mainLayout.setSpacing(0)
		mainLayout.addWidget(self.splitter)
		self.setLayout(mainLayout)

		### Statusbar ###
		statusbar = QStatusBar(self)
		statusbar.setSizeGripEnabled(False)
		mainLayout.addWidget(statusbar)
		statusbar.setSizePolicy(QSizePolicy.Policy.Minimum, 
			                    QSizePolicy.Policy.Maximum)
		self._statusbar = statusbar
		self._statusbar.hide() # hide statusbar by default. Will pop up if used.

		### MenuBar ###
		menubar = self.createDefaultMenuBar()
		mainLayout.setMenuBar(menubar)
		self._menubar = menubar

	def createDefaultMenuBar(self)->QMenuBar:
		menubar = QMenuBar(parent=self)
		menubar.setStyleSheet("""
			QMenuBar::item {
				padding: 0px 8px;  /* Adjust padding for the normal state */
			}
			QMenuBar::item:selected {  /* Hover state */
				padding: 0px 0px;  /* Ensure the same padding applies to the hover state */
			}
		""")

		""" View menu """
		view_menu = menubar.addMenu("View")
		zoom_in_action = QAction("Zoom In", self)
		zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)

		def increaseFontSize():
			font = QApplication.font()
			font.setPointSize(font.pointSize()+2)
			QApplication.setFont(font)

		def decreaseFontSize():
			font = QApplication.font()
			font.setPointSize(font.pointSize()-2)
			QApplication.setFont(font)

		zoom_in_action.triggered.connect(lambda: increaseFontSize())
		zoom_out_action = QAction("Zoom Out", self)
		zoom_out_action.triggered.connect(lambda: decreaseFontSize())
		zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)

		view_menu.addAction(zoom_in_action)
		view_menu.addAction(zoom_out_action)

		# Create a widget to add to the menu bar (e.g., a button)
		right_menu = QMenuBar(parent=menubar)
		live_toggle_action = QAction("live", parent=self)
		live_toggle_action.setCheckable(True)

		rightwidget = QWidget(parent=menubar)
		right_layout = QHBoxLayout()
		right_layout.setContentsMargins(1,0,1,0)
		rightwidget.setLayout(right_layout)
		live_toggle = QCheckBox("live", parent=self)
		live_toggle.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
		rightwidget.layout().addWidget(live_toggle)
		menubar.setCornerWidget(rightwidget)

		return menubar

	def statusBar(self)->QStatusBar:
		self._statusbar.show()
		return self._statusbar

	def setStatusBar(self, statusbar:QStatusBar|QWidget)->QStatusBar|QWidget:
		statusbar.setSizePolicy(QSizePolicy.Policy.Minimum, 
			                    QSizePolicy.Policy.Maximum)
		self.layout().replaceWidget(self._statusbar, statusbar)
		self._statusbar.show()
		return self._statusbar

	def menuBar(self)->QMenuBar:
		self._menubar.show()
		return self._menubar

	def setMenuBar(self, menubar:QMenuBar):
		self.layout().setMenuBar(menubar)
		self._menubar = menubar

	def preview(self)->QWidget:
		return self._preview

	def setPreview(self, preview:QWidget)->None:
		# clear preview area
		while self._preview_area_layout.count():
			item = self._preview_area_layout.takeAt(0)
			if widget:=item.widget():
				widget.deleteLater()
		self._preview_area_layout.addWidget(preview)
		self._preview = preview

	def editor(self)->QPlainTextEdit:
		return self._editor

	def setEditor(self, editor:QPlainTextEdit):
		self.splitter.replaceWidget(0, editor)
		self._editor = editor

	def terminal(self)->QWidget:
		return self._terminal

	def setTerminal(self, terminal:QWidget):
		self.right_pane.replaceWidget(1, terminal)
		self._terminal = terminal

	def setTerminalHeight(self, height:int):
		self.right_pane.setSizes([self.right_pane.height()-height, height])

	def sizeHint(self) -> QSize:
		return QSize(1200,600)

	def display(self, data:Any):
		match data:
			case QWidget():
				widget = cast(QWidget, data)
				self.setPreview(widget)
			case _:
				message_label = QLabel(f"{data}")
				self.setPreview(message_label)



def main():
	import sys
	app = QApplication(sys.argv)
	window = LiveScriptWindow.instance()
		
	# window.statusBar().showMessage("[StatusBar]")
	window.show()
	sys.exit(app.exec())

if __name__ == "__main__":
	main()
