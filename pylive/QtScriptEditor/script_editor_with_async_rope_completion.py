
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from typing import *

# syntax highlighter
from pylive.QtScriptEditor.components.PygmentsSyntaxHighlighter import PygmentsSyntaxHighlighter

# code assist
import rope.base.project
from rope.contrib import codeassist
from pylive.QtScriptEditor.components.async_rope_completer_for_textedit import AsyncRopeCompleter


class ScriptEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        """ Setup Textedit """
        self.setupTextEdit()
        self.setShowWhitespace(True)
        self.highlighter = PygmentsSyntaxHighlighter(self.document())

        """ Autocomplete """
        self.rope_project = rope.base.project.Project('.')
        self.completer = AsyncRopeCompleter(self, self.rope_project)


    def setupTextEdit(self):
        self.setWindowTitle("ScriptTextEdit")
        self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.setTabChangesFocus(False)
        
        # set a monospace font
        font = self.font()
        font.setFamilies(["monospace", "Operator Mono Book"])
        font.setPointSize(10)
        font.setWeight(QFont.Weight.Medium)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.setFont(font)

        self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(' ') * 4)
        
        # resize window
        width = QFontMetrics(font).horizontalAdvance('O') * 70
        self.resize(width, int(width*4/3))

    def setShowWhitespace(self, value):
        # show whitespace
        options = QTextOption()
        options.setFlags(QTextOption.Flag.ShowTabsAndSpaces)
        self.document().setDefaultTextOption(options)



def main():
    from pylive.thread_pool_tracker import ThreadPoolCounterWidget
    app = QApplication([])
    editor = ScriptEdit()
    from textwrap import dedent
    editor.setPlainText(dedent("""\
    def hello_world():
        print("Hello, World!"
        # This is a comment
        x = 42
        return x
    """))

    rope_project = rope.base.project.Project('.')
    window = QWidget()
    mainLayout = QVBoxLayout()
    mainLayout.setContentsMargins(0,0,0,0)
    window.setLayout(mainLayout)

    completer = AsyncRopeCompleter(editor, rope_project)

    mainLayout.addWidget(editor)
    mainLayout.addWidget(ThreadPoolCounterWidget())
    window.setWindowTitle("QTextEdit with Non-Blocking Rope Assist Completer")
    window.resize(600, 400)
    window.show()

    app.exec()


if __name__ == "__main__":
    main()
