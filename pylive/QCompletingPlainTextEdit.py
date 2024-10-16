"""A QPlainTextEdit subclass with completion and some extras

Adapted from
https://doc.qt.io/qt-5/qtwidgets-tools-customcompleter-example.html
with the intent to be a minimally complicated way to get as-you-type
autocomplete in a QTextEdit.

As such, a lot of needless complexity has been removed, and odd design choices
which make the code needlessly difficult to maintain have been corrected.

(eg. If you're going to override `focusInEvent` to prepare to share one
`QCompleter` between multiple text widgets, which you don't do in your example,
why are you forcibly configuring it as case-insensitive inside your
`setCompleter` instead of leaving that up to whoever initializes
the completer?)

Feel free to use this code under any license you're allowed to use the original
Qt example code under. I'm of the opinion that it does stuff that should really
be part of Qt to begin with.
-- Stephan Sokolow
"""

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class CompletingPlainTextEdit(QPlainTextEdit):
    """QPlainTextEdit with as-you-type completion.

    Includes a couple of extra features to make it more useful as a fake
    "QLineEdit, but with soft word-wrap".
    """

    #: The text that will be inserted after the selected completion.
    #: (Change from ' ' to ', ' for tag-entry fields.)
    completion_tail: str = " "

    #: Set this to True if you want a more convincing fake QLineEdit
    #:
    #: Ignores Enter/Return keypresses but allows newlines to be pasted in
    #: like QLineEdit does... though it doesn't attempt to render them as
    #: non-linebreaking arrow graphics.
    ignore_return: bool = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.completions = QStringListModel(self)
        self.completer = QCompleter(self.completions, self)
        self.completer.setWidget(self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.activated.connect(self.insert_completion)

    def complete(self):
        """Show any available completions at the current cursor position"""
        # TODO: Extend to support custom "what is a word character?" rules.
        #       (See https://stackoverflow.com/q/75485192/435253 for DO/DON'Ts)
        tc = self.textCursor()
        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        selected_text = tc.selectedText()

        # Depend on Qt's definition of word separators to control the popup
        # instead of replicating them in this code and hoping they don't change
        # (eg. Don't show an unfiltered popup after typing a comma, don't
        #  allow fo,<tab> to complete to fo,foo, and don't break if .strip()'s
        #  definition of whitespace differs.)
        if selected_text:
            self.completer.setCompletionPrefix(selected_text)

            popup = self.completer.popup()
            popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
            cr = self.cursorRect()
            cr.setWidth(popup.sizeHintForColumn(0) +
                        popup.verticalScrollBar().sizeHint().width())
            self.completer.complete(cr)
        else:
            self.completer.popup().hide()

    def insert_completion(self, completion):
        """Callback invoked by pressing Tab/Enter in the completion popup"""
        tc = self.textCursor()
        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        tc.insertText(completion + self.completion_tail)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        """Implement the modal interactions between completion and keys"""
        # If completer popup is open. Give it exclusive use of specific keys
        if self.completer.popup().isVisible() and e.key() in [
            # Navigate popup
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
            # Accept completion
            Qt.Key.Key_Enter,
            Qt.Key.Key_Return,
            Qt.Key.Key_Tab,
            Qt.Key.Key_Backtab,
        ]:
            e.ignore()
            return

        # Fall back to tabChangesFocus (must be off in QPlainTextEdit props)
        if e.key() == Qt.Key_Tab:  # type: ignore[attr-defined]
            e.ignore()  # Prevent QPlainTextEdit from entering literal Tab
            return
        elif e.key() == Qt.Key_Backtab:  # type: ignore[attr-defined]
            e.ignore()  # Prevent QPlainTextEdit from blocking Backtab
            return

        # Remove this line if you don't want a fake QLineEdit with word-wrap
        if self.ignore_return and e.key() in [
                Qt.Key.Key_Enter, Qt.Key.Key_Return]:
            e.ignore()
            return

        # If we reach here, let QPlainTextEdit's normal behaviour happen
        old_len = self.document().characterCount()
        super().keyPressEvent(e)

        # Now that QPlainTextEdit has incorporated any typed character,
        # proper as-you-type completion should react to that (with whitespace
        # and things like the ASCII backspace and delete characters excluded),
        # not a blanket textChanged which reacts to programmatic document
        # manipulation too.
        if e.text().strip() and self.document().characterCount() > old_len:
            self.complete()
        elif self.completer.popup().isVisible():
            self.completer.popup().hide()  # Fix "popup hangs around" bug


if __name__ == "__main__":
    import sys
    from PySide6.QtCore import QCommandLineOption, QCommandLineParser
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    te = CompletingPlainTextEdit()
    te.completions.setStringList(["def", "class", "print", "copper"])
    te.show()
    sys.exit(app.exec())