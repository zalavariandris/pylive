import ast
import textwrap
from typing import *
import networkx as nx

def analyze_dependencies(script):
	# Parse the Python script into an AST
	tree = ast.parse(script)
	
	# Dictionary to hold function dependencies
	function_dependencies = {}
	
	# Traverse the AST
	for node in ast.walk(tree):
		if isinstance(node, ast.FunctionDef):  # Find function definitions
			function_name = node.name
			function_dependencies[function_name] = []
			
			# Analyze the body of the function for function calls
			for subnode in ast.walk(node):
				if isinstance(subnode, ast.Call) and isinstance(subnode.func, ast.Name):
					called_function = subnode.func.id
					function_dependencies[function_name].append(called_function)
	
	return function_dependencies

def create_nx_graph_from_script(script:str)->nx.Graph:
	# Parse the Python script into an AST
	tree = ast.parse(script)
	
	# Dictionary to hold function dependencies
	G = nx.Graph()
	
	# Traverse the AST
	for node in ast.walk(tree):
		if isinstance(node, ast.FunctionDef):  # Find function definitions
			function_name = node.name
			
			# Analyze the body of the function for function calls
			for subnode in ast.walk(node):
				if isinstance(subnode, ast.Call) and isinstance(subnode.func, ast.Name):
					called_function = subnode.func.id
					G.add_edge(function_name, called_function)
	
	return G



if __name__ == "__main__":
	from PySide6.QtGui import *
	from PySide6.QtCore import *
	from PySide6.QtWidgets import *

	from pylive.QtGraphEditor.dag_graph_graphics_scene import (
		DAGScene, NodeWidget, InletWidget, OutletWidget, EdgeWidget
	)
	from pylive.QtScriptEditor.script_edit import ScriptEdit

	# Example usage
	from textwrap import dedent
	python_script = dedent("""
	def foo():
		bar()
		baz()

	def bar():
		baz()

	def baz():
		pass
	""")

	import sys
	app = QApplication(sys.argv)

	# setup main window
	window = QWidget()
	mainLayout = QHBoxLayout()
	mainLayout.setContentsMargins(0,0,0,0)
	window.setLayout(mainLayout)

	scriptedit = ScriptEdit()
	mainLayout.addWidget(scriptedit)
	graph_scene = DAGScene()
	graphview = QGraphicsView()
	mainLayout.addWidget(graphview)

	def update_dependency_graph():
		python_script = scriptedit.toPlainText()
		try:
			dependencies = analyze_dependencies(python_script)
			G = create_nx_graph_from_script(python_script)
		except SyntaxError:
			pass
		except Exception:
			pass
		else:
			for func, deps in dependencies.items():
				print(f"{func} calls: {', '.join(deps) if deps else 'None'}")

			for node in G.nodes():
				graph_scene.addNode(NodeWidget(title=str(node)))





	scriptedit.textChanged.connect(lambda: 
		update_dependency_graph())
	scriptedit.setPlainText(python_script)



	# # create graph scene
	# graphscene = DAGScene()
	# graphscene.setSceneRect(QRectF(-400, -400, 800, 800))
	# graphview.setScene(graphscene)

	# # Create nodes
	# read_text_node = NodeWidget("Read Text")
	# outlet = OutletWidget("text out")
	# read_text_node.addOutlet(outlet)
	# graphscene.addNode(read_text_node)
	# read_text_node.moveBy(-70, -70)

	# convert_node = NodeWidget("Markdown2Html")
	# inlet  =InletWidget("Markdown in")
	# convert_node.addInlet(inlet)
	# convert_node.addOutlet(OutletWidget("HTML out"))
	# graphscene.addNode(convert_node)
	# convert_node.moveBy(0, 0)

	# write_text_node = NodeWidget("Write Text")
	# write_text_node.addInlet(InletWidget("text in"))
	# graphscene.addNode(write_text_node)
	# write_text_node.moveBy(70, 100)

	# # create edge1
	# edge1 = EdgeWidget(outlet, inlet)
	# graphscene.addEdge(edge1)

	# set nodes orientation
	# for node in (item for item in graphscene.items() if isinstance(item, NodeWidget)):
	# 	node.setOrientation(Qt.Orientation.Vertical)

	# show window
	window.show()
	sys.exit(app.exec())

