from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import unittest
import sys
app = QApplication( sys.argv )

from pylive.VisualCode_v4.py_graph_item import PyGraphItem
from pathlib import Path
from textwrap import dedent

class TestDeserialization(unittest.TestCase):
    def test_single_node_deserialization(self):
        text=dedent("""\
        nodes:
        - name: node1
          kind: UniqueFunction
          source: |
            def func():
              ...
        """)
        graph = PyGraphItem()
        graph.deserialize(text)

        self.assertEqual(graph.nodes().rowCount(), 1)
        node_item = graph.nodes().nodeItem(0)
        self.assertEqual(node_item.name(), "node1")
        self.assertEqual(node_item.source(), "def func():\n  ...\n")

    def test_line_graph_edges_style_deserialization(self):
        text = dedent("""\
        nodes:
        - name: node1
          kind: UniqueFunction
          source: |
            def func2():
              ...

        - name: node2
          kind: UniqueFunction
          source: |
            def func2():
              ...

        edges:
        - source: node1
          target: node2
          inlet: md

        """)
        graph = PyGraphItem()
        graph.deserialize(text)

        self.assertEqual(graph.nodes().rowCount(), 2)
        self.assertEqual(graph.edges().rowCount(), 1)

        node1_index = graph.nodes().index(0,0)
        node2_index = graph.nodes().index(1,0)
        edge_item = graph.edges().edgeItem(0)

        source_node_index, outlet = graph.edges().source(0)
        target_node_index, inlet = graph.edges().target(0)
        self.assertEqual(source_node_index, node1_index)
        self.assertEqual(target_node_index, node2_index)

    @unittest.skip("not imlpemented yet")
    def test_line_graph_field_style_deserialization(self):
        text=dedent("""\
        nodes:
        - name: node1
          kind: UniqueFunction
          source: |
            def func2():
              ...

        - name: node2
          kind: UniqueFunction
          source: |
            def func2():
              ...
          fields:
            md: '@node1'

        """)
        graph = PyGraphItem()
        graph.deserialize(text)

        self.assertEqual(graph.nodes().rowCount(), 2)
        self.assertEqual(graph.edges().rowCount(), 1)

        node1_index = graph.nodes().index(0,0)
        node2_index = graph.nodes().index(1,0)
        edge_item = graph.edges().edgeItem(0)

        source_node_index, outlet = graph.edges().source(0)
        target_node_index, inlet = graph.edges().target(0)
        self.assertEqual(source_node_index, node1_index)
        self.assertEqual(target_node_index, node2_index)
        

        

# class TestFiles(unittest.TestCase):
#     def test_loading_graph_from_file(self):
#         graph = PyGraphItem()
#         graph.load("./website_builder.yaml")


class TestEvaluation(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = PyGraphItem()
        self.graph.deserialize("""\
        nodes:
        - name: "get_name1"
          kind: UniqueFunction
          source: |
            def get_name(name:str)->str:
              return name

          fields:
            name: Mása

        - name: "say_hello1" 
          kind: UniqueFunction
          source: |
            def say_hello(name:str)->str:
              return f"Hello {name}!"

        edges:
          - source: "get_name1"
            target: "say_hello1"
            inlet: md
        """)

    def test_single_node(self):
        node1_index = self.graph.nodes().index(0,0)
        node1_item = self.graph.nodes().nodeItem(node1_index.row())
        assert node1_item.name() == "get_name1", f"its: {node1_item.name()}"
        result = self.graph.evaluateNode(node1_index)
        self.assertEqual(result, "Mása")

    def test_mini_chain(self):
        node1_index = self.graph.nodes().index(0,0)
        node1_item = self.graph.nodes().nodeItem(node1_index.row())
        assert node1_item.name() == "get_name1", f"its: {node1_item.name()}"
        node2_index = self.graph.nodes().index(1,0)
        node2_item = self.graph.nodes().nodeItem(node2_index.row())
        assert node2_item.name() == "say_hello1", f"its: {node2_item.name()}"
        result = self.graph.evaluateNode(node1_index)
        self.assertEqual(result, "Mása")
    
if __name__ == "__main__":
    # app = QApplication()
    # app.exit()
    unittest.main()