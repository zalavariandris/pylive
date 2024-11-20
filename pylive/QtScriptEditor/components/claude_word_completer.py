from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from typing import *

class WordCompleter(QCompleter):
    def __init__(self, textedit: QTextEdit, words: List[str] = []) -> None:
        super().__init__(words, parent=textedit)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.text_edit = textedit
        self.setWidget(self.text_edit)
        self.activated.connect(self.insertCompletion)
        self.text_edit.installEventFilter(self)
        self.text_edit.textChanged.connect(self.updateCompletion)

        self._last_error: Optional[str] = None

    def insertCompletion(self, completion: str) -> bool:
        """
        Inserts the selected completion into the text at the cursor position.
        Now properly uses the selected completion from the popup.
        """
        try:
            tc = self.text_edit.textCursor()
            extra = len(completion) - len(self.completionPrefix())
            tc.movePosition(QTextCursor.Left)
            tc.movePosition(QTextCursor.EndOfWord)
            tc.insertText(completion[-extra:])
            self.text_edit.setTextCursor(tc)
            return True
        except Exception as e:
            self._last_error = str(e)
            return False

    def textUnderCursor(self) -> str:
        cursor = self.text_edit.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        return cursor.selectedText()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyRelease:
            print(f"text under cursor: '{self.textUnderCursor()}'")

        if event.type() == QEvent.KeyPress:
            if obj is self.text_edit or obj is self.popup():
                if event.key() in {Qt.Key_Enter, Qt.Key_Return} and self.popup().isVisible():
                    # Get the currently selected completion from the popup
                    current_index = self.popup().currentIndex()
                    selected_completion = self.completionModel().data(current_index, Qt.DisplayRole)
                    if selected_completion:
                        success = self.insertCompletion(selected_completion)
                        if not success:
                            print(f"Completion insertion failed: {self._last_error}")
                    self.popup().hide()
                    return True
                elif event.key() == Qt.Key_Escape and self.popup().isVisible():
                    print("Escape pressed")
                    self.popup().hide()
                    return True
                elif event.key() in {Qt.Key_Up, Qt.Key_Down} and self.popup().isVisible():
                    # Let the popup handle up/down keys for selection
                    return False

        return super().eventFilter(obj, event)

    def updateCompletion(self) -> None:
        try:
            prefix = self.textUnderCursor()
            if prefix and len(prefix) > 0 and prefix != self.currentCompletion():
                self.setCompletionPrefix(prefix)
                popup = self.popup()
                popup.setCurrentIndex(self.completionModel().index(0, 0))
                rect = self.text_edit.cursorRect()
                rect.setWidth(popup.sizeHintForColumn(0) + 
                            popup.verticalScrollBar().sizeHint().width())
                self.complete(rect)
            else:
                self.popup().hide()
        except Exception as e:
            self._last_error = str(e)
            print(f"Error updating completion: {self._last_error}")

    def updateWordList(self, new_words: List[str]) -> bool:
        try:
            model = QStringListModel(new_words)
            self.setModel(model)
            return True
        except Exception as e:
            self._last_error = str(e)
            return False

    def getLastError(self) -> Optional[str]:
        return self._last_error

if __name__ == "__main__":
    # create app
    app = QApplication([])
    
    # create completing editor
    editor = QTextEdit()
    
    # Example of custom popup style

    
    completer = WordCompleter(
        editor,
        ["apple", "ananas", "banana", "cherry", "date", "elderberry", 
         "fig", "grape", "honeydew", "kiwi", "lemon"]
    )
    
    editor.setWindowTitle("QTextEdit with Enhanced Completer")
    editor.resize(600, 400)
    
    words = [completer.model().index(row,0).data() 
             for row in range(completer.model().rowCount())]
    editor.setPlaceholderText("Start typing...\n\neg.: " + ", ".join(words))
    
    editor.show()
    app.exec()