from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

class Panel(QWidget):
    def __init__(self, direction=QBoxLayout.LeftToRight, children=[], menuBar=None, parent=None):
        super().__init__(parent)
        self.setLayout(QBoxLayout(direction))
        self.layout().setContentsMargins(0,0,0,0)
        if menuBar:
            self.layout().setMenuBar(menuBar)

        for child in children:
            self.layout().addWidget(child)
