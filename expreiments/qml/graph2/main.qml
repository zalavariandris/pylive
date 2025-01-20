import QtQuick 2.15
import QtQuick.Controls 2.15

ApplicationWindow {
    visible: true
    width: 800
    height: 600

    ListView {
        anchors.fill: parent
        model: graphModel
        delegate: Column {
            Text {
                text: model.name
                font.bold: true
            }

            ListView {
                model: model.nodes
                delegate: Column {
                    TextField {
                        text: model.name
                        onTextChanged: model.name = text
                    }
                    ListView {
                        model: model.attributes
                        delegate: Row {
                            TextField {
                                text: model.name
                                onTextChanged: model.name = text
                            }
                            TextField {
                                text: model.value
                                onTextChanged: model.value = text
                            }
                        }
                    }
                }
            }
        }
    }
}
