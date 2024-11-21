from typing import *

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

from textwrap import dedent

class NumberEditor(QObject):
    def __init__(self, textedit:QTextEdit):
        super().__init__(parent=textedit)
        
        self.hovered_cursor = None  # Store the currently hovered cursor
        self.default_format = QTextCharFormat()  # Store the default format
        self.highlight_format = QTextCharFormat()
        # self.highlight_format.setForeground(QColor("lightgreen"))
        self.highlight_format.setUnderlineStyle(QTextCharFormat.SingleUnderline)

        # Enable mouse tracking for the viewport
        self.dragging = False
        self.drag_start_y = None
        self.original_value = None
        self.number_cursor = None

        textedit.viewport().setMouseTracking(True)
        # Install the event filter on the viewport
        textedit.viewport().installEventFilter(self)
        self.textedit = textedit

    def getNumberCursor(self, cursor:QTextCursor)->QTextCursor|None:
        # acts like cursor.select(QTextCursor.WordUnderCursor) but includes tne '-' sign as well
        # (WordUnderCursor does not include the '-' sign.)
        word_cursor = QTextCursor(cursor)

        word_cursor.movePosition(QTextCursor.MoveOperation.PreviousCharacter, QTextCursor.MoveMode.KeepAnchor) # Workaropund: for some reason when i insert new number below, the cursor canot be moved back to its original location.
        word_cursor.select(QTextCursor.SelectionType.WordUnderCursor)

        word = word_cursor.selectedText()


        if word.isdigit():  # Check for digits without the negative sign
            start = word_cursor.selectionStart()
            end = word_cursor.selectionEnd()
            number_cursor = QTextCursor(word_cursor)
            number_cursor.setPosition(start-1, QTextCursor.MoveMode.MoveAnchor)
            number_cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            extended_text = number_cursor.selectedText()

            if extended_text.startswith('-'):  # Check if the '-' is part of the number
                return number_cursor
            else:
                return word_cursor
        else:
            return None


    # def getNumberCursor(self, cursor: QTextCursor) -> QTextCursor|None:
    #     text = self.textedit.toPlainText()  # Get the entire text from the editor
    #     offset = cursor.position()  # Get the current position of the cursor

    #     # Ensure the cursor is at a valid position
    #     if not (0 <= offset < len(text)) or not (text[offset].isdigit() or text[offset] == '-'):
    #         return None
    #         raise ValueError(f"No number found at cursor position {offset}")

    #     # Move the cursor to the start of the number
    #     cursor.setPosition(offset, QTextCursor.MoveAnchor)

    #     # Move backward to the start of the number
    #     while cursor.position() > 0 and (text[cursor.position() - 1].isdigit() or text[cursor.position() - 1] == '-'):
    #         cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor)

    #     # Now, move forward to find the end of the number
    #     end_position = cursor.position()
    #     while end_position < len(text) and text[end_position].isdigit():
    #         end_position += 1

    #     # Create a new cursor that spans the number
    #     new_cursor = QTextCursor(cursor.document())
    #     new_cursor.setPosition(cursor.position(), QTextCursor.MoveAnchor)
    #     new_cursor.setPosition(end_position, QTextCursor.KeepAnchor)

    #     return new_cursor

    def eventFilter(self, obj, event): #type: ignore
        if event.type() == QEvent.Type.MouseMove and not self.dragging:
            self.number_cursor = self.getNumberCursor(
                self.textedit.cursorForPosition(
                    event.position().toPoint()
                )
            )
            # if self.number_cursor:
            #     print(dedent(f"""\
            #     MOUSE HOVER MOVE
            #     position: {self.number_cursor.position()}
            #     anchor:   {self.number_cursor.anchor()}
            #     text: '{self.number_cursor.selectedText()}'

            #     """))
            # else:
            #     print(dedent(f"""\
            #     MOUSE HOVER MOVE
            #     - no number cursor -

            #     """))
            if self.number_cursor:
                self.applyHighlight(self.number_cursor)
                obj.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                self.clearHoverHighlight()
                obj.setCursor(Qt.CursorShape.IBeamCursor)

        elif event.type() == QEvent.Type.MouseButtonPress:
            if self.number_cursor:
                # Start dragging
                self.dragging = True
                self.drag_start = event.position().toPoint()
                # print(dedent(f"""\
                # MOUSE PRESS
                # position: {self.number_cursor.position()}
                # anchor:   {self.number_cursor.anchor()}
                # text: '{self.number_cursor.selectedText()}'

                # """))
                self.original_value = int(self.number_cursor.selectedText())

                return False

        elif event.type() == QEvent.Type.MouseMove and self.dragging:
            if self.number_cursor:
                # Calculate drag distance and compute the new value
                drag_distance = event.position().toPoint() - self.drag_start
                new_value = self.original_value + (drag_distance.x() - drag_distance.y()) // 5

                # Ensure we replace the entire number
                if self.number_cursor:
                    # print(dedent(f"""\
                    # MOUSE DRAG MOVE
                    # position: {self.number_cursor.position()}
                    # anchor:   {self.number_cursor.anchor()}
                    # text: '{self.number_cursor.selectedText()}'

                    # """))
                    position= self.number_cursor.position()
                    anchor=   self.number_cursor.anchor()
                    self.number_cursor.insertText(str(new_value))  # Replace with the new value

                    # note: insert text will move the cursor to the end of the number.
                    # find the newly inserted text
                    self.number_cursor = self.getNumberCursor(self.number_cursor)                

        elif event.type() == QEvent.Type.MouseButtonRelease and self.dragging:
            # Stop dragging
            self.dragging = False
            obj.setCursor(Qt.CursorShape.IBeamCursor)
            self.clearHoverHighlight()
            self.drag_cursor = None
            return True
        else:
            ...

        # THIS IS FOR DEBUG ONLY !!!!!!!!!!
        if event.type() == QEvent.Type.MouseMove:
            return True

        return super().eventFilter(obj, event)

    def applyHighlight(self, cursor:QTextCursor):
        """Highlight the current hovered word."""
        if self.hovered_cursor!=cursor:
            self.hovered_cursor = cursor
            self.textedit.blockSignals(True)
            cursor.setCharFormat(self.highlight_format)
            self.textedit.blockSignals(False)

    def clearHoverHighlight(self):
        """Remove the highlight from the previously hovered word."""
        if self.hovered_cursor:
            self.textedit.blockSignals(True)
            self.hovered_cursor.setCharFormat(self.default_format)
            self.textedit.blockSignals(False)
            self.hovered_cursor = None


if __name__ == "__main__":
    app = QApplication([])
    editor = QTextEdit()
    editor.textChanged.connect(lambda: print("text changed!"))
    editor.setWindowTitle("Edit numbers with mouse inside a QTextEdit")
    editor.setPlainText("Hover over numbers like -40 or (10, 250) to highlight, and drag to edit them.")
    number_editor = NumberEditor(editor)
    editor.show()
    app.exec()
