import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Window {
    width: 800
    height: 600
    visible: true
    title: "Rectangle Editor"

    // Model data
    ListModel {
        id: rectanglesModel
        ListElement {
            name: "Rectangle 10"
            rectWidth: 100
            rectHeight: 150
        }
        ListElement {
            name: "Rectangle 2"
            rectWidth: 200
            rectHeight: 100
        }
        ListElement {
            name: "Rectangle 3"
            rectWidth: 150
            rectHeight: 150
        }
    }

    // Main layout
    RowLayout {
        anchors.fill: parent
        spacing: 10

        // Left side - List view
        Rectangle {
            Layout.preferredWidth: 200
            Layout.fillHeight: true
            color: "#f0f0f0"
            border.color: "#d0d0d0"

            ListView {
                id: listView
                anchors.fill: parent
                model: rectanglesModel
                spacing: 5
                clip: true

                delegate: ItemDelegate {
                    width: parent.width
                    height: 40
                    
                    highlighted: ListView.isCurrentItem

                    contentItem: Text {
                        text: name
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                    }

                    onClicked: {
                        listView.currentIndex = index
                    }
                }
            }
        }

        // Right side - Details view
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#f8f8f8"
            border.color: "#d0d0d0"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 20

                Text {
                    text: "Rectangle Properties"
                    font.bold: true
                    font.pixelSize: 16
                }

                GridLayout {
                    columns: 2
                    rowSpacing: 10
                    columnSpacing: 10

                    Text { text: "Name:" }
                    TextField {
                        id: nameField
                        Layout.fillWidth: true
                        Component.onCompleted: {
                            if (listView.currentItem) {
                                text = rectanglesModel.get(listView.currentIndex).name
                            }
                        }
                        onTextChanged: {
                            if (listView.currentItem && text !== rectanglesModel.get(listView.currentIndex).name) {
                                rectanglesModel.setProperty(listView.currentIndex, "name", text)
                            }
                        }
                    }

                    Text { text: "Width:" }
                    SpinBox {
                        id: widthSpinBox
                        from: 1
                        to: 1000
                        value: listView.currentItem ? rectanglesModel.get(listView.currentIndex).rectWidth : 100
                        onValueChanged: {
                            if (listView.currentItem) {
                                rectanglesModel.setProperty(listView.currentIndex, "rectWidth", value)
                            }
                        }
                    }

                    Text { text: "Height:" }
                    SpinBox {
                        id: heightSpinBox
                        from: 1
                        to: 1000
                        value: listView.currentItem ? rectanglesModel.get(listView.currentIndex).rectHeight : 100
                        onValueChanged: {
                            if (listView.currentItem) {
                                rectanglesModel.setProperty(listView.currentIndex, "rectHeight", value)
                            }
                        }
                    }
                }

                // Preview of the rectangle
                Rectangle {
                    Layout.alignment: Qt.AlignCenter
                    Layout.preferredWidth: listView.currentItem ? rectanglesModel.get(listView.currentIndex).rectWidth : 0
                    Layout.preferredHeight: listView.currentItem ? rectanglesModel.get(listView.currentIndex).rectHeight : 0
                    color: "steelblue"
                    border.color: "darkblue"

                    Text {
                        anchors.centerIn: parent
                        text: listView.currentItem ? rectanglesModel.get(listView.currentIndex).name : ""
                        color: "white"
                    }

                    // Add a smooth animation for position changes
                    Behavior on x { NumberAnimation { duration: 50 } }
                    Behavior on y { NumberAnimation { duration: 50 } }

                    // Mouse area to handle drag functionality
                    MouseArea {
                        anchors.fill: parent
                        drag.target: parent
                        drag.axis: Drag.XAndY
                        // drag.minimumX: 0
                        // drag.maximumX: parent.parent.width - parent.width
                        // drag.minimumY: 0
                        // drag.maximumY: parent.parent.height - parent.height

                        // Change color when dragging
                        onPressed: parent.color = "darkblue"
                        onReleased: parent.color = "blue"
                    }
                }

                Item { Layout.fillHeight: true }
            }
        }
    }

    // Update fields when selection changes
    Connections {
        target: listView
        function onCurrentIndexChanged() {
            if (listView.currentItem) {
                var currentRect = rectanglesModel.get(listView.currentIndex)
                nameField.text = currentRect.name
                widthSpinBox.value = currentRect.rectWidth
                heightSpinBox.value = currentRect.rectHeight
            }
        }
    }
}