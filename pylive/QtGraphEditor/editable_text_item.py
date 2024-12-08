from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

class EditableTextItem(QGraphicsTextItem):
	textChanged = Signal(str)
	def __init__(self, text:str="", parent=None):
		super().__init__(text, parent)
		self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)  # Allow focus events
		self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)  # Initially non-editable
		# self.setFlag(QGraphicsItem.ItemIsSelectable, True)

		# Center-align the text within the item
		text_option = QTextOption()
		text_option.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.document().setDefaultTextOption(text_option)

		# Remove the default margins
		self.document().setDocumentMargin(0)

		self.document().contentsChanged.connect(lambda: self.textChanged.emit(self.document().toPlainText()))

	def setText(self, text:str):
		self.document().setPlainText(text)

	def mouseDoubleClickEvent(self, event):
		# Enable editing on double-click
		"""parent node must manually cal the double click event,
		because an item nor slectable nor movable will not receive press events"""
		self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
		self.setFocus(Qt.FocusReason.MouseFocusReason)

		click = QGraphicsSceneMouseEvent(QEvent.Type.GraphicsSceneMousePress)
		click.setButton(event.button())
		click.setPos(event.pos())
		self.mousePressEvent(click)
		# super().mouseDoubleClickEvent(event)

	def focusOutEvent(self, event: QFocusEvent):
		# When the item loses focus, disable editing
		self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
		super().focusOutEvent(event)