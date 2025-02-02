
from collections import defaultdict
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


from dataclasses import dataclass, field
from pylive.QtGraphEditor.fields_model import FieldsModel


# class NodeItem(Protocol):
#     kind: Literal["UniqueFunction", "Expression", "ModuleFunction"]
#     label:str
#     dirty:bool=True
#     fields: FieldsModel = field(default_factory=FieldsModel)

# @dataclass
# class ExpressionItem(NodeItem):
#     expression:str    

# @dataclass
# class ModuleFunctionItem(NodeItem):
#     source:str
#     module: str
#     func: str 

# @dataclass
# class LocalFunctionItem:
#     definition: QModelIndex

@dataclass
class UniqueFunctionItem:
    kind: Literal["UniqueFunction", "Expression", "ModuleFunction"]
    label:str
    source:str  
    dirty:bool
    fields: FieldsModel


class NodesModel(QAbstractItemModel):



    def __init__(self, parent: QObject|None=None) -> None:
        super().__init__(parent)
        self._nodes:list[UniqueFunctionItem] = []
        
    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows in the model."""
        return len(self._nodes)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role==Qt.ItemDataRole.DisplayRole:
            return ["name", "definition", "dirty", "fields"][section]
        else:
            return super().headerData(section, orientation, role)

    def columnCount(self, parent: QModelIndex|QPersistentModelIndex = QModelIndex()) -> int:
        return 2

    def data(self, index: QModelIndex|QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._nodes):
            return None

        item = self._nodes[index.row()]

        if index.column()==0:
            if role==Qt.ItemDataRole.DisplayRole:
                first_line = item.source.split("\n")[0]
                import re
                pattern = r"def\s+(?P<func_name>\w+)\s*\("
                match = re.search(pattern, first_line)
                if match:
                    return match.group("func_name") 
                else:
                    import textwrap
                    return textwrap.shorten(first_line, width=12, placeholder="...")

            elif role==Qt.ItemDataRole.EditRole:
                return item.source

            elif role==Qt.ItemDataRole.BackgroundRole:
                return None if item.dirty else QColor("red")

        elif index.column()==1:
            if role==Qt.ItemDataRole.DisplayRole or role==Qt.ItemDataRole.EditRole:
                return str(item.label)

        elif index.column()==2:
            if role==Qt.ItemDataRole.DisplayRole or role==Qt.ItemDataRole.EditRole:
                return bool(item.dirty)

        return None

    def setUniqueFunctionSource(self, index:QModelIndex, source:str):
        row = index.row()
        node_item = self._nodes[row]
        node_item.source = source
        self.dataChanged.emit(
            index.siblingAtColumn(0), index.siblingAtColumn(0), 
            [
                Qt.ItemDataRole.DisplayRole, 
                Qt.ItemDataRole.EditRole,
                Qt.ItemDataRole.BackgroundRole
            ]
        )

    def setData(self, index: QModelIndex|QPersistentModelIndex, value:Any, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._nodes):
            return None

        item = self._nodes[index.row()]

        if index.column()==0:
            if role==Qt.ItemDataRole.EditRole:
                item.source = value

        elif index.column()==1 and role==Qt.ItemDataRole.EditRole:
            item.label = str(value)

        elif index.column()==2 and role==Qt.ItemDataRole.EditRole:
            item.dirty = bool(value)

        return None

    def insertRows(self, row:int, count:int, parent=QModelIndex()):
        if len(self._nodes) <= row or row < 0:
            return False

        self.beginInsertRows(parent, row, row + count - 1)
        for _ in range(count):
            node = UniqueFunctionItem(
                kind="UniqueFunction",
                label="",
                source="""def func():/n  ...""",
                dirty=True,
                fields=FieldsModel()
            )
            self._nodes.append(node)
        self.endInsertRows()
        return True

    def addNodeItem(self, item:UniqueFunctionItem):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._nodes.append(item)
        self.endInsertRows()

    def nodeItem(self, row)->UniqueFunctionItem:
        return self._nodes[row]

    def nodeItemFromIndex(self, index:QModelIndex)->UniqueFunctionItem|None:
        if index.isValid() and index.model() == self:
            row = index.row()
            if row>=0 and row < len(self._nodes):
                return self._nodes[row]

    def insertNodeItem(self, row:int, item:UniqueFunctionItem):
        self.beginInsertRows(QModelIndex(), row, row)
        self._nodes.insert(row, item)
        self.endInsertRows()
        return True

    def removeRows(self, row:int, count:int, parent=QModelIndex()):
        """Removes rows from the model."""
        if row < 0 or row + count > len(self._nodes):
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        for row in reversed(range(row, row+count)):
            del self._nodes[row]
        self.endRemoveRows()
        return True

    def clear(self):
        self.blockSignals(True)
        self.removeRows(0, self.rowCount(), QModelIndex())
        self.blockSignals(False)
        self.modelReset.emit()

    def flags(self, index):
        """Returns the item flags for the given index."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable

    def index(self, row:int, column:int, parent=QModelIndex()):
        if parent.isValid():
            return QModelIndex()

        return self.createIndex(row, column)

    def parent(self, index:QModelIndex|QPersistentModelIndex)->QModelIndex:
        return QModelIndex()  # No parent for this flat model


if __name__ == "__main__":
    app = QApplication()
    window = QWidget()
    main_layout = QHBoxLayout()
    model = NodesModel()
    table_view = QTableView()
    table_view.setModel(model)
    list_view = QListView()
    list_view.setModel(model)
    add_field_action = QAction("add",window)
    def add_field():
        model.insertNodeItem(0, NodeItem("new node", QPersistentModelIndex(), FieldsModel(), True))

    add_field_action.triggered.connect(add_field)
    menubar = QMenuBar()
    menubar.addAction(add_field_action)
    main_layout.setMenuBar(menubar)
    main_layout.addWidget(table_view)
    main_layout.addWidget(list_view)
    window.setLayout(main_layout)
    window.show()
    app.exec()