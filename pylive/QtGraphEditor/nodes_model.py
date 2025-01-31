
from collections import defaultdict
from typing import *
from typing_extensions import deprecated
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from networkx.classes import graphviews

from pylive.qt_options_dialog import QOptionDialog
from pylive.utils import group_consecutive_numbers
from pylive.utils.qt import modelReset, signalsBlocked


from dataclasses import dataclass, field
from fields_model import FieldsModel


@dataclass
class NodeItem:
    name: str
    #content
    definition: QPersistentModelIndex = field(default_factory=QPersistentModelIndex)
    fields: FieldsModel = field(default_factory=FieldsModel)
    dirty:bool=True


class NodesModel(QAbstractItemModel):
    def __init__(self, parent: QObject|None=None) -> None:
        super().__init__(parent)
        self._nodes:list[NodeItem] = []
        
    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows in the model."""
        return len(self._nodes)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role==Qt.ItemDataRole.DisplayRole:
            return ["name", "definition", "dirty", "fields"][section]
        else:
            return super().headerData(section, orientation, role)

    def columnCount(self, parent: QModelIndex|QPersistentModelIndex = QModelIndex()) -> int:
        return 4

    def data(self, index: QModelIndex|QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._nodes):
            return None

        item = self._nodes[index.row()]

        if role==Qt.ItemDataRole.DisplayRole or role==Qt.ItemDataRole.EditRole:
            match index.column():
                case 0:
                    return item.name
                case 1:
                    return item.definition.data(Qt.ItemDataRole.DisplayRole)
                case 2:
                    return f"{item.dirty}"
                case 3:
                    if item.fields and item.fields.rowCount():
                        field_names = [
                            item.fields.index(row, 0).data(Qt.ItemDataRole.DisplayRole)
                            for row in range(item.fields.rowCount())
                        ]
                        return ", ".join(field_names)
                    else:
                        return ""
        elif role == Qt.ItemDataRole.UserRole:
            return item

        return None

    def setData(self, index: QModelIndex|QPersistentModelIndex, value:Any, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._nodes):
            return None

        item = self._nodes[index.row()]
        if index.column()==0:
            item.name = f"{value}"
            self.dataChanged.emit(index, index, [role])
            return True

        elif index.column()==1:
            assert isinstance(value, QPersistentModelIndex)
            item.definition = value
            self.dataChanged.emit(index, index, [role])
            return True
            
        else:
            return False

    def insertRows(self, row:int, count:int, parent=QModelIndex()):
        if len(self._nodes) <= row or row < 0:
            return False

        self.beginInsertRows(parent, row, row + count - 1)
        for _ in range(count):
            node = NodeItem(
                name= "",
                definition=QPersistentModelIndex(),
                dirty= True,
                fields= FieldsModel()
            )
            self._nodes.append(node)
        self.endInsertRows()
        return True

    def addNodeItem(self, item:NodeItem):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())

        self._nodes.append(item)
        self.endInsertRows()

    def insertNodeItem(self, row:int, item:NodeItem):
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