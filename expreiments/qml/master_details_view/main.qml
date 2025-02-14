import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    visible: true
    width: 800
    height: 600
    title: "Master-Details View"

    // Main layout
    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal

        // Master view (left side)
        Rectangle {
            SplitView.minimumWidth: 200
            SplitView.preferredWidth: 300
            color: "#f0f0f0"

            ListView {
                id: masterList
                anchors.fill: parent
                model: personModel  // Using the Python model
                clip: true
                
                delegate: ItemDelegate {
                    width: parent.width
                    height: 50
                    
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        
                        Text {
                            text: model.name  // Using role name
                            font.bold: true
                        }
                        Text {
                            text: model.occupation  // Using role name
                            color: "gray"
                        }
                    }
                    
                    highlighted: ListView.isCurrentItem
                    onClicked: masterList.currentIndex = index
                }
            }
        }

        // Details view (right side)
        Rectangle {
            SplitView.minimumWidth: 300
            SplitView.fillWidth: true
            color: "white"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 10

                visible: masterList.currentItem != null

                Text {
                    text: masterList.currentItem ? masterList.currentItem.model.name : ""
                    font.bold: true
                    font.pixelSize: 24
                }

                Text {
                    text: "Age: " + (masterList.currentItem ? masterList.currentItem.model.age : "")
                }

                Text {
                    text: "Occupation: " + (masterList.currentItem ? masterList.currentItem.model.occupation : "")
                }

                Text {
                    text: masterList.currentItem ? masterList.currentItem.model.description : ""
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }

                Item {
                    Layout.fillHeight: true
                }
            }
        }
    }
}