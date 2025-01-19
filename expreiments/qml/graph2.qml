// main.qml
import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15

Window {
    visible: true
    width: 800
    height: 600
    title: "Graph Editor"

    // Node component
    component Node: Rectangle {
        id: node
        width: 100
        height: 60
        radius: 5
        border.width: 2

        required property int nodeId
        required property string nodeText
        property bool isSelected: false

        color: isSelected ? Qt.lighter(border.color) : "white"
        border.color: {
            switch(nodeId % 4) {
                case 0: return "blue"
                case 1: return "green"
                case 2: return "red"
                case 3: return "purple"
            }
        }

        MouseArea {
            anchors.fill: parent
            drag.target: parent
            
            onPressed: parent.isSelected = true
            onReleased: {
                parent.isSelected = false
                controller.updateNodePosition(nodeId, parent.x, parent.y)
            }
            onPositionChanged: {
                if (drag.active) {
                    canvas.requestPaint()
                }
            }
        }

        Text {
            anchors.centerIn: parent
            text: nodeText
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "white"

        // Canvas for drawing connections
        Canvas {
            id: canvas
            anchors.fill: parent
            
            onPaint: {
                var ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                ctx.strokeStyle = "black"
                ctx.lineWidth = 2

                // Draw lines between all nodes
                for (var i = 0; i < nodesRepeater.count - 1; i++) {
                    var node1 = nodesRepeater.itemAt(i)
                    var node2 = nodesRepeater.itemAt(i + 1)
                    
                    if (node1 && node2) {
                        ctx.beginPath()
                        ctx.moveTo(node1.x + node1.width/2, node1.y + node1.height/2)
                        ctx.lineTo(node2.x + node2.width/2, node2.y + node2.height/2)
                        ctx.stroke()
                    }
                }
            }
        }

        // Node instances
        Repeater {
            id: nodesRepeater
            model: controller.nodes
            
            Node {
                x: modelData.x
                y: modelData.y
                nodeId: modelData.id
                nodeText: modelData.text
            }
        }

        // Add Node button
        Button {
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 10
            text: "Add Node"
            onClicked: controller.addNode()
        }
    }
}