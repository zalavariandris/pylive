from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

def indent_text(text, indent="    "):
    lines = text.split("\n")
    indented_lines = []
    for i, line in enumerate(lines):
        indented_lines.append(indent+line)

    return "\n".join(indented_lines)


def unindent_text(text, indent="    "):
                lines = text.split("\n")
                unindented_lines = []
                for i, line in enumerate(lines):
                    if line.startswith(indent):
                        unindented_lines.append(line[len(indent):])
                    else:
                        unindented_lines.append(line)
                return "\n".join(unindented_lines)

class IndentablePlainTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("IndentablePlainTextEdit")
        self.setTabChangesFocus(False)
        self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.resize(850, 850)

        self.setFont(QFont("Operator Mono", 10))
        self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(' ') * 4)

        self.indent_spaces = '    '  # Set indent spaces here

    def keyPressEvent(self, e: QKeyEvent) -> None:
        cursor = self.textCursor()
        if e.key() == Qt.Key_Tab:
            if cursor.hasSelection():
                self.indentSelection()
            else:
                cursor.insertText('\t')
        elif e.key() == Qt.Key_Backtab:  # Shift + Tab
            if cursor.hasSelection():
                self.unindentSelection()
        else:
            super().keyPressEvent(e)

    def indentSelection(self):
        cursor = self.textCursor()
        atBlockStart = cursor.atBlockStart()
        anchor = cursor.anchor()
        position = cursor.position()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        if cursor.hasSelection():
            cursor.beginEditBlock()

            # extend selection to lines
            cursor.setPosition(start, QTextCursor.MoveMode.MoveAnchor)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.MoveAnchor)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
            lines_start = cursor.selectionStart()
            lines_end = cursor.selectionEnd()
            startOffset = start - lines_start
            endOffset = end - lines_end

            # Replace the selected text with the indented text
            text = cursor.selection().toPlainText()
            

            indented_text = indent_text(text)
            cursor.insertText(indented_text)

            # Calculate the new start and end positions after indentation
            new_start = lines_start + len(self.indent_spaces) + startOffset if not atBlockStart else lines_start  # +4 for added indentation
            new_end = lines_start + len(indented_text) + endOffset

            if anchor<position:
                cursor.setPosition(new_start, QTextCursor.MoveMode.MoveAnchor)
                cursor.setPosition(new_end, QTextCursor.MoveMode.KeepAnchor)
            else:
                cursor.setPosition(new_end, QTextCursor.MoveMode.MoveAnchor)
                cursor.setPosition(new_start, QTextCursor.MoveMode.KeepAnchor)
            cursor.endEditBlock()
            self.setTextCursor(cursor)  # Set the cursor to the modified one

    def unindentSelection(self):
        cursor = self.textCursor()
        atBlockStart = cursor.atBlockStart()
        anchor = cursor.anchor()
        position = cursor.position()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        if cursor.hasSelection():
            cursor.beginEditBlock()

            # extend selection to lines
            cursor.setPosition(start, QTextCursor.MoveMode.MoveAnchor)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.MoveAnchor)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
            lines_start = cursor.selectionStart()
            lines_end = cursor.selectionEnd()
            startOffset = start - lines_start
            endOffset = end - lines_end

            # Replace the selected text with the indented text
            text = cursor.selection().toPlainText()
            lines = text.split("\n")

            unindented_text = unindent_text(text)
            cursor.insertText(unindented_text)

            # Calculate the new start and end positions after indentation
            new_start = lines_start - len(text.split("\n")[0]) + len(unindented_text.split("\n")[0]) + startOffset if not atBlockStart else lines_start
            new_end = lines_start + len(unindented_text) + endOffset

            if anchor<position:
                cursor.setPosition(new_start, QTextCursor.MoveMode.MoveAnchor)
                cursor.setPosition(new_end, QTextCursor.MoveMode.KeepAnchor)
            else:
                cursor.setPosition(new_end, QTextCursor.MoveMode.MoveAnchor)
                cursor.setPosition(new_start, QTextCursor.MoveMode.KeepAnchor)
            cursor.endEditBlock()
            self.setTextCursor(cursor)  # Set the cursor to the modified one



            





if __name__ == "__main__":
    import sys
    import textwrap
    from datetime import datetime
    import random
    app = QApplication(sys.argv)
    window = IndentablePlainTextEdit()

    window.setPlainText(textwrap.dedent("""\
    class Person:
        def __init__(self, name:str):
            self.name = name

        def say(self):
            print(self.name)

    peti = Person()
    """))
    window.show()
    sys.exit(app.exec())
