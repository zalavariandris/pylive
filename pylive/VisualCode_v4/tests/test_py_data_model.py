from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import unittest
import sys
app= QApplication( sys.argv )

from pylive.VisualCode_v4.graph_editor.graph_data_roles import GraphDataRole
from pylive.VisualCode_v4.py_data_model import PyDataModel, PyNodeItem, PyParameterItem

import inspect

from textwrap import dedent

say_hello_script = dedent("""\
nodes:
- name: person
  source: |
    def identity(data:Any):
    	return data
  fields:
    data: "TheName"

- name: say_hello
  source: |
    def say_hello(name:str):
    	return f"Hello {name}!"
  fields:
    name: "you"

edges:
  - source: person
    target: say_hello
    inlet: name
""")

math_script = dedent("""\
nodes:
- name: two
  source: |
    def two():
    	return 2

- name: three
  source: |
    def two():
    	return 3

- name: mult
  source: |
    def mult(x, y):
    	return 3

edges:
  - source: two
    target: mult
    inlet: x
  - source: three
    target: mult
    inlet: y
""")

class TestModelCRUD(unittest.TestCase):
	def test_read(self):
		...

	def test_create_node(self):
		...

	def test_attempt_linking_to_unexisting_nodes_and_inlets(self):
		data_model = PyDataModel()
		data_model.deserialize(math_script)

		with self.assertRaises(ValueError):
			data_model.linkNodes("NOTHING", "mult", "x")

		with self.assertRaises(ValueError):
			data_model.linkNodes("two", "NOTHING", "x")

		with self.assertRaises(ValueError):
			data_model.linkNodes("two", "mult", "NOTHING")


	def test_create_link(self):
		...

	def test_delete_link(self):
		...

	def test_create_parameter(self):
		...

	def test_delete_parameter(self):
		...

	def test_deserialize(self):
		data_model = PyDataModel()
		data_model.deserialize(dedent("""\
			nodes:
			- name: person
			  source: |
			    def identity(data:Any):
			    	return data
			  fields:
			    data: "TheName"

			- name: say_hello
			  source: |
			    def say_hello(name:str):
			    	return f"Hello {name}!"
			  fields:
			    name: "you"

			edges:
			  - source: person
			    target: say_hello
			    inlet: name
		"""))

		self.assertEqual(data_model.nodeCount(), 2)
		self.assertEqual(data_model.linkCount(), 1)
		nodes = set(_ for _ in data_model.nodes())
		self.assertEqual(nodes, {'person', 'say_hello'})
		links = {_ for _ in data_model.links()}
		self.assertEqual(links, {('person', 'say_hello', 'name')})

	def test_reset(self):
		data_model = PyDataModel()
		data_model.deserialize(say_hello_script)

		data_model.deserialize(math_script)
		self.assertEqual(data_model.nodeCount(), 3)
		self.assertEqual(data_model.linkCount(), 2)
		nodes = set(_ for _ in data_model.nodes())
		self.assertEqual(nodes, {'two', 'three', 'mult'})
		links = {_ for _ in data_model.links()}
		self.assertEqual(links, {
			('two', 'mult', 'x'),
			('three', 'mult', 'y'),
		})

	def test_serialize(self):
		...


class TestCompilation(unittest.TestCase):
	def test_compile_hello_function(self):
		
		data_model = PyDataModel()
		data_model.addNode("hello", PyNodeItem(source=dedent("""\
		def hello(name:str="you"):
			return f"Hello {name}"
		""")))

		self.assertEqual(data_model.nodeStatus("hello"), 'initalized')
		success = data_model.compileNodes(["hello"])
		self.assertEqual(data_model.nodeStatus("hello"), 'compiled')

	def test_compile_bad_syntax_function(self):
		from textwrap import dedent
		data_model = PyDataModel()
		data_model.addNode("bad", PyNodeItem(source="clas bum"))


		success = data_model.compileNodes(["bad"])
		self.assertFalse(success)
		self.assertEqual(data_model.nodeStatus("bad"), 'error')
		self.assertIsInstance(data_model.nodeError("bad"), SyntaxError)

	def test_compile_no_valid_function(self):
		"""if no functions found in the script, raise a ValueError"""
		"""currently only functions are supported. TODO: support classes, methods, expressions, values etc.?"""
		from textwrap import dedent
		data_model = PyDataModel()
		data_model.addNode("class_definition", PyNodeItem(source=dedent("""\
		class Person:
			...
		""")))


		success = data_model.compileNodes(["class_definition"])
		self.assertFalse(success)
		self.assertEqual(data_model.nodeStatus("class_definition"), 'error')
		self.assertIsInstance(data_model.nodeError("class_definition"), ValueError)


class TestParametersCRUD(unittest.TestCase):
	def test_init_with_empty_parameters(self):
		data_model = PyDataModel()
		data_model.addNode("node1", PyNodeItem(parameters=[
			PyParameterItem("input1"),
			PyParameterItem("input2")
		]))

		self.assertEqual(data_model.parameterCount("node1"), 2)

		param1 = data_model.parameterItem("node1", 0)
		param2 = data_model.parameterItem("node1", 1)
		self.assertEqual(param1.name, "input1")
		self.assertEqual(param2.name, "input2")

	def test_compile_parameters(self):
		from textwrap import dedent
		data_model = PyDataModel()
		data_model.addNode("hello", PyNodeItem(source=dedent("""\
		def hello(name:str="you"):
			return f"Hello {name}"
		""")))
		# data_model.addNode("bad_function", PyNodeItem(source=dedent("""\
		# de
		# """)))

		data_model.compileNodes(["hello"])
		self.assertEqual(data_model.parameterCount("hello"), 1)
		param_item = data_model.parameterItem("hello", 0)
		self.assertEqual(param_item.name, "name")
		self.assertEqual(param_item.annotation, str)
		self.assertEqual(param_item.default, "you")
		self.assertEqual(param_item.value, inspect.Parameter.empty)
		self.assertEqual(param_item.kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)

	def test_compile_parameters_with_stored_values(self):
		from textwrap import dedent
		data_model = PyDataModel()
		data_model.addNode("hello", PyNodeItem(
			source=dedent("""\
				def hello(name:str="you"):
					return f"Hello {name}"
				"""),
			parameters=[PyParameterItem(name="name", value="Mása")]
		))

		data_model.compileNodes(["hello"])
		self.assertEqual(data_model.parameterCount("hello"), 1)
		param_item = data_model.parameterItem("hello", 0)
		self.assertEqual(param_item.default, "you")
		self.assertEqual(param_item.value, "Mása")



if __name__ == "__main__":
	unittest.main()