import unittest
from typing import *
from pylive.QtScriptEditor.cell_support import cell_at_line, split_cells
from textwrap import dedent

class TestGraphCreations(unittest.TestCase):
	def test_split_cells(self):
		cell1 = dedent("""\
		# %% setup
		from textwrap import dedent

		script = \"\"\"
		# %% hello
		\"\"\"
		""")

		cell2 = dedent("""\
		# %% update
		from pylive.QtLiveApp import display

		display(script)
		""")
		script = "\n".join([cell1, cell2])
		cells = split_cells(script)

		# print(f"<script>\n{script}\n</script>")

		self.assertEqual(cells[0], cell1)
		self.assertEqual(cells[1], cell2)

	def test_cell_at_line(self):
		script = dedent("""\
		# %% setup
		from textwrap import dedent
 
 		script = \"\"\"
 		# %% hello
 		\"\"\"
 
 		# %% update
 		from pylive.QtLiveApp import display
  
  		display(script)""")

		cells = split_cells(script)
		# print( "!!!!!!!!!!", script.split("\n")[7] )
		self.assertEqual(cell_at_line(cells,  0), 0)
		self.assertEqual(cell_at_line(cells,  1), 0)
		self.assertEqual(cell_at_line(cells,  2), 0)
		self.assertEqual(cell_at_line(cells,  3), 0)
		self.assertEqual(cell_at_line(cells,  4), 0)
		self.assertEqual(cell_at_line(cells,  5), 0)
		self.assertEqual(cell_at_line(cells,  6), 0)
		self.assertEqual(cell_at_line(cells,  7), 1)
		self.assertEqual(cell_at_line(cells,  8), 1)
		self.assertEqual(cell_at_line(cells,  9), 1)
		self.assertEqual(cell_at_line(cells, 10), 1)
		with self.assertRaises(IndexError):
			cell_at_line(cells, 11)
		

if __name__ == "__main__":
	unittest.main()
	