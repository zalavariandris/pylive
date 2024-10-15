from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from pathlib import Path
import importlib
import traceback
from typing import Callable

current_window = None  # Global variable to track the current window

def get_current_window():
    return current_window  # Return the globally set window

class Proxy:
    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        """Return the attribute from the underlying module."""
        return getattr(self._module, name)

class LiveCode(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        
        global current_window
        current_window = self  # Set the current window globally here

        # animation frame
        self.animationFrameHandles = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.handleAnimationFrames)
        self.timer.start(1000/60)


    def handleAnimationFrames(self):
        for cb in self.animationFrameHandles:
            cb()

    def on_animate(self, cb:Callable):
        self.animationFrameHandles.append(cb)

    # def on_watch(self, file:Path):
    #     def watch_file(cb):
    #         watcher = QFileSystemWatcher()
    #         watcher.addPath(str(file))
    #         self.watchers[(file, cb)] = watcher


    #         watcher.fileChanged.connect(cb)
    #         cb()

    #     return watch_file

    @staticmethod
    def current():
        return globals().get("current_window")  # Return the current window

import re
def refactor(source_code: str) -> str:
    # Define regex patterns and their replacements
    replacements = [
        (r'import QLiveCoding', r'QLiveCoding = _QLiveCoding'),  # For import QLiveCoding
        (r'from QLiveCoding import (\w+)', r'\1 = _QLiveCoding.\1'),  # For from QLiveCoding import LiveCode
        (r'from QLiveCoding\.LiveCode import (\w+)', r'\1 = _QLiveCoding.LiveCode.\1')  # For from QLiveCoding.LiveCode import current
    ]
    
    for pattern, replacement in replacements:
        source_code = re.sub(pattern, replacement, source_code)
    
    return source_code

class ClassProxy:
    def __init__(self, window):
        self._window = window

    def current(self):
        return self._window

class ModuleProxy:
    def __init__(self, window):
        self.LiveCode = ClassProxy(window)


if __name__ == "__main__":
    import sys
    import subprocess
    app = QApplication(sys.argv)
    window = LiveCode()
    label = QLabel("Test")
    window.layout().addWidget(label)

    print("Current window before dynamic import:", LiveCode.current())  # This should print the window

    # Path to the dynamically executed script
    script = Path("parse_jupyter_notebook.py").read_text()  # Ensure this path is correct
    # script = refactor(script)
    for lineno, line in enumerate(script.split("\n")):
        print(f"{line}")
    print()
    # Call the dynamic import and execute function

    global_vars = globals()
    local_vars = locals()
    global_vars["QLiveCoding"] =  sys.modules[__name__]
    # exec(script, global_vars, global_vars)
    

    window.show()
    sys.exit(app.exec())
