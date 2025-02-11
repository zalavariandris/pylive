from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import unittest
import sys
app= QApplication( sys.argv )

from pylive.QtGraphEditor.py_functions_model import PyFunctionsModel

class TestFunctionsModelCRUD(unittest.TestCase):
	def setUp(self) -> None:
		self.model = PyFunctionsModel()

	def test_insert_hello_function(self):
		from textwrap import dedent
		source = dedent("""\
		def my_hello():
			return "HELLO"
		""")

		def my_hello():
			return "HELLO"


		self.model.insertFunction(0, my_hello)

		self.assertEqual(self.model.rowCount(), 1)
		self.assertEqual(self.model.functionName(0), "my_hello")
		self.assertEqual(self.model.functionSource(0), dedent(source))
		print("test_insert_function")

	def test_insert_placeholder_function(self):
		from textwrap import dedent
		source = dedent("""\
		def _():
			...
		""")

		def _():
			...

		self.model.insertFunction(0, _)
		self.assertEqual(self.model.rowCount(), 1)
		self.assertEqual(self.model.functionName(0), "_")
		self.assertEqual(self.model.functionSource(0), dedent(source))
		print("test_insert_function")

	def test_inserting_the_same_function_multiple_times(self):
		def func():
			...

		self.model.insertFunction(self.model.rowCount(), func)
		self.model.insertFunction(self.model.rowCount(), func)

		self.assertEqual(self.model.rowCount(), 2)

	def test_insert_rows(self):
		self.model.insertRows(0, 5)
		self.assertEqual(self.model.rowCount(), 5)

	def test_remove_rows(self):
		def func1():
			...
		def func2():
			...
		def func3():
			...
		def func4():
			...
		def func5():
			...
		self.model.insertFunction(0, func1)
		self.model.insertFunction(1, func2)
		self.model.insertFunction(2, func3)
		self.model.insertFunction(3, func4)
		self.model.insertFunction(4, func5)
		
		self.model.removeRows(1, 3)
		self.assertEqual(self.model.rowCount(), 2)
		self.assertEqual(self.model.functionName(0), "func1")
		self.assertEqual(self.model.functionName(1), "func5")

	@unittest.skip("lambdas not yet supported")
	def test_lambda_functions(self):
		...

	def test_function_source(self):
		...

	def test_source_with_built_in_functions(self):
		...

	def test_sett_function_source(self):
		print("test_data")

	def test_setting_function(self):
		print("test_setting_function")

if __name__ == "__main__":
	# app = QApplication()
	# app.exit()
	unittest.main()