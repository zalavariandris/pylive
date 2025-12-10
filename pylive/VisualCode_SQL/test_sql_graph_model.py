import unittest
from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from pylive.SQLPythonGraphEditor.sql_graph_model import SQLGraphModel

class TestNodeCRUD(unittest.TestCase):
    def setUp(self) -> None:
        self.app = QApplication()

    def test_create_graph(self):
        print(self.app)
        model = SQLGraphModel()
        graph_key = model.add_graph("MainGraph")
        print(graph_key)
        # graph.addNode("n1")
        # self.assertIn("n1", graph.nodes())

    # def test_adding_unique_nodes(self):
    #     """adding new functions must have unique id"""
    #     graph = SQLGraphModel()
    #     graph.addNode("n1")
    #     with self.assertRaises(ValueError):
    #         graph.addNode("n1")

    # def test_delete_node(self):
    #     """adding new functions must have unique id"""
    #     graph = SQLGraphModel()
    #     graph.addNode("n1")
    #     self.assertIn("n1", graph.nodes())

    #     graph.removeNode("n1")
    #     self.assertNotIn("n1", graph.nodes())
        
    # def tearDown(self):
    #     ...
    #     # del self.app

if __name__ == "__main__":
    unittest.main()