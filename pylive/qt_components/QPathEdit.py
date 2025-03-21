from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import pathlib
import pathlib


class QPathEdit(QLineEdit):
    pathChanged = Signal(str)
    
    def __init__(self, 
        path:pathlib.Path=pathlib.Path.cwd(), 
        parent:QWidget|None=None
    ):
        super().__init__(str(path), parent=parent)
        # self.setClearButtonEnabled(True)
        dir_pixmap = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        action = self.addAction(dir_pixmap, QLineEdit.ActionPosition.TrailingPosition)
        action.triggered.connect(self.open)
        
        # Store a reference to the dialog to prevent it from being garbage collected
        self._file_dialog = None
        
    def open(self):
        # Create a non-modal dialog
        filename, selectedFilter = QFileDialog.getOpenFileName(self)
        if filename:
            self.setText(filename)
        
    def setText(self, text: str) -> None:
        super().setText(text)
        self.pathChanged.emit(self.path())
        
    def path(self)->pathlib.Path:
        return pathlib.Path(self.text())
        
    def setPath(self, path:pathlib.Path|str):
        self.setText(str(path))


if __name__ == "__main__":
    app = QApplication()
    window = QWidget()
    main_layout = QVBoxLayout()
    window.setLayout(main_layout)
    path_edit = QPathEdit()

    main_layout.addWidget(path_edit)
    window.show()
    app.exec()