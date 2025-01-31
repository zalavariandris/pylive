from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class TileWidget(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)

        self._avatar = QLabel("<h2>Py</h2>")
        self._heading = QLabel("<h2>Heading</h2>")
        self._subheading = QLabel("subheading")

        layout = QGridLayout()
        layout.addWidget(self._avatar,     0, 0, 2, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._heading,    0, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)   
        layout.addWidget(self._subheading, 1, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.setColumnStretch(0,0)
        layout.setColumnStretch(1,1)
        self._avatar.hide()
        self.setLayout(layout)

    def setAvatar(self, avatar:str):
        self._avatar.setText(avatar)

    def setHeading(self, heading:str):
        self._heading.setText(f"<h2>{heading}</h2>")

    def setSubHeading(self, subheading:str):
        self._subheading.setText(subheading)


if __name__ == "__main__":
    app = QApplication()

    inspector = TileWidget()
    main_layout = QVBoxLayout()
    main_layout.addWidget(inspector)
    window = QWidget()
    window.setLayout(main_layout)
    window.show()
    app.exec()