from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from typing import *

class CustomCompleter(QCompleter):
    def __init__(self, words, textedit:QTextEdit):
        super().__init__(words, textedit)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.text_edit = textedit  # The QTextEdit instance
        self.setWidget(self.text_edit)
        self.activated.connect(self.insertCompletion)

        # Install event filter on the text edit

        self.text_edit.installEventFilter(self)
        # self.popup().installEventFilter(self)
        self.text_edit.viewport().installEventFilter(self)
        self.text_edit.viewport().setMouseTracking(True)

        self.text_edit.textChanged.connect(lambda: self.updateCompletion())

    def insertCompletion(self, completion):
        """
        Inserts the selected completion into the text at the cursor position.
        """
        tc = self.text_edit.textCursor()
        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        tc.insertText(completion)

    def textUnderCursor(self):
        """
        Returns the word under the cursor in the QTextEdit.
        """
        cursor = self.text_edit.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        return cursor.selectedText()

    def refreshCompleterPrefix(self):
        ...

    def eventFilter(self, obj, event):
        """
        Filters events for the QTextEdit and the completer popup.
        """
        # print(event)
        if event.type() == QEvent.Type.KeyRelease:
            print(f"'{self.textUnderCursor()}'")

        #superclass already installed an eventfilter on the popup() ListView
        if event.type() == QEvent.KeyPress:
            if obj is self.text_edit or obj is self.popup():
            
                # Handle key events for autocompletion
                if event.key() in {Qt.Key_Enter, Qt.Key_Return} and self.popup().isVisible():
                    self.insertCompletion(self.currentCompletion())
                    self.popup().hide()
                    return True
                elif event.key() == Qt.Key_Escape and self.popup().isVisible():
                    print("Escape pressed")
                    self.popup().hide()
                    return True

            # Update the completer based on the text under the cursor
        # if event.type() == QEvent.Type.KeyRelease:
        #     super().eventFilter(obj, event)
        #     self.updateCompletion()

        return super().eventFilter(obj, event)

    def updateCompletion(self):
        """
        Updates the completion prefix and shows the popup if necessary.
        """
        prefix = self.textUnderCursor()
        if prefix and len(prefix) > 0 and prefix != self.currentCompletion():
            self.setCompletionPrefix(prefix)
            popup = self.popup()
            popup.setCurrentIndex(self.completionModel().index(0, 0))

            rect = self.text_edit.cursorRect()
            rect.setWidth(popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width())
            self.complete(rect)
        else:
            self.popup().hide()



if __name__ == "__main__":
    app = QApplication([])

    words = [
            "apple", "ananas", "banana", "cherry", "date", "elderberry", "fig", "grape", "honeydew", "kiwi", "lemon",
            'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue',
            'def', 'del', 'elif', 'else', 'except', 'False', 'finally', 'for',
            'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None', 'nonlocal',
            'not', 'or', 'pass', 'raise', 'return', 'True', 'try', 'while', 'with', 'yield'
        ]
    editor = QTextEdit()
    editor.setPlaceholderText("Start typing...")
    completer = CustomCompleter(words, editor)
    editor.setWindowTitle("QTextEdit with Custom Completer")
    editor.resize(600, 400)
    editor.show()

    app.exec()
