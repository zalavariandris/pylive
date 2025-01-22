from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from pylive.utils.qtfactory import vboxlayout




class Element:
	def __init__(self):
		self.underlying = QWidget()
		self.children = dict()

	def addChildren(self, child:Self):
		

	def create(self)->QWidget|QLayout:
		...

	def setState(self, change:dict[str, object|None]):
		...

	def patch(self, *args, **kwargs)->None:
		...

	def render(self):
		...

	def __enter__(self):
		App.instance().push(self)

	def __exit__(self, exc_type, exc_val, exc_tb):
		App.instance().pop()


class Widget(Element):
	def create(self):
		return QWidget()


class VBoxLayout(Element):
	def __init__(self):
		self.underlying = QVBoxLayout()

	def __enter__(self):
		super().__enter__()

	def __exit__(self, exc_type, exc_val, exc_tb):
		super().__exit__(exc_type, exc_val, exc_tb)


class App:
	_instance = None
	def __init__(self, root):
		self.root:Element = root
		self.stack = []

	@staticmethod
	def instance()->'App|None':
		return App._instance

	def show(self):
		if self.root:
			return self.root.create().show()

	def push(self, item:Element):
		self.stack.append(item)

	def pop(self):
		return self.stack.pop()


class PushButton(Element):
	def __init__(self, text:str, on_pressed:Callable|None=None):
		self.text = text
		self.on_pressed = on_pressed
		self.underlying:QPushButton|None = None

	@override
	def create(self)->QWidget:
		self.underlying = QPushButton(self.text)
		if self.on_pressed:
			self.underlying.pressed.connect(self.on_pressed)
		return self.underlying

	@override
	def patch(self, text, on_pressed):
		assert self.underlying
		if text != self.text:
			self.text = text
			self.underlying.setText(text)

		if on_pressed != self.on_pressed:
			if self.on_pressed:
				self.underlying.pressed.disconnect(self.on_pressed)
			if on_pressed:
				self.underlying.pressed.connect(on_pressed)
			self.on_pressed = on_pressed


class Label(Element):
	def __init__(self, text:str):
		self.text = text
		self.underlying:QLabel|None = None

	def create(self):
		self.underlying = QLabel(self.text)
		return self.underlying

	def patch(self, text):
		assert self.underlying
		self.text = text
		self.underlying.setText(text)


class MyWidget(Widget):
	def render(self):
		with self:
			with VBoxLayout():
				PushButton("press me", on_pressed=lambda:print("pressed"))
				Label("hello")


if __name__ == "__main__":
	qapp = QApplication()


	lbl = Label("hello")

	App(root=MyWidget()).show()
	qapp.exec()