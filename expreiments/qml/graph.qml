// main.qml
import QtQuick 2.15
import QtQuick.Window 2.15

Window {
    visible: true
    width: 800
    height: 600
    title: "Graph Editor"

    Rectangle {
        anchors.fill: parent
        color: "white"

        // Line connecting the nodes
        Canvas {
            id: canvas
            anchors.fill: parent
            
            onPaint: {
                var ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                ctx.strokeStyle = "black"
                ctx.lineWidth = 2
                ctx.beginPath()
                ctx.moveTo(controller.node1X + node1.width/2, 
                          controller.node1Y + node1.height/2)
                ctx.lineTo(controller.node2X + node2.width/2, 
                          controller.node2Y + node2.height/2)
                ctx.stroke()
            }
        }

        // First draggable node
        Rectangle {
            id: node1
            width: 100
            height: 60
            radius: 5
            color: "lightblue"
            border.color: "blue"
            border.width: 2
            x: controller.node1X
            y: controller.node1Y

            MouseArea {
                anchors.fill: parent
                drag.target: parent
                
                onPositionChanged: {
                    if (drag.active) {
                        controller.node1X = parent.x
                        controller.node1Y = parent.y
                        canvas.requestPaint()
                    }
                }
            }

            Text {
                anchors.centerIn: parent
                text: "Node 1"
            }
        }

        // Second draggable node
        Rectangle {
            id: node2
            width: 100
            height: 60
            radius: 5
            color: "lightgreen"
            border.color: "green"
            border.width: 2
            x: controller.node2X
            y: controller.node2Y

            MouseArea {
                anchors.fill: parent
                drag.target: parent
                
                onPositionChanged: {
                    if (drag.active) {
                        controller.node2X = parent.x
                        controller.node2Y = parent.y
                        canvas.requestPaint()
                    }
                }
            }

            Text {
                anchors.centerIn: parent
                text: "Node 2"
            }
        }
    }
}