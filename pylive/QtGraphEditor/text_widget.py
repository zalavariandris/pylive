from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


class TextWidget(QGraphicsWidget):
    """# A simple QGraphicsWidget to ise with QGraphicsLayout"""

    def __init__(self, text, parent=None):
        super().__init__(parent)
        # Create the text item
        self.text_item = QGraphicsTextItem(text, self)
        self.text_item.document().setDocumentMargin(0)
        self.text_item.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextEditorInteraction
        )
        self.text_item.setAcceptedMouseButtons(
            Qt.MouseButton.NoButton
        )  # Transparent to mouse events
        self.text_item.setEnabled(False)

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.set_line_height(1.1)

    def toPlainText(self):
        return self.text_item.toPlainText()

    def setPlainText(self, text: str):
        return self.text_item.setPlainText(text)

    def set_line_height(self, line_height):
        """Set the line height for the text."""
        cursor = QTextCursor(self.text_item.document())
        cursor.select(QTextCursor.SelectionType.Document)

        # Configure block format
        block_format = QTextBlockFormat()
        block_format.setLineHeight(100, 1)
        cursor.mergeBlockFormat(block_format)

    def sizeHint(self, which, constraint=QSizeF()):
        text_size = QSize(self.text_item.document().size().toSize())
        return text_size
