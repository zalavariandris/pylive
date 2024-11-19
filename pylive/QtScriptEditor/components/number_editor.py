from typing import *

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *


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
        self.drag_cursor = None
        self.drag_range = None
        self.original_cursor = textedit.cursor()

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

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseMove and not self.dragging:
            cursor = self.textedit.cursorForPosition(event.position().toPoint())
            number_cursor = self.getNumberCursor(cursor)
            if number_cursor and number_cursor != self.hovered_cursor:
                self.applyHighlight(number_cursor)
                obj.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                self.clearHoverHighlight()
                obj.setCursor(Qt.CursorShape.IBeamCursor)

        elif event.type() == QEvent.Type.MouseButtonPress:
            cursor = self.textedit.cursorForPosition(event.position().toPoint())
            number_cursor = self.getNumberCursor(cursor)

            if number_cursor:
                # Start dragging
                self.dragging = True
                self.drag_start = event.position().toPoint()
                self.original_value = int(number_cursor.selectedText())
                self.drag_cursor = QTextCursor(cursor)
                self.drag_range = (cursor.anchor(), cursor.position())

                return False

        elif event.type() == QEvent.Type.MouseMove and self.dragging:
            if self.drag_cursor:
                # Calculate drag distance and compute the new value
                drag_distance = event.position().toPoint() - self.drag_start
                new_value = self.original_value + (drag_distance.x() - drag_distance.y()) // 5

                # Ensure we replace the entire number
                cursor = self.textedit.textCursor()
                number_cursor = self.getNumberCursor(cursor)
                if number_cursor:
                    number_cursor.insertText(str(new_value))  # Replace with the new value
                cursor.movePosition(QTextCursor.MoveOperation.PreviousCharacter) # Workaroun, seee above

                return True

        elif event.type() == QEvent.Type.MouseButtonRelease and self.dragging:
            # Stop dragging
            self.dragging = False
            obj.setCursor(Qt.CursorShape.IBeamCursor)
            self.clearHoverHighlight()
            self.drag_cursor = None

            return True
        else:
            ...

        return super().eventFilter(obj, event)

    def applyHighlight(self, cursor:QTextCursor):
        """Highlight the current hovered word."""
        self.textedit.blockSignals(True)
        cursor.setCharFormat(self.highlight_format)
        self.hovered_cursor = QTextCursor(cursor)
        self.textedit.blockSignals(False)

    def clearHoverHighlight(self):
        """Remove the highlight from the previously hovered word."""
        if self.hovered_cursor:
            self.textedit.blockSignals(True)
            cursor = self.hovered_cursor
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            cursor.setCharFormat(self.default_format)
            self.hovered_cursor = None
            self.textedit.blockSignals(False)


if __name__ == "__main__":
    app = QApplication([])
    editor = QTextEdit()
    editor.setWindowTitle("Edit numbers with mouse inside a QTextEdit")
    editor.setPlainText("Hover over numbers like -40 or (10, 250) to highlight, and drag to edit them.")
    number_editor = NumberEditor(editor)
    editor.show()
    app.exec()
