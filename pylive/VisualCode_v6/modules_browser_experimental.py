from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


# class ModulesModel(QAbstractItemModel):
#     def __init__(self, parent:QObject|None):
#         super().__init__(parent=parent)

#     def rowCount(self, /, parent: QModelIndex | QPersistentModelIndex = ...) -> int:
#         return 0

#     def columnCount(self, /, parent: QModelIndex | QPersistentModelIndex = ...) -> int:
#         return super().columnCount(parent)

#     def headerData(self, section: int, orientation: Qt.Orientation, /, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
#         return super().headerData(section, orientation, role)


# class ModulesView(QWidget):
#     def __init__(self, parent:QWidget|None=None):
#         super().__init__(parent=parent)
#         self.setWindowTitle("Modules")
#         self._model:ModulesModel|None = None
#         self.list_view = QListView()

#         layout = QVBoxLayout()
#         layout.addWidget(self.list_view)
#         self.setLayout(layout)


#     def setModel(self, model:ModulesModel):
#         self.list_view.setModel(model)

import sys
import os
import importlib.util

# Check if the module is built-in
def is_builtin(module_name):
    return module_name in sys.builtin_module_names

# Check if the module is part of the standard library
def is_standard_library(module_name):
    return module_name in sys.stdlib_module_names

# Check if the module is local (in the current directory or a subdirectory)
def is_local(module_name):
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        return False  # Module not found
    
    # Check if the module is located in the current working directory
    return os.path.dirname(spec.origin).startswith(os.getcwd())

# Main function to determine module type
def module_type(module_name):
    if is_builtin(module_name):
        return "Built-in"
    elif is_standard_library(module_name):
        return "Standard Library"
    elif is_local(module_name):
        return "Local"
    else:
        return "Third-party (Installed)"


class PyModulesModel(QAbstractItemModel):
    def __init__(self, parent:QObject|None=None):
        super().__init__(parent=parent)
        import pkgutil

        local_modules = [
            module.name for module in pkgutil.iter_modules()
            if module.module_finder and module.module_finder.path not in sys.base_prefix
        ]

        self._modules = [module for module in pkgutil.iter_modules() if not module.name.startswith("_")]

    def rowCount(self, /, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return len(self._modules)

    def columnCount(self, /, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return 2

    def data(self, index: QModelIndex | QPersistentModelIndex, /, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if index.column() == 0: #name
            if role == Qt.ItemDataRole.DisplayRole:
                module = self._modules[index.row()]
                return module.name

        if index.column() == 1: # 'origin'
            if role == Qt.ItemDataRole.DisplayRole:
                module = self._modules[index.row()]
                return module_type(module.name)


        return None

    def headerData(self, section: int, orientation: Qt.Orientation, /, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        return super().headerData(section, orientation, role)

    def index(self, row: int, column: int, /, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> QModelIndex:
        return self.createIndex(row, column)

    def parent(self, index):
        return QModelIndex()

