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
                    delegate: Column{ // NODE COMPONENT //
                            Text{ 
                                text: "Node: "+model.display.nam
                                font.pointSize: 24
                            }
                            
                            Column{
                                Text{
                                    text: 'attributes:'
                                }
                                Repeater{
                                    model: attributes
                                    delegate: Row{ // ATTRIBUTE COMPONENT //
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
                }
            }
        }

        
        // Column{
        //     Text{
        //         text: "Node: "+theNode.name
        //         font.pointSize: 24
        //     }
            
        //     Column{
        //         Text{
        //             text: 'attributes:'
        //         }
        //         Repeater{
        //             model: theNode.attributes
        //             delegate: Row{
        //                 Text{
        //                     text: ""+display.name+": "
        //                 }
        //                 Text{
        //                     text: display.value
        //                 }
        //             }
        //         }
        //     }
        // }

        // // ATTRIBUTE COMPONENT //
        // Column{
            
        //     Text{
        //         text: "Attr: "+theAttribute.name
        //         font.pointSize: 24
        //     }
        //     Text{
        //         text: "value: "+theAttribute.value
        //     }
        // }
        
    }
}