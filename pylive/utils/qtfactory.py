from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

def label(text:str)->QLabel:
	lbl = QLabel(text)
	return lbl

def vboxlayout(*children)->QVBoxLayout:
	layout = QVBoxLayout()
	for child in children:
		match child:
			case QWidget():
				layout.addWidget(child)
			case QLayout():
				layout.addLayout(child)
			case QLayoutItem():
				layout.addItem(child)

	return layout


type FormRowType=tuple[QWidget, QWidget]\
	| QLayout\
	| QWidget\
	| tuple[QWidget, QLayout]\
	| tuple[str, QLayout]\
	| tuple[str, QWidget]

def formlayout(*rows:FormRowType):
	layout = QFormLayout()
	layout.setContentsMargins(0,0,0,0)
	layout.setSpacing(0)

	"""
	While the folowing structural matching to match all the possible overloads
	is unnecessary. We explicitelly do it anyway for debugging pourposes.
	"""
	for row in rows: 
		match row:
			case (QWidget(), QWidget()):
				layout.addRow(row[0], row[1])
			case QLayout():
				layout.addRow(row)
			case QWidget():
				layout.addRow(row)
			case (QWidget(), QLayout()):
				layout.addRow(row[0], row[1])
			case (str(), QLayout()):
				layout.addRow(row[0], row[1])
			case (str(), QWidget()):
				layout.addRow(row[0], row[1])
			case _:
				raise NotImplementedError
	return layout

def lineedit(contents="", /, placeholder="", onTextChanged:Callable|None=None)->QLineEdit:
	lineedit = QLineEdit(contents)
	lineedit.setPlaceholderText(placeholder)
	if onTextChanged:
		print("connect textChanged")
		lineedit.textChanged.connect(onTextChanged)

	return lineedit