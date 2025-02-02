from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

class ListTileDelegate(QStyledItemDelegate):
	def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex|QPersistentModelIndex) -> QWidget:
		return super().createEditor(parent, option, index)

	def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex|QPersistentModelIndex) -> None:
		return super().paint(painter, option, index)

	def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex|QPersistentModelIndex) -> QSize:
		return super().sizeHint(option, index)

	def setEditorData(self, editor: QWidget, index: QModelIndex|QPersistentModelIndex) -> None:
		return super().setEditorData(editor, index)

	def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex|QPersistentModelIndex) -> None:
		return super().updateEditorGeometry(editor, option, index)

	def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex|QPersistentModelIndex) -> None:
		return super().setModelData(editor, model, index)