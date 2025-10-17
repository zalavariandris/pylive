import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    visible: true
    width: 800
    height: 600
    title: "Master-Details View"

    readonly property int nameRole: Qt.UserRole + 1
    readonly property int ageRole: Qt.UserRole + 2
    readonly property int occupationRole: Qt.UserRole + 3
    readonly property int descriptionRole: Qt.UserRole + 4

    property var currentPerson: {
        if (masterList.currentIndex !== -1) {
            return {
                name: masterList.model.data(masterList.model.index(masterList.currentIndex, 0), nameRole),
                age: masterList.model.data(masterList.model.index(masterList.currentIndex, 0), ageRole),
                occupation: masterList.model.data(masterList.model.index(masterList.currentIndex, 0), occupationRole),
                description: masterList.model.data(masterList.model.index(masterList.currentIndex, 0), descriptionRole)
            }
        }
        return null
    }

    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal

        Rectangle {
            SplitView.minimumWidth: 200
            SplitView.preferredWidth: 300
            color: "#f0f0f0"

            ListView {
                id: masterList
                anchors.fill: parent
                model: personModel
                clip: true
                
                delegate: ItemDelegate {
                    width: parent.width
                    height: 50
                    
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        
                        Text {
                            text: model.name
                            font.bold: true
                        }
                        Text {
                            text: model.occupation
                            color: "gray"
                        }
                    }
                    
                    highlighted: ListView.isCurrentItem
                    onClicked: masterList.currentIndex = index
                }
            }
        }

        Rectangle {
            SplitView.minimumWidth: 300
            SplitView.fillWidth: true
            color: "white"

            ColumnLayout {
                id: detailsLayout
                anchors.fill: parent
                anchors.margins: 20
                spacing: 15
                visible: currentPerson !== null

                TextField {
                    id: nameField
                    Layout.fillWidth: true
                    placeholderText: "Name"
                    text: currentPerson ? currentPerson.name : ""
                    font.pixelSize: 24
                    onTextChanged: {
                        if (currentPerson) {
                            personModel.setData(
                                personModel.index(masterList.currentIndex, 0),
                                text,
                                nameRole
                            )
                        }
                    }
                }

                SpinBox {
                    id: ageSpinBox
                    from: 0
                    to: 150
                    value: currentPerson ? currentPerson.age : 0
                    editable: true
                    onValueChanged: {
                        if (currentPerson) {
                            personModel.setData(
                                personModel.index(masterList.currentIndex, 0),
                                value,
                                ageRole
                            )
                        }
                    }
                }

                TextField {
                    id: occupationField
                    Layout.fillWidth: true
                    placeholderText: "Occupation"
                    text: currentPerson ? currentPerson.occupation : ""
                    onTextChanged: {
                        if (currentPerson) {
                            personModel.setData(
                                personModel.index(masterList.currentIndex, 0),
                                text,
                                occupationRole
                            )
                        }
                    }
                }

                TextArea {
                    id: descriptionArea
                    Layout.fillWidth: true
                    Layout.preferredHeight: 100
                    placeholderText: "Description"
                    text: currentPerson ? currentPerson.description : ""
                    wrapMode: TextArea.Wrap
                    onTextChanged: {
                        if (currentPerson) {
                            personModel.setData(
                                personModel.index(masterList.currentIndex, 0),
                                text,
                                descriptionRole
                            )
                        }
                    }
                }

                Item {
                    Layout.fillHeight: true
                }
            }
        }
    }
}