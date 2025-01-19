#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtQml import *
from PyQt6.QtQuick import *

# from dataclasses import dataclass
# @dataclass
# class Node:
#     name:str
#     x:int=0
#     y:int=0 
#     kind:str="function"


class AttributeController(QObject):
    nameChanged = pyqtSignal(str)
    valueChanged = pyqtSignal(str)
    def __init__(self, name:str, parent:QObject|None=None):
        super().__init__(parent=parent)
        self._name = name
        self._value = "Value"

    def getName(self)->str:
        return self._name

    def setName(self, value:str):
        self._name = value
        self.nameChanged.emit(value)

    def getValue(self)->str:
        return self._value

    def setValue(self, value:str):
        self._value = value
        self.valueChanged.emit(value)

    name = pyqtProperty(str, getName, setName, notify=nameChanged)
    value = pyqtProperty(str, getValue, setValue, notify=valueChanged)


class AttributeList(QAbstractListModel):
    def __init__(self, attributes: list, parent=None):
        super().__init__(parent)
        self._attributes = attributes

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._attributes)

    def data(self, index: QModelIndex, role=None):
        return self._attributes[index.row()]

    def addAttribute(self, attribute:AttributeController):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._attributes.append(attribute)
        self.endInsertRows()


class NodeController(QObject):
    nameChanged = pyqtSignal(str)
    attribeListChanged = pyqtSignal(AttributeList)
    def __init__(self, name="-node-", parent:QObject|None=None):
        super().__init__(parent=parent)
        self._name = name
        self._attributes = AttributeList([])

    def getName(self)->str:
        return self._name

    def setName(self, value:str):
        self._name = value
        self.nameChanged.emit(value)

    def getAttributeList(self):
        return self._attributes


    name = pyqtProperty(str, getName, setName, notify=nameChanged)
    attributes = pyqtProperty(AttributeList, getAttributeList, notify=attribeListChanged)


class NodeList(QAbstractListModel):
    def __init__(self, nodes: list, parent=None):
        super().__init__(parent)
        self._nodes = nodes

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._nodes)

    def data(self, index: QModelIndex, role=None):
        return self._nodes[index.row()]

    def addNode(self, node:NodeController):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._nodes.append(node)
        self.endInsertRows()


class GraphController(QObject):
    nodeListChanged = pyqtSignal(NodeList)
    def __init__(self, parent:QObject|None=None):
        super().__init__(parent=parent)
        self._node_list = NodeList([])

    def getNodeList(self):
        return self._node_list

    nodes = pyqtProperty(NodeList, getNodeList, notify=nodeListChanged)

if __name__ == '__main__':
    app = QGuiApplication(sys.argv)

    theGraph = GraphController()
    theNode = NodeController('read_text')
    theAttribute = AttributeController("attr1")
    theNode.attributes.addAttribute(theAttribute)
    theNode.attributes.addAttribute(AttributeController("attr2"))
    theGraph.nodes.addNode(theNode)
    theGraph.nodes.addNode(NodeController('process_text'))
    theGraph.nodes.addNode(NodeController('print_text'))

    engine = QQmlApplicationEngine()
    context = engine.rootContext()
    # view.setResizeMode(QQuickView.SizeRootObjectToView)
    context.setContextProperty('_background', "cyan")
    context.setContextProperty('theGraph', theGraph)
    context.setContextProperty('theNode', theNode)
    context.setContextProperty('theAttribute', theAttribute)
    engine.load(QUrl.fromLocalFile("main.qml"))

    timer = QTimer()
    def randomize_name():
        index = theGraph.nodes.index(0)
        nodeListItem = theGraph.nodes.data(index)
        nodeListItem.setName("judit")
        print(nodeListItem)
        print("hello")
        
    timer.timeout.connect(randomize_name)
    timer.start(1000)



    # view.setSource(QUrl('main.qml'))

    sys.exit(app.exec())
