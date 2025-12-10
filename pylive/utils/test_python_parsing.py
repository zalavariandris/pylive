from typing import *
import unittest

from pylive.utils.evaluate_python import compile_python_function
from textwrap import dedent


class TestParseFunctions(unittest.TestCase):
    def test_parse_single_function(self):
        script = dedent("""\
        def hello(name:str)->str:
            return f"Hello {name}!"
        """)
        func = compile_python_function(script)
        self.assertEqual(func.__name__, "hello")

    def test_multiple_functions(self):
        script = dedent("""\
        def hello1(name:str)->str:
            return f"Hello {name}!"

        def hello2(name:str)->str:
            return f"Hello {name}!"
        """)
        func = compile_python_function(script)
        self.assertEqual(func.__name__, "hello1")

    def test_python_script_with_imports(self):
        script = dedent("""\
        import sys
        import os
        def hello1(name:str)->str:
            return f"Hello {name}!"
        """)
        func = compile_python_function(script)
        print(func)
        self.assertEqual(func.__name__, "hello1")

    def test_python_script_with_typing_imports(self):
        script = dedent("""\
        from typing import *
        from PySide6.QtCore import *
        from PySide6.QtGui import *
        from PySide6.QtWidgets import *

        def create_widget():
            return QLabel("hello")
        """)

        func = compile_python_function(script)
        self.assertIsNotNone(func)
        self.assertEqual(func.__name__, 'create_widget')

    def test_python_script_without_function(self):
        with self.assertRaises(ValueError):
            func = compile_python_function("")






if __name__ == "__main__":
    unittest.main()
