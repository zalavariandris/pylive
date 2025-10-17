# main.py
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QUrl
import sys

class NodeController(QObject):
    nodesChanged = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._nodes = [
            {"id": 0, "x": 100, "y": 100, "text": "Node 1"},
            {"id": 1, "x": 300, "y": 100, "text": "Node 2"},
            {"id": 2, "x": 200, "y": 300, "text": "Node 3"}
        ]

    @pyqtProperty('QVariantList', notify=nodesChanged)
    def nodes(self):
        return self._nodes

    @pyqtSlot(int, float, float)
    def updateNodePosition(self, nodeId, x, y):
        for node in self._nodes:
            if node["id"] == nodeId:
                node["x"] = x
                node["y"] = y
                self.nodesChanged.emit()
                break

    @pyqtSlot()
    def addNode(self):
        new_id = max(node["id"] for node in self._nodes) + 1
        self._nodes.append({
            "id": new_id,
            "x": 200,
            "y": 200,
            "text": f"Node {new_id + 1}"
        })
        self.nodesChanged.emit()

if __name__ == '__main__':
    app = QGuiApplication(sys.argv)
    
    engine = QQmlApplicationEngine()
    controller = NodeController()
    engine.rootContext().setContextProperty("controller", controller)
    
    engine.load(QUrl.fromLocalFile("graph2.qml"))
    
    if not engine.rootObjects():
        sys.exit(-1)
        
    sys.exit(app.exec())