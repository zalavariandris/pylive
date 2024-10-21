import sys
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatter import Formatter

def complement(color:QColor):
    h, s, l, a = color.getHsl()
    return QColor.fromHsl((h+180)%360, s, l, a)

def shift(color:QColor, offset=180):
    h, s, l, a = color.getHsl()
    return QColor.fromHsl((h+offset)%360, s, l, a)

def dim(color:QColor, a=128):
    r,g,b,_ = color.getRgb()
    return QColor.fromRgb( r,g,b,a )


class PygmentsSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.lexer = PythonLexer()  # Use the lexer for the language you want to highlight

    def highlightBlock(self, text):
        """ Apply syntax highlighting to a block of text. """
        # Create the formatter for this block
        formatter = QtFormatter()
        # Use Pygments to tokenize the text and apply formatting
        highlight(text, self.lexer, formatter)

        # Apply the formats calculated by the formatter
        for start, length, format in formatter.formats:
            self.setFormat(start, length, format)

class QtFormatter(Formatter):
    """ Formatter that applies Pygments tokens to QTextCharFormat
    for QSyntaxHighlighter """
    def __init__(self):
        super().__init__()
        self.formats = []

    def format(self, tokensource, outfile):
        """ Convert Pygments tokens into QTextCharFormat for
        QSyntaxHighlighter """
        palette = QGuiApplication.palette()
        current_pos = 0
        for ttype, value in tokensource:
            length = len(value)
            if length > 0:
                # Create a QTextCharFormat based on the token type
                format = QTextCharFormat()

                # Apply basic styles from Pygments tokens
                if 'Keyword' in str(ttype):
                    # Blue for keywords
                    format.setForeground(complement(palette.color(QPalette.ColorRole.Highlight)))
                elif 'String' in str(ttype):
                    # Green for strings
                    format.setForeground(QColor("darkGreen"))
                elif 'Comment' in str(ttype):
                    # Gray for comments
                    format.setForeground(dim( palette.color(QPalette.ColorRole.Text), 150 )) 
                    format.setFontItalic(True)
                elif 'Name.Function' in str(ttype):
                    # Purple for function names
                    format.setForeground(QColor("darkcyan"))
                    format.setFontWeight(QFont.Bold)
                elif 'Number' in str(ttype):
                    # Red for numbers
                    format.setForeground(QColor("darkGreen"))
                else:
                    # Default to black for others
                    format.setForeground(palette.color(QPalette.ColorRole.Text))

                # Append the format with the
                # start position and length
                self.formats.append((current_pos, length, format))

            # Update the current position
            current_pos += length

### Main Application ###
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create a QTextEdit and apply the highlighter
    editor = QTextEdit()
    editor.setWindowTitle("PygmentsSyntaxHighlighter component example")
    highlighter = PygmentsSyntaxHighlighter(editor.document())

    # Set some Python code to highlight
    sample_code = """def hello_world():
    print("Hello, World!")
    # This is a comment
    x = 42
    return x
    """
    editor.setPlainText(sample_code)
    editor.show()

    sys.exit(app.exec())
