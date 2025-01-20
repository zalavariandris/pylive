from PyQt6.QtCore import Qt, QAbstractListModel, QModelIndex, QObject, pyqtSignal, pyqtProperty
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine


class Attribute(QObject):
    def __init__(self, name, value):
        super().__init__()
        self._name = name
        self._value = value

    nameChanged = pyqtSignal()
    valueChanged = pyqtSignal()

    @pyqtProperty(str, notify=nameChanged)
    def name(self):
        return self._name

    @pyqtProperty(str, notify=valueChanged)
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if self._value != value:
            self._value = value
            self.valueChanged.emit()


class Node(QObject):
    def __init__(self, name, attributes):
        super().__init__()
        self._name = name
        self._attributes = attributes

    nameChanged = pyqtSignal()

    @pyqtProperty(str, notify=nameChanged)
    def name(self):
        return self._name

    @pyqtProperty('QVariantList')
    def attributes(self):
        return self._attributes


class GraphModel(QAbstractListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    NodesRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self, graphs=None):
        super().__init__()
        self._graphs = graphs or []

    def data(self, index, role):
        if not index.isValid():
            return None
        graph = self._graphs[index.row()]
        if role == self.NameRole:
            return graph["name"]
        if role == self.NodesRole:
            return graph["nodes"]
        return None

    def rowCount(self, parent=QModelIndex()):
        return len(self._graphs)

    def roleNames(self):
        return {
            self.NameRole: b"name",
            self.NodesRole: b"nodes",
        }


# Sample Data
attribute1 = Attribute("Color", "Red")
attribute2 = Attribute("Size", "Large")
node1 = Node("Node1", [attribute1, attribute2])
node2 = Node("Node2", [])
graph = Graph("Graph1", nodes: [node1, node2])

app = QGuiApplication([])
engine = QQmlApplicationEngine()

# Expose the data model to QML

engine.rootContext().setContextProperty("graph", graph)

# Load QML UI
engine.load("main.qml")
if not engine.rootObjects():
    exit(-1)
app.exec()
