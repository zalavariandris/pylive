from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import unittest
import sys
app= QApplication( sys.argv )

from pylive.QtGraphEditor.main_py_functions import Window

class TestSerialization(unittest.TestCase):
	def setUp(self) -> None:
		self.window = Window()

	
	def test_file_open(self):
		self.window.openFile("./website_builder.yaml")

	

if __name__ == "__main__":
	unittest.main()