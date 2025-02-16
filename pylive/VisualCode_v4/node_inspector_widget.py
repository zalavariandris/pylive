from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from pylive.qt_components.tile_widget import TileWidget
from pylive.QtScriptEditor.script_edit import ScriptEdit

class NodeInspectorWidget(QFrame):
	def __init__(self, parent:QWidget|None=None):
		super().__init__( parent=parent)

		### NODEINSPECTOR
		self.setFrameShape(QFrame.Shape.StyledPanel)  # Styled panel for the frame
		self.setFrameShadow(QFrame.Shadow.Raised)
		inspector_header_tile = TileWidget()
		
		property_editor = QWidget()
		property_layout = QFormLayout()
		property_editor.setLayout(property_layout)
		property_layout.addRow("name", QLineEdit("hello"))
		property_layout.addRow("source", QLineEdit("def func..."))
		# property_editor.setModel(None)

		inspector_layout = QVBoxLayout()
		inspector_layout.addWidget(inspector_header_tile)
		inspector_layout.addWidget(property_editor)

		create_button = QPushButton("create")
		delete_button = QPushButton("delete")
		button_layout = QHBoxLayout()
		button_layout.addWidget(create_button)
		button_layout.addWidget(delete_button)
		inspector_layout.addLayout(button_layout)

		node_function_source_editor = ScriptEdit()
		inspector_layout.addWidget(node_function_source_editor)
		self.setLayout(inspector_layout)


	def insertField(self, idx:int, name:str, value:Any):
		...

	def indexFromName(self, name:str):
		...

	def removeField(self, idx):
		...


		

if __name__ == "__main__":
    app = QApplication()
    inspector = NodeInspectorWidget()
    inspector.show()
    app.exec()