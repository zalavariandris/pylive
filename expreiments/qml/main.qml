import QtQuick 2.15
import QtQuick.Controls 2.15

ApplicationWindow {
    visible: true
    width: 400
    height: 300
    title: "PySide6 QML Example"

    Column {
        anchors.centerIn: parent
        spacing: 10

        Text {
            id: label
            text: "Hello, QML!"
            font.pixelSize: 24
            horizontalAlignment: Text.AlignHCenter
        }

        Button {
            text: "Click Me"
            onClicked: {
                label.text = "Button Clicked!"
            }
        }
    }
}
