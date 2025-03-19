from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from pylive.VisualCode_v5.py_graph_model import PyGraphModel


""" WIDGETS """
def label(text:str)->QLabel:
    label = QLabel()
    label.setText(text)
    return label

def patch_label(label:QLabel, text:str):
    if label.text() != text:
        label.setText(text)

def scrollarea(widget:QWidget):
    area = QScrollArea()
    area.setWidget(widget)
    return area

""" WIDGETS """
def combobox(*, items:list[str], current_index:int=0, on_current_index_changed:Callable|None=None)->QComboBox:
    widget = QComboBox()
    widget.insertItems(0, items)
    if on_current_index_changed:
        widget.currentIndexChanged.connect(on_current_index_changed)
    return widget

def patch(widget, **kwargs):
    ...

def patch_combobox(widget:QComboBox, *, items:list[str], current_index:int=0,  on_current_index_changed:Callable|None=None):
    ### IMPLEMENT THIS
    widget.blockSignals(True)

    # udate items
    widget.clear()
    widget.insertItems(0, items)

    # patch current index
    widget.setCurrentIndex(current_index)

    # patch signals
    widget.currentIndexChanged.disconnect()
    if on_current_index_changed:
        widget.currentIndexChanged.connect(on_current_index_changed)

    widget.blockSignals(False)

def spinbox(*, value:int=0, on_value_changed:Callable|None=None)->QSpinBox:
    widget = QSpinBox()
    widget.setValue(value)
    if on_value_changed:
        widget.valueChanged.connect(on_value_changed)
    return widget

def patch_spinbox(widget:QSpinBox, *, value:int=0, on_value_changed:Callable|None=None):
    if widget.value() != value:
        widget.setValue(value)

    widget.valueChanged.disconnect()

    if on_value_changed:
        widget.valueChanged.connect(on_value_changed)

def lineedit(*, text="", /, placeholder="", on_text_changed:Callable|None=None)->QLineEdit:
    lineedit = QLineEdit(text)
    lineedit.setPlaceholderText(placeholder)
    if on_text_changed:
        lineedit.textChanged.connect(on_text_changed)

    return lineedit

def patch_lineedit(widget:QLineEdit, *, text="", /, placeholder="", onTextChanged:Callable|None=None):
    if widget.text() != text:
        widget.setText(text)
    if widget.placeholderText() != placeholder:
        widget.setPlaceholderText(placeholder)

    widget.textChanged.disconnect()
    if onTextChanged:
        widget.textChanged.connect(onTextChanged)

from pylive.qt_components.QPathEdit import QPathEdit
import pathlib
def pathedit(path:pathlib.Path=pathlib.Path.cwd(), *,  placeholder="", on_path_changed:Callable|None=None)->QLineEdit:
    pathedit = QPathEdit(path)
    pathedit.setPlaceholderText(placeholder)
    if on_path_changed:
        pathedit.pathChanged.connect(on_path_changed)

    return pathedit

def patch_pathedit(widget:QPathEdit, *, path:pathlib.Path=pathlib.Path.cwd(), /, placeholder="", on_path_changed:Callable|None=None):
    if widget.path() != path:
        widget.setPath(path)

    if widget.placeholderText() != placeholder:
        widget.setPlaceholderText(placeholder)

    widget.pathChanged.disconnect()
    if on_path_changed:
        widget.pathChanged.connect(on_path_changed)

def menubar(*, actions:Sequence[QAction])->QMenuBar:
    menubar = QMenuBar()
    for action in actions:
        menubar.addAction(action)
    return menubar

""" LAYOUTS """
def boxlayout(*, direction:QBoxLayout.Direction, children:Sequence[QWidget|QLayout|QLayoutItem], stretch:Sequence[int]=[])->QBoxLayout:
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

def patch_vboxlayout(layout:QVBoxLayout, children:Sequence[QWidget|QLayout|QLayoutItem], stretch:Sequence[int]=[]):
    count = layout.count()
    for i, child in enumerate(children):
        if i<count:
            if type(child) == type(layout.itemAt(i)):
                match child:
                    case QWidget():
                        ...
                    case QLayout():
                        ...
                    case QLayoutItem():
                        ...
        else:
            match child:
                case QWidget():
                    layout.addWidget(child)
                case QLayout():
                    layout.addLayout(child)
                case QLayoutItem():
                    layout.addItem(child)

        layout.itemAt(i)

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

def spacer(w:int, h:int, wPolicy=QSizePolicy.Policy.Minimum, hPolicy=QSizePolicy.Policy.Minimum):
    return QSpacerItem(w, h, wPolicy, hPolicy)

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

