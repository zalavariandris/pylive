from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt, QVariant

class PeopleModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.people = []

    def setPeople(self, people):
        self.beginResetModel()
        self.people = people
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.people)

    def columnCount(self, parent=QModelIndex()):
        return 3  # Name, Age, Occupation

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section == 0:
                    return "Name"
                elif section == 1:
                    return "Age"
                elif section == 2:
                    return "Occupation"
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()

        person = self.people[index.row()]

        if role == Qt.DisplayRole:
            if index.column() == 0:
                return person.name
            elif index.column() == 1:
                return person.age
            elif index.column() == 2:
                return person.occupation
        return QVariant()

    def index(self, row, column, parent=QModelIndex()):
        if parent.isValid():
            return QModelIndex()
        return self.createIndex(row, column)

    def parent(self, index):
        return QModelIndex()  # No parent for this flat model
