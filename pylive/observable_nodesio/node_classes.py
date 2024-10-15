from core import Node, TriggerInPort, TriggerOutPort
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel

class TickNode(Node):
	def __init__(self, window):
		super().__init__(window)
		self.tickPort = self.triggerOut("tick")

		self.timer = QTimer()
		self.timer.timeout.connect(self.tick)
		self.timer.start(1000/60)

		self.tick_number = 0

	def tick(self):
		self.tickPort.trigger(f"hello {self.tick_number}")
		self.tick_number+=1

class PrintNode(Node):
	def __init__(self, window):
		super().__init__(window)
		self.input_port = self.triggerIn("in")
		self.input_port.on_trigger(self.update)

		self.label = QLabel()
		window.preview.layout().addWidget(self.label)

	def update(self, value=None):
		print(f"update {value}")
		self.label.setText(f"{value}")

from typing import NoReturn
import inspect
class Operator(Node):
	def __init__(self, fn, window):
		super().__init__(window)
		self.fn = fn
		signature = inspect.signature(self.fn)
		for name, param in signature.parameters.items():
			print(param.name,  param.annotation, param.kind, param.default)
			self.triggerIn(param.name)
		if signature.return_annotation in [NoReturn, None]:
			print("no return")
		else:
			self.triggerOut("out")

if __name__ == "__main__":
	tickNode = TickNode(window)
	printNode = PrintNode(window)
	tickNode.tickPort.connect(printNode.input_port)