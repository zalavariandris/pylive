from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtTest import QSignalSpy

import unittest
import sys
app = QApplication( sys.argv )

from pylive.VisualCode_v4.py_data_model import PyDataModel
from pylive.VisualCode_v4.py_subgraph_proxy_model import PySubgraphProxyModel
from pathlib import Path
from textwrap import dedent

class TestSignals(unittest.TestCase):
    def test_source_signal(self):
        text=dedent("""\
        nodes:
        - name: node1
          kind: UniqueFunction
          source: |
            def func():
              ...
        """)
        graph = PyDataModel()
        graph.deserialize(text)

        subgraph = PySubgraphProxyModel(graph)
        subgraph.setNodes(["node1"])

        spy = QSignalSpy(subgraph.sourceChanged)
        graph.setSource('node1', """\
          def hello(name:str="You"):
              return "Hello {name}"
        """)

        self.assertEqual(spy.count(), 1)

    def test_source_signal(self):
        graph = PyDataModel()
        graph.fromData({
            'nodes':[
                {
                    'name': "node1",
                    'source': "def func():    ..."
                }            ]
        })

        subgraph = PySubgraphProxyModel(graph)
        subgraph.setNodes(["node1"])

        spy = QSignalSpy(subgraph.sourceChanged)
        graph.setSource('node1', dedent("""\
            def hello(name:str="You"):
                return "Hello {name}"
        """))

        self.assertEqual(spy.count(), 1)
        
    def test_auto_evaluate(self):
        graph = PyDataModel()
        graph.fromData({
            'nodes':[
                {
                    'name': "make_name",
                    'source': "def identity():    'Mása'"
                },
                {
                    'name': "say_hello",
                    'source': "def say_hello(name:str):    return 'Hello {name}!'",
                    'fields': {'name': "-> make_name"}
                }
            ]
        })

        subgraph = PySubgraphProxyModel(graph)
        subgraph.setNodes(graph.ancestors('say_hello') | {'say_hello'})
        result_changed_spy = QSignalSpy(graph.resultChanged)
        subgraph.sourceChanged.connect(lambda n: graph.evaluateNodes(['say_hello']))
        graph.setSource('make_name', dedent("def identity():    'Judit'"))

        self.assertEqual(result_changed_spy.count(), 1)
    
if __name__ == "__main__":
    # app = QApplication()
    # app.exit()
    unittest.main()