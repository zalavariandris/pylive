from dataclasses import dataclass
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import inspect


class PyFunctionsModel(QAbstractItemModel):
    ErrorRole = Qt.ItemDataRole.UserRole+1
    """Model for the detail view"""
    def __init__(self):
        super().__init__()
        self._sources:list[str] = []

        self./
        self._cached_functions:dict[str, Callable] = dict()
        self._errors:dict[Callable, Exception] = dict()

    def rowCount(self, parent: QModelIndex|QPersistentModelIndex = QModelIndex()) -> int:
        return len(self._sources)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role==Qt.ItemDataRole.DisplayRole:
            return ["name", "source"][section]
        else:
            return super().headerData(section, orientation, role)

    def columnCount(self, parent: QModelIndex|QPersistentModelIndex = QModelIndex()) -> int:
        return 2

    def functionName(self, row:int):
        if 0 <= row and row < len(self._sources):
            func = self._sources[row]
            return func.__name__

    def functionSource(self, row:int):
            return self._sources[row]

    def setFunctionSource(self, row:int, source:str)->bool:
        capture = {'__builtins__':__builtins__}
        try:
            exec(source, capture)
        except SyntaxError as err:
            print(f"SyntaxError: {err}")
            return False
        except Exception as err:
            print(f"Exception occured: {err}")
            return False

        capture_functions:list[tuple[str, Callable]] = []
        for name, attribute in capture.items():
            if name!='__builtins__':
                if callable(attribute) and not inspect.isclass(attribute):
                    capture_functions.append( (name, attribute) )

        if len(capture_functions)!=1:
            return False

        name, func = capture_functions[0]
        if not callable(func):
            return False

        self._functions[row] = func
        self.dataChanged.emit(self.index(row, 0), self.index(row, 2))
        return True

    def functionError(self, row:int)->Exception|None:
        func = self._functions[row]
        return self._errors.get(func, None)

    def data(self, index: QModelIndex|QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._functions):
            return None

        func = self._functions[index.row()]

        match index.column():
            case 0: #name
                match role:
                    case Qt.ItemDataRole.DisplayRole:
                        return self.functionName(index.row())

                    case Qt.ItemDataRole.DecorationRole:
                        func = self._functions[index.row()]
                        QColor("red")
                        if func in self._errors:
                            return QColor("red")

                    case Qt.ItemDataRole.UserRole:
                        func = self._functions[index.row()]
                        return func

            case 1: #source
                print("!!!!!!!!!!!!!!!!!")
                print(self._functions)
                if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                    return self.functionSource(index.row())


        return None

    def parent(self, index: QModelIndex|QPersistentModelIndex) -> QModelIndex:
        return QModelIndex()

    def setData(self, index: QModelIndex|QPersistentModelIndex, value:Any, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._functions):
            return False
        return False

    def index(self, row: int, column: int, parent: QModelIndex|QPersistentModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        return self.createIndex(row, column)

    def functionFromIndex(self, index:QModelIndex|QPersistentModelIndex)->Callable|None:
        if index.isValid() and index.model() == self:
            row = index.row()
            if row>=0 and row < len(self._functions):
                return self._functions[row]

    ### 
    def insertFunction(self, row:int, func:Callable):
        assert isinstance(row, int)
        assert callable(func)
        self.beginInsertRows(QModelIndex(), row, row)
        self._functions.insert(row, func)
        self.endInsertRows()
        return True

    def insertRows(self, row: int, count: int, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> bool:
        assert isinstance(row, int)
        def func():
            ...
        assert callable(func)
        self.beginInsertRows(QModelIndex(), row, row+count-1)
        self._functions[row:row] = [func for _ in range(count)]
        self.endInsertRows()
        return True

    def removeRows(self, row:int, count:int, parent=QModelIndex()):
        """Removes rows from the model."""
        if row < 0 or row + count > len(self._functions):
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        for row in reversed(range(row, row+count)):
            del self._functions[row]
        self.endRemoveRows()
        return True

    def flags(self, index: QModelIndex|QPersistentModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column()==1:
            flags|=Qt.ItemFlag.ItemIsEditable
        return flags


if __name__ == "__main__":
    
    from pylive.QtScriptEditor.script_edit import ScriptEdit
    app = QApplication()
    window = QWidget()
    window.setWindowTitle("PyFunctions example")
    main_layout = QHBoxLayout()
    model = PyFunctionsModel()

    selection = QItemSelectionModel(model)
    table_view = QTableView()
    table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
    table_view.setModel(model)
    table_view.setSelectionModel(selection)

    list_view = QListView()
    list_view.setModel(model)
    list_view.setSelectionModel(selection)

    function_editor = ScriptEdit()
    def show_source_in_editor():
        current = selection.currentIndex().siblingAtColumn(1)
        print(current)
        if source := model.data(current, Qt.ItemDataRole.EditRole):
            function_editor.setPlainText(source)
        else:
            function_editor.setPlainText("")

    selection.currentChanged.connect(show_source_in_editor)

    def set_current_source():
        print("set current source")
        new_source = function_editor.toPlainText()
        current = selection.currentIndex().siblingAtColumn(1)
        model.setFunctionSource(current.row(), new_source)
        

    function_editor.textChanged.connect(set_current_source)

    from pathlib import Path
    def hello_function(name:str)->str:
        return f"Hello {name}!"

    def _():
        return None

    menubar = QMenuBar()

    for func in [print, Path.read_text, hello_function, _]:
        action = QAction(f"add {func.__name__}", window)
        def add_item(func:Callable):
            assert callable(func), f"got: {func}"
            model.insertFunction(model.rowCount(), func)
        action.triggered.connect(lambda checked, func=func: add_item(func))
        menubar.addAction(action)


    

    main_layout.setMenuBar(menubar)
    main_layout.addWidget(table_view)
    main_layout.addWidget(list_view)
    main_layout.addWidget(function_editor)
    window.setLayout(main_layout)
    window.show()
    app.exec()