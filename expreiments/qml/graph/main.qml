import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.12

ApplicationWindow {
    visible: true
    width: 640
    height: 480
    title: qsTr("PyQt5 love QML")
    color: _background

    Row{
        spacing: 30
        ListView {
            width: 200; height: 250
            model: theGraph.nodes
            delegate: Item {
                id: nodeListItem
                width: ListView.view.width
                height: 40
                Column {
                    Text { text: '<b>Name:</b> ' + display.name + index }
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: { nodeListItem.ListView.view.currentIndex = index; }
                }
            }
            highlight: Rectangle { color: "lightsteelblue"; radius: 5 }
            focus: true
        }
        // GRAPH COMPONENT //
        Column{
            Text{
                text: "Graph"
                font.pointSize: 24
            }

            Column{
                Text{
                    text:"nodes:"
                    font.pointSize: 16
                }
                Repeater{
                    id:nodeList
                    model: theGraph.nodes
                    delegate: Text{
                        text: display.name
                    }
                }
            }
        }
        
        // NODE COMPONENT //
        Column{
            Text{
                text: "Node: "+theNode.name
                font.pointSize: 24
            }
            
            Column{
                Text{
                    text: 'attributes:'
                }
                Repeater{
                    model: theNode.attributes
                    delegate: Row{
                        Text{
                            text: ""+display.name+": "
                        }
                        Text{
                            text: display.value
                        }
                    }
                }
            }
        }

        // ATTRIBUTE COMPONENT //
        Column{
            
            Text{
                text: "Attr: "+theAttribute.name
                font.pointSize: 24
            }
            Text{
                text: "value: "+theAttribute.value
            }
        }
        
    }
    

    // GridLayout {
    //     columns: 2
    //     rows: 1



    //     Column{
    //         Repeater{
    //             id: nodeRepeater
    //             model: graph.nodes
    //             delegate: Column{
    //                 Column
    //                 {
    //                     id: nodeListItem
    //                     Text{
    //                         text: display.name
    //                     }
    //                     Column{
    //                         Repeater{
    //                             id: attributeRepeater
    //                             model: display.attributes
    //                             delegate: Text{
    //                                 text:display.name
    //                             }
    //                         }
    //                     }
    //                 }
    //             }

                
    //         }
    //     }
    // }
}