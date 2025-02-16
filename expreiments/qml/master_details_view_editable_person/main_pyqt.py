from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtQml import *

import sys
import os

class Person(QObject):
    def __init__(self, name, age, occupation, description):
        super().__init__()
        self._name = name
        self._age = age
        self._occupation = occupation
        self._description = description

    @pyqtProperty(str)
    def name(self):
        return self._name

    @pyqtProperty(int)
    def age(self):
        return self._age

    @pyqtProperty(str)
    def occupation(self):
        return self._occupation

    @pyqtProperty(str)
    def description(self):
        return self._description

class PersonModel(QAbstractListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    AgeRole = Qt.ItemDataRole.UserRole + 2
    OccupationRole = Qt.ItemDataRole.UserRole + 3
    DescriptionRole = Qt.ItemDataRole.UserRole + 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self._persons = []
        
        # Add sample data
        self.add_person("John Doe", 30, "Software Developer", "Experienced developer with focus on Qt/QML")
        self.add_person("Jane Smith", 28, "UX Designer", "Creative designer specializing in mobile interfaces")
        self.add_person("Bob Johnson", 35, "Project Manager", "Certified project manager with 10 years experience")

    def roleNames(self):
        return {
            self.NameRole: b"name",
            self.AgeRole: b"age",
            self.OccupationRole: b"occupation",
            self.DescriptionRole: b"description"
        }

    def rowCount(self, parent=QModelIndex()):
        return len(self._persons)

    def data(self, index, role):
        if not index.isValid():
            return None

        if 0 <= index.row() < self.rowCount():
            person = self._persons[index.row()]

            if role == self.NameRole:
                return person.name
            elif role == self.AgeRole:
                return person.age
            elif role == self.OccupationRole:
                return person.occupation
            elif role == self.DescriptionRole:
                return person.description

        return None

    @pyqtSlot(str, int, str, str)
    def add_person(self, name, age, occupation, description):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._persons.append(Person(name, age, occupation, description))
        self.endInsertRows()

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        
        if 0 <= index.row() < self.rowCount():
            person = self._persons[index.row()]
            if role == self.NameRole:
                person._name = value
            elif role == self.AgeRole:
                person._age = value
            elif role == self.OccupationRole:
                person._occupation = value
            elif role == self.DescriptionRole:
                person._description = value
            else:
                return False
                
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    # Add this method to handle the edit signal from QML
    @pyqtSlot(int, str, int, str, str)
    def edit_person(self, index, name, age, occupation, description):
        idx = self.index(index, 0)
        self.setData(idx, name, self.NameRole)
        self.setData(idx, age, self.AgeRole)
        self.setData(idx, occupation, self.OccupationRole)
        self.setData(idx, description, self.DescriptionRole)

def setup_qt_environment():
    dirname = os.path.dirname(os.path.dirname(__file__))
    plugin_path = os.path.join(dirname, 'plugins')
    os.environ['QT_PLUGIN_PATH'] = plugin_path
    qml_path = os.path.join(dirname, 'qml')
    os.environ['QML2_IMPORT_PATH'] = qml_path
    if sys.platform == 'win32':
        os.environ['PATH'] = dirname + os.pathsep + os.environ['PATH']
    # QQuickStyle.setStyle("Basic")



def main_old():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    person_model = PersonModel()
    engine.rootContext().setContextProperty("personModel", person_model)

    qml_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.qml")
    engine.load(qml_file)

    if not engine.rootObjects():
        print("Failed to load QML file!")
        return -1

    return app.exec()

def main():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    person_model = PersonModel()
    engine.rootContext().setContextProperty("personModel", person_model)
    
    # Load the QML file
    # Assuming the QML file is named 'main.qml' and is in the same directory
    qml_file = QUrl.fromLocalFile("main.qml")
    engine.load(qml_file)

    if not engine.rootObjects():
        sys.exit(-1)

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())

if __name__ == "__main__":
    sys.exit(main())
