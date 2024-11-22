from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from pylive.examples import livescript
from typing import *

import sys
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatter import Formatter
from pygments.token import Token

def complement(color:QColor):
    h, s, l, a = color.getHsl()
    return QColor.fromHsl((h+180)%360, s, l, a)

def shift(color:QColor, offset=180):
    h, s, l, a = color.getHsl()
    return QColor.fromHsl((h+offset)%360, s, l, a)

def dim(color:QColor, a=128):
    r,g,b,_ = color.getRgb()
    return QColor.fromRgb( r,g,b,a )
    
black =       QColor.fromHsl(0, 0*255/100, 0*255/100)
blue =        QColor.fromHsl(210, 50*255/100, 60*255/100)
blueVibrant = QColor.fromHsl(210, 60*255/100, 60*255/100)
blue2 =       QColor.fromHsl(210, 13*255/100, 40*255/100, 70)
blue3 =       QColor.fromHsl(210, 15*255/100, 22*255/100)
blue4 =       QColor.fromHsl(210, 13*255/100, 45*255/100)
blue5 =       QColor.fromHsl(180, 36*255/100, 54*255/100)
blue6 =       QColor.fromHsl(221, 12*255/100, 69*255/100)
green =       QColor.fromHsl(114, 31*255/100, 68*255/100)
grey =        QColor.fromHsl(0, 0*255/100, 20*255/100)
orange =      QColor.fromHsl(32, 93*255/100, 66*255/100)
orange2 =     QColor.fromHsl(32, 85*255/100, 55*255/100)
orange3 =     QColor.fromHsl(40, 94*255/100, 68*255/100)
pink =        QColor.fromHsl(300, 30*255/100, 68*255/100)
red =         QColor.fromHsl(357, 79*255/100, 65*255/100)
red2 =        QColor.fromHsl(13, 93*255/100, 66*255/100)
white =       QColor.fromHsl(0, 0*255/100, 100*255/100)
white2 =      QColor.fromHsl(0, 0*255/100, 97*255/100)
white3 =      QColor.fromHsl(219, 28*255/100, 82*255/100)

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
import re
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
                fmt = QTextCharFormat()

                # Apply basic styles from Pygments tokens
                if 'Comment' in str(ttype):
                    # Gray for comments
                    fmt.setForeground(dim( palette.color(QPalette.ColorRole.Text), 150 )) 
                    fmt.setFontItalic(True)
                elif 'String' in str(ttype):
                    # Green for strings
                    fmt.setForeground(green)
                elif 'Punctuation' in str(ttype): # this is not a pygment constant
                    fmt.setForeground(blue5)
                elif 'Keyword' in str(ttype):
                    # Blue for keywords
                    fmt.setForeground(complement(palette.color(QPalette.ColorRole.Highlight)))
                elif 'Number' in str(ttype):
                    fmt.setForeground(pink)
                elif 'Number Suffix' in str(ttype): # this is not a pygment constant
                    fmt.setForeground(pink)
                elif 'Built-in constant' in str(ttype):  # this is not a pygment constant
                    fmt.setForeground(red)
                    fmt.setFontItalic(True)
                elif "User-defined constant" in str(ttype):  # this is not a pygment constant
                    fmt.setForeground(pink)
                elif 'Name.Function' in str(ttype):
                    # Purple for function names
                    fmt.setForeground(blue5)
                    fmt.setFontWeight(QFont.Bold)
                elif ttype == Token.Operator:
                    fmt.setForeground(red2)

                # Whitespace
                elif re.match(r'[ \t]+', value):
                    text_color = palette.color(QPalette.ColorRole.Text)
                    text_color.setAlpha(30)
                    fmt.setForeground(text_color)

                elif "Text.Whitespace" in str(ttype):
                    text_color = palette.color(QPalette.ColorRole.Text)
                    text_color.setAlpha(100)
                    fmt.setForeground(QColor("darkcyan"))
                else:
                    # print(ttype, value)
                    # Default to black for others
                    fmt.setForeground(white3)

                # Append the format with the
                # start position and length
                self.formats.append((current_pos, length, fmt))

            # Update the current position
            current_pos += length


if __name__ == "__live__":
	from pylive.QtScriptEditor.script_edit import ScriptEdit
	editor = ScriptEdit()
	from pylive.preview_widget import PreviewWidget
	preview = PreviewWidget.instance()
	preview.display(editor)
	
	from textwrap import dedent
	editor.setPlainText(dedent("""\
		def hello():
		    print("hello")
	"""))

	
	editor.highlighter = PygmentsSyntaxHighlighter(editor.document())
	bgcolor = QColor()
	bgcolor.setHsl(192,31,49)
	palette = editor.palette()
	palette.setColor(QPalette.Base, blue3)  # Light yellow color
	editor.setPalette(palette)
	

if __name__ == "__main__":
	...

