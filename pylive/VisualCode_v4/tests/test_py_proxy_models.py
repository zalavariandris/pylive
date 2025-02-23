from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import *

import unittest
import sys
app= QApplication( sys.argv )

from pylive.VisualCode_v4.graph_editor.graph_data_roles import GraphDataRole
from pylive.VisualCode_v4.py_data_model import (
	PyDataModel, 
	PyNodeItem, 
	PyParameterItem,
	Empty
)

from pylive.VisualCode_v4.py_proxy_model import (
	PyProxyNodeModel, 
	PyProxyLinkModel, 
	PyProxyParameterModel,
)

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

class TestNodesCRUD(unittest.TestCase):
	def test_init_with_nodes(self) -> None:
		data_model = PyDataModel()
		data_model.addNode("node1", PyNodeItem())

		proxy_model = PyProxyNodeModel(data_model)
		self.assertEqual(proxy_model.rowCount(), 1)
		self.assertEqual(proxy_model.data(proxy_model.index(0,0), Qt.ItemDataRole.EditRole), "node1")

	def test_nodes_added(self) -> None:
		data_model = PyDataModel()
		proxy_model = PyProxyNodeModel(data_model)

		data_model.addNode("node1", PyNodeItem())
		self.assertEqual(proxy_model.rowCount(), 1)
		self.assertEqual(proxy_model.data(proxy_model.index(0,0), Qt.ItemDataRole.EditRole), "node1")

		data_model.addNode("node2", PyNodeItem())
		self.assertEqual(proxy_model.rowCount(), 2)
		self.assertEqual(proxy_model.data(proxy_model.index(1,0), Qt.ItemDataRole.EditRole), "node2")

	def test_remove_last_node(self) -> None:
		data_model = PyDataModel()
		data_model.addNode("node1", PyNodeItem())
		data_model.addNode("node2", PyNodeItem())
		data_model.addNode("node3", PyNodeItem())
		proxy_model = PyProxyNodeModel(data_model)

		data_model.removeNode("node3")
		proxy_names = []
		for row in range(proxy_model.rowCount()):
			index = proxy_model.index(row, 0)
			value = proxy_model.data(index)
			proxy_names.append(value)

		self.assertNotIn("node3", proxy_names)

	def test_remove_first_node(self) -> None:
		data_model = PyDataModel()
		data_model.addNode("node1", PyNodeItem())
		data_model.addNode("node2", PyNodeItem())
		data_model.addNode("node3", PyNodeItem())
		proxy_model = PyProxyNodeModel(data_model)

		data_model.removeNode("node1")
		proxy_names = []
		for row in range(proxy_model.rowCount()):
			index = proxy_model.index(row, 0)
			value = proxy_model.data(index)
			proxy_names.append(value)

		self.assertNotIn("node1", proxy_names)

	def test_node_comilation(self):
		data_model = PyDataModel()
		data_model.addNode("hello1", PyNodeItem(dedent("""\
			def hello(name:str='You'):
				...
		""")))
		data_model.compileNodes(['hello1'])

		proxy_model = PyProxyNodeModel(data_model)
		column = proxy_model._headers.index('compiled')
		node_status_index = proxy_model.index(0, column)

		self.assertEqual(proxy_model.data(node_status_index, Qt.ItemDataRole.DisplayRole), True)

	def test_source_model_reset(self):
		data_model = PyDataModel()
		data_model.addNode("node1", PyNodeItem())

		nodes_proxy = PyProxyNodeModel(data_model)
		
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

		self.assertEqual(nodes_proxy.rowCount(), 2)
		
class TestNodeSignals(unittest.TestCase):
	...



