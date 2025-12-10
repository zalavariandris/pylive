from typing import *
import unittest

from PySide6.QtWidgets import QApplication
from pylive.NXPythonGraphEditor.python_graph_model import PythonGraphModel


def hello_function(name:str):
    return f"Hello {name}"

class TestFunctionCRUD(unittest.TestCase):
    def setUp(self) -> None:
        self.app = QApplication.instance()
        return super().setUp()

    def test_create_function_node(self):
        graph = PythonGraphModel()
        node_id = graph.addFunction(print)
        self.assertIn(node_id, graph.nodes())

    def test_create_multiple_print_functions(self):
        """adding new functions must have unique id"""
        graph = PythonGraphModel()
        node1_id = graph.addFunction(print)
        node2_id = graph.addFunction(print)
        self.assertIn(node2_id, graph.nodes())

        graph.removeNode(node1_id)
        self.assertNotIn(node1_id, graph.nodes())

    def test_delete_function(self):
        """adding new functions must have unique id"""
        graph = PythonGraphModel()
        node_id = graph.addFunction(print)

        graph.removeNode(node_id)
        self.assertNotIn(node_id, graph.nodes())

    def tearDown(self):
        ...
        # del self.app


class TestFunctionParameters(unittest.TestCase):
    def test_function_parameters(self):
        graph = PythonGraphModel()
        node_id = graph.addFunction(hello_function)
        self.assertIn("name", graph.parameters(node_id))

    def test_initial_parameter_values(self):
        graph = PythonGraphModel()
        node_id = graph.addFunction(hello_function, name="Judit")
        self.assertEqual(graph.parameterValue(node_id, "name"), "Judit")

    def test_setting_parameter_values(self):
        graph = PythonGraphModel()
        node_id = graph.addFunction(hello_function, name="Judit")
        graph.setParameterValue(node_id, "name", "Mása")
        self.assertEqual(graph.parameterValue(node_id, "name"), "Mása")

    def test_deleting_parameter_values(self):
        graph = PythonGraphModel()
        node_id = graph.addFunction(hello_function, name="Judit")
        graph.deleteParameterValue(node_id, "name")
        with self.assertRaises(KeyError):
            value = graph.parameterValue(node_id, "name")


class TestFunctionPorts(unittest.TestCase):
    def test_function_inlets(self):
        graph = PythonGraphModel()
        node_id = graph.addFunction(hello_function, name="Judit")
        self.assertEqual([_ for _ in graph.inlets(node_id)], ["name"])

    def test_function_outlets(self):
        graph = PythonGraphModel()
        node_id = graph.addFunction(hello_function, name="Judit")
        self.assertEqual([_ for _ in graph.outlets(node_id)], ["out"])

        


class TextEdgeCRUD(unittest.TestCase):
    def setUp(self) -> None:
        self.app = QApplication.instance()
        return super().setUp()

    def test_create_edge_with_existing_nodes(self):
        from pathlib import Path

        graph = PythonGraphModel()
        cwd_node = graph.addFunction(Path.cwd)
        print_node = graph.addFunction(print)

        graph.addEdge(cwd_node, print_node, ("out", "args"))
        self.assertIn((cwd_node, print_node, ("out", "args")), graph.edges())

    def test_delete_edge(self):
        from pathlib import Path

        graph = PythonGraphModel()
        cwd_node = graph.addFunction(Path.cwd)
        print_node = graph.addFunction(print)
        edge_id = cwd_node, print_node, ("out", "args")
        graph.addEdge(*edge_id)

        graph.removeEdge(*edge_id)
        self.assertNotIn(edge_id, graph.edges())

    def create_edge_with_nonexistent_nodes(self):
        graph = PythonGraphModel()
        with self.assertRaises(KeyError):
            graph.addEdge("a", "b", ("out", "arg"))

    def tearDown(self):
        ...
        # del self.app


class TestGraphEvaluation(unittest.TestCase):
    def test_evaluate_a_single_function(self):
        from pathlib import Path

        graph = PythonGraphModel()
        args = {'name': "Mása"}
        hello_node = graph.addFunction(hello_function, **args)

        graph.evaluate(hello_node)

        self.assertEqual(graph.cache(hello_node), hello_function(**args))

    def test_evaluate_chain_of_function(self):
        from pathlib import Path

        graph = PythonGraphModel()
        args = {'name': "Mása"}
        hello_node = graph.addFunction(hello_function, **args)

        graph.evaluate(hello_node)

        self.assertEqual(graph.cache(hello_node), hello_function(**args))

    def test_evaluate_with_missing_required_arguments(self):
        ...

    # def test_cached_arguments_after_evaluation(self):
    #     from pathlib import Path

    #     graph = PythonGraphModel()
    #     cwd_node = graph.add(Path.cwd)
    #     graph.addNode("cwd1", )
    #     graph.addNode("print1", print)
    #     graph.addEdge("cwd1", "print1", "args")
    #     graph.setOutput("print1")

    #     self.assertEqual(graph(), None)
    #     self.assertEqual(
    #         graph.getNodeProperty("print1", "_arguments")["args"], [Path.cwd()]
    #     )


if __name__ == "__main__":
    unittest.main()
