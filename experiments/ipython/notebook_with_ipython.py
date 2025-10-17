import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QScrollArea
from IPython import embed

class NotebookApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive IPython Notebook")
        self.setGeometry(100, 100, 800, 600)
        
        self.layout = QVBoxLayout(self)
        
        self.create_code_cell()
        self.create_output_cell()
        
    def create_code_cell(self):
        # Code cell where user can type Python code
        self.code_cell = QTextEdit()
        self.code_cell.setPlaceholderText("Type Python code here...")
        # self.code_cell.setStyleSheet("background-color: #f4f4f4;")
        self.layout.addWidget(self.code_cell)

        # Execute button to run the code
        run_button = QPushButton("Run Code")
        run_button.clicked.connect(self.run_code)
        self.layout.addWidget(run_button)
        
    def create_output_cell(self):
        # Output area for showing results
        self.output_cell = QLabel()
        self.output_cell.setWordWrap(True)
        # self.output_cell.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ddd;")
        self.layout.addWidget(self.output_cell)
        
    def run_code(self):
        # Get the code from the QTextEdit widget
        code = self.code_cell.toPlainText()
        
        try:
            # Use IPython to execute the code
            from IPython.core.interactiveshell import InteractiveShell
            shell = InteractiveShell.instance()
            result = shell.run_cell(code)
            
            # Display the result in the output cell
            if result.success:
                output = str(result.result) if result.result else "No output"
            else:
                output = f"Error: {result.error_in_exec}"
                
            self.output_cell.setText(output)
        except Exception as e:
            self.output_cell.setText(f"Error executing code: {str(e)}")
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NotebookApp()
    window.show()
    sys.exit(app.exec())
