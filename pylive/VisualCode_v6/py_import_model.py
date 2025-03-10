from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import sys
from pathlib import *

class PyImportsModel(QAbstractItemModel):
    def __init__(self, parent:QObject|None=None):
        super().__init__(parent=parent)
        import pkgutil

        self._root = Path().cwd()
        self._enabled_modules:set[str] = set()

    def setRoot(self, path:str|Path):
        self.beginResetModel()
        self._root = Path(path)
        self.endResetModel()
        
    def _get_local_modules(self)->list[str]:
        modules = [file.stem for file in self._root.iterdir() if file.is_file() and file.suffix==".py" and file.name!="__init__.py"]
        return modules

    def rowCount(self, /, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        modules = self._get_local_modules()
        return len(modules)

    def columnCount(self, /, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return 2

    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        modules = self._get_local_modules()
        module_name = modules[index.row()]
        if index.column() == 0: #name
            if role == Qt.ItemDataRole.DisplayRole:
                return module_name

        if index.column() == 1: #name
            if role == Qt.ItemDataRole.DisplayRole:
                return module_name in self._enabled_modules
            if role == Qt.ItemDataRole.EditRole:
                return module_name in self._enabled_modules

        return None

    def setData(self, index: QModelIndex | QPersistentModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if index.column()==1:
            if role == Qt.ItemDataRole.EditRole:
                module_name = self._get_local_modules()[index.row()]
                if value and module_name not in self._enabled_modules:
                    self._enabled_modules.add(module_name)
                    self.dataChanged.emit(index, index)
                
                if not value and module_name in self._enabled_modules:
                    self._enabled_modules.remove(module_name)
                    self.dataChanged.emit(index, index)
        return super().setData(index, value, role)

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column()==1:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal:
            return ["name", "imported"][section]
        return super().headerData(section, orientation, role)

    def index(self, row: int, column: int, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> QModelIndex:
        return self.createIndex(row, column)

    def parent(self, index:QModelIndex)->QModelIndex: #type: ignore
        return QModelIndex()
