import sys
from PySide6.QtWidgets import *
from IPython.core.interactiveshell import InteractiveShell
from io import StringIO


class IPythonConsole(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize an InteractiveShell instance
        self.shell = InteractiveShell.instance()

        # Layout for the widget
        layout = QVBoxLayout(self)

        # Create a QTextEdit for output display
        self.output_display = QTextEdit(self)
        self.output_display.setReadOnly(True)
        layout.addWidget(self.output_display)

        # Create a QLineEdit for input
        self.input_line = QLineEdit(self)
        self.input_line.setPlaceholderText("Write Python code here...")
        layout.addWidget(self.input_line)

        # Create an "Execute" button
        self.execute_button = QPushButton("Execute", self)
        layout.addWidget(self.execute_button)

        # Connect the input and button to the execution method
        self.input_line.returnPressed.connect(self.execute_code)
        self.execute_button.clicked.connect(self.execute_code)

    def execute_code(self):
        """Execute the code entered in the QLineEdit."""
        code = self.input_line.text()
        if not code.strip():
            return  # Do nothing if the input is empty

        # Redirect stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()

        try:
            # Execute the code
            result = self.shell.run_cell(code)
            stdout_content = sys.stdout.getvalue()
            stderr_content = sys.stderr.getvalue()

            # Display output or errors
            if result.error_in_exec is not None:
                self.output_display.append(f"Error:\n{stderr_content}")
            else:
                self.output_display.append(stdout_content)
        except Exception as e:
            self.output_display.append(f"Exception: {str(e)}")
        finally:
            # Restore stdout and stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        # Clear the input line
        self.input_line.clear()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IPython QLineEdit Example")

        # Set the central widget
        self.console_widget = IPythonConsole(self)
        self.setCentralWidget(self.console_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
