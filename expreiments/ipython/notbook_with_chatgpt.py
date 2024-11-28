import sys
import io
import traceback
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QScrollArea, QFrame, QLabel
from IPython.core.interactiveshell import InteractiveShell
from IPython.terminal.prompts import Prompts, Token

class QtConsoleApp(QWidget):
    def __init__(self):
        super().__init__()

        # Setup window
        self.setWindowTitle('QtConsole-Like App')
        self.setGeometry(100, 100, 800, 600)

        # Main Layout
        self.setLayout( QVBoxLayout() )

        # Code input area (similar to the code editor)
        self.code_input = QTextEdit(self)
        self.code_input.setPlaceholderText("Type Python code here...")
        self.layout().addWidget(self.code_input)

        # Execute button to run code
        self.execute_button = QPushButton("Run Code", self)
        self.execute_button.clicked.connect(self.run_code)
        self.layout().addWidget(self.execute_button)

        # Scrollable output area
        self.output_area = QTextEdit(self)
        self.output_area.setReadOnly(True)  # Output only
        self.layout().addWidget(self.output_area)



        # Initialize IPython shell for code execution
        self.shell = InteractiveShell.instance()

    def run_code(self):
        # Get code input from QTextEdit
        code = self.code_input.toPlainText()

        # Prepare the output for capturing stdout/stderr
        stdout = io.StringIO()
        stderr = io.StringIO()

        try:
            # Execute code and capture output
            self._redirect_output(stdout, stderr)
            self.shell.run_cell(code)
            result = stdout.getvalue()
            error = stderr.getvalue()

            if result:
                self.display_output(f"Output:\n{result}")
            if error:
                self.display_output(f"Error:\n{error}")
        except Exception as e:
            # In case of any unexpected errors
            self.display_output(f"Error:\n{str(e)}")

    def _redirect_output(self, stdout, stderr):
        """Redirect stdout and stderr to capture the output of the code."""
        return io.StringIO(), stderr

    def display_output(self, text):
        """Display the output in the output area."""
        self.output_area.append(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QtConsoleApp()
    window.show()
    sys.exit(app.exec())
