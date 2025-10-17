import sys
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import QUrl

def main():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    
    # Load the QML file
    # Assuming the QML file is named 'main.qml' and is in the same directory
    engine.load(QUrl.fromLocalFile("main.qml"))

    if not engine.rootObjects():
        sys.exit(-1)

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())