class TestLinksCRUD(unittest.TestCase):
	def test_read_links(self) -> None:
		data_model = PyDataModel()
		data_model.addNode("node1", PyNodeItem())
		data_model.addNode("node2", PyNodeItem(parameters=[PyParameterItem('in')]))
		data_model.linkNodes("node1", "node2", "in")

		edges = PyProxyLinkModel(data_model)
		nodes = edges.itemsModel()
		assert nodes
		node1_index = nodes.match(nodes.index(0,0), Qt.ItemDataRole.EditRole, "node1", 1, Qt.MatchFlag.MatchExactly)[0]
		node2_index = nodes.match(nodes.index(0,0), Qt.ItemDataRole.EditRole, "node2", 1, Qt.MatchFlag.MatchExactly)[0]

		self.assertEqual(edges.rowCount(), 1)
		self.assertEqual(edges.data(edges.index(0,0), GraphDataRole.LinkSourceRole), (node1_index, "out") )
		self.assertEqual(edges.data(edges.index(0,0), GraphDataRole.LinkTargetRole), (node2_index, "in") )

	def test_create_link(self) -> None:
		data_model = PyDataModel()
		proxy_model = PyProxyLinkModel(data_model)
		
		data_model.addNode("node1", PyNodeItem())
		data_model.addNode("node2", PyNodeItem(parameters=[PyParameterItem('in')]))
		data_model.linkNodes("node1", "node2", "in")

		self.assertEqual(proxy_model.rowCount(), 1)
		self.assertEqual(proxy_model.data(proxy_model.index(0,0)), "node1")
		self.assertEqual(proxy_model.data(proxy_model.index(0,1)), "node2")
		self.assertEqual(proxy_model.data(proxy_model.index(0,2)), "in")

	def test_delete_link(self) -> None:
		data_model = PyDataModel()
		data_model.addNode("node1", PyNodeItem())
		data_model.addNode("node2", PyNodeItem(parameters=[PyParameterItem('in')]))
		data_model.linkNodes("node1", "node2", "in")

		proxy_model = PyProxyLinkModel(data_model)
		self.assertEqual(proxy_model.rowCount(), 1)
		data_model.unlinkNodes("node1", "node2", "in")
		self.assertEqual(proxy_model.rowCount(), 0)

	def test_source_model_reset(self):
		data_model = PyDataModel()
		data_model.addNode("node1", PyNodeItem())

		links_proxy = PyProxyLinkModel(data_model)
		nodes_proxy = links_proxy.itemsModel()
		
		data_model.deserialize(dedent(math_script))

		self.assertEqual(links_proxy.rowCount(), 2)
		for row in range(links_proxy.rowCount()):
			source, outlet = links_proxy.index(row, 0).data(GraphDataRole.LinkSourceRole)
			target, inlet = links_proxy.index(row, 0).data(GraphDataRole.LinkTargetRole)
			
			self.assertTrue(source.isValid())
			self.assertTrue(target.isValid())
			self.assertEqual(outlet, "out")
			self.assertIn(inlet, ("x", "y") )
			self.assertEqual(source.model(), nodes_proxy)
			self.assertEqual(target.model(), nodes_proxy)


class TestProxyLinkSignals(unittest.TestCase):
	def test_delete_link(self) -> None:
		data_model = PyDataModel()
		data_model.addNode("node1", PyNodeItem())
		data_model.addNode("node2", PyNodeItem(parameters=[PyParameterItem('in')]))
		data_model.linkNodes("node1", "node2", "in")

		proxy_model = PyProxyLinkModel(data_model)

		spy_about_to_be_removed = QSignalSpy(proxy_model.rowsAboutToBeRemoved)
		spy_removed = QSignalSpy(proxy_model.rowsRemoved)
		data_model.unlinkNodes("node1", "node2", "in")
		self.assertEqual(spy_about_to_be_removed.count(), 1, "'rowsAboutToBeRemoved' Signal was not emitted exactly once.")
		self.assertEqual(spy_removed.count(), 1, "'rowsRemoved' Signal was not emitted exactly once.")


import inspect
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

		proxy = PyProxyParameterModel(data_model)
		proxy.setNode("hello")

		data_model.compileNodes(["hello"])
		self.assertEqual(proxy.rowCount(), 1)

		self.assertEqual(proxy.data(proxy.index(0,0), Qt.ItemDataRole.DisplayRole), "name")
		self.assertEqual(proxy.data(proxy.index(0,0), Qt.ItemDataRole.EditRole), "name")
		self.assertEqual(proxy.data(proxy.index(0,1), Qt.ItemDataRole.DisplayRole), '-Empty-')
		self.assertEqual(proxy.data(proxy.index(0,1), Qt.ItemDataRole.EditRole), Empty)
		

if __name__ == "__main__":
	unittest.main()