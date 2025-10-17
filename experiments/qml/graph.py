# main.py
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, QUrl
import sys

class NodeController(QObject):
    node1Changed = pyqtSignal()
    node2Changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._node1_x = 100
        self._node1_y = 100
        self._node2_x = 300
        self._node2_y = 100

    @pyqtProperty(float, notify=node1Changed)
    def node1X(self):
        return self._node1_x

    @node1X.setter
    def node1X(self, x):
        self._node1_x = x
        self.node1Changed.emit()

    @pyqtProperty(float, notify=node1Changed)
    def node1Y(self):
        return self._node1_y

    @node1Y.setter
    def node1Y(self, y):
        self._node1_y = y
        self.node1Changed.emit()

    @pyqtProperty(float, notify=node2Changed)
    def node2X(self):
        return self._node2_x

    @node2X.setter
    def node2X(self, x):
        self._node2_x = x
        self.node2Changed.emit()

    @pyqtProperty(float, notify=node2Changed)
    def node2Y(self):
        return self._node2_y

    @node2Y.setter
    def node2Y(self, y):
        self._node2_y = y
        self.node2Changed.emit()

if __name__ == '__main__':
    app = QGuiApplication(sys.argv)
    
    engine = QQmlApplicationEngine()
    controller = NodeController()
    engine.rootContext().setContextProperty("controller", controller)
    
    engine.load(QUrl.fromLocalFile("graph.qml"))
    
    if not engine.rootObjects():
        sys.exit(-1)
        
    sys.exit(app.exec())