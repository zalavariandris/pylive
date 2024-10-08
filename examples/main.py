from definitions import TickNode, PrintNode

from PySide6.QtWidgets import QLabel
from core import Node

class Main(Node):
	def __init__(self, window):
		self.message = "hello"
		self.label = QLabel()
		self.label.setText("hello")
		window.preview.layout().addWidget(self.label)

	def destroy(self):
		self.label.deleteLater()

if __name__ == "__main__":
	node = Main()
	