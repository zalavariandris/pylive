import sys
from PySide6.QtCore import QUrl
from PySide6.QtQuick import QQuickView
from PySide6.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    view = QQuickView()

    # Load the QML file
    qml_file = QUrl("main.qml")
    view.setSource(qml_file)

    if view.status() == QQuickView.Error:
        sys.exit(-1)

    # Show the window
    view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
