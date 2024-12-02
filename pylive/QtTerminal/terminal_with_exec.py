from typing import *

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.QtTerminal.logwindow import LogWindow
from pylive.QtScriptEditor.components.async_jedi_completer import AsyncJediCompleter
import ast
class Terminal(QFrame):
    exceptionThrown = Signal(Exception)
    messageSent = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle("Terminal with exec")
        self.setContext({})
        self.setFrameStyle(QFrame.Shape.StyledPanel)

        self.output = LogWindow()


        self.output.setReadOnly(True)
        self.output.setFrameStyle(QFrame.Shape.NoFrame)

        self.input = QLineEdit()
        self.input.setPlaceholderText("code...")        
        self.input.setFrame(False)

        self.input_completer = AsyncJediCompleter(self.input)
        self.input.setCompleter(self.input_completer)

        self.input.returnPressed.connect(lambda: (
            self._execute(self.input.text(), 'single'),
            self.input.clear(),
            self.output.verticalScrollBar().setValue(self.output.verticalScrollBar().maximum())
        ))

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        self.setLayout(layout)
        layout.addWidget(self.output)
        bottom_layout = QHBoxLayout()
        label = QLabel(">", parent=self.input)
        label.move(2,4)
        label.setStyleSheet("color: palette(light);")


        layout.addWidget(self.input)

        self.exceptionThrown.connect(lambda exc: print(f"{exc}"))

    def sizeHint(self):
        return QSize(512,256)

    def context(self):
        return self._context

    def setContext(self, context:dict):
        self._context = context
        self._context['__builtins__'] = __builtins__

    def _execute(self, source:str, mode:Literal["exec","single"]="exec"):
        try:
            tree = ast.parse(source)
            try:
                code = compile(source, "<script>", mode=mode)
                try:
                    result = exec(code, self.context())
                    if result:
                        print(result)
                except SyntaxError as err:
                    self.exceptionThrown.emit(err) #label
                except Exception as err:
                    self.exceptionThrown.emit(err) #label
            except SyntaxError as err:
                self.exceptionThrown.emit(err) # underline
            except Exception as err:
                self.exceptionThrown.emit(err) # underline

        except SyntaxError as err:
            self.exceptionThrown.emit(err) # underline
        except Exception as err:
            self.exceptionThrown.emit(err) # underline

    def execute(self, source:str):
        self._execute(source, mode='exec')

    def clear(self):
        self.output.clear()

    def print(self, msg):
        ...

    def error(self, exception:Exception):
        ...

if __name__ == "__main__":
    import sys
    app = QApplication([])
    window = Terminal()
    window.show()

    app.exec()