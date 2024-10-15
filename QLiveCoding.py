from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from pathlib import Path

from typing import *
from types import FunctionType
current_window = None

def get_current_window():
	return current_window

class LiveCode(QWidget):
	def __init__(self, parent=None) -> None:
		super().__init__(parent)
		self.setLayout(QVBoxLayout())

		# file watching
		self.watchers = dict()

		# animation frame
		self.animationFrameHandles = []
		self.timer = QTimer()
		self.timer.timeout.connect(self.handleAnimationFrames)
		self.timer.start(1000/60)

		global current_window
		current_window = self

	@staticmethod
	def current():
		return globals().get("current_window")  # Access global scope using globals()

	def on_watch(self, file:Path):
		def watch_file(cb):
			watcher = QFileSystemWatcher()
			watcher.addPath(str(file))
			self.watchers[(file, cb)] = watcher


			watcher.fileChanged.connect(cb)
			cb()

		return watch_file

	def handleAnimationFrames(self):
		for cb in self.animationFrameHandles:
			cb()

	def on_animate(self, cb:Callable):
		self.animationFrameHandles.append(cb)

def find_main_function(local_vars)->Optional[FunctionType]:
	main_fn = None
	for name, value in reversed(local_vars.items()):
		if name=="main" and isinstance(value, FunctionType):
			main_fn = value
	return main_fn

if __name__ == "__main__":
	import sys
	from datetime import datetime
	
	app = QApplication(sys.argv)
	window = LiveCode()
	label = QLabel()
	window.layout().addWidget(label)


	cache_main_function = None
	@window.on_watch("parse_jupyter_notebook.py")
	def on_parse_changed():
		print("current window before reload:", LiveCode.current())  # Check current window before reload
		
		try:
			# Read and execute the file contents in the actual global context
			source = Path("parse_jupyter_notebook.py").read_text()
			compiled = compile(source, "__name__", "exec")
			eval(compiled, globals())  # Use the real global scope for execution
			
			print("Successfully reloaded:")
			
			# Optionally find and execute the main function, if any
			main_fn = find_main_function(globals())  # Look for main function in global scope
			if main_fn:
				print("Executing main function from reloaded code...")
				main_fn()

		except Exception as e:
			print(f"Error during file execution: {e}")



	@window.on_animate
	def animate():
		label.setText(str(datetime.now()))

	window.show()
	sys.exit(app.exec())