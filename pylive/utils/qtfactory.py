from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

""" WIDGETS """
def patch_label(label:QLabel, text:str):
    label.setText(text)

def label(text:str)->QLabel:
    lbl = QLabel()
    patch_label(lbl, text=text)
    return lbl

""" LAYOUTS """
def boxlayout(direction:QBoxLayout.Direction, children:Sequence[QWidget|QLayout|QLayoutItem], stretch:Sequence[int]=[])->QBoxLayout:
    layout = QBoxLayout(direction)
    layout.setSpacing(0)
    layout.setContentsMargins(0,0,0,0)
    for child in children:
        match child:
            case QLayoutItem():
                layout.addItem(child)
            case QLayout():
                layout.addLayout(child)
            case QWidget():
                layout.addWidget(child)
            
            

    return layout

def vboxlayout(children:Sequence[QWidget|QLayout|QLayoutItem], stretch:Sequence[int]=[])->QVBoxLayout:
    layout = QVBoxLayout()
    layout.setSpacing(0)
    layout.setContentsMargins(0,0,0,0)
    for child in children:
        match child:
            case QWidget():
                layout.addWidget(child)
            case QLayout():
                layout.addLayout(child)
            case QLayoutItem():
                layout.addItem(child)

    for i, value in enumerate(stretch):
        layout.setStretch(i, value)

    return layout

def widgetitem(widget: QWidget, alignment:Qt.AlignmentFlag=0):
    layout_item = QWidgetItem(widget)
    layout_item.setAlignment(alignment)
    return layout_item

def hboxlayout(children:Sequence[QWidget|QLayout|QLayoutItem], stretch:Sequence[int]=[])->QHBoxLayout:
    layout = QHBoxLayout()
    layout.setSpacing(0)
    layout.setContentsMargins(0,0,0,0)

    for i, child in enumerate(children):
        match child:
            case QWidget():
                layout.addWidget(child)

            case QLayout():
                layout.addLayout(child)
            case QLayoutItem():
                layout.addItem(child)

    for i, value in enumerate(stretch):
        layout.setStretch(i, value)



    return layout

def splitter(orientation:Qt.Orientation, children:Sequence[QWidget])->QSplitter:
    splitter = QSplitter(orientation)
    for child in children:
        splitter.addWidget(child)

    count = len(children)
    splitter.setSizes([splitter.width()//len(children) for _ in range( count )])
    return splitter

def tabwidget(pages:dict[str, QWidget]):
    tabwidget = QTabWidget()
    tabwidget.setDocumentMode(True)

    for label, page in pages.items():
        tabwidget.addTab(page, label)

    return tabwidget

def widget(layout:QLayout):
    widget = QWidget()
    widget.setLayout(layout)
    return widget

def gridlayout(cells:dict[tuple[int, int]|tuple[int,int,int]|tuple[int,int,int,int], QWidget|QLayoutItem])->QGridLayout:
    layout = QGridLayout()
    for position, element in cells.items():
        match element:
            case QWidget():
                layout.addWidget(element, *position)
            case QLayoutItem():
                layout.addItem(element, *position)
                
        

    return layout


# # def addItem  (item: QLayoutItem, row:int, column:int, rowSpan:int = 1, columnSpan:int = 1, alignment:Qt.AlignmentFlag.Alignment = Qt.Alignment())

# def addLayout(layout, row:int,     column:int, alignment:Qt.AlignmentFlag = 0):
#     ...
# def addWidget(widget, row:int,     column:int, alignment:Qt.AlignmentFlag = 0):
#     ...

# def addLayout(layout, row:int,     column:int,     rowSpan:int, columnSpan:int, Qt::Alignment alignment = 0)
# def addWidget(widget, fromRow:int, fromColumn:int, rowSpan:int, columnSpan:int, Qt::Alignment alignment = 0)


# gridlayout([
#     ()
# ])

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