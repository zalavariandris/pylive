import sys
from typing import *

from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager

from pylive.declerative_qt import Splitter, Panel
from pylive.live_preview_widgets.file_textdocument_link import FileTextDocumentLink
from pylive.QtScriptEditor.components.pygments_syntax_highlighter import PygmentsSyntaxHighlighter


class WidgetPreviewApp(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def instance(self):
        pass

    def addWidget(self, widget):
        pass

    def removeWidget(self, widget):
        pass

    def clearWidgets(self):
        pass


class IPythonWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IPython Console in PySide6")

        ### IPython Console widget ###
        self.console = RichJupyterWidget()
        self.console.style_sheet = "dracula"
        self.console.syntax_style = "dracula"
        
        # Set up an in-process kernel manager and hook up with the consol
        self.kernel_manager = QtInProcessKernelManager()
        self.kernel_manager.start_kernel()     
        self.console.kernel_manager = self.kernel_manager # Connect the kernel manager to the console widget
        self.console.kernel_client = self.kernel_manager.client()
        self.console.kernel_client.start_channels() # Start the kernel client channels (this is the communication between the UI and the kernel)

        ### Script Edit ###
        self.textedit = QPlainTextEdit()
        font = self.textedit.font()
        font.setFamilies(["monospace", "Operator Mono Book"])
        font.setWeight(QFont.Weight.Medium)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.textedit.setFont(font)
        self.textedit.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        highlighter = PygmentsSyntaxHighlighter(self.textedit.document())
        self.textedit.setTabStopDistance(self.textedit.fontMetrics().horizontalAdvance(" ")*4)
        self.textedit.setReadOnly(True)

        ### Script Edit ###
        from textwrap import dedent
        placeholder = QLabel(dedent("""
        [preview area]
        use .setAppWidget to show a widget here
        """))
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.app = placeholder
        self.app.setLayout(QVBoxLayout())
        # placeholder = QLabel("[preview area]")
        # placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.preview_area.layout().addWidget(placeholder)

        ### Layout ###
        self.console.setFixedHeight(140)
        main_splitter = Splitter(Qt.Orientation.Horizontal, [
            Panel(QBoxLayout.Direction.TopToBottom, [
                self.textedit
            ]),
            Panel(QBoxLayout.Direction.TopToBottom, [
                self.app,
                self.console
            ])
        ])
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0,0,0,0)
        mainLayout.addWidget(main_splitter)
        self.setLayout(mainLayout)

        ### access preview area from consol ###

        self.kernel_manager.kernel.shell.user_ns['app'] = self.app

    def sizeHint(self):
        return QSize(1200,700)

    def execute_code(self, code_str):
        self.kernel_manager.kernel.shell.run_cell(code_str)

    def setWidgets(self, app:List[QWidget]):
        # TODO:
        capable of previewing multiple widget just like the livepreview widget.
        This is supposed to be the framework to develop any pyside based app.
        make it an abc, and implement it without the Console, insted use as imple logger.
        self.app = app


def main():
    app = QApplication(sys.argv)
    
    window = IPythonWindow()
    window.show()
    
    # Execute a string of code using the execute_code method to add a widget
    from textwrap import dedent
    code_to_execute = dedent("""\
    from PySide6.QtWidgets import QPushButton

    # Create a new QPushButton
    button = QPushButton("Click Me")

    # Add the button to the layout in the main window
    app.layout().addWidget(button)
    """)
    window.textedit.setPlainText(code_to_execute)
    window.execute_code(code_to_execute)  # This will add a button to the layout
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
